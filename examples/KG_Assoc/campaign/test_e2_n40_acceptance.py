"""Exact N40 acceptance bindings and fail-closed unactivated registry guards."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import kg_assoc_e2 as e2
import kg_assoc_e2_registry as registry
from catalog_model import Catalog


class N40AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[3]
        self.root = self.repo/'examples/KG_Assoc/kg_assoc_100m'
        self.dossier = self.repo/'examples/KG_Assoc/reviews/e2_n40_formal_acceptance_20261014'
        self.registration = json.loads((self.dossier/'REGISTRATION.json').read_text())
        self.record_path = self.repo/self.registration['acceptance']
        self.record = json.loads(self.record_path.read_text())
        self.sid = 'F04_N040_RP080_EE08_EA04'
        self.system = e2.system_by_id(self.sid)

    def test_exact_payloads_review_and_permission(self):
        r = self.record
        self.assertEqual(r['permitted_systems'], [self.sid])
        self.assertEqual(r['permitted_use'], 'production_initial_state')
        self.assertEqual(r['status'], 'accepted_with_qualification')
        self.assertEqual(hashlib.sha256(self.record_path.read_bytes()).hexdigest(),
                         self.registration['acceptance_sha256'])
        decision = json.loads(Path(self.registration['scientific_decision']).read_text())
        pins = decision['systems'][self.sid]['proposed_endpoints']
        self.assertEqual(pins, self.registration['selected_endpoints'])
        self.assertEqual([h['replica'] for h in r['histories']], [1, 2, 3])
        for history, pin in zip(r['histories'], pins):
            self.assertEqual(history['prefix'], pin['prefix'])
            self.assertIn('/equilibrate_0a6a37a1e8264ceabbeead5362d8423d/', history['prefix'])
            self.assertEqual(history['end_step'], 8000000)
            self.assertTrue(all(history['sha256'][p] == digest
                                for p, digest in pin['state_sha256'].items()))
        registry.exclusive_validate(r, [self.system])
        for phrase in ('stationarity/decorrelation', 'shifted-window', '21%', '0.137',
                       'peripheral-network', 'Effective sampling', 'Historical E1 executable',
                       'current E2 executable', 'star/sticker number densities'):
            self.assertIn(phrase, r['qualification'])

    def test_immutability_and_absence_of_activation(self):
        previous = self.registration['prior_acceptance_sha256']
        self.assertEqual(len(previous), 6)
        e2.check_hashes(previous)
        for flag in ('registry_activation', 'active_selection', 'registry_publication',
                     'production_preparation', 'production_authorization', 'trajectory_launched'):
            self.assertFalse(self.registration[flag])
        before = self.record_path.read_bytes()
        with patch.object(e2, 'verify', side_effect=AssertionError('must fail first')), \
                patch.object(registry, 'publish', side_effect=AssertionError('forbidden')):
            with self.assertRaisesRegex(ValueError, 'new acceptance filename'):
                registry.accept(self.root, self.record_path, None, 'fixture',
                                Path(self.record['evidence']), [self.sid])
        self.assertEqual(self.record_path.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, 'explicit --e2-registry'):
            registry.resolve(self.root, None, self.system, 1)

    def test_substitution_and_broadening_fail_closed(self):
        source = e2.campaign.load_json(self.record['source_plan'])
        prefix = self.record['histories'][0]['prefix']
        for key, value in (('end_step', 6000000), ('prefix', prefix.replace('/equilibrate_', '/smoke_')),
                           ('prefix', prefix.replace('0a6a37a1e8264ceabbeead5362d8423d', 'other')),
                           ('replica', 2), ('chemistry_seed', 1),
                           ('physics', dict(self.record['histories'][0]['physics'], narm=20))):
            bad = copy.deepcopy(self.record)
            bad['histories'][0][key] = value
            with self.subTest(key=key), patch.object(e2, 'check_hashes'), \
                    patch.object(e2.campaign, 'load_json', return_value=source):
                with self.assertRaises(ValueError):
                    registry.exclusive_validate(bad, [self.system])
        bad = copy.deepcopy(self.record)
        path = prefix+'.assoc_restart'
        bad['histories'][0]['sha256'][path] = '0'*64
        with self.assertRaises(ValueError):
            registry.exclusive_validate(bad, [self.system])
        with self.assertRaisesRegex(ValueError, 'downstream system/use'):
            registry.permitted(self.record, e2.system_by_id('F04_N020_RP080_EE08_EA04'))

    def test_seventh_record_is_formal_but_unselected(self):
        index = json.loads((self.dossier/'RECORDS.json').read_text())
        self.assertEqual(len(index['records']), 7)
        self.assertEqual(len({r['system'] for r in index['records']}), 7)
        self.assertFalse(index['registry_activation'])
        self.assertFalse(index['production_authorization'])

        # Keep the historical seven-record snapshot fixed; allow only the approved eighth record.
        ee6_dossier = self.repo / 'examples/KG_Assoc/reviews/e2_ee6_formal_acceptance_20261014'
        ee6_registration = e2.campaign.load_json(ee6_dossier / 'REGISTRATION.json')
        historical_hashes = {str(self.repo / row['record']): row['sha256']
                             for row in index['records']}
        self.assertEqual(historical_hashes, ee6_registration['prior_acceptance_sha256'])
        e2.check_hashes(historical_hashes)
        expected = {}
        for row in index['records']:
            path = self.repo / row['record']
            record = e2.campaign.load_json(path)
            self.assertEqual(record['permitted_systems'], [row['system']])
            self.assertEqual(record['status'], row['status'])
            self.assertEqual([h['end_step'] for h in record['histories']], [row['end_step']] * 3)
            registry.exclusive_validate(record, [e2.system_by_id(row['system'])])
            expected['dataset:' + str(path.relative_to(self.root))] = record

        ee6_path = self.root / ('banks/e2_acceptance/'
                               'F04_N010_RP080_EE06_EA04_4M_qualified_20261014_v1.json')
        self.assertEqual(self.repo / ee6_registration['acceptance'], ee6_path)
        self.assertEqual(e2.campaign.sha256(ee6_path),
                         '55fbe03556fcc3cd184bffbc43603b27726863bd618a28a06da7f97b399c3319')
        ee6 = e2.campaign.load_json(ee6_path)
        self.assertEqual(ee6['permitted_systems'], ['F04_N010_RP080_EE06_EA04'])
        registry.exclusive_validate(ee6, [e2.system_by_id('F04_N010_RP080_EE06_EA04')])
        expected['dataset:' + str(ee6_path.relative_to(self.root))] = ee6

        graph = Catalog(self.repo, self.root).scan()
        system = next(s for s in graph['systems'] if s['system_id'] == self.sid)
        self.assertEqual(system['scientific'], 'formal_acceptance_recorded_payload_deferred')
        self.assertEqual(system['selection'], 'missing')
        self.assertEqual(len(graph['acceptances']), 8)
        self.assertCountEqual([record['source'] for record in graph['acceptances']], expected)
        for record in graph['acceptances']:
            self.assertEqual(record['data'], expected[record['source']])
            self.assertTrue(record['metadata_eligible'])
        self.assertFalse(graph['selections'])
        self.assertFalse(graph['registry_views'])
        self.assertIsNone(graph['selected_registry'])
        self.assertTrue(all(s['production_authorization'] == 'absent' for s in graph['systems']))
        self.assertEqual(len(system['formal_acceptance_records']), 1)


if __name__ == '__main__':
    unittest.main()
