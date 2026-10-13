#!/usr/bin/env python3
"""Read-only paired window-choice diagnostics; never combine window SEMs or IATs."""
import argparse
import collections
import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'campaign'))
import analyze_joint_e2 as joint

# MD-step intervals, chosen as exploratory sensitivity checks, not acceptance guards.
PAIRS = (((1000000, 3000000), (3000000, 5000000)),
         ((1000000, 3000000), (4000000, 6000000)),
         ((2000000, 4000000), (4000000, 6000000)),
         ((2000000, 3000000), (3000000, 4000000)),
         ((3000000, 4000000), (5000000, 6000000)),
         ((4000000, 5000000), (5000000, 6000000)),
         ((3000000, 5000000), (4000000, 6000000)),
         ((2000000, 5000000), (3000000, 6000000)))


def mean(record, category, name, start, end):
    joint.require(0 <= start < end, 'invalid comparison interval')
    windows = [w for w in record['windows'] if
               start <= w['start_step_exclusive'] and w['end_step_inclusive'] <= end]
    joint.require(windows and windows[0]['start_step_exclusive'] == start and
                  windows[-1]['end_step_inclusive'] == end and
                  all(a['end_step_inclusive'] == b['start_step_exclusive']
                      for a, b in zip(windows, windows[1:])) and
                  len({w['segment'] for w in windows}) == 1,
                  'interval must be exactly tiled within one continuous segment')
    return sum((w['end_step_inclusive'] - w['start_step_exclusive']) * w[category][name]['mean']
               for w in windows) / (end - start)


def summarize(summary, pairs=PAIRS):
    joint.require([r['replica'] for r in summary['records']] == [1, 2, 3],
                  'three independent histories required')
    comparisons = []
    for early, late in pairs:
        joint.require(min(early[0], late[0]) >= summary['windows_steps'],
                      'initial transient is context, not a stationary comparator')
        for category in ('metrics', 'activity'):
            for name in summary['records'][0]['windows'][0][category]:
                a = [mean(r, category, name, *early) for r in summary['records']]
                b = [mean(r, category, name, *late) for r in summary['records']]
                changes = [new - old for old, new in zip(a, b)]
                stats = joint.segment.review.analysis.dynamics.replica_statistics(changes)
                comparisons.append(dict(category=category, observable=name, early_steps=early,
                    late_steps=late, early_replica_means=a, late_replica_means=b,
                    per_replica_changes=changes, overlapping_steps=max(0, min(early[1], late[1]) -
                        max(early[0], late[0])), **stats,
                    excludes_zero=abs(stats['mean']) > stats['ci95_half_width']))
    return dict(schema_version=1, stage='E2_joint_window_sensitivity', automatic_acceptance=False,
        independent_units='three histories, Student-t df=2; overlapping comparisons are not independent evidence',
        uncertainty='paired history means only; no combination of window SEMs or IATs; exploratory unadjusted intervals',
        comparisons=comparisons)



def degree_histograms(rows, raw_events, system):
    """Capture distinct-neighbor degrees from the unchanged validated graph replay."""
    joint.require(rows[0]['step'] == 0 and rows[0]['bonds'] == 0,
                  'degree replay requires the original unbound continuous history')
    analysis = joint.segment.review.analysis
    original = analysis.topology.frame_observables
    frames = []

    def capture(*args, **kwargs):
        graph = original(*args, **kwargs)
        counts = dict(collections.Counter(graph['neighbor_degree'].values()))
        joint.require(sum(counts.values()) == len(system['stars']), 'degree coverage differs')
        frames.append(dict(step=int(args[1]), counts=counts))
        return graph

    analysis.topology.frame_observables = capture
    try:
        # The callback returns the original graph unchanged; input rows remain immutable.
        analysis.replay(copy.deepcopy(rows), raw_events, system, network=True)
    finally:
        analysis.topology.frame_observables = original
    return frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = summarize(joint.campaign.load_json(args.summary))
    result['source_summary_sha256'] = joint.campaign.sha256(args.summary)
    joint.runner.exclusive_json(args.output, result)


if __name__ == '__main__':
    main()
