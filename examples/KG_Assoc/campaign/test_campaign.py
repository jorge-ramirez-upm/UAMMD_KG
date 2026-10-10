#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("kg_assoc_campaign.py")
SPEC = importlib.util.spec_from_file_location("kg_assoc_campaign", MODULE_PATH)
CAMPAIGN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAMPAIGN)
STRUCTURE_PATH = MODULE_PATH.parents[1] / "analysis" / "analyze_campaign_structure.py"
STRUCTURE_SPEC = importlib.util.spec_from_file_location("analyze_campaign_structure", STRUCTURE_PATH)
STRUCTURE = importlib.util.module_from_spec(STRUCTURE_SPEC)
STRUCTURE_SPEC.loader.exec_module(STRUCTURE)


class CampaignTest(unittest.TestCase):
    def test_matrix_has_fifteen_associating_and_eight_controls(self):
        systems = CAMPAIGN.campaign_systems()
        self.assertEqual(15, sum(item["associating"] for item in systems))
        self.assertEqual(8, sum(not item["associating"] for item in systems))
        self.assertEqual(23, len({item["system_id"] for item in systems}))

    def test_reference_is_deduplicated_and_in_five_groups(self):
        reference = next(item for item in CAMPAIGN.campaign_systems()
                         if item["system_id"] == "F04_N010_RP080_EE08_EA04")
        self.assertEqual({"association", "kinetics", "density", "arm_length", "functionality"},
                         set(reference["groups"]))

    def test_initialization_writes_eight_geometry_requirements(self):
        with tempfile.TemporaryDirectory() as temporary:
            class Arguments:
                dataset_root = temporary
            CAMPAIGN.command_init(Arguments())
            requirements = list((Path(temporary) / "inputs").glob("*/requirements.example.json"))
            self.assertEqual(8, len(requirements))
            self.assertEqual(24, len(list((Path(temporary) / "banks" / "e1").glob("*/r*"))))
            config = CAMPAIGN.load_json(Path(temporary) / "production_config.json")
            self.assertFalse(config["continuation"])
            self.assertNotIn("checkpoint", config["cadence_steps"])

    def test_production_command_has_no_continuation_options(self):
        system = next(item for item in CAMPAIGN.campaign_systems()
                      if item["system_id"] == "F04_N010_RP080_EE08_EA04")
        run = {"replica": 1, "md_seed": 1, "parent_e2": "/bank/state",
               "parent_e1": "/bank/e1"}
        command = CAMPAIGN.production_command(Path("/dataset"), system, run)
        self.assertIn("--equilibrated-prefix", command)
        self.assertNotIn("--restart-prefix", command)
        self.assertFalse(any("checkpoint" in word or "resume" in word for word in command))

    def test_e1_launcher_uses_validated_dpd_timestep(self):
        with tempfile.TemporaryDirectory() as temporary:
            arguments = CAMPAIGN.build_parser().parse_args([
                "equilibrate", "--dataset-root", temporary, "--stage", "e1",
                "--system", "F04_N010_RP060_EE08_EA04", "--replicas", "2"])
            with mock.patch.object(CAMPAIGN, "run_or_print", return_value=0) as runner:
                CAMPAIGN.command_equilibrate(arguments)
            command = runner.call_args.args[0]
            self.assertEqual("0.002", command[command.index("--dt-dpd") + 1])
            self.assertEqual("0.01", command[command.index("--dt-wca") + 1])
            self.assertEqual("12002", command[command.index("--seed") + 1])
            self.assertEqual("20000", command[command.index("--stage3b-steps") + 1])
            self.assertFalse(runner.call_args.args[1])

    def test_short_e1_validator_rejects_incorrect_effective_gamma(self):
        script = MODULE_PATH.parents[1] / "scripts" / "validate_e1_rp060_short.sh"
        validator = script.read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "stdout.log").write_text("E1_PROMOTION PASS\n")
            log_line = ("[E1 DPD effective] dt=0.002 gamma=4.5 "
                        "noise_squared_dt=9 radial_noise_amplitude=67.0820381\n")
            (root / "stderr.log").write_text(log_line * 16)
            (root / "timing.txt").write_text("10 1 1 1000\n")
            (root / "diagnostics.tsv").write_text("".join(
                "# [E1 transition] label=during_stage3b_relaxation_hold "
                f"step={51400 + local} temperature=1 max_speed=5 "
                "min_permanent_bond=0.7 max_permanent_bond=1.35\n"
                for local in range(500, 20001, 500)))
            result = subprocess.run([sys.executable, "-c", validator, temporary],
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            summary = CAMPAIGN.load_json(root / "summary.json")
            self.assertEqual("passed", summary["status"])
            self.assertEqual(75900, summary["dpd_steps"] + summary["wca_steps"])
            (root / "stderr.log").write_text(log_line.replace("gamma=4.5", "gamma=1") * 16)
            result = subprocess.run([sys.executable, "-c", validator, temporary],
                                    capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("gamma/noise validation failed", result.stderr)

    def test_structure_reader_reconstructs_pbc_safe_rg(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tiny.bin"
            with path.open("wb") as output:
                output.write(b"KG_BEADS_BIN_V2\0")
                output.write(struct.pack("=IQQ6d", 2, 3, 2, 0, 10, 0, 10, 0, 10))
                output.write(struct.pack("=iii", 1, 1, 1))
                output.write(struct.pack("=iii", 2, 1, 1))
                output.write(struct.pack("=iii", 3, 1, 2))
                output.write(struct.pack("=ii", 1, 2))
                output.write(struct.pack("=ii", 2, 3))
                output.write(struct.pack("=Iqd", STRUCTURE.FRAME_MAGIC, 100, 1.0))
                output.write(struct.pack("=9f", 9, 1, 1, 3, 1, 1, 7, 1, 1))
            rows = STRUCTURE.analyze(path)
            self.assertEqual(100, rows[0][0])
            self.assertAlmostEqual(32.0 / 3.0, rows[0][2])

    def test_topology_and_com_frame_readers_require_complete_frames(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            topology = root / "run.topology"
            topology.write_text(
                "# header\nFRAME 10000 100 1\n4 8 1 2\nFRAME 20000 200 0\n",
                encoding="utf-8")
            com = root / "run.com_trajectory"
            com.write_text(
                "# header\n10000 100 1 0 0 0\n10000 100 2 1 0 0\n"
                "20000 200 1 0 1 0\n20000 200 2 1 1 0\n",
                encoding="utf-8")
            self.assertEqual(CAMPAIGN.read_topology_frames(topology),
                             CAMPAIGN.read_com_frames(com, 2))
            with com.open("a", encoding="utf-8") as output:
                output.write("20000 200 2 2 2 2\n")
            with self.assertRaisesRegex(ValueError, "duplicate molecule"):
                CAMPAIGN.read_com_frames(com, 2)


if __name__ == "__main__":
    unittest.main()
