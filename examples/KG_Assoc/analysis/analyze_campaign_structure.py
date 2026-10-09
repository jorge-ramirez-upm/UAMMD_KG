#!/usr/bin/env python3
"""Compute PBC-safe star radius of gyration from campaign bead trajectories."""

import argparse
from array import array
import csv
import json
import math
from pathlib import Path
import statistics
import struct
import sys


MAGIC = b"KG_BEADS_BIN_V2"
FRAME_MAGIC = 0x4652414D


def read_header(source):
    if sys.byteorder != "little":
        raise ValueError("campaign binary trajectories currently require a little-endian host")
    if source.read(16).rstrip(b"\0") != MAGIC:
        raise ValueError("invalid campaign bead-trajectory magic")
    version, = struct.unpack("=I", source.read(4))
    natoms, = struct.unpack("=Q", source.read(8))
    nbonds, = struct.unpack("=Q", source.read(8))
    bounds = struct.unpack("=6d", source.read(48))
    if version != 2 or natoms == 0:
        raise ValueError("unsupported campaign bead-trajectory header")
    atoms = [struct.unpack("=iii", source.read(12)) for _ in range(natoms)]
    if [atom[0] for atom in atoms] != list(range(1, natoms + 1)):
        raise ValueError("trajectory atom IDs are not stable and ordered")
    bonds = [struct.unpack("=ii", source.read(8)) for _ in range(nbonds)]
    if any(first <= 0 or second <= 0 or first > natoms or second > natoms
           for first, second in bonds):
        raise ValueError("trajectory permanent bond has an invalid atom ID")
    lengths = (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
    return natoms, atoms, bonds, lengths


def minimum_image(value, length):
    return value - length * round(value / length)


def unwrap_star(coordinates, indices, adjacency, lengths):
    anchor = indices[0]
    unwrapped = {anchor: tuple(coordinates[3 * anchor:3 * anchor + 3])}
    pending = [anchor]
    members = set(indices)
    while pending:
        current = pending.pop()
        current_raw = coordinates[3 * current:3 * current + 3]
        for neighbour in adjacency[current]:
            if neighbour not in members or neighbour in unwrapped:
                continue
            unwrapped[neighbour] = tuple(
                unwrapped[current][axis] + minimum_image(
                    coordinates[3 * neighbour + axis] - current_raw[axis], lengths[axis])
                for axis in range(3))
            pending.append(neighbour)
    if len(unwrapped) != len(indices):
        raise ValueError("permanent star topology is disconnected")
    return [unwrapped[index] for index in indices]


def frame_rg2(coordinates, stars, adjacency, lengths):
    total = 0.0
    for indices in stars:
        relative = unwrap_star(coordinates, indices, adjacency, lengths)
        center = tuple(sum(point[axis] for point in relative) / len(relative)
                       for axis in range(3))
        total += sum(sum((point[axis] - center[axis]) ** 2 for axis in range(3))
                     for point in relative) / len(relative)
    return total / len(stars)


def analyze(path):
    rows = []
    with Path(path).open("rb") as source:
        natoms, atoms, bonds, lengths = read_header(source)
        molecules = {}
        for index, (_, molecule, atom_type) in enumerate(atoms):
            if atom_type in (1, 2):
                molecules.setdefault(molecule, []).append(index)
        if not molecules:
            raise ValueError("trajectory contains no star-polymer beads")
        stars = [molecules[key] for key in sorted(molecules)]
        adjacency = [set() for _ in range(natoms)]
        for first, second in bonds:
            first -= 1
            second -= 1
            if atoms[first][1] != atoms[second][1]:
                raise ValueError("permanent bond crosses molecule IDs")
            adjacency[first].add(second)
            adjacency[second].add(first)
        frame_bytes = natoms * 12
        while True:
            marker = source.read(4)
            if not marker:
                break
            if len(marker) != 4 or struct.unpack("=I", marker)[0] != FRAME_MAGIC:
                raise ValueError("malformed campaign bead frame marker")
            step, time = struct.unpack("=qd", source.read(16))
            payload = source.read(frame_bytes)
            if len(payload) != frame_bytes:
                raise ValueError("truncated campaign bead frame")
            coordinates = array("f")
            coordinates.frombytes(payload)
            rows.append((step, time, frame_rg2(coordinates, stars, adjacency, lengths)))
    if not rows:
        raise ValueError("trajectory contains no frames")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("trajectories", nargs="+")
    arguments = parser.parse_args()
    replica_means = []
    with open(arguments.output_prefix + ".frames.csv", "w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["replica", "step", "time", "mean_rg2"])
        for replica, path in enumerate(arguments.trajectories, 1):
            rows = analyze(path)
            replica_means.append(sum(row[2] for row in rows) / len(rows))
            writer.writerows((replica,) + row for row in rows)
    mean = statistics.mean(replica_means)
    standard_deviation = statistics.stdev(replica_means) if len(replica_means) > 1 else 0.0
    summary = {"schema_version": 1, "replicas": len(replica_means),
               "mean_rg2": mean, "replica_standard_deviation": standard_deviation,
               "replica_sem": standard_deviation / math.sqrt(len(replica_means)),
               "replica_means": replica_means}
    with open(arguments.output_prefix + ".summary.json", "w", encoding="utf-8") as output:
        json.dump(summary, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
