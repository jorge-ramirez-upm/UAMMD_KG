#!/usr/bin/env python3
"""CPU-only exact Ee12 review. Raw inputs are read-only; output must be new."""
import argparse
import csv
from pathlib import Path
import sys

REPOSITORY = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY / 'examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014'))
import reproduce_joint as reused

joint = reused.joint
ROOT = reused.ROOT
ATTEMPT = ROOT / ('banks/e2_attempts/F04_N010_RP080_EE12/'
                  'equilibrate_9be4b5a8840d48b79b2bc5f9d714f9c0')
PLAN_HASH = '80c888e6adb0c5738cd549fe119a6ac188cc08b621dc4554da235f4095c822bc'
SYSTEM = 'F04_N010_RP080_EE12_EA04'
CHECKPOINT = ROOT / 'aggregate/e2/review_4026917652c74ffd97eda5650adedf6d'
WIDTHS = (500000, 1000000, 2000000, 4000000)
PAIRS = tuple(((a, a + width), (a + width, a + 2 * width))
              for width in WIDTHS
              for a in range(0, 16000000 - 2 * width + 1, width)) + (
    ((4000000, 8000000), (12000000, 16000000)),
    ((6000000, 10000000), (10000000, 14000000)),
    ((9000000, 13000000), (11000000, 15000000)),
    ((10000000, 14000000), (12000000, 16000000)),
    ((11000000, 13000000), (13000000, 15000000)),
    ((11000000, 13000000), (14000000, 16000000)),
    ((13000000, 14000000), (15000000, 16000000)),
    ((14000000, 15500000), (14500000, 16000000)),
    ((14500000, 15500000), (15000000, 16000000)),
    ((15500000, 15750000), (15750000, 16000000)))


def verify_inputs():
    directory = Path(__file__).parent
    joint.runner.check_hashes(joint.campaign.load_json(directory / 'PRESERVED_SHA256.json'))
    authentication = joint.campaign.load_json(directory / 'AUTHENTICATION.json')
    joint.runner.check_hashes(authentication['lammps']['source_sha256'])
    reference = authentication['reference_record']
    joint.runner.check_hashes({reference['path']: reference['sha256']})
    joint.require(joint.campaign.load_json(reference['path']) == reference['record'],
                  'qualified Ee10 reference differs')
    joint.runner.check_hashes(joint.campaign.load_json(CHECKPOINT / 'review_complete.json')['report_sha256'])
    import kg_assoc_e2_registry as registry
    registry.exclusive_validate(reference['record'], [joint.runner.system_by_id(
        'F04_N010_RP080_EE10_EA04')])
    joint.require(len(authentication['prior_acceptance_sha256']) == 11, 'eleven records required')
    joint.runner.check_hashes(authentication['prior_acceptance_sha256'])
    plan = joint.runner.check_plan(ROOT, ATTEMPT)
    for entry, witness in zip(plan['histories'], authentication['execution']):
        started = joint.campaign.load_json(Path(entry['output_prefix']).parent / 'started.json')
        joint.require(started == witness['started'] and started['command'] == entry['command'] and
                      started['plan_sha256'] == PLAN_HASH and started['approval_sha256'] ==
                      joint.campaign.sha256(ATTEMPT / 'approval.json'), 'execution witness differs')
        joint.runner.check_hashes(started['smoke_sha256'])
    config = joint.campaign.load_json(CHECKPOINT / 'analysis_config.json')
    joint.require(config['attempt'] == str(ATTEMPT) and config['plan_sha256'] == PLAN_HASH and
                  config['discard_steps'] == 0 and config['window_steps'] == 500000,
                  'checkpoint coverage differs')
    joint.runner.check_hashes(config['source_sha256'])


def authenticate():
    joint.require(joint.campaign.sha256(ATTEMPT / 'plan.json') == PLAN_HASH,
                  'exact source plan differs')
    analysis = reused.multigraph.analysis
    original = analysis.topology.frame_observables
    captures = []

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        if args[0] == 0:
            captures.append([])
        captures[-1].append((int(args[1]), reused.multigraph.distributions(result, 1000, 4)))
        return result

    analysis.topology.frame_observables = capture
    try:
        source = reused.graph.authenticate_with_graphs(ROOT, [ATTEMPT])[0]
    finally:
        analysis.topology.frame_observables = original
    joint.require(len(captures) == 3, 'three independent histories required')
    for history, frames in zip(source['histories'], captures):
        joint.require([step for step, _ in frames] == list(range(0, 16000001, 1000)),
                      'full multiplicity context differs')
        for row, (step, values) in zip(history['rows'], frames):
            joint.require(row['step'] == step and row['L1'] ==
                          sum(k * (k - 1) / 2 * values[f'edges_m{k}'] for k in range(1, 5)),
                          'L1 multiplicity accounting differs')
            joint.require(row['intra'] == values['stars_intra_loops_1'] +
                          2 * values['stars_intra_loops_2'], 'intra-loop accounting differs')
            row.update(values)
    return source


def write_evidence(source, output):
    joint.check_lineage([source])
    joint.require(source['plan']['system']['system_id'] == SYSTEM and
                  all((h['entry']['start_step'], h['entry']['end_step']) == (0, 16000000)
                      for h in source['histories']), 'exact Ee12 0–16M scope required')
    joint.require(not output.exists(), 'immutable output already exists')
    extra = tuple(k for k in source['histories'][0]['rows'][0]
                  if k.startswith(('edges_m', 'stars_intra_loops_'))) + (
        'mean_edge_multiplicity', 'fraction_parallel_edges', 'max_edge_multiplicity')
    intervals = sorted({i for pair in PAIRS for i in pair} |
                       {(a, a + width) for width in WIDTHS
                        for a in range(0, 16000000, width)} |
                       {(a, a + 250000) for a in range(14000000, 16000000, 250000)})
    records = []
    original_metrics = joint.segment.METRICS
    joint.segment.METRICS = original_metrics + extra
    try:
        for history in source['histories']:
            windows = [reused.previous.fresh_window(source, history, start, end)
                       for start, end in intervals]
            records.append(dict(replica=history['entry']['replica'], windows=windows))
            print('Fresh 500k/1M/2M/4M estimates r%03d' % history['entry']['replica'], flush=True)
    finally:
        joint.segment.METRICS = original_metrics
    comparisons = [c for early, late in PAIRS for c in reused.compare(records, early, late)]
    output.mkdir(parents=True, exist_ok=False)
    joint.runner.exclusive_json(output / 'summary.json', dict(schema_version=1,
        system=source['plan']['system'], records=records, comparisons=comparisons,
        automatic_acceptance=False, independent_units='three original histories; Student-t df=2',
        uncertainty='exploratory unadjusted paired intervals; zero inclusion is not stationarity',
        transient_policy='step zero and all 0–16M windows retained; early contrasts labeled context'))
    paths = [Path(__file__), Path(reused.__file__), Path(reused.previous.__file__),
             Path(reused.multigraph.__file__), Path(reused.graph.__file__), Path(joint.__file__)]
    paths += [Path(reused.previous.continuous.__file__),
              Path(reused.graph.sensitivity.__file__), Path(joint.segment.review.__file__),
              Path(joint.segment.review.analysis.stationarity.__file__)]
    paths += [ATTEMPT / name for name in ('plan.json', 'approval.json', 'r001/complete.json',
                                        'r002/complete.json', 'r003/complete.json')]
    joint.runner.exclusive_json(output / 'provenance.json', dict(schema_version=1,
        read_only=True, formal_acceptance=False, registry_selection=False,
        production_authorization=False, starting_git_sha=joint.campaign.git_sha(),
        source_sha256=joint.runner.hash_files(paths), source_plan=source['plan'],
        build_authentication_scope=source['build_authentication_scope'],
        validated_histories=[dict(entry=h['entry'], validation=h['validation'])
                             for h in source['histories']],
        proposed_endpoints=[dict(replica=h['entry']['replica'], prefix=h['entry']['output_prefix'],
            end_step=h['entry']['end_step'], chemistry_seed=h['entry']['chemistry_seed'],
            md_seed=h['entry']['md_seed'], effective_md_seed=h['entry']['effective_md_seed'],
            state_sha256={h['entry']['output_prefix'] + suffix: digest
                          for suffix, digest in h['validation']['output_sha256'].items()})
            for h in source['histories']]))
    names = reused.previous.continuous.metric_names(source['plan']['system']) + extra + (
        'temperature', 'min_permanent_bond', 'max_permanent_bond')
    for history in source['histories']:
        with (output / ('r%03d_frames.csv' % history['entry']['replica'])).open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=('step', 'time') + names,
                                    extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            writer.writerows(history['rows'])
    with (output / 'window_estimates.csv').open('x') as stream:
        fields = ('replica', 'start_step', 'end_step', 'initial_context', 'category',
                  'observable', 'mean', 'tau_time', 'effective_samples_estimate', 'slope',
                  'sem_estimate', 'sem_5', 'sem_10', 'sem_20', 'resolution_warning')
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for record in records:
            for window in record['windows']:
                for category in ('metrics', 'activity'):
                    for name, value in window[category].items():
                        writer.writerow(dict(replica=record['replica'],
                            start_step=window['start_step_exclusive'],
                            end_step=window['end_step_inclusive'],
                            initial_context=window['start_step_exclusive'] < 1000000,
                            category=category, observable=name,
                            **{k: value[k] for k in ('mean', 'tau_time',
                                'effective_samples_estimate', 'slope', 'sem_estimate',
                                'resolution_warning')},
                            **{'sem_' + str(k): v for k, v in
                               value['blocking_sem_sensitivity'].items()}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    joint.require(not args.output.exists(), 'immutable output already exists')
    verify_inputs()
    write_evidence(authenticate(), args.output)


if __name__ == '__main__':
    main()
