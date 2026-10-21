"""Operator-handoff tests, provided for the user to run; no GPU or campaign execution."""
import argparse
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import e1_d14_phase_b_host as host


class HostHandoffTests(unittest.TestCase):
    def test_exact_limits_and_phase_b_only_command(self):
        self.assertEqual(host.LIMITS, dict(per_run_seconds=120, aggregate_seconds=3600,
            per_run_output_bytes=134217728, aggregate_output_bytes=1073741824,
            max_host_rss_bytes=2147483648, min_available_host_bytes=8589934592,
            min_free_gpu_bytes=4294967296, min_free_disk_bytes=10737418240))
        command = host.command(Path('/tmp/example'), dict(build_receipt='/tmp/build.json',
            build_sha256='b'*64, approval_sha256='a'*64))
        self.assertIn('--authorize-phase-b-execution', command)
        self.assertNotIn('--authorize-phase-a-execution', command)
        self.assertIn(host.MANIFEST, command)

    def test_refuse_without_explicit_flags_before_any_probe(self):
        with patch.object(host.runner, 'preflight', side_effect=AssertionError('must not probe')):
            with self.assertRaises(ValueError):
                host.prepare(argparse.Namespace(write_approved_record=False))
            with self.assertRaises(ValueError):
                host.execute(argparse.Namespace(authorize_phase_b_execution=False))

    def test_completion_requires_both_success_records(self):
        first = dict(mode='read-only preflight', blockers=[])
        last = dict(status='completed', root='/tmp/example/campaign', completion_sha256='c'*64)
        text = json.dumps(first)+'\n'+json.dumps(last)+'\n'
        self.assertEqual(host.returned_completion(text), last)
        for text in (json.dumps(first), json.dumps(last), json.dumps(dict(first, blockers=['failure']))+'\n'+json.dumps(last)):
            with self.assertRaises(ValueError): host.returned_completion(text)

    def test_summary_retains_individual_replica_values_without_verdict(self):
        metrics = {key:dict(reference=5., replica_values=[4.,6.]) for key in
                   ('re2','rg2','mean_r','mean_r2','connector_e2','A_joint','B_joint')}
        windows = {key:dict(paired_late_minus_early=dict(replica_values=[-.1,.2])) for key in metrics}
        result = dict(cells={'1':dict(time_resolved={'0':dict(metrics=metrics),'10':dict(metrics=metrics)},
                                    early_versus_late=windows)})
        text = host.summary(result)
        self.assertIn('4, 6', text)
        self.assertIn('-0.1, 0.2', text)
        self.assertIn('No scientific acceptance verdict', text)


if __name__ == '__main__': unittest.main()
