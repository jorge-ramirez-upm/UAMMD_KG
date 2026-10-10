#!/usr/bin/env python3
"""Prepare the fresh C1 E2 pilot; launching requires a separate --execute action."""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

import kg_assoc_campaign as campaign
import kg_assoc_e1 as e1

sys.path.insert(0, str(campaign.ANALYSIS_DIR))
import analyze_c1_e2_pilot as analysis


def plans(root, replicas):
    system = analysis.model()
    result = []
    for replica in replicas:
        source = campaign.e1_bank_path(root, campaign.geometry_id(system), replica) / "state.e1.lammpsdat"
        snapshot = e1.check_snapshot(source, system)
        with source.open() as stream:
            seed_match = re.search(r"\bseed=(\d+)\b", stream.readline())
        if seed_match is None or int(seed_match[1]) != 12000 + replica:
            raise ValueError("incorrect E1 preparation seed: " + str(source))
        bank = root / "banks/e2" / analysis.BANK_ID / f"r{replica:03d}"
        command = campaign.e2_command(root, system, replica, bank, analysis.STEPS)
        executable = Path(command[0])
        result.append({"schema_version": 1, "stage": "e2", "pilot": "C1_fresh_6M",
                       "replica": replica, "status": "planned", "command": command,
                       "git_sha": campaign.git_sha(), "parent_e1": str(source),
                       "parent_e1_sha256": snapshot["sha256"],
                       "parent_e1_temperature": snapshot["final_temperature"],
                       "e1_seed": 12000 + replica, "md_seed": 22000 + replica,
                       "chemistry_seed": 22000 + replica, "initial_temporary_bonds": 0,
                       "e2_start_step": 0, "requested_e2_steps": analysis.STEPS,
                       "executable_sha256": campaign.sha256(executable) if executable.exists() else None,
                       "geometry": campaign.expected_geometry(system), "bank": str(bank)})
    if len({item["parent_e1_sha256"] for item in result}) != len(result):
        raise ValueError("E2 replicas must have distinct E1 states")
    return result


def prepare(root, entries, evidence):
    if not evidence or not evidence.is_file():
        raise ValueError("prepare requires --e1-review pointing to retained scientific acceptance evidence")
    for entry in entries:
        bank = Path(entry["bank"])
        if bank.exists() and any(bank.iterdir()):
            raise ValueError("refusing to overwrite existing E2 bank: " + str(bank))
        if entry["executable_sha256"] is None:
            raise ValueError("build kg_assoc_stars before preparation")
    for entry in entries:
        entry.update(e1_review=str(evidence), e1_review_sha256=campaign.sha256(evidence),
                     prepared_at=datetime.now(timezone.utc).isoformat())
        campaign.write_json(Path(entry["bank"]) / "command.json", entry)
    print("Prepared", len(entries), "C1 E2 replicas; no MD launched")


def launch(root, entries, execute):
    records = []
    for entry in entries:
        bank = Path(entry["bank"])
        record = campaign.load_json(bank / "command.json")
        if record["status"] != "planned" or {path.name for path in bank.iterdir()} != {"command.json"}:
            raise ValueError("E2 bank already used or incomplete; no automatic retry: " + str(bank))
        for key in ("command", "bank", "parent_e1", "parent_e1_sha256", "executable_sha256",
                    "md_seed", "chemistry_seed", "requested_e2_steps", "pilot"):
            if record[key] != entry[key]:
                raise ValueError("E2 preparation changed; investigate before launching: " + key)
        if campaign.sha256(Path(record["e1_review"])) != record["e1_review_sha256"]:
            raise ValueError("E1 scientific review evidence changed")
        records.append(record)
        print(" ".join(record["command"]))
    if not execute:
        print("DRY RUN: E2 pilot not executed")
        return
    lock = root / "banks/e2" / analysis.BANK_ID / ".launch.lock"
    with lock.open("x") as stream:
        json.dump({"pid": os.getpid(), "host": socket.gethostname()}, stream)
    try:
        preflight = subprocess.run([records[0]["command"][0], "--self-test"],
                                   capture_output=True, text=True)
        if preflight.returncode or "SELF_TEST PASS" not in preflight.stdout:
            raise ValueError("E2 executable self-test failed")
        for record in records:
            bank = Path(record["bank"])
            if {path.name for path in bank.iterdir()} != {"command.json"}:
                raise ValueError("E2 output appeared during preflight; refusing overwrite")
            record.update(status="running", launch_git_sha=campaign.git_sha(),
                          started_at=datetime.now(timezone.utc).isoformat())
            campaign.write_json(bank / "command.json", record)
            try:
                with (bank / "stdout.log").open("x") as stdout, (bank / "stderr.log").open("x") as stderr:
                    process = subprocess.Popen(record["command"], stdout=stdout, stderr=stderr)
                    record["pid"] = process.pid
                    campaign.write_json(bank / "command.json", record)
                    try:
                        code = process.wait()
                    except KeyboardInterrupt:
                        process.terminate()
                        process.wait()
                        raise
                if code != 0 or "STAR_ASSOCIATION_SMOKE PASS" not in (bank / "stdout.log").read_text():
                    raise ValueError("E2 executable failed or lacks completion marker")
                metadata, _, _, validation = analysis.verify_outputs(
                    bank / "state", seed=record["chemistry_seed"])
                if metadata["input_file"] != record["parent_e1"]:
                    raise ValueError("E2 loaded the wrong E1 state")
                first_numeric = (bank / "state.numerics.tsv").read_text().splitlines()[1].split()
                if not math.isclose(float(first_numeric[3]), record["parent_e1_temperature"], rel_tol=1e-5):
                    raise ValueError("E2 initial velocities disagree with E1")
                log = (bank / "stderr.log").read_text()
                for field, value in (("Temperature", "1.000000"), ("Time step", "0.010000"),
                                     ("Friction", "0.500000")):
                    if f"[VerletNVT::GronbechJensen] {field}: {value}" not in log:
                        raise ValueError("E2 runtime NVT parameter not confirmed: " + field)
                campaign.write_json(bank / "complete.json", validation)
                record.update(status="finished", exit_code=0, completed_e2_steps=analysis.STEPS,
                              scientific_acceptance="review_required",
                              finished_at=datetime.now(timezone.utc).isoformat())
                campaign.write_json(bank / "command.json", record)
            except (OSError, ValueError, KeyError, KeyboardInterrupt) as error:
                record.update(status="incomplete", error=str(error))
                campaign.write_json(bank / "command.json", record)
                raise ValueError("C1 E2 stopped; incomplete artifacts retained: " + str(bank)) from error
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "prepare", "launch", "status", "verify"))
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--replicas", default="1,2,3")
    parser.add_argument("--e1-review")
    parser.add_argument("--output", help="new versioned plan directory under aggregate/e2")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = Path(args.dataset_root).resolve()
    try:
        if not (root / "manifest.json").is_file():
            raise ValueError("missing dataset manifest")
        replicas = campaign.replicas(args.replicas)
        if not replicas or len(set(replicas)) != len(replicas):
            raise ValueError("replicas must be unique")
        if args.action in ("status", "verify"):
            for replica in replicas:
                bank = root / "banks/e2" / analysis.BANK_ID / f"r{replica:03d}"
                record = campaign.load_json(bank / "command.json") if (bank / "command.json").exists() else {}
                if args.action == "verify":
                    if record.get("status") != "finished" or not (bank / "complete.json").exists():
                        raise ValueError("E2 replica is incomplete")
                    _, _, _, validation = analysis.verify_outputs(bank / "state", seed=22000 + replica)
                    if campaign.load_json(bank / "complete.json")["files"] != validation["files"]:
                        raise ValueError("E2 output integrity changed")
                status = record.get("status", "unprepared")
                if not record and bank.exists() and any(bank.iterdir()):
                    status = "unrecorded_artifacts_investigate"
                print(f"r{replica:03d}", status,
                      record.get("scientific_acceptance", "not_reviewed"))
            return 0
        entries = plans(root, replicas)
        if args.action == "plan":
            if args.output:
                output = Path(args.output).resolve()
                output.relative_to(root / "aggregate/e2")
                output.mkdir(parents=True, exist_ok=False)
                campaign.write_json(output / "launch_plan.json", {"replicas": entries, "executed": False})
            for entry in entries:
                print(" ".join(entry["command"]))
        elif args.action == "prepare":
            prepare(root, entries, Path(args.e1_review).resolve() if args.e1_review else None)
        else:
            launch(root, entries, args.execute)
    except (OSError, ValueError, KeyError) as error:
        print("C1 E2 ERROR:", error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
