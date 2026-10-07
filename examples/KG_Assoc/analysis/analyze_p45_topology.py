#!/usr/bin/env python3
"""Static transient-network topology analysis for KG_Assoc topology streams."""

import argparse
import collections
import csv
import json
import math
import statistics


def fail(path, message):
    raise ValueError('{}: {}'.format(path, message))


def read_system(path, sticker_type):
    """Read atom ID, molecule ID, and type from a LAMMPS Atoms section."""
    atom_to_star = {}
    stickers = set()
    reading_atoms = False
    try:
        with open(path, encoding='utf-8') as input_file:
            for line in input_file:
                fields = line.split()
                if not fields:
                    continue
                if fields[0] == 'Atoms':
                    reading_atoms = True
                    continue
                if not reading_atoms:
                    continue
                if fields[0][0].isalpha():
                    break
                if len(fields) < 3:
                    fail(path, 'malformed Atoms record')
                atom, star, atom_type = (int(value) for value in fields[:3])
                if atom <= 0 or star <= 0:
                    fail(path, 'invalid atom/molecule ID')
                if atom_type in (1, sticker_type):
                    if atom in atom_to_star:
                        fail(path, 'duplicate star-particle atom ID')
                    atom_to_star[atom] = star
                    if atom_type == sticker_type:
                        stickers.add(atom)
    except OSError as error:
        fail(path, str(error))
    if not atom_to_star or not stickers:
        fail(path, 'missing Atoms records or stickers')
    stars = tuple(sorted(set(atom_to_star.values())))
    stickers_per_star = collections.Counter(atom_to_star[atom] for atom in stickers)
    if set(stickers_per_star) != set(stars):
        fail(path, 'at least one star has no sticker atoms')
    return {'atom_to_star': atom_to_star, 'stickers': stickers, 'stars': stars,
            'stickers_per_star': stickers_per_star}


def topology_frames(path, system):
    """Yield production topology frames; the format stores each bond once."""
    with open(path, encoding='utf-8') as input_file:
        header = input_file.readline().strip()
        expected = '# FRAME step time active_pairs; pairs: atom_i atom_j molecule_i molecule_j'
        if header != expected:
            fail(path, 'unexpected topology header')
        frame = 0
        while True:
            line = input_file.readline()
            if not line:
                return
            fields = line.split()
            if len(fields) != 4 or fields[0] != 'FRAME':
                fail(path, 'malformed FRAME record')
            step = int(fields[1])
            time = float(fields[2])
            declared_bonds = int(fields[3])
            if step < 0 or time < 0.0 or declared_bonds < 0:
                fail(path, 'invalid FRAME values')
            pairs = []
            atoms = set()
            bonds = set()
            for _ in range(declared_bonds):
                pair_fields = input_file.readline().split()
                if len(pair_fields) != 4:
                    fail(path, 'malformed topology pair')
                first, second, first_star, second_star = (int(value) for value in pair_fields)
                if first >= second or first <= 0:
                    fail(path, 'topology pair is not uniquely atom-ordered')
                if first not in system['stickers'] or second not in system['stickers']:
                    fail(path, 'topology endpoint is not a sticker atom')
                if (first_star != system['atom_to_star'][first] or
                        second_star != system['atom_to_star'][second]):
                    fail(path, 'topology molecule ID disagrees with system file')
                bond = (first, second)
                if bond in bonds or first in atoms or second in atoms:
                    fail(path, 'duplicate, reciprocal, or nonreciprocal sticker topology')
                bonds.add(bond)
                atoms.update(bond)
                pairs.append((first, second, first_star, second_star))
            yield frame, step, time, pairs
            frame += 1


def components(stars, neighbors):
    unseen = set(stars)
    sizes = []
    while unseen:
        first = unseen.pop()
        size = 1
        frontier = [first]
        while frontier:
            node = frontier.pop()
            for neighbor in neighbors[node]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    frontier.append(neighbor)
                    size += 1
        sizes.append(size)
    return sorted(sizes, reverse=True)


def frame_observables(frame, step, time, pairs, system):
    stars = system['stars']
    bond_degree = collections.Counter()
    intra_degree = collections.Counter()
    neighbors = {star: set() for star in stars}
    multiplicity = collections.Counter()
    used_stickers = set()
    intra = 0
    inter = 0
    for first, second, first_star, second_star in pairs:
        if first == second or first in used_stickers or second in used_stickers:
            raise ValueError('duplicate, reciprocal, or nonreciprocal sticker topology')
        used_stickers.add(first)
        used_stickers.add(second)
        if first_star == second_star:
            intra += 1
            intra_degree[first_star] += 1
        else:
            inter += 1
            bond_degree[first_star] += 1
            bond_degree[second_star] += 1
            edge = tuple(sorted((first_star, second_star)))
            multiplicity[edge] += 1
            neighbors[first_star].add(second_star)
            neighbors[second_star].add(first_star)
    temporary = intra + inter
    component_sizes = components(stars, neighbors)
    sticker_total = len(system['stickers'])
    inter_incidence = sum(bond_degree.values())
    intra_incidence = 2 * intra
    free_stickers = sticker_total - inter_incidence - intra_incidence
    if free_stickers < 0 or free_stickers + inter_incidence + intra_incidence != sticker_total:
        raise ValueError('sticker conservation failure')
    neighbor_degree = {star: len(neighbors[star]) for star in stars}
    edge_values = list(multiplicity.values())
    return {
        'frame': frame,
        'step': step,
        'time': time,
        'temporary_bonds': temporary,
        'intra_bonds': intra,
        'inter_bonds': inter,
        'fraction_intra': intra / temporary if temporary else 0.0,
        'fraction_inter': inter / temporary if temporary else 0.0,
        'mean_k_bond': inter_incidence / len(stars),
        'mean_k_neighbor': sum(neighbor_degree.values()) / len(stars),
        'isolated_fraction': sum(value == 0 for value in neighbor_degree.values()) / len(stars),
        'bond_isolated_fraction': sum(value == 0 for value in bond_degree.values()) / len(stars),
        'mean_intra_bonds_per_star': intra / len(stars),
        'mean_free_stickers_per_star': free_stickers / len(stars),
        'mean_intra_stickers_per_star': intra_incidence / len(stars),
        'mean_inter_stickers_per_star': inter_incidence / len(stars),
        'connected_components': len(component_sizes),
        'largest_component_size': component_sizes[0],
        'largest_component_fraction': component_sizes[0] / len(stars),
        'second_largest_component_size': component_sizes[1] if len(component_sizes) > 1 else 0,
        'mean_edge_multiplicity': statistics.mean(edge_values) if edge_values else 0.0,
        'fraction_edge_multiplicity_ge_2': (
            sum(value >= 2 for value in edge_values) / len(edge_values) if edge_values else 0.0),
        'max_edge_multiplicity': max(edge_values, default=0),
        'bond_degree': bond_degree,
        'intra_degree': intra_degree,
        'neighbors': neighbors,
        'neighbor_degree': neighbor_degree,
        'edge_multiplicity': multiplicity,
        'component_sizes': component_sizes,
    }


def summarize_replica(rows):
    result = {}
    for key in rows[0]:
        if isinstance(rows[0][key], (int, float)):
            values = [row[key] for row in rows]
            result[key] = statistics.mean(values)
    thirds = []
    for start, end in ((0, len(rows) // 3), (len(rows) // 3, 2 * len(rows) // 3),
                       (2 * len(rows) // 3, len(rows))):
        block = rows[start:end]
        if block:
            thirds.append({key: statistics.mean(row[key] for row in block)
                           for key in ('inter_bonds', 'mean_k_neighbor',
                                       'largest_component_fraction')})
    result['stationarity_blocks'] = thirds
    return result


def t_critical_95(replica_count):
    return {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
            7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}.get(replica_count, 1.96)


def histogram_rows(name, histograms):
    rows = []
    for replica, histogram in histograms.items():
        total = sum(histogram.values())
        for value, count in sorted(histogram.items()):
            rows.append({'replica': replica, name: value, 'count': count,
                         'probability': count / total if total else 0.0})
    return rows


def write_outputs(prefix, frame_rows, histograms, replica_summaries, system):
    frame_path = prefix + '.frames.csv'
    with open(frame_path, 'w', newline='', encoding='utf-8') as output:
        fields = tuple(key for key, value in frame_rows[0].items()
                       if not isinstance(value, (collections.Counter, dict, list)))
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: value for key, value in row.items() if key in fields}
                          for row in frame_rows])
    paths = [frame_path]
    for name, histogram in histograms.items():
        path = '{}.{}.csv'.format(prefix, name)
        with open(path, 'w', newline='', encoding='utf-8') as output:
            fields = ('replica', name, 'count', 'probability')
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            writer.writerows(histogram_rows(name, histogram))
        paths.append(path)
    metrics = ('temporary_bonds', 'intra_bonds', 'inter_bonds', 'fraction_intra', 'mean_k_bond',
               'mean_k_neighbor', 'isolated_fraction', 'mean_intra_bonds_per_star',
               'mean_free_stickers_per_star', 'connected_components',
               'largest_component_fraction', 'mean_edge_multiplicity',
               'fraction_edge_multiplicity_ge_2')
    ensemble = {}
    for metric in metrics:
        values = [summary[metric] for summary in replica_summaries]
        sample_std = statistics.stdev(values) if len(values) > 1 else 0.0
        sem = sample_std / math.sqrt(len(values)) if values else 0.0
        ensemble[metric] = {'mean': statistics.mean(values), 'sample_std': sample_std, 'sem': sem,
                            'ci95': t_critical_95(len(values)) * sem}
    summary = {
        'nodes': len(system['stars']),
        'stickers': len(system['stickers']),
        'stickers_per_star': sorted(set(system['stickers_per_star'].values())),
        'topology_encoding': 'each physical temporary bond is listed once, atom_i < atom_j',
        'intra_counting': 'one intra bond counts once for n_intra and consumes two stickers',
        'inter_counting': (
            'one inter bond contributes one edge and one sticker incidence at each endpoint'),
        'pbc_caveat': 'largest component is not a percolation or wrapping criterion',
        'replica_summaries': replica_summaries,
        'ensemble_replica_statistics': ensemble,
    }
    summary_path = prefix + '.summary.json'
    with open(summary_path, 'w', encoding='utf-8') as output:
        json.dump(summary, output, indent=2)
        output.write('\n')
    paths.append(summary_path)
    return paths


def self_test():
    system = {'stars': (1, 2, 3, 4, 5), 'stickers': set(range(1, 21)),
              'atom_to_star': {atom: (atom - 1) // 4 + 1 for atom in range(1, 21)},
              'stickers_per_star': collections.Counter({star: 4 for star in range(1, 6)})}
    empty = frame_observables(0, 0, 0.0, [], system)
    assert empty['largest_component_size'] == 1 and empty['isolated_fraction'] == 1.0
    one = frame_observables(0, 0, 0.0, [(1, 5, 1, 2)], system)
    assert one['inter_bonds'] == 1 and one['largest_component_size'] == 2
    parallel = frame_observables(0, 0, 0.0, [(1, 5, 1, 2), (2, 6, 1, 2)], system)
    assert parallel['mean_k_bond'] == .8 and parallel['mean_edge_multiplicity'] == 2.0
    intra = frame_observables(0, 0, 0.0, [(1, 2, 1, 1)], system)
    assert intra['intra_bonds'] == 1 and intra['mean_intra_stickers_per_star'] == .4
    triangle = frame_observables(0, 0, 0.0, [(1, 5, 1, 2), (6, 9, 2, 3), (10, 3, 3, 1)], system)
    assert triangle['largest_component_size'] == 3 and triangle['mean_k_neighbor'] == 1.2
    clusters = frame_observables(0, 0, 0.0, [(1, 5, 1, 2), (9, 13, 3, 4)], system)
    assert clusters['component_sizes'] == [2, 2, 1]
    try:
        frame_observables(0, 0, 0.0, [(1, 5, 1, 2), (1, 6, 1, 2)], system)
    except ValueError:
        pass
    else:
        raise AssertionError('nonreciprocal synthetic topology was accepted')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--system', required=False)
    parser.add_argument('--sticker-type', type=int, default=2)
    parser.add_argument('--output-prefix')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('topology_files', nargs='*')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        print('P4.5 TOPOLOGY SELF_TEST PASS')
        return
    if not arguments.system or not arguments.output_prefix or not arguments.topology_files:
        parser.error('--system, --output-prefix, and one or more topology files are required')
    system = read_system(arguments.system, arguments.sticker_type)
    frame_rows = []
    histograms = {name: {} for name in ('degree_bond', 'degree_neighbor', 'edge_multiplicity',
                                        'cluster_sizes')}
    replica_summaries = []
    for replica, path in enumerate(arguments.topology_files, 1):
        rows = []
        counters = {name: collections.Counter() for name in histograms}
        for frame, step, time, pairs in topology_frames(path, system):
            row = frame_observables(frame, step, time, pairs, system)
            row.update({'replica': replica, 'source': path})
            rows.append(row)
            counters['degree_bond'].update(
                row['bond_degree'].get(star, 0) for star in system['stars'])
            counters['degree_neighbor'].update(row['neighbor_degree'].values())
            counters['edge_multiplicity'].update(row['edge_multiplicity'].values())
            counters['cluster_sizes'].update(row['component_sizes'])
        if not rows:
            fail(path, 'no topology frames')
        summary = summarize_replica(rows)
        summary.update({'replica': replica, 'source': path, 'frames': len(rows)})
        replica_summaries.append(summary)
        frame_rows.extend(rows)
        for name, counter in counters.items():
            histograms[name][str(replica)] = counter
            histograms[name].setdefault('all_frames', collections.Counter()).update(counter)
    paths = write_outputs(
        arguments.output_prefix, frame_rows, histograms, replica_summaries, system)
    print('P4.5 topology analysis written: {}'.format(', '.join(paths)))


if __name__ == '__main__':
    main()
