"""Tiny technical fixtures only; no Stage D scientific pilot or acceptance gates."""
import csv
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e1_observer_check import verify
from semiflexible_reference import Chain
SIM = Path(sys.argv.pop(1)).resolve()
ARTIFACTS = Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


class ObserverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='e1-d1-technical-')
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_sim(self, name, n=8, kappa=10, dt='.00025', z=6, rate=20000, steps=12, observer=True, snapshots=True, extra=()):
        out = self.root/name
        schedule = self.root/(name+'.steps'); schedule.write_text(f'0 1 2 5 {steps}\n' if steps else '0\n')
        argv = [str(SIM), '--output', str(out), '--springs', str(n), '--chains', '4', '--steps', str(steps),
                '--sample', '4', '--seed', '914203', '--kappa', str(kappa), '--dt', dt,
                '--slip-count', str(z), '--slip-ms2', '5', '--hop-rate', str(rate), '--end-renewal', '1']
        if observer:
            argv += ['--equilibrium-steps', str(schedule)]
            if snapshots:
                argv += ['--equilibrium-snapshots', str(schedule)]
        result = subprocess.run(argv+list(extra), text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return out

    def compare_legacy(self,off,on):
        legacy = sorted(p.name for p in off.iterdir())
        for name in legacy:
            if name == 'metadata.json':
                a,b = json.loads((off/name).read_text()), json.loads((on/name).read_text())
                timing = {key for key in a if 'seconds' in key or 'ns_per_bead_step' in key or key=='bead_updates_per_second'}
                self.assertEqual({k:v for k,v in a.items() if k not in timing}, {k:v for k,v in b.items() if k not in timing})
                pattern = r'("(?:'+'|'.join(sorted(timing))+r')":)[^,}]*'
                self.assertEqual(re.sub(pattern,r'\1TIMING',(off/name).read_text()),
                                 re.sub(pattern,r'\1TIMING',(on/name).read_text()))
            else:
                self.assertEqual((off/name).read_bytes(), (on/name).read_bytes(), name)

    def test_reconstruction_nonperturbation_both_backbones_and_timesteps(self):
        metrics = []
        accepted_hops = cross_renewals = empty = multiple = 0
        for n, k, dt, z, rate in ((8,0,'.0001',6,20000), (32,10,'.00025',6,20000),
                                  (8,10,'.00005',6,20000), (8,0,'.00025',0,0),
                                  (8,10,'.0001',6,0), (1,0,'.00025',8,20000)):
            off = self.run_sim('off', n,k,dt,z,rate,observer=False)
            on = self.run_sim('on', n,k,dt,z,rate)
            result = verify(on)
            self.assertEqual(result['frames'],5)
            self.compare_legacy(off,on)
            # Actual initialized/final coordinates and spring anchors must be the
            # same as the observer's synchronized endpoint snapshots.
            for step,name in ((0,'initial.csv'),(12,'final.csv')):
                snap=[{k:r[k] for k in ('chain','bead','x','y','z')} for r in rows(on/'equilibrium_positions.csv') if int(r['step'])==step]
                self.assertEqual(snap,rows(on/name))
                if z:
                    name='slip_springs_'+('initial' if step==0 else 'final')+'.csv'
                    if not (on/name).exists(): name='fixed_slip_springs.csv'
                    keys=tuple(rows(on/name)[0])
                    actual=[{k:r[k] for k in keys} for r in rows(on/'equilibrium_attachments.csv') if int(r['step'])==step]
                    self.assertEqual(actual,rows(on/name))
            # At legacy sample steps these are the exact same reductions/values.
            supplement=rows(on/'equilibrium_backbone.csv')
            self.assertEqual({int(r['step']) for r in supplement},{1,2,5})
            bb={(r['step'],r['chain']):r for r in rows(on/'samples.csv')+supplement}
            for r in rows(on/'samples.csv'):
                if (r['step'],r['chain']) in bb:
                    for key,value in bb[r['step'],r['chain']].items():
                        if key in r:self.assertEqual(value,r[key])
            # Independent snapshot sizes and connector states give identical D0
            # joint diagnostics, including empty and multiply populated chains.
            for step in (0,1,2,5,12):
                r=np.array([[float(v[k]) for k in ('x','y','z')] for v in rows(on/'equilibrium_positions.csv') if int(v['step'])==step]).reshape(4,n+1,3)
                re2=np.sum((r[:,-1]-r[:,0])**2,axis=1)
                at=[v for v in rows(on/'equilibrium_attachments.csv') if int(v['step'])==step]
                pops=np.zeros(4);squares=np.zeros(4)
                for a in at:
                    c=int(a['chain']);pops[c]+=1;e=r[c,int(a['bead'])]-[float(a[k]) for k in ('ax','ay','az')];squares[c]+=e@e
                cs=[v for v in rows(on/'equilibrium_chains.csv') if int(v['step'])==step]
                measured_re2=np.array([float(bb[str(step),str(c)]['re2']) for c in range(4)])
                measured_z=np.array([int(v['z']) for v in cs]);measured_e2=np.array([float(v['e2_sum']) for v in cs])
                target=Chain.homogeneous(n,kappa=k).equilibrium_predictions()['re2']
                f=re2/target-1;observed_f=measured_re2/target-1
                np.testing.assert_allclose((f*(squares-5*pops)).sum()/(max(z,1)*5),
                    (observed_f*(measured_e2-5*measured_z)).sum()/(max(z,1)*5),rtol=3e-12,atol=3e-12)
                if 0<z<4*(n+1):
                    rho=z/(4*(n+1));sigma=np.sqrt((n+1)*rho*(1-rho)*(3*(n+1))/(4*(n+1)-1))
                    np.testing.assert_allclose((f*(pops-z/4)).sum()/(4*sigma),
                        (observed_f*(measured_z-z/4)).sum()/(4*sigma),rtol=3e-12,atol=3e-12)
            if z and rate and n>1:
                counts=json.loads((on/'hopping_metadata.json').read_text())
                accepted_hops += counts['accepted']
                cross_renewals += counts['renewal_cross_chain']
                for key,name in (('batches','batches'),('attempts','attempts'),('accepted','accepted'),('boundary','outward_proposals'),
                                 ('occupied','occupied_rejected'),('metropolis','metropolis_rejected'),('renewal_proposed','renewal_proposed'),
                                 ('renewal_accepted','renewal_accepted'),('renewal_occupied','renewal_occupied_rejected'),
                                 ('renewal_same_chain','renewal_same_chain'),('renewal_cross_chain','renewal_cross_chain')):
                    self.assertEqual(result['totals'][key],counts[name])
            for state in rows(on/'equilibrium_chains.csv'):
                empty += int(state['z']) == 0
                multiple += int(state['z']) > 1
            metrics.append({'N':n,'kappa':k,'dt':dt,'Z':z,'rate':rate,
                            'off':json.loads((off/'metadata.json').read_text()),'on':json.loads((on/'metadata.json').read_text()),
                            'observer':json.loads((on/'equilibrium_complete.json').read_text())})
            if ARTIFACTS:
                target=ARTIFACTS/f'N{n}-k{k}-dt{dt}-z{z}-rate{rate}'
                shutil.copytree(on,target)
            shutil.rmtree(on);shutil.rmtree(off)
        self.assertGreater(accepted_hops,0)
        self.assertGreater(cross_renewals,0)
        self.assertGreater(empty,0)
        self.assertGreater(multiple,0)
        if ARTIFACTS:
            ARTIFACTS.mkdir(parents=True,exist_ok=True)
            (ARTIFACTS/'metrics.json').write_text(json.dumps(metrics,indent=2))

    def test_partial_final_interval_and_renewal_off(self):
        extra=('--end-renewal','0')
        off=self.run_sim('off-partial', kappa=0, dt='.0001', steps=13, observer=False, extra=extra)
        on=self.run_sim('on-partial', kappa=0, dt='.0001', steps=13, snapshots=False, extra=extra)
        result=verify(on)
        self.compare_legacy(off,on)
        self.assertEqual(result['frames'],5)
        self.assertEqual(result['snapshots'],2)
        self.assertEqual(result['totals']['batches'],13)
        counters=json.loads((on/'hopping_metadata.json').read_text())
        self.assertEqual(result['totals']['boundary'],counters['boundary_rejected'])
        self.assertGreater(counters['boundary_rejected'],0)
        self.assertEqual(result['totals']['renewal_proposed'],0)
        self.assertEqual(int(rows(on/'equilibrium_events.csv')[-1]['step']),13)
        self.assertEqual({int(r['step']) for r in rows(on/'equilibrium_backbone.csv')},{1,2,5,13})

    def test_zero_steps_and_default_endpoint_snapshots(self):
        out=self.run_sim('zero',steps=0,snapshots=False)
        self.assertEqual(verify(out)['snapshots'],1)
        out=self.run_sim('default',snapshots=False)
        self.assertEqual(verify(out)['snapshots'],2)
        complete=out/'equilibrium_complete.json';saved=complete.read_bytes();complete.unlink()
        with self.assertRaises(OSError):verify(out)
        complete.write_bytes(saved)
        with (out/'equilibrium_backbone.csv').open('a') as stream:stream.write('truncated\n')
        with self.assertRaises(ValueError):verify(out)

    def test_schedule_validation_before_execution(self):
        schedule=self.root/'steps'
        for text in ('','1 12','0 0 12','0 2 1 12','0 13','0 1','0 .0001 12','0 1e-4 12','0 -1 12'):
            schedule.write_text(text)
            out=self.root/'invalid'
            result=subprocess.run([str(SIM),'--output',str(out),'--steps','12','--equilibrium-steps',str(schedule)],capture_output=True,timeout=20)
            self.assertNotEqual(result.returncode,0);self.assertFalse(out.exists())

        schedule.write_text('0 1 2 5 12\n')
        snapshots=self.root/'snapshots'
        for text in ('0 3 12', '0 1 2 3 4 5 6 7 12', '0 1', '0 .5 12'):
            snapshots.write_text(text)
            result=subprocess.run([str(SIM),'--output',str(self.root/'invalid'),'--steps','12',
                '--equilibrium-steps',str(schedule),'--equilibrium-snapshots',str(snapshots)],capture_output=True,timeout=20)
            self.assertNotEqual(result.returncode,0);self.assertFalse((self.root/'invalid').exists())
        result=subprocess.run([str(SIM),'--output',str(self.root/'invalid'),'--equilibrium-times','0,.0001'],capture_output=True,timeout=20)
        self.assertNotEqual(result.returncode,0);self.assertFalse((self.root/'invalid').exists())


if __name__=='__main__':
    if ARTIFACTS: ARTIFACTS.mkdir(parents=True,exist_ok=True)
    unittest.main()
