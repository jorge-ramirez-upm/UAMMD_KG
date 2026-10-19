import pathlib
import subprocess
import unittest


SCRIPT = pathlib.Path(__file__).with_name('run_stage4a3c_stage_b.sh')


class StageBRunnerContractTest(unittest.TestCase):
    def test_shell_syntax_and_bounded_sequential_contract(self):
        subprocess.run(['bash', '-n', str(SCRIPT)], check=True)
        source = SCRIPT.read_text()
        self.assertIn('steps=8000000', source)
        self.assertIn('limit_seconds=1800', source)
        self.assertIn('--stress-mode every-step', source)
        self.assertIn('--scalar-output full', source)
        self.assertIn('run_case 0\nrun_case 10', source)
        self.assertIn('checkpoint_restart=unsupported', source)
        self.assertIn('if [[ "$execute" != true ]]', source)


if __name__ == '__main__':
    unittest.main()
