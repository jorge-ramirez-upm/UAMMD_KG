#!/usr/bin/env python3
"""CPU-only authenticated 0–8M review with segment-local correlation estimates."""
import argparse
import collections
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
BANK = ROOT / 'banks/e2_attempts/F04_N010_RP040_EE08'
ATTEMPTS = (BANK / 'equilibrate_704163de5b044a3f8293eedd2e1c5304',
            BANK / 'equilibrate_ea8bd8e305aa4edfa9871dc977213948')
PLAN_HASHES = ('5884973e9a8db39cf40fbb5e0e4298a65b41c517e76db1b60f0552cfbdb79b50',
               'b88f2eec2bdff278393d11db52252abb1bcbb9bbdbca3edeb374d3022d10e6c4')
PAIRS = tuple(((a, a + width), (a + width, a + 2 * width))
    for width in (500000, 1000000, 2000000)
    for a in range(width, 8000000 - 2 * width + 1, width) if a >= 1000000) + (
    ((1000000, 2000000), (7000000, 8000000)),
    ((1000000, 3000000), (6000000, 8000000)),
    ((2000000, 4000000), (6000000, 8000000)),
    ((5000000, 6000000), (7000000, 8000000)),
    ((4500000, 6000000), (6500000, 8000000)),
    ((3500000, 5500000), (6000000, 8000000)),
    ((6000000, 7500000), (6500000, 8000000)),
    ((6250000, 7250000), (6750000, 7750000)))


def local_source(sources, replica, start, end):
    joint.require(0 <= start < end <= 8000000, 'invalid interval')
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
    # Reauthenticate original executable bytes preserved before the extension build.
    archive_path = ROOT / 'aggregate/e2/rp040_6to8m_20261014_22da4b77d556/historical_binary_archive.json'
    archive = joint.campaign.load_json(archive_path)
    joint.require(archive['source_plan_sha256'] == PLAN_HASHES[0] and
        {p: v['sha256'] for p, v in archive['executable_archives'].items()} ==
        sources[0]['plan']['build']['executable_sha256'], 'archived build identity differs')
    joint.runner.check_hashes({v['archive']: v['sha256'] for v in archive['executable_archives'].values()})
    sources[0]['build_authentication_scope'] = 'original_archived_binary_bytes_and_source_build_logs_authenticated'
    return sources


def write_evidence(sources, output):
    joint.check_lineage(sources)
    joint.require([[(h['entry']['start_step'], h['entry']['end_step']) for h in s['histories']]
        for s in sources] == [[(0, 6000000)] * 3, [(6000000, 8000000)] * 3],
        'exact 0–6M and 6–8M segments required')
    joint.require(all(s['plan']['system']['system_id'] == 'F04_N010_RP040_EE08_EA04'
                      for s in sources), 'wrong system')
    output.mkdir(parents=True, exist_ok=False)
    extra = tuple(k for k in sources[0]['histories'][0]['rows'][0]
        if k.startswith('edges_m') or k.startswith('stars_intra_loops_')) + (
        'mean_edge_multiplicity', 'fraction_parallel_edges', 'max_edge_multiplicity')
    intervals = sorted({i for pair in PAIRS for i in pair} |
        {(a, a + width) for width in (500000, 1000000, 2000000)
         for a in range(0, 8000000, width)} |
        {(7500000, 7750000), (7750000, 8000000)})
    records = []
    original_metrics = joint.segment.METRICS
    joint.segment.METRICS = original_metrics + extra
    try:
        for replica in (1, 2, 3):
            windows = []
            for start, end in intervals:
                source, history = local_source(sources, replica, start, end)
                windows.append(previous.fresh_window(source, history, start, end))
            records.append(dict(replica=replica, windows=windows))
            print('Segment-local estimates r%03d complete' % replica, flush=True)
    finally:
        joint.segment.METRICS = original_metrics
    comparisons = [c for early, late in dict.fromkeys(PAIRS) for c in compare(records, early, late)]
    joint.runner.exclusive_json(output / 'summary.json', dict(schema_version=1,
        system=sources[-1]['plan']['system'], records=records, comparisons=comparisons,
        automatic_acceptance=False, independent_units='three original histories; Student-t df=2',
        boundary_policy='IAT/SEM estimates remain segment-local; no interval crosses 6M reseeding',
        uncertainty='exploratory unadjusted paired intervals; zero-containing intervals do not prove stationarity'))
    sources_hashes = joint.runner.hash_files([Path(__file__), Path(previous.__file__),
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
    names = previous.continuous.metric_names(sources[-1]['plan']['system']) + extra
    for replica in (1, 2, 3):
        rows = sources[0]['histories'][replica - 1]['rows'] + sources[1]['histories'][replica - 1]['rows'][1:]
        joint.require([r['step'] for r in rows] == list(range(0, 8000001, 1000)), 'full context coverage differs')
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
    write_evidence(authenticate(), args.output)


if __name__ == '__main__':
    main()
