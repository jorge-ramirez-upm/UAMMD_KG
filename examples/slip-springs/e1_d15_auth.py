"""D1.5 bindings to unchanged accepted receipt/schema/environment verification."""
import math
from pathlib import Path
import e1_d15_prepare as spec
import e1_d13_phase_a_auth as accepted
from e1_d13_reuse import bind
from e1_d1_pilot import require,load

base=bind('auth',spec)
_output=base.validate_output
_build=base.validate_build
COUNTERS=base.SIDECAR_COUNTERS
validate_environment=accepted.validate_environment


def validate_output(root,run,observations,snapshots,gpu):
    result=_output(root,run,observations,snapshots,gpu)
    accepted.timers(result['metadata'],load(Path(root)/'equilibrium_complete.json'))
    accepted.counters(load(Path(root)/'hopping_metadata.json'),run)
    return result


def validate_build(path,sha,manifest,live=False):
    value=_build(path,sha,manifest,live)
    require(value['architecture']=='sm_86' and 'release 13.' in value['nvcc']['version'],'CUDA13/sm86 required')
    require(value['source']['origin'] in ('git@github.com:jorge-ramirez-upm/UAMMD_KG.git',
              'https://github.com/jorge-ramirez-upm/UAMMD_KG.git'),'incorrect origin')
    return value


base.validate_output=validate_output
base.validate_build=validate_build


def authenticate_campaign(root,manifest_path,manifest_sha,approval_sha,completion_sha):
    manifest,items=base.authenticate_campaign(root,manifest_path,manifest_sha,approval_sha,completion_sha)
    require(manifest['execution_supported'] and len(items)==4,'only complete bounded D1.5 cohorts supported')
    approval=load(Path(root)/'approval.json');ledger=load(Path(root)/'campaign.json')
    require(set(approval)==BASE_APPROVAL_FIELDS|REVIEW_FIELDS,'unexpected approval fields')
    require(type(approval['version']) is int and approval['version']==1 and
        isinstance(approval['approval_reference'],str) and approval['approval_reference'].strip(),'invalid independent approval reference')
    require(ledger['output_root']==approval['output_root'],'approved evidence root mismatch')
    build=validate_build(Path(root)/'build.json',approval['build_receipt_sha256'],manifest)
    validate_environment(ledger['environment'],build,approval)
    approval_reviews(approval,manifest)
    for item in items:
        receipt=item['receipt']
        require(type(receipt['wall_seconds']) in (int,float) and math.isfinite(receipt['wall_seconds'])
                and receipt['wall_seconds']>0 and type(receipt['max_rss_bytes']) is int and receipt['max_rss_bytes']>0,
                'invalid wall/RSS measurement')
    return manifest,items


REVIEW_FIELDS={'readiness_review','benchmark_review'}
BASE_APPROVAL_FIELDS={'version','execution_authorized','approval_reference','manifest_sha256',
    'build_receipt_sha256','environment_sha256','output_root','gpu_uuid','limits'}


def reviewed_record(pointer,schema):
    require(isinstance(pointer,dict) and set(pointer)=={'path','sha256'},'separate review record and external SHA256 required')
    path=Path(pointer['path'])
    require(path.is_absolute() and not path.is_symlink() and spec.digest(path)==pointer['sha256'],'review moved/changed/missing')
    value=load(path)
    require(value['schema']==schema and isinstance(value['review_reference'],str)
            and value['review_reference'].strip(),'independent review reference required')
    return value


def approval_reviews(approval,manifest):
    require(set(approval)==BASE_APPROVAL_FIELDS|REVIEW_FIELDS,'D1.5 approval/review schema mismatch')
    require(type(approval['version']) is int and approval['version']==1
            and type(approval['execution_authorized']) is bool,'invalid approval version/flag type')
    ready=reviewed_record(approval['readiness_review'],'e1-d15-readiness-review-v1')
    require(ready['manifest_sha256']==spec.identity(manifest)
        and ready['build_receipt_sha256']==approval['build_receipt_sha256']
        and ready['all_local_preparation_checks_reviewed'] is True,'local checks not reviewed for this exact manifest/build')
    require(isinstance(ready['artifacts'],dict) and ready['artifacts'],'reviewed check evidence required')
    for path,proof in ready['artifacts'].items():
        require(Path(path).is_absolute() and proof['bytes']>0 and spec.file_record(path)==proof,'local check evidence changed/missing')
    if manifest['kind']=='benchmark':
        require(approval['benchmark_review'] is None,'benchmark cannot adopt a prior pilot review')
        return
    require(manifest['kind']=='pilot','long exploratory design is not executable')
    review=reviewed_record(approval['benchmark_review'],'e1-d15-benchmark-review-v1')
    require(review['approved_pilot_manifest_sha256']==spec.identity(manifest)
        and review['resource_and_observation_suitability_reviewed'] is True,'benchmark not reviewed for this bounded pilot')
    prior,items=authenticate_campaign(review['benchmark_root'],CONFIG_BENCH/'manifest.json',
        review['manifest_sha256'],review['approval_sha256'],review['completion_sha256'])
    require(prior['kind']=='benchmark' and len(items)==4,'wrong/incomplete benchmark evidence')


CONFIG_BENCH=spec.CONFIG/'benchmark'
