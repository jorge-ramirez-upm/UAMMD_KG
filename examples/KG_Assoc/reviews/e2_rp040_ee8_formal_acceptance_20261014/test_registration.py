"""Exact authorized RP040 Ee8 endpoints, qualifications and unselected inventory."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import kg_assoc_e2 as e2
import kg_assoc_e2_registry as registry
from catalog_model import Catalog


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[4]
        self.root = self.repo / 'examples/KG_Assoc/kg_assoc_100m'
        self.dossier = Path(__file__).resolve().parent
        self.registration = e2.campaign.load_json(self.dossier / 'REGISTRATION.json')
        self.path = self.repo / self.registration['acceptance']
        self.record = e2.campaign.load_json(self.path)
        self.sid = 'F04_N010_RP040_EE08_EA04'
        self.system = e2.system_by_id(self.sid)

    def test_exact_review_endpoint_seed_and_permission_bindings(self):
        r = self.record
        self.assertEqual(e2.campaign.sha256(self.path), self.registration['acceptance_sha256'])
        self.assertEqual(r['publisher_git_sha'], 'a8d5c2353de2ee3545be7ae850ea6a1956394881')
        self.assertEqual(r['status'], 'accepted_with_qualification')
        self.assertEqual(r['permitted_use'], 'production_initial_state')
        self.assertEqual(r['permitted_systems'], [self.sid])
        self.assertEqual(r['source_plan_sha256'],
                         'b88f2eec2bdff278393d11db52252abb1bcbb9bbdbca3edeb374d3022d10e6c4')
        self.assertEqual([h['replica'] for h in r['histories']], [1, 2, 3])
        self.assertEqual([h['chemistry_seed'] for h in r['histories']], [420201, 420202, 420203])
        for h, pin in zip(r['histories'], self.registration['selected_endpoints']):
            self.assertEqual(h['prefix'], pin['prefix'])
            self.assertIn('/equilibrate_ea8bd8e305aa4edfa9871dc977213948/', h['prefix'])
            self.assertEqual(h['end_step'], 8000000)
            for path, digest in pin['state_sha256'].items():
                self.assertEqual(h['sha256'][path], digest)
        registry.exclusive_validate(r, [self.system])
        for phrase in ('Complete stationarity', 'full structural decorrelation', 'r002 L1',
                       'initialization bias', 'multiplicity', 'final-250k', 'MD-reseeding boundary at 6M',
                       'no stitched IAT or SEM', 'Historical E1 executable bytes'):
            self.assertIn(phrase, r['qualification'])

    def test_prior_evidence_and_exclusive_creation(self):
        self.assertEqual(len(self.registration['prior_acceptance_sha256']), 8)
        e2.check_hashes(self.registration['prior_acceptance_sha256'])
        e2.check_hashes(self.registration['scientific_dossier_sha256'])
        preserved = e2.campaign.load_json(self.dossier / 'PRESERVED_EVIDENCE.json')
        maintenance = {'examples/KG_Assoc/campaign/test_e2_n40_acceptance.py',
                       'examples/KG_Assoc/campaign/test_e2_ee6_acceptance.py'}
        e2.check_hashes({str(self.repo / n): h for n, h in preserved.items() if n not in maintenance})
        integrity = e2.campaign.load_json(self.dossier / 'INTEGRITY.json')
        self.assertEqual(set(integrity['test_maintenance']), maintenance)
        for n, hashes in integrity['test_maintenance'].items():
            self.assertEqual(hashes['before'], preserved[n])
            self.assertEqual(hashes['after'], e2.campaign.sha256(self.repo / n))
        before = self.path.read_bytes()
        with patch.object(e2, 'verify', side_effect=AssertionError('must reject before replay')):
            with self.assertRaisesRegex(ValueError, 'new acceptance filename'):
                registry.accept(self.root, self.path, None, 'fixture', Path(self.record['evidence']), [self.sid])
        self.assertEqual(before, self.path.read_bytes())

    def test_endpoint_hash_seed_and_scope_substitution_rejected(self):
        for key, value in [('end_step', 6000000), ('chemistry_seed', 420999),
                           ('prefix', self.record['histories'][0]['prefix'].replace('ea8bd8e', 'other'))]:
            bad = copy.deepcopy(self.record)
            bad['histories'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                registry.exclusive_validate(bad, [self.system])
        bad = copy.deepcopy(self.record)
        path = bad['histories'][0]['prefix'] + '.assoc_restart'
        bad['histories'][0]['sha256'][path] = '0' * 64
        with self.assertRaises(ValueError):
            registry.exclusive_validate(bad, [self.system])
        bad = copy.deepcopy(self.record)
        bad['permitted_use'] = 'production_authorization'
        with self.assertRaises(ValueError):
            registry.exclusive_validate(bad, [self.system])
        with self.assertRaises(ValueError):
            registry.permitted(self.record, e2.system_by_id('F04_N010_RP020_EE08_EA04'))

    def test_exact_nine_record_inventory_without_selection(self):
        index = e2.campaign.load_json(self.dossier / 'RECORDS.json')
        self.assertEqual(len(index['records']), 9)
        expected = {str(self.repo / row['record']): row['sha256'] for row in index['records']}
        self.assertEqual(expected, {**self.registration['prior_acceptance_sha256'],
                                   str(self.path): self.registration['acceptance_sha256']})
        e2.check_hashes(expected)
        graph = Catalog(self.repo, self.root).scan()
        self.assertEqual(len(graph['acceptances']), 9)
        self.assertCountEqual([row['source'] for row in graph['acceptances']],
            ['dataset:' + str(Path(n).relative_to(self.root)) for n in expected])
        self.assertFalse(graph['selections'])
        self.assertFalse(graph['registry_views'])
        self.assertIsNone(graph['selected_registry'])
        self.assertFalse((self.root / 'banks/e2_registry').exists())
        self.assertTrue(all(s['production_authorization'] == 'absent' for s in graph['systems']))
        for flag in ('registry_activation', 'active_selection', 'registry_publication',
                     'production_preparation', 'production_authorization', 'trajectory_launched'):
            self.assertFalse(self.registration[flag])
        with self.assertRaisesRegex(ValueError, 'explicit --e2-registry'):
            registry.resolve(self.root, None, self.system, 1)


if __name__ == '__main__':
    unittest.main()
