"""Authenticated, resumable host management. No execution without explicit flag.

Generate with the unchanged semiflexible_stress_host.py first. See --help.
"""
import argparse
import contextlib
import datetime
import fcntl
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tempfile
import time

import numpy as np
import semiflexible_stress_analysis as science

PROJECT=science.PROJECT
VERSION=1


def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=science.encoded(value)+b'\n'
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.'+path.name,delete=False) as f:
        tmp=Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def envelope(path,value):
    atomic(path,dict(payload=value,sha256=science.identity(value)))


def unenvelope(path):
    obj=science.load(path)
    science.require(set(obj)=={'payload','sha256'} and obj['sha256']==science.identity(obj['payload']),'corrupted checkpoint/reference envelope: '+str(path))
    return obj['payload']


@contextlib.contextmanager
def lock(root,name='.execution.lock'):
    with open(root/name,'a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)


def version():
    return science.identity(dict(version=VERSION,numpy=np.__version__,files={str(p.relative_to(PROJECT)):science.digest(p) for p in
        [Path(__file__),Path(science.__file__),PROJECT/'semiflexible_reference.py',PROJECT/'semiflexible_stress_reference.py',PROJECT/'stream_analysis.py',PROJECT/'tests/semiflexible_stress_host.py']}))


def stat(path):
    s=path.stat()
    return dict(size=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,inode=s.st_ino)


def run_files(run):
    out=Path(run['output'])
    paths=sorted(p for p in out.rglob('*') if p.is_file()) if out.exists() else []
    paths += [p for p in out.parent.glob(out.name+'.*') if p.is_file()]
    return paths


def fingerprints(run,hashes=True):
    return {str(p):dict(stat=stat(p),**({'sha256':science.digest(p)} if hashes else {})) for p in run_files(run)}


def unchanged(run,previous,verify=False,skip_receipt=False):
    now=fingerprints(run,hashes=False)
    if skip_receipt:now.pop(run['output']+'.execution.json',None)
    if set(now)!=set(previous):return False
    for name,value in now.items():
        if value['stat']!=previous[name]['stat']:return False
        if verify and science.digest(Path(name))!=previous[name]['sha256']:return False
    return True


_BINARY_HASHES={}
def binary_digest(path):
    key=(str(path),tuple(stat(Path(path)).values()))
    if key not in _BINARY_HASHES:_BINARY_HASHES[key]=science.digest(path)
    return _BINARY_HASHES[key]

def command_output(argv):
    try:
        p=subprocess.run(argv,capture_output=True,text=True,timeout=15)
        return dict(command=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
    except (OSError,subprocess.TimeoutExpired) as e:
        return dict(command=argv,unavailable=str(e))


def provenance(root,manifest,manifest_hash,build_log=None):
    path=root/'campaign-provenance.json'
    binaries={r['precision']:r['command'][0] for r in manifest}
    ids={key:dict(path=value,sha256=science.digest(value)) for key,value in binaries.items()}
    if path.exists():
        p=unenvelope(path)
        science.require(p['manifest_hash']==manifest_hash and p['plan_hash']==science.PLAN_HASH and p['executables']==ids,'campaign executable identity or provenance changed; do not mix binaries')
        if build_log:science.require(p.get('build_transcript',{}).get('sha256')==science.digest(build_log),'supply an original build transcript on the first provenance capture; existing ledger is immutable')
        git_now=command_output(['git','-C',str(PROJECT),'rev-parse','HEAD'])
        dirty_now=command_output(['git','-C',str(PROJECT),'status','--porcelain','--untracked-files=no'])
        science.require(git_now.get('stdout','').strip()==p['repository_sha'] and dirty_now.get('exit_code')==0 and not dirty_now['stdout'],'execution checkout changed since campaign provenance was frozen')
        return p
    git=command_output(['git','-C',str(PROJECT),'rev-parse','HEAD'])
    dirty=command_output(['git','-C',str(PROJECT),'status','--porcelain','--untracked-files=no'])
    science.require(git.get('exit_code')==0 and dirty.get('exit_code')==0 and not dirty['stdout'],'execution requires a clean versioned repository')
    p=dict(manifest_hash=manifest_hash,plan_hash=science.PLAN_HASH,executables=ids,repository_sha=git['stdout'].strip(),
           timestamp_utc=utc(),platform=platform.platform(),python=sys.version,numpy=np.__version__,
           environment={k:os.environ.get(k) for k in ('CUDA_VISIBLE_DEVICES','PATH','LD_LIBRARY_PATH','OMP_NUM_THREADS')},
           accepted_sources=science.ACCEPTED_SOURCE_HASHES,
           gpu=command_output(['nvidia-smi']),system_nvcc=command_output(['nvcc','--version']),
           compiler_identity='unknown unless an archived build transcript establishes compilation; system nvcc is not compiler proof')
    if build_log:
        import shutil
        target=root/'compiler-build-transcript.txt'
        science.require(not target.exists(),'build transcript already exists without ledger')
        shutil.copyfile(build_log,target);p['build_transcript']=dict(path=str(target),sha256=science.digest(target))
    envelope(path,p);return p


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def provenance_checks(root,run,rid,manifest_hash):
    checks=[];ledger=root/'campaign-provenance.json';record=Path(run['output']+'.execution.json')
    if not ledger.exists() or not record.exists():
        return [dict(name='execution/executable provenance',status='missing_provenance',reason='original command exit record and executable ledger unavailable')]
    p=unenvelope(ledger);r=unenvelope(record)
    science.require(p['manifest_hash']==manifest_hash and p['plan_hash']==science.PLAN_HASH,'provenance campaign identity mismatch')
    science.require(p.get('accepted_sources')==science.ACCEPTED_SOURCE_HASHES,'missing/inconsistent accepted simulator source identities')
    science.require(r['manifest_hash']==manifest_hash and r['run_id']==rid and r['command']==run['command'],'execution command/run identity mismatch')
    science.require(r['status']=='completed' and r['exit_code']==0,'execution failed or incomplete')
    for name,proof in r.get('completion_files',{}).items():
        target=Path(name)
        science.require(target.exists(),'recorded completed file is absent: '+name)
        if stat(target)!=proof['stat']:science.require(science.digest(target)==proof['sha256'],'completed file hash mismatch: '+name)
    science.require(r.get('completion_files'),'missing completion file identities')
    binary=Path(run['command'][0])
    if binary.exists():science.require(binary_digest(binary)==r['executable_sha256'],'current executable differs from original receipt')
    science.require(r['executable_sha256']==p['executables'][run['precision']]['sha256'],'execution executable identity mismatch')
    science.require(math_finite_nonnegative(r['wall_seconds']) and r['finished_utc']>=r['started_utc'],'inconsistent execution times')
    science.require(isinstance(p.get('repository_sha'),str) and len(p['repository_sha'])==40,'missing repository SHA')
    if not p.get('build_transcript'):
        checks.append(dict(name='original compilation toolkit',status='missing_provenance',reason='no original build transcript; system nvcc does not establish compiler identity'))
    else:
        b=p['build_transcript'];science.require(science.digest(b['path'])==b['sha256'],'build transcript identity mismatch')
        checks.append(dict(name='original compilation toolkit',status='review_required',reason='archived transcript requires inspection; a no-op build is not compilation evidence'))
    checks.append(dict(name='recorded execution identity',status='passed',repository_sha=p['repository_sha'],executable_sha256=r['executable_sha256']))
    return checks


def math_finite_nonnegative(value):
    return isinstance(value,(float,int)) and np.isfinite(value) and value>=0


def reference_catalog(root,manifest_hash=None):
    path=root/'equilibrium-references.json'
    if not path.exists():return {}
    p=unenvelope(path)
    science.require(p['analysis_version']==version() and p['plan_hash']==science.PLAN_HASH,'CPU reference analysis version/plan mismatch')
    if manifest_hash is not None:science.require(p['manifest_hash']==manifest_hash,'CPU reference manifest mismatch')
    for key,ref in p['references'].items():
        science.require(key==ref['key'] and ref['count']==65536 and all(ref['statistics'][k]['count']==65536 for k in ('mean','products','covariance')),'CPU reference ensemble identity/count mismatch')
        m=ref['parameters'];model=science.Chain(m['b0'],m['kb'],m['kappa'])
        science.require(science.model_key(model,ref['kbt'])==key,'CPU reference parameters mismatch')
    return p['references']


def prepare_references(root,manifest,manifest_hash):
    path=root/'equilibrium-references.json';refs=reference_catalog(root,manifest_hash)
    for i,run in enumerate(manifest):
        if run['phase'] not in ('diagnostic','reference'):continue
        o=science.options(run);model=science.model_file(o['parameters']);temp=float(o['kbt']);key=science.model_key(model,temp)
        if key in refs:continue
        print('CPU independent equilibrium ensemble',run['label'],'kBT',temp,flush=True)
        refs[key]=science.equilibrium_reference(model,temp,seed=433301+i)
        envelope(path,dict(analysis_version=version(),plan_hash=science.PLAN_HASH,manifest_hash=manifest_hash,references=refs))


def prerequisite_checks(root,manifest):
    path=root/'bounded-prerequisites.json'
    if not path.exists():return [dict(name='bounded geometry/replay prerequisites',status='missing_provenance')]
    p=unenvelope(path)
    science.require(p['analysis_version']==version(),'bounded prerequisite version changed')
    for precision in ('single','double'):
        item=p['checks'][precision]
        science.require(item['exit_code']==0 and science.digest(item['log'])==item['log_sha256'],'bounded prerequisite failure or log corruption')
        binary=next(r['command'][0] for r in manifest if r['precision']==precision)
        science.require(science.digest(binary)==item['binary_sha256'],'bounded prerequisite executable changed')
    return [dict(name='bounded geometry/replay prerequisites',status='passed')]


def analyze(root,manifest,ids,manifest_hash,verify=False,selected=None):
    root=Path(root);cache=root/'analysis-checkpoint.json';stamp=version();previous={}
    if cache.exists():
        p=unenvelope(cache)
        science.require(p['manifest_hash']==manifest_hash and p['plan_hash']==science.PLAN_HASH,'checkpoint manifest/plan mismatch')
        if p['analysis_version']==stamp:previous=p['runs']
    references=reference_catalog(root,manifest_hash);records={};results={};reused=0
    for run,rid in zip(manifest,ids):
        if selected is not None and rid not in selected:
            continue
        record=previous.get(rid)
        receipt=Path(run['output']+'.execution.json')
        execution_state=unenvelope(receipt) if receipt.exists() else {}
        failures=list(Path(run['output']).glob('*failure*'))
        pending=execution_state.get('status')=='running' or not (Path(run['output'])/'metadata.json').exists()
        if execution_state.get('status')=='failed' or failures:
            evidence=failures+([receipt] if receipt.exists() else [])
            result=dict(checks=[dict(name='execution/numerical failure',status='failed',reason='failure record present; this is not an unfinished successful run')],failure_evidence={str(p):science.digest(p) for p in evidence if p.is_file()})
            record=dict(files={},result=result)
        elif pending:
            result=dict(checks=[dict(name='complete outputs',status='missing_data',reason='not completed; live/absent outputs are not accepted or scanned')])
            record=dict(files={},result=result)
        elif record and unchanged(run,record['files'],verify):
            result=record['result'];reused+=1
        else:
            before=fingerprints(run,hashes=False)
            try:
                result=science.validate_run(run)
                if run['phase']=='memory':
                    result['memory']=science.memory_observation(run,result);result['checks']+=result['memory']['checks']
                # Execution provenance is rechecked below even when expensive science is cached.
            except FileNotFoundError as e:
                result=dict(checks=[dict(name='complete outputs',status='missing_data',reason=str(e))])
            except (ValueError,KeyError,TypeError,OverflowError) as e:
                result=dict(checks=[dict(name='input/numerical validation',status='failed',reason=str(e))])
            after=fingerprints(run,hashes=True)
            science.require({k:v['stat'] for k,v in before.items()}=={k:v['stat'] for k,v in after.items()},'run files changed during analysis: '+run['output'])
            record=dict(files=after,result=result)
        records[rid]=record
        results[rid]={**result,'checks':list(result['checks'])}
        if 'metadata' in result:
            try:results[rid]['checks']+=provenance_checks(root,run,rid,manifest_hash)
            except (ValueError,KeyError,FileNotFoundError) as e:results[rid]['checks'].append(dict(name='execution provenance',status='failed',reason=str(e)))
        # Each completed run is durable before the next potentially expensive read.
        envelope(cache,dict(manifest_hash=manifest_hash,plan_hash=science.PLAN_HASH,analysis_version=stamp,runs={**previous,**records}))
    extra=[]
    try:
        extra+=science.campaign_comparisons(manifest,ids,results,references)
        extra+=prerequisite_checks(root,manifest)
    except (ValueError,KeyError,FileNotFoundError) as e:
        extra.append(dict(name='campaign evidence consistency',status='failed',reason=str(e)))
    report=dict(manifest_hash=manifest_hash,plan_hash=science.PLAN_HASH,analysis_version=stamp,generated_utc=utc(),
                expected_runs=282,analyzed_runs=len(records),reused_runs=reused,runs=results,campaign_checks=extra)
    checks=[g for r in results.values() for g in r['checks']]+extra
    statuses={s:sum(g['status']==s for g in checks) for s in sorted({g['status'] for g in checks})}
    if len(records)!=282:statuses['not_analyzed_runs']=282-len(records)
    report['status_counts']=statuses
    aggregates={}
    for run,rid in zip(manifest,ids):
        result=results.get(rid,{})
        if run['phase']=='memory' and 'performance' in result:
            group=run['precision']+'/steps'+str(result['metadata']['steps'])
            aggregates.setdefault(group,[]).append(result['performance'])
    report['memory_timing_replica_summary']={}
    for group,items in aggregates.items():
        metrics={}
        for key in items[0]:
            values=[p[key] for p in items]
            if all(isinstance(v,(int,float)) for v in values):metrics[key]=dict(mean=float(np.mean(values)),spread_std=float(np.std(values,ddof=1)) if len(values)>1 else None,minimum=min(values),maximum=max(values))
        report['memory_timing_replica_summary'][group]=dict(replicas=len(items),metrics=metrics)
    report['scientific_status']='passed' if statuses and all(s in ('passed','statistically_unresolved_bias') for s in statuses) else 'failed' if statuses.get('failed') else 'incomplete'
    report['overall_status']=report['scientific_status']
    scientific={s:n for s,n in statuses.items() if s not in ('missing_provenance','review_required')}
    report['scientific_status']='passed' if scientific and all(s in ('passed','statistically_unresolved_bias') for s in scientific) else 'failed' if scientific.get('failed') else 'incomplete'
    report['convergence_order']='not measured; unresolved bias is not evidence of an order'
    atomic(root/'scientific-analysis.json',report)
    lines=['Stage 4A.3c host analysis: '+report['overall_status'].upper(),f'Runs {len(records)}/282; reused {reused}',str(statuses),'Scientific gates: '+report['scientific_status'],report['convergence_order'],
           'No density assigned; raw products; independent-chain clusters; no tail fitting.']
    for rid,result in results.items():
        for gate in result['checks']:
            if gate['status'] not in ('passed','statistically_unresolved_bias'):
                lines.append(rid[:12]+' '+gate['status']+' '+gate['name']+': '+gate.get('reason',''))
    for g in extra:
        if g['status'] not in ('passed','statistically_unresolved_bias'):lines.append(g['status']+' '+g['name']+': '+g.get('reason',''))
    if len(lines)>45:lines=lines[:45]+['Further details are retained in scientific-analysis.json.']
    (root/'scientific-summary.txt').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[:5]));return report


def proc_rss(pid):
    """Sum live process-tree RSS; do not sum per-thread RSS multiple times."""
    try:
        children=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
        rss=next(int(line.split()[1]) for line in Path(f'/proc/{pid}/status').read_text().splitlines() if line.startswith('VmRSS:'))
        return rss+sum(proc_rss(int(p)) for p in children)
    except (OSError,StopIteration):return 0


def execute_one(root,run,rid,manifest_hash,ledger,verify=False):
    out=Path(run['output']);record_path=Path(str(out)+'.execution.json')
    if out.exists() or record_path.exists():
        science.require(out.exists() and record_path.exists(),'partial output exists; preserve it and investigate, never overwrite')
        record=unenvelope(record_path)
        science.require(record['status']=='completed' and record['exit_code']==0 and record['command']==run['command'] and record['run_id']==rid and record['manifest_hash']==manifest_hash,'partial/failed execution record; no automatic overwrite')
        science.require(record['executable_sha256']==ledger['executables'][run['precision']]['sha256'],'completed run binary identity mismatch')
        science.require(unchanged(run,record['completion_files'],verify=verify,skip_receipt=True),'completed run output identities changed')
        print('verified completed; skip',rid[:12],out.name);return
    science.require(not run_files(run),'orphan execution/monitor evidence exists; preserve it, never overwrite')
    science.require(science.digest(run['command'][0])==ledger['executables'][run['precision']]['sha256'],'executable changed before launch')
    start=time.monotonic();record=dict(run_id=rid,manifest_hash=manifest_hash,command=run['command'],started_utc=utc(),status='running',
                                     executable_sha256=ledger['executables'][run['precision']]['sha256'])
    envelope(record_path,record)
    try:
        with open(str(out)+'.log','x') as log,open(str(out)+'.monitor.csv','x') as monitor,open(str(out)+'.gpu.csv','x') as gpu,open(str(out)+'.disk.csv','x') as disk:
            disk.write('elapsed_seconds,scalar_csv_bytes,output_bytes\n')
            monitor.write('elapsed_seconds,cpu_rss_kib,production_observed\n');gpu.write('timestamp, memory.used [MiB],production_observed\n')
            # /usr/bin/time wraps, but does not alter, the exact original argv.
            child=subprocess.Popen(['/usr/bin/time','-v','-o',str(out)+'.time']+run['command'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                while child.poll() is None:
                    active=int((out/'samples.csv').exists() and (out/'samples.csv').stat().st_size>0)
                    monitor.write(f'{time.monotonic()-start:.9f},{proc_rss(child.pid)},{active}\n');monitor.flush()
                    scalar=out/'samples.csv';total=sum(p.stat().st_size for p in out.iterdir() if p.is_file()) if out.exists() else 0
                    disk.write(f'{time.monotonic()-start:.9f},{scalar.stat().st_size if scalar.exists() else 0},{total}\n');disk.flush()
                    query=command_output(['nvidia-smi','--query-gpu=timestamp,memory.used','--format=csv,noheader','--id='+os.environ.get('CUDA_VISIBLE_DEVICES','0').split(',')[0]])
                    if query.get('exit_code')==0:
                        gpu.write(''.join(line.rstrip()+','+str(active)+'\n' for line in query['stdout'].splitlines()));gpu.flush()
                    time.sleep(1)
            except BaseException:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                raise
            code=child.returncode
        record.update(exit_code=code,wall_seconds=time.monotonic()-start,finished_utc=utc(),status='failed')
        science.require(code==0,'execution failed, see '+str(out)+'.log')
        science.validate_run(run)  # completeness, not scientific acceptance
        record['status']='completed'
        # Exclude the self-referential execution receipt from its own fingerprint.
        files=fingerprints(run);files.pop(str(record_path),None);record['completion_files']=files
        envelope(record_path,record)
    except BaseException as e:
        record.update(status='failed',finished_utc=utc(),wall_seconds=time.monotonic()-start,error=str(e))
        envelope(record_path,record);raise
    print('completed',out.name,'wall_seconds',record['wall_seconds'])


def pilot(manifest,ids,diagnostic=False):
    pairs=[(r,i) for r,i in zip(manifest,ids) if r['phase']==('diagnostic' if diagnostic else 'stream') and r['label']=='finite-N8-k10' and r['precision']=='single' and r.get('seed')==433201 and science.options(r)['dt']=='2.5e-05']
    science.require(len(pairs)==1,'frozen pilot identity missing')
    return pairs[0]


def pilot_report(root,manifest,ids):
    run,rid=pilot(manifest,ids);out=Path(run['output']);receipt=unenvelope(Path(str(out)+'.execution.json'))
    science.require(receipt['status']=='completed' and receipt['run_id']==rid and receipt['command']==run['command'],'pilot is not complete or identity differs')
    pilot_provenance=provenance_checks(root,run,rid,science.identity(manifest))
    result=science.validate_run(run);opts=science.options(run)
    diagnostic,diagnostic_id=pilot(manifest,ids,diagnostic=True)
    diagnostic_result=science.validate_run(diagnostic)
    pilot_provenance+=provenance_checks(root,diagnostic,diagnostic_id,science.identity(manifest))
    rows=(int(opts['steps'])//int(opts['sample'])+1)*int(opts['chains'])
    wall=receipt['wall_seconds'];disk=result['disk_bytes']
    growth=[];previous=-1.
    for row in science.rows(Path(str(out)+'.disk.csv'),('elapsed_seconds','scalar_csv_bytes','output_bytes')):
        t=science.number(row,'elapsed_seconds');size=science.number(row,'output_bytes',True)
        science.require(t>previous and size>=0,'invalid disk-growth monitor')
        if not growth:growth.append(dict(seconds=t,bytes=size))
        elif len(growth)==1:growth.append(dict(seconds=t,bytes=size))
        else:growth[1]=dict(seconds=t,bytes=size)
        previous=t
    seconds_per_step=result['metadata']['integration_seconds']/int(opts['steps'])
    overhead_per_frame=max(0,result['metadata']['production_wall_seconds']-result['metadata']['integration_seconds'])/result['stress_metadata']['frames']
    same_system=[];disk_projection=[]
    row_bytes=(out/'samples.csv').stat().st_size/rows
    for item in manifest:
        o=science.options(item);steps=int(o['steps']);frames=steps//int(o['sample'])+1
        disk_projection.append(dict(output=item['output'],estimated_scalar_csv_bytes=row_bytes*frames*int(o['chains'])))
        if item['phase']=='stream' and item['label']==run['label'] and item['precision']==run['precision']:
            same_system.append(dict(output=item['output'],estimated_production_seconds=seconds_per_step*steps+overhead_per_frame*frames))
    report=dict(run_id=rid,exact_command=run['command'],measured_wall_seconds=wall,measured_output_bytes=disk,observed_disk_growth_endpoints=growth,
                scalar_observation_rows=rows,bytes_per_scalar_row=row_bytes,estimated_same_system_production=same_system,
                estimated_campaign_scalar_bytes=sum(x['estimated_scalar_csv_bytes'] for x in disk_projection),disk_estimate_assumption='Pilot scalar CSV bytes/row applied to manifest row counts; other models can differ; reserve at least twice this rough projection plus logs and other outputs',
                estimated_same_configuration_seconds_per_million_steps=wall/int(opts['steps'])*1e6,
                timing=result['performance'],provenance=pilot_provenance,independent_diagnostic=dict(run_id=diagnostic_id,checks=diagnostic_result['checks'],virials=diagnostic_result['virial_statistics']),limitations='Measured full frozen pilot only. Extrapolations apply approximately to identical N/precision/cadence; not a nonlinear terminal claim or other-model benchmark.')
    atomic(root/'pilot-readiness.json',report);print(science.encoded(report).decode())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('campaign',type=Path);p.add_argument('action',choices=['list','analyze','references','run','pilot-report','prerequisites'])
    p.add_argument('--phase',choices=['stream','diagnostic','reference','memory']);p.add_argument('--pilot',action='store_true');p.add_argument('--run-id')
    p.add_argument('--authorize-host-execution',choices=['STAGE4A3C']);p.add_argument('--verify-hashes',action='store_true');p.add_argument('--build-log',type=Path)
    args=p.parse_args();root=args.campaign.resolve();safe_root=False
    try:
        from semiflexible_stress_host import safe
        safe(root);safe_root=True
        with lock(root,'.analysis.lock' if args.action=='analyze' else '.inspection.lock' if args.action in ('list','pilot-report') else '.execution.lock'):
            manifest,ids,mhash=science.authenticate(root)
            selected=[(r,i) for r,i in zip(manifest,ids) if (not args.phase or r['phase']==args.phase) and (not args.run_id or i==args.run_id)]
            if args.pilot:
                science.require(args.phase in (None,'stream','diagnostic'),'pilot supports diagnostic or stream phase')
                selected=[pilot(manifest,ids,args.phase=='diagnostic')]
            science.require(selected,'no matching runs')
            science.require(not (args.pilot and args.run_id),'choose --pilot or --run-id, not both')
            if args.action in ('references','prerequisites','pilot-report'):science.require(not(args.pilot or args.phase or args.run_id),'selection flags do not apply to this action')
            if args.action=='list':
                for run,rid in selected:print(rid,run['phase'],Path(run['output']).name)
            elif args.action=='analyze':
                report=analyze(root,manifest,ids,mhash,args.verify_hashes,{i for _,i in selected})
                return 0 if report['overall_status']=='passed' else 1 if report['overall_status']=='failed' else 2
            elif args.action=='pilot-report':pilot_report(root,manifest,ids)
            else:
                science.require(args.authorize_host_execution=='STAGE4A3C','explicit user-host execution authorization flag required; no run started')
                if args.action=='references':prepare_references(root,manifest,mhash)
                else:
                    ledger=provenance(root,manifest,mhash,args.build_log)
                    if args.action=='run':
                        for run,rid in selected:execute_one(root,run,rid,mhash,ledger,args.verify_hashes)
                    elif args.action=='prerequisites':
                        if (root/'bounded-prerequisites.json').exists():
                            prerequisite_checks(root,manifest);print('verified bounded prerequisites; skip');return 0
                        fixture=PROJECT/'build/semiflexible_stress_correlator'
                        checks={}
                        for precision in ('single','double'):
                            binary=ledger['executables'][precision]['path'];other=ledger['executables']['double' if precision=='single' else 'single']['path']
                            log=root/f'bounded-{precision}.log';science.require(not log.exists(),'bounded evidence already exists')
                            argv=[sys.executable,str(PROJECT/'tests/test_semiflexible_stress_gpu.py'),binary,str(fixture),other]
                            with open(log,'x') as f:cp=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
                            science.require(cp.returncode==0,'bounded prerequisites failed')
                            checks[precision]=dict(exit_code=cp.returncode,command=argv,log=str(log),log_sha256=science.digest(log),binary_sha256=science.digest(binary))
                        envelope(root/'bounded-prerequisites.json',dict(analysis_version=version(),checks=checks))
        return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as e:
        if safe_root and root.is_dir():
            try:atomic(root/'readiness-refusal.json',dict(status='refused',action=args.action,reason=str(e),timestamp_utc=utc(),
                manifest_sha256=science.digest(root/'manifest.json') if (root/'manifest.json').exists() else None,
                observed_plan_sha256=science.digest(root/'validation-plan.md') if (root/'validation-plan.md').exists() else None))
            except OSError:pass
        print('REFUSED:',e,file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
