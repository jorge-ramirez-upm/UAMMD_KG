#!/usr/bin/env python3
"""Windowed, two-replica diagnostics for the P4.2 rheology pilot."""

import argparse
import csv
import json
import math
import statistics
import tempfile


CHANNELS = ('Gxy', 'Gxz', 'Gyz', 'GNxy', 'GNxz', 'GNyz')
LEGACY_HEADER = '# time Gxy Gxz Gyz GNxy GNxz GNyz G'
COUNT_HEADER = LEGACY_HEADER + ' n_pairs'
NONZERO = 'resolved_nonzero_tail_or_plateau'
ZERO = 'resolved_decay_to_zero'
UNRESOLVED = 'unresolved_tail'


def fail(path, message):
    raise ValueError('{}: {}'.format(path, message))


def read_companion_temperature(path):
    state_path = path[:-len('.stress_correlator')] + '.state'
    try:
        with open(state_path, encoding='utf-8') as state_file:
            for line in state_file:
                if line.startswith('#'):
                    for token in line[1:].split():
                        if token.startswith('T='):
                            temperature = float(token[2:])
                            if temperature > 0.0 and math.isfinite(temperature):
                                return temperature
    except OSError as error:
        raise ValueError('{}: missing companion state file {}'.format(path, state_path)) from error
    fail(path, 'missing valid T provenance in {}'.format(state_path))


def read_stress_correlator(path):
    metadata = {}
    rows = []
    with open(path, encoding='utf-8') as input_file:
        lines = [line.strip() for line in input_file if line.strip()]
    if len(lines) < 3 or not lines[0].startswith('# stress_samples='):
        fail(path, 'missing stress provenance header')
    for token in lines[0][1:].split():
        if '=' in token:
            key, value = token.split('=', 1)
            metadata[key] = value
    if metadata.get('step0_sampled') != 'no' or metadata.get('stress_interval_steps') != '1':
        fail(path, 'unexpected stress sampling convention')
    try:
        metadata['stress_samples'] = int(metadata['stress_samples'])
        metadata['dt'] = float(metadata['dt'])
    except (KeyError, ValueError) as error:
        raise ValueError('{}: invalid stress provenance'.format(path)) from error
    if metadata['stress_samples'] <= 0 or metadata['dt'] <= 0.0:
        fail(path, 'nonpositive stress provenance')
    metadata['temperature'] = read_companion_temperature(path)
    if lines[1] == COUNT_HEADER:
        metadata['support_mode'] = 'exact_n_pairs'
        expected_columns = 9
    elif lines[1] == LEGACY_HEADER:
        metadata['support_mode'] = 'legacy_fixed_lag_fraction'
        expected_columns = 8
    else:
        fail(path, 'unexpected stress columns')
    previous_time = -math.inf
    for line in lines[2:]:
        fields = line.split()
        if len(fields) != expected_columns:
            fail(path, 'unexpected stress column count')
        try:
            values = [float(field) for field in fields[:8]]
        except ValueError as error:
            raise ValueError('{}: invalid stress row {}'.format(path, line)) from error
        if not all(math.isfinite(value) for value in values):
            fail(path, 'nonfinite stress value')
        if values[0] <= previous_time:
            fail(path, 'lag times are not strictly increasing')
        previous_time = values[0]
        if expected_columns == 9:
            try:
                n_pairs = int(fields[8])
            except ValueError as error:
                raise ValueError('{}: invalid n_pairs {}'.format(path, fields[8])) from error
            if n_pairs <= 0 or str(n_pairs) != fields[8]:
                fail(path, 'n_pairs must be a positive integer')
        else:
            n_pairs = None
        contributions = dict(zip(CHANNELS, values[1:7]))
        recomputed = ((contributions['Gxy'] + contributions['Gxz'] + contributions['Gyz']) /
                      (5.0 * metadata['temperature']) +
                      (contributions['GNxy'] + contributions['GNxz'] + contributions['GNyz']) /
                      (30.0 * metadata['temperature']))
        if not math.isclose(recomputed, values[7], rel_tol=2e-10, abs_tol=2e-12):
            fail(path, 'six-channel modulus does not match reported G')
        contributions.update(time=values[0], G=recomputed, n_pairs=n_pairs)
        rows.append(contributions)
    if not rows:
        fail(path, 'no stress rows')
    return metadata, rows


def require_matching_lags(replicas):
    reference = replicas[0]['rows']
    support_mode = replicas[0]['metadata']['support_mode']
    for replica in replicas[1:]:
        if (replica['metadata']['dt'] != replicas[0]['metadata']['dt'] or
                replica['metadata']['temperature'] != replicas[0]['metadata']['temperature']):
            fail(replica['path'], 'replica physical provenance differs')
        if replica['metadata']['support_mode'] != support_mode:
            fail(replica['path'], 'cannot mix exact and legacy support formats')
        if len(replica['rows']) != len(reference):
            fail(replica['path'], 'replica has different lag-bin count')
        for expected, actual in zip(reference, replica['rows']):
            if not math.isclose(expected['time'], actual['time'], rel_tol=1e-12,
                                abs_tol=1e-12):
                fail(replica['path'], 'replica lag bins differ')
            if expected['n_pairs'] != actual['n_pairs']:
                fail(replica['path'], 'replica support counts differ')


def linear_slope(times, values):
    mean_time = statistics.mean(times)
    mean_value = statistics.mean(values)
    denominator = sum((time - mean_time) ** 2 for time in times)
    if denominator == 0.0:
        return 0.0
    return sum((time - mean_time) * (value - mean_value)
               for time, value in zip(times, values)) / denominator


def window_diagnostic(replicas, start, end, z_threshold, eligible, support_threshold):
    values = [[row['G'] for row in replica['rows'][start:end + 1]]
              for replica in replicas]
    replica_means = [statistics.mean(series) for series in values]
    window_mean = statistics.mean(replica_means)
    disagreement = (statistics.stdev(replica_means) / math.sqrt(len(replica_means))
                    if len(replica_means) > 1 else math.inf)
    residuals = [value - replica_mean
                 for series, replica_mean in zip(values, replica_means)
                 for value in series]
    local_scatter = (math.sqrt(statistics.mean(value * value for value in residuals)) /
                     math.sqrt(len(values) * len(values[0]))
                     if residuals else math.inf)
    noise_scale = max(disagreement, local_scatter)
    signal_to_noise = (abs(window_mean) / noise_scale if noise_scale > 0.0
                       else (0.0 if window_mean == 0.0 else math.inf))
    replica_consistent = disagreement <= z_threshold * max(local_scatter, 1e-15)
    replica_agreement = max(
        0.0, 1.0 - disagreement / max(abs(window_mean) + local_scatter, 1e-15))
    bin_means = [statistics.mean(replica['rows'][index]['G'] for replica in replicas)
                 for index in range(start, end + 1)]
    sign_matches = sum(value == 0.0 or value * window_mean > 0.0 for value in bin_means)
    times = [replicas[0]['rows'][index]['time'] for index in range(start, end + 1)]
    trend = linear_slope(times, bin_means)
    trend_change = trend * (times[-1] - times[0])
    flat = abs(trend_change) <= z_threshold * noise_scale
    if not eligible:
        classification = UNRESOLVED
    elif signal_to_noise >= z_threshold and sign_matches / len(bin_means) >= 0.8 and replica_consistent:
        classification = NONZERO
    elif signal_to_noise < z_threshold and flat and replica_consistent:
        classification = ZERO
    else:
        classification = UNRESOLVED
    supports = [replicas[0]['rows'][index]['n_pairs'] for index in range(start, end + 1)]
    return {
        'start': times[0], 'end': times[-1], 'bin_count': len(bin_means),
        'mean_g': window_mean, 'noise_scale': noise_scale,
        'signal_to_noise': signal_to_noise,
        'sign_agreement': sign_matches / len(bin_means),
        'replica_agreement': replica_agreement, 'replica_consistent': replica_consistent,
        'trend': trend, 'trend_change': trend_change, 'classification': classification,
        'support_eligible': eligible, 'support_threshold': support_threshold,
        'min_n_pairs': min(supports) if supports[0] is not None else None,
        'median_n_pairs': statistics.median(supports) if supports[0] is not None else None,
    }


def classify_tail(replicas, legacy_reliable_fraction, window_bins, z_threshold,
                  min_support_count=8, min_support_fraction=1.0e-5):
    require_matching_lags(replicas)
    rows = replicas[0]['rows']
    maximum_time = rows[-1]['time']
    support_mode = replicas[0]['metadata']['support_mode']
    if support_mode == 'exact_n_pairs':
        reference_support = max(row['n_pairs'] for row in rows)
        support_threshold = max(min_support_count,
                                math.ceil(min_support_fraction * reference_support))
        eligible = [row['n_pairs'] >= support_threshold for row in rows]
        nonzero = [row for row in rows if row['n_pairs'] > 0]
        max_nonzero_lag = nonzero[-1]['time'] if nonzero else None
        support_rule = ('n_pairs >= max({}, ceil({} * {})) = {}'
                        .format(min_support_count, min_support_fraction,
                                reference_support, support_threshold))
    else:
        support_threshold = None
        reference_support = None
        limit = legacy_reliable_fraction * maximum_time
        eligible = [row['time'] <= limit for row in rows]
        max_nonzero_lag = None
        support_rule = 'legacy: time <= {} * max_lag_time'.format(legacy_reliable_fraction)
    windows = []
    for start in range(len(rows) - window_bins + 1):
        end = start + window_bins - 1
        windows.append(window_diagnostic(
            replicas, start, end, z_threshold, all(eligible[start:end + 1]), support_threshold))
    selected = [window for window in windows if window['support_eligible']]
    reliable_times = [row['time'] for row, is_eligible in zip(rows, eligible) if is_eligible]
    last = selected[-1] if selected else None
    classified = [window for window in selected if window['classification'] != UNRESOLVED]
    resolved_max = max((window['end'] for window in classified), default=None)
    if last is None:
        recommendation_type = 'longer_trajectory_and_more_replicas'
        next_action = 'increase support and add seeds; no late window meets the support rule'
        tail_classification = UNRESOLVED
    elif last['classification'] == NONZERO:
        recommendation_type = 'longer_trajectory_and_more_replicas'
        next_action = 'extend the trajectory; a persistent nonzero tail is not duration-resolved'
        tail_classification = NONZERO
    elif last['classification'] == ZERO:
        recommendation_type = 'more_replicas_before_production'
        next_action = 'tail is locally zero-compatible; confirm with more independent seeds'
        tail_classification = ZERO
    else:
        recommendation_type = 'longer_trajectory_and_more_replicas'
        next_action = 'extend lag support and add seeds; the weak tail is unresolved'
        tail_classification = UNRESOLVED
    tail = last or {}
    return windows, {
        'max_lag_time': maximum_time,
        'max_lag_with_nonzero_support': max_nonzero_lag,
        'reliable_max_lag_time': max(reliable_times) if reliable_times else None,
        'support_mode': support_mode,
        'support_reference_count': reference_support,
        'support_threshold': support_threshold,
        'support_rule': support_rule,
        'legacy_reliable_lag_fraction': (legacy_reliable_fraction
                                         if support_mode != 'exact_n_pairs' else None),
        'window_bins': window_bins, 'z_threshold': z_threshold,
        'tail_classification': tail_classification,
        'tail_window_start': tail.get('start'), 'tail_window_end': tail.get('end'),
        'tail_window_mean_g': tail.get('mean_g'),
        'tail_window_noise_scale': tail.get('noise_scale'),
        'tail_signal_to_noise': tail.get('signal_to_noise'),
        'tail_replica_agreement': tail.get('replica_agreement'),
        'tail_sign_agreement': tail.get('sign_agreement'),
        'tail_replica_consistent': tail.get('replica_consistent'),
        'tail_trend': tail.get('trend'),
        'tail_window_min_n_pairs': tail.get('min_n_pairs'),
        'tail_window_median_n_pairs': tail.get('median_n_pairs'),
        'resolved_max_lag_time': resolved_max,
        'recommendation_type': recommendation_type,
        'recommended_next_action': next_action,
        'needs_longer_trajectory': tail_classification != ZERO,
        'needs_more_independent_replicas': True,
        'statistical_caveat': ('Only two independent replicas are available; SEM and window labels '
                               'are rough pilot diagnostics, not final significance estimates.'),
        'support_caveat': (
            'n_pairs is the raw number of Correlator6 contributions, not an effective '
            'number of independent time origins.' if support_mode == 'exact_n_pairs' else
            'n_pairs is unavailable in this legacy eight-column file; the explicit fixed '
            'lag-fraction fallback is provisional.'),
    }


def write_outputs(prefix, replicas, windows, report):
    replica_path = prefix + '.replicas.csv'
    mean_path = prefix + '.mean.csv'
    window_path = prefix + '.windows.csv'
    report_path = prefix + '.summary.json'
    with open(replica_path, 'w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=('replica', 'source', 'time') + CHANNELS +
                                    ('G', 'n_pairs'))
        writer.writeheader()
        for replica_index, replica in enumerate(replicas, 1):
            for row in replica['rows']:
                writer.writerow(dict(row, replica=replica_index, source=replica['path']))
    with open(mean_path, 'w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=('time',) + CHANNELS + ('G', 'n_pairs'))
        writer.writeheader()
        for index, row in enumerate(replicas[0]['rows']):
            values = {channel: statistics.mean(replica['rows'][index][channel]
                                                for replica in replicas)
                      for channel in CHANNELS + ('G',)}
            writer.writerow(dict(values, time=row['time'], n_pairs=row['n_pairs']))
    with open(window_path, 'w', newline='', encoding='utf-8') as output:
        fields = tuple(windows[0])
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(windows)
    with open(report_path, 'w', encoding='utf-8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write('\n')
    return replica_path, mean_path, window_path, report_path


def synthetic_replicas(values_a, values_b, support=None):
    support = support or [None] * len(values_a)
    mode = 'exact_n_pairs' if support[0] is not None else 'legacy_fixed_lag_fraction'
    replicas = []
    for replica_index, values in enumerate((values_a, values_b)):
        replicas.append({
            'path': 'synthetic{}'.format(replica_index),
            'metadata': {'dt': 0.01, 'temperature': 1.0, 'stress_samples': len(values),
                         'support_mode': mode},
            'rows': [{'time': index, 'G': value, 'n_pairs': support[index]}
                     for index, value in enumerate(values)],
        })
    return replicas


def expect_classification(values_a, values_b, expected, label, support=None):
    _, report = classify_tail(synthetic_replicas(values_a, values_b, support), 1.0, 5, 2.0)
    if report['tail_classification'] != expected:
        raise AssertionError('{} classified as {}'.format(label, report['tail_classification']))


def check_new_format_parser():
    with tempfile.TemporaryDirectory() as directory:
        path = directory + '/pilot.stress_correlator'
        with open(directory + '/pilot.state', 'w', encoding='utf-8') as state_file:
            state_file.write('# T=1\n')
        with open(path, 'w', encoding='utf-8') as output:
            output.write('# stress_samples=10 step0_sampled=no stress_interval_steps=1 dt=0.01\n')
            output.write(COUNT_HEADER + '\n')
            output.write('0 0 0 0 0 0 0 0 10\n')
        metadata, rows = read_stress_correlator(path)
        if metadata['support_mode'] != 'exact_n_pairs' or rows[0]['n_pairs'] != 10:
            raise AssertionError('new-format stress-correlator parser failed')


def self_test():
    expect_classification([10, 3, 1, .01, .001, .001, .001, .001],
                          [10.1, 2.9, 1.1, .0011, .0009, .001, .0011, .0009],
                          NONZERO, 'weak plateau')
    expect_classification([10, 3, 1, .01, 0, 0, 0, 0, 0, 0],
                          [10, 3, 1, .01, 0, 0, 0, 0, 0, 0], ZERO, 'zero tail')
    expect_classification([10, 3, 1, .01, .1, .1, .1, .1],
                          [10.1, 2.9, 1.1, -.01, -.1, -.1, -.1, -.1],
                          UNRESOLVED, 'unresolved tail')
    windows, _ = classify_tail(synthetic_replicas([10, 3, 1, .01, .1, .1, 0, .1],
                                                   [10, 3, 1, .01, -.1, -.1, 0, -.1]),
                               1.0, 5, 2.0)
    if len(windows) != 4 or windows[-1]['classification'] != UNRESOLVED:
        raise AssertionError('isolated low-SEM bin became a tail classification')
    _, report = classify_tail(synthetic_replicas([10, 3, 1, .1, .08, .06, .04, .02],
                                                 [10.1, 2.9, 1.1, .11, .09, .07, .05, .03]),
                             1.0, 5, 2.0)
    if report['recommendation_type'] != 'longer_trajectory_and_more_replicas':
        raise AssertionError('persistent slow decay did not request a longer trajectory')
    plateau_a = [10, 3, 1, .01, .001, .001, .001, .001]
    plateau_b = [10.1, 2.9, 1.1, .0011, .0009, .001, .0011, .0009]
    expect_classification(plateau_a, plateau_b, UNRESOLVED, 'under-supported plateau',
                          [100, 100, 100, 2, 2, 2, 2, 2])
    expect_classification(plateau_a, plateau_b, NONZERO, 'supported plateau', [100] * 8)
    check_new_format_parser()
    print('P4.2 RHEOLOGY PILOT ANALYZER SELF_TEST PASS seven synthetic/parser regimes')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stress_files', nargs='*')
    parser.add_argument('--output-prefix')
    parser.add_argument('--reliable-fraction', type=float, default=0.75,
                        help='legacy eight-column fallback only')
    parser.add_argument('--min-support-count', type=int, default=8)
    parser.add_argument('--min-support-fraction', type=float, default=1.0e-5)
    parser.add_argument('--window-bins', type=int, default=5)
    parser.add_argument('--z-threshold', type=float, default=2.0)
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if len(arguments.stress_files) < 2:
        parser.error('at least two independent-replica stress files are required')
    if not arguments.output_prefix:
        parser.error('--output-prefix is required')
    if (not 0.0 < arguments.reliable_fraction <= 1.0 or arguments.window_bins < 3 or
            arguments.z_threshold <= 0.0 or arguments.min_support_count < 1 or
            not 0.0 <= arguments.min_support_fraction <= 1.0):
        parser.error('invalid support or window parameters')
    replicas = []
    for path in arguments.stress_files:
        metadata, rows = read_stress_correlator(path)
        replicas.append({'path': path, 'metadata': metadata, 'rows': rows})
    windows, report = classify_tail(replicas, arguments.reliable_fraction,
                                    arguments.window_bins, arguments.z_threshold,
                                    arguments.min_support_count,
                                    arguments.min_support_fraction)
    report['replicas'] = len(replicas)
    report['g0_mean'] = statistics.mean(replica['rows'][0]['G'] for replica in replicas)
    output_paths = write_outputs(arguments.output_prefix, replicas, windows, report)
    print('P4.2 rheology pilot analysis written: {}'.format(', '.join(output_paths)))
    print('tail_classification={}'.format(report['tail_classification']))
    print('recommended_next_action={}'.format(report['recommended_next_action']))


if __name__ == '__main__':
    main()
