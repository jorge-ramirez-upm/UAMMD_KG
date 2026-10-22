#!/usr/bin/env python3
"""Local D1.5 evidence handoff. No default action; never creates authorization.

Uses the frozen host runner for every build, probe, execution and authentication.
Only readiness launches tests. Packaging uses the standard library exclusively.
"""
import argparse
import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

BASE = '7a2d75a4f55976f1f36d5880c81e7e6a3ec8edda'
SCIENCE = '0dea651b58171a72206774bcebb2f4c74960069b'
MANIFEST_SHA = '4c6805221db1ddf3d3ffaa6ae62f2f890150b6c967214be97642546941454dc9'
GPU = 'GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274'
PROJECT = Path(__file__).resolve().parent
REL = Path('examples/slip-springs')
CPU_TESTS = ('test_e1_d15_local.py', 'test_e1_d15_preparation.py',
             'test_e1_d14_phase_b.py', 'test_e1_d13_phase_a.py',
             'test_e1_d12_plan.py', 'test_e1_d1_pilot.py')
EXPECTED_BLOCKER = 'independent approval and explicit resource budgets required'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def write(path, value):
    with Path(path).open('xb') as stream:
        stream.write(encoded(value))


def unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON key: ' + key)
        value[key] = item
    return value


def documents(path):
    require(path.stat().st_size <= 4 * 1024 * 1024, 'oversized JSON: ' + str(path))
    decoder = json.JSONDecoder(object_pairs_hook=unique_pairs,
                               parse_constant=lambda s: require(False, 'nonfinite JSON: ' + s))
    body = path.read_text().strip()
    result = []
    while body:
        value, end = decoder.raw_decode(body)
        result.append(value)
        body = body[end:].strip()
    return result


def load(path):
    result = documents(Path(path))
    require(len(result) == 1 and isinstance(result[0], dict), 'one JSON object required: ' + str(path))
    return result[0]


def proof(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'missing/nonregular evidence: ' + str(path))
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return {'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def git(repo, *args):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_ASKPASS='/bin/false',
               SSH_ASKPASS='/bin/false', GCM_INTERACTIVE='Never',
               GIT_SSH_COMMAND='ssh -oBatchMode=yes -oConnectTimeout=10')
    return subprocess.check_output(['git', '-C', str(repo), *args], env=env,
                                   timeout=45, stderr=subprocess.PIPE).decode().strip()


def clean(repo):
    require(not git(repo, 'status', '--porcelain', '--untracked-files=all'), 'worktree is not clean: ' + str(repo))


def checked_session(root):
    session = load(root / 'session.json')
    require(session['root'] == str(root), 'evidence moved; approved absolute paths must persist')
    project = Path(session['project'])
    require(project == root / 'preparation' / REL, 'incorrect preparation checkout')
    require(git(project, 'rev-parse', 'HEAD') == session['preparation_commit'], 'preparation revision changed')
    clean(project)
    require(proof(project / 'e1_d15_local.py') == session['utility'], 'handoff utility changed')
    require(proof(project / 'e1_d15_config/benchmark/manifest.json')['sha256'] == MANIFEST_SHA,
            'frozen benchmark changed')
    return session, project


def command(root, name, argv, cwd, timeout, env):
    """Bound the entire delegated process group; no shell, retries or resume."""
    logs = root / 'logs'
    logs.mkdir(exist_ok=True)
    started = time.monotonic()
    record = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'timeout_seconds': timeout}
    process = None
    try:
        with (logs / (name + '.stdout')).open('xb') as out, (logs / (name + '.stderr')).open('xb') as err:
            process = subprocess.Popen(record['argv'], cwd=cwd, env=env, stdout=out,
                                       stderr=err, start_new_session=True)
            record['exit_code'] = process.wait(timeout=timeout)
            require(record['exit_code'] == 0, name + ' failed; inspect ' + str(logs))
    except BaseException as error:
        record['error'] = str(error) or type(error).__name__
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        raise
    finally:
        record['wall_seconds'] = time.monotonic() - started
        write(logs / (name + '.command.json'), record)
    return logs / (name + '.stdout')


def local_env(root):
    return {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'TZ': 'UTC',
            'PYTHONDONTWRITEBYTECODE': '1', 'OPENBLAS_NUM_THREADS': '1',
            'OMP_NUM_THREADS': '1', 'TMPDIR': str(root / 'scratch')}


def host_args(project):
    return [sys.executable, str(project / 'e1_d15_host.py')]


def manifest_args(project):
    return ['--manifest', str(project / 'e1_d15_config/benchmark/manifest.json'),
            '--manifest-sha256', MANIFEST_SHA]


def build_args(root, project, build_sha):
    return manifest_args(project) + ['--build-receipt', str(root / 'build/build.json'),
            '--build-sha256', build_sha, '--gpu-uuid', GPU,
            '--output-root', str(root / 'benchmark-campaign')]


def readiness(args):
    parent = args.evidence_parent.expanduser().resolve()
    require(not any(parent.is_relative_to(Path(p)) for p in ('/tmp', '/var/tmp', '/dev/shm')),
            'choose durable storage, not tmpfs or a temporary directory')
    parent.mkdir(parents=True, exist_ok=True)
    require(not any((p / '.git').exists() for p in (parent, *parent.parents)), 'evidence must be outside Git repositories')
    root = Path(tempfile.mkdtemp(prefix='readiness-', dir=parent))
    (root / 'scratch').mkdir()
    print('D15_ROOT=' + str(root), flush=True)
    state = {'schema': 'e1-d15-local-readiness-v1', 'root': str(root), 'status': 'failed',
             'manifest_sha256': MANIFEST_SHA, 'scientific_acceptance': None}
    try:
        repo = Path(git(PROJECT, 'rev-parse', '--show-toplevel'))
        clean(repo)
        require(git(repo, 'branch', '--show-current') == 'slip-springs', 'slip-springs checkout required')
        head = git(repo, 'rev-parse', 'HEAD')
        require(git(repo, 'merge-base', BASE, head) == BASE, 'unexpected starting history')
        origin = git(repo, 'remote', 'get-url', 'origin')
        require(origin in ('git@github.com:jorge-ramirez-upm/UAMMD_KG.git',
                           'https://github.com/jorge-ramirez-upm/UAMMD_KG.git'), 'wrong origin')
        remote = git(repo, 'ls-remote', '--exit-code', 'origin', 'refs/heads/slip-springs')
        require(remote.split() == [head, 'refs/heads/slip-springs'], 'local HEAD differs from remote; update before readiness')
        common = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
        require(not any(common.is_relative_to(Path(p)) for p in ('/tmp', '/var/tmp', '/dev/shm')),
                'Git common directory must remain on durable storage')
        env = local_env(root)
        for name, commit in (('preparation', head), ('source', SCIENCE)):
            command(root, 'checkout-' + name, ['git', '-C', repo, 'worktree', 'add', '--detach', root / name, commit],
                    repo, 60, env)
        project = root / 'preparation' / REL
        session = {'schema': 'e1-d15-local-session-v1', 'root': str(root), 'project': str(project),
                   'preparation_commit': head, 'source_commit': SCIENCE, 'origin': origin,
                   'remote_head': remote, 'git_common_dir': str(common),
                   'utility': proof(project / 'e1_d15_local.py'), 'python': sys.executable}
        write(root / 'session.json', session)
        checked_session(root)
        command(root, 'projections', [sys.executable, project / 'e1_d15_prepare.py',
                '--project', root / 'projections.json'], project, 120, env)
        require((root / 'projections.json').read_bytes() == (project / 'e1_d15_projections.json').read_bytes(),
                'projection differs from frozen preparation')
        for test in CPU_TESTS:
            command(root, test.removesuffix('.py'), [sys.executable, project / 'tests' / test], project, 120, env)
        result = command(root, 'build', host_args(project) + ['build'] + manifest_args(project) +
                         ['--source-tree', root / 'source', '--build-root', root / 'build',
                          '--cuda-home', args.cuda_home.resolve(), '--arch', 'sm_86', '--cxx', '/usr/bin/g++'],
                         project, 480, env)
        build = load(result)
        require(proof(root / 'build/build.json')['sha256'] == build['build_receipt_sha256'], 'build result mismatch')
        state['build'] = build
        command(root, 'tiny-gpu', [sys.executable, project / 'tests/test_e1_d14_phase_b_technical.py',
                                  root / 'build/bin/semiflexible'], project, 120, env)
        result = command(root, 'preflight', host_args(project) + ['preflight'] +
                         build_args(root, project, build['build_receipt_sha256']), project, 180, env)
        preflight = load(result)
        write(root / 'preflight.json', preflight)
        state['preflight_blockers'] = preflight['blockers']
        require(preflight['execution_authorized'] is False and preflight['blockers'] == [EXPECTED_BLOCKER]
                and len(preflight['environment_sha256']) == 64, 'unexpected preflight blockers/identity; readiness failed')
        checked_session(root)
        state.update(status='ready-for-independent-review', environment_sha256=preflight['environment_sha256'])
    except BaseException as error:
        state['error'] = str(error) or type(error).__name__
    finally:
        state['artifacts'] = {str(p): proof(p) for p in sorted((root / 'logs').glob('*')) if p.stat().st_size}
        for p in (root / 'session.json', root / 'projections.json', root / 'preflight.json',
                  root / 'build/build.json', root / 'build/build.log'):
            if p.is_file() and p.stat().st_size:
                state['artifacts'][str(p)] = proof(p)
        write(root / 'readiness.json', state)
        if state['status'] == 'ready-for-independent-review':
            # Populate identities only. Both human decision gates remain false/null.
            review = load(project / 'e1_d15_readiness.template.json')
            review.update(manifest_sha256=MANIFEST_SHA, build_receipt_sha256=state['build']['build_receipt_sha256'],
                          artifacts=dict(state['artifacts'], **{str(root / 'readiness.json'): proof(root / 'readiness.json')}))
            write(root / 'readiness-review.DRAFT.json', review)
            approval = load(project / 'e1_d15_config/benchmark/approval.template.json')
            approval.update(build_receipt_sha256=state['build']['build_receipt_sha256'],
                            environment_sha256=state['environment_sha256'], gpu_uuid=GPU,
                            output_root=str(root / 'benchmark-campaign'))
            write(root / 'benchmark-approval.DRAFT.json', approval)
        package(root, 'readiness')
        print('Readiness: ' + state['status'] + '; ' + state.get('error', EXPECTED_BLOCKER), flush=True)
    return 0 if state['status'] == 'ready-for-independent-review' else 1


def ready(root):
    session, project = checked_session(root)
    state = load(root / 'readiness.json')
    require(state['status'] == 'ready-for-independent-review', 'readiness failed or incomplete')
    for path, expected in state['artifacts'].items():
        require(proof(path) == expected, 'readiness artifact changed: ' + path)
    return state, project


def benchmark(args):
    require(args.execute_reviewed_benchmark, 'separate --execute-reviewed-benchmark flag required')
    root = args.root.resolve()
    state, project = ready(root)
    approval_path = args.approval.resolve()
    require(proof(approval_path)['sha256'] == args.approval_sha256, 'externally trusted approval SHA mismatch')
    approval = load(approval_path)
    require(approval['execution_authorized'] is True and approval['manifest_sha256'] == MANIFEST_SHA
            and approval['build_receipt_sha256'] == state['build']['build_receipt_sha256']
            and approval['environment_sha256'] == state['environment_sha256']
            and approval['gpu_uuid'] == GPU and approval['output_root'] == str(root / 'benchmark-campaign'),
            'approval does not bind this benchmark/readiness')
    require(not (root / 'benchmark-campaign').exists() and not (root / 'benchmark-launch.json').exists(),
            'fresh campaign required; no retries or resume')
    limit = approval['limits']['aggregate_seconds']
    require(type(limit) in (int, float) and math.isfinite(limit) and 0 < limit <= 3600, 'invalid aggregate wall budget')
    launch = {'schema': 'e1-d15-local-launch-v1', 'status': 'started', 'approval_path': str(approval_path),
              'approval_sha256': args.approval_sha256, 'readiness': proof(root / 'readiness.json')}
    write(root / 'benchmark-launch.json', launch)
    # A separate immutable result records success/failure; the launch cannot be reused.
    result = {'status': 'failed'}
    try:
        out = command(root, 'benchmark', host_args(project) + ['preflight'] +
                      build_args(root, project, state['build']['build_receipt_sha256']) +
                      ['--approval', approval_path, '--approval-sha256', args.approval_sha256,
                       '--authorize-d15-local-execution'], project, limit + 600, local_env(root))
        docs = documents(out)
        require(len(docs) == 2 and docs[0]['blockers'] == [] and docs[1]['status'] == 'completed'
                and docs[1]['root'] == str(root / 'benchmark-campaign'), 'missing authenticated completion result')
        result = docs[1]
    except BaseException as error:
        result['error'] = str(error) or type(error).__name__
        raise
    finally:
        write(root / 'benchmark-result.json', result)
        print('Preserve launch/result and evidence; no automatic retry. Stage C authenticates before summarizing.')


def summarize(args):
    root = args.root.resolve()
    _, project = ready(root)
    launch = load(root / 'benchmark-launch.json')
    result = load(root / 'benchmark-result.json')
    require(result['status'] == 'completed', 'benchmark incomplete; package failures without claiming authentication')
    require(proof(root / 'readiness.json') == launch['readiness'], 'readiness changed after approval')
    # Fresh output each invocation; repeated authentication never overwrites a report.
    report = root / ('benchmark-summary-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    out = command(root, report.stem, host_args(project) + ['summarize'] + manifest_args(project) +
                  ['--root', root / 'benchmark-campaign', '--approval-sha256', launch['approval_sha256'],
                   '--completion-sha256', result['completion_sha256'], '--report', report], project, 600, local_env(root))
    receipt = load(out)
    require(proof(report)['sha256'] == receipt['sha256'], 'authenticated summary changed')
    write(report.with_suffix('.receipt.json'), {'report': str(report), 'file': proof(report),
          'launch': proof(root / 'benchmark-launch.json'), 'result': proof(root / 'benchmark-result.json')})
    package(root, 'benchmark')


def approval_draft(args):
    root = args.root.resolve()
    state, _ = ready(root)
    review = args.review.resolve()
    value = load(review)
    require(value['schema'] == 'e1-d15-readiness-review-v1'
            and value['manifest_sha256'] == MANIFEST_SHA
            and value['build_receipt_sha256'] == state['build']['build_receipt_sha256']
            and value['all_local_preparation_checks_reviewed'] is True
            and isinstance(value['review_reference'], str) and value['review_reference'].strip(),
            'separately reviewed readiness record required')
    expected = dict(state['artifacts'], **{str(root / 'readiness.json'): proof(root / 'readiness.json')})
    require(value['artifacts'] == expected, 'review must bind all collected readiness artifacts')
    draft = load(root / 'benchmark-approval.DRAFT.json')
    require(draft['execution_authorized'] is False and draft['approval_reference'] is None
            and all(v is None for v in draft['limits'].values()), 'original false approval draft changed')
    draft['readiness_review'] = {'path': str(review), 'sha256': proof(review)['sha256']}
    path = root / 'benchmark-approval.LINKED-DRAFT.json'
    write(path, draft)
    print(str(path) + '\nStill execution_authorized=false; reviewer must decide all budgets and authorization.')


def compact_file(path, limit=65536):
    expected = proof(path)
    with path.open('rb') as stream:
        if expected['bytes'] <= limit:
            body = stream.read()
        else:
            body = stream.read(limit // 2)
            stream.seek(-limit // 2, 2)
            body += b'\n[TRUNCATED: full local file identified in contents.json]\n' + stream.read()
    return body, expected


def package(root, kind):
    """Allowlisted small artifacts only; original evidence is never altered."""
    root = root.resolve()
    require(root.is_dir(), 'evidence root missing')
    names = ['session.json', 'readiness.json', 'projections.json', 'preflight.json', 'readiness-review.DRAFT.json',
             'benchmark-approval.DRAFT.json', 'benchmark-approval.LINKED-DRAFT.json', 'build/build.json', 'build/build.log']
    paths = [root / n for n in names] + sorted((root / 'logs').glob('*'))
    project = root / 'preparation' / REL
    paths += [project / n for n in ('e1_d15_config/benchmark/manifest.json',
              'e1_d15_observed_rows.json', 'e1_d15_local.py', 'tests/test_e1_d15_local.py',
              'E1_STAGE_D15_LOCAL_EXECUTION_HANDOFF.md')]
    lines = ['D1.5 LOCAL ' + kind.upper() + ' RETURN', 'Evidence root: ' + str(root),
             'No scientific acceptance or execution authorization is conferred by this archive.']
    if (root / 'readiness.json').is_file():
        state = load(root / 'readiness.json')
        lines += ['Readiness: ' + state['status'], 'Readiness error: ' + state.get('error', 'none'),
                  'Preflight blockers: ' + str(state.get('preflight_blockers', 'not reached')),
                  'Build identity: ' + json.dumps(state.get('build', 'not reached'), sort_keys=True)]
    else:
        lines += ['Readiness: INCOMPLETE (readiness.json missing); no success claim.']
    for log in sorted((root / 'logs').glob('*.command.json')):
        step = load(log)
        lines.append('%s: exit=%s; wall=%.3fs; error=%s' %
                     (log.stem, step.get('exit_code', 'not exited'), step['wall_seconds'], step.get('error', 'none')))
    if (root / 'logs/preflight.stdout').is_file():
        try:
            flight = load(root / 'logs/preflight.stdout')
            lines += ['Environment SHA256: ' + str(flight.get('environment_sha256')),
                      'Observed readiness resources: ' + json.dumps(flight.get('observed_resources'), sort_keys=True),
                      'GPU identity: ' + GPU]
        except (ValueError, OSError):
            lines += ['Preflight output incomplete/invalid; inspect preserved log.']
    if kind == 'benchmark':
        paths += [root / n for n in ('benchmark-launch.json', 'benchmark-result.json')]
        campaign = root / 'benchmark-campaign'
        paths += [campaign / n for n in ('manifest.json', 'approval.json', 'build.json', 'campaign.json',
                                        'status.json', 'campaign_complete.json')]
        paths += sorted(campaign.glob('runs/*/execution.json')) + sorted(campaign.glob('runs/*/process.json'))
        reports = sorted(root.glob('benchmark-summary-*.receipt.json'))
        if reports:
            receipt = load(reports[-1])
            report = Path(receipt['report'])
            require(report.parent == root and proof(report) == receipt['file'], 'summary identity changed')
            require(proof(root / 'benchmark-launch.json') == receipt['launch']
                    and proof(root / 'benchmark-result.json') == receipt['result'], 'summary anchors changed')
            paths += [report, reports[-1]]
            lines += ['Whole-cohort authentication passed when this frozen-host summary was produced: ' + str(report),
                      'Raw CSV evidence is referenced by authenticated execution receipts; not bundled or reauthenticated by packaging.']
            observed = load(project / 'e1_d15_observed_rows.json')['timing_measurements']
            for item in load(report)['runs']:
                run, meta = item['run'], item['metadata']
                updates = run['M'] * (run['N'] + 1) * run['steps']
                lines.append('%s: integration %.3f, production %.3f ns/bead/step; events/s %.3f; output %d bytes; peak RSS %d bytes' %
                             (run['id'], 1e9 * meta['integration_seconds'] / updates,
                              1e9 * meta['production_wall_seconds'] / updates,
                              item['accepted_events_per_production_second'], item['raw_output_bytes'], item['peak_host_rss_bytes']))
                observer = item['observer']
                lines.append('  child %.6fs; initialization %.6fs; final output %.6fs; observer exclusive %.6fs (%.2f%% of production), wall %.6fs, transfer %.6fs; attempts/s %.3f' %
                             (item['child_wall_seconds'], meta['initialization_seconds'], meta['final_output_seconds'],
                              observer['exclusive_seconds'], 100 * observer['exclusive_seconds'] / meta['production_wall_seconds'],
                              observer['observer_wall_seconds'], observer['transfer_seconds'],
                              item['hopping']['attempts'] / meta['production_wall_seconds']))
                if run['kappa'] == 10:
                    old = observed[str(run['dt'])]
                    old_updates = old['M'] * (old['N'] + 1) * round(old['T'] / float(run['dt']))
                    old_cost = 1e9 * old['production_seconds'] / old_updates
                    lines.append('  M64 recorded production cost %.3f ns/bead/step; M256/M64 cost ratio %.3f' %
                                 (old_cost, (1e9 * meta['production_wall_seconds'] / updates) / old_cost))
            lines += ['M64 comparison: committed hash-bound Phase A measurements, NOT freshly authenticated raw M64 evidence.',
                      'M64 T=.25 vs M256 T=.1 and different observation schedules: descriptive costs, not a scaling law.',
                      'No matching flexible M64 baseline is asserted. Observer timers are nested, not additive.',
                      'Per-run observer/event/timing details are in the summary; headroom in execution receipts.',
                      'GPU peak usage is unavailable (null); before/after free-memory readings are not peaks.']
        else:
            lines += ['FAILED/INCOMPLETE OR NOT YET AUTHENTICATED: no four-run performance claim. Run summarize after success.']
    payload, inventory = {}, {}
    for path in sorted(set(paths)):
        if not path.exists():
            continue
        require(path.is_relative_to(root), 'archive artifact escaped evidence root')
        name = str(path.relative_to(root))
        # JSON receipts/scripts are complete; only logs may be shortened explicitly.
        limit = 4 * 1024 * 1024 if path.suffix in ('.json', '.py', '.md') else 65536
        body, original = compact_file(path, limit)
        require(path.suffix not in ('.json', '.py', '.md') or len(body) == original['bytes'], 'mandatory artifact too large')
        payload[name] = body
        inventory[name] = {'local_path': str(path), 'original': original,
                           'archived_bytes': len(body), 'archived_sha256': hashlib.sha256(body).hexdigest(),
                           'truncated': len(body) != original['bytes']}
    payload['SUMMARY.txt'] = ('\n'.join(lines) + '\n').encode()
    payload['contents.json'] = encoded({'schema': 'e1-d15-return-contents-v1', 'kind': kind,
                                       'evidence_root': str(root), 'files': inventory})
    payload['SHA256SUMS'] = ''.join(hashlib.sha256(body).hexdigest() + '  ' + name + '\n'
                                  for name, body in sorted(payload.items())).encode()
    require(sum(map(len, payload.values())) <= 8 * 1024 * 1024, 'return packet exceeds 8 MiB; retain evidence and review')
    returns = root / 'returns'
    returns.mkdir(exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=kind + '-return-', suffix='.tar.gz', dir=returns)
    os.close(fd)
    archive = Path(name)
    with tarfile.open(archive, 'w:gz') as tar:
        for name, body in sorted(payload.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(body), 0o600
            tar.addfile(info, io.BytesIO(body))
    digest = proof(archive)['sha256']
    with archive.with_name(archive.name + '.sha256').open('x') as stream:
        stream.write(digest + '  ' + archive.name + '\n')
    print('RETURN_ARCHIVE=' + str(archive) + '\nSHA256=' + digest, flush=True)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('readiness', help='LOCAL tests/build/tiny fixtures/read-only preflight; NO benchmark')
    p.add_argument('--evidence-parent', type=Path, required=True)
    p.add_argument('--cuda-home', type=Path, default=Path('/usr/local/cuda'))
    b = sub.add_parser('benchmark', help='existing four-cell runner, separately approved benchmark ONLY')
    b.add_argument('--approval', type=Path, required=True)
    b.add_argument('--approval-sha256', required=True)
    b.add_argument('--execute-reviewed-benchmark', action='store_true')
    s = sub.add_parser('summarize', help='authenticate via frozen host runner; package results; NO simulation')
    d = sub.add_parser('approval-draft', help='link an independent readiness review; decision stays FALSE')
    d.add_argument('--review', type=Path, required=True)
    p = sub.add_parser('package', help='small evidence archive only; NO tests/probe/build/benchmark')
    p.add_argument('--kind', choices=('readiness', 'benchmark'), required=True)
    for child in (b, s, d, p):
        child.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    def stop(signum, frame):
        raise KeyboardInterrupt('signal ' + str(signum))
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGHUP, stop)
    try:
        if args.action == 'package':
            package(args.root, args.kind)
        else:
            return globals()[args.action.replace('-', '_')](args) or 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        print('D1.5 LOCAL STOP: ' + (str(error) or type(error).__name__), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
