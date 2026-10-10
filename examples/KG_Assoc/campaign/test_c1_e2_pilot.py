#!/usr/bin/env python3
"""Offline bookkeeping fixtures, NOT physical configurations or MD validation."""

import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import kg_assoc_c1_e2 as pilot

analysis = pilot.analysis
campaign = pilot.campaign


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def snapshot():
    length = (41000 / 0.8) ** (1 / 3)
    lines = ["43563 atoms", "40000 bonds", "3 atom types", "1 bond types", ""]
    lines += [f"{-length / 2:.15g} {length / 2:.15g} {axis}lo {axis}hi" for axis in "xyz"]
    lines += ["", "Masses", "", "1 1", "2 1", "3 1", "", "Atoms # molecular", ""]
    bonds = []
    for star in range(1000):
        center = 41 * star + 1
        lines.append(f"{center} {star + 1} 1 {star * 0.01:.15g} 0 0")
        for arm, vector in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
            previous = center
            for bead in range(1, 11):
                atom = center + arm * 10 + bead
                x, y = star * 0.01 + 0.8 * bead * vector[0], 0.8 * bead * vector[1]
                lines.append(f"{atom} {star + 1} {2 if bead == 10 else 1} {x:.15g} {y:.15g} 0")
                bonds.append(f"{len(bonds) + 1} 1 {previous} {atom}")
                previous = atom
    lines += [f"{atom} {atom - 40000} 3 0 0 0" for atom in range(41001, 43564)]
    lines += ["", "Velocities", ""] + [f"{atom} 1 1 1" for atom in range(1, 43564)]
    lines += ["", "Bonds", ""] + bonds
    return "\n".join(lines) + "\n"


def fixture(root, replica, body):
    prefix = root / "banks/e2" / analysis.BANK_ID / f"r{replica:03d}" / "state"
    metadata = dict(analysis.restart.CANONICAL, T=1, diagnostic_every=1000, start_step=0,
                    total_requested_steps=12000, total_particles=43563, stickers=4000,
                    permanent_bonds=40000, chemistry_sweeps=120, seed=22000 + replica,
                    input_file="independent_e1_r" + str(replica), original_lammps_atom_ids="1_based")
    metadata.pop("temperature")
    header = "# " + " ".join(f"{key}={value}" for key, value in metadata.items()) + "\n"
    rows = []
    observations = 0
    for step in range(0, 12001, 1000):
        creations = 0 if step == 0 else 1 if step <= 2000 else 2
        breaks = int(step >= 2000)
        bonds = creations - breaks
        observations += bonds
        rows.append([step, step * 0.01, 4000 - 2 * bonds, bonds, creations, breaks, 0, bonds,
                     bonds / 2000, 1000 - bonds, 1 + bonds, (1 + bonds) / 1000,
                     bonds * 0.002, bonds * 0.002, 0, 0, observations,
                     0.01 if observations else 0, 0, 0, 0])
    write(Path(str(prefix) + ".state"), header + "# " + analysis.stationarity.COLUMNS + "\n" +
          "\n".join(" ".join(map(str, row)) for row in rows) + "\n")
    write(Path(str(prefix) + ".events"), header +
          "100 C 11 52 1 2\n1100 B 11 52 1 2\n2100 C 11 52 1 2\n")
    write(Path(str(prefix) + ".numerics.tsv"),
          "# step time kinetic_energy temperature min_permanent_bond max_permanent_bond\n" +
          "\n".join(f"{step} {step * .01} 65344.5 1 .8 .8" for step in range(0, 12001, 1000)) + "\n")
    for suffix in (".restart.lammpsdat", ".final_permanent.lammpsdat"):
        write(Path(str(prefix) + suffix), "Offline fixture step 12000\n" + body)
    sidecar = dict(analysis.restart.CANONICAL, seed=22000 + replica,
                   completed_steps=12000, creations=2, breaks=1)
    write(Path(str(prefix) + ".assoc_restart"), "KG_ASSOC_RESTART 1\n" +
          "\n".join(f"{key} {value}" for key, value in sidecar.items()) +
          "\nactive_bonds 1\n11 52\nend\n")
    write(Path(str(prefix) + ".final_associations"), "11 52 1 2\n")
    return prefix


class PilotTests(unittest.TestCase):
    def test_full_outputs_and_reproducible_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body = snapshot()
            for replica in (1, 2, 3):
                prefix = fixture(root, replica, body)
                _, rows, events, validation = analysis.verify_outputs(
                    prefix, steps=12000, seed=22000 + replica, network=True)
                self.assertEqual(len(rows), 13)
                self.assertEqual(len(events), 3)
                self.assertEqual(events[1]["neighbor_loss"], 1)
                campaign.write_json(prefix.parent / "complete.json", validation)
                campaign.write_json(prefix.parent / "command.json", {"status": "finished", "exit_code": 0})
            with mock.patch.object(analysis, "STEPS", 12000):
                analysis.analyze(root, root / "review1", [])
                analysis.analyze(root, root / "review2", [])
            for name in ("windowed_observables.csv", "windowed_events.csv", "summary.json",
                         "historical_comparison.csv"):
                self.assertEqual((root / "review1" / name).read_bytes(),
                                 (root / "review2" / name).read_bytes())
            self.assertTrue((root / "review1/time_series.png").is_file())
            self.assertTrue((root / "review1/block_means.png").is_file())
            with self.assertRaisesRegex(ValueError, "already exists"):
                analysis.analyze(root, root / "review1", [])
            # A lost accepted event must be a hard failure, not stationarity evidence.
            path = Path(str(prefix) + ".events")
            path.write_text(path.read_text().replace("1100 B 11 52 1 2\n", ""))
            with self.assertRaisesRegex(ValueError, "accounting mismatch"):
                analysis.verify_outputs(prefix, steps=12000, network=True)

    def test_parallel_bonds_and_triangle_turnover(self):
        system = {"stars": (10, 20, 30), "stickers": set(range(1, 9)),
                  "atom_to_star": {1: 10, 2: 20, 3: 10, 4: 20,
                                   5: 20, 6: 30, 7: 10, 8: 30}}
        events = [(100, "C", (1, 2)), (100, "C", (3, 4)), (100, "C", (5, 6)),
                  (100, "C", (7, 8)), (200, "B", (1, 2)), (300, "B", (3, 4))]
        rows = []
        for step, bonds, breaks, l1, l2, degree, moment in (
                (100, 4, 0, 1, 1, 2, 4), (200, 3, 1, 0, 1, 2, 4),
                (300, 2, 2, 0, 0, 4 / 3, 2)):
            rows.append(dict(step=step, time=step * .01, creations=4, breaks=breaks,
                             bonds=bonds, intra=0, inter=bonds, components=1, largest_size=3,
                             largest_cluster_fraction=1, mean_degree=degree,
                             second_degree_moment=moment, L1=l1, L2=l2))
        _, records = analysis.replay(rows, events, system)
        self.assertEqual([event["neighbor_gain"] for event in records], [1, 0, 1, 1, 0, 0])
        self.assertEqual([event["neighbor_loss"] for event in records], [0, 0, 0, 0, 0, 1])
        with self.assertRaisesRegex(ValueError, "valence-one"):
            analysis.replay(copy.deepcopy(rows), [events[0], events[0]], system)

    def test_window_boundaries(self):
        rows = [dict(step=step, time=step * .01, **{name: 1 for name in analysis.METRICS})
                for step in range(500000, 4000001, 500000)]
        events = [dict(step=2000000, type="C", neighbor_gain=1, neighbor_loss=0),
                  dict(step=2000100, type="B", neighbor_gain=0, neighbor_loss=1)]
        first = analysis.describe_window(rows, events, 0, 2000000)
        second = analysis.describe_window(rows, events, 2000000, 4000000)
        self.assertEqual(first["event_counts"]["creations"], 1)
        self.assertEqual(first["event_counts"]["breaks"], 0)
        self.assertEqual(second["event_counts"]["breaks"], 1)
        self.assertIsNone(first["metrics"]["bonds"]["sem_estimate"])

    def test_prepare_and_dry_launch_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "review.md"
            evidence.write_text("Accepted independent E1 histories")
            entries = [dict(bank=str(root / f"r{replica}"), executable_sha256="fixture",
                            status="planned", command=["never-execute"], parent_e1="fixture",
                            parent_e1_sha256=str(replica), md_seed=22000 + replica,
                            chemistry_seed=22000 + replica, requested_e2_steps=6000000,
                            pilot="C1_fresh_6M") for replica in (1, 2)]
            pilot.prepare(root, entries, evidence)
            before = [(Path(entry["bank"]) / "command.json").read_bytes() for entry in entries]
            with mock.patch.object(pilot.subprocess, "Popen", side_effect=AssertionError("MD forbidden")):
                pilot.launch(root, entries, False)
            self.assertEqual(before, [(Path(entry["bank"]) / "command.json").read_bytes() for entry in entries])
            with self.assertRaisesRegex(ValueError, "overwrite"):
                pilot.prepare(root, entries, evidence)
            record = campaign.load_json(Path(entries[0]["bank"]) / "command.json")
            record["status"] = "incomplete"
            campaign.write_json(Path(entries[0]["bank"]) / "command.json", record)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                pilot.launch(root, entries, False)

    def test_failed_execution_stops_before_next_replica(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "banks/e2" / analysis.BANK_ID
            parent.mkdir(parents=True)
            evidence = root / "review.md"
            evidence.write_text("Accepted E1")
            entries = [dict(bank=str(parent / f"r{replica:03d}"), executable_sha256="fixture",
                            status="planned", command=["never-execute"], parent_e1="fixture",
                            parent_e1_sha256=str(replica), md_seed=22000 + replica,
                            chemistry_seed=22000 + replica, requested_e2_steps=6000000,
                            pilot="C1_fresh_6M") for replica in (1, 2)]
            pilot.prepare(root, entries, evidence)
            process = mock.Mock(pid=123, wait=mock.Mock(return_value=1))
            preflight = mock.Mock(returncode=0, stdout="SELF_TEST PASS")
            with mock.patch.object(pilot.subprocess, "run", return_value=preflight), \
                    mock.patch.object(pilot.subprocess, "Popen", return_value=process) as start:
                with self.assertRaisesRegex(ValueError, "incomplete artifacts retained"):
                    pilot.launch(root, entries, True)
            self.assertEqual(start.call_count, 1)
            first = campaign.load_json(parent / "r001/command.json")
            second = campaign.load_json(parent / "r002/command.json")
            self.assertEqual(first["status"], "incomplete")
            self.assertEqual(second["status"], "planned")
            self.assertFalse((parent / ".launch.lock").exists())
            self.assertFalse((parent / "r001/complete.json").exists())

    def test_frozen_launcher_and_generic_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            system = analysis.model()
            command = campaign.e2_command(root, system, 2, root / "bank", 6000000)
            expected = {"--arms": "4", "--narm": "10", "--dt": "0.01", "--temperature": "1",
                        "--Ea": "4", "--Ee": "8", "--nu0": "20", "--Nevery": "100",
                        "--r-assoc": "1.25", "--damp": "2", "--K": "30", "--R0": "1.5",
                        "--seed": "22002", "--steps": "6000000", "--diagnostic-every": "1000"}
            for option, value in expected.items():
                self.assertEqual(command[command.index(option) + 1], value)
            self.assertNotIn("--restart-prefix", command)
            self.assertFalse(any("dpd" in item.lower() for item in command))
            args = campaign.build_parser().parse_args([
                "equilibrate", "--dataset-root", str(root), "--stage", "e2",
                "--system", system["system_id"], "--replicas", "2", "--steps", "6000000"])
            campaign.command_equilibrate(args)
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
