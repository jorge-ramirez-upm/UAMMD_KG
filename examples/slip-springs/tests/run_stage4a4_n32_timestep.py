#!/usr/bin/env python3
"""Prepare four N32 cases; GPU execution requires --execute-n32 on the host."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time

DEVELOPMENT = Path('/tmp/UAMMD_KG-slip-springs-dev')
PROTECTED = (Path('/tmp/UAMMD_KG-slip-springs'), Path('/tmp/UAMMD_KG-stage4a3c-exec'))
PIN = '4e46d6014aa812b1fc687335654c4b1f681ddd22'
START = '8440bb377c458120a97ff74bc39baf20bb291341'
EXECUTABLE_SHA = '0a8d5bb7f3fc87617e4c6790457e504f4946816e884de9f44b22728ae538e859'
PROJECT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def git(directory, *args):
    return subprocess.check_output(['git', '-C', str(directory), *args], text=True).strip()


def identity(executable, expected_sha):
    if Path.cwd().resolve() != DEVELOPMENT or PROJECT != DEVELOPMENT/'examples/slip-springs':
        raise ValueError(f'run only from {DEVELOPMENT}')
    if git(DEVELOPMENT, 'branch', '--show-current') != 'slip-springs':
        raise ValueError('slip-springs branch required')
    if git(DEVELOPMENT, 'remote', 'get-url', 'origin') not in (
            'git@github.com:jorge-ramirez-upm/UAMMD_KG.git',
            'https://github.com/jorge-ramirez-upm/UAMMD_KG.git'):
        raise ValueError('repository identity mismatch')
    subprocess.run(['git', 'merge-base', '--is-ancestor', START, 'HEAD'], check=True)
    for directory in (DEVELOPMENT, *PROTECTED):
        if git(directory, 'status', '--porcelain', '--untracked-files=all'):
            raise ValueError(f'dirty worktree: {directory}')
        if directory in PROTECTED and git(directory, 'rev-parse', 'HEAD') != PIN:
            raise ValueError(f'protected worktree not pinned: {directory}')
    if not os.access(executable, os.X_OK) or digest(executable) != expected_sha:
        raise ValueError('executable missing or SHA-256 mismatch; never rebuild campaign binaries')
    return git(DEVELOPMENT, 'rev-parse', 'HEAD')


def cases(root, executable):
    result = []
    for kappa in (0, 10):
        for dt, steps, sample, limit in (('.000025', 800000, 400, 1800), ('.0005', 40000, 20, 300)):
            tag = f'N32-k{kappa}-dt{dt}'
            argv = [str(executable), '--output', str(root/f'run-double-{tag}'), '--springs', '32',
                    '--chains', '512', '--b0', '1', '--kb', '30', '--kappa', str(kappa),
                    '--dt', dt, '--steps', str(steps), '--sample', str(sample), '--seed', '433201',
                    '--stress-mode', 'every-step', '--stress-batch', '256', '--cpu-workers', '8',
                    '--corr-levels', '24', '--corr-slots', '32', '--corr-m', '2',
                    '--correlator-mib', '512', '--scalar-output', 'full']
            result.append(dict(tag=tag, kappa=kappa, dt=float(dt), steps=steps, sample=sample,
                               timeout_seconds=limit, argv=argv))
    return result


def timed(root, tag, argv, limit):
    """Bound the whole process group and keep receipts even on Ctrl-C or failure."""
    write(root/'receipts'/f'{tag}-started.json', dict(argv=argv, timeout_seconds=limit, restart='unsupported'))
    code, status, process = None, 'launch_failure', None
    started = time.monotonic()
    try:
        with (root/'logs'/f'{tag}.log').open('xb') as log:
            process = subprocess.Popen(['/usr/bin/time', '-v', '-o', str(root/'receipts'/f'{tag}.time.txt'),
                                        *argv], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=limit)
                status = 'completed' if code == 0 else 'application_failure'
            except subprocess.TimeoutExpired:
                status = 'timeout'
                raise
            except KeyboardInterrupt:
                status = 'interrupted'
                raise
    finally:
        if process is not None and process.poll() is None:
            try: os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait()
        write(root/'receipts'/f'{tag}.json', dict(status=status, exit_code=code,
              child_returncode=process.returncode if process is not None else None,
              elapsed_seconds=time.monotonic()-started, timeout_seconds=limit,
              partial_evidence_preserved=True, restart='unsupported'))
    if code != 0: raise RuntimeError(f'{tag} failed with {code}; evidence retained, no restart')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-n32', action='store_true')
    parser.add_argument('--root', type=Path, help='new absolute evidence directory outside all worktrees')
    args = parser.parse_args()
    executable = PROJECT/'build/double/semiflexible'
    head = identity(executable, EXECUTABLE_SHA)
    if args.root is not None:
        root = args.root
        if not root.is_absolute(): parser.error('--root must be absolute')
        root = root.resolve()
        for directory in (DEVELOPMENT, *PROTECTED, Path('/home/jramirez/UAMMD_KG')):
            if root == directory or directory in root.parents: parser.error('--root must be outside worktrees')
        root.mkdir(parents=True, exist_ok=False)
    else: root = Path(tempfile.mkdtemp(prefix='stage4a4-n32-'))
    for name in ('commands', 'environment', 'logs', 'receipts', 'references'): (root/name).mkdir()
    print(f'EVIDENCE_ROOT={root}', flush=True)
    plan = cases(root, executable)
    write(root/'environment/identity.json', dict(head=head, origin=git(DEVELOPMENT, 'remote', 'get-url', 'origin'),
          executable=str(executable), executable_sha256=digest(executable), protected_sha=PIN,
          compilation_provenance='not inferred from toolkit version or executable checksum'))
    write(root/'environment/host.json', dict(os=list(os.uname()), python=sys.version,
          cpu_affinity=sorted(os.sched_getaffinity(0)), load_average=list(os.getloadavg())))
    for case in plan:
        (root/'commands'/f"{case['tag']}.cmd").write_text(shlex.join(case['argv'])+'\n')
    write(root/'receipts/preflight.json', dict(mode='execution-requested' if args.execute_n32 else 'preflight',
          cases=plan, expected_gpu_seconds=832, gpu_timeout_total_seconds=4200,
          free_disk_bytes=shutil.disk_usage(root).free, minimum_free_disk_gib=4,
          recommended_host_ram_gib=2, recommended_gpu_free_gib=1, cpu_workers=8,
          restart='unsupported; every invocation requires a fresh root',
          scalar_rows_per_case=1024512, stress_frames=[800001, 40001],
          source_sha256={str(p.relative_to(PROJECT)): digest(p) for p in
                         (Path(__file__).resolve(), PROJECT/'tests/stage4a4_n32_timestep_analysis.py',
                          PROJECT/'tests/stage4a4_equilibrium_reference.py',
                          PROJECT/'tests/stage4a4_static_drift_analysis.py',
                          PROJECT/'tests/stage4a4_dynamic_timestep_analysis.py',
                          PROJECT/'tests/stage4a4_intermediate_timestep_analysis.py',
                          PROJECT/'semiflexible_reference.py')}))
    if shutil.disk_usage(root).free < 4*2**30: raise ValueError('need at least 4 GiB free disk')
    if not args.execute_n32:
        print('PREFLIGHT_PASS: commands prepared; no simulator, GPU query, reference ensemble or analysis launched')
        return
    if not Path('/usr/bin/time').is_file(): raise ValueError('/usr/bin/time required')
    with (root/'environment/gpu.txt').open('x') as stream:
        subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total,memory.free',
                        '--format=csv'], stdout=stream, check=True, timeout=15)
    cuda = Path(os.environ.get('CUDA_HOME', '/usr/local/cuda-13.0'))
    version = subprocess.check_output([str(cuda/'bin/nvcc'), '--version'], text=True, timeout=15)
    (root/'environment/nvcc.txt').write_text(version)
    if 'release 13.0' not in version: raise ValueError('CUDA Toolkit 13.0 required')
    # References are host-only work, bounded separately from each GPU case.
    for kappa in (0, 10):
        timed(root, f'N32-k{kappa}-reference', [sys.executable, str(PROJECT/'tests/stage4a4_equilibrium_reference.py'),
              '--springs', '32', '--kappa', str(kappa), '--chains', '65536', '--seed', '440401',
              '--report', str(root/'references'/f'N32-k{kappa}.json')], 900)
    for case in plan:
        if identity(executable, EXECUTABLE_SHA) != head: raise ValueError('HEAD changed after preflight')
        timed(root, case['tag'], case['argv'], case['timeout_seconds'])
        if identity(executable, EXECUTABLE_SHA) != head: raise ValueError('HEAD changed during case')
        output = Path(case['argv'][2])
        write(root/'receipts'/f"{case['tag']}-files.json",
              {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()})
    for kappa in (0, 10):
        timed(root, f'N32-k{kappa}-analysis', [sys.executable, str(PROJECT/'tests/stage4a4_n32_timestep_analysis.py'),
              '--small', str(root/f'run-double-N32-k{kappa}-dt.000025'),
              '--large', str(root/f'run-double-N32-k{kappa}-dt.0005'),
              '--reference', str(root/'references'/f'N32-k{kappa}.json'),
              '--report', str(root/'receipts'/f'N32-k{kappa}-analysis-result.json')], 600)
    print(f'EXECUTION_COMPLETED: inspect scientific decisions in {root}/receipts; completion is not acceptance')


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    try: main()
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        print(f'STOP: {error}; preserve evidence; interrupted trajectories are not resumable', file=sys.stderr)
        sys.exit(1)
