#!/usr/bin/env python3
"""Phase A only: authenticated build and read-only preflight unless separately approved."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import e1_d13_phase_a as spec
import e1_d13_phase_a_auth as auth
from e1_d13_reuse import bind
from e1_d1_pilot import require, load, digest, file_record, atomic

shared=bind('runner',spec)
shared.auth=auth.base
_machine=shared.machine


def machine(build,uuid):
    stable,free=_machine(build,uuid)
    auth.validate_environment(stable,build,{'gpu_uuid':uuid})
    return stable,free


shared.machine=machine


def host_inventory():
    """Availability only; it never supplies an approval or a safety limit."""
    result={'approved_limits':None}
    try:
        query=shared.capture(['nvidia-smi','--query-gpu=uuid,name,compute_cap,driver_version,memory.total,memory.free',
                              '--format=csv,noheader,nounits'],env=shared.environment())
        result['gpu_query_csv']=query
        cuda=Path('/usr/local/cuda').resolve();nvcc=cuda/'bin/nvcc';runtime=(cuda/'lib64/libcudart.so').resolve()
        result['cuda_toolkit']={'path':str(nvcc),'version':shared.capture([nvcc,'--version']), 'file':file_record(nvcc)}
        result['runtime']=json.loads(shared.capture([sys.executable, spec.PROJECT/'e1_d1_pilot_runner.py',
                               '_probe_runtime','--runtime-library',runtime],env=shared.environment(cuda)))
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        result['probe_unavailable']=str(error)
    return result


def preflight(args):
    summary,manifest,build,approval,limits=shared.preflight(args)
    summary['required_limits']=manifest['approved_limits']
    summary['host_inventory_availability_only']=host_inventory()
    summary['execution_flag_required']='--authorize-phase-a-execution'
    if args.output_root:
        root=spec.output_path(args.output_root,build['source']['path'] if build else None)
        if root.exists() or not root.parent.is_dir():summary['blockers'].append('new output root with existing parent required')
    return summary,manifest,build,approval,limits


def execute(args,summary,manifest,build,approval,limits):
    require(args.authorize_phase_a_execution is True,'explicit Phase A execution flag required')
    require(not summary['blockers'] and approval is not None and limits is not None,'Phase A execution blocked')
    require(spec.validate_manifest(args.manifest,args.manifest_sha256)==manifest,'manifest changed')
    root=spec.output_path(args.output_root,build['source']['path'])
    require(digest(args.approval)==args.approval_sha256,'approval identity changed')
    require(shared.validate_approval(approval,args.manifest_sha256,args.build_sha256,root,
                summary['environment_sha256'])==limits,'approved limits changed')
    auth.validate_environment(summary['environment'],build,approval)
    auth.validate_build(args.build_receipt,args.build_sha256,manifest,live=True)
    require(not root.exists() and root.parent.is_dir(),'fresh output root required')
    root.mkdir(exist_ok=False)
    start=time.monotonic();status={'version':1,'status':'preparing','started_utc':spec.utc(),'completed_run_ids':[]}
    atomic(root/'status.json',status)
    try:
        for name in ('runs','config','provenance'):(root/name).mkdir()
        for source,name in ((args.manifest,'manifest.json'),(args.approval,'approval.json'),(args.build_receipt,'build.json')):
            shutil.copyfile(source,root/name)
        for name in manifest['schedules']:shutil.copyfile(args.manifest.parent/name,root/'config'/name)
        shutil.copyfile(build['binary']['path'],root/'provenance/semiflexible');(root/'provenance/semiflexible').chmod(0o500)
        shutil.copyfile(build['log']['path'],root/'provenance/build.log')
        ledger={'version':1,'campaign':manifest['campaign'],'manifest_sha256':args.manifest_sha256,
            'approval_sha256':args.approval_sha256,'build_receipt_sha256':args.build_sha256,
            'environment':summary['environment'],'environment_sha256':summary['environment_sha256'],
            'started_utc':status['started_utc'],'output_root':str(root),'limits':limits,
            'source':build['source'],'preparation_sources':manifest['preparation_sources']}
        atomic(root/'campaign.json',ledger);status['status']='running';atomic(root/'status.json',status)
        for run in manifest['runs']:
            require(spec.validate_manifest(args.manifest,args.manifest_sha256)==manifest,'configuration changed')
            auth.validate_build(args.build_receipt,args.build_sha256,manifest,live=True)
            require(digest(args.approval)==args.approval_sha256,'approval changed')
            stable,free=machine(build,approval['gpu_uuid'])
            require(spec.identity(stable)==summary['environment_sha256'],'runtime environment changed')
            resources=shared.resource_check(root,limits,free)
            require(time.monotonic()-start<limits['aggregate_seconds'] and shared.tree_bytes(root)<limits['aggregate_output_bytes'],'aggregate budget exhausted')
            require(digest(root/'manifest.json')==args.manifest_sha256 and digest(root/'approval.json')==args.approval_sha256,'archived inputs changed')
            for name,proof in manifest['schedules'].items():require(digest(root/'config'/name)==proof['sha256'],'archived schedule changed')
            require(file_record(root/'provenance/semiflexible')==build['binary']['file'],'archived executable changed')
            directory=root/'runs'/run['id'];directory.mkdir(exist_ok=False)
            argv=spec.command(run,root/'provenance/semiflexible',directory/'output',root/'config')
            receipt={'version':1,'status':'running','started_utc':spec.utc(),'run':run,'command':argv,
                'manifest_sha256':args.manifest_sha256,'build_receipt_sha256':args.build_sha256,
                'environment_sha256':summary['environment_sha256'],'resources_before':resources,'exit_code':None}
            atomic(directory/'execution.json',receipt)
            try:
                process=shared.run_process(argv,directory,shared.environment(build['cuda_home'],approval['gpu_uuid']),limits,root,start)
                receipt.update(process,ended_utc=spec.utc())
                require(process['status']=='exited' and process['exit_code']==0,'run failure/resource limit: '+process['status'])
                data=auth.validate_output(directory/'output',run,manifest['schedules'][run['schedule']]['steps'],manifest['schedules'][run['snapshots']]['steps'],stable['gpu']['name'])
                auth.validate_build(args.build_receipt,args.build_sha256,manifest,live=True)
                require(file_record(root/'provenance/semiflexible')==build['binary']['file'],'executed binary changed')
                require(spec.validate_manifest(args.manifest,args.manifest_sha256)==manifest,'configuration changed during run')
                after,free_after=machine(build,approval['gpu_uuid'])
                require(spec.identity(after)==summary['environment_sha256'],'post-run environment changed')
                receipt.update(status='completed',output_files=data['files'],event_totals=data['event_totals'],
                    free_gpu_bytes_after=free_after,peak_gpu_bytes=None,
                    logs={name:file_record(directory/name) for name in ('stdout.log','stderr.log','process.json')})
            except BaseException as error:
                if (directory/'process.json').exists():receipt.update(load(directory/'process.json'))
                receipt.update(status='interrupted' if isinstance(error,(KeyboardInterrupt,SystemExit)) else 'failed',error=str(error),ended_utc=spec.utc())
                raise
            finally:atomic(directory/'execution.json',receipt)
            if shared.tree_bytes(directory)>limits['per_run_output_bytes']:
                receipt.update(status='failed',error='post-authentication per-run output limit')
                atomic(directory/'execution.json',receipt)
                raise spec.Invalid(receipt['error'])
            status['completed_run_ids'].append(run['id']);atomic(root/'status.json',status)
        require(digest(root/'manifest.json')==args.manifest_sha256,'archived manifest changed')
        for name,proof in manifest['schedules'].items():
            require(digest(root/'config'/name)==proof['sha256'],'archived schedule changed')
        require(digest(root/'approval.json')==args.approval_sha256 and load(root/'campaign.json')==ledger,'archived approval/ledger changed')
        auth.validate_build(root/'build.json',args.build_sha256,manifest)
        require(file_record(root/'provenance/build.log')==build['log']['file'],'archived build log changed')
        # Authenticate every receipt and pair BEFORE publishing any complete marker.
        for run in manifest['runs']:
            auth.base.authenticate_run(root/'runs'/run['id'],run,manifest,ledger,approval,digest(root/'runs'/run['id']/'execution.json'))
        for pair in manifest['pairing']:
            auth.compare_pair(root/'runs'/pair['off']/'output',root/'runs'/pair['on']/'output')
        require(time.monotonic()-start<=limits['aggregate_seconds'] and shared.tree_bytes(root)<=limits['aggregate_output_bytes'],'aggregate post-validation limit')
        status.update(status='completed',ended_utc=spec.utc(),wall_seconds=time.monotonic()-start);atomic(root/'status.json',status)
        atomic(root/'campaign_complete.pending.json',{'version':1,'status':'completed',
            'campaign_sha256':digest(root/'campaign.json'),'status_sha256':digest(root/'status.json'),
            'run_ids':[r['id'] for r in manifest['runs']],
            'receipts':{r['id']:digest(root/'runs'/r['id']/'execution.json') for r in manifest['runs']}})
        require(shared.tree_bytes(root)<=limits['aggregate_output_bytes'],'completion exceeds output budget')
        os.replace(root/'campaign_complete.pending.json',root/'campaign_complete.json')
    except BaseException as error:
        status.update(status='interrupted' if isinstance(error,(KeyboardInterrupt,SystemExit)) else 'failed',ended_utc=spec.utc(),error=str(error))
        atomic(root/'status.json',status);raise
    return {'status':'completed','root':str(root),'completion_sha256':digest(root/'campaign_complete.json')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action')
    b=subs.add_parser('build',help='fresh accepted-source double compilation only')
    b.add_argument('--source-tree',type=Path,required=True);b.add_argument('--build-root',type=Path,required=True)
    b.add_argument('--cuda-home',type=Path,required=True);b.add_argument('--arch',required=True)
    b.add_argument('--cxx',type=Path,default=Path('/usr/bin/g++'))
    p=subs.add_parser('preflight',help='read-only unless flag AND independent approval are supplied')
    for key in ('build-receipt','approval','output-root'):p.add_argument('--'+key,type=Path)
    for key in ('build-sha256','approval-sha256','gpu-uuid'):p.add_argument('--'+key)
    p.add_argument('--authorize-phase-a-execution',action='store_true')
    for child in (b,p):
        child.add_argument('--manifest',type=Path,default=spec.CONFIG/'manifest.json')
        child.add_argument('--manifest-sha256',default=(spec.CONFIG/'manifest.sha256').read_text().split()[0])
    if len(sys.argv)==1:sys.argv.append('preflight')
    args=parser.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    try:
        if args.action=='build':result=shared.build(args)
        elif args.action=='preflight':
            summary,manifest,build,approval,limits=preflight(args);print(json.dumps(summary,indent=2,allow_nan=False),flush=True)
            if not args.authorize_phase_a_execution:return
            require(not summary['blockers'] and approval is not None,'Phase A preflight blocked')
            with shared.gpu_lock(approval['gpu_uuid']):result=execute(args,summary,manifest,build,approval,limits)
        else:parser.print_help();return
        print(json.dumps(result,indent=2,allow_nan=False))
    except KeyboardInterrupt as error:parser.exit(130,f'Phase A interrupted; evidence preserved: {error}\n')
    except (OSError,ValueError,KeyError,TypeError,AssertionError,subprocess.SubprocessError) as error:
        parser.exit(1,f'Phase A refused: {error}\n')


if __name__=='__main__':main()
