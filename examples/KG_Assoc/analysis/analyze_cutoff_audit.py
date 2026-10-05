#!/usr/bin/env python3
"""Deterministic reference and checks for kg_assoc_dimer bonded cutoff audits."""
import argparse
import glob
import math
import sys

K = 30.0
R0 = 1.5
T = 1.0
CUTOFFS = (2.0 ** (1.0 / 6.0), 1.15, 1.20, 1.25)
DECISION_CUTOFFS = (2.0 ** (1.0 / 6.0), 1.20, 1.25)


def fene(r):
    return -0.5 * K * R0 * R0 * math.log1p(-r * r / (R0 * R0))


def wca(r):
    if r >= 2.0 ** (1.0 / 6.0):
        return 0.0
    inverse6 = r ** -6
    return 4.0 * (inverse6 * inverse6 - inverse6) + 1.0


def rstar():
    lo, hi = 0.5, 2.0 ** (1.0 / 6.0)
    for _ in range(100):
        middle = (lo + hi) / 2.0
        derivative = (-48.0 / middle ** 13 + 24.0 / middle ** 7 +
                      K * middle / (1.0 - middle * middle / (R0 * R0)))
        if derivative < 0.0:
            lo = middle
        else:
            hi = middle
    return (lo + hi) / 2.0


def break_acceptance(r, ee, r_star=None):
    delta_u = fene(r) - fene(rstar() if r_star is None else r_star) - ee
    return min(1.0, math.exp(delta_u / T))


def reference(ee, intervals=200000):
    """Midpoint integration avoids evaluating singular endpoints."""
    total = 0.0
    weights = [0.0 for _ in CUTOFFS]
    break_total = 0.0
    break_weights = [0.0 for _ in CUTOFFS]
    r_star = rstar()
    dr = R0 / intervals
    for index in range(intervals):
        r = (index + 0.5) * dr
        density = r * r * math.exp(-(wca(r) + fene(r)) / T)
        total += density
        acceptance_weight = density * break_acceptance(r, ee, r_star)
        break_total += acceptance_weight
        for cutoff_index, cutoff in enumerate(CUTOFFS):
            if r > cutoff:
                weights[cutoff_index] += density
                break_weights[cutoff_index] += acceptance_weight
    return [(cutoff, tail / total, missing / break_total)
            for cutoff, tail, missing in zip(CUTOFFS, weights, break_weights)]


def read_audit(path):
    values = {}
    rows = {}
    with open(path) as audit_file:
        for line in audit_file:
            fields = line.split()
            if not fields:
                continue
            if fields[0] == 'cutoff':
                rows[float(fields[1])] = (float(fields[3]), float(fields[7]))
            elif len(fields) == 2:
                values[fields[0]] = fields[1]
    return float(values['Ee']), int(values['active_bond_observations']), rows


def check_samples(paths, tolerance):
    samples = [read_audit(path) for path in paths]
    if {sample[0] for sample in samples} != {4.0, 6.0, 8.0}:
        raise ValueError('provide one or more bonded audit files for each Ee=4,6,8')
    sample_rows = []
    for ee, observations, rows in samples:
        if observations == 0:
            raise ValueError('empty bonded audit')
        allowed = max(tolerance, 5.0 / math.sqrt(observations))
        for cutoff, expected_tail, expected_missing in reference(ee):
            matching_cutoff = min(rows, key=lambda value: abs(value - cutoff))
            if abs(matching_cutoff - cutoff) > 1e-9:
                raise AssertionError('{}: missing cutoff {}'.format(ee, cutoff))
            tail, missing = rows[matching_cutoff]
            if abs(tail - expected_tail) > allowed:
                raise AssertionError('{}: tail at {} differs by {} > {}'.format(
                    ee, cutoff, abs(tail - expected_tail), allowed))
            if abs(missing - expected_missing) > allowed:
                raise AssertionError('{}: F_miss at {} differs by {} > {}'.format(
                    ee, cutoff, abs(missing - expected_missing), allowed))
        ordered = [rows[min(rows, key=lambda value: abs(value - cutoff))]
                   for cutoff in CUTOFFS]
        if any(ordered[index][0] < ordered[index + 1][0] or
               ordered[index][1] < ordered[index + 1][1]
               for index in range(len(ordered) - 1)):
            raise AssertionError('{}: cutoff monotonicity failed'.format(ee))
        sample_rows.append((observations, ordered))
    for cutoff_index, cutoff in enumerate(CUTOFFS):
        tails = [row[1][cutoff_index][0] for row in sample_rows]
        allowed = 2.0 * max(tolerance, max(
            5.0 / math.sqrt(row[0]) for row in sample_rows))
        if max(tails) - min(tails) > allowed:
            raise AssertionError('sampled bonded tail differs across Ee at {}'.format(cutoff))
    print('PASS sampled tails/F_miss agree with deterministic reference; '
          'Ee-independence is checked against the common reference')


def self_test():
    values4 = reference(4.0, 50000)
    values6 = reference(6.0, 50000)
    values8 = reference(8.0, 50000)
    values12 = reference(12.0, 50000)
    values16 = reference(16.0, 50000)
    for values in (values4, values6, values8, values12, values16):
        if any(values[index][1] < values[index + 1][1] or
               values[index][2] < values[index + 1][2]
               for index in range(len(values) - 1)):
            raise AssertionError('reference cutoff monotonicity failed')
    if any(abs(left[1] - right[1]) > 1e-12
           for left, right in zip(values4, values8)):
        raise AssertionError('bonded radial reference incorrectly depends on Ee')
    if any(values12[index][2] < values12[index + 1][2] or
           values16[index][2] < values16[index + 1][2]
           for index in range(len(DECISION_CUTOFFS) - 1)):
        raise AssertionError('high-Ee reference cutoff monotonicity failed')
    print('SELF_TEST PASS deterministic cutoff reference')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*')
    parser.add_argument('--intervals', type=int, default=200000)
    parser.add_argument('--tolerance', type=float, default=0.02)
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if not arguments.files:
        for ee in (4.0, 6.0, 8.0, 12.0, 16.0):
            print('Ee', ee)
            for cutoff, tail, missing in reference(ee, arguments.intervals):
                print('{:.12f} tail {:.12g} F_miss {:.12g}'.format(
                    cutoff, tail, missing))
        print('P3.0 decision table (F_miss)')
        print('cutoff F_miss_Ee8 F_miss_Ee12 F_miss_Ee16')
        references = {ee: dict((cutoff, missing)
                               for cutoff, _, missing in reference(ee,
                                                                   arguments.intervals))
                      for ee in (8.0, 12.0, 16.0)}
        for cutoff in DECISION_CUTOFFS:
            values = [references[ee][cutoff] for ee in (8.0, 12.0, 16.0)]
            print('{:.12f} {:.12g} {:.12g} {:.12g}'.format(
                cutoff, *values))
        return
    paths = sorted({path for pattern in arguments.files for path in glob.glob(pattern)})
    check_samples(paths, arguments.tolerance)


if __name__ == '__main__':
    main()
