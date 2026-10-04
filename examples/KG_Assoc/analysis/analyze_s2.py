#!/usr/bin/env python3
"""Fail-closed S2 analysis for associating-star state and event outputs."""

import argparse
import csv
import json
import math
import os
import statistics
import sys
import tempfile


REQUIRED_METADATA = {
    'input_file': str,
    'arms': int,
    'narm': int,
    'total_particles': int,
    'stickers': int,
    'permanent_bonds': int,
    'T': float,
    'dt': float,
    'Ea': float,
    'Ee': float,
    'nu0': float,
    'Nevery': int,
    'r_assoc': float,
    'damping': float,
    'K': float,
    'R0': float,
    'seed': int,
    'total_requested_steps': int,
}
STATE_COLUMNS = (
    'timestep time N_free_stickers N_assoc_bonds creations breaks N_intra N_inter')
EVENT_COLUMNS = 'timestep event_type sticker_i sticker_j molecule_i molecule_j'


def metadata_from_comment(line, metadata, path):
    for token in line[1:].split():
        if '=' not in token:
            continue
        key, value = token.split('=', 1)
        if key in metadata and metadata[key] != value:
            raise ValueError('{}: conflicting metadata {} values'.format(path, key))
        metadata[key] = value


def require_metadata(metadata, path):
    parsed = {}
    for key, converter in REQUIRED_METADATA.items():
        if key not in metadata or not metadata[key]:
            raise ValueError('{}: missing required metadata {}'.format(path, key))
        try:
            parsed[key] = converter(metadata[key])
        except ValueError as error:
            raise ValueError('{}: invalid metadata {}={}'.format(
                path, key, metadata[key])) from error
    if parsed['stickers'] <= 0 or parsed['total_particles'] <= 0:
        raise ValueError('{}: nonpositive particle metadata'.format(path))
    if parsed['dt'] <= 0 or parsed['T'] <= 0 or parsed['Nevery'] <= 0:
        raise ValueError('{}: invalid physical metadata'.format(path))
    for key, value in metadata.items():
        parsed.setdefault(key, value)
    return parsed


def read_state(path):
    metadata = {}
    rows = []
    saw_columns = False
    with open(path, encoding='utf-8') as state_file:
        for raw_line in state_file:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if line[1:].strip() == STATE_COLUMNS:
                    saw_columns = True
                metadata_from_comment(line, metadata, path)
                continue
            fields = line.split()
            if len(fields) != 8:
                raise ValueError('{}: expected eight state columns'.format(path))
            try:
                rows.append({
                    'timestep': int(fields[0]),
                    'time': float(fields[1]),
                    'free': int(fields[2]),
                    'bonds': int(fields[3]),
                    'creations': int(fields[4]),
                    'breaks': int(fields[5]),
                    'intra': int(fields[6]),
                    'inter': int(fields[7]),
                })
            except ValueError as error:
                raise ValueError('{}: invalid state record {}'.format(path, line)) from error
    if not saw_columns:
        raise ValueError('{}: missing state column header'.format(path))
    metadata = require_metadata(metadata, path)
    if len(rows) < 3:
        raise ValueError('{}: too few state records'.format(path))
    previous_step = -1
    previous_time = -math.inf
    for row in rows:
        if row['timestep'] <= previous_step or row['time'] <= previous_time:
            raise ValueError('{}: state records are not strictly ordered'.format(path))
        if row['free'] + 2 * row['bonds'] != metadata['stickers']:
            raise ValueError('{}: free/bond state invariant failed'.format(path))
        if row['bonds'] != row['creations'] - row['breaks']:
            raise ValueError('{}: creation/break state invariant failed'.format(path))
        if row['bonds'] != row['intra'] + row['inter']:
            raise ValueError('{}: intra/inter state invariant failed'.format(path))
        previous_step = row['timestep']
        previous_time = row['time']
    if rows[-1]['timestep'] != metadata['total_requested_steps']:
        raise ValueError('{}: final timestep does not equal total_requested_steps'.format(path))
    return metadata, rows


def read_events(path):
    metadata = {}
    events = []
    saw_columns = False
    with open(path, encoding='utf-8') as event_file:
        for raw_line in event_file:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if line[1:].strip() == EVENT_COLUMNS:
                    saw_columns = True
                metadata_from_comment(line, metadata, path)
                continue
            fields = line.split()
            if len(fields) != 6:
                raise ValueError('{}: expected six event columns'.format(path))
            if fields[1] not in ('C', 'B'):
                raise ValueError('{}: unknown event type {}'.format(path, fields[1]))
            try:
                event = {
                    'timestep': int(fields[0]),
                    'type': fields[1],
                    'first': int(fields[2]),
                    'second': int(fields[3]),
                    'first_molecule': int(fields[4]),
                    'second_molecule': int(fields[5]),
                }
            except ValueError as error:
                raise ValueError('{}: invalid event record {}'.format(path, line)) from error
            if event['first'] >= event['second'] or event['first'] < 1:
                raise ValueError('{}: invalid 1-based sticker pair'.format(path))
            events.append(event)
    if not saw_columns:
        raise ValueError('{}: missing event column header'.format(path))
    if metadata.get('original_lammps_atom_ids') != '1_based':
        raise ValueError('{}: missing original 1-based ID provenance'.format(path))
    return require_metadata(metadata, path), events


def reconstruct_events(events, state_rows, metadata, path):
    if state_rows[0]['bonds'] != 0:
        raise ValueError('{}: nonzero initial bonds are left-censored and unsupported'.format(path))
    active = {}
    partner = {}
    lifetimes = []
    creations = 0
    breaks = 0
    previous_step = -1
    for event in events:
        if event['timestep'] < previous_step or event['timestep'] > state_rows[-1]['timestep']:
            raise ValueError('{}: event timestep is out of order or range'.format(path))
        previous_step = event['timestep']
        pair = (event['first'], event['second'])
        if event['type'] == 'C':
            if event['first'] in partner or event['second'] in partner or pair in active:
                raise ValueError('{}: creation violates sticker valence one'.format(path))
            active[pair] = event['timestep']
            partner[event['first']] = event['second']
            partner[event['second']] = event['first']
            creations += 1
        else:
            if pair not in active or partner.get(event['first']) != event['second']:
                raise ValueError('{}: break without matching active bond'.format(path))
            lifetimes.append((event['timestep'] - active[pair]) * metadata['dt'])
            del active[pair]
            del partner[event['first']]
            del partner[event['second']]
            breaks += 1
    if creations != state_rows[-1]['creations'] or breaks != state_rows[-1]['breaks']:
        raise ValueError('{}: event totals disagree with final state'.format(path))

    event_index = 0
    active_count = 0
    for row in state_rows:
        while event_index < len(events) and events[event_index]['timestep'] <= row['timestep']:
            active_count += 1 if events[event_index]['type'] == 'C' else -1
            event_index += 1
        if active_count != row['bonds']:
            raise ValueError('{}: event reconstruction does not reproduce N_assoc'.format(path))
    return lifetimes, 0, len(active)


def mean(values):
    if not values:
        raise ValueError('cannot average an empty series')
    return statistics.mean(values)


def mean_or_nan(values):
    return mean(values) if values else float('nan')


def linear_slope(times, values):
    time_mean = mean(times)
    value_mean = mean(values)
    denominator = sum((time - time_mean) ** 2 for time in times)
    if denominator == 0:
        raise ValueError('stationarity window has zero time span')
    return sum((time - time_mean) * (value - value_mean)
               for time, value in zip(times, values)) / denominator


def analyze(state_path, event_path, burn_in_fraction=0.5):
    if not 0.0 <= burn_in_fraction < 1.0:
        raise ValueError('burn-in fraction must satisfy 0 <= fraction < 1')
    metadata, rows = read_state(state_path)
    event_metadata, events = read_events(event_path)
    for key in REQUIRED_METADATA:
        if event_metadata[key] != metadata[key]:
            raise ValueError('{}: state/event metadata {} disagrees'.format(state_path, key))
    lifetimes, left_censored, right_censored = reconstruct_events(
        events, rows, metadata, state_path)

    start_time = rows[0]['time']
    end_time = rows[-1]['time']
    analysis_start = start_time + burn_in_fraction * (end_time - start_time)
    window = [row for row in rows if row['time'] >= analysis_start]
    if len(window) < 3:
        raise ValueError('{}: too few post-burn-in samples'.format(state_path))
    midpoint = analysis_start + 0.5 * (end_time - analysis_start)
    first_half = [row for row in window if row['time'] <= midpoint]
    second_half = [row for row in window if row['time'] > midpoint]
    if not first_half or not second_half:
        raise ValueError('{}: stationarity halves are empty'.format(state_path))

    bonded_fractions = [2.0 * row['bonds'] / metadata['stickers'] for row in window]
    free_fractions = [row['free'] / metadata['stickers'] for row in window]
    first_fraction = mean([2.0 * row['bonds'] / metadata['stickers'] for row in first_half])
    second_fraction = mean([2.0 * row['bonds'] / metadata['stickers'] for row in second_half])
    mean_bonds = mean([row['bonds'] for row in window])
    slope = linear_slope([row['time'] for row in window],
                         [row['bonds'] for row in window])
    analysis_events = [event for event in events if event['timestep'] >= window[0]['timestep']]
    duration = window[-1]['time'] - window[0]['time']
    if duration <= 0:
        raise ValueError('{}: zero analysis duration'.format(state_path))
    creation_count = sum(event['type'] == 'C' for event in analysis_events)
    break_count = sum(event['type'] == 'B' for event in analysis_events)
    chemistry_dt = metadata['Nevery'] * metadata['dt']
    q = -math.expm1(-metadata['nu0'] * math.exp(-metadata['Ea'] / metadata['T']) * chemistry_dt)
    attempt_rate = q / chemistry_dt
    candidate_pairs = float(metadata.get('candidate_sticker_pairs', 'nan'))
    chemistry_sweeps = float(metadata.get('chemistry_sweeps', 'nan'))

    return {
        'state_file': state_path,
        'event_file': event_path,
        'seed': metadata['seed'],
        'Ea': metadata['Ea'],
        'Ee': metadata['Ee'],
        'Nevery': metadata['Nevery'],
        'dt': metadata['dt'],
        'delta_t_chem': chemistry_dt,
        'attempt_probability': q,
        'attempt_rate': attempt_rate,
        'mean_N_assoc': mean_bonds,
        'mean_bonded_sticker_fraction': mean(bonded_fractions),
        'mean_free_sticker_fraction': mean(free_fractions),
        'mean_N_intra': mean([row['intra'] for row in window]),
        'mean_N_inter': mean([row['inter'] for row in window]),
        'intra_fraction_active_bonds': mean_or_nan([row['intra'] / row['bonds']
                                                    for row in window if row['bonds']]),
        'inter_fraction_active_bonds': mean_or_nan([row['inter'] / row['bonds']
                                                    for row in window if row['bonds']]),
        'creation_count_analysis_window': creation_count,
        'break_count_analysis_window': break_count,
        'creation_rate': creation_count / duration,
        'break_rate': break_count / duration,
        'mean_candidate_pairs_per_sweep': (
            candidate_pairs / chemistry_sweeps if chemistry_sweeps else float('nan')),
        'mean_bound_fraction_first_half': first_fraction,
        'mean_bound_fraction_second_half': second_fraction,
        'stationarity_absolute_difference': abs(second_fraction - first_fraction),
        'stationarity_pass_0p01': abs(second_fraction - first_fraction) <= 0.01,
        'normalized_N_assoc_drift_slope': slope / mean_bonds if mean_bonds else float('nan'),
        'complete_lifetime_count': len(lifetimes),
        'mean_complete_lifetime': mean(lifetimes) if lifetimes else float('nan'),
        'median_complete_lifetime': statistics.median(lifetimes) if lifetimes else float('nan'),
        'left_censored_bonds_excluded': left_censored,
        'right_censored_bonds_excluded': right_censored,
    }


def write_summary(results, path):
    keys = sorted({key for result in results for key in result})
    with open(path, 'w', newline='', encoding='utf-8') as summary_file:
        writer = csv.DictWriter(summary_file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)


def annotate_replica_groups(results):
    groups = {}
    for result in results:
        key = (result['Ea'], result['Ee'], result['Nevery'], result['dt'])
        groups.setdefault(key, []).append(result)
    for group in groups.values():
        if len(group) < 2:
            span = float('nan')
            passed = None
        else:
            fractions = [result['mean_bonded_sticker_fraction'] for result in group]
            span = max(fractions) - min(fractions)
            passed = span <= 0.02
        for result in group:
            result['replica_count_same_condition'] = len(group)
            result['replica_bonded_fraction_span'] = span
            result['replica_reproducibility_pass_0p02'] = passed


def run_self_test():
    state_header = (
        '# timestep time N_free_stickers N_assoc_bonds creations breaks N_intra N_inter\n'
        '# input_file=test.lammpsdat arms=2 narm=3 total_particles=20 stickers=4 '
        'permanent_bonds=18 T=1 dt=1 Ea=4 Ee=8 nu0=20 Nevery=1 r_assoc=1.1 '
        'damping=2 K=30 R0=1.5 seed=7 total_requested_steps=4\n')
    event_header = (
        '# timestep event_type sticker_i sticker_j molecule_i molecule_j\n'
        '# input_file=test.lammpsdat arms=2 narm=3 total_particles=20 stickers=4 '
        'permanent_bonds=18 T=1 dt=1 Ea=4 Ee=8 nu0=20 Nevery=1 r_assoc=1.1 '
        'damping=2 K=30 R0=1.5 seed=7 total_requested_steps=4 '
        'original_lammps_atom_ids=1_based\n')
    states = (
        '0 0 4 0 0 0 0 0\n'
        '1 1 2 1 1 0 1 0\n'
        '2 2 4 0 1 1 0 0\n'
        '3 3 2 1 2 1 0 1\n'
        '4 4 4 0 2 2 0 0\n'
        '# chemistry_sweeps=4 candidate_sticker_pairs=12\n')
    events = '1 C 1 2 10 10\n2 B 1 2 10 10\n3 C 3 4 11 12\n4 B 3 4 11 12\n'
    with tempfile.TemporaryDirectory() as directory:
        state_path = os.path.join(directory, 'test.state')
        event_path = os.path.join(directory, 'test.events')
        with open(state_path, 'w', encoding='utf-8') as state_file:
            state_file.write(state_header + states)
        with open(event_path, 'w', encoding='utf-8') as event_file:
            event_file.write(event_header + events)
        result = analyze(state_path, event_path)
        if (result['complete_lifetime_count'] != 2 or
                result['right_censored_bonds_excluded'] != 0 or
                not math.isclose(result['mean_complete_lifetime'], 1.0) or
                not math.isclose(result['mean_candidate_pairs_per_sweep'], 3.0) or
                not math.isclose(result['mean_bound_fraction_first_half'], 0.25) or
                not math.isclose(result['mean_bound_fraction_second_half'], 0.0)):
            raise AssertionError('event reconstruction or lifetime regression failed')

        for bad_events, message in (
                ('1 C 1 2 10 10\n1 C 1 3 10 11\n', 'duplicate creation'),
                ('1 B 1 2 10 10\n', 'break without active bond')):
            with open(event_path, 'w', encoding='utf-8') as event_file:
                event_file.write(event_header + bad_events)
            try:
                analyze(state_path, event_path)
                raise AssertionError(message + ' was accepted')
            except ValueError:
                pass

        with open(state_path, 'w', encoding='utf-8') as state_file:
            state_file.write(state_header.replace('stickers=4', ''))
            state_file.write(states)
        try:
            read_state(state_path)
            raise AssertionError('missing metadata was accepted')
        except ValueError:
            pass

    print('S2 ANALYZER SELF_TEST PASS event reconstruction, censoring, stationarity, metadata')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('state_files', nargs='*')
    parser.add_argument('--events', help='event file for one state file')
    parser.add_argument('--burn-in-fraction', type=float, default=0.5)
    parser.add_argument('--summary', help='write per-trajectory CSV')
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()
    if arguments.self_test:
        run_self_test()
        return
    if not arguments.state_files:
        parser.error('at least one .state file is required')
    if arguments.events and len(arguments.state_files) != 1:
        parser.error('--events requires exactly one state file')
    results = []
    for state_path in arguments.state_files:
        event_path = arguments.events or os.path.splitext(state_path)[0] + '.events'
        results.append(analyze(state_path, event_path, arguments.burn_in_fraction))
    annotate_replica_groups(results)
    if arguments.summary:
        write_summary(results, arguments.summary)
    json.dump(results, sys.stdout, indent=2, allow_nan=True)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
