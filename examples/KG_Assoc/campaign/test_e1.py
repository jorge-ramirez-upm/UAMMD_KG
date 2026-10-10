import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import kg_assoc_e1 as e1
import kg_assoc_campaign as campaign


class E1Test(unittest.TestCase):
    def failed_entry(self, root):
        geometry = "F04_N010_RP060"
        bank = root / "banks" / "e1" / geometry / "r002"
        bank.mkdir(parents=True)
        (bank / "diagnostics.tsv").write_text("original failed diagnostics\n")
        campaign.write_json(bank / "command.json", {"status": "incomplete"})
        return next(row for row in e1.inventory(root) if
                    row["geometry"] == geometry and row["replica"] == 2)

    def test_inventory_and_dry_run_preserve_originals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failed = self.failed_entry(root)
            completed = root / "banks/e1/F04_N010_RP060/r001"
            completed.mkdir()
            (completed / "state.e1.lammpsdat").write_text("accepted state\n")
            before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
            rows = e1.inventory(root)
            self.assertEqual(24, len(rows))
            self.assertEqual(1, sum(row["status"] == "completed" for row in rows))
            args = SimpleNamespace(retry=["F04_N010_RP060/r002"], execute=False)
            with mock.patch.object(e1.subprocess, "Popen") as launch, \
                    contextlib.redirect_stdout(io.StringIO()):
                e1.run(args, root)
            launch.assert_not_called()
            self.assertEqual(before, {path: path.read_bytes() for path in root.rglob("*")
                                      if path.is_file()})
            retry = e1.next_attempt(root, failed)
            self.assertIn("e1_retries", retry.parts)
            self.assertNotEqual(failed["bank"], retry)

    def test_retry_requires_explicit_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.failed_entry(root)
            with contextlib.redirect_stdout(io.StringIO()), \
                    self.assertRaisesRegex(ValueError, "requires explicit --retry"):
                e1.run(SimpleNamespace(retry=[], execute=False), root)

    def test_failed_execution_stops_and_keeps_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failed = self.failed_entry(root)
            original = (failed["bank"] / "diagnostics.tsv").read_bytes()
            process = mock.Mock(pid=123)
            process.wait.return_value = 1
            preflight = subprocess.CompletedProcess([], 0, "E1_SELF_TEST PASS",
                "[E1 DPD effective] dt=0.00200000009 gamma=4.5")
            pending = dict(failed, replica=3, seed=12003, status="pending",
                           bank=root / "banks/e1/F04_N010_RP060/r003")
            with mock.patch.object(e1, "inventory", return_value=[failed, pending]), \
                    mock.patch.object(campaign, "validate_geometry"), \
                    mock.patch.object(campaign, "sha256", return_value="test-hash"), \
                    mock.patch.object(e1.subprocess, "run", return_value=preflight), \
                    mock.patch.object(e1.subprocess, "Popen", return_value=process) as launch, \
                    contextlib.redirect_stdout(io.StringIO()), \
                    self.assertRaisesRegex(ValueError, "stopping immediately"):
                e1.run(SimpleNamespace(retry=["F04_N010_RP060/r002"], execute=True), root)
            self.assertEqual(1, launch.call_count)
            self.assertEqual(original, (failed["bank"] / "diagnostics.tsv").read_bytes())
            self.assertFalse((root / "banks/e1/.run.lock").exists())
            attempt = root / "banks/e1_retries/F04_N010_RP060/r002/attempt001/command.json"
            self.assertEqual("incomplete", campaign.load_json(attempt)["status"])

    def test_output_that_failed_validation_requires_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failed = self.failed_entry(root)
            (failed["bank"] / "state.e1.lammpsdat").write_text("invalid output")
            campaign.write_json(failed["bank"] / "command.json", {
                "status": "incomplete", "validation_error": "invalid FENE bond"})
            row = next(row for row in e1.inventory(root) if
                       row["geometry"] == failed["geometry"] and row["replica"] == 2)
            self.assertEqual("failed", row["status"])

    def test_active_reference_keeps_original_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failed = self.failed_entry(root)
            retry = e1.next_attempt(root, failed)
            retry.mkdir(parents=True)
            e1.publish(root, failed, retry)
            self.assertEqual(retry, campaign.e1_bank_path(root, "F04_N010_RP060", 2))
            self.assertEqual("original failed diagnostics\n",
                             (failed["bank"] / "diagnostics.tsv").read_text())

    def test_effective_parameters_require_all_corrected_segments(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stderr.log"
            segment = "[E1 DPD effective] dt=0.002 gamma=4.5 noise_squared_dt=9\n"
            path.write_text(segment * 16)
            self.assertEqual("4.5", e1.check_effective_dpd(path)["gamma"])
            for incorrect in (segment * 15, (segment * 16).replace("gamma=4.5", "gamma=1"),
                              (segment * 16).replace("noise_squared_dt=9", "noise_squared_dt=2")):
                path.write_text(incorrect)
                with self.assertRaises(ValueError):
                    e1.check_effective_dpd(path)

    def test_corrected_state_requires_exact_steps_and_seed(self):
        with tempfile.TemporaryDirectory() as directory:
            bank = Path(directory)
            state = bank / "state.e1.lammpsdat"
            (bank / "diagnostics.tsv").touch()
            entry = {"bank": bank, "system": {"N": 10}, "seed": 12002}
            rows = [{"step": step, "max_permanent_bond": 1.3,
                     "min_permanent_bond": 0.9, "mean_rg2": 2,
                     "mean_center_terminal_r2": 3} for step in (1000, 2000)]
            with mock.patch.object(e1, "check_snapshot", return_value={}), \
                    mock.patch.object(e1, "check_effective_dpd", return_value={}), \
                    mock.patch.object(e1.stationarity, "read_diagnostics", return_value=rows), \
                    mock.patch.object(e1.stationarity, "select_uniform_stage4_suffix",
                                      return_value=(rows, 10)), \
                    mock.patch.object(e1.stationarity, "summarize", return_value={}):
                state.write_text("E1 seed=12002 step 2075900\n")
                self.assertEqual("valid", e1.validate(entry, True)["numerical_status"])
                for header in ("E1 seed=12001 step 2075900\n", "E1 seed=12002 step 2075901\n"):
                    state.write_text(header)
                    with self.assertRaisesRegex(ValueError, "wrong step count or seed"):
                        e1.validate(entry, True)

    def test_snapshot_rejects_nonfinite_state_and_invalid_fene(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.lammpsdat"
            system = {"f": 3, "N": 1, "number_of_stars": 1,
                      "rho_p": 0.1, "total_bead_density": 0.1}
            length = 40 ** (1 / 3)
            text = (f"test\n4 atoms\n3 bonds\n3 atom types\n1 bond types\n"
                    f"0 {length} xlo xhi\n0 {length} ylo yhi\n0 {length} zlo zhi\n"
                    "Atoms\n1 1 1 0 0 0\n2 1 2 0.8 0 0\n"
                    "3 1 2 0 0.8 0\n4 1 2 0 0 0.8\n"
                    "Velocities\n1 1 1 1\n2 1 1 1\n3 1 1 1\n4 1 1 1\n"
                    "Bonds\n1 1 1 2\n2 1 1 3\n3 1 1 4\n")
            path.write_text(text)
            self.assertAlmostEqual(1.0, e1.check_snapshot(path, system)["final_temperature"])
            path.write_text(text.replace("2 1 2 0.8", "2 1 2 1.5"))
            with self.assertRaisesRegex(ValueError, "invalid final permanent FENE"):
                e1.check_snapshot(path, system)
            path.write_text(text.replace("Velocities\n1 1 1 1", "Velocities\n1 nan 1 1"))
            with self.assertRaisesRegex(ValueError, "nonfinite"):
                e1.check_snapshot(path, system)


if __name__ == "__main__":
    unittest.main()
