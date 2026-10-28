#!/usr/bin/env python3
"""Prepared CPU-only malformed-output checks; never launches campaign children."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
from e1_d2a5_validate import curve_header, curves, finite_json
from e1_d2a5_campaign import authenticate


def reject(action):
    try:
        action()
    except (ValueError,KeyError,AssertionError):
        return
    raise AssertionError('malformed evidence accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=PROJECT/'build/d2a5-campaign-regression-v1')
    output = parser.parse_args().output.resolve()
    assert output.is_relative_to((PROJECT/'build').resolve()), 'persistent project build fixture required'
    output.mkdir(parents=True,exist_ok=False)
    config = PROJECT/'e1_d2a5_production_config'
    raw = (config/'manifest.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (config/'manifest.sha256').read_text().split()[0]
    manifest = json.loads(raw)
    reject(lambda: authenticate(config,'0'*64))
    runs = manifest['runs']
    assert len(runs) == len({r['seed'] for r in runs}) == len({r['replica_id'] for r in runs}) == 24
    for prior in ('e1_d2a3_config','e1_d2a4_config'):
        old = json.loads((PROJECT/prior/'manifest.json').read_text())
        assert {r['seed'] for r in runs}.isdisjoint(r['seed'] for r in old['runs'])
    assert [r['id'] for r in runs] == [f'n{n}-{cell}-r{i}' for n in (64,128) for cell in 'ABCD' for i in (1,2,3)]
    for run in runs:
        e = run['expected']
        assert run['Z'] == (256*run['N']//4 if run['cell'] in 'BD' else 0)
        assert e['exported_bins_per_chain'] == (143 if run['N'] == 64 else 159)
        assert e['scalar_frames'] == 1001 and e['full_frames'] == 11
        assert e['primary_last']['origins_per_chain'] == 49
        assert e['last_exported']['origins_per_chain'] == 1
        argv = run['argv']; flags = dict(zip(argv[1::2],argv[2::2]))
        assert flags['--dynamics-stride'] == '100' and flags['--stress-mode'] == 'off'
        assert int(flags['--steps']) == (100000000 if run['N'] == 64 else 400000000)
    # Independently enumerated 37-frame support: fine16, eight level1 bins,
    # one level2 bin; partial/deepest levels contribute no extra rows.
    grid = [(i,1) for i in range(16)]+[(2*i,2) for i in range(8,16)]+[(32,4)]
    for n in (64,128):
        run = dict(N=n,replica_id=123,expected=dict(
            dynamics_frames=37,levels=5,slots=16,m=2,stride=100,dt=.0001))
        header = curve_header(n)
        assert header[11:16] == [f'bead{i}_msd' for i in (0,n//4,n//2,3*n//4,n)]
        rows = []
        for lag,block in grid:
            row = {k:0 for k in header}
            row.update(replica=123,chain='0',lag_samples=lag,lag_steps=lag*100,
                       lag_time=(lag*100)*.0001,origins_per_chain=37//block-lag//block,
                       decimation_samples=block,diffusion_phase_samples=block-1,
                       orientation_block_samples=block,orientation_block_duration=(block*100)*.0001)
            rows.append(row)
        def write(label, values, columns=header):
            path = output/f'n{n}-{label}.csv'
            with path.open('x',newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=columns)
                writer.writeheader(); writer.writerows(values)
            return path
        assert curves(write('valid',rows),run,['0']) == 25
        reject(lambda: curves(write('missing',rows[:-1]),run,['0']))
        reject(lambda: curves(write('extra',rows+[rows[-1]]),run,['0']))
        for key,value in [('origins_per_chain',2),('lag_steps',3201),('lag_samples','32.0'),
                          ('orientation_block_duration',.05),('diffusion_phase_samples',0),
                          ('c2','nan'),('chain','1')]:
            bad = [dict(row) for row in rows]
            bad[-1][key] = value
            reject(lambda: curves(write('bad-'+key,bad),run,['0']))
    for label,raw in [('overflow','{"x":1e999}'),('duplicate','{"x":1,"x":2}')]:
        path = output/(label+'.json'); path.write_text(raw)
        reject(lambda: finite_json(path))
    print('CPU infrastructure checks completed; no simulation or scientific acceptance')


if __name__ == '__main__':
    main()
