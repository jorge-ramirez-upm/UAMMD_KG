#!/usr/bin/env python3
"""Local D1.6B A/B/C handoff. Readiness never starts the T100 campaign."""
import argparse
import datetime
import gzip
import hashlib
import io
import os
from pathlib import Path
import resource
import signal
import sys
import tarfile
import tempfile
import time

import e1_d16b_spec as spec
from e1_d15_local import write, load, proof, git, clean, command, local_env
from e1_d1_pilot import require, digest, file_record, encoded

REL=Path('examples/slip-springs')


def checked(root):
    root=spec.durable(root)
    session=load(root/'session.json');project=root/'preparation'/REL
    require(session['schema']=='e1-d16b-local-session-v1' and session['root']==str(root)
            and session['project']==str(project),'session/root mismatch')
    require(git(project,'rev-parse','HEAD')==session['commit'],'preparation revision changed')
    clean(project)
    require(session['sources']=={name:digest(project/name) for name in session['sources']}
            and session['sources']==spec.tool_hashes(),'preparation source closure changed')
    require(session['manifest']==proof(project/'e1_d16b_config/manifest.json'),'manifest changed')
    require(str(Path(sys.executable).resolve())==session['python'],'use original readiness Python')
    spec.validate_manifest(project/'e1_d16b_config/manifest.json',session['manifest']['sha256'])
    return session,project


def environment():
    # Actual dependency closure of both orchestration and exploratory inference.
    import e1_d16b_host
    import e1_d16b_analysis
    import e1_d16b_references
    from e1_d16a2_local import environment as snapshot
    return snapshot()


def verify_environment(root,project,name):
    output=root/'scratch'/(name+'.json')
    command(root,name,[sys.executable,project/'e1_d16b_local.py','_environment','--output',output],
            project,180,local_env(root))
    observed,expected=proof(output),proof(root/'environment.json')
    same=observed==expected
    retained=root/'environment.json' if same else root/(name+'-unexpected.json')
    if not same:
        require(not retained.exists(),'unexpected environment record already exists')
        output.rename(retained)
    write(root/(name+'.json'),{'matches_readiness':same,'observed':observed,'expected':expected,
                              'full_snapshot':str(retained)})
    require(same,'Python/scientific dependency environment changed')



def package(root,kind):
    require(kind in ('readiness','results'),'invalid return kind')
    require(not (root/'execution-running.json').exists(),'active/orphan execution marker: preserve, no packaging/resume')
    returns=root/'returns';returns.mkdir(exist_ok=True)
    payload={};inventory={}
    excluded={'preparation','source','scratch','returns'}
    for parent,dirs,files in os.walk(root,followlinks=False):
        parent=Path(parent)
        for name in dirs:require(not (parent/name).is_symlink(),'evidence directory symlink')
        if parent==root:dirs[:]=[d for d in dirs if d not in excluded]
        for name in sorted(files):
            path=parent/name;rel=str(path.relative_to(root))
            require(not path.is_symlink(),'evidence file symlink')
            # Build binaries and raw trajectories are hashed, never embedded.
            record=proof(path);inventory[rel]=dict(record,local_path=str(path))
            allowed=(path.suffix in ('.json','.jsonl','.stdout','.stderr','.md') or name=='build.log'
                     or name=='analysis.json.gz')
            if allowed:
                require(record['bytes']<=16*1024**2,'compact member exceeds 16 MiB; preserve evidence')
                payload[rel]=path.read_bytes()
    payload['contents.json']=encoded({'schema':'e1-d16b-return-inventory-v1','kind':kind,'root':str(root),'files':inventory,
        'integrity':'SHA256 detects changes, not adversarial replacement of all records; raw CSV retained locally'})
    payload['SUMMARY.md']=(f'D1.6B {kind}: exploratory only; no automatic D0 acceptance.\n'
        'Readiness: '+(load(root/'readiness.json')['status'] if (root/'readiness.json').exists() else 'INCOMPLETE')+'\n'
        'Original evidence: '+str(root)+'\n'
        'See stage-result records for incomplete, provenance, resource and correlation-support outcomes.\n').encode()
    payload['SHA256SUMS']=''.join(hashlib.sha256(body).hexdigest()+'  '+name+'\n'
        for name,body in sorted(payload.items())).encode()
    require(sum(map(len,payload.values()))<=32*1024**2,'compact return exceeds 32 MiB; no evidence dropped')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive=returns/f'd16b-{kind}-return-{stamp}.tar.gz'
    with archive.open('xb') as stream,tarfile.open(fileobj=stream,mode='w:gz') as tar:
        for name,body in sorted(payload.items()):
            info=tarfile.TarInfo(name);info.size=len(body);info.mode=0o600;tar.addfile(info,io.BytesIO(body))
    sidecar=Path(str(archive)+'.sha256')
    with sidecar.open('x') as stream:stream.write(digest(archive)+'  '+archive.name+'\n')
    print('UPLOAD',archive,flush=True);print('UPLOAD',sidecar,flush=True)
    return archive


def readiness(args):
    require(args.authorize_tiny_readiness_fixtures is True,'explicit local authorization for tiny readiness fixtures required')
    parent=spec.durable(args.evidence_parent)
    require(not any((a/'session.json').exists() for a in (parent,*parent.parents)),'do not nest inside existing evidence')
    require(not any((a/'.git').exists() for a in (parent,*parent.parents)),'evidence outside Git required')
    parent.mkdir(parents=True,exist_ok=True)
    root=Path(tempfile.mkdtemp(prefix='d16b-readiness-',dir=parent))
    print('D16B_ROOT='+str(root),flush=True)
    (root/'scratch').mkdir();(root/'logs').mkdir()
    env=local_env(root);state={'schema':'e1-d16b-readiness-v1','status':'FAILED','artifacts':{}}
    try:
        repo=spec.PROJECT.parents[1];clean(repo)
        require(git(repo,'branch','--show-current')=='slip-springs','use slip-springs branch')
        git(repo,'fetch','origin','slip-springs')
        commit=git(repo,'rev-parse','HEAD')
        require(commit==git(repo,'rev-parse','origin/slip-springs'),'HEAD differs from fetched tip')
        git(repo,'merge-base','--is-ancestor',spec.START,commit)
        spec.durable(git(repo,'rev-parse','--path-format=absolute','--git-common-dir'))
        for name,sha in (('preparation',commit),('source',spec.ACCEPTED_SHA)):
            command(root,'checkout-'+name,['git','-C',repo,'worktree','add','--detach',root/name,sha],repo,60,env)
        project=root/'preparation'/REL
        write(root/'session.json',{'schema':'e1-d16b-local-session-v1','root':str(root),'project':str(project),
            'commit':commit,'python':str(Path(sys.executable).resolve()),'sources':spec.tool_hashes(),
            'manifest':proof(project/'e1_d16b_config/manifest.json')})
        checked(root)
        for source,target in (('manifest.json','candidate-manifest.json'),('resources.json','resource-amendment.json'),
                              ('reference-lock.json','reviewed-reference-lock.json'),('performance-lock.json','performance-lock.json')):
            write(root/target,load(project/'e1_d16b_config'/source))
        command(root,'environment',[sys.executable,project/'e1_d16b_local.py','_environment','--output',root/'environment.json'],project,180,env)
        command(root,'deterministic-tests',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_e1_d16b.py','-v'],project,120,env)
        command(root,'reference-import',[sys.executable,project/'e1_d16b_local.py','_references','--output',root/'references.json'],project,600,env)
        command(root,'performance-import',[sys.executable,project/'e1_d16b_local.py','_performance','--output',root/'performance.json'],project,900,env)
        command(root,'build',[sys.executable,project/'e1_d16b_host.py','build','--source-tree',root/'source',
            '--build-root',root/'build','--cuda-home',spec.durable(args.cuda_home),'--arch','sm_86'],project,480,env)
        # Exact existing nine-step technical fixtures, never M256/T100 members.
        from e1_d16b_host import gpu_lock
        with gpu_lock():
            command(root,'preflight-before-fixtures',[sys.executable,project/'e1_d16b_host.py','preflight',
                '--root',root,'--output',root/'preflight-before-fixtures.json'],project,180,env)
            command(root,'tiny-gpu',[sys.executable,project/'tests/test_e1_d14_phase_b_technical.py',
                root/'build/bin/semiflexible'],project,120,env)
            command(root,'preflight',[sys.executable,project/'e1_d16b_host.py','preflight','--root',root,
                '--output',root/'preflight.json'],project,180,env)
        verify_environment(root,project,'environment-after-readiness')
        checked(root)
        state['status']='READY_FOR_INDEPENDENT_REVIEW'
    except BaseException as error:state['error']=str(error) or type(error).__name__
    for path in sorted((root/'logs').iterdir()):state['artifacts'][str(path)]=proof(path)
    for name in ('session.json','environment.json','references.json','performance.json','preflight.json','build/build.json','build/build.log',
                 'candidate-manifest.json','resource-amendment.json','reviewed-reference-lock.json','performance-lock.json'):
        path=root/name
        if path.is_file():state['artifacts'][str(path)]=proof(path)
    write(root/'readiness.json',state)
    if state['status']=='READY_FOR_INDEPENDENT_REVIEW':
        from e1_d16b_auth import approval_template
        write(root/'approval-template.json',approval_template(root))
    package(root,'readiness')
    require(state['status']=='READY_FOR_INDEPENDENT_REVIEW','readiness failed; return packet, no T100 execution')


def run(args):
    started=time.monotonic()
    require(args.execute_reviewed_t100 is True,'separate explicit T100 flag required')
    root=spec.durable(args.root);_,project=checked(root)
    approval_path=spec.durable(args.approval)
    require(digest(approval_path)==args.approval_sha256,'external approval SHA256 mismatch')
    from e1_d16b_auth import validate_approval
    validate_approval(load(approval_path),root,args.approval_sha256)
    require(not (root/'campaign').exists(),'campaign root already consumed')
    write(root/'launch.json',{'schema':'e1-d16b-local-launch-v1','approval_path':str(approval_path),
        'approval_sha256':args.approval_sha256,'readiness':proof(root/'readiness.json'),
        'started_utc':spec.utc(),'parent_pid':os.getpid()})
    write(root/'execution-running.json',{'pid':os.getpid()})
    result={'status':'INCOMPLETE','scientific_acceptance':None}
    try:
        verify_environment(root,project,'environment-before-execution')
        remaining=14400-(time.monotonic()-started)
        require(remaining>0,'aggregate wall budget exhausted before cohort launch')
        out=command(root,'campaign',[sys.executable,project/'e1_d16b_host.py','_execute','--root',root,
            '--approval',approval_path,'--approval-sha256',args.approval_sha256,'--execute-reviewed-t100'],
            project,remaining,local_env(root))
        result=load(out)
        result['local_campaign_wall_seconds']=time.monotonic()-started
        require(result['status']=='completed' and result['local_campaign_wall_seconds']<=14400,
                'cohort incomplete or entire local campaign wall budget exceeded')
    except BaseException as error:
        result.update(status='INCOMPLETE',error=str(error) or type(error).__name__,
                      local_campaign_wall_seconds=time.monotonic()-started)
        raise
    finally:
        write(root/'execution-result.json',result)
        (root/'execution-running.json').unlink()


def results(root):
    root=spec.durable(root);stamp=str(time.time_ns())
    outcome={'schema':'e1-d16b-results-v1','status':'INCOMPLETE','scientific_acceptance':None}
    try:
        _,project=checked(root)
        require(not (root/'execution-running.json').exists(),'active/interrupted execution; preserve marker for review')
        launch=load(root/'launch.json');result=load(root/'execution-result.json')
        require(result['status']=='completed','partial campaign; no complete-cohort inference')
        outcome['status']='NUMERICAL_OR_PROVENANCE_FAILURE'
        verify_environment(root,project,'environment-results-'+stamp)
        stage=root/('analysis-'+stamp);stage.mkdir()
        from e1_d16b_host import shared, environment
        limits={'per_run_seconds':7200,'aggregate_seconds':7200,'per_run_output_bytes':256*1024**2,
            'aggregate_output_bytes':256*1024**2,'max_host_rss_bytes':4*1024**3,'min_free_disk_bytes':10*1024**3}
        argv=[sys.executable,project/'e1_d16b_local.py','_analysis','--root',root,
              '--output',stage/'analysis.json.gz','--receipt',stage/'analysis-result.json']
        completed=shared.run_process(list(map(str,argv)),stage,environment(),limits,stage,time.monotonic())
        if completed['status'] not in ('exited','application_failure'):
            outcome['status']='RESOURCE_FAILURE'
        require(completed['status']=='exited' and completed['exit_code']==0,'analysis resource/provenance/numerical failure: '+completed['status'])
        outcome.update(load(stage/'analysis-result.json'))
    except BaseException as error:
        outcome['error']=str(error) or type(error).__name__
    write(root/f'results-{stamp}.json',outcome)
    package(root,'results')
    require(outcome['status']=='EXPLORATORY_COMPLETE','return incomplete/failure packet; no acceptance or automatic retry')


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    a=sub.add_parser('readiness');a.add_argument('--evidence-parent',type=Path,required=True)
    a.add_argument('--cuda-home',type=Path,default=Path('/usr/local/cuda'))
    a.add_argument('--authorize-tiny-readiness-fixtures',action='store_true',required=True)
    b=sub.add_parser('run');b.add_argument('--root',type=Path,required=True)
    b.add_argument('--approval',type=Path,required=True);b.add_argument('--approval-sha256',required=True)
    b.add_argument('--execute-reviewed-t100',action='store_true',required=True)
    for action in ('results','package-readiness'):
        child=sub.add_parser(action);child.add_argument('--root',type=Path,required=True)
    for action in ('_environment','_references','_performance','_analysis'):
        child=sub.add_parser(action);child.add_argument('--output',type=Path,required=True)
        if action=='_analysis':
            child.add_argument('--root',type=Path,required=True);child.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    if args.action=='readiness':readiness(args)
    elif args.action=='run':run(args)
    elif args.action=='results':results(args.root)
    elif args.action=='package-readiness':checked(args.root);package(args.root,'readiness')
    elif args.action=='_environment':write(args.output,environment())
    elif args.action=='_references':
        from e1_d16b_references import import_moments
        write(args.output,import_moments())
    elif args.action=='_performance':
        from e1_d16b_references import import_performance
        write(args.output,import_performance())
    else:
        from e1_d16b_analysis import analyze
        launch=load(args.root/'launch.json');result=load(args.root/'execution-result.json')
        write(args.receipt,analyze(args.root/'campaign',args.output,launch['approval_sha256'],result['completion_sha256']))


if __name__=='__main__':main()
