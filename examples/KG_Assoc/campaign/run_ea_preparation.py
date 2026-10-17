#!/usr/bin/env python3
"""User-run, restart-safe Ea6/8/10 preparation. No MD unless --execute is supplied."""
import argparse
import copy
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import kg_assoc_e2 as e2
import kg_assoc_e2_transfer as transfer
import run_e2

STEPS = 16000000
BUILD = 'ea_transfer_16m_20261017_v1'


def save(path, state):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    e2.exclusive_json(temporary, state)
    os.replace(temporary, path)


def jobs():
    return [dict(system=sid, replica=replica, status='pending', retired_attempts=[])
            for sid in transfer.TARGETS for replica in (1, 2, 3)]


def fresh_reservation(root):
    chemical, requested, effective, _ = transfer.streams_in_use(root)
    for path in [transfer.RESERVATIONS, *(root / 'banks/e2_seed_reservations').glob('*.json')]:
        for row in e2.campaign.load_json(path)['streams']:
            chemical.add(row['chemistry_seed'])
            requested.add(row['md_seed'])
            effective.add(e2.validation.effective_md_seed(row['md_seed']))
    original = e2.campaign.load_json(transfer.RESERVATIONS)
    offset = 500000
    while True:
        policy = copy.deepcopy(original)
        for row in policy['streams']:
            row['chemistry_seed'] += offset
            row['md_seed'] += offset
        seeds = [row[key] for row in policy['streams'] for key in ('chemistry_seed', 'md_seed')]
        kernels = [e2.validation.effective_md_seed(row['md_seed']) for row in policy['streams']]
        if (len(set(seeds)) == 24 and len(set(kernels)) == 12 and
                not set(seeds) & (chemical | requested) and not set(kernels) & effective):
            break
        offset += 100000
    identity = 'manual_ea16m_' + uuid.uuid4().hex
    policy.update(reservation_id=identity, purpose=(
        'User-run nine-history E2 preparation; unused format-required streams remain reserved. '
        'Interrupted runs are preserved; replacement histories use fresh reservations.'))
    path = root / 'banks/e2_seed_reservations' / (identity + '.json')
    e2.exclusive_json(path, policy)
    transfer.reserved_streams(root, seed_reservations=path)
    return path


def new_plan(root, directory, system, build):
    attempt = root / 'banks/e2_attempts/F04_N010_RP080_EE08' / (
        'derived_' + system + '_manual_' + uuid.uuid4().hex)
    policy = fresh_reservation(root)
    evidence = directory / ('request_' + uuid.uuid4().hex + '.json')
    e2.exclusive_json(evidence, dict(
        authorization='explicit_user_terminal_command_--execute', reviewer=getpass.getuser(),
        invocation=sys.argv, requested_at=e2.timestamp(), system=system,
        replicas=[1, 2, 3], additional_steps_per_history=STEPS,
        absolute_start_step=8000000, absolute_end_step=24000000,
        window_steps=500000, no_formal_acceptance=True))
    print('PREPARE', system, attempt, flush=True)
    transfer.prepare(root, attempt, system, STEPS, evidence, smoke=False,
                     build_evidence=build, seed_reservations=policy)
    return str(attempt)


def bind_job(root, directory, state, job, build):
    attempt = state['plans'].get(job['system'])
    if attempt:
        plan = e2.check_plan(root, Path(attempt))
        entry = plan['histories'][job['replica'] - 1]
        if (plan['git_sha'] != e2.campaign.git_sha() or
                any(Path(entry['output_prefix']).parent.iterdir())):
            attempt = None
    if not attempt:
        attempt = new_plan(root, directory, job['system'], build)
        state['plans'][job['system']] = attempt
    attempt = Path(attempt)
    approval = attempt / f"approval_r{job['replica']:03d}.json"
    record = dict(
        schema_version=1, approved=True, purpose='e2_derived_segment',
        plan_sha256=e2.campaign.sha256(attempt / 'plan.json'),
        reviewer=getpass.getuser() + ': explicit terminal --execute', approved_at=e2.timestamp(),
        selector_scope='Ea_transfer_16M_preparation_v1', authorized_system=job['system'],
        authorized_replicas=[job['replica']], maximum_additional_MD_steps_per_history=STEPS,
        maximum_additional_MD_steps=STEPS, absolute_start_step=8000000,
        absolute_end_step=24000000)
    if not approval.exists():
        e2.exclusive_json(approval, record)
    e2.scoped_launch_approval(approval, attempt, 'e2_derived_segment',
                             e2.check_plan(root, attempt), None, [job['replica']])
    job.update(attempt=str(attempt), approval=str(approval),
               plan_sha256=e2.campaign.sha256(attempt / 'plan.json'),
               approval_sha256=e2.campaign.sha256(approval), status='prepared')


def authenticate(job):
    attempt = Path(job['attempt'])
    root = Path(e2.campaign.load_json(attempt / 'plan.json')['dataset_root'])
    e2.require(e2.campaign.sha256(attempt / 'plan.json') == job['plan_sha256'] and
               e2.campaign.sha256(Path(job['approval'])) == job['approval_sha256'],
               'saved plan or approval changed')
    plan = e2.check_plan(root, attempt)
    e2.require(e2.scientific_source_hashes(plan['source_sha256']) ==
               e2.scientific_source_hashes(e2.sources()), 'scientific source changed')
    e2.check_hashes(plan['executable_sha256'])
    e2.scoped_launch_approval(Path(job['approval']), attempt, 'e2_derived_segment',
                             plan, None, [job['replica']])
    return plan, plan['histories'][job['replica'] - 1]


def classify(job):
    if 'attempt' not in job:
        return 'pending'
    plan, entry = authenticate(job)
    directory = Path(entry['output_prefix']).parent
    completion = directory / 'complete.json'
    if completion.exists():
        record = e2.campaign.load_json(completion)
        e2.require(record['status'] == 'validated' and
                   record['plan_sha256'] == job['plan_sha256'] and
                   record['end_step'] == 24000000, 'invalid saved completion')
        e2.check_hashes(record['output_sha256'])
        e2.validation.validate(entry, oracle=True)
        return 'complete'
    stderr = (directory / 'stderr.log').read_text() if (directory / 'stderr.log').exists() else ''
    e2.require(not (directory / 'state.candidate_mismatch.tsv').exists() and
               'STAR_ASSOCIATION_SMOKE FAIL:' not in stderr, 'numerical failure: preserved; no automatic retry')
    failure = directory / 'incomplete.json'
    if failure.exists():
        e2.require(not e2.campaign.load_json(failure)['error'],
                   'failed history: preserved; no automatic seed retry')
    stdout = (directory / 'stdout.log').read_text() if (directory / 'stdout.log').exists() else ''
    if 'STAR_ASSOCIATION_SMOKE PASS' in stdout:
        # MD finished before the receipt was written. Validate it without repeating MD.
        started = e2.campaign.load_json(directory / 'started.json')
        e2.require(started['plan_sha256'] == job['plan_sha256'] and
                   started['approval_sha256'] == job['approval_sha256'] and
                   started['command'] == entry['command'], 'interrupted receipt provenance mismatch')
        e2.check_hashes(started['smoke_sha256'])
        _, _, validation = e2.validation.validate(entry, oracle=True)
        e2.exclusive_json(completion, dict(
            status='validated', plan_sha256=job['plan_sha256'], end_step=24000000,
            validation=validation, finished_at=e2.timestamp(), wall_seconds=None,
            receipt_recovered_without_MD=True, output_sha256=e2.hash_files(directory.iterdir())))
        return 'complete'
    return 'interrupted' if any(directory.iterdir()) else 'prepared'


def execute(root, build, state_path):
    directory = state_path.parent
    directory.mkdir(parents=True, exist_ok=True)
    with run_e2.workflow_lock(root):
        state = e2.campaign.load_json(state_path) if state_path.exists() else dict(
            schema_version=1, jobs=jobs(), plans={}, created_at=e2.timestamp())
        e2.require([(j['system'], j['replica']) for j in state['jobs']] ==
                   [(j['system'], j['replica']) for j in jobs()], 'manual state scope differs')
        save(state_path, state)
        for job in state['jobs']:
            try:
                e2.require(job['status'] != 'failed', 'campaign held after a genuine failure; inspect logs')
                status = classify(job)
                if status == 'complete':
                    job['status'] = 'complete'
                    save(state_path, state)
                    print('SKIP validated', job['system'], job['replica'], flush=True)
                    continue
                if status == 'interrupted':
                    print('PRESERVE interrupted; restart this history from its 8M parent:',
                          job['system'], job['replica'], flush=True)
                    job['retired_attempts'].append(dict(attempt=job['attempt'],
                        plan_sha256=job['plan_sha256'], reason='interrupted_without_complete_endpoint'))
                    for key in ('attempt', 'approval', 'plan_sha256', 'approval_sha256'):
                        job.pop(key, None)
                if 'attempt' not in job:
                    bind_job(root, directory, state, job, build)
                else:
                    plan, _ = authenticate(job)
                    if plan['git_sha'] != e2.campaign.git_sha():
                        job['retired_attempts'].append(dict(attempt=job['attempt'], reason='administrative_source_update'))
                        bind_job(root, directory, state, job, build)
                job['status'] = 'running'
                save(state_path, state)
                attempt = Path(job['attempt'])
                smoke = root / 'banks/e2_attempts/F04_N010_RP080_EE08' / (
                    'derived_' + job['system'] + '_remaining_smoke_20261017_v1')
                print('RUN', job['system'], f"r{job['replica']:03d}",
                      '8M -> 24M; logs:', attempt / f"r{job['replica']:03d}", flush=True)
                e2.launch(root, attempt, execute=True, approval=Path(job['approval']),
                          smoke_attempt=smoke, replicas=[job['replica']])
                job['status'] = 'complete'
                save(state_path, state)
                print('PASS', job['system'], job['replica'], flush=True)
            except KeyboardInterrupt:
                job['status'] = 'interrupted'
                save(state_path, state)
                print('\nStopped. Run the same command to continue; earlier outputs are preserved.', flush=True)
                return 130
            except Exception as error:
                job.update(status='failed', error=str(error))
                save(state_path, state)
                raise
        print('ALL NINE 24M ENDPOINTS VALIDATED. Scientific acceptance is still separate.', flush=True)
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--execute', action='store_true', help='user authorizes the nine capped histories')
    group.add_argument('--status', action='store_true')
    group.add_argument('--check', action='store_true', help='CPU authentication only; no MD or reservations')
    args = parser.parse_args()
    root = run_e2.discover()
    state_path = root / 'aggregate/e2/manual_ea16m_v1/state.json'
    if args.status:
        if not state_path.exists():
            print('Not started. Run with --execute.')
        else:
            state = e2.campaign.load_json(state_path)
            for job in state['jobs']:
                print(job['system'], f"r{job['replica']:03d}", job['status'], job.get('attempt', ''))
        return 0
    e2.clean_tree()
    build = root / 'builds' / BUILD
    e2.check_build(build)
    transfer.reference(root)
    if not args.execute:
        print('CHECK PASS: exact parents, native build, branch and clean sources authenticated. No GPU execution.')
        print('Run this script with --execute on titan. Rerun the same command after Ctrl+C.')
        return 0
    e2.require(e2.socket.gethostname() == 'titan', 'this campaign is configured for titan')
    return execute(root, build, state_path)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('Stopped before launch. Run the same command when ready.', file=sys.stderr)
        sys.exit(130)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('STOP:', error, file=sys.stderr)
        sys.exit(1)
