#!/usr/bin/env python3
"""Host-only report aggregation; never launches a simulation."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import validate as rouse

def precision(root):
    checks=[]
    for n in (8,32,100):
        runs=[json.loads((root/f'terminal-{p}-N{n}'/'stream_analysis.json').read_text())
              for p in ('single','double')]
        if any(not run['passed'] for run in runs): raise ValueError('terminal science gates failed')
        if runs[0]['metadata']['seed']==runs[1]['metadata']['seed']:
            raise ValueError('precision contrast requires independent seeds for independent-error SE')
        maps=[{(x['lag_samples'],x['block_samples']):x for x in run['checks'] if x['name']=='g'} for run in runs]
        if maps[0].keys()!=maps[1].keys(): raise ValueError('precision lag grids differ')
        for lag,x in maps[0].items():
            y=maps[1][lag]
            contrast=(x['value']-x['reference'])-(y['value']-y['reference'])
            item=rouse.record(f'N{n}_lag{lag[0]}_block{lag[1]}',contrast,np.hypot(x['se'],y['se']),0)
            checks.append(item)
    result=dict(checks=checks,passed=all(x['passed'] for x in checks))
    rouse.save(root/'precision_comparison.json',result)
    print('PASS' if result['passed'] else 'FAIL',len(checks),'precision contrasts;',root/'precision_comparison.json')
    return result['passed']

def performance(root):
    records=[]
    fields=('integration_ns_per_bead_step','overall_ns_per_bead_step','production_seconds',
            'measured_simulation_seconds','update_seconds','sampling_seconds','transfer_seconds',
            'cpu_correlation_seconds','buffer_wait_seconds','transfer_wait_seconds','final_output_seconds',
            'correlator_estimated_bytes','buffer_device_bytes','buffer_pinned_bytes','cuda_memory_delta_bytes')
    print('run,'+','.join(fields))
    for path in sorted(root.glob('performance-*/metadata.json')):
        meta=json.loads(path.read_text())
        records.append(dict(run=path.parent.name,**{key:meta[key] for key in fields}))
        print(path.parent.name+','+','.join(str(meta[key]) for key in fields))
    if len(records)!=9: raise ValueError('expected three modes by three batch sizes')
    rouse.save(root/'performance_comparison.json',records)
    return True

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('precision','performance'))
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    raise SystemExit(0 if globals()[args.command](args.root) else 1)
