#!/usr/bin/env python3
"""Explicit short GPU check only: 10,000 E2 steps per selected C1 E1 parent."""

import argparse
import math
from pathlib import Path
import subprocess
import time

import kg_assoc_c1_e2 as pilot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--output", required=True, help="new directory under aggregate/e2")
    parser.add_argument("--replicas", default="1,2,3")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = Path(args.dataset_root).resolve()
    output = Path(args.output).resolve()
    output.relative_to(root / "aggregate/e2")
    entries = pilot.plans(root, pilot.campaign.replicas(args.replicas))
    if not args.execute:
        print("DRY RUN: short smoke requires --execute; no MD launched")
        return
    output.mkdir(parents=True, exist_ok=False)
    for entry in entries:
        directory = output / f"r{entry['replica']:03d}"
        directory.mkdir()
        command = list(entry["command"])
        command[command.index("--steps") + 1] = "10000"
        command[command.index("--output") + 1] = str(directory / "state")
        start = time.monotonic()
        with (directory / "stdout.log").open("x") as stdout, (directory / "stderr.log").open("x") as stderr:
            subprocess.run(command, stdout=stdout, stderr=stderr, check=True)
        elapsed = time.monotonic() - start
        _, rows, _, validation = pilot.analysis.verify_outputs(
            directory / "state", steps=10000, seed=entry["chemistry_seed"], network=True)
        if not math.isclose(rows[0]["temperature"], entry["parent_e1_temperature"], rel_tol=1e-5):
            raise ValueError("loaded E1 velocities disagree")
        if pilot.campaign.sha256(Path(entry["parent_e1"])) != entry["parent_e1_sha256"]:
            raise ValueError("E1 source integrity changed")
        log = (directory / "stderr.log").read_text()
        for field, value in (("Temperature", "1.000000"), ("Time step", "0.010000"),
                             ("Friction", "0.500000")):
            if f"[VerletNVT::GronbechJensen] {field}: {value}" not in log:
                raise ValueError("effective KG parameter not confirmed: " + field)
        pilot.campaign.write_json(directory / "validation.json",
                                  dict(parent_plan=entry, command=command, validation=validation,
                                       wall_seconds=elapsed, requested_steps=10000,
                                       estimated_6M_seconds=elapsed * 600,
                                       bytes=sum(path.stat().st_size for path in directory.iterdir()),
                                       scientific_acceptance="not_a_stationarity_test"))
        print(f"r{entry['replica']:03d}: short GPU checks passed, {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
