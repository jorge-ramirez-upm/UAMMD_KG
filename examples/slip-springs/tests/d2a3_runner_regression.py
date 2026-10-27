"""Prepared, UNEXECUTED CPU-only malformed-output checks. Never launches a child.

Local command: python3 -B examples/slip-springs/tests/d2a3_runner_regression.py
These synthetic records do not verify GPU dynamics or resource enforcement.
"""
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e1_d2a3_run import HEADER, curves, load


class AcquisitionRecords(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'curves.csv'
        self.rows = []
        for chain in ('0', '1'):
            for block in (1, 2, 4, 8, 16, 32, 64, 128, 256, 512):
                for lag in range(0 if block == 1 else 8 * block, 16 * block, block):
                    row = dict.fromkeys(HEADER, 0)
                    row.update(replica=732303101, chain=chain, lag_samples=lag,
                               lag_steps=lag * 100, lag_time=lag * 100 * 0.0001,
                               origins_per_chain=10001 // block - lag // block,
                               decimation_samples=block, diffusion_phase_samples=block - 1,
                               orientation_block_samples=block,
                               orientation_block_duration=block * 100 * 0.0001)
                    self.rows.append(row)

    def write(self, rows):
        with self.path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=HEADER)
            writer.writeheader()
            writer.writerows(rows)

    def test_complete_support_and_finite_curves(self):
        self.write(self.rows)
        self.assertEqual(curves(self.path, 732303101, ['0', '1']), 176)
        self.assertEqual(self.rows[-1]['origins_per_chain'], 4)
        self.assertEqual(self.rows[-1]['lag_time'], 76.8)

    def test_wrong_identity_count_clock_and_nonfinite_rejected(self):
        for key, value in (('replica', 732303102), ('chain', '7'),
                           ('origins_per_chain', 999), ('lag_time', 1),
                           ('diffusion_phase_samples', 12), ('orientation_block_samples', 3),
                           ('cm_msd', 'nan'), ('c2', 'inf')):
            with self.subTest(key=key):
                rows = [dict(row) for row in self.rows]
                rows[0][key] = value
                self.write(rows)
                with self.assertRaises(ValueError):
                    curves(self.path, 732303101, ['0', '1'])

    def test_missing_or_extra_rows_rejected(self):
        for rows in (self.rows[:-1], self.rows + [self.rows[-1]]):
            self.write(rows)
            with self.assertRaises(ValueError):
                curves(self.path, 732303101, ['0', '1'])

    def test_json_numeric_overflow_rejected(self):
        for text in ('{"dt": NaN}', '{"dt": 1e999}'):
            self.path.write_text(text)
            with self.assertRaises(ValueError):
                load(self.path)


if __name__ == '__main__':
    unittest.main()
