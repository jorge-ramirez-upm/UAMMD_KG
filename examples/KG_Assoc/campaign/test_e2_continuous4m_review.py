"""CPU-only scope, immutability and independent-history guards for the 4M review."""
from pathlib import Path
import copy
import sys
import tempfile
import unittest
from unittest import mock

import analyze_e2_continuous4m_review as review


class Continuous4mTests(unittest.TestCase):
    def test_rejects_incomplete_or_extended_histories(self):
        for end in (3000000, 5000000):
            source = dict(plan=dict(smoke=False), histories=[dict(
                entry=dict(replica=r, start_step=0, end_step=end)) for r in (1, 2, 3)])
            with self.assertRaisesRegex(ValueError, '0–4M'):
                review.summarize(source)

    def test_no_overwrite_or_wrong_plan_before_authentication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / 'output'
            output.write_bytes(b'immutable')
            (root / 'plan.json').write_text('{}')
            args = ['review', '--dataset-root', temp, '--attempt', temp,
                    '--plan-sha256', 'f' * 64, '--output', str(output)]
            with mock.patch.object(sys, 'argv', args), mock.patch.object(
                    review.graph, 'authenticate_with_graphs') as auth:
                with self.assertRaisesRegex(ValueError, 'immutable'):
                    review.main()
                self.assertEqual(output.read_bytes(), b'immutable')
                args[-1] = str(root / 'new')
                with self.assertRaisesRegex(ValueError, 'source plan hash'):
                    review.main()
                auth.assert_not_called()

    def test_shifted_windows_are_paired_and_not_extra_replicates(self):
        summary = dict(windows_steps=500000, records=[dict(replica=r, windows=[dict(
            start_step_exclusive=i * 500000, end_step_inclusive=(i + 1) * 500000,
            segment='continuous', metrics={'shape': dict(mean=r * i)}, activity={})
            for i in range(8)]) for r in (1, 2, 3)])
        original = copy.deepcopy(summary)
        result = review.graph.sensitivity.summarize(summary, review.PAIRS)
        self.assertEqual(summary, original)
        self.assertTrue(all(c['replicas'] == 3 for c in result['comparisons']))
        self.assertFalse(result['automatic_acceptance'])
        self.assertTrue(any(c['overlapping_steps'] > 0 for c in result['comparisons']))
        self.assertTrue(all(c['early_steps'][0] >= 1000000 for c in result['comparisons']))


if __name__ == '__main__':
    unittest.main()
