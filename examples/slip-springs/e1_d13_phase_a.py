#!/usr/bin/env python3
"""Frozen Phase A execution specification. Preparation never authorizes execution."""
import argparse
import hashlib
from pathlib import Path
import sys

import e1_d1_pilot as old
import e1_d12_plan as design
from e1_d1_pilot import (require, Invalid, load, digest, file_record, atomic, capture,
                        encoded, identity, output_path, utc, source_identity, validate_limits)

PROJECT=old.PROJECT
CONFIG=PROJECT/'e1_d13_phase_a_config'
ACCEPTED_SHA=old.ACCEPTED_SHA
REPOSITORY_ID=old.REPOSITORY_ID
GPU_UUID='GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274'
DESIGN_SHA='2da957a5ee44956c395004bd20c23bee8e809b6d312ceee814e3f6934b2a5bbe'
TOOLS=('e1_d13_phase_a.py','e1_d13_phase_a_auth.py','e1_d13_phase_a_runner.py',
       'e1_d13_phase_a_analysis.py','e1_d13_reuse.py')
TIMING_FIELDS=('initialization_seconds','integration_seconds','production_wall_seconds',
    'observation_seconds','recurrent_output_seconds','final_output_seconds',
    'force_and_diagnostic_wall_seconds','integration_ns_per_bead_step',
    'overall_ns_per_bead_step','bead_updates_per_second')


def tool_hashes():
    names=TOOLS+old.TOOL_FILES+('e1_d12_plan.py','e1_d12_schema_calibration.json','e1_observer_check.py')
    return {name:digest(PROJECT/name) for name in names}


def command(run,binary,output,config):
    argv=old.command(run,binary,output,config)
    require(run['profile'] in ('off','sparse'),'unsupported profile')
    return argv[:argv.index('--equilibrium-steps')] if run['profile']=='off' else argv


def row_counts(run,observation_steps=None,snapshot_steps=None):
    s=design.schedules('0.25',run['dt'])
    observations=s['full_steps'] if observation_steps is None else observation_steps
    snapshots=s['snapshot_steps'] if snapshot_steps is None else snapshot_steps
    if run['profile']=='off':observations=[];snapshots=[]
    counts=old.row_counts(run,observations,snapshots)
    return {name:count for name,count in counts.items() if run['profile']=='sparse' or not name.startswith('equilibrium_')}


def state_estimate(run):
    value=old.state_estimate(run)
    if run['profile']=='off':value['observer_vector_bytes']=0
    return value


def estimates(manifest):
    return {'processes':8,'physical_initializations':4,'replica_bd_steps':sum(r['steps'] for r in manifest['runs']),
            'expected_attempts':51520,'runtime_seconds':None,'storage':design.phase_plan('A')['aggregate'],
            'state_by_run':{r['id']:state_estimate(r) for r in manifest['runs']}}


def proposed_manifest():
    design.check(design.CONFIG,DESIGN_SHA)
    proposal=load(design.CONFIG/'phase-A/proposal.json')
    runs=proposal['runs_proposed_for_review']
    schedules={}
    for dt,s in proposal['schedule_by_dt'].items():
        for kind,key in (('scalar','scalar_steps'),('full','full_steps'),('snapshots','snapshot_steps')):
            name=f'dt{dt}.{kind}.steps';values=s[key]
            schedules[name]={'steps':values,'sha256':hashlib.sha256(old.schedule_text(values)).hexdigest()}
    return {'version':1,'schema':'e1-d13-phase-a-execution-v1','campaign':'e1-stage-d13-phase-a-v1',
        'purpose':'performance/output feasibility benchmark only; no equilibrium acceptance',
        'repository':REPOSITORY_ID,'accepted_source_sha':ACCEPTED_SHA,'accepted_sources':old.source_hashes(),
        'preparation_sources':tool_hashes(),'parent_design_sha256':DESIGN_SHA,
        'parent_phase_a_sha256':digest(design.CONFIG/'phase-A/proposal.json'),
        'common':dict(proposal['common'],T='0.25',precision_bits=64),
        'pairing':[{'cell':c,'seed':next(r['seed'] for r in runs if r['cell']==c),
                    'off':next(r['id'] for r in runs if r['cell']==c and r['profile']=='off'),
                    'on':next(r['id'] for r in runs if r['cell']==c and r['profile']=='sparse')} for c in range(1,5)],
        'runs':runs,'schedules':schedules,
        'argument_templates':{r['id']:command(r,'{binary}','{output}','{config}') for r in runs},
        'expected_schemas':{'legacy_timer':1,'hopping':2,'observer':1,
            'row_counts':{r['id']:row_counts(r) for r in runs},
            'off_optional_equilibrium_files':False,'on_final_observation_required':True},
        'required_authentication':['manifest_sha256','build_receipt_sha256','environment_sha256',
            'approval_sha256','completion_sha256','source','toolchain','executable_sha256','gpu_uuid',
            'raw_file_sizes_sha256','complete_eight_process_cohort','paired_byte_identity'],
        'target_gpu':{'uuid':GPU_UUID,'name':'NVIDIA GeForce RTX 3060 Ti','compute_capability':'8.6','architecture':'sm_86','cuda_major':13},
        'execution_authorized':False,'approved_limits':{k:None for k in design.BUDGETS}}


def validate_manifest(path,expected_hash):
    require(isinstance(expected_hash,str) and len(expected_hash)==64,'trusted manifest SHA256 required')
    require(digest(path)==expected_hash,'manifest SHA256 mismatch')
    value=load(path)
    require(encoded(value)==encoded(proposed_manifest()),'not the frozen Phase A matrix/source/tools')
    require(len(value['runs'])==8 and len({r['seed'] for r in value['runs']})==4,'exactly eight processes/four initializations required')
    for name,record in value['schedules'].items():
        require(file_record(Path(path).parent/name)=={'bytes':len(old.schedule_text(record['steps'])),'sha256':record['sha256']},'schedule changed')
    return value


def freeze(destination):
    destination=output_path(destination);value=proposed_manifest()
    destination.mkdir(parents=True,exist_ok=False)
    (destination/'manifest.json').write_bytes(encoded(value))
    for name,record in value['schedules'].items():(destination/name).write_bytes(old.schedule_text(record['steps']))
    sha=digest(destination/'manifest.json');(destination/'manifest.sha256').write_text(sha+'  manifest.json\n')
    approval={'version':1,'execution_authorized':False,'approval_reference':None,'manifest_sha256':sha,
        'build_receipt_sha256':None,'environment_sha256':None,'output_root':None,'gpu_uuid':None,
        'limits':{k:None for k in design.BUDGETS}}
    (destination/'approval.template.json').write_bytes(encoded(approval))
    return sha


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',type=Path,required=True)
    args=parser.parse_args();print(freeze(args.freeze))
