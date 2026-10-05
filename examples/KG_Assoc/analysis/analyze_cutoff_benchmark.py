#!/usr/bin/env python3
"""Summarize repeated K1 wall-time/candidate-edge benchmark logs."""
import argparse
import math
import re
import statistics

from analyze_cutoff_audit import DECISION_CUTOFFS, reference

BASE_CUTOFF = 2.0 ** (1.0 / 6.0)
FIELDS = ('wall_seconds', 'chemistry_sweeps', 'total_candidate_pairs',
          'mean_candidate_pairs_per_sweep', 'creations', 'breaks',
          'particle_timesteps_per_second')


def parse_log(path):
    text = open(path).read()
    cutoff_match = re.search(r'\br_assoc\s+(\S+)', text)
    metrics = {}
    for field in FIELDS:
        match = re.search(r'\b{}\s+(\S+)'.format(field), text)
        if match:
            metrics[field] = float(match.group(1))
    mean_match = re.search(r'\bmean_candidate_edges\s+(\S+)', text)
    if 'mean_candidate_pairs_per_sweep' not in metrics and mean_match:
        metrics['mean_candidate_pairs_per_sweep'] = float(mean_match.group(1))
    if 'total_candidate_pairs' not in metrics:
        if ('chemistry_sweeps' in metrics and
                'mean_candidate_pairs_per_sweep' in metrics):
            metrics['total_candidate_pairs'] = (
                metrics['chemistry_sweeps'] *
                metrics['mean_candidate_pairs_per_sweep'])
    if 'particle_timesteps_per_second' not in metrics:
        match = re.search(r'\btimesteps_per_second\s+(\S+)', text)
        if match:
            metrics['particle_timesteps_per_second'] = float(match.group(1))
    if set(FIELDS) - set(metrics):
        raise ValueError('{} is missing {}'.format(
            path, ', '.join(sorted(set(FIELDS) - set(metrics)))))
    if cutoff_match is None:
        raise ValueError('{} is missing r_assoc'.format(path))
    metrics['r_assoc'] = float(cutoff_match.group(1))
    metrics['file'] = path
    return metrics


def summarize(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row['r_assoc'], []).append(row)
    baseline_key = min(grouped, key=lambda value: abs(value - BASE_CUTOFF))
    baseline_wall = statistics.mean(
        row['wall_seconds'] for row in grouped[baseline_key])
    print('cutoff repetitions wall_seconds wall_time_relative chemistry_sweeps '
          'total_candidate_pairs mean_candidate_pairs_per_sweep creations breaks '
          'particle_timesteps_per_second')
    for cutoff, group in sorted(grouped.items()):
        mean = lambda field: statistics.mean(row[field] for row in group)
        print('{:.12g} {} {:.12g} {:.12g} {:.12g} {:.12g} {:.12g} {:.12g} '
              '{:.12g}'.format(
                  cutoff, len(group), mean('wall_seconds'),
                  mean('wall_seconds') / baseline_wall,
                  mean('chemistry_sweeps'), mean('total_candidate_pairs'),
                  mean('mean_candidate_pairs_per_sweep'), mean('creations'),
                  mean('breaks'), mean('particle_timesteps_per_second')))
    references = {ee: dict((cutoff, missing)
                           for cutoff, _, missing in reference(ee))
                  for ee in (8.0, 12.0, 16.0)}
    print('P3.0 decision cutoff F_miss_Ee8 F_miss_Ee12 F_miss_Ee16 '
          'relative_K1_wall_time mean_candidate_pairs_per_sweep')
    for cutoff, group in sorted(grouped.items()):
        mean_wall = statistics.mean(row['wall_seconds'] for row in group)
        mean_edges = statistics.mean(
            row['mean_candidate_pairs_per_sweep'] for row in group)
        values = [references[ee][min(references[ee],
                                     key=lambda value: abs(value - cutoff))]
                  for ee in (8.0, 12.0, 16.0)]
        print('{:.12g} {:.12g} {:.12g} {:.12g} {:.12g} {:.12g}'.format(
            cutoff, *values, mean_wall / baseline_wall, mean_edges))


def self_test():
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w') as baseline:
        baseline.write('r_assoc 1.122462048309373\nK1 done wall_seconds 10 '
                       'chemistry_sweeps 5 '
                       'total_candidate_pairs 20 mean_candidate_edges 4 '
                       'creations 2 breaks 1\n'
                       'particle_timesteps_per_second 100\n')
        baseline.flush()
        row = parse_log(baseline.name)
        assert math.isclose(row['mean_candidate_pairs_per_sweep'], 4.0)
        assert row['total_candidate_pairs'] == 20.0
        assert row['particle_timesteps_per_second'] == 100.0
    print('SELF_TEST PASS cutoff benchmark parser')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*')
    parser.add_argument('--self-test', action='store_true')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if not arguments.files:
        parser.error('provide benchmark log files')
    summarize([parse_log(path) for path in arguments.files])


if __name__ == '__main__':
    main()
