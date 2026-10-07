#!/usr/bin/env python3
"""Topology-first walking/hopping episodes on segment-local COM trajectories."""
import argparse
import bisect
import collections
import csv
import json
import math
import statistics

from analyze_p45_topology import read_system, topology_frames
from analyze_p46_bond_dynamics import bond_kind, read_events, read_restart


def read_com(path):
    frames = collections.defaultdict(dict)
    with open(path, encoding='utf-8') as source:
        if source.readline().strip() != '# step time molecule_id com_x com_y com_z':
            raise ValueError('{}: unexpected COM header'.format(path))
        for line in source:
            step, time, star, x, y, z = line.split()
            frames[int(step)][int(star)] = (float(time), float(x), float(y), float(z))
    steps = sorted(frames)
    if not steps or any(set(frames[s]) != set(frames[steps[0]]) for s in steps):
        raise ValueError('{}: incomplete COM frames'.format(path))
    return steps, frames


def displacement(steps, frames, star, event_step, window, dt):
    offset = round(window / dt)
    left = bisect.bisect_right(steps, event_step - offset) - 1
    right = bisect.bisect_left(steps, event_step + offset)
    if left < 0 or right == len(steps):
        return None
    before, after = steps[left], steps[right]
    first, second = frames[before][star], frames[after][star]
    squared = sum((a - b) ** 2 for a, b in zip(first[1:], second[1:]))
    return before, after, first[0], second[0], math.sqrt(squared), squared


def initialize(initial, system):
    neighbors = {star: set() for star in system['stars']}
    multiplicity = collections.Counter()
    for pair in initial:
        if bond_kind(pair, system) == 'inter':
            first, second = (system['atom_to_star'][atom] for atom in pair)
            edge = tuple(sorted((first, second)))
            multiplicity[edge] += 1
            neighbors[first].add(second)
            neighbors[second].add(first)
    return neighbors, multiplicity


def apply_event(action, pair, neighbors, multiplicity, system):
    first, second = (system['atom_to_star'][atom] for atom in pair)
    edge = tuple(sorted((first, second)))
    if action == 'B':
        multiplicity[edge] -= 1
        if multiplicity[edge] == 0:
            neighbors[first].remove(second)
            neighbors[second].remove(first)
    else:
        if multiplicity[edge] == 0:
            neighbors[first].add(second)
            neighbors[second].add(first)
        multiplicity[edge] += 1


def validate_topology(path, initial, events, system):
    neighbors, multiplicity = initialize(initial, system)
    index = 0
    checked = 0
    for _, step, _, pairs in topology_frames(path, system):
        while index < len(events) and events[index][0] <= step:
            _, action, pair = events[index]
            if bond_kind(pair, system) == 'inter':
                apply_event(action, pair, neighbors, multiplicity, system)
            index += 1
        actual = {(a, b) for a, b, _, _ in pairs}
        reconstructed = set()
        for edge, count in multiplicity.items():
            if count:
                reconstructed.add(edge)
        expected_edges = {tuple(sorted((first_star, second_star)))
                          for _, _, first_star, second_star in pairs
                          if first_star != second_star}
        if reconstructed != expected_edges:
            raise ValueError('{}: event/topology neighbor mismatch'.format(path))
        checked += 1
    if not checked:
        raise ValueError('{}: no topology frames'.format(path))


def analyze(prefix, system, windows):
    metadata, events = read_events(prefix + '.events', system)
    restart = metadata['input_file'].replace('.restart.lammpsdat', '.assoc_restart')
    initial = read_restart(restart, system, metadata)
    validate_topology(prefix + '.topology', initial, events, system)
    steps, frames = read_com(prefix + '.com_trajectory')
    neighbors, multiplicity = initialize(initial, system)
    grouped = collections.defaultdict(list)
    for event in events:
        grouped[event[0]].append(event)
    isolated = {}
    episodes = []
    for step in sorted(grouped):
        affected = set()
        for _, _, pair in grouped[step]:
            if bond_kind(pair, system) == 'inter':
                affected.update(system['atom_to_star'][atom] for atom in pair)
        before = {star: set(neighbors[star]) for star in affected}
        for _, action, pair in grouped[step]:
            if bond_kind(pair, system) == 'inter':
                apply_event(action, pair, neighbors, multiplicity, system)
        for star, old in before.items():
            new = set(neighbors[star])
            if old == new:
                kind = 'multiplicity_only'
            elif not new:
                isolated.setdefault(star, (step, old))
                continue
            elif star in isolated:
                start, old_neighbors = isolated.pop(star)
                episodes.append({'star': star, 'type': 'hop', 'start_step': start,
                                 'end_step': step, 'duration': (step - start) * metadata['dt'],
                                 'k_before': len(old_neighbors), 'k_after': len(new),
                                 'old_neighbors': ';'.join(map(str, sorted(old_neighbors))),
                                 'new_neighbors': ';'.join(map(str, sorted(new))), 'censored': False})
                continue
            else:
                kind = 'walking'
            episodes.append({'star': star, 'type': kind, 'start_step': step, 'end_step': step,
                             'duration': 0.0, 'k_before': len(old), 'k_after': len(new),
                             'old_neighbors': ';'.join(map(str, sorted(old))),
                             'new_neighbors': ';'.join(map(str, sorted(new))), 'censored': False})
    for star, (start, old) in isolated.items():
        episodes.append({'star': star, 'type': 'hop', 'start_step': start,
                         'end_step': metadata['total_requested_steps'],
                         'duration': (metadata['total_requested_steps'] - start) * metadata['dt'],
                         'k_before': len(old), 'k_after': 0,
                         'old_neighbors': ';'.join(map(str, sorted(old))), 'new_neighbors': '',
                         'censored': True})
    displacement_rows = []
    for episode in episodes:
        for window in windows:
            value = displacement(steps, frames, episode['star'], episode['start_step'], window,
                                 metadata['dt'])
            if value:
                before, after, time_before, time_after, distance, squared = value
                displacement_rows.append({'star': episode['star'], 'type': episode['type'],
                                          'window': window, 'before_step': before, 'after_step': after,
                                          'before_time': time_before, 'after_time': time_after,
                                          'distance': distance, 'distance_squared': squared})
    return metadata, episodes, displacement_rows


def self_test():
    frames = {0: {1: (0, 0, 0, 0)}, 10: {1: (1, 1, 0, 0)},
              20: {1: (2, 3, 0, 0)}}
    assert displacement([0, 10, 20], frames, 1, 10, 5, 1)[-2:] == (3.0, 9.0)
    assert displacement([0, 10, 20], frames, 1, 0, 10, 1) is None


def replica_statistics(values):
    mean = statistics.mean(values)
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    sem = std / math.sqrt(len(values))
    return {'mean': mean, 'sample_std': std, 'sem': sem,
            'ci95_half_width': 2.776 * sem if len(values) == 5 else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system')
    parser.add_argument('--output-prefix')
    parser.add_argument('--windows', type=float, nargs='+', default=(100, 200, 500, 1000))
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('prefixes', nargs='*')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test(); print('P4.7 WALKING_HOPPING SELF_TEST PASS'); return
    if not arguments.system or not arguments.output_prefix or not arguments.prefixes:
        parser.error('--system, --output-prefix, and prefixes are required')
    system = read_system(arguments.system, 2)
    episodes, displacements, summaries = [], [], []
    for replica, prefix in enumerate(arguments.prefixes, 1):
        metadata, current, current_displacements = analyze(prefix, system, arguments.windows)
        for row in current: row['replica'] = replica
        for row in current_displacements: row['replica'] = replica
        episodes.extend(current); displacements.extend(current_displacements)
        duration = (metadata['total_requested_steps'] - metadata['start_step']) * metadata['dt']
        summary = {'replica': replica, 'duration': duration}
        for kind in ('multiplicity_only', 'walking', 'hop'):
            count = sum(row['type'] == kind for row in current)
            summary[kind + '_count'] = count
            summary[kind + '_rate'] = count / duration
        for kind in ('multiplicity_only', 'walking', 'hop'):
            for window in arguments.windows:
                values = [row['distance_squared'] for row in current_displacements
                          if row['type'] == kind and row['window'] == window]
                if values:
                    summary['{}_msd_{}'.format(kind, window)] = statistics.mean(values)
        summaries.append(summary)
    for path, rows in ((arguments.output_prefix + '.episodes.csv', episodes),
                       (arguments.output_prefix + '.displacements.csv', displacements)):
        with open(path, 'w', newline='', encoding='utf-8') as output:
            writer = csv.DictWriter(output, fieldnames=sorted({key for row in rows for key in row}))
            writer.writeheader(); writer.writerows(rows)
    with open(arguments.output_prefix + '.summary.json', 'w', encoding='utf-8') as output:
        ensemble = {key: replica_statistics([row[key] for row in summaries])
                    for key in summaries[0] if key not in ('replica', 'duration')}
        json.dump({'replica_summaries': summaries, 'ensemble_replica_statistics': ensemble,
                   'grouping': 'same star and chemistry step only',
                   'com_windows': 'outward-snapped segment-local COM frames',
                   'topology_validation': 'all synchronized frames'}, output, indent=2)


if __name__ == '__main__':
    main()
