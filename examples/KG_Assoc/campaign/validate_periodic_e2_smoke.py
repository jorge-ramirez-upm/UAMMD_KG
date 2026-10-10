#!/usr/bin/env python3
"""Explicitly gated 10k-step oracle-checked GPU tests from preserved C1 E2 states.

Never launches recovery equilibration. Without --execute it only prints commands.
--verify validates an existing smoke directory without running MD.
"""

import argparse
import json
import math
from pathlib import Path
import subprocess
import time

import kg_assoc_c1_e2 as pilot

analysis = pilot.analysis
campaign = pilot.campaign
require = analysis.require
STEPS = 10000


def validate(prefix, parent, replica, steps=STEPS, oracle=True, md_seed=None):
    for suffix in analysis.OUTPUTS + ((".candidate_validation.tsv",) if oracle else ()):
        require(Path(str(prefix) + suffix).is_file(), "missing smoke output " + suffix)
    original, initial_pairs = analysis.restart.read_metadata(str(parent) + ".assoc_restart")
    start = int(original["completed_steps"])
    end = start + steps
    require(start == 6000000 and int(original["seed"]) == 22000 + replica,
            "unexpected C1 parent step/seed")
    metadata, rows = analysis.stationarity.read_state(str(prefix) + ".state")
    for key, value in analysis.restart.CANONICAL.items():
        require(float(original[key]) == value and float(metadata["T" if key == "temperature"
                                                               else key]) == value,
                "frozen parameter mismatch: " + key)
    require(int(metadata["seed"]) == int(original["seed"]) and
            int(metadata["start_step"]) == start and
            int(metadata["total_requested_steps"]) == end and
            int(metadata["chemistry_sweeps"]) == steps // 100,
            "wrong seed, timestamps or sweep count")
    require(Path(metadata["input_file"]).resolve() ==
            Path(str(parent) + ".restart.lammpsdat").resolve(), "wrong parent configuration")
    require([row["step"] for row in rows] == list(range(start, end + 1, 1000)) and
            all(math.isclose(row["time"], row["step"] * .01, abs_tol=1e-9) for row in rows),
            "incomplete, duplicate or mistimed state diagnostics")
    require(all(0 <= row["max_active_bond_distance"] < 1.5 for row in rows),
            "invalid sampled temporary bond geometry")
    final_snapshot = Path(str(prefix) + ".restart.lammpsdat")
    with final_snapshot.open() as source:
        require(source.readline().rstrip().endswith("step " + str(end)), "final snapshot timestamp mismatch")
    snapshot_check = analysis.e1.check_snapshot(final_snapshot, analysis.model())
    system = analysis.topology.read_system(str(final_snapshot), 2)
    event_metadata, events = analysis.dynamics.read_events(str(prefix) + ".events", system)
    for key in ("input_file", "seed", "start_step", "total_requested_steps", "dt", "Nevery"):
        same = (event_metadata[key] == metadata[key] if key == "input_file" else
                float(event_metadata[key]) == float(metadata[key]))
        require(same, "event/state metadata mismatch: " + key)
    require(all(start < step <= end and step % 100 == 0 for step, _, _ in events),
            "event outside absolute chemistry cadence")
    active, _ = analysis.replay(rows, events, system, network=True,
                               initial=dict(pairs=initial_pairs,
                                            creations=int(original["creations"]),
                                            breaks=int(original["breaks"])))
    final, final_pairs = analysis.restart.read_metadata(str(prefix) + ".assoc_restart")
    require(set(final_pairs) == active and len(final_pairs) == len(active) and
            int(final["completed_steps"]) == end, "final partner/step mismatch")
    for key in analysis.restart.CANONICAL:
        require(final[key] == original[key], "final physical parameter mismatch")
    require(final["seed"] == original["seed"], "final seed mismatch")
    require(int(final["creations"]) == rows[-1]["creations"] and
            int(final["breaks"]) == rows[-1]["breaks"], "final event counter mismatch")
    data = campaign.parse_lammps_data(final_snapshot)
    for first, second in active:
        require(analysis.restart.distance(data["positions"][first], data["positions"][second],
                                         data["bounds"]) < 1.5, "invalid temporary bond geometry")
    mirrored = []
    with Path(str(prefix) + ".final_associations").open() as source:
        for line in source:
            if line.strip() and not line.startswith("#"):
                first, second, first_star, second_star = map(int, line.split())
                require((first_star, second_star) ==
                        (system["atom_to_star"][first], system["atom_to_star"][second]),
                        "incorrect mirrored molecule IDs")
                mirrored.append((first, second))
    require(set(mirrored) == active and len(mirrored) == len(active), "final mirror mismatch")
    require(Path(str(prefix) + ".final_permanent.lammpsdat").read_bytes().split(b"\n", 1)[1] ==
            final_snapshot.read_bytes().split(b"\n", 1)[1], "archival particle state mismatch")
    numeric = analysis.numerics(Path(str(prefix) + ".numerics.tsv"), rows, 43563)
    parent_temperature = analysis.e1.check_snapshot(
        Path(str(parent) + ".restart.lammpsdat"), analysis.model())["final_temperature"]
    require(math.isclose(numeric[0][3], parent_temperature, rel_tol=1e-5) and
            math.isclose(numeric[-1][3], snapshot_check["final_temperature"], rel_tol=1e-5),
            "loaded/final numerical velocities disagree with configuration")
    checks = []
    if oracle:
        with Path(str(prefix) + ".candidate_validation.tsv").open() as source:
            require(source.readline().strip() ==
                    "# step candidates oracle_verified_active_candidates", "incorrect oracle header")
            checks = [list(map(int, line.split())) for line in source]
        require(all(len(row) == 3 and 0 <= row[2] <= min(row[1], 2000) for row in checks) and
                [row[0] for row in checks] == list(range(start + 100, end + 1, 100)),
                "incomplete per-sweep oracle verification")
        require(sum(row[1] for row in checks) == int(metadata["candidate_sticker_pairs"]),
                "candidate accounting mismatch")
    log = (prefix.parent / "stderr.log").read_text()
    if md_seed is not None:
        effective = {32001: 3928609932, 32002: 3937019018, 32003: 3945428108}
        require(int(metadata.get("md_seed", -1)) == md_seed and
                int(event_metadata.get("md_seed", -1)) == md_seed and
                f"[E2 MD stream] requested_seed={md_seed} effective_seed={effective[md_seed]} "
                "internal_start_step=0" in log,
                "fresh MD stream provenance missing or incorrect")
    for field, value in (("Temperature", "1.000000"), ("Time step", "0.010000"),
                         ("Friction", "0.500000")):
        require(f"[VerletNVT::GronbechJensen] {field}: {value}" in log,
                "effective KG parameter not confirmed: " + field)
    return dict(oracle_sweeps=len(checks), accepted_events=len(events),
                final_bonds=len(active), temperature_start=numeric[0][3],
                temperature_final=numeric[-1][3],
                max_sampled_permanent_bond=max(row[5] for row in numeric),
                scientific_acceptance="short_numerical_test_only")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--output", required=True, help="new directory below aggregate/e2")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--fresh-md", action="store_true", help="test fresh MD seeds 32001..32003")
    args = parser.parse_args()
    require(not (args.execute and args.verify), "choose execution OR verification")
    root = Path(args.dataset_root).resolve()
    output = Path(args.output).resolve()
    output.relative_to(root / "aggregate/e2")
    executable = campaign.HERE.parent / "kg_assoc_stars_candidate_smoke"
    parents = [root / "banks/e2" / analysis.BANK_ID / f"r{replica:03d}" / "state"
               for replica in (1, 2, 3)]
    commands = [[str(executable), "--restart-prefix", str(parent), "--steps", str(STEPS),
                 "--diagnostic-every", "1000", "--seed", str(22000 + replica),
                 "--output", str(output / f"r{replica:03d}" / "state")]
                for replica, parent in enumerate(parents, 1)]
    if args.fresh_md:
        for replica, command in enumerate(commands, 1):
            command.extend(["--md-seed", str(32000 + replica)])
    if not args.execute and not args.verify:
        print(json.dumps(dict(status="dry_run_no_MD", commands=commands), indent=2))
        return
    if args.verify:
        manifest = json.loads((output / "manifest.json").read_text())
    else:
        parent_hashes = {str(Path(str(parent) + suffix)): campaign.sha256(Path(str(parent) + suffix))
                         for parent in parents for suffix in (".restart.lammpsdat", ".assoc_restart")}
        manifest = dict(status="running", commands=commands, parent_sha256=parent_hashes,
                        git_sha=subprocess.check_output(
                            ["git", "rev-parse", "HEAD"], cwd=campaign.HERE, text=True).strip(),
                        executable_sha256=campaign.sha256(executable),
                        rng_policy=("fresh_MD_reseed" if args.fresh_md else
                                    "existing_reader_MD_reseed; chemistry_absolute_step_hash"),
                        md_steps_per_replica=STEPS)
        output.mkdir(parents=True, exist_ok=False)
        campaign.write_json(output / "manifest.json", manifest)
    try:
        for replica, (parent, command) in enumerate(zip(parents, commands), 1):
            directory = output / f"r{replica:03d}"
            if args.execute:
                directory.mkdir(exist_ok=False)
                start = time.monotonic()
                with (directory / "stdout.log").open("x") as stdout, \
                        (directory / "stderr.log").open("x") as stderr:
                    subprocess.run(command, stdout=stdout, stderr=stderr, check=True)
                elapsed = time.monotonic() - start
            else:
                elapsed = None
            fresh = manifest["rng_policy"] == "fresh_MD_reseed"
            result = validate(directory / "state", parent, replica,
                              md_seed=32000 + replica if fresh else None)
            result["wall_seconds"] = elapsed
            if args.execute:
                result["output_sha256"] = {path.name: campaign.sha256(path)
                                           for path in directory.iterdir() if path.is_file()}
                campaign.write_json(directory / "validation.json", result)
            print(f"r{replica:03d}: {result}")
        for path, expected in manifest["parent_sha256"].items():
            require(campaign.sha256(Path(path)) == expected, "parent integrity changed: " + path)
    except Exception as error:
        if args.execute:
            manifest.update(status="incomplete", error=str(error))
            campaign.write_json(output / "manifest.json", manifest)
        raise
    if args.execute:
        manifest["status"] = "short_numerical_validation_passed_not_equilibrated"
        campaign.write_json(output / "manifest.json", manifest)


if __name__ == "__main__":
    main()
