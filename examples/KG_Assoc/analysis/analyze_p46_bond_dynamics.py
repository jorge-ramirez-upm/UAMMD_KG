#!/usr/bin/env python3
"""Censoring-aware temporary-bond lifetime and partner-exchange analysis."""

import argparse
import collections
import csv
import json
import math
import statistics

from analyze_p45_topology import read_system, topology_frames


EVENT_HEADER = 'timestep event_type sticker_i sticker_j molecule_i molecule_j'
CAMPAIGN_EVENT_HEADER = 'step time event_type sticker_i sticker_j molecule_i molecule_j'


def fail(path, message):
    raise ValueError('{}: {}'.format(path, message))


def metadata_line(line, metadata):
    for token in line[1:].split():
        if '=' in token:
            key, value = token.split('=', 1)
            if key in metadata and metadata[key] != value:
                raise ValueError('conflicting metadata {}'.format(key))
            metadata[key] = value


def read_events(path, system):
    metadata = {}
    events = []
    with open(path, encoding='utf-8') as input_file:
        for raw_line in input_file:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if line[1:].strip() not in (EVENT_HEADER, CAMPAIGN_EVENT_HEADER):
                    metadata_line(line, metadata)
                continue
            fields = line.split()
            campaign = len(fields) == 7 and fields[2] in ('C', 'B')
            legacy = len(fields) == 6 and fields[1] in ('C', 'B')
            if not campaign and not legacy:
                fail(path, 'malformed event record')
            if campaign:
                step = int(fields[0])
                event_time = float(fields[1])
                event_type = fields[2]
                first, second, first_star, second_star = map(int, fields[3:])
            else:
                step = int(fields[0])
                event_time = None
                event_type = fields[1]
                first, second, first_star, second_star = map(int, fields[2:])
            if first <= 0 or first >= second or first not in system['stickers'] or second not in system['stickers']:
                fail(path, 'invalid ordered sticker pair')
            if (system['atom_to_star'][first], system['atom_to_star'][second]) != (first_star, second_star):
                fail(path, 'event molecule IDs disagree with system file')
            if event_time is not None and not math.isclose(
                    event_time, step * float(metadata.get('dt', 'nan')),
                    rel_tol=1e-12, abs_tol=1e-12):
                fail(path, 'event time disagrees with absolute step and dt')
            events.append((step, event_type, (first, second)))
    required = ('input_file', 'dt', 'seed', 'start_step', 'total_requested_steps',
                'original_lammps_atom_ids')
    if any(key not in metadata for key in required) or metadata['original_lammps_atom_ids'] != '1_based':
        fail(path, 'missing required event provenance')
    metadata['dt'] = float(metadata['dt'])
    metadata['seed'] = int(metadata['seed'])
    if 'initial_state_seed' in metadata:
        metadata['initial_state_seed'] = int(metadata['initial_state_seed'])
    metadata['start_step'] = int(metadata['start_step'])
    metadata['total_requested_steps'] = int(metadata['total_requested_steps'])
    if metadata['dt'] <= 0.0 or metadata['start_step'] < 0 or metadata['total_requested_steps'] < metadata['start_step']:
        fail(path, 'invalid event time provenance')
    if any(step < metadata['start_step'] or step > metadata['total_requested_steps']
           for step, _, _ in events) or any(events[i][0] > events[i + 1][0] for i in range(len(events) - 1)):
        fail(path, 'out-of-range or unordered events')
    return metadata, events


def read_restart(path, system, metadata):
    fields = []
    with open(path, encoding='utf-8') as input_file:
        fields = [line.split() for line in input_file if line.split()]
    if not fields or fields[0] != ['KG_ASSOC_RESTART', '1']:
        fail(path, 'unsupported restart format')
    values = {row[0]: row[1] for row in fields[1:] if len(row) == 2}
    if int(values.get('completed_steps', '-1')) != metadata['start_step']:
        fail(path, 'restart step disagrees with event stream')
    expected_seed = metadata.get('initial_state_seed', metadata['seed'])
    if float(values.get('dt', 'nan')) != metadata['dt'] or int(values.get('seed', '-1')) != expected_seed:
        fail(path, 'restart metadata disagrees with event stream')
    count = int(values.get('active_bonds', '-1'))
    start = next((index for index, row in enumerate(fields) if row[0] == 'active_bonds'), -1)
    bonds = set()
    for row in fields[start + 1:start + 1 + count]:
        if len(row) != 2:
            fail(path, 'malformed active bond')
        pair = tuple(map(int, row))
        if pair[0] >= pair[1] or pair[0] not in system['stickers'] or pair[1] not in system['stickers'] or pair in bonds:
            fail(path, 'invalid active bond')
        bonds.add(pair)
    if len(bonds) != count:
        fail(path, 'truncated active bonds')
    return bonds


def bond_kind(pair, system):
    return 'intra' if system['atom_to_star'][pair[0]] == system['atom_to_star'][pair[1]] else 'inter'


def kaplan_meier(episodes):
    known = [row for row in episodes if not row['left_censored']]
    if not known:
        return [], None, None
    by_time = collections.defaultdict(list)
    for row in known:
        by_time[row['lifetime']].append(row)
    risk = len(known)
    survival = 1.0
    rows = [{'lifetime': 0.0, 'survival': 1.0, 'at_risk': risk,
             'observed_breaks': 0, 'right_censored': 0}]
    median = one_over_e = None
    for time in sorted(by_time):
        group = by_time[time]
        breaks = sum(not row['right_censored'] for row in group)
        censored = sum(row['right_censored'] for row in group)
        if breaks:
            survival *= 1.0 - breaks / risk
        rows.append({'lifetime': time, 'survival': survival, 'at_risk': risk,
                     'observed_breaks': breaks, 'right_censored': censored})
        if median is None and survival <= .5:
            median = time
        if one_over_e is None and survival <= 1.0 / math.e:
            one_over_e = time
        risk -= breaks + censored
    return rows, median, one_over_e


def replica_statistics(values):
    count = len(values)
    if count == 0:
        return {'mean': None, 'sample_std': None, 'sem': None,
                'ci95_half_width': None, 'replicas': 0}
    mean = statistics.mean(values)
    sample_std = statistics.stdev(values) if count > 1 else 0.0
    sem = sample_std / math.sqrt(count)
    critical = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776}.get(count, 1.96)
    return {'mean': mean, 'sample_std': sample_std, 'sem': sem,
            'ci95_half_width': critical * sem, 'replicas': count}


def validate_topology(path, initial, events, system):
    active = set(initial)
    event_index = 0
    checked = 0
    for _, step, _, pairs in topology_frames(path, system):
        while event_index < len(events) and events[event_index][0] <= step:
            _, event_type, pair = events[event_index]
            if event_type == 'C':
                active.add(pair)
            else:
                active.remove(pair)
            event_index += 1
        if active != {(first, second) for first, second, _, _ in pairs}:
            fail(path, 'event reconstruction disagrees with topology frame')
        checked += 1
    if not checked:
        fail(path, 'no topology frames')
    return checked


def analyze_run(path, system, topology_path=None):
    metadata, events = read_events(path, system)
    restart = metadata['input_file'].replace('.restart.lammpsdat', '.assoc_restart')
    initial = read_restart(restart, system, metadata)
    if topology_path:
        validate_topology(topology_path, initial, events, system)
    active = {pair: {'start_step': metadata['start_step'], 'left_censored': True}
              for pair in initial}
    partners = {atom: other for pair in initial for atom, other in (pair, pair[::-1])}
    multiplicity = collections.Counter()
    for pair in initial:
        if bond_kind(pair, system) == 'inter':
            multiplicity[tuple(sorted((system['atom_to_star'][pair[0]], system['atom_to_star'][pair[1]])))] += 1
    episodes = []
    pending = {}
    rebinding = collections.Counter()
    waits = collections.defaultdict(list)
    exchange = collections.Counter()
    changes_by_step = collections.defaultdict(lambda: [set(), set()])
    for step, event_type, pair in events:
        first, second = pair
        kind = bond_kind(pair, system)
        stars = tuple(sorted((system['atom_to_star'][first], system['atom_to_star'][second])))
        if event_type == 'C':
            if pair in active or first in partners or second in partners:
                fail(path, 'duplicate creation or valence-one violation')
            for atom, other in ((first, second), (second, first)):
                if atom in pending:
                    previous, previous_star, break_step = pending.pop(atom)
                    category = ('same_sticker' if other == previous else
                                'same_star_different_sticker' if system['atom_to_star'][other] == previous_star else
                                'different_star')
                    rebinding[category] += 1
                    waits[category].append((step - break_step) * metadata['dt'])
            active[pair] = {'start_step': step, 'left_censored': False}
            partners[first], partners[second] = second, first
            if kind == 'inter':
                if multiplicity[stars] == 0:
                    exchange['neighbor_gain_events'] += 1
                    changes_by_step[step][0].update(stars)
                else:
                    exchange['k_bond_only_events'] += 1
                multiplicity[stars] += 1
            else:
                exchange['neither_events'] += 1
        else:
            if pair not in active or partners.get(first) != second or partners.get(second) != first:
                fail(path, 'break without active bond')
            episode = active.pop(pair)
            episodes.append({'sticker_i': first, 'sticker_j': second,
                             'star_i': system['atom_to_star'][first], 'star_j': system['atom_to_star'][second],
                             'classification': kind, 'creation_step': episode['start_step'],
                             'break_step': step, 'creation_time': episode['start_step'] * metadata['dt'],
                             'break_time': step * metadata['dt'],
                             'lifetime': (step - episode['start_step']) * metadata['dt'],
                             'left_censored': episode['left_censored'], 'right_censored': False})
            del partners[first], partners[second]
            pending[first] = (second, system['atom_to_star'][second], step)
            pending[second] = (first, system['atom_to_star'][first], step)
            if kind == 'inter':
                multiplicity[stars] -= 1
                if multiplicity[stars] == 0:
                    exchange['neighbor_loss_events'] += 1
                    changes_by_step[step][1].update(stars)
                else:
                    exchange['k_bond_only_events'] += 1
            else:
                exchange['neither_events'] += 1
    end_step = metadata['total_requested_steps']
    for pair, episode in active.items():
        first, second = pair
        episodes.append({'sticker_i': first, 'sticker_j': second,
                         'star_i': system['atom_to_star'][first], 'star_j': system['atom_to_star'][second],
                         'classification': bond_kind(pair, system), 'creation_step': episode['start_step'],
                         'break_step': '', 'creation_time': episode['start_step'] * metadata['dt'],
                         'break_time': '', 'lifetime': (end_step - episode['start_step']) * metadata['dt'],
                         'left_censored': episode['left_censored'], 'right_censored': True})
    rebinding['unbound_until_end'] += len(pending)
    exchange['same_step_neighbor_replacements'] = sum(len(gains & losses)
                                                       for gains, losses in changes_by_step.values())
    exchange['events'] = len(events)
    exchange['duration'] = (end_step - metadata['start_step']) * metadata['dt']
    return metadata, episodes, rebinding, waits, exchange


def self_test():
    system = {'stickers': {1, 2, 3, 4, 5, 6}, 'atom_to_star': {1: 1, 2: 2, 3: 2, 4: 3, 5: 1, 6: 1}}
    episodes = [{'lifetime': 2.0, 'left_censored': False, 'right_censored': False},
                {'lifetime': 3.0, 'left_censored': False, 'right_censored': True}]
    rows, median, _ = kaplan_meier(episodes)
    assert rows[-1]['at_risk'] == 1 and median == 2.0
    assert bond_kind((5, 6), system) == 'intra' and bond_kind((1, 2), system) == 'inter'
    assert replica_statistics([1.0, 2.0, 3.0])['mean'] == 2.0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system')
    parser.add_argument('--output-prefix')
    parser.add_argument('--topology', action='append')
    parser.add_argument('--sticker-type', type=int, default=2)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('event_files', nargs='*')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        print('P4.6 BOND_DYNAMICS SELF_TEST PASS')
        return
    if not arguments.system or not arguments.output_prefix or not arguments.event_files:
        parser.error('--system, --output-prefix, and event files are required')
    if arguments.topology and len(arguments.topology) != len(arguments.event_files):
        parser.error('--topology requires one matching file per event file')
    system = read_system(arguments.system, arguments.sticker_type)
    all_episodes, summaries = [], []
    survival = {kind: [] for kind in ('all', 'intra', 'inter')}
    rebinding_rows, exchange_rows = [], []
    for replica, path in enumerate(arguments.event_files, 1):
        topology = arguments.topology[replica - 1] if arguments.topology else None
        metadata, episodes, rebinding, waits, exchange = analyze_run(path, system, topology)
        for row in episodes:
            row['replica'] = replica
        all_episodes.extend(episodes)
        for kind in survival:
            selected = episodes if kind == 'all' else [row for row in episodes if row['classification'] == kind]
            curve, median, one_over_e = kaplan_meier(selected)
            for row in curve:
                row.update({'replica': replica, 'classification': kind})
                survival[kind].append(row)
            summaries.append({'replica': replica, 'classification': kind, 'episodes': len(selected),
                              'complete': sum(not row['right_censored'] for row in selected),
                              'left_censored': sum(row['left_censored'] for row in selected),
                              'right_censored': sum(row['right_censored'] for row in selected),
                              'median_lifetime': median, 'one_over_e_lifetime': one_over_e})
        total = sum(rebinding.values())
        for category in ('same_sticker', 'same_star_different_sticker', 'different_star', 'unbound_until_end'):
            values = waits[category]
            rebinding_rows.append({'replica': replica, 'category': category, 'count': rebinding[category],
                                   'fraction': rebinding[category] / total if total else 0.0,
                                   'mean_wait': statistics.mean(values) if values else '',
                                   'median_wait': statistics.median(values) if values else ''})
        exchange_rows.append({'replica': replica, **exchange,
                              'neighbor_change_events': exchange['neighbor_gain_events'] + exchange['neighbor_loss_events']})
    def write_csv(path, rows):
        with open(path, 'w', newline='', encoding='utf-8') as output:
            writer = csv.DictWriter(output, fieldnames=rows[0])
            writer.writeheader(); writer.writerows(rows)
    prefix = arguments.output_prefix
    write_csv(prefix + '.episodes.csv', all_episodes)
    for kind, rows in survival.items(): write_csv(prefix + '.survival_{}.csv'.format(kind), rows)
    write_csv(prefix + '.rebinding.csv', rebinding_rows)
    write_csv(prefix + '.partner_exchange.csv', exchange_rows)
    ensemble = {}
    for kind in ('all', 'intra', 'inter'):
        rows = [row for row in summaries if row['classification'] == kind]
        for metric in ('episodes', 'median_lifetime', 'one_over_e_lifetime'):
            values = [row[metric] for row in rows if row[metric] is not None]
            ensemble['{}_{}'.format(kind, metric)] = replica_statistics(values)
    for category in ('same_sticker', 'same_star_different_sticker', 'different_star',
                     'unbound_until_end'):
        values = [row['fraction'] for row in rebinding_rows if row['category'] == category]
        ensemble['rebinding_{}'.format(category)] = replica_statistics(values)
    for metric in ('neighbor_gain_events', 'neighbor_loss_events', 'k_bond_only_events',
                   'neither_events', 'same_step_neighbor_replacements'):
        values = [row[metric] / row['duration'] for row in exchange_rows]
        ensemble['{}_rate'.format(metric)] = replica_statistics(values)
    with open(prefix + '.summary.json', 'w', encoding='utf-8') as output:
        json.dump({'replicas': len(arguments.event_files), 'episode_summary': summaries,
                   'ensemble_replica_statistics': ensemble,
                   'censoring': 'left-censored opening bonds are excluded from Kaplan-Meier risk sets; right-censored known-origin bonds are retained',
                   'bond_identity': 'unordered sticker pair (min atom ID, max atom ID)',
                   'star_exchange': 'neighbor gains/losses are multiplicity 0<->1 transitions; replacements are same-step gain/loss intersections'}, output, indent=2)
        output.write('\n')
    print('P4.6 bond dynamics written: {}'.format(prefix))


if __name__ == '__main__':
    main()
