#!/usr/bin/env python3
"""Frozen Phase B specification; never grants execution approval."""
import argparse
import hashlib
from pathlib import Path

import e1_d1_pilot as old
import e1_d12_plan as design
import e1_d13_phase_a as phase_a
from e1_d1_pilot import (require, Invalid, load, digest, file_record, atomic, capture,
                        encoded, identity, output_path, utc, source_identity, validate_limits)

PROJECT=old.PROJECT
CONFIG=PROJECT/'e1_d14_phase_b_config'
ACCEPTED_SHA=old.ACCEPTED_SHA
REPOSITORY_ID=old.REPOSITORY_ID
GPU_UUID=phase_a.GPU_UUID
DESIGN_SHA=phase_a.DESIGN_SHA
TOOLS=('e1_d14_phase_b.py','e1_d14_phase_b_runner.py','e1_d14_phase_b_auth.py','e1_d14_phase_b_analysis.py')
ANALYSIS_POLICY={'replicas_per_cell':2,'primary_unit':'entire independently seeded 64-chain replica',
 'pointwise_interval':'Student t1, exploratory only; no simultaneous or equivalence decision',
 'early_window':['0','1'],'late_window':['9','10'],'backbone_spacing':'0.1','e1_spacing':'0.5',
 'event_windows':'sum exact counters between shared boundaries; separate uniform .5 bins for ACF/windows',
 'acf_max_lags':20,'acf_max_fraction':4,'tau_int':None,'scientific_acceptance':None}


def tool_hashes():
    names=set(TOOLS)|set(phase_a.tool_hashes())|{'e1_d1_pilot_analysis.py','semiflexible_reference.py'}
    return {name:digest(PROJECT/name) for name in sorted(names)}


def parent():
    design.check(design.CONFIG,DESIGN_SHA)
    return load(design.CONFIG/'phase-B/proposal.json')


def schedule(dt):
    proposal=parent();result=proposal['schedule_by_dt'][dt]
    for kind,key in (('scalar','scalar_steps'),('full','full_steps'),('snapshots','snapshot_steps')):
        path=design.CONFIG/'phase-B'/f'dt{dt}.{kind}.steps'
        require(path.read_bytes()==old.schedule_text(result[key]),'parent schedule bytes differ')
    require(tuple(map(len,(result['scalar_steps'],result['full_steps'],result['snapshot_steps'])))==(101,26,4),
            'Phase B requires 101 scalar,26 E1,4 snapshot frames')
    return result


def row_counts(run,observation_steps=None,snapshot_steps=None):
    if observation_steps is None or snapshot_steps is None:
        selected=schedule(run['dt'])
        if observation_steps is None:observation_steps=selected['full_steps']
        if snapshot_steps is None:snapshot_steps=selected['snapshot_steps']
    return old.row_counts(run,observation_steps,snapshot_steps)


def command(run,binary,output,config):
    require(run['profile']=='sparse','Phase B only supports the accepted sparse observer')
    return old.command(run,binary,output,config)


state_estimate=old.state_estimate


def estimates(manifest):
    return {'processes':8,'independent_replicas':8,'cells':4,'replica_bd_steps':sum(r['steps'] for r in manifest['runs']),
        'expected_attempts':4096000,'production_seconds_proxy_stiff_fine':12.08062808,
        'production_seconds_proxy_stiff_coarse':6.5511068,'runtime_seconds':None,
        'note':'Phase A 40x work proxies, not measurements or runtime limits; N32 flexible unbenchmarked',
        'storage':parent()['aggregate'],'state_by_run':{r['id']:state_estimate(r) for r in manifest['runs']}}


def proposed_manifest():
    proposal=parent();runs=proposal['runs_proposed_for_review'];schedules={}
    for dt in old.TIMESTEPS:
        s=schedule(dt)
        for kind,key in (('scalar','scalar_steps'),('full','full_steps'),('snapshots','snapshot_steps')):
            name=f'dt{dt}.{kind}.steps';values=s[key]
            schedules[name]={'steps':values,'sha256':hashlib.sha256(old.schedule_text(values)).hexdigest()}
    return {'version':1,'schema':'e1-d14-phase-b-execution-v1','campaign':'e1-stage-d14-phase-b-v1',
        'purpose':'exploratory exact-start equilibrium drift; no confirmatory equivalence or mixing claim',
        'repository':REPOSITORY_ID,'accepted_source_sha':ACCEPTED_SHA,'accepted_sources':old.source_hashes(),
        'preparation_sources':tool_hashes(),'parent_design_sha256':DESIGN_SHA,
        'parent_phase_b_sha256':digest(design.CONFIG/'phase-B/proposal.json'),
        'phase_a_results_sha256':digest(PROJECT/'E1_STAGE_D13_PHASE_A_RESULTS.md'),
        'phase_a_execution_references_sha256':digest(PROJECT/'e1_d13_phase_a_execution_references.json'),
        'common':dict(proposal['common'],T='10',precision_bits=64),'pairing':[],
        'pairing_policy':'No shared initial states, seeds or RNG states across replicas/cells; time changes within replica only',
        'runs':runs,'schedules':schedules,'analysis_policy':ANALYSIS_POLICY,
        'argument_templates':{r['id']:command(r,'{binary}','{output}','{config}') for r in runs},
        'expected_schemas':{'legacy_timer':1,'hopping':2,'observer':1,
            'row_counts':{r['id']:row_counts(r,schedules[r['schedule']]['steps'],schedules[r['snapshots']]['steps']) for r in runs}},
        'required_authentication':['manifest_sha256','build_receipt_sha256','environment_sha256','approval_sha256',
            'completion_sha256','source','toolchain','executable_sha256','gpu_uuid','raw_file_sizes_sha256','complete_eight_replica_cohort'],
        'target_gpu':{'uuid':GPU_UUID,'name':'NVIDIA GeForce RTX 3060 Ti','compute_capability':'8.6','architecture':'sm_86','cuda_major':13},
        'execution_authorized':False,'approved_limits':{k:None for k in design.BUDGETS}}


def validate_manifest(path,expected_hash):
    require(isinstance(expected_hash,str) and len(expected_hash)==64,'external Phase B manifest SHA256 required')
    require(digest(path)==expected_hash,'Phase B manifest SHA256 mismatch')
    value=load(path)
    require(encoded(value)==encoded(proposed_manifest()),'not the frozen Phase B matrix/source/analysis/schedules')
    require(len(value['runs'])==8 and len({r['seed'] for r in value['runs']})==8,'eight independent Phase B seeds required')
    for c in range(1,5):require([r['replica'] for r in value['runs'] if r['cell']==c]==[1,2],'two replicas/cell required')
    for name,record in value['schedules'].items():
        require(file_record(Path(path).parent/name)=={'bytes':len(old.schedule_text(record['steps'])),'sha256':record['sha256']},'Phase B schedule changed')
    return value


def freeze(destination):
    destination=output_path(destination);value=proposed_manifest();destination.mkdir(parents=True,exist_ok=False)
    (destination/'manifest.json').write_bytes(encoded(value))
    for name,record in value['schedules'].items():(destination/name).write_bytes(old.schedule_text(record['steps']))
    sha=digest(destination/'manifest.json');(destination/'manifest.sha256').write_text(sha+'  manifest.json\n')
    template=load(phase_a.CONFIG/'approval.template.json')
    template['manifest_sha256']=sha
    require(template['execution_authorized'] is False and all(v is None for v in template['limits'].values()),'unapproved template required')
    (destination/'approval.template.json').write_bytes(encoded(template));return sha


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--freeze',type=Path,required=True)
    args=parser.parse_args();print(freeze(args.freeze))
