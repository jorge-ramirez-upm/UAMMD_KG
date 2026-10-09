#!/usr/bin/env python3
"""Prepare and validate the fixed associating-star campaign without launching by default."""

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "campaign_protocol.json"
ANALYSIS_DIR = HERE.parent / "analysis"
REPOSITORY_ROOT = HERE.parents[2]


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


def e2_bank_id(system):
    if not system["associating"]:
        return None
    return geometry_id(system) + f"_EE{round(system['Ee']):02d}"


def expected_geometry(system):
    polymer_beads = system["number_of_stars"] * (1 + system["f"] * system["N"])
    volume = polymer_beads / system["rho_p"]
    total_beads = math.floor(system["total_bead_density"] * volume + 0.5)
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
            if len(words) < 6:
                raise ValueError("Atoms rows must include ID, molecule, type and xyz")
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
                                         "systems": [item["system_id"] for item in systems],
                                         "production_continuation": False})
    write_json(root / "production_config.json", {
        "schema_version": 1, "steps": protocol["production_steps"],
        "dt": protocol["dt"], "temperature": protocol["temperature"],
        "total_density": protocol["total_bead_density"], "nu0": protocol["nu0"],
        "Nevery": protocol["Nevery"], "r_assoc": protocol["r_assoc"],
        "continuation": False, "cadence_steps": protocol["cadence_steps"]})
    geometries = {}
    for system in systems:
        system_root = root / "systems" / system["system_id"]
        system = dict(system, e1_bank_id=geometry_id(system), e2_bank_id=e2_bank_id(system))
        write_json(system_root / "system.json", system)
        for name in ("production",
                     "analysis/topology", "analysis/bond_dynamics", "analysis/walking_hopping",
                     "analysis/percolation", "analysis/rheology", "analysis/transport",
                     "analysis/structure", "analysis/figures"):
            (system_root / name).mkdir(parents=True, exist_ok=True)
        geometries.setdefault(geometry_id(system), expected_geometry(system))
    for identifier, geometry in sorted(geometries.items()):
        input_root = root / "inputs" / identifier
        input_root.mkdir(parents=True, exist_ok=True)
        write_json(input_root / "requirements.example.json", geometry)
        for replica in (1, 2, 3):
            (root / "banks" / "e1" / identifier / f"r{replica:03d}").mkdir(
                parents=True, exist_ok=True)
    for identifier in sorted({e2_bank_id(system) for system in systems if system["associating"]}):
        for replica in (1, 2, 3):
            (root / "banks" / "e2" / identifier / f"r{replica:03d}").mkdir(
                parents=True, exist_ok=True)
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


def git_sha():
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, check=True,
        text=True, capture_output=True).stdout.strip()


def run_or_print(command, execute, stdout_path=None, stderr_path=None):
    print(" ".join(str(item) for item in command))
    if not execute:
        return 0
    if stdout_path is None:
        return subprocess.run(command, check=False).returncode
    with Path(stdout_path).open("x", encoding="utf-8") as stdout, \
            Path(stderr_path).open("x", encoding="utf-8") as stderr:
        return subprocess.run(command, stdout=stdout, stderr=stderr, check=False).returncode


def selected_bank_systems(args):
    systems = select_systems(args)
    unique = {}
    for system in systems:
        key = geometry_id(system) if args.stage == "e1" else e2_bank_id(system)
        if key is not None:
            unique.setdefault(key, system)
    return unique


def command_equilibrate(args):
    root = Path(args.dataset_root).resolve()
    executable = HERE.parent / ("kg_assoc_star_equilibrate" if args.stage == "e1"
                                else "kg_assoc_stars")
    for bank_id, system in selected_bank_systems(args).items():
        for replica in replicas(args.replicas):
            bank = root / "banks" / args.stage / bank_id / f"r{replica:03d}"
            if args.stage == "e1":
                output = bank / "state.e1.lammpsdat"
                diagnostics = bank / "diagnostics.tsv"
                if output.exists() or diagnostics.exists():
                    raise ValueError(f"E1 output already exists: {bank}")
                stage4_steps = {10: 2000000, 20: 2000000, 40: 8000000}[system["N"]]
                command = [str(executable), "--input",
                           str(root / "inputs" / geometry_id(system) / "initial.lammpsdat"),
                           "--output", str(output), "--diagnostics", str(diagnostics),
                           "--arms", str(system["f"]), "--narm", str(system["N"]),
                           "--seed", str(12000 + replica), "--stage3b-steps", "20000",
                           "--wca-ramp", "--wca-ramp-steps", "500",
                           "--stage4-steps", str(stage4_steps), "--dt-dpd", "0.01",
                           "--dt-wca", "0.01", "--conformation-every", "1000"]
            else:
                if args.steps is None:
                    raise ValueError("E2 requires --steps chosen from stationarity evidence")
                output_prefix = bank / "state"
                if any(bank.glob("state.*")):
                    raise ValueError(f"E2 output already exists: {bank}")
                command = [str(executable), "--input",
                           str(root / "banks" / "e1" / geometry_id(system) /
                               f"r{replica:03d}" / "state.e1.lammpsdat"),
                           "--output", str(output_prefix), "--arms", str(system["f"]),
                           "--narm", str(system["N"]), "--steps", str(args.steps),
                           "--dt", "0.01", "--temperature", "1", "--Ea", str(args.equilibration_ea),
                           "--Ee", str(system["Ee"]), "--nu0", "20", "--Nevery", "100",
                           "--r-assoc", "1.25", "--seed", str(22000 + replica),
                           "--diagnostic-every", "1000"]
            write_json(bank / "command.json", {
                "schema_version": 1, "stage": args.stage, "bank_id": bank_id,
                "replica": replica, "command": command, "git_sha": git_sha(),
                "status": "planned"})
            return_code = run_or_print(command, args.execute, bank / "stdout.log",
                                       bank / "stderr.log") if args.execute else run_or_print(command, False)
            if args.execute:
                record = load_json(bank / "command.json")
                record.update(status="finished" if return_code == 0 else "incomplete",
                              exit_code=return_code)
                write_json(bank / "command.json", record)
                if return_code != 0:
                    raise ValueError(f"{args.stage.upper()} failed; retained incomplete state: {bank}")


def command_validate_equilibration(args):
    root = Path(args.dataset_root).resolve()
    for bank_id, _ in selected_bank_systems(args).items():
        reports = []
        for replica in replicas(args.replicas):
            bank = root / "banks" / args.stage / bank_id / f"r{replica:03d}"
            source = bank / ("diagnostics.tsv" if args.stage == "e1" else "state.state")
            if not source.is_file():
                raise ValueError(f"missing equilibration diagnostics: {source}")
            analyzer = (HERE.parent / "analyze_e1_stationarity.py" if args.stage == "e1"
                        else ANALYSIS_DIR / "analyze_e2_stationarity.py")
            result = subprocess.run([sys.executable, str(analyzer), str(source)], check=True,
                                    text=True, capture_output=True)
            report = bank / "stationarity_report.txt"
            report.write_text(result.stdout, encoding="utf-8")
            reports.append({"replica": replica, "report": str(report),
                            "sha256": sha256(report)})
        validation = root / "banks" / args.stage / bank_id / "validation.json"
        write_json(validation, {"schema_version": 1, "stage": args.stage,
                                "bank_id": bank_id, "status": "review_required",
                                "reports": reports})
        print(validation)


def command_accept_equilibration(args):
    root = Path(args.dataset_root).resolve()
    validation = root / "banks" / args.stage / args.bank_id / "validation.json"
    record = load_json(validation)
    if record.get("status") != "review_required":
        raise ValueError("equilibration must first have review_required diagnostics")
    evidence = Path(args.evidence).resolve()
    if not evidence.is_file():
        raise ValueError(f"missing review evidence: {evidence}")
    record.update(status="accepted", accepted_evidence=str(evidence),
                  accepted_evidence_sha256=sha256(evidence),
                  accepted_at=datetime.now(timezone.utc).isoformat())
    write_json(validation, record)
    print(validation)


def command_prepare_production(args):
    root = Path(args.dataset_root).resolve()
    for system in select_systems(args):
        bank_stage = "e2" if system["associating"] else "e1"
        bank_id = e2_bank_id(system) if system["associating"] else geometry_id(system)
        validation_path = root / "banks" / bank_stage / bank_id / "validation.json"
        if not validation_path.is_file() or load_json(validation_path).get("status") != "accepted":
            raise ValueError(f"equilibration bank is not accepted: {validation_path}")
        for replica in replicas(args.replicas):
            run_root = root / "systems" / system["system_id"] / "production" / f"r{replica:03d}"
            run_path = run_root / "run.json"
            if run_path.exists():
                raise ValueError(f"production replica already prepared: {run_path}")
            parent = root / "banks" / bank_stage / bank_id / f"r{replica:03d}"
            particle = parent / ("state.restart.lammpsdat" if system["associating"]
                                 else "state.e1.lammpsdat")
            chemistry = parent / "state.assoc_restart"
            required = [particle] + ([chemistry] if system["associating"] else [])
            if any(not path.is_file() for path in required):
                raise ValueError("missing validated restart-bank parent: " + str(parent))
            expected = expected_geometry(system)
            validated = validate_geometry(particle, expected)
            if system["associating"]:
                validate_assoc_initial_state(chemistry, system)
            run_root.mkdir(parents=True)
            system_index = [item["system_id"] for item in campaign_systems()].index(
                system["system_id"])
            seed = 700000 + 100 * system_index + replica
            write_json(run_path, {
                "schema_version": 1, "system_id": system["system_id"], "replica": replica,
                "status": "prepared", "completed_production_steps": 0,
                "parent_e1": str(root / "banks" / "e1" / geometry_id(system) /
                                 f"r{replica:03d}" / "state.e1.lammpsdat"),
                "parent_e2": str(parent / "state") if system["associating"] else None,
                "md_seed": seed, "chemistry_seed": seed, "attempt": 1,
                "command": [], "exit_code": None, "validation": {}, "files": {},
                "git_sha": git_sha(), "production_continuation": False,
                "geometry": {**expected, **validated},
                "output_cadence_steps": system["cadence_steps"],
            })
            print(run_path)


def production_command(root, system, run):
    executable = HERE.parent / "kg_assoc_campaign_production"
    run_root = root / "systems" / system["system_id"] / "production" / f"r{run['replica']:03d}"
    output = run_root / "run"
    command = [str(executable), "--output", str(output), "--seed", str(run["md_seed"])]
    if system["associating"]:
        command += ["--equilibrated-prefix", run["parent_e2"], "--Ea", str(system["Ea"]),
                    "--Ee", str(system["Ee"])]
    else:
        command += ["--input", run["parent_e1"], "--arms", str(system["f"]),
                    "--narm", str(system["N"]), "--non-associating"]
    return command


def command_launch_production(args):
    root = Path(args.dataset_root).resolve()
    if not args.execute:
        print("DRY RUN: pass --execute to start selected uninterrupted trajectories")
    for system in select_systems(args):
        for replica in replicas(args.replicas):
            run_path = root / "systems" / system["system_id"] / "production" / f"r{replica:03d}" / "run.json"
            run = load_json(run_path)
            if run["status"] != "prepared":
                raise ValueError(f"only a prepared replica may launch: {run_path}")
            command = production_command(root, system, run)
            print(" ".join(command))
            if not args.execute:
                continue
            executable = Path(command[0])
            if not executable.is_file():
                raise ValueError(f"missing production executable: {executable}")
            with (run_path.parent / "stdout.log").open("x", encoding="utf-8") as stdout, \
                    (run_path.parent / "stderr.log").open("x", encoding="utf-8") as stderr:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
                run.update(status="running", command=command, pid=process.pid,
                           started_at=datetime.now(timezone.utc).isoformat(),
                           executable=str(executable.resolve()),
                           executable_sha256=sha256(executable))
                write_json(run_path, run)
                try:
                    return_code = process.wait()
                except KeyboardInterrupt:
                    process.terminate()
                    process.wait()
                    run = load_json(run_path)
                    run.update(status="incomplete", exit_code=process.returncode,
                               finished_at=datetime.now(timezone.utc).isoformat(),
                               completed_production_steps=0)
                    write_json(run_path, run)
                    raise ValueError(f"production interrupted and marked incomplete: {run_path}")
            run = load_json(run_path)
            run.update(exit_code=return_code, finished_at=datetime.now(timezone.utc).isoformat())
            completion = run_path.parent / "run.complete.json"
            if return_code == 0 and completion.is_file():
                completed = load_json(completion).get("production_steps")
                run["status"] = "complete" if completed == 100000000 else "invalid"
                run["completed_production_steps"] = completed or 0
            else:
                run["status"] = "incomplete"
                run["completed_production_steps"] = 0
            write_json(run_path, run)
            if run["status"] != "complete":
                raise ValueError(f"production did not complete; no resume is permitted: {run_path}")


def verify_binary_trajectory(path, natoms):
    with Path(path).open("rb") as source:
        if source.read(16).rstrip(b"\0") != b"KG_BEADS_BIN_V2":
            raise ValueError("invalid full-bead binary trajectory magic")
        version = struct.unpack("=I", source.read(4))[0]
        particles = struct.unpack("=Q", source.read(8))[0]
        bonds = struct.unpack("=Q", source.read(8))[0]
    if version != 2 or particles != natoms:
        raise ValueError("full-bead binary header mismatch")
    header = 16 + 4 + 8 + 8 + 6 * 8 + natoms * 12 + bonds * 8
    frame = 4 + 8 + 8 + natoms * 12
    size = Path(path).stat().st_size
    if size < header or (size - header) % frame:
        raise ValueError("invalid full-bead binary trajectory size")
    frames = []
    with Path(path).open("rb") as source:
        source.seek(header)
        for _ in range((size - header) // frame):
            marker, step, time = struct.unpack("=Iqd", source.read(20))
            if marker != 0x4652414D:
                raise ValueError("invalid full-bead frame marker")
            frames.append((step, time))
            source.seek(natoms * 12, os.SEEK_CUR)
    return frames


def verify_thermo(path, completion, initial_bonds, sticker_count):
    expected_step = completion["initial_absolute_step"] + 1000
    rows = 0
    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip() or line.startswith("#"):
                continue
            words = line.split()
            if len(words) != 15:
                raise ValueError("malformed thermodynamic row")
            step = int(words[0])
            values = [float(value) for value in words[1:9]]
            bonds, intra, inter, free, creations, breaks = map(int, words[9:])
            if step != expected_step or not math.isclose(values[0], step * 0.01,
                                                          rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("thermodynamic cadence or time mismatch")
            if not all(math.isfinite(value) for value in values):
                raise ValueError("nonfinite thermodynamic value")
            if bonds != initial_bonds + creations - breaks or intra + inter != bonds:
                raise ValueError("thermodynamic bond-count conservation failure")
            if free != sticker_count - 2 * bonds:
                raise ValueError("thermodynamic unbound-sticker count mismatch")
            expected_step += 1000
            rows += 1
    if expected_step - 1000 != completion["final_absolute_step"]:
        raise ValueError("thermodynamic stream does not reach the final step")
    return rows


def read_topology_frames(path):
    frames = []
    remaining_pairs = 0
    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip() or line.startswith("#"):
                continue
            words = line.split()
            if remaining_pairs:
                if len(words) != 4:
                    raise ValueError("malformed topology pair row")
                remaining_pairs -= 1
                continue
            if len(words) != 4 or words[0] != "FRAME":
                raise ValueError("malformed topology frame header")
            frames.append((int(words[1]), float(words[2])))
            remaining_pairs = int(words[3])
    if remaining_pairs:
        raise ValueError("truncated topology frame")
    return frames


def read_com_frames(path, stars_per_frame):
    frames = []
    current = None
    molecule_ids = set()
    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip() or line.startswith("#"):
                continue
            words = line.split()
            if len(words) != 6:
                raise ValueError("malformed COM row")
            frame = (int(words[0]), float(words[1]))
            molecule = int(words[2])
            if current is not None and frame != current:
                if len(molecule_ids) != stars_per_frame:
                    raise ValueError("incomplete COM frame")
                frames.append(current)
                molecule_ids = set()
            if molecule in molecule_ids:
                raise ValueError("duplicate molecule ID in COM frame")
            current = frame
            molecule_ids.add(molecule)
    if current is not None:
        if len(molecule_ids) != stars_per_frame:
            raise ValueError("incomplete COM frame")
        frames.append(current)
    return frames


def read_initial_active_pairs(path):
    pairs = set()
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    marker = next((index for index, line in enumerate(lines)
                   if line.startswith("active_bonds ")), None)
    if marker is None:
        return pairs
    count = int(lines[marker].split()[1])
    for line in lines[marker + 1:marker + 1 + count]:
        first, second = map(int, line.split())
        pairs.add((first, second))
    return pairs


def validate_assoc_initial_state(path, system):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "KG_ASSOC_RESTART 1":
        raise ValueError(f"unsupported E2 state metadata: {path}")
    values = {}
    for line in lines[1:]:
        words = line.split()
        if len(words) == 2 and words[0] not in {"end"}:
            values.setdefault(words[0], words[1])
    expected = {"arms": system["f"], "narm": system["N"], "dt": 0.01,
                "temperature": 1.0, "Ee": system["Ee"], "nu0": 20.0,
                "Nevery": 100, "r_assoc": 1.25}
    for key, value in expected.items():
        if key not in values or not math.isclose(float(values[key]), float(value),
                                                  rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"E2 state {key} does not match system: {path}")
    pairs = read_initial_active_pairs(path)
    endpoints = [atom for pair in pairs for atom in pair]
    if len(endpoints) != len(set(endpoints)):
        raise ValueError("E2 state violates valence-one partner state")
    if int(values.get("creations", -1)) - int(values.get("breaks", -1)) != len(pairs):
        raise ValueError("E2 state event counters disagree with active bonds")
    return pairs


def reconstruct_events(event_path, initial_pairs):
    active = set(initial_pairs)
    partners = {atom for pair in active for atom in pair}
    events = 0
    with Path(event_path).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip() or line.startswith("#"):
                continue
            words = line.split()
            event_type = words[2]
            pair = tuple(sorted((int(words[3]), int(words[4]))))
            if event_type == "C":
                if pair in active or pair[0] in partners or pair[1] in partners:
                    raise ValueError("event stream violates reciprocal valence-one state")
                active.add(pair)
                partners.update(pair)
            elif event_type == "B":
                if pair not in active:
                    raise ValueError("event stream breaks an inactive pair")
                active.remove(pair)
                partners.difference_update(pair)
            else:
                raise ValueError("unknown production event type")
            events += 1
    return active, events


def read_final_pairs(path):
    pairs = set()
    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip() or line.startswith("#"):
                continue
            first, second = map(int, line.split()[:2])
            pairs.add(tuple(sorted((first, second))))
    return pairs


def verify_run(root, system, replica, hashes=True, expected_steps=100000000):
    run_root = root / "systems" / system["system_id"] / "production" / f"r{replica:03d}"
    prefix = run_root / "run"
    required = [prefix.with_suffix(suffix) for suffix in (
        ".thermo.tsv", ".events", ".stress_correlator", ".com_trajectory",
        ".topology", ".beads.bin", ".final.lammpsdat", ".final_associations",
        ".complete.json")]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError("missing production outputs: " + ", ".join(missing))
    completion = load_json(prefix.with_suffix(".complete.json"))
    if completion.get("production_steps") != expected_steps:
        raise ValueError("completion record has the wrong production duration")
    run = load_json(run_path(root, system, replica))
    initial = (read_initial_active_pairs(run["parent_e2"] + ".assoc_restart")
               if system["associating"] else set())
    thermo_rows = verify_thermo(prefix.with_suffix(".thermo.tsv"), completion,
                                len(initial), system["number_of_stars"] * system["f"])
    if thermo_rows != expected_steps // 1000:
        raise ValueError("thermodynamic sample count mismatch")
    topology_frames = read_topology_frames(prefix.with_suffix(".topology"))
    com_frames = read_com_frames(prefix.with_suffix(".com_trajectory"),
                                 system["number_of_stars"])
    if len(topology_frames) != expected_steps // 10000:
        raise ValueError("topology frame count mismatch")
    if com_frames != topology_frames:
        raise ValueError("COM and topology frames are not synchronized")
    expected_topology = [(step, step * 0.01) for step in range(
        completion["initial_absolute_step"] + 10000,
        completion["final_absolute_step"] + 1, 10000)]
    if topology_frames != expected_topology:
        raise ValueError("COM/topology cadence does not span the production interval")
    geometry = expected_geometry(system)
    bead_frames = verify_binary_trajectory(prefix.with_suffix(".beads.bin"),
                                           geometry["total_beads"])
    expected_beads = [(step, step * 0.01) for step in range(
        completion["initial_absolute_step"] + 100000,
        completion["final_absolute_step"] + 1, 100000)]
    if bead_frames != expected_beads:
        raise ValueError("full-bead frame count mismatch")
    stress_header = prefix.with_suffix(".stress_correlator").read_text(
        encoding="utf-8", errors="replace").splitlines()[0]
    match = re.search(r"stress_samples=(\d+)", stress_header)
    if not match or int(match.group(1)) != expected_steps:
        raise ValueError("stress sample count mismatch")
    final, event_count = reconstruct_events(prefix.with_suffix(".events"), initial)
    if final != read_final_pairs(prefix.with_suffix(".final_associations")):
        raise ValueError("event reconstruction disagrees with final temporary bonds")
    validate_geometry(prefix.with_suffix(".final.lammpsdat"), geometry)
    files = {path.name: {"size": path.stat().st_size} for path in required}
    if hashes:
        for path in required:
            files[path.name]["sha256"] = sha256(path)
    return {"status": "valid", "event_count": event_count, "files": files}


def run_path(root, system, replica):
    return root / "systems" / system["system_id"] / "production" / f"r{replica:03d}" / "run.json"


def command_verify_production(args):
    root = Path(args.dataset_root).resolve()
    for system in select_systems(args):
        for replica in replicas(args.replicas):
            path = run_path(root, system, replica)
            run = load_json(path)
            validation = verify_run(root, system, replica, not args.skip_hashes)
            run.update(status="complete", completed_production_steps=100000000,
                       validation=validation, files=validation["files"])
            write_json(path, run)
            print(system["system_id"], f"r{replica:03d}", "PASS")


def command_status(args):
    root = Path(args.dataset_root).resolve()
    for system in select_systems(args):
        for replica in replicas(args.replicas):
            path = run_path(root, system, replica)
            if not path.is_file():
                status = "not_prepared"
            else:
                record = load_json(path)
                status = record["status"]
                if status == "running":
                    completion = path.parent / "run.complete.json"
                    if completion.is_file() and load_json(completion).get("production_steps") == 100000000:
                        status = "complete"
                        record.update(status=status, completed_production_steps=100000000)
                        write_json(path, record)
                    else:
                        try:
                            pid = record.get("pid")
                            if not isinstance(pid, int) or pid <= 0:
                                raise ProcessLookupError
                            os.kill(pid, 0)
                        except OSError:
                            status = "incomplete"
                            record.update(status=status, completed_production_steps=0)
                            write_json(path, record)
            print(system["system_id"], f"r{replica:03d}", status)


ANALYZERS = {
    "topology": "analyze_p45_topology.py",
    "bond_dynamics": "analyze_p46_bond_dynamics.py",
    "walking_hopping": "analyze_p47_walking_hopping.py",
    "percolation": "analyze_p48_percolation.py",
    "rheology": "analyze_p42_rheology_pilot.py",
    "com_msd": "analyze_p44_com_diffusion.py",
    "fsqt": "analyze_p44_com_fsqt.py",
    "structure": "analyze_campaign_structure.py",
}


def command_analyze(args):
    root = Path(args.dataset_root).resolve()
    for system in select_systems(args):
        analysis_root = (root / "systems" / system["system_id"] / "analysis" /
                         args.analysis / args.version)
        if analysis_root.exists():
            raise ValueError(f"analysis version already exists: {analysis_root}")
        prefixes = [root / "systems" / system["system_id"] / "production" /
                    f"r{replica:03d}" / "run" for replica in (1, 2, 3)]
        if any(not prefix.with_suffix(".complete.json").is_file() for prefix in prefixes):
            raise ValueError(f"analysis requires three complete replicas: {system['system_id']}")
        output_prefix = analysis_root / args.analysis
        script = ANALYSIS_DIR / ANALYZERS[args.analysis]
        system_file = Path(load_json(run_path(root, system, 1))["parent_e1"])
        if args.analysis == "topology":
            command = [sys.executable, str(script), "--system", str(system_file),
                       "--output-prefix", str(output_prefix)] + [
                           str(prefix.with_suffix(".topology")) for prefix in prefixes]
        elif args.analysis == "bond_dynamics":
            command = [sys.executable, str(script), "--system", str(system_file),
                       "--output-prefix", str(output_prefix)] + [
                           str(prefix.with_suffix(".events")) for prefix in prefixes]
        elif args.analysis in ("walking_hopping", "percolation"):
            command = [sys.executable, str(script), "--system", str(system_file),
                       "--output-prefix", str(output_prefix)] + [str(item) for item in prefixes]
        elif args.analysis == "rheology":
            command = [sys.executable, str(script), "--output-prefix", str(output_prefix)] + [
                str(prefix.with_suffix(".stress_correlator")) for prefix in prefixes]
        elif args.analysis in ("com_msd", "fsqt"):
            interpreter = shutil.which("python3.11") or sys.executable
            command = [interpreter, str(script), "--output-prefix", str(output_prefix)] + [
                str(prefix.with_suffix(".com_trajectory")) for prefix in prefixes]
        else:
            command = [sys.executable, str(script), "--output-prefix", str(output_prefix)] + [
                str(prefix.with_suffix(".beads.bin")) for prefix in prefixes]
        if not args.execute:
            run_or_print(command, False)
            continue
        analysis_root.mkdir(parents=True)
        write_json(analysis_root / "analysis.json", {
            "schema_version": 1, "analysis": args.analysis, "version": args.version,
            "system_id": system["system_id"], "command": command, "git_sha": git_sha(),
            "status": "planned"})
        return_code = run_or_print(command, True, analysis_root / "stdout.log",
                                   analysis_root / "stderr.log")
        record = load_json(analysis_root / "analysis.json")
        record.update(status="complete" if return_code == 0 else "failed",
                      exit_code=return_code,
                      completed_at=datetime.now(timezone.utc).isoformat())
        write_json(analysis_root / "analysis.json", record)
        if return_code != 0:
            raise ValueError(f"analysis failed: {analysis_root}")


def flatten_scalars(value, prefix=""):
    rows = []
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{prefix}.{key}" if prefix else key
            rows.extend(flatten_scalars(child, name))
    elif isinstance(value, (int, float, str, bool)) or value is None:
        rows.append((prefix, value))
    return rows


def command_aggregate(args):
    root = Path(args.dataset_root).resolve()
    aggregate = root / "aggregate"
    aggregate.mkdir(exist_ok=True)
    with (aggregate / "systems.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["system_id", "associating", "f", "N", "rho_p", "Ee", "Ea"])
        for system in campaign_systems():
            writer.writerow([system[key] for key in ("system_id", "associating", "f", "N",
                                                      "rho_p", "Ee", "Ea")])
    rows = []
    for system in campaign_systems():
        analysis_root = root / "systems" / system["system_id"] / "analysis"
        system_summary = {"schema_version": 1, "system_id": system["system_id"],
                          "production": {}, "analyses": []}
        for replica in (1, 2, 3):
            path = run_path(root, system, replica)
            system_summary["production"][f"r{replica:03d}"] = (
                load_json(path).get("status") if path.is_file() else "not_prepared")
        for summary in analysis_root.glob("*/*/*.json"):
            if summary.name == "analysis.json":
                continue
            try:
                values = load_json(summary)
            except json.JSONDecodeError:
                continue
            system_summary["analyses"].append(str(summary))
            for observable, value in flatten_scalars(values):
                rows.append([system["system_id"], summary.parent.parent.name,
                             summary.parent.name, observable, value, str(summary)])
        write_json(root / "systems" / system["system_id"] / "summary.json",
                   system_summary)
    with (aggregate / "observables.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["system_id", "analysis", "version", "observable", "value", "source"])
        writer.writerows(rows)
    print(aggregate / "systems.csv")
    print(aggregate / "observables.csv")


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
    child = subparsers.add_parser("equilibrate")
    child.add_argument("--dataset-root", required=True)
    child.add_argument("--stage", choices=("e1", "e2"), required=True)
    child.add_argument("--system", action="append")
    child.add_argument("--group", choices=sorted(load_json(PROTOCOL_PATH)["groups"]))
    child.add_argument("--replicas", default="1,2,3")
    child.add_argument("--steps", type=int, help="E2 duration; must be justified by stationarity")
    child.add_argument("--equilibration-ea", type=float, default=4.0)
    child.add_argument("--execute", action="store_true")
    child.set_defaults(function=command_equilibrate)
    child = subparsers.add_parser("validate-equilibration")
    child.add_argument("--dataset-root", required=True)
    child.add_argument("--stage", choices=("e1", "e2"), required=True)
    child.add_argument("--system", action="append")
    child.add_argument("--group", choices=sorted(load_json(PROTOCOL_PATH)["groups"]))
    child.add_argument("--replicas", default="1,2,3")
    child.set_defaults(function=command_validate_equilibration)
    child = subparsers.add_parser("accept-equilibration")
    child.add_argument("--dataset-root", required=True)
    child.add_argument("--stage", choices=("e1", "e2"), required=True)
    child.add_argument("--bank-id", required=True)
    child.add_argument("--evidence", required=True)
    child.set_defaults(function=command_accept_equilibration)
    for name, function in (("launch-production", command_launch_production),
                           ("status", command_status),
                           ("verify-production", command_verify_production)):
        child = subparsers.add_parser(name)
        child.add_argument("--dataset-root", required=True)
        child.add_argument("--system", action="append")
        child.add_argument("--group", choices=sorted(load_json(PROTOCOL_PATH)["groups"]))
        child.add_argument("--replicas", default="1,2,3")
        if name == "launch-production":
            child.add_argument("--execute", action="store_true")
        if name == "verify-production":
            child.add_argument("--skip-hashes", action="store_true")
        child.set_defaults(function=function)
    child = subparsers.add_parser("analyze")
    child.add_argument("--dataset-root", required=True)
    child.add_argument("--system", action="append", required=True)
    child.add_argument("--group", choices=sorted(load_json(PROTOCOL_PATH)["groups"]))
    child.add_argument("--analysis", choices=sorted(ANALYZERS), required=True)
    child.add_argument("--version", required=True)
    child.add_argument("--execute", action="store_true")
    child.set_defaults(function=command_analyze)
    child = subparsers.add_parser("aggregate")
    child.add_argument("--dataset-root", required=True)
    child.set_defaults(function=command_aggregate)
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
