#!/usr/bin/env python3
"""User-run Ea8/Ea10 24M extensions; --check/--status/--prepare never launch MD."""
import argparse
import getpass
from pathlib import Path
import signal
import subprocess
import sys
import uuid

import kg_assoc_e2 as e2
import kg_assoc_e2_extension as extension
import run_e2
from run_ea_preparation import save, request_stop

RESTART_OVERHEAD_AUTHORIZED = True
STATE_DIRECTORY = 'manual_ea_extensions_readback_v2'
EXECUTION_APPROVAL_SUFFIX = '_execution.json'
RECOVERY_FAILURE = 'prepared extension sources/history changed'
RECOVERY_RECORD = 'validation_recovery.json'


def jobs():
    return [dict(system=sid, replica=r, steps=steps, end_step=24000000 + steps,
                 status='pending', retired_attempts=[])
            for sid, steps in extension.DURATIONS.items() for r in (1, 2, 3)]


def validate_state(state):
    expected = jobs()
    e2.require(state.get('schema_version') == 1 and state.get('scope') == extension.SCOPE and
               [(j['system'], j['replica'], j['steps'], j['end_step']) for j in state['jobs']] ==
               [(j['system'], j['replica'], j['steps'], j['end_step']) for j in expected] and
               type(state.get('completed_extension_cap')) is int and
               state['completed_extension_cap'] == 144000000 and
               state['restart_overhead_authorized'] is RESTART_OVERHEAD_AUTHORIZED,
               'extension state scope/caps or restart authorization differs')


def bind(root, directory, state, job, build):
    attempt = state['plans'].get(job['system'])
    if attempt:
        plan = e2.check_plan(root, Path(attempt))
        entry = plan['histories'][job['replica'] - 1]
        if any(Path(entry['output_prefix']).parent.iterdir()):
            attempt = None
    if not attempt:
        attempt = root / 'banks/e2_attempts/F04_N010_RP080_EE08' / (
            'extension_' + job['system'] + '_readback_v2_' + uuid.uuid4().hex)
        extension.prepare(root, attempt, job['system'], build, extension.DOSSIER / 'AUTHORIZATION.md')
        state['plans'][job['system']] = str(attempt)
    attempt = Path(attempt)
    approval = attempt / f"approval_r{job['replica']:03d}.json"
    record = dict(schema_version=1, approved=True, purpose='e2_derived_extension',
        plan_sha256=e2.campaign.sha256(attempt / 'plan.json'), reviewer=getpass.getuser() +
        ': explicit user-authorized extension preparation', approved_at=e2.timestamp(),
        selector_scope=extension.SCOPE, authorized_system=job['system'],
        authorized_replicas=[job['replica']], maximum_additional_MD_steps_per_history=job['steps'],
        maximum_additional_MD_steps=job['steps'], absolute_start_step=24000000,
        absolute_end_step=job['end_step'], diagnostic_window_steps=500000,
        GPU_execution_authorized=False)
    if not approval.exists():
        e2.exclusive_json(approval, record)
    job.update(attempt=str(attempt), approval=str(approval),
        plan_sha256=e2.campaign.sha256(attempt / 'plan.json'),
        approval_sha256=e2.campaign.sha256(approval), status='prepared')
    authenticate(job)


def authenticate(job):
    attempt = Path(job['attempt'])
    e2.check_hashes({str(attempt / 'plan.json'): job['plan_sha256'],
                     job['approval']: job['approval_sha256']})
    raw = e2.campaign.load_json(attempt / 'plan.json')
    root = Path(raw['dataset_root'])
    plan = e2.check_plan(root, attempt)
    e2.check_hashes(plan['executable_sha256'])
    preparation = e2.scoped_launch_approval(
        Path(job['approval']), attempt, 'e2_derived_extension', plan, None, [job['replica']])
    e2.require(preparation.get('GPU_execution_authorized') is False,
               'preparation approval must remain GPU-disabled')
    return plan, plan['histories'][job['replica'] - 1]


def execution_approval(job):
    """Return the separate immutable approval needed to start this exact attempt."""
    plan, entry = authenticate(job)
    e2.require(isinstance(job.get('execution_approval'), str) and
               isinstance(job.get('execution_approval_sha256'), str),
               'fresh replacement requires a new immutable execution approval')
    path = Path(job['execution_approval'])
    e2.check_hashes({str(path): job['execution_approval_sha256']})
    record = e2.scoped_launch_approval(
        path, Path(job['attempt']), 'e2_derived_extension', plan, None, [job['replica']])
    e2.require(record.get('GPU_execution_authorized') is True and
               record.get('preparation_approval_sha256') == job['approval_sha256'],
               'execution approval does not bind the immutable preparation approval')
    source_key = ('recovery_source_authorization'
                  if 'recovery_source_authorization' in job else 'source_authorization')
    source_hash_key = source_key + '_sha256'
    e2.require(isinstance(job.get(source_key), str) and
               isinstance(job.get(source_hash_key), str),
               'extension source authorization absent')
    source_path = Path(job[source_key])
    e2.check_hashes({str(source_path): job[source_hash_key]})
    source_record = e2.extension_source_authorization(source_path, plan, path)
    if source_key == 'recovery_source_authorization':
        e2.require(source_record.get('prior_source_authorization_sha256') ==
                   job['source_authorization_sha256'],
                   'recovery source authorization does not bind prior authorization')
    e2.live_code(plan, source_record['source_sha256_overrides'])
    return path, source_path, plan, entry


def recovery_record(job, entry, failure_path):
    """Authenticate the distinct receipt for an approved post-native recovery."""
    directory = Path(entry['output_prefix']).parent
    path = directory / RECOVERY_RECORD
    e2.require(path.exists(), 'recovery record absent')
    record = e2.campaign.load_json(path)
    e2.require(record.get('schema_version') == 1 and
               record.get('status') == 'independently_validated_recovery' and
               record.get('plan_sha256') == job['plan_sha256'] and
               record.get('end_step') == job['end_step'] and
               record.get('original_incomplete_sha256') == e2.campaign.sha256(failure_path) and
               record.get('original_failure') == RECOVERY_FAILURE and
               record.get('execution_approval_sha256') == job['execution_approval_sha256'] and
               record.get('source_authorization_sha256') == job['source_authorization_sha256'],
               'invalid recovery record')
    e2.check_hashes(record['output_sha256'])
    return path, record


def recover_completed_ea8_r001(root, state_path):
    """CPU-only one-history recovery after the known post-native source-check defect."""
    state = e2.campaign.load_json(state_path)
    validate_state(state)
    job = next((item for item in state['jobs']
                if item['system'] == 'F04_N010_RP080_EE08_EA08' and item['replica'] == 1), None)
    e2.require(job is not None and job.get('status') == 'failed' and
               job.get('error') == RECOVERY_FAILURE, 'only the recorded Ea8 r001 failure is recoverable')
    approval, source_authorization, plan, entry = execution_approval(job)
    directory = Path(entry['output_prefix']).parent
    failure = directory / 'incomplete.json'
    e2.require(failure.is_file() and e2.campaign.load_json(failure).get('error') == RECOVERY_FAILURE,
               'original administrative failure evidence differs')
    e2.require(not (directory / 'complete.json').exists(), 'ordinary completion receipt already exists')
    e2.require('STAR_ASSOCIATION_SMOKE PASS' in (directory / 'stdout.log').read_text(),
               'native completion marker absent')
    started = e2.campaign.load_json(directory / 'started.json')
    e2.require(started.get('plan_sha256') == job['plan_sha256'] and
               started.get('approval_sha256') == job['execution_approval_sha256'] and
               started.get('command') == entry['command'], 'untrusted native start receipt')
    e2.check_hashes(started['smoke_sha256'])
    _, _, validation = e2.validation.validate(entry, oracle=True)
    outputs = e2.hash_files(path for path in directory.iterdir()
                            if path.is_file() and path.name != RECOVERY_RECORD)
    record = dict(schema_version=1, status='independently_validated_recovery',
                  recovery_kind='post_native_administrative_validation_recovery',
                  plan_sha256=job['plan_sha256'], end_step=job['end_step'],
                  execution_approval_sha256=job['execution_approval_sha256'],
                  source_authorization_sha256=job['source_authorization_sha256'],
                  original_incomplete_sha256=e2.campaign.sha256(failure),
                  original_failure=RECOVERY_FAILURE,
                  started_sha256=e2.campaign.sha256(directory / 'started.json'),
                  validation=validation, output_sha256=outputs,
                  recovered_at=e2.timestamp(), recovered_without_MD=True)
    path = directory / RECOVERY_RECORD
    if path.exists():
        _, existing = recovery_record(job, entry, failure)
        e2.require(existing == record, 'existing recovery record differs')
    else:
        extension.atomic_receipt(path, record)
    job.update(status='recovered_complete', recovery_record=str(path),
               recovery_record_sha256=e2.campaign.sha256(path),
               recovered_from_status='failed', recovered_from_error=RECOVERY_FAILURE,
               original_incomplete_sha256=e2.campaign.sha256(failure))
    save(state_path, state)
    return record


def classify(job, recover=False, replay=True):
    if 'attempt' not in job:
        return 'pending'
    approval, source_authorization, plan, entry = execution_approval(job)
    directory = Path(entry['output_prefix']).parent
    if extension.native_running(directory / 'process.json', job['plan_sha256'], entry['command']):
        return 'running'
    stderr = (directory / 'stderr.log').read_text() if (directory / 'stderr.log').exists() else ''
    e2.require(not Path(entry['output_prefix'] + '.candidate_mismatch.tsv').exists() and
               'STAR_ASSOCIATION_SMOKE FAIL:' not in stderr,
               'numerical/candidate failure preserved; no automatic retry')
    failure = directory / 'incomplete.json'
    recovered = directory / RECOVERY_RECORD
    if recovered.exists():
        e2.require(failure.exists(), 'recovery lacks original failure evidence')
        _, record = recovery_record(job, entry, failure)
        if replay:
            _, _, validation = e2.validation.validate(entry, oracle=True)
            e2.require(validation == record['validation'], 'recovery replay differs')
        return 'recovered_complete'
    if failure.exists():
        e2.require(not e2.campaign.load_json(failure)['error'],
                   'failed trajectory preserved; no automatic retry')
    completion = directory / 'complete.json'
    if completion.exists():
        record = e2.campaign.load_json(completion)
        e2.require(record['status'] == 'validated' and record['end_step'] == job['end_step'] and
                   record['plan_sha256'] == job['plan_sha256'], 'invalid extension completion')
        e2.check_hashes(record['output_sha256'])
        if replay:
            _, _, validation = e2.validation.validate(entry, oracle=True)
            e2.require(validation == record['validation'], 'completion replay differs')
        return 'complete'
    started_path = directory / 'started.json'
    if started_path.exists():
        started = e2.campaign.load_json(started_path)
        e2.require(started.get('plan_sha256') == job['plan_sha256'] and
                   started.get('approval_sha256') == job['execution_approval_sha256'] and
                   started.get('command') == entry['command'], 'untrusted partial attempt provenance')
        e2.check_hashes(started['smoke_sha256'])
    elif any(directory.iterdir()):
        e2.require(all(p.name.startswith('started.json.') and p.name.endswith('.tmp')
                       for p in directory.iterdir()), 'outputs lack an authenticated start receipt')
    stdout = (directory / 'stdout.log').read_text() if (directory / 'stdout.log').exists() else ''
    if 'STAR_ASSOCIATION_SMOKE PASS' in stdout:
        started = e2.campaign.load_json(directory / 'started.json')
        e2.require(started['plan_sha256'] == job['plan_sha256'] and
                   started['approval_sha256'] == job['execution_approval_sha256'] and
                   started['command'] == entry['command'], 'untrusted interrupted receipt')
        e2.check_hashes(started['smoke_sha256'])
        if not recover:
            return 'finished_pending_independent_validation'
        e2.require(False, 'post-native recovery requires explicit --recover-ea8-r001')
    return 'interrupted' if any(directory.iterdir()) else 'prepared'


def prepare_state(root, build, state_path):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if state_path.exists():
        state = e2.campaign.load_json(state_path)
        validate_state(state)
        e2.require(not any(j['status'] == 'failed' for j in state['jobs']),
                   'campaign held after failure; no automatic preparation/retry')
    else:
        state = dict(schema_version=1, scope=extension.SCOPE, jobs=jobs(), plans={},
            created_at=e2.timestamp(), completed_extension_cap=144000000,
            restart_overhead_authorized=RESTART_OVERHEAD_AUTHORIZED)
    for job in state['jobs']:
        if 'attempt' not in job:
            try:
                bind(root, state_path.parent, state, job, build)
            except KeyboardInterrupt:
                job['status'] = 'interrupted'
                save(state_path, state)
                raise
            except Exception as error:
                job.update(status='failed', error=str(error))
                save(state_path, state)
                raise
            save(state_path, state)
    return state


def execute(root, build, state_path):
    with run_e2.workflow_lock(root):
        state = prepare_state(root, build, state_path)
        for job in state['jobs']:
            try:
                e2.require(not any(j['status'] == 'failed' for j in state['jobs']),
                           'campaign held after failure; no automatic retry')
                status = classify(job, recover=True)
                if status == 'running':
                    print('Prior native process is still stopping; preserve it and reissue --execute after it exits.', flush=True)
                    return 75
                if status in ('complete', 'recovered_complete'):
                    job['status'] = status
                    save(state_path, state)
                    print('SKIP independently validated', job['system'], job['replica'], flush=True)
                    continue
                if status == 'interrupted':
                    prefix = Path(job['attempt']) / f"r{job['replica']:03d}/state"
                    bounds = extension.partial_step_bounds(prefix, job['steps'])
                    if not (prefix.parent / 'started.json').exists():
                        bounds = dict(completed_MD_steps_lower_bound=0,
                            authorized_MD_steps_upper_bound=0, exact_partial_MD_steps_known=True)
                    retired = {key: job[key] for key in (
                        'attempt', 'plan_sha256', 'approval', 'approval_sha256',
                        'execution_approval', 'execution_approval_sha256',
                        'source_authorization', 'source_authorization_sha256') if key in job}
                    job['retired_attempts'].append(dict(
                        **retired, reason='interrupted; no bitwise integrator checkpoint', **bounds))
                    for key in ('attempt', 'plan_sha256', 'approval', 'approval_sha256',
                                'execution_approval', 'execution_approval_sha256',
                                'source_authorization', 'source_authorization_sha256'):
                        job.pop(key, None)
                    state['plans'].pop(job['system'], None)
                    job['status'] = 'pending'
                    save(state_path, state)
                if 'attempt' not in job:
                    bind(root, state_path.parent, state, job, build)
                job['status'] = 'running'
                save(state_path, state)
                print('RUN', job['system'], f"r{job['replica']:03d}", '24M ->',
                      job['end_step'], 'logs:', Path(job['attempt']) / f"r{job['replica']:03d}", flush=True)
                approval, source_authorization, _, _ = execution_approval(job)
                e2.launch(root, Path(job['attempt']), execute=True,
                          approval=approval, replicas=[job['replica']],
                          source_authorization=source_authorization)
                e2.require(classify(job, replay=True) == 'complete', 'completed extension did not validate')
                job['status'] = 'complete'
                save(state_path, state)
            except KeyboardInterrupt:
                job['status'] = 'interrupted'
                save(state_path, state)
                print('Stopped safely. Outputs/reservations preserved. Reissue --execute when ready.', flush=True)
                return 130
            except Exception as error:
                job.update(status='failed', error=str(error))
                save(state_path, state)
                raise
        print('ALL SIX EXTENSIONS NUMERICALLY VALIDATED. Ea8/Ea10 scientific acceptance is still held.', flush=True)
        return 0



def status(job):
    """Read immutable metadata only; do not parse a live native output mid-write."""
    if 'attempt' not in job:
        return 'pending', None
    attempt = Path(job['attempt'])
    e2.check_hashes({str(attempt / 'plan.json'): job['plan_sha256'],
                     job['approval']: job['approval_sha256']})
    _, _, plan, entry = execution_approval(job)
    directory = Path(entry['output_prefix']).parent
    if extension.native_running(directory / 'process.json', job['plan_sha256'], entry['command']):
        return 'running', extension.partial_step_bounds(Path(entry['output_prefix']), job['steps'])
    recovered = directory / RECOVERY_RECORD
    if recovered.exists():
        failure = directory / 'incomplete.json'
        _, record = recovery_record(job, entry, failure)
        return 'recovered_completion_recorded; full replay on --execute', None
    complete = directory / 'complete.json'
    if complete.exists():
        receipt = e2.campaign.load_json(complete)
        e2.require(receipt['status'] == 'validated' and receipt['end_step'] == job['end_step'] and
                   receipt['plan_sha256'] == job['plan_sha256'], 'completion metadata differs')
        return 'complete_receipt_recorded; full replay on --execute', None
    stdout = directory / 'stdout.log'
    if stdout.exists() and 'STAR_ASSOCIATION_SMOKE PASS' in stdout.read_text():
        if not Path(entry['output_prefix'] + '.initial_device_validation.tsv').is_file():
            return 'validation_hold_missing_initial_device_readback', None
        return 'finished_pending_independent_validation', None
    return ('interrupted' if any(directory.iterdir()) else 'prepared'), None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--status', action='store_true')
    group.add_argument('--prepare', action='store_true', help='CPU-only immutable plans/MD reservations')
    group.add_argument('--execute', action='store_true', help='user runs only the six authorized extensions')
    group.add_argument('--recover-ea8-r001', action='store_true',
                       help='CPU-only explicit recovery of the known completed Ea8 r001 attempt')
    args = parser.parse_args()
    root = run_e2.discover()
    state_path = root / 'aggregate/e2' / STATE_DIRECTORY / 'state.json'
    if args.status:
        if not state_path.exists():
            print('Not prepared. --prepare is CPU-only; --execute is user-run MD.')
        else:
            state = e2.campaign.load_json(state_path)
            validate_state(state)
            print('Completed-extension cap: 144000000 MD steps; recorded restart overhead authorized.')
            print('Abandoned partial overhead lower/upper:',
                  sum(r.get('completed_MD_steps_lower_bound', 0) for j in state['jobs'] for r in j['retired_attempts']),
                  sum(r.get('authorized_MD_steps_upper_bound', 0) for j in state['jobs'] for r in j['retired_attempts']))
            for job in state['jobs']:
                observed, progress = status(job)
                print(job['system'], f"r{job['replica']:03d}", job['status'],
                      observed, job.get('attempt', ''), progress or '')
        return 0
    build = root / 'builds' / extension.BUILD
    e2.require_extension_readback_build(e2.campaign.load_json(build / 'manifest.json'))
    e2.clean_tree()
    e2.check_build(build)
    for sid in extension.DURATIONS:
        extension.predecessor(root, sid)
    if args.execute or args.prepare:
        signal.signal(signal.SIGINT, request_stop)
        signal.signal(signal.SIGTERM, request_stop)
    if args.prepare:
        with run_e2.workflow_lock(root):
            state = prepare_state(root, build, state_path)
        print('PREPARED six exact 24M-parent extensions. No GPU execution.')
        return 0
    if args.recover_ea8_r001:
        with run_e2.workflow_lock(root):
            recover_completed_ea8_r001(root, state_path)
        print('RECOVERY PASS: Ea8 r001 independently validated without MD.')
        return 0
    if not args.execute:
        if state_path.exists():
            state = e2.campaign.load_json(state_path)
            validate_state(state)
            for job in state['jobs']:
                authenticate(job)
        print('CHECK PASS: exact parents/build/source/approvals authenticated; no writes or GPU execution.')
        return 0
    e2.require(state_path.exists(), 'CPU preparation required before execution approval')
    state = e2.campaign.load_json(state_path)
    validate_state(state)
    for job in state['jobs']:
        execution_approval(job)
    e2.require(e2.socket.gethostname() == 'titan', 'extension execution is configured only for titan')
    return execute(root, build, state_path)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('Stopped before MD launch; preserved existing attempts.', file=sys.stderr)
        sys.exit(130)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('STOP:', error, file=sys.stderr)
        sys.exit(1)
