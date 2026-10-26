"""Prepared local deterministic fixtures. No production or equilibrium draws.

Fixtures are in-memory or explicitly marked disposable mathematical fixtures
under the permanent checkout / readiness scratch. Never evidence of GPU runs.
"""
import copy
from fractions import Fraction
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d16b_spec as spec
import e1_d16b_analysis as analysis
import e1_d16b_references as refs
import e1_d16b_auth as auth
import e1_d16b_local as local
import e1_d16b_host as host
from e1_observer_check import Rows


def fixture_directory():
    parent=spec.durable(os.environ.get('TMPDIR',spec.PROJECT/'build/d16b-fixtures'))
    parent.mkdir(parents=True,exist_ok=True)
    return tempfile.TemporaryDirectory(prefix='constructed-fixture-not-production-',dir=parent)


class FrozenProtocolTests(unittest.TestCase):
    def test_matrix_and_all_sixteen_seed_identities(self):
        manifest=spec.validate_manifest(spec.CONFIG/'manifest.json',spec.digest(spec.CONFIG/'manifest.json'))
        self.assertFalse(manifest['execution_authorized']);self.assertTrue(manifest['candidate_only'])
        expected=[721530000+100*cell+replica for cell in range(1,5) for replica in range(1,5)]
        self.assertEqual([r['seed'] for r in manifest['runs']],expected)
        self.assertEqual(manifest['runs'],spec.runs())
        self.assertEqual(manifest['common'],{'N':32,'M':256,'Z':2048,'Ne':4,'A2':5,'b0':1,'kb':30,
            'kBT':1,'zeta':1,'nu_hop':100,'end_renewal':True,'stress':'off','precision_bits':64,
            'initialization':'accepted exact E1'})
        old=spec.load(spec.PROJECT/'e1_d15_config/exploratory/manifest.json')
        self.assertFalse(old['execution_supported']);self.assertFalse(old['execution_authorized'])
        self.assertEqual(spec.digest(spec.PROJECT/'e1_d15_config/exploratory/manifest.json'),
                         'c4ffe6758b3c913c7b4ed2a9894d603e3f8f01fc3496448dc83e4ca269bdb0b5')

    def test_schedules_rows_and_audits(self):
        for run in spec.runs():
            s=spec.schedule(run['dt']);dt=Fraction(run['dt'])
            self.assertEqual((len(s['scalar']),len(s['full']),len(s['regular_full']),len(s['union'])),(201,56,51,206))
            self.assertEqual([Fraction(step)*dt for step in s['snapshots']],list(map(Fraction,('0','.01','50','100'))))
            self.assertEqual([Fraction(step)*dt for step in s['extra_early']],
                [dt]+list(map(Fraction,('.0005','.0025','.01','.05'))))
            rows=spec.row_counts(run)
            self.assertEqual(rows['samples.csv'],51456);self.assertEqual(rows['equilibrium_backbone.csv'],1280)
            for name,count in {'tangents':14336,'chains':14336,'sites':473088,'connectors':114688,
                               'events':56,'positions':33792,'attachments':8192}.items():
                self.assertEqual(rows['equilibrium_'+name+'.csv'],count)
            self.assertEqual(rows['initial.csv'],8448);self.assertEqual(rows['initial_bonds.csv'],8192)
            self.assertEqual(rows['slip_springs_final.csv'],2048)
        with self.assertRaises(ValueError):spec.exact_step('.0001','.00025')

    def test_resource_amendment_does_not_enlarge_old_validator(self):
        limits=spec.load(spec.CONFIG/'resources.json')['limits']
        self.assertEqual(spec.validate_limits(limits),limits)
        with self.assertRaises(ValueError):spec.old.validate_limits(limits)
        for key in limits:
            bad=dict(limits);bad[key]+=1
            with self.assertRaises(ValueError):spec.validate_limits(bad)
        envelope=spec.estimates(spec.load(spec.CONFIG/'manifest.json'))
        self.assertEqual(envelope['csv_width_envelope_per_run'],115192412)
        self.assertEqual(envelope['initial_disk_required_bytes'],18*1024**3)
        for path in ('/tmp/persistent','/var/tmp/project','/dev/shm/evidence'):
            with self.assertRaises(ValueError):spec.durable(path)


class MathematicalInferenceTests(unittest.TestCase):
    def test_finite_M_population_exact_small_fixture(self):
        value=analysis.canonical_population(3,2,3)
        expected=[math.comb(3,k)*math.comb(6,3-k)/math.comb(9,3) for k in range(4)]
        np.testing.assert_allclose(value['pmf'],expected,rtol=0,atol=1e-15)
        self.assertAlmostEqual(sum(value['pmf']),1.)
        self.assertAlmostEqual(sum(k*p for k,p in enumerate(value['pmf'])),1.)
        self.assertAlmostEqual(sum((k-1)**2*p for k,p in enumerate(value['pmf'])),value['variance'])
        self.assertAlmostEqual(value['cross_chain_covariance'],-value['variance']/2)
        self.assertGreater(sum(value['pmf'][2:]),0.)
        actual=analysis.canonical_population()
        self.assertEqual(actual['mean'],8.)
        self.assertAlmostEqual(actual['site_probability'],8/33)

    def test_analytical_connector_distribution(self):
        self.assertEqual(analysis.science.chi3_cdf(0),0.)
        for p in analysis.science.PROBABILITIES:
            cut=analysis.science.chi3_quantile(p)
            self.assertAlmostEqual(analysis.science.chi3_cdf(cut),p,places=13)
        # For e_d ~ N(0,5/3), E|e|^4 = 15*(5/3)^2.
        self.assertAlmostEqual(15*(5/3)**2,125/3)
        self.assertAlmostEqual(3*(5/3),5.)

    def test_uncertainty_uses_four_replica_estimators(self):
        values=[1.,2.,3.,4.]
        result=analysis.summary(values)
        self.assertAlmostEqual(result['standard_error'],np.std(values,ddof=1)/2)
        self.assertEqual(result['replica_values'],values)
        contrast=analysis.independent_contrast(values,[2.,3.,4.,5.])
        self.assertAlmostEqual(contrast['standard_error'],math.sqrt(2)*result['standard_error'])
        self.assertEqual(contrast['coarse_minus_fine'],1.)
        self.assertIn('coarse_variance_contribution',contrast)
        bounded=analysis.summary([0.]*4,{'estimate':.1,'interval':[.1,.1],'standard_error':0.},'occupancy[0]')
        self.assertGreater(bounded['trajectory_interval'][1],.1)
        self.assertIn('INSUFFICIENT_INDEPENDENT_REPLICA_PRECISION',bounded['outcomes'])

    def test_reference_intervals_are_propagated_and_unresolved_C_retained(self):
        r={'estimate':2.,'interval':[1.5,2.5],'standard_error':.2,'precision_status':'CDF_PRECISION_UNRESOLVED'}
        a=analysis.summary([1.,2.,3.,4.],r,key='test')
        np.testing.assert_allclose(a['difference_interval'],
            [a['trajectory_interval'][0]-2.5,a['trajectory_interval'][1]-1.5])
        self.assertIn('REFERENCE_CDF_PRECISION_UNRESOLVED',a['outcomes'])
        self.assertAlmostEqual(a['independent_combined_standard_error'],math.hypot(a['standard_error'],.2))

    def test_correlated_and_dispersed_deterministic_series(self):
        times=[str(Fraction(i,2)) for i in range(201)]
        slow=np.arange(201,dtype=float)
        dispersed=np.array([((1103515245*(i+1)+12345) % 2147483648)/2147483648 for i in range(201)])
        a=analysis.acf_diagnostic(times,slow,'.5')
        b=analysis.acf_diagnostic(times,dispersed,'.5')
        self.assertGreater(a['acf'][0],b['acf'][0])
        self.assertIsNone(a['tau_int']);self.assertTrue(a['unresolved_tail'])
        self.assertEqual(a['lag_times'][-1],25.)
        self.assertEqual(a['origin_counts'][-1],151)
        constant=analysis.acf_diagnostic(times,[8.]*201,'.5',8.)
        self.assertIsNone(constant['tau_int']);self.assertNotEqual(constant['tau_int'],0)
        with self.assertRaises(ValueError):analysis.acf_diagnostic(['0','.5','1.1'],[1,2,3],'.5')

    def test_timestep_matching_and_window_membership(self):
        def replica(dt):
            s=spec.schedule(dt)
            return {'series':{analysis.time_key(step,dt):{'diagnostic_only':step==1,'metrics':{'re2':float(step)*float(dt)}}
                              for step in s['union']},
                    'regular_scalar_times':[analysis.time_key(step,dt) for step in s['scalar']],
                    'regular_e1_times':[analysis.time_key(step,dt) for step in s['regular_full']]}
        fine,coarse=replica('.0001'),replica('.00025')
        common=analysis.matched_times(fine,coarse)
        self.assertEqual(len(common),205)
        self.assertNotIn('1/10000',common);self.assertNotIn('1/4000',common)
        self.assertIn('1/2000',common)
        self.assertEqual(len(analysis.window_values(fine,'re2',True)['times']),21)
        self.assertEqual(len(analysis.window_values(fine,'re2',False)['times']),21)
        with self.assertRaises(ValueError):analysis.aggregate([],{'runs':spec.runs()},{})


class AuthenticationAndControlTests(unittest.TestCase):
    def test_reference_file_identity_corruption_rejected(self):
        with fixture_directory() as tmp:
            root=Path(tmp);path=root/'synthetic.json'
            path.write_text('{"schema":"mathematical-fixture-not-production"}\n')
            record=spec.file_record(path);refs.verify_files(root,{'synthetic.json':record})
            path.write_text('{"changed":true}\n')
            with self.assertRaises(ValueError):refs.verify_files(root,{'synthetic.json':record})
            with self.assertRaises(ValueError):refs.verify_files(root,{'../unsafe':record})

    def test_import_preserves_MC_covariance_and_rejects_non_PSD_record(self):
        import e1_d16a2_local as reference_auth
        from e1_d16a_reference import NAMES
        means=dict(zip(refs.MOMENT_NAMES,[10.,2.,4.,1.,.5,104.,5.]))
        numerical={'flexible':means,'flexible_absolute_error_estimates':dict.fromkeys(means,0.),
            'size_means':{'10':{k:means[k] for k in ('mean_X','mean_Y')}},
            'size_mean_absolute_error_estimates':{'10':dict.fromkeys(('mean_X','mean_Y'),0.)},
            'radial_recurrence':{'1':1.,'2':1.1},'radial_absolute_error_estimates':{'1':1e-12,'2':1e-12}}
        inference={'names':list(NAMES),'estimate':list(means.values())+[.5]*18,
            'delta_se':[.01]*25,'interval':[[v-.02,v+.02] for v in list(means.values())+[.5]*18],
            'covariance_of_estimates_delta':np.eye(25).tolist()}
        assessment={'moments_accepted':True,'consistency_status':'CONSISTENT_NOMINAL',
            'moments_status':'MOMENTS_PRECISION_RESOLVED_NOMINAL','cdf_status':'CDF_PRECISION_UNRESOLVED',
            'observables':[{'precision_decision':'PASS'} for _ in range(25)]}
        lock={'schema':'e1-d16b-reviewed-reference-lock-v1','root':'/synthetic/d16b-reference',
              'files':{},'source_commit':'synthetic-fixture'}
        def fake_load(path):
            name=Path(path).name
            return {'reference-lock.json':lock,'numerical.json':numerical,'assessment.json':assessment,
                    'final-inference.json':inference,'quantiles.json':{'cuts':[[1.]*9]*2},'joint-null-law.json':{}}[name]
        with patch.object(refs,'load',side_effect=fake_load),patch.object(refs,'verify_files'), \
                patch.object(refs,'file_record',return_value={'sha256':'fixture','bytes':1}), \
                patch.object(reference_auth,'checked',return_value=({'commit':'synthetic-fixture'},Path('/synthetic'))), \
                patch.object(reference_auth,'authenticate_case',return_value={'status':'MOMENTS_PRECISION_RESOLVED_NOMINAL'}):
            imported=refs.import_moments()
            self.assertEqual(imported['cases']['10']['values']['spatial_var_re2']['source'],'INDEPENDENT_MONTE_CARLO')
            self.assertEqual(imported['cases']['0']['values']['spatial_var_re2']['source'],'ANALYTICAL')
            self.assertEqual(imported['cases']['10']['sampling_inference']['covariance_of_estimates_delta'],np.eye(25).tolist())
            self.assertEqual(imported['cases']['10']['cdf_status'],'CDF_PRECISION_UNRESOLVED')
            inference['covariance_of_estimates_delta'][0][0]=-1.
            with self.assertRaises(ValueError):refs.import_moments()

    def test_approval_and_unauthorized_execution_fail_closed(self):
        with fixture_directory() as tmp:
            root=Path(tmp);(root/'build').mkdir()
            for name in ('session','references','performance'):
                local.write(root/(name+'.json'),{'schema':'constructed-metadata-fixture'})
            local.write(root/'preflight.json',{'environment':{'fixture':True}})
            local.write(root/'build/build.json',{'schema':'constructed-build-fixture'})
            local.write(root/'readiness.json',{'status':'READY_FOR_INDEPENDENT_REVIEW','artifacts':{}})
            template=auth.approval_template(root);local.write(root/'approval-template.json',template)
            with self.assertRaises(ValueError):auth.validate_approval(template,root,spec.identity(template))
            approved=dict(template,execution_authorized=True,independent_readiness_reviewed=True,approval_reference='fixture-only')
            self.assertEqual(auth.validate_approval(approved,root,spec.identity(approved)),template['limits'])
            wrong=dict(approved,schema='e1-d15-approval-v1')
            with self.assertRaises(ValueError):auth.validate_approval(wrong,root,spec.identity(wrong))
            with self.assertRaises(ValueError):auth.validate_approval(approved,root,'0'*64)
            with self.assertRaises(FileExistsError):local.write(root/'approval-template.json',template)
        class Args:execute_reviewed_t100=False
        with self.assertRaises(ValueError):local.run(Args())

    def test_output_authentication_shares_remaining_run_resources(self):
        with fixture_directory() as tmp:
            root=Path(tmp);directory=root/'constructed-run';directory.mkdir()
            (directory/'fixture.txt').write_text('constructed control fixture, no GPU data')
            limits=spec.load(spec.CONFIG/'resources.json')['limits']
            with patch.object(host.shared,'run_process',return_value={'status':'per_run_timeout','exit_code':-15}) as child:
                now=host.time.monotonic()
                with self.assertRaisesRegex(ValueError,'bounded output authentication failed'):
                    host.bounded_output_check(root,directory,{'id':'constructed-check'},limits,now,now,
                                              {'cuda_home':'/usr/local/cuda'})
                restricted=child.call_args.args[3]
                self.assertGreater(restricted['per_run_seconds'],0)
                self.assertLessEqual(restricted['per_run_seconds'],600)
                self.assertLess(restricted['per_run_output_bytes'],limits['per_run_output_bytes'])

    def test_failed_execution_is_preserved_and_cannot_be_reinvoked(self):
        with fixture_directory() as tmp:
            root=Path(tmp);approval=root/'synthetic-approval.json'
            local.write(approval,{'schema':'constructed-control-fixture-not-production'})
            local.write(root/'readiness.json',{'schema':'constructed-readiness-fixture'})
            args=SimpleNamespace(root=root,approval=approval,approval_sha256=spec.digest(approval),execute_reviewed_t100=True)
            with patch.object(local,'checked',return_value=({},root)), \
                    patch.object(auth,'validate_approval',return_value={}), \
                    patch.object(local,'verify_environment'), \
                    patch.object(local,'command',side_effect=RuntimeError('constructed supervisor resource failure')) as command:
                with self.assertRaises(RuntimeError):local.run(args)
                result=local.load(root/'execution-result.json')
                self.assertEqual(result['status'],'INCOMPLETE')
                self.assertIn('resource failure',result['error'])
                self.assertTrue((root/'launch.json').exists())
                self.assertFalse((root/'execution-running.json').exists())
                with self.assertRaises(FileExistsError):local.run(args)
                self.assertEqual(command.call_count,1)

    def test_missing_frames_and_strict_json(self):
        with fixture_directory() as tmp:
            root=Path(tmp);path=root/'constructed-missing-frame.csv'
            path.write_text('step,time,chain\n0,0,0\n')
            reader=Rows(path)
            try:
                with self.assertRaises(ValueError):reader.take(2,0,.0001)
            finally:reader.file.close()
            bad=root/'duplicate.json';bad.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):local.load(bad)

    def test_compact_packet_checksums_and_raw_omission(self):
        with fixture_directory() as tmp:
            root=Path(tmp);local.write(root/'readiness.json',{'status':'FAILED','synthetic':True})
            (root/'constructed.csv').write_text('fixture only; no production values\n')
            archive=local.package(root,'readiness')
            with tarfile.open(archive) as tar:
                self.assertNotIn('constructed.csv',tar.getnames())
                inventory=json.load(tar.extractfile('contents.json'))
                self.assertEqual(inventory['files']['constructed.csv']['sha256'],spec.digest(root/'constructed.csv'))
                for line in tar.extractfile('SHA256SUMS').read().decode().splitlines():
                    sha,name=line.split('  ',1)
                    self.assertEqual(hashlib.sha256(tar.extractfile(name).read()).hexdigest(),sha)
            sidecar=Path(str(archive)+'.sha256')
            self.assertEqual(sidecar.read_text().split()[0],spec.digest(archive))
            local.write(root/'execution-running.json',{'fixture':True})
            with self.assertRaises(ValueError):local.package(root,'results')


if __name__=='__main__':unittest.main()
