#!/usr/bin/env python3.11
"""Selected-lag isotropic self F_s(q,t) for independently run star COM segments."""

import argparse
import csv
import json
import math

import numpy as np

import correlator

from analyze_p44_com_diffusion import read_com_trajectory, validate_replica_ensemble


Q_VALUES = np.array([
    0.1,
    0.177827941,
    0.316227766,
    0.562341325,
    1.0,
    1.778279410,
    3.162277660,
    5.623413252,
    10.0,
])


def multi_tau_fsqt(positions, q_values=Q_VALUES):
    """Average the package's isotropic self correlator over star IDs."""
    lag_reference = None
    count_reference = None
    total = None
    for star in range(positions.shape[1]):
        estimator = correlator.SqtCorrelatorIsotropicManyQ(20, 16, 2)
        estimator.set_q(q_values)
        estimator.add_many(positions[:, star, :])
        lag, values, count = estimator.evaluate()
        if lag_reference is None:
            lag_reference = lag
            count_reference = count
            total = np.zeros_like(values)
        elif not (np.array_equal(lag, lag_reference) and
                  np.array_equal(count, count_reference)):
            raise ValueError('SqtCorrelatorIsotropicManyQ returned inconsistent lag grids')
        total += values
    return lag_reference.astype(np.int64), total / positions.shape[1], count_reference


def repeated_single_q_fsqt(positions, q_values):
    values = []
    lag_reference = None
    count_reference = None
    for q_value in q_values:
        total = None
        for star in range(positions.shape[1]):
            estimator = correlator.SqtCorrelatorIsotropic(20, 16, 2)
            estimator.set_q(float(q_value))
            estimator.add_many(positions[:, star, :])
            lag, result, count = estimator.evaluate()
            if lag_reference is None:
                lag_reference = lag
                count_reference = count
            elif not (np.array_equal(lag, lag_reference) and
                      np.array_equal(count, count_reference)):
                raise AssertionError('single-q Sqt output grid mismatch')
            if total is None:
                total = np.zeros_like(result)
            total += result
        values.append(total / positions.shape[1])
    return lag_reference.astype(np.int64), np.column_stack(values), count_reference


def validate_synthetic_fsqt():
    q_values = np.array([0.2, 1.0])
    static = np.zeros((64, 3, 3))
    _, values, _ = multi_tau_fsqt(static, q_values)
    if not np.array_equal(values, np.ones_like(values)):
        raise AssertionError('static F_s(q,t) is not one')

    velocity = np.array([1.0, -2.0, .5])
    ballistic = np.arange(64.0)[:, None, None] * velocity[None, None, :]
    lag, values, _ = multi_tau_fsqt(ballistic, q_values)
    expected = np.sinc(np.outer(lag, q_values) * np.linalg.norm(velocity) / math.pi)
    if not np.allclose(values, expected, rtol=1e-12, atol=1e-12):
        raise AssertionError('ballistic isotropic F_s(q,t) mismatch')

    rng = np.random.default_rng(12001)
    diffusion = .05
    brownian = np.cumsum(
        rng.normal(scale=math.sqrt(2.0 * diffusion), size=(64, 128, 3)), axis=0)
    lag, values, _ = multi_tau_fsqt(brownian, q_values)
    expected = np.exp(-diffusion * np.outer(lag[:16], q_values * q_values))
    if not np.allclose(values[:16], expected, atol=.06):
        raise AssertionError('Brownian F_s(q,t) is inconsistent with exp(-D q^2 t)')


def validate_real_slice(positions):
    short_slice = positions[:64, :4, :]
    lag_many, values_many, count_many = multi_tau_fsqt(short_slice, Q_VALUES)
    lag_single, values_single, count_single = repeated_single_q_fsqt(short_slice, Q_VALUES)
    if not (np.array_equal(lag_many, lag_single) and
            np.array_equal(count_many, count_single) and
            np.allclose(values_many, values_single, rtol=1e-12, atol=1e-12)):
        raise AssertionError('C1 ManyQ and repeated single-q F_s(q,t) mismatch')


def crossings(times, values):
    result = {}
    for level in (.8, .5, 1.0 / math.e, .2):
        selected = np.flatnonzero((times > 0.0) & (values <= level))
        result[str(level)] = float(times[selected[0]]) if len(selected) else None
    return result


def write_outputs(prefix, replica_rows, mean_rows, summary):
    paths = (
        prefix + '.fsqt.replicas.csv',
        prefix + '.fsqt.mean.csv',
        prefix + '.fsqt.summary.json',
    )
    for path, rows, fields in (
            (paths[0], replica_rows,
             ('replica', 'source', 'q', 'lag_frames', 'lag_time', 'fsqt',
              'time_origins_per_star', 'star_time_origin_pairs')),
            (paths[1], mean_rows,
             ('q', 'lag_frames', 'lag_time', 'fsqt_mean', 'fsqt_sample_std', 'fsqt_sem',
              'time_origins_per_star', 'star_time_origin_pairs'))):
        with open(path, 'w', newline='', encoding='utf-8') as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    with open(paths[2], 'w', encoding='utf-8') as output:
        json.dump(summary, output, indent=2)
        output.write('\n')
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('com_files', nargs='*')
    parser.add_argument('--output-prefix')
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()
    if arguments.self_test:
        validate_synthetic_fsqt()
        print('P4.4 COM F_S(Q,T) SELF_TEST PASS')
        return
    if not arguments.output_prefix:
        parser.error('--output-prefix is required')
    if len(arguments.com_files) < 2:
        parser.error('at least two independent COM trajectories are required')

    replicas = []
    for path in arguments.com_files:
        steps, times, positions = read_com_trajectory(path)
        replicas.append({'path': path, 'steps': steps, 'times': times, 'positions': positions})
    first = validate_replica_ensemble(replicas)
    validate_synthetic_fsqt()
    validate_real_slice(first['positions'])

    lag_frames = None
    origin_counts = None
    all_values = []
    replica_rows = []
    sample_interval = first['times'][1] - first['times'][0]
    for replica_index, replica in enumerate(replicas, 1):
        lags, values, counts = multi_tau_fsqt(replica['positions'])
        if lag_frames is None:
            lag_frames = lags
            origin_counts = counts
        elif not (np.array_equal(lags, lag_frames) and np.array_equal(counts, origin_counts)):
            raise ValueError('{}: multi-tau output grid differs'.format(replica['path']))
        all_values.append(values)
        for q_index, q_value in enumerate(Q_VALUES):
            for lag, value, count in zip(lags, values[:, q_index], counts):
                replica_rows.append({
                    'replica': replica_index,
                    'source': replica['path'],
                    'q': float(q_value),
                    'lag_frames': int(lag),
                    'lag_time': float(lag * sample_interval),
                    'fsqt': float(value),
                    'time_origins_per_star': int(count),
                    'star_time_origin_pairs': int(count * first['positions'].shape[1]),
                })
    all_values = np.asarray(all_values)
    lag_times = lag_frames * sample_interval
    mean_values = np.mean(all_values, axis=0)
    mean_rows = []
    q_diagnostics = []
    for q_index, q_value in enumerate(Q_VALUES):
        for index, lag in enumerate(lag_frames):
            values = all_values[:, index, q_index]
            sample_std = float(np.std(values, ddof=1))
            mean_rows.append({
                'q': float(q_value),
                'lag_frames': int(lag),
                'lag_time': float(lag_times[index]),
                'fsqt_mean': float(mean_values[index, q_index]),
                'fsqt_sample_std': sample_std,
                'fsqt_sem': sample_std / math.sqrt(len(replicas)),
                'time_origins_per_star': int(origin_counts[index]),
                'star_time_origin_pairs': int(origin_counts[index] * first['positions'].shape[1]),
            })
        values = mean_values[:, q_index]
        replica_std = np.std(all_values[:, :, q_index], axis=0, ddof=1)
        q_diagnostics.append({
            'q': float(q_value),
            'first_positive_lag_time': float(lag_times[1]),
            'fsqt_first_positive_lag': float(values[1]),
            'fsqt_first_positive_lag_sample_std': float(replica_std[1]),
            'fsqt_last_lag': float(values[-1]),
            'fsqt_last_lag_sample_std': float(replica_std[-1]),
            'minimum_fsqt': float(np.min(values)),
            'crossing_times': crossings(lag_times, values),
            'appreciably_decayed': bool(np.min(values) <= .8),
            'high_q_decay_before_first_positive_lag': bool(values[1] <= .2),
        })
    summary = {
        'method': 'isotropic self F_s(q,t) = mean sinc(q |Delta R|) over stars',
        'implementation': 'correlator.SqtCorrelatorIsotropicManyQ(20, 16, 2)',
        'q_values': [float(value) for value in Q_VALUES],
        'all_time_origins': False,
        'selected_lag_origin_semantics': (
            'per-star multi-tau origin count; not an independent-sample count'),
        'replicas': len(replicas),
        'frames_per_replica': int(first['positions'].shape[0]),
        'stars_per_replica': int(first['positions'].shape[1]),
        'com_sampling_interval': float(sample_interval),
        'input_trajectories': [replica['path'] for replica in replicas],
        'segment_step_range': [int(first['steps'][0]), int(first['steps'][-1])],
        'segment_time_range': [float(first['times'][0]), float(first['times'][-1])],
        'q_diagnostics': q_diagnostics,
        'msd_diffusion_comparison': 'omitted: P4.4 has not established terminal diffusion',
        'validation': 'static, ballistic, Brownian, and C1 ManyQ/single-q checks passed',
    }
    paths = write_outputs(arguments.output_prefix, replica_rows, mean_rows, summary)
    print('P4.4 COM F_s(q,t) analysis written: {}'.format(', '.join(paths)))


if __name__ == '__main__':
    main()
