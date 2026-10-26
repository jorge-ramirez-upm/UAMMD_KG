"""Prepared deterministic fixtures only; no production evidence or GPU activity."""
import copy
from fractions import Fraction
import gzip
import hashlib
import io
import json
import os
import shutil
from pathlib import Path
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d16c_spec as spec
import e1_d16c_json as streaming
import e1_d16c_evidence as evidence
import e1_d16c_audit as science
import e1_d16c_local as local


def fixture():
    parent=spec.durable(os.environ.get('TMPDIR',spec.PROJECT/'build/d16c-fixtures'))
    parent.mkdir(parents=True,exist_ok=True)
    return tempfile.TemporaryDirectory(prefix='constructed-non-scientific-fixture-',dir=parent)


class StreamTests(unittest.TestCase):
    def test_selected_metadata_and_unselected_structures(self):
        text='{"unused":[{"n":1},2,3],"selected":{"label":"a\\\"b","n":1.25},"null":null}'
        result=streaming.extract(io.StringIO(text),{('selected',),('null',)},10000)
        self.assertEqual(result[('selected',)],{'label':'a"b','n':1.25})
        self.assertIsNone(result[('null',)])
        self.assertNotIn(('unused',),result)

    def test_invalid_unselected_members_are_still_rejected(self):
        for text in ('{"skip":{"x":1,"x":2}}','{"skip":1e999}','{"skip":[1,]}','{"skip":1} trailing','{"skip":"unfinished}'):
            with self.assertRaises(ValueError):streaming.extract(io.StringIO(text),set(),10000)
        with self.assertRaises(ValueError):streaming.extract(io.StringIO('[1,2,3]'),set(),3)

    def test_chunk_boundaries_and_full_gzip_integrity(self):
        text=json.dumps({'skip':'x'*70000,'value':123456789,'arrays':[list(range(50))]*2000})
        found=streaming.extract(io.StringIO(text),{('value',)},len(text)+1)
        self.assertEqual(found[('value',)],123456789)
        with fixture() as tmp:
            path=Path(tmp)/'constructed-not-production.gz'
            with gzip.open(path,'wt') as stream:stream.write(text)
            with gzip.open(path,'rt') as stream:
                self.assertEqual(streaming.extract(stream,{('value',)},len(text)+1),found)
            body=path.read_bytes();path.write_bytes(body[:-6])
            with self.assertRaises((EOFError,OSError)):
                with gzip.open(path,'rt') as stream:streaming.extract(stream,set(),len(text)+1)


class EvidenceTests(unittest.TestCase):
    def test_frozen_user_analysis_identity_and_completion(self):
        lock=spec.original()
        self.assertEqual(lock['analysis_identity']['bytes'],28386811)
        self.assertEqual(lock['analysis_identity']['sha256'],'04570c0ccb3b06df0f9be265a2bde602f1c2dcce59c474af963ca8634a17652f')
        self.assertEqual(lock['completion_sha256'],'afde6f5e10d41cc02b6b1ebcc91a8ac03dc806044aa3d60d797831caf4056b68')

    def test_corrupt_missing_and_nonoverwriting(self):
        with fixture() as tmp:
            root=Path(tmp);path=root/'constructed.json';local.write(path,{'schema':'constructed-not-scientific'})
            record=spec.file_record(path);evidence.verify_file(path,record)
            with self.assertRaises(FileExistsError):local.write(path,{})
            path.write_text('{"corrupt":true}')
            with self.assertRaises(ValueError):evidence.verify_file(path,record)
            path.unlink()
            with self.assertRaises((OSError,ValueError)):evidence.verify_file(path,record)

    def test_incomplete_cohort_stops_before_reference_or_payload_use(self):
        import e1_d16b_local as old_control
        import e1_d16b_auth as old_auth
        import e1_d16b_references as old_reference
        with fixture() as tmp:
            root=Path(tmp);session={'commit':'fixture','manifest':{'sha256':'fixture'}}
            with patch.object(evidence,'verify_lock',return_value=({'source_commit':'fixture','completion_sha256':'fixture'},root)), \
                    patch.object(old_control,'checked',return_value=(session,root)), \
                    patch.object(evidence,'load',return_value={'approval_sha256':'fixture'}), \
                    patch.object(old_auth,'authenticate_campaign',return_value=({},[{}]*15)), \
                    patch.object(old_reference,'import_moments') as references:
                with self.assertRaisesRegex(ValueError,'incomplete original cohort'):evidence.authenticate()
                references.assert_not_called()

    def test_oversize_metadata_fails_without_truncating_the_payload(self):
        with fixture() as tmp:
            root=Path(tmp);source=root/'constructed-byte-fixture';source.write_bytes(b'fixture only')
            record=spec.file_record(source);limits=spec.load(spec.CONFIG/'resources.json')
            limits['metadata_max_bytes']=64
            with patch.object(evidence,'load',return_value=limits):
                with self.assertRaisesRegex(ValueError,'metadata cap exceeded'):
                    evidence.return_pair(root/'returns','existing',source,record,{'fixture.json':{'data':'x'*100}})
            self.assertEqual(spec.file_record(root/'returns/d16b-original-analysis.json.gz'),record)
            self.assertFalse((root/'returns/d16c-existing-metadata.tar.gz').exists())

    def test_large_payload_is_exact_and_not_embedded_in_metadata(self):
        with fixture() as tmp:
            root=Path(tmp);source=root/'constructed-not-scientific.byte-fixture'
            with source.open('xb') as stream:
                for _ in range(272):stream.write(b'NON_SCIENTIFIC___'*4096)
            record=spec.file_record(source)
            self.assertGreater(record['bytes'],16*1024**2)
            result=evidence.return_pair(root/'returns','existing',source,record,
                {'fixture.json':{'schema':'constructed-payload-test-not-production'}})
            destination=root/'returns/d16b-original-analysis.json.gz'
            self.assertEqual(spec.file_record(destination),record)
            self.assertEqual(spec.file_record(source),record)
            with tarfile.open(root/'returns/d16c-existing-metadata.tar.gz') as archive:
                self.assertNotIn('d16b-original-analysis.json.gz',archive.getnames())
                self.assertEqual(json.load(archive.extractfile('payload-binding.json'))['scientific_payload']['sha256'],record['sha256'])
                for line in archive.extractfile('SHA256SUMS').read().decode().splitlines():
                    sha,name=line.split('  ',1)
                    self.assertEqual(hashlib.sha256(archive.extractfile(name).read()).hexdigest(),sha)
            manifest=evidence.finalize_return(result,{'status':'exited','exit_code':0}, {'schema':'constructed-test-context'})
            for name,entry in manifest['files'].items():
                self.assertEqual(spec.file_record(root/'returns'/name),entry)
            self.assertTrue((root/'returns/return-manifest.json').is_file())
            with self.assertRaises(FileExistsError):evidence.return_pair(root/'returns','existing',source,record,{})
            with self.assertRaises(ValueError):evidence.copy_payload(source,root/'oversized',record,record['bytes']-1)
            self.assertFalse((root/'oversized').exists())

    def approval_fixture(self,root):
        for name in ('stage-a','tests','stage-a/returns'):(root/name).mkdir(exist_ok=True)
        for name in ('session.json','environment.json','stage-a/readiness-binding.json','stage-a/authentication.json'):
            local.write(root/name,{'schema':'constructed-control-fixture'})
        (root/'stage-a/returns/d16c-existing-metadata.tar.gz').write_bytes(b'constructed-control-fixture')
        local.write(root/'stage-a-complete.json',{'status':'EXISTING_RESULT_RETURN_READY',
            'files':local.tree_records(root/'stage-a'),'tests':{}})
        template=local.approval_template(root);local.write(root/'audit-approval-template.json',template)
        return template

    def test_audit_identity_and_approval_are_separate(self):
        with fixture() as tmp,patch.object(spec,'checked',return_value=({},Path('/synthetic'))):
            root=Path(tmp);template=self.approval_fixture(root);path=root/'reviewed.json'
            local.write(path,template)
            with self.assertRaises(ValueError):local.approved(root,path,spec.digest(path))
            path.unlink();value=dict(template,audit_authorized=True,review_reference='constructed-test-only',
                stage_a_metadata_sha256=spec.digest(root/'stage-a/returns/d16c-existing-metadata.tar.gz'))
            local.write(path,value);self.assertEqual(local.approved(root,path,spec.digest(path)),value)
            wrong=dict(value,schema='e1-d16b-exploratory-approval-v1');path.unlink();local.write(path,wrong)
            with self.assertRaises(ValueError):local.approved(root,path,spec.digest(path))
        with self.assertRaises(ValueError):local.audit(SimpleNamespace(execute_reviewed_audit=False))

    def test_worker_failure_preserved_and_consumes_attempt(self):
        with fixture() as tmp:
            root=Path(tmp);(root/'stage-a').mkdir()
            args=SimpleNamespace(root=root,parent_pid=42,mode='existing')
            with patch.object(spec,'checked'),patch.object(local.os,'getppid',return_value=42), \
                    patch.object(local.ctypes,'CDLL') as library,patch.object(local,'authenticate',side_effect=ValueError('constructed missing evidence')) as auth:
                library.return_value.prctl.return_value=0
                with self.assertRaises(ValueError):local.worker(args)
                self.assertIn('missing evidence',spec.load(root/'stage-a/worker-failure.json')['error'])
                with self.assertRaises(FileExistsError):local.worker(args)
                self.assertEqual(auth.call_count,1)

    def test_resource_limit_failure_and_durable_storage(self):
        with fixture() as tmp:
            root=Path(tmp);(root/'scratch').mkdir();stage=root/'stage-a';stage.mkdir()
            with patch.object(local,'run_process',return_value={'status':'host_memory_limit','exit_code':-15}) as process, \
                    patch.object(shutil,'disk_usage',return_value=SimpleNamespace(free=10*1024**3)):
                with self.assertRaisesRegex(ValueError,'host_memory_limit'):local.run_worker(root,root,stage,'existing')
                limits=process.call_args.args[3]
                self.assertEqual(limits['max_host_rss_bytes'],4*1024**3)
                self.assertLessEqual(limits['per_run_seconds'],1800)
                self.assertEqual(process.call_args.args[2]['CUDA_VISIBLE_DEVICES'],'')
        for path in ('/tmp/retained','/var/tmp/evidence'):
            with self.assertRaises(ValueError):spec.durable(path)


class ScientificFixtureTests(unittest.TestCase):
    def test_whole_replica_uncertainty_and_independent_contrasts(self):
        values=[1.,2.,3.,4.];result=science.uncertainty(values,family_size=6)
        self.assertAlmostEqual(result['standard_error'],np.std(values,ddof=1)/2)
        self.assertEqual(result['replica_contributions_to_mean'],[.25,.5,.75,1.])
        contrast=science.uncertainty([3.,4.,5.,6.],other=values)
        self.assertEqual(contrast['difference'],2.)
        self.assertAlmostEqual(contrast['standard_error'],math.sqrt(2)*result['standard_error'])
        self.assertEqual(contrast['degrees_of_freedom'],6.)
        self.assertGreater(result['intervals']['pointwise_nominal'][0],result['intervals']['six_contrast_nominal_sensitivity'][0])
        with self.assertRaises(ValueError):science.uncertainty(values*10)

    def test_spatial_fluctuation_vs_mean_shift_and_temporal_variance(self):
        reference={'values':{'re2':{'estimate':5.,'numerical_error':1e-12},'rg2':{'estimate':2.}}}
        x=np.linspace(1,9,256);y=x/3+np.sin(x)
        rows=[dict(re2=a,rg2=b,mean_r=1.,mean_r2=1.1) for a,b in zip(x,y)]
        values,_,_=science.spatial_frame(rows,reference)
        shifted=[dict(r,re2=r['re2']+10) for r in rows]
        changed,_,_=science.spatial_frame(shifted,reference)
        self.assertAlmostEqual(values['spatial_var_re2'],changed['spatial_var_re2'])
        self.assertGreater(changed['reference_squared_re2'],values['reference_squared_re2'])
        self.assertAlmostEqual(values['spatial_centering_identity_residual'],0.,places=12)
        self.assertAlmostEqual(changed['spatial_centering_identity_residual'],0.,places=11)
        self.assertNotEqual(np.var([values['re2'],changed['re2']],ddof=1),values['spatial_var_re2'])

    def test_exact_times_and_no_timestep_pairing(self):
        fine={'0':{},'1/10000':{},'1/2000':{},'50':{}}
        coarse={'0':{},'1/4000':{},'1/2000':{},'50':{}}
        self.assertEqual(science.matched_times(fine,coarse),['0','1/2000','50'])
        with self.assertRaises(ValueError):science.matched_times({'0.5':{}},{'1/2':{}})

    def test_connector_weighting_and_unsupported_strata(self):
        value=science.occupancy_weighting([1,2],[1.,18.],[[1,1],[2,2]],[.5,.5])
        self.assertAlmostEqual(value['all_live_spring_mean'],19/3)
        self.assertAlmostEqual(value['equal_occupied_chain_mean'],5.)
        self.assertAlmostEqual(value['fixed_reference_weight_mean'],5.)
        unsupported=science.occupancy_weighting([1,1],[1.,1.],[[1,1],[2,2]],[.5,.5])
        self.assertIsNone(unsupported['fixed_reference_weight_mean'])
        early={'complete_stratum_support':True,'all_spring_mean':19/3,'groups':[{'weight':1/3,'mean':1.},{'weight':2/3,'mean':9.}]}
        late={'complete_stratum_support':True,'all_spring_mean':5.,'groups':[{'weight':.5,'mean':1.},{'weight':.5,'mean':9.}]}
        delta=science.weight_decomposition(early,late)
        self.assertEqual(delta['within'],0.)
        self.assertAlmostEqual(delta['composition'],5-19/3)
        self.assertAlmostEqual(delta['identity_residual'],0.)

    def test_correlated_ACF_support_never_becomes_zero_IAT(self):
        times=[str(Fraction(i,2)) for i in range(201)]
        slow=science.secondary_acf(times,np.arange(201),'.5',100.)
        dispersed=science.secondary_acf(times,[((1103515245*(i+1)+12345)%2147483648)/2147483648 for i in range(201)],'.5',.5)
        self.assertGreater(slow['estimators']['demeaned']['overlap_corrected_acf'][1],dispersed['estimators']['demeaned']['overlap_corrected_acf'][1])
        self.assertTrue(slow['horizon_failure']);self.assertIsNone(slow['tau_int'])
        self.assertEqual(slow['estimators']['demeaned']['origin_counts'][-1],151)
        self.assertEqual(slow['estimators']['demeaned']['lag_times'][-1],25.)
        constant=science.secondary_acf(times,[1.]*201,'.5',1.)
        self.assertIsNone(constant['tau_int'])
        self.assertEqual(constant['estimators']['demeaned']['status'],'UNDEFINED_ZERO_VARIANCE')

    def test_postselection_is_not_familywise_confirmation(self):
        protocol=spec.load(spec.CONFIG/'protocol.json')
        self.assertTrue(protocol['post_selection_exploratory']);self.assertEqual(len(protocol['primary_contrasts']),6)
        self.assertIn('do not establish controlled',science.QUALIFICATION)
        result=science.uncertainty([100.,101.,102.,103.])
        self.assertIsNone(result['scientific_acceptance'])
        self.assertEqual(result['qualification'],science.QUALIFICATION)


if __name__=='__main__':unittest.main()
