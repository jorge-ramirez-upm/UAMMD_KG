"""CPU-only 16M preparation authorization and validation-lineage regression tests."""
import hashlib
import unittest
from unittest import mock

import kg_assoc_e2 as e2
import test_e2_single_history as single


class DerivedPreparationTests(unittest.TestCase):
    setUp = single.SingleHistoryTests.setUp
    write_approval = single.SingleHistoryTests.write_approval
    mocked_execution = single.SingleHistoryTests.mocked_execution

    def configure(self, ea=6):
        self.plan.update(reference_control=False, smoke=False, steps=16000000,
                         system=dict(system_id=f'F04_N010_RP080_EE08_EA{ea:02d}'))
        for entry in self.plan['histories']:
            entry.update(start_step=8000000, end_step=24000000)
        (self.attempt / 'plan.json').write_text(e2.json.dumps(self.plan))
        self.record.update(purpose='e2_derived_segment',
            plan_sha256=e2.campaign.sha256(self.attempt / 'plan.json'),
            selector_scope='Ea_transfer_16M_preparation_v1',
            authorized_system=self.plan['system']['system_id'], authorized_replicas=[1, 2, 3],
            maximum_additional_MD_steps_per_history=16000000,
            maximum_additional_MD_steps=48000000,
            absolute_start_step=8000000, absolute_end_step=24000000)
        self.write_approval(self.record)

    def test_exact_three_target_triplets(self):
        for ea in (6, 8, 10):
            self.configure(ea)
            self.assertTrue(e2.derived_preparation(self.plan))
            self.assertEqual(e2.launch_scope(self.plan, None), self.plan['histories'])
            e2.scoped_launch_approval(self.approval, self.attempt, 'e2_derived_segment',
                                     self.plan, None)

    def test_wrong_target_control_duration_and_endpoints(self):
        for mutation in (dict(steps=16000001), dict(steps=10000), dict(steps=16000000.0),
                         dict(reference_control=True),
                         dict(system=dict(system_id='F04_N010_RP080_EE08_EA04'))):
            self.configure()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                e2.launch_scope(dict(self.plan, **mutation), None)
        for key, value in (('start_step', 8000001), ('end_step', 24000001), ('replica', 4)):
            self.configure()
            self.plan['histories'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                e2.launch_scope(self.plan, None)

    def test_subsets_and_old_smoke_approvals_cannot_launch(self):
        self.configure()
        for replica, replicas in ((1, None), (None, []), (None, [3, 1]), (None, [4])):
            with self.subTest(replica=replica, replicas=replicas), self.assertRaises(ValueError):
                e2.launch_scope(self.plan, replica, replicas)
        for mutation in (dict(selector_scope='Ea_transfer_remaining_smoke_v1'),
                         dict(purpose='e2_derived_smoke'), dict(approved=False),
                         dict(plan_sha256='tampered'), dict(authorized_replicas=[1, 2]),
                         dict(authorized_replicas=[True, 2, 3]),
                         dict(authorized_system='F04_N010_RP080_EE08_EA08'),
                         dict(maximum_additional_MD_steps=144000000),
                         dict(maximum_additional_MD_steps_per_history=16000001),
                         dict(absolute_start_step=0), dict(absolute_end_step=24000001)):
            self.write_approval(dict(self.record, **mutation))
            with self.subTest(mutation=mutation), self.mocked_execution() as popen:
                with self.assertRaises(ValueError):
                    e2.launch(self.root, self.attempt, True, self.approval)
                popen.assert_not_called()

    def test_missing_or_wrong_typed_approval_fields(self):
        self.configure()
        for key in ('selector_scope', 'authorized_system', 'authorized_replicas',
                    'maximum_additional_MD_steps_per_history', 'maximum_additional_MD_steps',
                    'absolute_start_step', 'absolute_end_step'):
            record = dict(self.record)
            del record[key]
            self.write_approval(record)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                e2.scoped_launch_approval(self.approval, self.attempt, 'e2_derived_segment',
                                         self.plan, None)
        for key in ('maximum_additional_MD_steps_per_history', 'maximum_additional_MD_steps',
                    'absolute_start_step', 'absolute_end_step'):
            self.write_approval(dict(self.record, **{key: float(self.record[key])}))
            with self.subTest(float_field=key), self.assertRaises(ValueError):
                e2.scoped_launch_approval(self.approval, self.attempt, 'e2_derived_segment',
                                         self.plan, None)

    def test_only_titan_and_matching_smoke_are_allowed(self):
        self.configure()
        with self.mocked_execution() as popen, mock.patch.object(
                e2.socket, 'gethostname', return_value='other'):
            with self.assertRaisesRegex(ValueError, 'only on titan'):
                e2.launch(self.root, self.attempt, True, self.approval)
            popen.assert_not_called()
        with self.mocked_execution() as popen, mock.patch.object(
                e2.socket, 'gethostname', return_value='titan'), mock.patch.object(
                e2, 'matching_smoke', side_effect=ValueError('unqualified smoke')):
            with self.assertRaisesRegex(ValueError, 'unqualified smoke'):
                e2.launch(self.root, self.attempt, True, self.approval)
            popen.assert_not_called()

    def test_first_failure_stops_and_used_outputs_cannot_restart(self):
        self.configure()
        with self.mocked_execution(status=1) as popen, mock.patch.object(
                e2.socket, 'gethostname', return_value='titan'), mock.patch.object(
                e2, 'matching_smoke', return_value={}):
            with self.assertRaisesRegex(ValueError, 'MD executable failed'):
                e2.launch(self.root, self.attempt, True, self.approval)
            self.assertEqual(popen.call_count, 1)
        self.assertTrue((self.attempt / 'r001/incomplete.json').exists())
        for replica in (2, 3):
            self.assertEqual(list((self.attempt / f'r{replica:03d}').iterdir()), [])
        with self.mocked_execution() as popen:
            with self.assertRaisesRegex(ValueError, 'attempt already used'):
                e2.launch(self.root, self.attempt, True, self.approval)
            popen.assert_not_called()

    def test_diagnostic_executable_selected_for_ordinary_16m(self):
        self.configure()
        entry = dict(self.plan['histories'][0], parent_Ea=4, physics=dict(Ea=6),
            chemistry_seed=101, md_seed=202,
            lineage=dict(parent_chemistry_seed=99, branch_id='fixture', reference_control=False))
        entry['parent'].update(kind='e2', prefix='fixture_parent')
        command = e2.command(entry, False)
        self.assertTrue(command[0].endswith('/kg_assoc_stars_candidate_smoke'))
        self.assertIn('16000000', command)
        self.assertIn('--reseed-chemistry-from', command)

    def test_compatibility_canonicalizes_only_exact_validation_changes(self):
        self.configure()
        before, after = {}, {}
        for relative, transitions in e2.VALIDATION_TRANSITIONS.items():
            path = (e2.HERE.parent / relative).resolve()
            text = path.read_text()
            after[str(path)] = hashlib.sha256(text.encode()).hexdigest()
            for new, old in transitions:
                self.assertEqual(text.count(new), 1)
                text = text.replace(new, old, 1)
            before[str(path)] = hashlib.sha256(text.encode()).hexdigest()
        key = str(e2.HERE.parent / 'kg_assoc_kinetics.cuh')
        before[key] = after[key] = 'frozen_physics_fixture'
        smoke = dict(source_sha256=before, executable_sha256={})
        self.plan.update(source_sha256=after, executable_sha256={'new_build_fixture': 'hash'})
        with mock.patch.object(e2, 'check_hashes') as checked:
            self.assertTrue(e2.smoke_code_compatible(smoke, self.plan))
            self.assertEqual(checked.call_count, 2)
            self.plan['source_sha256'][key] = 'modified_physics'
            self.assertFalse(e2.smoke_code_compatible(smoke, self.plan))
            self.plan['source_sha256'][key] = before[key]
            self.plan['source_sha256'][str(e2.HERE.parent / 'kg_assoc_stars.cu')] = 'tampered'
            self.assertFalse(e2.smoke_code_compatible(smoke, self.plan))
