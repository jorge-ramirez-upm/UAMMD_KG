"""Finite remaining-smoke selection fixtures; no GPU or real campaign mutations."""
import itertools
import unittest
from unittest import mock

import kg_assoc_e2 as e2
import test_e2_single_history as single


class RemainingSmokeTests(unittest.TestCase):
    setUp = single.SingleHistoryTests.setUp
    write_approval = single.SingleHistoryTests.write_approval
    mocked_execution = single.SingleHistoryTests.mocked_execution

    def configure(self, ea=4, replicas=None):
        replicas = [2, 3] if replicas is None else replicas
        self.plan.update(reference_control=ea == 4,
                         system=dict(system_id=f'F04_N010_RP080_EE08_EA{ea:02d}'))
        (self.attempt / 'plan.json').write_text(e2.json.dumps(self.plan))
        self.record.update(plan_sha256=e2.campaign.sha256(self.attempt / 'plan.json'),
            selector_scope='Ea_transfer_remaining_smoke_v1',
            authorized_system=self.plan['system']['system_id'], authorized_replicas=replicas,
            maximum_additional_MD_steps_per_history=10000,
            maximum_additional_MD_steps=10000 * len(replicas))
        self.write_approval(self.record)

    def test_exact_authorized_identity_set_and_all_nonempty_subsets(self):
        authorized = set()
        for ea in (4, 6, 8, 10):
            allowed = [2, 3] if ea == 4 else [1, 2, 3]
            self.configure(ea)
            for size in range(1, len(allowed) + 1):
                for subset in itertools.combinations(allowed, size):
                    selected = e2.launch_scope(self.plan, None, list(subset))
                    self.assertEqual([entry['replica'] for entry in selected], list(subset))
                    authorized.update((ea, entry['replica']) for entry in selected)
        self.assertEqual(authorized, {(4, 2), (4, 3)} |
                         {(ea, replica) for ea in (6, 8, 10) for replica in (1, 2, 3)})

    def test_control_r001_and_malformed_selections_are_prohibited(self):
        self.configure()
        for selection in ([1], [1, 2], [1, 3], [1, 2, 3], [], [3, 2], [2, 2],
                          [True], [2.0], ['2'], [0], [4], (2, 3)):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                e2.launch_scope(self.plan, None, selection)
        with self.assertRaisesRegex(ValueError, 'one explicit selector'):
            e2.launch_scope(self.plan, 1, [2, 3])

    def test_wrong_system_mode_control_or_duration_is_prohibited(self):
        self.configure(6)
        for mutation in (dict(system=dict(system_id='F03_N010_RP080_EE08_EA04')),
                         dict(reference_control=True), dict(lineage_mode='ordinary'),
                         dict(smoke=False), dict(steps=0), dict(steps=10001), dict(steps=True)):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                e2.launch_scope(dict(self.plan, **mutation), None, [1])

    def test_approval_requires_exact_system_subset_and_both_caps(self):
        self.configure()
        mutations = [dict(authorized_replicas=[2]), dict(authorized_replicas=[1, 2, 3]),
                     dict(authorized_replicas=[True, 3]), dict(selector_scope='wrong'),
                     dict(authorized_system='F04_N010_RP080_EE08_EA06'),
                     dict(maximum_additional_MD_steps=10000),
                     dict(maximum_additional_MD_steps=30000),
                     dict(maximum_additional_MD_steps_per_history=10001),
                     dict(maximum_additional_MD_steps_per_history=True),
                     dict(maximum_additional_MD_steps=20000.0),
                     dict(plan_sha256='tampered'), dict(approved=False)]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.mocked_execution() as popen:
                self.write_approval(dict(self.record, **mutation))
                with self.assertRaises(ValueError):
                    e2.launch(self.root, self.attempt, True, self.approval, replicas=[2, 3])
                popen.assert_not_called()
                self.assertFalse((self.attempt / 'r002/started.json').exists())

    def test_omitted_selector_or_scope_field_cannot_launch(self):
        self.configure()
        for missing in (None, 'authorized_replicas', 'selector_scope',
                        'maximum_additional_MD_steps_per_history', 'authorized_system'):
            record = dict(self.record)
            if missing:
                del record[missing]
            self.write_approval(record)
            with self.subTest(missing=missing), self.mocked_execution() as popen:
                with self.assertRaises(ValueError):
                    e2.launch(self.root, self.attempt, True, self.approval)
                if missing:
                    with self.assertRaises(ValueError):
                        e2.launch(self.root, self.attempt, True, self.approval, replicas=[2, 3])
                popen.assert_not_called()

    def test_selected_controls_leave_r001_completely_untouched(self):
        self.configure()
        with self.mocked_execution() as popen:
            e2.launch(self.root, self.attempt, True, self.approval, replicas=[2, 3])
            self.assertEqual([call.args[0] for call in popen.call_args_list],
                             [entry['command'] for entry in self.plan['histories'][1:]])
        self.assertEqual(list((self.attempt / 'r001').iterdir()), [])
        for replica in (2, 3):
            self.assertTrue((self.attempt / f'r{replica:03d}/complete.json').is_file())

    def test_target_subset_never_starts_omitted_replicas(self):
        self.configure(8, [2])
        with self.mocked_execution() as popen:
            e2.launch(self.root, self.attempt, True, self.approval, replicas=[2])
            self.assertEqual(popen.call_count, 1)
        for replica in (1, 3):
            self.assertEqual(list((self.attempt / f'r{replica:03d}').iterdir()), [])

    def test_first_failure_stops_remaining_selected_histories_and_prevents_reuse(self):
        self.configure(6, [1, 2, 3])
        statuses = iter([0, 1])
        def start(command, stdout, stderr):
            stdout.write('STAR_ASSOCIATION_SMOKE PASS\n')
            process = mock.Mock()
            process.wait.return_value = next(statuses)
            return process
        with self.mocked_execution() as popen:
            popen.side_effect = start
            with self.assertRaisesRegex(ValueError, 'MD executable failed'):
                e2.launch(self.root, self.attempt, True, self.approval, replicas=[1, 2, 3])
            self.assertEqual(popen.call_count, 2)
        self.assertTrue((self.attempt / 'r001/complete.json').is_file())
        self.assertTrue((self.attempt / 'r002/incomplete.json').is_file())
        self.assertFalse((self.attempt / 'r002/complete.json').exists())
        self.assertEqual(list((self.attempt / 'r003').iterdir()), [])
        receipt = (self.attempt / 'r002/incomplete.json').read_bytes()
        with self.mocked_execution() as popen:
            with self.assertRaisesRegex(ValueError, 'attempt already used'):
                e2.launch(self.root, self.attempt, True, self.approval, replicas=[1, 2, 3])
            popen.assert_not_called()
        self.assertEqual((self.attempt / 'r002/incomplete.json').read_bytes(), receipt)

    def test_selected_and_unselected_output_reuse_rejected_before_start(self):
        self.configure()
        for replica in (1, 2):
            path = self.attempt / f'r{replica:03d}/previous'
            path.write_text('fixture')
            with self.subTest(replica=replica), self.mocked_execution() as popen:
                with self.assertRaisesRegex(ValueError, 'attempt already used'):
                    e2.launch(self.root, self.attempt, True, self.approval, replicas=[2, 3])
                popen.assert_not_called()
            path.unlink()

    def test_seed_collision_and_live_source_checks_still_precede_execution(self):
        self.configure()
        for error in ('effective MD seed collision', 'source mismatch'):
            with self.subTest(error=error), self.mocked_execution() as popen:
                with mock.patch.object(e2, 'check_plan', side_effect=ValueError(error)):
                    with self.assertRaisesRegex(ValueError, error):
                        e2.launch(self.root, self.attempt, True, self.approval, replicas=[2, 3])
                popen.assert_not_called()

    def test_approval_is_rechecked_between_selected_histories(self):
        self.configure()
        calls = 0
        def checked_plan(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 3:
                self.write_approval(dict(self.record, authorized_replicas=[3]))
            return self.plan
        with self.mocked_execution() as popen:
            with mock.patch.object(e2, 'check_plan', side_effect=checked_plan):
                with self.assertRaisesRegex(ValueError, 'scope/cap differs'):
                    e2.launch(self.root, self.attempt, True, self.approval, replicas=[2, 3])
            self.assertEqual(popen.call_count, 1)
        self.assertTrue((self.attempt / 'r002/complete.json').exists())
        self.assertEqual(list((self.attempt / 'r003').iterdir()), [])
