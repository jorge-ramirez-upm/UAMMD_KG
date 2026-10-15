#!/usr/bin/env python3
"""Bounded pipeline tests; no scientific campaign. Pass --sync-only during bring-up."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np

COLS = ('Cxy','Cxz','Cyz','Cxx_yy','Cxx_zz','Cyy_zz')

def compare(csv, stream):
    meta = json.loads((stream/'metadata.json').read_text())
    raw = np.atleast_1d(np.genfromtxt(csv/'samples.csv', names=True, delimiter=','))
    raw = raw[raw['step'] % meta['sample'] == 0].reshape(-1, meta['chains'])
    series = np.stack([raw['Sxy'],raw['Sxz'],raw['Syz'],raw['Sxx']-raw['Syy'],
                       raw['Sxx']-raw['Szz'],raw['Syy']-raw['Szz']], axis=-1)
    rows = np.atleast_1d(np.genfromtxt(stream/'relaxation.csv', names=True, delimiter=','))
    assert len(series) == meta['stress_frames'] == meta['steps']//meta['sample']+1
    assert not (stream/'samples.csv').exists()
    for field in ('transfer_seconds','sampling_gpu_seconds','cpu_correlation_seconds',
                  'buffer_wait_seconds','transfer_wait_seconds','final_output_seconds'):
        assert meta[field]>=0
    if not meta['steps']:
        for field in ('integration_ns_per_bead_step','overall_ns_per_bead_step','bead_updates_per_second'):
            assert meta[field] is None
    else:
        updates=meta['beads']*meta['steps']
        np.testing.assert_allclose(meta['integration_ns_per_bead_step'],1e9*meta['update_seconds']/updates)
        np.testing.assert_allclose(meta['overall_ns_per_bead_step'],1e9*meta['production_seconds']/updates)
    assert meta['coordinate_diagnostics_available'] is False
    assert meta['max_abs_coordinate'] is None
    for row in rows:
        block = int(row['block_samples'])
        lag = int(row['lag_samples'])//block
        blocks = series[:len(series)//block*block].reshape(-1,block,meta['chains'],6).mean(axis=1)
        products = (blocks[lag:]*blocks[:len(blocks)-lag]).mean(axis=0)
        expected = products.mean(axis=0)
        np.testing.assert_allclose([row[x] for x in COLS], expected, rtol=2e-11, atol=2e-11)
        g = products[:,:3].sum(axis=1)/5 + products[:,3:].sum(axis=1)/30
        np.testing.assert_allclose(row['g'],g.mean(),rtol=2e-11,atol=2e-11)
        np.testing.assert_allclose(row['g_se'],g.std(ddof=1)/np.sqrt(len(g)) if len(g)>1 else float('nan'),rtol=2e-11,atol=2e-11)
        assert row['pairs_per_chain']==len(blocks)-lag
        assert row['pairs_total']==(len(blocks)-lag)*meta['chains']
        np.testing.assert_allclose(row['lag_time'],row['lag_samples']*meta['sample']*meta['dt'])
    return rows

def main():
    if sys.argv[1]=='--compare':
        compare(Path(sys.argv[2]),Path(sys.argv[3]))
        print('PASS: existing CSV versus streaming, including block bins and paired uncertainty')
        return
    binary = str(Path(sys.argv[1]).resolve())
    sync_only = '--sync-only' in sys.argv[2:]
    with tempfile.TemporaryDirectory(prefix='rouse-stream-short-') as temp:
        root = Path(temp)
        # Includes initial/zero samples, initial-only equilibration, incomplete
        # final batch, irregular final MD interval, exact batch boundary and N=1.
        cases = [(0,0,3,4,1),(0,3,3,4,8),(7,3,2,3,1),(76,2,2,4,8),(76,0,2,1,8),(0,0,2,4,1)]
        for index,(steps,equil,stride,batch,n) in enumerate(cases):
            args = [binary,'--springs',str(n),'--chains',('1' if index==5 else '8'),'--dt','0.005','--steps',str(steps),
                    '--equil',str(equil),'--sample',str(stride),'--seed','582001',
                    '--corr-levels','5','--corr-slots',('12' if index==4 else '8'),
                    '--corr-m',('3' if index==4 else '2'),'--batch',str(batch)]
            paths = {}
            for mode in ('csv','sync') if sync_only else ('csv','sync','async'):
                dest = root/f'{index}-{mode}'
                cmd = args+['--output',str(dest)]
                if mode!='csv': cmd += ['--output-mode','stream','--backend',mode]
                completed = subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                if completed.returncode: raise AssertionError(completed.stdout)
                paths[mode]=dest
            sync = compare(paths['csv'],paths['sync'])
            if not sync_only:
                compare(paths['csv'],paths['async'])
                assert (paths['sync']/'relaxation.csv').read_bytes()==(paths['async']/'relaxation.csv').read_bytes()
            assert len(sync)>0
            if index==3 and not sync_only:
                for other_batch in (1,39,40):
                    dest=root/f'batch-{other_batch}'
                    completed=subprocess.run(args+['--batch',str(other_batch),'--output-mode','stream',
                       '--backend','async','--output',str(dest)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                    if completed.returncode: raise AssertionError(completed.stdout)
                    assert (dest/'relaxation.csv').read_bytes()==(paths['sync']/'relaxation.csv').read_bytes()
        for index,extra in enumerate((['--batch','0'],['--batch','4097'],['--backend','other'],
                ['--corr-slots','7'],['--corr-m','1'],['--corr-levels','48','--corr-slots','65536'],
                ['--chains','100000','--correlator-mib','1'],['--chains','100000','--batch','4096'])):
            dest=root/f'invalid-{index}'
            completed=subprocess.run([binary,'--output-mode','stream','--output',str(dest)]+extra,
                                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            assert completed.returncode!=0 and not dest.exists(), completed.stdout
        print(f'PASS: {len(cases)} bounded pipeline cases; all raw channels, paired g SE, lag/count/block/timer conventions; 8 input guards')

if __name__=='__main__': main()
