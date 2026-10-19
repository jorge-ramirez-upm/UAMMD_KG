"""CPU-only reproduction of missing extension readback; no native MD is invoked."""
from pathlib import Path
import sys
import unittest
from unittest import mock

import kg_assoc_e2 as e2
import kg_assoc_e2_extension as extension
import kg_assoc_e2_readback as readback
import run_ea_extensions as runner
import test_e2_extensions as fixtures
import test_e2_readback as readback_fixtures


BROKEN_NATIVE = '07b6eb5f725f46c1f5b04ef45123fd8915a562c62cee916e2eb0b18eda581ae7'
BROKEN_BUILD = dict(source_sha256={'kg_assoc_stars.cu': BROKEN_NATIVE})


class ExtensionReadbackHoldTests(unittest.TestCase):
    setUp = fixtures.LifecycleTests.setUp
    started = fixtures.LifecycleTests.started

    def snapshot(self):
        return {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_exact_native_PASS_missing_readback_exception_preserves_attempt(self):
        self.started()
        (self.directory/'stdout.log').write_text('STAR_ASSOCIATION_SMOKE PASS\n')
        missing = str(self.directory/'state.initial_device_validation.tsv')
        self.job.update(status='failed', error=f"[Errno 2] No such file or directory: '{missing}'")
        e2.exclusive_json(self.directory/'incomplete.json', dict(error=self.job['error']))
        before = self.snapshot()
        with mock.patch.object(e2, 'launch') as launch, self.assertRaisesRegex(
                ValueError, 'failed trajectory preserved; no automatic retry'):
            runner.classify(self.job, recover=True)
        launch.assert_not_called()
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.directory/'complete.json').exists())
        self.assertEqual(self.job['status'], 'failed')

    def test_missing_original_evidence_rejects_recovery_without_incomplete_receipt(self):
        self.started()
        (self.directory/'stdout.log').write_text('STAR_ASSOCIATION_SMOKE PASS\n')
        missing = self.directory/'state.initial_device_validation.tsv'
        before = self.snapshot()
        with mock.patch.object(e2.validation, 'validate', side_effect=FileNotFoundError(
                2, 'No such file or directory', str(missing))), mock.patch.object(e2, 'launch') as launch:
            with self.assertRaises(FileNotFoundError):
                runner.classify(self.job, recover=True)
        launch.assert_not_called()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(missing.exists())

    def test_strict_readback_checker_rejects_absence(self):
        with self.assertRaises(FileNotFoundError):
            readback.check(self.directory/'state.initial_device_validation.tsv', {}, {}, [])
        self.assertEqual(self.snapshot(), {})

    def test_finished_recovery_still_requires_authenticated_original_evidence(self):
        # Synthetic CPU fixture only. No real campaign output is created or changed.
        fixture = readback_fixtures.ReadbackTests('test_valid_and_exact_periodic_image')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.started()
        (self.directory/'stdout.log').write_text('STAR_ASSOCIATION_SMOKE PASS\n')
        before = self.snapshot()
        evidence_before = fixture.path.read_bytes()

        def validate(entry, oracle):
            self.assertIs(entry, self.entry)
            self.assertTrue(oracle)
            result = fixture.check()
            return [], [], dict(initial_device_readback=result)

        with mock.patch.object(e2.validation, 'validate', side_effect=validate), mock.patch.object(e2, 'launch') as launch:
            self.assertEqual(runner.classify(self.job, recover=True), 'complete')
        launch.assert_not_called()
        self.assertEqual(fixture.path.read_bytes(), evidence_before)
        for name, data in before.items():
            self.assertEqual(Path(name).read_bytes(), data)
        complete = e2.campaign.load_json(self.directory/'complete.json')
        self.assertTrue(complete['receipt_recovered_without_MD'])
        self.assertEqual(complete['validation']['initial_device_readback']['status'], 'valid')

    def test_check_prepare_execute_block_before_mutation_or_GPU(self):
        before = self.snapshot()
        with mock.patch.object(runner.run_e2, 'discover', return_value=self.root), \
                mock.patch.object(e2.campaign, 'load_json', return_value=BROKEN_BUILD), \
                mock.patch.object(runner, 'execute') as execute, \
                mock.patch.object(runner, 'prepare_state') as prepare, \
                mock.patch.object(e2, 'launch') as launch:
            for option in ('--check', '--prepare', '--execute'):
                with self.subTest(option=option), mock.patch.object(
                        sys, 'argv', ['run_ea_extensions.py', option]), self.assertRaisesRegex(
                        ValueError, 'not authenticated'):
                    runner.main()
            execute.assert_not_called()
            prepare.assert_not_called()
            launch.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_missing_native_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'not authenticated'):
            e2.require_extension_readback_build({})

    def test_direct_launcher_cannot_start_affected_extension(self):
        (self.directory/'preserved').write_text('original bytes')
        before = self.snapshot()
        plan = dict(lineage_mode=extension.MODE, build=BROKEN_BUILD)
        with mock.patch.object(e2, 'check_plan', return_value=plan), \
                mock.patch.object(e2, 'launch_scope', return_value=[]), \
                mock.patch.object(e2.subprocess, 'Popen') as popen, self.assertRaisesRegex(
                ValueError, 'not authenticated'):
            e2.launch(self.root, self.root, execute=True, replicas=[1])
        popen.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_all_six_actual_plans_share_the_rejected_build(self):
        state = e2.campaign.load_json(e2.HERE.parent/
            'kg_assoc_100m/aggregate/e2/manual_ea_extensions_v1/state.json')
        for job in state['jobs']:
            plan = e2.campaign.load_json(Path(job['attempt'])/'plan.json')
            with self.subTest(system=job['system'], replica=job['replica']), \
                    self.assertRaisesRegex(ValueError, 'not authenticated'):
                e2.require_extension_readback_build(plan['build'])
        self.assertEqual(len(state['jobs']), 6)


if __name__ == '__main__':
    unittest.main()
