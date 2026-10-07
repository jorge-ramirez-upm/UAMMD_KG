#!/usr/bin/env python3.11
"""Multi-tau star-COM MSD and limited long-time diffusion analysis."""

import argparse
import csv
import json
import math
import statistics

import numpy as np

import correlator


STUDENT_T_95_DF4 = 2.776445


def fail(path, message):
    raise ValueError('{}: {}'.format(path, message))


def read_com_trajectory(path):
    """Read one self-contained, temporally unwrapped COM output segment."""
    steps = []
    times = []
    frames = []
    current_step = None
    current_time = None
    current_ids = []
    current_positions = []

    def finish_frame():
        if not current_positions:
            return
        expected_ids = list(range(1, len(current_ids) + 1))
        if current_ids != expected_ids:
            fail(path, 'molecule IDs are not exactly ordered 1..Nstars')
        steps.append(current_step)
        times.append(current_time)
        frames.append(current_positions)

    with open(path, encoding='utf-8') as input_file:
        header = input_file.readline().strip()
        if header != '# step time molecule_id com_x com_y com_z':
            fail(path, 'unexpected COM header')
        for line in input_file:
            fields = line.split()
            if len(fields) != 6:
                fail(path, 'malformed COM row')
            step = int(fields[0])
            time = float(fields[1])
            molecule_id = int(fields[2])
            position = [float(value) for value in fields[3:]]
            if not all(math.isfinite(value) for value in (time, *position)):
                fail(path, 'nonfinite COM value')
            if current_step is None:
                current_step = step
                current_time = time
            if step != current_step:
                finish_frame()
                current_step = step
                current_time = time
                current_ids = []
                current_positions = []
            elif time != current_time:
                fail(path, 'inconsistent frame time')
            current_ids.append(molecule_id)
            current_positions.append(position)
    finish_frame()
    if len(frames) < 2:
        fail(path, 'fewer than two COM frames')
    if any(later <= earlier for earlier, later in zip(steps, steps[1:])):
        fail(path, 'nonincreasing COM steps')
    if any(later <= earlier for earlier, later in zip(times, times[1:])):
        fail(path, 'nonincreasing COM times')
    step_intervals = {later - earlier for earlier, later in zip(steps, steps[1:])}
    time_intervals = {later - earlier for earlier, later in zip(times, times[1:])}
    if len(step_intervals) != 1 or len(time_intervals) != 1:
        fail(path, 'nonuniform COM sampling interval')
    return np.asarray(steps), np.asarray(times), np.asarray(frames, dtype=np.float64)


def multi_tau_msd(positions):
    """Average the installed one-vector multi-tau estimator over star IDs."""
    lag_reference = None
    count_reference = None
    total = None
    for star in range(positions.shape[1]):
        estimator = correlator.DiffusionCorrelator(20, 16, 2)
        estimator.add_many(positions[:, star, :])
        lag, msd, count = estimator.evaluate()
        if lag_reference is None:
            lag_reference = lag
            count_reference = count
            total = np.zeros_like(msd)
        elif not (np.array_equal(lag, lag_reference) and np.array_equal(count, count_reference)):
            raise ValueError('DiffusionCorrelator returned inconsistent lag grids')
        total += msd
    return lag_reference.astype(np.int64), total / positions.shape[1], count_reference


def brute_force_msd(positions):
    values = []
    for lag in range(positions.shape[0]):
        if lag == 0:
            values.append(0.0)
        else:
            displacement = positions[lag:] - positions[:-lag]
            values.append(float(np.mean(np.sum(displacement * displacement, axis=2))))
    return np.asarray(values)


def validate_synthetic_correlator():
    """Focused exact checks for the selected-lag multi-tau estimator."""
    rng = np.random.default_rng(12001)
    brownian = np.cumsum(rng.normal(size=(64, 1, 3)), axis=0)
    multiple = np.cumsum(rng.normal(size=(64, 4, 3)), axis=0)
    for name, positions in (('brownian', brownian), ('multiple', multiple)):
        estimator = correlator.DiffusionCorrelator(1, 64, 2)
        estimator.add_many(positions[:, 0, :])
        lag, msd, _ = estimator.evaluate()
        reference = brute_force_msd(positions[:, :1, :])
        if not np.allclose(msd, reference[lag.astype(int)], rtol=1e-12, atol=1e-12):
            raise AssertionError('{} single-particle MSD mismatch'.format(name))
    lag, msd, _ = multi_tau_msd(multiple)
    reference = brute_force_msd(multiple)
    if not np.allclose(msd[:16], reference[lag[:16]], rtol=1e-12, atol=1e-12):
        raise AssertionError('multiple-particle fine-lag MSD mismatch')
    velocity = np.array([1.0, -2.0, .5])
    ballistic = np.arange(64.0)[:, None, None] * velocity[None, None, :]
    lag, msd, _ = multi_tau_msd(ballistic)
    if not np.allclose(msd, np.dot(velocity, velocity) * lag * lag, rtol=1e-12, atol=1e-12):
        raise AssertionError('ballistic selected-lag MSD mismatch')
    constant = np.ones((64, 3, 3))
    _, msd, _ = multi_tau_msd(constant)
    if not np.array_equal(msd, np.zeros_like(msd)):
        raise AssertionError('constant trajectory MSD is nonzero')
    regions = sustained_diffusive_regions(
        np.arange(8.0), np.array([np.nan, 1.01, .97, 1.04, .96, .8, .9, np.nan]), .05, 4)
    if regions != [{'start_time': 1.0, 'end_time': 4.0, 'lag_points': 4}]:
        raise AssertionError('diffusive-region detection mismatch')


def validate_correlator(actual_positions):
    validate_synthetic_correlator()
    short_slice = actual_positions[:64]
    lag, msd, _ = multi_tau_msd(short_slice)
    reference = brute_force_msd(short_slice)
    if not np.allclose(msd[:16], reference[lag[:16]], rtol=1e-12, atol=1e-12):
        raise AssertionError('C1 short-slice fine-lag MSD mismatch')


def local_log_slope(times, values):
    slopes = np.full(len(times), np.nan)
    for index in range(2, len(times) - 2):
        local_times = times[index - 2:index + 3]
        local_values = values[index - 2:index + 3]
        if np.all(local_times > 0.0) and np.all(local_values > 0.0):
            slopes[index] = np.polyfit(np.log(local_times), np.log(local_values), 1)[0]
    return slopes


def sustained_diffusive_regions(times, slopes, tolerance, minimum_bins):
    """Return contiguous local-slope regions compatible with diffusion."""
    regions = []
    start = None
    for index, slope in enumerate(slopes):
        is_diffusive = math.isfinite(slope) and abs(slope - 1.0) <= tolerance
        if is_diffusive and start is None:
            start = index
        if start is not None and (not is_diffusive or index == len(slopes) - 1):
            end = index if is_diffusive and index == len(slopes) - 1 else index - 1
            if end - start + 1 >= minimum_bins:
                regions.append({
                    'start_time': float(times[start]),
                    'end_time': float(times[end]),
                    'lag_points': end - start + 1,
                })
            start = None
    return regions


def fit_diffusion(times, msd, start, end):
    selected = (times >= start) & (times <= end)
    if np.count_nonzero(selected) < 3:
        raise ValueError('diffusion fit window has fewer than three lag points')
    design = np.column_stack((6.0 * times[selected], np.ones(np.count_nonzero(selected))))
    coefficient, _, _, _ = np.linalg.lstsq(design, msd[selected], rcond=None)
    return float(coefficient[0]), float(coefficient[1]), int(np.count_nonzero(selected))


def parse_windows(text):
    windows = []
    for token in text.split(','):
        start, end = (float(value) for value in token.split(':', 1))
        if not 0.0 < start < end:
            raise ValueError('fit windows must be start:end with 0 < start < end')
        windows.append((start, end))
    if not windows:
        raise ValueError('at least one diffusion fit window is required')
    return windows


def student_statistics(values):
    mean = statistics.mean(values)
    sample_std = statistics.stdev(values)
    sem = sample_std / math.sqrt(len(values))
    half_width = STUDENT_T_95_DF4 * sem
    return mean, sample_std, sem, mean - half_width, mean + half_width


def write_outputs(prefix, replica_rows, mean_rows, fit_rows, summary):
    paths = (prefix + '.diffusion.replicas.csv', prefix + '.diffusion.mean.csv',
             prefix + '.diffusion_fits.csv', prefix + '.diffusion.summary.json')
    for path, rows, fields in (
            (paths[0], replica_rows, ('replica', 'source', 'lag_frames', 'lag_time', 'msd',
                                      'time_origins_per_star', 'star_time_origin_pairs')),
            (paths[1], mean_rows, ('lag_frames', 'lag_time', 'msd_mean', 'msd_sample_std',
                                   'msd_sem', 'alpha', 'instantaneous_d',
                                   'time_origins_per_star', 'star_time_origin_pairs')),
            (paths[2], fit_rows, ('window_start', 'window_end', 'replica', 'diffusion',
                                  'intercept', 'lag_points'))):
        with open(path, 'w', newline='', encoding='utf-8') as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    with open(paths[3], 'w', encoding='utf-8') as output:
        json.dump(summary, output, indent=2)
        output.write('\n')
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('com_files', nargs='*')
    parser.add_argument('--output-prefix')
    parser.add_argument('--fit-windows', default='20000:80000,30000:100000,40000:120000')
    parser.add_argument('--alpha-tolerance', type=float, default=.1)
    parser.add_argument('--min-diffusive-bins', type=int, default=5)
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()
    if arguments.self_test:
        validate_synthetic_correlator()
        print('P4.4 COM DIFFUSION SELF_TEST PASS')
        return
    if not arguments.output_prefix:
        parser.error('--output-prefix is required')
    if len(arguments.com_files) != 5:
        parser.error('the C1 P4.4 analysis requires exactly five independent COM trajectories')
    if arguments.alpha_tolerance <= 0.0:
        parser.error('--alpha-tolerance must be positive')
    if arguments.min_diffusive_bins < 2:
        parser.error('--min-diffusive-bins must be at least two')
    try:
        windows = parse_windows(arguments.fit_windows)
    except ValueError as error:
        parser.error(str(error))

    replicas = []
    for path in arguments.com_files:
        steps, times, positions = read_com_trajectory(path)
        replicas.append({'path': path, 'steps': steps, 'times': times, 'positions': positions})
    first = replicas[0]
    for replica in replicas[1:]:
        if (replica['positions'].shape != first['positions'].shape or
                not np.array_equal(replica['steps'] - replica['steps'][0],
                                   first['steps'] - first['steps'][0]) or
                not np.allclose(replica['times'] - replica['times'][0],
                                first['times'] - first['times'][0])):
            fail(replica['path'], 'replica COM grid or star count differs')
    validate_correlator(first['positions'])

    replica_rows = []
    lag_frames = None
    counts = None
    all_msd = []
    for replica_index, replica in enumerate(replicas, 1):
        lags, msd, origin_counts = multi_tau_msd(replica['positions'])
        if lag_frames is None:
            lag_frames, counts = lags, origin_counts
        elif not (np.array_equal(lags, lag_frames) and np.array_equal(origin_counts, counts)):
            fail(replica['path'], 'multi-tau output grid differs')
        all_msd.append(msd)
        for lag, value, count in zip(lags, msd, origin_counts):
            replica_rows.append({
                'replica': replica_index, 'source': replica['path'], 'lag_frames': int(lag),
                'lag_time': float(lag * (first['times'][1] - first['times'][0])),
                'msd': float(value),
                'time_origins_per_star': int(count),
                'star_time_origin_pairs': int(count * first['positions'].shape[1]),
            })
    all_msd = np.asarray(all_msd)
    lag_times = lag_frames * (first['times'][1] - first['times'][0])
    mean_msd = np.mean(all_msd, axis=0)
    alpha = local_log_slope(lag_times, mean_msd)
    diffusive_regions = sustained_diffusive_regions(
        lag_times, alpha, arguments.alpha_tolerance, arguments.min_diffusive_bins)
    mean_rows = []
    for index, lag in enumerate(lag_frames):
        values = all_msd[:, index]
        sample_std = float(np.std(values, ddof=1))
        mean_rows.append({
            'lag_frames': int(lag), 'lag_time': float(lag_times[index]),
            'msd_mean': float(mean_msd[index]), 'msd_sample_std': sample_std,
            'msd_sem': sample_std / math.sqrt(len(replicas)), 'alpha': float(alpha[index]),
            'instantaneous_d': (float(mean_msd[index] / (6.0 * lag_times[index]))
                                if lag_times[index] > 0.0 else None),
            'time_origins_per_star': int(counts[index]),
            'star_time_origin_pairs': int(counts[index] * first['positions'].shape[1]),
        })
    fit_rows = []
    fit_summaries = []
    for start, end in windows:
        diffusion = []
        for replica_index, msd in enumerate(all_msd, 1):
            value, intercept, points = fit_diffusion(lag_times, msd, start, end)
            diffusion.append(value)
            fit_rows.append({'window_start': start, 'window_end': end, 'replica': replica_index,
                             'diffusion': value, 'intercept': intercept, 'lag_points': points})
        mean, sample_std, sem, ci_low, ci_high = student_statistics(diffusion)
        fit_summaries.append({
            'window_start': start, 'window_end': end, 'mean_d': mean,
            'sample_std': sample_std, 'sem': sem, 'ci_low': ci_low, 'ci_high': ci_high,
        })
    recommended = fit_summaries[len(fit_summaries) // 2]
    sensitivity = max(abs(item['mean_d'] - recommended['mean_d']) for item in fit_summaries)
    summary = {
        'method': 'installed correlator.DiffusionCorrelator multi-tau MSD averaged over stars',
        'multi_tau_parameters': {'num_correlators': 20, 'points_per_level': 16, 'binning': 2},
        'all_time_origins': False,
        'selected_lag_origin_semantics': (
            'per-star multi-tau origin count; not an independent-sample count'),
        'com_sampling_interval': float(first['times'][1] - first['times'][0]),
        'frames_per_replica': int(first['positions'].shape[0]),
        'stars_per_replica': int(first['positions'].shape[1]),
        'replicas': len(replicas),
        'input_trajectories': [replica['path'] for replica in replicas],
        'segment_step_range': [int(first['steps'][0]), int(first['steps'][-1])],
        'segment_time_range': [float(first['times'][0]), float(first['times'][-1])],
        'local_alpha_method': (
            'five-point least-squares slope of log(mean MSD) versus log(lag time)'),
        'diffusive_regime': {
            'criterion': ('|local alpha - 1| <= {} for at least {} adjacent multi-tau lag points'
                          .format(arguments.alpha_tolerance, arguments.min_diffusive_bins)),
            'regions': diffusive_regions,
            'established': bool(diffusive_regions),
        },
        'candidate_fit_windows': fit_summaries,
        'diagnostic_window': recommended,
        'recommended_window': recommended if diffusive_regions else None,
        'diffusion_estimate_adequate': bool(diffusive_regions),
        'cutoff_sensitivity_max_absolute_change': sensitivity,
        'student_t_critical_value': STUDENT_T_95_DF4,
        'validation': 'synthetic and C1 short-slice selected-lag checks passed',
    }
    paths = write_outputs(arguments.output_prefix, replica_rows, mean_rows, fit_rows, summary)
    print('P4.4 COM diffusion analysis written: {}'.format(', '.join(paths)))
    if diffusive_regions:
        print('recommended_D={}'.format(recommended['mean_d']))
    else:
        print('terminal diffusion not established; diagnostic_D={}'.format(recommended['mean_d']))


if __name__ == '__main__':
    main()
