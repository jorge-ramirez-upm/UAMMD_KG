#!/usr/bin/env python3
"""Tabulate local estimates and compare the final quarters without recomputing errors."""
import argparse
import csv
from pathlib import Path
import reproduce_joint as review


def main(directory):
    directory = Path(directory)
    paths = [directory / 'terminal_quarter.json', directory / 'window_estimates.csv']
    review.joint.require(not any(p.exists() for p in paths), 'immutable supplement already exists')
    source = directory / 'summary.json'
    summary = review.joint.campaign.load_json(source)
    comparisons = review.compare(summary['records'], (7500000, 7750000), (7750000, 8000000))
    review.joint.runner.exclusive_json(paths[0], dict(comparisons=comparisons,
        formal_acceptance=False, uncertainty='three paired original histories; exploratory Student-t df=2',
        source_sha256=review.joint.runner.hash_files([source, Path(__file__)])))
    with paths[1].open('x') as stream:
        fields = ('replica', 'start_step', 'end_step', 'segment', 'initial_context', 'category',
                  'observable', 'mean', 'tau_time', 'effective_samples_estimate', 'slope',
                  'sem_estimate', 'sem_5', 'sem_10', 'sem_20', 'resolution_warning',
                  'constant_not_mixing_evidence')
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for record in summary['records']:
            for window in record['windows']:
                for category in ('metrics', 'activity'):
                    for name, value in window[category].items():
                        writer.writerow(dict(replica=record['replica'],
                            start_step=window['start_step_exclusive'], end_step=window['end_step_inclusive'],
                            segment=window['segment'], initial_context=window['start_step_exclusive'] < 1000000,
                            category=category, observable=name,
                            **{k: value[k] for k in ('mean', 'tau_time', 'effective_samples_estimate',
                                'slope', 'sem_estimate', 'resolution_warning', 'constant_not_mixing_evidence')},
                            **{'sem_' + str(k): v for k, v in value['blocking_sem_sensitivity'].items()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
