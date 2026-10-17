"""Bounded Stage 4A.3b tests, independent tensor and block-product oracles."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain
from semiflexible_stress_reference import virials

COMPARE = sys.argv[1:2]==['--compare']
if not COMPARE:
    BINARY, FIXTURE = map(lambda p: Path(p).resolve(), sys.argv[1:3])
    OTHER = Path(sys.argv[3]).resolve() if len(sys.argv)>3 else None
    sys.argv[1:] = []
COLS = ('Cxy','Cxz','Cyz','Cxx_yy','Cxx_zz','Cyy_zz')


def csv(path):
    return np.atleast_1d(np.genfromtxt(path, names=True, delimiter=',', dtype=None, encoding='utf-8'))


def parameters(path, model):
    path.write_text(str(model.n)+'\n'+''.join(f'{b:.17g} {k:.17g}\n' for b,k in zip(model.b0,model.kb))
                    +' '.join(f'{k:.17g}' for k in model.kappa)+'\n')


def actual_model(path):
    values = path.read_text().split();n=int(values[0]);bonds=np.array(values[1:1+2*n],float).reshape(n,2)
    return Chain(bonds[:,0],bonds[:,1],np.array(values[1+2*n:],float))


def coords(path):
    table=csv(path)
    return np.column_stack([table[k] for k in ('x','y','z')])


def check_direct(test, series, path, spacing, kbt, density, cfg=(5,8,2)):
    rows=csv(path)
    test.assertGreater(len(rows),0)
    levels,slots,m=cfg
    highest,width=0,1
    while highest+1<levels and width*m<=len(series):highest+=1;width*=m
    expected_lags=list(range(min(slots,len(series))))
    for level in range(1,highest):
        block=m**level
        expected_lags += [j*block for j in range(slots//m,slots) if j<len(series)//block]
    test.assertEqual(list(rows['lag_samples']),expected_lags)
    for row in rows:
        block=int(row['block_samples']);lag=int(row['lag_samples'])//block
        complete=len(series)//block
        blocks=series[:complete*block].reshape(complete,block,series.shape[1],6).mean(axis=1)
        products=(blocks[lag:]*blocks[:len(blocks)-lag]).mean(axis=0)
        expected=products.mean(axis=0)
        np.testing.assert_allclose([row[k] for k in COLS],expected,rtol=3e-11,atol=3e-11)
        paired=products[:,:3].sum(axis=1)/5+products[:,3:].sum(axis=1)/30
        se=paired.std(ddof=1)/math.sqrt(len(paired)) if len(paired)>1 else np.nan
        np.testing.assert_allclose([row['H'],row['H_se']],[paired.mean(),se],rtol=3e-11,atol=3e-11,equal_nan=True)
        np.testing.assert_allclose(row['g'],row['H']/kbt**2,rtol=2e-14)
        np.testing.assert_allclose(row['g_se'],row['H_se']/kbt**2,rtol=2e-14,equal_nan=True)
        if density:
            np.testing.assert_allclose(row['G'],density*row['H']/kbt,rtol=2e-14)
        test.assertEqual(row['pairs_per_chain'],complete-lag)
        test.assertEqual(row['pairs_total'],(complete-lag)*len(products))
        test.assertAlmostEqual(row['lag_time'],row['lag_samples']*spacing,delta=1e-12)
        expected_se=products.std(axis=0,ddof=1)/math.sqrt(len(products)) if len(products)>1 else np.full(6,np.nan)
        np.testing.assert_allclose([row[k+'_se'] for k in COLS],expected_se,rtol=3e-11,atol=3e-11,equal_nan=True)
    return rows


class StressChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='semiflexible-stress-bounded-')
        self.root=Path(self.temp.name);self.serial=0

    def tearDown(self):
        self.temp.cleanup()

    def run_model(self,model,positions=None,mode='off',chains=3,steps=0,stride=1,batch=4,workers=1,kbt=1.7,extra=(),expect=True,binary=None):
        self.serial+=1;out=self.root/str(self.serial);p=self.root/f'p{self.serial}.txt';parameters(p,model)
        args=[str(binary or BINARY),'--output',str(out),'--springs',str(model.n),'--chains',str(chains),'--parameters',str(p),
              '--steps',str(steps),'--sample',str(stride),'--dt','0.0001','--seed','433101','--kbt',str(kbt),
              '--stress-mode',mode,'--stress-batch',str(batch),'--cpu-workers',str(workers),'--corr-levels','5','--corr-slots','8']
        if positions is not None:
            initial=self.root/f'i{self.serial}.txt';np.savetxt(initial,np.asarray(positions).reshape(-1,3),fmt='%.17g')
            args+=['--force-input' if mode=='diagnostic' else '--initial',str(initial)]
        result=subprocess.run(args+list(extra),capture_output=True,text=True,timeout=60)
        if expect:self.assertEqual(result.returncode,0,result.stderr)
        else:self.assertNotEqual(result.returncode,0)
        return out

    def test_independent_tensors_precision_and_geometry(self):
        rotation,_=np.linalg.qr(np.random.default_rng(433102).normal(size=(3,3)))
        shapes=[np.array([[0,0,0],[1.1,0,0],[1.8,.7,-.2],[2.1,.3,.9]]),
                np.array([[0,0,0],[1,0,0],[2,1e-7,0],[1,2e-7,1e-8]]),
                np.column_stack([np.arange(4),np.zeros(4),np.zeros(4)])]
        models=[Chain.homogeneous(1),Chain.homogeneous(2,kappa=4),Chain.homogeneous(3,kappa=0),
                Chain([0,.8,1.2],[2,15,40],[0,0,1000,0]),Chain.homogeneous(3,b0=0,kb=3,kappa=0)]
        records=[]
        for model in models:
            configurations=np.array([x[:model.n+1] for x in shapes]+[shapes[0][:model.n+1]@rotation+[2,-3,4]])
            out=self.run_model(model,configurations,mode='diagnostic',chains=4)
            stored=coords(out/'initial.csv').reshape(4,model.n+1,3)
            effective=actual_model(out/'parameters.txt');table=csv(out/'stress_tensors.csv')
            single=json.loads((out/'metadata.json').read_text())['precision_bits']==32
            records.append(dict(phase='diagnostic',precision='single' if single else 'double',output=str(out)))
            scale=max(1,model.kappa.max(),model.kb.max())
            terms={}
            for term in ('stretch','bend','total'):
                rows=table[table['term']==term]
                tensors=np.array([[row[f'w{a}{b}'] for a in range(3) for b in range(3)] for row in rows]).reshape(4,3,3)
                terms[term]=tensors
                for c in range(4):
                    expected=virials(effective,stored[c])[term]
                    np.testing.assert_allclose(tensors[c],expected,rtol=3e-6 if single else 3e-12,
                                               atol=(2e-7 if single else 5e-13)*scale)
                    np.testing.assert_allclose(tensors[c],tensors[c].T,rtol=0,atol=1e-11*scale)
                    if term=='bend':self.assertAlmostEqual(np.trace(tensors[c]),0,delta=3e-11*scale)
                np.testing.assert_allclose(tensors[3],rotation.T@tensors[0]@rotation,
                                           atol=(1e-5 if single else 3e-12)*scale,rtol=3e-5 if single else 3e-12)
            np.testing.assert_allclose(terms['total'],terms['stretch']+terms['bend'],rtol=3e-14,atol=3e-12*scale)
            np.testing.assert_array_equal(coords(out/'initial.csv'),coords(out/'final.csv'))
            meta=json.loads((out/'stress_metadata.json').read_text())
            if effective.active_angles is None:
                self.assertEqual(meta['bending_stress_device_bytes'],0)
                self.assertEqual(meta['bending_stress_launches'],0)
            if OTHER:
                other=self.run_model(model,configurations,mode='diagnostic',chains=4,binary=OTHER)
                other_table=csv(other/'stress_tensors.csv')
                for a in range(3):
                    for b in range(3):
                        np.testing.assert_allclose(table[f'w{a}{b}'],other_table[f'w{a}{b}'],atol=1e-5*scale,rtol=3e-5)

        import semiflexible_stress_host as host
        (self.root/'manifest.json').write_text(json.dumps(records))
        self.assertFalse(host.check_diagnostics(self.root))

    def test_singular_and_inactive_angles(self):
        mixed=Chain([0,1,1],[2,3,4],[0,0,2,0])
        positions=[[0,0,0],[0,0,0],[1,0,0],[1,1,0]]
        self.run_model(mixed,positions,mode='diagnostic',chains=1)
        for model in (Chain.homogeneous(2),Chain.homogeneous(2,b0=0,kappa=2)):
            out=self.run_model(model,np.zeros((3,3)),mode='diagnostic',chains=1,expect=False)
            self.assertTrue((out/'failure.json').exists() or (out/'stress_failure.json').exists())
        for extra in (('--stress-mode','bad'),('--stress-batch','0'),('--cpu-workers','4'),
                      ('--corr-slots','7'),('--chain-density','-1'),('--correlator-mib','0')):
            self.run_model(Chain.homogeneous(2),mode='stream',chains=3,extra=extra,expect=False)

    def test_stream_replay_isolation_unchanged_trajectory_and_direct(self):
        for model in (Chain.homogeneous(1,kappa=0),Chain([.8,1.2,1],[20,40,30],[0,0,3,0])):
            temperature=1 if model.n==1 else 1.7
            baseline=self.run_model(model,steps=39,stride=2,kbt=temperature)
            previous=None
            for workers,batch in ((1,1),(2,7),(3,32),(0,4)):
                out=self.run_model(model,mode='stream',steps=39,stride=2,workers=workers,batch=batch,kbt=temperature,
                                   extra=('--stress-dump','1','--chain-density','0.25'))
                for name in ('initial.csv','final.csv','samples.csv','bond_statistics.csv'):
                    self.assertEqual((baseline/name).read_bytes(),(out/name).read_bytes())
                if previous:
                    for name in ('stress_samples.csv','stress_correlations.csv','stress_moments.csv'):
                        self.assertEqual((previous/name).read_bytes(),(out/name).read_bytes())
                previous=out
                series=csv(out/'stress_samples.csv');self.assertEqual(len(series),20*3)
                self.assertEqual(set(series['step']),set(range(0,39,2)))
                values=np.column_stack([series[k] for k in ('xy','xz','yz','xx_yy','xx_zz','yy_zz')]).reshape(20,3,6)
                check_direct(self,values,out/'stress_correlations.csv',0.0002,temperature,.25)
                moments=csv(out/'stress_moments.csv')
                selected=values[10:]  # step>=floor(39/2): frames20..38.
                for c in range(3):
                    self.assertEqual(moments[c]['frames'],len(selected))
                    np.testing.assert_allclose([moments[c][f'mean{a}'] for a in range(6)],selected[:,c].mean(axis=0),rtol=2e-14,atol=2e-14)
                meta=json.loads((out/'stress_metadata.json').read_text())
                self.assertEqual(meta['frames'],20)
                for field in ('gpu_stress_seconds','stress_transfer_seconds','cpu_correlation_seconds','cpu_barrier_seconds','finalization_output_seconds'):
                    self.assertGreaterEqual(meta[field],0)
                if model.active_angles is None:
                    self.assertEqual(meta['bending_stress_device_bytes'],0);self.assertEqual(meta['bending_stress_launches'],0)
                else:self.assertEqual(meta['bending_stress_launches'],20)
            more=self.run_model(model,mode='stream',chains=5,steps=39,stride=2,kbt=temperature,extra=('--stress-dump','1'))
            np.testing.assert_array_equal(coords(more/'final.csv')[:3*(model.n+1)],coords(baseline/'final.csv'))
            longer=csv(more/'stress_samples.csv').reshape(20,5)[:,:3]
            original=csv(previous/'stress_samples.csv').reshape(20,3)
            for name in ('xy','xz','yz','xx_yy','xx_zz','yy_zz'):np.testing.assert_array_equal(longer[name],original[name])
        zero=self.run_model(Chain.homogeneous(2),mode='stream',steps=0,extra=('--stress-dump','1'))
        self.assertEqual(json.loads((zero/'stress_metadata.json').read_text())['frames'],1)
        self.assertIsNone(json.loads((zero/'metadata.json').read_text())['integration_ns_per_bead_step'])

    def test_gaussian_control_reuses_validated_discrete_rouse_reference(self):
        from stream_analysis import reference
        model=Chain.homogeneous(2,b0=0,kb=3,kappa=0)
        out=self.run_model(model,mode='stream',chains=2048,steps=40,stride=2,kbt=1.7,extra=('--dt','.02'))
        meta=dict(springs=2,dt=.02,sample=2,stress_frames=21,equil=0)
        for row in csv(out/'stress_correlations.csv'):
            expected=reference(meta,int(row['lag_samples']),int(row['block_samples']))
            self.assertLessEqual(abs(row['g']-expected),6*row['g_se']+1e-5)
            for name in COLS:
                factor=4 if name in COLS[3:] else 1
                target=expected*factor*1.7**2
                self.assertLessEqual(abs(row[name]-target),6*row[name+'_se']+1e-5)

    def test_campaign_generation_does_not_execute(self):
        import semiflexible_stress_host as host
        root=self.root/'campaign'
        manifest=host.generate(root,BINARY.parent.parent)
        from collections import Counter
        self.assertEqual(Counter(r['phase'] for r in manifest),dict(stream=162,diagnostic=54,reference=54,memory=12))
        self.assertEqual(len(list(root.glob('*/metadata.json'))),0)
        for script in root.glob('*.sh'):
            result=subprocess.run(['sh','-n',str(script)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('STAGE4A3B_REVIEWED',script.read_text())
        with self.assertRaises(FileExistsError):host.generate(root,BINARY.parent.parent)

    def test_cpu_admission_errors_join_persistent_workers(self):
        for value in ('-10000000000','nan'):
            initial=self.root/f'invalid-{value}.txt'
            initial.write_text('3 1\n'+(' '.join([value]+['1']*5)+'\n')*3)
            self.serial+=1;out=self.root/str(self.serial)
            result=subprocess.run([str(FIXTURE),str(initial),str(out),'5','8','2','2','7','1','0','0'],capture_output=True,text=True,timeout=15)
            self.assertNotEqual(result.returncode,0)
            self.assertTrue('sentinel' in result.stderr or 'nonfinite' in result.stderr,result.stderr)

    def test_direct_synthetic_correlations_all_blocks_workers(self):
        rng=np.random.default_rng(433103)
        series=[np.ones((1,1,6))*2,np.tile(np.arange(18).reshape(1,3,6)/5,(7,1,1)),
                np.sin(np.arange(64)[:,None,None]*np.pi/4)*np.ones((1,3,6)),rng.normal(size=(65,4,6))+2]
        stretch=rng.normal(size=(47,3,6));bend=.7*stretch+1
        series.append(stretch+bend)  # Nonzero cross terms must survive assembly.
        series.append(np.repeat(rng.normal(size=(35,1,6)),3,axis=1))
        for case,values in enumerate(series):
            initial=self.root/f'seq{case}.txt'
            with initial.open('w') as f:
                f.write(f'{values.shape[1]} {len(values)}\n');np.savetxt(f,values.reshape(-1,6),fmt='%.17g')
            for coarsening,slots in ((2,8),(3,6)):
                previous=None
                for workers,batch in ((1,1),(values.shape[1],7),(0,32)):
                    self.serial+=1;out=self.root/str(self.serial)
                    result=subprocess.run([str(FIXTURE),str(initial),str(out),'5',str(slots),str(coarsening),str(workers),str(batch),'1.7','.25','1'],capture_output=True,text=True,timeout=30)
                    self.assertEqual(result.returncode,0,result.stderr)
                    rows=check_direct(self,values,out/'stress_correlations.csv',.125,1.7,.25,(5,slots,coarsening))
                    if previous:self.assertEqual((previous/'stress_correlations.csv').read_bytes(),(out/'stress_correlations.csv').read_bytes())
                    previous=out
                    if case==4:
                        lag0=rows[rows['lag_samples']==0][0]
                        total=values**2;separate=stretch**2+bend**2
                        self.assertGreater(np.max(np.abs(total.mean(axis=(0,1))-separate.mean(axis=(0,1)))),.1)
                        np.testing.assert_allclose(lag0['Cxy'],total[:,:,0].mean())


if __name__=='__main__':
    if COMPARE:
        root=Path(sys.argv[2]);meta=json.loads((root/'stress_metadata.json').read_text())
        table=csv(root/'stress_samples.csv');chains=int(table['chain'].max())+1
        series=np.column_stack([table[k] for k in ('xy','xz','yz','xx_yy','xx_zz','yy_zz')]).reshape(-1,chains,6)
        assert len(series)==meta['frames']
        check_direct(unittest.TestCase(),series,root/'stress_correlations.csv',meta['spacing'],meta['kbt'],meta['chain_density'],(meta['levels'],meta['slots'],meta['coarsening']))
        print('PASS direct block products and normalization; not scientific acceptance')
    else:
        unittest.main(verbosity=2)
