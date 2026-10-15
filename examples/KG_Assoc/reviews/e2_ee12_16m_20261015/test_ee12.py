"""CPU-only scientific guards for the exact Ee12 16M review."""
import copy
import csv
from pathlib import Path
import sys
import statistics
import tempfile
import unittest
from unittest.mock import patch

import reproduce_ee12 as review
import tabulate_ee12 as tables

DIRECTORY = Path(review.__file__).parent


class Ee12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = review.joint.campaign.load_json(DIRECTORY / 'evidence/summary.json')

    def test_all_four_tilings_retain_preparation_and_three_units(self):
        self.assertEqual([r['replica'] for r in self.summary['records']], [1, 2, 3])
        self.assertFalse(self.summary['automatic_acceptance'])
        for record in self.summary['records']:
            intervals = {(w['start_step_exclusive'], w['end_step_inclusive'])
                         for w in record['windows']}
            for width, count in zip(review.WIDTHS, (32, 16, 8, 4)):
                tiled = [(a, a + width) for a in range(0, 16000000, width)]
                self.assertEqual(len(tiled), count)
                self.assertTrue(set(tiled) <= intervals)
        for pair in review.PAIRS:
            for start, end in pair:
                self.assertTrue(0 <= start < end <= 16000000)
        with self.assertRaisesRegex(ValueError, 'three original'):
            review.reused.compare(self.summary['records'][:2], (8000000, 12000000),
                                  (12000000, 16000000))
        comparison = next(c for c in self.summary['comparisons'] if
            c['observable'] == 'intra' and c['early_steps'] == [8000000, 12000000] and
            c['late_steps'] == [12000000, 16000000])
        self.assertEqual(comparison['replicas'], 3)
        self.assertLess(comparison['per_replica_changes'][1], 0)
        self.assertGreater(comparison['per_replica_changes'][2], 0)

    def test_full_frames_conserve_multiplicity_degree_loops_and_periphery(self):
        for replica in (1, 2, 3):
            with (DIRECTORY / f'evidence/r{replica:03d}_frames.csv').open() as stream:
                rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(stream)]
            self.assertEqual([int(r['step']) for r in rows], list(range(0, 16000001, 1000)))
            self.assertEqual(rows[0]['bonds'], 0)
            self.assertEqual(rows[0]['free'], 4000)
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
                    self.assertEqual(row['components'],
                        1 + row['isolated_stars'] + row['satellite_components'])
                    self.assertAlmostEqual(1000 * (1 - row['largest_cluster_fraction']),
                        row['isolated_stars'] + row['satellite_stars'])

    def test_checkpoint_agrees_with_fresh_scalar_estimates_and_counts(self):
        checkpoint = review.joint.campaign.load_json(review.CHECKPOINT / 'summary.json')
        for original, fresh in zip(checkpoint['records'], self.summary['records']):
            for old in original['windows']:
                new = next(w for w in fresh['windows'] if
                    (w['start_step_exclusive'], w['end_step_inclusive']) ==
                    (old['start_step_exclusive'], old['end_step_inclusive']))
                self.assertEqual(new['event_counts'], old['event_counts'])
                self.assertEqual(new['exposure'], old['exposure'])
                for category in ('metrics', 'activity'):
                    for name, estimate in old[category].items():
                        for key in ('mean', 'slope', 'tau_time', 'sem_estimate'):
                            self.assertAlmostEqual(estimate[key], new[category][name][key], delta=1e-12)
                        for blocks in ('5', '10', '20'):
                            self.assertAlmostEqual(estimate['blocking_sem_sensitivity'][blocks],
                                new[category][name]['blocking_sem_sensitivity'][blocks], delta=1e-12)

    def test_coarse_means_counts_and_exposures_match_disjoint_500k_windows(self):
        # This checks additive quantities only; IATs/SEMs must not be averaged.
        for record in self.summary['records']:
            for width in review.WIDTHS[1:]:
                for start in range(0, 16000000, width):
                    coarse = next(w for w in record['windows'] if
                        (w['start_step_exclusive'], w['end_step_inclusive']) == (start, start + width))
                    pieces = [w for w in record['windows'] if
                        start <= w['start_step_exclusive'] and w['end_step_inclusive'] <= start + width
                        and w['end_step_inclusive'] - w['start_step_exclusive'] == 500000]
                    self.assertEqual(len(pieces), width // 500000)
                    for category in ('metrics', 'activity'):
                        for name, value in coarse[category].items():
                            self.assertAlmostEqual(value['mean'], statistics.mean(
                                w[category][name]['mean'] for w in pieces), delta=1e-10)
                    for category in ('event_counts', 'exposure'):
                        for name, value in coarse[category].items():
                            self.assertEqual(value, sum(w[category][name] for w in pieces))

    def test_immutable_output_rejected_before_authentication(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'existing'
            path.write_text('immutable')
            with patch.object(sys, 'argv', ['review', '--output', str(path)]), \
                    patch.object(review, 'verify_inputs') as verify:
                with self.assertRaisesRegex(ValueError, 'immutable'):
                    review.main()
                verify.assert_not_called()
            self.assertEqual(path.read_text(), 'immutable')

    def test_wrong_plan_rejected_before_replay(self):
        with patch.object(review.joint.campaign, 'sha256', return_value='0' * 64), \
                patch.object(review.reused.graph, 'authenticate_with_graphs') as replay:
            with self.assertRaisesRegex(ValueError, 'source plan'):
                review.authenticate()
            replay.assert_not_called()

    def test_wrong_system_or_step_cannot_create_output(self):
        source = dict(plan=dict(system=dict(system_id=review.SYSTEM), smoke=False),
            attempt='fixture', histories=[dict(entry=dict(replica=r, start_step=0,
                end_step=16000000), rows=[{}]) for r in (1, 2, 3)])
        for change in ('system', 'step'):
            bad = copy.deepcopy(source)
            if change == 'system':
                bad['plan']['system']['system_id'] = 'F04_N010_RP080_EE10_EA04'
            else:
                bad['histories'][1]['entry']['end_step'] = 8000000
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'new'
                with self.assertRaisesRegex(ValueError, 'exact Ee12'):
                    review.write_evidence(bad, output)
                self.assertFalse(output.exists())

    def test_metric_estimator_restored_after_failure(self):
        source = dict(plan=dict(system=dict(system_id=review.SYSTEM), smoke=False),
            attempt='fixture', histories=[dict(entry=dict(replica=r, start_step=0,
                end_step=16000000), rows=[dict(edges_m1=0)]) for r in (1, 2, 3)])
        original = review.joint.segment.METRICS
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'new'
            with patch.object(review.reused.previous, 'fresh_window', side_effect=RuntimeError('fixture')):
                with self.assertRaisesRegex(RuntimeError, 'fixture'):
                    review.write_evidence(source, output)
            self.assertIs(review.joint.segment.METRICS, original)
            self.assertFalse(output.exists())

    def test_correlations_are_descriptive_and_constants_undefined(self):
        self.assertIsNone(tables.pearson([1, 1, 1, 1], [1, 2, 3, 4]))
        self.assertAlmostEqual(tables.pearson([1, 2, 3, 4], [4, 3, 2, 1]), -1)
        data = review.joint.campaign.load_json(DIRECTORY / 'evidence/CORRELATIONS.json')
        self.assertTrue(all(r['bins'] >= 4 for r in data['records']))
        self.assertIn('no frame/block p-values', data['interpretation'])

    def test_event_time_isolation_retains_subframe_exchanges_and_censoring(self):
        events = [(100, 'C', (1, 2)), (400, 'B', (1, 2)),
                  (600, 'C', (1, 2)), (900, 'B', (1, 2))]
        spells = tables.isolation_spells([10, 20], {1: 10, 2: 20}, events, 1000)
        for star in (10, 20):
            selected = [s for s in spells if s['star'] == star]
            self.assertEqual([(s['start'], s['end'], s['right_censored']) for s in selected],
                             [(0, 100, False), (400, 600, False), (900, 1000, True)])
            self.assertEqual(sum(s['end'] - s['start'] for s in selected), 400)
        with self.assertRaisesRegex(ValueError, 'negative'):
            tables.isolation_spells([10, 20], {1: 10, 2: 20}, [(100, 'B', (1, 2))], 1000)

    def test_preserved_evidence_reference_and_eleven_records_unchanged(self):
        review.verify_inputs()
        authentication = review.joint.campaign.load_json(DIRECTORY / 'AUTHENTICATION.json')
        self.assertEqual(len(authentication['prior_acceptance_sha256']), 11)
        self.assertEqual(len(authentication['preexisting_binary_replacements']), 6)
        provenance = review.joint.campaign.load_json(DIRECTORY / 'evidence/provenance.json')
        self.assertFalse(provenance['formal_acceptance'])
        self.assertEqual(provenance['build_authentication_scope'], 'current_binary_hashes_authenticated')
        self.assertEqual([h['end_step'] for h in provenance['proposed_endpoints']], [16000000] * 3)
        self.assertEqual([h['chemistry_seed'] for h in provenance['proposed_endpoints']],
                         [420801, 420802, 420803])
        self.assertEqual([h['md_seed'] for h in provenance['proposed_endpoints']], [520124, 520125, 520126])
        for history in provenance['validated_histories']:
            receipt = review.joint.campaign.load_json(
                Path(history['entry']['output_prefix']).parent / 'complete.json')
            self.assertEqual(receipt['validation'], history['validation'])
            self.assertEqual(receipt['plan_sha256'], review.PLAN_HASH)
        self.assertEqual(len(list((review.ROOT / 'banks/e2_acceptance').glob('*.json'))), 11)
        self.assertFalse((review.ROOT / 'banks/e2_registry').exists())


if __name__ == '__main__':
    unittest.main()
