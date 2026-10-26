#!/usr/bin/env python3
"""Separately gated D1.6C authentication/packaging, audit and audit-return stages."""
import argparse
import ctypes
import gzip
import hashlib
import io
import os
from pathlib import Path
import signal
import sys
import tarfile
import tempfile
import time

import e1_d16c_spec as spec
from e1_d1_pilot import require, load, file_record, digest, encoded
from e1_d15_local import write, git, clean, command, local_env
from e1_d1_pilot_runner import run_process
from e1_d16c_evidence import authenticate, evidence_inventory, original_metadata, return_pair, verify_file, finalize_return


def tree_records(root):
    result={}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(),'symlink in new evidence')
        if path.is_file():result[str(path.relative_to(root))]=file_record(path)
    return result


def verify_records(root,records):
    require(tree_records(root)==records,'new stage evidence inventory changed')


def environment_snapshot():
    import e1_d16c_audit
    import e1_d16c_json
    from e1_d16a2_local import environment
    return environment()


def verify_environment(root,project,name):
    output=root/'scratch'/(name+'.json')
    command(root,name,[sys.executable,project/'e1_d16c_local.py','_environment','--output',output],
            project,180,local_env(root))
    if file_record(output)!=file_record(root/'environment.json'):
        retained=root/(name+'-unexpected.json');require(not retained.exists(),'environment observation already exists')
        output.rename(retained)
        raise ValueError('dependency/environment changed; retained '+str(retained))


def approval_template(root):
    return {'schema':'e1-d16c-secondary-audit-approval-v1','audit_authorized':False,'review_reference':None,
        'root':str(root),'output':str(root/'stage-b'),'GPU_authorized':False,
        'stage_a_binding':file_record(root/'stage-a/readiness-binding.json'),'stage_a_metadata_sha256':None,'session':file_record(root/'session.json'),
        'environment':file_record(root/'environment.json'),'protocol':file_record(spec.CONFIG/'protocol.json'),
        'resources':file_record(spec.CONFIG/'resources.json'),'original_lock':file_record(spec.CONFIG/'original-lock.json'),
        'authentication':file_record(root/'stage-a/authentication.json')}


def approved(root,path,sha):
    spec.checked(root);verify_file(path,{'sha256':sha,'bytes':Path(path).stat().st_size})
    value=load(path);template=load(root/'audit-approval-template.json')
    require(template==approval_template(root),'reviewed Stage A/configuration changed')
    expected=dict(template,audit_authorized=True,review_reference=value.get('review_reference'),
                  stage_a_metadata_sha256=digest(root/'stage-a/returns/d16c-existing-metadata.tar.gz'))
    require(type(value.get('audit_authorized')) is bool and value==expected
            and isinstance(value['review_reference'],str) and value['review_reference'].strip(),
            'new independently reviewed read-only audit approval required')
    completion=load(root/'stage-a-complete.json')
    require(completion['status']=='EXISTING_RESULT_RETURN_READY','Stage A failed')
    verify_records(root/'stage-a',completion['files'])
    verify_records(root/'tests',completion['tests'])
    return value


def run_worker(root,project,stage,mode,started=None):
    contract=spec.resources(mode);started=time.monotonic() if started is None else started
    remaining=contract['seconds']-(time.monotonic()-started)
    require(remaining>0,'stage wall budget exhausted')
    limits={'per_run_seconds':remaining,'aggregate_seconds':contract['seconds'],
        'per_run_output_bytes':contract['output_bytes'],'aggregate_output_bytes':contract['output_bytes'],
        'max_host_rss_bytes':contract['rss_bytes'],'min_free_disk_bytes':contract['min_free_disk_bytes']}
    require(__import__('shutil').disk_usage(stage).free>=contract['min_free_disk_bytes']+contract['output_bytes'],'insufficient durable disk headroom')
    env=local_env(root);env['CUDA_VISIBLE_DEVICES']=''
    argv=[sys.executable,'-B',str(project/'e1_d16c_local.py'),'_worker','--root',str(root),
          '--mode',mode,'--parent-pid',str(os.getpid())]
    result=run_process(argv,stage,env,limits,stage,started)
    require(result['status']=='exited' and result['exit_code']==0,'bounded D1.6C '+mode+' failed: '+result['status'])
    return result


def uploads(receipt):
    for name in receipt['upload']:print('UPLOAD',Path(receipt['directory'])/name,flush=True)


def failure_packet(root,stage,error):
    # Reporting an unfavorable failure does not retry authentication/analysis/packaging.
    directory=root/(stage+'-failure-return');directory.mkdir(exist_ok=False)
    archive=directory/'d16c-failure-metadata.tar.gz'
    payload={'failure.json':encoded({'schema':'e1-d16c-failure-v1','stage':stage,'error':str(error),
        'this_D16C_stage_complete':False,'root':str(root),
        'original_campaign':'Reported completed; this D1.6C failure does not reclassify it','originals_modified':False})}
    source=root/stage
    if source.exists():
        for name in ('process.json','worker-failure.json','stderr.log'):
            path=source/name
            if path.is_file() and path.stat().st_size<=1024**2:payload[name]=path.read_bytes()
    with archive.open('xb') as stream,tarfile.open(fileobj=stream,mode='w:gz') as tar:
        for name,body in payload.items():
            info=tarfile.TarInfo(name);info.size=len(body);tar.addfile(info,io.BytesIO(body))
    (directory/'SHA256SUMS').write_text(digest(archive)+'  '+archive.name+'\n')
    print('UPLOAD',archive,flush=True);print('UPLOAD',directory/'SHA256SUMS',flush=True)


def existing(args):
    started=time.monotonic();parent=spec.fresh_output(args.evidence_parent)
    root=Path(tempfile.mkdtemp(prefix='d16c-existing-',dir=parent));print('D16C_ROOT='+str(root),flush=True)
    (root/'scratch').mkdir();(root/'logs').mkdir()
    try:
        repo=spec.PROJECT.parents[1];clean(repo)
        require(git(repo,'branch','--show-current')=='slip-springs','use slip-springs')
        git(repo,'fetch','origin','slip-springs');commit=git(repo,'rev-parse','HEAD')
        require(commit==git(repo,'rev-parse','origin/slip-springs'),'HEAD differs from fetched tip')
        git(repo,'merge-base','--is-ancestor',spec.START,commit)
        spec.durable(git(repo,'rev-parse','--path-format=absolute','--git-common-dir'))
        command(root,'checkout',['git','-C',repo,'worktree','add','--detach',root/'preparation',commit],repo,60,local_env(root))
        project=root/'preparation/examples/slip-springs'
        write(root/'session.json',{'schema':'e1-d16c-session-v1','commit':commit,'root':str(root),'project':str(project),
            'python':str(Path(sys.executable).resolve()),'tools':spec.tools()})
        command(root,'environment',[sys.executable,project/'e1_d16c_local.py','_environment','--output',root/'environment.json'],project,180,local_env(root))
        tests=root/'tests';tests.mkdir()
        test_limits=spec.resources('tests');env=local_env(root);env['CUDA_VISIBLE_DEVICES']=''
        process_limits={'per_run_seconds':test_limits['seconds'],'aggregate_seconds':test_limits['seconds'],
            'per_run_output_bytes':test_limits['output_bytes'],'aggregate_output_bytes':test_limits['output_bytes'],
            'max_host_rss_bytes':test_limits['rss_bytes'],'min_free_disk_bytes':test_limits['min_free_disk_bytes']}
        process=run_process([sys.executable,'-B','-m','unittest','discover','-s',str(project/'tests'),'-p','test_e1_d16c.py','-v'],
            tests,env,process_limits,tests,time.monotonic())
        require(process['status']=='exited' and process['exit_code']==0,'D1.6C deterministic local verification failed')
        stage=root/'stage-a';stage.mkdir()
        process=run_worker(root,project,stage,'existing',started)
        result=load(stage/'result.json')
        finalize_return(result['return'],process,{'session':file_record(root/'session.json'),
            'tests':tree_records(tests),'original_analysis':spec.original()['analysis_identity']})
        require(time.monotonic()-started<=spec.resources('existing')['seconds'],'Stage A wall cap exceeded at finalization')
        write(root/'stage-a-complete.json',dict(result,files=tree_records(stage),process=process,tests=tree_records(tests)))
        uploads(result['return'])
    except BaseException as error:
        write(root/'stage-a-failed.json',{'status':'FAILED','error':str(error) or type(error).__name__})
        failure_packet(root,'stage-a',error);raise


def audit(args):
    require(args.execute_reviewed_audit is True,'explicit audit-only execution flag required')
    started=time.monotonic();root=spec.durable(args.root);_,project=spec.checked(root)
    approved(root,args.approval,args.approval_sha256)
    write(root/'audit-attempt.json',{'schema':'e1-d16c-audit-attempt-v1','approval_sha256':args.approval_sha256,
                                    'parent_pid':os.getpid(),'original_authentication':file_record(root/'stage-a/authentication.json')})
    with Path(args.approval).open('rb') as src,(root/'reviewed-audit-approval.json').open('xb') as dst:dst.write(src.read())
    stage=root/'stage-b';stage.mkdir()
    try:
        verify_environment(root,project,'environment-before-audit')
        process=run_worker(root,project,stage,'audit',started)
        result=load(stage/'audit-result.json')
        write(root/'stage-b-complete.json',{'status':'SECONDARY_EXPLORATORY_COMPLETE','result':result,
            'process':process,'files':tree_records(stage),'approval':file_record(root/'reviewed-audit-approval.json')})
        print('SECONDARY AUDIT COMPLETE; run return-audit to package the new results.',flush=True)
    except BaseException as error:
        write(root/'stage-b-failed.json',{'status':'FAILED','error':str(error) or type(error).__name__})
        failure_packet(root,'stage-b',error);raise


def audit_return(args):
    started=time.monotonic();root=spec.durable(args.root);_,project=spec.checked(root)
    stage=root/'stage-c';stage.mkdir()
    try:
        process=run_worker(root,project,stage,'return',started)
        result=load(stage/'result.json')
        finalize_return(result['return'],process,{'audit_completion':file_record(root/'stage-b-complete.json'),
            'session':file_record(root/'session.json'),'original_analysis':spec.original()['analysis_identity']})
        require(time.monotonic()-started<=spec.resources('return')['seconds'],'Stage C wall cap exceeded at finalization')
        write(root/'stage-c-complete.json',{'status':'AUDIT_RETURN_READY','process':process,'files':tree_records(stage)})
        uploads(result['return'])
    except BaseException as error:
        write(root/'stage-c-failed.json',{'status':'FAILED','error':str(error) or type(error).__name__})
        failure_packet(root,'stage-c',error);raise


def worker(args):
    root=spec.durable(args.root);spec.checked(root)
    require(os.getppid()==args.parent_pid,'authenticated local supervisor required')
    require(ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGKILL,0,0,0)==0 and os.getppid()==args.parent_pid,'parent-death guard failed')
    stage=root/{'existing':'stage-a','audit':'stage-b','return':'stage-c'}[args.mode]
    write(stage/'worker-started.json',{'pid':os.getpid(),'mode':args.mode})
    try:
        if args.mode=='existing':
            authentication=authenticate();inventory=evidence_inventory()
            write(stage/'authentication.json',authentication);write(stage/'original-inventory.json',inventory)
            write(stage/'readiness-binding.json',{'status':'AUTHENTICATED_EXISTING_EXPLORATORY_RESULT',
                'authentication':file_record(stage/'authentication.json'),'inventory':file_record(stage/'original-inventory.json'),
                'tests':tree_records(root/'tests'),'session':file_record(root/'session.json'),
                'environment':file_record(root/'environment.json')})
            template=approval_template(root);write(root/'audit-approval-template.json',template)
            metadata=original_metadata(authentication,inventory)
            metadata['audit-approval-template.json']=template
            metadata['readiness-binding.json']=load(stage/'readiness-binding.json')
            metadata['d16c-session.json']=load(root/'session.json');metadata['d16c-environment.json']=load(root/'environment.json')
            metadata['local-tests.json']=tree_records(root/'tests')
            for name in ('stdout.log','stderr.log','process.json'):metadata['local-tests/'+name]=(root/'tests'/name).read_bytes()
            lock=spec.original()
            packet=return_pair(stage/'returns','existing',Path(lock['root'])/lock['analysis'],lock['analysis_identity'],metadata)
            require(authenticate()==authentication and evidence_inventory()==inventory,'original evidence changed during packaging')
            write(stage/'result.json',{'status':'EXISTING_RESULT_RETURN_READY','return':packet,'authentication':file_record(stage/'authentication.json')})
        elif args.mode=='audit':
            attempt=load(root/'audit-attempt.json')
            require(attempt['parent_pid']==args.parent_pid,'wrong audit invocation')
            approved(root,root/'reviewed-audit-approval.json',attempt['approval_sha256'])
            from e1_d16c_audit import audit as scientific_audit
            write(stage/'audit-result.json',scientific_audit(stage/'secondary-audit.json.gz',root/'stage-a/authentication.json'))
        else:
            complete=load(root/'stage-b-complete.json')
            require(complete['status']=='SECONDARY_EXPLORATORY_COMPLETE','secondary audit incomplete')
            verify_records(root/'stage-b',complete['files'])
            attempt=load(root/'audit-attempt.json');approved(root,root/'reviewed-audit-approval.json',attempt['approval_sha256'])
            verify_file(root/'stage-b/secondary-audit.json.gz',complete['result']['payload'])
            require(authenticate()==load(root/'stage-a/authentication.json'),'original source evidence changed')
            metadata={'secondary-result.json':complete,'secondary-approval.json':load(root/'reviewed-audit-approval.json'),
                'original-authentication.json':load(root/'stage-a/authentication.json'),
                'original-inventory.json':load(root/'stage-a/original-inventory.json'),
                'source-session.json':load(root/'session.json'),'protocol.json':load(spec.CONFIG/'protocol.json'),
                'resources.json':load(spec.CONFIG/'resources.json')}
            for path in sorted((root/'stage-b').glob('*.svg')):metadata['figures/'+path.name]=path.read_bytes()
            for name in ('stdout.log','stderr.log','process.json'):metadata['audit-process/'+name]=(root/'stage-b'/name).read_bytes()
            packet=return_pair(stage/'returns','audit',root/'stage-b/secondary-audit.json.gz',complete['result']['payload'],metadata)
            verify_records(root/'stage-b',complete['files'])
            write(stage/'result.json',{'status':'AUDIT_RETURN_READY','return':packet})
    except BaseException as error:
        write(stage/'worker-failure.json',{'status':'FAILED','error':str(error) or type(error).__name__,'scientific_acceptance':None});raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    a=sub.add_parser('existing');a.add_argument('--evidence-parent',type=Path,required=True)
    b=sub.add_parser('audit');b.add_argument('--root',type=Path,required=True);b.add_argument('--approval',type=Path,required=True)
    b.add_argument('--approval-sha256',required=True);b.add_argument('--execute-reviewed-audit',action='store_true',required=True)
    c=sub.add_parser('return-audit');c.add_argument('--root',type=Path,required=True)
    w=sub.add_parser('_worker');w.add_argument('--root',type=Path,required=True);w.add_argument('--mode',choices=('existing','audit','return'),required=True)
    w.add_argument('--parent-pid',type=int,required=True)
    e=sub.add_parser('_environment');e.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    if args.action=='existing':existing(args)
    elif args.action=='audit':audit(args)
    elif args.action=='return-audit':audit_return(args)
    elif args.action=='_worker':worker(args)
    else:write(args.output,environment_snapshot())


if __name__=='__main__':main()
