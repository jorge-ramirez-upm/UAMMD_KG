#!/usr/bin/env python3
"""Prepare and validate the fixed associating-star campaign without launching by default."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "campaign_protocol.json"
ANALYSIS_DIR = HERE.parent / "analysis"


def load_json(path):
    with Path(path).open(encoding="utf-8") as source:
        return json.load(source)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


def system_id(system):
    prefix = f"F{system['f']:02d}_N{system['N']:03d}_RP{round(100 * system['rho_p']):03d}"
    if not system["associating"]:
        return prefix + "_NONASSOC"
    return prefix + f"_EE{round(system['Ee']):02d}_EA{round(system['Ea']):02d}"


def campaign_systems(protocol=None):
    protocol = protocol or load_json(PROTOCOL_PATH)
    reference = protocol["associating_axes"]["reference"]
    unique = {}
    axes = {
        "association": ("Ee", protocol["associating_axes"]["association"]["Ee"]),
        "kinetics": ("Ea", protocol["associating_axes"]["kinetics"]["Ea"]),
        "density": ("rho_p", protocol["associating_axes"]["density"]["rho_p"]),
        "arm_length": ("N", protocol["associating_axes"]["arm_length"]["N"]),
        "functionality": ("f", protocol["associating_axes"]["functionality"]["f"]),
    }
    for group, (field, values) in axes.items():
        for value in values:
            system = dict(reference, associating=True)
            system[field] = value
            identifier = system_id(system)
            unique.setdefault(identifier, dict(system, groups=[]))["groups"].append(group)
    for control in protocol["controls"]:
        system = dict(control, associating=False, Ee=None, Ea=None, groups=["control"])
        unique[system_id(system)] = system

    common = {
        "schema_version": 1,
        "number_of_stars": protocol["number_of_stars"],
        "replicas": protocol["replicas"],
        "production_steps": protocol["production_steps"],
        "temperature": protocol["temperature"],
        "total_bead_density": protocol["total_bead_density"],
        "dt": protocol["dt"],
        "nu0": protocol["nu0"],
        "Nevery": protocol["Nevery"],
        "r_assoc": protocol["r_assoc"],
        "cadence_steps": protocol["cadence_steps"],
    }
    systems = []
    for identifier, system in sorted(unique.items()):
        systems.append(dict(common, system_id=identifier, **system))
    return systems


def select_systems(args):
    systems = campaign_systems()
    if getattr(args, "system", None):
        requested = set(args.system)
        systems = [item for item in systems if item["system_id"] in requested]
        missing = requested - {item["system_id"] for item in systems}
        if missing:
            raise ValueError("unknown system IDs: " + ", ".join(sorted(missing)))
    if getattr(args, "group", None):
        systems = [item for item in systems if args.group in item["groups"]]
    return systems


def geometry_id(system):
    return f"F{system['f']:02d}_N{system['N']:03d}_RP{round(100 * system['rho_p']):03d}"


def expected_geometry(system):
    polymer_beads = system["number_of_stars"] * (1 + system["f"] * system["N"])
    volume = polymer_beads / system["rho_p"]
    total_beads = round(system["total_bead_density"] * volume)
    return {
        "geometry_id": geometry_id(system),
        "f": system["f"],
        "N": system["N"],
        "rho_p": system["rho_p"],
        "number_of_stars": system["number_of_stars"],
        "polymer_beads": polymer_beads,
        "solvent_beads": total_beads - polymer_beads,
        "total_beads": total_beads,
        "target_volume": volume,
        "total_bead_density": system["total_bead_density"],
        "required_filename": "initial.lammpsdat",
        "generated_externally": True,
    }


def parse_lammps_data(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    result = {"atoms": {}, "bonds": [], "counts": {}, "bounds": {}}
    section = None
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        words = line.split()
        if len(words) >= 2 and words[1] in {"atoms", "bonds", "atom", "bond"}:
            if words[0].isdigit():
                result["counts"][" ".join(words[1:])] = int(words[0])
                continue
        if len(words) == 4 and words[2:] in (["xlo", "xhi"], ["ylo", "yhi"], ["zlo", "zhi"]):
            result["bounds"][words[2][0]] = (float(words[0]), float(words[1]))
            continue
        if words[0] in {"Atoms", "Bonds", "Velocities", "Masses"}:
            section = words[0]
            continue
        if section == "Atoms" and words[0].isdigit():
            if len(words) < 7:
                raise ValueError("Atoms rows must use LAMMPS full style")
            atom_id, molecule, atom_type = map(int, words[:3])
            if atom_id in result["atoms"]:
                raise ValueError(f"duplicate atom ID {atom_id}")
            result["atoms"][atom_id] = (molecule, atom_type)
        elif section == "Bonds" and words[0].isdigit():
            if len(words) < 4:
                raise ValueError("malformed Bonds row")
            result["bonds"].append((int(words[2]), int(words[3])))
    return result


def validate_geometry(path, expected):
    data = parse_lammps_data(path)
    atoms = data["atoms"]
    if len(atoms) != expected["total_beads"]:
        raise ValueError(f"expected {expected['total_beads']} atoms, found {len(atoms)}")
    if set(atoms) != set(range(1, len(atoms) + 1)):
        raise ValueError("atom IDs must be unique and contiguous from 1")
    if set(data["bounds"]) != {"x", "y", "z"}:
        raise ValueError("orthorhombic x/y/z box bounds are required")
    volume = math.prod(data["bounds"][axis][1] - data["bounds"][axis][0] for axis in "xyz")
    polymer = {atom for atom, (_, kind) in atoms.items() if kind in (1, 2)}
    solvent = {atom for atom, (_, kind) in atoms.items() if kind == 3}
    if len(polymer) != expected["polymer_beads"] or len(solvent) != expected["solvent_beads"]:
        raise ValueError("polymer/solvent bead counts do not match the requested geometry")
    if any(kind not in (1, 2, 3) for _, kind in atoms.values()):
        raise ValueError("only bead types 1 (polymer), 2 (sticker), and 3 (solvent) are allowed")
    stars = {}
    for atom in polymer:
        molecule, kind = atoms[atom]
        stars.setdefault(molecule, []).append((atom, kind))
    if len(stars) != expected["number_of_stars"]:
        raise ValueError(f"expected {expected['number_of_stars']} stars, found {len(stars)}")
    beads_per_star = 1 + expected["f"] * expected["N"]
    for molecule, members in stars.items():
        if len(members) != beads_per_star:
            raise ValueError(f"star {molecule} has {len(members)} beads, expected {beads_per_star}")
        if sum(kind == 2 for _, kind in members) != expected["f"]:
            raise ValueError(f"star {molecule} has the wrong sticker count")
    adjacency = {atom: set() for atom in polymer}
    for first, second in data["bonds"]:
        if first not in polymer or second not in polymer:
            raise ValueError("permanent bonds must connect polymer beads only")
        if atoms[first][0] != atoms[second][0]:
            raise ValueError("permanent bond crosses star molecule IDs")
        adjacency[first].add(second)
        adjacency[second].add(first)
    expected_bonds = expected["number_of_stars"] * expected["f"] * expected["N"]
    if len(data["bonds"]) != expected_bonds:
        raise ValueError(f"expected {expected_bonds} permanent bonds, found {len(data['bonds'])}")
    for molecule, members in stars.items():
        member_ids = {atom for atom, _ in members}
        pending = [next(iter(member_ids))]
        visited = set(pending)
        while pending:
            for neighbour in adjacency[pending.pop()]:
                if neighbour not in visited:
                    visited.add(neighbour)
                    pending.append(neighbour)
        if visited != member_ids:
            raise ValueError(f"star {molecule} permanent topology is disconnected")
        stickers = [atom for atom, kind in members if kind == 2]
        if any(len(adjacency[atom]) != 1 for atom in stickers):
            raise ValueError(f"star {molecule} has a nonterminal sticker")
        if sum(len(adjacency[atom]) == expected["f"] for atom, kind in members if kind == 1) != 1:
            raise ValueError(f"star {molecule} does not have one functionality-{expected['f']} center")
    polymer_density = len(polymer) / volume
    total_density = len(atoms) / volume
    if not math.isclose(polymer_density, expected["rho_p"], rel_tol=2e-4):
        raise ValueError(f"polymer density {polymer_density:.12g} differs from target {expected['rho_p']}")
    if not math.isclose(total_density, expected["total_bead_density"], rel_tol=2e-4):
        raise ValueError(f"total density {total_density:.12g} differs from target {expected['total_bead_density']}")
    return {"path": str(Path(path).resolve()), "sha256": sha256(path), "volume": volume,
            "polymer_density": polymer_density, "total_density": total_density}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_list(args):
    for system in select_systems(args):
        print(system["system_id"], ",".join(system["groups"]))


def command_init(args):
    root = Path(args.dataset_root).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"dataset root is not empty: {root}")
    protocol = load_json(PROTOCOL_PATH)
    write_json(root / "campaign_protocol.json", protocol)
    systems = campaign_systems(protocol)
    write_json(root / "manifest.json", {"schema_version": 1, "campaign": protocol["campaign"],
                                         "systems": [item["system_id"] for item in systems]})
    geometries = {}
    for system in systems:
        system_root = root / "systems" / system["system_id"]
        write_json(system_root / "system.json", system)
        for name in ("equilibration/e1", "equilibration/e2", "restart_bank", "production",
                     "analysis/topology", "analysis/bond_dynamics", "analysis/walking_hopping",
                     "analysis/percolation", "analysis/rheology", "analysis/transport",
                     "analysis/structure", "analysis/figures"):
            (system_root / name).mkdir(parents=True, exist_ok=True)
        geometries.setdefault(geometry_id(system), expected_geometry(system))
    for identifier, geometry in sorted(geometries.items()):
        input_root = root / "inputs" / identifier
        input_root.mkdir(parents=True, exist_ok=True)
        write_json(input_root / "requirements.example.json", geometry)
    (root / "aggregate" / "figures").mkdir(parents=True, exist_ok=True)
    print(root)


def command_validate_inputs(args):
    root = Path(args.dataset_root).resolve()
    seen = set()
    for system in select_systems(args):
        identifier = geometry_id(system)
        if identifier in seen:
            continue
        seen.add(identifier)
        path = root / "inputs" / identifier / "initial.lammpsdat"
        if not path.is_file():
            raise ValueError(f"missing user-generated input: {path}")
        result = validate_geometry(path, expected_geometry(system))
        write_json(path.with_suffix(path.suffix + ".validation.json"), result)
        print(identifier, "PASS", result["sha256"])


def replicas(value):
    selected = [int(item) for item in value.split(",")]
    if not selected or any(item not in (1, 2, 3) for item in selected) or len(set(selected)) != len(selected):
        raise ValueError("--replicas must be a unique comma-separated subset of 1,2,3")
    return selected


def command_prepare_production(args):
    root = Path(args.dataset_root).resolve()
    for system in select_systems(args):
        for replica in replicas(args.replicas):
            run_root = root / "systems" / system["system_id"] / "production" / f"r{replica:03d}"
            run_path = run_root / "run.json"
            if run_path.exists():
                raise ValueError(f"production replica already prepared: {run_path}")
            parent = root / "systems" / system["system_id"] / "restart_bank" / f"r{replica:03d}"
            particle = parent / "state.restart.lammpsdat"
            chemistry = parent / "state.assoc_restart"
            required = [particle] + ([chemistry] if system["associating"] else [])
            if any(not path.is_file() for path in required):
                raise ValueError("missing validated restart-bank parent: " + str(parent))
            run_root.mkdir(parents=True)
            write_json(run_path, {
                "schema_version": 1, "system_id": system["system_id"], "replica": replica,
                "status": "prepared", "completed_production_steps": 0,
                "parent_e1": str(parent / "e1_provenance.json"),
                "parent_e2": str(parent / "e2_provenance.json") if system["associating"] else None,
                "md_seed": 700000 + replica, "chemistry_seed": 800000 + replica,
                "checkpoint_history": [], "segments": [], "files": {}
            })
            print(run_path)


ANALYZERS = {
    "topology": "analyze_p45_topology.py",
    "bond_dynamics": "analyze_p46_bond_dynamics.py",
    "walking_hopping": "analyze_p47_walking_hopping.py",
    "percolation": "analyze_p48_percolation.py",
    "rheology": "analyze_p42_rheology_pilot.py",
    "com_msd": "analyze_p44_com_diffusion.py",
    "fsqt": "analyze_p44_com_fsqt.py",
}


def command_analyze(args):
    script = ANALYSIS_DIR / ANALYZERS[args.analysis]
    command = [sys.executable, str(script)] + args.analyzer_args
    print(" ".join(command))
    if args.execute:
        subprocess.run(command, check=True)


def build_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)
    for name in ("list", "validate-inputs"):
        child = subparsers.add_parser(name)
        child.add_argument("--system", action="append")
        child.add_argument("--group", choices=sorted(load_json(PROTOCOL_PATH)["groups"]))
        if name == "validate-inputs":
            child.add_argument("--dataset-root", required=True)
            child.set_defaults(function=command_validate_inputs)
        else:
            child.set_defaults(function=command_list)
    child = subparsers.add_parser("init")
    child.add_argument("--dataset-root", required=True)
    child.set_defaults(function=command_init)
    child = subparsers.add_parser("prepare-production")
    child.add_argument("--dataset-root", required=True)
    child.add_argument("--system", action="append")
    child.add_argument("--group", choices=sorted(load_json(PROTOCOL_PATH)["groups"]))
    child.add_argument("--replicas", default="1,2,3")
    child.set_defaults(function=command_prepare_production)
    child = subparsers.add_parser("analyze")
    child.add_argument("analysis", choices=sorted(ANALYZERS))
    child.add_argument("--execute", action="store_true")
    child.add_argument("analyzer_args", nargs=argparse.REMAINDER)
    child.set_defaults(function=command_analyze)
    return parser


def main():
    try:
        args = build_parser().parse_args()
        args.function(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
