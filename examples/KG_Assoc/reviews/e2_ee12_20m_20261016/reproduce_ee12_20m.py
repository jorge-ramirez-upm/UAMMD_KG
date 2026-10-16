#!/usr/bin/env python3
"""CPU-only authenticated 0–20M review with segment-local correlation estimates."""
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
BANK = ROOT / 'banks/e2_attempts/F04_N010_RP080_EE12'
ATTEMPTS = (BANK / 'equilibrate_9be4b5a8840d48b79b2bc5f9d714f9c0',
            BANK / 'equilibrate_553522b9ed9b4253a6b910d817ad65f8')
PLAN_HASHES = ('80c888e6adb0c5738cd549fe119a6ac188cc08b621dc4554da235f4095c822bc',
               '5d0045e99d2c7631a4c8d96416229c07d9e12d241a9753e8ba721f8d4071b0b9')
OLD_REVIEW = REPOSITORY / 'examples/KG_Assoc/reviews/e2_ee12_16m_20261015'
SYSTEM = 'F04_N010_RP080_EE12_EA04'
CHECKPOINT = ROOT / 'aggregate/e2/review_ff92b2fc3f5342ae9fd2409391d39c4c'
WIDTHS = (500000, 1000000, 2000000, 4000000)
PAIRS = tuple(((a, a + width), (a + width, a + 2 * width))
    for width in WIDTHS for a in range(0, 20000000 - 2 * width + 1, width)) + (
    ((8000000, 12000000), (16000000, 20000000)),
    ((14000000, 16000000), (18000000, 20000000)),
    ((16000000, 19000000), (17000000, 20000000)),
    ((16000000, 18000000), (17500000, 19500000)),
    ((16500000, 18500000), (17500000, 19500000)),
    ((17000000, 19000000), (18000000, 20000000)),
    ((17000000, 18500000), (18500000, 20000000)),
    ((18000000, 19500000), (18500000, 20000000)),
    ((18250000, 19250000), (18750000, 19750000)),
    ((19500000, 19750000), (19750000, 20000000)))


def verify_inputs():
    directory = Path(__file__).parent
    joint.runner.check_hashes(joint.campaign.load_json(directory / 'PRESERVED_SHA256.json'))
    auth = joint.campaign.load_json(directory / 'AUTHENTICATION.json')
    joint.runner.check_hashes(auth['old_review_sha256'])
    joint.runner.check_hashes(auth['lammps']['source_sha256'])
    integrity = joint.campaign.load_json(OLD_REVIEW / 'INTEGRITY.json')
    joint.runner.check_hashes({str(OLD_REVIEW / n): h for n, h in integrity['sha256'].items()})
    joint.runner.check_hashes(auth['prior_acceptance_sha256'])
    joint.require(len(auth['prior_acceptance_sha256']) == 11, 'eleven prior records required')
    for attempt in ATTEMPTS:
        plan = joint.runner.check_plan(ROOT, attempt)
        for entry in plan['histories']:
            receipt = joint.campaign.load_json(Path(entry['output_prefix']).parent / 'started.json')
            witness = next(w for w in auth['execution'] if
                w['attempt'] == str(attempt) and w['replica'] == entry['replica'])
            joint.require(receipt == witness['started'] and receipt['command'] == entry['command'],
                          'execution witness differs')
            joint.require(receipt['plan_sha256'] == joint.campaign.sha256(attempt / 'plan.json') and
                receipt['approval_sha256'] == joint.campaign.sha256(attempt / 'approval.json'),
                'execution approval binding differs')
            joint.runner.check_hashes(receipt['smoke_sha256'])
    config = joint.campaign.load_json(CHECKPOINT / 'analysis_config.json')
    joint.require(config['attempt'] == str(ATTEMPTS[-1]) and
        config['plan_sha256'] == PLAN_HASHES[-1] and config['discard_steps'] == 0 and
        config['window_steps'] == 500000, 'extension checkpoint differs')
    joint.runner.check_hashes(config['source_sha256'])
    joint.runner.check_hashes(joint.campaign.load_json(CHECKPOINT / 'review_complete.json')['report_sha256'])


def local_source(sources, replica, start, end):
    joint.require(0 <= start < end <= 20000000, 'invalid interval')
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


def peripheral_membership(graph):
    """Identify every sampled satellite component; isolated identities are exact."""
    isolated = sorted(star for star, degree in graph['neighbor_degree'].items() if degree == 0)
    satellites = []
    if any(size > 1 for size in graph['component_sizes'][1:]):
        remaining = set(graph['neighbors'])
        components = []
        while remaining:
            seed = min(remaining)
            stack = [seed]
            component = set()
            while stack:
                star = stack.pop()
                if star in component:
                    continue
                component.add(star)
                stack.extend(graph['neighbors'][star] - component)
            remaining -= component
            components.append(sorted(component))
        components.sort(key=lambda c: (-len(c), c))
        satellites = [c for c in components[1:] if len(c) > 1]
        joint.require(sorted([len(c) for c in components], reverse=True) == graph['component_sizes'],
                      'component membership sizes differ')
    return dict(isolated=isolated, satellites=satellites)


def boundary_proof(sources):
    records = []
    for old, new in zip(sources[0]['histories'], sources[1]['histories']):
        a, b = old['entry'], new['entry']
        metadata, partners = joint.runner.validation.analysis.restart.read_metadata(
            a['output_prefix'] + '.assoc_restart')
        _, initial = joint.runner.validation.read_parent(b)
        joint.require(partners == initial['pairs'] and
            initial['creations'] == old['rows'][-1]['creations'] == new['rows'][0]['creations'] and
            initial['breaks'] == old['rows'][-1]['breaks'] == new['rows'][0]['breaks'],
            'chemical boundary state differs')
        records.append(dict(replica=b['replica'], absolute_step=16000000,
            parent_sha256=b['parent']['sha256'], chemical_seed=int(metadata['seed']),
            creations=initial['creations'], breaks=initial['breaks'], partners=partners,
            old_md_seed=a['md_seed'], new_md_seed=b['md_seed'],
            old_effective_md_seed=a['effective_md_seed'], new_effective_md_seed=b['effective_md_seed'],
            internal_start_step=0, initVelocities=False, bitwise_md_continuation=False))
    return records


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
        captured[-1].append((int(args[1]), multigraph.distributions(result, 1000, 4),
                             peripheral_membership(result)))
        return result

    analysis.topology.frame_observables = capture
    try:
        sources = graph.authenticate_with_graphs(ROOT, list(ATTEMPTS))
    finally:
        analysis.topology.frame_observables = original
    histories = [h for s in sources for h in s['histories']]
    joint.require(len(captured) == 6, 'six segment/replica captures required')
    for h, frames in zip(histories, captured):
        h['peripheral_frames'] = [dict(step=step, **membership) for step, _, membership in frames]
        joint.require([step for step, _, _ in frames] == [r['step'] for r in h['rows']],
                      'multigraph frame coverage differs')
        for row, (_, values, membership) in zip(h['rows'], frames):
            joint.require(row['L1'] == sum(k * (k - 1) / 2 * values[f'edges_m{k}']
                for k in range(1, 5)) and row['intra'] ==
                values['stars_intra_loops_1'] + 2 * values['stars_intra_loops_2'],
                'L1/intra distribution accounting differs')
            row.update(values)
    approved = joint.campaign.load_json(OLD_REVIEW / 'evidence/provenance.json')
    joint.require(sources[0]['plan'] == approved['source_plan'] and
        [dict(entry=h['entry'], validation=h['validation']) for h in sources[0]['histories']] ==
        approved['validated_histories'], 'fresh original authentication differs from 16M review')
    return sources


def write_evidence(sources, output):
    joint.check_lineage(sources)
    joint.require([[(h['entry']['start_step'], h['entry']['end_step']) for h in s['histories']]
        for s in sources] == [[(0, 16000000)] * 3, [(16000000, 20000000)] * 3],
        'exact 0–16M and 16–20M segments required')
    joint.require(all(s['plan']['system']['system_id'] == 'F04_N010_RP080_EE12_EA04'
                      for s in sources), 'wrong system')
    output.mkdir(parents=True, exist_ok=False)
    extra = tuple(k for k in sources[0]['histories'][0]['rows'][0]
        if k.startswith('edges_m') or k.startswith('stars_intra_loops_')) + (
        'mean_edge_multiplicity', 'fraction_parallel_edges', 'max_edge_multiplicity')
    intervals = sorted({i for pair in PAIRS for i in pair} |
        {(a, a + width) for width in WIDTHS
         for a in range(0, 20000000, width)} |
        {(a, a + 250000) for a in range(18000000, 20000000, 250000)})
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
        boundary_policy='IAT/SEM estimates remain segment-local; no interval crosses 16M reseeding',
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
    joint.runner.exclusive_json(output / 'BOUNDARY.json', dict(records=boundary_proof(sources)))
    joint.runner.exclusive_json(output / 'PERIPHERAL_FRAMES.json', dict(
        records=[dict(replica=replica, frames=sources[0]['histories'][replica - 1]['peripheral_frames'] +
            sources[1]['histories'][replica - 1]['peripheral_frames'][1:]) for replica in (1, 2, 3)],
        scope='sampled identities/components only; actual component boundaries are between diagnostic frames'))
    names = previous.continuous.metric_names(sources[-1]['plan']['system']) + extra + (
        'temperature', 'min_permanent_bond', 'max_permanent_bond')
    for replica in (1, 2, 3):
        rows = sources[0]['histories'][replica - 1]['rows'] + sources[1]['histories'][replica - 1]['rows'][1:]
        joint.require([r['step'] for r in rows] == list(range(0, 20000001, 1000)), 'full context coverage differs')
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
