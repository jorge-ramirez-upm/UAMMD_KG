#!/usr/bin/env python3
"""Descriptive, fail-closed stationarity diagnostics for P3.1 E2 state files."""
import argparse
import json
import math
import statistics
import tempfile
import sys


COLUMNS = ('timestep time N_free_stickers N_assoc_bonds creations breaks '
           'N_intra N_inter bound_fraction connected_components '
           'largest_cluster_size largest_cluster_fraction mean_degree '
           'second_degree_moment L1 L2 active_bond_observations '
           'max_active_bond_distance fraction_active_gt_1p25 '
           'fraction_active_gt_1p30 fraction_active_gt_1p40')
METRICS = ('bound_fraction', 'intra', 'inter', 'L1', 'L2',
           'largest_cluster_fraction', 'mean_degree')


def read_state(path):
    metadata = {}
    rows = []
    saw_header = False
    with open(path, encoding='utf-8') as state_file:
        for raw_line in state_file:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if line[1:].strip() == COLUMNS:
                    saw_header = True
                for token in line[1:].split():
                    if '=' in token:
                        key, value = token.split('=', 1)
                        if key in metadata and metadata[key] != value:
                            raise ValueError('{}: conflicting metadata {}'.format(path, key))
                        metadata[key] = value
                continue
            fields = line.split()
            if len(fields) != 21:
                raise ValueError('{}: expected 21 E2 state columns'.format(path))
            try:
                values = [float(field) for field in fields]
            except ValueError as error:
                raise ValueError('{}: invalid numeric state row'.format(path)) from error
            if not all(math.isfinite(value) for value in values):
                raise ValueError('{}: nonfinite state value'.format(path))
            rows.append(dict(zip(
                ('step', 'time', 'free', 'bonds', 'creations', 'breaks', 'intra',
                 'inter', 'bound_fraction', 'components', 'largest_size',
                 'largest_cluster_fraction', 'mean_degree', 'second_degree_moment',
                 'L1', 'L2', 'active_observations', 'max_active_bond_distance',
                 'fraction_active_gt_1p25', 'fraction_active_gt_1p30',
                 'fraction_active_gt_1p40'), values)))
    if not saw_header or len(rows) < 4:
        raise ValueError('{}: missing E2 header or too few samples'.format(path))
    for key in ('stickers', 'dt', 'total_requested_steps'):
        if key not in metadata:
            raise ValueError('{}: missing metadata {}'.format(path, key))
    stickers = int(metadata['stickers'])
    if stickers <= 0 or float(metadata['dt']) <= 0:
        raise ValueError('{}: invalid physical metadata'.format(path))
    previous = None
    for row in rows:
        if previous and (row['step'] <= previous['step'] or row['time'] <= previous['time']):
            raise ValueError('{}: nonmonotonic diagnostic rows'.format(path))
        if row['free'] + 2 * row['bonds'] != stickers:
            raise ValueError('{}: free/bond invariant failed'.format(path))
        if row['bonds'] != row['creations'] - row['breaks'] or row['bonds'] != row['intra'] + row['inter']:
            raise ValueError('{}: bond-count invariant failed'.format(path))
        if not math.isclose(row['bound_fraction'], 2 * row['bonds'] / stickers,
                            rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError('{}: bound-fraction invariant failed'.format(path))
        previous = row
    return metadata, rows


def slope(times, values):
    average_time = statistics.mean(times)
    denominator = sum((time - average_time) ** 2 for time in times)
    if denominator == 0:
        raise ValueError('zero time span')
    average_value = statistics.mean(values)
    return sum((time - average_time) * (value - average_value)
               for time, value in zip(times, values)) / denominator


def iat(values, times):
    intervals = [right - left for left, right in zip(times, times[1:])]
    if not intervals or max(intervals) - min(intervals) > 1e-10 * max(intervals):
        return float('nan'), float('nan')
    centered = [value - statistics.mean(values) for value in values]
    variance = sum(value * value for value in centered)
    if variance == 0:
        return 0.5, len(values)
    tau = 0.5
    for lag in range(1, len(values)):
        correlation = sum(centered[index] * centered[index + lag]
                          for index in range(len(values) - lag)) / variance
        if correlation <= 0:
            break
        tau += correlation
    return tau, len(values) / (2.0 * tau)


def block_values(values, block_count):
    block_count = min(block_count, len(values))
    if block_count < 1:
        raise ValueError('at least one sample is required for blocks')
    return [values[index * len(values) // block_count:
                   (index + 1) * len(values) // block_count]
            for index in range(block_count)]


def block_means(values, block_count):
    return [statistics.mean(block) for block in block_values(values, block_count)]


def describe(rows, blocks):
    times = [row['time'] for row in rows]
    midpoint = 0.5 * (times[0] + times[-1])
    first = [row for row in rows if row['time'] <= midpoint]
    second = [row for row in rows if row['time'] > midpoint]
    if not first or not second:
        raise ValueError('empty half-window')
    result = {}
    for metric in METRICS:
        values = [row[metric] for row in rows]
        first_mean = statistics.mean(row[metric] for row in first)
        second_values = [row[metric] for row in second]
        second_mean = statistics.mean(second_values)
        tau_lag, effective = iat(values, times)
        result[metric] = {
            'first_half_mean': first_mean,
            'second_half_mean': second_mean,
            'relative_half_difference': ((second_mean - first_mean) /
                                         max(abs(first_mean), 1e-12)),
            'second_half_linear_slope': slope([row['time'] for row in second], second_values),
            'block_means': block_means(values, blocks),
            'integrated_autocorrelation_time': (
                tau_lag * statistics.mean(
                    right - left for left, right in zip(times, times[1:]))
                if math.isfinite(tau_lag) else tau_lag),
            'integrated_autocorrelation_lag_steps': tau_lag,
            'effective_sample_count': effective,
        }
    duration = times[-1] - times[0]
    second_duration = second[-1]['time'] - second[0]['time']
    second_creations = second[-1]['creations'] - second[0]['creations']
    second_breaks = second[-1]['breaks'] - second[0]['breaks']
    return {
        'sample_count': len(rows),
        'time_range': [times[0], times[-1]],
        'sampling_interval': (statistics.mean(
            right - left for left, right in zip(times, times[1:]))
                              if len(times) > 1 else float('nan')),
        'metrics': result,
        'event_balance': {
            'total_creations': rows[-1]['creations'] - rows[0]['creations'],
            'total_breaks': rows[-1]['breaks'] - rows[0]['breaks'],
            'net_bond_change': rows[-1]['bonds'] - rows[0]['bonds'],
            'creation_rate': (rows[-1]['creations'] - rows[0]['creations']) / duration,
            'break_rate': (rows[-1]['breaks'] - rows[0]['breaks']) / duration,
        },
        'second_half_event_balance': {
            'creations': second_creations,
            'breaks': second_breaks,
            'net_bond_change': second[-1]['bonds'] - second[0]['bonds'],
            'creation_rate': second_creations / second_duration,
            'break_rate': second_breaks / second_duration,
        },
        'active_bond_distance_safety': {
            'maximum_active_bond_distance_observed': max(
                row['max_active_bond_distance'] for row in rows),
            'fraction_active_gt_1p25_mean': statistics.mean(
                row['fraction_active_gt_1p25'] for row in rows),
            'fraction_active_gt_1p25_final': rows[-1]['fraction_active_gt_1p25'],
            'fraction_active_gt_1p30_mean': statistics.mean(
                row['fraction_active_gt_1p30'] for row in rows),
            'fraction_active_gt_1p30_final': rows[-1]['fraction_active_gt_1p30'],
            'fraction_active_gt_1p40_mean': statistics.mean(
                row['fraction_active_gt_1p40'] for row in rows),
            'fraction_active_gt_1p40_final': rows[-1]['fraction_active_gt_1p40'],
        },
    }


def run_self_test():
    header = ('# ' + COLUMNS + '\n# stickers=4 dt=1 total_requested_steps=4\n')
    rows = (
        '0 0 4 0 0 0 0 0 0 2 1 .5 0 0 0 0 0 0 0 0 0\n'
        '1 1 2 1 1 0 0 1 .5 1 2 1 1 1 0 0 1 1 0 0 0\n'
        '2 2 2 1 1 0 0 1 .5 1 2 1 1 1 0 0 2 1.1 0 0 0\n'
        '3 3 4 0 1 1 0 0 0 2 1 .5 0 0 0 0 2 1.1 0 0 0\n'
        '4 4 4 0 1 1 0 0 0 2 1 .5 0 0 0 0 2 1.1 0 0 0\n')
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as state_file:
        state_file.write(header + rows)
        state_file.flush()
        _, parsed = read_state(state_file.name)
        report = describe(parsed, 2)
        if report['sample_count'] != 5 or report['event_balance']['net_bond_change'] != 0:
            raise AssertionError('E2 parsing or event balance regression failed')
        if report['sampling_interval'] != 1.0:
            raise AssertionError('sampling interval regression failed')
        if not math.isfinite(report['metrics']['bound_fraction']['integrated_autocorrelation_time']):
            raise AssertionError('E2 autocorrelation regression failed')
        long_rows = []
        for index in range(2001):
            row = parsed[0].copy()
            row['step'] = index
            row['time'] = 0.25 * index
            long_rows.append(row)
        if [len(block) for block in block_values(range(2001), 5)] != [400, 400, 400, 400, 401]:
            raise AssertionError('equal-sized block partition regression failed')
        long_report = describe(long_rows, 5)
        if len(long_report['metrics']['bound_fraction']['block_means']) != 5:
            raise AssertionError('2001-sample block count regression failed')
        if not math.isclose(long_report['sampling_interval'], 0.25):
            raise AssertionError('physical diagnostic interval regression failed')
        if not math.isclose(
                long_report['metrics']['bound_fraction']['integrated_autocorrelation_time'],
                0.125):
            raise AssertionError('physical IAT conversion regression failed')
        nonuniform_tau, nonuniform_effective = iat([0.0, 1.0, 0.0], [0.0, 1.0, 3.0])
        if not math.isnan(nonuniform_tau) or not math.isnan(nonuniform_effective):
            raise AssertionError('nonuniform autocorrelation handling regressed')
        with open(state_file.name, 'w', encoding='utf-8') as malformed:
            malformed.write(header + rows.replace('1 1 2 1', '1 1 3 1'))
        try:
            read_state(state_file.name)
            raise AssertionError('malformed E2 invariant was accepted')
        except ValueError:
            pass
    print('E2 ANALYZER SELF_TEST PASS parsing, blocks, trends, autocorrelation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('state_file', nargs='?')
    parser.add_argument('--blocks', type=int, default=5)
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()
    if arguments.self_test:
        run_self_test()
        return
    if arguments.blocks < 1:
        parser.error('--blocks must be positive')
    if not arguments.state_file:
        parser.error('state_file is required unless --self-test is used')
    metadata, rows = read_state(arguments.state_file)
    report = describe(rows, arguments.blocks)
    report['metadata'] = metadata
    json.dump(report, sys.stdout, indent=2, allow_nan=True)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
