#!/usr/bin/env python3
"""Summarize independent-replica P4.2 relaxation-modulus pilot outputs."""

import argparse
import csv
import json
import math
import os
import statistics
import sys
import tempfile


CHANNELS = ('Gxy', 'Gxz', 'Gyz', 'GNxy', 'GNxz', 'GNyz')
HEADER = '# time Gxy Gxz Gyz GNxy GNxz GNyz G'


def fail(path, message):
    raise ValueError('{}: {}'.format(path, message))


def read_companion_temperature(path):
    if not path.endswith('.stress_correlator'):
        fail(path, 'expected a .stress_correlator file')
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
    if lines[1] != HEADER:
        fail(path, 'unexpected stress columns')
    previous_time = -math.inf
    for line in lines[2:]:
        fields = line.split()
        if len(fields) != 8:
            fail(path, 'expected eight stress columns')
        try:
            values = [float(field) for field in fields]
        except ValueError as error:
            raise ValueError('{}: invalid stress row {}'.format(path, line)) from error
        if not all(math.isfinite(value) for value in values):
            fail(path, 'nonfinite stress value')
        time = values[0]
        if time <= previous_time:
            fail(path, 'lag times are not strictly increasing')
        previous_time = time
        contributions = dict(zip(CHANNELS, values[1:7]))
        recomputed = ((contributions['Gxy'] + contributions['Gxz'] + contributions['Gyz']) /
                      (5.0 * metadata['temperature']) +
                      (contributions['GNxy'] + contributions['GNxz'] + contributions['GNyz']) /
                      (30.0 * metadata['temperature']))
        if not math.isclose(recomputed, values[7], rel_tol=2e-10, abs_tol=2e-12):
            fail(path, 'six-channel modulus does not match reported G')
        contributions['time'] = time
        contributions['G'] = recomputed
        rows.append(contributions)
    if not rows:
        fail(path, 'no stress rows')
    return metadata, rows


def require_matching_lags(replicas):
    reference = replicas[0]['rows']
    for replica in replicas[1:]:
        if replica['metadata']['dt'] != replicas[0]['metadata']['dt'] or \
                replica['metadata']['temperature'] != replicas[0]['metadata']['temperature']:
            fail(replica['path'], 'replica physical provenance differs')
        rows = replica['rows']
        if len(rows) != len(reference):
            fail(replica['path'], 'replica has different lag-bin count')
        for expected, actual in zip(reference, rows):
            if not math.isclose(expected['time'], actual['time'], rel_tol=1e-12,
                                abs_tol=1e-12):
                fail(replica['path'], 'replica lag bins differ')


def summarize(replicas, resolved_fraction, noise_fraction):
    require_matching_lags(replicas)
    count = len(replicas)
    g0 = statistics.mean(replica['rows'][0]['G'] for replica in replicas)
    summary_rows = []
    for index, reference in enumerate(replicas[0]['rows']):
        row = {'time': reference['time']}
        for channel in CHANNELS + ('G',):
            values = [replica['rows'][index][channel] for replica in replicas]
            row[channel] = statistics.mean(values)
            row[channel + '_sem'] = (statistics.stdev(values) / math.sqrt(count)
                                     if count > 1 else math.nan)
        uncertainty_limit = max(resolved_fraction * abs(row['G']),
                                noise_fraction * abs(g0))
        row['resolved'] = math.isfinite(row['G_sem']) and row['G_sem'] <= uncertainty_limit
        summary_rows.append(row)

    tail_rows = [row for row in summary_rows if row['time'] >= 0.5 * summary_rows[-1]['time']]
    resolved_tail = [row for row in tail_rows if row['resolved']]
    tail_sem = [row['G_sem'] for row in resolved_tail]
    tail_values = [row['G'] for row in resolved_tail]
    tail_noise = math.sqrt(statistics.mean(value * value for value in tail_sem)) if tail_sem else math.nan
    tail_mean = statistics.mean(tail_values) if tail_values else math.nan
    decayed = (len(resolved_tail) >= 3 and math.isfinite(tail_noise) and
               abs(tail_mean) <= tail_noise)
    resolved_times = [row['time'] for row in summary_rows if row['resolved']]
    resolved_max_time = max(resolved_times) if resolved_times else math.nan
    total_steps = min(int(replica['metadata']['stress_samples']) for replica in replicas)
    dt = replicas[0]['metadata']['dt']
    if not decayed or not math.isfinite(resolved_max_time):
        recommendation = {
            'status': 'pilot_not_sufficient_for_production_duration',
            'next_pilot_steps_per_seed': 2 * total_steps,
            'reason': 'tail is not both resolved and consistent with zero',
        }
    else:
        planning_steps = max(total_steps, math.ceil(10.0 * resolved_max_time / dt))
        recommendation = {
            'status': 'provisional_duration_scale_only',
            'minimum_steps_per_seed': planning_steps,
            'reason': 'ten resolved-tail windows; confirm with a larger pilot before production',
        }
    return summary_rows, {
        'replicas': count,
        'g0_mean': g0,
        'resolved_tail_criterion': (
            'SEM(G) <= max({:.3g} * |mean(G)|, {:.3g} * |mean(G(0))|)'.format(
                resolved_fraction, noise_fraction)),
        'decayed_criterion': (
            'at least three resolved bins at lag >= half the maximum lag and '
            '|their mean G| <= RMS of their replica SEMs'),
        'max_lag_time': summary_rows[-1]['time'],
        'resolved_max_lag_time': resolved_max_time,
        'tail_resolved_bins': len(resolved_tail),
        'tail_mean_g': tail_mean,
        'tail_rms_sem': tail_noise,
        'tail_decayed_toward_zero': decayed,
        'production_duration_recommendation': recommendation,
    }


def write_outputs(prefix, replicas, summary_rows, report):
    replica_path = prefix + '.replicas.csv'
    mean_path = prefix + '.mean.csv'
    report_path = prefix + '.summary.json'
    with open(replica_path, 'w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=('replica', 'source', 'time') + CHANNELS + ('G',))
        writer.writeheader()
        for replica_index, replica in enumerate(replicas, 1):
            for row in replica['rows']:
                writer.writerow(dict(row, replica=replica_index, source=replica['path']))
    fields = ('time',) + CHANNELS + ('G',) + tuple(channel + '_sem' for channel in CHANNELS + ('G',)) + ('resolved',)
    with open(mean_path, 'w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)
    with open(report_path, 'w', encoding='utf-8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write('\n')
    return replica_path, mean_path, report_path


def self_test():
    rows_a = ('# stress_samples=4 step0_sampled=no stress_interval_steps=1 dt=0.01\n' + HEADER + '\n' +
              '0 5 5 5 5 5 5 3.5\n1 2 2 2 2 2 2 1.4\n2 .1 .1 .1 .1 .1 .1 .07\n')
    rows_b = ('# stress_samples=4 step0_sampled=no stress_interval_steps=1 dt=0.01\n' + HEADER + '\n' +
              '0 5.1 5.1 5.1 5.1 5.1 5.1 3.57\n1 2.1 2.1 2.1 2.1 2.1 2.1 1.47\n2 .09 .09 .09 .09 .09 .09 .063\n')
    with tempfile.TemporaryDirectory() as directory:
        paths = []
        for index, text in enumerate((rows_a, rows_b)):
            path = os.path.join(directory, 'seed{}.stress_correlator'.format(index))
            with open(path, 'w', encoding='utf-8') as output:
                output.write(text)
            with open(path[:-len('.stress_correlator')] + '.state', 'w', encoding='utf-8') as output:
                output.write('# T=1\n')
            paths.append(path)
        replicas = [dict(path=path, metadata=read_stress_correlator(path)[0],
                         rows=read_stress_correlator(path)[1]) for path in paths]
        summary_rows, report = summarize(replicas, 0.25, 0.05)
        if len(summary_rows) != 3 or report['replicas'] != 2:
            raise AssertionError('replica summary regression failed')
        output_paths = write_outputs(os.path.join(directory, 'pilot'), replicas, summary_rows, report)
        if not all(os.path.isfile(path) for path in output_paths):
            raise AssertionError('output write regression failed')
    print('P4.2 RHEOLOGY PILOT ANALYZER SELF_TEST PASS')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stress_files', nargs='*')
    parser.add_argument('--output-prefix')
    parser.add_argument('--resolved-fraction', type=float, default=0.25)
    parser.add_argument('--noise-fraction', type=float, default=0.05)
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if len(arguments.stress_files) < 2:
        parser.error('at least two independent-replica stress files are required')
    if not arguments.output_prefix:
        parser.error('--output-prefix is required')
    if not 0.0 < arguments.resolved_fraction < 1.0 or \
            not 0.0 < arguments.noise_fraction < 1.0:
        parser.error('heuristic fractions must be positive and below one')
    replicas = []
    for path in arguments.stress_files:
        metadata, rows = read_stress_correlator(path)
        replicas.append({'path': path, 'metadata': metadata, 'rows': rows})
    summary_rows, report = summarize(replicas, arguments.resolved_fraction,
                                     arguments.noise_fraction)
    output_paths = write_outputs(arguments.output_prefix, replicas, summary_rows, report)
    print('P4.2 rheology pilot analysis written: {}'.format(', '.join(output_paths)))


if __name__ == '__main__':
    main()
