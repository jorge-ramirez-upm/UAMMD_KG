"""Independent Phase B receipt/raw/cohort authentication; no Phase A pairing."""
import math
from pathlib import Path
import e1_d14_phase_b as spec
import e1_d13_phase_a_auth as accepted
from e1_d13_reuse import bind
from e1_d1_pilot import require, load

base=bind('auth',spec)
_output=base.validate_output
_build=base.validate_build
COUNTERS=base.COUNTERS
validate_environment=accepted.validate_environment


def validate_output(root,run,observation_steps,snapshots,gpu_name):
    require(run['profile']=='sparse','Phase B requires sparse equilibrium observer')
    result=_output(root,run,observation_steps,snapshots,gpu_name)
    accepted.timers(result['metadata'],load(Path(root)/'equilibrium_complete.json'))
    accepted.counters(load(Path(root)/'hopping_metadata.json'),run)
    return result


def validate_build(path,sha,manifest,live=False):
    result=_build(path,sha,manifest,live)
    require(result['architecture']=='sm_86' and 'release 13.' in result['nvcc']['version'],'Phase B CUDA13/sm86 required')
    require(result['source']['origin'] in ('git@github.com:jorge-ramirez-upm/UAMMD_KG.git',
        'https://github.com/jorge-ramirez-upm/UAMMD_KG.git'),'incorrect build repository')
    return result


base.validate_output=validate_output
base.validate_build=validate_build


def authenticate_campaign(root,manifest_path,manifest_sha,approval_sha,completion_sha):
    root=Path(root)
    manifest,items=base.authenticate_campaign(root,manifest_path,manifest_sha,approval_sha,completion_sha)
    approval=load(root/'approval.json');ledger=load(root/'campaign.json')
    build=validate_build(root/'build.json',approval['build_receipt_sha256'],manifest)
    require(set(approval)=={'version','execution_authorized','approval_reference','manifest_sha256',
        'build_receipt_sha256','environment_sha256','output_root','gpu_uuid','limits'}
        and type(approval['version']) is int and approval['version']==1
        and isinstance(approval['approval_reference'],str) and approval['approval_reference'].strip(),'invalid Phase B approval')
    require(ledger['output_root']==approval['output_root'],'approved evidence root mismatch')
    validate_environment(ledger['environment'],build,approval)
    require(len(items)==8 and len({item['run']['seed'] for item in items})==8,'complete independent eight-replica cohort required')
    for item in items:
        receipt=item['receipt']
        require(type(receipt['wall_seconds']) in (int,float) and math.isfinite(receipt['wall_seconds'])
            and receipt['wall_seconds']>0 and type(receipt['max_rss_bytes']) is int and receipt['max_rss_bytes']>0,'invalid runtime/RSS receipt')
    return manifest,items
