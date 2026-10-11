#!/usr/bin/env python3
"""Publish immutable acceptance records and explicitly selected active E2 registries."""

import argparse
from pathlib import Path

import kg_assoc_campaign as campaign
import kg_assoc_e2 as e2

require = e2.require


def permitted(record, system):
    require(system['system_id'] in record['permitted_systems'] and record['permitted_use'] == 'production_initial_state',
            'acceptance does not permit this downstream system/use')
    require(record['bank_id'] == campaign.e2_bank_id(system), 'wrong accepted chemistry bank')
    require(record['status'] in ('accepted', 'accepted_with_qualification') and
            record['reviewer'].strip() and record['reviewed_at'].strip() and
            isinstance(record['qualification'], str), 'acceptance is absent or incomplete')
    if record['status'] == 'accepted_with_qualification':
        require(record['qualification'].strip(), 'qualified acceptance requires a qualification')


def accept(root, output, attempt, reviewer, evidence, identifiers, qualification='', c1=False):
    output = e2.inside(root, output)
    require(output.parent == root / 'banks/e2_acceptance' and not output.exists(), 'new acceptance filename required')
    require(reviewer.strip() and evidence.is_file(), 'reviewer and scientific evidence are required')
    systems = [e2.system_by_id(identifier) for identifier in identifiers]
    require(systems and len(set(identifiers)) == len(identifiers) and
            len({campaign.e2_bank_id(system) for system in systems}) == 1, 'one bank per acceptance')
    bank = campaign.e2_bank_id(systems[0])
    entries = []
    if c1:
        require(bank == 'F04_N010_RP080_EE08' and qualification.strip(), 'C1 requires slow-topology qualification')
        for replica in (1, 2, 3):
            parent = e2.corrected_c1(root, replica)
            metadata, _ = e2.validation.analysis.restart.read_metadata(parent['prefix'] + '.assoc_restart')
            entries.append(dict(replica=replica, prefix=parent['prefix'], end_step=8000000,
                                chemistry_seed=int(metadata['seed']), physics=e2.validation.physics(systems[0]),
                                sha256=parent['sha256']))
        source = root / 'banks/e2_extensions/C1_periodic_recovery_v1/plan.json'
    else:
        require(attempt is not None, 'accepted segment required')
        plan = e2.verify(root, e2.inside(root, attempt))
        require(not plan['smoke'] and campaign.e2_bank_id(plan['system']) == bank,
                'smokes or wrong banks cannot be accepted')
        source = attempt / 'plan.json'
        for entry in plan['histories']:
            prefix = entry['output_prefix']
            entries.append(dict(replica=entry['replica'], prefix=prefix, end_step=entry['end_step'],
                                chemistry_seed=entry['chemistry_seed'], physics=entry['physics'],
                                sha256=e2.hash_files([Path(prefix + suffix) for suffix in e2.validation.OUTPUTS] +
                                                    [Path(prefix).parent / 'complete.json', source])))
    record = dict(schema_version=1, stage='E2_acceptance', bank_id=bank,
                  provenance_kind='corrected_C1_8M' if c1 else 'E2_G1_segment',
                  status='accepted_with_qualification' if qualification else 'accepted',
                  reviewer=reviewer, reviewed_at=e2.timestamp(), evidence=str(evidence.resolve()),
                  evidence_sha256=campaign.sha256(evidence), source_plan=str(source),
                  source_plan_sha256=campaign.sha256(source), histories=entries,
                  permitted_use='production_initial_state', permitted_systems=identifiers,
                  qualification=qualification, numerical_qualification=
                  'q cancels in fixed-configuration forward/reverse ratio; exact coupled integrator invariance unproven',
                  publisher_git_sha=campaign.git_sha())
    exclusive_validate(record, systems)
    e2.exclusive_json(output, record)
    return record


def exclusive_validate(record, systems):
    require({'schema_version', 'stage', 'bank_id', 'provenance_kind', 'status', 'reviewer',
             'reviewed_at', 'evidence', 'evidence_sha256', 'source_plan', 'source_plan_sha256',
             'histories', 'permitted_use', 'permitted_systems', 'qualification',
             'numerical_qualification', 'publisher_git_sha'} <= record.keys(), 'incomplete acceptance schema')
    require(record.get('schema_version') == 1 and record.get('stage') == 'E2_acceptance', 'bad acceptance schema')
    require([entry['replica'] for entry in record['histories']] == [1, 2, 3], 'acceptance requires three histories')
    require(len({entry['prefix'] for entry in record['histories']}) == 3 and
            len({entry['chemistry_seed'] for entry in record['histories']}) == 3,
            'duplicate accepted histories/chemistry seeds')
    e2.check_hashes({record['evidence']: record['evidence_sha256'],
                     record['source_plan']: record['source_plan_sha256']})
    for system in systems:
        permitted(record, system)
    source = campaign.load_json(record['source_plan'])
    require(record.get('provenance_kind') in ('corrected_C1_8M', 'E2_G1_segment'),
            'acceptance requires authenticated segment provenance')
    for entry in record['histories']:
        if record['provenance_kind'] == 'E2_G1_segment':
            require(source.get('stage') == 'E2-G1' and source.get('smoke') is False,
                    'accepted source is not an ordinary E2 segment')
            history = source['histories'][entry['replica'] - 1]
            require(history['output_prefix'] == entry['prefix'] and
                    history['end_step'] == entry['end_step'] and
                    history['physics'] == entry['physics'] and
                    history['chemistry_seed'] == entry['chemistry_seed'], 'accepted segment identity mismatch')
            complete_path = str(Path(entry['prefix']).parent / 'complete.json')
            require(complete_path in entry['sha256'], 'accepted completion hash absent')
            complete = campaign.load_json(complete_path)
            require(complete['status'] == 'validated' and complete['plan_sha256'] ==
                    record['source_plan_sha256'], 'accepted completion absent or wrong plan')
        else:
            inventory = campaign.load_json(e2.INVENTORY)
            suffix = inventory['C1_recovery'][entry['replica'] - 1]['prefix']
            require(entry['end_step'] == 8000000 and entry['prefix'].endswith('/' + suffix) and
                    record['bank_id'] == 'F04_N010_RP080_EE08' and record['qualification'].strip(),
                    'only qualified corrected C1 8M import is permitted')
            status_path = str(Path(entry['prefix']).parent / 'status.json')
            require(status_path in entry['sha256'] and
                    campaign.load_json(status_path)['status'] == 'validated', 'corrected C1 completion absent')
            for suffix in ('.restart.lammpsdat', '.assoc_restart'):
                path = entry['prefix'] + suffix
                relative = 'examples/KG_Assoc/kg_assoc_100m/' + inventory['C1_recovery'][entry['replica'] - 1]['prefix'] + suffix
                require(entry['sha256'][path] == inventory['preserved_files'][relative]['sha256'],
                        'C1 accepted endpoint differs from pinned correction')
        e2.check_hashes(entry['sha256'])
        require(all(path in entry['sha256'] for path in
                    (entry['prefix'] + '.assoc_restart', entry['prefix'] + '.restart.lammpsdat')),
                'accepted parent hashes absent')
        metadata, _ = e2.validation.analysis.restart.read_metadata(entry['prefix'] + '.assoc_restart')
        e2.validation.check_physics(metadata, entry['physics'])
        require(int(metadata['completed_steps']) == entry['end_step'] and
                int(metadata['seed']) == entry['chemistry_seed'], 'accepted step/seed changed')
        e2.validation.e1.check_snapshot(Path(entry['prefix'] + '.restart.lammpsdat'), systems[0])
        campaign.validate_assoc_initial_state(Path(entry['prefix'] + '.assoc_restart'), systems[0])
        require(entry['end_step'] > 0, 'accepted segment must have completed dynamics')
        if record['bank_id'] == 'F04_N010_RP080_EE08':
            require(entry['end_step'] >= 8000000 and '/banks/e2/F04_N010_RP080_EE08/' not in entry['prefix'],
                    'defective historical C1 bank is never an active production start')


def publish(root, output, acceptances):
    output = e2.inside(root, output)
    require(output.parent == root / 'banks/e2_registry' and not output.exists(), 'new registry filename required')
    selected = {}
    for path in acceptances:
        path = e2.inside(root, path)
        record = campaign.load_json(path)
        systems = [e2.system_by_id(identifier) for identifier in record['permitted_systems']]
        exclusive_validate(record, systems)
        for system in systems:
            identifier = system['system_id']
            require(identifier not in selected, 'duplicate active system selection')
            selected[identifier] = dict(acceptance=str(path), sha256=campaign.sha256(path))
    require(selected, 'empty active registry')
    e2.exclusive_json(output, dict(schema_version=1, stage='E2_active_registry',
                                  systems=selected, published_at=e2.timestamp(), git_sha=campaign.git_sha()))


def resolve(root, registry, system, replica):
    require(registry is not None, 'associating production requires explicit --e2-registry')
    registry = e2.inside(root, registry)
    active = campaign.load_json(registry)
    require(active.get('schema_version') == 1 and active.get('stage') == 'E2_active_registry', 'bad active E2 registry')
    reference = active.get('systems', {}).get(system['system_id'])
    require(reference is not None, 'active E2 acceptance absent for system')
    path = e2.inside(root, reference['acceptance'])
    require(campaign.sha256(path) == reference['sha256'], 'active acceptance changed')
    record = campaign.load_json(path)
    exclusive_validate(record, [system])
    entry = record['histories'][replica - 1]
    snapshot = Path(entry['prefix'] + '.restart.lammpsdat')
    chemistry = Path(entry['prefix'] + '.assoc_restart')
    e2.inside(root, snapshot)
    e2.inside(root, chemistry)
    parent_entry = dict(system=system, parent=dict(kind='e2', prefix=entry['prefix'], snapshot=str(snapshot)),
                        start_step=entry['end_step'], chemistry_seed=entry['chemistry_seed'],
                        physics=entry['physics'], parent_Ea=entry['physics']['Ea'])
    e2.validation.read_parent(parent_entry)
    return dict(prefix=entry['prefix'], parent_Ea=entry['physics']['Ea'],
                registry=str(registry), registry_sha256=campaign.sha256(registry),
                acceptance=str(path), acceptance_sha256=campaign.sha256(path),
                snapshot_sha256=campaign.sha256(snapshot), chemistry_sha256=campaign.sha256(chemistry),
                accepted_step=entry['end_step'], qualification=record['qualification'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('accept', 'publish'))
    parser.add_argument('--dataset-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--attempt', type=Path)
    parser.add_argument('--c1', action='store_true')
    parser.add_argument('--reviewer')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--permitted-systems')
    parser.add_argument('--qualification', default='')
    parser.add_argument('--acceptance', nargs='+', type=Path)
    args = parser.parse_args()
    root = args.dataset_root.resolve()
    if args.action == 'accept':
        require(args.reviewer and args.evidence and args.permitted_systems, 'reviewer, evidence and permitted systems required')
        accept(root, args.output, args.attempt.resolve() if args.attempt else None,
               args.reviewer, args.evidence.resolve(), args.permitted_systems.split(','), args.qualification, args.c1)
    else:
        require(args.acceptance, 'acceptance records required')
        publish(root, args.output, args.acceptance)


if __name__ == '__main__':
    main()
