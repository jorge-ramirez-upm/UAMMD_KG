"""Acceptance API bookkeeping tests: no GPU, registry publication or MD launch."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import kg_assoc_e2 as e2
import kg_assoc_e2_registry as registry
from test_e2_g1 import fixture


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.histories = []
        for replica in (1, 2, 3):
            entry = fixture(self.root / str(replica), f=4, ee=4)
            entry['replica'] = replica
            entry['chemistry_seed'] += replica
            path = Path(entry['output_prefix'] + '.assoc_restart')
            path.write_text(path.read_text().replace('seed 420001', 'seed ' + str(entry['chemistry_seed'])))
            self.histories.append(entry)
        self.system = self.histories[0]['system']
        self.plan = dict(stage='E2-G1', smoke=False, system=self.system, histories=self.histories)
        self.attempt = self.root / 'approved'
        self.source = self.attempt / 'plan.json'
        e2.exclusive_json(self.source, self.plan)
        for h in self.histories:
            e2.exclusive_json(Path(h['output_prefix']).parent / 'complete.json',
                dict(status='validated', end_step=h['end_step'], plan_sha256=e2.campaign.sha256(self.source)))
        self.evidence = self.root / 'approved-review.md'
        self.evidence.write_text('Explicit approved qualified initialization review fixture')
        self.output = self.root / 'banks/e2_acceptance/qualified.json'

    def accept(self, plan=None):
        with patch.object(e2, 'verify', return_value=plan or self.plan), \
                patch.object(e2, 'system_by_id', return_value=self.system), \
                patch.object(registry, 'publish', side_effect=AssertionError('activation forbidden')):
            return registry.accept(self.root, self.output, self.attempt, 'explicit user approval',
                self.evidence, [self.system['system_id']], 'slow topology not proven decorrelated')

    def test_qualified_acceptance_is_immutable_and_does_not_activate(self):
        record = self.accept()
        self.assertEqual(record['status'], 'accepted_with_qualification')
        self.assertEqual(record['permitted_systems'], [self.system['system_id']])
        self.assertEqual(record['permitted_use'], 'production_initial_state')
        self.assertEqual([h['prefix'] for h in record['histories']],
                         [h['output_prefix'] for h in self.histories])
        before = self.output.read_bytes()
        self.assertFalse((self.root / 'banks/e2_registry').exists())
        with self.assertRaisesRegex(ValueError, 'new acceptance filename'):
            self.accept()
        self.assertEqual(self.output.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, 'explicit --e2-registry'):
            registry.resolve(self.root, None, self.system, 1)

    def test_smoke_duplicate_and_unmatched_source_fail_closed(self):
        plan = dict(self.plan, smoke=True)
        with self.assertRaisesRegex(ValueError, 'smokes'):
            self.accept(plan)
        plan = copy.deepcopy(self.plan)
        plan['histories'][1] = plan['histories'][0]
        with self.assertRaisesRegex(ValueError, 'three histories'):
            self.accept(plan)
        plan = copy.deepcopy(self.plan)
        plan['histories'][0]['end_step'] += 1000
        with self.assertRaisesRegex(ValueError, 'segment identity'):
            self.accept(plan)
        self.assertFalse(self.output.exists())

    def test_changed_receipt_and_endpoint_bytes_reject_record(self):
        record = self.accept()
        receipt = Path(record['histories'][0]['prefix']).parent / 'complete.json'
        original = receipt.read_bytes()
        receipt.write_text('{"status": "failed"}')
        with self.assertRaises(ValueError):
            registry.exclusive_validate(record, [self.system])
        receipt.write_bytes(original)
        endpoint = Path(record['histories'][0]['prefix'] + '.assoc_restart')
        endpoint.write_text(endpoint.read_text() + '# tampered\n')
        with self.assertRaisesRegex(ValueError, 'authenticated file changed'):
            registry.exclusive_validate(record, [self.system])

    def test_historical_C1_cannot_masquerade_as_corrected_import(self):
        record = self.accept()
        record.update(provenance_kind='corrected_C1_8M', bank_id='F04_N010_RP080_EE08')
        with patch.object(registry, 'permitted'):
            with self.assertRaisesRegex(ValueError, 'only qualified corrected C1'):
                registry.exclusive_validate(record, [self.system])


    def test_committed_acceptances_cover_only_the_approved_endpoint_sets(self):
        import hashlib
        import json
        repo = Path(__file__).resolve().parents[3]
        dossier = repo / 'examples/KG_Assoc/reviews/e2_formal_acceptance_20261013'
        index = json.loads((dossier / 'RECORDS.json').read_text())
        self.assertFalse(index['registry_activation'])
        self.assertFalse(index['production_authorization'])
        expected = {'F04_N010_RP080_EE04_EA04': 2000000,
                    'F04_N010_RP020_EE08_EA04': 6000000,
                    'F04_N010_RP080_EE08_EA04': 8000000}
        self.assertEqual({r['system']: r['end_step'] for r in index['records']}, expected)
        for reference in index['records']:
            path = repo / reference['record']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), reference['sha256'])
            record = json.loads(path.read_text())
            self.assertEqual(record['permitted_systems'], [reference['system']])
            self.assertEqual(record['status'], 'accepted_with_qualification')
            self.assertEqual(record['permitted_use'], 'production_initial_state')
            self.assertEqual([h['replica'] for h in record['histories']], [1, 2, 3])
            self.assertTrue(all(h['end_step'] == reference['end_step'] for h in record['histories']))
            self.assertTrue(all(h['physics']['Ea'] == 4 for h in record['histories']))
            self.assertNotIn('/smoke_', ' '.join(h['prefix'] for h in record['histories']))
            if reference['system'] == 'F04_N010_RP080_EE08_EA04':
                self.assertEqual(record['provenance_kind'], 'corrected_C1_8M')
                self.assertTrue(all('/C1_periodic_recovery_v1/' in h['prefix'] for h in record['histories']))
            if reference['system'] == 'F04_N010_RP020_EE08_EA04':
                decision = json.loads((repo / 'examples/KG_Assoc/reviews/e2_reassessment6m_20261013/decision.json').read_text())
                pins = decision['systems'][reference['system']]['proposed_endpoints']
                self.assertEqual([h['prefix'] for h in record['histories']], [h['prefix'] for h in pins])
                for history, pin in zip(record['histories'], pins):
                    self.assertTrue(all(history['sha256'].get(p) == d for p, d in pin['state_sha256'].items()))
        auth = dossier / 'AUTHENTICATION.json'
        self.assertEqual(hashlib.sha256(auth.read_bytes()).hexdigest(), index['authentication_sha256'])


if __name__ == '__main__':
    unittest.main()
