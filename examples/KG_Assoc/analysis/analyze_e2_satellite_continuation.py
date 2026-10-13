#!/usr/bin/env python3
"""Read-only restart-aware satellite diagnostics through validated graph replay."""
import argparse
import collections
from pathlib import Path

import analyze_joint_e2 as joint
import analyze_e2_window_sensitivity as sensitivity

EXTRA = ('isolated_stars', 'satellite_components', 'satellite_stars')
PAIRS = (((2000000, 4000000), (4000000, 6000000)),
         ((4000000, 6000000), (6000000, 8000000)),
         ((6000000, 7000000), (7000000, 8000000)),
         ((4000000, 5500000), (6000000, 7500000)),
         ((4500000, 6000000), (6500000, 8000000)),
         ((5000000, 6000000), (7000000, 8000000)))


def graph_metrics(graph, stars, functionality):
    counts = collections.Counter(graph['neighbor_degree'].values())
    joint.require(sum(counts.values()) == stars and max(counts, default=0) <= functionality,
                  'distinct-neighbor degree coverage differs')
    sizes = graph['component_sizes']
    joint.require(sum(sizes) == stars and sizes == sorted(sizes, reverse=True),
                  'component size coverage differs')
    satellites = [size for size in sizes[1:] if size > 1]
    return dict(isolated_stars=counts[0], satellite_components=len(satellites),
                satellite_stars=sum(satellites),
                **{f'degree_{degree}_fraction': counts[degree] / stars
                   for degree in range(functionality + 1)})


def authenticate_with_graphs(root, attempts):
    """Observe validation callbacks, preserving the graph, validator and raw files."""
    analysis = joint.segment.review.analysis
    original = analysis.topology.frame_observables
    captures = []

    # Save only compact metrics rather than retaining all 1000-star graphs.
    def compact_capture(*args, **kwargs):
        graph = original(*args, **kwargs)
        if args[0] == 0:
            captures.append([])
        system = args[4]
        functionality = len(system['stickers']) // len(system['stars'])
        captures[-1].append((int(args[1]), graph_metrics(graph, len(system['stars']), functionality)))
        return graph

    analysis.topology.frame_observables = compact_capture
    try:
        segments = joint.authenticate(root, attempts)
    finally:
        analysis.topology.frame_observables = original
    histories = [h for s in segments for h in s['histories']]
    joint.require(len(captures) == len(histories), 'validation capture coverage differs')
    for history, frames in zip(histories, captures):
        joint.require([step for step, _ in frames] == [row['step'] for row in history['rows']],
                      'graph/diagnostic steps differ')
        for row, (_, metrics) in zip(history['rows'], frames):
            row.update(metrics)
    return segments


def make_window(source, history, start, end):
    entry = history['entry']
    joint.require(entry['start_step'] <= start < end <= entry['end_step'],
                  'window crosses a restart boundary')
    names = joint.segment.METRICS + EXTRA + tuple(
        f'degree_{degree}_fraction' for degree in range(entry['system']['f'] + 1))
    window = joint.segment.review.window(history['rows'], history['events'], start, end,
        stickers=entry['system']['f'] * entry['system']['number_of_stars'],
        dt=entry['physics']['dt'], stars=entry['system']['number_of_stars'], metrics=names)
    window['segment'] = source['attempt']
    for category in ('metrics', 'activity'):
        for item in window[category].values():
            constant = len(set(item['blocks'])) == 1 and item['sem_estimate'] == 0
            item['constant_not_mixing_evidence'] = constant
            item['resolution_warning'] |= constant or item['effective_samples_estimate'] < 10
    return window


def summarize(segments):
    segments = joint.check_lineage(segments)
    records, long_records = [], []
    for index, replica in enumerate((1, 2, 3)):
        windows, long_windows = [], []
        for source in segments:
            history = source['histories'][index]
            entry = history['entry']
            joint.require((entry['end_step'] - entry['start_step']) % 500000 == 0,
                          'segment must tile 500k windows')
            for start in range(entry['start_step'], entry['end_step'], 500000):
                windows.append(make_window(source, history, start, start + 500000))
            for start, end in sorted({interval for pair in PAIRS for interval in pair}):
                if entry['start_step'] <= start < end <= entry['end_step']:
                    long_windows.append(make_window(source, history, start, end))
        records.append(dict(replica=replica, windows=windows))
        long_records.append(dict(replica=replica, windows=long_windows))
    result = sensitivity.summarize(dict(records=records, windows_steps=500000), PAIRS)
    result.update(stage='E2_restart_aware_satellite_review', records=records,
                  interval_estimates=long_records, windows_steps=500000,
                  boundary_policy='No IAT, blocking, lifetimes or transport stitched across MD reseeding',
                  transient='0–1M retained as initial unbound context, not certified stationary',
                  definitions='satellites are non-singleton components outside one largest component; '
                              'degree is distinct inter-star neighbors; initial isolated largest is excluded',
                  system=segments[-1]['plan']['system'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', required=True, type=Path)
    parser.add_argument('--attempt', required=True, nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    joint.require(not args.output.exists(), 'immutable output already exists')
    segments = authenticate_with_graphs(args.dataset_root.resolve(), [p.resolve() for p in args.attempt])
    result = summarize(segments)
    result['source_sha256'] = joint.runner.hash_files([Path(__file__), Path(sensitivity.__file__),
        Path(joint.__file__)] + [Path(s['attempt']) / name for s in segments for name in
        ('plan.json', 'approval.json', 'r001/complete.json', 'r002/complete.json', 'r003/complete.json')])
    result['source_authentication'] = [dict(attempt=s['attempt'], plan=s['plan'],
        build_authentication_scope=s['build_authentication_scope'],
        histories=[dict(entry=h['entry'], validation=h['validation']) for h in s['histories']])
        for s in segments]
    joint.runner.exclusive_json(args.output, result)


if __name__ == '__main__':
    main()
