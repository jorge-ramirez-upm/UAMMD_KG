#!/usr/bin/env python3
"""K1 event/exposure analysis for kg_assoc_k1 compact .state files."""
import argparse
import csv
import glob
import math
import os
import re
import statistics
import sys
import tempfile

LEGACY_PATTERN = re.compile(
    r'Ea([0-9.]+)_Ee([0-9.]+)_N([0-9]+)_r([0-9]+)')


def read(path):
    rows = []
    metadata = {}
    with open(path) as state_file:
        for line in state_file:
            if line.startswith('#'):
                for token in line[1:].split():
                    if '=' in token:
                        key, value = token.split('=', 1)
                        metadata[key] = value
                continue
            fields = line.split()
            if len(fields) == 6:
                rows.append(tuple(map(float, fields)))

    if len(rows) < 2:
        raise ValueError(path + ' has too few samples')

    number_particles = rows[0][2] + 2 * rows[0][3]
    for row in rows:
        if (row[2] + 2 * row[3] != number_particles or
                row[3] != row[4] - row[5]):
            raise ValueError(path + ' invariant failure')
    return rows, int(number_particles), metadata


def integrate(rows, function, kind='trap'):
    return sum(
        (rows[index + 1][1] - rows[index][1]) *
        ((function(rows[index]) + function(rows[index + 1])) / 2
         if kind == 'trap'
         else function(rows[index + (kind == 'right')]))
        for index in range(len(rows) - 1))


def meanse(values):
    mean = statistics.mean(values)
    standard_error = (statistics.stdev(values) / math.sqrt(len(values))
                      if len(values) > 1 else float('nan'))
    return mean, standard_error


def linear_fit(points):
    x_values, y_values = zip(*points)
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(y_values)
    fitted_slope = (sum((x - x_mean) * (y - y_mean)
                        for x, y in points) /
                    sum((x - x_mean) ** 2 for x in x_values))
    return fitted_slope, y_mean - fitted_slope * x_mean


def chemistry_attempt_rate(nu0, ea, temperature, every, dt):
    chemistry_dt = every * dt
    q = -math.expm1(-nu0 * math.exp(-ea / temperature) * chemistry_dt)
    return q, q / chemistry_dt


def legacy_parameters(path):
    match = LEGACY_PATTERN.search(os.path.basename(path))
    if not match:
        return {}
    return {
        'Ea': float(match[1]),
        'Ee': float(match[2]),
        'Nevery': int(match[3]),
        'replica': int(match[4]),
    }


def values_agree(left, right):
    if isinstance(left, float) or isinstance(right, float):
        return math.isclose(left, right, rel_tol=1e-12, abs_tol=0.0)
    return left == right


def resolve_parameter(path, metadata, legacy, name, converter, required=True,
                      default=None):
    metadata_value = converter(metadata[name]) if name in metadata else None
    legacy_value = legacy.get(name)

    if (metadata_value is not None and legacy_value is not None and
            not values_agree(metadata_value, legacy_value)):
        raise ValueError(
            '{}: metadata {}={} disagrees with filename value {}'.format(
                path, name, metadata_value, legacy_value))

    if metadata_value is not None:
        return metadata_value
    if legacy_value is not None:
        return legacy_value
    if default is not None:
        return default
    if required:
        raise ValueError(
            '{}: missing {} in .state metadata; legacy filenames only '
            'provide Ea, Ee, Nevery, and replica'.format(path, name))
    return None


def analyze_file(path):
    rows, actual_particles, metadata = read(path)
    legacy = legacy_parameters(path)

    header_particles = resolve_parameter(
        path, metadata, legacy, 'N', int, required=False)
    if (header_particles is not None and
            header_particles != actual_particles):
        raise ValueError(
            '{}: metadata N={} disagrees with sampled particle count {}'.format(
                path, header_particles, actual_particles))

    rho = resolve_parameter(path, metadata, legacy, 'rho', float)
    temperature = resolve_parameter(
        path, metadata, legacy, 'T', float, default=1.0)
    dt = resolve_parameter(path, metadata, legacy, 'dt', float)
    nu0 = resolve_parameter(
        path, metadata, legacy, 'nu0', float, default=20.0)
    ea = resolve_parameter(path, metadata, legacy, 'Ea', float)
    ee = resolve_parameter(path, metadata, legacy, 'Ee', float)
    every = resolve_parameter(path, metadata, legacy, 'Nevery', int)

    replica = resolve_parameter(
        path, metadata, legacy, 'replica', int, required=False)
    if replica is None:
        replica = 'seed_' + metadata['seed'] if 'seed' in metadata else 'metadata'

    volume = actual_particles / rho
    creations = rows[-1][4] - rows[0][4]
    breaks = rows[-1][5] - rows[0][5]
    free_exposure = integrate(
        rows, lambda row: row[2] * (row[2] - 1) / volume)
    bound_exposure = integrate(rows, lambda row: row[3])
    exposure_difference = max(
        abs(integrate(
            rows, lambda row: row[2] * (row[2] - 1) / volume, 'left') /
            free_exposure - 1),
        abs(integrate(
            rows, lambda row: row[2] * (row[2] - 1) / volume, 'right') /
            free_exposure - 1),
        abs(integrate(rows, lambda row: row[3], 'left') /
            bound_exposure - 1) if bound_exposure else 0,
        abs(integrate(rows, lambda row: row[3], 'right') /
            bound_exposure - 1) if bound_exposure else 0)

    equilibrium_rows = rows[len(rows) // 2:]
    direct_equilibrium = [
        (row[3] / volume) / (row[2] / volume) ** 2
        for row in equilibrium_rows if row[2] > 0]
    q, attempt_rate = chemistry_attempt_rate(
        nu0, ea, temperature, every, dt)

    return dict(
        file=path,
        Nparticles=actual_particles,
        rho=rho,
        nu0=nu0,
        Ea=ea,
        Ee=ee,
        Nevery=every,
        replica=replica,
        run_type=run_type(path),
        creations=creations,
        breaks=breaks,
        kf_event=creations / free_exposure if free_exposure else float('nan'),
        kb_event=breaks / bound_exposure if bound_exposure else float('nan'),
        kf_over_q=(creations / free_exposure / q
                   if free_exposure else float('nan')),
        kb_over_q=(breaks / bound_exposure / q
                   if bound_exposure else float('nan')),
        attempt_rate=attempt_rate,
        kf_over_attempt_rate=(creations / free_exposure / attempt_rate
                              if free_exposure else float('nan')),
        kb_over_attempt_rate=(breaks / bound_exposure / attempt_rate
                              if bound_exposure else float('nan')),
        Keq_event=(creations / free_exposure) / (breaks / bound_exposure)
        if bound_exposure and breaks else float('nan'),
        Keq_direct=statistics.mean(direct_equilibrium),
        exposure_relative_difference=exposure_difference)


def condition_key(result):
    return (result['Nparticles'], result['rho'], result['Ea'], result['Ee'],
            result['nu0'], result['Nevery'])


def run_type(path):
    return 'pilot' if os.path.basename(path).startswith('pilot_') else 'production'


def production_results(results):
    return [result for result in results if result['run_type'] == 'production']


def group_conditions(results):
    groups = {}
    for result in results:
        groups.setdefault(condition_key(result), []).append(result)
    return groups


def run_self_test():
    q, attempt_rate = chemistry_attempt_rate(20.0, 4.0, 1.0, 100, 0.005)
    if (not math.isclose(q, 0.16736206976502233, rel_tol=1e-14) or
            not math.isclose(attempt_rate, 0.33472413953004465,
                             rel_tol=1e-14)):
        raise AssertionError('attempt-rate normalization regression failed')

    fitted_slope, fitted_intercept = linear_fit(
        [(2.0, 3.0), (4.0, 5.0), (6.0, 7.0), (8.0, 9.0)])
    if (not math.isclose(fitted_slope, 1.0, rel_tol=1e-14) or
            not math.isclose(fitted_intercept, 1.0, rel_tol=1e-14)):
        raise AssertionError('linear equilibrium-fit regression failed')

    header = (
        '# N={n} rho={rho} T=1 dt=0.005 nu0={nu0} damp=2 Ea=4 Ee=4 '
        'Nevery=100 seed={seed} push=5000 warmup=20000 production=100\n')
    with tempfile.TemporaryDirectory() as directory:
        paths = []
        for particle_count, density, attempt_frequency in (
                (256, 0.05, 20),
                (8192, 0.05, 20),
                (32768, 0.05, 20),
                (256, 0.025, 20),
                (256, 0.05, 5)):
            path = os.path.join(
                directory,
                'sizecheck_N{}_rho{}_nu{}.state'.format(
                    particle_count, density, attempt_frequency))
            with open(path, 'w') as state_file:
                state_file.write(header.format(
                    n=particle_count, rho=density, nu0=attempt_frequency,
                    seed=700000 + particle_count + attempt_frequency))
                state_file.write('0 0 {} 0 0 0\n'.format(particle_count))
                state_file.write('100 0.5 {} 0 0 0\n'.format(particle_count))
            paths.append(path)

        results = [analyze_file(path) for path in paths]
        pilot_path = os.path.join(directory, 'pilot_sizecheck_N256.state')
        with open(pilot_path, 'w') as state_file:
            state_file.write(header.format(n=256, rho=0.05, nu0=20,
                                           seed=700256))
            state_file.write('0 0 256 0 0 0\n')
            state_file.write('100 0.5 256 0 0 0\n')
        pilot_result = analyze_file(pilot_path)
        if pilot_result['run_type'] != 'pilot':
            raise AssertionError('pilot filename was not identified')

        groups = group_conditions(production_results(results + [pilot_result]))
        if len(groups) != 5 or set(key[0] for key in groups) != {
                256, 8192, 32768}:
            raise AssertionError(
                'particle counts, parameters, or pilot results were incorrectly grouped')

    try:
        resolve_parameter(
            'Ea4_Ee4_N100_r1.state', {'Ea': '5'},
            legacy_parameters('Ea4_Ee4_N100_r1.state'), 'Ea', float)
        raise AssertionError('metadata/filename conflict was not rejected')
    except ValueError:
        pass

    print('SELF_TEST PASS metadata conflicts and size-separated grouping')


def write_outputs(results, summary_path):
    with open(summary_path, 'w', newline='') as summary_file:
        writer = csv.DictWriter(summary_file, fieldnames=results[0])
        writer.writeheader()
        writer.writerows(results)

    production = production_results(results)
    groups = group_conditions(production)
    fields = (
        ['Nparticles', 'rho', 'Ea', 'Ee', 'nu0', 'Nevery', 'replicas'] +
        [quantity + suffix for quantity in (
            'creations', 'breaks', 'kf_event', 'kb_event', 'kf_over_q',
            'kb_over_q', 'attempt_rate', 'kf_over_attempt_rate',
            'kb_over_attempt_rate', 'Keq_event', 'Keq_direct',
            'exposure_relative_difference') for suffix in ('', '_se')])
    condition_path = os.path.splitext(summary_path)[0] + '_conditions.csv'
    with open(condition_path, 'w', newline='') as condition_file:
        writer = csv.DictWriter(condition_file, fieldnames=fields)
        writer.writeheader()
        for key, group in sorted(groups.items()):
            result = dict(zip(
                ('Nparticles', 'rho', 'Ea', 'Ee', 'nu0', 'Nevery'), key))
            result['replicas'] = len(group)
            for quantity in (
                    'creations', 'breaks', 'kf_event', 'kb_event',
                    'kf_over_q', 'kb_over_q', 'attempt_rate',
                    'kf_over_attempt_rate', 'kb_over_attempt_rate',
                    'Keq_event', 'Keq_direct',
                    'exposure_relative_difference'):
                result[quantity], result[quantity + '_se'] = meanse(
                    [entry[quantity] for entry in group])
            writer.writerow(result)

    print('wrote', summary_path,
          'and condition table; all sampled invariants passed;',
          len(results) - len(production), 'pilot rows excluded from conditions')


def print_equilibrium_slopes(results):
    production = production_results(results)
    parameter_sets = sorted(set(
        (result['Nparticles'], result['rho'], result['nu0'])
        for result in production))
    for particle_count, density, attempt_frequency in parameter_sets:
        selected = [
            result for result in production
            if (result['Nparticles'] == particle_count and
                result['rho'] == density and
                result['nu0'] == attempt_frequency and
                result['Ea'] == 4 and result['Nevery'] == 100)]
        if len({result['Ee'] for result in selected}) < 2:
            continue
        prefix = '' if len(parameter_sets) == 1 else (
            'Nparticles {} rho {} nu0 {} '.format(
                particle_count, density, attempt_frequency))
        for quantity in ('Keq_event', 'Keq_direct'):
            points = [
                (result['Ee'], math.log(result[quantity]))
                for result in selected if result[quantity] > 0]
            if len(points) >= 2:
                fitted_slope, fitted_intercept = linear_fit(points)
                print('{}ln {} vs Ee slope {} intercept {}'.format(
                    prefix, quantity, fitted_slope, fitted_intercept))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*')
    parser.add_argument('--summary', default='k1.csv')
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()

    if arguments.self_test:
        run_self_test()
        return
    if not arguments.files:
        parser.error('at least one .state file is required')

    paths = sorted(set(
        path for pattern in arguments.files for path in glob.glob(pattern)))
    results = [analyze_file(path) for path in paths]
    if not results:
        sys.exit('no K1 files matched')

    write_outputs(results, arguments.summary)
    print_equilibrium_slopes(results)


if __name__ == '__main__':
    main()
