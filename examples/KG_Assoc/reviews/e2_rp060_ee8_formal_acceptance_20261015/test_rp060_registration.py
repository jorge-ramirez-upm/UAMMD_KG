"""Exact RP060 qualified registration, immutable prior evidence and unselected inventory."""
import copy
import unittest
from unittest.mock import patch

import register as registration

e2 = registration.e2
registry = registration.registry


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.dossier = registration.DOSSIER
        self.registration = e2.campaign.load_json(self.dossier / 'REGISTRATION.json')
        self.path = registration.REPO / self.registration['acceptance']
        self.record = e2.campaign.load_json(self.path)
        self.system = e2.system_by_id(registration.SID)

    def test_exact_endpoint_seeds_scope_and_qualifications(self):
        record = self.record
        self.assertEqual(e2.campaign.sha256(self.path), self.registration['acceptance_sha256'])
        self.assertEqual(record['publisher_git_sha'], registration.APPROVED_SHA)
        self.assertEqual(record['status'], 'accepted_with_qualification')
        self.assertEqual(record['permitted_use'], 'production_initial_state')
        self.assertEqual(record['permitted_systems'], [registration.SID])
        self.assertEqual(record['source_plan_sha256'], registration.scientific.PLAN_HASH)
        self.assertEqual(record['qualification'], registration.QUALIFICATION)
        self.assertEqual([h['replica'] for h in record['histories']], [1, 2, 3])
        self.assertEqual([h['chemistry_seed'] for h in record['histories']], [420301, 420302, 420303])
        for history, pin in zip(record['histories'], self.registration['selected_endpoints']):
            self.assertEqual(history['prefix'], pin['prefix'])
            self.assertEqual(history['end_step'], 6000000)
            for name, digest in pin['state_sha256'].items():
                self.assertEqual(history['sha256'][name], digest)
        for phrase in ('Complete stationarity, structural decorrelation',
                       'absence of initialization bias have not been demonstrated',
                       'Late intra/inter', 'poorly resolved L1', "r003's late conformational",
                       'residual initialization', 'incomplete slow-topology sampling',
                       'Historical E1 executable bytes', 'accepted active E1 retry attempt001'):
            self.assertIn(phrase, record['qualification'])
        registry.exclusive_validate(record, [self.system])

    def test_nine_prior_records_and_all_preserved_evidence_unchanged(self):
        prior = self.registration['prior_acceptance_sha256']
        self.assertEqual(len(prior), 9)
        e2.check_hashes(prior)
        e2.check_hashes(self.registration['scientific_dossier_sha256'])
        preserved = e2.campaign.load_json(self.dossier / 'PRESERVED_EVIDENCE.json')
        self.assertEqual(len(preserved), 772)
        e2.check_hashes(preserved)
        self.assertTrue(set(prior) <= set(preserved))

    def test_duplicate_registration_fails_before_replay(self):
        before = self.path.read_bytes()
        with patch.object(e2, 'verify', side_effect=AssertionError('must reject before replay')):
            with self.assertRaisesRegex(ValueError, 'new acceptance filename'):
                registry.accept(registration.ROOT, self.path, registration.scientific.ATTEMPT,
                    'fixture', registration.REVIEW / 'ASSESSMENT.md', [registration.SID])
        self.assertEqual(before, self.path.read_bytes())

    def test_endpoint_hash_seed_and_scope_substitution_rejected(self):
        prefix = self.record['histories'][0]['prefix']
        for key, value in (('end_step', 8000000), ('chemistry_seed', 420999),
                           ('prefix', prefix.replace('92296b2a', 'other'))):
            bad = copy.deepcopy(self.record)
            bad['histories'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                registry.exclusive_validate(bad, [self.system])
        for suffix in ('.assoc_restart', '.restart.lammpsdat'):
            bad = copy.deepcopy(self.record)
            bad['histories'][0]['sha256'][prefix + suffix] = '0' * 64
            with self.assertRaises(ValueError):
                registry.exclusive_validate(bad, [self.system])
        bad = copy.deepcopy(self.record)
        bad['permitted_use'] = 'production_authorization'
        with self.assertRaises(ValueError):
            registry.exclusive_validate(bad, [self.system])
        with self.assertRaises(ValueError):
            registry.permitted(self.record, e2.system_by_id('F04_N010_RP040_EE08_EA04'))

    def test_accepted_retry_and_md_seed_pins_cannot_be_substituted(self):
        provenance = e2.campaign.load_json(registration.REVIEW / 'evidence/provenance.json')
        text = (registration.REVIEW / 'ENDPOINTS.md').read_text()
        registration.check_pins(provenance, text)
        for mutation in ('failed_parent', 'md_seed'):
            bad = copy.deepcopy(provenance)
            if mutation == 'failed_parent':
                bad['validated_histories'][1]['entry']['parent']['snapshot'] = str(
                    registration.ROOT / 'banks/e1/F04_N010_RP060/r002/state.e1.lammpsdat')
            else:
                bad['proposed_endpoints'][1]['md_seed'] += 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                registration.check_pins(bad, text)

    def test_exact_ten_record_inventory_without_selection_or_authorization(self):
        index = e2.campaign.load_json(self.dossier / 'RECORDS.json')
        expected = {str(registration.REPO / row['record']): row['sha256']
                    for row in index['records']}
        self.assertEqual(len(index['records']), 10)
        self.assertEqual(len({row['system'] for row in index['records']}), 10)
        self.assertEqual(expected, {**self.registration['prior_acceptance_sha256'],
                                   str(self.path): self.registration['acceptance_sha256']})
        e2.check_hashes(expected)
        graph = registration.Catalog(registration.REPO, registration.ROOT).scan()
        self.assertEqual(len(graph['acceptances']), 10)
        self.assertCountEqual([r['source'] for r in graph['acceptances']],
            ['dataset:' + str(registration.Path(n).relative_to(registration.ROOT)) for n in expected])
        self.assertTrue(all(r['metadata_eligible'] for r in graph['acceptances']))
        self.assertFalse(graph['selections'])
        self.assertFalse(graph['registry_views'])
        self.assertIsNone(graph['selected_registry'])
        self.assertFalse((registration.ROOT / 'banks/e2_registry').exists())
        self.assertTrue(all(s['production_authorization'] == 'absent' for s in graph['systems']))
        for flag in ('registry_activation', 'active_selection', 'registry_publication',
                     'production_preparation', 'production_authorization', 'trajectory_launched'):
            self.assertFalse(self.registration[flag])
        with self.assertRaisesRegex(ValueError, 'explicit --e2-registry'):
            registry.resolve(registration.ROOT, None, self.system, 1)


if __name__ == '__main__':
    unittest.main()
