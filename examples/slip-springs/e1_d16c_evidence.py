"""D1.6C read-only original authentication and full-payload return packaging."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile

import e1_d16c_spec as spec
from e1_d16c_json import extract
from e1_d1_pilot import require, load, file_record, digest, encoded

HEADER_KEYS=('schema','status','scientific_acceptance','authentication','outcomes','outcome_counts','confirmatory_planning')


def verify_file(path,record):
    require(file_record(path)==record,'missing/corrupt evidence: '+str(path))


def verify_lock():
    lock=spec.original();root=Path(lock['root'])
    require(root==spec.durable(root),'original root moved')
    for name,record in lock['files'].items():verify_file(root/name,record)
    verify_file(root/lock['analysis'],lock['analysis_identity'])
    require(digest(root/'campaign/campaign_complete.json')==lock['completion_sha256'],'wrong cohort completion')
    return lock,root


def analysis_metadata(paths=()):
    lock=spec.original();source=Path(lock['root'])/lock['analysis']
    verify_file(source,lock['analysis_identity'])
    selected={(key,) for key in HEADER_KEYS}|set(paths)
    with gzip.open(source,'rt',encoding='utf-8') as stream:
        found=extract(stream,selected,load(spec.CONFIG/'resources.json')['json_decompressed_max_chars'])
    require(all((key,) in found for key in HEADER_KEYS),'original analysis header missing')
    verify_file(source,lock['analysis_identity'])
    return {key:found[(key,)] for key in HEADER_KEYS},found


def authenticate():
    """No draws, GPU queries or recomputation of original scientific estimators."""
    import e1_d16b_local as original_control
    import e1_d16b_auth as original_auth
    import e1_d16b_spec as original_spec
    from e1_d16b_references import import_moments
    lock,root=verify_lock()
    require(not (root/'execution-running.json').exists(),'original execution is active/orphaned')
    session,_=original_control.checked(root)
    require(session['commit']==lock['source_commit'],'wrong archived scientific-analysis source')
    launch=load(root/'launch.json')
    manifest,items=original_auth.authenticate_campaign(root/'campaign',root/'campaign/manifest.json',
        session['manifest']['sha256'],launch['approval_sha256'],lock['completion_sha256'])
    require(len(items)==16,'incomplete original cohort')
    references=import_moments()
    require(references==load(root/'references.json'),'accepted reference import changed')
    header,_=analysis_metadata()
    require(header['schema']=='e1-d16b-exploratory-analysis-v1' and header['status']=='EXPLORATORY_COMPLETE'
            and header['scientific_acceptance'] is None,'original analysis incomplete or incorrectly relabeled')
    authentication=header['authentication']
    for key,name in (('manifest','manifest.json'),('approval','approval.json'),('completion','campaign_complete.json')):
        require(authentication[key]==file_record(root/'campaign'/name),'analysis/campaign identity mismatch: '+key)
    require(authentication['sources']==session['sources']==original_spec.tool_hashes(), 'original analysis source closure changed')
    receipts={item['run']['id']:file_record(item['root'].parent/'execution.json') for item in items}
    require(authentication['raw_receipts']==receipts,'analysis/raw receipt identity mismatch')
    recorded=load(root/lock['recorded_result'])
    receipt=load(root/Path(lock['analysis']).parent/'analysis-result.json')
    require(receipt['file']==recorded['file']==lock['analysis_identity'] and receipt['status']==recorded['status']=='EXPLORATORY_COMPLETE',
            'saved result/analysis receipt mismatch')
    require(receipt['output']==recorded['output']==str(root/lock['analysis']),'analysis absolute path changed')
    for key in ('outcomes','outcome_counts','confirmatory_planning'):
        require(header[key]==recorded[key]==receipt[key],'saved scientific summary disagreement: '+key)
    process=load(root/Path(lock['analysis']).parent/'process.json')
    require(process['status']=='exited' and process['exit_code']==0 and process['wall_seconds']<=7200
            and process['max_rss_bytes']<=4*1024**3,'original analysis resource/process failure')
    verify_lock()
    return {'schema':'e1-d16c-original-authentication-v1','status':'AUTHENTICATED_EXISTING_EXPLORATORY_RESULT',
        'original_lock':file_record(spec.CONFIG/'original-lock.json'),'analysis':lock['analysis_identity'],
        'completion_sha256':lock['completion_sha256'],'header':header,'original_session':session,
        'raw_inventory':{item['run']['id']:{'receipt':receipts[item['run']['id']],
            'original_path':str(item['root']), 'files':item['data']['files']} for item in items},
        'new_scientific_calculations':False,'original_packaging_failure_is_campaign_failure':False}


def evidence_inventory():
    root=Path(spec.original()['root']);result={}
    # Preserve original evidence inventories and raw hashes; never embed CSV/binaries.
    for parent,dirs,files in os.walk(root,followlinks=False):
        parent=Path(parent)
        if parent==root:dirs[:]=[d for d in dirs if d not in ('source','preparation','scratch')]
        require(not any((parent/d).is_symlink() for d in dirs),'symlink in original evidence')
        for name in sorted(files):
            path=parent/name;relative=str(path.relative_to(root))
            result[relative]=dict(file_record(path),local_path=str(path))
    return result


def copy_payload(source,destination,expected,max_bytes):
    require(expected['bytes']<=max_bytes,'payload cap exceeded; preserve data, do not truncate')
    verify_file(source,expected)
    with Path(source).open('rb') as src,Path(destination).open('xb') as dst:
        shutil.copyfileobj(src,dst,1024*1024)
    verify_file(destination,expected);verify_file(source,expected)


def return_pair(directory,kind,payload_source,payload_record,metadata):
    """Two unchanged payloads; the supervisor adds a manifest after resource accounting."""
    require(kind in ('existing','audit'),'invalid independently versioned payload kind')
    require(not ({'payload-binding.json','SHA256SUMS'} & set(metadata)), 'reserved metadata member name')
    directory=spec.durable(directory)
    require(not directory.is_relative_to(Path(spec.original()['root'])), 'never write into original evidence')
    directory.mkdir(exist_ok=False)
    limits=load(spec.CONFIG/'resources.json')
    payload_name='d16b-original-analysis.json.gz' if kind=='existing' else 'd16c-secondary-audit.json.gz'
    metadata_name='d16c-existing-metadata.tar.gz' if kind=='existing' else 'd16c-audit-metadata.tar.gz'
    copy_payload(payload_source,directory/payload_name,payload_record,limits['payload_max_bytes'])
    bodies={name:(body if isinstance(body,bytes) else encoded(body)) for name,body in metadata.items()}
    bodies['payload-binding.json']=encoded({'schema':'e1-d16c-payload-pair-v1','kind':kind,
        'scientific_payload':{'filename':payload_name,**payload_record},
        'preservation':'original payload bytes unchanged' if kind=='existing' else 'new separately versioned secondary diagnostics'})
    bodies['SHA256SUMS']=''.join(hashlib.sha256(body).hexdigest()+'  '+name+'\n' for name,body in sorted(bodies.items())).encode()
    require(sum(map(len,bodies.values()))<=limits['metadata_max_bytes'],'metadata cap exceeded; nothing silently omitted')
    with (directory/metadata_name).open('xb') as stream,tarfile.open(fileobj=stream,mode='w:gz') as tar:
        for name,body in sorted(bodies.items()):
            require(not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe archive member')
            info=tarfile.TarInfo(name);info.size=len(body);info.mode=0o600;tar.addfile(info,io.BytesIO(body))
    files={name:file_record(directory/name) for name in (metadata_name,payload_name)}
    # Re-read both members before emitting upload instructions.
    for name,record in files.items():verify_file(directory/name,record)
    return {'schema':'e1-d16c-return-v1','kind':kind,'files':files,'directory':str(directory),
            'upload':[metadata_name,payload_name,'return-manifest.json']}


def original_metadata(authentication,inventory):
    lock=spec.original();root=Path(lock['root'])
    values={'authentication.json':authentication,'original-evidence-inventory.json':inventory,
            'new-source-identity.json':{'sources':spec.tools(),'protocol':load(spec.CONFIG/'protocol.json'),
                                        'resources':load(spec.CONFIG/'resources.json')}}
    # Copy exact original metadata/receipts: preserving old inventories is not rebuilding them.
    for name in lock['files']:values['original/'+name]=(root/name).read_bytes()
    for run in authentication['raw_inventory']:
        path=root/'campaign/runs'/run/'execution.json'
        values['original/campaign/runs/'+run+'/execution.json']=path.read_bytes()
    return values



def finalize_return(receipt,process,context):
    require(process['status']=='exited' and process['exit_code']==0,'cannot issue a completed return manifest for failed worker')
    root=Path(receipt['directory'])
    expected={'d16c-existing-metadata.tar.gz','d16b-original-analysis.json.gz'} if receipt['kind']=='existing' else {'d16c-audit-metadata.tar.gz','d16c-secondary-audit.json.gz'}
    require(receipt['kind'] in ('existing','audit') and set(receipt['files'])==expected, 'incomplete return payload pair')
    for name,record in receipt['files'].items():verify_file(root/name,record)
    value={'schema':'e1-d16c-detached-return-manifest-v1','kind':receipt['kind'],
           'files':receipt['files'],'bounded_stage_process':process,'context':context,
           'integrity':'SHA256 binds sizes and bytes; not a digital signature against wholesale replacement.'}
    with (root/'return-manifest.json').open('xb') as stream:stream.write(encoded(value))
    return value
