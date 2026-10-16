"""CPU-only segment/replica guards for the joint Ee12 review."""
import copy
import csv
import re
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import reproduce_ee12_20m as review


def sources():
    result = [dict(attempt='old', plan=dict(smoke=False, parent_attempt=None,
        system=dict(system_id='F04_N010_RP080_EE12_EA04')), histories=[]),
        dict(attempt='new', plan=dict(smoke=False, parent_attempt='old',
        system=dict(system_id='F04_N010_RP080_EE12_EA04')), histories=[])]
    fields = ('free', 'bonds', 'intra', 'inter', 'L1', 'L2', 'components',
              'largest_size', 'creations', 'breaks')
    for replica in (1, 2, 3):
        for index, (start, end) in enumerate(((0, 16000000), (16000000, 20000000))):
            prefix = ('old' if index == 0 else 'new') + '/r%03d/state' % replica
            result[index]['histories'].append(dict(entry=dict(replica=replica,
                start_step=start, end_step=end, chemistry_seed=400 + replica,
                md_seed=10 + replica + 100 * index,
                effective_md_seed=1000 + replica + 100 * index, physics={},
                output_prefix=prefix, parent=dict(prefix='old/r%03d/state' % replica)),
                rows=[dict.fromkeys(fields, 0)], events=[]))
    return result


class Joint20mTests(unittest.TestCase):
    def test_complete_exports_conserve_multigraph_and_peripheral_populations(self):
        directory = Path(review.__file__).parent / 'evidence'
        for replica in (1, 2, 3):
            with (directory / f'r{replica:03d}_frames.csv').open() as stream:
                rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)]
            self.assertEqual([int(r['step']) for r in rows], list(range(0, 20000001, 1000)))
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
        self.assertIs(review.local_source(data, 1, 12000000, 16000000)[0], data[0])
        self.assertIs(review.local_source(data, 1, 16000000, 20000000)[0], data[1])
        for interval in ((15000000, 17000000), (15750000, 16250000)):
            with self.assertRaisesRegex(ValueError, 'reseeding boundary'):
                review.local_source(data, 1, *interval)
        for pair in review.PAIRS:
            for interval in pair:
                review.local_source(data, 1, *interval)
                self.assertGreaterEqual(interval[0], 0)

    def test_pairing_preserves_three_history_changes(self):
        records = [dict(replica=r, windows=[dict(start_step_exclusive=a,
            end_step_inclusive=b, metrics={'shape': dict(mean=value)}, activity={})
            for a, b, value in ((12000000, 16000000, old),
                                (16000000, 20000000, old + change))])
            for r, old, change in ((1, 10, -1), (2, 100, 2), (3, 1000, 3))]
        before = copy.deepcopy(records)
        result = review.compare(records, (12000000, 16000000), (16000000, 20000000))[0]
        self.assertEqual(result['per_replica_changes'], [-1, 2, 3])
        self.assertEqual(result['replicas'], 3)
        self.assertAlmostEqual(result['mean'], 4 / 3)
        self.assertEqual(records, before)
        with self.assertRaisesRegex(ValueError, 'three original'):
            review.compare(records + [records[0]], (12000000, 16000000), (16000000, 20000000))

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
        data[1]['histories'][0]['entry']['end_step'] = 17000000
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'new'
            with self.assertRaisesRegex(ValueError, 'exact 0–16M'):
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
        import tabulate_ee12_20m as tables
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
                self.assertFalse(start < 16000000 < end)
                if end <= 16000000:
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
        checkpoint = review.ROOT / 'aggregate/e2/review_ff92b2fc3f5342ae9fd2409391d39c4c'
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
                            if key == 'effective_samples_estimate' and values[key] is None:
                                self.assertTrue(after[category][name]['constant_not_mixing_evidence'])
                                self.assertTrue(after[category][name]['resolution_warning'])
                                continue
                            a, b = after[category][name][key], values[key]
                            left = list(a.values()) if isinstance(a, dict) else (
                                a if isinstance(a, list) else [a])
                            right = list(b.values()) if isinstance(b, dict) else (
                                b if isinstance(b, list) else [b])
                            self.assertEqual(len(left), len(right))
                            self.assertTrue(all(math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12)
                                                for x, y in zip(left, right)))


class PeripheralAndAuthenticationTests(unittest.TestCase):
    def test_component_memberships_separate_isolates_satellites_and_giant(self):
        neighbors = {1: {2}, 2: {1, 3}, 3: {2}, 5: {6}, 6: {5}, 9: set()}
        graph = dict(neighbors=neighbors, component_sizes=[3, 2, 1],
                     neighbor_degree={star: len(n) for star, n in neighbors.items()})
        self.assertEqual(review.peripheral_membership(graph),
                         dict(isolated=[9], satellites=[[5, 6]]))
        graph['component_sizes'] = [3, 3]
        with self.assertRaisesRegex(ValueError, 'membership sizes'):
            review.peripheral_membership(graph)

    def test_all_tilings_and_peripheral_identities_match_full_frames(self):
        directory = Path(review.__file__).parent / 'evidence'
        summary = review.joint.campaign.load_json(directory / 'summary.json')
        captured = review.joint.campaign.load_json(directory / 'PERIPHERAL_FRAMES.json')
        for record, peripheral in zip(summary['records'], captured['records']):
            intervals = {(w['start_step_exclusive'], w['end_step_inclusive']) for w in record['windows']}
            for width, count in zip(review.WIDTHS, (40, 20, 10, 5)):
                tiled = {(a, a + width) for a in range(0, 20000000, width)}
                self.assertEqual(len(tiled), count)
                self.assertTrue(tiled <= intervals)
            with (directory / f"r{record['replica']:03d}_frames.csv").open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(peripheral['frames']), 20001)
            for captured_row, row in zip(peripheral['frames'], rows):
                self.assertEqual(captured_row['step'], int(float(row['step'])))
                self.assertEqual(len(captured_row['isolated']), float(row['isolated_stars']))
                self.assertEqual(len(captured_row['satellites']), float(row['satellite_components']))
                self.assertEqual(sum(map(len, captured_row['satellites'])), float(row['satellite_stars']))
                self.assertFalse(set(captured_row['isolated']) &
                    {star for component in captured_row['satellites'] for star in component})

    def test_boundary_identity_receipts_and_protected_evidence(self):
        review.verify_inputs()
        directory = Path(review.__file__).parent / 'evidence'
        provenance = review.joint.campaign.load_json(directory / 'provenance.json')
        self.assertFalse(provenance['formal_acceptance'])
        sources = provenance['source_authentication']
        self.assertIn('binary_bytes_not_reauthenticated', sources[0]['build_authentication_scope'])
        self.assertEqual(sources[1]['build_authentication_scope'], 'current_binary_hashes_authenticated')
        boundary = review.joint.campaign.load_json(directory / 'BOUNDARY.json')['records']
        for index, row in enumerate(boundary):
            self.assertEqual(row['absolute_step'], 16000000)
            self.assertFalse(row['bitwise_md_continuation'])
            self.assertEqual(row['chemical_seed'], 420801 + index)
            self.assertEqual(row['new_md_seed'], 520130 + index)
            self.assertEqual(row['new_effective_md_seed'], (3381585552, 3373217424, 3398338192)[index])
            new = sources[1]['histories'][index]['entry']
            _, initial = review.joint.runner.validation.read_parent(new)
            self.assertEqual([list(pair) for pair in initial['pairs']], row['partners'])
            self.assertEqual(initial['creations'], row['creations'])
            self.assertEqual(initial['breaks'], row['breaks'])
        for source in sources:
            for history in source['histories']:
                path = Path(history['entry']['output_prefix']).parent / 'complete.json'
                self.assertEqual(review.joint.campaign.load_json(path)['validation'], history['validation'])
        self.assertEqual([p['end_step'] for p in provenance['proposed_endpoints']], [20000000] * 3)
        self.assertEqual(len(list((review.ROOT / 'banks/e2_acceptance').glob('*.json'))), 11)
        self.assertFalse((review.ROOT / 'banks/e2_registry').exists())
        self.assertIn('hold', (review.OLD_REVIEW / 'ASSESSMENT.md').read_text().lower())

    def test_satellite_topology_replay_preserves_parallel_edges_and_loops(self):
        import tabulate_ee12_20m as tables
        system = dict(atom_to_star={1: 10, 2: 20, 3: 10, 4: 20,
                                    5: 10, 6: 20, 7: 10, 8: 10})
        old_events = [(100, 'C', (1, 2)), (200, 'C', (3, 4))]
        new_events = [(16000100, 'C', (5, 6)), (17000100, 'B', (1, 2)),
                      (17000200, 'C', (7, 8))]
        provenance = dict(source_authentication=[dict(histories=[dict(entry=dict(output_prefix=p))])
                                                for p in ('old', 'new')])
        captured = dict(records=[dict(replica=1, frames=[dict(step=step, satellites=[[10, 20]])
            for step in (16000000, 16500000, 17500000)])])
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            review.joint.runner.exclusive_json(directory / 'provenance.json', provenance)
            with mock.patch.object(review.joint.runner.validation, 'read_parent',
                    return_value=(system, {})), mock.patch.object(
                    review.joint.segment.review.analysis.dynamics, 'read_events',
                    side_effect=[({}, old_events), ({}, new_events)]):
                tables.satellite_topologies(directory, captured)
            output = review.joint.campaign.load_json(directory / 'SATELLITE_TOPOLOGY.json')
            rows = output['records'][0]['observations']
            self.assertEqual([r['inter_edges'] for r in rows],
                             [[[10, 20, 2]], [[10, 20, 3]], [[10, 20, 2]]])
            self.assertEqual(rows[-1]['intra_loops'], {'10': 1, '20': 0})

    def test_endpoint_markdown_matches_exact_parent_final_pairs_and_receipts(self):
        directory = Path(review.__file__).parent
        provenance = review.joint.campaign.load_json(directory / 'evidence/provenance.json')
        text = (directory / 'ENDPOINTS.md').read_text()
        for old, new in zip(provenance['source_authentication'][0]['histories'],
                            provenance['source_authentication'][1]['histories']):
            entry = new['entry']
            section = text.split(f"## r{entry['replica']:03d}\n", 1)[1].split('\n## ', 1)[0]
            self.assertIn(entry['output_prefix'], section)
            self.assertIn(old['entry']['output_prefix'], section)
            for step, source in ((16, old), (20, new)):
                for suffix in ('.restart.lammpsdat', '.assoc_restart'):
                    digest = re.search(r'\| ' + str(step) + r'M `state' + re.escape(suffix) +
                        r'` \| `([0-9a-f]{64})` \|', section).group(1)
                    self.assertEqual(digest, source['validation']['output_sha256'][suffix])
                    review.joint.runner.check_hashes({source['entry']['output_prefix'] + suffix: digest})
            receipt = Path(entry['output_prefix']).parent / 'complete.json'
            self.assertIn(review.joint.campaign.sha256(receipt), section)

    def test_isolation_diagnostics_are_observed_residence_not_stitched_lifetimes(self):
        directory = Path(review.__file__).parent / 'evidence'
        data = review.joint.campaign.load_json(directory / 'ISOLATION.json')
        self.assertIn('not a stitched bond lifetime', data['definitions'])
        for record in data['records']:
            for interval in record['intervals']:
                self.assertAlmostEqual(interval['time_averaged_isolated_stars'],
                    sum(s['overlap_steps'] for s in interval['spells']) /
                    (interval['end_step'] - interval['start_step']))
                for spell in interval['spells']:
                    self.assertEqual(spell['crosses_md_reseeding'], spell['start'] < 16000000 < spell['end'])


if __name__ == '__main__':
    unittest.main()
