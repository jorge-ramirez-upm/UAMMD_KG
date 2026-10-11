#!/usr/bin/env python3
"""Immutable, correlation-aware three-history review of one authenticated E2 segment."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'campaign'))
import kg_assoc_e2 as runner
import analyze_c1_recovery as review

campaign = runner.campaign
require = runner.require
METRICS = review.analysis.METRICS + ('components', 'second_degree_moment',
                                   'mean_rg2', 'mean_center_terminal_r2')


def analyze(root, attempt, output, window_steps, discard_steps=0):
    output = output.resolve()
    output.relative_to(root / 'aggregate/e2')
    require(not output.exists(), 'analysis output already exists')
    plan = runner.verify(root, attempt)
    require(window_steps >= 4000 and window_steps % 1000 == 0 and
            discard_steps >= 0 and discard_steps % 1000 == 0, 'invalid review windows')
    require((plan['steps'] - discard_steps) % window_steps == 0, 'review windows must cover retained segment')
    records = []
    for entry in plan['histories']:
        rows, events, _ = runner.validation.validate(entry, oracle=plan['smoke'])
        start = entry['start_step'] + discard_steps
        require(start < entry['end_step'], 'discard removes entire segment')
        windows = []
        for boundary in range(start, entry['end_step'], window_steps):
            window = review.window(rows, events, boundary, boundary + window_steps,
                                   stickers=entry['system']['f'] * entry['system']['number_of_stars'],
                                   dt=entry['physics']['dt'], stars=entry['system']['number_of_stars'],
                                   metrics=METRICS)
            for category in ('metrics', 'activity'):
                for item in window[category].values():
                    constant = len(set(item['blocks'])) == 1 and item['sem_estimate'] == 0
                    item['constant_not_mixing_evidence'] = constant
                    if constant:
                        item['effective_samples_estimate'] = None
                        item['resolution_warning'] = True
                    else:
                        item['resolution_warning'] |= item['effective_samples_estimate'] < 10
            windows.append(window)
        records.append(dict(replica=entry['replica'], windows=windows))
    ensemble = []
    for category in ('metrics', 'activity'):
        for name in records[0]['windows'][0][category]:
            for index in range(len(records[0]['windows'])):
                values = [record['windows'][index][category][name]['mean'] for record in records]
                ensemble.append(dict(category=category, observable=name, window=index + 1,
                                     **review.analysis.dynamics.replica_statistics(values)))
            if len(records[0]['windows']) >= 2:
                values = [record['windows'][-1][category][name]['mean'] -
                          record['windows'][-2][category][name]['mean'] for record in records]
                ensemble.append(dict(category=category, observable=name, window='last_minus_previous',
                                     **review.analysis.dynamics.replica_statistics(values)))
    output.mkdir(parents=True, exist_ok=False)
    runner.exclusive_json(output / 'summary.json', dict(records=records, comparisons=ensemble,
                          scientific_status='review_required', automatic_acceptance=False))
    runner.exclusive_json(output / 'analysis_config.json', dict(
        attempt=str(attempt), plan_sha256=campaign.sha256(attempt / 'plan.json'),
        source_sha256={str(attempt / f"r{entry['replica']:03d}/complete.json"):
                       campaign.sha256(attempt / f"r{entry['replica']:03d}/complete.json")
                       for entry in plan['histories']},
        analyzer_git_sha=campaign.git_sha(), analyzer_source_sha256=runner.sources(),
        window_steps=window_steps, discard_steps=discard_steps,
        seed_boundary_policy='segment_local_no_transport_or_lifetime_stitching',
        iat='first_nonpositive_lag_heuristic', blocks=[5, 10, 20],
        units='three_original_histories; paired comparisons; Student-t df=2'))
    review.analysis.write_csv(output / 'replica_comparisons.csv', ensemble)
    with (output / 'REPORT.md').open('x') as stream:
        stream.write('# E2 segment review\n\nNumerical/event/network and conformation checks passed.\n'
                     'Scientific acceptance requires human review of activity, populations, intra/inter,\n'
                     'connectivity, L1/L2, shape and correlation-aware late-window changes.\n'
                     'Broad uncertainty, constant metrics, continuing drift or replica disagreement\n'
                     'do not establish equilibrium. No universal percentage or automatic stopping gate.\n'
                     'Histories and restart boundaries remain explicitly labeled.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', required=True, type=Path)
    parser.add_argument('--attempt', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--window-steps', required=True, type=int)
    parser.add_argument('--discard-steps', default=0, type=int)
    args = parser.parse_args()
    analyze(args.dataset_root.resolve(), args.attempt.resolve(), args.output,
            args.window_steps, args.discard_steps)
