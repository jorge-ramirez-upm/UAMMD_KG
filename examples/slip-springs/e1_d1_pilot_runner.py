#!/usr/bin/env python3
"""D1 preparation/build and read-only preflight by default. No automatic resume."""
import argparse
import csv
import contextlib
import fcntl
import ctypes
import json
import os
from pathlib import Path
import platform
import re
import resource
import shlex
import shutil
import signal
import subprocess
import sys
import time

import numpy as np
import e1_d1_pilot as spec
import e1_d1_pilot_auth as auth
from e1_d1_pilot import require, Invalid, load, digest, file_record, atomic, capture


def environment(cuda=None, gpu_uuid=None):
    # Do not inherit compiler injection flags, LD_PRELOAD, Python path overrides,
    # or secrets. CUDA_VISIBLE_DEVICES selects one approved physical UUID.
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'TZ': 'UTC',
           'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
    if cuda:
        env['PATH'] = str(Path(cuda)/'bin')+':'+env['PATH']
        env['LD_LIBRARY_PATH'] = str(Path(cuda)/'lib64')
    if gpu_uuid:
        env['CUDA_VISIBLE_DEVICES'] = gpu_uuid
    return env


def dependencies(source, cuda, cxx, arch, env):
    project = Path(source)/'examples/slip-springs'
    argv = [str(Path(cuda)/'bin/nvcc'), '-ccbin='+str(cxx), '-std=c++17', '--extended-lambda',
            '-arch='+arch, '-DDOUBLE_PRECISION', '-DSLIP_SPRINGS_DIR="'+str(project)+'"',
            '-I'+str(Path(source)/'src'), '-I'+str(Path(source)/'src/third_party'), '-M', str(project/'semiflexible.cu')]
    text = capture(argv, env=env, timeout=60)
    paths = shlex.split(text.replace('\\\n', ' ').partition(':')[2])
    require(paths and str(project/'semiflexible.cu') in paths, 'missing compilation dependency closure')
    records = {str(Path(p).resolve()): file_record(Path(p).resolve()) for p in paths}
    for name in ('examples/KG/correlator.cpp', 'examples/KG/correlator.h'):
        path = Path(source)/name; records[str(path)] = file_record(path)
    return argv, records


def build(args):
    manifest = spec.validate_manifest(args.manifest, args.manifest_sha256)
    source = spec.source_identity(args.source_tree)
    require(re.fullmatch(r'sm_[0-9]+', args.arch) is not None, 'architecture must be explicit sm_NN')
    root = spec.output_path(args.build_root,args.source_tree); require(not root.exists(), 'build directory must be fresh (no no-op/adopted binary)')
    cuda = args.cuda_home.resolve(); cxx = Path(shutil.which(str(args.cxx)) or args.cxx).resolve()
    nvcc = cuda/'bin/nvcc'; runtime = (cuda/'lib64/libcudart.so').resolve()
    compiler = {'path': str(cxx), 'file': file_record(cxx), 'version': capture([cxx, '--version'])}
    toolkit = {'path': str(nvcc), 'file': file_record(nvcc), 'version': capture([nvcc, '--version'])}
    require('release 13.' in toolkit['version'], 'accepted CUDA 13 build required; other toolkits need review')
    env = environment(cuda)
    dep_command, dep = dependencies(args.source_tree.resolve(), cuda, cxx, args.arch, env)
    root.mkdir(parents=True); command = auth.build_command(args.source_tree.resolve(), root, cuda, cxx, args.arch)
    receipt = {'version': 1, 'status': 'building', 'started_utc': spec.utc(), 'source': source,
               'manifest_sha256': args.manifest_sha256, 'preparation_sources': manifest['preparation_sources'],
               'command': command, 'build_root': str(root), 'cuda_home': str(cuda), 'precision_bits': 64,
               'architecture': args.arch, 'nvcc': toolkit, 'cxx': compiler, 'environment': env,
               'dependency_command': dep_command, 'dependencies': dep,
               'runtime_library': {'path': str(runtime), 'file': file_record(runtime)}}
    atomic(root/'build.json', receipt)
    started = time.monotonic();started_ns=time.time_ns()
    try:
        with (root/'build.log').open('xb') as stream:
            p = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, env=env, timeout=240)
        require(p.returncode == 0, 'compilation failed; preserve build.log')
        binary = root/'bin/semiflexible'
        require(binary.is_file() and binary.stat().st_mtime_ns>=started_ns, 'no freshly compiled executable')
        transcript=(root/'build.log').read_text()
        require(any(str(nvcc) in line and '-DDOUBLE_PRECISION' in line and 'semiflexible.cu' in line
                    and 'correlator.cpp' in line and '-o '+str(binary) in line for line in transcript.splitlines()),
                'build transcript does not prove the requested compilation; no-op/adopted build refused')
        require(spec.source_identity(args.source_tree) == source, 'source changed while compiling')
        require(spec.tool_hashes()==manifest['preparation_sources'], 'preparation tools changed while building')
        require(dep == dependencies(args.source_tree.resolve(), cuda, cxx, args.arch, env)[1], 'compiler headers changed while building')
        linked = capture(['/usr/bin/ldd', binary], env=env)
        libraries = re.findall(r'(?:=>\s+)?(/[^\s]+)\s+\(', linked)
        require(libraries and 'not found' not in linked, 'missing linked library')
        receipt.update(status='completed', exit_code=0, compilation_observed=True, ended_utc=spec.utc(), wall_seconds=time.monotonic()-started,
                       binary={'path': str(binary), 'file': file_record(binary)},
                       log={'path': str(root/'build.log'), 'file': file_record(root/'build.log')},
                       linker_libraries={str(Path(p).resolve()): file_record(Path(p).resolve()) for p in libraries})
        atomic(root/'build.json', receipt)
        auth.validate_build(root/'build.json', digest(root/'build.json'), manifest, live=True)
    except BaseException as error:
        receipt.update(status='failed', error=str(error), ended_utc=spec.utc())
        atomic(root/'build.json', receipt)
        raise
    return {'build_receipt': str(root/'build.json'), 'build_receipt_sha256': digest(root/'build.json'),
            'binary_sha256': receipt['binary']['file']['sha256']}


def runtime_probe(library):
    cuda = ctypes.CDLL(str(library))
    def call(name, *args):
        require(getattr(cuda, name)(*args) == 0, 'CUDA runtime probe failed: '+name)
    count = ctypes.c_int(); call('cudaGetDeviceCount', ctypes.byref(count)); require(count.value == 1, 'one visible GPU required')
    call('cudaSetDevice', ctypes.c_int(0))
    runtime, driver = ctypes.c_int(), ctypes.c_int()
    call('cudaRuntimeGetVersion', ctypes.byref(runtime)); call('cudaDriverGetVersion', ctypes.byref(driver))
    free, total = ctypes.c_size_t(), ctypes.c_size_t()
    call('cudaMemGetInfo', ctypes.byref(free), ctypes.byref(total))
    return {'runtime_version': runtime.value, 'driver_api_version': driver.value,
            'free_device_bytes': free.value, 'total_device_bytes': total.value}


def machine(build, gpu_uuid):
    require(isinstance(gpu_uuid, str) and re.fullmatch(r'GPU-[0-9a-fA-F-]+', gpu_uuid), 'explicit physical GPU UUID required')
    env = environment(build['cuda_home'], gpu_uuid)
    query = ['nvidia-smi', '-i', gpu_uuid, '--query-gpu=uuid,name,driver_version,compute_cap,memory.total,memory.free',
             '--format=csv,noheader,nounits']
    values = list(csv.reader(capture(query, env=env).splitlines()))
    require(len(values) == 1 and len(values[0]) == 6, 'ambiguous GPU query')
    uuid, name, driver, capability, total, free = map(str.strip, values[0])
    require(uuid == gpu_uuid and 'sm_'+capability.replace('.', '') == build['architecture'], 'GPU UUID/architecture mismatch')
    apps = capture(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], env=env)
    require(not any(line.split(',')[0].strip() == gpu_uuid for line in apps.splitlines()), 'GPU has another compute process')
    probe = json.loads(capture([sys.executable, Path(__file__).resolve(), '_probe_runtime',
                               '--runtime-library', build['runtime_library']['path']], env=env))
    stable = {'platform': platform.platform(), 'machine': platform.machine(),
              'python': sys.version, 'python_executable': file_record(Path(sys.executable).resolve()),
              'numpy': np.__version__, 'numpy_module': file_record(np.__file__),
              'numpy_extension':file_record(np._core._multiarray_umath.__file__),
              'gpu': {'uuid': uuid, 'name': name, 'driver': driver, 'compute_capability': capability,
                      'total_bytes': int(float(total)*1024**2)},
              'runtime_version': probe['runtime_version'], 'driver_api_version': probe['driver_api_version'],
              'runtime_library': build['runtime_library']['file'], 'environment': env}
    return stable, min(probe['free_device_bytes'], int(float(free)*1024**2))


def host_available():
    fields = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(fields['MemAvailable'].split()[0])*1024
    # Respect visible unified-cgroup headroom as well as whole-host MemAvailable.
    candidates = [Path('/sys/fs/cgroup')]
    for line in Path('/proc/self/cgroup').read_text().splitlines():
        if line.startswith('0::'):
            rel = line[3:].lstrip('/')
            if '..' not in Path(rel).parts:
                path = Path('/sys/fs/cgroup')/rel
                while str(path).startswith('/sys/fs/cgroup'):
                    candidates.append(path)
                    if path == Path('/sys/fs/cgroup'): break
                    path = path.parent
    for path in set(candidates):
        limit, current = path/'memory.max', path/'memory.current'
        if limit.exists() and current.exists() and limit.read_text().strip() != 'max':
            available = min(available, max(0, int(limit.read_text())-int(current.read_text())))
    return available


def validate_approval(approval, manifest_sha, build_sha, root, env_sha):
    require(set(approval) == {'version', 'execution_authorized', 'approval_reference', 'manifest_sha256',
        'build_receipt_sha256', 'environment_sha256', 'output_root', 'gpu_uuid', 'limits'}, 'malformed approval')
    require(approval['version'] == 1 and approval['execution_authorized'] is True
            and isinstance(approval['approval_reference'], str) and approval['approval_reference'].strip(), 'independent execution approval missing')
    require((approval['manifest_sha256'], approval['build_receipt_sha256'], approval['environment_sha256'], approval['output_root'])
            == (manifest_sha, build_sha, env_sha, str(root)), 'approval is for different manifest/build/environment/output root')
    return spec.validate_limits(approval['limits'])


def resource_check(parent, limits, gpu_free):
    resources = {'free_disk_bytes': shutil.disk_usage(parent).free, 'available_host_bytes': host_available(),
                 'free_gpu_bytes': gpu_free}
    require(resources['free_disk_bytes'] >= limits['min_free_disk_bytes'] + limits['per_run_output_bytes'], 'insufficient free disk/headroom')
    require(resources['available_host_bytes'] >= limits['min_available_host_bytes'], 'insufficient host/cgroup memory')
    require(gpu_free >= limits['min_free_gpu_bytes'], 'insufficient GPU memory')
    return resources


def tree_bytes(root):
    size = 0
    for path in Path(root).rglob('*'):
        require(not path.is_symlink(), 'symlink in evidence root')
        if path.is_file(): size += path.stat().st_size
    return size


def run_process(argv, directory, env, limits, campaign_root, campaign_start):
    """Sequential POSIX child supervision; also exercised with tiny CPU test children."""
    start = time.monotonic(); reason = None; peak = 0
    parent_pid=os.getpid()
    def child_limits():
        # Linux parent-death signal also kills the child if supervision is SIGKILLed.
        require(ctypes.CDLL(None).prctl(1, signal.SIGKILL, 0, 0, 0)==0, 'cannot set parent-death guard')
        if os.getppid()!=parent_pid:os.kill(os.getpid(),signal.SIGKILL)
        resource.setrlimit(resource.RLIMIT_FSIZE, (int(limits['per_run_output_bytes']), int(limits['per_run_output_bytes'])))
    with (directory/'stdout.log').open('xb') as stdout, (directory/'stderr.log').open('xb') as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, env=env,
                                   start_new_session=True, preexec_fn=child_limits)
        def stop():
            try: os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            deadline = time.monotonic()+1
            while True:
                pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                if pid: return status, usage
                if time.monotonic() >= deadline:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    return os.wait4(process.pid, 0)[1:]
                time.sleep(.02)
        try:
            while True:
                pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                if pid: break
                status_file = Path('/proc')/str(process.pid)/'status'
                try:
                    match = re.search(r'^VmRSS:\s+(\d+) kB', status_file.read_text(), re.M)
                    if match: peak = max(peak, int(match.group(1))*1024)
                except FileNotFoundError:
                    pass  # wait4 supplies the final peak even if /proc disappeared.
                now = time.monotonic()
                if now-start > limits['per_run_seconds']: reason = 'per_run_timeout'
                elif now-campaign_start > limits['aggregate_seconds']: reason = 'aggregate_timeout'
                elif peak > limits['max_host_rss_bytes']: reason = 'host_memory_limit'
                elif tree_bytes(directory) > limits['per_run_output_bytes']: reason = 'per_run_output_limit'
                elif tree_bytes(campaign_root) > limits['aggregate_output_bytes']: reason = 'aggregate_output_limit'
                elif shutil.disk_usage(campaign_root).free < limits['min_free_disk_bytes']: reason = 'disk_headroom_limit'
                if reason:
                    status, usage = stop(); break
                time.sleep(.05)
        except BaseException as error:
            status, usage = stop(); process.returncode = os.waitstatus_to_exitcode(status)
            atomic(directory/'process.json', {'status':'interrupted' if isinstance(error,(KeyboardInterrupt,SystemExit)) else 'failed',
                'exit_code':process.returncode,'wall_seconds':time.monotonic()-start,'max_rss_bytes':int(usage.ru_maxrss)*1024,'error':str(error)})
            raise
        process.returncode = os.waitstatus_to_exitcode(status)
    peak = max(peak, int(usage.ru_maxrss)*1024)
    elapsed = time.monotonic()-start
    if elapsed > limits['per_run_seconds']: reason = reason or 'per_run_timeout'
    if time.monotonic()-campaign_start > limits['aggregate_seconds']: reason = reason or 'aggregate_timeout'
    if peak > limits['max_host_rss_bytes']: reason = reason or 'host_memory_limit'
    if tree_bytes(directory) > limits['per_run_output_bytes']: reason = reason or 'per_run_output_limit'
    if tree_bytes(campaign_root) > limits['aggregate_output_bytes']: reason = reason or 'aggregate_output_limit'
    result={'exit_code': process.returncode, 'wall_seconds': elapsed, 'max_rss_bytes': peak,
            'status': reason or ('exited' if process.returncode == 0 else 'application_failure')}
    atomic(directory/'process.json',result)
    return result


def preflight(args):
    manifest = spec.validate_manifest(args.manifest, args.manifest_sha256)
    summary = {'mode': 'read-only preflight', 'manifest_sha256': args.manifest_sha256,
               'execution_authorized': False, 'estimates': spec.estimates(manifest), 'runs': manifest['runs'],
               'blockers': [], 'build': None, 'environment': None,
               'observed_resources':{'available_host_bytes':host_available(),
                 'free_disk_bytes':shutil.disk_usage(args.output_root.resolve().parent if args.output_root and args.output_root.resolve().parent.exists() else Path.cwd()).free}}
    build = approval = stable = limits = None
    if args.build_receipt and args.build_sha256:
        build = auth.validate_build(args.build_receipt, args.build_sha256, manifest, live=True)
        summary['build'] = {'receipt_sha256': args.build_sha256, 'binary': build['binary'], 'source': build['source']}
    else: summary['blockers'].append('fresh authenticated build receipt and its SHA256 required')
    if args.approval:
        approval = load(args.approval)
        if not args.approval_sha256 or digest(args.approval) != args.approval_sha256:
            summary['blockers'].append('trusted approval SHA256 missing/mismatched')
    else: summary['blockers'].append('independent approval and explicit resource budgets required')
    gpu_uuid = args.gpu_uuid or (approval or {}).get('gpu_uuid')
    if build and gpu_uuid:
        stable, free = machine(build, gpu_uuid)
        summary['environment'] = stable; summary['environment_sha256'] = spec.identity(stable)
        summary['observed_resources']['free_gpu_bytes']=free
        if approval and not summary['blockers']:
            try:
                require(args.output_root is not None, 'fresh output root required')
                root = spec.output_path(args.output_root,build['source']['path'])
                require(not root.exists() and root.parent.is_dir(), 'output root must be new with an existing parent')
                require(not root.is_relative_to(Path(build['source']['path'])), 'outputs must stay outside the pinned source checkout')
                limits = validate_approval(approval, args.manifest_sha256, args.build_sha256, root, spec.identity(stable))
                require(approval['gpu_uuid'] == gpu_uuid, 'GPU UUID differs from approval')
                state=[spec.state_estimate(run) for run in manifest['runs']]
                require(limits['min_free_gpu_bytes']>=max(s['device_array_bytes'] for s in state), 'approved GPU headroom below explicit state allocation')
                require(limits['max_host_rss_bytes']>=max(s['legacy_workspace_estimate_bytes']+s['observer_vector_bytes'] for s in state), 'approved host budget below state estimate; CUDA overhead also needs review')
                summary['resources'] = resource_check(root.parent, limits, free)
                summary['approved_limits'] = limits
            except (ValueError, OSError, KeyError, TypeError) as error:
                summary['blockers'].append(str(error))
    else: summary['blockers'].append('build and physical GPU UUID required for runtime/resource preflight')
    root=args.output_root.resolve() if args.output_root else Path('(new root)')
    summary['schedules']=manifest['schedules']
    summary['commands'] = [spec.command(r, root/'provenance/semiflexible', root/'runs'/r['id']/'output',
                                        root/'config') for r in manifest['runs']]
    return summary, manifest, build, approval, limits


def execute(args, summary, manifest, build, approval, limits):
    # No caller can turn a default preflight into execution by editing the manifest.
    require(args.authorize_pilot_execution is True, 'explicit --authorize-pilot-execution flag required')
    require(not summary['blockers'] and limits is not None, 'execution preflight blocked: '+str(summary['blockers']))
    root = spec.output_path(args.output_root,build['source']['path']); root.mkdir(exist_ok=False)
    atomic(root/'status.json', {'version':1, 'status':'preparing', 'started_utc':spec.utc()})
    start = time.monotonic()
    (root/'runs').mkdir(); (root/'config').mkdir(); (root/'provenance').mkdir()
    shutil.copyfile(args.manifest, root/'manifest.json'); shutil.copyfile(args.approval, root/'approval.json')
    shutil.copyfile(args.build_receipt, root/'build.json')
    for name in manifest['schedules']: shutil.copyfile(args.manifest.parent/name, root/'config'/name)
    shutil.copyfile(build['binary']['path'], root/'provenance/semiflexible')
    (root/'provenance/semiflexible').chmod(0o500)
    shutil.copyfile(build['log']['path'], root/'provenance/build.log')
    ledger = {'version': 1, 'campaign': manifest['campaign'], 'manifest_sha256': args.manifest_sha256,
              'approval_sha256': args.approval_sha256, 'build_receipt_sha256': args.build_sha256,
              'environment': summary['environment'], 'environment_sha256': summary['environment_sha256'],
              'started_utc': spec.utc(), 'output_root': str(root), 'limits': limits,
              'source': build['source'], 'preparation_sources': manifest['preparation_sources']}
    atomic(root/'campaign.json', ledger)
    status = {'version': 1, 'status': 'running', 'started_utc': ledger['started_utc'], 'completed_run_ids': []}
    atomic(root/'status.json', status)
    try:
        for run in manifest['runs']:
            require(spec.validate_manifest(args.manifest, args.manifest_sha256) == manifest, 'configuration changed')
            auth.validate_build(args.build_receipt, args.build_sha256, manifest, live=True)
            require(digest(args.approval) == args.approval_sha256, 'approval changed')
            stable, free = machine(build, approval['gpu_uuid'])
            require(spec.identity(stable) == summary['environment_sha256'], 'runtime environment changed')
            resources = resource_check(root, limits, free)
            require(time.monotonic()-start < limits['aggregate_seconds'] and tree_bytes(root) < limits['aggregate_output_bytes'], 'aggregate budget exhausted')
            require(digest(root/'manifest.json') == args.manifest_sha256 and digest(root/'approval.json') == args.approval_sha256, 'archived plan/approval changed')
            for name, proof in manifest['schedules'].items():
                require(digest(root/'config'/name) == proof['sha256'], 'archived schedule changed')
            require(file_record(root/'provenance/semiflexible') == build['binary']['file'], 'archived executable changed')
            directory = root/'runs'/run['id']; directory.mkdir(exist_ok=False)
            argv = spec.command(run, root/'provenance/semiflexible', directory/'output', root/'config')
            receipt = {'version': 1, 'status': 'running', 'started_utc': spec.utc(), 'run': run, 'command': argv,
                       'manifest_sha256': args.manifest_sha256, 'build_receipt_sha256': args.build_sha256, 'exit_code':None,
                       'environment_sha256': summary['environment_sha256'], 'resources_before': resources}
            atomic(directory/'execution.json', receipt)
            try:
                result = run_process(argv, directory, environment(build['cuda_home'], approval['gpu_uuid']), limits, root, start)
                receipt.update(result, ended_utc=spec.utc())
                require(result['status'] == 'exited' and result['exit_code'] == 0, 'run failed/resource limit: '+result['status'])
                data = auth.validate_output(directory/'output', run, manifest['schedules'][run['schedule']]['steps'],
                                            manifest['schedules'][run['snapshots']]['steps'], stable['gpu']['name'])
                auth.validate_build(args.build_receipt, args.build_sha256, manifest, live=True)
                require(file_record(root/'provenance/semiflexible') == build['binary']['file'], 'executed binary changed')
                require(spec.validate_manifest(args.manifest, args.manifest_sha256) == manifest, 'configuration changed during run')
                receipt.update(status='completed', output_files=data['files'], event_totals=data['event_totals'],
                               logs={name: file_record(directory/name) for name in ('stdout.log', 'stderr.log','process.json')})
            except BaseException as error:
                if (directory/'process.json').exists():receipt.update(load(directory/'process.json'))
                receipt.update(status='interrupted' if isinstance(error, (KeyboardInterrupt, SystemExit)) else 'failed',
                               error=str(error), ended_utc=spec.utc())
                raise
            finally:
                atomic(directory/'execution.json', receipt)
            if tree_bytes(directory)>limits['per_run_output_bytes'] or tree_bytes(root)>limits['aggregate_output_bytes']:
                receipt.update(status='failed',error='post-authentication evidence size limit')
                atomic(directory/'execution.json',receipt)
                raise Invalid('post-authentication evidence size limit')
            status['completed_run_ids'].append(run['id']); atomic(root/'status.json', status)
        require(time.monotonic()-start <= limits['aggregate_seconds'] and tree_bytes(root) <= limits['aggregate_output_bytes'], 'aggregate post-validation limit')
        status.update(status='completed', ended_utc=spec.utc(), wall_seconds=time.monotonic()-start)
        atomic(root/'status.json', status)
        atomic(root/'campaign_complete.pending.json', {'version': 1, 'status': 'completed', 'campaign_sha256': digest(root/'campaign.json'), 'status_sha256':digest(root/'status.json'),
               'run_ids': [r['id'] for r in manifest['runs']],
               'receipts': {r['id']: digest(root/'runs'/r['id']/'execution.json') for r in manifest['runs']}})
        require(tree_bytes(root)<=limits['aggregate_output_bytes'],'final receipt exceeds aggregate output budget')
        os.replace(root/'campaign_complete.pending.json',root/'campaign_complete.json')
    except BaseException as error:
        status.update(status='interrupted' if isinstance(error, (KeyboardInterrupt, SystemExit)) else 'failed',
                      ended_utc=spec.utc(), error=str(error))
        atomic(root/'status.json', status)
        raise
    return {'status': 'completed', 'root': str(root), 'completion_sha256':digest(root/'campaign_complete.json')}


@contextlib.contextmanager
def gpu_lock(uuid):
    require(re.fullmatch(r'GPU-[0-9a-fA-F-]+',uuid) is not None,'invalid GPU lock UUID')
    fd=os.open('/tmp/e1-d1-'+uuid+'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action')
    b = sub.add_parser('build', help='compile accepted source into a NEW build root; no trajectories')
    b.add_argument('--source-tree', type=Path, required=True); b.add_argument('--build-root', type=Path, required=True)
    b.add_argument('--cuda-home', type=Path, required=True); b.add_argument('--arch', required=True)
    b.add_argument('--cxx', type=Path, default=Path('/usr/bin/g++'))
    p = sub.add_parser('preflight', help='read-only by default; independent approval required for any execution')
    p.add_argument('--build-receipt', type=Path); p.add_argument('--build-sha256')
    p.add_argument('--approval', type=Path); p.add_argument('--approval-sha256')
    p.add_argument('--gpu-uuid'); p.add_argument('--output-root', type=Path)
    p.add_argument('--authorize-pilot-execution', action='store_true')
    probe = sub.add_parser('_probe_runtime', help=argparse.SUPPRESS); probe.add_argument('--runtime-library', type=Path, required=True)
    for child in (b, p):
        child.add_argument('--manifest', type=Path, default=spec.CONFIG/'manifest.json')
        child.add_argument('--manifest-sha256', required=True)
    if len(sys.argv)==1:
        sys.argv += ['preflight','--manifest-sha256',(spec.CONFIG/'manifest.sha256').read_text().split()[0]]
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM, interrupted);signal.signal(signal.SIGHUP, interrupted)
    try:
        if args.action == 'build': result = build(args)
        elif args.action == '_probe_runtime': result = runtime_probe(args.runtime_library)
        elif args.action == 'preflight':
            summary, manifest, built, approval, limits = preflight(args)
            print(json.dumps(summary, indent=2, allow_nan=False), flush=True)
            if args.authorize_pilot_execution:
                require(not summary['blockers'] and approval is not None,'execution preflight blocked')
                with gpu_lock(approval['gpu_uuid']):result = execute(args, summary, manifest, built, approval, limits)
            else: return
        else: parser.print_help(); return
        print(json.dumps(result, indent=2, allow_nan=False))
    except KeyboardInterrupt as error:
        parser.exit(130, f'D1 interrupted; partial evidence preserved: {error}\n')
    except (OSError, ValueError, KeyError, TypeError, AssertionError, subprocess.SubprocessError) as error:
        parser.exit(1, f'D1 runner refused: {error}\n')


if __name__ == '__main__':
    main()
