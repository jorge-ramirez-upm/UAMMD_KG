"""Exact Ee6 4M formal bindings, qualifications and immutable unselected state."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import kg_assoc_e2 as e2
import kg_assoc_e2_registry as registry
from catalog_model import Catalog


class Ee6AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[3]
        self.root = self.repo / 'examples/KG_Assoc/kg_assoc_100m'
        self.dossier = self.repo / 'examples/KG_Assoc/reviews/e2_ee6_formal_acceptance_20261014'
        self.registration = e2.campaign.load_json(self.dossier / 'REGISTRATION.json')
        self.path = self.repo / self.registration['acceptance']
        self.record = e2.campaign.load_json(self.path)
        self.sid = 'F04_N010_RP080_EE06_EA04'
        self.system = e2.system_by_id(self.sid)

    def test_exact_approved_endpoints_and_qualifications(self):
        record = self.record
        self.assertEqual(record['permitted_systems'], [self.sid])
        self.assertEqual(record['permitted_use'], 'production_initial_state')
        self.assertEqual(record['status'], 'accepted_with_qualification')
        self.assertEqual(e2.campaign.sha256(self.path), self.registration['acceptance_sha256'])
        self.assertEqual(record['source_plan_sha256'],
                         '20eb13c5047cfce5a26646adb95839b4b575d232943b2b4bf7c37c49b0e623c6')
        review = self.repo / 'examples/KG_Assoc/reviews/e2_ee6_4m_20261014'
        pins = e2.campaign.load_json(review / 'provenance.json')['proposed_endpoints']
        self.assertEqual(pins, self.registration['selected_endpoints'])
        sections = (review / 'ENDPOINTS.md').read_text()
        for history, pin in zip(record['histories'], pins):
            self.assertEqual(history['prefix'], pin['prefix'])
            self.assertEqual(history['end_step'], 4000000)
            self.assertIn('/equilibrate_c6051f0ca57140819c10ae01e63036b5/', history['prefix'])
            section = sections.split(f"## r{history['replica']:03d}\n", 1)[1].split('\n## ', 1)[0]
            for suffix in ('.restart.lammpsdat', '.assoc_restart'):
                digest = history['sha256'][history['prefix'] + suffix]
                self.assertEqual(digest, pin['state_sha256'][history['prefix'] + suffix])
                self.assertIn(f'| `state{suffix}` | `{digest}` |', section)
            self.assertTrue(all(history['sha256'][path] == digest
                                for path, digest in pin['state_sha256'].items()))
        registry.exclusive_validate(record, [self.system])
        for phrase in ('stationarity/decorrelation', '0.19%', '0.25%', 'r001',
                       'initialization bias', 'final 250k', 'global stationarity',
                       'Slow-shape sampling', 'block uncertainty', 'shifted comparisons',
                       'Historical E1 executable bytes', 'Rejected reaction opportunities',
                       'inter-diagnostic coordinates', 'no production launch authorization'):
            self.assertIn(phrase, record['qualification'])

    def test_prior_records_and_review_unchanged_no_overwrite_or_registry(self):
        self.assertEqual(len(self.registration['prior_acceptance_sha256']), 7)
        e2.check_hashes(self.registration['prior_acceptance_sha256'])
        e2.check_hashes(self.registration['scientific_dossier_sha256'])
        for flag in ('registry_activation', 'active_selection', 'registry_publication',
                     'production_preparation', 'production_authorization', 'trajectory_launched'):
            self.assertFalse(self.registration[flag])
        before = self.path.read_bytes()
        with patch.object(e2, 'verify', side_effect=AssertionError('must fail first')), \
                patch.object(registry, 'publish', side_effect=AssertionError('forbidden')):
            with self.assertRaisesRegex(ValueError, 'new acceptance filename'):
                registry.accept(self.root, self.path, None, 'fixture',
                                Path(self.record['evidence']), [self.sid])
        self.assertEqual(self.path.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, 'explicit --e2-registry'):
            registry.resolve(self.root, None, self.system, 1)

    def test_endpoint_seed_physics_or_permission_substitution_rejected(self):
        source = e2.campaign.load_json(self.record['source_plan'])
        prefix = self.record['histories'][0]['prefix']
        changes = (('end_step', 2000000), ('prefix', prefix.replace('/equilibrate_', '/smoke_')),
                   ('prefix', prefix.replace('c6051f0ca57140819c10ae01e63036b5', 'other')),
                   ('replica', 2), ('chemistry_seed', 1),
                   ('physics', dict(self.record['histories'][0]['physics'], Ee=8)))
        for key, value in changes:
            bad = copy.deepcopy(self.record)
            bad['histories'][0][key] = value
            with self.subTest(key=key), patch.object(e2, 'check_hashes'), \
                    patch.object(e2.campaign, 'load_json', return_value=source):
                with self.assertRaises(ValueError):
                    registry.exclusive_validate(bad, [self.system])
        bad = copy.deepcopy(self.record)
        bad['histories'][0]['sha256'][prefix + '.assoc_restart'] = '0' * 64
        with self.assertRaises(ValueError):
            registry.exclusive_validate(bad, [self.system])
        with self.assertRaisesRegex(ValueError, 'downstream system/use'):
            registry.permitted(self.record, e2.system_by_id('F04_N010_RP080_EE08_EA04'))

    def test_eighth_acceptance_is_visible_and_unselected(self):
        index = e2.campaign.load_json(self.dossier / 'RECORDS.json')
        self.assertEqual(len(index['records']), 8)
        self.assertEqual(len({r['system'] for r in index['records']}), 8)
        graph = Catalog(self.repo, self.root).scan()
        system = next(s for s in graph['systems'] if s['system_id'] == self.sid)
        self.assertEqual(len(graph['acceptances']), 8)
        self.assertEqual(system['scientific'], 'formal_acceptance_recorded_payload_deferred')
        self.assertEqual(system['selection'], 'missing')
        self.assertEqual(system['production_authorization'], 'absent')
        self.assertFalse(graph['selections'])
        self.assertFalse(graph['registry_views'])
        self.assertIsNone(graph['selected_registry'])


if __name__ == '__main__':
    unittest.main()
