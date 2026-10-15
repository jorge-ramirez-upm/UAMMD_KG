#!/usr/bin/env python3
"""CPU-only authenticated 0–12M review with segment-local correlation estimates."""
import argparse
import copy
import csv
from pathlib import Path
import sys

REPOSITORY = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(REPOSITORY / 'examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014'),
    str(REPOSITORY / 'examples/KG_Assoc/analysis'), str(REPOSITORY / 'examples/KG_Assoc/campaign')]
import reproduce as previous
import multiplicity as multigraph

joint = previous.joint
graph = previous.graph
ROOT = REPOSITORY / 'examples/KG_Assoc/kg_assoc_100m'
BANK = ROOT / 'banks/e2_attempts/F04_N010_RP080_EE10'
ATTEMPTS = (BANK / 'equilibrate_fb8954dc860740d6b923759b2b21a703',
            BANK / 'equilibrate_18d492ee0f4b4a7d98ca32e39ce8f95a')
PLAN_HASHES = ('489af3d03ca1d54a1c42515b59961fea7fa889378410b5ddac8b835bd8f06812',
               '9ceb3ce52582e1e781ee36072b4018254dca0f663f58a73edb3111093322f28a')
OLD_REVIEW = REPOSITORY / 'examples/KG_Assoc/reviews/e2_ee10_8m_20261015'
SYSTEM = 'F04_N010_RP080_EE10_EA04'
PAIRS = tuple(((a, a + width), (a + width, a + 2 * width))
    for width in (500000, 1000000, 2000000)
    for a in range(0, 12000000 - 2 * width + 1, width)) + (
    ((6000000, 8000000), (10000000, 12000000)),
    ((8000000, 10000000), (10000000, 12000000)),
    ((8000000, 11000000), (9000000, 12000000)),
    ((8500000, 10500000), (9500000, 11500000)),
    ((9000000, 11000000), (10000000, 12000000)),
    ((9500000, 11000000), (10500000, 12000000)),
    ((10250000, 11250000), (10750000, 11750000)),
    ((11500000, 11750000), (11750000, 12000000)))


def verify_inputs():
    directory = Path(__file__).parent
    joint.runner.check_hashes(joint.campaign.load_json(directory / 'PRESERVED_SHA256.json'))
    auth = joint.campaign.load_json(directory / 'AUTHENTICATION.json')
    joint.runner.check_hashes(auth['old_review_sha256'])
    joint.runner.check_hashes(auth['lammps']['source_sha256'])
    integrity = joint.campaign.load_json(OLD_REVIEW / 'INTEGRITY.json')
    joint.runner.check_hashes({str(OLD_REVIEW / n): h for n, h in integrity['sha256'].items()})
    for attempt in ATTEMPTS:
        plan = joint.runner.check_plan(ROOT, attempt)
        for entry in plan['histories']:
            receipt = joint.campaign.load_json(Path(entry['output_prefix']).parent / 'started.json')
            witness = next(w for w in auth['execution'] if
                w['attempt'] == str(attempt) and w['replica'] == entry['replica'])
            joint.require(receipt == witness['started'] and receipt['command'] == entry['command'],
                          'execution witness differs')
            joint.runner.check_hashes(receipt['smoke_sha256'])


def local_source(sources, replica, start, end):
    joint.require(0 <= start < end <= 12000000, 'invalid interval')
    matches = [(s, s['histories'][replica - 1]) for s in sources
        if s['histories'][replica - 1]['entry']['start_step'] <= start and
           end <= s['histories'][replica - 1]['entry']['end_step']]
    joint.require(len(matches) == 1, 'interval crosses MD-reseeding boundary')
    return matches[0]


def compare(records, early, late):
    joint.require([r['replica'] for r in records] == [1, 2, 3], 'three original histories required')
    chosen = [[next(w for w in r['windows'] if
        (w['start_step_exclusive'], w['end_step_inclusive']) == interval)
        for r in records] for interval in (early, late)]
    result = []
    for category in ('metrics', 'activity'):
        for name in chosen[0][0][category]:
            a = [w[category][name]['mean'] for w in chosen[0]]
            b = [w[category][name]['mean'] for w in chosen[1]]
            changes = [new - old for old, new in zip(a, b)]
            stats = joint.segment.review.analysis.dynamics.replica_statistics(changes)
            result.append(dict(category=category, observable=name, early_steps=early, late_steps=late,
                early_replica_means=a, late_replica_means=b, per_replica_changes=changes,
                overlapping_steps=max(0, min(early[1], late[1]) - max(early[0], late[0])),
                **stats, excludes_zero=abs(stats['mean']) > stats['ci95_half_width']))
    return result


def authenticate():
    for path, digest in zip(ATTEMPTS, PLAN_HASHES):
        joint.require(joint.campaign.sha256(path / 'plan.json') == digest, 'exact plan hash differs')
    captured = []
    analysis = multigraph.analysis
    original = analysis.topology.frame_observables

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        if args[0] == 0:
            captured.append([])
        captured[-1].append((int(args[1]), multigraph.distributions(result, 1000, 4)))
        return result

    analysis.topology.frame_observables = capture
    try:
        sources = graph.authenticate_with_graphs(ROOT, list(ATTEMPTS))
    finally:
        analysis.topology.frame_observables = original
    histories = [h for s in sources for h in s['histories']]
    joint.require(len(captured) == 6, 'six segment/replica captures required')
    for h, frames in zip(histories, captured):
        joint.require([step for step, _ in frames] == [r['step'] for r in h['rows']],
                      'multigraph frame coverage differs')
        for row, (_, values) in zip(h['rows'], frames):
            joint.require(row['L1'] == sum(k * (k - 1) / 2 * values[f'edges_m{k}']
                for k in range(1, 5)) and row['intra'] ==
                values['stars_intra_loops_1'] + 2 * values['stars_intra_loops_2'],
                'L1/intra distribution accounting differs')
            row.update(values)
    return sources


def write_evidence(sources, output):
    joint.check_lineage(sources)
    joint.require([[(h['entry']['start_step'], h['entry']['end_step']) for h in s['histories']]
        for s in sources] == [[(0, 8000000)] * 3, [(8000000, 12000000)] * 3],
        'exact 0–8M and 8–12M segments required')
    joint.require(all(s['plan']['system']['system_id'] == 'F04_N010_RP080_EE10_EA04'
                      for s in sources), 'wrong system')
    output.mkdir(parents=True, exist_ok=False)
    extra = tuple(k for k in sources[0]['histories'][0]['rows'][0]
        if k.startswith('edges_m') or k.startswith('stars_intra_loops_')) + (
        'mean_edge_multiplicity', 'fraction_parallel_edges', 'max_edge_multiplicity')
    intervals = sorted({i for pair in PAIRS for i in pair} |
        {(a, a + width) for width in (500000, 1000000, 2000000)
         for a in range(0, 12000000, width)} |
        {(a, a + 250000) for a in range(10000000, 12000000, 250000)})
    records = []
    cache = joint.campaign.load_json(OLD_REVIEW / 'evidence/summary.json')
    original_metrics = joint.segment.METRICS
    joint.segment.METRICS = original_metrics + extra
    try:
        for replica in (1, 2, 3):
            windows = []
            for start, end in intervals:
                source, history = local_source(sources, replica, start, end)
                cached = [w for w in cache['records'][replica - 1]['windows'] if
                    (w['start_step_exclusive'], w['end_step_inclusive']) == (start, end)]
                if source is sources[0] and cached:
                    window = copy.deepcopy(cached[0])
                    window['statistics_source'] = dict(path=str(OLD_REVIEW / 'evidence/summary.json'),
                        sha256=joint.campaign.sha256(OLD_REVIEW / 'evidence/summary.json'))
                else:
                    window = previous.fresh_window(source, history, start, end)
                windows.append(window)
            records.append(dict(replica=replica, windows=windows))
            print('Segment-local estimates r%03d complete' % replica, flush=True)
    finally:
        joint.segment.METRICS = original_metrics
    comparisons = [c for early, late in dict.fromkeys(PAIRS) for c in compare(records, early, late)]
    joint.runner.exclusive_json(output / 'summary.json', dict(schema_version=1,
        system=sources[-1]['plan']['system'], records=records, comparisons=comparisons,
        automatic_acceptance=False, independent_units='three original histories; Student-t df=2',
        boundary_policy='IAT/SEM estimates remain segment-local; no interval crosses 8M reseeding',
        uncertainty='exploratory unadjusted paired intervals; zero-containing intervals do not prove stationarity'))
    sources_hashes = joint.runner.hash_files([Path(__file__), OLD_REVIEW / 'INTEGRITY.json',
        OLD_REVIEW / 'evidence/summary.json', Path(previous.__file__),
        Path(multigraph.__file__), Path(graph.__file__), Path(joint.__file__)] +
        [p / n for p in ATTEMPTS for n in ('plan.json', 'approval.json',
                                         'r001/complete.json', 'r002/complete.json', 'r003/complete.json')])
    joint.runner.exclusive_json(output / 'provenance.json', dict(schema_version=1,
        read_only=True, formal_acceptance=False, registry_selection=False, production_authorization=False,
        starting_git_sha=joint.campaign.git_sha(), source_sha256=sources_hashes,
        source_authentication=[dict(attempt=s['attempt'], plan=s['plan'],
            build_authentication_scope=s['build_authentication_scope'],
            histories=[dict(entry=h['entry'], validation=h['validation']) for h in s['histories']])
            for s in sources], proposed_endpoints=[dict(replica=h['entry']['replica'],
            prefix=h['entry']['output_prefix'], end_step=h['entry']['end_step'],
            chemistry_seed=h['entry']['chemistry_seed'], md_seed=h['entry']['md_seed'],
            effective_md_seed=h['entry']['effective_md_seed'],
            state_sha256={h['entry']['output_prefix'] + suffix: digest for suffix, digest in
                          h['validation']['output_sha256'].items()}) for h in sources[-1]['histories']]))
    names = previous.continuous.metric_names(sources[-1]['plan']['system']) + extra + (
        'temperature', 'min_permanent_bond', 'max_permanent_bond')
    for replica in (1, 2, 3):
        rows = sources[0]['histories'][replica - 1]['rows'] + sources[1]['histories'][replica - 1]['rows'][1:]
        joint.require([r['step'] for r in rows] == list(range(0, 12000001, 1000)), 'full context coverage differs')
        with (output / ('r%03d_frames.csv' % replica)).open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=('step', 'time') + names,
                                    extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    joint.require(not args.output.exists(), 'immutable output already exists')
    verify_inputs()
    write_evidence(authenticate(), args.output)


if __name__ == '__main__':
    main()
