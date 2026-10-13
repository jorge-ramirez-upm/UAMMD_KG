"""CPU-only guards for continuous 6M review and exact mean-window accounting."""
from pathlib import Path
import copy
import sys
import tempfile
import unittest
from unittest import mock

from test_e2_g1 import fixture
import analyze_e2_continuous_review as review


class ContinuousReviewTests(unittest.TestCase):
    def source(self, end=6000000):
        return dict(attempt='continuous', plan=dict(smoke=False, system={'f': 4}),
                    histories=[dict(entry=dict(replica=r, start_step=0, end_step=end)) for r in (1, 2, 3)])

    def test_exact_diagnostic_and_event_means_keep_source_unchanged(self):
        source = dict(attempt='segment')
        history = dict(entry=dict(start_step=0, end_step=8000, physics={'dt': .01}),
            rows=[dict(step=step, shape=step/1000) for step in range(0, 8001, 1000)],
            events=[dict(step=4000, type='C', neighbor_gain=1, neighbor_loss=0),
                    dict(step=4100, type='B', neighbor_gain=0, neighbor_loss=1)])
        original = copy.deepcopy(history)
        windows = review.mean_windows(source, history, ('shape',), 4000)
        self.assertEqual([w['metrics']['shape']['mean'] for w in windows], [2.5, 6.5])
        self.assertEqual(windows[0]['activity']['creations']['mean'], .025)
        self.assertEqual(windows[1]['activity']['breaks']['mean'], .025)
        self.assertEqual(history, original)
        history['rows'].pop(2)
        with self.assertRaisesRegex(ValueError, 'missing frame'):
            review.mean_windows(source, history, ('shape',), 4000)

    def test_exact_6m_scope_and_metric_restoration_on_failure(self):
        with self.assertRaisesRegex(ValueError, '0–6M'):
            review.summarize(self.source(5000000))
        source = self.source()
        original = review.joint.segment.METRICS
        with mock.patch.object(review.joint, 'summarize', side_effect=ValueError('fixture failure')):
            with self.assertRaisesRegex(ValueError, 'fixture failure'):
                review.summarize(source)
        self.assertIs(review.joint.segment.METRICS, original)
        source['histories'][0]['entry']['start_step'] = 2000000
        with self.assertRaises(ValueError):
            review.summarize(source)

    def test_no_overwrite_and_wrong_plan_fail_before_authentication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root/'output'
            output.write_bytes(b'immutable')
            plan = root/'plan.json'
            plan.write_text('{}')
            args = ['review', '--dataset-root', temp, '--attempt', temp,
                    '--plan-sha256', 'f'*64, '--output', str(output)]
            with mock.patch.object(sys, 'argv', args), \
                    mock.patch.object(review.graph_review, 'authenticate_with_graphs') as auth:
                with self.assertRaisesRegex(ValueError, 'immutable'):
                    review.main()
                self.assertEqual(output.read_bytes(), b'immutable')
                args[-1] = str(root/'new_output')
                with self.assertRaisesRegex(ValueError, 'source plan hash'):
                    review.main()
                auth.assert_not_called()

    def test_fractional_window_comparisons_preserve_three_histories(self):
        summary = dict(windows_steps=500000, records=[dict(replica=r, windows=[dict(
            start_step_exclusive=i*500000, end_step_inclusive=(i+1)*500000,
            segment='continuous', metrics={'mean_rg2': dict(mean=r*i)}, activity={})
            for i in range(12)]) for r in (1, 2, 3)])
        result = review.graph_review.sensitivity.summarize(summary, review.PAIRS)
        self.assertTrue(all(c['replicas'] == 3 for c in result['comparisons']))
        self.assertFalse(result['automatic_acceptance'])
        self.assertTrue(any(c['overlapping_steps'] > 0 for c in result['comparisons']))


if __name__ == '__main__':
    unittest.main()
