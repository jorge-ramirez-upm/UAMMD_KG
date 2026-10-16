"""Deterministic launcher scope fixtures; subprocesses and GPU execution are mocked."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import kg_assoc_e2 as e2


class SingleHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.attempt = self.root / 'attempt'
        self.attempt.mkdir()
        self.plan = dict(lineage_mode='Ea_reference_transfer_v1', reference_control=True,
                         smoke=True, steps=10000,
                         system=dict(system_id='F04_N010_RP080_EE08_EA04'), histories=[])
        for replica in (1, 2, 3):
            directory = self.attempt / f'r{replica:03d}'
            directory.mkdir()
            self.plan['histories'].append(dict(replica=replica,
                output_prefix=str(directory / 'state'), command=['fixture_no_execution', str(replica)],
                parent=dict(sha256={}), end_step=8010000))
        e2.exclusive_json(self.attempt / 'plan.json', self.plan)
        self.approval = self.attempt / 'approval.json'
        self.record = dict(schema_version=1, approved=True, purpose='e2_derived_smoke',
                           plan_sha256=e2.campaign.sha256(self.attempt / 'plan.json'),
                           reviewer='CPU_fixture_only', approved_at='fixture',
                           authorized_replicas=[1], maximum_additional_MD_steps=10000)
        self.write_approval(self.record)

    def write_approval(self, record):
        self.approval.write_text(json.dumps(record))

    @contextlib.contextmanager
    def mocked_execution(self, status=0):
        def start(command, stdout, stderr):
            stdout.write('STAR_ASSOCIATION_SMOKE PASS\n')
            process = mock.Mock()
            process.wait.return_value = status
            return process
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(e2, 'check_plan', return_value=self.plan))
            stack.enter_context(mock.patch.object(e2, 'live_code'))
            stack.enter_context(mock.patch.object(e2.subprocess, 'check_output', return_value='fixture_GPU'))
            stack.enter_context(mock.patch.object(e2.validation, 'validate',
                                                   return_value=([], [], {'fixture_only': True})))
            popen = stack.enter_context(mock.patch.object(e2.subprocess, 'Popen', side_effect=start))
            yield popen

    def test_selected_success_never_starts_other_histories(self):
        with self.mocked_execution() as popen:
            e2.launch(self.root, self.attempt, True, self.approval, replica=1)
            self.assertEqual(popen.call_count, 1)
            self.assertEqual(popen.call_args.args[0], self.plan['histories'][0]['command'])
        self.assertTrue((self.attempt / 'r001/complete.json').is_file())
        for replica in (2, 3):
            self.assertEqual(list((self.attempt / f'r{replica:03d}').iterdir()), [])

    def test_failed_selected_history_stops_without_retry(self):
        with self.mocked_execution(status=1) as popen:
            with self.assertRaisesRegex(ValueError, 'MD executable failed'):
                e2.launch(self.root, self.attempt, True, self.approval, replica=1)
            self.assertEqual(popen.call_count, 1)
        self.assertTrue((self.attempt / 'r001/incomplete.json').is_file())
        self.assertFalse((self.attempt / 'r001/complete.json').exists())
        for replica in (2, 3):
            self.assertEqual(list((self.attempt / f'r{replica:03d}').iterdir()), [])

    def test_scope_and_step_approval_required_before_any_execution(self):
        mutations = [dict(authorized_replicas=None), dict(authorized_replicas=[1, 2, 3]),
                     dict(authorized_replicas=[True]), dict(maximum_additional_MD_steps=30000),
                     dict(maximum_additional_MD_steps=True), dict(approved=False),
                     dict(plan_sha256='wrong'), dict(purpose='e2_smoke')]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.mocked_execution() as popen:
                self.write_approval(dict(self.record, **mutation))
                with self.assertRaises(ValueError):
                    e2.launch(self.root, self.attempt, True, self.approval, replica=1)
                popen.assert_not_called()
                self.assertFalse((self.attempt / 'r001/started.json').exists())

    def test_scoped_approval_cannot_launch_default_triplet(self):
        with self.mocked_execution() as popen:
            with self.assertRaisesRegex(ValueError, 'explicit selector required'):
                e2.launch(self.root, self.attempt, True, self.approval)
            popen.assert_not_called()

    def test_default_unscoped_launch_retains_three_history_behavior(self):
        record = dict(self.record)
        del record['authorized_replicas']
        del record['maximum_additional_MD_steps']
        self.write_approval(record)
        with self.mocked_execution() as popen:
            e2.launch(self.root, self.attempt, True, self.approval)
            self.assertEqual(popen.call_count, 3)

    def test_wrong_mode_target_replica_or_duration_is_rejected(self):
        for replica in (0, 2, 3, True, '1'):
            with self.subTest(replica=replica), self.assertRaises(ValueError):
                e2.launch_scope(self.plan, replica)
        for mutation in (dict(lineage_mode='ordinary'), dict(reference_control=False),
                         dict(smoke=False), dict(steps=0), dict(steps=10001),
                         dict(system=dict(system_id='F04_N010_RP080_EE08_EA06'))):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                e2.launch_scope(dict(self.plan, **mutation), 1)
        for histories in ([], self.plan['histories'] + [self.plan['histories'][0]]):
            with self.assertRaises(ValueError):
                e2.launch_scope(dict(self.plan, histories=histories), 1)

    def test_dry_run_shows_exactly_one_command_and_no_process(self):
        with self.mocked_execution() as popen, contextlib.redirect_stdout(io.StringIO()) as stdout:
            e2.launch(self.root, self.attempt, replica=1)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result['commands'], [self.plan['histories'][0]['command']])
            popen.assert_not_called()

    def test_used_unselected_directory_still_fails_closed(self):
        (self.attempt / 'r002/unexpected').write_text('fixture')
        with self.mocked_execution() as popen:
            with self.assertRaisesRegex(ValueError, 'attempt already used'):
                e2.launch(self.root, self.attempt, True, self.approval, replica=1)
            popen.assert_not_called()

    def test_live_plan_failure_prevents_execution(self):
        with self.mocked_execution() as popen:
            with mock.patch.object(e2, 'check_plan', side_effect=ValueError('source mismatch')):
                with self.assertRaisesRegex(ValueError, 'source mismatch'):
                    e2.launch(self.root, self.attempt, True, self.approval, replica=1)
            popen.assert_not_called()

    def test_scope_is_rechecked_immediately_before_start(self):
        def changed_approval(*args, **kwargs):
            self.write_approval(dict(self.record, authorized_replicas=[2]))
            return self.plan
        with self.mocked_execution() as popen:
            calls = 0

            def checked_plan(*args, **kwargs):
                nonlocal calls
                calls += 1
                return changed_approval() if calls == 2 else self.plan
            with mock.patch.object(e2, 'check_plan', side_effect=checked_plan):
                with self.assertRaisesRegex(ValueError, 'scope/cap differs'):
                    e2.launch(self.root, self.attempt, True, self.approval, replica=1)
            popen.assert_not_called()
            self.assertFalse((self.attempt / 'r001/started.json').exists())
