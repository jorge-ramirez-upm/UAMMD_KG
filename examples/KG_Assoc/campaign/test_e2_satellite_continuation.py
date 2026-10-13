"""CPU-only continuation graph capture and independent-history regression tests."""
import copy
from pathlib import Path
import tempfile
import sys
import unittest
from unittest import mock

from test_e2_g1 import fixture
import analyze_e2_satellite_continuation as satellite


class SatelliteContinuationTests(unittest.TestCase):
    def test_component_definition_includes_only_non_singleton_satellites(self):
        graph = dict(neighbor_degree={1: 2, 2: 2, 3: 2, 4: 1, 5: 1, 6: 0},
                     component_sizes=[3, 2, 1])
        original = copy.deepcopy(graph)
        metrics = satellite.graph_metrics(graph, 6, 3)
        self.assertEqual(metrics['satellite_components'], 1)
        self.assertEqual(metrics['satellite_stars'], 2)
        self.assertEqual(metrics['isolated_stars'], 1)
        self.assertEqual(metrics['degree_0_fraction'], 1/6)
        self.assertEqual(graph, original)
        graph['component_sizes'] = [1] * 6
        graph['neighbor_degree'] = {i: 0 for i in range(6)}
        self.assertEqual(satellite.graph_metrics(graph, 6, 3)['satellite_components'], 0)
        with self.assertRaises(ValueError):
            satellite.graph_metrics(graph, 7, 3)

    def test_seeded_continuation_uses_validator_and_restores_callback(self):
        with tempfile.TemporaryDirectory() as temp:
            entry = fixture(Path(temp), f=3, start=6000000)
            analysis = satellite.joint.segment.review.analysis
            original = analysis.topology.frame_observables
            def authenticate(root, attempts):
                rows, events, result = satellite.joint.runner.validation.validate(entry)
                return [dict(attempt='continuation', histories=[dict(entry=entry, rows=rows,
                    events=events, validation=result)])]
            with mock.patch.object(satellite.joint, 'authenticate', side_effect=authenticate):
                segments = satellite.authenticate_with_graphs(Path(temp), [])
            rows = segments[0]['histories'][0]['rows']
            self.assertEqual(rows[0]['step'], 6000000)
            self.assertEqual(rows[0]['isolated_stars'], 14)
            self.assertEqual(rows[1]['isolated_stars'], 16)
            self.assertIs(analysis.topology.frame_observables, original)
            with mock.patch.object(satellite.joint, 'authenticate', side_effect=ValueError('bad parent')):
                with self.assertRaisesRegex(ValueError, 'bad parent'):
                    satellite.authenticate_with_graphs(Path(temp), [])
            self.assertIs(analysis.topology.frame_observables, original)

    def test_existing_output_is_never_overwritten_or_reauthenticated(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'immutable.json'
            output.write_bytes(b'original evidence')
            args = ['satellite', '--dataset-root', temp, '--attempt', temp,
                    '--output', str(output)]
            with mock.patch.object(sys, 'argv', args), \
                    mock.patch.object(satellite, 'authenticate_with_graphs') as authenticate:
                with self.assertRaisesRegex(ValueError, 'immutable output'):
                    satellite.main()
                authenticate.assert_not_called()
            self.assertEqual(output.read_bytes(), b'original evidence')

    def test_window_cannot_cross_reseed_and_pairing_is_three_histories(self):
        history = dict(entry=dict(start_step=6000000, end_step=8000000))
        with self.assertRaisesRegex(ValueError, 'restart boundary'):
            satellite.make_window({}, history, 5500000, 6500000)
        summary = dict(windows_steps=500000, records=[dict(replica=r, windows=[dict(
            start_step_exclusive=i*500000, end_step_inclusive=(i+1)*500000,
            segment='original' if i < 12 else 'continuation',
            metrics={'satellite_stars': dict(mean=i*r)}, activity={})
            for i in range(16)]) for r in (1, 2, 3)])
        original = copy.deepcopy(summary)
        result = satellite.sensitivity.summarize(summary, satellite.PAIRS)
        self.assertEqual(result, satellite.sensitivity.summarize(summary, satellite.PAIRS))
        self.assertEqual(summary, original)
        self.assertTrue(all(c['replicas'] == 3 for c in result['comparisons']))
        self.assertFalse(result['automatic_acceptance'])
        with self.assertRaisesRegex(ValueError, 'continuous segment'):
            satellite.sensitivity.summarize(summary, [((5500000, 6500000), (6500000, 7500000))])


if __name__ == '__main__':
    unittest.main()
