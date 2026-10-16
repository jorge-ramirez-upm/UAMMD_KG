"""CPU-only readback evidence fixtures; no GPU or trajectories."""
import json
from pathlib import Path
import tempfile
import unittest

import kg_assoc_e2_readback as readback


class ReadbackTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.executable = self.root / 'cpu_fixture'
        self.executable.write_text('not an executable or physical trajectory')
        self.build = dict(executable_sha256={str(self.executable):
                         readback.campaign.sha256(self.executable)})
        (self.root / 'manifest.json').write_text(json.dumps(self.build))
        self.parent = dict(atoms={1: (1, 2), 2: (1, 2)},
            positions={1: (0, 0, 0), 2: (1, 0, 0)},
            velocities={1: (.5, 0, 0), 2: (0, 0, .5)},
            bounds={axis: (-20, 20) for axis in 'xyz'})
        self.entry = dict(start_step=8000000, command=[str(self.executable)],
                          lineage=dict(branch_id='F04_N010_RP080_EE08_EA06:cpu_fixture:r001'))
        self.path = self.root / 'initial.tsv'
        self.text = ('# validation_evidence_version=1 real_bytes=4 rounding_mode=0 absolute_step=8000000 '
            'chemistry_sweep=0 branch=' + self.entry['lineage']['branch_id'] + '\n' +
            '# executable=' + str(self.executable) + ' build_manifest=' + str(self.root/'manifest.json') + '\n' +
            '# build ' + json.dumps(self.build) + '\n' +
            '# initial_device_readback_version=1 branch_age=0 mapping_valid=1\n' +
            'particle 0 0 1 2 2 1 1 0 0 0 0 0 0 .5 0 0 .5 0 0\n' +
            'particle 1 1 1 2 2 0 0 1 0 0 1 0 0 0 0 .5 0 0 .5\n' +
            '# readback_pass=1 particles=2 max_position_mic_error=0 max_velocity_error=0\n')
        self.path.write_text(self.text)

    def check(self):
        return readback.check(self.path, self.entry, self.parent, [(1, 2)])

    def test_valid_and_exact_periodic_image(self):
        self.assertEqual(self.check()['particles'], 2)
        self.path.write_text(self.text.replace('0 0 0 0 0 0 .5', '0 0 0 40 0 0 .5'))
        self.assertEqual(self.check()['status'], 'valid')

    def test_parent_representation_and_periodic_folding(self):
        self.parent['positions'][2] = (41, 0, 0)
        self.assertEqual(self.check()['status'], 'valid')
        bounds = {axis: (-20, 20) for axis in 'xyz'}
        self.assertEqual(readback.represented_position((40.25, -40.5, 80.75), bounds),
                         [.25, -.5, .75])
        self.assertEqual(readback.represented_position((20, -20, 0), bounds), [20, 20, 0])

    def test_missing_malformed_and_failed_evidence(self):
        for text in [self.text.replace('readback_pass=1','readback_pass=0'),
                     self.text.replace('mapping_valid=1','mapping_valid=0'),
                     self.text.replace('rounding_mode=0','rounding_mode=2048'),
                     self.text.replace('branch_age=0','branch_age=1'),
                     self.text.replace('particle 1 1','particle 0 1'),
                     self.text.replace('particle 1 1 1 2 2 0 0','particle 1 1 1 2 2 0 -1'),
                     self.text.replace('0 0 0 0 0 0 .5','0 0 0 .001 0 0 .5'),
                     self.text.replace('.5 0 0 .5 0 0','.5 0 0 .6 0 0'),
                     self.text.replace('0 0 0 .5 0 0','0 nan 0 .5 0 0'),
                     '\n'.join(line for line in self.text.splitlines() if not line.startswith('particle 1'))]:
            self.path.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.check()

    def test_authenticated_parent_and_build_tampering(self):
        self.parent['velocities'][1] = (.6, 0, 0)
        with self.assertRaisesRegex(ValueError, 'velocity'):
            self.check()
        self.parent['velocities'][1] = (.5, 0, 0)
        self.parent['positions'][1] = (.1, 0, 0)
        with self.assertRaisesRegex(ValueError, 'coordinates'):
            self.check()
        self.parent['positions'][1] = (0, 0, 0)
        self.executable.write_text('corruption')
        with self.assertRaisesRegex(ValueError, 'build identity'):
            self.check()


if __name__ == '__main__':
    unittest.main()
