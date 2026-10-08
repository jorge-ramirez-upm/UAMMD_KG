#!/usr/bin/env python3
"""Topology-defined walking/hopping analysis on segment-local COM trajectories."""

import argparse
import bisect
import collections
import csv
import json
import math
import statistics
from pathlib import Path

from analyze_p45_topology import read_system, topology_frames
from analyze_p46_bond_dynamics import bond_kind, read_events, read_restart

QUANTILES = (0.50, 0.75, 0.90, 0.95, 0.99, 0.995)
KINDS = ('multiplicity_only', 'walking', 'hop')


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


def displacement(steps, frames, star, event_step, half_window, dt):
    """Return an outward-snapped event displacement; half_window is not total lag."""
    offset = round(half_window / dt)
    left = bisect.bisect_right(steps, event_step - offset) - 1
    right = bisect.bisect_left(steps, event_step + offset)
    if left < 0 or right == len(steps):
        return None
    before, after = steps[left], steps[right]
    first, second = frames[before][star], frames[after][star]
    squared = sum((a - b) ** 2 for a, b in zip(first[1:], second[1:]))
    return before, after, first[0], second[0], math.sqrt(squared), squared


def lag_statistics(steps, frames, lag, stars, dt, reservoir_size=100000):
    """Stream exact-lag COM displacements, retaining only a bounded quantile sample."""
    step_lag = round(lag / dt)
    step_set = set(steps)
    count = 0
    squared_sum = 0.0
    reservoir = []
    for step in steps:
        if step + step_lag not in step_set:
            continue
        for star in stars:
            first, second = frames[step][star], frames[step + step_lag][star]
            squared = sum((a - b) ** 2 for a, b in zip(first[1:], second[1:]))
            distance = math.sqrt(squared)
            count += 1
            squared_sum += squared
            if len(reservoir) < reservoir_size:
                reservoir.append(distance)
            else:
                # Deterministic bounded sample: preserve reproducibility without storing all rows.
                replacement = int((count * 1103515245 + round(lag) * 12345) % count)
                if replacement < reservoir_size:
                    reservoir[replacement] = distance
    return {'count': count, 'msd': squared_sum / count if count else None,
            'distances': reservoir}


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
        reconstructed = {edge for edge, count in multiplicity.items() if count}
        expected = {tuple(sorted((first_star, second_star)))
                    for _, _, first_star, second_star in pairs
                    if first_star != second_star}
        if reconstructed != expected:
            raise ValueError('{}: event/topology neighbor mismatch'.format(path))
        checked += 1
    if not checked:
        raise ValueError('{}: no topology frames'.format(path))


def parse_key_values(path):
    values = {}
    with open(path, encoding='utf-8') as source:
        for line in source:
            if line.startswith('#'):
                for token in line[1:].split():
                    if '=' in token:
                        key, value = token.split('=', 1)
                        values[key] = value
    return values


def system_metadata(system_path, event_metadata, system):
    values = parse_key_values(system_path)
    values.update(event_metadata)
    input_file = event_metadata.get('input_file', '')
    label = Path(input_file).parent.name if input_file else 'unavailable'
    result = {
        'system_label': label,
        'number_of_stars': len(system['stars']),
        'arms_per_star': int(values['arms']) if 'arms' in values else None,
        'arm_length': int(values['narm']) if 'narm' in values else None,
        'stickers_per_star': (len(system['stickers']) // len(system['stars'])
                              if system['stars'] else None),
        'total_polymer_density': None,
        'Ea': float(event_metadata['Ea']) if 'Ea' in event_metadata else None,
        'Ee': float(event_metadata['Ee']) if 'Ee' in event_metadata else None,
        'nu0': float(event_metadata['nu0']) if 'nu0' in event_metadata else None,
        'Nevery': int(event_metadata['Nevery']) if 'Nevery' in event_metadata else None,
        'r_assoc': float(event_metadata['r_assoc']) if 'r_assoc' in event_metadata else None,
        'temperature': float(event_metadata['T']) if 'T' in event_metadata else None,
        'dt': event_metadata['dt'], 'seed': event_metadata['seed'],
        'replica_id': event_metadata['seed'], 'box_size': None,
    }
    bounds = []
    try:
        with open(system_path, encoding='utf-8') as source:
            lines = iter(source)
            for line in lines:
                fields = line.split()
                if len(fields) == 4 and fields[2:] == ['xlo', 'xhi']:
                    bounds = [float(value) for value in fields[:2]]
                    bounds += [float(value) for value in next(lines).split()[:2]]
                    bounds += [float(value) for value in next(lines).split()[:2]]
                    break
    except (OSError, StopIteration, ValueError):
        bounds = []
    if len(bounds) == 6:
        box = [bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]]
        result['box_size'] = box
        if 'total_particles' in event_metadata:
            result['total_polymer_density'] = int(event_metadata['total_particles']) / math.prod(box)
    return result


def classify(prefix, system, half_windows):
    metadata, events = read_events(prefix + '.events', system)
    restart = metadata['input_file'].replace('.restart.lammpsdat', '.assoc_restart')
    initial = read_restart(restart, system, metadata)
    validate_topology(prefix + '.topology', initial, events, system)
    steps, frames = read_com(prefix + '.com_trajectory')
    neighbors, multiplicity = initialize(initial, system)
    grouped = collections.defaultdict(list)
    for event in events:
        grouped[event[0]].append(event)
    isolated, episodes = {}, []
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
                                 'censored': False})
                continue
            else:
                kind = 'walking'
            episodes.append({'star': star, 'type': kind, 'start_step': step,
                             'end_step': step, 'duration': 0.0,
                             'k_before': len(old), 'k_after': len(new), 'censored': False})
    for star, (start, old) in isolated.items():
        episodes.append({'star': star, 'type': 'hop', 'start_step': start,
                         'end_step': metadata['total_requested_steps'],
                         'duration': (metadata['total_requested_steps'] - start) * metadata['dt'],
                         'k_before': len(old), 'k_after': 0, 'censored': True})
    rows = []
    for episode in episodes:
        for half_window in half_windows:
            value = displacement(steps, frames, episode['star'], episode['start_step'],
                                 half_window, metadata['dt'])
            if value:
                before, after, time_before, time_after, distance, squared = value
                rows.append({'star': episode['star'], 'type': episode['type'],
                             'half_window': half_window, 'window': half_window,
                             'total_lag': time_after - time_before,
                             'before_step': before, 'after_step': after,
                             'before_time': time_before, 'after_time': time_after,
                             'distance': distance, 'distance_squared': squared})
    return metadata, episodes, rows, steps, frames


def quantile(values, probability):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def empirical_ccdf(values, radii):
    return [sum(value >= radius for value in values) / len(values) if values else None
            for radius in radii]


def replica_statistics(values):
    values = [value for value in values if value is not None]
    if not values:
        return {'mean': None, 'sample_std': None, 'sem': None, 'ci95_half_width': None}
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    critical = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776}.get(len(values), 1.96)
    return {'mean': statistics.mean(values), 'sample_std': std,
            'sem': std / math.sqrt(len(values)), 'ci95_half_width': critical * std / math.sqrt(len(values))}


def write_csv(path, rows):
    fields = sorted({key for row in rows for key in row})
    with open(path, 'w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def kaplan_meier(durations):
    """KM survival where each item is (duration, completed)."""
    grouped = collections.defaultdict(lambda: [0, 0])
    for duration, completed in durations:
        grouped[duration][0 if completed else 1] += 1
    risk, survival = len(durations), 1.0
    result = [{'duration': 0.0, 'survival': 1.0, 'at_risk': risk,
               'completed': 0, 'right_censored': 0}]
    for duration in sorted(grouped):
        completed, censored = grouped[duration]
        if completed:
            survival *= 1.0 - completed / risk
        result.append({'duration': duration, 'survival': survival, 'at_risk': risk,
                       'completed': completed, 'right_censored': censored})
        risk -= completed + censored
    return result


def analyze(prefix, system, half_windows):
    metadata, episodes, event_rows, steps, frames = classify(prefix, system, half_windows)
    lags = sorted({row['total_lag'] for row in event_rows})
    unconditional = {lag: lag_statistics(steps, frames, lag, system['stars'], metadata['dt'])
                     for lag in lags}
    provenance_path = metadata['input_file'].replace('.restart.lammpsdat', '.restart.lammpsdat')
    return metadata, episodes, event_rows, unconditional, system_metadata(provenance_path, metadata, system)


def self_test():
    frames = {0: {1: (0, 0, 0, 0)}, 10: {1: (1, 1, 0, 0)}, 20: {1: (2, 3, 0, 0)}}
    assert displacement([0, 10, 20], frames, 1, 10, 5, 1)[-2:] == (3.0, 9.0)
    assert displacement([0, 10, 20], frames, 1, 0, 10, 1) is None
    ballistic = {step: {1: (step, step, 0, 0)} for step in range(4)}
    assert lag_statistics([0, 1, 2, 3], ballistic, 1, (1,), 1)['msd'] == 1.0
    constant = {step: {1: (step, 4, 5, 6)} for step in range(3)}
    assert lag_statistics([0, 1, 2], constant, 1, (1,), 1)['msd'] == 0.0
    assert quantile([1, 2, 3, 4], .5) == 2.5
    assert empirical_ccdf([1, 2, 3], [1, 2, 4]) == [1.0, 2 / 3, 0.0]
    assert kaplan_meier([(1, True), (2, False)])[-1]['survival'] == 0.5
    print('P4.7B SELF_TEST PASS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system')
    parser.add_argument('--output-prefix')
    parser.add_argument('--windows', type=float, nargs='+', default=(100, 200, 500, 1000))
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('prefixes', nargs='*')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if not arguments.system or not arguments.output_prefix or not arguments.prefixes:
        parser.error('--system, --output-prefix, and prefixes are required')
    system = read_system(arguments.system, 2)
    all_events, all_displacements = [], []
    unconditional_rows, unconditional_quantiles = [], collections.defaultdict(list)
    summaries, metadata_by_replica, survival_rows = [], {}, []
    for replica, prefix in enumerate(arguments.prefixes, 1):
        metadata, episodes, event_rows, unconditional, provenance = analyze(prefix, system, arguments.windows)
        for row in episodes:
            row.update(replica=replica)
        for row in event_rows:
            row.update(replica=replica)
        for lag, values in unconditional.items():
            distances = values['distances']
            unconditional_rows.append({'replica': replica, 'total_lag': lag,
                                        'support': values['count'], 'msd': values['msd'],
                                        'q90': quantile(distances, .9), 'q95': quantile(distances, .95),
                                        'q99': quantile(distances, .99)})
            unconditional_quantiles[lag].append({
                'q90': quantile(distances, .9), 'q95': quantile(distances, .95),
                'q99': quantile(distances, .99)})
        all_events.extend(episodes)
        all_displacements.extend(event_rows)
        metadata_by_replica[replica] = provenance
        summary = {'replica': replica,
                   'duration': (metadata['total_requested_steps'] - metadata['start_step']) * metadata['dt']}
        for kind in KINDS:
            kind_rows = [row for row in episodes if row['type'] == kind]
            summary[kind + '_count'] = len(kind_rows)
            summary[kind + '_rate'] = len(kind_rows) / summary['duration']
            if kind == 'hop':
                completed = [row['duration'] for row in kind_rows if not row['censored']]
                censored = [row['duration'] for row in kind_rows if row['censored']]
                summary['hop_completed_count'] = len(completed)
                summary['hop_right_censored_count'] = len(censored)
                for name, probability in (('median', .5), ('p75', .75), ('p90', .9), ('p95', .95), ('p99', .99)):
                    summary['hop_duration_' + name] = quantile(completed, probability)
                summary['hop_duration_max'] = max(completed) if completed else None
                survival_rows.extend(dict(row, replica=replica)
                                     for row in kaplan_meier([(row['duration'], not row['censored']) for row in kind_rows]))
        for lag in sorted(unconditional):
            summary['unconditional_msd_{}'.format(lag)] = unconditional[lag]['msd']
            for kind in KINDS:
                values = [row['distance_squared'] for row in event_rows
                          if row['type'] == kind and row['total_lag'] == lag]
                conditioned = statistics.mean(values) if values else None
                summary['{}_msd_{}'.format(kind, lag)] = conditioned
                summary['{}_ratio_{}'.format(kind, lag)] = conditioned / summary['unconditional_msd_{}'.format(lag)] if conditioned else None
        summaries.append(summary)
    write_csv(arguments.output_prefix + '.episodes.csv', all_events)
    write_csv(arguments.output_prefix + '.displacements.csv', all_displacements)
    write_csv(arguments.output_prefix + '.unconditional.csv', unconditional_rows)
    quantile_rows = []
    lags = sorted({row['total_lag'] for row in all_displacements})
    for replica in range(1, len(summaries) + 1):
        for kind in KINDS:
            for lag in lags:
                values = [row['distance'] for row in all_displacements
                          if row['replica'] == replica and row['type'] == kind and row['total_lag'] == lag]
                quantile_rows.append({'replica': replica, 'type': kind, 'total_lag': lag, 'count': len(values),
                                      **{'q{}'.format(str(p).replace('.', '')): quantile(values, p) for p in QUANTILES}})
    for kind in KINDS:
        for lag in lags:
            replica_values = [row for row in quantile_rows
                              if row['type'] == kind and row['total_lag'] == lag]
            if replica_values:
                quantile_rows.append({'replica': 'ensemble', 'type': kind, 'total_lag': lag,
                                      'count': sum(row['count'] for row in replica_values),
                                      **{'q{}'.format(str(p).replace('.', '')): replica_statistics(
                                          [row['q{}'.format(str(p).replace('.', ''))] for row in replica_values]
                                          )['mean'] for p in QUANTILES}})
    write_csv(arguments.output_prefix + '.displacement_quantiles.csv', quantile_rows)

    duration_displacement_rows = []
    completed_hops = [row for row in all_events if row['type'] == 'hop' and not row['censored'] and row['duration'] > 0]
    if completed_hops:
        displacement_index = collections.defaultdict(list)
        for row in all_displacements:
            displacement_index[(row['replica'], row['star'], row['type'], row['total_lag'])].append(row)
        minimum = min(row['duration'] for row in completed_hops)
        maximum = max(row['duration'] for row in completed_hops)
        bin_count = min(8, max(1, math.ceil(math.log10(maximum / minimum + 1.0) * 3)))
        edges = [minimum * (maximum / minimum) ** (index / bin_count)
                 for index in range(bin_count + 1)] if maximum > minimum else [minimum, maximum + 1.0]
        for lag in lags:
            for index in range(len(edges) - 1):
                lower, upper = edges[index], edges[index + 1]
                selected = []
                for hop in completed_hops:
                    if not (lower <= hop['duration'] < upper or
                            index == len(edges) - 2 and hop['duration'] == upper):
                        continue
                    selected.extend(row for row in displacement_index[
                        (hop['replica'], hop['star'], 'hop', lag)]
                                    if row['before_step'] <= hop['start_step'] <= row['after_step'])
                distances = [row['distance'] for row in selected]
                squared = [row['distance_squared'] for row in selected]
                durations = [hop['duration'] for hop in completed_hops
                             if lower <= hop['duration'] < upper or
                             index == len(edges) - 2 and hop['duration'] == upper]
                duration_displacement_rows.append({
                    'total_lag': lag, 'bin': index, 'duration_lower': lower,
                    'duration_upper': upper, 'event_count': len(durations),
                    'displacement_count': len(distances),
                    'median_duration': quantile(durations, .5),
                    'mean_displacement': statistics.mean(distances) if distances else None,
                    'median_displacement': quantile(distances, .5),
                    'q90_displacement': quantile(distances, .9),
                    'mean_squared_displacement': statistics.mean(squared) if squared else None,
                    'q90_squared_displacement': quantile(squared, .9)})
    write_csv(arguments.output_prefix + '.hop_duration_displacement.csv', duration_displacement_rows)
    tail_rows = []
    displacements_by_lag_kind = collections.defaultdict(list)
    for row in all_displacements:
        displacements_by_lag_kind[(row['total_lag'], row['type'])].append(row)
    for lag in lags:
        thresholds = {name: statistics.mean(row[name] for row in unconditional_quantiles[lag])
                      for name in ('q90', 'q95', 'q99')}
        classified = [row for kind in KINDS for row in displacements_by_lag_kind[(lag, kind)]]
        for threshold_name, threshold in thresholds.items():
            tail = [row for row in classified if row['distance'] > threshold]
            for kind in KINDS:
                kind_all = displacements_by_lag_kind[(lag, kind)]
                tail_kind = [row for row in kind_all if row['distance'] > threshold]
                tail_rows.append({'total_lag': lag, 'threshold': threshold_name, 'threshold_radius': threshold,
                                  'type': kind, 'class_count': len(kind_all), 'tail_count': len(tail_kind),
                                  'P_tail_given_class': len(tail_kind) / len(kind_all) if kind_all else None,
                                  'fraction_of_tail': len(tail_kind) / len(tail) if tail else None,
                                  'tail_count_all_classes': len(tail)})
    write_csv(arguments.output_prefix + '.displacement_tail.csv', tail_rows)
    all_distances = [row['distance'] for row in all_displacements]
    if all_distances:
        radius_min, radius_max = min(all_distances), max(all_distances)
        radii = ([radius_min] if radius_min == radius_max else
                 [radius_min + (radius_max - radius_min) * index / 31 for index in range(32)])
        ccdf_rows = []
        for lag in lags:
            for kind in KINDS:
                values = [row['distance'] for row in all_displacements
                          if row['total_lag'] == lag and row['type'] == kind]
                for radius, probability in zip(radii, empirical_ccdf(values, radii)):
                    ccdf_rows.append({'total_lag': lag, 'type': kind, 'radius': radius,
                                      'ccdf': probability, 'count': len(values)})
        write_csv(arguments.output_prefix + '.displacement_ccdf.csv', ccdf_rows)
    write_csv(arguments.output_prefix + '.hop_duration_survival.csv', survival_rows)
    write_csv(arguments.output_prefix + '.hop_duration_quantiles.csv', [
        {key: value for key, value in row.items() if key.startswith('hop_') or key == 'replica'}
        for row in summaries])
    ensemble = {key: replica_statistics([row[key] for row in summaries])
                for key in summaries[0] if key not in ('replica', 'duration')}
    summary = {'replica_summaries': summaries, 'ensemble_replica_statistics': ensemble,
               'system_metadata': metadata_by_replica,
               'grouping': 'same star and chemistry step only',
               'half_window_definition': 'event_step +/- half_window, outward-snapped to sampled COM frames',
               'total_lag_definition': 'after_time - before_time; no interpolation or restart stitching',
               'uncertainty': 'replica-level Student-t intervals; event rows are descriptive support',
               'topology_validation': 'all synchronized frames'}
    with open(arguments.output_prefix + '.summary.json', 'w', encoding='utf-8') as output:
        json.dump(summary, output, indent=2)


if __name__ == '__main__':
    main()
