#!/usr/bin/env python3
"""D1.5 immutable proposals and resource projections; never grants approval."""
import argparse
from fractions import Fraction
import hashlib
import math
from pathlib import Path

import e1_d1_pilot as old
import e1_d14_phase_b as phase_b
from e1_d1_pilot import (require, Invalid, load, digest, file_record, encoded,
    identity, output_path, utc, source_identity, validate_limits, capture)

PROJECT=old.PROJECT
CONFIG=PROJECT/'e1_d15_config'
ACCEPTED_SHA=old.ACCEPTED_SHA
REPOSITORY_ID=old.REPOSITORY_ID
START='7a889b060132a6d248a88128009fc9f595ef2b88'
GPU_UUID=phase_b.GPU_UUID
KINDS={'benchmark':('0.1',1,1),'pilot':('1',1,2),'exploratory':('100',4,3)}
TOOLS=('e1_d15_prepare.py','e1_d15_auth.py','e1_d15_host.py','tests/test_e1_d15_preparation.py',
       'e1_d15_observed_rows.json')


def tool_hashes():
    return dict(phase_b.tool_hashes(),**{name:digest(PROJECT/name) for name in TOOLS})


def schedule(horizon,dt):
    end=old.exact_step(horizon,dt)
    scalar=old.exact_step(min(Fraction(horizon),Fraction('0.5')),dt)
    full=sorted({0,1,end}|{old.exact_step(t,dt) for t in ('0.0005','0.0025','0.01','0.05')}|
                set(range(0,end+1,old.exact_step('2',dt))))
    snapshots=[0,1,old.exact_step('0.01',dt),end]
    require(len(set(snapshots))==4 and set(snapshots)<=set(full),'four complete-state audits required')
    return {'scalar_steps':list(range(0,end+1,scalar)),'full_steps':full,
            'snapshot_steps':snapshots,'legacy_stride':scalar}


def runs(kind,chains=256):
    horizon,reps,phase=KINDS[kind]
    result=[]
    for cell,(kappa,dt) in enumerate(((k,d) for k in (0,10) for d in old.TIMESTEPS),1):
        selected=schedule(horizon,dt)
        for replica in range(1,reps+1):
            result.append(dict(id=f'D15-{kind}-c{cell}-r{replica}',cell=cell,replica=replica,
                profile='sparse',N=32,M=chains,Ne=4,Z=8*chains,kappa=kappa,nu_hop=100,
                rho='8/33',dt=dt,T=horizon,steps=old.exact_step(horizon,dt),
                sample=selected['legacy_stride'],seed=721500000+10000*phase+100*cell+replica,
                schedule=f'dt{dt}.full.steps',snapshots=f'dt{dt}.snapshots.steps'))
    return result


def row_counts(run,observation_steps=None,snapshot_steps=None):
    selected=schedule(run['T'],run['dt'])
    return old.row_counts(run,selected['full_steps'] if observation_steps is None else observation_steps,
                          selected['snapshot_steps'] if snapshot_steps is None else snapshot_steps)


command=old.command
state_estimate=old.state_estimate


def storage(run):
    """Observed CSV serialization and a separate conservative width envelope."""
    calibration=load(PROJECT/'e1_d15_observed_rows.json')['files']
    counts=row_counts(run);result={}
    integer={'step','previous_step','chain','bead','bond','spring','previous','next','frames','z'}
    counters={'batches','attempts','accepted','boundary','occupied','metropolis','renewal_proposed',
              'renewal_accepted','renewal_occupied','renewal_same_chain','renewal_cross_chain'}
    for name,count in counts.items():
        observed=calibration[name];header=observed['header']
        widths=[]
        for field in header:
            coordinate_z=field=='z' and name in ('initial.csv','final.csv','equilibrium_positions.csv')
            is_integer=(field in integer and not coordinate_z) or field in counters or field.startswith('bin')
            widths.append(20 if is_integer else 24)
        header_bytes=len(','.join(header).encode())+1
        result[name]={'rows':count,'observed_mean_row_bytes':observed['data_bytes']/observed['data_rows'],
            'empirical_bytes':math.ceil(count*observed['data_bytes']/observed['data_rows'])+header_bytes,
            'width_envelope_bytes':count*(sum(widths)+len(header))+header_bytes}
    return {'files':result,'empirical_csv_bytes':sum(v['empirical_bytes'] for v in result.values()),
            'wide_csv_bytes':sum(v['width_envelope_bytes'] for v in result.values()),
            'json_logs_receipts_allowance_bytes':2*1024**2,
            'classification':'projection, not a measurement or approved quota; no compression assumed'}


def estimates(manifest):
    selected=manifest['runs']
    return {'processes':len(selected),'bd_steps':sum(r['steps'] for r in selected),
        'bead_updates':sum(r['steps']*33*r['M'] for r in selected),
        'expected_attempts':sum(int(r['Z']*r['nu_hop']*Fraction(r['T'])) for r in selected),
        'storage_by_run':{r['id']:storage(r) for r in selected},
        'state_by_run':{r['id']:state_estimate(r) for r in selected},'runtime_seconds':None}


def proposed_manifest(kind):
    require(kind in KINDS,'unknown D1.5 proposal')
    horizon,reps,_=KINDS[kind];selected=runs(kind);schedules={}
    for dt in old.TIMESTEPS:
        item=schedule(horizon,dt)
        for name,key in (('scalar','scalar_steps'),('full','full_steps'),('snapshots','snapshot_steps')):
            steps=item[key];body=old.schedule_text(steps)
            schedules[f'dt{dt}.{name}.steps']={'steps':steps,'sha256':hashlib.sha256(body).hexdigest()}
    return {'version':1,'schema':'e1-d15-preparation-v1','kind':kind,'campaign':f'e1-d15-{kind}-v1',
        'starting_preparation_sha':START,'repository':REPOSITORY_ID,
        'accepted_source_sha':ACCEPTED_SHA,'accepted_sources':old.source_hashes(),
        'preparation_sources':tool_hashes(),'parent_phase_b_manifest_sha256':digest(phase_b.CONFIG/'manifest.json'),
        'phase_a_execution_references_sha256':digest(PROJECT/'e1_d13_phase_a_execution_references.json'),
        'execution_authorized':False,'execution_supported':kind!='exploratory',
        'required_prior_review':'authenticated benchmark completion and independent resource/science review' if kind=='pilot' else
            ('new execution protocol and explicit scientific/resource authorization' if kind=='exploratory' else 'independent host readiness, preparation checks and execution authorization'),
        'approved_limits':{k:None for k in phase_b.design.BUDGETS},
        'common':dict(M=256,N=32,Ne=4,Z=2048,A2=5,b0=1,kb=30,kBT=1,zeta=1,
            nu_hop=100,end_renewal=True,stress='off',precision_bits=64,initialization='accepted exact E1'),
        'runs':selected,'pairing':[],'replicas_per_cell':reps,'schedules':schedules,
        'pairing_policy':'independent seeds across every cell, replica and phase; no retrospective pairing',
        'argument_templates':{r['id']:command(r,'{binary}','{output}','{config}') for r in selected},
        'expected_schemas':{'legacy_timer':1,'hopping':2,'observer':1,
                           'row_counts':{r['id']:row_counts(r) for r in selected}},
        'target_gpu':dict(load(phase_b.CONFIG/'manifest.json')['target_gpu']),
        'scientific_acceptance':None,'D0_tolerances_changed':False}


def validate_manifest(path,sha):
    require(isinstance(sha,str) and len(sha)==64 and digest(path)==sha,'external D1.5 manifest SHA256 missing/mismatched')
    value=load(path)
    require(encoded(value)==encoded(proposed_manifest(value['kind'])),'D1.5 frozen source/matrix/schedule changed')
    root=Path(path).parent
    require(not root.is_symlink(),'symlink configuration root')
    for name,item in value['schedules'].items():
        p=root/name
        require(not p.is_symlink() and p.read_bytes()==old.schedule_text(item['steps']),'schedule bytes changed')
    return value


def freeze(destination,kind):
    root=output_path(destination);value=proposed_manifest(kind)
    root.mkdir(parents=True,exist_ok=False)
    (root/'manifest.json').write_bytes(encoded(value))
    for name,item in value['schedules'].items():(root/name).write_bytes(old.schedule_text(item['steps']))
    sha=digest(root/'manifest.json');(root/'manifest.sha256').write_text(sha+'  manifest.json\n')
    approval=load(phase_b.CONFIG/'approval.template.json');approval['manifest_sha256']=sha
    approval.update(readiness_review=None,benchmark_review=None)
    require(approval['execution_authorized'] is False and all(v is None for v in approval['limits'].values()),'non-authorizing template required')
    (root/'approval.template.json').write_bytes(encoded(approval))
    return {'kind':kind,'manifest_sha256':sha,'execution_authorized':False}


def projections():
    measured=load(PROJECT/'e1_d15_observed_rows.json')['timing_measurements']
    result={'version':1,'kind':'preparation arithmetic, no new performance/science measurements',
        'starting_sha':START,'measured_phase_a':measured,'phase_b_campaign_measurements':None,
        'phases':{k:estimates(proposed_manifest(k)) for k in KINDS},'larger_systems':{}}
    for chains in (256,512,1024,2048):
        run=next(r for r in runs('exploratory',chains) if r['kappa']==10 and r['dt']=='0.0001')
        state=state_estimate(run);size=storage(run)
        result['larger_systems'][str(chains)]={
            'beads':33*chains,'slip_springs':8*chains,
            'force_update_grid_blocks_at_256_threads':(33*chains+255)//256,
            'poisson_mean_fine':8*chains*100*.0001,'poisson_mean_coarse':8*chains*100*.00025,
            'expected_attempts_per_T100_run':8*chains*100*100,
            'bead_updates_T100_fine':33*chains*1000000,'bead_updates_T100_coarse':33*chains*400000,
            'device_array_bytes_stiff':state['device_array_bytes'],
            'legacy_workspace_estimate_bytes':state['legacy_workspace_estimate_bytes'],
            'observer_vector_bytes':state['observer_vector_bytes'],
            'regular_and_full_position_readback_bytes_T100':32*33*chains*206,
            'full_E1_additional_readback_bytes_T100':56*(48*8*chains+36*33*chains+88),
            'diagnostic_readback_bytes_T100_fine':12*1000000,
            'diagnostic_readback_bytes_T100_coarse':12*400000,
            'T100_empirical_csv_bytes_per_run':size['empirical_csv_bytes'],
            'T100_wide_csv_bytes_per_run':size['wide_csv_bytes'],
            'T100_16_run_empirical_csv_bytes':16*size['empirical_csv_bytes'],
            'T100_16_run_wide_csv_bytes':16*size['wide_csv_bytes'],
            'unverified_proxy_seconds_T100_fine_if_all_cost_linear_in_M':measured['0.0001']['production_seconds']*400*chains/64,
            'unverified_proxy_seconds_T100_coarse_if_all_cost_linear_in_M':measured['0.00025']['production_seconds']*400*chains/64,
            'proxy_warning':'NOT measurements or runtime bounds; stiff Phase A only, different cadence; no kernel cost decomposition or throughput scaling established'}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze',type=Path);group.add_argument('--project',type=Path)
    parser.add_argument('--kind',choices=KINDS)
    args=parser.parse_args()
    if args.freeze:
        if args.kind is None:parser.error('--kind required with --freeze')
        print(encoded(freeze(args.freeze,args.kind)).decode())
    else:
        destination=output_path(args.project)
        require(destination.parent.is_dir(),'existing projection output parent required')
        with destination.open('xb') as stream:stream.write(encoded(projections()))
        print(digest(destination))
