"""Generate a frozen, unexecuted Stage 4A.3c campaign; no --run option.

Independent review and separate user authorization are required before execution.
--check-diagnostics checks saved host results; it does not establish acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain
from semiflexible_stress_reference import virials

PROJECT=Path(__file__).resolve().parents[1]
SEEDS=(433201,433202,433203)


def write_parameters(path,model):
    path.write_text(str(model.n)+'\n'+''.join(f'{b:.17g} {k:.17g}\n' for b,k in zip(model.b0,model.kb))
                    +' '.join(f'{k:.17g}' for k in model.kappa)+'\n')


def safe(path):
    path=path.resolve()
    if path.is_relative_to(PROJECT.parents[1]) and not path.is_relative_to(PROJECT):
        raise ValueError('repository output must stay in examples/slip-springs')
    return path


def generate(root,build):
    root=safe(root);root.mkdir(parents=True,exist_ok=False)
    models=[('single-bond',Chain.homogeneous(1,kappa=0),20)]
    models += [(f'finite-N{n}-k{k}',Chain.homogeneous(n,kappa=k),200 if n==8 else 4000)
               for n in (8,32) for k in (0,2,10)]
    models += [('heterogeneous',Chain([.8,1.2]*4,[20,40]*4,[0,0,2,0,10,0,2,0,0]),200),
               ('gaussian-control',Chain.homogeneous(8,b0=0,kb=3,kappa=0),100)]
    manifest=[]
    for label,model,duration in models:
        params=root/f'{label}.txt';write_parameters(params,model)
        for precision in ('single','double'):
            binary=str((build/precision/'semiflexible').resolve())
            for seed in SEEDS:
                timesteps=(.001,.0005,.00025) if label=='gaussian-control' else (.0001,.00005,.000025)
                spacing=.002 if label=='gaussian-control' else .01
                for h in timesteps:
                    output=root/f'{precision}-{label}-{seed}-{h}'
                    command=[binary,'--output',str(output),'--springs',str(model.n),'--chains','2048',
                             '--parameters',str(params),'--dt',str(h),'--steps',str(round(duration/h)),
                             '--sample',str(round(spacing/h)),'--seed',str(seed),'--stress-mode','stream',
                             '--cpu-workers','4','--stress-batch','32','--corr-levels','20','--corr-slots','32','--corr-m','2','--correlator-mib','512']
                    manifest.append(dict(phase='stream',label=label,precision=precision,seed=seed,output=str(output),command=command))
                output=root/f'{precision}-{label}-{seed}-diagnostic'
                command=[binary,'--output',str(output),'--springs',str(model.n),'--chains','2048',
                         '--parameters',str(params),'--dt',str(timesteps[-1]),'--steps','0','--seed',str(seed),'--stress-mode','diagnostic']
                manifest.append(dict(phase='diagnostic',label=label,precision=precision,seed=seed,output=str(output),command=command))
    for label,model,duration in models:
        params=root/f'{label}.txt'
        for precision in ('single','double'):
            binary=str((build/precision/'semiflexible').resolve())
            h=.001 if label=='gaussian-control' else .0001
            spacing=.002 if label=='gaussian-control' else .01
            for workers,batch in ((1,1),(2,7),(4,32)):
                output=root/f'{precision}-{label}-reference-w{workers}-b{batch}'
                command=[binary,'--output',str(output),'--springs',str(model.n),'--chains','64',
                         '--parameters',str(params),'--dt',str(h),'--steps',str(8192*round(spacing/h)),
                         '--sample',str(round(spacing/h)),'--seed',str(SEEDS[0]),'--kbt','1.7',
                         '--stress-mode','stream','--stress-dump','1','--chain-density','.25',
                         '--cpu-workers',str(workers),'--stress-batch',str(batch),'--corr-levels','20','--corr-slots','32']
                manifest.append(dict(phase='reference',label=label,precision=precision,output=str(output),command=command))
    for precision in ('single','double'):
        binary=str((build/precision/'semiflexible').resolve())
        for repeat in range(3):
            for steps in (20000,400000):
                output=root/f'{precision}-memory-r{repeat}-s{steps}'
                command=[binary,'--output',str(output),'--springs','8','--chains','2048','--parameters',str(root/'finite-N8-k10.txt'),
                         '--dt','.00005','--steps',str(steps),'--sample','200','--seed',str(SEEDS[0]),
                         '--stress-mode','stream','--cpu-workers','4','--stress-batch','32','--corr-levels','20','--corr-slots','32']
                manifest.append(dict(phase='memory',label='memory',precision=precision,output=str(output),command=command))
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for phase in ('diagnostic','stream','reference'):
        (root/f'commands_{phase}.sh').write_text('#!/bin/sh\nset -eu\n: "${STAGE4A3B_REVIEWED:?Independent review and explicit host authorization required}"\n'
                    +''.join(shlex.join(r['command'])+'\n' for r in manifest if r['phase']==phase))
    guard='#!/bin/sh\nset -eu\n: "${STAGE4A3B_REVIEWED:?Independent review and explicit host authorization required}"\n'
    memory=guard
    for run in manifest:
        if run['phase']!='memory':continue
        target=run['output']
        memory += 'nvidia-smi --query-gpu=timestamp,memory.used --format=csv > '+shlex.quote(target+'.gpu.csv')+'\n'
        memory += '(/usr/bin/time -v -o '+shlex.quote(target+'.time')+' '+shlex.join(run['command'])+' > '+shlex.quote(target+'.log')+' 2>&1) &\njob=$!\n'
        memory += 'while kill -0 "$job" 2>/dev/null; do nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader >> '+shlex.quote(target+'.gpu.csv')+'; sleep 1; done\nwait "$job"\n'
    (root/'commands_memory.sh').write_text(memory)
    (root/'commands_reference_analysis.sh').write_text(guard+''.join(shlex.join([sys.executable,str(PROJECT/'tests/test_semiflexible_stress_gpu.py'),'--compare',r['output']])+'\n' for r in manifest if r['phase']=='reference'))
    plan=PROJECT/'STAGE4A3C_VALIDATION_PLAN.md'
    (root/'validation-plan.md').write_bytes(plan.read_bytes())
    (root/'PLAN_SHA256').write_text(hashlib.sha256(plan.read_bytes()).hexdigest()+'  validation-plan.md\n')
    print(f'Generated {len(manifest)} commands (162 stream,54 diagnostic,54 direct-reference,12 memory). No experiments executed. Independent review required.')
    return manifest


def check_diagnostics(root):
    failures=[];compared=0
    for run in json.loads((root/'manifest.json').read_text()):
        if run['phase']!='diagnostic':continue
        out=Path(run['output']);p=(out/'parameters.txt').read_text().split();n=int(p[0]);bonds=np.array(p[1:1+2*n],float).reshape(n,2)
        model=Chain(bonds[:,0],bonds[:,1],np.array(p[1+2*n:],float))
        positions=np.atleast_1d(np.genfromtxt(out/'initial.csv',names=True,delimiter=','))
        r=np.column_stack([positions[k] for k in ('x','y','z')]).reshape(-1,n+1,3)
        tensors=np.atleast_1d(np.genfromtxt(out/'stress_tensors.csv',names=True,delimiter=',',dtype=None,encoding='utf-8'))
        single=run['precision']=='single';scale=max(1,model.kb.max(),model.kappa.max())
        # One reference call per configuration; preserve separate terms in checks.
        expected=[virials(model,position) for position in r]
        for term in ('stretch','bend','total'):
            rows=tensors[tensors['term']==term]
            actual=np.array([[row[f'w{a}{b}'] for a in range(3) for b in range(3)] for row in rows]).reshape(-1,3,3)
            target=np.array([result[term] for result in expected])
            tol=(2e-7 if single else 5e-13)*scale+(3e-6 if single else 3e-12)*np.abs(target)
            if np.any(~np.isfinite(actual)) or np.any(np.abs(actual-target)>tol):failures.append(run['output']+': '+term)
            if np.max(np.abs(actual-actual.transpose(0,2,1)))>1e-11*scale:failures.append(run['output']+': symmetry '+term)
            if term=='bend' and np.max(np.abs(np.trace(actual,axis1=1,axis2=2)))>3e-11*scale:failures.append(run['output']+': trace')
            compared+=len(rows)
    report=dict(compared_tensors=compared,failures=failures,status='diagnostic check only; not scientific acceptance')
    target=root/'diagnostic_analysis.json'
    if target.exists():raise FileExistsError('refusing to overwrite diagnostic analysis')
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],'failures:',len(failures))
    return bool(failures)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--build',type=Path,default=PROJECT/'build');p.add_argument('--check-diagnostics',type=Path)
    args=p.parse_args()
    if args.check_diagnostics:return check_diagnostics(safe(args.check_diagnostics))
    if args.output is None:p.error('--output or --check-diagnostics required')
    generate(args.output,args.build.resolve());return 0


if __name__=='__main__':sys.exit(main())
