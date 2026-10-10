"""Deterministic recovery gates and scientific window accounting; no MD."""

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import kg_assoc_c1_recovery as recovery
import analyze_c1_recovery as review


class RecoveryTests(unittest.TestCase):
    def test_commands_use_original_parents_and_separate_seeds(self):
        commands = recovery.commands(Path("/dataset"), Path("/dataset/banks/e2_extensions/new"))
        for replica, command in enumerate(commands, 1):
            self.assertIn(f"/dataset/banks/e2/F04_N010_RP080_EE08/r{replica:03d}/state", command)
            self.assertEqual(command[command.index("--steps") + 1], "2000000")
            self.assertEqual(command[command.index("--seed") + 1], str(22000 + replica))
            self.assertEqual(command[command.index("--md-seed") + 1], str(32000 + replica))
            self.assertNotIn("--force", command)

    def test_dry_run_approval_and_existing_artifact_gates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for replica in (1, 2, 3):
                (root / f"r{replica:03d}").mkdir()
            plan = dict(commands=recovery.commands(root, root))
            with mock.patch.object(recovery, "authenticate_plan", return_value=plan), \
                    mock.patch.object(recovery.subprocess, "Popen") as process:
                recovery.launch(root, root, False, None, None)
                process.assert_not_called()
                with self.assertRaisesRegex(ValueError, "approval and fresh MD smoke"):
                    recovery.launch(root, root, True, None, None)
                (root / "r001/unexpected.events").write_text("preserve")
                with self.assertRaisesRegex(ValueError, "attempt already used"):
                    recovery.launch(root, root, False, None, None)
                self.assertEqual((root / "r001/unexpected.events").read_text(), "preserve")
                process.assert_not_called()

    def test_authentication_rejects_changed_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "executable"
            path.write_text("original")
            recovery.campaign.write_json(root / "plan.json", dict(
                commands=recovery.commands(root, root), git_sha="test", sha256={str(path): "wrong"}))
            with mock.patch.object(recovery.campaign, "git_sha", return_value="test"), \
                    mock.patch.object(recovery.subprocess, "check_output", return_value=""):
                with self.assertRaisesRegex(ValueError, "authenticated file changed"):
                    recovery.authenticate_plan(root, root)

    def test_first_failure_is_retained_and_stops_other_replicas(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for replica in (1, 2, 3):
                (root / f"r{replica:03d}").mkdir()
            plan = dict(commands=recovery.commands(root, root), git_sha="test")
            recovery.campaign.write_json(root / "plan.json", plan)
            approval = root / "approval.json"
            recovery.campaign.write_json(approval, dict(approved=True, reviewer="fixture",
                approved_at="test", purpose="C1_corrected_2M_recovery",
                plan_sha256=recovery.campaign.sha256(root / "plan.json")))
            with mock.patch.object(recovery, "authenticate_plan", return_value=plan), \
                    mock.patch.object(recovery, "smoke_evidence", return_value={}), \
                    mock.patch.object(recovery.subprocess, "Popen") as process:
                process.return_value.wait.return_value = 1
                with self.assertRaisesRegex(ValueError, "MD executable failed"):
                    recovery.launch(root, root, True, approval, root / "fake_smoke")
                self.assertEqual(process.call_count, 1)
            status = recovery.campaign.load_json(root / "r001/status.json")
            self.assertEqual(status["status"], "incomplete")
            self.assertFalse(any((root / "r002").iterdir()))
            self.assertFalse((root / ".launch.lock").exists())

    def test_event_windows_and_exact_exposure(self):
        rows = []
        for step in range(0, 20001, 1000):
            row = dict(step=step, time=step * .01)
            row.update({key: 1 for key in review.analysis.METRICS})
            row["bonds"] = 0 if 5000 <= step < 6000 else 1
            rows.append(row)
        events = [dict(step=5000, type="B", neighbor_loss=1, neighbor_gain=0),
                  dict(step=6000, type="C", neighbor_loss=0, neighbor_gain=1)]
        first = review.window(rows, events, 0, 5000)
        second = review.window(rows, events, 5000, 10000)
        self.assertEqual(first["event_counts"]["breaks"], 1)
        self.assertEqual(second["event_counts"]["breaks"], 0)
        self.assertEqual(second["event_counts"]["creations"], 1)
        self.assertEqual(first["duration"], 50)
        self.assertEqual(first["event_rates_per_time"]["breaks"], .02)
        self.assertEqual(first["exposure"]["active_bond_time"], 50)
        self.assertEqual(first["exposure"]["free_sticker_time"], 3998 * 50)
        self.assertEqual(second["exposure"]["active_bond_time"], 40)
        self.assertEqual(second["exposure"]["free_sticker_time"], 4000 * 10 + 3998 * 40)
        self.assertAlmostEqual(first["activity"]["breaks"]["mean"], .02)
        again = review.window(rows, events, 0, 5000)
        self.assertEqual(first, again)

    def test_independent_replica_and_paired_comparisons(self):
        records = []
        for value in (1, 2, 3):
            metric = dict(metrics=dict(bonds=dict(mean=value)), activity=dict(creations=dict(mean=value)))
            records.append(dict(corrected=[metric] * 4, defective=[metric] * 4))
        results = review.comparisons(records)
        self.assertEqual(results[0]["replicas"], 3)
        self.assertEqual(results[0]["mean"], 2)
        self.assertAlmostEqual(results[0]["ci95_half_width"], 4.303 / (3 ** .5))
        self.assertEqual(results[4]["mean"], 0)

    def test_analysis_pipeline_reproducible_without_md(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt = root / "banks/e2_extensions/fixture"
            def frames(start, end):
                return [dict(step=step, time=step * .01,
                             **{key: 1 for key in review.analysis.METRICS})
                        for step in range(start, end + 1, 1000)]
            old = frames(4000000, 6000000)
            for row in old:
                row.update(temperature=1, min_permanent_bond=.8, max_permanent_bond=.9)
            corrected = frames(6000000, 8000000)
            for replica in (1, 2, 3):
                directory = attempt / f"r{replica:03d}"
                directory.mkdir(parents=True)
                for suffix in review.analysis.OUTPUTS:
                    (directory / ("state" + suffix)).write_text("offline pipeline fixture")
            def parent(root, replica, oracle=False):
                return root / "banks/e2" / review.analysis.BANK_ID / f"r{replica:03d}/state", {}
            with mock.patch.object(recovery, "verify"), \
                    mock.patch.object(recovery, "authenticate_parent", side_effect=parent), \
                    mock.patch.object(review.analysis, "verify_outputs", return_value=({}, old, [], {})), \
                    mock.patch.object(review.analysis.stationarity, "read_state", return_value=({}, corrected)), \
                    mock.patch.object(review.analysis, "numerics", return_value=[
                        [row["step"], row["time"], 1, 1, .8, .9] for row in corrected]), \
                    mock.patch.object(review.analysis.topology, "read_system", return_value={}), \
                    mock.patch.object(review.analysis.dynamics, "read_events", return_value=({}, [])), \
                    mock.patch.object(review.analysis.restart, "read_metadata", return_value=(
                        dict(creations=1, breaks=0), [(1, 2)])), \
                    mock.patch.object(review.analysis, "replay", return_value=({(1, 2)}, [])):
                first, second = root / "aggregate/e2/review1", root / "aggregate/e2/review2"
                review.analyze(root, attempt, first)
                review.analyze(root, attempt, second)
                for name in ("summary.json", "windowed_observables.csv", "windowed_events.csv",
                             "replica_comparisons.csv", "window_comparison.png"):
                    self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
                with self.assertRaisesRegex(ValueError, "already exists"):
                    review.analyze(root, attempt, first)


if __name__ == "__main__":
    unittest.main()
