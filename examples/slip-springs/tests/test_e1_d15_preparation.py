"""LOCAL ONLY: offline D1.5 checks. Not executed during preparation in Codex."""
import argparse
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d15_prepare as spec
import e1_d15_auth as auth
import e1_d15_host as host

class Preparation(unittest.TestCase):
    def test_exact_matrix_clocks_counts_and_seeds(self):
        all_seeds=[]
        for kind in spec.KINDS:
            value=spec.proposed_manifest(kind)
            self.assertFalse(value['execution_authorized'])
            self.assertTrue(all(v is None for v in value['approved_limits'].values()))
            self.assertEqual(len(value['runs']),16 if kind=='exploratory' else 4)
            for run in value['runs']:
                self.assertEqual((run['M'],run['Z'],run['N']),(256,2048,32))
                all_seeds.append(run['seed'])
                schedule=spec.schedule(run['T'],run['dt'])
                self.assertEqual(len(schedule['snapshot_steps']),4)
                self.assertEqual(schedule['full_steps'][-1],run['steps'])
                if kind=='exploratory':
                    self.assertEqual([len(schedule[k]) for k in ('scalar_steps','full_steps','snapshot_steps')],[201,56,4])
                    counts=spec.row_counts(run)
                    self.assertEqual(counts['samples.csv'],256*201)
                    self.assertEqual(counts['equilibrium_backbone.csv'],256*5)
                    self.assertEqual(counts['equilibrium_sites.csv'],8448*56)
        self.assertEqual(len(all_seeds),len(set(all_seeds)))

    def test_freeze_nonoverwrite_and_tampering(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)/'config';proof=spec.freeze(root,'benchmark')
            value=spec.validate_manifest(root/'manifest.json',proof['manifest_sha256'])
            self.assertEqual(value['kind'],'benchmark')
            template=spec.load(root/'approval.template.json')
            self.assertIsNone(template['readiness_review']);self.assertIsNone(template['benchmark_review'])
            with self.assertRaises(FileExistsError):spec.freeze(root,'benchmark')
            path=root/'dt0.0001.full.steps';path.write_text(path.read_text()+'1\n')
            with self.assertRaises(ValueError):spec.validate_manifest(root/'manifest.json',proof['manifest_sha256'])

    def test_long_design_and_missing_approval_cannot_execute(self):
        with self.assertRaises(ValueError):host.require_bounded(spec.proposed_manifest('exploratory'))
        value=spec.proposed_manifest('benchmark')
        args=argparse.Namespace(authorize_d15_local_execution=True)
        with patch.object(host.accepted,'execute',side_effect=AssertionError('must not delegate')):
            with self.assertRaises(ValueError):host.execute(args,{'blockers':['unapproved']},value,None,None,None)
            args.authorize_d15_local_execution=False
            with self.assertRaises(ValueError):host.execute(args,{'blockers':[]},value,None,{},None)
        with self.assertRaises(ValueError):auth.reviewed_record(None,'e1-d15-readiness-review-v1')

    def test_projection_is_not_a_runtime_measurement(self):
        for chains in (256,512,1024,2048):
            run=spec.runs('exploratory',chains)[0]
            estimate=spec.storage(run)
            self.assertGreater(estimate['wide_csv_bytes'],estimate['empirical_csv_bytes'])
            self.assertGreater(spec.state_estimate(run)['device_array_bytes'],0)
            self.assertEqual(run['Z'],8*chains)
            self.assertLess(run['Z']*100*.00025,10000)
        self.assertIsNone(spec.estimates(spec.proposed_manifest('benchmark'))['runtime_seconds'])

    def test_review_corruption_and_provenance_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'review.json'
            path.write_bytes(spec.encoded({'schema':'expected','review_reference':'independent-review'}))
            pointer={'path':str(path),'sha256':spec.digest(path)}
            self.assertEqual(auth.reviewed_record(pointer,'expected')['review_reference'],'independent-review')
            path.write_text('{}\n')
            with self.assertRaises(ValueError):auth.reviewed_record(pointer,'expected')
        bad={k:None for k in auth.BASE_APPROVAL_FIELDS|auth.REVIEW_FIELDS}
        with self.assertRaises(ValueError):auth.approval_reviews(bad,spec.proposed_manifest('pilot'))

if __name__=='__main__':unittest.main()
