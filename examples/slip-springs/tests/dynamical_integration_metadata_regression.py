"""Prepared, UNEXECUTED deterministic verifier regression; no simulator imports/runs.

Local command: python3 examples/slip-springs/tests/dynamical_integration_metadata_regression.py
Only disposable synthetic JSON/physical-record fixtures are created.
"""
import json
from pathlib import Path
import tempfile
import unittest

from dynamical_integration_tiny import EQUILIBRIUM_TIMING, MAIN_TIMING, same_physics


class MetadataComparison(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.left, self.right = [Path(temporary.name) / name for name in ('left', 'right')]
        for root, seconds in ((self.left, 0.1), (self.right, 0.123456789)):
            root.mkdir()
            for name in ('initial.csv', 'final.csv', 'equilibrium_positions.csv',
                         'equilibrium_attachments.csv', 'equilibrium_events.csv'):
                (root / name).write_text('physical-record\n')
            self.write(root, 'metadata.json', {
                **dict.fromkeys(MAIN_TIMING, seconds), 'dt': 0.0001,
                'unknown_physical_field': 7,
            })
            self.write(root, 'equilibrium_complete.json', {
                **dict.fromkeys(EQUILIBRIUM_TIMING, seconds), 'complete': True, 'frames': 7,
                'files': {p.name: p.stat().st_size for p in root.iterdir()},
            })

    @staticmethod
    def write(root, name, value):
        (root / name).write_text(json.dumps(value, sort_keys=True) + '\n')

    def changed(self, name, mutate):
        value = json.loads((self.right / name).read_text())
        mutate(value)
        self.write(self.right, name, value)

    def test_timing_and_main_metadata_length_may_differ(self):
        self.assertNotEqual((self.left / 'metadata.json').stat().st_size,
                            (self.right / 'metadata.json').stat().st_size)
        same_physics(self.left, self.right)

    def test_physical_inventory_size_rejected(self):
        self.changed('equilibrium_complete.json',
                     lambda m: m['files'].__setitem__('final.csv', 999))
        with self.assertRaises(AssertionError):
            same_physics(self.left, self.right)

    def test_inventory_filenames_rejected(self):
        self.changed('equilibrium_complete.json',
                     lambda m: m['files'].__setitem__('unknown.csv', 0))
        with self.assertRaises(AssertionError):
            same_physics(self.left, self.right)

    def test_missing_inventory_metadata_rejected(self):
        self.changed('equilibrium_complete.json', lambda m: m['files'].pop('metadata.json'))
        with self.assertRaises(AssertionError):
            same_physics(self.left, self.right)

    def test_unknown_fields_and_physical_values_rejected(self):
        for name, key, value in (
                ('metadata.json', 'new_unknown_field', 1),
                ('metadata.json', 'unknown_physical_field', 8),
                ('metadata.json', 'dt', 0.0002),
                ('equilibrium_complete.json', 'new_unknown_field', 1),
                ('equilibrium_complete.json', 'frames', 8)):
            with self.subTest(name=name, key=key):
                original = (self.right / name).read_bytes()
                self.changed(name, lambda m: m.__setitem__(key, value))
                with self.assertRaises(AssertionError):
                    same_physics(self.left, self.right)
                (self.right / name).write_bytes(original)

    def test_equal_length_physical_records_rejected(self):
        for name in ('initial.csv', 'final.csv', 'equilibrium_positions.csv',
                     'equilibrium_attachments.csv', 'equilibrium_events.csv'):
            with self.subTest(name=name):
                original = (self.right / name).read_bytes()
                (self.right / name).write_bytes(original.replace(b'physical', b'PHYSICAL'))
                with self.assertRaises(AssertionError):
                    same_physics(self.left, self.right)
                (self.right / name).write_bytes(original)


if __name__ == '__main__':
    unittest.main()
