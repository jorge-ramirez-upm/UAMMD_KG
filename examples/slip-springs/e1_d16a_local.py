#!/usr/bin/env python3
"""D1.6A CPU-only local handoff; readiness never starts reference sampling."""
import argparse
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

# Reuse the established strict JSON, SHA256, bounded-command and Git helpers.
from e1_d15_local import require, encoded, write, load, proof, git, clean, command, local_env

PROJECT = Path(__file__).resolve().parent
REL = Path('examples/slip-springs')
BASE = 'cca7f0d5f235e4048648d4b159e10ad68311b956'
SAMPLER_SHA = 'a293806e16c4dcb58188ae680d852a487d5f3b95920222a2bb72b4aee8c17967'
LIMITS = {'batch_seconds': 30, 'stiffness_seconds': 1200,
          'rss_bytes': 1024**3, 'output_bytes': 16*1024**2}
SOURCES = ('e1_d16a_local.py', 'e1_d16a_reference.py', 'e1_d16a_sampling.py',
           'tests/test_e1_d16a_reference.py', 'tests/test_e1_d16a_local.py',
           'semiflexible_reference.py', 'e1_d15_local.py',
           'E1_STAGE_D16_SCIENTIFIC_DESIGN_V1.md', 'E1_STAGE_D16_REFERENCE_MOMENTS_V1.md',
           'E1_STAGE_D16_RESOURCE_PLAN_V1.md')


def configuration():
    return {'schema': 'e1-d16a-reference-v1', 'purpose': 'independent CPU backbone reference ONLY',
            'N': 32, 'b0': 1, 'kb': 30, 'kBT': 1, 'kappas': [0, 10], 'dtype': 'float64',
            'generator': 'NumPy PCG64', 'seed_entropy': '[721610000,kappa,phase,batch_index]',
            'phase_ids': {'calibration': 1, 'sizing_pilot': 2, 'final_reference': 3},
            'batch_size': 512, 'calibration_count': 65536, 'pilot_count': 8192,
            'final_grid': [16384, 32768, 65536, 131072, 262144, 524288],
            'maximum_draws_per_kappa': 598016, 'alpha': .05, 'reference_family_size': 50,
            'pilot_SE_multiplier': 2, 'relative_half_width': .05, 'cdf_half_width': .005,
            'quantile_probabilities': [.01, .05, .10, .25, .50, .75, .90, .95, .99],
            'sampler_sha256': SAMPLER_SHA, 'limits': LIMITS,
            'no_resume': True, 'no_automatic_retry': True, 'GPU_campaign_authorized': False}


def tree_bytes(root):
    files = list(root.rglob('*'))
    require(not any(p.is_symlink() for p in files), 'symlink in evidence')
    return sum(p.stat().st_size for p in files if p.is_file())


def case_bytes(root, kappa):
    marker = f'kappa-{kappa}'
    external = [p for base in (root, root/'logs') if base.exists()
                for p in base.iterdir() if p.is_file() and marker in p.name]
    require(not any(p.is_symlink() for p in external), 'symlink in case metadata')
    return tree_bytes(root/marker)+sum(p.stat().st_size for p in external)


def process_rss(pid):
    text = Path(f'/proc/{pid}/status').read_text()
    values = [int(line.split()[1])*1024 for line in text.splitlines() if line.startswith(('VmRSS:', 'VmHWM:'))]
    return max(values, default=0)


def checked(root):
    session = load(root/'session.json')
    require(session['root'] == str(root), 'evidence root moved')
    project = root/'preparation'/REL
    require(session['project'] == str(project), 'incorrect preparation path')
    require(git(project, 'rev-parse', 'HEAD') == session['commit'], 'preparation revision changed')
    clean(project)
    require(session['sources'] == {name: proof(project/name) for name in SOURCES}, 'source identity changed')
    require(proof(Path(__file__)) == session['sources']['e1_d16a_local.py'], 'use the pinned handoff utility')
    require(session['sources']['semiflexible_reference.py']['sha256'] == SAMPLER_SHA, 'accepted sampler changed')
    require(load(root/'config.json') == configuration(), 'frozen reference configuration changed')
    return session, project


def environment():
    # Called only by an explicit local readiness/preflight child, never on import.
    import numpy
    import scipy
    import e1_d16a_reference  # Load the actual dependency closure used for inference.
    import e1_d16a_sampling  # Accepted sampler plus ctypes/resource worker dependencies.
    identities = {}
    for package in (numpy, scipy):
        parent = Path(package.__file__).resolve().parent
        for base in (parent, parent.parent/(package.__name__+'.libs')):
            if base.exists():
                for path in sorted(base.rglob('*')):
                    if (path.is_file() and '__pycache__' not in path.parts and 'tests' not in path.parts
                            and (path.suffix == '.py' or '.so' in path.name)):
                        # Resolve distribution symlinks; record absolute dependency identity.
                        resolved = path.resolve()
                        identities[str(resolved)] = proof(resolved)
    # Capture libm/libc/Python/BLAS libraries already mapped by the actual imports.
    for line in Path('/proc/self/maps').read_text().splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) == 6 and parts[5].startswith('/') and Path(parts[5]).is_file():
            path = Path(parts[5]).resolve()
            identities[str(path)] = proof(path)
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name and Path(name).is_file():
            path = Path(name).resolve()
            identities[str(path)] = proof(path)
    return {'python': str(Path(sys.executable).resolve()), 'python_identity': proof(Path(sys.executable).resolve()),
            'python_version': sys.version, 'numpy_version': numpy.__version__, 'scipy_version': scipy.__version__,
            'system': list(os.uname()), 'dependencies': identities,
            'thread_environment': {k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')},
            'float_precision': 'IEEE float64; no CUDA dependencies'}


def resource_preflight(root):
    require(sys.platform.startswith('linux'), 'Linux /proc resource supervision required')
    memory = {line.split(':')[0]: int(line.split()[1])*1024
              for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    available = memory['MemAvailable']
    # Explicit CPU-reference headroom floors, not copied GPU campaign budgets.
    require(available >= 2*1024**3, 'need 2 GiB available host RAM for a 1 GiB RSS child')
    disk = shutil.disk_usage(root).free
    require(disk >= 1024**3, 'need 1 GiB free disk for bounded CPU reference evidence')
    return {'available_host_bytes': available, 'free_disk_bytes': disk,
            'min_available_host_bytes': 2*1024**3, 'min_free_disk_bytes': 1024**3,
            'note': 'read-only CPU reference preflight; no GPU query or sampling'}


def verify_environment(root, project, name, timeout=120):
    raw = root/'scratch'/(name+'.json')
    command(root, name, [sys.executable, project/'e1_d16a_local.py', '_environment', '--output', raw],
            project, timeout, local_env(root))
    observed, expected = proof(raw), proof(root/'environment.json')
    same = observed == expected
    retained = root/'environment.json' if same else root/(name+'-unexpected.json')
    if same:
        raw.unlink()  # Exact duplicate bytes remain in the primary immutable snapshot.
    else:
        raw.rename(retained)  # Preserve an unfavorable environment observation in full.
    write(root/(name+'.json'), {'matches_readiness': same, 'observed': observed,
                               'expected': expected, 'full_snapshot': str(retained)})
    require(same, 'dependency/environment identity changed; new review required')
    return observed


def approval_template(root):
    return {'schema': 'e1-d16a-reference-approval-v1',
            'purpose': 'CPU equilibrium reference only; NO GPU trajectory authorization',
            'root': str(root), 'kappas': [0, 10], 'limits': LIMITS,
            'readiness': proof(root/'readiness.json'), 'configuration': proof(root/'config.json'),
            'environment': proof(root/'environment.json'), 'numerical': proof(root/'numerical.json'),
            'session': proof(root/'session.json'), 'execution_authorized': False, 'review_reference': None}


def approved(root, path, trusted_sha):
    session, project = checked(root)
    require(proof(path)['sha256'] == trusted_sha, 'approval SHA256 mismatch')
    value = load(path)
    template = load(root/'approval-template.json')
    require(template == approval_template(root), 'unapproved template identity/budget change')
    expected = dict(template, execution_authorized=True, review_reference=value.get('review_reference'))
    require(value == expected, 'approval fields differ from the reviewed reference-only template')
    require(isinstance(value['review_reference'], str) and value['review_reference'].strip(), 'independent review reference required')
    require(load(root/'readiness.json')['status'] == 'READY_FOR_REVIEW', 'readiness did not pass')
    require(value['readiness'] == proof(root/'readiness.json')
            and value['configuration'] == proof(root/'config.json')
            and value['environment'] == proof(root/'environment.json')
            and value['numerical'] == proof(root/'numerical.json')
            and value['session'] == proof(root/'session.json'), 'approval binding changed')
    return value


def package(root, kind):
    """Small allowlist packet + full raw-file references. Original evidence stays local."""
    require(kind in ('readiness', 'results'), 'invalid package kind')
    require(not (root/'reference-running.json').exists(), 'active or interrupted reference; cannot package mutable evidence')
    returns = root/'returns'
    returns.mkdir(exist_ok=True)
    payload, inventory = {}, {}
    # No checkout, scalar sample .npy, executable, scratch or earlier archives.
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if rel.parts[0] in ('preparation', 'scratch', 'returns') or not path.is_file():
            continue
        require(not path.is_symlink(), 'evidence symlink')
        identity = proof(path)
        inventory[str(rel)] = dict(identity, local_path=str(path))
        if path.suffix in ('.json', '.jsonl', '.stdout', '.stderr', '.md'):
            require(identity['bytes'] <= 4*1024**2, 'oversized compact evidence member')
            payload[str(rel)] = path.read_bytes()
    summary = ['D1.6A '+kind.upper(), 'Original evidence: '+str(root),
               'No GPU/dynamical-preservation conclusion is possible from this reference.']
    readiness = load(root/'readiness.json') if (root/'readiness.json').exists() else {'status': 'INCOMPLETE'}
    summary.append('Readiness: '+readiness['status'])
    for kappa in (0, 10):
        result = root/f'kappa-{kappa}'/'completion.json'
        summary.append(f'kappa={kappa}: '+(load(result)['status'] if result.exists() else 'NOT COMPLETED'))
    summary.append('Scalar samples omitted; full local paths, sizes and SHA256 are in contents.json.')
    summary.append('Review high-moment stability and delta/jackknife differences; nominal CLT precision is not a rigorous tail guarantee.')
    payload['SUMMARY.md'] = ('\n'.join(summary)+'\n').encode()
    payload['contents.json'] = encoded({'kind': kind, 'root': str(root), 'files': inventory,
                                       'integrity': 'SHA256 detects changes; not a digital signature or proof against an adversary replacing all evidence'})
    payload['SHA256SUMS'] = ''.join(hashlib.sha256(body).hexdigest()+'  '+name+'\n'
                                   for name, body in sorted(payload.items())).encode()
    require(sum(map(len, payload.values())) <= 8*1024**2, 'compact packet exceeds 8 MiB; stop, preserve evidence')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive = returns/f'd16a-{kind}-return-{stamp}.tar.gz'
    with archive.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for name, body in sorted(payload.items()):
            info = tarfile.TarInfo(name)
            info.size = len(body)
            info.mode = 0o600
            tar.addfile(info, io.BytesIO(body))
    digest = proof(archive)['sha256']
    sidecar = Path(str(archive)+'.sha256')
    with sidecar.open('x') as stream:
        stream.write(digest+'  '+archive.name+'\n')
    print('UPLOAD', archive, flush=True)
    print('UPLOAD', sidecar, flush=True)
    return archive


def readiness(args):
    parent = args.evidence_parent.expanduser().resolve()
    require(not any(parent.is_relative_to(Path(p)) for p in ('/tmp', '/var/tmp', '/dev/shm')),
            'choose durable storage, not temporary storage')
    parent.mkdir(parents=True, exist_ok=True)
    require(not any((p/'.git').exists() for p in (parent, *parent.parents)), 'evidence must be outside Git repositories')
    root = Path(tempfile.mkdtemp(prefix='d16a-readiness-', dir=parent))
    print('D16A_ROOT='+str(root), flush=True)
    (root/'scratch').mkdir()
    status = {'status': 'FAILED', 'errors': []}
    try:
        repo = Path(git(PROJECT, 'rev-parse', '--show-toplevel'))
        require(git(repo, 'branch', '--show-current') == 'slip-springs', 'use branch slip-springs')
        clean(repo)
        require(git(repo, 'remote', 'get-url', 'origin') in (
            'git@github.com:jorge-ramirez-upm/UAMMD_KG.git', 'https://github.com/jorge-ramirez-upm/UAMMD_KG.git'), 'wrong origin')
        git(repo, 'fetch', 'origin', 'slip-springs')
        commit = git(repo, 'rev-parse', 'HEAD')
        require(commit == git(repo, 'rev-parse', 'origin/slip-springs'), 'local HEAD differs from freshly fetched origin/slip-springs')
        git(repo, 'merge-base', '--is-ancestor', BASE, commit)
        common = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
        require(not any(common.is_relative_to(Path(p)) for p in ('/tmp', '/var/tmp', '/dev/shm')), 'Git common directory must be durable')
        resource_preflight(root)
        command(root, 'checkout', ['git', '-C', repo, 'worktree', 'add', '--detach', root/'preparation', commit],
                repo, 60, local_env(root))
        project = root/'preparation'/REL
        session = {'root': str(root), 'project': str(project), 'commit': commit,
                   'python': str(Path(sys.executable).resolve()), 'sources': {name: proof(project/name) for name in SOURCES}}
        require(session['sources']['semiflexible_reference.py']['sha256'] == SAMPLER_SHA, 'accepted sampler hash differs')
        write(root/'session.json', session)
        write(root/'config.json', configuration())
        write(root/'preflight.json', resource_preflight(root))
        command(root, 'environment', [sys.executable, project/'e1_d16a_local.py', '_environment', '--output', root/'environment.json'],
                project, 120, local_env(root))
        command(root, 'cpu-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_e1_d16a_*.py', '-v'],
                project, 120, local_env(root))
        command(root, 'numerical-checks', [sys.executable, project/'e1_d16a_local.py', '_numerical', '--output', root/'numerical.json'],
                project, 120, local_env(root))
        checked(root)
        verify_environment(root, project, 'environment-after-readiness')
        status['status'] = 'READY_FOR_REVIEW'
    except BaseException as error:
        status['errors'].append(str(error) or type(error).__name__)
    write(root/'readiness.json', status)
    if status['status'] == 'READY_FOR_REVIEW':
        write(root/'approval-template.json', approval_template(root))
    package(root, 'readiness')
    require(status['status'] == 'READY_FOR_REVIEW', 'readiness failed; return the error archive; do not retry in this root')


def stop(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=2)
        return
    except (ProcessLookupError, subprocess.TimeoutExpired):
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def supervise(root, project, kappa, approval_path, approval_sha):
    case = root/f'kappa-{kappa}'
    case.mkdir()  # A failed or unresolved attempt permanently consumes this case.
    with (case/'reviewed-approval.json').open('xb') as stream:
        stream.write(approval_path.read_bytes())
    require(proof(case/'reviewed-approval.json')['sha256'] == approval_sha, 'copied reviewed approval changed')
    launch = {'kappa': kappa, 'parent_pid': os.getpid(), 'approval_path': str(case/'reviewed-approval.json'),
              'original_approval_path': str(approval_path),
              'approval_sha256': approval_sha, 'config': proof(root/'config.json'),
              'session': proof(root/'session.json'), 'limits': LIMITS}
    write(case/'launch.json', launch)
    process = None
    started = time.monotonic()
    peak, error, result = 0, None, None
    try:
        with (case/'worker.stdout').open('xb') as out, (case/'worker.stderr').open('xb') as err:
            process = subprocess.Popen([sys.executable, str(project/'e1_d16a_sampling.py'), '--root', str(root), '--kappa', str(kappa)],
                                       cwd=project, env=local_env(root), stdout=out, stderr=err, start_new_session=True)
            while process.poll() is None:
                require(time.monotonic()-started <= LIMITS['stiffness_seconds'], 'per-stiffness wall limit exceeded')
                try:
                    peak = max(peak, process_rss(process.pid)+process_rss(os.getpid()))
                except FileNotFoundError:
                    pass  # Process exited between /proc reads.
                require(peak <= LIMITS['rss_bytes'], 'maximum reference RSS exceeded')
                require(case_bytes(root, kappa) <= LIMITS['output_bytes'], 'maximum reference output exceeded')
                resource_preflight(root)
                progress = case/'progress.json'
                if progress.exists():
                    item = load(progress)
                    if item['active']:
                        require(time.monotonic()-item['started_monotonic'] <= LIMITS['batch_seconds'], 'batch wall limit exceeded')
                time.sleep(.05)
            require(process.returncode == 0, 'reference worker failed')
        require(time.monotonic()-started <= LIMITS['stiffness_seconds'], 'per-stiffness wall limit exceeded')
        require(case_bytes(root, kappa) <= LIMITS['output_bytes']-65536, 'output cap: no room for completion record')
        result = load(case/'worker-result.json')
        require(result['config'] == proof(root/'config.json') and result['kappa'] == kappa, 'worker result binding differs')
        require(result['peak_host_rss_bytes'] <= LIMITS['rss_bytes'], 'worker RSS high-water exceeded')
        peak = max(peak, result['peak_host_rss_bytes']+process_rss(os.getpid()))
        require(peak <= LIMITS['rss_bytes'], 'combined supervisor/worker RSS high-water exceeds limit')
        authenticate_case(root, kappa, incomplete_ok=True)
        remaining = LIMITS['stiffness_seconds']-(time.monotonic()-started)
        require(remaining > 0, 'per-stiffness wall budget exhausted during authentication')
        verify_environment(root, project, f'environment-after-kappa-{kappa}', min(120, remaining))
        require(time.monotonic()-started <= LIMITS['stiffness_seconds'], 'per-stiffness wall limit exceeded after authentication')
        require(case_bytes(root, kappa) <= LIMITS['output_bytes']-65536, 'output cap exceeded by case authentication')
    except BaseException as caught:
        error = str(caught) or type(caught).__name__
        if process is not None:
            stop(process)
    completion = {'status': 'FAILED' if error else result['status'], 'error': error,
                  'kappa': kappa, 'launch': proof(case/'launch.json'),
                  'supervised_wall_seconds': time.monotonic()-started, 'peak_host_rss_bytes': peak,
                  'resource_scope': '1200 s includes supervised worker and post-run authentication; RSS is conservative supervisor+worker high-water sum; case output includes stiffness-specific metadata/logs; shared readiness/return packets separate',
                  'files': {str(p.relative_to(case)): proof(p) for p in sorted(case.iterdir()) if p.is_file()}}
    write(case/'completion.json', completion)
    print('COMPLETION', case/'completion.json', proof(case/'completion.json')['sha256'], flush=True)
    require(error is None and completion['status'] == 'PRECISION_RESOLVED_NOMINAL',
            'reference failed or precision unresolved; preserve evidence and return results, no retry')


def authenticate_case(root, kappa, incomplete_ok=False):
    """Check approved identities, exact ledger/count coverage and all file hashes."""
    session, project = checked(root)
    case = root/f'kappa-{kappa}'
    launch = load(case/'launch.json')
    approved(root, Path(launch['approval_path']), launch['approval_sha256'])
    require(launch['config'] == proof(root/'config.json') and launch['session'] == proof(root/'session.json')
            and launch['limits'] == LIMITS and launch['kappa'] == kappa, 'launch/configuration binding changed')
    if not incomplete_ok:
        completion = load(case/'completion.json')
        require(completion['launch'] == proof(case/'launch.json'), 'completion launch mismatch')
        actual = {str(p.relative_to(case)): proof(p) for p in sorted(case.iterdir()) if p.is_file() and p.name != 'completion.json'}
        require(actual == completion['files'], 'case file inventory changed')
        if completion['status'] == 'FAILED':
            return completion  # Preserve authenticated failure, never relabel as complete.
    result = load(case/'worker-result.json')
    require(result['config'] == proof(root/'config.json') and result['kappa'] == kappa
            and result['quantiles'] == proof(case/'quantiles.json'), 'worker result mismatch')
    selected = load(case/'selection.json')['selected_count']
    require(selected is None or selected in configuration()['final_grid'], 'non-grid final count')
    counts = result['actual_counts']
    require(counts == {'calibration': 65536, 'pilot': 8192, 'final': selected or 0}, 'phase count mismatch')
    seed_identities = set()
    for phase, count in ((1, 65536), (2, 8192), (3, selected or 0)):
        path = case/f'phase-{phase}-batches.jsonl'
        if count == 0:
            require(not path.exists() and not (case/f'phase-{phase}-xy.npy').exists(), 'unselected final data exists')
            continue
        with path.open() as stream:
            rows = [json.loads(line) for line in stream]
        require(len(rows) == count//512, 'missing/extra batch')
        for index, row in enumerate(rows):
            entropy = [721610000, kappa, phase, index]
            require(row['seed_entropy'] == entropy and row['phase'] == phase and row['batch'] == index
                    and row['count'] == 512 and row['wall_seconds'] <= 30, 'batch identity/count/time mismatch')
            identity = tuple(row['seed_generated_uint32'])
            require(len(identity) == 4 and identity not in seed_identities, 'duplicate seed identity')
            seed_identities.add(identity)
        require((case/f'phase-{phase}-xy.npy').is_file(), 'scalar evidence missing')
    assessment = load(case/'assessment.json')
    require(assessment['status'] == result['status'], 'assessment/result disagreement')
    if not incomplete_ok:
        require(completion['status'] == result['status'], 'completion/result disagreement')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    ready = sub.add_parser('readiness')
    ready.add_argument('--evidence-parent', type=Path, required=True)
    for name in ('preflight', 'run', 'results', 'package-readiness'):
        item = sub.add_parser(name)
        item.add_argument('--root', type=Path, required=True)
        if name == 'run':
            item.add_argument('--kappa', type=int, choices=(0, 10), required=True)
            item.add_argument('--approval', type=Path, required=True)
            item.add_argument('--approval-sha256', required=True)
            item.add_argument('--execute-reviewed-reference', action='store_true', required=True)
    for name in ('_environment', '_numerical', '_verify-case'):
        item = sub.add_parser(name)
        item.add_argument('--output', type=Path, required=True)
        if name == '_verify-case':
            item.add_argument('--root', type=Path, required=True)
            item.add_argument('--kappa', type=int, choices=(0, 10), required=True)
    args = parser.parse_args()
    if args.action == 'readiness':
        readiness(args)
    elif args.action == '_environment':
        write(args.output, environment())
    elif args.action == '_numerical':
        from e1_d16a_reference import numerical_checks
        write(args.output, numerical_checks())
    elif args.action == '_verify-case':
        from e1_d16a_sampling import verify_saved
        write(args.output, verify_saved(args.root.resolve(), args.kappa))
    else:
        root = args.root.expanduser().resolve()
        session, project = checked(root)
        require(str(Path(sys.executable).resolve()) == session['python'], 'use original readiness Python executable')
        if args.action == 'package-readiness':
            package(root, 'readiness')
        elif args.action == 'preflight':
            stamp = str(time.time_ns())
            env = verify_environment(root, project, 'environment-preflight-'+stamp)
            path = root/('preflight-'+stamp+'.json')
            write(path, dict(resource_preflight(root), environment=env))
            print(path)
        elif args.action == 'run':
            approval = args.approval.expanduser().resolve()
            approved(root, approval, args.approval_sha256)
            lock = root/'reference-running.json'
            write(lock, {'pid': os.getpid(), 'kappa': args.kappa})
            try:
                verify_environment(root, project, f'environment-before-kappa-{args.kappa}')
                write(root/f'preflight-kappa-{args.kappa}.json', resource_preflight(root))
                supervise(root, project, args.kappa, approval, args.approval_sha256)
            finally:
                lock.unlink()
        elif args.action == 'results':
            require(not (root/'reference-running.json').exists(), 'reference still active/interrupted; stop for review')
            summary = {'status': 'AUTHENTICATED_RESULTS', 'cases': {}, 'errors': []}
            stamp = str(time.time_ns())
            try:
                for kappa in (0, 10):
                    if (root/f'kappa-{kappa}'/'completion.json').exists():
                        result = authenticate_case(root, kappa)
                        summary['cases'][str(kappa)] = result['status']
                        if result['status'] != 'FAILED':
                            verify_environment(root, project, f'environment-results-kappa-{kappa}-{stamp}')
                            command(root, f'authenticate-kappa-{kappa}-{stamp}', [sys.executable, project/'e1_d16a_local.py',
                                    '_verify-case', '--root', root, '--kappa', str(kappa), '--output', root/f'authentication-kappa-{kappa}-{stamp}.json'],
                                    project, 120, local_env(root))
                            require(case_bytes(root, kappa) <= LIMITS['output_bytes'], 'case output cap exceeded during results authentication')
                    else:
                        summary['cases'][str(kappa)] = 'INCOMPLETE_OR_NOT_RUN'
                if any(value != 'PRECISION_RESOLVED_NOMINAL' for value in summary['cases'].values()):
                    summary['status'] = 'REFERENCE_INCOMPLETE_OR_UNRESOLVED'
            except BaseException as error:
                summary['status'] = 'AUTHENTICATION_FAILED'
                summary['errors'].append(str(error) or type(error).__name__)
            write(root/f'results-{stamp}.json', summary)
            package(root, 'results')
            require(summary['status'] == 'AUTHENTICATED_RESULTS', 'reference incomplete, unresolved or authentication failed; return packet for review')


if __name__ == '__main__':
    main()
