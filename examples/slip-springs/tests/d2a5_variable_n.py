#!/usr/bin/env python3
"""Prepared, UNEXECUTED variable-N bounded verification/benchmark driver.

Explicit local execution only. No production run, restart or scientific campaign.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain
from e1_d1_pilot import atomic, file_record, require
from e1_d1_pilot_runner import run_process, tree_bytes
from e1_d2a3_run import exported_grid
from dynamical_integration_tiny import same_physics, same_json, DYNAMICS_TIMING

BASELINE_SHA = 'da303c4c2b2de94172fe0114f4f5cc2d78fd9499ef188938a15114cc3100f342'
M = 256


def load(p):
    value = json.loads(p.read_text())
    json.dumps(value, allow_nan=False)
    return value


def rows(p):
    with p.open(newline='') as f:
        reader = csv.DictReader(f)
        require(reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)), f'bad header: {p}')
        for row in reader:
            require(None not in row and all(v is not None for v in row.values()), f'bad CSV row: {p}')
            yield row


def selected(n):
    return [0, n // 4, n // 2, 3 * n // 4, n]


def names(n):
    return ['cm_msd', *[f'bead{i}_msd' for i in selected(n)], 'end_msd', 'quarter_msd',
            'end_msd_difference', 'quarter_msd_difference', 'c1', 'c2']


def validate(root, n, z, kappa, steps, stride=3, sample=4, context=None):
    context = list(range(0,steps+1,4)) if context is None else context
    main = load(root / 'metadata.json')
    for key, value in dict(precision_bits=64, springs=n, chains=M, beads_per_chain=n+1,
                           total_beads=M*(n+1), dt=.0001, steps=steps, sample=sample,
                           kbt=1, zeta=1, slip_count=z, active_angles=(n-1 if kappa else 0)).items():
        require(main[key] == value, f'physical metadata: {key}')
    require(list(map(float, (root/'parameters.txt').read_text().split())) ==
            [n] + [1,30]*n + [0] + [kappa]*(n-1) + [0], 'backbone parameter indexing')
    complete = load(root / 'equilibrium_complete.json')
    require(complete['complete'] is True and complete['frames'] == len(context), 'E1 completion')
    expected_files = {p.name for p in root.iterdir() if p.is_file()} - {'parameters.txt','equilibrium_complete.json'}
    require(set(complete['files']) == expected_files, 'physical inventory')
    for name, size in complete['files'].items():
        require(type(size) is int and (root/name).stat().st_size == size, 'physical inventory byte size')
    # Every retained joint frame: unique occupancy, stable IDs and contour links.
    snapshots = {}
    for row in rows(root/'equilibrium_attachments.csv'):
        step, j, c, b = [int(row[k]) for k in ('step','spring','chain','bead')]
        require(0 <= c < M and 0 <= b <= n, 'attachment chain/bead bounds')
        require(all(math.isfinite(float(row[k])) for k in ('ax','ay','az')), 'nonfinite anchor')
        state = snapshots.setdefault(step, {})
        require(j not in state, 'duplicate spring identity')
        state[j] = (c,b,int(row['previous']),int(row['next']))
    for state in snapshots.values():
        require(set(state) == set(range(z)) and len({(v[0],v[1]) for v in state.values()}) == z,
                'canonical count/exclusion')
        for c in range(M):
            ordered = sorted((j for j in state if state[j][0] == c), key=lambda j:state[j][1])
            for pos,j in enumerate(ordered):
                require(state[j][2:] == (ordered[pos-1] if pos else -1,
                                         ordered[pos+1] if pos+1 < len(ordered) else -1), 'contour order')
    require(not z or set(snapshots) == set(context), 'snapshot support')
    for filename in ('initial.csv','final.csv','equilibrium_positions.csv'):
        count=0;identities=set()
        for row in rows(root/filename):
            require(0 <= int(row['chain']) < M and 0 <= int(row['bead']) <= n, 'coordinate identity')
            require(all(math.isfinite(float(row[k])) for k in ('x','y','z')), 'nonfinite coordinate')
            step=int(row['step']) if filename.startswith('equilibrium') else 0
            require(not filename.startswith('equilibrium') or step in context,'coordinate step')
            identity=(step,int(row['chain']),int(row['bead']))
            require(identity not in identities,'duplicate coordinate identity');identities.add(identity)
            count += 1
        require(count == M*(n+1)*(len(context) if filename.startswith('equilibrium') else 1), 'coordinate completeness')
    dyn = root/'dynamics'
    require({p.name for p in dyn.iterdir()} == {'metadata.json','chain_correlations.csv','replica_correlations.csv'}, 'dynamic output set')
    meta = load(dyn/'metadata.json')
    for key,value in dict(complete=True,N=n,beads_per_chain=n+1,selected_beads=selected(n),chains=M,
                           precision_bits=64,frames=steps//stride+1,first_step=0,stride=stride,last_step=(steps//stride)*stride,
                           correlator_levels=4,correlator_slots=4,correlator_m=2,
                           b0=[1]*n,kb=[30]*n,kappa=[0]+[kappa]*(n-1)+[0],slip_count=z).items():
        require(meta[key] == value, f'dynamic identity: {key}')
    for key in ('dt','kbt','zeta','seed','slip_count','slip_ms2','effective_mobility_step','effective_noise'):
        require(meta[key]==main[key],f'physical/observer metadata agreement: {key}')
    require(meta['end_renewal_active']==bool(z) and meta['independent_replicas']==1 and
            meta['standard_error'] is None,'renewal/replica metadata')
    require(0 < meta['conservative_observer_estimate_bytes'] <= meta['memory_budget_bytes'] == 256*1024**2,
            'observer memory guard/estimate')
    frames=steps//stride+1
    grid=exported_grid(dict(dynamics_frames=frames,levels=4,slots=4,m=2))
    bare_reference=[]
    for filename, ids in [('chain_correlations.csv',list(map(str,range(M)))),('replica_correlations.csv',[''])]:
        data=list(rows(dyn/filename));require(len(data)==len(ids)*len(grid), 'correlation rows')
        for i,row in enumerate(data):
            lag,block=grid[i%len(grid)]
            require(row['chain']==ids[i//len(grid)] and int(row['replica'])==9077, 'immutable correlation identity')
            require(all(math.isfinite(float(v)) for k,v in row.items() if k!='chain'), 'nonfinite correlation')
            require(list(row)[10:]==names(n), 'actual monomer labels')
            for k,v in dict(lag_samples=lag,lag_steps=lag*stride,origins_per_chain=frames//block-lag//block,
                            decimation_samples=block,diffusion_phase_samples=block-1,orientation_block_samples=block).items():
                require(int(row[k])==v, f'lag/count support: {k}')
            require(float(row['lag_time'])==(lag*stride)*.0001 and
                    float(row['orientation_block_duration'])==(block*stride)*.0001, 'physical lag support')
            if not z and filename=='replica_correlations.csv' and lag:
                reference=6*float(row['lag_time'])/(n+1)
                bare_reference.append(dict(lag_time=float(row['lag_time']),reference=reference,
                                           ratio=float(row['cm_msd'])/reference))
    if not z:
        atomic(root.parent/'bare-com-reference.json',dict(
            description='Descriptive only: tiny trajectories cannot test a diffusion law; no acceptance threshold.',
            N=n,bins=bare_reference))
    return main,meta


def force_check(root,n,z,kappa):
    require(load(root/'metadata.json')['precision_bits']==64, 'double force fixture required')
    data=list(rows(root/'initial.csv'))
    r=np.array([[float(row[k]) for k in ('x','y','z')] for row in data]).reshape(M,n+1,3)
    expected=np.empty_like(r);energies=np.empty(M)
    model=Chain.homogeneous(n,b0=1,kb=30,kappa=kappa)
    for c in range(M):energies[c],expected[c]=model.energy_forces(r[c])
    if z:
        anchors=list(rows(root/'fixed_slip_springs.csv'));require(len(anchors)==z, 'force occupancy count')
        seen=set()
        for row in anchors:
            c,b=int(row['chain']),int(row['bead']);require((c,b) not in seen, 'force site overlap');seen.add((c,b))
            delta=r[c,b]-np.array([float(row[k]) for k in ('ax','ay','az')])
            expected[c,b]-=.6*delta;energies[c]+=.3*np.dot(delta,delta)
    force=list(rows(root/'forces.csv'))
    require(len(force)==M*(n+1), 'force dimensions')
    actual=np.array([[float(row[k]) for k in ('fx','fy','fz')] for row in force]).reshape(M,n+1,3)
    energy=np.array([float(row['energy']) for row in force]).reshape(M,n+1).sum(axis=1)
    # Same double-precision force tolerances as the existing bounded backbone suite.
    np.testing.assert_allclose(actual,expected,rtol=2e-12,atol=3e-14*max(30,kappa,1))
    np.testing.assert_allclose(energy,energies,rtol=3e-14,atol=3e-14)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run-reviewed-bounded',action='store_true')
    mode.add_argument('--run-reviewed-benchmark',action='store_true')
    p.add_argument('--binary',type=Path,required=True)
    p.add_argument('--baseline-binary',type=Path)
    p.add_argument('--correctness-summary',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();binary=a.binary.resolve(strict=True);binary_record=file_record(binary)
    if a.run_reviewed_bounded:
        require(a.baseline_binary is not None,'accepted N32 baseline required')
        baseline=a.baseline_binary.resolve(strict=True)
        require(file_record(baseline)['sha256']==BASELINE_SHA and baseline!=binary,'baseline identity')
    else:
        require(a.correctness_summary is not None,'completed correctness summary required before benchmark')
        check=load(a.correctness_summary)
        require(check['status']=='bounded_checks_completed' and check['binary']==binary_record,'correctness/binary mismatch')
    root=a.output.resolve();require(not root.is_relative_to(Path(__file__).resolve().parents[3]),'outputs outside repository')
    require(not root.is_relative_to(Path('/tmp')) and not root.is_relative_to(Path('/var/tmp')),'permanent output required')
    root.parent.mkdir(parents=True,exist_ok=True);root.mkdir(exist_ok=False)
    start=time.monotonic();records=[]
    limits=dict(per_run_seconds=120,aggregate_seconds=600,max_host_rss_bytes=2*1024**3,
                per_run_output_bytes=128*1024**2,aggregate_output_bytes=2*1024**3,min_free_disk_bytes=10*1024**3)
    def run(exe,label,n,z,kappa,steps=24,dynamics=True,force=False):
        expected=binary_record if exe==binary else dict(sha256=BASELINE_SHA)
        actual=file_record(exe)
        require(all(actual[key]==value for key,value in expected.items()),'executable changed before fixture')
        directory=root/label;directory.mkdir()
        context=list(range(0,steps+1,4)) if not a.run_reviewed_benchmark else [0,steps]
        full=directory/'full.steps';full.write_text('\n'.join(map(str,context))+'\n')
        stride,sample=(100,5000) if a.run_reviewed_benchmark else (3,4)
        command=[str(exe),'--springs',str(n),'--chains',str(M),'--steps',str(steps),'--dt','.0001',
                 '--sample',str(sample),'--seed','73350501','--kappa',str(kappa),'--kb','30','--b0','1','--kbt','1',
                 '--zeta','1','--slip-count',str(z),'--slip-ms2','5','--hop-rate','100','--end-renewal',str(int(z>0)),
                 '--stress-mode','off','--output',str(directory/'output')]
        if force:
            source=directory/'positions.txt'
            with source.open('w') as f:
                for c in range(M):
                    for b in range(n+1):f.write(f'{1.05*b+10*c:.17g} {.2*math.sin(.1*b):.17g} {.1*math.cos(.17*b):.17g}\n')
            command+=['--force-input',str(source)]
        else:
            command+=['--equilibrium-steps',str(full),'--equilibrium-snapshots',str(full),'--dynamics',str(int(dynamics))]
            if dynamics:command+=['--dynamics-stride',str(stride),'--dynamics-levels','4','--dynamics-slots','4','--dynamics-m','2',
                                   '--dynamics-mib','256','--dynamics-replica','9077']
        atomic(directory/'command.json',{'argv':command})
        result=run_process(command,directory,None,limits,root,start)
        require(file_record(exe)==actual,'executable changed during fixture')
        records.append(dict(label=label,N=n,Z=z,kappa=kappa,steps=steps,process=result))
        require(result['status']=='exited' and result['exit_code']==0,f'fixture failed: {label}')
        return directory/'output'
    try:
        for n in (32,64,128):
            for kappa in (0,10):
                for z in (0,M*n//4):
                    label=f'n{n}-k{kappa}-z{z}'
                    if a.run_reviewed_benchmark:
                        for count in (100,1000):
                            output=run(binary,label+f'-s{count}',n,z,kappa,count)
                            physical,observer=validate(output,n,z,kappa,count,100,5000,[0,count])
                            records[-1]['physical_metadata']=physical
                            records[-1]['observer_metadata']=observer
                        continue
                    off=run(binary,label+'-off',n,z,kappa,dynamics=False)
                    on=run(binary,label+'-on',n,z,kappa)
                    replay=run(binary,label+'-replay',n,z,kappa)
                    same_physics(off,on);same_physics(on,replay)
                    validate(on,n,z,kappa,24);validate(replay,n,z,kappa,24)
                    for name in ('chain_correlations.csv','replica_correlations.csv'):
                        require((on/'dynamics'/name).read_bytes()==(replay/'dynamics'/name).read_bytes(),'deterministic curve replay')
                    same_json(on/'dynamics/metadata.json',replay/'dynamics/metadata.json',DYNAMICS_TIMING)
                    if n==32:
                        old_off=run(baseline,label+'-baseline-off',n,z,kappa,dynamics=False)
                        old_on=run(baseline,label+'-baseline-on',n,z,kappa)
                        same_physics(old_off,off);same_physics(old_on,on)
                        for name in ('chain_correlations.csv','replica_correlations.csv'):
                            require((old_on/'dynamics'/name).read_bytes()==(on/'dynamics'/name).read_bytes(),'N32 matched curve bytes')
                        old_meta,new_meta=load(old_on/'dynamics/metadata.json'),load(on/'dynamics/metadata.json')
                        require(0<old_meta['conservative_observer_estimate_bytes']<=old_meta['memory_budget_bytes'],
                                'baseline observer allocation estimate')
                        # Only this implementation memory estimate can change; validate its budget separately above.
                        same_json(old_on/'dynamics/metadata.json',on/'dynamics/metadata.json',
                                  DYNAMICS_TIMING|{'conservative_observer_estimate_bytes'})
                        atomic(root/(label+'-allocation-comparison.json'),{'old':old_meta['conservative_observer_estimate_bytes'],
                                                                       'new':new_meta['conservative_observer_estimate_bytes']})
                    frozen=run(binary,label+'-forces',n,z,kappa,0,False,True)
                    force_check(frozen,n,z,kappa)
        status='bounded_checks_completed' if a.run_reviewed_bounded else 'bounded_benchmark_completed'
        atomic(root/'summary.json',dict(status=status,binary=binary_record,records=records,wall_seconds=time.monotonic()-start,
                                       scope='technical bounded checks or measured small-case timers; not production/scientific acceptance'))
        require(tree_bytes(root)<=limits['aggregate_output_bytes'],'final output cap')
    except BaseException as error:
        atomic(root/'FAILED.json',{'error':str(error),'records':records});raise


if __name__=='__main__':main()
