#!/usr/bin/env python3
"""Inventory, safely retry, and review E1 banks; execution is opt-in."""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone

import kg_assoc_campaign as campaign

sys.path.insert(0, str(campaign.HERE.parent))
import analyze_e1_stationarity as stationarity


def geometries():
    return {campaign.geometry_id(item): item for item in campaign.campaign_systems()}


def inventory(root):
    entries = []
    for geometry, system in sorted(geometries().items()):
        for replica in (1, 2, 3):
            bank = campaign.e1_bank_path(root, geometry, replica)
            attempts = root / "banks" / "e1_retries" / geometry / f"r{replica:03d}"
            retained = sorted(attempts.glob("attempt[0-9][0-9][0-9]"))
            if retained:
                bank = retained[-1]
            record = campaign.load_json(bank / "command.json") if (
                bank / "command.json").exists() else {}
            if record.get("validation_error"):
                status = "failed"
            elif record.get("status") == "running":
                status = "running"
            elif (bank / "state.e1.lammpsdat").exists():
                status = "completed"
            elif record.get("status") == "incomplete" or any(
                    (bank / name).exists() for name in ("diagnostics.tsv", "stdout.log", "stderr.log")):
                status = "failed"
            else:
                status = "pending"
            entries.append({"geometry": geometry, "replica": replica, "seed": 12000 + replica,
                            "status": status, "bank": bank, "system": system})
    return entries


def check_snapshot(path, system):
    geometry = campaign.validate_geometry(path, campaign.expected_geometry(system))
    data = campaign.parse_lammps_data(path)
    if set(data["velocities"]) != set(data["atoms"]):
        raise ValueError("final state is missing particle velocities")
    for field in ("positions", "velocities"):
        if any(len(values) != 3 or not all(math.isfinite(value) for value in values)
               for values in data[field].values()):
            raise ValueError(f"final state has nonfinite or malformed {field}")
    lengths = [data["bounds"][axis][1] - data["bounds"][axis][0] for axis in "xyz"]
    distances = []
    for first, second in data["bonds"]:
        delta = [data["positions"][second][axis] - data["positions"][first][axis]
                 for axis in range(3)]
        distance = math.sqrt(sum((value - length * round(value / length)) ** 2
                                 for value, length in zip(delta, lengths)))
        if not 0.0 < distance < 1.5:
            raise ValueError(f"invalid final permanent FENE bond {first}--{second}: {distance}")
        distances.append(distance)
    geometry.update(minimum_bond=min(distances), maximum_bond=max(distances),
                    final_temperature=sum(sum(value * value for value in velocity)
                                          for velocity in data["velocities"].values()) /
                    (3 * len(data["atoms"])))
    return geometry


def check_effective_dpd(path):
    records = []
    for line in path.read_text().splitlines():
        if "[E1 DPD effective]" not in line:
            continue
        values = dict(re.findall(r"(\w+)=([^\s]+)", line))
        if (float(values.get("gamma", "nan")) != 4.5 or
                not math.isclose(float(values.get("dt", "nan")), 0.002, rel_tol=1e-6) or
                not math.isclose(float(values.get("noise_squared_dt", "nan")), 9.0, rel_tol=1e-5)):
            raise ValueError("incorrect effective E1 DPD parameters")
        records.append(values)
    if len(records) != 16:
        raise ValueError("missing effective parameters for the 16 DPD segments")
    return records[-1]


def validate(entry, require_corrected=False):
    bank = entry["bank"]
    snapshot = check_snapshot(bank / "state.e1.lammpsdat", entry["system"])
    with (bank / "diagnostics.tsv").open() as source:
        rows = stationarity.read_diagnostics(source)
    selected, interval = stationarity.select_uniform_stage4_suffix(rows)
    stride = selected[-1]["step"] - selected[-2]["step"]
    if not math.isclose(interval / stride, 0.01, rel_tol=1e-6):
        raise ValueError("final diagnostic suffix is not at the KG timestep 0.01")
    if any(row["max_permanent_bond"] >= 1.5 or row["min_permanent_bond"] <= 0
           for row in selected):
        raise ValueError("invalid sampled Stage-4 permanent bond")
    summary = stationarity.summarize(rows, 5)
    if any(row["mean_rg2"] <= 0 or row["mean_center_terminal_r2"] <= 0
           for row in selected):
        raise ValueError("invalid structural observable")
    effective = check_effective_dpd(bank / "stderr.log") if require_corrected else None
    if require_corrected:
        with (bank / "state.e1.lammpsdat").open() as source:
            header = source.readline()
        steps = 71400 + 4500 + {10: 2000000, 20: 2000000, 40: 8000000}[entry["system"]["N"]]
        if (not re.search(rf"\bstep\s+{steps}\b", header) or
                not re.search(rf"\bseed={entry['seed']}\b", header)):
            raise ValueError("final E1 state has the wrong step count or seed")
    return {"numerical_status": "valid", "scientific_status": "review_required",
            "snapshot": snapshot, "stationarity": summary, "effective_dpd": effective,
            "diagnostics_sha256": campaign.sha256(bank / "diagnostics.tsv")}


def next_attempt(root, entry):
    original = root / "banks" / "e1" / entry["geometry"] / f"r{entry['replica']:03d}"
    if entry["status"] == "pending" and (not original.exists() or not any(original.iterdir())):
        return original
    parent = root / "banks" / "e1_retries" / entry["geometry"] / f"r{entry['replica']:03d}"
    for attempt in range(1, 1000):
        candidate = parent / f"attempt{attempt:03d}"
        if not candidate.exists():
            return candidate
    raise ValueError("E1 attempt limit reached")


def publish(root, entry, bank):
    path = root / "banks" / "e1" / "active_states.json"
    pointers = campaign.load_json(path) if path.exists() else {}
    pointers[f"{entry['geometry']}/r{entry['replica']:03d}"] = str(bank.relative_to(root))
    campaign.write_json(path, pointers)


def run(args, root):
    entries = inventory(root)
    keys = {f"{row['geometry']}/r{row['replica']:03d}" for row in entries}
    retries = set(args.retry)
    if retries - keys:
        raise ValueError("unknown retry entries: " + ", ".join(sorted(retries - keys)))
    selected = []
    for entry in entries:
        key = f"{entry['geometry']}/r{entry['replica']:03d}"
        if entry["status"] == "completed":
            print("SKIP completed", key)
            continue
        if entry["status"] == "running":
            raise ValueError(f"recorded E1 run is still running; investigate first: {key}")
        if entry["status"] == "failed" and key not in retries:
            raise ValueError(f"failed E1 entry requires explicit --retry {key}")
        bank = next_attempt(root, entry)
        command = campaign.e1_command(root, entry["system"], entry["replica"], bank)
        selected.append((entry, bank, command))
        print(" ".join(command))
    if not args.execute:
        print("DRY RUN: no simulation or dataset changes")
        return
    lock = root / "banks" / "e1" / ".run.lock"
    with lock.open("x") as output:
        json.dump({"pid": os.getpid(), "host": socket.gethostname()}, output)
    try:
        if selected:
            executable = Path(selected[0][2][0])
            preflight = subprocess.run([str(executable), "--self-test"],
                                       capture_output=True, text=True)
            if (preflight.returncode or "E1_SELF_TEST PASS" not in preflight.stdout or
                    "[E1 DPD effective] dt=0.002" not in preflight.stderr or
                    "gamma=4.5" not in preflight.stderr):
                raise ValueError("rebuild E1: corrected effective-parameter self-test is missing or failed")
            for entry, _, command in selected:
                campaign.validate_geometry(Path(command[command.index("--input") + 1]),
                                           campaign.expected_geometry(entry["system"]))
        for entry, bank, command in selected:
            # Recheck after acquiring the campaign lock; a completed state is never replaced.
            current = next(row for row in inventory(root) if
                           (row["geometry"], row["replica"]) ==
                           (entry["geometry"], entry["replica"]))
            if current["status"] == "completed":
                continue
            executable = Path(command[0])
            record = {"stage": "e1", "bank_id": entry["geometry"],
                      "runner": "kg_assoc_e1_v1",
                      "replica": entry["replica"], "seed": entry["seed"],
                      "command": command, "git_sha": campaign.git_sha(),
                      "executable_sha256": campaign.sha256(executable),
                      "input_sha256": campaign.sha256(Path(command[command.index("--input") + 1])),
                      "previous_attempt": str(entry["bank"]) if bank != entry["bank"] else None,
                      "status": "running",
                      "started_at": datetime.now(timezone.utc).isoformat()}
            bank.mkdir(parents=True, exist_ok=True)
            if any(bank.iterdir()):
                raise ValueError(f"refusing to overwrite E1 output: {bank}")
            campaign.write_json(bank / "command.json", record)
            with (bank / "stdout.log").open("x") as stdout, (bank / "stderr.log").open("x") as stderr:
                try:
                    process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
                except OSError as error:
                    record.update(status="incomplete", launch_error=str(error))
                    campaign.write_json(bank / "command.json", record)
                    raise
                record["pid"] = process.pid
                record["host"] = socket.gethostname()
                campaign.write_json(bank / "command.json", record)
                try:
                    code = process.wait()
                except KeyboardInterrupt:
                    process.terminate()
                    process.wait()
                    record.update(status="incomplete", exit_code=process.returncode)
                    campaign.write_json(bank / "command.json", record)
                    raise
            record.update(status="finished" if code == 0 else "incomplete", exit_code=code,
                          finished_at=datetime.now(timezone.utc).isoformat())
            campaign.write_json(bank / "command.json", record)
            if code != 0:
                raise ValueError(f"E1 failed; stopping immediately, outputs retained: {bank}")
            completed = dict(entry, bank=bank)
            try:
                result = validate(completed, require_corrected=True)
            except (OSError, ValueError) as error:
                record.update(status="incomplete", validation_error=str(error))
                campaign.write_json(bank / "command.json", record)
                raise ValueError(f"E1 validation failed; stopping immediately: {bank}: {error}")
            campaign.write_json(bank / "numerical_validation.json", result)
            publish(root, entry, bank)
            print("COMPLETED; scientific review required", entry["geometry"], entry["replica"])
        review_path = root / "aggregate" / "e1" / datetime.now(timezone.utc).strftime(
            "review_%Y%m%dT%H%M%S_%fZ")
        report(argparse.Namespace(action="review", report_dir=str(review_path)), root)
        print("E1 selection finished; review the 24-entry table before scientific acceptance.")
    finally:
        lock.unlink()


def report(args, root):
    entries = inventory(root)
    target = Path(args.report_dir).resolve() if args.report_dir else None
    if args.action == "review" and target is None:
        raise ValueError("review requires a new --report-dir")
    if target is not None:
        target.mkdir(parents=True, exist_ok=False)
    results = []
    for entry in entries:
        row = {name: entry[name] for name in ("geometry", "replica", "seed", "status")}
        row["bank"] = str(entry["bank"])
        row["input_available"] = (root / "inputs" / entry["geometry"] /
                                  "initial.lammpsdat").is_file()
        if args.action == "review" and entry["status"] == "completed":
            try:
                command_path = entry["bank"] / "command.json"
                corrected = (command_path.exists() and campaign.load_json(command_path).get(
                    "runner") == "kg_assoc_e1_v1")
                result = validate(entry, require_corrected=corrected)
                row["numerical_status"] = result["numerical_status"]
                row["scientific_status"] = result["scientific_status"]
                row["final_temperature"] = result["snapshot"]["final_temperature"]
                row["maximum_final_bond"] = result["snapshot"]["maximum_bond"]
                row["maximum_sampled_kg_bond"] = result["stationarity"]["max_permanent_bond"]["maximum"]
                row["minimum_sampled_kg_bond"] = result["stationarity"]["min_permanent_bond"]["minimum"]
                for name in stationarity.OBSERVABLES:
                    row[name + "_late_mean"] = result["stationarity"][name]["second_mean"]
                    row[name + "_half_difference"] = result["stationarity"][name]["relative_difference"]
                    row[name + "_late_slope"] = result["stationarity"][name]["second_half_slope"]
                campaign.write_json(target / f"{entry['geometry']}_r{entry['replica']:03d}.json", result)
            except (OSError, ValueError) as error:
                row["numerical_status"] = "review_issue"
                row["issue"] = str(error)
                print(f"REVIEW ISSUE {entry['bank']}: {error}", file=sys.stderr)
        results.append(row)
    fields = list(dict.fromkeys(name for row in results for name in row))
    output = (target / "e1_summary.csv").open("x", newline="") if target else sys.stdout
    try:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    finally:
        if target:
            output.close()
    if target:
        campaign.write_json(target / "inventory.json", {"git_sha": campaign.git_sha(), "entries": results})
        print(target / "e1_summary.csv")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "run", "review"))
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--retry", action="append", default=[], help="explicit GEOMETRY/rNNN retry")
    parser.add_argument("--execute", action="store_true", help="run E1 only; default is dry-run")
    parser.add_argument("--report-dir", help="new directory for inventory/validation reports")
    args = parser.parse_args()
    root = Path(args.dataset_root).resolve()
    try:
        if not (root / "manifest.json").is_file():
            raise ValueError(f"missing campaign manifest: {root / 'manifest.json'}")
        if args.action == "run":
            run(args, root)
        else:
            report(args, root)
    except (OSError, ValueError, KeyboardInterrupt) as error:
        print(f"E1 ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
