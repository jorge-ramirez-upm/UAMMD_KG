#!/usr/bin/env python3
"""User-operated D1.5 preparation/build/preflight; no implicit execution/approval."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import signal
import subprocess

import e1_d15_prepare as spec
import e1_d15_auth as auth
from e1_d13_reuse import bind
from e1_d1_pilot import require

# Private bindings retain accepted build, environment, supervision and output checks.
definition=importlib.util.spec_from_file_location('_d15_accepted_orchestration',spec.PROJECT/'e1_d13_phase_a_runner.py')
accepted=importlib.util.module_from_spec(definition);definition.loader.exec_module(accepted)
accepted.spec=spec;accepted.auth=auth
accepted.shared=bind('runner',spec);accepted.shared.auth=auth.base
accepted._machine=accepted.shared.machine
accepted.shared.machine=accepted.machine
shared=accepted.shared
_validate_approval=shared.validate_approval


def validate_approval(value,manifest_sha,build_sha,root,env_sha):
    manifest=spec.validate_manifest(CURRENT_MANIFEST,manifest_sha)
    auth.approval_reviews(value,manifest)
    return _validate_approval({k:v for k,v in value.items() if k not in auth.REVIEW_FIELDS},
                             manifest_sha,build_sha,root,env_sha)


shared.validate_approval=validate_approval
CURRENT_MANIFEST=None


def require_bounded(manifest):
    require(manifest['kind'] in ('benchmark','pilot') and manifest['execution_supported'] is True,
            'T=100 and larger-M designs need a new execution protocol; no bypass flag')


def preflight(args):
    require_bounded(spec.validate_manifest(args.manifest,args.manifest_sha256))
    summary,*rest=accepted.preflight(args)
    summary['execution_flag_required']='--authorize-d15-local-execution'
    summary['preparation_only_in_codex']=True
    return summary,*rest


def execute(args,summary,manifest,build,approval,limits):
    require(args.authorize_d15_local_execution is True,'separate explicit local execution flag required')
    require_bounded(manifest)
    require(not summary['blockers'] and approval is not None,'D1.5 execution blocked')
    auth.approval_reviews(approval,manifest)
    bound=copy.copy(args);bound.authorize_phase_a_execution=True
    result=accepted.execute(bound,summary,manifest,build,approval,limits)
    # Never return a completion trust anchor before new review gates and the
    # entire inherited evidence/receipt closure have authenticated again.
    auth.authenticate_campaign(result['root'],args.manifest,args.manifest_sha256,
                               args.approval_sha256,result['completion_sha256'])
    return result


def summarize(args):
    manifest,items=auth.authenticate_campaign(args.root,args.manifest,args.manifest_sha256,
                                              args.approval_sha256,args.completion_sha256)
    result={'schema':'e1-d15-observed-performance-v1','kind':manifest['kind'],
            'scientific_acceptance':None,'independent_replicas_per_cell':1,'runs':[]}
    for item in items:
        run=item['run']
        # Raw input locations derive from authenticated canonical run identities.
        root=Path(args.root)/'runs'/run['id']/'output'
        meta=spec.load(root/'metadata.json');observer=spec.load(root/'equilibrium_complete.json')
        hop=spec.load(root/'hopping_metadata.json');receipt=item['receipt']
        production=meta['production_wall_seconds']
        serialized={}
        for name,proof in receipt['output_files'].items():
            if not name.endswith('.csv'):continue
            count=spec.row_counts(run)[name]
            with (root/name).open('rb') as stream:header_bytes=len(stream.readline())
            serialized[name]=dict(proof,rows=count,data_bytes=proof['bytes']-header_bytes,
                mean_row_bytes=(proof['bytes']-header_bytes)/count if count else None)
        result['runs'].append({'run':run,'metadata':meta,'observer':observer,
            'hopping':hop,'child_wall_seconds':receipt['wall_seconds'],
            'peak_host_rss_bytes':receipt['max_rss_bytes'],
            'accepted_events_per_production_second':(hop['accepted']+hop['renewal_accepted'])/production,
            'raw_output_bytes':sum(r['bytes'] for r in receipt['output_files'].values()),
            'csv_serialization':serialized})
    auth.authenticate_campaign(args.root,args.manifest,args.manifest_sha256,args.approval_sha256,args.completion_sha256)
    out=spec.output_path(args.report)
    require(not out.exists() and out.parent.is_dir(),'fresh report path with existing parent required')
    require(not out.is_relative_to(Path(args.root).resolve()),'report must remain outside raw evidence')
    with out.open('xb') as stream:stream.write(spec.encoded(result))
    return {'report':str(out),'sha256':spec.digest(out),'scientific_acceptance':None}


def main():
    global CURRENT_MANIFEST
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action')
    b=subs.add_parser('build',help='LOCAL ONLY: fresh pinned-source compilation, no simulation')
    for name in ('source-tree','build-root','cuda-home'):b.add_argument('--'+name,type=Path,required=True)
    b.add_argument('--arch',required=True);b.add_argument('--cxx',type=Path,default=Path('/usr/bin/g++'))
    p=subs.add_parser('preflight',help='read-only unless flag AND independently approved record supplied')
    for name in ('build-receipt','approval','output-root'):p.add_argument('--'+name,type=Path)
    for name in ('build-sha256','approval-sha256','gpu-uuid'):p.add_argument('--'+name)
    p.add_argument('--authorize-d15-local-execution',action='store_true')
    a=subs.add_parser('summarize',help='authenticate completed bounded cohort; never runs simulations')
    for name in ('root','report'):a.add_argument('--'+name,type=Path,required=True)
    for name in ('approval-sha256','completion-sha256'):a.add_argument('--'+name,required=True)
    for child in (b,p,a):
        child.add_argument('--manifest',type=Path,required=True)
        child.add_argument('--manifest-sha256',required=True)
    args=parser.parse_args()
    if args.action is None:parser.print_help();return
    CURRENT_MANIFEST=args.manifest
    def stop(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGHUP,stop)
    try:
        manifest=spec.validate_manifest(args.manifest,args.manifest_sha256);require_bounded(manifest)
        if args.action=='build':result=shared.build(args)
        elif args.action=='summarize':result=summarize(args)
        else:
            summary,manifest,build,approval,limits=preflight(args)
            print(json.dumps(summary,indent=2,allow_nan=False),flush=True)
            if not args.authorize_d15_local_execution:return
            require(not summary['blockers'] and approval is not None,'D1.5 preflight blocked')
            with shared.gpu_lock(approval['gpu_uuid']):result=execute(args,summary,manifest,build,approval,limits)
        print(json.dumps(result,indent=2,allow_nan=False))
    except KeyboardInterrupt as error:parser.exit(130,f'D1.5 interrupted; preserve evidence: {error}\n')
    except (OSError,ValueError,KeyError,TypeError,AssertionError,subprocess.SubprocessError) as error:
        parser.exit(1,f'D1.5 refused: {error}\n')


if __name__=='__main__':main()
