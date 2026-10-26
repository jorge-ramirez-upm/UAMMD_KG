"""D1.6B-specific approval, build and output authentication; frozen tools unchanged."""
from pathlib import Path
import math

import e1_d16b_spec as spec
import e1_d13_phase_a_auth as accepted
from e1_d13_reuse import bind
from e1_d1_pilot import require, load, file_record, digest, identity

# Private instances bind schema-generic helpers to the NEW contract only.
base = bind('auth',spec)
_raw_output, _build = base.validate_output, base.validate_build
COUNTERS = base.COUNTERS


def validate_output(root,run,observations,snapshots,gpu):
    result=_raw_output(root,run,observations,snapshots,gpu)
    accepted.timers(result['metadata'],load(Path(root)/'equilibrium_complete.json'))
    accepted.counters(load(Path(root)/'hopping_metadata.json'),run)
    return result


def validate_build(path,sha,manifest,live=False):
    value=_build(path,sha,manifest,live)
    require(value['architecture']=='sm_86' and 'release 13.' in value['nvcc']['version'], 'CUDA13/sm86 build required')
    require(value['source']['origin'] in ('git@github.com:jorge-ramirez-upm/UAMMD_KG.git',
             'https://github.com/jorge-ramirez-upm/UAMMD_KG.git'), 'incorrect origin')
    spec.durable(value['source']['path']);spec.durable(value['build_root'])
    return value


base.validate_output=validate_output
base.validate_build=validate_build


def validate_environment(value,build,uuid):
    expected=load(spec.CONFIG/'manifest.json')['target_gpu']
    require(value['gpu']['uuid']==uuid==spec.GPU_UUID and value['gpu']['name']==expected['name']
            and value['gpu']['compute_capability']=='8.6', 'unreviewed GPU')
    require(value['runtime_version']//1000==13 and value['driver_api_version']>=13000
            and value['runtime_library']==build['runtime_library']['file'], 'CUDA runtime mismatch')
    expected_env=accepted.expected_environment(build['cuda_home'],uuid)
    scratch=value['environment'].get('TMPDIR')
    require(isinstance(scratch,str) and Path(scratch).is_dir(), 'durable scratch required')
    expected_env['TMPDIR']=str(spec.durable(scratch))
    require(value['environment']==expected_env, 'execution environment mismatch')


def approval_template(root):
    root=spec.durable(root)
    return {'schema':'e1-d16b-exploratory-approval-v1','version':1,
        'execution_authorized':False,'approval_reference':None,'independent_readiness_reviewed':False,
        'manifest_sha256':digest(spec.CONFIG/'manifest.json'),
        'build_receipt_sha256':digest(root/'build/build.json'),
        'environment_sha256':identity(load(root/'preflight.json')['environment']),
        'output_root':str(root/'campaign'),'gpu_uuid':spec.GPU_UUID,
        'limits':load(spec.CONFIG/'resources.json')['limits'],
        'resource_amendment':file_record(spec.CONFIG/'resources.json'),
        'readiness':file_record(root/'readiness.json'),'session':file_record(root/'session.json'),
        'references':file_record(root/'references.json'),'performance':file_record(root/'performance.json'),
        'reference_lock':file_record(spec.CONFIG/'reference-lock.json'),
        'schedule_identity':identity(load(spec.CONFIG/'manifest.json')['schedules']),
        'analysis_identity':identity(load(spec.CONFIG/'manifest.json')['analysis'])}


def validate_approval(value,root,sha):
    root=spec.durable(root)
    template=load(root/'approval-template.json')
    require(template==approval_template(root), 'readiness/template changed')
    expected=dict(template,execution_authorized=True, independent_readiness_reviewed=True,
                  approval_reference=value.get('approval_reference'))
    require(type(value.get('execution_authorized')) is bool
            and type(value.get('independent_readiness_reviewed')) is bool,'approval flags must be booleans')
    require(value==expected and isinstance(value['approval_reference'],str) and value['approval_reference'].strip(),
            'new independent D1.6B approval required; prior approvals rejected')
    require(load(root/'readiness.json')['status']=='READY_FOR_INDEPENDENT_REVIEW', 'readiness failed')
    require(identity(value)==sha, 'trusted approval identity mismatch')
    for name,proof in load(root/'readiness.json')['artifacts'].items():
        require(file_record(name)==proof, 'readiness artifact changed: '+name)
    return spec.validate_limits(value['limits'])


def authenticate_campaign(root,manifest_path,manifest_sha,approval_sha,completion_sha):
    root=spec.durable(root)
    approval=load(root/'approval.json')
    require(digest(root/'approval.json')==approval_sha,'approval file changed')
    validate_approval(approval,root.parent,approval_sha)
    local_result=load(root.parent/'execution-result.json')
    require(local_result['status']=='completed' and local_result['completion_sha256']==completion_sha
            and 0<local_result['local_campaign_wall_seconds']<=14400,'local aggregate wall/completion failure')
    manifest,items=base.authenticate_campaign(root,manifest_path,manifest_sha,approval_sha,completion_sha)
    build=validate_build(root/'build.json',approval['build_receipt_sha256'],manifest)
    validate_environment(load(root/'campaign.json')['environment'],build,approval['gpu_uuid'])
    require(len(items)==16 and [i['run'] for i in items]==spec.runs(), 'complete independent 16-run cohort required')
    for item in items:
        receipt=item['receipt']
        require(0<receipt['run_stage_wall_seconds']<=600, 'child plus output-authentication wall budget exceeded')
        for name,record in receipt['output_authentication'].items():
            require((root/name).resolve().is_relative_to(root) and file_record(root/name)==record,
                    'bounded output authentication evidence changed')
        check=root/'authentication'/item['run']['id']
        require(sum(p.stat().st_size for p in check.rglob('*') if p.is_file())+
                sum(p.stat().st_size for p in item['root'].parent.rglob('*') if p.is_file())
                <=approval['limits']['per_run_output_bytes'], 'combined run/authentication output cap exceeded')
    return manifest,items
