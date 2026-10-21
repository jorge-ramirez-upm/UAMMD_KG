#!/usr/bin/env python3
"""CPU preparation/check/status for six reviewed extensions. GPU approval is separate."""
import argparse
from pathlib import Path
import signal
import sys
import uuid

import kg_assoc_e2 as e2
import kg_assoc_e2_next_extension as extension
import run_e2
from run_ea_preparation import request_stop, save


def expected_jobs():
    return [(sid, replica, start, end) for sid,(start,end) in extension.RANGES.items()
            for replica in (1,2,3)]


def validate_state(state):
    e2.require(state.get('schema_version') == 1 and state.get('campaign') == extension.CAMPAIGN and
        state.get('scope') == extension.SCOPE and state.get('GPU_execution_authorized') is False and
        type(state.get('completed_extension_cap')) is int and state['completed_extension_cap'] == 120000000 and
        [(j['system'],j['replica'],j['start_step'],j['end_step']) for j in state['jobs']] == expected_jobs() and
        len({(j['attempt'],j['replica']) for j in state['jobs']}) == 6,
        'immutable reviewed campaign identity or scope differs')


def prepare_approval(plan, replica):
    start, end = extension.RANGES[plan['system']['system_id']]
    attempt = Path(plan['attempt'])
    path = attempt/f'approval_r{replica:03d}.json'
    e2.exclusive_json(path, dict(schema_version=1, approved=True, purpose='e2_derived_extension',
        plan_sha256=e2.campaign.sha256(attempt/'plan.json'), reviewer='explicit user CPU-preparation approval',
        approved_at=e2.timestamp(), selector_scope=extension.SCOPE,
        authorized_system=plan['system']['system_id'], authorized_replicas=[replica],
        maximum_additional_MD_steps_per_history=end-start, maximum_additional_MD_steps=end-start,
        absolute_start_step=start, absolute_end_step=end, diagnostic_window_steps=500000,
        GPU_execution_authorized=False))
    source = attempt/f'approval_r{replica:03d}_preparation_sources.json'
    e2.exclusive_json(source, dict(schema_version=1, approved=True,
        purpose='e2_extension_source_authorization', plan_sha256=e2.campaign.sha256(attempt/'plan.json'),
        execution_approval_sha256=e2.campaign.sha256(path),
        reviewer='explicit user CPU preparation; does not authorize GPU execution',
        approved_at=e2.timestamp(), source_sha256_overrides={}))
    return dict(system=plan['system']['system_id'], replica=replica, start_step=start, end_step=end,
        status='prepared',
        attempt=str(attempt), plan_sha256=e2.campaign.sha256(attempt/'plan.json'),
        approval=str(path), approval_sha256=e2.campaign.sha256(path),
        preparation_source_authorization=str(source),
        preparation_source_authorization_sha256=e2.campaign.sha256(source))


def authenticate(root, job, execution=False):
    attempt = Path(job['attempt'])
    e2.check_hashes({str(attempt/'plan.json'):job['plan_sha256'],job['approval']:job['approval_sha256'],
        job['preparation_source_authorization']:job['preparation_source_authorization_sha256']})
    plan = e2.check_plan(root, attempt, live=False)
    preparation = e2.scoped_launch_approval(Path(job['approval']),attempt,'e2_derived_extension',
                                            plan,None,[job['replica']])
    e2.require(preparation.get('GPU_execution_authorized') is False, 'preparation approval was altered')
    approval = Path(job['approval'])
    source = Path(job['preparation_source_authorization'])
    if execution:
        approval = attempt/f"approval_r{job['replica']:03d}_execution.json"
        source = attempt/f"approval_r{job['replica']:03d}_execution_sources.json"
        e2.require(approval.is_file() and source.is_file(), 'GPU execution is NOT authorized; preparation only')
        record = e2.scoped_launch_approval(approval,attempt,'e2_derived_extension',plan,None,[job['replica']])
        e2.require(record.get('GPU_execution_authorized') is True and
                   record.get('preparation_approval_sha256') == job['approval_sha256'],
                   'GPU approval does not bind this preparation')
    record = e2.extension_source_authorization(source,plan,approval)
    e2.live_code(plan,record['source_sha256_overrides'])
    return plan, plan['histories'][job['replica']-1], approval, source


def prepare(root, state_path):
    e2.clean_tree()
    if state_path.exists():
        state = e2.campaign.load_json(state_path)
        validate_state(state)
        for job in state['jobs']:
            authenticate(root,job)
        return state
    jobs = []
    for sid in extension.RANGES:
        attempt = root/'banks/e2_attempts/F04_N010_RP080_EE08'/(
            'extension_'+sid+'_next_'+uuid.uuid4().hex)
        plan = extension.prepare(root,attempt,sid,root/'builds'/extension.BUILD,
                                 extension.DOSSIER/'AUTHORIZATION.md')
        jobs.extend(prepare_approval(plan,replica) for replica in (1,2,3))
    state = dict(schema_version=1,campaign=extension.CAMPAIGN,scope=extension.SCOPE,
        completed_extension_cap=120000000,GPU_execution_authorized=False,
        restart_overhead_policy='preserve partial attempts; record overhead separately; fresh plan-bound approval',
        created_at=e2.timestamp(),jobs=jobs)
    validate_state(state)
    extension.atomic_receipt(state_path,state)
    return state


def classify(job, entry, replay=False):
    directory = Path(entry['output_prefix']).parent
    if extension.native_running(directory/'process.json',job['plan_sha256'],entry['command']):
        return 'running'
    if (directory/'incomplete.json').exists():
        failure = e2.campaign.load_json(directory/'incomplete.json')
        e2.require(not failure.get('error'), 'failed history held; never automatically retry')
    e2.require(not Path(entry['output_prefix']+'.candidate_mismatch.tsv').exists(), 'candidate failure held')
    stderr = directory/'stderr.log'
    e2.require(not stderr.exists() or 'STAR_ASSOCIATION_SMOKE FAIL:' not in stderr.read_text(),
               'native numerical failure held')
    complete = directory/'complete.json'
    if complete.exists():
        receipt = e2.campaign.load_json(complete)
        e2.require(receipt.get('status') == 'validated' and receipt.get('end_step') == entry['end_step'] and
                   receipt.get('plan_sha256') == job['plan_sha256'], 'completion receipt differs')
        e2.check_hashes(receipt['output_sha256'])
        if replay:
            _,_,result = e2.validation.validate(entry,oracle=True)
            e2.require(result == receipt['validation'], 'independent completion replay differs')
        return 'complete'
    stdout = directory/'stdout.log'
    if stdout.exists() and 'STAR_ASSOCIATION_SMOKE PASS' in stdout.read_text():
        return 'native_PASS_validation_hold; never retry MD'
    if not any(directory.iterdir()):
        return 'prepared'
    started = e2.campaign.load_json(directory/'started.json')
    e2.require(started.get('plan_sha256') == job['plan_sha256'] and started.get('command') == entry['command'],
               'untrusted partial history')
    return 'interrupted'


def replace_interrupted(root, state_path, state, index, job, entry):
    """Allocate CPU-only replacement and preserve overhead; never copy GPU authority."""
    directory = Path(entry['output_prefix']).parent
    e2.require(classify(job,entry) == 'interrupted', 'only genuine partial MD may receive a replacement')
    sid = job['system']
    attempt = root/'banks/e2_attempts/F04_N010_RP080_EE08'/('extension_'+sid+'_next_'+uuid.uuid4().hex)
    plan = extension.prepare(root,attempt,sid,root/'builds'/extension.BUILD,
                             extension.DOSSIER/'AUTHORIZATION.md')
    fresh = prepare_approval(plan,job['replica'])
    bounds = extension.partial_step_bounds(Path(entry['output_prefix']),entry['start_step'],
                                           entry['end_step']-entry['start_step'])
    retired = dict(job=job,reason='interrupted; no bitwise GJ checkpoint',**bounds)
    prior = state['jobs'][index].get('retired_attempts',[])
    fresh['retired_attempts'] = prior+[retired]
    state['jobs'][index] = fresh
    save(state_path,state)
    raise ValueError('partial attempt preserved; fresh replacement prepared; separate GPU approval required')


def execute(root, frozen_state, runtime_path):
    state = e2.campaign.load_json(runtime_path) if runtime_path.exists() else frozen_state
    validate_state(state)
    # Fail before any launch or mutable state change unless all selected jobs have GPU approval.
    for job in state['jobs']:
        authenticate(root,job,execution=True)
    for index, job in enumerate(state['jobs']):
        _,entry,approval,source = authenticate(root,job,execution=True)
        status = classify(job,entry,replay=True)
        if status == 'complete':
            print('SKIP independently validated',job['system'],job['replica'],flush=True)
            continue
        if status == 'interrupted':
            replace_interrupted(root,runtime_path,state,index,job,entry)
        e2.require(status == 'prepared', 'history is running or held after native completion; no MD retry')
        e2.launch(root,Path(job['attempt']),execute=True,approval=approval,
                  replicas=[job['replica']],source_authorization=source)
        e2.require(classify(job,entry,replay=True) == 'complete', 'independent endpoint validation failed')
    print('ALL SIX NEXT EXTENSIONS NUMERICALLY VALIDATED; scientific acceptance remains held.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true')
    group.add_argument('--check',action='store_true')
    group.add_argument('--status',action='store_true')
    group.add_argument('--execute',action='store_true',help='requires a later immutable GPU approval')
    args = parser.parse_args()
    root = run_e2.discover()
    state_path = root/'aggregate/e2'/extension.CAMPAIGN/'state.json'
    if args.prepare:
        with run_e2.workflow_lock(root):
            state = prepare(root,state_path)
        print('PREPARED six histories; GPU_execution_authorized=false')
        return
    state = e2.campaign.load_json(state_path)
    validate_state(state)
    runtime_path = state_path.with_name('runtime.json')
    if args.execute:
        signal.signal(signal.SIGINT,request_stop)
        signal.signal(signal.SIGTERM,request_stop)
        with run_e2.workflow_lock(root):
            execute(root,state,runtime_path)
        return
    if runtime_path.exists():
        state = e2.campaign.load_json(runtime_path)
        validate_state(state)
    for job in state['jobs']:
        _,entry,_,_ = authenticate(root,job)
        print(job['system'],f"r{job['replica']:03d}",classify(job,entry),
              entry['start_step'],'->',entry['end_step'])
    print('CHECK PASS; preparation only; no GPU execution authorized')


if __name__ == '__main__':
    try:
        main()
    except (ValueError,OSError,e2.subprocess.CalledProcessError) as error:
        print('STOP:',error,file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print('Interrupted; evidence preserved. Inspect --status before any future execution.',file=sys.stderr)
        sys.exit(130)
