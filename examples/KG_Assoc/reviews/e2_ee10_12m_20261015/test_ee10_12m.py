"""CPU-only segment/replica guards for the joint Ee10 review."""
import copy
import csv
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import reproduce_ee10_12m as review


def sources():
    result = [dict(attempt='old', plan=dict(smoke=False, parent_attempt=None,
        system=dict(system_id='F04_N010_RP080_EE10_EA04')), histories=[]),
        dict(attempt='new', plan=dict(smoke=False, parent_attempt='old',
        system=dict(system_id='F04_N010_RP080_EE10_EA04')), histories=[])]
    fields = ('free', 'bonds', 'intra', 'inter', 'L1', 'L2', 'components',
              'largest_size', 'creations', 'breaks')
    for replica in (1, 2, 3):
        for index, (start, end) in enumerate(((0, 8000000), (8000000, 12000000))):
            prefix = ('old' if index == 0 else 'new') + '/r%03d/state' % replica
            result[index]['histories'].append(dict(entry=dict(replica=replica,
                start_step=start, end_step=end, chemistry_seed=400 + replica,
                md_seed=10 + replica + 100 * index,
                effective_md_seed=1000 + replica + 100 * index, physics={},
                output_prefix=prefix, parent=dict(prefix='old/r%03d/state' % replica)),
                rows=[dict.fromkeys(fields, 0)], events=[]))
    return result


class Joint12mTests(unittest.TestCase):
    def test_complete_exports_conserve_multigraph_and_peripheral_populations(self):
        directory = Path(review.__file__).parent / 'evidence'
        for replica in (1, 2, 3):
            with (directory / f'r{replica:03d}_frames.csv').open() as stream:
                rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)]
            self.assertEqual([int(r['step']) for r in rows], list(range(0, 12000001, 1000)))
            self.assertEqual(rows[0]['bonds'], 0)
            for row in rows:
                self.assertEqual(row['inter'], sum(k * row[f'edges_m{k}'] for k in range(1, 5)))
                self.assertEqual(row['L1'], sum(k * (k - 1) / 2 * row[f'edges_m{k}']
                                              for k in range(1, 5)))
                self.assertEqual(row['intra'], row['stars_intra_loops_1'] +
                                 2 * row['stars_intra_loops_2'])
                self.assertEqual(sum(row[f'stars_intra_loops_{k}'] for k in range(3)), 1000)
                self.assertGreaterEqual(row['isolated_stars'], row['stars_intra_loops_2'])
                self.assertAlmostEqual(500 * row['mean_degree'],
                                       sum(row[f'edges_m{k}'] for k in range(1, 5)))
                self.assertAlmostEqual(sum(row[f'degree_{k}_fraction'] for k in range(5)), 1)
                self.assertAlmostEqual(sum(k * k * row[f'degree_{k}_fraction'] for k in range(5)),
                                       row['second_degree_moment'])
                if row['step'] > 0:
                    self.assertAlmostEqual(row['components'],
                        1 + row['isolated_stars'] + row['satellite_components'])
                    self.assertAlmostEqual(1000 * (1 - row['largest_cluster_fraction']),
                        row['isolated_stars'] + row['satellite_stars'])

    def test_boundary_never_stitches_correlation_windows(self):
        data = sources()
        self.assertIs(review.local_source(data, 1, 4000000, 8000000)[0], data[0])
        self.assertIs(review.local_source(data, 1, 8000000, 12000000)[0], data[1])
        for interval in ((7000000, 9000000), (7750000, 8250000)):
            with self.assertRaisesRegex(ValueError, 'reseeding boundary'):
                review.local_source(data, 1, *interval)
        for pair in review.PAIRS:
            for interval in pair:
                review.local_source(data, 1, *interval)
                self.assertGreaterEqual(interval[0], 0)

    def test_pairing_preserves_three_history_changes(self):
        records = [dict(replica=r, windows=[dict(start_step_exclusive=a,
            end_step_inclusive=b, metrics={'shape': dict(mean=value)}, activity={})
            for a, b, value in ((4000000, 8000000, old),
                                (8000000, 12000000, old + change))])
            for r, old, change in ((1, 10, -1), (2, 100, 2), (3, 1000, 3))]
        before = copy.deepcopy(records)
        result = review.compare(records, (4000000, 8000000), (8000000, 12000000))[0]
        self.assertEqual(result['per_replica_changes'], [-1, 2, 3])
        self.assertEqual(result['replicas'], 3)
        self.assertAlmostEqual(result['mean'], 4 / 3)
        self.assertEqual(records, before)
        with self.assertRaisesRegex(ValueError, 'three original'):
            review.compare(records + [records[0]], (4000000, 8000000), (8000000, 12000000))

    def test_existing_output_cannot_authenticate_or_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'evidence'
            output.write_text('immutable')
            with mock.patch.object(sys, 'argv', ['review', '--output', str(output)]), \
                 mock.patch.object(review, 'authenticate') as authenticate:
                with self.assertRaisesRegex(ValueError, 'immutable'):
                    review.main()
                authenticate.assert_not_called()
            self.assertEqual(output.read_text(), 'immutable')

    def test_wrong_endpoint_scope_cannot_create_output(self):
        data = sources()
        data[1]['histories'][0]['entry']['end_step'] = 9000000
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'new'
            with self.assertRaisesRegex(ValueError, 'exact 0–8M'):
                review.write_evidence(data, output)
            self.assertFalse(output.exists())

    def test_metric_selection_is_restored_on_estimation_failure(self):
        data = sources()
        original = review.joint.segment.METRICS
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(
                review.previous, 'fresh_window', side_effect=ValueError('injected failure')):
            with self.assertRaisesRegex(ValueError, 'injected failure'):
                review.write_evidence(data, Path(temp) / 'new')
        self.assertIs(review.joint.segment.METRICS, original)


class AdditionalGuards(unittest.TestCase):
    def test_descriptive_correlations_handle_constant_and_algebraic_cases(self):
        import tabulate_ee10_12m as tables
        self.assertEqual(tables.pearson([1, 2, 3], [3, 2, 1]), -1)
        self.assertEqual(tables.pearson([1, 2, 3], [2, 4, 6]), 1)
        self.assertIsNone(tables.pearson([1, 1, 1], [2, 3, 4]))
        with self.assertRaisesRegex(ValueError, 'coverage'):
            tables.pearson([1, 2], [1, 2, 3])

    def test_exact_old_estimates_are_reused_and_new_estimates_stay_local(self):
        import json
        directory = Path(review.__file__).parent / 'evidence'
        summary = json.loads((directory / 'summary.json').read_text())
        old = json.loads((review.OLD_REVIEW / 'evidence/summary.json').read_text())
        for record in summary['records']:
            for window in record['windows']:
                start, end = window['start_step_exclusive'], window['end_step_inclusive']
                self.assertFalse(start < 8000000 < end)
                if end <= 8000000:
                    match = next(w for w in old['records'][record['replica'] - 1]['windows']
                        if (w['start_step_exclusive'], w['end_step_inclusive']) == (start, end))
                    for key in ('metrics', 'activity', 'exposure'):
                        self.assertEqual(window[key], match[key])
                    self.assertIn('statistics_source', window)
                else:
                    self.assertNotIn('statistics_source', window)

    def test_current_checkpoint_statistics_match_roundoff(self):
        import json
        import math
        directory = Path(review.__file__).parent / 'evidence'
        summary = json.loads((directory / 'summary.json').read_text())
        checkpoint = review.ROOT / 'aggregate/e2/review_a3c9091ae9cf452fbf13bdd18f534aba'
        old = json.loads((checkpoint / 'summary.json').read_text())
        for record, prior in zip(summary['records'], old['records']):
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


if __name__ == '__main__':
    unittest.main()
