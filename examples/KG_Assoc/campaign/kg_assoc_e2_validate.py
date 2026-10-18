#!/usr/bin/env python3
"""General E2 segment validation; uses the validated C1 event/network replay."""

import math
from pathlib import Path
import re
import sys

import kg_assoc_campaign as campaign
import kg_assoc_e1 as e1

sys.path.insert(0, str(campaign.ANALYSIS_DIR))
import analyze_c1_e2_pilot as analysis
import analyze_campaign_structure as structure

require = analysis.require
OUTPUTS = analysis.OUTPUTS + ('.conformation.tsv',)


def effective_md_seed(seed):
    """Third next32 of UAMMD Xorshift128plus; checked against the C++ host query."""
    require(type(seed) is int and 0 < seed < 2**64, 'invalid MD seed')
    mask = 2**64 - 1
    first = seed
    second = ((seed + 15438657923749336752) & mask) % mask
    for _ in range(3):
        value = first
        first = second
        value ^= (value << 23) & mask
        value ^= value >> 17
        value ^= second ^ (second >> 26)
        second = value & mask
        result = ((second + first) & mask) % (2**32 - 1)
    return result


def physics(system, ea=4):
    return dict(arms=system['f'], narm=system['N'], dt=.01, temperature=1,
                Ea=ea, Ee=system['Ee'], nu0=20, Nevery=100, r_assoc=1.25,
                damping=2, K=30, R0=1.5)


def check_physics(metadata, expected, state=False):
    for key, value in expected.items():
        name = 'T' if state and key == 'temperature' else key
        require(float(metadata.get(name, 'nan')) == value, 'physics mismatch: ' + key)


def read_parent(entry):
    parent = entry['parent']
    path = Path(parent['snapshot'])
    e1.check_snapshot(path, entry['system'])
    system = analysis.topology.read_system(str(path), 2)
    if parent['kind'] == 'e1':
        require(entry['start_step'] == 0, 'E1 start must be step zero')
        return system, dict(pairs=[], creations=0, breaks=0)
    metadata, pairs = analysis.restart.read_metadata(parent['prefix'] + '.assoc_restart')
    expected = dict(entry['physics'], Ea=entry['parent_Ea'])
    check_physics(metadata, expected)
    parent_seed = entry['chemistry_seed']
    if 'lineage' in entry:
        import kg_assoc_e2_transfer as transfer
        if entry['lineage']['mode'] == 'Ea_24M_extension_v1':
            import kg_assoc_e2_extension as extension
            extension.validate_lineage(entry, metadata, pairs)
        else:
            transfer.validate_lineage(entry, metadata, pairs)
        parent_seed = entry['lineage']['parent_chemistry_seed']
    require(int(metadata['completed_steps']) == entry['start_step'] and
            int(metadata['seed']) == parent_seed, 'parent step/chemistry seed mismatch')
    initial = dict(pairs=pairs, creations=int(metadata['creations']), breaks=int(metadata['breaks']))
    require(initial['creations'] >= initial['breaks'] >= 0 and
            initial['creations'] - initial['breaks'] == len(pairs), 'parent counters invalid')
    # Uses the same strict stable-ID, reciprocal valence-one reader as event analysis.
    analysis.dynamics.read_restart(parent['prefix'] + '.assoc_restart', system,
                                  dict(start_step=entry['start_step'],
                                       seed=parent_seed, dt=entry['physics']['dt']))
    data = campaign.parse_lammps_data(path)
    require(all(analysis.restart.distance(data['positions'][a], data['positions'][b],
                                         data['bounds']) < entry['physics']['R0']
                for a, b in pairs), 'invalid parent temporary FENE')
    return system, initial


def snapshot_conformation(path, arms):
    """Independent offline BFS reconstruction of the two endpoint observables."""
    data = campaign.parse_lammps_data(path)
    coordinates = [value for atom in sorted(data['atoms']) for value in data['positions'][atom]]
    adjacency = [set() for _ in coordinates[::3]]
    for first, second in data['bonds']:
        adjacency[first - 1].add(second - 1)
        adjacency[second - 1].add(first - 1)
    molecules = {}
    for atom, (molecule, kind) in data['atoms'].items():
        if kind in (1, 2):
            molecules.setdefault(molecule, []).append(atom - 1)
    lengths = [data['bounds'][axis][1] - data['bounds'][axis][0] for axis in 'xyz']
    rg2 = terminal_r2 = 0.0
    terminal_count = 0
    for indices in molecules.values():
        centers = [index for index in indices if len(adjacency[index]) == arms and
                   data['atoms'][index + 1][1] == 1]
        require(len(centers) == 1, 'invalid conformation center')
        points = structure.unwrap_star(coordinates, indices, adjacency, lengths)
        unwrapped = dict(zip(indices, points))
        center = [sum(point[axis] for point in points) / len(points) for axis in range(3)]
        rg2 += sum(sum((point[axis] - center[axis])**2 for axis in range(3))
                   for point in points) / len(points)
        for index in indices:
            if data['atoms'][index + 1][1] == 2:
                terminal_r2 += sum((unwrapped[index][axis] - unwrapped[centers[0]][axis])**2
                                   for axis in range(3))
                terminal_count += 1
    return rg2 / len(molecules), terminal_r2 / terminal_count


def diagnostic_steps(start, end, cadence=1000):
    steps = [start] + list(range((start // cadence + 1) * cadence, end + 1, cadence))
    if steps[-1] != end:
        steps.append(end)
    return steps


def validate(entry, oracle=False):
    # Ordinary 16M Ea transfers retain every smoke diagnostic; callers cannot disable them.
    oracle = oracle or (bool(entry.get('lineage')) and
                        entry['end_step'] - entry['start_step'] == 16000000)
    if entry.get('lineage', {}).get('mode') == 'Ea_24M_extension_v1':
        # A caller cannot disable either readback or the oracle for an extension.
        oracle = True
    prefix = Path(entry['output_prefix'])
    for suffix in OUTPUTS:
        require(Path(str(prefix) + suffix).is_file(), 'missing E2 output: ' + suffix)
    system, initial = read_parent(entry)
    start, end = entry['start_step'], entry['end_step']
    expected = entry['physics']
    dt, every = expected['dt'], expected['Nevery']
    metadata, rows = analysis.stationarity.read_state(str(prefix) + '.state')
    check_physics(metadata, expected, state=True)
    if 'lineage' in entry:
        lineage = entry['lineage']
        expected_lineage = dict(lineage_mode=lineage['mode'], branch_id=lineage['branch_id'],
            parent_chemistry_seed=lineage['parent_chemistry_seed'],
            reference_control=int(lineage['reference_control']),
            branch_origin_step=lineage['branch_origin_step'],
            parent_creations=lineage['parent_creations'], parent_breaks=lineage['parent_breaks'],
            branch_age_start=0, bitwise_md_continuation=0)
        for key, value in expected_lineage.items():
            require(str(metadata.get(key)) == str(value), 'derived metadata mismatch: ' + key)
    geometry = campaign.expected_geometry(entry['system'])
    for key, value in dict(seed=entry['chemistry_seed'], md_seed=entry['md_seed'],
                           start_step=start, total_requested_steps=end, diagnostic_every=1000,
                           total_particles=geometry['total_beads'],
                           stickers=entry['system']['f'] * entry['system']['number_of_stars'],
                           permanent_bonds=entry['system']['f'] * entry['system']['N'] *
                           entry['system']['number_of_stars'],
                           ea_switch=int(entry['parent_Ea'] != expected['Ea']),
                           parent_Ea=entry['parent_Ea']).items():
        require(float(metadata.get(key, 'nan')) == value, 'segment metadata mismatch: ' + key)
    require(Path(metadata['input_file']).resolve() == Path(entry['parent']['snapshot']).resolve(),
            'wrong parent snapshot')
    require([row['step'] for row in rows] == diagnostic_steps(start, end) and
            all(math.isclose(row['time'], row['step'] * dt, abs_tol=1e-9) for row in rows),
            'incomplete or mistimed diagnostics')
    sweeps = end // every - start // every
    require(int(metadata['chemistry_sweeps']) == sweeps, 'incorrect sweep count')
    final = Path(str(prefix) + '.restart.lammpsdat')
    final_check = e1.check_snapshot(final, entry['system'])
    parent_data = campaign.parse_lammps_data(entry['parent']['snapshot'])
    data = campaign.parse_lammps_data(final)
    require(data['atoms'] == parent_data['atoms'] and data['bonds'] == parent_data['bonds'] and
            data['bounds'] == parent_data['bounds'], 'permanent identity/geometry changed')
    require(re.search(r'\bstep ' + str(end) + r'$', final.read_text().splitlines()[0]),
            'final snapshot timestamp mismatch')
    event_metadata, events = analysis.dynamics.read_events(str(prefix) + '.events', system)
    for key in ('input_file', 'seed', 'md_seed', 'start_step', 'total_requested_steps',
                'ea_switch', 'parent_Ea'):
        require(str(event_metadata[key]) == str(metadata[key]) or
                (key != 'input_file' and float(event_metadata[key]) == float(metadata[key])),
                'event provenance mismatch: ' + key)
    check_physics(event_metadata, expected, state=True)
    for key in ('validation_diagnostics_version', 'initial_device_readback_required'):
        if key in metadata:
            require(event_metadata.get(key) == metadata[key], 'device evidence metadata differs')
    if 'lineage' in entry:
        require(all(event_metadata.get(key) == metadata.get(key) for key in expected_lineage),
                'derived event/state lineage differs')
    require(all(start < step <= end and step % every == 0 for step, _, _ in events),
            'event outside absolute chemistry cadence')
    active, event_rows = analysis.replay(rows, events, system, network=True, initial=initial)
    sidecar, pairs = analysis.restart.read_metadata(str(prefix) + '.assoc_restart')
    check_physics(sidecar, expected)
    require(set(pairs) == active and len(pairs) == len(active) and
            int(sidecar['completed_steps']) == end and
            int(sidecar['seed']) == entry['chemistry_seed'] and
            int(sidecar['creations']) == rows[-1]['creations'] and
            int(sidecar['breaks']) == rows[-1]['breaks'], 'final chemistry/counters mismatch')
    require(all(analysis.restart.distance(data['positions'][a], data['positions'][b], data['bounds'])
                < expected['R0'] for a, b in active), 'invalid final temporary FENE')
    mirrors = []
    for line in Path(str(prefix) + '.final_associations').read_text().splitlines():
        if line and not line.startswith('#'):
            fields = list(map(int, line.split()))
            require(len(fields) == 4 and fields[2:] ==
                    [system['atom_to_star'][fields[0]], system['atom_to_star'][fields[1]]],
                    'invalid association mirror')
            mirrors.append(tuple(fields[:2]))
    require(set(mirrors) == active and len(mirrors) == len(active), 'association mirror mismatch')
    require(Path(str(prefix) + '.final_permanent.lammpsdat').read_bytes().split(b'\n', 1)[1] ==
            final.read_bytes().split(b'\n', 1)[1], 'particle mirrors disagree')
    numeric = analysis.numerics(Path(str(prefix) + '.numerics.tsv'), rows, geometry['total_beads'])
    parent_temperature = e1.check_snapshot(Path(entry['parent']['snapshot']), entry['system'])['final_temperature']
    require(math.isclose(numeric[0][3], parent_temperature, rel_tol=1e-5) and
            math.isclose(numeric[-1][3], final_check['final_temperature'], rel_tol=1e-5),
            'loaded/final velocity mismatch')
    path = Path(str(prefix) + '.conformation.tsv')
    lines = path.read_text().splitlines()
    require(lines[0] == '# step time mean_rg2 mean_center_terminal_r2', 'conformation header mismatch')
    conformations = [list(map(float, line.split())) for line in lines[1:]]
    require(len(conformations) == len(rows), 'conformation cadence mismatch')
    previous = None
    observed_bonds = 0
    integer_fields = ('free', 'bonds', 'creations', 'breaks', 'intra', 'inter', 'components',
                      'largest_size', 'L1', 'L2', 'active_observations')
    for row, values, sample in zip(rows, numeric, conformations):
        require(all(row[key] >= 0 and row[key].is_integer() for key in integer_fields),
                'invalid diagnostic counts')
        if previous is not None:
            observed_bonds += row['bonds']
            require(all(row[key] >= previous[key] for key in
                        ('creations', 'breaks', 'active_observations', 'max_active_bond_distance')),
                    'nonmonotonic cumulative diagnostics')
        require(row['active_observations'] == observed_bonds and
                all(0 <= row[key] <= 1 for key in ('fraction_active_gt_1p25',
                    'fraction_active_gt_1p30', 'fraction_active_gt_1p40')), 'active distance accounting mismatch')
        previous = row
        require(len(sample) == 4 and all(math.isfinite(value) for value in sample) and
                sample[:2] == [row['step'], row['time']] and min(sample[2:]) > 0,
                'invalid conformation sample')
        require(0 <= row['max_active_bond_distance'] < expected['R0'], 'invalid active distance')
        row.update(temperature=values[3], min_permanent_bond=values[4], max_permanent_bond=values[5],
                   mean_rg2=sample[2], mean_center_terminal_r2=sample[3])
    for path, sample in ((entry['parent']['snapshot'], conformations[0]), (final, conformations[-1])):
        actual = snapshot_conformation(path, entry['system']['f'])
        require(all(math.isclose(a, b, rel_tol=2e-4, abs_tol=1e-6)
                    for a, b in zip(actual, sample[2:])), 'endpoint conformation mismatch')
    log = (prefix.parent / 'stderr.log').read_text()
    seed_line = (f"[E2 MD stream] requested_seed={entry['md_seed']} "
                 f"effective_seed={entry['effective_md_seed']} internal_start_step=0")
    require(seed_line in log, 'effective MD stream mismatch')
    for field, value in (('Temperature', '1.000000'), ('Time step', '0.010000'), ('Friction', '0.500000')):
        require(f'[VerletNVT::GronbechJensen] {field}: {value}' in log, 'runtime NVT mismatch')
    device_readback = None
    if oracle and 'lineage' in entry:
        build = campaign.load_json(Path(entry['command'][0]).parent / 'manifest.json')
        modern = any(Path(name).name == 'kg_assoc_validation_evidence.cuh'
                     for name in build.get('source_sha256', {}))
        if modern or 'validation_diagnostics_version' in metadata:
            require(metadata.get('validation_diagnostics_version') == '1' and
                    metadata.get('initial_device_readback_required') == '1',
                    'initial device evidence declaration absent')
            import kg_assoc_e2_readback
            device_readback = kg_assoc_e2_readback.check(
                str(prefix) + '.initial_device_validation.tsv', entry,
                campaign.parse_lammps_data(entry['parent']['snapshot']), initial['pairs'])
    if oracle:
        lines = Path(str(prefix) + '.candidate_validation.tsv').read_text().splitlines()
        require(lines[0] == '# step candidates oracle_verified_active_candidates', 'oracle header mismatch')
        checks = [list(map(int, line.split())) for line in lines[1:]]
        require([line[0] for line in checks] == list(range((start // every + 1) * every, end + 1, every)) and
                all(len(line) == 3 and 0 <= line[2] <= line[1] for line in checks) and
                sum(line[1] for line in checks) == int(metadata['candidate_sticker_pairs']),
                'incomplete oracle sweeps')
    return rows, event_rows, dict(numerical_status='valid', scientific_status='review_required',
                                 **({'initial_device_readback': device_readback} if device_readback else {}),
                                 samples=len(rows), accepted_events=len(events), final_bonds=len(active),
                                 oracle_sweeps=sweeps if oracle else 0,
                                 output_sha256={suffix: campaign.sha256(Path(str(prefix) + suffix))
                                                for suffix in OUTPUTS +
                                                (('.candidate_validation.tsv',) if oracle else ())})
