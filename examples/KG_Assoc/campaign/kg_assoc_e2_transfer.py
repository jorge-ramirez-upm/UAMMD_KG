#!/usr/bin/env python3
"""Inspect/prepare explicitly derived Ea branches; inspection never builds or runs MD."""
import argparse
import json
from pathlib import Path
import re

import kg_assoc_e2 as e2

MODE = 'Ea_reference_transfer_v1'
REFERENCE = 'F04_N010_RP080_EE08_EA04'
TARGETS = tuple(f'F04_N010_RP080_EE08_EA{ea:02d}' for ea in (6, 8, 10))
ACCEPTANCE_NAME = REFERENCE + '_8M_qualified_20261013_v1.json'
ACCEPTANCE_SHA256 = '525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22'
RESERVATIONS = e2.HERE / 'e2_transfer_seeds_v1.json'
require = e2.require


def reference(root):
    """Authenticate only the exact accepted corrected endpoints, never the old 6M bank."""
    import kg_assoc_e2_registry as registry
    path = root / 'banks/e2_acceptance' / ACCEPTANCE_NAME
    require(e2.campaign.sha256(path) == ACCEPTANCE_SHA256, 'reference acceptance identity differs')
    record = e2.campaign.load_json(path)
    require(record['permitted_systems'] == [REFERENCE] and
            record['permitted_use'] == 'production_initial_state' and
            record['provenance_kind'] == 'corrected_C1_8M', 'reference scope differs')
    registry.exclusive_validate(record, [e2.system_by_id(REFERENCE)])
    parents = []
    for history in record['histories']:
        replica = history['replica']
        expected = root / 'banks/e2_extensions/C1_periodic_recovery_v1' / f'r{replica:03d}/state'
        require(history['prefix'] == str(expected) and history['end_step'] == 8000000 and
                history['physics'] == e2.validation.physics(e2.system_by_id(REFERENCE), 4) and
                history['chemistry_seed'] == 22000 + replica, 'wrong reference endpoint')
        parent = e2.corrected_c1(root, replica, replay=False)
        # The acceptance also binds every reference output and its historical receipt.
        parent['sha256'].update(history['sha256'])
        parent['sha256'][str(path)] = ACCEPTANCE_SHA256
        parent['reference_acceptance'] = str(path)
        parent['reference_acceptance_sha256'] = ACCEPTANCE_SHA256
        parents.append(parent)
    return record, parents


def streams_in_use(root, ignore_attempt=None, ignore_md_reservation=None):
    """Inspect recorded streams without invoking executables or changing reservations."""
    policy = e2.campaign.load_json(e2.HERE / 'e2_seed_map.json')
    requested = set(policy['reserved_md_system_seeds'])
    chemical = {s for values in policy['chemical_seeds'].values() for s in values}
    md = {e2.validation.effective_md_seed(s) for s in requested}
    uses = [(s, None, '<policy>') for s in chemical | requested]
    uses += [(None, s, '<policy>') for s in md]
    for path in (root / 'banks/e2_md_reservations').glob('*.json'):
        if ignore_md_reservation and path.resolve() == Path(ignore_md_reservation).resolve():
            continue
        for row in e2.campaign.load_json(path)['streams']:
            requested.add(row['md_seed'])
            md.add(row['effective_md_seed'])
    for path in (root / 'banks').rglob('*.json'):
        if ignore_attempt and Path(ignore_attempt) in path.parents:
            continue
        data = e2.campaign.load_json(path)
        for history in data.get('histories', []):
            prefix = history.get('output_prefix', history.get('prefix'))
            if ignore_attempt and prefix and Path(ignore_attempt) in Path(prefix).parents:
                continue
            if 'chemistry_seed' in history:
                chemical.add(history['chemistry_seed'])
                uses.append((history['chemistry_seed'], None, prefix))
            if 'md_seed' in history:
                requested.add(history['md_seed'])
                md.add(e2.validation.effective_md_seed(history['md_seed']))
                uses.append((history['md_seed'], e2.validation.effective_md_seed(history['md_seed']), prefix))
            if 'effective_md_seed' in history:
                md.add(history['effective_md_seed'])
                uses.append((None, history['effective_md_seed'], prefix))
        # Legacy sidecars/logs retain streams not represented by modern plans.
    for path in (root / 'banks').rglob('*.assoc_restart'):
        if ignore_attempt and Path(ignore_attempt) in path.parents:
            continue
        metadata, _ = e2.validation.analysis.restart.read_metadata(str(path))
        chemical.add(int(metadata['seed']))
        uses.append((int(metadata['seed']), None, str(path)[:-len('.assoc_restart')]))
    for path in (root / 'banks').rglob('*.state'):
        if ignore_attempt and Path(ignore_attempt) in path.parents:
            continue
        with path.open() as stream:
            for line in stream:
                if not line.startswith('#'):
                    break
                for key, value in re.findall(r'\b(seed|md_seed)=([0-9]+)', line):
                    uses.append((int(value), e2.validation.effective_md_seed(int(value))
                                 if key == 'md_seed' else None, str(path)[:-len('.state')]))
                    if key == 'seed':
                        chemical.add(int(value))
                    else:
                        requested.add(int(value))
                        md.add(e2.validation.effective_md_seed(int(value)))
    return chemical, requested, md, uses


def validate_lineage(entry, metadata, pairs):
    """Authenticate derived parent/seed identity even for a standalone segment reader."""
    lineage, parent = entry['lineage'], entry['parent']
    require(type(entry['replica']) is int and 1 <= entry['replica'] <= 3,
            'invalid original replica identity')
    sid = entry['system']['system_id']
    control = lineage['reference_control']
    require((sid in TARGETS and control is False) or (sid == REFERENCE and control is True),
            'unsupported derived target/control')
    acceptance = Path(parent['reference_acceptance'])
    require(acceptance.name == ACCEPTANCE_NAME and
            e2.campaign.sha256(acceptance) == ACCEPTANCE_SHA256, 'reference acceptance differs')
    root = acceptance.parents[2]
    record = e2.campaign.load_json(acceptance)
    history = record['histories'][entry['replica'] - 1]
    expected_prefix = str(root / 'banks/e2_extensions/C1_periodic_recovery_v1' /
                          f"r{entry['replica']:03d}/state")
    require(parent['prefix'] == history['prefix'] == expected_prefix and
            parent['snapshot'] == expected_prefix + '.restart.lammpsdat' and
            parent['reference_acceptance_sha256'] == ACCEPTANCE_SHA256,
            'derived parent identity differs')
    for suffix in ('.restart.lammpsdat', '.assoc_restart'):
        name = expected_prefix + suffix
        e2.check_hashes({name: history['sha256'][name]})
    policy_path = reservation_path(root, lineage['seed_reservations'])
    require(e2.campaign.sha256(policy_path) == lineage['seed_reservations_sha256'],
            'derived seed-reservation binding differs')
    expected = dict(mode=MODE, reference_control=control, system_id=sid,
        seed_reservations=str(policy_path), seed_reservations_sha256=e2.campaign.sha256(policy_path),
        target_Ea=entry['system']['Ea'], parent_chemistry_seed=history['chemistry_seed'],
        parent_Ea=4, branch_origin_step=8000000, parent_creations=int(metadata['creations']),
        parent_breaks=int(metadata['breaks']), initial_bonds=len(pairs),
        reference_acceptance=str(acceptance), reference_acceptance_sha256=ACCEPTANCE_SHA256,
        reference_qualification=record['qualification'], bitwise_md_continuation=False,
        independent_parent_replica=entry['replica'], branch_id=sid + ':' +
        Path(entry['output_prefix']).parents[1].name + f":r{entry['replica']:03d}")
    require(lineage == expected and entry['start_step'] == 8000000 and entry['parent_Ea'] == 4 and
            int(metadata['seed']) == history['chemistry_seed'] and
            entry['physics'] == e2.validation.physics(e2.system_by_id(sid), entry['system']['Ea']),
            'derived lineage/physics/offset mismatch')
    streams = e2.campaign.load_json(policy_path)['streams']
    require(any(row['system_id'] == sid and row['reference_control'] == control and
                row['replica'] == entry['replica'] and
                row['chemistry_seed'] == entry['chemistry_seed'] and
                row['md_seed'] == entry['md_seed'] for row in streams) and
            entry['chemistry_seed'] != int(metadata['seed']) and
            entry['effective_md_seed'] == e2.validation.effective_md_seed(entry['md_seed']),
            'derived random stream identity differs')


def reservation_path(root, path=None):
    path = Path(path or RESERVATIONS).resolve()
    require(path == RESERVATIONS.resolve() or
            path.parent == (Path(root) / 'banks/e2_seed_reservations').resolve(),
            'additional reservations must be immutable dataset seed-reservation files')
    return path


def reserved_streams(root, ignore_attempt=None, seed_reservations=None):
    policy_path = reservation_path(root, seed_reservations)
    reservation = e2.campaign.load_json(policy_path)
    require(reservation['schema_version'] == 1 and len(reservation['streams']) == 12,
            'invalid transfer reservation set')
    rows = reservation['streams']
    require({(r['system_id'], r['replica'], r['reference_control']) for r in rows} ==
            {(s, r, s == REFERENCE) for s in (*TARGETS, REFERENCE) for r in (1, 2, 3)},
            'reservation identities differ')
    chemical, requested, md, uses = streams_in_use(root, ignore_attempt)
    new_chemical = [r['chemistry_seed'] for r in rows]
    new_md = [r['md_seed'] for r in rows]
    effective = [e2.validation.effective_md_seed(s) for s in new_md]
    for other_path in [RESERVATIONS, *(Path(root) / 'banks/e2_seed_reservations').glob('*.json')]:
        if other_path.resolve() == policy_path:
            continue
        other = e2.campaign.load_json(other_path)['streams']
        other_seeds = {r[k] for r in other for k in ('chemistry_seed', 'md_seed')}
        other_effective = {e2.validation.effective_md_seed(r['md_seed']) for r in other}
        require(not (set(new_chemical + new_md) & other_seeds or set(effective) & other_effective),
                'seed reservation sets collide')
    require(all(type(s) is int and 0 < s < 2**64 for s in new_chemical + new_md) and
            len(set(new_chemical + new_md)) == 24 and len(set(effective)) == 12,
            'transfer reservation seed collision')
    # Check only unclaimed rows; other target preparations may already own their rows.
    for row, kernel in zip(rows, effective):
        owners = []
        for path in (root / 'banks/e2_attempts').glob('*/*/plan.json'):
            if ignore_attempt and path.parent == Path(ignore_attempt):
                continue
            plan = e2.campaign.load_json(path)
            if plan.get('lineage_mode') == MODE:
                owners.extend(h for h in plan['histories'] if
                              h['chemistry_seed'] == row['chemistry_seed'] and
                              h['md_seed'] == row['md_seed'] and
                              h['system']['system_id'] == row['system_id'] and
                              h['replica'] == row['replica'])
        used = (row['chemistry_seed'] in chemical | requested or
                row['md_seed'] in requested | chemical or kernel in md)
        row['claimed'] = bool(owners)
        require(not used or len(owners) == 1, 'reserved stream collides with existing evidence')
        allowed = {h['output_prefix'] for h in owners}
        # Same-condition extensions keep chemistry, but must descend from this family.
        pending = [e2.campaign.load_json(p) for p in
                   (root / 'banks/e2_attempts').glob('*/*/plan.json')]
        changed = True
        while changed:
            changed = False
            for plan in pending:
                if (plan.get('lineage_mode') not in (None, 'Ea_24M_extension_v1',
                                                    'Ea_reviewed_extension_v2') or
                        plan.get('system', {}).get('system_id') != row['system_id']):
                    continue
                for history in plan.get('histories', []):
                    if (history.get('replica') == row['replica'] and
                            history.get('chemistry_seed') == row['chemistry_seed'] and
                            history.get('parent', {}).get('prefix') in allowed and
                            history.get('output_prefix') not in allowed):
                        e2.check_hashes(history['parent']['sha256'])
                        e2.validation.read_parent(history)
                        allowed.add(history['output_prefix'])
                        changed = True
        require(all(prefix in allowed for seed, effective_seed, prefix in uses
                    if seed in (row['chemistry_seed'], row['md_seed']) or effective_seed == kernel),
                'reserved stream has conflicting owners')
        row['effective_md_seed'] = kernel
    return reservation, rows


def inspect(root, output, identifier, steps=10000, smoke=True, control=False,
            ignore_attempt=None, executable_directory=None, seed_reservations=None):
    root, output = Path(root).resolve(), e2.inside(root, output)
    require(type(smoke) is bool and type(control) is bool, 'explicit boolean smoke/control required')
    require((identifier in TARGETS and not control) or (identifier == REFERENCE and control),
            'unsupported derived target/control')
    system = e2.system_by_id(identifier)
    require(e2.campaign.load_json(root / 'campaign_protocol.json') ==
            e2.campaign.load_json(e2.campaign.PROTOCOL_PATH) and
            set(e2.campaign.load_json(root / 'manifest.json')['systems']) ==
            {s['system_id'] for s in e2.campaign.campaign_systems()}, 'dataset protocol/matrix differs')
    require(output.parent == root / 'banks/e2_attempts' / e2.campaign.e2_bank_id(system) and
            output.name.startswith('derived_' + identifier + '_') and
            re.fullmatch(r'[A-Za-z0-9_]+', output.name), 'full derived system/attempt identity required')
    require(not output.exists() or output == ignore_attempt, 'derived output already exists')
    require(type(steps) is int and 3000 <= steps and (not smoke or steps <= 10000),
            'invalid derived duration; smoke capped at 10000')
    accepted, parents = reference(root)
    policy_path = reservation_path(root, seed_reservations)
    reservation, streams = reserved_streams(root, ignore_attempt, policy_path)
    histories = []
    for replica, parent in enumerate(parents, 1):
        seed = next(s for s in streams if s['system_id'] == identifier and s['replica'] == replica)
        require(not seed['claimed'], 'reservation already used; retain attempt and reserve new streams')
        meta, pairs = e2.validation.analysis.restart.read_metadata(parent['prefix'] + '.assoc_restart')
        lineage = dict(mode=MODE, reference_control=control, system_id=identifier,
            seed_reservations=str(policy_path), seed_reservations_sha256=e2.campaign.sha256(policy_path),
            target_Ea=system['Ea'], parent_chemistry_seed=int(meta['seed']),
            parent_Ea=4, branch_origin_step=8000000, parent_creations=int(meta['creations']),
            parent_breaks=int(meta['breaks']), initial_bonds=len(pairs),
            reference_acceptance=parent['reference_acceptance'],
            reference_acceptance_sha256=ACCEPTANCE_SHA256,
            reference_qualification=accepted['qualification'],
            bitwise_md_continuation=False, independent_parent_replica=replica,
            branch_id=identifier + ':' + output.name + f':r{replica:03d}')
        entry = dict(replica=replica, system=system, parent=parent,
            physics=e2.validation.physics(system, system['Ea']), parent_Ea=4,
            start_step=8000000, end_step=8000000 + steps, lineage=lineage,
            chemistry_seed=seed['chemistry_seed'], md_seed=seed['md_seed'],
            effective_md_seed=seed['effective_md_seed'],
            output_prefix=str(output / f'r{replica:03d}/state'))
        if executable_directory is not None:
            entry['executable_directory'] = str(Path(executable_directory).resolve())
        e2.validation.read_parent(entry)
        entry['command'] = e2.command(entry, smoke)
        histories.append(entry)
    return dict(schema_version=1, stage='E2-G1', lineage_mode=MODE, dataset_root=str(root),
        attempt=str(output), system=system, histories=histories, steps=steps, smoke=smoke,
        preparation_Ea=system['Ea'], reference_control=control, segment_index=1,
        parent_attempt=None, reservation_id=reservation['reservation_id'],
        reservation_sha256=e2.hash_files([policy_path]),
        executed=False, scientific_status='review_required', production_authorization=False)


def check_plan(root, output, plan, live=False):
    require(len(plan['reservation_sha256']) == 1, 'one seed-reservation set per branch')
    e2.check_hashes(plan['reservation_sha256'])
    policy_path = next(iter(plan['reservation_sha256']))
    directory = None
    if plan.get('build', {}).get('out_of_tree'):
        names = plan['build']['executable_sha256']
        directory = next(Path(name).parent for name in names if Path(name).name == 'kg_assoc_stars')
        require(set(names) == {str(directory / name) for name in e2.EXECUTABLES}, 'bad build paths')
    expected = inspect(root, output, plan['system']['system_id'], plan['steps'], plan['smoke'],
                       plan['reference_control'], ignore_attempt=output, executable_directory=directory,
                       seed_reservations=policy_path)
    require(all(plan.get(key) == value for key, value in expected.items()),
            'derived plan identity, lineage, physics or streams differ')
    require(len(plan.get('initial_state_checks', [])) == 3 and
            all('INITIAL_STATE_VALIDATED' in s for s in plan['initial_state_checks']),
            'derived CPU initialization receipts absent')
    e2.check_hashes(plan['evidence_sha256'])
    manifests = [Path(name) for name in plan['evidence_sha256']
                 if Path(name).name == 'manifest.json']
    require(len(manifests) == 1 and e2.campaign.load_json(manifests[0]) == plan['build'],
            'derived embedded build differs from manifest')
    if live:
        e2.live_code(plan)
    return plan


def prepare(root, output, identifier, steps, evidence, smoke=True, control=False,
            build_evidence=None, seed_reservations=None):
    """Reserve a NEW immutable plan under the existing global E2 preparation lock."""
    root, output = Path(root).resolve(), Path(output).resolve()
    require(Path(evidence).is_file(), 'scientific evidence required')
    e2.clean_tree()
    build, manifest = e2.check_build(build_evidence)
    require(build.get("out_of_tree") is True, "derived preparation requires preserved-binary out-of-tree build")
    lock = root / 'banks/.e2.prepare.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('x'):
        pass
    try:
        plan = inspect(root, output, identifier, steps, smoke, control,
                       executable_directory=manifest.parent, seed_reservations=seed_reservations)
        # Host-only validation returns before System/ParticleData construction or output I/O.
        checks = []
        for entry in plan['histories']:
            result = e2.subprocess.run(entry['command'] + ['--validate-initial-state'],
                                       check=True, capture_output=True, text=True)
            require('INITIAL_STATE_VALIDATED' in result.stdout, 'host initial-state check failed')
            actual = e2.subprocess.check_output([str(manifest.parent / 'kg_assoc_stars'),
                '--md-seed-info', str(entry['md_seed'])], text=True).strip()
            require(int(actual) == entry['effective_md_seed'], 'native effective MD seed differs')
            checks.append(result.stdout.strip())
        plan.update(git_sha=e2.campaign.git_sha(), source_sha256=e2.sources(),
            executable_sha256=e2.hash_files([manifest.parent / name for name in e2.EXECUTABLES]),
            build=build, initial_state_checks=checks,
            evidence_sha256=e2.hash_files([Path(evidence), manifest]) | plan['reservation_sha256'])
        output.mkdir(parents=True, exist_ok=False)
        e2.exclusive_json(output / 'plan.json', plan)
        for replica in (1, 2, 3):
            (output / f'r{replica:03d}').mkdir()
        e2.exclusive_json(output / 'approval.example.json', dict(schema_version=1, approved=False,
            purpose='e2_derived_smoke' if smoke else 'e2_derived_segment',
            plan_sha256=e2.campaign.sha256(output / 'plan.json'), reviewer='', approved_at=''))
        return plan
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'prepare'))
    parser.add_argument('--dataset-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--system', required=True, choices=(*TARGETS, REFERENCE))
    parser.add_argument('--steps', type=int, default=10000)
    parser.add_argument('--ordinary', action='store_true')
    parser.add_argument('--control', action='store_true')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--build-evidence', type=Path)
    parser.add_argument('--seed-reservations', type=Path)
    args = parser.parse_args()
    if args.action == 'inspect':
        directory = None
        if args.build_evidence:
            build, manifest = e2.check_build(args.build_evidence)
            require(build.get('out_of_tree'), 'derived inspection requires an out-of-tree build')
            directory = manifest.parent
        value = inspect(args.dataset_root, args.output, args.system, args.steps,
                        not args.ordinary, args.control, executable_directory=directory,
                        seed_reservations=args.seed_reservations)
    else:
        require(args.evidence is not None, 'prepare needs scientific evidence')
        value = prepare(args.dataset_root, args.output, args.system, args.steps,
                        args.evidence, not args.ordinary, args.control, args.build_evidence, args.seed_reservations)
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
