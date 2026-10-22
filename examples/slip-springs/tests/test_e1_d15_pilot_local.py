"""USER-run offline pilot handoff checks. No CUDA, child processes or scientific data."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import e1_d15_local as local


class PilotHandoffTests(unittest.TestCase):
    def test_manifest_selection_preserves_benchmark_default(self):
        project = Path('/unused/project')
        self.assertEqual(local.manifest_args(project)[-1], local.MANIFEST_SHA)
        self.assertEqual(local.manifest_args(project, 'pilot')[-1], local.PILOT_SHA)
        self.assertIn('/pilot/', local.manifest_args(project, 'pilot')[1])
        self.assertEqual(set(local.MANIFESTS), {'benchmark', 'pilot'})

    def test_explicit_pilot_gate_and_copied_benchmark_approval_refused(self):
        with patch.object(local, 'command') as delegate:
            with self.assertRaises(ValueError):
                local.pilot(argparse.Namespace(execute_reviewed_pilot=False))
            delegate.assert_not_called()
        args = argparse.Namespace(execute_reviewed_pilot=True, root=Path('/unused/pilot'),
                                  approval=Path('/unused/approval.json'), approval_sha256='a' * 64)
        copied = {'execution_authorized': True, 'manifest_sha256': local.MANIFEST_SHA}
        with patch.object(local, 'ready', return_value=({'kind': 'pilot'}, Path('/unused/project'))), \
             patch.object(local, 'proof', return_value={'sha256': 'a' * 64}), \
             patch.object(local, 'load', return_value=copied), patch.object(local, 'command') as delegate:
            with self.assertRaises(ValueError):
                local.pilot(args)
            delegate.assert_not_called()

    def test_user_ceilings_cannot_be_expanded_or_headroom_reduced(self):
        local.pilot_limits(dict(local.PILOT_LIMITS))
        for key in local.PILOT_LIMITS:
            changed = dict(local.PILOT_LIMITS)
            changed[key] += -1 if key.startswith('min_') else 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                local.pilot_limits(changed)
        changed = dict(local.PILOT_LIMITS, per_run_seconds=True)
        with self.assertRaises(ValueError):
            local.pilot_limits(changed)

    def test_reviewed_archive_pins_completion_and_local_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = {'session.json': {'root': str(root)}, 'readiness.json': {'status': 'synthetic'},
                      'benchmark-launch.json': {'approval_sha256': 'a' * 64},
                      'benchmark-result.json': {'status': 'completed', 'root': str(root / 'benchmark-campaign'),
                                                'completion_sha256': 'b' * 64},
                      'benchmark-summary-test.json': {'kind': 'benchmark', 'runs': [{}] * 4}}
            for name, value in values.items():
                local.write(root / name, value)
            values['benchmark-summary-test.receipt.json'] = {
                'report': str(root / 'benchmark-summary-test.json'),
                'file': local.proof(root / 'benchmark-summary-test.json'),
                'launch': local.proof(root / 'benchmark-launch.json'),
                'result': local.proof(root / 'benchmark-result.json')}
            values['contents.json'] = {'kind': 'benchmark', 'evidence_root': str(root)}
            payload = {name: local.encoded(value) for name, value in values.items()}
            payload['SHA256SUMS'] = ''.join(hashlib.sha256(body).hexdigest() + '  ' + name + '\n'
                                          for name, body in sorted(payload.items())).encode()
            archive = root / 'reviewed.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                for name, body in payload.items():
                    info = tarfile.TarInfo(name)
                    info.size = len(body)
                    tar.addfile(info, io.BytesIO(body))
            digest = local.proof(archive)['sha256']
            prior, launch, result = local.reviewed_benchmark(archive, digest)
            self.assertEqual(prior, root)
            self.assertEqual(result['completion_sha256'], 'b' * 64)
            with self.assertRaises(ValueError):
                local.reviewed_benchmark(archive, '0' * 64)
            (root / 'benchmark-result.json').write_text('{}')
            with self.assertRaises(ValueError):
                local.reviewed_benchmark(archive, digest)

    def test_failed_prior_authentication_never_writes_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = argparse.Namespace(benchmark_review_reference='synthetic review',
                                      benchmark_return=root / 'unused.tar.gz', benchmark_return_sha256='a' * 64)
            with patch.object(local, 'reviewed_benchmark', return_value=(root, {'approval_sha256': 'a' * 64},
                               {'completion_sha256': 'b' * 64})), \
                 patch.object(local, 'ready', return_value=({'kind': 'benchmark'}, root)), \
                 patch.object(local, 'command', side_effect=ValueError('synthetic authentication failure')):
                with self.assertRaises(ValueError):
                    local.pilot_prior_review(args, root, root, {})
            self.assertFalse((root / 'benchmark-review.json').exists())

    def test_pilot_failure_packet_preserves_kind_and_excludes_raw_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            local.write(root / 'session.json', {'kind': 'pilot'})
            local.write(root / 'readiness.json', {'status': 'failed', 'error': 'synthetic pilot failure'})
            (root / 'raw.csv').write_text('not bundled')
            with patch('sys.stdout', new_callable=io.StringIO):
                archive = local.package(root, 'pilot-readiness')
            self.assertTrue(archive.name.startswith('pilot-readiness-return-'))
            with tarfile.open(archive) as tar:
                self.assertNotIn('raw.csv', tar.getnames())
                self.assertEqual(json.load(tar.extractfile('contents.json'))['kind'], 'pilot-readiness')
            with self.assertRaises(ValueError):
                local.package(root, 'benchmark')


if __name__ == '__main__':
    unittest.main()
