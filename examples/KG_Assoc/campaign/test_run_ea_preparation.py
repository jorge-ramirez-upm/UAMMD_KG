"""User-run lifecycle fixtures: all launches mocked; no GPU execution."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import kg_assoc_e2 as e2
import run_ea_preparation as runner
import test_e2_derived_preparation as derived


class SelectedPreparationTests(unittest.TestCase):
    setUp = derived.DerivedPreparationTests.setUp
    configure = derived.DerivedPreparationTests.configure
    write_approval = derived.DerivedPreparationTests.write_approval
    mocked_execution = derived.DerivedPreparationTests.mocked_execution

    def test_single_replica_scope_and_unselected_outputs_are_preserved(self):
        self.configure()
        self.record.update(authorized_replicas=[2], maximum_additional_MD_steps=16000000)
        self.write_approval(self.record)
        sentinel = self.attempt / 'r001/previous_output'
        sentinel.write_text('preserve')
        with self.mocked_execution() as popen, mock.patch.object(
                e2.socket, 'gethostname', return_value='titan'), mock.patch.object(
                e2, 'matching_smoke', return_value={}):
            e2.launch(self.root, self.attempt, True, self.approval, replicas=[2])
            self.assertEqual(popen.call_count, 1)
            self.assertEqual(popen.call_args.args[0], self.plan['histories'][1]['command'])
        self.assertEqual(sentinel.read_text(), 'preserve')
        self.assertEqual(list((self.attempt / 'r003').iterdir()), [])
        with self.assertRaises(ValueError):
            e2.scoped_launch_approval(self.approval, self.attempt, 'e2_derived_segment',
                                     self.plan, None)

    def test_subsets_are_bound_exactly_and_cannot_implicitly_expand(self):
        self.configure()
        for selection in ([1], [2], [3], [1, 3], [1, 2, 3]):
            self.record.update(authorized_replicas=selection,
                               maximum_additional_MD_steps=16000000 * len(selection))
            self.write_approval(self.record)
            self.assertEqual([h['replica'] for h in e2.launch_scope(self.plan, None, selection)],
                             selection)
            e2.scoped_launch_approval(self.approval, self.attempt, 'e2_derived_segment',
                                     self.plan, None, selection)
        for selection in ([True], [1, 1], [3, 1], [], [0], [4]):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                e2.launch_scope(self.plan, None, selection)


class ManualLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'r001'
        self.directory.mkdir()
        self.job = dict(system=runner.transfer.TARGETS[0], replica=1, status='running',
                        attempt=str(self.root), plan_sha256='plan', approval_sha256='approval')
        self.entry = dict(output_prefix=str(self.directory / 'state'), command=['mock_only'])
        self.patch = mock.patch.object(runner, 'authenticate', return_value=({}, self.entry))
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_empty_prepared_partial_and_numerical_failure_classification(self):
        self.assertEqual(runner.classify(self.job), 'prepared')
        (self.directory / 'state.state').write_text('interrupted partial fixture')
        self.assertEqual(runner.classify(self.job), 'interrupted')
        e2.exclusive_json(self.directory / 'incomplete.json', dict(error=''))
        self.assertEqual(runner.classify(self.job), 'interrupted')
        (self.directory / 'stderr.log').write_text('STAR_ASSOCIATION_SMOKE FAIL: mismatch')
        with self.assertRaisesRegex(ValueError, 'numerical failure'):
            runner.classify(self.job)

    def test_nonempty_failure_or_mismatch_evidence_never_triggers_new_seed_retry(self):
        e2.exclusive_json(self.directory / 'incomplete.json', dict(error='MD executable failed'))
        with self.assertRaisesRegex(ValueError, 'no automatic seed retry'):
            runner.classify(self.job)
        (self.directory / 'incomplete.json').unlink()
        (self.directory / 'state.candidate_mismatch.tsv').write_text('preserve failure')
        with self.assertRaisesRegex(ValueError, 'numerical failure'):
            runner.classify(self.job)

    def test_completed_receipt_is_validated_without_launch(self):
        e2.exclusive_json(self.directory / 'complete.json', dict(
            status='validated', plan_sha256='plan', end_step=24000000, output_sha256={}))
        with mock.patch.object(e2.validation, 'validate') as validate, mock.patch.object(
                e2, 'launch') as launch:
            self.assertEqual(runner.classify(self.job), 'complete')
            validate.assert_called_once_with(self.entry, oracle=True)
            launch.assert_not_called()

    def test_post_md_interrupt_recovers_receipt_without_repeating_md(self):
        (self.directory / 'stdout.log').write_text('STAR_ASSOCIATION_SMOKE PASS\n')
        e2.exclusive_json(self.directory / 'started.json', dict(plan_sha256='plan',
            approval_sha256='approval', command=['mock_only'], smoke_sha256={}))
        with mock.patch.object(e2.validation, 'validate', return_value=([], [], {})), mock.patch.object(
                e2, 'launch') as launch:
            self.assertEqual(runner.classify(self.job), 'complete')
            self.assertTrue((self.directory / 'complete.json').exists())
            launch.assert_not_called()

    def test_scope_is_exact_nine_and_atomic_status_updates_do_not_overwrite_outputs(self):
        jobs = runner.jobs()
        self.assertEqual([(j['system'], j['replica']) for j in jobs],
                         [(sid, r) for sid in runner.transfer.TARGETS for r in (1, 2, 3)])
        path = self.root / 'state.json'
        runner.save(path, dict(status='running'))
        runner.save(path, dict(status='interrupted'))
        self.assertEqual(e2.campaign.load_json(path)['status'], 'interrupted')
        self.assertEqual(list(self.root.glob('*.tmp')), [])


class ManualExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'manual/state.json'
        self.bound = []

    def bind(self, root, directory, state, job, build):
        attempt = directory / ('attempt_' + str(len(self.bound)))
        self.bound.append(str(attempt))
        job.update(attempt=str(attempt), approval=str(attempt / 'approval.json'),
                   plan_sha256='fixture', approval_sha256='fixture', status='prepared')

    def test_same_command_skips_completed_and_replaces_only_interrupted_history(self):
        def classify(job):
            return 'complete' if job['status'] == 'complete' else (
                'interrupted' if job['status'] == 'interrupted' else 'pending')
        with mock.patch.object(runner, 'bind_job', side_effect=self.bind), mock.patch.object(
                runner, 'classify', side_effect=classify), mock.patch.object(
                e2, 'launch', side_effect=[None, KeyboardInterrupt()]) as launch:
            self.assertEqual(runner.execute(self.root, self.root, self.path), 130)
            self.assertEqual(launch.call_count, 2)
        first = e2.campaign.load_json(self.path)
        self.assertEqual([j['status'] for j in first['jobs'][:3]],
                         ['complete', 'interrupted', 'pending'])
        old_attempt = first['jobs'][1]['attempt']
        with mock.patch.object(runner, 'bind_job', side_effect=self.bind), mock.patch.object(
                runner, 'classify', side_effect=classify), mock.patch.object(e2, 'launch') as launch:
            self.assertEqual(runner.execute(self.root, self.root, self.path), 0)
            self.assertEqual(launch.call_count, 8)
        final = e2.campaign.load_json(self.path)
        self.assertTrue(all(j['status'] == 'complete' for j in final['jobs']))
        self.assertEqual(final['jobs'][0]['attempt'], first['jobs'][0]['attempt'])
        self.assertNotEqual(final['jobs'][1]['attempt'], old_attempt)
        self.assertEqual(final['jobs'][1]['retired_attempts'][0]['attempt'], old_attempt)
        with mock.patch.object(runner, 'classify', return_value='complete'), mock.patch.object(
                e2, 'launch') as launch:
            self.assertEqual(runner.execute(self.root, self.root, self.path), 0)
            launch.assert_not_called()

    def test_genuine_failure_stops_campaign_and_subsequent_invocation(self):
        with mock.patch.object(runner, 'bind_job', side_effect=self.bind), mock.patch.object(
                runner, 'classify', return_value='pending'), mock.patch.object(
                e2, 'launch', side_effect=ValueError('oracle mismatch')) as launch:
            with self.assertRaisesRegex(ValueError, 'oracle mismatch'):
                runner.execute(self.root, self.root, self.path)
            self.assertEqual(launch.call_count, 1)
        with mock.patch.object(e2, 'launch') as launch:
            with self.assertRaisesRegex(ValueError, 'campaign held'):
                runner.execute(self.root, self.root, self.path)
            launch.assert_not_called()


class ReservationAndPreparationTests(unittest.TestCase):
    def test_fresh_reservations_exclude_all_prior_requested_and_effective_streams(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(runner.transfer, 'streams_in_use',
                                   return_value=(set(), set(), set(), [])), mock.patch.object(
                    runner.transfer, 'reserved_streams'):
                first = runner.fresh_reservation(root)
                second = runner.fresh_reservation(root)
            one = e2.campaign.load_json(first)['streams']
            two = e2.campaign.load_json(second)['streams']
            self.assertNotEqual(first, second)
            self.assertFalse({r[k] for r in one for k in ('chemistry_seed', 'md_seed')} &
                             {r[k] for r in two for k in ('chemistry_seed', 'md_seed')})
            self.assertFalse({e2.validation.effective_md_seed(r['md_seed']) for r in one} &
                             {e2.validation.effective_md_seed(r['md_seed']) for r in two})

    def test_existing_unused_approval_is_authenticated_and_reused_after_prepare_interrupt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            replica_dir = root / 'r001'
            replica_dir.mkdir()
            e2.exclusive_json(root / 'plan.json', dict(fixture=True))
            sid = runner.transfer.TARGETS[0]
            plan = dict(git_sha='fixture', histories=[dict(output_prefix=str(replica_dir/'state'))])
            state = dict(plans={sid:str(root)})
            with mock.patch.object(e2, 'check_plan', return_value=plan), mock.patch.object(
                    e2.campaign, 'git_sha', return_value='fixture'), mock.patch.object(
                    e2, 'scoped_launch_approval'):
                first = dict(system=sid, replica=1)
                runner.bind_job(root, root, state, first, root)
                approval = Path(first['approval'])
                before = approval.read_bytes()
                second = dict(system=sid, replica=1)
                runner.bind_job(root, root, state, second, root)
                self.assertEqual(approval.read_bytes(), before)
                self.assertEqual(first['approval_sha256'], second['approval_sha256'])
