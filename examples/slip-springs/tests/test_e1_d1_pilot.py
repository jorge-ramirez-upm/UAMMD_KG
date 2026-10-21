"""Bounded synthetic/unit checks only. Never sets the pilot execution flag."""
import argparse
import copy
from fractions import Fraction
import itertools
import json
import math
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np
from numpy.polynomial.legendre import leggauss
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d1_pilot as spec
import e1_d1_pilot_auth as auth
import e1_d1_pilot_runner as runner
import e1_d1_pilot_analysis as science


class SpecificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='d11-unit-');self.root=Path(self.tmp.name)
        self.config=self.root/'config';self.sha=spec.freeze(self.config)
        self.manifest=spec.validate_manifest(self.config/'manifest.json',self.sha)
    def tearDown(self):self.tmp.cleanup()

    def test_exact_matrix_seeds_and_rounding(self):
        runs=self.manifest['runs'];self.assertEqual(len(runs),32)
        self.assertEqual(len({r['seed'] for r in runs}),32)
        self.assertEqual({(r['N'],r['kappa'],r['Ne'],r['nu_hop']) for r in runs},set(spec.BASE_CASES))
        for cell in range(1,9):self.assertEqual([r['replica'] for r in runs if r['cell']==cell],[1,2,3,4])
        self.assertEqual({(r['N'],r['Ne'],r['Z']) for r in runs},{(8,16,32),(8,4,128),(32,4,512),(32,16,128)})
        for r in runs:
            self.assertEqual(Fraction(r['rho']['numerator'],r['rho']['denominator']), Fraction(r['Z'],r['M']*(r['N']+1)))
        self.assertEqual(spec.round_half_up(Fraction(5,2)),3)
        self.assertEqual(spec.round_half_up(Fraction(7,3)),2)
        self.assertEqual(spec.estimates(self.manifest)['replica_bd_steps'],56000)
        self.assertEqual(spec.estimates(self.manifest)['expected_attempts'],131200)
        self.assertFalse(self.manifest['execution_authorized'])
        approval=spec.load(self.config/'approval.template.json')
        self.assertFalse(approval['execution_authorized']);self.assertTrue(all(v is None for v in approval['limits'].values()))

    def test_exact_schedules_cadences_and_no_interpolation(self):
        times=[]
        for dt in spec.TIMESTEPS:
            s=spec.schedule(dt)
            self.assertEqual(len(s['steps']),70);self.assertEqual(len(s['snapshot_steps']),6)
            self.assertEqual(s['steps'],sorted(set(s['steps'])))
            self.assertEqual(s['steps'][0],0);self.assertEqual(Fraction(dt)*s['steps'][-1],Fraction(1,4))
            self.assertTrue(set(s['snapshot_steps'])<=set(s['steps']))
            self.assertEqual(s['diagnostic_only_steps'],[1]);self.assertNotIn(1,s['shared_steps'])
            self.assertEqual(Fraction(dt)*s['legacy_stride'],Fraction(1,200))
            times.append([Fraction(dt)*step for step in s['shared_steps']])
        self.assertEqual(times[0],times[1]);self.assertEqual(len(times[0]),69)
        self.assertEqual(times[0][:21],[Fraction(i,2000) for i in range(21)])
        with self.assertRaises(spec.Invalid):spec.exact_step('0.0001','0.00025')

    def test_manifest_schedule_tool_corruption_rejected(self):
        path=self.config/'manifest.json';original=path.read_bytes()
        path.write_bytes(original+b' ')
        with self.assertRaises(spec.Invalid):spec.validate_manifest(path,self.sha)
        path.write_bytes(original)
        obj=spec.load(path);obj['runs'][0]['Z']+=1;path.write_bytes(spec.encoded(obj))
        with self.assertRaises(spec.Invalid):spec.validate_manifest(path,spec.digest(path))
        path.write_bytes(original)
        name=self.manifest['runs'][0]['schedule'];schedule=self.config/name
        schedule.write_bytes(schedule.read_bytes()+b'2500\n')
        with self.assertRaises(spec.Invalid):spec.validate_manifest(path,self.sha)
        with patch.object(spec,'tool_hashes',return_value={}):
            with self.assertRaises(spec.Invalid):spec.validate_manifest(path,self.sha)

    def test_strict_json_and_missing_authentication(self):
        p=self.root/'bad.json'
        for data in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}'):
            p.write_text(data)
            with self.assertRaises(spec.Invalid):spec.load(p)
        with self.assertRaises(spec.Invalid):spec.validate_manifest(self.config/'manifest.json',None)
        p.write_text('{"version":1,"status":"building"}')
        with self.assertRaises((spec.Invalid,KeyError)):auth.validate_build(p,spec.digest(p),self.manifest)

    def test_default_preflight_and_authorization_refusal(self):
        args=argparse.Namespace(manifest=self.config/'manifest.json',manifest_sha256=self.sha,
             build_receipt=None,build_sha256=None,approval=None,approval_sha256=None,gpu_uuid=None,
             output_root=self.root/'not-created',authorize_pilot_execution=False)
        with patch.object(subprocess,'Popen',side_effect=AssertionError('no simulation launch')):
            # Manifest source lookup uses check_output/Popen; already checked above.
            with patch.object(spec,'validate_manifest',return_value=self.manifest):
                result,manifest,built,approval,limits=runner.preflight(args)
                self.assertEqual(result['mode'],'read-only preflight');self.assertTrue(result['blockers'])
                with self.assertRaises(spec.Invalid):runner.execute(args,result,manifest,built,approval,limits)
        self.assertFalse(args.output_root.exists())
        p=subprocess.run([sys.executable,str(spec.PROJECT/'e1_d1_pilot_runner.py'),'preflight',
             '--manifest',str(args.manifest),'--manifest-sha256',self.sha],capture_output=True,text=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(len(json.loads(p.stdout)['runs']),32)
        self.assertFalse(args.output_root.exists())

    def test_repository_output_isolation_before_writes(self):
        forbidden=spec.REPOSITORY/'src/e1-d11-forbidden-fixture'
        with self.assertRaises(spec.Invalid):spec.output_path(forbidden)
        with self.assertRaises(spec.Invalid):spec.freeze(forbidden)
        self.assertFalse(forbidden.exists())
        self.assertEqual(spec.output_path(spec.PROJECT/'build/e1-d11-fixture'),spec.PROJECT/'build/e1-d11-fixture')
        with self.assertRaises(spec.Invalid):spec.output_path(self.root/'child',self.root)

    def test_packaged_default_and_reproducible_config(self):
        path=spec.CONFIG/'manifest.json';sha=(spec.CONFIG/'manifest.sha256').read_text().split()[0]
        self.assertEqual(spec.validate_manifest(path,sha),self.manifest)
        self.assertEqual(path.read_bytes(),(self.config/'manifest.json').read_bytes())
        p=subprocess.run([sys.executable,str(spec.PROJECT/'e1_d1_pilot_runner.py')],capture_output=True,text=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)
        result=json.loads(p.stdout);self.assertFalse(result['execution_authorized']);self.assertTrue(result['blockers'])
        self.assertGreater(result['observed_resources']['available_host_bytes'],0)

    def test_incomplete_analysis_creates_no_output(self):
        args=argparse.Namespace(campaign=self.root/'absent',manifest=self.config/'manifest.json',manifest_sha256=self.sha,
             approval_sha256='0'*64,completion_sha256='0'*64,output=self.root/'must-not-exist.json')
        with self.assertRaises((OSError,spec.Invalid)):science.analyze(args)
        self.assertFalse(args.output.exists())

    def test_incomplete_interrupted_campaign_never_analyzed(self):
        root=self.root/'interrupted';root.mkdir()
        spec.atomic(root/'status.json',{'version':1,'status':'interrupted'})
        with self.assertRaises((OSError,spec.Invalid,KeyError)):
            auth.authenticate_campaign(root,self.config/'manifest.json',self.sha,'0'*64)
        self.assertFalse((root/'campaign_complete.json').exists())

    def test_approval_templates_and_resource_failures(self):
        approval=spec.load(self.config/'approval.template.json')
        with self.assertRaises(spec.Invalid):runner.validate_approval(approval,self.sha,'b'*64,self.root,'e'*64)
        # Pure synthetic approval object, never passed to execution or persisted.
        approval.update(execution_authorized=True,approval_reference='SYNTHETIC UNIT TEST ONLY',
                        build_receipt_sha256='b'*64,environment_sha256='e'*64,output_root=str(self.root))
        approval['limits']={key:1 for key in approval['limits']}
        runner.validate_approval(approval,self.sha,'b'*64,self.root,'e'*64)
        approval['limits']['per_run_seconds']=121
        with self.assertRaises(spec.Invalid):runner.validate_approval(approval,self.sha,'b'*64,self.root,'e'*64)
        approval['limits']['per_run_seconds']=1;approval['limits']['min_free_gpu_bytes']=10**20
        with self.assertRaises(spec.Invalid):runner.resource_check(self.root,approval['limits'],1024)

    def test_complete_synthetic_cohort_authentication_and_changed_status(self):
        # Mock the separately tested build/per-run readers. No trajectories,
        # executable approval, or pilot execution flag is involved.
        root=self.root/'synthetic-reader';root.mkdir();(root/'config').mkdir();(root/'runs').mkdir();(root/'provenance').mkdir()
        import shutil
        shutil.copyfile(self.config/'manifest.json',root/'manifest.json')
        for name in self.manifest['schedules']:shutil.copyfile(self.config/name,root/'config'/name)
        (root/'provenance/semiflexible').write_text('nonexecutable synthetic proof')
        (root/'provenance/build.log').write_text('synthetic transcript')
        (root/'build.json').write_text('{}')
        for run in self.manifest['runs']:(root/'runs'/run['id']).mkdir()
        approval=spec.load(self.config/'approval.template.json')
        approval.update(execution_authorized=True,approval_reference='SYNTHETIC READER TEST ONLY',output_root=str(root),
                        build_receipt_sha256=spec.digest(root/'build.json'),gpu_uuid='GPU-00000000',environment_sha256=spec.identity({'gpu':{'uuid':'GPU-00000000'}}))
        approval['limits']={key:1 for key in approval['limits']};approval['limits'].update(per_run_output_bytes=1024**2,aggregate_output_bytes=1024**2)
        spec.atomic(root/'approval.json',approval)
        ledger={'version':1,'campaign':self.manifest['campaign'],'manifest_sha256':self.sha,'approval_sha256':spec.digest(root/'approval.json'),
                'environment':{'gpu':{'uuid':'GPU-00000000'}},'environment_sha256':approval['environment_sha256'],
                'preparation_sources':self.manifest['preparation_sources'],'limits':approval['limits'],'started_utc':'2026-01-01T00:00:00+00:00'}
        source={'repository':spec.REPOSITORY_ID,'sha':spec.ACCEPTED_SHA}
        ledger.update(source=source,build_receipt_sha256=approval['build_receipt_sha256'])
        spec.atomic(root/'campaign.json',ledger)
        status={'version':1,'status':'completed','completed_run_ids':[r['id'] for r in self.manifest['runs']],'wall_seconds':.5}
        spec.atomic(root/'status.json',status)
        final={'version':1,'status':'completed','campaign_sha256':spec.digest(root/'campaign.json'),'status_sha256':spec.digest(root/'status.json'),
               'run_ids':status['completed_run_ids'],'receipts':{r['id']:'0'*64 for r in self.manifest['runs']}}
        spec.atomic(root/'campaign_complete.json',final)
        completion_sha=spec.digest(root/'campaign_complete.json')
        build={'source':source,'binary':{'file':spec.file_record(root/'provenance/semiflexible')},'log':{'file':spec.file_record(root/'provenance/build.log')}}
        def item(directory,run,*args):
            return {'run':run,'receipt':{'started_utc':'2026-01-01T00:00:00+00:00','ended_utc':'2026-01-01T00:00:00+00:00','wall_seconds':.001}}
        with patch.object(auth,'validate_build',return_value=build),patch.object(auth,'authenticate_run',side_effect=item):
            _,runs=auth.authenticate_campaign(root,self.config/'manifest.json',self.sha,spec.digest(root/'approval.json'),completion_sha);self.assertEqual(len(runs),32)
            status['status']='interrupted';spec.atomic(root/'status.json',status)
            with self.assertRaises(spec.Invalid):auth.authenticate_campaign(root,self.config/'manifest.json',self.sha,spec.digest(root/'approval.json'),completion_sha)



class ReferenceTests(unittest.TestCase):
    def test_independent_radial_integrals_and_finite_chain_covariance(self):
        nodes,w=leggauss(384);end=1+16/math.sqrt(30);ell=(nodes+1)*end/2
        weight=w*ell**2*np.exp(-15*(ell-1)**2)
        mu1=float(weight@ell/weight.sum());mu2=float(weight@(ell**2)/weight.sum())
        for n,kappa,ne,nu in spec.BASE_CASES:
            z=64*n//ne;ref=science.reference(n,64,z,kappa,nu)
            np.testing.assert_allclose([ref['mu1'],ref['mu2']],[mu1,mu2],rtol=2e-13,atol=2e-13)
            covariance=np.array([[mu2 if i==j else mu1**2*ref['h']**abs(i-j) for j in range(n)] for i in range(n)])
            accumulate=np.tril(np.ones((n+1,n)),k=-1)
            coordinate=accumulate@covariance@accumulate.T;center=np.eye(n+1)-np.ones((n+1,n+1))/(n+1)
            self.assertAlmostEqual(ref['targets']['re2'],covariance.sum(),places=10)
            self.assertAlmostEqual(ref['targets']['rg2'],np.trace(center@coordinate@center)/(n+1),places=10)
            if kappa==0:self.assertAlmostEqual(ref['targets']['rg2'],mu2*((n+1)**2-1)/(6*(n+1)),places=12)

    def test_independent_orientation_transfer_matrix(self):
        u,w=leggauss(48)
        for k in (0,2,10):
            kernel=np.ones((48,48))/2 if k==0 else k/(2*math.sinh(k))*np.exp(k*np.outer(u,u))*np.i0(k*np.outer(np.sqrt(1-u*u),np.sqrt(1-u*u)))
            transition=kernel*w[None,:];np.testing.assert_allclose(transition.sum(axis=1),1,atol=1e-12)
            vector=u.copy()
            for s in range(1,17):
                vector=transition@vector
                actual=3*np.dot(w*u/2,vector)
                self.assertAlmostEqual(actual,science.langevin(k)**s,places=11)

    def test_exact_hypergeometric_against_enumerated_subsets(self):
        counts=np.zeros(4);occupancy=np.zeros(9);states=list(itertools.combinations(range(9),3))
        for sites in states:
            occupancy[list(sites)]+=1
            for c in range(3):counts[sum(c*3<=i<(c+1)*3 for i in sites)]+=1
        ref=science.reference(2,3,3,0,10)
        np.testing.assert_allclose(counts/(3*len(states)),ref['population_pmf'],atol=1e-15)
        np.testing.assert_allclose(occupancy/len(states),1/3,atol=1e-15)
        pmf=ref['population_pmf'];self.assertAlmostEqual(sum(i*p for i,p in enumerate(pmf)),1)
        self.assertAlmostEqual(sum((i-1)**2*p for i,p in enumerate(pmf)),ref['sigma_Z']**2)

    def test_gaussian_connector_and_rate_overlap_references(self):
        # Independent numerical overlap of two 1D normal densities.
        u,w=leggauss(256);sigma=math.sqrt(5/3)
        for length in (.5,1.,1.5):
            lo,hi=-12*sigma,length/2
            x=(lo+hi)/2+(hi-lo)*u/2
            overlap=2*(hi-lo)/2*np.dot(w,np.exp(-.5*((x-length)/sigma)**2)/(sigma*math.sqrt(2*math.pi)))
            self.assertAlmostEqual(overlap,math.erfc(length/(2*math.sqrt(2)*sigma)),places=12)
        for p in science.PROBABILITIES:
            cut=math.sqrt(science.chi3_quantile(p));r=(u+1)*cut/2
            integrated=cut/2*np.dot(w,math.sqrt(2/math.pi)*r*r*np.exp(-r*r/2))
            self.assertAlmostEqual(integrated,p,places=12)
            self.assertAlmostEqual(science.chi3_cdf(cut*cut),p,places=13)
        ref=science.reference(8,64,32,0,10)['targets']
        self.assertEqual(ref['connector_e2'],5)
        for d in 'xyz':self.assertAlmostEqual(ref['connector_second_'+d],5/3)
        self.assertAlmostEqual(ref['rate_attempts'],ref['rate_accepted']+ref['rate_boundary']+ref['rate_occupied']+ref['rate_metropolis'])
        self.assertAlmostEqual(ref['rate_renewal_accepted'],ref['rate_renewal_same_chain']+ref['rate_renewal_cross_chain'])


class ScienceTests(unittest.TestCase):
    def test_replica_not_chain_standard_deviation_and_independent_contrasts(self):
        values=[1,3,5,7];out=science.summary(values,4)
        self.assertEqual(out['replicas'],4);self.assertEqual(out['mean'],4)
        self.assertAlmostEqual(out['replica_sd'],math.sqrt(20/3))
        self.assertAlmostEqual(out['standard_error'],math.sqrt(20/3)/2)
        self.assertAlmostEqual(science.T3,3.1824463052837)
        contrast=science.independent_contrast(values,[2,4,6,8])
        self.assertEqual(contrast['coarse_minus_fine'],1)
        self.assertAlmostEqual(contrast['standard_error'],math.sqrt(10/3))
        with self.assertRaises(spec.Invalid):science.summary([1]*256)

    def test_balanced_synthetic_connectors_and_joint_bias(self):
        run={'N':2,'M':4,'Z':8,'kappa':0,'nu_hop':10}
        ref=science.reference(2,4,8,0,10)
        re2=ref['targets']['re2']
        bb=[{'re2':re2,'rg2':ref['targets']['rg2'],'mean_r':ref['mu1'],'mean_r2':ref['mu2'],'tangent1':0} for _ in range(4)]
        xyz=np.array(list(itertools.product((-1,1),repeat=3)))*math.sqrt(5/3)
        con=[dict(zip(('ex','ey','ez'),r),e2=float(r@r)) for r in xyz]
        ids=[0,1,-1,2,3,-1,4,5,-1,6,7,-1]
        pop=[{'z':2,'e2_sum':10} for _ in range(4)]
        result=science.frame_statistics(run,bb,pop,con,ids,[])
        for key in ('re2','rg2','mean_r','mean_r2','connector_e2','A_joint','B_joint'):
            self.assertAlmostEqual(result[key],ref['targets'][key])
        for d in 'xyz':self.assertAlmostEqual(result['connector_mean_'+d],0);self.assertAlmostEqual(result['connector_second_'+d],5/3)
        biased=copy.deepcopy(bb);biased[0]['re2']*=2
        biased_pop=[{'z':3,'e2_sum':30},{'z':1,'e2_sum':5},{'z':2,'e2_sum':10},{'z':2,'e2_sum':10}]
        biased_con=copy.deepcopy(con)
        for row in biased_con[:3]:
            for d in ('ex','ey','ez'):row[d]*=math.sqrt(2)
            row['e2']*=2
        actual=science.frame_statistics(run,biased,biased_pop,biased_con,[0,1,2,3,-1,-1,4,5,-1,6,7,-1],[])
        self.assertGreater(actual['re2']-ref['targets']['re2'],0)
        self.assertAlmostEqual(actual['A_joint'],1/(4*ref['sigma_Z']))
        self.assertAlmostEqual(actual['B_joint'],15/40)

    def test_equilibrium_centered_and_biased_synthetic_32_replica_aggregation(self):
        records=[]
        for run in spec.proposed_manifest()['runs']:
            target=science.reference(run['N'],64,run['Z'],run['kappa'],run['nu_hop'])['targets']['re2']
            offset=(-3,-1,1,3)[run['replica']-1]*.01
            shift=.1*target if run['cell']%2==0 else 0
            shared={tick:{'re2':target+offset+shift} for tick in spec.shared_ticks()}
            records.append({'run':run,'shared':shared,'diagnostic_only':[], 'event_totals':{},'coverage':{}})
        # ACF endpoints used by production aggregation include these observables.
        for r in records:
            for values in r['shared'].values():
                for key in ('rg2','connector_e2','A_joint','B_joint'):values[key]=0.
        result=science.aggregate(records)
        cell=result['cells']['1']['shared_times']['0']['metrics']['re2']
        self.assertAlmostEqual(cell['difference_from_reference'],0)
        contrast=result['timestep_contrasts'][0]['shared_times']['0']['metrics']['re2']
        self.assertAlmostEqual(contrast['coarse_minus_fine'],.1*cell['reference'])
        self.assertIn('no scientific equivalence',result['classification'])
        self.assertIsNone(science.acf_diagnostic([1,2]*25)['tau_int'])
        with self.assertRaises(spec.Invalid):science.aggregate(records[:-1])


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='d11-process-');self.root=Path(self.tmp.name)
        self.limits={'per_run_seconds':2,'aggregate_seconds':4,'per_run_output_bytes':1024*1024,
                     'aggregate_output_bytes':2*1024*1024,'max_host_rss_bytes':128*1024*1024,'min_free_disk_bytes':1}
    def tearDown(self):self.tmp.cleanup()
    def child(self,code):return [sys.executable,'-c',code]
    def run_child(self,code):return runner.run_process(self.child(code),self.root,runner.environment(),self.limits,self.root,time.monotonic())
    def test_success_and_application_failure(self):
        result=self.run_child("print('bounded CPU technical child')")
        self.assertEqual(result['exit_code'],0);self.assertEqual(result['status'],'exited');self.assertGreater(result['max_rss_bytes'],0)
        self.assertEqual(spec.load(self.root/'process.json')['status'],'exited')
    def test_failure_is_not_completion(self):
        result=self.run_child("raise SystemExit(7)")
        self.assertEqual(result['exit_code'],7);self.assertEqual(result['status'],'application_failure')
    def test_timeout_and_partial_logs_preserved(self):
        self.limits['per_run_seconds']=.1
        result=self.run_child("import time;print('partial',flush=True);time.sleep(5)")
        self.assertEqual(result['status'],'per_run_timeout');self.assertNotEqual(result['exit_code'],0)
        self.assertIn('partial',(self.root/'stdout.log').read_text())
    def test_interruption_reaps_child_and_preserves_failure_record(self):
        original=time.sleep;calls=0
        def interrupt_once(seconds):
            nonlocal calls
            calls+=1
            if calls==1:raise KeyboardInterrupt('synthetic test interruption')
            original(seconds)
        with patch.object(runner.time,'sleep',side_effect=interrupt_once):
            with self.assertRaises(KeyboardInterrupt):self.run_child('import time;time.sleep(5)')
        record=spec.load(self.root/'process.json');self.assertEqual(record['status'],'interrupted');self.assertLess(record['exit_code'],0)
        self.assertFalse((self.root/'campaign_complete.json').exists())

    def test_aggregate_timeout_and_output_limits(self):
        self.limits['aggregate_seconds']=.1
        result=self.run_child('import time;time.sleep(5)')
        self.assertEqual(result['status'],'aggregate_timeout')
        (self.root/'stdout.log').unlink();(self.root/'stderr.log').unlink()
        self.limits['aggregate_seconds']=4;self.limits['per_run_output_bytes']=1024
        result=self.run_child("print('x'*100000)")
        self.assertNotEqual(result['status'],'exited')

    def test_parent_death_guard_prevents_orphan_child(self):
        script="""import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import e1_d1_pilot_runner as r
root=Path(sys.argv[2]);limits={"per_run_seconds":10,"aggregate_seconds":10,"per_run_output_bytes":1048576,"aggregate_output_bytes":2097152,"max_host_rss_bytes":134217728,"min_free_disk_bytes":1}
r.run_process([sys.executable,"-c","import os,time;print(os.getpid(),flush=True);time.sleep(5)"],root,r.environment(),limits,root,time.monotonic())
"""
        parent=subprocess.Popen([sys.executable,'-c',script,str(spec.PROJECT),str(self.root)],env=runner.environment())
        try:
            deadline=time.monotonic()+3;pid=None
            while time.monotonic()<deadline:
                path=self.root/'stdout.log'
                if path.exists() and path.read_text().strip():pid=int(path.read_text().strip());break
                time.sleep(.02)
            self.assertIsNotNone(pid)
            parent.kill();parent.wait(timeout=2)
            deadline=time.monotonic()+2
            while time.monotonic()<deadline:
                state=Path('/proc')/str(pid)/'status'
                if not state.exists() or 'State:\tZ' in state.read_text():break
                time.sleep(.02)
            else:self.fail('orphan technical child survived its supervisor')
        finally:
            if parent.poll() is None:parent.kill();parent.wait(timeout=2)



if __name__=='__main__':unittest.main()
