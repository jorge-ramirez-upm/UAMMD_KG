import pathlib
import subprocess
import unittest


SCRIPT = pathlib.Path(__file__).with_name('run_stage4a3c_nonlinear_pilot.sh')


class NonlinearPilotRunnerContractTest(unittest.TestCase):
    def test_shell_syntax_and_fail_closed_contract(self):
        subprocess.run(['bash', '-n', str(SCRIPT)], check=True)
        source = SCRIPT.read_text()
        self.assertIn('run only from $development', source)
        self.assertIn('checkpoint_restart=unsupported', source)
        self.assertIn('timeout --foreground --signal=TERM --kill-after=20s', source)
        self.assertIn('steps=100000', source)
        self.assertIn('--stress-mode every-step', source)
        self.assertIn('--scalar-output full', source)
        self.assertNotIn('--scalar-output compact', source)
        self.assertIn('if [[ "$execute" != true ]]', source)
        self.assertIn('protected checkout not pinned', source)
        self.assertIn('partial_evidence_preserved=true', source)


if __name__ == '__main__':
    unittest.main()
