"""CPU-only checks for the Milestone A host evidence runner and protocol."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RunnerTests(unittest.TestCase):
    def test_runner_is_bounded_and_captures_required_evidence(self):
        runner = ROOT / "tests/run_stage4a3c_gpu_validation.sh"
        check = subprocess.run(["bash", "-n", str(runner)], capture_output=True, text=True, timeout=10)
        self.assertEqual(check.returncode, 0, check.stderr)
        text = runner.read_text()
        for token in ("release 13\\.0", "timeout 120s", "nvidia-smi", "binary-sha256.txt",
                      "oracle-single", "oracle-double", "replay-$precision", "status.tsv",
                      "/tmp/UAMMD_KG-slip-springs-dev"):
            self.assertIn(token, text)

    def test_protocol_is_explicitly_milestone_a_only(self):
        text = (ROOT / "STAGE4A3C_GPU_VALIDATION_PROTOCOL.md").read_text()
        self.assertIn("does not authorize", text)
        self.assertIn("CUDA_HOME=/usr/local/cuda-13.0", text)
        self.assertIn("CUDA_ARCH=sm_86", text)

if __name__ == "__main__":
    unittest.main()
