"""Bounded GPU-host checks for the explicit every-step stress mode."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BIN = Path(sys.argv[1]).resolve()
sys.argv[1:] = []

class EveryStepGpuTests(unittest.TestCase):
    def setUp(self): self.temp = tempfile.TemporaryDirectory(prefix="every-step-gpu-")
    def tearDown(self): self.temp.cleanup()
    def run(self, name, *extra):
        out = Path(self.temp.name)/name
        cmd = [str(BIN), "--output", str(out), "--springs", "8", "--chains", "8", "--steps", "39",
               "--sample", "7", "--dt", ".000025", "--seed", "433201", "--kappa", "10"] + list(extra)
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stdout+done.stderr)
        return out
    def test_step_zero_partial_turnover_and_replay(self):
        off = self.run("off", "--stress-mode", "off")
        previous = None
        for batch in (1, 7, 256):
            every = self.run(f"every-{batch}", "--stress-mode", "every-step", "--stress-batch", str(batch),
                             "--corr-levels", "5", "--corr-slots", "8", "--cpu-workers", "2")
            self.assertEqual((off/"final.csv").read_bytes(), (every/"final.csv").read_bytes())
            meta = json.loads((every/"stress_metadata.json").read_text())
            self.assertEqual(meta["frames"], 40)
            self.assertEqual(meta["spacing"], .000025)
            self.assertEqual(meta["moment_frames"], 21)
            self.assertIn("chain-major", meta["buffer_mode"])
            self.assertGreaterEqual(meta["buffer_wait_seconds"], 0)
            self.assertEqual(meta["queue_slot_capacity"], 2)
            self.assertLessEqual(meta["max_inflight_slots"], 2)
            self.assertTrue((every/"stress_correlations.csv").exists())
            self.assertTrue((every/"stress_moments.csv").exists())
            if previous:
                self.assertEqual((previous/"stress_correlations.csv").read_bytes(),
                                 (every/"stress_correlations.csv").read_bytes())
            previous = every
    def test_zero_bending_every_step(self):
        out = self.run("zero", "--kappa", "0", "--stress-mode", "every-step", "--stress-batch", "7",
                       "--corr-levels", "5", "--corr-slots", "8")
        meta = json.loads((out/"stress_metadata.json").read_text())
        self.assertEqual(meta["frames"], 40)
        self.assertEqual(meta["bending_stress_launches"], 0)
        self.assertEqual(meta["bending_stress_device_bytes"], 0)

if __name__ == "__main__": unittest.main()
