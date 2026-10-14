#!/usr/bin/env python3
"""Permanent-star multigraph and intra-loop distributions from validated event replay."""
import argparse
import collections
import copy
import csv
from pathlib import Path
import reproduce as review

analysis = review.joint.segment.review.analysis


def distributions(graph, stars, functionality):
    edges = collections.Counter(graph['edge_multiplicity'].values())
    loops = collections.Counter(graph['intra_degree'].values())
    review.joint.require(all(1 <= k <= functionality for k in edges) and
                         all(1 <= k <= functionality // 2 for k in loops),
                         'multiplicity exceeds permanent-star valence')
    review.joint.require(sum(k * v for k, v in edges.items()) == graph['inter_bonds'] and
                         sum(k * v for k, v in loops.items()) == graph['intra_bonds'],
                         'multiplicity/loop bond accounting differs')
    return dict(**{f'edges_m{k}': edges[k] for k in range(1, functionality + 1)},
        **{f'stars_intra_loops_{k}': (stars - sum(loops.values()) if k == 0 else loops[k])
           for k in range(functionality // 2 + 1)},
        mean_edge_multiplicity=graph['mean_edge_multiplicity'],
        fraction_parallel_edges=graph['fraction_edge_multiplicity_ge_2'],
        max_edge_multiplicity=graph['max_edge_multiplicity'])


def collect(entry, expected_rows):
    system, initial = review.joint.runner.validation.read_parent(entry)
    _, events = analysis.dynamics.read_events(entry['output_prefix'] + '.events', system)
    captured = []
    original = analysis.topology.frame_observables

    def capture(*args, **kwargs):
        graph = original(*args, **kwargs)
        values = distributions(graph, len(system['stars']), entry['system']['f'])
        row = expected_rows[len(captured)]
        review.joint.require(row['step'] == int(args[1]) and row['L1'] ==
            sum(k * (k - 1) / 2 * values[f'edges_m{k}'] for k in range(1, 5)),
            'frame/multiplicity motif identity differs')
        captured.append(dict(step=row['step'], time=row['time'], **values))
        return graph

    analysis.topology.frame_observables = capture
    try:
        analysis.replay(copy.deepcopy(expected_rows), events, system, network=True, initial=initial)
    finally:
        analysis.topology.frame_observables = original
    review.joint.require(len(captured) == 6001, 'multiplicity history coverage differs')
    return captured


def main(directory):
    directory = Path(directory)
    output = directory / 'multiplicity.json'
    review.joint.require(not output.exists(), 'immutable multiplicity output already exists')
    provenance = review.joint.campaign.load_json(directory / 'provenance.json')
    summary = review.joint.campaign.load_json(directory / 'summary.json')
    review.joint.require(provenance['source_plan']['system']['system_id'] ==
        'F04_N010_RP040_EE08_EA04', 'wrong system')
    records = []
    for history, estimates in zip(provenance['validated_histories'], summary['interval_estimates']):
        entry = history['entry']
        review.joint.require(entry['replica'] == estimates['replica'], 'replica order differs')
        review.joint.runner.check_hashes({entry['output_prefix'] + suffix: digest
            for suffix, digest in history['validation']['output_sha256'].items()})
        _, rows = analysis.stationarity.read_state(entry['output_prefix'] + '.state')
        frames = collect(entry, rows)
        names = tuple(k for k in frames[0] if k not in ('step', 'time'))
        stationarity = analysis.stationarity
        original = stationarity.iat
        stationarity.iat = review.memoized_iat
        try:
            windows = []
            for interval in estimates['windows']:
                start, end = interval['start_step_exclusive'], interval['end_step_inclusive']
                selected = [r for r in frames if start < r['step'] <= end]
                metrics = {k: review.joint.segment.review.estimate([r[k] for r in selected],
                    [r['time'] for r in selected]) for k in names}
                for value in metrics.values():
                    value['constant_not_mixing_evidence'] = value['sem_estimate'] == 0
                windows.append(dict(start_step_exclusive=start, end_step_inclusive=end, metrics=metrics))
        finally:
            stationarity.iat = original
        with (directory / ('r%03d_multiplicity.csv' % entry['replica'])).open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=tuple(frames[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(frames)
        records.append(dict(replica=entry['replica'], windows=windows))
        print('Multiplicity replay r%03d complete' % entry['replica'], flush=True)
    review.joint.runner.exclusive_json(output, dict(schema_version=1, records=records,
        formal_acceptance=False, independent_units='three original histories only',
        definitions='edges_mk: distinct star pairs carrying k bonds; stars_intra_loops_k: permanent stars carrying k intra bonds',
        source_sha256=review.joint.runner.hash_files([Path(__file__), directory / 'provenance.json',
            directory / 'summary.json', Path(analysis.topology.__file__), Path(analysis.__file__)])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
