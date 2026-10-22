"""Preparation/authentication tests using temporary synthetic metadata only."""
import copy
import hashlib
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import e1_d16a_local as local
import e1_d16a_reference as ref
import e1_d16a_sampling as sampling


class HandoffTests(unittest.TestCase):
    def test_configuration_is_fixed_and_has_no_gpu_authority(self):
        value = local.configuration()
        self.assertFalse(value['GPU_campaign_authorized'])
        self.assertEqual(value['limits'], {'batch_seconds': 30, 'stiffness_seconds': 1200,
                                         'rss_bytes': 1024**3, 'output_bytes': 16*1024**2})
        self.assertEqual(value['maximum_draws_per_kappa'], 65536+8192+524288)
        self.assertEqual(value['reference_family_size'], 50)
        self.assertEqual(value['seed_entropy'], '[721610000,kappa,phase,batch_index]')
        self.assertEqual(value['final_grid'], list(ref.GRID))
        self.assertEqual(value['batch_size'], ref.BATCH)
        self.assertEqual(value['reference_family_size'], ref.FAMILY)
        self.assertEqual(value['alpha'], ref.ALPHA)
        self.assertEqual(value['quantile_probabilities'], list(ref.PROBABILITIES))

    def test_preflight_fails_closed_on_headroom(self):
        with patch.object(Path, 'read_text', return_value='MemAvailable: 8388608 kB\n'), \
                patch.object(local.shutil, 'disk_usage') as disk:
            disk.return_value.free = 4*1024**3
            self.assertEqual(local.resource_preflight(Path('/'))['available_host_bytes'], 8*1024**3)
            disk.return_value.free = 512*1024**2
            with self.assertRaises(ValueError):
                local.resource_preflight(Path('/'))
        with patch.object(Path, 'read_text', return_value='MemAvailable: 1048576 kB\n'):
            with self.assertRaises(ValueError):
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
        local.write(root/'readiness.json', {'status': 'READY_FOR_REVIEW'})
        value = local.approval_template(root)
        local.write(root/'approval-template.json', value)
        return value

    def test_approval_rejects_false_modified_or_wrong_digest(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(local, 'checked', return_value=({}, Path(tmp))):
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
        with tempfile.TemporaryDirectory() as tmp:
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
        with tempfile.TemporaryDirectory() as tmp:
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


if __name__ == '__main__':
    unittest.main()
