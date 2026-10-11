"""Recover the original frozen segment; never repeat partial or completed MD."""
import os
import getpass
from pathlib import Path
import socket
import subprocess
import time

import kg_assoc_e2 as e2

campaign = e2.campaign
require = e2.require


def authenticate(root, attempt):
    plan = e2.check_plan(root, attempt)
    require(not plan['smoke'], 'recovery is for an ordinary E2 segment only')
    e2.clean_tree()
    require(subprocess.run(['git', 'merge-base', '--is-ancestor', plan['git_sha'], campaign.git_sha()],
                           cwd=campaign.REPOSITORY_ROOT, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL).returncode == 0,
            'original plan commit is not an ancestor of recovery code')
    require(e2.scientific_source_hashes(plan['source_sha256']) ==
            e2.scientific_source_hashes(e2.sources()), 'scientifically relevant sources changed')
    e2.check_hashes(plan['executable_sha256'])
    if plan.get('build'):
        e2.check_hashes(plan['build']['executable_sha256'])
        e2.check_hashes(plan['build']['build_log_sha256'])
    e2.approval_record(attempt / 'approval.json', attempt / 'plan.json', 'e2_segment')
    require(not (attempt / '.launch.lock').exists(), 'original launch lock present; recovery refused')
    return plan


def select_attempt(root, system):
    paths = []
    for path in (root / 'banks/e2_attempts' / campaign.e2_bank_id(system)).glob('*/plan.json'):
        plan = campaign.load_json(path)
        if plan.get('smoke') is False and plan.get('system') == system:
            paths.append(path.parent)
    require(len(paths) == 1, 'recover requires exactly one ordinary attempt for this system; '
            'ambiguous attempts are never selected by timestamp')
    return paths[0]


def has_marker(path):
    if not path.is_file():
        return False
    with path.open() as stream:
        return any('STAR_ASSOCIATION_SMOKE PASS' in line for line in stream)


def started_evidence(attempt, entry):
    directory = Path(entry['output_prefix']).parent
    path = directory / 'started.json'
    if not path.exists():
        return None
    started = campaign.load_json(path)
    require(started['plan_sha256'] == campaign.sha256(attempt / 'plan.json') and
            started['approval_sha256'] == campaign.sha256(attempt / 'approval.json') and
            started['command'] == entry['command'], 'original start provenance differs')
    e2.check_hashes(started['smoke_sha256'])
    return started


def smoke_evidence(root, attempt, plan):
    for entry in plan['histories']:
        started = started_evidence(attempt, entry)
        if started:
            paths = [Path(p).parent for p in started['smoke_sha256'] if Path(p).name == 'plan.json']
            require(len(paths) == 1, 'original start lacks unique smoke evidence')
            return e2.matching_smoke(root, paths[0], plan)
    for path in sorted((root / 'banks/e2_attempts' / campaign.e2_bank_id(plan['system'])).glob('*/plan.json')):
        candidate = campaign.load_json(path)
        if candidate.get('smoke') and e2.smoke_code_compatible(candidate, plan):
            try:
                return e2.matching_smoke(root, path.parent, plan)
            except (ValueError, OSError, KeyError):
                continue
    raise ValueError('no authenticated matching smoke; recovery will not run a replacement smoke')


def preserved_marker(attempt, entry):
    directory = Path(entry['output_prefix']).parent
    if has_marker(directory / 'stdout.log'):
        return True
    root = Path(campaign.load_json(attempt / 'plan.json')['dataset_root'])
    for receipt in (root / 'banks/e2_recoveries').glob('*/*/r%03d/md_complete.json' % entry['replica']):
        record = campaign.load_json(receipt)
        if record.get('plan_sha256') != campaign.sha256(attempt / 'plan.json') or record.get('command') != entry['command']:
            continue
        auth = receipt.parent.parent / 'authorization.json'
        e2.approval_record(auth, attempt / 'plan.json', 'e2_recovery')
        require(campaign.sha256(auth) == record['authorization_sha256'], 'recovered MD authorization changed')
        e2.check_hashes(record['output_sha256'])
        if has_marker(Path(record['stdout'])):
            return True
    # A hard interruption can occur while hashing the new endpoint receipt. Treat this
    # orphan exactly like the original post-MD orphan: bound start + PASS + full validation.
    for start_path in (root / 'banks/e2_recoveries').glob('*/*/r%03d/started.json' % entry['replica']):
        started = campaign.load_json(start_path)
        if (started.get('plan_sha256') != campaign.sha256(attempt / 'plan.json') or
                started.get('command') != entry['command']):
            continue
        auth = start_path.parent.parent / 'authorization.json'
        e2.approval_record(auth, attempt / 'plan.json', 'e2_recovery')
        require(campaign.sha256(auth) == started.get('recovery_authorization_sha256'),
                'recovered start authorization changed')
        if has_marker(start_path.parent / 'stdout.log'):
            return True
    return False


def classify(attempt, entry):
    directory = Path(entry['output_prefix']).parent
    require(directory.resolve() == directory and directory.is_dir(),
            'replica directory is missing or redirects outside the original attempt')
    started = started_evidence(attempt, entry)
    complete_path = directory / 'complete.json'
    if complete_path.exists():
        complete = campaign.load_json(complete_path)
        require(complete['status'] == 'validated' and complete['plan_sha256'] ==
                campaign.sha256(attempt / 'plan.json') and complete['end_step'] == entry['end_step'],
                'original completion differs from plan')
        e2.check_hashes(complete['output_sha256'])
        require(started or complete.get('recovery_authorization'), 'completion lacks launch provenance')
        return 'validate_completed'
    outputs = [Path(entry['output_prefix'] + suffix) for suffix in e2.validation.OUTPUTS]
    if any(p.exists() for p in outputs) or any(directory.glob('state*')):
        require(started and all(p.is_file() for p in outputs) and preserved_marker(attempt, entry),
                'partial MD outputs present; refusing to rerun or overwrite this history')
        return 'validate_preserved'
    # Before-MD interruptions may leave administrative files, never simulation output.
    permitted = {'started.json', 'environment.json', 'incomplete.json', 'stdout.log', 'stderr.log'}
    require(all(p.name in permitted for p in directory.iterdir()), 'unrecognized pre-MD files')
    require(not any((directory / n).exists() and (directory / n).stat().st_size
                    for n in ('stdout.log', 'stderr.log')), 'nonempty MD logs without outputs; ambiguous execution')
    return 'run_missing'


def verify_authorization(recovery, attempt):
    path = recovery / 'authorization.json'
    record = e2.approval_record(path, attempt / 'plan.json', 'e2_recovery')
    e2.check_hashes({record['command_record']: record['command_record_sha256']})
    e2.check_hashes(record['preserved_sha256'])
    return path


def recover(root, attempt, recovery, invocation, journal):
    plan = authenticate(root, attempt)
    smoke_hashes = smoke_evidence(root, attempt, plan)
    decisions = [classify(attempt, e) for e in plan['histories']]
    # Freeze all existing bytes before validation/MD, including orphaned output and failure receipts.
    preserved = e2.hash_files([p for p in attempt.rglob('*') if p.is_file()])
    e2.exclusive_json(recovery / 'authorization.json', dict(
        schema_version=1, approved=True, purpose='e2_recovery',
        plan_sha256=campaign.sha256(attempt / 'plan.json'), reviewer=getpass.getuser(),
        approved_at=e2.timestamp(), authorization='explicit_user_cli_recovery_request',
        invocation=invocation, command_record=str(journal / 'request.json'),
        command_record_sha256=campaign.sha256(journal / 'request.json'),
        original_git_sha=plan['git_sha'], recovery_git_sha=campaign.git_sha(),
        original_approval_sha256=campaign.sha256(attempt / 'approval.json'),
        attempt=str(attempt), decisions=decisions, preserved_sha256=preserved,
        smoke_sha256=smoke_hashes, scope='original_plan_only_missing_histories',
        scientific_equilibrium_acceptance=False, host=socket.gethostname(), pid=os.getpid()))
    results = []
    # Validate every preserved endpoint before allocating any missing GPU work.
    for entry, decision in zip(plan['histories'], decisions):
        if decision != 'run_missing':
            _, _, validation = e2.validation.validate(entry, oracle=False)
            results.append((entry, decision, validation))
    for entry, decision in zip(plan['histories'], decisions):
        if decision == 'run_missing':
            authenticate(root, attempt)
            verify_authorization(recovery, attempt)
            e2.check_hashes(smoke_hashes)
            require(classify(attempt, entry) == 'run_missing', 'outputs appeared during recovery preflight')
            directory = Path(entry['output_prefix']).parent
            receipt = recovery / f"r{entry['replica']:03d}"
            e2.exclusive_json(receipt / 'started.json', dict(plan_sha256=campaign.sha256(attempt / 'plan.json'),
                command=entry['command'], recovery_authorization_sha256=campaign.sha256(recovery / 'authorization.json'),
                started_at=e2.timestamp(), host=socket.gethostname()))
            if not (directory / 'started.json').exists():
                e2.exclusive_json(directory / 'started.json', dict(
                    plan_sha256=campaign.sha256(attempt / 'plan.json'), command=entry['command'],
                    approval_sha256=campaign.sha256(attempt / 'approval.json'), smoke_sha256=smoke_hashes,
                    host=socket.gethostname(), started_at=e2.timestamp(), recovery=str(recovery)))
            start = time.monotonic()
            environment = subprocess.check_output(['nvidia-smi', '--query-gpu=name,uuid,driver_version',
                                                   '--format=csv,noheader'], text=True)
            e2.exclusive_json(receipt / 'environment.json', dict(gpu=environment, host=socket.gethostname()))
            # Logs for a fresh replica remain in the normal location; interrupted pre-MD logs stay untouched.
            log_directory = directory if not (directory / 'stdout.log').exists() and not (directory / 'stderr.log').exists() else receipt
            with (log_directory / 'stdout.log').open('x') as stdout, (log_directory / 'stderr.log').open('x') as stderr:
                process = subprocess.Popen(entry['command'], stdout=stdout, stderr=stderr)
                try:
                    require(process.wait() == 0, 'MD executable failed')
                except BaseException:
                    process.terminate()
                    process.wait()
                    raise
            require(has_marker(log_directory / 'stdout.log'), 'missing executable completion marker')
            e2.exclusive_json(receipt / 'md_complete.json', dict(
                plan_sha256=campaign.sha256(attempt / 'plan.json'), command=entry['command'],
                authorization_sha256=campaign.sha256(recovery / 'authorization.json'),
                stdout=str(log_directory / 'stdout.log'), output_sha256=e2.hash_files(
                    [Path(entry['output_prefix'] + suffix) for suffix in e2.validation.OUTPUTS] +
                    [log_directory / 'stdout.log', log_directory / 'stderr.log'])))
            authenticate(root, attempt)
            verify_authorization(recovery, attempt)
            _, _, validation = e2.validation.validate(entry, oracle=False)
            validation = dict(validation, recovery_wall_seconds=time.monotonic() - start)
            results.append((entry, decision, validation))
    authenticate(root, attempt)
    verify_authorization(recovery, attempt)
    receipts = []
    for entry, decision, validation in sorted(results, key=lambda item: item[0]['replica']):
        directory = Path(entry['output_prefix']).parent
        completion = directory / 'complete.json'
        if not completion.exists():
            evidence = [p for p in directory.iterdir() if p.is_file()]
            evidence += [p for p in (recovery / f"r{entry['replica']:03d}").glob('*') if p.is_file()]
            evidence += [recovery / 'authorization.json']
            e2.exclusive_json(completion, dict(status='validated',
                plan_sha256=campaign.sha256(attempt / 'plan.json'), end_step=entry['end_step'],
                validation=validation, finished_at=e2.timestamp(), wall_seconds=None,
                recovery_authorization=str(recovery / 'authorization.json'),
                original_git_sha=plan['git_sha'], recovery_git_sha=campaign.git_sha(),
                authorized_recovery_git_sha=campaign.load_json(recovery / 'authorization.json')['recovery_git_sha'],
                output_sha256=e2.hash_files(evidence)))
        receipt = dict(replica=entry['replica'], operation=decision, validation=validation,
                       completion_sha256=campaign.sha256(completion))
        e2.exclusive_json(recovery / f"r{entry['replica']:03d}/validated.json", receipt)
        receipts.append(receipt)
    e2.check_hashes(preserved)
    e2.verify(root, attempt)
    e2.exclusive_json(recovery / 'complete.json', dict(status='validated', attempt=str(attempt),
        original_git_sha=plan['git_sha'], recovery_git_sha=campaign.git_sha(),
        plan_sha256=campaign.sha256(attempt / 'plan.json'), histories=receipts,
        finished_at=e2.timestamp(), scientific_status='review_required'))
    return plan, receipts
