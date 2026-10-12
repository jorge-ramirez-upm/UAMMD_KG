"""Deterministic joint-review bookkeeping fixtures; no GPU or convergence claims."""
import copy
from pathlib import Path
import tempfile
import unittest

from test_e2_g1 import fixture
import kg_assoc_e2 as e2
import analyze_joint_e2 as joint


class JointReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.sources = [dict(attempt=str(root / 'first'), plan=dict(smoke=False, system={}, parent_attempt=None), histories=[]),
                        dict(attempt=str(root / 'second'), plan=dict(smoke=False, system={}, parent_attempt=str(root / 'first')), histories=[])]
        for replica in (1, 2, 3):
            first = fixture(root / f'first_{replica}')
            second = fixture(root / f'second_{replica}', start=12000)
            old_rows, old_events, _ = e2.validation.validate(first)
            rows, events, _ = e2.validation.validate(second)
            # Fixture histories are bookkeeping replicas, not simulated independent samples.
            for entry in (first, second):
                entry['replica'] = replica
                entry['chemistry_seed'] = 420000 + replica
            second['md_seed'] += 100
            second['effective_md_seed'] = e2.validation.effective_md_seed(second['md_seed'])
            second['parent']['prefix'] = first['output_prefix']
            for field in ('creations', 'breaks'):
                offset = old_rows[-1][field] - rows[0][field]
                for row in rows:
                    row[field] += offset
            self.sources[0]['histories'].append(dict(entry=first, rows=old_rows, events=old_events))
            self.sources[1]['histories'].append(dict(entry=second, rows=rows, events=events))

    def test_restart_boundary_keeps_histories_and_windows_separate(self):
        summary = joint.summarize(self.sources, 6000)
        self.assertEqual(len(summary['records']), 3)
        windows = summary['records'][0]['windows']
        self.assertEqual([(w['start_step_exclusive'], w['end_step_inclusive']) for w in windows],
                         [(0, 6000), (6000, 12000), (12000, 18000), (18000, 24000)])
        self.assertFalse(summary['automatic_acceptance'])
        self.assertEqual(summary['scientific_status'], 'review_required')
        self.assertTrue(windows[0]['metrics']['L2']['constant_not_mixing_evidence'])
        self.assertTrue(windows[0]['metrics']['L2']['resolution_warning'])
        self.assertEqual(summary['late_segment_long_windows'][0]['window']['start_step_exclusive'], 12000)

    def test_seed_parent_step_boundary_and_replica_mismatches_fail(self):
        mutations = [('chemistry_seed', 1), ('md_seed', self.sources[0]['histories'][0]['entry']['md_seed']),
                     ('start_step', 11000)]
        for field, value in mutations:
            with self.subTest(field=field):
                sources = copy.deepcopy(self.sources)
                sources[1]['histories'][0]['entry'][field] = value
                with self.assertRaises(ValueError):
                    joint.check_lineage(sources)
        sources = copy.deepcopy(self.sources)
        sources[1]['histories'][0]['rows'][0]['L2'] += 1
        with self.assertRaisesRegex(ValueError, 'boundary state'):
            joint.check_lineage(sources)
        sources[1]['histories'].pop()
        with self.assertRaisesRegex(ValueError, 'three ordinary'):
            joint.check_lineage(sources)

    def test_pairing_uses_three_replica_changes_not_frames(self):
        records = [dict(windows=[dict(metrics={'L2': dict(mean=old)}),
                                 dict(metrics={'L2': dict(mean=new)})])
                   for old, new in ((10, 7), (20, 18), (30, 28))]
        result = joint.compare(records, 'metrics', 'L2', 0, 1)
        self.assertEqual(result['per_replica_changes'], [-3, -2, -2])
        self.assertEqual(result['replicas'], 3)
        self.assertLess(result['mean'], 0)
        self.assertTrue(result['excludes_zero'])

    def test_report_no_overwrite_and_no_automatic_acceptance(self):
        output = Path(self.temp.name) / 'report'
        summary = joint.summarize(self.sources, 6000)
        joint.write_report(summary, output)
        before = (output / 'REPORT.md').read_bytes()
        with self.assertRaises(FileExistsError):
            joint.write_report(summary, output)
        self.assertEqual((output / 'REPORT.md').read_bytes(), before)
        self.assertFalse(list(output.glob('*acceptance*')))


if __name__ == '__main__':
    unittest.main()
