#!/usr/bin/env python3
"""Read-only dossier reproduction; output must be a new directory. Never runs MD."""
import argparse
import csv
from pathlib import Path
import statistics
import sys
from types import FunctionType, SimpleNamespace

REPOSITORY = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(REPOSITORY / 'examples/KG_Assoc/analysis'),
               str(REPOSITORY / 'examples/KG_Assoc/campaign')]
import analyze_e2_continuous_review as continuous
import analyze_e2_continuous4m_review as figures

joint = continuous.joint
graph = continuous.graph_review
PLAN_HASH = '5884973e9a8db39cf40fbb5e0e4298a65b41c517e76db1b60f0552cfbdb79b50'
ATTEMPT = REPOSITORY / ('examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/'
    'F04_N010_RP040_EE08/equilibrate_704163de5b044a3f8293eedd2e1c5304')
PAIRS = continuous.PAIRS + graph.sensitivity.PAIRS + (
    ((1000000, 2000000), (5000000, 6000000)),
    ((1000000, 3000000), (4000000, 6000000)),
    ((5000000, 5500000), (5500000, 6000000)))
BASE_IAT = joint.segment.review.analysis.stationarity.iat


def memoized_iat(values, times):
    """Execute unchanged IAT bytecode; cache its repeated identical mean call."""
    cached = []

    def mean(argument):
        joint.require(argument is values, 'IAT mean-cache input convention changed')
        if not cached:
            cached.append(statistics.mean(values))
        return cached[0]

    namespace = dict(BASE_IAT.__globals__, statistics=SimpleNamespace(mean=mean))
    return FunctionType(BASE_IAT.__code__, namespace)(values, times)


def fresh_window(source, history, start, end):
    # The source helper redundantly recomputes the same mean for each centered sample.
    # No arithmetic is reordered; the original function is restored after every window.
    stationarity = joint.segment.review.analysis.stationarity
    original = stationarity.iat
    stationarity.iat = memoized_iat
    try:
        return graph.make_window(source, history, start, end)
    finally:
        stationarity.iat = original


def write_evidence(source, output):
    joint.check_lineage([source])
    joint.require(source['plan']['system']['system_id'] == 'F04_N010_RP040_EE08_EA04' and
        all(h['entry']['start_step'] == 0 and h['entry']['end_step'] == 6000000
            for h in source['histories']), 'exact RP040 0–6M histories required')
    output.mkdir(parents=True, exist_ok=False)
    names = continuous.metric_names(source['plan']['system'])
    records = [dict(replica=h['entry']['replica'],
                   windows=continuous.mean_windows(source, h, names))
               for h in source['histories']]
    paired = graph.sensitivity.summarize(dict(records=records, windows_steps=500000),
                                        tuple(dict.fromkeys(PAIRS)))
    intervals = sorted({i for p in PAIRS for i in p} |
        {(a, a + width) for width in (500000, 1000000, 2000000)
         for a in range(0, 6000000, width)} |
        {(a, a + 250000) for a in range(5000000, 6000000, 250000)})
    estimates = []
    for history in source['histories']:
        windows = []
        for start, end in intervals:
            selected = [r for r in history['rows'] if start < r['step'] <= end]
            joint.require([r['step'] for r in selected] == list(range(start + 1000, end + 1, 1000)),
                          'missing diagnostic frame')
            window = fresh_window(source, history, start, end)
            windows.append(window)
        estimates.append(dict(replica=history['entry']['replica'], windows=windows))
        print('Fresh interval estimates r%03d' % history['entry']['replica'], flush=True)
    joint.runner.exclusive_json(output / 'summary.json', dict(schema_version=1,
        system=source['plan']['system'], records=records, windows_steps=500000,
        interval_estimates=estimates, **{k: v for k, v in paired.items() if k != 'schema_version'}))
    paths = [Path(__file__), Path(continuous.__file__), Path(figures.__file__),
        Path(graph.__file__), Path(joint.__file__), Path(graph.sensitivity.__file__),
        ATTEMPT / 'plan.json', ATTEMPT / 'approval.json']
    paths += [ATTEMPT / ('r%03d/complete.json' % r) for r in (1, 2, 3)]
    joint.runner.exclusive_json(output / 'provenance.json', dict(schema_version=1,
        read_only=True, formal_acceptance=False, registry_activation=False,
        production_authorization=False, starting_git_sha=joint.campaign.git_sha(),
        source_sha256=joint.runner.hash_files(paths), source_plan=source['plan'],
        build_authentication_scope=source['build_authentication_scope'],
        validated_histories=[dict(entry=h['entry'], validation=h['validation'])
                             for h in source['histories']],
        proposed_endpoints=[dict(replica=h['entry']['replica'], prefix=h['entry']['output_prefix'],
            end_step=h['entry']['end_step'], chemistry_seed=h['entry']['chemistry_seed'],
            md_seed=h['entry']['md_seed'], effective_md_seed=h['entry']['effective_md_seed'],
            state_sha256={h['entry']['output_prefix'] + suffix: digest for suffix, digest in
                          h['validation']['output_sha256'].items()}) for h in source['histories']]))
    figures.write_paths_and_figures(source, output)
    with (output / 'window_estimates.csv').open('x') as stream:
        fields = ('replica', 'start_step', 'end_step', 'category', 'observable', 'mean',
                  'tau_time', 'effective_samples_estimate', 'slope', 'sem_estimate',
                  'sem_5', 'sem_10', 'sem_20', 'resolution_warning')
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for record in estimates:
            for window in record['windows']:
                for category in ('metrics', 'activity'):
                    for name, value in window[category].items():
                        writer.writerow(dict(replica=record['replica'],
                            start_step=window['start_step_exclusive'],
                            end_step=window['end_step_inclusive'], category=category, observable=name,
                            **{k: value[k] for k in ('mean', 'tau_time', 'effective_samples_estimate',
                                'slope', 'sem_estimate', 'resolution_warning')},
                            **{'sem_' + str(k): v for k, v in value['blocking_sem_sensitivity'].items()}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    joint.require(not args.output.exists(), 'immutable output already exists')
    joint.require(joint.campaign.sha256(ATTEMPT / 'plan.json') == PLAN_HASH, 'source plan hash differs')
    root = REPOSITORY / 'examples/KG_Assoc/kg_assoc_100m'
    source = graph.authenticate_with_graphs(root, [ATTEMPT])[0]
    write_evidence(source, args.output)


if __name__ == '__main__':
    main()
