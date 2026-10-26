"""Preparation/authentication tests using temporary synthetic metadata only."""
import copy
import hashlib
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import e1_d16a2_local as local
import e1_d16a2_reference as ref
import e1_d16a2_sampling as sampling


def fixture_directory():
    parent = Path(os.environ.get('TMPDIR', str(local.PROJECT/'build/d16a2-fixtures')))
    parent.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=parent)


class HandoffTests(unittest.TestCase):
    def test_configuration_is_fixed_and_has_no_gpu_authority(self):
        value = local.configuration()
        self.assertFalse(value['GPU_campaign_authorized'])
        self.assertEqual(value['limits'], {'batch_seconds': 30, 'stiffness_seconds': 1200,
                                         'rss_bytes': 1024**3, 'output_bytes': 16*1024**2})
        self.assertEqual(value['maximum_draws_per_kappa'], 65536+8192+524288)
        self.assertEqual(value['M_family_size_across_kappas'], 14)
        self.assertEqual(value['C_family_size_across_kappas'], 36)
        self.assertEqual(value['seed_entropy'], '[721612000,kappa,phase,batch_index]')
        self.assertEqual(value['final_grid'], list(ref.GRID))
        self.assertEqual(value['batch_size'], ref.BATCH)
        self.assertEqual(value['M_alpha']+value['C_alpha'], ref.ALPHA)
        self.assertEqual(value['alpha'], ref.ALPHA)
        self.assertEqual(value['quantile_probabilities'], list(ref.PROBABILITIES))

    def test_preflight_fails_closed_on_headroom(self):
        with patch.object(Path, 'read_text', return_value='MemAvailable: 8388608 kB\n'), \
                patch.object(local.shutil, 'disk_usage') as disk:
            disk.return_value.free = 4*1024**3
            self.assertEqual(local.resource_preflight(Path('/'))['available_host_bytes'], 8*1024**3)
            disk.return_value.free = 512*1024**2
            with self.assertRaises(local.ResourceFailure):
                local.resource_preflight(Path('/'))
        with patch.object(Path, 'read_text', return_value='MemAvailable: 1048576 kB\n'):
            with self.assertRaises(local.ResourceFailure):
                local.resource_preflight(Path('/'))

    def test_parent_death_guard_without_installing_a_real_signal(self):
        with patch.object(sampling.ctypes, 'CDLL') as library, patch.object(sampling.os, 'getppid', return_value=42):
            library.return_value.prctl.return_value = 0
            sampling.parent_guard(42)
            library.return_value.prctl.assert_called_with(1, sampling.signal.SIGKILL, 0, 0, 0)
            with self.assertRaises(ValueError):
                sampling.parent_guard(43)
            library.return_value.prctl.return_value = -1
            with self.assertRaises(ValueError):
                sampling.parent_guard(42)

    def approval_fixture(self, root):
        for name in ('config', 'environment', 'numerical', 'session'):
            local.write(root/(name+'.json'), {'synthetic': name})
        local.write(root/'seed-audit.json', {'status': 'NO_PLANNED_COLLISIONS'})
        local.write(root/'readiness.json', {'status': 'READY_FOR_REVIEW'})
        value = local.approval_template(root)
        local.write(root/'approval-template.json', value)
        return value

    def test_approval_rejects_false_modified_or_wrong_digest(self):
        with fixture_directory() as tmp, patch.object(local, 'checked', return_value=({}, Path(tmp))):
            root = Path(tmp)
            value = self.approval_fixture(root)
            path = root/'reviewed.json'
            local.write(path, value)
            with self.assertRaises(ValueError):
                local.approved(root, path, local.proof(path)['sha256'])
            path.unlink()
            approved = dict(value, execution_authorized=True, review_reference='unit-test synthetic review, not real authorization')
            local.write(path, approved)
            self.assertEqual(local.approved(root, path, local.proof(path)['sha256']), approved)
            with self.assertRaises(ValueError):
                local.approved(root, path, '0'*64)
            path.unlink()
            bad = copy.deepcopy(approved)
            bad['limits']['batch_seconds'] = 31
            local.write(path, bad)
            with self.assertRaises(ValueError):
                local.approved(root, path, local.proof(path)['sha256'])

    def test_nonoverwrite_strict_json_and_symlink_rejection(self):
        with fixture_directory() as tmp:
            root = Path(tmp)
            path = root/'value.json'
            local.write(path, {'status': 'synthetic'})
            with self.assertRaises(FileExistsError):
                local.write(path, {})
            bad = root/'bad.json'
            bad.write_text('{"x":1,"x":2}')
            with self.assertRaises(ValueError):
                local.load(bad)
            (root/'link').symlink_to(path)
            with self.assertRaises(ValueError):
                local.tree_bytes(root)

    def test_return_archive_omits_scalar_arrays_but_authenticates_them(self):
        with fixture_directory() as tmp:
            root = Path(tmp)
            local.write(root/'readiness.json', {'status': 'FAILED', 'errors': ['synthetic failure']})
            scalar = root/'raw.npy'
            scalar.write_bytes(b'synthetic scalar placeholder, not sampled data')
            archive = local.package(root, 'readiness')
            with tarfile.open(archive) as tar:
                names = tar.getnames()
                self.assertNotIn('raw.npy', names)
                self.assertIn('contents.json', names)
                self.assertIn('SUMMARY.md', names)
                checks = tar.extractfile('SHA256SUMS').read().decode().splitlines()
                for line in checks:
                    sha, name = line.split('  ', 1)
                    self.assertEqual(hashlib.sha256(tar.extractfile(name).read()).hexdigest(), sha)
            self.assertTrue(Path(str(archive)+'.sha256').exists())
            local.write(root/'reference-running.json', {'synthetic': True})
            with self.assertRaises(ValueError):
                local.package(root, 'readiness')


class VersionedExecutionTests(unittest.TestCase):
    def test_old_sources_and_contracts_unchanged(self):
        local.verify_preserved(local.PROJECT)
        self.assertEqual(local.configuration()['excluded_seed_namespaces'], [721610000])

    def test_unauthorized_worker_stops_before_sampler_construction(self):
        root = Path('/synthetic/d16a2')
        with patch.object(local, 'checked', return_value=({}, root)), \
                patch.object(local, 'load', return_value={
                    'parent_pid': 42, 'kappa': 0, 'approval_path': '/synthetic/approval',
                    'approval_sha256': 'untrusted'}), \
                patch.object(sampling, 'parent_guard'), \
                patch.object(sampling.os, 'getppid', return_value=42), \
                patch.object(local, 'approved', side_effect=ValueError('not authorized')), \
                patch.object(sampling.Chain, 'homogeneous') as sampler:
            with self.assertRaisesRegex(ValueError, 'not authorized'):
                sampling.run(root, 0)
            sampler.assert_not_called()

    def test_old_approval_schema_is_rejected(self):
        with fixture_directory() as tmp, patch.object(local, 'checked', return_value=({}, Path(tmp))):
            root = Path(tmp)
            fixture = HandoffTests().approval_fixture(root)
            fixture.update(schema='e1-d16a-reference-approval-v1', execution_authorized=True,
                           review_reference='synthetic')
            path = root/'old-approval.json'
            local.write(path, fixture)
            with self.assertRaises(ValueError):
                local.approved(root, path, local.proof(path)['sha256'])

    def supervise_fixture(self, root, kappa, worker_error=None, rss=0):
        local.write(root/'config.json', local.configuration())
        local.write(root/'session.json', {'synthetic': True})
        approval = root/'approval.json'
        local.write(approval, {'synthetic': True})
        real_write = local.write

        def write_with_result(path, value):
            real_write(path, value)
            if path.name == 'launch.json' and worker_error is None:
                real_write(path.parent/'worker-result.json', {
                    'status': local.SUCCESS, 'moments_status': local.SUCCESS,
                    'cdf_status': 'CDF_PRECISION_UNRESOLVED', 'kappa': kappa,
                    'config': local.proof(root/'config.json'), 'peak_host_rss_bytes': 0})

        with patch.object(local, 'write', side_effect=write_with_result), \
                patch.object(local.subprocess, 'Popen') as process, \
                patch.object(local, 'authenticate_case'), \
                patch.object(local, 'verify_environment'), \
                patch.object(local, 'process_rss', return_value=rss):
            process.return_value.poll.return_value = 0
            process.return_value.returncode = 0
            if worker_error:
                process.side_effect = worker_error
            local.supervise(root, root, kappa, approval, local.proof(approval)['sha256'])

    def test_m_success_c_unresolved_completes_without_generic_failure(self):
        with fixture_directory() as tmp:
            root = Path(tmp)
            self.supervise_fixture(root, 0)
            completion = local.load(root/'kappa-0/completion.json')
            self.assertTrue(local.successful(completion['status']))
            self.assertEqual(completion['cdf_status'], 'CDF_PRECISION_UNRESOLVED')
            with self.assertRaises(FileExistsError):
                local.supervise(root, root, 0, root/'approval.json', 'unused')

    def test_worker_launch_failure_is_preserved_and_consumes_case(self):
        with fixture_directory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                self.supervise_fixture(root, 10, OSError('synthetic launch failure'))
            completion = local.load(root/'kappa-10/completion.json')
            self.assertEqual(completion['status'], 'EXECUTION_FAILED')
            self.assertIn('synthetic launch failure', completion['error'])
            self.assertIn('worker.stderr', completion['files'])
            self.assertFalse(local.successful(completion['status']))

    def test_supervisor_rss_limit_failure_is_preserved(self):
        with fixture_directory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                self.supervise_fixture(root, 0, rss=local.LIMITS['rss_bytes']+1)
            completion = local.load(root/'kappa-0/completion.json')
            self.assertEqual(completion['status'], 'RESOURCE_FAILED')
            self.assertIn('RSS', completion['error'])

    def test_resource_failure_is_distinct(self):
        with self.assertRaises(local.ResourceFailure):
            local.resource_require(False, 'synthetic resource cap')
        for status in ('MOMENTS_PRECISION_UNRESOLVED', 'NUMERICAL_CONSISTENCY_FAILED', *local.FAILURES):
            self.assertFalse(local.successful(status))


if __name__ == '__main__':
    unittest.main()
