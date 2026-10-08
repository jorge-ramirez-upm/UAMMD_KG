#!/usr/bin/env python3
"""Periodic wrapping analysis of synchronized star-network snapshots."""

import argparse
import collections
import csv
import json
import math
import statistics
import sys
from pathlib import Path

from analyze_p45_topology import read_system, topology_frames
from analyze_p47_walking_hopping import parse_key_values, system_metadata


def nearest_integer_antisymmetric(value, tolerance=1e-12):
    """Round to the nearest integer, resolving half-box ties antisymmetrically."""
    nearest_half = abs(abs(value - math.floor(value)) - 0.5) < tolerance
    if nearest_half:
        return 1 if value > 0.0 else -1
    return math.floor(value + 0.5)


def edge_translation(first_position, second_position, box):
    """Return n where r_second + n*L - r_first is minimum image."""
    return tuple(nearest_integer_antisymmetric((first - second) / length)
                 for first, second, length in zip(first_position, second_position, box))


def wrapping_components(stars, edges):
    """Find connected components and winding axes using lattice-offset BFS.

    Each edge is (first_star, second_star, n), with the convention
    r_second + n*L - r_first being the physical minimum-image displacement.
    """
    simple_edges = {}
    for first, second, translation in edges:
        if first == second:
            continue
        if first > second:
            first, second = second, first
            translation = tuple(-value for value in translation)
        key = (first, second)
        previous = simple_edges.get(key)
        if previous is not None and previous != translation:
            raise ValueError('parallel edges imply inconsistent periodic translations for {}'.format(key))
        simple_edges[key] = translation

    adjacency = {star: [] for star in stars}
    for (first, second), translation in simple_edges.items():
        adjacency[first].append((second, translation))
        adjacency[second].append((first, tuple(-value for value in translation)))

    unseen = set(stars)
    components = []
    while unseen:
        root = min(unseen)
        unseen.remove(root)
        labels = {root: (0, 0, 0)}
        queue = collections.deque([root])
        winding = set()
        winding_vectors = set()
        while queue:
            first = queue.popleft()
            for second, translation in adjacency[first]:
                implied = tuple(labels[first][axis] + translation[axis] for axis in range(3))
                if second not in labels:
                    labels[second] = implied
                    unseen.discard(second)
                    queue.append(second)
                else:
                    discrepancy = tuple(implied[axis] - labels[second][axis] for axis in range(3))
                    if discrepancy != (0, 0, 0):
                        winding_vectors.add(discrepancy)
                        winding.update(axis for axis, value in enumerate(discrepancy) if value)
        components.append({'size': len(labels), 'nodes': set(labels), 'wraps': winding,
                           'winding_vectors': winding_vectors})
    return components


def finite_cluster_susceptibility(components):
    sizes = [component['size'] for component in components if not component['wraps']]
    denominator = sum(sizes)
    return sum(size * size for size in sizes) / denominator if denominator else 0.0


def read_com_frames(path, expected_stars):
    with open(path, encoding='utf-8') as source:
        if source.readline().strip() != '# step time molecule_id com_x com_y com_z':
            raise ValueError('{}: unexpected COM header'.format(path))
        while True:
            line = source.readline()
            if not line:
                return
            step, time, star, x, y, z = line.split()
            step, star = int(step), int(star)
            frame = {star: (float(x), float(y), float(z))}
            frame_time = float(time)
            for _ in range(len(expected_stars) - 1):
                fields = source.readline().split()
                if len(fields) != 6:
                    raise ValueError('{}: malformed COM frame'.format(path))
                other_step, other_time, other_star, x, y, z = fields
                if int(other_step) != step or float(other_time) != frame_time:
                    raise ValueError('{}: COM frame is not synchronized'.format(path))
                other_star = int(other_star)
                if other_star in frame:
                    raise ValueError('{}: duplicate star in COM frame'.format(path))
                frame[other_star] = (float(x), float(y), float(z))
            if set(frame) != set(expected_stars):
                raise ValueError('{}: COM star IDs do not match system'.format(path))
            yield step, frame_time, frame


def read_box(path):
    bounds = []
    with open(path, encoding='utf-8') as source:
        for line in source:
            fields = line.split()
            if len(fields) == 4 and fields[2:] == ['xlo', 'xhi']:
                bounds = [float(value) for value in fields[:2]]
                bounds += [float(value) for value in next(source).split()[:2]]
                bounds += [float(value) for value in next(source).split()[:2]]
                break
    if len(bounds) != 6:
        raise ValueError('{}: missing box bounds'.format(path))
    lengths = (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
    if any(length <= 0.0 for length in lengths):
        raise ValueError('{}: invalid box lengths'.format(path))
    return lengths


def event_metadata(path):
    values = parse_key_values(path)
    required = ('input_file', 'dt', 'seed', 'start_step', 'total_requested_steps')
    missing = [key for key in required if key not in values]
    if missing:
        raise ValueError('{}: missing provenance {}'.format(path, ', '.join(missing)))
    values['dt'] = float(values['dt'])
    values['seed'] = int(values['seed'])
    values['start_step'] = int(values['start_step'])
    values['total_requested_steps'] = int(values['total_requested_steps'])
    return values


def analyze_replica(prefix, system, box, system_path, replica, progress=None):
    topology_path = prefix + '.topology'
    com_path = prefix + '.com_trajectory'
    metadata = event_metadata(prefix + '.events')
    com_frames = read_com_frames(com_path, system['stars'])
    frame_rows = []
    com_step, com_time, positions = next(com_frames, (None, None, None))
    frame_count = 0
    for _, step, time, pairs in topology_frames(topology_path, system):
        while com_step is not None and com_step < step:
            com_step, com_time, positions = next(com_frames, (None, None, None))
        if com_step != step or not math.isclose(com_time, time, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError('{}: topology/COM frame mismatch at step {}'.format(prefix, step))
        wrapped = {star: tuple(value % length for value, length in zip(position, box))
                   for star, position in positions.items()}
        edges = []
        for first_atom, second_atom, first_star, second_star in pairs:
            if first_star == second_star:
                continue
            first, second = sorted((first_star, second_star))
            translation = edge_translation(wrapped[first], wrapped[second], box)
            edges.append((first, second, translation))
        components = wrapping_components(system['stars'], edges)
        wrapping = [component for component in components if component['wraps']]
        wrapping_nodes = set().union(*(component['nodes'] for component in wrapping)) if wrapping else set()
        largest = max(component['size'] for component in components)
        non_wrapping = [component['size'] for component in components if not component['wraps']]
        finite_susceptibility = finite_cluster_susceptibility(components)
        wraps_x = any(0 in component['wraps'] for component in wrapping)
        wraps_y = any(1 in component['wraps'] for component in wrapping)
        wraps_z = any(2 in component['wraps'] for component in wrapping)
        frame_rows.append({'replica': replica, 'step': step, 'time': time,
                           'n_components': len(components), 'largest_component_size': largest,
                           'largest_component_fraction': largest / len(system['stars']),
                           'wraps_x': int(wraps_x), 'wraps_y': int(wraps_y), 'wraps_z': int(wraps_z),
                           'n_wrap_dimensions': int(wraps_x) + int(wraps_y) + int(wraps_z),
                           'any_wrap': int(bool(wrapping)), 'all_xyz_wrap': int(wraps_x and wraps_y and wraps_z),
                           'n_wrapping_components': len(wrapping),
                           'wrapping_component_size_max': max((component['size'] for component in wrapping), default=0),
                           'wrapping_fraction': len(wrapping_nodes) / len(system['stars']),
                           'largest_nonwrapping_component_size': max(non_wrapping, default=0),
                           'finite_cluster_susceptibility': finite_susceptibility})
        frame_count += 1
        if progress and frame_count % progress[0] == 0:
            print('{}: frames={} step={} time={:.6g}'.format(
                progress[1], frame_count, step, time), file=sys.stderr, flush=True)
        com_step, com_time, positions = next(com_frames, (None, None, None))
    if frame_count == 0:
        raise ValueError('{}: no synchronized frames'.format(prefix))
    if com_step is not None:
        raise ValueError('{}: COM trajectory has unsynchronized trailing frames'.format(prefix))
    return frame_rows, metadata, system_metadata(system_path, metadata, system)


def replica_statistics(values):
    if not values:
        return {'mean': None, 'sample_std': None, 'sem': None, 'ci95_half_width': None}
    sample_std = statistics.stdev(values) if len(values) > 1 else 0.0
    critical = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776}.get(len(values), 1.96)
    return {'mean': statistics.mean(values), 'sample_std': sample_std,
            'sem': sample_std / math.sqrt(len(values)),
            'ci95_half_width': critical * sample_std / math.sqrt(len(values))}


def write_csv(path, rows):
    fields = sorted({key for row in rows for key in row})
    with open(path, 'w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_metadata(metadata_rows):
    if not metadata_rows:
        return
    keys = ('system_label', 'number_of_stars', 'arms_per_star', 'arm_length',
            'stickers_per_star', 'total_density', 'polymer_density', 'Ea', 'Ee',
            'nu0', 'Nevery', 'r_assoc', 'temperature', 'dt', 'box_size')
    reference = metadata_rows[0]
    for index, row in enumerate(metadata_rows[1:], 2):
        for key in keys:
            if row.get(key) != reference.get(key):
                raise ValueError('incompatible replica metadata at replica {}: {}'.format(index, key))


def self_test():
    stars = (1, 2, 3, 4)
    assert wrapping_components(stars, [(1, 2, (0, 0, 0)), (2, 3, (0, 0, 0)),
                                       (3, 4, (0, 0, 0))])[0]['wraps'] == set()
    assert wrapping_components(stars, [(1, 2, (1, 0, 0)), (2, 3, (0, 0, 0)),
                                       (3, 4, (0, 0, 0)), (4, 1, (0, 0, 0))])[0]['wraps'] == {0}
    assert wrapping_components(stars, [(1, 2, (1, 0, 0)), (2, 3, (0, 1, 0)),
                                       (3, 4, (0, 0, 1)), (4, 1, (0, 0, 0))])[0]['wraps'] == {0, 1, 2}
    assert wrapping_components(stars, [(1, 2, (-1, 0, 0)), (2, 3, (0, 0, 0)),
                                       (3, 4, (0, 0, 0)), (4, 1, (0, 0, 0))])[0]['wraps'] == {0}
    ordinary = wrapping_components(stars, [(1, 2, (0, 0, 0)), (2, 3, (0, 0, 0)),
                                           (3, 4, (0, 0, 0)), (4, 1, (0, 0, 0))])
    assert ordinary[0]['wraps'] == set() and finite_cluster_susceptibility(ordinary) == 4.0
    assert len(wrapping_components(stars, [(1, 2, (0, 0, 0)), (1, 2, (0, 0, 0))])) == 3
    disconnected = wrapping_components((1, 2, 3, 4, 5, 6),
                                       [(1, 2, (1, 0, 0)), (2, 3, (0, 0, 0)),
                                        (3, 4, (0, 0, 0)), (4, 1, (0, 0, 0)),
                                        (5, 6, (0, 0, 0))])
    assert sum(bool(component['wraps']) for component in disconnected) == 1
    assert edge_translation((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (10.0, 10.0, 10.0))[0] == -1
    assert edge_translation((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (10.0, 10.0, 10.0)) == \
        edge_translation((10.0, 0.0, 0.0), (15.0, 0.0, 0.0), (10.0, 10.0, 10.0))
    try:
        wrapping_components(stars, [(1, 2, (0, 0, 0)), (1, 2, (1, 0, 0))])
    except ValueError:
        pass
    else:
        raise AssertionError('inconsistent parallel edge accepted')
    assert replica_statistics([1.0, 1.0, 1.0])['sem'] == 0.0
    print('P4.8A SELF_TEST PASS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', required=False)
    parser.add_argument('--output-prefix', required=False)
    parser.add_argument('--progress-interval', type=int, default=100)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('prefixes', nargs='*')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if not arguments.system or not arguments.output_prefix or not arguments.prefixes:
        parser.error('--system, --output-prefix, and prefixes are required')
    if arguments.progress_interval <= 0:
        parser.error('--progress-interval must be positive')
    system = read_system(arguments.system, 2)
    box = read_box(arguments.system)
    all_frames, metadata_rows = [], []
    durations = []
    for replica, prefix in enumerate(arguments.prefixes, 1):
        progress = (arguments.progress_interval, 'P4.8a replica {}/{}'.format(
            replica, len(arguments.prefixes)))
        print('{}: starting {}'.format(progress[1], prefix), file=sys.stderr, flush=True)
        rows, metadata, provenance = analyze_replica(
            prefix, system, box, arguments.system, replica, progress)
        duration = (metadata['total_requested_steps'] - metadata['start_step']) * metadata['dt']
        durations.append((replica, duration))
        all_frames.extend(rows)
        metadata_rows.append(provenance)
    if len(set(duration for _, duration in durations)) != 1:
        raise ValueError('incompatible replica durations: {}'.format(durations))
    validate_metadata(metadata_rows)
    write_csv(arguments.output_prefix + '.frames.csv', all_frames)
    replica_rows = []
    summary_metrics = collections.defaultdict(list)
    for replica in range(1, len(arguments.prefixes) + 1):
        rows = [row for row in all_frames if row['replica'] == replica]
        summary = {'replica': replica, 'n_frames': len(rows),
                   'P_wrap_any': statistics.mean(row['any_wrap'] for row in rows),
                   'P_wrap_x': statistics.mean(row['wraps_x'] for row in rows),
                   'P_wrap_y': statistics.mean(row['wraps_y'] for row in rows),
                   'P_wrap_z': statistics.mean(row['wraps_z'] for row in rows),
                   'P_wrap_xyz': statistics.mean(row['all_xyz_wrap'] for row in rows),
                   'mean_largest_component_fraction': statistics.mean(
                       row['largest_component_fraction'] for row in rows),
                   'mean_wrapping_fraction': statistics.mean(row['wrapping_fraction'] for row in rows),
                   'mean_finite_cluster_susceptibility': statistics.mean(
                       row['finite_cluster_susceptibility'] for row in rows),
                   'multiple_wrapping_components_frames': sum(
                       row['n_wrapping_components'] > 1 for row in rows)}
        replica_rows.append(summary)
        for key, value in summary.items():
            if key not in ('replica', 'n_frames', 'multiple_wrapping_components_frames'):
                summary_metrics[key].append(value)
    write_csv(arguments.output_prefix + '.replicas.csv', replica_rows)
    ensemble = {key: replica_statistics(values) for key, values in summary_metrics.items()}
    with open(arguments.output_prefix + '.summary.json', 'w', encoding='utf-8') as output:
        json.dump({'system_metadata': metadata_rows, 'replica_summaries': replica_rows,
                   'ensemble_replica_statistics': ensemble,
                   'periodic_edge_convention': 'r_j + n_ij L - r_i is minimum-image; BFS image labels add n_ij',
                   'half_box_rule': 'exact half-box ties choose the sign away from zero, preserving antisymmetry',
                   'coordinate_basis': 'wrapped star COM positions; synchronized sticker coordinates are unavailable',
                   'finite_cluster_susceptibility': 'sum(s^2 n_s) / sum(s n_s), excluding all wrapping components',
                   'uncertainty': 'replica-level; frames are descriptive support only'}, output, indent=2)


if __name__ == '__main__':
    main()
