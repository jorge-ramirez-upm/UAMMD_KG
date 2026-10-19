"""Deterministic extension administration tests; every simulation launch is mocked."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import kg_assoc_e2 as e2
import kg_assoc_e2_extension as extension
import run_ea_extensions as runner
import test_e2_single_history as single

class ExtensionScopeTests(unittest.TestCase):
    setUp = single.SingleHistoryTests.setUp
    write_approval = single.SingleHistoryTests.write_approval

    def configure(self, ea=8):
        sid = f'F04_N010_RP080_EE08_EA{ea:02d}'
        steps = extension.DURATIONS[sid]
        self.plan.update(lineage_mode=extension.MODE, reference_control=False, smoke=False, steps=steps, system=dict(system_id=sid))
        self.plan['build'] = dict(source_sha256={'kg_assoc_stars.cu': 'cpu_fixture_native'})
        for entry in self.plan['histories']:
            entry.update(start_step=24000000, end_step=24000000 + steps)
        (self.attempt / 'plan.json').write_text(json.dumps(self.plan))
        self.record.update(purpose='e2_derived_extension', selector_scope=extension.SCOPE, plan_sha256=e2.campaign.sha256(self.attempt / 'plan.json'), authorized_system=sid, authorized_replicas=[2], maximum_additional_MD_steps_per_history=steps, maximum_additional_MD_steps=steps, absolute_start_step=24000000, absolute_end_step=24000000 + steps, diagnostic_window_steps=500000, GPU_execution_authorized=True)
        self.write_approval(self.record)

    @contextlib.contextmanager
    def execution(self, status=0):

        def start(command, stdout, stderr, **options):
            stdout.write('STAR_ASSOCIATION_SMOKE PASS\n')
            process = mock.Mock(pid=12345)
            process.wait.return_value = status
            return process
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(e2, 'check_plan', return_value=self.plan))
            stack.enter_context(mock.patch.object(e2, 'live_code'))
            stack.enter_context(mock.patch.object(e2, 'require_extension_readback_build'))
            stack.enter_context(mock.patch.object(e2, 'extension_source_authorization',
                                                  return_value={'source_sha256_overrides': {}}))
            stack.enter_context(mock.patch.object(e2, 'live_code'))
            stack.enter_context(mock.patch.object(e2, 'matching_smoke', return_value={}))
            stack.enter_context(mock.patch.object(e2.socket, 'gethostname', return_value='titan'))
            stack.enter_context(mock.patch.object(extension, 'revalidate_parent'))
            stack.enter_context(mock.patch.object(extension, 'process_identity', return_value=dict(pid=12345, boot_id='test', start_ticks='1')))
            stack.enter_context(mock.patch.object(e2.subprocess, 'check_output', return_value='mock GPU'))
            stack.enter_context(mock.patch.object(e2.validation, 'validate', return_value=([], [], {})))
            popen = stack.enter_context(mock.patch.object(e2.subprocess, 'Popen', side_effect=start))
            yield popen

    def test_exact_two_scopes_and_no_implicit_replicas(self):
        for ea in (8, 10):
            self.configure(ea)
            self.assertEqual([h['replica'] for h in e2.launch_scope(self.plan, None, [2])], [2])
            e2.scoped_launch_approval(self.approval, self.attempt, 'e2_derived_extension', self.plan, None, [2])
            for selection in (None, [], [True], [3, 1], [1, 1], [4]):
                with self.subTest(selection=selection), self.assertRaises(ValueError):
                    e2.launch_scope(self.plan, None, selection)
            with self.assertRaises(ValueError):
                e2.launch_scope(self.plan, 1)

    def test_wrong_target_steps_start_and_end_fail_closed(self):
        self.configure()
        for change in (dict(steps=16000001), dict(steps=16000000.0), dict(smoke=True), dict(reference_control=True), dict(system=dict(system_id=extension.transfer.TARGETS[0]))):
            with self.subTest(change=change), self.assertRaises(ValueError):
                e2.launch_scope(dict(self.plan, **change), None, [2])
        for (key, value) in [('start_step', 8000000), ('end_step', 40000001), ('replica', True)]:
            plan = copy.deepcopy(self.plan)
            plan['histories'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                e2.launch_scope(plan, None, [2])

    def test_tampered_approvals_never_launch(self):
        self.configure()
        changes = [dict(approved=False), dict(purpose='e2_derived_segment'), dict(plan_sha256='wrong'), dict(selector_scope='unrestricted'), dict(authorized_system=extension.transfer.TARGETS[0]), dict(authorized_replicas=[1, 2, 3]), dict(authorized_replicas=[True]), dict(maximum_additional_MD_steps=48000000), dict(maximum_additional_MD_steps_per_history=1), dict(absolute_start_step=8000000), dict(absolute_end_step=40000001), dict(diagnostic_window_steps=1000)]
        for change in changes:
            self.write_approval(dict(self.record, **change))
            with self.subTest(change=change), self.execution() as popen:
                with self.assertRaises(ValueError):
                    e2.launch(self.root, self.attempt, True, self.approval, replicas=[2])
                popen.assert_not_called()

    def test_selected_execution_preserves_unselected_and_used_attempts(self):
        self.configure(10)
        sentinel = self.attempt / 'r001/preserved'
        sentinel.write_text('earlier history')
        with self.execution() as popen:
            e2.launch(self.root, self.attempt, True, self.approval, replicas=[2])
            self.assertEqual(popen.call_count, 1)
            self.assertTrue(callable(popen.call_args.kwargs['preexec_fn']))
        self.assertEqual(sentinel.read_text(), 'earlier history')
        self.assertEqual(list((self.attempt / 'r003').iterdir()), [])
        self.assertTrue((self.attempt / 'r002/process.json').exists())
        self.assertTrue((self.attempt / 'r002/complete.json').exists())
        with self.execution() as popen, self.assertRaisesRegex(ValueError, 'attempt already used'):
            e2.launch(self.root, self.attempt, True, self.approval, replicas=[2])
        popen.assert_not_called()

    def test_first_failure_preserved_and_remaining_unstarted(self):
        self.configure()
        with self.execution(status=1) as popen, self.assertRaisesRegex(ValueError, 'MD executable failed'):
            e2.launch(self.root, self.attempt, True, self.approval, replicas=[2])
        self.assertEqual(popen.call_count, 1)
        self.assertTrue((self.attempt / 'r002/incomplete.json').exists())
        self.assertEqual(list((self.attempt / 'r001').iterdir()), [])
        self.assertEqual(list((self.attempt / 'r003').iterdir()), [])

    def test_command_keeps_chemistry_and_uses_diagnostic_executable(self):
        entry = dict(parent=dict(kind='e2', prefix='/qualified24M'), parent_Ea=10, physics=dict(Ea=10), start_step=24000000, end_step=56000000, lineage=dict(mode=extension.MODE, branch_id='family'), chemistry_seed=1321001, md_seed=9999999, output_prefix='/fresh/state')
        command = e2.command(entry, False)
        self.assertTrue(command[0].endswith('kg_assoc_stars_candidate_smoke'))
        self.assertIn('--e2-extension', command)
        self.assertNotIn('--reseed-chemistry-from', command)
        self.assertNotIn('--switch-ea-from', command)
        self.assertEqual(command[command.index('--seed') + 1], '1321001')
        self.assertEqual(command[command.index('--steps') + 1], '32000000')

    def test_preparation_approval_cannot_launch_GPU(self):
        self.configure()
        self.write_approval(dict(self.record, GPU_execution_authorized=False))
        with self.execution() as popen, self.assertRaisesRegex(ValueError, 'pending separate'):
            e2.launch(self.root, self.attempt, True, self.approval, replicas=[2])
        popen.assert_not_called()
        for replica in (1, 2, 3):
            self.assertEqual(list((self.attempt / f'r{replica:03d}').iterdir()), [])


class SourceAuthorizationTests(unittest.TestCase):

    def test_exact_map_rejects_missing_extra_physics_and_nonancestor_sources(self):
        plan = dict(lineage_mode=extension.MODE, git_sha='prepared', executable_sha256={},
                    source_sha256={'admin.py': 'old-admin', 'physics.cuh': 'frozen'})
        overrides = {'admin.py': 'new-admin'}

        def check(current, ancestor=True, succeeds=True):
            result = mock.Mock(returncode=0 if ancestor else 1)
            with mock.patch.object(e2, 'clean_tree'), mock.patch.object(e2, 'sources', return_value=current), \
                    mock.patch.object(e2.campaign, 'git_sha', return_value='live'), \
                    mock.patch.object(e2.subprocess, 'run', return_value=result), \
                    mock.patch.object(e2, 'check_hashes'):
                if succeeds:
                    e2.live_code(plan, overrides)
                else:
                    with self.assertRaisesRegex(ValueError, 'prepared extension sources/history changed'):
                        e2.live_code(plan, overrides)

        check({'admin.py': 'new-admin', 'physics.cuh': 'frozen'})
        check({'admin.py': 'new-admin'}, succeeds=False)
        check({'admin.py': 'new-admin', 'physics.cuh': 'frozen', 'extra.py': 'extra'}, succeeds=False)
        check({'admin.py': 'new-admin', 'physics.cuh': 'modified'}, succeeds=False)
        check({'admin.py': 'new-admin', 'physics.cuh': 'frozen'}, ancestor=False, succeeds=False)

class LifecycleTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'r001'
        self.directory.mkdir()
        self.job = dict(system=list(extension.DURATIONS)[0], replica=1, steps=16000000, end_step=40000000, status='running', attempt=str(self.root), plan_sha256='plan', approval_sha256='preparation', execution_approval_sha256='approval', retired_attempts=[])
        self.entry = dict(output_prefix=str(self.directory / 'state'), command=['mock_only'])
        self.patcher = mock.patch.object(
            runner, 'execution_approval',
            return_value=(Path('approval_execution.json'), Path('source_authorization.json'), {}, self.entry))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def started(self):
        e2.exclusive_json(self.directory / 'started.json', dict(plan_sha256='plan', approval_sha256='approval', command=['mock_only'], smoke_sha256={}))

    def test_prepared_partial_and_failure_classification(self):
        self.assertEqual(runner.classify(self.job), 'prepared')
        self.started()
        (self.directory / 'state.state').write_text('partial')
        self.assertEqual(runner.classify(self.job), 'interrupted')
        (self.directory / 'state.candidate_mismatch.tsv').write_text('actual differing pairs')
        with self.assertRaisesRegex(ValueError, 'failure preserved'):
            runner.classify(self.job)

    def test_untrusted_partial_is_not_an_automatic_retry(self):
        (self.directory / 'state.state').write_text('unexplained output')
        with self.assertRaisesRegex(ValueError, 'authenticated start'):
            runner.classify(self.job)

    def test_completed_receipt_is_independently_replayed_without_MD(self):
        e2.exclusive_json(self.directory / 'complete.json', dict(status='validated', end_step=40000000, plan_sha256='plan', output_sha256={}, validation={'checked': True}))
        with mock.patch.object(e2.validation, 'validate', return_value=([], [], {'checked': True})) as validate, mock.patch.object(e2, 'launch') as launch:
            self.assertEqual(runner.classify(self.job), 'complete')
            validate.assert_called_once_with(self.entry, oracle=True)
            launch.assert_not_called()

    def test_finished_MD_receipt_cannot_be_promoted_by_generic_execution(self):
        self.started()
        (self.directory / 'stdout.log').write_text('STAR_ASSOCIATION_SMOKE PASS\n')
        before = set(self.directory.iterdir())
        self.assertEqual(runner.classify(self.job, recover=False), 'finished_pending_independent_validation')
        self.assertEqual(set(self.directory.iterdir()), before)
        with self.assertRaisesRegex(ValueError, 'explicit --recover-ea8-r001'):
            runner.classify(self.job, recover=True)
        self.assertFalse((self.directory / 'complete.json').exists())

    def test_recovery_record_is_distinct_and_replayed(self):
        failure = self.directory / 'incomplete.json'
        e2.exclusive_json(failure, dict(error=runner.RECOVERY_FAILURE))
        (self.directory / 'evidence').write_text('immutable')
        output_hashes = e2.hash_files([self.directory / 'evidence'])
        e2.exclusive_json(self.directory / runner.RECOVERY_RECORD, dict(
            schema_version=1, status='independently_validated_recovery', plan_sha256='plan',
            end_step=40000000, execution_approval_sha256='approval',
            source_authorization_sha256='source',
            original_incomplete_sha256=e2.campaign.sha256(failure),
            original_failure=runner.RECOVERY_FAILURE, output_sha256=output_hashes,
            validation={'checked': True}))
        self.job['source_authorization_sha256'] = 'source'
        with mock.patch.object(e2.validation, 'validate', return_value=([], [], {'checked': True})):
            self.assertEqual(runner.classify(self.job), 'recovered_complete')
        self.assertFalse((self.directory / 'complete.json').exists())
        (self.directory / 'evidence').write_text('forged')
        with self.assertRaisesRegex(ValueError, 'authenticated file changed'):
            runner.classify(self.job)

    def test_numerical_failure_overrides_a_completion_receipt(self):
        e2.exclusive_json(self.directory / 'complete.json', dict(status='validated', end_step=40000000, plan_sha256='plan', output_sha256={}, validation={}))
        e2.exclusive_json(self.directory / 'incomplete.json', dict(error='real numerical failure'))
        with self.assertRaisesRegex(ValueError, 'failed trajectory'):
            runner.classify(self.job)

    def test_active_native_process_prevents_duplicate_execution(self):
        with mock.patch.object(extension, 'native_running', return_value=True):
            self.assertEqual(runner.classify(self.job), 'running')

    def test_partial_work_bounds_do_not_claim_an_exact_step_count(self):
        p = self.directory / 'state.candidate_validation.tsv'
        p.write_text('# recorded sweep\n24000100 20 3\n24000200 20 3\n24000300 2')
        bounds = extension.partial_step_bounds(self.directory / 'state', 16000000)
        self.assertEqual(bounds['completed_MD_steps_lower_bound'], 200)
        self.assertEqual(bounds['authorized_MD_steps_upper_bound'], 16000000)
        self.assertFalse(bounds['exact_partial_MD_steps_known'])

    def test_state_cannot_expand_scope_or_remove_caps(self):
        state = dict(schema_version=1, scope=extension.SCOPE, jobs=runner.jobs(), plans={}, restart_overhead_authorized=True, completed_extension_cap=144000000)
        runner.validate_state(state)
        self.assertEqual(sum((j['steps'] for j in state['jobs'])), 144000000)
        for change in [dict(completed_extension_cap=144000001), dict(restart_overhead_authorized=False), dict(jobs=state['jobs'][:-1])]:
            with self.assertRaises(ValueError):
                runner.validate_state(dict(state, **change))

    def test_atomic_receipt_never_overwrites(self):
        path = self.directory / 'receipt.json'
        extension.atomic_receipt(path, {'a': 1})
        with self.assertRaises(FileExistsError):
            extension.atomic_receipt(path, {'a': 2})
        self.assertEqual(e2.campaign.load_json(path), {'a': 1})

class CompatibilityTests(unittest.TestCase):

    def test_exact_transition_and_frozen_physics(self):
        review = e2.campaign.load_json(extension.REVIEW / 'PROVENANCE.log')
        parent = e2.campaign.load_json(Path(review['histories'][3]['attempt']) / 'plan.json')
        plan = dict(source_sha256=e2.sources(), executable_sha256=parent['executable_sha256'])
        self.assertTrue(extension.code_compatible(parent, plan))
        changed = copy.deepcopy(plan)
        key = str(e2.HERE.parent / 'kg_assoc_kinetics.cuh')
        changed['source_sha256'][key] = 'changed physics'
        self.assertFalse(extension.code_compatible(parent, changed))
        changed = copy.deepcopy(plan)
        changed['source_sha256'][str(e2.HERE.parent / 'kg_assoc_stars.cu')] = 'changed native'
        self.assertFalse(extension.code_compatible(parent, changed))

    def test_linux_process_birth_identity_and_reuse(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'process.json'
            record = extension.process_identity(os.getpid())
            record.update(plan_sha256='plan', command=['fixture'])
            e2.exclusive_json(path, record)
            self.assertTrue(extension.native_running(path, 'plan', ['fixture']))
            record['start_ticks'] = 'not this birth'
            path.write_text(json.dumps(record))
            self.assertFalse(extension.native_running(path, 'plan', ['fixture']))

    def test_parent_death_supervision_with_short_CPU_child(self):
        with tempfile.TemporaryDirectory() as temp:
            pidfile = Path(temp) / 'pid'
            code = "import os,subprocess,sys,time;sys.path.insert(0,sys.argv[1]);import kg_assoc_e2_extension as e;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],preexec_fn=e.parent_death_guard(os.getpid()));open(sys.argv[2],'w').write(str(p.pid));p.wait()"
            parent = subprocess.Popen([sys.executable, '-c', code, str(e2.HERE), str(pidfile)])
            child = None
            try:
                deadline = time.monotonic() + 5
                while not pidfile.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(pidfile.exists())
                child = int(pidfile.read_text())
                parent.kill()
                parent.wait(timeout=5)
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    stat = Path(f'/proc/{child}/stat')
                    if not stat.exists() or stat.read_text().rsplit(')', 1)[1].split()[0] == 'Z':
                        break
                    time.sleep(0.02)
                else:
                    self.fail('child survived death of CPU parent')
            finally:
                if parent.poll() is None:
                    parent.kill()
                    parent.wait(timeout=5)
                if child:
                    try:
                        os.kill(child, 15)
                    except ProcessLookupError:
                        pass

class ExecuteLifecycleTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'manual/state.json'
        self.bound = []
        self.done = set()
        self.calls = 0

    def bind(self, root, directory, state, job, build):
        attempt = directory / f'attempt_{len(self.bound)}'
        self.bound.append(attempt)
        replica = attempt / f"r{job['replica']:03d}"
        replica.mkdir(parents=True)
        e2.exclusive_json(attempt / 'MD_RESERVATION.json', dict(md_seed=9000000 + len(self.bound)))
        job.update(attempt=str(attempt), approval=str(attempt / 'approval.json'), plan_sha256='plan', approval_sha256='approval', status='prepared')

    def classify(self, job, **kwargs):
        if job.get('attempt') in self.done:
            return 'complete'
        return 'interrupted' if job['status'] == 'interrupted' else 'prepared'

    def launch(self, root, attempt, **kwargs):
        self.calls += 1
        if self.calls == 2:
            replica = attempt / 'r002'
            e2.exclusive_json(replica / 'started.json', dict(mocked_only=True))
            (replica / 'state.candidate_validation.tsv').write_text('# steps\n24000100 20 3\n')
            raise KeyboardInterrupt
        self.done.add(str(attempt))

    def test_same_command_preserves_partial_reservation_and_restarts_only_that_slot(self):
        with mock.patch.object(runner, 'bind', side_effect=self.bind), mock.patch.object(runner, 'classify', side_effect=self.classify), mock.patch.object(runner, 'execution_approval', return_value=(Path('approval.json'), Path('source.json'), {}, {})), mock.patch.object(e2, 'launch', side_effect=self.launch):
            self.assertEqual(runner.execute(self.root, self.root, self.path), 130)
        first = e2.campaign.load_json(self.path)
        old = Path(first['jobs'][1]['attempt'])
        before = {str(p): p.read_bytes() for p in old.rglob('*') if p.is_file()}
        self.assertEqual([j['status'] for j in first['jobs'][:3]], ['complete', 'interrupted', 'prepared'])
        with mock.patch.object(runner, 'bind', side_effect=self.bind), mock.patch.object(runner, 'classify', side_effect=self.classify), mock.patch.object(runner, 'execution_approval', return_value=(Path('approval.json'), Path('source.json'), {}, {})), mock.patch.object(e2, 'launch', side_effect=self.launch) as launch:
            self.assertEqual(runner.execute(self.root, self.root, self.path), 0)
            self.assertEqual(launch.call_count, 5)
        final = e2.campaign.load_json(self.path)
        self.assertTrue(all((j['status'] == 'complete' for j in final['jobs'])))
        self.assertNotEqual(final['jobs'][1]['attempt'], str(old))
        self.assertEqual(final['jobs'][0]['attempt'], first['jobs'][0]['attempt'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in old.rglob('*') if p.is_file()})
        retired = final['jobs'][1]['retired_attempts'][0]
        self.assertEqual(retired['completed_MD_steps_lower_bound'], 100)
        self.assertEqual(retired['authorized_MD_steps_upper_bound'], 16000000)
        with mock.patch.object(runner, 'classify', return_value='complete'), mock.patch.object(runner, 'execution_approval', return_value=(Path('approval.json'), Path('source.json'), {}, {})), mock.patch.object(e2, 'launch') as launch:
            self.assertEqual(runner.execute(self.root, self.root, self.path), 0)
            launch.assert_not_called()

    def test_genuine_failure_stops_all_future_starts(self):
        with mock.patch.object(runner, 'bind', side_effect=self.bind), mock.patch.object(runner, 'classify', return_value='prepared'), mock.patch.object(runner, 'execution_approval', return_value=(Path('approval.json'), Path('source.json'), {}, {})), mock.patch.object(e2, 'launch', side_effect=ValueError('oracle mismatch')) as launch:
            with self.assertRaisesRegex(ValueError, 'oracle mismatch'):
                runner.execute(self.root, self.root, self.path)
            self.assertEqual(launch.call_count, 1)
        bound = len(self.bound)
        with mock.patch.object(runner, 'bind', side_effect=self.bind), mock.patch.object(runner, 'execution_approval', return_value=(Path('approval.json'), Path('source.json'), {}, {})), mock.patch.object(e2, 'launch') as launch:
            with self.assertRaisesRegex(ValueError, 'campaign held'):
                runner.execute(self.root, self.root, self.path)
            launch.assert_not_called()
        self.assertEqual(len(self.bound), bound)

    def test_check_and_status_are_read_only_and_never_launch(self):
        with mock.patch.object(runner.run_e2, 'discover', return_value=self.root), mock.patch.object(e2, 'clean_tree'), mock.patch.object(e2, 'check_build'), mock.patch.object(e2, 'require_extension_readback_build'), mock.patch.object(e2.campaign, 'load_json', return_value={'source_sha256': {'kg_assoc_stars.cu': 'cpu_fixture_native'}}), mock.patch.object(extension, 'predecessor'), mock.patch.object(e2, 'launch') as launch, contextlib.redirect_stdout(io.StringIO()):
            for option in ('--check', '--status'):
                with mock.patch.object(sys, 'argv', ['run_ea_extensions.py', option]):
                    self.assertEqual(runner.main(), 0)
            launch.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [])

class MDReservationTests(unittest.TestCase):

    def test_fresh_reservations_and_original_allocator_exclude_unused_streams(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sid = next(iter(extension.DURATIONS))
            first = root / 'banks/e2_attempts/F04_N010_RP080_EE08' / ('extension_' + sid + '_one')
            second = first.with_name('extension_' + sid + '_two')
            one = extension.reserve_md(root, first, sid)
            two = extension.reserve_md(root, second, sid)
            a = e2.campaign.load_json(one)
            b = e2.campaign.load_json(two)
            self.assertFalse({r['md_seed'] for r in a['streams']} & {r['md_seed'] for r in b['streams']})
            reserved = {r['effective_md_seed'] for p in (a, b) for r in p['streams']}
            self.assertFalse(reserved & {e2.validation.effective_md_seed(s) for s in e2.allocate_md_seeds(root)})
            self.assertTrue(all(('chemistry_seed' not in r for p in (a, b) for r in p['streams'])))
            b['streams'][0]['md_seed'] = a['streams'][0]['md_seed']
            b['streams'][0]['effective_md_seed'] = a['streams'][0]['effective_md_seed']
            two.write_text(json.dumps(b))
            with self.assertRaisesRegex(ValueError, 'collid'):
                extension.reservation(root, two, second, sid)

class FrozenPhysicalSourceTests(unittest.TestCase):
    def test_physical_loader_and_integration_tail_are_byte_identical(self):
        old = subprocess.check_output(['git', 'show',
            'ceb4048a00897b8c335d718d885f9e14ac2c37e7:examples/KG_Assoc/kg_assoc_stars.cu'],
            text=True, cwd=e2.campaign.REPOSITORY_ROOT)
        current = (e2.HERE.parent / 'kg_assoc_stars.cu').read_text()
        current = current.replace('    kg_assoc_test::dispatchInitialReadback(\n        parameters.reseedChemistry, parameters.e2Extension, [&]() {\n          initialDeviceReadback(parameters, data, simulationBox, particles, state, lengths,\n                                diagnosticContext);\n        });', '    if (parameters.reseedChemistry) {\n      initialDeviceReadback(parameters, data, simulationBox, particles, state, lengths,\n                            diagnosticContext);\n    }')
        marker = '      const double requestedEa = targetEa;'
        self.assertEqual(old.split(marker, 1)[1], current.split(marker, 1)[1])
        marker = 'void initialDeviceReadback('
        self.assertEqual(old[old.index(marker):old.index('int main(')],
                         current[current.index(marker):current.index('int main(')])


class PreparedParentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = e2.HERE.parent / 'kg_assoc_100m'
        state = cls.root / 'aggregate/e2' / runner.STATE_DIRECTORY / 'state.json'
        if not state.exists():
            raise unittest.SkipTest('real CPU-only preparation is not yet present')
        cls.jobs = e2.campaign.load_json(state)['jobs']
        if any(job['status'] != 'prepared' for job in cls.jobs):
            raise unittest.SkipTest('pre-execution fixtures no longer apply after user-run MD')

    def test_all_six_prepared_histories_are_empty_and_exactly_bound(self):
        for job in self.jobs:
            (plan, entry) = runner.authenticate(job)
            self.assertEqual(entry['start_step'], 24000000)
            self.assertEqual(entry['end_step'], job['end_step'])
            self.assertEqual(entry['end_step'] - entry['start_step'], job['steps'])
            self.assertEqual(list(Path(entry['output_prefix']).parent.iterdir()), [])
            (_, initial) = e2.validation.read_parent(entry)
            self.assertEqual(initial['creations'], entry['lineage']['parent_creations'])
            self.assertEqual(initial['breaks'], entry['lineage']['parent_breaks'])

    def test_execution_approval_requires_the_unchanged_preparation_approval(self):
        for job in self.jobs:
            approval, source_authorization, plan, entry = runner.execution_approval(job)
            self.assertTrue(approval.name.endswith('_execution.json'))
            self.assertTrue(source_authorization.name.endswith('_source_authorization.json'))
            self.assertEqual(plan['system']['system_id'], job['system'])
            self.assertEqual(entry['replica'], job['replica'])
            record = e2.campaign.load_json(approval)
            self.assertTrue(record['GPU_execution_authorized'])
            self.assertEqual(record['preparation_approval_sha256'], job['approval_sha256'])

    def test_parent_seed_family_counter_and_output_tampering_are_rejected(self):
        (_, entry) = runner.authenticate(self.jobs[0])
        for (field, value) in [('chemistry_seed', entry['chemistry_seed'] + 1), ('md_seed', entry['md_seed'] + 1), ('start_step', 8000000), ('end_step', 40000001)]:
            bad = copy.deepcopy(entry)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                e2.validation.read_parent(bad)
        for (field, value) in [('parent_creations', entry['lineage']['parent_creations'] + 1), ('original_parent_replica', 2), ('branch_id', 'tampered')]:
            bad = copy.deepcopy(entry)
            bad['lineage'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                e2.validation.read_parent(bad)

    def test_native_host_checks_return_without_any_MD_output(self):
        for job in self.jobs:
            (_, entry) = runner.authenticate(job)
            output = subprocess.check_output(entry['command'] + ['--validate-initial-state'], text=True, timeout=60)
            self.assertIn('INITIAL_STATE_VALIDATED', output)
            self.assertEqual(list(Path(entry['output_prefix']).parent.iterdir()), [])

    def test_native_rejects_wrong_duration_reseeding_barrier_family_and_overrides(self):
        (_, entry) = runner.authenticate(self.jobs[0])
        base = entry['command']
        variants = []
        for (flag, value) in [('--steps', '32000000'), ('--seed', str(entry['chemistry_seed'] + 1)), ('--Ea', '6'), ('--derived-branch-id', entry['lineage']['branch_id'][:-1] + '2')]:
            bad = base[:]
            bad[bad.index(flag) + 1] = value
            variants.append(bad)
        variants += [base + ['--dt', '.02'], base + ['--reseed-chemistry-from', str(entry['chemistry_seed'])]]
        for command in variants:
            result = subprocess.run(command + ['--validate-initial-state'], capture_output=True, text=True, timeout=60)
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(Path(entry['output_prefix']).parent.iterdir()), [])
if __name__ == '__main__':
    unittest.main()
