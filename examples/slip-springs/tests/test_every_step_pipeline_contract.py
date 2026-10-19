"""CPU-only contract checks; GPU execution is intentionally delegated to cholosimeone."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class EveryStepPipelineContract(unittest.TestCase):
    def test_source_preserves_separate_clocks_and_bounded_backpressure(self):
        driver = (ROOT/"semiflexible.cu").read_text()
        adapter = (ROOT/"semiflexible_stress_stream.h").read_text()
        for token in ("everyStep())stressObserver->sample(current,0)",
                      "everyStep())stressObserver->sample(current,step+1)",
                      "!o.stress.everyStep())stressObserver->sample(current,step)"):
            self.assertIn(token, driver)
        for token in ("chain_major::Bank", "chain_major::Workers", "cudaMemcpyAsync",
                      "cudaStreamWaitEvent", "Slot::free", "every-step stress frame accounting mismatch"):
            self.assertIn(token, adapter)
        self.assertIn("slots.push_back", adapter)
    def test_validated_chain_major_cpu_equivalence_suite(self):
        # Existing deterministic test covers chronological chains, worker ranges,
        # repeated batch turnovers, partial inputs, exceptions and bounded bank budget.
        done = subprocess.run([sys.executable, str(ROOT/"tests/run_stress_throughput.py")],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stdout+done.stderr)

if __name__ == "__main__": unittest.main()
