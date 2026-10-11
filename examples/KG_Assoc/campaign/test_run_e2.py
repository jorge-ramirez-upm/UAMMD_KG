"""Administrative workflow regression tests: no NVIDIA GPU or MD execution."""

import copy
from contextlib import ExitStack
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_e2 as cli

E = cli.e2
C = cli.campaign


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.system = E.system_by_id(cli.SMOKE_SYSTEMS[0])

    def journal(self):
        path = self.root / 'journal'
        E.exclusive_json(path / 'request.json', {'invocation': ['run_e2.py', 'smoke-all']})
        return path

    def plan(self, path, system=None):
        system = system or self.system
        parents = [dict(kind='e1', sha256={'input': 'authenticated'}, snapshot='input') for _ in range(3)]
        plan = dict(smoke=True, steps=10000, preparation_Ea=system['Ea'], system=system,
                    source_sha256={'model.cuh': 'physics', 'kg_assoc_e2.py': 'old-admin'},
                    executable_sha256={'binary': 'executable'},
                    histories=[dict(parent=p, chemistry_seed=seed,
                               physics=E.validation.physics(system, system['Ea']))
                               for p, seed in zip(parents, E.seed_map()[C.e2_bank_id(system)])])
        E.exclusive_json(path / 'plan.json', plan)
        return plan, parents

    def test_paths_discovered_independent_of_cwd_and_wrong_branch_rejected(self):
        script = self.root / 'examples/KG_Assoc/campaign/run_e2.py'
        script.parent.mkdir(parents=True)
        dataset = self.root / 'examples/KG_Assoc/kg_assoc_100m'
        E.exclusive_json(dataset / 'campaign_protocol.json', C.load_json(C.PROTOCOL_PATH))
        E.exclusive_json(dataset / 'manifest.json', dict(systems=[s['system_id'] for s in C.campaign_systems()]))
        with mock.patch.object(cli.subprocess, 'check_output', return_value='KremerGrest\n') as git:
            self.assertEqual(cli.discover(script), dataset)
            self.assertEqual(git.call_args.kwargs['cwd'], self.root)
        with mock.patch.object(cli.subprocess, 'check_output', return_value='main\n'):
            with self.assertRaisesRegex(ValueError, 'KremerGrest'):
                cli.discover(script)

    def test_build_reuse_and_incompatible_rebuild(self):
        old = self.root / 'builds/old'
        E.exclusive_json(old / 'manifest.json', {})
        with mock.patch.object(E, 'clean_tree'), mock.patch.object(E, 'live_code'), \
                mock.patch.object(E, 'check_build'), mock.patch.object(E, 'build') as build:
            self.assertEqual(cli.ensure_build(self.root), old)
            build.assert_not_called()
        def check(path):
            if path == old:
                raise ValueError('stale executable')
        with mock.patch.object(E, 'clean_tree'), mock.patch.object(E, 'check_build', side_effect=check), \
                mock.patch.object(E, 'build') as build:
            new = cli.ensure_build(self.root)
            self.assertNotEqual(new, old)
            build.assert_called_once_with(self.root, new)
            self.assertTrue((old / 'manifest.json').exists())

    def test_build_reuse_across_administrative_commits_keeps_original_provenance(self):
        path = self.root/'build'
        original = dict(schema_version=1, status='built', git_sha='ancestor',
                        source_sha256={'model.cuh': 'same', 'run_e2.py': 'old'},
                        executable_sha256={str((E.HERE.parent/n).resolve()): 'same' for n in E.BUILD_TARGETS},
                        build_log_sha256={'log': 'same'})
        E.exclusive_json(path/'manifest.json', original)
        current = {'model.cuh': 'same', 'run_e2.py': 'new', 'test_new.py': 'new'}
        with mock.patch.object(C, 'git_sha', return_value='current'), \
                mock.patch.object(E, 'sources', return_value=current), \
                mock.patch.object(E, 'check_hashes'), \
                mock.patch.object(E.subprocess, 'run', return_value=mock.Mock(returncode=0)):
            self.assertEqual(E.check_build(path)[0], original)
            self.assertEqual(C.load_json(path/'manifest.json'), original)
            with mock.patch.object(E, 'sources', return_value=dict(current, **{'model.cuh': 'changed'})):
                with self.assertRaisesRegex(ValueError, 'scientific'):
                    E.check_build(path)
            with mock.patch.object(E.subprocess, 'run', return_value=mock.Mock(returncode=1)):
                with self.assertRaisesRegex(ValueError, 'history'):
                    E.check_build(path)

    def test_exclusive_directories_lock_and_no_overwrite(self):
        one = cli.new_path(self.root, 'attempt')
        E.exclusive_json(one / 'plan.json', {'one': 1})
        two = cli.new_path(self.root, 'attempt')
        self.assertNotEqual(one, two)
        with self.assertRaises(FileExistsError):
            E.exclusive_json(one / 'plan.json', {})
        with cli.workflow_lock(self.root):
            with self.assertRaisesRegex(ValueError, 'active'):
                with cli.workflow_lock(self.root):
                    pass
        with cli.workflow_lock(self.root):
            pass

    def test_plan_bound_automatic_approval_and_provenance(self):
        attempt = self.root / 'attempt'
        E.exclusive_json(attempt / 'plan.json', {'steps': 10000})
        invocation = ['run_e2.py', 'smoke', '--system', self.system['system_id']]
        approval = cli.authorize(attempt, invocation, True, self.journal())
        record = E.approval_record(approval, attempt / 'plan.json', 'e2_smoke')
        self.assertEqual(record['invocation'], invocation)
        self.assertFalse(record['scientific_equilibrium_acceptance'])
        E.check_hashes({record['command_record']: record['command_record_sha256']})
        with self.assertRaises(FileExistsError):
            cli.authorize(attempt, invocation, True, self.root / 'journal')
        (attempt / 'plan.json').write_text('{}')
        with self.assertRaises(ValueError):
            E.approval_record(approval, attempt / 'plan.json', 'e2_smoke')

    def test_discovery_verified_skip_and_tamper_or_physics_mismatch_reject(self):
        path = self.root / 'banks/e2_attempts' / C.e2_bank_id(self.system) / 'old'
        plan, parents = self.plan(path)
        current_sources = dict(plan['source_sha256'], **{'kg_assoc_e2.py': 'new-admin', 'run_e2.py': 'new-cli'})
        with mock.patch.object(cli, 'desired_parents', return_value=parents), \
                mock.patch.object(E, 'verify', return_value=plan) as verify, \
                mock.patch.object(E, 'sources', return_value=current_sources), \
                mock.patch.object(E, 'hash_files', return_value=plan['executable_sha256']):
            self.assertEqual(cli.find_smoke(self.root, self.system), path)
            verify.assert_called_once()
            with mock.patch.object(cli, 'execute_segment') as launch:
                result = cli.smoke_one(self.root, self.system, None, ['smoke'], None)
                self.assertEqual(result['status'], 'skipped_verified')
                launch.assert_not_called()
            with mock.patch.object(E, 'verify', side_effect=ValueError('tampered outputs')):
                self.assertIsNone(cli.find_smoke(self.root, self.system))
            with mock.patch.object(E, 'sources', return_value=dict(current_sources, **{'model.cuh': 'changed'})):
                self.assertIsNone(cli.find_smoke(self.root, self.system))
            changed = copy.deepcopy(plan)
            changed['histories'][0]['physics']['Ee'] += 1
            with mock.patch.object(E, 'verify', return_value=changed):
                self.assertIsNone(cli.find_smoke(self.root, self.system))

    def test_shared_smoke_gate_rejects_binary_or_validation_changes(self):
        base = dict(source_sha256={'validator.py': 'same', 'model.cuh': 'same'},
                    executable_sha256={'exe': 'same'})
        changed = copy.deepcopy(base)
        changed['source_sha256']['validator.py'] = 'changed'
        self.assertFalse(E.smoke_code_compatible(base, changed))
        changed = copy.deepcopy(base)
        changed['executable_sha256']['exe'] = 'changed'
        self.assertFalse(E.smoke_code_compatible(base, changed))

    def test_failure_retains_attempt_logs_and_rerun_gets_new_identity(self):
        journal = self.journal()
        paths = []
        def prepare(root, path, *args):
            paths.append(path)
            E.exclusive_json(path / 'plan.json', {'failed': False})
            (path / 'stderr.log').write_text('GPU failure evidence')
        with mock.patch.object(E, 'prepare', side_effect=prepare), \
                mock.patch.object(E, 'launch', side_effect=RuntimeError('GPU failed')):
            for _ in range(2):
                with self.assertRaisesRegex(RuntimeError, 'GPU failed'):
                    cli.execute_segment(self.root, self.system, 10000, None, ['smoke'], journal, True)
        self.assertNotEqual(*paths)
        self.assertEqual(len(list(journal.glob('failure_*.json'))), 2)
        self.assertTrue(all((p / 'stderr.log').read_text() == 'GPU failure evidence' for p in paths))

    def test_c1_selects_corrected_parents_and_explicit_switch(self):
        system = E.system_by_id(cli.SMOKE_SYSTEMS[-1])
        with mock.patch.object(E, 'corrected_c1', side_effect=lambda root, r, replay: {'replica': r}) as source:
            self.assertEqual(cli.desired_parents(self.root, system), [{'replica': r} for r in (1, 2, 3)])
            self.assertEqual(source.call_count, 3)
        journal = self.journal()
        def prepare(root, path, identifier, steps, evidence, parent, smoke, c1, ea, build):
            self.assertTrue(smoke and c1)
            self.assertEqual((identifier, steps, ea), (system['system_id'], 10000, 8))
            E.exclusive_json(path / 'plan.json', {})
        with mock.patch.object(E, 'prepare', side_effect=prepare), mock.patch.object(E, 'launch'), \
                mock.patch.object(E, 'verify'):
            cli.execute_segment(self.root, system, 10000, None, ['smoke-all'], journal, True)
        entry = dict(parent={'kind': 'e2', 'prefix': 'corrected_C1_8M'}, parent_Ea=4,
                     physics={'Ea': 8}, end_step=8010000, start_step=8000000,
                     chemistry_seed=22001, md_seed=520001, output_prefix='new')
        command = E.command(entry, True)
        self.assertIn('--switch-ea-from', command)
        self.assertEqual(command[command.index('--switch-ea-from')+1], '4')
        self.assertEqual(command[command.index('--Ea')+1], '8')

    def test_authorization_boundaries_and_no_automatic_extension(self):
        for arguments in (['equilibrate', '--system', cli.SMOKE_SYSTEMS[-1], '--steps', '10000'],
                          ['equilibrate', '--system', self.system['system_id'], '--steps', '-1']):
            with self.assertRaises(ValueError), mock.patch.object(cli, 'execute_segment') as launch:
                cli.run(cli.parser().parse_args(arguments), self.root, arguments)
            launch.assert_not_called()
        with self.assertRaises(SystemExit), mock.patch('sys.stderr', new=io.StringIO()):
            cli.parser().parse_args(['equilibrate', '--system', self.system['system_id']])
        arguments = ['equilibrate', '--system', self.system['system_id'], '--steps', '12000']
        with mock.patch.object(cli.subprocess, 'check_output'), mock.patch.object(cli, 'ensure_build'), \
                mock.patch.object(cli, 'completed_segments', return_value=[(Path('prior'), {})]), \
                mock.patch.object(cli, 'execute_segment') as launch:
            with self.assertRaisesRegex(ValueError, '--extend'):
                cli.run(cli.parser().parse_args(arguments), self.root, arguments)
            launch.assert_not_called()

    def test_clean_end_to_end_mock_smoke_all_then_skips_without_gpu(self):
        launches = []
        stored = {}
        def prepare(root, path, identifier, steps, evidence, parent, smoke, c1, ea, build):
            system = E.system_by_id(identifier)
            parents = [dict(kind='e1', sha256={'parent': identifier}, snapshot='input') for _ in range(3)]
            seeds = E.seed_map().get(C.e2_bank_id(system), [22001, 22002, 22003])
            plan = dict(smoke=True, steps=steps, system=system, preparation_Ea=ea,
                        source_sha256={}, executable_sha256={}, histories=[dict(parent=p, chemistry_seed=seed,
                        physics=E.validation.physics(system, ea)) for p, seed in zip(parents, seeds)])
            E.exclusive_json(path / 'plan.json', plan)
            stored[path] = plan
        def launch(root, path, execute, approval, smoke_attempt):
            self.assertTrue(execute)
            E.approval_record(approval, path / 'plan.json', 'e2_smoke')
            self.assertLessEqual(stored[path]['steps'], 10000)
            launches.append(stored[path]['system']['system_id'])
        def find(root, system, parent=None):
            for path, plan in stored.items():
                if plan['system'] == system:
                    E.verify(root, path)
                    return path
        with ExitStack() as stack:
            for target, name, value in ((cli.subprocess, 'check_output', lambda *a, **kw: 'mock GPU'),
                                        (cli, 'ensure_build', lambda root: root/'build'),
                                        (cli, 'find_smoke', find), (E, 'prepare', prepare),
                                        (E, 'launch', launch), (E, 'verify', lambda root, path: stored[path])):
                stack.enter_context(mock.patch.object(target, name, side_effect=value))
            for identifier in cli.SMOKE_SYSTEMS[:2]:
                prepare(self.root, self.root/'banks/e2_attempts'/C.e2_bank_id(E.system_by_id(identifier))/'existing',
                        identifier, 10000, None, None, True, False, 4, None)
            args = cli.parser().parse_args(['smoke-all'])
            self.assertEqual(cli.run(args, self.root, ['run_e2.py', 'smoke-all']), 0)
            self.assertEqual(cli.run(args, self.root, ['run_e2.py', 'smoke-all']), 0)
        self.assertEqual(launches, list(cli.SMOKE_SYSTEMS[2:]))
        self.assertEqual(len(list(self.root.glob('aggregate/e2/workflow/*/report.json'))), 2)

    def test_explicit_equilibration_launches_only_named_steps_and_scope(self):
        arguments = ['equilibrate', '--system', self.system['system_id'], '--steps', '12000']
        with mock.patch.object(cli.subprocess, 'check_output'), mock.patch.object(cli, 'ensure_build'), \
                mock.patch.object(cli, 'completed_segments', return_value=[]), \
                mock.patch.object(cli, 'smoke_one') as smoke, \
                mock.patch.object(cli, 'execute_segment', return_value=self.root/'segment') as launch, \
                mock.patch.object(cli, 'review_segment', return_value=self.root/'report.md') as review:
            self.assertEqual(cli.run(cli.parser().parse_args(arguments), self.root, arguments), 0)
            launch.assert_called_once()
            self.assertEqual(launch.call_args.args[1:3], (self.system, 12000))
            self.assertFalse(launch.call_args.args[6])
            review.assert_called_once_with(self.root, self.root/'segment', 6000)
            smoke.assert_called_once()
            self.assertEqual(smoke.call_args.args[1], self.system)
        attempt = self.root/'explicit'
        E.exclusive_json(attempt/'plan.json', {'steps': 12000})
        approval = cli.authorize(attempt, arguments, False, self.journal())
        self.assertEqual(E.approval_record(approval, attempt/'plan.json', 'e2_segment')['scope'],
                         'requested_system_and_step_count')

    def test_review_automatically_analyzes_without_launching(self):
        arguments = ['review', '--system', self.system['system_id']]
        with mock.patch.object(cli, 'completed_segments', return_value=[(self.root/'segment', {'steps': 12000})]), \
                mock.patch.object(cli, 'review_segment', return_value=self.root/'report.md') as analyze, \
                mock.patch.object(cli, 'execute_segment') as launch:
            self.assertEqual(cli.run(cli.parser().parse_args(arguments), self.root, arguments), 0)
            analyze.assert_called_once()
            self.assertEqual(analyze.call_args.args[-1], 6000)
            launch.assert_not_called()

    def test_wave_a_checkpoint_default_four_windows_and_no_extension(self):
        arguments = ['equilibrate', '--system', self.system['system_id'], '--steps', '2000000']
        with mock.patch.object(cli.subprocess, 'check_output'), mock.patch.object(cli, 'ensure_build'), \
                mock.patch.object(cli, 'completed_segments', return_value=[]), \
                mock.patch.object(cli, 'smoke_one') as smoke, \
                mock.patch.object(cli, 'execute_segment', return_value=self.root/'segment') as launch, \
                mock.patch.object(cli, 'review_segment', return_value=self.root/'report.md') as review:
            self.assertEqual(cli.run(cli.parser().parse_args(arguments), self.root, arguments), 0)
            self.assertEqual(launch.call_args.args[1:3], (self.system, 2000000))
            self.assertIsNone(launch.call_args.args[-1])
            launch.assert_called_once()
            smoke.assert_called_once()
            review.assert_called_once_with(self.root, self.root/'segment', 500000)
        request = C.load_json(next(self.root.glob('aggregate/e2/workflow/*/request.json')))
        self.assertEqual(request['review_window_steps'], 500000)
        self.assertFalse(request['extend'])
        report = C.load_json(next(self.root.glob('aggregate/e2/workflow/*/report.json')))
        self.assertFalse(report['scientific_acceptance'])
        self.assertEqual(report['results'][0]['report'], str(self.root/'report.md'))

    def test_invalid_review_window_fails_before_md_and_analysis_failure_is_retained(self):
        args = cli.parser().parse_args(['equilibrate', '--system', self.system['system_id'],
                                       '--steps', '2000000', '--window-steps', '600000'])
        with mock.patch.object(cli, 'execute_segment') as launch:
            with self.assertRaisesRegex(ValueError, 'partition'):
                cli.run(args, self.root, ['invalid'])
            launch.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'partition'):
            cli.review_window(2000000, 0)
        args.window_steps = 500000
        with mock.patch.object(cli.subprocess, 'check_output'), mock.patch.object(cli, 'ensure_build'), \
                mock.patch.object(cli, 'completed_segments', return_value=[]), \
                mock.patch.object(cli, 'smoke_one'), \
                mock.patch.object(cli, 'execute_segment', return_value=self.root/'segment') as launch, \
                mock.patch.object(cli, 'review_segment', side_effect=ValueError('analysis failed')):
            with self.assertRaisesRegex(ValueError, 'analysis failed'):
                cli.run(args, self.root, ['equilibrate'])
            launch.assert_called_once()
        failure = C.load_json(next(self.root.glob('aggregate/e2/workflow/*/failed.json')))
        self.assertIn('analysis failed', failure['error'])
        self.assertEqual(failure['results'][0]['attempt'], str(self.root/'segment'))
        self.assertEqual(failure['results'][0]['status'], 'numerically_valid_review_pending')
        self.assertFalse(any(self.root.glob('aggregate/e2/workflow/*/report.json')))

    def test_pending_failed_and_running_status(self):
        attempt = self.root/'status'
        self.assertEqual(cli.unfinished_state(attempt), 'pending')
        E.exclusive_json(attempt/'r001/started.json', {})
        self.assertIn('running/unresolved', cli.unfinished_state(attempt))
        E.exclusive_json(attempt/'approval.json', {'host': cli.socket.gethostname(), 'pid': os.getpid()})
        self.assertEqual(cli.unfinished_state(attempt), 'running')
        with mock.patch.object(cli.os, 'kill', side_effect=ProcessLookupError):
            self.assertEqual(cli.unfinished_state(attempt), 'failed/interrupted')
        E.exclusive_json(attempt/'r001/incomplete.json', {'error': 'failure'})
        self.assertEqual(cli.unfinished_state(attempt), 'failed')

    def test_status_and_review_cannot_launch_or_accept_equilibrium(self):
        with mock.patch.object(cli, 'status') as status, mock.patch.object(cli, 'execute_segment') as launch:
            self.assertEqual(cli.run(cli.parser().parse_args(['status']), self.root, ['status']), 0)
            status.assert_called_once_with(self.root)
            launch.assert_not_called()
        with mock.patch.object(cli, 'completed_segments', return_value=[]), \
                mock.patch.object(cli, 'execute_segment') as launch:
            with self.assertRaisesRegex(ValueError, 'no completed'):
                cli.run(cli.parser().parse_args(['review', '--system', self.system['system_id']]),
                        self.root, ['review'])
            launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
