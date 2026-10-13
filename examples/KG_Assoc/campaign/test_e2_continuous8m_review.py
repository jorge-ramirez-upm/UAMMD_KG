"""CPU guards for 8M review scope, independent units and immutable outputs."""
from pathlib import Path
import copy
import sys
import tempfile
import unittest
from unittest import mock

import test_e2_continuous_review as continuous_tests
import analyze_e2_continuous8m_review as review


class Continuous8MTests(unittest.TestCase):
    def test_8m_scope_and_metric_restoration(self):
        fixture = continuous_tests.ContinuousReviewTests()
        with self.assertRaisesRegex(ValueError, '0–8M'):
            review.summarize(fixture.source())
        source = fixture.source(8000000)
        before = copy.deepcopy(source)
        metrics = review.joint.segment.METRICS
        with mock.patch.object(review.joint, 'summarize', side_effect=ValueError('stop')):
            with self.assertRaisesRegex(ValueError, 'stop'):
                review.summarize(source)
        self.assertIs(review.joint.segment.METRICS, metrics)
        self.assertEqual(source, before)

    def test_pairs_preserve_three_units_and_reject_gaps(self):
        summary = dict(windows_steps=500000, records=[dict(replica=r, windows=[dict(
            start_step_exclusive=i*500000, end_step_inclusive=(i+1)*500000,
            segment='continuous', metrics={'intra': dict(mean=r*i)}, activity={})
            for i in range(16)]) for r in (1, 2, 3)])
        result = review.continuous.graph_review.sensitivity.summarize(summary, review.PAIRS)
        self.assertTrue(all(c['replicas'] == 3 for c in result['comparisons']))
        self.assertFalse(result['automatic_acceptance'])
        self.assertTrue(any(c['overlapping_steps'] > 0 for c in result['comparisons']))
        self.assertTrue(all(min(interval) >= 2000000 for pair in review.PAIRS for interval in pair))
        summary['records'][0]['windows'].pop(13)
        with self.assertRaises(ValueError):
            review.continuous.graph_review.sensitivity.summarize(summary, review.PAIRS)

    def test_existing_output_and_wrong_plan_fail_before_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'plan.json').write_text('{}')
            output = root/'output'
            output.write_bytes(b'preserved')
            args = ['review', '--dataset-root', temp, '--attempt', temp,
                    '--plan-sha256', 'f'*64, '--output', str(output)]
            with mock.patch.object(sys, 'argv', args), mock.patch.object(
                    review.continuous.graph_review, 'authenticate_with_graphs') as auth:
                with self.assertRaisesRegex(ValueError, 'immutable'):
                    review.main()
                self.assertEqual(output.read_bytes(), b'preserved')
                args[-1] = str(root/'new')
                with self.assertRaisesRegex(ValueError, 'source plan hash'):
                    review.main()
                auth.assert_not_called()


    def test_real_dossier_bindings_and_catalog_recommendation(self):
        import json
        import hashlib
        import catalog_model
        root = Path(__file__).resolve().parents[3]
        dossier = root/'examples/KG_Assoc/reviews/e2_n40_8m_20261013'
        decision = json.loads((dossier/'decision.json').read_text())
        sid = 'F04_N040_RP080_EE08_EA04'
        self.assertFalse(decision['formal_acceptance'])
        selected = decision['systems'][sid]
        self.assertEqual(selected['end_step'], 8000000)
        self.assertEqual([e['replica'] for e in selected['proposed_endpoints']], [1, 2, 3])
        for path, digest in decision['evidence_sha256'].items():
            self.assertEqual(hashlib.sha256((root/path).read_bytes()).hexdigest(), digest)
        for e in selected['proposed_endpoints']:
            self.assertIn('equilibrate_0a6a37a1e8264ceabbeead5362d8423d', e['prefix'])
            self.assertEqual(e['end_step'], 8000000)
            for path, digest in e['state_sha256'].items():
                self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), digest)
        provenance = json.loads((dossier/'provenance.json').read_text())
        self.assertEqual(provenance['build_authentication_scope'], 'current_binary_hashes_authenticated')
        for key in ('formal_acceptance', 'registry_activation', 'production_authorization'):
            self.assertFalse(provenance[key])
        graph = catalog_model.Catalog(root, root/'examples/KG_Assoc/kg_assoc_100m').scan()
        system = next(s for s in graph['systems'] if s['system_id'] == sid)
        self.assertEqual(system['scientific'], selected['status'])
        self.assertFalse(any(a.get('data', {}).get('permitted_systems') == [sid]
                             for a in graph['acceptances']))


if __name__ == '__main__':
    unittest.main()
