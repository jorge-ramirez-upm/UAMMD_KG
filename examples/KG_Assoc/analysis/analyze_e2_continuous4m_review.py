#!/usr/bin/env python3
"""Immutable 0–4M review using authenticated event/graph replay; no MD execution."""
import argparse
import csv
from pathlib import Path

import analyze_e2_continuous_review as continuous

joint = continuous.joint
graph = continuous.graph_review
PAIRS = (((1000000, 2000000), (2000000, 3000000)),
         ((2000000, 3000000), (3000000, 4000000)),
         ((1000000, 2000000), (3000000, 4000000)),
         ((3000000, 3500000), (3500000, 4000000)),
         ((2000000, 2500000), (3500000, 4000000)),
         ((1500000, 2500000), (2500000, 3500000)),
         ((2000000, 3500000), (2500000, 4000000)))


def summarize(source):
    joint.check_lineage([source])
    joint.require(all(h['entry']['start_step'] == 0 and h['entry']['end_step'] == 4000000
                      for h in source['histories']), 'continuous 0–4M histories required')
    names = continuous.metric_names(source['plan']['system'])
    records = [dict(replica=h['entry']['replica'],
                    windows=continuous.mean_windows(source, h, names))
               for h in source['histories']]
    sensitivity = graph.sensitivity.summarize(dict(records=records, windows_steps=500000), PAIRS)
    intervals = sorted({interval for pair in PAIRS for interval in pair} |
                       {(start, start + width) for width in (500000, 1000000)
                        for start in range(0, 4000000, width)})
    estimates = [dict(replica=h['entry']['replica'], windows=[
        graph.make_window(source, h, start, end) for start, end in intervals])
        for h in source['histories']]
    return dict(schema_version=1, stage='E2_continuous4m_scientific_review',
                automatic_acceptance=False, system=source['plan']['system'], records=records,
                interval_estimates=estimates, comparisons=sensitivity['comparisons'],
                independent_units=sensitivity['independent_units'],
                uncertainty=sensitivity['uncertainty'], windows_steps=500000,
                transient='All 0–1M frames retained as context, not stationary comparators',
                definitions='Degree counts distinct inter-star neighbors; satellites are non-singleton '
                            'components outside one largest component; L1 parallel bond pairs, L2 triangles',
                correlation_policy='Fresh interval IAT and 5/10/20 blocks; no averaging of errors or IATs')


def write_paths_and_figures(source, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fields = ('step', 'time') + continuous.metric_names(source['plan']['system'])
    for history in source['histories']:
        with (output / f"r{history['entry']['replica']:03d}_frames.csv").open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(history['rows'])
    groups = {'chemistry': ('bound_fraction', 'intra', 'inter', 'L1', 'L2', 'mean_degree'),
              'periphery': ('largest_cluster_fraction', 'components', 'isolated_stars',
                            'satellite_components', 'satellite_stars', 'second_degree_moment'),
              'shape': continuous.SHAPES}
    for label, names in groups.items():
        fig, axes = plt.subplots(len(names), 1, figsize=(10, 2.3 * len(names)), sharex=True)
        for axis, name in zip(axes, names):
            for history in source['histories']:
                rows = history['rows']
                replica = history['entry']['replica']
                line, = axis.plot([r['step'] / 1e6 for r in rows], [r[name] for r in rows],
                                  alpha=.22, linewidth=.5)
                means = continuous.mean_windows(source, history, (name,))
                axis.plot([(w['start_step_exclusive'] + 250000) / 1e6 for w in means],
                          [w['metrics'][name]['mean'] for w in means], 'o-',
                          color=line.get_color(), label=f'r{replica:03d}: 500k mean')
            axis.axvspan(0, 1, color='gray', alpha=.12)
            axis.set_ylabel(name)
            axis.legend(fontsize=7, loc='best')
        axes[-1].set_xlabel('Absolute MD step / million (shaded: initial context)')
        fig.tight_layout()
        fig.savefig(output / f'{label}.png', dpi=140)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', required=True, type=Path)
    parser.add_argument('--attempt', required=True, type=Path)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    joint.require(not args.output.exists(), 'immutable review output already exists')
    attempt = args.attempt.resolve()
    joint.require(joint.campaign.sha256(attempt / 'plan.json') == args.plan_sha256,
                  'source plan hash differs')
    source = graph.authenticate_with_graphs(args.dataset_root.resolve(), [attempt])[0]
    summary = summarize(source)
    args.output.mkdir(parents=True, exist_ok=False)
    joint.runner.exclusive_json(args.output / 'summary.json', summary)
    paths = [Path(__file__), Path(continuous.__file__), Path(graph.__file__), Path(joint.__file__),
             Path(graph.sensitivity.__file__), attempt / 'plan.json', attempt / 'approval.json']
    paths += [attempt / f'r{r:03d}/complete.json' for r in (1, 2, 3)]
    provenance = dict(schema_version=1, read_only=True, formal_acceptance=False,
        registry_activation=False, production_authorization=False,
        starting_git_sha=joint.campaign.git_sha(), source_sha256=joint.runner.hash_files(paths),
        source_plan=source['plan'], build_authentication_scope=source['build_authentication_scope'],
        validated_histories=[dict(entry=h['entry'], validation=h['validation'])
                             for h in source['histories']],
        proposed_endpoints=[dict(replica=h['entry']['replica'], prefix=h['entry']['output_prefix'],
            end_step=h['entry']['end_step'], chemistry_seed=h['entry']['chemistry_seed'],
            md_seed=h['entry']['md_seed'], effective_md_seed=h['entry']['effective_md_seed'],
            state_sha256={h['entry']['output_prefix'] + suffix: digest
                          for suffix, digest in h['validation']['output_sha256'].items()})
            for h in source['histories']])
    joint.runner.exclusive_json(args.output / 'provenance.json', provenance)
    write_paths_and_figures(source, args.output)
    print('Read-only 4M review complete: ' + str(args.output), flush=True)


if __name__ == '__main__':
    main()
