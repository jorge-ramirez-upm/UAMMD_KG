#!/usr/bin/env python3
"""Windowed independent-replica diagnostics for the P4.2 rheology pilot."""

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
STUDENT_T_95 = (12.706205, 4.302653, 3.182446, 2.776445, 2.570582,
                2.446912, 2.364624, 2.306004, 2.262157, 2.228139,
                2.200985, 2.178813, 2.160369, 2.144787, 2.131450,
                2.119905, 2.109816, 2.100922, 2.093024, 2.085963,
                2.079614, 2.073873, 2.068658, 2.063899, 2.059539,
                2.055529, 2.051831, 2.048407, 2.045230, 2.042272)
PERSISTENCE_WINDOWS = 3


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


def student_t_critical_95(degrees_of_freedom):
    """Two-sided 95% critical value; df>=30 uses conservative df=30 value."""
    if degrees_of_freedom < 1:
        raise ValueError('Student-t confidence interval requires at least two replicas')
    return STUDENT_T_95[min(degrees_of_freedom, len(STUDENT_T_95)) - 1]


def window_diagnostic(replicas, start, end, eligible, support_threshold):
    values = [[row['G'] for row in replica['rows'][start:end + 1]]
              for replica in replicas]
    replica_means = [statistics.mean(series) for series in values]
    window_mean = statistics.mean(replica_means)
    replica_std = statistics.stdev(replica_means)
    replica_sem = replica_std / math.sqrt(len(replica_means))
    critical_value = student_t_critical_95(len(replica_means) - 1)
    ci_half_width = critical_value * replica_sem
    ci_low = window_mean - ci_half_width
    ci_high = window_mean + ci_half_width
    signal_to_noise = (abs(window_mean) / replica_sem if replica_sem > 0.0
                       else (0.0 if window_mean == 0.0 else math.inf))
    bin_means = [statistics.mean(replica['rows'][index]['G'] for replica in replicas)
                 for index in range(start, end + 1)]
    times = [replicas[0]['rows'][index]['time'] for index in range(start, end + 1)]
    trend = linear_slope(times, bin_means)
    trend_change = trend * (times[-1] - times[0])
    trend_within_ci = abs(trend_change) <= ci_half_width
    zero_compatible = eligible and ci_low <= 0.0 <= ci_high and trend_within_ci
    nonzero_resolved = eligible and (ci_low > 0.0 or ci_high < 0.0) and trend_within_ci
    classification = NONZERO if nonzero_resolved else ZERO if zero_compatible else UNRESOLVED
    supports = [replicas[0]['rows'][index]['n_pairs'] for index in range(start, end + 1)]
    return {
        'start': times[0], 'end': times[-1], 'bin_count': len(bin_means),
        'mean_g': window_mean, 'replica_window_mean': window_mean,
        'replica_window_values': ';'.join('{:.17g}'.format(value)
                                          for value in replica_means),
        'replica_window_std': replica_std, 'replica_window_sem': replica_sem,
        'replica_window_ci_low': ci_low, 'replica_window_ci_high': ci_high,
        'replica_count': len(replica_means), 'student_t_critical_95': critical_value,
        'noise_scale': replica_sem,
        'signal_to_noise': signal_to_noise,
        'trend': trend, 'trend_change': trend_change, 'trend_within_ci': trend_within_ci,
        'zero_compatible': zero_compatible, 'nonzero_resolved': nonzero_resolved,
        'classification': classification,
        'support_eligible': eligible, 'support_threshold': support_threshold,
        'min_n_pairs': min(supports) if supports[0] is not None else None,
        'median_n_pairs': statistics.median(supports) if supports[0] is not None else None,
    }


def sustained_regions(windows, key, require_same_sign=False):
    """Return runs of at least PERSISTENCE_WINDOWS qualifying overlapping windows."""
    regions = []
    start = None
    sign = None
    for index, window in enumerate(windows + [None]):
        qualifies = window is not None and window[key]
        current_sign = (1 if window['mean_g'] > 0.0 else -1) if qualifies else None
        if qualifies and (start is None or not require_same_sign or current_sign == sign):
            if start is None:
                start, sign = index, current_sign
            continue
        if start is not None and index - start >= PERSISTENCE_WINDOWS:
            regions.append((start, index - 1))
        start = index if qualifies else None
        sign = current_sign if qualifies else None
    return regions


def classify_tail(replicas, legacy_reliable_fraction, window_bins,
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
            replicas, start, end, all(eligible[start:end + 1]), support_threshold))
    selected = [window for window in windows if window['support_eligible']]
    reliable_times = [row['time'] for row, is_eligible in zip(rows, eligible) if is_eligible]
    zero_regions = sustained_regions(selected, 'zero_compatible')
    nonzero_regions = sustained_regions(selected, 'nonzero_resolved', require_same_sign=True)
    for start, end in zero_regions:
        for window in selected[start:end + 1]:
            window['sustained_zero_compatible'] = True
    for start, end in nonzero_regions:
        for window in selected[start:end + 1]:
            window['sustained_nonzero_resolved'] = True
    for window in windows:
        window.setdefault('sustained_zero_compatible', False)
        window.setdefault('sustained_nonzero_resolved', False)
    last = selected[-1] if selected else None
    last_zero = zero_regions[-1] if zero_regions else None
    last_nonzero = nonzero_regions[-1] if nonzero_regions else None
    first_zero = zero_regions[0] if zero_regions else None
    later_nonzero = (first_zero is not None and
                     any(start > first_zero[1] for start, _ in nonzero_regions))
    if last is None:
        recommendation_type = 'longer_trajectory_and_more_replicas'
        next_action = 'increase support and add seeds; no late window meets the support rule'
        tail_classification = UNRESOLVED
    elif later_nonzero:
        recommendation_type = 'longer_trajectory_and_more_replicas'
        next_action = 'a later nonzero region follows zero-compatible windows; extend and add seeds'
        tail_classification = NONZERO
    elif last_zero is not None:
        recommendation_type = 'ready_for_production_design'
        next_action = 'relaxation is persistently compatible with the noise floor; design production precision'
        tail_classification = ZERO
    elif last_nonzero is not None:
        recommendation_type = 'longer_trajectory_and_more_replicas'
        next_action = 'a nonzero tail persists without a later zero-compatible region; extend before production'
        tail_classification = NONZERO
    else:
        recommendation_type = 'longer_trajectory_and_more_replicas'
        next_action = 'extend lag support and add seeds; the weak tail is unresolved'
        tail_classification = UNRESOLVED
    tail = last or {}
    last_zero_window = selected[last_zero[1]] if last_zero is not None else {}
    last_nonzero_window = selected[last_nonzero[1]] if last_nonzero is not None else {}
    return windows, {
        'max_lag_time': maximum_time,
        'max_lag_with_nonzero_support': max_nonzero_lag,
        'reliable_max_lag_time': max(reliable_times) if reliable_times else None,
        'last_eligible_window_start': tail.get('start'),
        'last_eligible_window_end': tail.get('end'),
        'support_mode': support_mode,
        'support_reference_count': reference_support,
        'support_threshold': support_threshold,
        'support_rule': support_rule,
        'legacy_reliable_lag_fraction': (legacy_reliable_fraction
                                         if support_mode != 'exact_n_pairs' else None),
        'window_bins': window_bins,
        'confidence_level': 0.95,
        'student_t_critical_value_policy': (
            'two-sided 95% Student-t; tabulated df=1..30, conservative df=30 for df>30'),
        'persistence_windows': PERSISTENCE_WINDOWS,
        'tail_classification': tail_classification,
        'tail_window_start': tail.get('start'), 'tail_window_end': tail.get('end'),
        'tail_window_mean_g': tail.get('mean_g'),
        'tail_window_noise_scale': tail.get('noise_scale'),
        'tail_window_ci_low': tail.get('replica_window_ci_low'),
        'tail_window_ci_high': tail.get('replica_window_ci_high'),
        'tail_replica_count': tail.get('replica_count'),
        'tail_signal_to_noise': tail.get('signal_to_noise'),
        'tail_trend': tail.get('trend'),
        'tail_window_min_n_pairs': tail.get('min_n_pairs'),
        'tail_window_median_n_pairs': tail.get('median_n_pairs'),
        'first_sustained_zero_compatible_window_start': (
            selected[first_zero[0]]['start'] if first_zero is not None else None),
        'first_sustained_zero_compatible_window_end': (
            selected[first_zero[0]]['end'] if first_zero is not None else None),
        'first_sustained_zero_compatible_confirmation_end': (
            selected[first_zero[0] + PERSISTENCE_WINDOWS - 1]['end']
            if first_zero is not None else None),
        'last_sustained_zero_compatible_window_start': (
            selected[last_zero[1]]['start'] if last_zero is not None else None),
        'last_sustained_zero_compatible_window_end': (
            selected[last_zero[1]]['end'] if last_zero is not None else None),
        'last_sustained_nonzero_window_start': (
            selected[last_nonzero[1]]['start'] if last_nonzero is not None else None),
        'last_sustained_nonzero_window_end': (
            selected[last_nonzero[1]]['end'] if last_nonzero is not None else None),
        'last_sustained_nonzero_window_mean_g': last_nonzero_window.get('mean_g'),
        'last_sustained_zero_window_mean_g': last_zero_window.get('mean_g'),
        'later_positive_excursion_replica_robust': later_nonzero,
        'recommendation_type': recommendation_type,
        'recommended_next_action': next_action,
        'needs_longer_trajectory': tail_classification != ZERO,
        'needs_more_independent_replicas': tail_classification != ZERO,
        'replicas': len(replicas),
        'statistical_caveat': ('{} independent replicas are available; SEM and window labels are '
                               'rough pilot diagnostics, not final significance estimates.'
                               .format(len(replicas))),
        'support_caveat': (
            'n_pairs is the raw number of Correlator6 contributions, not an effective '
            'number of independent time origins.' if support_mode == 'exact_n_pairs' else
            'n_pairs is unavailable in this legacy eight-column file; the explicit fixed '
            'lag-fraction fallback is provisional.'),
    }


def support_sensitivity(replicas, legacy_reliable_fraction, window_bins, thresholds):
    support_mode = replicas[0]['metadata']['support_mode']
    reports = []
    windows_by_threshold = []
    if support_mode == 'exact_n_pairs':
        for threshold in thresholds:
            windows, report = classify_tail(
                replicas, legacy_reliable_fraction, window_bins,
                threshold, 0.0)
            windows_by_threshold.append(windows)
            reports.append(report)
    else:
        windows, report = classify_tail(
            replicas, legacy_reliable_fraction, window_bins)
        windows_by_threshold.append(windows)
        reports.append(report)
    classifications = [report['tail_classification'] for report in reports]
    zero_confirmation_ends = [report['first_sustained_zero_compatible_confirmation_end']
                              for report in reports
                              if report['tail_classification'] == ZERO]
    zero_confirmation_end = min(zero_confirmation_ends, default=None)
    zero_support_limited = [
        zero_confirmation_end is not None and
        report['reliable_max_lag_time'] < zero_confirmation_end
        for report in reports]
    if len(set(classifications)) == 1 and classifications[0] == NONZERO:
        overall = 'robust_resolved_nonzero_tail'
    elif (zero_confirmation_end is not None and
          all(classification == ZERO or limited
              for classification, limited in zip(classifications, zero_support_limited))):
        overall = 'robust_resolved_decay_to_zero'
    elif len(set(classifications)) == 1 and classifications[0] == UNRESOLVED:
        overall = UNRESOLVED
    else:
        overall = 'support_sensitive_tail'
    sensitivity_rows = []
    for threshold, report in zip(
            thresholds if support_mode == 'exact_n_pairs' else [None], reports):
        sensitivity_rows.append({
            'support_threshold': threshold,
            'reliable_max_lag_time': report['reliable_max_lag_time'],
            'last_eligible_window_start': report['last_eligible_window_start'],
            'last_eligible_window_end': report['last_eligible_window_end'],
            'tail_window_start': report['tail_window_start'],
            'tail_window_end': report['tail_window_end'],
            'tail_classification': report['tail_classification'],
            'tail_window_mean_g': report['tail_window_mean_g'],
            'tail_window_noise_scale': report['tail_window_noise_scale'],
            'tail_window_ci_low': report['tail_window_ci_low'],
            'tail_window_ci_high': report['tail_window_ci_high'],
            'tail_replica_count': report['tail_replica_count'],
            'tail_signal_to_noise': report['tail_signal_to_noise'],
            'tail_replica_window_sem': report['tail_window_noise_scale'],
            'tail_trend': report['tail_trend'],
            'tail_window_min_n_pairs': report['tail_window_min_n_pairs'],
            'tail_window_median_n_pairs': report['tail_window_median_n_pairs'],
            'first_sustained_zero_compatible_window_start': (
                report['first_sustained_zero_compatible_window_start']),
            'first_sustained_zero_compatible_confirmation_end': (
                report['first_sustained_zero_compatible_confirmation_end']),
            'last_sustained_nonzero_window_end': report['last_sustained_nonzero_window_end'],
            'later_positive_excursion_replica_robust': (
                report['later_positive_excursion_replica_robust']),
            'zero_test_support_limited': zero_support_limited[len(sensitivity_rows)],
        })
    primary = dict(reports[0])
    primary['tail_classification'] = overall
    primary['support_threshold'] = None
    primary['support_rule'] = ('support sensitivity thresholds: ' +
                               ','.join(str(threshold) for threshold in thresholds)
                               if support_mode == 'exact_n_pairs' else
                               'legacy fixed lag-fraction fallback')
    primary['support_sensitivity'] = {
        'thresholds': thresholds if support_mode == 'exact_n_pairs' else [],
        'results': sensitivity_rows,
        'overall_interpretation': overall,
    }
    if overall == 'robust_resolved_decay_to_zero':
        primary['recommendation_type'] = 'ready_for_production_design'
        primary['recommended_next_action'] = (
            'tail is persistently compatible with the noise floor across support choices')
        primary['needs_longer_trajectory'] = False
        primary['needs_more_independent_replicas'] = False
    elif overall == 'robust_resolved_nonzero_tail':
        primary['recommendation_type'] = 'longer_trajectory_and_more_replicas'
        primary['recommended_next_action'] = (
            'a nonzero tail persists across support choices; extend before production')
        primary['needs_longer_trajectory'] = True
    else:
        primary['recommendation_type'] = 'longer_trajectory_and_more_replicas'
        primary['recommended_next_action'] = (
            'support choices do not give one robust tail conclusion; extend and add seeds')
        primary['needs_longer_trajectory'] = True
    return windows_by_threshold[0], primary, sensitivity_rows


def write_outputs(prefix, replicas, windows, report, sensitivity_rows):
    replica_path = prefix + '.replicas.csv'
    mean_path = prefix + '.mean.csv'
    window_path = prefix + '.windows.csv'
    sensitivity_path = prefix + '.support_sensitivity.csv'
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
    with open(sensitivity_path, 'w', newline='', encoding='utf-8') as output:
        fields = tuple(sensitivity_rows[0])
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sensitivity_rows)
    with open(report_path, 'w', encoding='utf-8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write('\n')
    return replica_path, mean_path, window_path, sensitivity_path, report_path


def synthetic_replicas(*series, support=None):
    if len(series) < 2:
        raise ValueError('at least two synthetic replicas are required')
    support = support or [None] * len(series[0])
    mode = 'exact_n_pairs' if support[0] is not None else 'legacy_fixed_lag_fraction'
    replicas = []
    for replica_index, values in enumerate(series):
        if len(values) != len(support):
            raise ValueError('synthetic replica length mismatch')
        replicas.append({
            'path': 'synthetic{}'.format(replica_index),
            'metadata': {'dt': 0.01, 'temperature': 1.0, 'stress_samples': len(values),
                         'support_mode': mode},
            'rows': [{'time': index, 'G': value, 'n_pairs': support[index]}
                     for index, value in enumerate(values)],
        })
    return replicas


def expect_classification(series, expected, label, support=None, window_bins=3):
    _, report = classify_tail(synthetic_replicas(*series, support=support),
                              1.0, window_bins)
    if report['tail_classification'] != expected:
        raise AssertionError('{} classified as {}'.format(label, report['tail_classification']))


def expect_sensitivity(series, expected, label, support, thresholds, window_bins=3):
    _, report, rows = support_sensitivity(
        synthetic_replicas(*series, support=support), 1.0, window_bins, thresholds)
    if report['tail_classification'] != expected:
        raise AssertionError('{} interpreted as {}'.format(label, report['tail_classification']))
    if len(rows) != len(thresholds):
        raise AssertionError('{} did not report every threshold'.format(label))


def five_series(values):
    return tuple([value + offset for value in values]
                 for offset in (-.0002, -.0001, 0.0, .0001, .0002))


def expect_five_replica_sensitivity():
    values = five_series([.01] * 8)
    _, report, _ = support_sensitivity(
        synthetic_replicas(*values, support=[64] * 8), 1.0, 3, [8, 16, 32, 64])
    if report['tail_classification'] != 'robust_resolved_nonzero_tail':
        raise AssertionError('five-replica plateau did not remain resolved')
    if report['replicas'] != 5 or not report['statistical_caveat'].startswith('5 independent'):
        raise AssertionError('five-replica metadata was not retained')


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
    if not math.isclose(student_t_critical_95(4), 2.776445, rel_tol=0.0, abs_tol=1e-12):
        raise AssertionError('Student-t critical-value table changed')
    nonzero = five_series([.01] * 8)
    expect_classification(nonzero, NONZERO, 'five-replica positive tail', [64] * 8)
    zero = ([.0002] * 8, [-.0001] * 8, [0.0] * 8, [.0001] * 8, [-.0002] * 8)
    expect_classification(zero, ZERO, 'mixed-sign zero-compatible tail', [64] * 8)
    _, outlier = classify_tail(synthetic_replicas(
        *([.001] * 8, [.001] * 8, [.001] * 8, [.001] * 8, [-.02] * 8), support=[64] * 8),
        1.0, 3)
    if outlier['tail_classification'] == NONZERO:
        raise AssertionError('outlier replica produced false nonzero certainty')
    transient = ([0, 0, 0, 0, 0, .01, .01, .01, .01, .01],
                 [0, 0, 0, 0, 0, .0101, .0101, .0101, .0101, .0101],
                 [0, 0, 0, 0, 0, .0099, .0099, .0099, .0099, .0099],
                 [0, 0, 0, 0, 0, .01, .01, .01, .01, .01],
                 [0, 0, 0, 0, 0, .01, .01, .01, .01, .01])
    expect_classification(transient, NONZERO, 'transient zero followed by nonzero tail', [64] * 10)
    expect_classification(zero, ZERO, 'sustained zero-compatible region', [64] * 8)
    late_outlier = ([0, 0, 0, 0, 0, .001, .001, .001, .001, .001],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    _, report = classify_tail(synthetic_replicas(*late_outlier, support=[64] * 10), 1.0, 3)
    if report['later_positive_excursion_replica_robust']:
        raise AssertionError('one-replica late excursion became robust')
    expect_sensitivity(nonzero, 'robust_resolved_nonzero_tail',
                       'stable moderate-support plateau', [64] * 8, [8, 16, 32, 64])
    expect_sensitivity(nonzero, UNRESOLVED,
                       'one-count apparent plateau', [2] * 8, [8, 16, 32, 64])
    expect_sensitivity(nonzero, 'support_sensitive_tail',
                       'threshold-sensitive plateau', [32] * 8, [8, 16, 32, 64])
    expect_five_replica_sensitivity()
    check_new_format_parser()
    print('P4.2 RHEOLOGY PILOT ANALYZER SELF_TEST PASS ten synthetic/parser regimes')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stress_files', nargs='*')
    parser.add_argument('--output-prefix')
    parser.add_argument('--reliable-fraction', type=float, default=0.75,
                        help='legacy eight-column fallback only')
    parser.add_argument('--min-support-count', type=int, default=8)
    parser.add_argument('--min-support-fraction', type=float, default=1.0e-5,
                        help='legacy single-threshold compatibility; exact files use the sweep')
    parser.add_argument('--support-thresholds', default='8,16,32,64,128',
                        help='comma-separated exact raw-support sensitivity thresholds')
    parser.add_argument('--window-bins', type=int, default=5)
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
            arguments.min_support_count < 1 or
            not 0.0 <= arguments.min_support_fraction <= 1.0):
        parser.error('invalid support or window parameters')
    try:
        support_thresholds = sorted(set(int(value) for value in
                                        arguments.support_thresholds.split(',')))
    except ValueError as error:
        parser.error('support thresholds must be positive integers')
    if not support_thresholds or support_thresholds[0] < 1:
        parser.error('support thresholds must be positive integers')
    replicas = []
    for path in arguments.stress_files:
        metadata, rows = read_stress_correlator(path)
        replicas.append({'path': path, 'metadata': metadata, 'rows': rows})
    windows, report, sensitivity_rows = support_sensitivity(
        replicas, arguments.reliable_fraction, arguments.window_bins, support_thresholds)
    report['replicas'] = len(replicas)
    report['g0_mean'] = statistics.mean(replica['rows'][0]['G'] for replica in replicas)
    output_paths = write_outputs(arguments.output_prefix, replicas, windows, report,
                                 sensitivity_rows)
    print('P4.2 rheology pilot analysis written: {}'.format(', '.join(output_paths)))
    print('tail_classification={}'.format(report['tail_classification']))
    print('recommended_next_action={}'.format(report['recommended_next_action']))


if __name__ == '__main__':
    main()
