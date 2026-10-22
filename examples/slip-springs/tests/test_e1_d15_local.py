"""Offline wrapper checks for USER execution; no CUDA, subprocess or scientific data."""
import argparse
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import e1_d15_local as local


class LocalHandoffTests(unittest.TestCase):
    def test_json_stream_and_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stream.json'
            path.write_text('{"blockers": []}\n{"status": "completed"}\n')
            self.assertEqual(len(local.documents(path)), 2)
            with self.assertRaises(ValueError):
                local.load(path)
            path.write_text('{"a": 1, "a": 2}')
            with self.assertRaises(ValueError):
                local.load(path)

    def test_benchmark_requires_both_gate_and_true_external_approval(self):
        args = argparse.Namespace(execute_reviewed_benchmark=False)
        with patch.object(local, 'command') as delegate:
            with self.assertRaises(ValueError):
                local.benchmark(args)
            delegate.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            approval = root / 'approval.json'
            local.write(approval, {'execution_authorized': False})
            args = argparse.Namespace(execute_reviewed_benchmark=True, root=root,
                                      approval=approval, approval_sha256=local.proof(approval)['sha256'])
            with patch.object(local, 'ready', return_value=({}, root)), patch.object(local, 'command') as delegate:
                with self.assertRaises(ValueError):
                    local.benchmark(args)
                delegate.assert_not_called()
            self.assertFalse((root / 'benchmark-launch.json').exists())

    def test_packet_is_small_allowlisted_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'logs').mkdir()
            (root / 'build/bin').mkdir(parents=True)
            (root / 'build/bin/semiflexible').write_bytes(b'NOT AN EXECUTABLE')
            (root / 'raw.csv').write_text('large raw history must not be bundled\n')
            log = root / 'logs/example.stderr'
            log.write_bytes(b'x' * 100000)
            original = local.proof(log)
            local.write(root / 'readiness.json', {'status': 'failed', 'error': 'synthetic test failure'})
            with patch('sys.stdout', new_callable=io.StringIO):
                first = local.package(root, 'readiness')
                second = local.package(root, 'readiness')
            self.assertNotEqual(first, second)
            self.assertEqual(local.proof(log), original)
            with tarfile.open(first) as archive:
                names = archive.getnames()
                self.assertNotIn('build/bin/semiflexible', names)
                self.assertNotIn('raw.csv', names)
                self.assertIn('SHA256SUMS', names)
                self.assertIn('contents.json', names)
                self.assertIn(b'TRUNCATED', archive.extractfile('logs/example.stderr').read())
                self.assertIn(b'synthetic test failure', archive.extractfile('SUMMARY.txt').read())
                for line in archive.extractfile('SHA256SUMS').read().decode().splitlines():
                    digest, name = line.split('  ', 1)
                    self.assertEqual(hashlib.sha256(archive.extractfile(name).read()).hexdigest(), digest)
            self.assertIn(local.proof(first)['sha256'], first.with_name(first.name + '.sha256').read_text())


if __name__ == '__main__':
    unittest.main()
