"""Private local build, preflight and sequential D1.6B execution. No default action."""
import argparse
import contextlib
import ctypes
import fcntl
import os
from pathlib import Path
import shutil
import signal
import sys
import time

import e1_d16b_spec as spec
import e1_d16b_auth as auth
from e1_d13_reuse import bind
from e1_d15_local import write
from e1_d1_pilot import require, load, digest, file_record, identity, atomic

shared=bind('runner',spec)
shared.auth=auth.base
_original_environment=shared.environment


def environment(cuda=None,gpu_uuid=None):
    value=_original_environment(cuda,gpu_uuid)
    scratch=spec.durable(os.environ.get('TMPDIR',spec.PROJECT/'build/d16b-scratch'))
    scratch.mkdir(parents=True,exist_ok=True)
    value['TMPDIR']=str(scratch)
    return value


shared.environment=environment


@contextlib.contextmanager
def gpu_lock():
    # New durable lock namespace; no historical lock or approval is modified.
    parent=Path('/home/jramirez/UAMMD_KG-evidence/d16b/.locks')
    parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(parent/(spec.GPU_UUID+'.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:os.close(fd)


def preflight(root):
    root=spec.durable(root)
    manifest=spec.validate_manifest(spec.CONFIG/'manifest.json',digest(spec.CONFIG/'manifest.json'))
    build=auth.validate_build(root/'build/build.json',digest(root/'build/build.json'),manifest,live=True)
    stable,free=shared.machine(build,spec.GPU_UUID)
    auth.validate_environment(stable,build,spec.GPU_UUID)
    limits=spec.validate_limits(load(spec.CONFIG/'resources.json')['limits'])
    resources=shared.resource_check(root,limits,free)
    require(resources['free_disk_bytes']>=limits['min_free_disk_bytes']+2*limits['aggregate_output_bytes'],
            'need disk floor plus two full campaign quotas (18 GiB initially)')
    return {'schema':'e1-d16b-preflight-v1','execution_authorized':False,
            'environment':stable,'environment_sha256':identity(stable),'resources':resources,
            'estimates':spec.estimates(manifest),'build':file_record(root/'build/build.json')}


def bounded_output_check(root,directory,run,limits,start,run_start,build):
    check=root/'authentication'/run['id'];check.mkdir(parents=True,exist_ok=False)
    remaining=min(limits['per_run_seconds']-(time.monotonic()-run_start),
                  limits['aggregate_seconds']-(time.monotonic()-start))
    require(remaining>0,'output authentication has no remaining wall budget')
    remaining_output=limits['per_run_output_bytes']-shared.tree_bytes(directory)-65536
    require(remaining_output>0,'output authentication has no remaining output budget')
    restricted=dict(limits,per_run_seconds=remaining,per_run_output_bytes=remaining_output)
    argv=[sys.executable,str(spec.PROJECT/'e1_d16b_host.py'),'_check-output',
          '--root',str(root),'--run-id',run['id'],'--output',str(check/'result.json')]
    result=shared.run_process(argv,check,environment(build['cuda_home']),restricted,root,start)
    require(result['status']=='exited' and result['exit_code']==0,'bounded output authentication failed: '+result['status'])
    require(shared.tree_bytes(directory)+shared.tree_bytes(check)<=limits['per_run_output_bytes'],
            'combined run/authentication output budget exceeded')
    return load(check/'result.json')


def execute(session_root,approval_path,approval_sha,explicit):
    require(explicit is True,'explicit --execute-reviewed-t100 required')
    session_root=spec.durable(session_root)
    from e1_d16b_local import checked
    checked(session_root)
    require(digest(approval_path)==approval_sha,'trusted approval SHA256 mismatch')
    approval=load(approval_path)
    limits=auth.validate_approval(approval,session_root,approval_sha)
    launch=load(session_root/'launch.json')
    parent=os.getppid()
    require(launch['parent_pid']==parent and launch['approval_sha256']==approval_sha
            and launch['readiness']==file_record(session_root/'readiness.json'), 'authenticated local parent required')
    require(ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGKILL,0,0,0)==0
            and os.getppid()==parent, 'cannot guard local-supervisor death')
    manifest=spec.validate_manifest(spec.CONFIG/'manifest.json',approval['manifest_sha256'])
    root=Path(approval['output_root'])
    require(root==session_root/'campaign' and not root.exists(),'fresh fixed campaign root required; no retries')
    write(session_root/'execution-attempt.json',{'approval':file_record(approval_path),'parent_pid':os.getppid(),
                                             'started_utc':spec.utc()})
    # Everything below lies inside the local outer 14,400-second command bound.
    flight=preflight(session_root)
    require(flight['environment_sha256']==approval['environment_sha256'],'environment changed since review')
    from e1_d16b_references import import_moments
    require(import_moments()==load(session_root/'references.json'),'reference import changed since review')
    build=auth.validate_build(session_root/'build/build.json',approval['build_receipt_sha256'],manifest,live=True)
    root.mkdir(exist_ok=False)
    start=time.monotonic()
    status={'version':1,'status':'preparing','started_utc':spec.utc(),'completed_run_ids':[]}
    atomic(root/'status.json',status)
    try:
        for name in ('runs','config','provenance','authentication'):(root/name).mkdir()
        for source,name in ((spec.CONFIG/'manifest.json','manifest.json'),(approval_path,'approval.json'),
                             (session_root/'build/build.json','build.json')):shutil.copyfile(source,root/name)
        for name in manifest['schedules']:shutil.copyfile(spec.CONFIG/name,root/'config'/name)
        shutil.copyfile(build['binary']['path'],root/'provenance/semiflexible')
        (root/'provenance/semiflexible').chmod(0o500)
        shutil.copyfile(build['log']['path'],root/'provenance/build.log')
        ledger={'version':1,'campaign':manifest['campaign'],'manifest_sha256':approval['manifest_sha256'],
            'approval_sha256':approval_sha,'build_receipt_sha256':approval['build_receipt_sha256'],
            'environment':flight['environment'],'environment_sha256':flight['environment_sha256'],
            'started_utc':status['started_utc'],'output_root':str(root),'limits':limits,
            'source':build['source'],'preparation_sources':manifest['preparation_sources'],
            'references':approval['references'],'readiness':approval['readiness']}
        atomic(root/'campaign.json',ledger)
        status['status']='running';atomic(root/'status.json',status)
        for run in manifest['runs']:
            spec.validate_manifest(spec.CONFIG/'manifest.json',approval['manifest_sha256'])
            auth.validate_build(session_root/'build/build.json',approval['build_receipt_sha256'],manifest,live=True)
            require(digest(approval_path)==approval_sha,'approval changed')
            stable,free=shared.machine(build,approval['gpu_uuid'])
            auth.validate_environment(stable,build,approval['gpu_uuid'])
            require(identity(stable)==flight['environment_sha256'],'runtime environment changed')
            resources=shared.resource_check(root,limits,free)
            require(time.monotonic()-start<limits['aggregate_seconds'],'aggregate wall budget exhausted')
            require(file_record(root/'provenance/semiflexible')==build['binary']['file'],'archived executable changed')
            directory=root/'runs'/run['id'];directory.mkdir(exist_ok=False)
            argv=spec.command(run,root/'provenance/semiflexible',directory/'output',root/'config')
            receipt={'version':1,'status':'running','started_utc':spec.utc(),'run':run,'command':argv,
                'manifest_sha256':approval['manifest_sha256'],'build_receipt_sha256':approval['build_receipt_sha256'],
                'environment_sha256':flight['environment_sha256'],'resources_before':resources,'exit_code':None}
            atomic(directory/'execution.json',receipt);run_start=time.monotonic()
            try:
                result=shared.run_process(argv,directory,environment(build['cuda_home'],approval['gpu_uuid']),limits,root,start)
                receipt.update(result)
                require(result['status']=='exited' and result['exit_code']==0,'run failure/resource limit: '+result['status'])
                data=bounded_output_check(root,directory,run,limits,start,run_start,build)
                receipt.update(status='completed',output_files=data['files'],event_totals=data['event_totals'],
                    logs={name:file_record(directory/name) for name in ('stdout.log','stderr.log','process.json')},
                    output_authentication={str(p.relative_to(root)):file_record(p)
                        for p in sorted((root/'authentication'/run['id']).iterdir()) if p.is_file()},
                    run_stage_wall_seconds=time.monotonic()-run_start)
                require(receipt['run_stage_wall_seconds']<=limits['per_run_seconds'],'run stage wall cap exceeded')
            except BaseException as error:
                if (directory/'process.json').exists():receipt.update(load(directory/'process.json'))
                receipt.update(status='interrupted' if isinstance(error,(KeyboardInterrupt,SystemExit)) else 'failed',error=str(error))
                raise
            finally:
                receipt['ended_utc']=spec.utc();atomic(directory/'execution.json',receipt)
            status['completed_run_ids'].append(run['id']);atomic(root/'status.json',status)
        # Full independent raw authentication before issuing any completion identity.
        for run in manifest['runs']:
            auth.base.authenticate_run(root/'runs'/run['id'],run,manifest,ledger,approval,
                                       digest(root/'runs'/run['id']/'execution.json'))
        require(load(root/'campaign.json')==ledger and digest(root/'approval.json')==approval_sha,'archived inputs changed')
        auth.validate_build(session_root/'build/build.json',approval['build_receipt_sha256'],manifest,live=True)
        require(time.monotonic()-start<=limits['aggregate_seconds'] and shared.tree_bytes(root)<limits['aggregate_output_bytes'],
                'aggregate post-authentication budget exceeded')
        status.update(status='completed',ended_utc=spec.utc(),wall_seconds=time.monotonic()-start)
        atomic(root/'status.json',status)
        atomic(root/'campaign_complete.json',{'version':1,'status':'completed',
            'campaign_sha256':digest(root/'campaign.json'),'status_sha256':digest(root/'status.json'),
            'run_ids':[r['id'] for r in manifest['runs']],
            'receipts':{r['id']:digest(root/'runs'/r['id']/'execution.json') for r in manifest['runs']}})
        require(shared.tree_bytes(root)<=limits['aggregate_output_bytes'],'completion output budget exceeded')
    except BaseException as error:
        status.update(status='interrupted' if isinstance(error,(KeyboardInterrupt,SystemExit)) else 'failed',
                      ended_utc=spec.utc(),error=str(error))
        atomic(root/'status.json',status)
        raise
    return {'status':'completed','root':str(root),'completion_sha256':digest(root/'campaign_complete.json')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    build=sub.add_parser('build')
    for name in ('source-tree','build-root','cuda-home'):build.add_argument('--'+name,type=Path,required=True)
    build.add_argument('--arch',default='sm_86');build.add_argument('--cxx',type=Path,default=Path('/usr/bin/g++'))
    for action in ('preflight','_execute','_check-output'):
        child=sub.add_parser(action);child.add_argument('--root',type=Path,required=True)
        if action=='preflight':child.add_argument('--output',type=Path,required=True)
        if action=='_execute':
            child.add_argument('--approval',type=Path,required=True);child.add_argument('--approval-sha256',required=True)
            child.add_argument('--execute-reviewed-t100',action='store_true',required=True)
        if action=='_check-output':
            child.add_argument('--run-id',required=True);child.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    if args.action=='build':
        spec.durable(args.source_tree);spec.durable(args.build_root)
        args.manifest=spec.CONFIG/'manifest.json';args.manifest_sha256=digest(args.manifest)
        print(spec.encoded(shared.build(args)).decode())
    elif args.action=='preflight':write(args.output,preflight(args.root))
    elif args.action=='_execute':
        with gpu_lock():
            print(spec.encoded(execute(args.root,args.approval,args.approval_sha256,args.execute_reviewed_t100)).decode())
    else:
        manifest=spec.validate_manifest(spec.CONFIG/'manifest.json',digest(spec.CONFIG/'manifest.json'))
        run=next(r for r in manifest['runs'] if r['id']==args.run_id)
        gpu=load(args.root/'campaign.json')['environment']['gpu']['name']
        write(args.output,auth.validate_output(args.root/'runs'/run['id']/'output',run,
            manifest['schedules'][run['schedule']]['steps'],manifest['schedules'][run['snapshots']]['steps'],gpu))


if __name__=='__main__':main()
