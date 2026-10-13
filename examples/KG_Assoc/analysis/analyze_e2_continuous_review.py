#!/usr/bin/env python3
"""Read-only 6M continuous-history review with shape and satellite diagnostics."""
import argparse
from pathlib import Path
import statistics

import analyze_e2_satellite_continuation as graph_review

joint = graph_review.joint
PAIRS = (((2000000, 4000000), (4000000, 6000000)),
         ((4000000, 5000000), (5000000, 6000000)),
         ((3000000, 4000000), (5000000, 6000000)),
         ((3000000, 5000000), (4000000, 6000000)),
         ((2500000, 4500000), (3500000, 5500000)),
         ((3000000, 4500000), (4500000, 6000000)),
         ((3500000, 5000000), (4500000, 6000000)),
         ((4500000, 5000000), (5500000, 6000000)))
SHAPES = ('mean_rg2', 'mean_center_terminal_r2')


def metric_names(system):
    return joint.segment.METRICS + graph_review.EXTRA + tuple(
        f'degree_{degree}_fraction' for degree in range(system['f'] + 1))


def mean_windows(source, history, names, window_steps=500000):
    """Exactly tiled frame/event means; deliberately no pooled uncertainty."""
    entry = history['entry']
    start, end = entry['start_step'], entry['end_step']
    joint.require((end - start) % window_steps == 0, 'window coverage differs')
    result = []
    for boundary in range(start, end, window_steps):
        selected = [row for row in history['rows'] if boundary < row['step'] <= boundary + window_steps]
        joint.require([row['step'] for row in selected] ==
                      list(range(boundary + 1000, boundary + window_steps + 1, 1000)),
                      'missing frame or window crosses a diagnostic boundary')
        events = [event for event in history['events'] if boundary < event['step'] <= boundary + window_steps]
        counts = dict(creations=sum(event['type'] == 'C' for event in events),
                      breaks=sum(event['type'] == 'B' for event in events),
                      neighbor_gains=sum(event['neighbor_gain'] for event in events),
                      neighbor_losses=sum(event['neighbor_loss'] for event in events))
        result.append(dict(start_step_exclusive=boundary, end_step_inclusive=boundary + window_steps,
            segment=source['attempt'], transient_context=boundary < 1000000,
            metrics={name: dict(mean=statistics.mean(row[name] for row in selected)) for name in names},
            activity={name: dict(mean=count / (window_steps * entry['physics']['dt']))
                      for name, count in counts.items()}))
    return result


def summarize(source):
    segments = joint.check_lineage([source])
    joint.require(all(h['entry']['start_step'] == 0 and h['entry']['end_step'] == 6000000
                      for h in source['histories']), 'continuous 0–6M histories required')
    names = metric_names(source['plan']['system'])
    original = joint.segment.METRICS
    joint.segment.METRICS = names
    try:
        summary = joint.summarize(segments)
    finally:
        joint.segment.METRICS = original
    records = [dict(replica=h['entry']['replica'], windows=mean_windows(source, h, names))
               for h in source['histories']]
    sensitivity = graph_review.sensitivity.summarize(dict(records=records, windows_steps=500000), PAIRS)
    intervals = sorted({pair for comparison in PAIRS for pair in comparison} |
                       {(start, start + 500000) for start in range(0, 6000000, 500000)})
    shape_records = []
    for history in source['histories']:
        windows = []
        for start, end in intervals:
            selected = [row for row in history['rows'] if start < row['step'] <= end]
            windows.append(dict(start_step_exclusive=start, end_step_inclusive=end,
                segment=source['attempt'], transient_context=start < 1000000,
                metrics={name: joint.segment.review.estimate([row[name] for row in selected],
                    [row['time'] for row in selected]) for name in SHAPES}))
        shape_records.append(dict(replica=history['entry']['replica'], windows=windows))
    return summary, dict(schema_version=1, stage='E2_continuous_window_sensitivity',
        automatic_acceptance=False, records=records, comparisons=sensitivity['comparisons'],
        shape_interval_estimates=shape_records, independent_units=sensitivity['independent_units'],
        uncertainty=sensitivity['uncertainty'], windows_steps=500000,
        mean_policy='500k means only; no averaging or stitching IATs, SEMs or blocking errors')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', required=True, type=Path)
    parser.add_argument('--attempt', required=True, type=Path)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    joint.require(not args.output.exists(), 'immutable review output already exists')
    attempt = args.attempt.resolve()
    joint.require(joint.campaign.sha256(attempt / 'plan.json') == args.plan_sha256, 'source plan hash differs')
    sources = graph_review.authenticate_with_graphs(args.dataset_root.resolve(), [attempt])
    summary, sensitivity = summarize(sources[0])
    joint.write_report(summary, args.output / 'joint6m')
    hashes = joint.runner.hash_files([Path(__file__), Path(graph_review.__file__), Path(joint.__file__),
        Path(graph_review.sensitivity.__file__), attempt / 'plan.json', attempt / 'approval.json'] +
        [attempt / f'r{r:03d}/complete.json' for r in (1, 2, 3)])
    joint.runner.exclusive_json(args.output / 'window_sensitivity.json', dict(sensitivity, source_sha256=hashes))
    source = sources[0]
    joint.runner.exclusive_json(args.output / 'provenance.json', dict(schema_version=1,
        stage='E2_joint_review_provenance', read_only=True, formal_acceptance=False,
        registry_activation=False, production_authorization=False, starting_git_sha=joint.campaign.git_sha(),
        source_sha256=hashes, source_plan=source['plan'],
        build_authentication_scope=source['build_authentication_scope'],
        validated_histories=[dict(entry=h['entry'], validation=h['validation']) for h in source['histories']],
        proposed_endpoints=[dict(replica=h['entry']['replica'], prefix=h['entry']['output_prefix'],
            end_step=h['entry']['end_step'], chemistry_seed=h['entry']['chemistry_seed'],
            md_seed=h['entry']['md_seed'], effective_md_seed=h['entry']['effective_md_seed'],
            state_sha256={h['entry']['output_prefix'] + suffix: digest
                          for suffix, digest in h['validation']['output_sha256'].items()})
            for h in source['histories']]))
    print('Read-only review complete: ' + str(args.output), flush=True)


if __name__ == '__main__':
    main()
