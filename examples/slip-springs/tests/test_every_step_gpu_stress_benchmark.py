"""Static and bounded checks for the isolated Stage 4A.3c benchmark driver."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class EveryStepBenchmarkTests(unittest.TestCase):
    def test_scope_and_required_measurements(self):
        text = (ROOT / "tests/every_step_gpu_stress_benchmark.cu").read_text()
        for token in ("stretchTensor", "bendTensor", "channels", "cudaMallocHost",
                      "cudaMemcpyAsync", "frame_hash", "integration_ns_per_bead_step",
                      "overall_ns_per_bead_step", "final partial D2H"):
            self.assertIn(token, text)
        self.assertNotIn('#include "../semiflexible.cu"', text)

    def test_existing_prescribed_coordinate_oracle_remains_runnable(self):
        # This is the independent six-channel reference used by the GPU fixture.
        completed = subprocess.run([sys.executable, str(ROOT / "tests/test_semiflexible_reference.py")],
                                   capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    @unittest.skipUnless(os.getenv("SEMIFLEXIBLE_GPU_BIN") and os.getenv("EVERY_STEP_GPU_BENCHMARK_BIN")
                         and os.getenv("SEMIFLEXIBLE_STRESS_FIXTURE"),
                         "set SEMIFLEXIBLE_GPU_BIN, EVERY_STEP_GPU_BENCHMARK_BIN and SEMIFLEXIBLE_STRESS_FIXTURE")
    def test_gpu_oracle_and_transport_replay(self):
        simulator = os.environ["SEMIFLEXIBLE_GPU_BIN"]
        benchmark = os.environ["EVERY_STEP_GPU_BENCHMARK_BIN"]
        fixture = os.environ["SEMIFLEXIBLE_STRESS_FIXTURE"]
        # Existing suite compares all nine stretch/bend/total tensor entries and
        # derives all six channels against the independent prescribed-coordinate
        # reference, including the zero-bending fast path and both precisions.
        oracle = subprocess.run([sys.executable, str(ROOT / "tests/test_semiflexible_stress_gpu.py"), simulator, fixture],
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(oracle.returncode, 0, oracle.stdout + oracle.stderr)
        for kappa, batch in ((10, 256), (0, 256), (10, 1024)):
            hashes = []
            for mode in ("direct", "batch", "async"):
                run = subprocess.run([benchmark, "--n", "8", "--chains", "16", "--steps", "8",
                                      "--warmup", "1", "--batch", str(batch), "--kappa", str(kappa), "--mode", mode],
                                     capture_output=True, text=True, timeout=120)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                row = json.loads(run.stdout)
                self.assertEqual(row["frames"], 9)  # Step 0 plus all eight updates.
                self.assertEqual(row["bend_seconds"], 0 if kappa == 0 else row["bend_seconds"])
                hashes.append(row["frame_hash"])
            self.assertEqual(len(set(hashes)), 1, "transport dropped, duplicated, or reordered a frame")

if __name__ == "__main__":
    unittest.main()
