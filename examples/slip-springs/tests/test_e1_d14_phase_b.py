"""CPU/reference/synthetic Phase B tests; no physical trajectories or executable approval."""
import argparse
import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import e1_d14_phase_b as spec
import e1_d14_phase_b_auth as auth
import e1_d14_phase_b_runner as runner
import e1_d14_phase_b_analysis as analysis
import e1_d13_phase_a_runner as phase_a_runner
import test_e1_d13_phase_a as prior_tests
from test_e1_d1_pilot import ReferenceTests # Independent quadrature/transfer/covariance/enumeration tests.


def synthetic_replicas(manifest,drift=False):
    """Deterministic reduced-observable oracles, not authentic raw simulation evidence."""
    result=[]
    for run in manifest['runs']:
        ref=analysis.reference(run['N'],run['M'],run['Z'],run['kappa'],run['nu_hop'])
        targets=ref['targets'];full=manifest['schedules'][run['schedule']]['steps']
        regular=list(range(0,run['steps']+1,run['sample']));all_steps=sorted(set(full)|set(regular))
        series={}
        for step in all_steps:
            time=Fraction(step)*Fraction(run['dt'])
            keys=set(targets)-{k for k in targets if k.startswith('rate_')} if step in full else set(analysis.SHORT)
            if step in full and step not in (0,1):keys|={k for k in targets if k.startswith('rate_')}
            values={k:targets[k] for k in keys}
            if drift:
                values['re2']*=1+.02*float(time)+(.03 if run['cell']%2==0 else 0)+(.001 if run['replica']==2 else -.001)
                if 'A_joint' in values:values['A_joint']=.01*float(time)
            series[str(time)]={'step':step,'time':float(time),'diagnostic_only':step==1,'metrics':values}
        rates={str(Fraction(i,2)):{'metrics':{k:v for k,v in targets.items() if k.startswith('rate_')}} for i in range(1,21)}
        result.append({'run':run,'series':series,'reference':ref,
            'regular_scalar_times':[analysis.time_key(s,run['dt']) for s in regular],
            'regular_e1_times':[str(Fraction(i,2)) for i in range(21)],'regular_event_rates':rates})
    return result


class PhaseBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='d14-cpu-');cls.root=Path(cls.temp.name)
        cls.config=cls.root/'config';cls.sha=spec.freeze(cls.config)
        cls.manifest=spec.validate_manifest(cls.config/'manifest.json',cls.sha)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_manifest_matrix_seeds_counts_and_parent_bytes(self):
        m=self.manifest;self.assertEqual(len(m['runs']),8);self.assertEqual(m['pairing'],[])
        self.assertEqual(len({r['seed'] for r in m['runs']}),8)
        self.assertEqual([r['seed'] for r in m['runs']],[721400101,721400102,721400201,721400202,721400301,721400302,721400401,721400402])
        self.assertEqual(sum(r['steps'] for r in m['runs']),560000)
        self.assertEqual(spec.estimates(m)['expected_attempts'],4096000)
        self.assertEqual({(r['N'],r['M'],r['Z'],r['Ne'],r['nu_hop']) for r in m['runs']},{(32,64,512,4,100)})
        self.assertEqual({(r['kappa'],r['dt']) for r in m['runs']},{(0,'0.0001'),(0,'0.00025'),(10,'0.0001'),(10,'0.00025')})
        for r in m['runs']:
            self.assertEqual(Fraction(r['dt'])*r['steps'],10)
            f=m['schedules'][r['schedule']]['steps'];s=m['schedules'][r['snapshots']]['steps']
            self.assertEqual((len(f),len(s)),(26,4));self.assertEqual(f[0],0);self.assertEqual(f[-1],r['steps'])
            self.assertTrue(set(s)<=set(f));self.assertEqual(r['sample']*Fraction(r['dt']),Fraction('0.1'))
            self.assertEqual(spec.row_counts(r,f,s)['samples.csv'],64*101)
            self.assertEqual(spec.row_counts(r,f,s)['equilibrium_backbone.csv'],64*5)
        for name,entry in m['schedules'].items():
            self.assertEqual((self.config/name).read_bytes(),(spec.design.CONFIG/'phase-B'/name).read_bytes())
        self.assertEqual(m['parent_design_sha256'],spec.DESIGN_SHA)
        self.assertEqual(spec.digest(spec.CONFIG/'manifest.json'),self.sha)

    def test_deterministic_freeze_and_no_permissions(self):
        path=self.root/'reproduced';self.assertEqual(spec.freeze(path),self.sha)
        for p in self.config.iterdir():self.assertEqual(p.read_bytes(),(path/p.name).read_bytes())
        self.assertFalse(self.manifest['execution_authorized'])
        self.assertTrue(all(v is None for v in self.manifest['approved_limits'].values()))
        approval=spec.load(self.config/'approval.template.json');self.assertFalse(approval['execution_authorized'])
        self.assertTrue(all(v is None for v in approval['limits'].values()))
        with self.assertRaises(FileExistsError):spec.freeze(path)

    def test_changed_or_other_phase_refusal(self):
        for key in ('source','matrix','tools','extra','phase'):
            value=copy.deepcopy(self.manifest)
            if key=='source':value['accepted_source_sha']='0'*40
            elif key=='matrix':value['runs'][0]['kappa']=2
            elif key=='tools':value['preparation_sources']['e1_d14_phase_b_analysis.py']='0'*64
            elif key=='extra':value['runs'].append(value['runs'][0])
            else:value['campaign']='phase-C'
            path=self.root/('changed-'+key+'.json');path.write_bytes(spec.encoded(value))
            with self.assertRaises(ValueError):spec.validate_manifest(path,spec.digest(path))
        with self.assertRaises(ValueError):spec.validate_manifest(spec.phase_a.CONFIG/'manifest.json',spec.digest(spec.phase_a.CONFIG/'manifest.json'))
        copied=self.root/'bad-schedule';shutil.copytree(self.config,copied)
        (copied/'dt0.0001.full.steps').write_text('0 1 100000\n')
        with self.assertRaises(ValueError):spec.validate_manifest(copied/'manifest.json',self.sha)
        with self.assertRaises(ValueError):spec.old.exact_step('0.0001','0.00025')

    def test_refusal_of_execution_and_phase_a_approval(self):
        args=argparse.Namespace(authorize_phase_b_execution=False)
        with patch.object(runner.accepted,'execute',side_effect=AssertionError('no execution')):
            with self.assertRaises(ValueError):runner.execute(args,{},self.manifest,None,None,None)
        approval=spec.load(spec.phase_a.CONFIG/'approval.template.json')
        with self.assertRaises(ValueError):runner.shared.validate_approval(approval,self.sha,'b'*64,self.root,'e'*64)
        with self.assertRaises(ValueError):auth.validate_build('/tmp/e1-d13-build/build.json',
            '1739e51ebbe43a81a810d09274d9a9304fafb339166d7e13f5e4600bd32d37e0',self.manifest)
        self.assertIs(phase_a_runner.spec,spec.phase_a)
        for flag in ('--authorize-phase-a-execution','--phase-C'):
            p=subprocess.run([sys.executable,str(spec.PROJECT/'e1_d14_phase_b_runner.py'),'preflight',flag],capture_output=True,timeout=10)
            self.assertNotEqual(p.returncode,0)

    def test_r2_intervals_and_independent_contrast(self):
        result=analysis.summary([1.,3.],2.)
        self.assertEqual(result['replica_values'],[1.,3.]);self.assertEqual(result['mean'],2)
        self.assertAlmostEqual(result['replica_sd'],math.sqrt(2));self.assertEqual(result['standard_error'],1.)
        self.assertAlmostEqual(analysis.T1,12.7062047361747,places=11)
        self.assertAlmostEqual(result['pointwise_nominal_95_interval'][1],2+analysis.T1)
        self.assertEqual(result['difference_from_reference'],0)
        contrast=analysis.independent_contrast([1,3],[2,4]);self.assertEqual(contrast['coarse_minus_fine'],1)
        self.assertAlmostEqual(contrast['standard_error'],math.sqrt(2))
        self.assertTrue(analysis.summary([2,2])['zero_observed_replica_variance'])
        for x in ([1],[1,2,3,4],[1,float('nan')]):
            with self.assertRaises(ValueError):analysis.summary(x)

    def test_exact_equilibrium_reduced_oracle_and_supported_grids(self):
        replicas=synthetic_replicas(self.manifest);result=analysis.aggregate(replicas,self.manifest)
        self.assertIsNone(result['scientific_acceptance'])
        for cell in result['cells'].values():
            self.assertEqual(cell['time_resolved']['0']['metrics']['re2']['difference_from_reference'],0)
            self.assertEqual(cell['time_resolved']['10']['paired_change_from_initial']['re2']['mean'],0)
            self.assertEqual(cell['early_versus_late']['re2']['paired_late_minus_early']['mean'],0)
            self.assertNotIn('A_joint',cell['time_resolved']['1/10']['metrics'])
            self.assertNotIn('tangent8',cell['time_resolved']['1/10']['metrics'])
            self.assertIn('A_joint',cell['time_resolved']['1/2']['metrics'])
            self.assertIsNone(cell['time_resolved']['1/2']['paired_change_from_initial']['rate_accepted'])
            acf=next(iter(cell['acf_by_replica'].values()))
            self.assertEqual(acf['re2']['samples'],101);self.assertEqual(acf['connector_e2']['samples'],21)
            self.assertEqual(acf['rate_accepted']['samples'],20)
        for contrast in result['timestep_contrasts']:
            self.assertEqual(contrast['shared_physical_times']['1/2000']['re2']['coarse_minus_fine'],0)
            self.assertNotIn('1/10000',contrast['shared_physical_times'])
            self.assertNotIn('1/4000',contrast['shared_physical_times'])

    def test_drift_early_late_and_timestep_contrasts(self):
        replicas=synthetic_replicas(self.manifest,True);result=analysis.aggregate(replicas,self.manifest)
        ref=replicas[0]['reference']['targets']['re2']
        change=result['cells']['1']['early_versus_late']['re2']['paired_late_minus_early']['mean']
        self.assertAlmostEqual(change,.18*ref)
        self.assertAlmostEqual(result['cells']['1']['time_resolved']['10']['paired_change_from_initial']['re2']['mean'],.2*ref)
        self.assertAlmostEqual(result['cells']['1']['early_versus_late']['A_joint']['paired_late_minus_early']['mean'],.09)
        self.assertAlmostEqual(result['timestep_contrasts'][0]['shared_physical_times']['10']['re2']['coarse_minus_fine'],.03*ref)
        self.assertEqual(len(result['cells']['1']['time_resolved']['10']['metrics']['re2']['replica_values']),2)

    def test_transient_drift_is_not_an_endpoint_pass(self):
        replicas=synthetic_replicas(self.manifest)
        for r in replicas:r['series']['5']['metrics']['re2']*=1.1
        result=analysis.aggregate(replicas,self.manifest)
        cell=result['cells']['1'];self.assertEqual(cell['time_resolved']['10']['paired_change_from_initial']['re2']['mean'],0)
        self.assertGreater(cell['variation_across_times']['re2']['maximum_replica_mean'],cell['variation_across_times']['re2']['minimum_replica_mean'])
        self.assertIsNone(result['scientific_acceptance'])

    def test_acf_exact_grid_variance_shape_and_tail(self):
        times=[str(Fraction(i,10)) for i in range(101)];x=np.sin(np.arange(101)*.3)
        acf=analysis.acf_diagnostic(times,x,'0.1')
        centered=x-x.mean();self.assertAlmostEqual(acf['acf'][0],float(centered[:-1]@centered[1:]/(centered@centered)))
        self.assertAlmostEqual(acf['variance'],float(x.var(ddof=1)))
        self.assertIsNone(acf['tau_int']);self.assertTrue(acf['unresolved_long_time_tail']);self.assertFalse(acf['independent_samples_established'])
        self.assertEqual(len(acf['lags']),20)
        self.assertIsNone(analysis.acf_diagnostic(times,[1]*101,'.1')['tau_int'])
        constant=analysis.acf_diagnostic(times,[5/3]*101,'.1')
        self.assertEqual(constant['variance'],0);self.assertEqual(constant['acf'],[])
        times[1]='1/2000'
        with self.assertRaises(ValueError):analysis.acf_diagnostic(times,x,'.1')

    def test_event_summation_including_first_step(self):
        def counts(n,batches):
            d={k:0 for k in auth.COUNTERS};d.update(batches=batches,attempts=n,accepted=n);return d
        events=[{'step':s,'counts':counts(n,bd)} for s,n,bd in ((0,0,0),(1,2,1),(5,3,4),(10,7,5))]
        rebinned=analysis.rates_between(events,[0,5,10],'.0001')
        self.assertEqual(rebinned[5]['counts']['attempts'],5)
        self.assertEqual(rebinned[5]['metrics']['rate_attempts'],10000)
        self.assertEqual(sum(r['counts']['attempts'] for r in rebinned.values()),12)
        wide=analysis.rates_between(events,[0,10],'.0001');self.assertEqual(wide[10]['metrics']['rate_attempts'],12000)
        with self.assertRaises(ValueError):analysis.rates_between(events,[0,4,10],'.0001')

    def test_joint_component_and_population_reconstruction(self):
        run={'N':3,'M':3,'Z':6,'kappa':0,'nu_hop':10}
        ref=analysis.reference(3,3,6,0,10)
        bb=[dict(re2=ref['targets']['re2'],rg2=ref['targets']['rg2'],mean_r=ref['mu1'],mean_r2=ref['mu2'],tangent1=0,tangent2=0) for _ in range(3)]
        e=np.sqrt(5)*np.vstack([np.eye(3),-np.eye(3)])
        con=[dict(ex=x,ey=y,ez=z,e2=x*x+y*y+z*z) for x,y,z in e]
        pop=[dict(z=z,e2_sum=5*z) for z in (0,2,4)]
        sites=[-1]*4+[0,1,-1,-1]+[2,3,4,5]
        result=analysis.science.frame_statistics(run,bb,pop,con,sites,[])
        self.assertAlmostEqual(result['connector_e2'],5);self.assertAlmostEqual(result['connector_second_x'],5/3)
        self.assertAlmostEqual(result['connector_mean_y'],0);self.assertEqual(result['A_joint'],0);self.assertEqual(result['B_joint'],0)
        for row,f in zip(bb,(-.1,0,.1)):row['re2']*=1+f
        pop[2]['e2_sum']+=4
        for row in con[2:]:
            for key in ('ex','ey','ez'):row[key]*=math.sqrt(6/5)
            row['e2']=6
        result=analysis.science.frame_statistics(run,bb,pop,con,sites,[])
        self.assertAlmostEqual(result['A_joint'],.4/(3*ref['sigma_Z']))
        self.assertAlmostEqual(result['B_joint'],.4/(6*5))
        dense=analysis.reference(32,64,512,10,100)
        pmf=dense['population_pmf'];self.assertAlmostEqual(sum(pmf),1)
        self.assertAlmostEqual(sum(z*p for z,p in enumerate(pmf)),8)
        self.assertAlmostEqual(sum((z-8)**2*p for z,p in enumerate(pmf)),dense['sigma_Z']**2)

    def test_build_source_and_executable_authentication(self):
        path,value=prior_tests.AdapterTests.build_record(self)
        self.assertEqual(auth.validate_build(path,spec.digest(path),self.manifest),value)
        changed=copy.deepcopy(value);changed['source']['sha']='0'*40;path.write_bytes(spec.encoded(changed))
        with self.assertRaises(ValueError):auth.validate_build(path,spec.digest(path),self.manifest)
        path.write_bytes(spec.encoded(value))
        with patch.object(spec,'source_identity',return_value=value['source']):
            auth.validate_build(path,spec.digest(path),self.manifest,live=True)
            binary=Path(value['binary']['path']);original=binary.read_bytes();binary.write_text('CORRUPT')
            with self.assertRaises(ValueError):auth.validate_build(path,spec.digest(path),self.manifest,live=True)
            binary.write_bytes(original)
            compiler=Path(value['cxx']['path']);compiler.write_text('CORRUPT')
            with self.assertRaises(ValueError):auth.validate_build(path,spec.digest(path),self.manifest,live=True)

    def test_cohort_missing_corrupt_interrupted_and_environment(self):
        root,build=prior_tests.AdapterTests.cohort(self)
        def item(directory,run,*unused):
            return {'run':run,'root':directory/'output','receipt':{'started_utc':'2026-01-01T00:00:00+00:00',
                'ended_utc':'2026-01-01T00:00:00+00:00','wall_seconds':.001,'max_rss_bytes':1}}
        def check():return auth.authenticate_campaign(root,self.config/'manifest.json',self.sha,spec.digest(root/'approval.json'),spec.digest(root/'campaign_complete.json'))
        with patch.object(auth,'validate_build',return_value=build),patch.object(auth.base,'validate_build',return_value=build),patch.object(auth.base,'authenticate_run',side_effect=item):
            _,items=check();self.assertEqual(len(items),8)
            binary=root/'provenance/semiflexible';data=binary.read_bytes();binary.write_text('corrupt')
            with self.assertRaises(ValueError):check()
            binary.write_bytes(data)
            ledger_path=root/'campaign.json';old=ledger_path.read_bytes();ledger=spec.load(ledger_path)
            ledger['environment']['gpu']['uuid']='wrong';spec.atomic(ledger_path,ledger)
            complete=spec.load(root/'campaign_complete.json');complete['campaign_sha256']=spec.digest(ledger_path);spec.atomic(root/'campaign_complete.json',complete)
            with self.assertRaises(ValueError):check()
            ledger_path.write_bytes(old);complete['campaign_sha256']=spec.digest(ledger_path);spec.atomic(root/'campaign_complete.json',complete)
            folder=root/'runs'/self.manifest['runs'][0]['id'];folder.rmdir()
            with self.assertRaises(ValueError):check()
            folder.mkdir();state=spec.load(root/'status.json');state['status']='interrupted';spec.atomic(root/'status.json',state)
            complete['status_sha256']=spec.digest(root/'status.json');spec.atomic(root/'campaign_complete.json',complete)
            with self.assertRaises(ValueError):check()
            (root/'campaign_complete.json').unlink()
            with self.assertRaises(OSError):check()

    def test_mocked_orchestration_stops_and_preserves_failures(self):
        # Every child is mocked; no executable or real Phase B approval exists.
        path,build=prior_tests.AdapterTests.build_record(type('Fixture',(),{'root':self.root/'supervision','sha':self.sha,'manifest':self.manifest})())
        environment={'gpu':{'uuid':spec.GPU_UUID,'name':'NVIDIA GeForce RTX 3060 Ti','compute_capability':'8.6'},
            'runtime_version':13000,'driver_api_version':13000,'runtime_library':build['runtime_library']['file'],
            'environment':auth.accepted.expected_environment(build['cuda_home'],spec.GPU_UUID)}
        limits={k:1 for k in spec.design.BUDGETS};limits.update(per_run_seconds=30,aggregate_seconds=60,
            per_run_output_bytes=16*1024**2,aggregate_output_bytes=64*1024**2,max_host_rss_bytes=1000,min_available_host_bytes=1000)
        resources={'free_disk_bytes':128*1024**2,'available_host_bytes':1000,'free_gpu_bytes':1000}
        for mode in ('interrupt','bad-output','success'):
            root=self.root/('mock-'+mode);approval_path=self.root/(mode+'-mock.json')
            approval={'version':1,'execution_authorized':True,'approval_reference':'NONEXECUTABLE UNIT MOCK ONLY',
                'manifest_sha256':self.sha,'build_receipt_sha256':spec.digest(path),'environment_sha256':spec.identity(environment),
                'output_root':str(root),'gpu_uuid':spec.GPU_UUID,'limits':limits}
            spec.atomic(approval_path,approval)
            args=argparse.Namespace(authorize_phase_b_execution=True,manifest=self.config/'manifest.json',manifest_sha256=self.sha,
                output_root=root,approval=approval_path,approval_sha256=spec.digest(approval_path),build_receipt=path,build_sha256=spec.digest(path))
            summary={'blockers':[],'environment':environment,'environment_sha256':spec.identity(environment)}
            def child(argv,directory,*unused):
                for name in ('stdout.log','stderr.log'):(directory/name).write_text('synthetic child')
                value={'status':'interrupted' if mode=='interrupt' else 'exited','exit_code':0,'wall_seconds':.001,'max_rss_bytes':100}
                spec.atomic(directory/'process.json',value)
                if mode=='interrupt':raise KeyboardInterrupt('synthetic interruption')
                return value
            with patch.object(auth,'validate_build',return_value=build),patch.object(runner.accepted,'machine',return_value=(environment,1000)),\
                 patch.object(runner.shared,'resource_check',return_value=resources),patch.object(runner.shared,'run_process',side_effect=child) as process,\
                 patch.object(auth,'validate_output',side_effect=ValueError('synthetic corruption') if mode=='bad-output' else None,return_value={'files':{},'event_totals':{}}),\
                 patch.object(auth.base,'authenticate_run',return_value={}):
                if mode=='success':
                    self.assertEqual(runner.execute(args,summary,self.manifest,build,approval,limits)['status'],'completed')
                    self.assertEqual(process.call_count,8);self.assertTrue((root/'campaign_complete.json').exists())
                else:
                    with self.assertRaises(KeyboardInterrupt if mode=='interrupt' else ValueError):runner.execute(args,summary,self.manifest,build,approval,limits)
                    self.assertEqual(process.call_count,1);self.assertFalse((root/'campaign_complete.json').exists())
                    self.assertEqual(spec.load(root/'status.json')['status'],'interrupted' if mode=='interrupt' else 'failed')

    def test_incomplete_reader_and_analysis_refusal(self):
        args=argparse.Namespace(campaign=self.root/'missing',output=self.root/'must-not-exist.json',manifest=self.config/'manifest.json',
            manifest_sha256=self.sha,approval_sha256='0'*64,completion_sha256='0'*64)
        with self.assertRaises((OSError,ValueError)):analysis.analyze(args)
        self.assertFalse(args.output.exists())
        with self.assertRaises(ValueError):analysis.aggregate(synthetic_replicas(self.manifest)[:-1],self.manifest)


if __name__=='__main__':unittest.main()
