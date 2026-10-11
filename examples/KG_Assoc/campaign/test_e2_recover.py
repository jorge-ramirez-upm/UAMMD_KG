"""Recovery regression tests. All GPU processes are replaced by deterministic fixtures."""
from contextlib import ExitStack, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import kg_assoc_e2_recover as recovery
import run_e2 as cli

E = recovery.e2
C = recovery.campaign
SYSTEM = 'F04_N010_RP020_EE08_EA04'


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.system = E.system_by_id(SYSTEM)
        self.attempt = self.root / 'banks/e2_attempts/F04_N010_RP020_EE08/original'
        self.model = self.root / 'physics.cuh'
        self.model.write_text('unchanged science')
        self.binary = self.root / 'binary'
        self.binary.write_text('unchanged executable')
        self.plan = dict(schema_version=1, stage='E2-G1', git_sha='original',
            dataset_root=str(self.root), attempt=str(self.attempt), smoke=False, steps=2000000,
            system=self.system, source_sha256=E.hash_files([self.model]),
            executable_sha256=E.hash_files([self.binary]), histories=[])
        for replica in (1, 2, 3):
            prefix = str(self.attempt / f'r{replica:03d}/state')
            Path(prefix).parent.mkdir(parents=True)
            self.plan['histories'].append(dict(replica=replica, output_prefix=prefix,
                end_step=2000000, start_step=0, chemistry_seed=420000 + replica,
                md_seed=520000 + replica, command=['fake-md', '--output', prefix,
                                                '--seed', str(420000 + replica), '--md-seed', str(520000 + replica)]))
        E.exclusive_json(self.attempt / 'plan.json', self.plan)
        E.exclusive_json(self.attempt / 'approval.json', dict(schema_version=1, approved=True,
            purpose='e2_segment', plan_sha256=C.sha256(self.attempt / 'plan.json'),
            reviewer='original_user', approved_at='then'))
        self.smoke = self.root / 'smoke/plan.json'
        E.exclusive_json(self.smoke, {'smoke': True})
        self.smoke_hashes = E.hash_files([self.smoke])
        self.md_calls = []

    def start(self, entry):
        E.exclusive_json(Path(entry['output_prefix']).parent / 'started.json', dict(
            plan_sha256=C.sha256(self.attempt / 'plan.json'), command=entry['command'],
            approval_sha256=C.sha256(self.attempt / 'approval.json'), smoke_sha256=self.smoke_hashes))

    def outputs(self, entry):
        for suffix in E.validation.OUTPUTS:
            Path(entry['output_prefix'] + suffix).write_text('steps=2000000; authenticated by validator fixture')

    def completed(self, entry):
        self.start(entry)
        self.outputs(entry)
        directory = Path(entry['output_prefix']).parent
        (directory / 'stdout.log').write_text('STAR_ASSOCIATION_SMOKE PASS\n')
        E.exclusive_json(directory / 'complete.json', dict(status='validated',
            end_step=entry['end_step'], plan_sha256=C.sha256(self.attempt / 'plan.json'),
            output_sha256=E.hash_files(directory.iterdir())))

    def interrupted_after_MD(self, entry):
        self.start(entry)
        self.outputs(entry)
        directory = Path(entry['output_prefix']).parent
        (directory / 'stdout.log').write_text('STAR_ASSOCIATION_SMOKE PASS\n')
        E.exclusive_json(directory / 'incomplete.json', {'error': 'prepared code SHA changed'})

    def context(self):
        stack = ExitStack()
        stack.enter_context(patch.object(E, 'check_plan', return_value=self.plan))
        stack.enter_context(patch.object(E, 'clean_tree'))
        stack.enter_context(patch.object(E, 'sources', side_effect=lambda: E.hash_files([self.model])))
        stack.enter_context(patch.object(C, 'git_sha', return_value='recovery'))
        stack.enter_context(patch.object(recovery.subprocess, 'run', return_value=Mock(returncode=0)))
        stack.enter_context(patch.object(E, 'matching_smoke', return_value=self.smoke_hashes))
        stack.enter_context(patch.object(E.validation, 'validate', side_effect=self.validate))
        stack.enter_context(patch.object(E, 'verify', side_effect=self.verify))
        stack.enter_context(patch.object(recovery.subprocess, 'check_output', return_value='fixture GPU (not hardware)'))
        stack.enter_context(patch.object(recovery.subprocess, 'Popen', side_effect=self.popen))
        return stack

    def validate(self, entry, oracle=False):
        for suffix in E.validation.OUTPUTS:
            self.assertIn('steps=2000000', Path(entry['output_prefix'] + suffix).read_text())
        return [], [], dict(numerical_status='valid', scientific_status='review_required')

    def verify(self, root, attempt):
        for entry in self.plan['histories']:
            self.assertEqual(recovery.classify(attempt, entry), 'validate_completed')
            self.validate(entry)
        return self.plan

    def popen(self, command, stdout, stderr):
        entry = next(e for e in self.plan['histories'] if e['command'] == command)
        self.md_calls.append(entry['replica'])
        self.outputs(entry)
        stdout.write('STAR_ASSOCIATION_SMOKE PASS\n')
        stdout.flush()
        return Mock(wait=Mock(return_value=0))

    def run_recovery(self):
        journal = cli.new_path(self.root / 'aggregate/e2/workflow', 'recover')
        E.exclusive_json(journal / 'request.json', dict(invocation=['run_e2.py', 'recover', '--system', SYSTEM]))
        output = cli.new_path(self.root / 'banks/e2_recoveries/F04_N010_RP020_EE08', 'recover')
        return output, recovery.recover(self.root, self.attempt, output, ['recover', '--system', SYSTEM], journal)

    def test_preserved_r001_r002_only_r003_MD_and_repeated_invocation(self):
        self.completed(self.plan['histories'][0])
        self.interrupted_after_MD(self.plan['histories'][1])
        before = E.hash_files([p for p in self.attempt.rglob('*') if p.is_file()])
        with self.context():
            output, (_, receipts) = self.run_recovery()
            self.assertEqual(self.md_calls, [3])
            self.assertEqual([r['operation'] for r in receipts],
                             ['validate_completed', 'validate_preserved', 'run_missing'])
            second, (_, repeated) = self.run_recovery()
            self.assertNotEqual(second, output)
            self.assertEqual(self.md_calls, [3])
            self.assertTrue(all(r['operation'] == 'validate_completed' for r in repeated))
        E.check_hashes(before)
        auth = C.load_json(output / 'authorization.json')
        self.assertEqual(auth['original_git_sha'], 'original')
        self.assertEqual(auth['recovery_git_sha'], 'recovery')
        self.assertFalse(auth['scientific_equilibrium_acceptance'])

    def test_before_MD_interruption_retains_administrative_files(self):
        for entry in self.plan['histories'][:2]:
            self.completed(entry)
        entry = self.plan['histories'][2]
        self.start(entry)
        directory = Path(entry['output_prefix']).parent
        (directory / 'stdout.log').touch()
        (directory / 'stderr.log').touch()
        with self.context():
            self.run_recovery()
        self.assertEqual(self.md_calls, [3])
        self.assertEqual((directory / 'stdout.log').read_text(), '')

    def test_after_recovery_MD_before_validation_repeated_invocation_never_repeats_MD(self):
        for entry in self.plan['histories'][:2]:
            self.completed(entry)
        entry = self.plan['histories'][2]
        self.start(entry)
        directory = Path(entry['output_prefix']).parent
        (directory / 'stdout.log').touch()
        (directory / 'stderr.log').touch()
        failed_once = [False]
        def interrupted(e, oracle=False):
            if e['replica'] == 3 and not failed_once[0]:
                failed_once[0] = True
                raise ValueError('interrupted after MD')
            return self.validate(e)
        with self.context(), patch.object(E.validation, 'validate', side_effect=interrupted):
            with self.assertRaisesRegex(ValueError, 'after MD'):
                self.run_recovery()
            self.run_recovery()
        self.assertEqual(self.md_calls, [3])

    def test_incompatible_science_or_executable_fails_before_MD(self):
        with self.context():
            self.model.write_text('changed physics')
            with self.assertRaisesRegex(ValueError, 'sources changed'):
                self.run_recovery()
            self.model.write_text('unchanged science')
            self.binary.write_text('changed executable')
            with self.assertRaisesRegex(ValueError, 'authenticated file changed'):
                self.run_recovery()
        self.assertEqual(self.md_calls, [])

    def test_admin_changes_allowed_and_new_science_rejected(self):
        current = dict(self.plan['source_sha256'], **{'run_e2.py': 'new', 'catalog.py': 'new',
                                                     'catalog_model.py': 'new', 'test_recover.py': 'new'})
        with self.context(), patch.object(E, 'sources', return_value=current):
            recovery.authenticate(self.root, self.attempt)
            with patch.object(E, 'sources', return_value=dict(current, **{'src/catalog.py': 'new science despite filename'})):
                with self.assertRaisesRegex(ValueError, 'sources changed'):
                    recovery.authenticate(self.root, self.attempt)

    def test_partial_MD_or_changed_outputs_never_relaunched(self):
        self.start(self.plan['histories'][0])
        Path(self.plan['histories'][0]['output_prefix'] + '.events').write_text('partial')
        with self.context(), self.assertRaisesRegex(ValueError, 'partial MD'):
            self.run_recovery()
        self.assertEqual(self.md_calls, [])

    def test_bad_start_approval_parent_and_original_lock_fail_closed(self):
        self.completed(self.plan['histories'][0])
        path = self.attempt / 'r001/started.json'
        original = C.load_json(path)
        changed = dict(original, approval_sha256='changed')
        path.write_text(__import__('json').dumps(changed))
        with self.context(), self.assertRaisesRegex(ValueError, 'start provenance'):
            self.run_recovery()
        path.write_text(__import__('json').dumps(original))
        (self.attempt / '.launch.lock').write_text('held')
        with self.context(), self.assertRaisesRegex(ValueError, 'launch lock'):
            self.run_recovery()
        (self.attempt / '.launch.lock').unlink()
        with self.context(), patch.object(E, 'check_plan', side_effect=ValueError('parent changed')):
            with self.assertRaisesRegex(ValueError, 'parent changed'):
                self.run_recovery()
        self.assertFalse(self.md_calls)

    def test_all_preserved_endpoints_validate_before_missing_MD(self):
        self.completed(self.plan['histories'][0])
        self.interrupted_after_MD(self.plan['histories'][1])
        with self.context(), patch.object(E.validation, 'validate', side_effect=ValueError('wrong final seeds')):
            with self.assertRaisesRegex(ValueError, 'wrong final seeds'):
                self.run_recovery()
        self.assertEqual(self.md_calls, [])

    def test_one_command_mock_workflow_review_500k_no_build_or_smoke_launch(self):
        self.completed(self.plan['histories'][0])
        self.interrupted_after_MD(self.plan['histories'][1])
        args = cli.parser().parse_args(['recover', '--system', SYSTEM])
        with self.context(), patch.object(cli, 'review_segment', return_value=self.root / 'REVIEW.md') as review, \
                patch.object(cli, 'ensure_build', side_effect=AssertionError('must not rebuild')), \
                patch.object(cli, 'smoke_one', side_effect=AssertionError('must not launch smoke')), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(cli.run(args, self.root, ['recover', '--system', SYSTEM]), 0)
        review.assert_called_once_with(self.root, self.attempt, 500000)
        self.assertEqual(self.md_calls, [3])

    def test_ambiguous_attempt_not_selected_by_timestamp(self):
        self.assertEqual(recovery.select_attempt(self.root, self.system), self.attempt)
        other = self.attempt.parent / 'other'
        E.exclusive_json(other / 'plan.json', self.plan)
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            recovery.select_attempt(self.root, self.system)


    def test_documentation_commit_during_recovery_keeps_scientific_gate(self):
        for entry in self.plan['histories']:
            self.completed(entry)
        with self.context():
            output, _ = self.run_recovery()
            with patch.object(C, 'git_sha', return_value='later-documentation'):
                recovery.authenticate(self.root, self.attempt)
                recovery.verify_authorization(output, self.attempt)
        self.assertFalse(self.md_calls)

    def test_review_reuse_is_hash_bound_and_never_accepts_equilibrium(self):
        output = self.root / 'aggregate/e2/review_existing'
        for name in ('SCIENTIFIC_REVIEW.md', 'summary.json', 'replica_comparisons.csv'):
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('immutable review fixture')
        for entry in self.plan['histories']:
            self.completed(entry)
        config = dict(attempt=str(self.attempt), window_steps=500000,
                      plan_sha256=C.sha256(self.attempt / 'plan.json'),
                      source_sha256=E.hash_files([self.attempt / f'r{r:03d}/complete.json' for r in (1, 2, 3)]))
        E.exclusive_json(output / 'analysis_config.json', config)
        E.exclusive_json(output / 'review_complete.json', dict(
            plan_sha256=C.sha256(self.attempt / 'plan.json'), scientific_status='review_required',
            automatic_acceptance=False, report_sha256=E.hash_files(output.iterdir())))
        with patch.object(cli, 'review_segment', side_effect=AssertionError('no repeated analysis')):
            self.assertEqual(cli.recovered_review(self.root, self.attempt, 500000), output / 'SCIENTIFIC_REVIEW.md')
            (output / 'summary.json').write_text('changed evidence')
            with self.assertRaisesRegex(ValueError, 'authenticated file changed'):
                cli.recovered_review(self.root, self.attempt, 500000)


    def test_interrupted_endpoint_hashing_uses_authenticated_recovery_start(self):
        for entry in self.plan['histories'][:2]:
            self.completed(entry)
        entry = self.plan['histories'][2]
        self.start(entry)
        directory = Path(entry['output_prefix']).parent
        (directory / 'stdout.log').touch()
        (directory / 'stderr.log').touch()
        exclusive = E.exclusive_json
        def interrupt(path, value):
            if Path(path).name == 'md_complete.json':
                raise KeyboardInterrupt('interrupted during endpoint receipt')
            return exclusive(path, value)
        with self.context(), patch.object(E, 'exclusive_json', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_recovery()
        with self.context():
            self.run_recovery()
        self.assertEqual(self.md_calls, [3])


    def test_completed_output_tampering_fails_before_missing_MD(self):
        self.completed(self.plan['histories'][0])
        Path(self.plan['histories'][0]['output_prefix'] + '.events').write_text('changed output')
        with self.context(), self.assertRaisesRegex(ValueError, 'authenticated file changed'):
            self.run_recovery()
        self.assertFalse(self.md_calls)

    def test_nonancestor_checkout_and_redirected_replica_fail_closed(self):
        with self.context(), patch.object(recovery.subprocess, 'run', return_value=Mock(returncode=1)):
            with self.assertRaisesRegex(ValueError, 'ancestor'):
                self.run_recovery()
        self.completed(self.plan['histories'][0])
        directory = self.attempt / 'r003'
        directory.rmdir()
        outside = self.root / 'redirected'
        outside.mkdir()
        directory.symlink_to(outside, target_is_directory=True)
        with self.context(), self.assertRaisesRegex(ValueError, 'redirects'):
            self.run_recovery()
        self.assertFalse(self.md_calls)


if __name__ == '__main__':
    unittest.main()
