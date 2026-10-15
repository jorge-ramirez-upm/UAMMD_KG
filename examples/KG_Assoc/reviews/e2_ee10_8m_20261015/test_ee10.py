"""CPU regressions for exact scope, full transient context and paired evidence."""
import copy
import csv
import json
import math
from pathlib import Path
import statistics
import tempfile
import unittest
from unittest import mock

import reproduce_ee10 as review


class ReviewTests(unittest.TestCase):
    def test_qualified_ee8_reference_uses_only_corrected_windows_and_same_other_physics(self):
        directory = Path(review.__file__).parent
        authentication = json.loads((directory / 'AUTHENTICATION.json').read_text())
        provenance = json.loads((directory / 'evidence/provenance.json').read_text())
        reference = authentication['reference_record']['record']
        self.assertEqual(reference['status'], 'accepted_with_qualification')
        self.assertEqual(reference['permitted_use'], 'production_initial_state')
        physics = dict(provenance['source_plan']['histories'][0]['physics'], Ee=8)
        comparison = json.loads((directory / 'evidence/EE8_COMPARISON.json').read_text())
        self.assertEqual(comparison['interval'], [6000000, 8000000])
        for history, old, result in zip(reference['histories'], authentication['reference_windows'],
                                        comparison['records']):
            self.assertEqual(history['physics'], physics)
            self.assertEqual([(w['start_step_exclusive'], w['end_step_inclusive'])
                              for w in old['windows']],
                             [(a, a + 500000) for a in range(6000000, 8000000, 500000)])
            for name, count in result['event_counts'].items():
                self.assertEqual(count, sum(w['event_counts'][name] for w in old['windows']))
                self.assertEqual(result['activity'][name], count / 20000)

    def test_preserved_sources_and_execution_receipts_authenticate(self):
        review.verify_inputs()

    def test_wrong_scope_never_creates_output(self):
        source = dict(plan=dict(smoke=False, system=dict(system_id=review.SYSTEM)),
                      histories=[dict(entry=dict(replica=r, start_step=0, end_step=8000000))
                                 for r in (1, 2, 3)])
        for system, end in ((review.SYSTEM, 4000000), ('F04_N010_RP080_EE08_EA04', 8000000)):
            candidate = copy.deepcopy(source)
            candidate['plan']['system']['system_id'] = system
            candidate['histories'][0]['entry']['end_step'] = end
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'new'
                with self.assertRaisesRegex(ValueError, 'exact Ee10'):
                    review.write_evidence(candidate, output)
                self.assertFalse(output.exists())

    def test_all_nonoverlapping_context_scales_are_compared(self):
        for width in (500000, 1000000, 2000000):
            for start in range(0, 8000000 - 2 * width + 1, width):
                self.assertIn(((start, start + width), (start + width, start + 2 * width)),
                              review.PAIRS)

    def test_three_paired_units_even_when_frame_uncertainty_is_tiny(self):
        records = []
        for replica, delta in enumerate((1., 2., 9.), 1):
            windows = [dict(start_step_exclusive=a, end_step_inclusive=b,
                            metrics=dict(L1=dict(mean=value)), activity={})
                       for a, b, value in ((4000000, 6000000, 10.),
                                           (6000000, 8000000, 10. + delta))]
            records.append(dict(replica=replica, windows=windows))
        result = review.reused.compare(records, (4000000, 6000000), (6000000, 8000000))[0]
        self.assertEqual(result['per_replica_changes'], [1., 2., 9.])
        self.assertEqual(result['mean'], 4.)
        expected = review.joint.segment.review.analysis.dynamics.replica_statistics([1., 2., 9.])
        self.assertEqual(result['ci95_half_width'], expected['ci95_half_width'])
        with self.assertRaisesRegex(ValueError, 'three original'):
            review.reused.compare(records[:2], (4000000, 6000000), (6000000, 8000000))

    def test_graph_callback_restored_on_authentication_failure(self):
        topology = review.reused.multigraph.analysis.topology
        original = topology.frame_observables
        with mock.patch.object(review.joint.campaign, 'sha256', return_value=review.PLAN_HASH), \
             mock.patch.object(review.reused.graph, 'authenticate_with_graphs',
                               side_effect=ValueError('bad source')):
            with self.assertRaisesRegex(ValueError, 'bad source'):
                review.authenticate()
        self.assertIs(topology.frame_observables, original)

    def test_existing_output_does_not_authenticate(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch('sys.argv', ['review', '--output', temporary]), \
                 mock.patch.object(review, 'authenticate') as authenticate:
                with self.assertRaisesRegex(ValueError, 'immutable'):
                    review.main()
                authenticate.assert_not_called()

    def test_checkpoint_estimates_match_at_roundoff_precision(self):
        directory = Path(review.__file__).parent / 'evidence'
        fresh = json.loads((directory / 'summary.json').read_text())
        checkpoint = review.CHECKPOINT
        old = json.loads((checkpoint / 'summary.json').read_text())
        for record, prior in zip(fresh['records'], old['records']):
            for before in prior['windows']:
                after = next(w for w in record['windows'] if
                    (w['start_step_exclusive'], w['end_step_inclusive']) ==
                    (before['start_step_exclusive'], before['end_step_inclusive']))
                for category in ('metrics', 'activity'):
                    for name, values in before[category].items():
                        for key in ('mean', 'tau_time', 'effective_samples_estimate', 'slope',
                                    'sem_estimate', 'blocking_sem_sensitivity', 'blocks'):
                            a, b = after[category][name][key], values[key]
                            left = list(a.values()) if isinstance(a, dict) else (
                                a if isinstance(a, list) else [a])
                            right = list(b.values()) if isinstance(b, dict) else (
                                b if isinstance(b, list) else [b])
                            self.assertEqual(len(left), len(right))
                            self.assertTrue(all(math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12)
                                                for x, y in zip(left, right)))

    def test_exported_full_context_and_distribution_accounting(self):
        directory = Path(review.__file__).parent / 'evidence'
        summary = json.loads((directory / 'summary.json').read_text())
        self.assertEqual([r['replica'] for r in summary['records']], [1, 2, 3])
        for record in summary['records']:
            with (directory / ('r%03d_frames.csv' % record['replica'])).open() as stream:
                rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(stream)]
            self.assertEqual([int(r['step']) for r in rows], list(range(0, 8000001, 1000)))
            self.assertEqual(rows[0]['bonds'], 0)
            for row in rows:
                self.assertEqual(row['inter'], sum(k * row[f'edges_m{k}'] for k in range(1, 5)))
                self.assertEqual(row['L1'], sum(k * (k - 1) / 2 * row[f'edges_m{k}']
                                              for k in range(1, 5)))
                self.assertEqual(row['intra'], row['stars_intra_loops_1'] +
                                 2 * row['stars_intra_loops_2'])
                self.assertAlmostEqual(sum(row[f'degree_{k}_fraction'] for k in range(5)), 1.)
                if row['step'] > 0:
                    self.assertEqual(row['components'],
                                     1 + row['isolated_stars'] + row['satellite_components'])
                    self.assertAlmostEqual(1000 * (1 - row['largest_cluster_fraction']),
                                           row['isolated_stars'] + row['satellite_stars'])
            for window in record['windows']:
                selected = [r for r in rows if window['start_step_exclusive'] < r['step'] <=
                            window['end_step_inclusive']]
                for name, value in window['metrics'].items():
                    self.assertEqual(statistics.mean(r[name] for r in selected), value['mean'])


if __name__ == '__main__':
    unittest.main()
