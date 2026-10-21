"""Exact reviewed 40M/56M parents to 48M/88M. Preparation never authorizes GPU work."""
import csv
from functools import lru_cache
import hashlib
from pathlib import Path

import kg_assoc_e2 as e2
import kg_assoc_e2_extension as legacy
from kg_assoc_e2_extension import atomic_receipt, native_running, parent_death_guard, process_identity

MODE = 'Ea_reviewed_extension_v2'
SCOPE = 'Ea_transfer_40M_56M_extensions_v1'
CAMPAIGN = 'manual_ea_extensions_48m_88m_v1'
BUILD = 'ea_extensions_48m_88m_20261021_v1'
REVIEW = e2.HERE.parent / 'reviews/e2_ea_extensions_joint_20261021'
DOSSIER = e2.HERE.parent / 'reviews/e2_ea_next_extensions_cpu_20261021'
REVIEW_HASH = 'bdc800e35620c5e41022101b3c96d5e91638062865da6f581c615bbad205e701'
PARENT_SOURCE_COMMIT = '88ccd6fee6e783bf6897ccdd96969e73b496a4bf'
RANGES = {'F04_N010_RP080_EE08_EA08': (40000000, 48000000),
          'F04_N010_RP080_EE08_EA10': (56000000, 88000000)}
NATIVE_HASH = '9e77c0963af20bf0f8540fa2a8cc66c8e19ce211c320c11ab94b154753b6e48d'
require = e2.require


@lru_cache(maxsize=1)
def historical_sources():
    """Recover the exact reviewed source map from immutable Git blobs, without checkout."""
    repo = e2.campaign.REPOSITORY_ROOT
    names = e2.subprocess.check_output(['git', 'ls-tree', '-r', '--name-only',
        PARENT_SOURCE_COMMIT, '--', 'src', 'examples/KG', 'examples/KG_Assoc'],
        cwd=repo, text=True).splitlines()
    names = [n for n in names if Path(n).suffix in ('.cu', '.cuh', '.h', '.cpp', '.py', '.json')
             or Path(n).name == 'Makefile']
    queries = ''.join(PARENT_SOURCE_COMMIT + ':' + n + '\n' for n in names).encode()
    payload = e2.subprocess.run(['git', 'cat-file', '--batch'], input=queries,
        stdout=e2.subprocess.PIPE, cwd=repo, check=True).stdout
    result = {}
    offset = 0
    for name in names:
        header_end = payload.index(b'\n', offset)
        fields = payload[offset:header_end].split()
        require(len(fields) == 3 and fields[1] == b'blob', 'historical source blob absent')
        size = int(fields[2])
        begin = header_end + 1
        result[str(repo / name)] = hashlib.sha256(payload[begin:begin+size]).hexdigest()
        offset = begin + size + 1
    require(offset == len(payload), 'historical source batch malformed')
    return result


def predecessor(root, sid):
    require(sid in RANGES, 'unapproved reviewed extension system')
    e2.check_hashes({str(REVIEW / 'INTEGRITY.sha256'): REVIEW_HASH})
    e2.check_hashes(e2.campaign.load_json(REVIEW / 'INTEGRITY.sha256'))
    proof = e2.campaign.load_json(REVIEW / 'RESULTS.log')
    with (REVIEW / 'ENDPOINTS.csv').open(newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if r['system'] == sid]
    require([int(r['replica']) for r in rows] == [1, 2, 3], 'reviewed parent family missing')
    histories = [h for h in proof['histories'] if h['entry']['system']['system_id'] == sid]
    require([h['entry']['replica'] for h in histories] == [1, 2, 3], 'review proof family differs')
    state_path = root / 'aggregate/e2/manual_ea_extensions_readback_v2/state.json'
    e2.check_hashes({str(state_path): e2.campaign.load_json(REVIEW/'PROVENANCE.sha256')[str(state_path)]})
    state = e2.campaign.load_json(state_path)
    plan = e2.campaign.load_json(Path(histories[0]['job']['attempt']) / 'plan.json')
    for row, reviewed in zip(rows, histories):
        job, entry = reviewed['job'], reviewed['entry']
        require(next(j for j in state['jobs'] if (j['system'], j['replica']) ==
                     (sid, entry['replica'])) == job, 'historical campaign state differs')
        require(plan['histories'][entry['replica']-1] == entry and
                entry['end_step'] == int(row['end_step']) == RANGES[sid][0] and
                entry['output_prefix']+'.restart.lammpsdat' == row['restart'],
                'unrelated parent endpoint or replica')
        e2.check_hashes({str(Path(job['attempt'])/'plan.json'): row['plan_sha256'],
            row['restart']: row['restart_sha256'], row['sidecar']: row['sidecar_sha256'],
            row['receipt']: row['receipt_sha256']})
        prep = e2.scoped_launch_approval(Path(job['approval']), Path(job['attempt']),
            'e2_derived_extension', plan, None, [entry['replica']])
        execution = e2.scoped_launch_approval(Path(job['execution_approval']), Path(job['attempt']),
            'e2_derived_extension', plan, None, [entry['replica']])
        require(prep['GPU_execution_authorized'] is False and
                execution['GPU_execution_authorized'] is True and
                execution['preparation_approval_sha256'] == job['approval_sha256'],
                'historical approval chain differs')
        for key in ('approval', 'execution_approval', 'source_authorization',
                    'recovery_source_authorization', 'recovery_source_authorization_v2'):
            e2.check_hashes({job[key]: job[key+'_sha256']})
        prior = e2.extension_source_authorization(Path(job['recovery_source_authorization']),
                                                 plan, Path(job['execution_approval']))
        source = e2.extension_source_authorization(Path(job['recovery_source_authorization_v2']),
                                                  plan, Path(job['execution_approval']))
        e2.extension_source_authorization(Path(job['source_authorization']), plan,
                                          Path(job['execution_approval']))
        require(prior['prior_source_authorization_sha256'] == job['source_authorization_sha256'] and
                source['prior_source_authorization_sha256'] == job['source_authorization_sha256'] and
                source['prior_recovery_source_authorization_sha256'] ==
                job['recovery_source_authorization_sha256'] and
                dict(plan['source_sha256'], **source['source_sha256_overrides']) == historical_sources(),
                'historical authorized source map differs')
        require(e2.subprocess.run(['git', 'merge-base', '--is-ancestor', plan['git_sha'],
            PARENT_SOURCE_COMMIT], cwd=e2.campaign.REPOSITORY_ROOT).returncode == 0,
            'historical source ancestry differs')
        receipt = e2.campaign.load_json(row['receipt'])
        require(receipt['validation'] == reviewed['validation'] and
                receipt['validation']['numerical_status'] == 'valid' and
                receipt['validation']['oracle_sweeps'] == (entry['end_step']-entry['start_step'])//100 and
                receipt['validation']['initial_device_readback']['status'] == 'valid',
                'reviewed parent numerical qualification absent')
        directory = Path(entry['output_prefix']).parent
        if entry['replica'] == 1 and sid.endswith('EA08'):
            import run_ea_extensions as original
            original.recovery_record(job, entry, directory/'incomplete.json')
            require(receipt['status'] == 'independently_validated_recovery' and
                    job['status'] == 'recovered_complete' and
                    row['receipt_sha256'] == job['recovery_record_sha256'], 'invalid recovered parent lineage')
        else:
            require(receipt['status'] == 'validated' and job['status'] == 'complete' and
                    not (directory/'incomplete.json').exists(), 'incomplete parent')
        e2.check_hashes(receipt['output_sha256'])
        e2.check_hashes(entry['parent']['sha256'])
        e2.check_hashes(plan['reservation_sha256'])
        e2.check_hashes(plan['evidence_sha256'])
    e2.check_hashes(plan['executable_sha256'])
    e2.check_hashes(plan['build']['build_log_sha256'])
    e2.require_extension_readback_build(plan['build'])
    return plan, rows


def parent_descriptor(prior, row):
    receipt = e2.campaign.load_json(row['receipt'])
    paths = [Path(p) for p in receipt['output_sha256']]
    paths.append(Path(row['receipt']))
    paths.append(Path(prior['output_prefix']).parents[1]/'plan.json')
    return dict(kind='e2', prefix=prior['output_prefix'],
                snapshot=row['restart'], sha256=e2.hash_files(paths))


def inspect(root, output, sid, build, policy_path):
    output = e2.inside(root, output)
    require(output.parent == root/'banks/e2_attempts/F04_N010_RP080_EE08' and
            output.name.startswith('extension_'+sid+'_next_') and
            all(c.isalnum() or c == '_' for c in output.name), 'invalid isolated child attempt')
    previous, rows = predecessor(root, sid)
    policy = legacy.reservation(root, policy_path, output, sid, scope=SCOPE)
    start, end = RANGES[sid]
    histories = []
    for prior, row, stream in zip(previous['histories'], rows, policy['streams']):
        metadata, pairs = e2.validation.analysis.restart.read_metadata(row['sidecar'])
        require(int(metadata['completed_steps']) == start and
                int(metadata['seed']) == prior['chemistry_seed'], 'parent chemistry/step differs')
        lineage = dict(mode=MODE, reference_control=False, system_id=sid,
            target_Ea=prior['physics']['Ea'], parent_Ea=prior['physics']['Ea'],
            parent_chemistry_seed=prior['chemistry_seed'], branch_origin_step=start,
            parent_creations=int(metadata['creations']), parent_breaks=int(metadata['breaks']),
            initial_bonds=len(pairs), original_parent_replica=prior['replica'],
            original_branch_id=prior['lineage']['branch_id'],
            parent_plan=str(Path(prior['output_prefix']).parents[1]/'plan.json'),
            parent_plan_sha256=row['plan_sha256'], parent_receipt=row['receipt'],
            parent_receipt_sha256=row['receipt_sha256'],
            reference_acceptance=prior['lineage']['reference_acceptance'],
            reference_acceptance_sha256=prior['lineage']['reference_acceptance_sha256'],
            seed_reservations=str(policy_path), seed_reservations_sha256=e2.campaign.sha256(policy_path),
            chemistry_continuation='same_seed_absolute_step_keys', bitwise_md_continuation=False,
            branch_id=sid+':'+output.name+f":r{prior['replica']:03d}")
        entry = dict(replica=prior['replica'], system=prior['system'], physics=prior['physics'],
            parent_Ea=prior['parent_Ea'], parent=parent_descriptor(prior, row), lineage=lineage,
            chemistry_seed=prior['chemistry_seed'], md_seed=stream['md_seed'],
            effective_md_seed=stream['effective_md_seed'], start_step=start, end_step=end,
            executable_directory=str(build), output_prefix=str(output/f"r{prior['replica']:03d}/state"))
        entry['command'] = e2.command(entry, False)
        histories.append(entry)
    return dict(schema_version=1, stage='E2-G1', lineage_mode=MODE, dataset_root=str(root),
        attempt=str(output), system=previous['system'], histories=histories, steps=end-start,
        smoke=False, reference_control=False, preparation_Ea=previous['preparation_Ea'],
        parent_attempt=str(Path(rows[0]['restart']).parents[1]),
        segment_index=previous['segment_index']+1, diagnostic_window_steps=500000,
        reservation_id=Path(policy_path).stem, reservation_sha256=e2.hash_files([policy_path]),
        rng_policy='inherited_chemistry_absolute_step_keys; fresh_GJ_MD; no_cross_segment_IAT_or_lifetimes',
        scientific_status='hold_pending_extension_review', production_authorization=False)


def validate_lineage(entry, metadata, pairs):
    lineage = entry['lineage']
    root = Path(lineage['parent_plan']).parents[4]
    expected = inspect(root, Path(entry['output_prefix']).parents[1], entry['system']['system_id'],
                       Path(entry['executable_directory']), Path(lineage['seed_reservations']))
    require(type(entry['replica']) is int and entry['replica'] in (1,2,3) and
            entry == expected['histories'][entry['replica']-1] and
            int(metadata['creations']) == lineage['parent_creations'] and
            int(metadata['breaks']) == lineage['parent_breaks'] and len(pairs) == lineage['initial_bonds'],
            'reviewed extension lineage/chemistry differs')


def check_build(build):
    record, manifest = e2.check_build(build)
    native = str(e2.HERE.parent/'kg_assoc_stars.cu')
    require(record['out_of_tree'] and record['source_sha256'][native] == NATIVE_HASH,
            'selected executable does not contain the reviewed extension guard')
    e2.require_extension_readback_build(record)
    return record, manifest


def prepare(root, output, sid, build, evidence):
    e2.clean_tree()
    record, manifest = check_build(build)
    require(not output.exists(), 'new immutable attempt required')
    policy = legacy.reserve_md(root, output, sid, scope=SCOPE)
    plan = inspect(root, output, sid, build, policy)
    checks = []
    for entry in plan['histories']:
        e2.validation.read_parent(entry)
        result = e2.subprocess.run(entry['command']+['--validate-initial-state'],
            check=True, capture_output=True, text=True, timeout=60)
        require('INITIAL_STATE_VALIDATED' in result.stdout, 'host initialization failed')
        seed = e2.subprocess.check_output([str(build/'kg_assoc_stars'), '--md-seed-info',
            str(entry['md_seed'])], text=True, timeout=60)
        require(int(seed) == entry['effective_md_seed'], 'native MD stream identity differs')
        checks.append(result.stdout.strip())
    plan.update(git_sha=e2.campaign.git_sha(), source_sha256=e2.sources(), build=record,
        executable_sha256=e2.hash_files(build/name for name in e2.EXECUTABLES),
        evidence_sha256=e2.hash_files([evidence, manifest]), initial_state_checks=checks)
    output.mkdir(parents=True, exist_ok=False)
    e2.exclusive_json(output/'plan.json', plan)
    for replica in (1,2,3):
        (output/f'r{replica:03d}').mkdir()
    return plan


def check_plan(root, output, plan, live=False):
    require(len(plan['reservation_sha256']) == 1, 'one immutable MD reservation required')
    e2.check_hashes(plan['reservation_sha256'])
    build = Path(plan['histories'][0]['executable_directory'])
    expected = inspect(root, output, plan['system']['system_id'], build,
                       Path(next(iter(plan['reservation_sha256']))))
    require(all(plan.get(k) == v for k,v in expected.items()), 'reviewed extension plan differs')
    require(build == root/'builds'/BUILD, 'unapproved reviewed extension build')
    record, manifest = check_build(build)
    require(record == plan['build'] and len(plan['initial_state_checks']) == 3 and
            e2.scientific_source_hashes(record['source_sha256']) ==
            e2.scientific_source_hashes(plan['source_sha256']) and
            all('INITIAL_STATE_VALIDATED' in s for s in plan['initial_state_checks']) and
            plan['executable_sha256'] == e2.hash_files(build/n for n in e2.EXECUTABLES),
            'build, executable or initial-state identity differs')
    e2.check_hashes(plan['evidence_sha256'])
    if live:
        e2.live_code(plan)
    return plan


def launch_scope(plan, replica, replicas):
    sid = plan['system']['system_id']
    require(sid in RANGES, 'unapproved extension system')
    start, end = RANGES[sid]
    require(plan.get('lineage_mode') == MODE and plan.get('smoke') is False and
            plan.get('reference_control') is False and type(plan['steps']) is int and
            plan['steps'] == end-start and [h['replica'] for h in plan['histories']] == [1,2,3] and
            all(type(h['replica']) is int and h['start_step'] == start and h['end_step'] == end
                for h in plan['histories']), 'reviewed extension scope differs')
    require(replica is None and type(replicas) is list and bool(replicas) and
            all(type(r) is int for r in replicas) and replicas == sorted(set(replicas)) and
            set(replicas) <= {1,2,3}, 'explicit reviewed replica selection required')
    return [h for h in plan['histories'] if h['replica'] in replicas]


def check_approval(record, plan, replica, replicas):
    selected = launch_scope(plan, replica, replicas)
    start, end = RANGES[plan['system']['system_id']]
    require(record.get('purpose') == 'e2_derived_extension' and record.get('selector_scope') == SCOPE and
            record.get('authorized_system') == plan['system']['system_id'] and
            record.get('authorized_replicas') == replicas and
            all(type(r) is int for r in record['authorized_replicas']) and
            all(type(record.get(k)) is int and record[k] == v for k,v in (
                ('maximum_additional_MD_steps_per_history',end-start),
                ('maximum_additional_MD_steps',(end-start)*len(selected)),
                ('absolute_start_step',start),('absolute_end_step',end),
                ('diagnostic_window_steps',500000))), 'reviewed preparation/launch approval differs')


def inherited_gpu_evidence(root, plan):
    _, rows = predecessor(root, plan['system']['system_id'])
    return e2.hash_files(Path(row['receipt']) for row in rows)


def revalidate_parent(entry):
    root = Path(entry['lineage']['parent_plan']).parents[4]
    plan, rows = predecessor(root, entry['system']['system_id'])
    _, _, result = e2.validation.validate(plan['histories'][entry['replica']-1], oracle=True)
    receipt = e2.campaign.load_json(rows[entry['replica']-1]['receipt'])
    require(result == receipt['validation'], 'independent reviewed parent replay differs')


def partial_step_bounds(prefix, start, steps):
    return legacy.partial_step_bounds(prefix, steps, start=start)
