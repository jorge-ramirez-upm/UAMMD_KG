#!/usr/bin/env python3
"""Fail-closed validation for the generated P3.3 C1 chemical restart bank."""
import argparse
import math
import os
import re
import statistics
import tempfile


CANONICAL = {
    'arms': 4, 'narm': 10, 'dt': 0.01, 'temperature': 1.0, 'Ea': 4.0,
    'Ee': 8.0, 'nu0': 20.0, 'Nevery': 100, 'r_assoc': 1.25,
    'damping': 2.0, 'K': 30.0, 'R0': 1.5,
}
LABEL = re.compile(r'^C1_e2_s(12001|12002)_t(40000|50000|60000)$')
METRICS = ('bound_fraction', 'intra', 'inter', 'L1', 'L2',
           'largest_cluster_fraction', 'mean_degree')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_metadata(path):
    lines = [line.strip() for line in open(path, encoding='utf-8') if line.strip()]
    require(lines and lines[0] == 'KG_ASSOC_RESTART 1', path + ': bad schema/version')
    values, pairs = {}, []
    index = 1
    while index < len(lines) and not lines[index].startswith('active_bonds '):
        fields = lines[index].split()
        require(len(fields) == 2 and fields[0] not in values, path + ': malformed field')
        values[fields[0]] = fields[1]
        index += 1
    require(index < len(lines), path + ': missing active_bonds')
    fields = lines[index].split()
    require(len(fields) == 2, path + ': malformed active_bonds')
    count = int(fields[1])
    for line in lines[index + 1:index + 1 + count]:
        pair = tuple(map(int, line.split()))
        require(len(pair) == 2 and pair[0] < pair[1], path + ': malformed pair')
        pairs.append(pair)
    require(lines[index + 1 + count:] == ['end'], path + ': missing/trailing end marker')
    return values, pairs


def read_snapshot(path):
    lines = open(path, encoding='utf-8').read().splitlines()
    atoms, bonds, positions, types, molecules = {}, [], {}, {}, {}
    bounds = {}
    declared_atoms = declared_bonds = None
    section = None
    for line in lines:
        words = line.split()
        if not words:
            continue
        if len(words) == 2 and words[1] == 'atoms':
            declared_atoms = int(words[0])
        elif len(words) == 2 and words[1] == 'bonds':
            declared_bonds = int(words[0])
        elif len(words) == 4 and words[2:] in (['xlo', 'xhi'], ['ylo', 'yhi'], ['zlo', 'zhi']):
            bounds[words[2][0]] = (float(words[0]), float(words[1]))
        elif words[0] == 'Atoms':
            section = 'atoms'
        elif words[0] == 'Velocities':
            section = 'velocities'
        elif words[0] == 'Bonds':
            section = 'bonds'
        elif section == 'atoms' and len(words) >= 6:
            atom, molecule, atom_type = map(int, words[:3])
            require(atom not in atoms, path + ': duplicate atom ID')
            atoms[atom] = words
            molecules[atom] = molecule
            types[atom] = atom_type
            positions[atom] = tuple(map(float, words[3:6]))
        elif section == 'bonds' and len(words) >= 4:
            bonds.append((int(words[2]), int(words[3])))
    require(declared_atoms == len(atoms) and declared_bonds == len(bonds), path + ': snapshot counts')
    require(set(bounds) == {'x', 'y', 'z'}, path + ': missing box bounds')
    return atoms, bonds, positions, types, molecules, bounds


def distance(a, b, bounds):
    squared = 0.0
    for coordinate, left, right in zip(range(3), 'xyz', 'xyz'):
        length = bounds[left][1] - bounds[left][0]
        delta = b[coordinate] - a[coordinate]
        delta -= length * round(delta / length)
        squared += delta * delta
    return math.sqrt(squared)


def graph(molecules, pairs):
    nodes = sorted(set(molecules.values()))
    neighbors = {node: set() for node in nodes}
    multiplicity = {}
    for first, second in pairs:
        left, right = molecules[first], molecules[second]
        if left == right:
            continue
        edge = tuple(sorted((left, right)))
        multiplicity[edge] = multiplicity.get(edge, 0) + 1
        neighbors[left].add(right)
        neighbors[right].add(left)
    l1 = sum(count * (count - 1) // 2 for count in multiplicity.values())
    l2 = sum(1 for a in nodes for b in neighbors[a] if b > a
             for c in neighbors[b] if c > b and c in neighbors[a])
    visited, clusters = set(), []
    for node in nodes:
        if node in visited:
            continue
        stack, size = [node], 0
        visited.add(node)
        while stack:
            current = stack.pop()
            size += 1
            for neighbor in neighbors[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        clusters.append(size)
    degrees = [len(neighbors[node]) for node in nodes]
    return l1, l2, max(clusters) / len(nodes), statistics.mean(degrees)


def validate(prefix):
    label = os.path.basename(prefix)
    match = LABEL.match(label)
    require(match is not None, prefix + ': unexpected bank label')
    seed, time_label = int(match.group(1)), int(match.group(2))
    metadata, pairs = read_metadata(prefix + '.assoc_restart')
    atoms, bonds, positions, types, molecules, bounds = read_snapshot(prefix + '.restart.lammpsdat')
    for key, expected in CANONICAL.items():
        require(key in metadata, prefix + ': missing ' + key)
        actual = float(metadata[key]) if isinstance(expected, float) else int(metadata[key])
        require(math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12), prefix + ': ' + key)
    require(int(metadata['seed']) == seed, prefix + ': seed mismatch')
    require(int(metadata['completed_steps']) == time_label * 100, prefix + ': step/label mismatch')
    require(len(atoms) == 43563 and len(bonds) == 40000, prefix + ': C1 size mismatch')
    stickers = {atom for atom, atom_type in types.items() if atom_type == 2}
    require(len(stickers) == 4000, prefix + ': sticker count')
    seen, maximum = set(), 0.0
    intra = inter = 0
    for first, second in pairs:
        require(first in atoms and second in atoms and first in stickers and second in stickers,
                prefix + ': invalid temporary endpoint')
        require(first not in seen and second not in seen, prefix + ': valence violation')
        seen.update((first, second))
        current = distance(positions[first], positions[second], bounds)
        require(current < CANONICAL['R0'], prefix + ': FENE distance >= R0')
        maximum = max(maximum, current)
        if molecules[first] == molecules[second]:
            intra += 1
        else:
            inter += 1
    require(int(metadata['creations']) - int(metadata['breaks']) == len(pairs),
            prefix + ': event/bond mismatch')
    polymer_molecules = {atom: molecule for atom, molecule in molecules.items()
                         if types[atom] in (1, 2)}
    l1, l2, largest, mean_degree = graph(polymer_molecules, pairs)
    return {'prefix': prefix, 'bonds': len(pairs), 'bound_fraction': 2 * len(pairs) / 4000,
            'intra': intra, 'inter': inter, 'L1': l1, 'L2': l2,
            'largest_cluster_fraction': largest, 'mean_degree': mean_degree,
            'max_active_bond_distance': maximum}


def self_test():
    with tempfile.TemporaryDirectory() as directory:
        prefix = os.path.join(directory, 'C1_e2_s12001_t40000')
        with open(prefix + '.assoc_restart', 'w', encoding='utf-8') as output:
            output.write('KG_ASSOC_RESTART 1\ncompleted_steps 4000000\narms 4\nnarm 10\n'
                         'dt 0.01\ntemperature 1\nEa 4\nEe 8\nnu0 20\nNevery 100\n'
                         'r_assoc 1.25\ndamping 2\nK 30\nR0 1.5\nseed 12001\n'
                         'creations 1\nbreaks 0\nactive_bonds 1\n1 2\nend\n')
        # The full C1-size guard is intentionally separate from parser self-tests.
        values, pairs = read_metadata(prefix + '.assoc_restart')
        require(values['completed_steps'] == '4000000' and pairs == [(1, 2)], 'metadata self-test')
        snapshot = prefix + '.restart.lammpsdat'
        with open(snapshot, 'w', encoding='utf-8') as output:
            output.write('test\n\n2 atoms\n1 bonds\n\n0 10 xlo xhi\n0 10 ylo yhi\n0 10 zlo zhi\n\n'
                         'Atoms # bond\n\n1 1 2 0 0 0\n2 2 2 0.5 0 0\n\n'
                         'Velocities\n\n1 0 0 0\n2 0 0 0\n\nBonds\n\n1 1 1 2\n')
        atoms, bonds, positions, types, molecules, bounds = read_snapshot(snapshot)
        require(len(atoms) == 2 and bonds == [(1, 2)] and types[1] == 2,
                'snapshot self-test')
        require(math.isclose(distance(positions[1], positions[2], bounds), 0.5),
                'minimum-image self-test')
        l1, l2, largest, mean_degree = graph(molecules, [(1, 2)])
        require((l1, l2, largest, mean_degree) == (0, 0, 1.0, 1.0), 'graph self-test')
    print('C1 RESTART BANK VALIDATOR SELF_TEST PASS')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bank-dir')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    require(args.bank_dir is not None, '--bank-dir is required')
    prefixes = sorted(os.path.join(args.bank_dir, name[:-14]) for name in os.listdir(args.bank_dir)
                      if name.endswith('.assoc_restart'))
    require(len(prefixes) == 6, 'expected exactly six C1 restart metadata files')
    records = [validate(prefix) for prefix in prefixes]
    print('prefix bonds bound_fraction N_intra N_inter L1 L2 largest_cluster_fraction mean_degree max_active_distance')
    for record in records:
        print('{prefix} {bonds} {bound_fraction:.9f} {intra} {inter} {L1} {L2} '
              '{largest_cluster_fraction:.9f} {mean_degree:.9f} {max_active_bond_distance:.9f}'.format(**record))
    for metric in METRICS:
        values = [record[metric] for record in records]
        print('bank {} mean={:.9g} range=[{:.9g}, {:.9g}]'.format(metric, statistics.mean(values), min(values), max(values)))


if __name__ == '__main__':
    main()
