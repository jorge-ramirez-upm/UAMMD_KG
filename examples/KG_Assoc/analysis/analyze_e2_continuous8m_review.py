#!/usr/bin/env python3
"""Read-only continuous 0–8M review; no simulation or acceptance operations."""
import argparse
from pathlib import Path

import analyze_e2_continuous_review as continuous

joint = continuous.joint
PAIRS = (((2000000, 4000000), (4000000, 6000000)),
         ((4000000, 6000000), (6000000, 8000000)),
         ((2000000, 4000000), (6000000, 8000000)),
         ((6000000, 7000000), (7000000, 8000000)),
         ((5000000, 7000000), (6000000, 8000000)),
         ((4500000, 6500000), (5500000, 7500000)),
         ((5000000, 6500000), (6500000, 8000000)),
         ((5500000, 7000000), (6500000, 8000000)),
         ((6500000, 7000000), (7500000, 8000000)))
SLOW_METRICS = continuous.SHAPES + ('intra', 'inter', 'mean_degree', 'second_degree_moment')


def summarize(source):
    segments = joint.check_lineage([source])
    joint.require(all(h['entry']['start_step'] == 0 and h['entry']['end_step'] == 8000000
                      for h in source['histories']), 'continuous 0–8M histories required')
    names = continuous.metric_names(source['plan']['system'])
    original = joint.segment.METRICS
    joint.segment.METRICS = names
    try:
        summary = joint.summarize(segments)
    finally:
        joint.segment.METRICS = original
    records = [dict(replica=h['entry']['replica'],
                    windows=continuous.mean_windows(source, h, names)) for h in source['histories']]
    sensitivity = continuous.graph_review.sensitivity.summarize(
        dict(records=records, windows_steps=500000), PAIRS)
    intervals = sorted({interval for comparison in PAIRS for interval in comparison} |
                       {(start, start + 500000) for start in range(0, 8000000, 500000)})
    slow_records = []
    for history in source['histories']:
        windows = []
        for start, end in intervals:
            selected = [row for row in history['rows'] if start < row['step'] <= end]
            windows.append(dict(start_step_exclusive=start, end_step_inclusive=end,
                segment=source['attempt'], transient_context=start < 1000000,
                metrics={name: joint.segment.review.estimate([row[name] for row in selected],
                    [row['time'] for row in selected]) for name in SLOW_METRICS}))
        slow_records.append(dict(replica=history['entry']['replica'], windows=windows))
    return summary, dict(schema_version=1, stage='E2_continuous8m_window_sensitivity',
        automatic_acceptance=False, records=records, comparisons=sensitivity['comparisons'],
        slow_interval_estimates=slow_records, independent_units=sensitivity['independent_units'],
        uncertainty=sensitivity['uncertainty'], windows_steps=500000,
        mean_policy='Exactly tiled 500k means; no pooling of IATs, SEMs or blocking uncertainties')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('dataset-root', 'attempt', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    joint.require(not args.output.exists(), 'immutable review output already exists')
    attempt = args.attempt.resolve()
    joint.require(joint.campaign.sha256(attempt / 'plan.json') == args.plan_sha256,
                  'source plan hash differs')
    sources = continuous.graph_review.authenticate_with_graphs(args.dataset_root.resolve(), [attempt])
    summary, sensitivity = summarize(sources[0])
    joint.write_report(summary, args.output / 'joint8m')
    files = [Path(__file__), Path(continuous.__file__), Path(continuous.graph_review.__file__),
             Path(joint.__file__), Path(continuous.graph_review.sensitivity.__file__),
             attempt / 'plan.json', attempt / 'approval.json']
    files += [attempt / f'r{r:03d}/complete.json' for r in (1, 2, 3)]
    hashes = joint.runner.hash_files(files)
    joint.runner.exclusive_json(args.output / 'window_sensitivity.json',
                                dict(sensitivity, source_sha256=hashes))
    source = sources[0]
    joint.runner.exclusive_json(args.output / 'provenance.json', dict(schema_version=1,
        stage='E2_joint_review_provenance', read_only=True, formal_acceptance=False,
        registry_activation=False, production_authorization=False,
        starting_git_sha=joint.campaign.git_sha(), source_sha256=hashes, source_plan=source['plan'],
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
