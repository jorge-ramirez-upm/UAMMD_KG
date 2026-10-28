"""Authenticated serial D2A.5 campaign preparation; no execution on import."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import struct
import sys
import time

from e1_d1_pilot import atomic, capture, digest, file_record, require, utc
from e1_d1_pilot_runner import environment, host_available, resource_check, run_process, tree_bytes
from e1_d2a3_run import exported_grid, gpu_state, inventory
from e1_d2a5_validate import finite_json, validate_output

PROJECT = Path(__file__).resolve().parent


def authenticate(config, pin):
    require(sys.platform == 'linux' and struct.calcsize('L') == 8 and struct.calcsize('P') == 8,
            '64-bit Linux/LP64 required')
    require(digest(config/'manifest.json') == pin and
            (config/'manifest.sha256').read_text().split()[0] == pin, 'manifest identity')
    manifest = finite_json(config/'manifest.json')
    for name, expected in manifest['tools'].items():
        require(file_record(PROJECT/name) == expected, f'campaign tool changed: {name}')
    for name, expected in manifest['schedules'].items():
        require(file_record(config/name) == expected, f'schedule changed: {name}')
    binary = manifest['executable']
    require(file_record(binary['path']) == binary['file'], 'verified executable changed')
    for label, proof in manifest['prerequisites'].items():
        require(file_record(proof['path']) == proof['file'], f'prerequisite changed: {label}')
    correctness = finite_json(Path(manifest['prerequisites']['correctness']['path']))
    sustained = finite_json(Path(manifest['prerequisites']['sustained']['path']))
    require(correctness['status'] == 'bounded_checks_completed' and
            correctness['binary'] == binary['file'], 'same-binary correctness required')
    require(sustained['status'] == 'completed_two_configurations_not_scientific_acceptance' and
            sustained['binary'] == binary['file'] and
            sustained['source_sha'] == manifest['implementation_sha'] and
            sustained['resource_limit_violations'] == [], 'completed sustained preflight required')
    require([r['N'] for r in sustained['run_records']] == [64,128], 'sustained configuration set')
    evidence = Path(manifest['prerequisites']['sustained']['path']).parent
    for record in sustained['run_records']:
        require(record['status'] == 'completed_timing_only' and
                record['resource_limit_violations'] == [] and
                record['process']['status'] == 'exited' and record['process']['exit_code'] == 0,
                'failed sustained member')
        for name, expected in record['output_files'].items():
            path = evidence/f"n{record['N']}"/'output'/name
            require(file_record(path) == expected, f'sustained output identity: {path}')
    for name, expected in sustained['provenance'].items():
        require(file_record(evidence/'provenance'/name) == expected, 'sustained provenance changed')
    for run in manifest['runs']:
        e = run['expected']
        require(len(exported_grid(e)) == e['exported_bins_per_chain'], 'frozen grid count')
        require((config/e['context_schedule']).read_text().split() ==
                list(map(str,e['full_steps'])), 'context schedule/manifest mismatch')
    require(capture(['git','-C',PROJECT,'branch','--show-current']) == 'slip-springs', 'branch')
    require(not capture(['git','-C',PROJECT,'status','--porcelain']), 'dirty preparation checkout')
    capture(['git','-C',PROJECT,'merge-base','--is-ancestor',manifest['implementation_sha'],'HEAD'])
    return manifest


def campaign_main(config, pin, entry_point):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--verify-preparation', action='store_true')
    mode.add_argument('--execute-reviewed-24', action='store_true')
    args = parser.parse_args()
    manifest = authenticate(config, pin)
    if args.verify_preparation:
        print(json.dumps(dict(status='authenticated_preparation_no_gpu_execution', manifest_sha256=pin,
                              runs=len(manifest['runs']), output_root=manifest['output_root']), indent=2))
        return
    root = Path(manifest['output_root'])
    require(root == root.resolve() and not root.exists() and not root.is_symlink(), 'fresh canonical evidence root required')
    require(not root.is_relative_to(PROJECT.parents[1]) and
            root.is_relative_to(Path('/home/jramirez/UAMMD_KG-evidence')), 'persistent external evidence required')
    root.parent.mkdir(parents=True, exist_ok=True)
    lockdir = Path('/home/jramirez/UAMMD_KG-evidence/.locks')
    lockdir.mkdir(exist_ok=True)
    fd = os.open(lockdir/(manifest['gpu_uuid']+'.lock'), os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        root.mkdir(exist_ok=False)
        execute(manifest, config, pin, root, entry_point)


def execute(manifest, config, pin, root, entry_point):
    start = time.monotonic()
    deadline = start+manifest['limits']['aggregate_seconds']
    run_deadline = deadline
    summary = dict(status='preparing', started_utc=utc(), manifest_sha256=pin,
                   completed_runs=[], run_records=[], active_run=None, phase='preparation',
                   resource_limit_violations=[], gpu_peak_memory_bytes=None,
                   max_child_rss_bytes=0, child_wall_seconds_sum=0)
    directory = None
    env = environment(manifest['cuda_home'], manifest['gpu_uuid'])
    def interrupted(signum, frame):
        raise InterruptedError(f'operator signal {signum}')
    def arm():
        remaining = min(deadline, run_deadline)-time.monotonic()
        require(remaining > 0, 'campaign or run deadline exhausted')
        signal.setitimer(signal.ITIMER_REAL, min(60,remaining))
    def heartbeat(signum=None, frame=None):
        now = time.monotonic()
        snapshot = dict(utc=utc(), active_run=summary['active_run'], phase=summary['phase'],
                        campaign_elapsed_seconds=now-start, available_host_bytes=host_available(),
                        free_disk_bytes=shutil.disk_usage(root).free,
                        evidence_bytes=tree_bytes(root))
        # Append to an existing file: no concurrent temporary-file rename during tree polling.
        with (root/'progress.jsonl').open('a') as stream:
            stream.write(json.dumps(snapshot,allow_nan=False)+'\n')
            stream.flush()
            os.fsync(stream.fileno())
        for violated, reason in (
            (now >= deadline, 'aggregate_timeout'), (now >= run_deadline, 'run_stage_timeout'),
            (snapshot['available_host_bytes'] < manifest['limits']['min_runtime_available_host_bytes'], 'runtime_host_headroom'),
            (snapshot['free_disk_bytes'] < manifest['limits']['min_free_disk_bytes'], 'disk_headroom_limit'),
            (snapshot['evidence_bytes'] > manifest['limits']['aggregate_output_bytes'], 'aggregate_output_limit')):
            if violated:
                summary['resource_limit_violations'].append(reason)
                raise RuntimeError(reason)
        arm()
    for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):
        signal.signal(sig,interrupted)
    signal.signal(signal.SIGALRM,heartbeat)
    try:
        atomic(root/'summary.json',summary)
        (root/'progress.jsonl').touch(exist_ok=False)
        (root/'runs').mkdir()
        archived = root/'config'
        archived.mkdir()
        for name in ('manifest.json','manifest.sha256',*manifest['schedules']):
            shutil.copyfile(config/name,archived/name)
            (archived/name).chmod(0o444)
        provenance = root/'provenance'
        provenance.mkdir()
        for name in manifest['tools']:
            target = provenance/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(PROJECT/name,target)
        shutil.copyfile(entry_point,provenance/Path(entry_point).name)
        for label,proof in manifest['prerequisites'].items():
            shutil.copyfile(proof['path'],provenance/(label+'-'+Path(proof['path']).name))
        sustained = finite_json(Path(manifest['prerequisites']['sustained']['path']))
        old_provenance = Path(manifest['prerequisites']['sustained']['path']).parent/'provenance'
        (provenance/'sustained').mkdir()
        for name in sustained['provenance']:
            shutil.copyfile(old_provenance/name,provenance/'sustained'/name)
        atomic(provenance/'launch.json',dict(
            preparation_sha=capture(['git','-C',PROJECT,'rev-parse','HEAD']),
            implementation_sha=manifest['implementation_sha'], executable=manifest['executable'],
            compiler_provenance=manifest['compiler_provenance'], manifest_sha256=pin,
            platform=platform.platform(), python=sys.version, environment=env,
            affinity=sorted(os.sched_getaffinity(0)), preserved_files=inventory(provenance),
            source_tree=capture(['git','-C',PROJECT,'ls-tree','-r',manifest['implementation_sha']])))
        require(shutil.disk_usage(root).free >= manifest['limits']['initial_free_disk_bytes'], 'initial disk headroom')
        heartbeat()
        for run in manifest['runs']:
            summary.update(status='running',active_run=run['id'],phase='authentication')
            atomic(root/'summary.json',summary)
            stage_start = time.monotonic()
            run_deadline = stage_start+run['per_run_seconds']
            arm()
            authenticate(config,pin)
            require(digest(archived/'manifest.json') == pin, 'archived manifest changed')
            for name,proof in manifest['schedules'].items():
                require(file_record(archived/name) == proof, 'archived schedule changed')
            directory = root/'runs'/run['id']
            directory.mkdir(exist_ok=False)
            gpu = gpu_state(manifest,env)
            atomic(directory/'preflight.json',dict(utc=utc(),gpu=gpu,
                   available_host_bytes=host_available(),free_disk_bytes=shutil.disk_usage(root).free))
            before = resource_check(root,manifest['limits'],gpu['free_bytes'])
            atomic(directory/'launch.json',dict(utc=utc(),argv=run['argv'],environment=env,
                                               gpu=gpu,resources=before,seed=run['seed'],replica_id=run['replica_id']))
            summary['phase'] = 'simulation'
            limits = dict(manifest['limits'],per_run_seconds=run['per_run_seconds'])
            process = run_process(run['argv'],directory,env,limits,root,start)
            if process['status'] not in ('exited','application_failure'):
                summary['resource_limit_violations'].append(process['status'])
            require(process['status'] == 'exited' and process['exit_code'] == 0, f"child failed: {process['status']}")
            summary['phase'] = 'completion_validation'
            validation = validate_output(Path(run['output']),run)
            require(finite_json(Path(run['output'])/'metadata.json')['gpu'] == gpu['name'], 'executed GPU identity')
            authenticate(config,pin)
            require(digest(archived/'manifest.json') == pin, 'archived manifest changed during run')
            for name,proof in manifest['schedules'].items():
                require(file_record(archived/name) == proof, 'archived schedule changed during run')
            receipt = dict(id=run['id'],manifest_sha256=pin,validation=validation,
                           process=process,finished_utc=utc(),files=inventory(directory))
            atomic(directory/'receipt.json',receipt)
            record = dict(id=run['id'],process=process,stage_wall_seconds=time.monotonic()-stage_start,
                          output_bytes=tree_bytes(directory),receipt=file_record(directory/'receipt.json'))
            require(record['stage_wall_seconds'] <= run['per_run_seconds'], 'run stage timeout')
            require(record['output_bytes'] <= limits['per_run_output_bytes'], 'post-receipt output cap')
            require(tree_bytes(root) <= limits['aggregate_output_bytes'], 'post-receipt aggregate output cap')
            require(shutil.disk_usage(root).free >= limits['min_free_disk_bytes'], 'post-run disk floor')
            summary['completed_runs'].append(run['id'])
            summary['run_records'].append(record)
            summary['max_child_rss_bytes'] = max(summary['max_child_rss_bytes'],process['max_rss_bytes'])
            summary['child_wall_seconds_sum'] += process['wall_seconds']
            atomic(root/'summary.json',summary)
            run_deadline = deadline
            heartbeat()
            print(f"Completed {run['id']} ({len(summary['completed_runs'])}/24)",flush=True)
            directory = None
        summary.update(status='completed_24_runs_not_scientific_acceptance',active_run=None,phase='finished')
        heartbeat()
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        summary.update(status='stopped',error=f'{type(error).__name__}: {error}')
        if directory is not None:
            failure = dict(id=summary['active_run'],error=summary['error'],utc=utc())
            if (directory/'process.json').is_file():
                failure['process'] = finite_json(directory/'process.json')
            atomic(directory/'failure.json',failure)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        summary.update(finished_utc=utc(),wall_seconds=time.monotonic()-start,
                       evidence_bytes_before_final_summary=tree_bytes(root))
        atomic(root/'summary.json',summary)
        if tree_bytes(root) > manifest['limits']['aggregate_output_bytes']:
            summary['resource_limit_violations'].append('final_aggregate_output_limit')
            summary.update(status='stopped',error=summary.get('error','final aggregate output limit'))
            atomic(root/'summary.json',summary)
            raise RuntimeError('final aggregate output limit')
