#!/usr/bin/env python3
"""Prepare/validate C1 corrected-chemistry recovery; launch is separately gated."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import time

import kg_assoc_c1_e2 as pilot
import validate_periodic_e2_smoke as segment

campaign = pilot.campaign
analysis = pilot.analysis
require = analysis.require
STEPS = 2000000
COUNTS = (2484, 2538, 2438)
COMPLETION_HASHES = (
    "80d281ffd89e28855b4b795d98189266b6427c383f4eb4020a99cd6ddf645784",
    "bab4b16a3e7e6bec6c5328d00232dc40c84fd8b5a297b201271b9a7f40626ecd",
    "e55468f2bbe1f9609d4db345748cdf3401b3a77cd7df8dcc40019c0b7fb2dd74",
)
PARENTS = (
    ("3f2f2c3da1be18a490fd26c972006d68c519d7e85709835a4c56fd18dbe04118",
     "f7aa72bad0d76d2ab72c047b9abcc1d14528c3e3336f6efbeed82f9b6f1b5c3a"),
    ("04f0cc53ae3056df338feb7005d0e8757e9874d13862722dee4ea72bccdcc8ea",
     "9ee3cf208cb17ac4a1993de23d2c187b0d7484a085b24a33623f4c64ee903ab9"),
    ("d664f2313ff39ccdc8f77d6bce1b4cfef6c270aa0e1bd9f5a12ba596d57e06e4",
     "c8a2e1b353438fa03e7c7006bb5e855be3c6e61ea4dc58b628db9eae6daac3c6"),
)


def authenticate_parent(root, replica, oracle=True):
    parent = root / "banks/e2" / analysis.BANK_ID / f"r{replica:03d}" / "state"
    hashes = {}
    for suffix, expected in zip((".restart.lammpsdat", ".assoc_restart"), PARENTS[replica - 1]):
        path = Path(str(parent) + suffix)
        require(campaign.sha256(path) == expected, "not the original 6M parent: " + str(path))
    completion = parent.parent / "complete.json"
    require(campaign.sha256(completion) == COMPLETION_HASHES[replica - 1],
            "original E2 completion record changed")
    complete = campaign.load_json(completion)
    hashes[str(completion)] = campaign.sha256(completion)
    command_path = parent.parent / "command.json"
    original_command = campaign.load_json(command_path)
    require(original_command["status"] == "finished" and original_command["exit_code"] == 0,
            "original E2 is not complete")
    e1 = root / "banks/e1/F04_N010_RP080" / f"r{replica:03d}" / "state.e1.lammpsdat"
    require(campaign.sha256(e1) == original_command["parent_e1_sha256"], "original E1 parent changed")
    for path in (e1, command_path):
        hashes[str(path)] = campaign.sha256(path)
    for suffix in analysis.OUTPUTS:
        path = Path(str(parent) + suffix)
        hashes[str(path)] = campaign.sha256(path)
        require(hashes[str(path)] == complete["files"][suffix], "original E2 output changed")
    values, pairs = analysis.restart.read_metadata(str(parent) + ".assoc_restart")
    require(int(values["completed_steps"]) == 6000000 and
            int(values["seed"]) == 22000 + replica and
            int(values["creations"]) - int(values["breaks"]) == len(pairs), "invalid parent counters")
    for key, value in analysis.restart.CANONICAL.items():
        require(float(values[key]) == value, "incorrect parent physics: " + key)
    analysis.e1.check_snapshot(Path(str(parent) + ".restart.lammpsdat"), analysis.model())
    system = analysis.topology.read_system(str(parent) + ".restart.lammpsdat", 2)
    analysis.dynamics.read_restart(str(parent) + ".assoc_restart", system,
                                  dict(start_step=6000000, seed=22000 + replica, dt=.01))
    if oracle:
        process = subprocess.run([str(campaign.HERE.parent / "kg_assoc_candidates_test"),
                                  str(parent) + ".restart.lammpsdat", str(COUNTS[replica - 1])],
                                 capture_output=True, text=True, check=True)
        require("ACTIVE SNAPSHOT PASS" in process.stdout, "parent oracle failed")
    return parent, hashes


def smoke_evidence(path, fresh=False, git_sha=None):
    manifest = campaign.load_json(path / "manifest.json")
    require(manifest["status"] == "short_numerical_validation_passed_not_equilibrated",
            "GPU smoke is not validated")
    if fresh:
        require(manifest["git_sha"] == git_sha and manifest["rng_policy"] == "fresh_MD_reseed",
                "fresh MD smoke must use prepared code and RNG policy")
    hashes = {str(path / "manifest.json"): campaign.sha256(path / "manifest.json")}
    for replica in (1, 2, 3):
        directory = path / f"r{replica:03d}"
        result = campaign.load_json(directory / "validation.json")
        require(result["oracle_sweeps"] == 100, "missing smoke oracle sweeps")
        for name, expected in result["output_sha256"].items():
            require(campaign.sha256(directory / name) == expected, "GPU smoke output changed")
            hashes[str(directory / name)] = expected
        parent = path.parents[2] / "banks/e2" / analysis.BANK_ID / f"r{replica:03d}" / "state"
        segment.validate(directory / "state", parent, replica,
                         md_seed=32000 + replica if fresh else None)
        hashes[str(directory / "validation.json")] = campaign.sha256(directory / "validation.json")
    return hashes


def commands(root, output):
    executable = campaign.HERE.parent / "kg_assoc_stars"
    return [[str(executable), "--restart-prefix", str(root / "banks/e2" / analysis.BANK_ID /
             f"r{replica:03d}" / "state"), "--steps", str(STEPS), "--diagnostic-every", "1000",
             "--seed", str(22000 + replica), "--md-seed", str(32000 + replica),
             "--output", str(output / f"r{replica:03d}" / "state")]
            for replica in (1, 2, 3)]


def authenticate_plan(root, output):
    plan = campaign.load_json(output / "plan.json")
    require(plan["commands"] == commands(root, output), "prepared commands changed")
    require(campaign.git_sha() == plan["git_sha"], "code changed since preparation")
    require(not subprocess.check_output(["git", "status", "--porcelain"],
                                       cwd=campaign.REPOSITORY_ROOT, text=True).strip(),
            "uncommitted source changes since preparation")
    for path, expected in plan["sha256"].items():
        require(campaign.sha256(Path(path)) == expected, "authenticated file changed: " + path)
    for replica in (1, 2, 3):
        authenticate_parent(root, replica)
    return plan


def prepare(root, output, evidence):
    require(not output.exists(), "recovery attempt already exists")
    require(not subprocess.check_output(["git", "status", "--porcelain"],
                                       cwd=campaign.REPOSITORY_ROOT, text=True).strip(),
            "commit scientific source changes before preparation")
    executable = campaign.HERE.parent / "kg_assoc_stars"
    oracle = campaign.HERE.parent / "kg_assoc_candidates_test"
    smoke = campaign.HERE.parent / "kg_assoc_stars_candidate_smoke"
    subprocess.run(["make", "-q", "kg_assoc_stars", "kg_assoc_candidates_test", "kg_assoc_stars_candidate_smoke"],
                   cwd=campaign.HERE.parent, check=True)
    hashes = {str(path): campaign.sha256(path) for path in (executable, oracle, smoke)}
    hashes.update(smoke_evidence(evidence))
    for replica in (1, 2, 3):
        _, parent_hashes = authenticate_parent(root, replica)
        hashes.update(parent_hashes)
    result = subprocess.run([str(executable), "--self-test"], capture_output=True, text=True, check=True)
    require("SELF_TEST PASS" in result.stdout, "executable self-test failed")
    help_text = subprocess.check_output([str(executable), "--help"], text=True)
    require("--md-seed" in help_text, "executable lacks independent MD reseeding")
    output.mkdir(parents=True, exist_ok=False)
    for replica in (1, 2, 3):
        (output / f"r{replica:03d}").mkdir()
    campaign.write_json(output / "plan.json", dict(
        git_sha=campaign.git_sha(), commands=commands(root, output), sha256=hashes,
        rng_policy="fresh_MD_reseed; inherited_stateless_chemistry_absolute_step",
        independent_units="three_original_E1_E2_histories_not_new_replicas",
        absolute_start_step=6000000, absolute_end_step=8000000,
        build=dict(makefile_sha256=campaign.sha256(campaign.HERE.parent / "Makefile"),
                   command=subprocess.check_output(["make", "-n", "-B", "kg_assoc_stars"],
                                                   cwd=campaign.HERE.parent, text=True)),
        prepared_at=datetime.now(timezone.utc).isoformat(), scientific_acceptance="review_required"))
    campaign.write_json(output / "approval.example.json", dict(
        approved=False, purpose="C1_corrected_2M_recovery",
        plan_sha256=campaign.sha256(output / "plan.json"), reviewer="", approved_at=""))


def verify(root, output):
    authenticate_plan(root, output)
    for replica in (1, 2, 3):
        directory = output / f"r{replica:03d}"
        status = campaign.load_json(directory / "status.json")
        require(status["status"] == "validated", "recovery is incomplete")
        for name, expected in status["output_sha256"].items():
            require(campaign.sha256(directory / name) == expected, "recovery output changed")
        parent, _ = authenticate_parent(root, replica)
        segment.validate(directory / "state", parent, replica, steps=STEPS,
                         oracle=False, md_seed=32000 + replica)


def launch(root, output, execute, approval, fresh_smoke):
    plan = authenticate_plan(root, output)
    for replica in (1, 2, 3):
        require(not any((output / f"r{replica:03d}").iterdir()),
                "attempt already used; no overwrite or automatic continuation")
    if not execute:
        print(json.dumps(dict(status="dry_run_no_MD", commands=plan["commands"]), indent=2))
        return
    require(approval is not None and fresh_smoke is not None, "execution requires approval and fresh MD smoke")
    approved = campaign.load_json(approval)
    require(approved["approved"] is True and approved["purpose"] == "C1_corrected_2M_recovery" and
            approved["plan_sha256"] == campaign.sha256(output / "plan.json") and
            bool(approved["reviewer"]) and bool(approved["approved_at"]), "invalid execution approval")
    fresh_hashes = smoke_evidence(fresh_smoke, fresh=True, git_sha=plan["git_sha"])
    lock = output / ".launch.lock"
    with lock.open("x") as stream:
        json.dump(dict(pid=os.getpid(), host=socket.gethostname()), stream)
    try:
        for replica, command in enumerate(plan["commands"], 1):
            authenticate_plan(root, output)
            directory = output / f"r{replica:03d}"
            require(not any(directory.iterdir()), "replica artifacts appeared during preflight")
            status = dict(status="running", command=command, host=socket.gethostname(),
                          approval_sha256=campaign.sha256(approval), fresh_smoke_sha256=fresh_hashes,
                          started_at=datetime.now(timezone.utc).isoformat())
            campaign.write_json(directory / "status.json", status)
            start = time.monotonic()
            try:
                with (directory / "stdout.log").open("x") as stdout, \
                        (directory / "stderr.log").open("x") as stderr:
                    process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
                    try:
                        require(process.wait() == 0, "MD executable failed")
                    except BaseException:
                        process.terminate()
                        process.wait()
                        raise
                require("STAR_ASSOCIATION_SMOKE PASS" in (directory / "stdout.log").read_text(),
                        "missing executable completion marker")
                parent, _ = authenticate_parent(root, replica)
                result = segment.validate(directory / "state", parent, replica,
                                          steps=STEPS, oracle=False, md_seed=32000 + replica)
                status.update(status="validated", numerical_validation=result,
                              wall_seconds=time.monotonic() - start,
                              completed_absolute_step=8000000, scientific_acceptance="review_required",
                              output_sha256={path.name: campaign.sha256(path) for path in directory.iterdir()
                                             if path.is_file() and path.name != "status.json"})
            except BaseException as error:
                status.update(status="incomplete", error=str(error))
                raise
            finally:
                campaign.write_json(directory / "status.json", status)
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "prepare", "launch", "verify", "status"))
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--output", required=True, help="new attempt under banks/e2_extensions")
    parser.add_argument("--smoke-evidence", type=Path)
    parser.add_argument("--fresh-md-smoke", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root, output = Path(args.dataset_root).resolve(), Path(args.output).resolve()
    require(output.parent == root / "banks/e2_extensions", "output must be a direct e2_extensions child")
    if args.action == "plan":
        for replica in (1, 2, 3):
            authenticate_parent(root, replica)
        print(json.dumps(dict(commands=commands(root, output), executed=False), indent=2))
    elif args.action == "prepare":
        require(args.smoke_evidence is not None, "prepare requires retained GPU smoke evidence")
        prepare(root, output, args.smoke_evidence.resolve())
    elif args.action == "launch":
        launch(root, output, args.execute, args.approval, args.fresh_md_smoke)
    elif args.action == "verify":
        verify(root, output)
    else:
        for replica in (1, 2, 3):
            path = output / f"r{replica:03d}" / "status.json"
            status = campaign.load_json(path) if path.exists() else dict(status="prepared_or_unprepared")
            label = status["status"]
            if label == "running":
                label = "running_or_interrupted_NOT_COMPLETE"
            print(f"r{replica:03d}", label, "scientific acceptance: review_required")


if __name__ == "__main__":
    main()
