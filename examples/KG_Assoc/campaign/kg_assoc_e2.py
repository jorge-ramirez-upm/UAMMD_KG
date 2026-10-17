#!/usr/bin/env python3
"""Authenticated, immutable three-history E2 segments; MD requires hash-bound approval."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import shlex
import subprocess
import time

import kg_assoc_campaign as campaign
import kg_assoc_e2_validate as validation

require = validation.require
HERE = campaign.HERE
INVENTORY = HERE / 'e2_remaining_inventory_20261011.json'
EXECUTABLES = ('kg_assoc_stars', 'kg_assoc_stars_candidate_smoke', 'kg_assoc_candidates_test')
BUILD_TARGETS = EXECUTABLES + ('kg_assoc_production', 'kg_assoc_campaign_production',
                               'kg_assoc_campaign_production_smoke')


def exclusive_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def inside(root, path):
    path = Path(path).resolve()
    path.relative_to(root.resolve())
    return path


def check_hashes(hashes):
    for name, expected in hashes.items():
        require(campaign.sha256(Path(name)) == expected, 'authenticated file changed: ' + name)


def hash_files(paths):
    return {str(Path(path).resolve()): campaign.sha256(path) for path in paths}


def system_by_id(identifier):
    systems = [system for system in campaign.campaign_systems() if system['system_id'] == identifier]
    require(len(systems) == 1 and systems[0]['associating'], 'unknown associating system')
    return systems[0]


def seed_map():
    policy = campaign.load_json(HERE / 'e2_seed_map.json')
    require(policy['schema_version'] == 1, 'unknown RNG policy')
    return policy['chemical_seeds']


def sources():
    files = subprocess.check_output(['git', 'ls-files', 'src', 'examples/KG', 'examples/KG_Assoc'],
                                    cwd=campaign.REPOSITORY_ROOT, text=True).splitlines()
    paths = [campaign.REPOSITORY_ROOT / name for name in files
             if Path(name).suffix in ('.cu', '.cuh', '.h', '.cpp', '.py', '.json') or
             Path(name).name == 'Makefile']
    return hash_files(paths)


def clean_tree():
    require(not subprocess.check_output(['git', 'status', '--porcelain'],
                                       cwd=campaign.REPOSITORY_ROOT, text=True).strip(),
            'commit source changes before preparing or launching MD')


def live_code(plan=None):
    clean_tree()
    if plan is not None:
        require(campaign.git_sha() == plan['git_sha'], 'prepared code SHA changed')
        check_hashes(plan['source_sha256'])
        check_hashes(plan['executable_sha256'])
        if plan.get('build'):
            check_hashes(plan['build']['build_log_sha256'])
            check_hashes(plan['build']['executable_sha256'])
    if not (plan and plan.get('lineage_mode') == 'Ea_reference_transfer_v1' and
            plan.get('build', {}).get('out_of_tree')):
        subprocess.run(['make', '-q', *EXECUTABLES], cwd=HERE.parent, check=True)


def build(root, output, out_of_tree=False):
    """Force header-based compilation and retain immutable build provenance; never runs MD."""
    clean_tree()
    output = inside(root, output)
    require(output.parent == root / 'builds' and not output.exists(), 'choose a new build directory')
    before = sources()
    output.mkdir(parents=True, exist_ok=False)
    targets = EXECUTABLES if out_of_tree else BUILD_TARGETS
    command = ['make', '-n', '-B', *targets] if out_of_tree else ['make', '-B', '-j2', *targets]
    compile_commands = []
    binaries = [output / target for target in targets] if out_of_tree else [
        HERE.parent / target for target in targets]
    started = time.monotonic()
    try:
        with (output / 'stdout.log').open('x') as stdout, (output / 'stderr.log').open('x') as stderr:
            if out_of_tree:
                commands = subprocess.check_output(command, cwd=HERE.parent, text=True).splitlines()
                for line in commands:
                    native = shlex.split(line)
                    index = native.index('-o') + 1
                    require(native[index] in targets, 'unexpected build target')
                    native[index] = str(output / native[index])
                    compile_commands.append(native)
                    subprocess.run(native, cwd=HERE.parent, stdout=stdout, stderr=stderr, check=True)
            else:
                subprocess.run(command, cwd=HERE.parent, stdout=stdout, stderr=stderr, check=True)
        clean_tree()
        check_hashes(before)
        exclusive_json(output / 'manifest.json', dict(
            schema_version=1, status='built', git_sha=campaign.git_sha(), source_sha256=before,
            executable_sha256=hash_files(binaries), out_of_tree=out_of_tree,
            command=command, compile_commands=compile_commands, cwd=str(HERE.parent), wall_seconds=time.monotonic() - started,
            nvcc=subprocess.check_output(['/usr/local/cuda-12.8/bin/nvcc', '--version'], text=True),
            compiler=subprocess.check_output(['/usr/local/gcc-11.2.0/bin/g++', '--version'], text=True),
            build_log_sha256=hash_files([output / 'stdout.log', output / 'stderr.log']),
            finished_at=timestamp()))
    except BaseException as error:
        exclusive_json(output / 'incomplete.json', dict(error=str(error), finished_at=timestamp()))
        raise


def scientific_source_hashes(hashes):
    # Administrative entry points/tests do not change simulation or validation semantics.
    ignored = {'run_e2.py', 'kg_assoc_e2.py', 'kg_assoc_e2_recover.py',
               'catalog.py', 'catalog_model.py'}
    def administrative(name):
        path = Path(name)
        campaign_file = (len(path.parts) == 1 or
                         path.parts[-4:-1] == ('examples', 'KG_Assoc', 'campaign'))
        return campaign_file and (path.name in ignored or path.name.startswith('test_'))

    return {name: value for name, value in hashes.items() if not administrative(name)}


def check_build(path):
    require(path is not None, 'prepare requires explicit --build-evidence from forced build action')
    manifest_path = Path(path) / 'manifest.json'
    record = campaign.load_json(manifest_path)
    current_sha = campaign.git_sha()
    ancestor = record['git_sha'] == current_sha or subprocess.run(
        ['git', 'merge-base', '--is-ancestor', record['git_sha'], current_sha],
        cwd=campaign.REPOSITORY_ROOT, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL).returncode == 0
    require(record['schema_version'] == 1 and record['status'] == 'built' and ancestor and
            scientific_source_hashes(record['source_sha256']) == scientific_source_hashes(sources()),
            'build evidence differs from current committed scientific sources/history')
    check_hashes(record['executable_sha256'])
    check_hashes(record['build_log_sha256'])
    binary_directory = manifest_path.parent if record.get('out_of_tree') else HERE.parent
    targets = EXECUTABLES if record.get('out_of_tree') else BUILD_TARGETS
    require(set(record['executable_sha256']) ==
            {str((binary_directory / target).resolve()) for target in targets},
            'build evidence lacks required executables')
    return record, manifest_path


def original_e1(root, system, replica):
    state = inside(root, campaign.e1_bank_path(root, campaign.geometry_id(system), replica) /
                   'state.e1.lammpsdat')
    inventory = campaign.load_json(INVENTORY)
    records = [item for item in inventory['e1_states'] if item['geometry'] == campaign.geometry_id(system)
               and item['replica'] == replica]
    require(len(records) == 1 and root / records[0]['path'] == state and
            campaign.sha256(state) == records[0]['sha256'], 'E1 differs from frozen active inventory')
    record = campaign.load_json(state.parent / 'command.json')
    require(record['status'] == 'finished' and record['exit_code'] == 0, 'E1 completion absent')
    validation.e1.check_snapshot(state, system)
    return dict(kind='e1', snapshot=str(state), sha256=hash_files(
        [state, state.parent / 'command.json', state.parent / 'diagnostics.tsv',
         root / 'banks/e1/active_states.json', INVENTORY]))


def corrected_c1(root, replica, replay=True):
    """Authenticate accepted historical recovery without demanding its old code be current."""
    import kg_assoc_c1_recovery as recovery
    import validate_periodic_e2_smoke as legacy
    inventory = campaign.load_json(INVENTORY)
    prefix = root / inventory['C1_recovery'][replica - 1]['prefix']
    paths = [prefix.parent / 'status.json', prefix.parent.parent / 'plan.json']
    paths += [Path(str(prefix) + suffix) for suffix in validation.analysis.OUTPUTS]
    for path in paths:
        name = str(path.relative_to(root.parent.parent.parent))
        require(name in inventory['preserved_files'] and campaign.sha256(path) ==
                inventory['preserved_files'][name]['sha256'], 'corrected C1 provenance changed')
    old_parent, _ = recovery.authenticate_parent(root, replica, oracle=False)
    if replay:
        legacy.validate(prefix, old_parent, replica, steps=2000000, oracle=False, md_seed=32000 + replica)
    status = campaign.load_json(prefix.parent / 'status.json')
    require(status['status'] == 'validated' and status['completed_absolute_step'] == 8000000,
            'accepted corrected C1 endpoint absent')
    return dict(kind='e2', prefix=str(prefix), snapshot=str(prefix) + '.restart.lammpsdat',
                sha256=hash_files(paths + [INVENTORY]), historical_C1=True)


def command(entry, smoke):
    executable = Path(entry.get('executable_directory', HERE.parent)) / (
        'kg_assoc_stars_candidate_smoke' if smoke else 'kg_assoc_stars')
    parent = entry['parent']
    result = [str(executable), '--input' if parent['kind'] == 'e1' else '--restart-prefix',
              parent['snapshot'] if parent['kind'] == 'e1' else parent['prefix']]
    if parent['kind'] == 'e1':
        p = entry['physics']
        result += ['--arms', str(p['arms']), '--narm', str(p['narm'])]
        for key, option in (('dt', '--dt'), ('temperature', '--temperature'), ('Ea', '--Ea'),
                            ('Ee', '--Ee'), ('nu0', '--nu0'), ('Nevery', '--Nevery'),
                            ('r_assoc', '--r-assoc'), ('damping', '--damp'), ('K', '--K'), ('R0', '--R0')):
            result += [option, str(p[key])]
    elif entry['parent_Ea'] != entry['physics']['Ea']:
        result += ['--switch-ea-from', str(entry['parent_Ea']), '--Ea', str(entry['physics']['Ea'])]
    if entry.get('lineage'):
        result += ['--reseed-chemistry-from', str(entry['lineage']['parent_chemistry_seed']),
                   '--derived-branch-id', entry['lineage']['branch_id']]
        if entry['lineage']['reference_control']:
            result += ['--reference-control', '--Ea', '4']
    result += ['--steps', str(entry['end_step'] - entry['start_step']), '--diagnostic-every', '1000',
               '--seed', str(entry['chemistry_seed']), '--md-seed', str(entry['md_seed']),
               '--output', entry['output_prefix']]
    return result


def check_plan(root, attempt, live=False):
    attempt = inside(root, attempt)
    plan = campaign.load_json(attempt / 'plan.json')
    require(plan['schema_version'] == 1 and plan['stage'] == 'E2-G1' and
            plan['dataset_root'] == str(root) and plan['attempt'] == str(attempt), 'wrong E2 plan')
    if plan.get('lineage_mode'):
        import kg_assoc_e2_transfer as transfer
        require(plan['lineage_mode'] == transfer.MODE, 'unknown derived lineage mode')
        return transfer.check_plan(root, attempt, plan, live)
    require(not any('lineage' in h or 'executable_directory' in h for h in plan['histories']),
            'derived lineage/executable paths require explicit mode')
    system = system_by_id(plan['system']['system_id'])
    require(system == plan['system'], 'system differs from frozen campaign matrix')
    require([entry['replica'] for entry in plan['histories']] == [1, 2, 3], 'three histories required')
    for entry in plan['histories']:
        require(entry['system'] == system and entry['end_step'] - entry['start_step'] == plan['steps'] and
                entry['output_prefix'] == str(attempt / f"r{entry['replica']:03d}/state") and
                entry['command'] == command(entry, plan['smoke']) and
                entry['physics'] == validation.physics(system, plan['preparation_Ea']) and
                entry['md_seed'] != entry['chemistry_seed'] and
                entry['effective_md_seed'] == validation.effective_md_seed(entry['md_seed']),
                'command/physics/seed plan mismatch')
        check_hashes(entry['parent']['sha256'])
        validation.read_parent(entry)
    require(len({e['chemistry_seed'] for e in plan['histories']}) == 3 and
            len({e['effective_md_seed'] for e in plan['histories']}) == 3, 'seed collision')
    check_hashes(plan['evidence_sha256'])
    starts = {entry['start_step'] for entry in plan['histories']}
    require(len(starts) == 1 and plan['steps'] >= 3000 and
            (not plan['smoke'] or plan['steps'] <= 10000), 'invalid segment range')
    for entry in plan['histories']:
        parent = entry['parent']
        if parent['kind'] == 'e1':
            expected = original_e1(root, system, entry['replica'])
            require(parent == expected and entry['chemistry_seed'] == seed_map()[campaign.e2_bank_id(system)][entry['replica'] - 1],
                    'fresh history identity differs from frozen E1/seed map')
        else:
            if parent.get('historical_C1'):
                require(campaign.e2_bank_id(system) == 'F04_N010_RP080_EE08' and
                        parent == corrected_c1(root, entry['replica'], replay=False) and plan['smoke'],
                        'historical parent is not the pinned corrected C1 endpoint')
            else:
                require(plan['parent_attempt'] is not None, 'extension lacks an authenticated predecessor')
                predecessor = inside(root, plan['parent_attempt'])
                previous = campaign.load_json(predecessor / 'plan.json')
                history = previous['histories'][entry['replica'] - 1]
                complete_path = predecessor / f"r{entry['replica']:03d}/complete.json"
                require(str(complete_path) in parent['sha256'] and
                        str(predecessor / 'plan.json') in parent['sha256'], 'transition hashes absent')
                complete = campaign.load_json(complete_path)
                require(previous['system'] == system and previous['smoke'] is False and
                        history['output_prefix'] == parent['prefix'] and
                        history['end_step'] == entry['start_step'] and
                        history['chemistry_seed'] == entry['chemistry_seed'] and
                        plan['segment_index'] == previous['segment_index'] + 1 and
                        complete['status'] == 'validated' and complete['plan_sha256'] ==
                        campaign.sha256(predecessor / 'plan.json'), 'invalid frozen segment transition')
            require(entry['physics']['Ea'] == entry['parent_Ea'] or
                    (plan['smoke'] and parent.get('historical_C1') and
                     entry['start_step'] == 8000000 and entry['physics']['Ea'] in (6, 8, 10)),
                    'unapproved chemistry parameter transition')
    if live:
        live_code(plan)
    return plan


def allocate_md_seeds(root):
    policy = campaign.load_json(HERE / 'e2_seed_map.json')
    reserved = {validation.effective_md_seed(seed) for seed in policy['reserved_md_system_seeds']}
    for policy_path in [HERE / 'e2_transfer_seeds_v1.json',
                        *(root / 'banks/e2_seed_reservations').glob('*.json')]:
        transfer_policy = campaign.load_json(policy_path)
        reserved.update(validation.effective_md_seed(row['md_seed'])
                        for row in transfer_policy['streams'])
    used = set()
    for path in (root / 'banks/e2_attempts').glob('*/*/plan.json'):
        plan = campaign.load_json(path)
        for entry in plan['histories']:
            used.add(entry['md_seed'])
            reserved.add(entry['effective_md_seed'])
    seed = max(used, default=policy['md_seed_floor']) + 1
    result = []
    while len(result) < 3:
        effective = validation.effective_md_seed(seed)
        if effective not in reserved:
            result.append(seed)
            reserved.add(effective)
        seed += 1
    return result


def prepare(root, output, identifier, steps, evidence, parent_attempt=None, smoke=False,
            c1=False, ea=4, build_evidence=None):
    system = system_by_id(identifier)
    bank = campaign.e2_bank_id(system)
    output = inside(root, output)
    require(output.parent == root / 'banks/e2_attempts' / bank and not output.exists(),
            'choose a NEW direct attempt child of banks/e2_attempts/<bank>')
    require(type(steps) is int and steps >= 3000 and
            (not smoke or steps <= 10000), 'at least 3000 steps for diagnostic validation; smoke capped at 10000')
    require(ea == 4 or (smoke and c1 and ea in (6, 8, 10)) or
            (parent_attempt is not None and ea in (6, 8, 10)), 'fresh preparation requires Ea=4')
    require(evidence.is_file(), 'review evidence is required')
    require(not (c1 and parent_attempt), 'choose one parent mode')
    require(not c1 or (bank == 'F04_N010_RP080_EE08' and smoke),
            'C1 import here is a capped switch smoke only, never an additional recovery')
    require(c1 or bank != 'F04_N010_RP080_EE08' or parent_attempt,
            'accepted C1 must not be replaced with a fresh bank')
    live_code()
    build_record, build_manifest = check_build(build_evidence)
    require(not build_record.get('out_of_tree'), 'ordinary preparation requires a standard build')
    protocol = root / 'campaign_protocol.json'
    require(campaign.load_json(protocol) == campaign.load_json(campaign.PROTOCOL_PATH), 'dataset protocol mismatch')
    require(set(campaign.load_json(root / 'manifest.json')['systems']) ==
            {s['system_id'] for s in campaign.campaign_systems()}, 'dataset manifest matrix mismatch')
    previous = verify(root, inside(root, parent_attempt)) if parent_attempt else None
    if previous:
        require(previous['system'] == system and not previous['smoke'] and
                all(h['physics'] == validation.physics(system, ea) for h in previous['histories']),
                'extension parent must be a complete ordinary segment of the same condition')
    lock = root / 'banks/.e2.prepare.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('x') as stream:
        json.dump(dict(host=socket.gethostname(), pid=os.getpid()), stream)
    try:
        md_seeds = allocate_md_seeds(root)
        histories = []
        for replica in (1, 2, 3):
            if previous:
                prior = previous['histories'][replica - 1]
                prefix = prior['output_prefix']
                directory = Path(prefix).parent
                parent = dict(kind='e2', prefix=prefix, snapshot=prefix + '.restart.lammpsdat',
                              sha256=hash_files([Path(prefix + suffix) for suffix in validation.OUTPUTS] +
                                               [directory / 'complete.json', Path(parent_attempt) / 'plan.json']))
                chemistry_seed = prior['chemistry_seed']
            elif c1:
                parent = corrected_c1(root, replica)
                chemistry_seed = 22000 + replica
            else:
                parent = original_e1(root, system, replica)
                chemistry_seed = seed_map()[bank][replica - 1]
            if parent['kind'] == 'e2':
                metadata, _ = validation.analysis.restart.read_metadata(parent['prefix'] + '.assoc_restart')
                start, parent_ea = int(metadata['completed_steps']), float(metadata['Ea'])
            else:
                start, parent_ea = 0, ea
            entry = dict(replica=replica, system=system, parent=parent, physics=validation.physics(system, ea),
                         parent_Ea=parent_ea, start_step=start, end_step=start + steps,
                         chemistry_seed=chemistry_seed, md_seed=md_seeds[replica - 1],
                         effective_md_seed=validation.effective_md_seed(md_seeds[replica - 1]),
                         output_prefix=str(output / f'r{replica:03d}/state'))
            validation.read_parent(entry)
            entry['command'] = command(entry, smoke)
            histories.append(entry)
        executable_hashes = hash_files([HERE.parent / name for name in EXECUTABLES])
        require(subprocess.run([str(HERE.parent / 'kg_assoc_stars'), '--self-test'],
                               capture_output=True, text=True, check=True).stdout.find('SELF_TEST PASS') >= 0,
                'E2 host self-test failed')
        subprocess.run([str(HERE.parent / 'kg_assoc_candidates_test')], check=True, capture_output=True)
        for entry in histories:
            actual = subprocess.check_output([str(HERE.parent / 'kg_assoc_stars'), '--md-seed-info',
                                              str(entry['md_seed'])], text=True).strip()
            require(int(actual) == entry['effective_md_seed'], 'MD effective-seed implementation mismatch')
        plan = dict(schema_version=1, stage='E2-G1', dataset_root=str(root), attempt=str(output),
                    system=system, histories=histories, steps=steps, smoke=smoke, preparation_Ea=ea,
                    segment_index=previous['segment_index'] + 1 if previous else 1,
                    parent_attempt=str(parent_attempt) if parent_attempt else None,
                    git_sha=campaign.git_sha(), source_sha256=sources(), executable_sha256=executable_hashes,
                    evidence_sha256=hash_files([evidence, protocol, root / 'manifest.json', INVENTORY, build_manifest]),
                    rng_policy='distinct_new_bank_chemistry; inherited_absolute_step_identity; fresh_MD_each_segment',
                    image_policy='fold_on_restart; no_transport_or_lifetime_stitching',
                    prepared_at=timestamp(), scientific_status='review_required',
                    build=build_record)
        output.mkdir(parents=True, exist_ok=False)
        exclusive_json(output / 'plan.json', plan)
        for replica in (1, 2, 3):
            (output / f'r{replica:03d}').mkdir()
        exclusive_json(output / 'approval.example.json', dict(
            schema_version=1, approved=False, purpose='e2_smoke' if smoke else 'e2_segment',
            plan_sha256=campaign.sha256(output / 'plan.json'), reviewer='', approved_at=''))
    finally:
        lock.unlink()
    return plan


def verify(root, attempt):
    plan = check_plan(root, attempt)
    for entry in plan['histories']:
        directory = Path(entry['output_prefix']).parent
        complete = campaign.load_json(directory / 'complete.json')
        require(complete['status'] == 'validated' and complete['plan_sha256'] ==
                campaign.sha256(attempt / 'plan.json'), 'completion absent or wrong plan')
        check_hashes(complete['output_sha256'])
        validation.validate(entry, oracle=plan['smoke'])
    return plan


def approval_record(path, plan_path, purpose):
    require(path is not None, 'execution requires a plan-hash-bound approval')
    record = campaign.load_json(path)
    require(record.get('schema_version') == 1 and record.get('approved') is True and
            record.get('purpose') == purpose and record.get('plan_sha256') == campaign.sha256(plan_path) and
            isinstance(record.get('reviewer'), str) and record['reviewer'].strip() and
            isinstance(record.get('approved_at'), str) and record['approved_at'].strip(), 'invalid approval')
    return record


def smoke_code_compatible(smoke, plan):
    return (smoke['executable_sha256'] == plan['executable_sha256'] and
            scientific_source_hashes(smoke['source_sha256']) ==
            scientific_source_hashes(plan['source_sha256']))


def matching_smoke(root, attempt, plan):
    require(attempt is not None, 'ordinary E2 requires matching capped GPU smoke evidence')
    smoke = verify(root, inside(root, attempt))
    require(smoke['smoke'] and smoke['steps'] <= 10000 and
            smoke_code_compatible(smoke, plan), 'smoke code/build differs from segment')
    for test, entry in zip(smoke['histories'], plan['histories']):
        derived = plan.get('lineage_mode') == 'Ea_reference_transfer_v1'
        require(test['physics'] == entry['physics'] and test['parent']['sha256'] == entry['parent']['sha256'] and
                (test['chemistry_seed'] == entry['chemistry_seed'] or (derived and
                 smoke.get('lineage_mode') == plan['lineage_mode'] and
                 test['lineage']['reference_control'] == entry['lineage']['reference_control'])) and
                test['parent_Ea'] == entry['parent_Ea'],
                'smoke did not test this parent/chemistry path')
    return hash_files([attempt / 'plan.json'] +
                      [attempt / f'r{replica:03d}/complete.json' for replica in (1, 2, 3)])


def launch_scope(plan, replica, replicas=None):
    require(replica is None or replicas is None, 'choose one explicit selector')
    if replicas is not None:
        import kg_assoc_e2_transfer as transfer
        sid = plan['system']['system_id']
        allowed = [2, 3] if sid == transfer.REFERENCE else (
            [1, 2, 3] if sid in transfer.TARGETS else [])
        require(type(replicas) is list and bool(replicas) and
                all(type(value) is int for value in replicas) and
                replicas == sorted(set(replicas)) and set(replicas) <= set(allowed) and
                plan.get('lineage_mode') == transfer.MODE and plan['smoke'] is True and
                plan.get('reference_control') is (sid == transfer.REFERENCE) and
                type(plan['steps']) is int and 3000 <= plan['steps'] <= 10000,
                'remaining-smoke selector requires an authorized Ea4 r002/r003 or Ea6/8/10 subset')
        histories = [entry for entry in plan['histories'] if entry['replica'] in replicas]
        require([entry['replica'] for entry in histories] == replicas,
                'selected histories missing or duplicated')
        return histories
    if replica is None:
        return plan['histories']
    require(type(replica) is int and replica == 1 and
            plan.get('lineage_mode') == 'Ea_reference_transfer_v1' and
            plan.get('reference_control') is True and plan['smoke'] is True and
            plan['system']['system_id'] == 'F04_N010_RP080_EE08_EA04' and
            3000 <= plan['steps'] <= 10000,
            'single-history selection requires derived Ea4 r001 control smoke')
    histories = [entry for entry in plan['histories'] if entry['replica'] == replica]
    require(len(histories) == 1, 'selected history missing or duplicated')
    return histories


def scoped_launch_approval(path, attempt, purpose, plan, replica, replicas=None):
    record = approval_record(path, attempt / 'plan.json', purpose)
    if replicas is not None:
        histories = launch_scope(plan, replica, replicas)
        require(record.get('selector_scope') == 'Ea_transfer_remaining_smoke_v1' and
                record.get('authorized_system') == plan['system']['system_id'] and
                type(record.get('authorized_replicas')) is list and
                all(type(value) is int for value in record['authorized_replicas']) and
                record['authorized_replicas'] == replicas and
                type(record.get('maximum_additional_MD_steps_per_history')) is int and
                record['maximum_additional_MD_steps_per_history'] == plan['steps'] and
                type(record.get('maximum_additional_MD_steps')) is int and
                record['maximum_additional_MD_steps'] == plan['steps'] * len(histories),
                'remaining-smoke approval scope/cap differs; explicit selector required')
    elif replica is not None or any(key in record for key in (
            'authorized_replicas', 'selector_scope', 'authorized_system',
            'maximum_additional_MD_steps_per_history')):
        require(replica == 1 and type(record.get('authorized_replicas')) is list and
                record['authorized_replicas'] == [1] and
                type(record['authorized_replicas'][0]) is int and
                type(record.get('maximum_additional_MD_steps')) is int and
                record['maximum_additional_MD_steps'] == plan['steps'],
                'single-history approval scope/cap differs; explicit selector required')
    return record


def launch(root, attempt, execute=False, approval=None, smoke_attempt=None,
           replica=None, replicas=None):
    plan = check_plan(root, attempt, live=execute)
    histories = launch_scope(plan, replica, replicas)
    for entry in plan['histories']:
        require(not any(Path(entry['output_prefix']).parent.iterdir()), 'attempt already used; preserve it')
    if not execute:
        print(json.dumps(dict(executed=False, commands=[e['command'] for e in histories]), indent=2))
        return
    purpose = ('e2_derived_smoke' if plan['smoke'] else 'e2_derived_segment') if plan.get(
        'lineage_mode') else ('e2_smoke' if plan['smoke'] else 'e2_segment')
    scoped_launch_approval(approval, attempt, purpose, plan, replica, replicas)
    smoke_hashes = {} if plan['smoke'] else matching_smoke(root, smoke_attempt, plan)
    lock = attempt / '.launch.lock'
    with lock.open('x') as stream:
        json.dump(dict(pid=os.getpid(), host=socket.gethostname()), stream)
    try:
        for entry in histories:
            check_plan(root, attempt, live=True)
            check_hashes(smoke_hashes)
            scoped_launch_approval(approval, attempt, purpose, plan, replica, replicas)
            directory = Path(entry['output_prefix']).parent
            require(not any(directory.iterdir()), 'replica outputs appeared during preflight')
            exclusive_json(directory / 'started.json', dict(plan_sha256=campaign.sha256(attempt / 'plan.json'),
                           command=entry['command'], approval_sha256=campaign.sha256(approval),
                           smoke_sha256=smoke_hashes, host=socket.gethostname(), started_at=timestamp()))
            start = time.monotonic()
            try:
                environment = subprocess.check_output(['nvidia-smi', '--query-gpu=name,uuid,driver_version',
                                                       '--format=csv,noheader'], text=True)
                exclusive_json(directory / 'environment.json', dict(gpu=environment, host=socket.gethostname()))
                with (directory / 'stdout.log').open('x') as stdout, (directory / 'stderr.log').open('x') as stderr:
                    process = subprocess.Popen(entry['command'], stdout=stdout, stderr=stderr)
                    try:
                        require(process.wait() == 0, 'MD executable failed')
                    except BaseException:
                        process.terminate()
                        process.wait()
                        raise
                require('STAR_ASSOCIATION_SMOKE PASS' in (directory / 'stdout.log').read_text(),
                        'missing executable completion marker')
                check_hashes(entry['parent']['sha256'])
                live_code(plan)
                _, _, result = validation.validate(entry, oracle=plan['smoke'])
                exclusive_json(directory / 'complete.json', dict(
                    status='validated', plan_sha256=campaign.sha256(attempt / 'plan.json'),
                    validation=result, end_step=entry['end_step'], wall_seconds=time.monotonic() - start,
                    finished_at=timestamp(), output_sha256=hash_files(directory.iterdir())))
            except BaseException as error:
                exclusive_json(directory / 'incomplete.json', dict(error=str(error), finished_at=timestamp()))
                raise
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'prepare', 'launch', 'verify', 'status'))
    parser.add_argument('--dataset-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--system')
    parser.add_argument('--steps', type=int)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--build-evidence', type=Path)
    parser.add_argument('--parent-attempt', type=Path)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--c1', action='store_true')
    parser.add_argument('--out-of-tree', action='store_true', help='build into NEW evidence directory')
    parser.add_argument('--ea', type=float, default=4)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--approval', type=Path)
    parser.add_argument('--smoke-attempt', type=Path)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--replica', type=int, choices=(1,),
                           help='legacy single Ea4 r001 selector; requires its own approval')
    selection.add_argument('--replicas', type=int, nargs='+', choices=(1, 2, 3),
                           help='explicit remaining-smoke subset; requires scoped system/cap approval')
    args = parser.parse_args()
    root, output = args.dataset_root.resolve(), args.output.resolve()
    if args.action == 'build':
        build(root, output, args.out_of_tree)
    elif args.action == 'prepare':
        require(args.system and args.steps and args.evidence, 'prepare needs system, steps and evidence')
        prepare(root, output, args.system, args.steps, args.evidence.resolve(),
                args.parent_attempt.resolve() if args.parent_attempt else None, args.smoke, args.c1, args.ea, args.build_evidence)
    elif args.action == 'launch':
        launch(root, output, args.execute, args.approval,
               args.smoke_attempt.resolve() if args.smoke_attempt else None,
               args.replica, args.replicas)
    elif args.action == 'verify':
        verify(root, output)
        print('E2 numerical/event/network verification PASS; scientific review required')
    else:
        for replica in (1, 2, 3):
            directory = output / f'r{replica:03d}'
            status = 'validated' if (directory / 'complete.json').exists() else 'incomplete' if (
                directory / 'incomplete.json').exists() else 'running_or_interrupted' if (
                directory / 'started.json').exists() else 'unlaunched'
            print(f'r{replica:03d}: {status}; scientific review required')


if __name__ == '__main__':
    main()
