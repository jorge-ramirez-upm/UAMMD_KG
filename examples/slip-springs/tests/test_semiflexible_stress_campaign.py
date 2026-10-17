"""Bounded independent fixtures; never execute a frozen campaign member."""
import contextlib
import copy
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import semiflexible_stress_analysis as a
import semiflexible_stress_campaign as manager
from semiflexible_stress_host import generate,write_parameters

BINARIES=[Path(p).resolve() for p in sys.argv[1:]]
sys.argv[1:]=[]


def mutate_csv(path,change):
    import csv
    with open(path,newline='') as f:
        reader=csv.DictReader(f);header=reader.fieldnames;data=list(reader)
    change(data)
    with open(path,'w',newline='') as f:
        writer=csv.DictWriter(f,header);writer.writeheader();writer.writerows(data)


def mutate_json(path,key,value):
    d=json.loads(path.read_text());d[key]=value;path.write_text(json.dumps(d))


class HostReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='stress-readiness-bounded-');cls.root=Path(cls.tmp.name)
        cls.runs=[]
        for index,binary in enumerate(BINARIES):
            for diagnostic in (False,True):
                out=cls.root/f'gpu-{index}-{diagnostic}';param=cls.root/'model.txt'
                write_parameters(param,a.Chain.homogeneous(8,kappa=10))
                cmd=[str(binary),'--output',str(out),'--springs','8','--chains','32','--parameters',str(param),
                     '--steps','0' if diagnostic else '39','--sample','2','--dt','.0001','--seed','433201',
                     '--kbt','1.7','--stress-mode','diagnostic' if diagnostic else 'stream','--stress-dump','1',
                     '--stress-batch','7','--cpu-workers','2','--corr-levels','5','--corr-slots','8','--chain-density','.25']
                cp=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
                if cp.returncode:raise RuntimeError(cp.stderr)
                cls.runs.append(dict(phase='diagnostic' if diagnostic else 'reference',label='finite-N8-k10',
                                     precision='single' if index==0 else 'double',output=str(out),command=cmd))
        with contextlib.redirect_stdout(io.StringIO()):
            cls.manifest=generate(cls.root/'campaign',BINARIES[0].parents[1])

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=self.root);self.work=Path(self.temp.name)

    def tearDown(self):self.temp.cleanup()

    def clone(self,index=0):
        run=copy.deepcopy(self.runs[index]);source=Path(run['output']);out=self.work/'result'
        shutil.copytree(source,out);run['output']=str(out)
        run['command'][run['command'].index('--output')+1]=str(out)
        return run,out

    def test_gpu_outputs_both_precisions_and_missing_support(self):
        for run in self.runs:
            result=a.validate_run(run)
            self.assertEqual(result['metadata']['steps'],0 if run['phase']=='diagnostic' else 39)
            if run['phase']=='reference':
                self.assertTrue(any(g['name'].startswith('all direct') and g['status']=='passed' for g in result['checks']))
                self.assertEqual(result['stress_metadata']['moment_frames'],10)
        run=copy.deepcopy(self.runs[0]);run['phase']='stream'
        r=a.validate_run(run)
        self.assertTrue(any(g['status']=='insufficient_support' for g in r['checks']))

    def test_authentication_unchanged_manifest_plan_and_pilot(self):
        manifest,ids,_=a.authenticate(self.root/'campaign')
        self.assertEqual(len(ids),282);self.assertEqual(len(set(ids)),282)
        run,rid=manager.pilot(manifest,ids)
        self.assertEqual(a.options(run)['steps'],'8000000')
        self.assertEqual(a.options(run)['sample'],'400')
        self.assertEqual(run['precision'],'single');self.assertEqual(run['seed'],433201)
        diagnostic,_=manager.pilot(manifest,ids,True);self.assertEqual(diagnostic['phase'],'diagnostic')
        target=self.work/'campaign';shutil.copytree(self.root/'campaign',target)
        # Relocation without rewriting original absolute inputs must fail closed.
        with self.assertRaisesRegex(a.Invalid,'identity'):a.authenticate(target)
        plan=self.root/'campaign/PLAN_SHA256';original=plan.read_bytes()
        try:
            plan.write_text('0'*64+'  validation-plan.md\n')
            with self.assertRaisesRegex(a.Invalid,'PLAN_SHA256'):a.authenticate(self.root/'campaign')
        finally:plan.write_bytes(original)
        file=self.root/'campaign/manifest.json';original=file.read_bytes()
        for change in ('dt','chains','seed'):
            try:
                bad=json.loads(original);cmd=bad[0]['command'];cmd[cmd.index('--'+change)+1]='123'
                file.write_text(json.dumps(bad))
                with self.assertRaisesRegex(a.Invalid,'manifest scientific'):a.authenticate(self.root/'campaign')
            finally:file.write_bytes(original)
        with patch.object(sys,'argv',['manager',str(self.root/'campaign'),'run','--pilot']):
            with patch.object(subprocess,'Popen') as launch:
                self.assertEqual(manager.main(),1);launch.assert_not_called()
        refusal=a.load(self.root/'campaign/readiness-refusal.json')
        self.assertEqual(refusal['status'],'refused')
        self.assertIn('authorization',refusal['reason'])

    def test_structural_corruptions_rejected_explicitly(self):
        mutations=[
            ('samples.csv',lambda d:d.pop(5),'missing frame'),
            ('samples.csv',lambda d:d[1].update(chain='0'),'chain ID'),
            ('stress_samples.csv',lambda d:d.pop(),'truncated direct'),
            ('stress_samples.csv',lambda d:d[2].update(chain='999'),'chain ID'),
            ('stress_samples.csv',lambda d:[r.update(xx_yy=str(float(r['xx_yy'])/2)) for r in d],'normal factors'),
            ('stress_correlations.csv',lambda d:d[0].update(g='999'),'temperature normalization'),
            ('stress_correlations.csv',lambda d:d[1].update(pairs_per_chain='1'),'pairs_per_chain'),
            ('stress_correlations.csv',lambda d:d.pop(),'correlation bins'),
            ('stress_correlations.csv',lambda d:d[0].update(Cxx_yy=str(float(d[0]['Cxx_yy'])/4)),'weights'),
            ('stress_moments.csv',lambda d:d[0].update(frames='1'),'final-half stress'),
            ('stress_moments.csv',lambda d:d[1].update(chain='0'),'moment chain'),
        ]
        for i,(file,change,reason) in enumerate(mutations):
            with self.subTest(file=file,reason=reason):
                dest=self.work/str(i);run=copy.deepcopy(self.runs[0]);shutil.copytree(run['output'],dest);run['output']=str(dest)
                mutate_csv(dest/file,change)
                with self.assertRaisesRegex(a.Invalid,reason):a.validate_run(run)
        for i,(file,key,value,reason) in enumerate([
            ('metadata.json','dt',.02,'metadata inconsistent: dt'),
            ('metadata.json','integration_seconds',-1,'performance metadata'),
            ('metadata.json','overall_ns_per_bead_step',999,'performance rate'),
            ('stress_metadata.json','frames',19,'frames'),
            ('stress_metadata.json','cpu_barrier_seconds',999,'barrier'),
            ('stress_metadata.json','bending_stress_launches',0,'bending_stress_launches')]):
            with self.subTest(key=key):
                dest=self.work/f'json{i}';run=copy.deepcopy(self.runs[0]);shutil.copytree(run['output'],dest);run['output']=str(dest)
                mutate_json(dest/file,key,value)
                with self.assertRaisesRegex(a.Invalid,reason):a.validate_run(run)
        run,out=self.clone();(out/'final.csv').unlink()
        with self.assertRaises(FileNotFoundError):a.validate_run(run)

    def test_parameters_tensor_trace_and_parts(self):
        run,out=self.clone(1)
        mutate_csv(out/'stress_tensors.csv',lambda d:d[1].update(w00=str(float(d[1]['w00'])+.1)))
        with self.assertRaisesRegex(a.Invalid,'bending trace'):a.validate_run(run)
        shutil.rmtree(out);run,out=self.clone(1)
        # Opposite errors cancel in total but cannot pass separate term checks.
        def opposite(d):
            d[0]['w00']=str(float(d[0]['w00'])+1)
            d[1]['w00']=str(float(d[1]['w00'])-1)
            d[1]['w11']=str(float(d[1]['w11'])+1)
            d[0]['w11']=str(float(d[0]['w11'])-1)
        mutate_csv(out/'stress_tensors.csv',opposite)
        with self.assertRaisesRegex(a.Invalid,'CPU stretch'):a.validate_run(run)
        shutil.rmtree(out);run,out=self.clone(1)
        p=out/'parameters.txt';text=p.read_text().split();text[2]='20';p.write_text(' '.join(text))
        with self.assertRaisesRegex(a.Invalid,'parameter/indexing'):a.validate_run(run)

    def test_exact_gaussian_reference_against_explicit_mode_covariances(self):
        m=dict(springs=3,sample=3,kbt=1.7,effective_mobility_step=float(np.float32(.0123)),effective_noise=float(np.float32(.173)))
        lam=12*np.sin(np.arange(1,4)*np.pi/8)**2;decay=1-m['effective_mobility_step']*lam
        frames=17;variance=[m['kbt']/lam]
        for step in range(frames*m['sample']):variance.append(decay**2*variance[-1]+m['effective_noise']**2)
        for block,lag in ((1,0),(1,3),(2,4),(4,8)):
            expected=0;origins=frames//block-lag//block
            for origin in range(origins):
                for i in range(block):
                    for j in range(block):
                        earlier=(origin*block+i)*m['sample'];later=(origin*block+lag+j)*m['sample']
                        covariance=decay**abs(later-earlier)*variance[min(earlier,later)]
                        expected+=np.sum(lam**2*covariance**2)/(origins*block**2)
            self.assertAlmostEqual(a.gaussian_reference(m,lag,block,frames),expected,delta=2e-12)
        wrong=copy.deepcopy(m);wrong['effective_noise']*=1.01
        self.assertGreater(abs(a.gaussian_reference(wrong,3,1,frames)-a.gaussian_reference(m,3,1,frames)),.01)

    def test_statistical_pass_fail_unresolved_and_terminal_support(self):
        rng=np.random.default_rng(433311);x=rng.normal(size=(128,6));stat=a.channel_statistics(x)
        jackknife=np.array([np.cov(np.delete(x,i,axis=0),rowvar=False) for i in range(len(x))])
        independent_se=np.sqrt((len(x)-1)/len(x)*np.sum((jackknife-jackknife.mean(0))**2,axis=0))
        np.testing.assert_allclose(stat['covariance']['se'],independent_se,rtol=1e-12,atol=1e-12)
        checks=a.equilibrium_checks(stat,dict(statistics=stat))
        self.assertTrue(all(g['status']=='passed' for g in checks))
        bad=copy.deepcopy(stat);bad['products']['mean'][0][0]+=100
        self.assertTrue(any(g['status']=='failed' for g in a.equilibrium_checks(bad,dict(statistics=stat))))
        make=lambda mean,se:dict(mean=np.array(mean),se=np.array(se))
        checks=a.refinement('controlled',make(0,.01),make(0,.01),make(0,.01),1,make(0,0))
        self.assertEqual(checks[-1]['status'],'statistically_unresolved_bias')
        checks=a.refinement('bad refinement',make(1,.001),make(1,.001),make(1,.001),1,make(0,0))
        self.assertEqual(checks[-1]['status'],'failed')
        checks=a.refinement('good refinement',make(1,.001),make(.1,.001),make(.1,.001),1,make(0,0))
        self.assertTrue(all(c['status']=='passed' for c in checks))
        trace=[dict(lag_time=float(t),H=math.exp(-t),H_se=1e-5,pairs_per_chain=100,block_samples=1) for t in np.arange(0,10,.25)]
        self.assertEqual(a.terminal(trace,.25)['status'],'passed')
        self.assertEqual(a.terminal(trace[:10],.25)['status'],'insufficient_support')
        bad=copy.deepcopy(trace)
        for row in bad:row['pairs_per_chain']=1
        self.assertEqual(a.terminal(bad,.25)['status'],'insufficient_support')
        bad=copy.deepcopy(trace)
        for row in bad:
            if row['lag_time']>4:row['H']=.5
        self.assertEqual(a.terminal(bad,.25)['status'],'failed')

    def test_complete_replica_timestep_and_memory_comparison_matrices(self):
        manifest=[];ids=[];results={};base=a.validate_run(self.runs[0])
        for seed in (433201,433202,433203):
            for dt in (.0001,.00005,.000025):
                run=copy.deepcopy(self.runs[0]);run.update(phase='stream',seed=seed)
                run['command'][run['command'].index('--seed')+1]=str(seed)
                run['command'][run['command'].index('--dt')+1]=str(dt)
                rid=f'{seed}/{dt}';result=copy.deepcopy(base);result.pop('initial_channels',None)
                result['time_statistics']=dict(mean=dict(count=32,mean=[0.]*6,se=[.01]*6),products=dict(count=32,mean=np.eye(6).tolist(),se=(np.ones((6,6))*.01).tolist()))
                result['correlations']=[dict(lag_samples=0,H=1.,H_se=.01,**{k:1. for k in a.COLS},**{k+'_se':.01 for k in a.COLS}),dict(lag_samples=1,H=.9,H_se=.01,**{k:.9 for k in a.COLS},**{k+'_se':.01 for k in a.COLS})]
                manifest.append(run);ids.append(rid);results[rid]=result
        checks=a.campaign_comparisons(manifest,ids,results,{})
        self.assertTrue(all(g['status'] in ('passed','statistically_unresolved_bias') for g in checks))
        results[ids[-1]]['time_statistics']['mean']['mean'][0]=100
        self.assertTrue(any(g['status']=='failed' for g in a.campaign_comparisons(manifest,ids,results,{})))
        manifest=[];ids=[];results={}
        for repeat in range(3):
            for steps in (20000,400000):
                rid=f'r{repeat}s{steps}';run=dict(phase='memory',label='memory',precision='single',output=str(self.work/f'single-memory-r{repeat}-s{steps}'),command=self.runs[0]['command'])
                result=copy.deepcopy(base);result.pop('initial_channels',None);result['metadata']['steps']=steps
                result['memory']=dict(peak_rss_kib=108000,whole_device_gpu_mib=[145,145])
                manifest.append(run);ids.append(rid);results[rid]=result
        checks=a.campaign_comparisons(manifest,ids,results,{})
        self.assertTrue(all(g['status']=='passed' for g in checks))
        results[ids[-1]]['memory']['peak_rss_kib']=300000
        self.assertTrue(any(g['status']=='failed' for g in a.campaign_comparisons(manifest,ids,results,{})))

    def test_checkpoint_resume_identity_and_atomic_corruption(self):
        run,out=self.clone();root=self.work/'analysis';root.mkdir()
        with patch.object(a,'validate_run',wraps=a.validate_run) as parse:
            first=manager.analyze(root,[run],['fixture'],'manifest')
            self.assertEqual(parse.call_count,1);self.assertNotEqual(first['overall_status'],'passed')
            second=manager.analyze(root,[run],['fixture'],'manifest')
            self.assertEqual(parse.call_count,1);self.assertEqual(second['reused_runs'],1)
            self.assertFalse(any(root.glob('.analysis-checkpoint*')))
            mutate_json(out/'metadata.json','dt',.03)
            third=manager.analyze(root,[run],['fixture'],'manifest',verify=True)
            self.assertEqual(parse.call_count,2);self.assertEqual(third['overall_status'],'failed')
        p=root/'analysis-checkpoint.json';data=json.loads(p.read_text());data['sha256']='0'*64;p.write_text(json.dumps(data))
        with self.assertRaisesRegex(a.Invalid,'corrupted checkpoint'):manager.analyze(root,[run],['fixture'],'manifest')

    def test_running_outputs_not_scanned_and_provenance_is_separate(self):
        run,out=self.clone();root=self.work/'analysis';root.mkdir()
        manager.envelope(Path(str(out)+'.execution.json'),dict(status='running'))
        with patch.object(a,'validate_run') as parse,patch.object(manager,'fingerprints') as fingerprint:
            report=manager.analyze(root,[run],['fixture'],'manifest')
            parse.assert_not_called();fingerprint.assert_not_called()
            self.assertEqual(report['overall_status'],'incomplete')
        # Missing original evidence is not a fabricated executable identity.
        self.assertEqual(manager.provenance_checks(root,run,'fixture','manifest')[0]['status'],'missing_provenance')
        manager.envelope(Path(str(out)+'.execution.json'),dict(status='failed',exit_code=1))
        with patch.object(a,'validate_run') as parse:
            failed=manager.analyze(root,[run],['fixture'],'manifest');parse.assert_not_called()
        self.assertEqual(failed['overall_status'],'failed')
        self.assertIn('failure_evidence',failed['runs']['fixture'])

    def test_completion_skip_partial_refusal_and_execution_failure(self):
        run,out=self.clone();rid='fixture';ledger=dict(executables={run['precision']:dict(sha256=a.digest(run['command'][0]))})
        with self.assertRaisesRegex(a.Invalid,'partial output'):manager.execute_one(self.work,run,rid,'manifest',ledger)
        record=dict(status='completed',exit_code=0,command=run['command'],run_id=rid,manifest_hash='manifest',
                    executable_sha256=ledger['executables'][run['precision']]['sha256'],completion_files=manager.fingerprints(run))
        receipt=Path(str(out)+'.execution.json');manager.envelope(receipt,record)
        with patch.object(subprocess,'Popen') as launch:
            manager.execute_one(self.work,run,rid,'manifest',ledger);launch.assert_not_called()
        (out/'final.csv').write_text('corrupted')
        with self.assertRaisesRegex(a.Invalid,'identities changed'):manager.execute_one(self.work,run,rid,'manifest',ledger)
        fresh=copy.deepcopy(run);fresh['output']=str(self.work/'failed');fresh['command'][fresh['command'].index('--output')+1]=fresh['output']
        fake=unittest.mock.Mock();fake.poll.return_value=1;fake.returncode=1
        with patch.object(subprocess,'Popen',return_value=fake) as launch:
            with self.assertRaisesRegex(a.Invalid,'execution failed'):manager.execute_one(self.work,fresh,rid,'manifest',ledger)
            self.assertEqual(launch.call_args.args[0][4:],fresh['command'])
        self.assertEqual(manager.unenvelope(Path(fresh['output']+'.execution.json'))['status'],'failed')

    def test_runner_monitoring_and_post_pilot_estimates_with_mock_execution(self):
        fresh=copy.deepcopy(self.runs[0]);out=self.work/'successful';fresh['output']=str(out);fresh['phase']='stream'
        fresh['command'][fresh['command'].index('--output')+1]=str(out)
        ledger=dict(executables={fresh['precision']:dict(sha256=a.digest(fresh['command'][0]))})
        fake=unittest.mock.Mock();fake.poll.side_effect=[None,0];fake.returncode=0;fake.pid=os.getpid()
        def launch(*args,**kwargs):
            shutil.copytree(self.runs[0]['output'],out);return fake
        with patch.object(subprocess,'Popen',side_effect=launch),patch.object(manager,'command_output',return_value=dict(exit_code=0,stdout='2026-10-17 00:00:00, 145 MiB\n')),patch.object(manager.time,'sleep'):
            manager.execute_one(self.work,fresh,'fixture','manifest',ledger)
        self.assertEqual(manager.unenvelope(Path(str(out)+'.execution.json'))['status'],'completed')
        self.assertTrue(Path(str(out)+'.disk.csv').exists())
        def choose(manifest,ids,diagnostic=False):
            return (self.runs[1],'diagnostic-fixture') if diagnostic else (fresh,'fixture')
        with patch.object(manager,'pilot',side_effect=choose),patch.object(manager,'provenance_checks',return_value=[]):
            with contextlib.redirect_stdout(io.StringIO()):manager.pilot_report(self.work,[fresh],['fixture'])
        report=a.load(self.work/'pilot-readiness.json')
        self.assertEqual(report['scalar_observation_rows'],640)
        self.assertEqual(len(report['estimated_same_system_production']),1)
        self.assertGreater(report['estimated_campaign_scalar_bytes'],0)
        orphan=copy.deepcopy(fresh);orphan['output']=str(self.work/'orphan')
        Path(orphan['output']+'.time').write_text('original evidence')
        with self.assertRaisesRegex(a.Invalid,'orphan'):manager.execute_one(self.work,orphan,'orphan','manifest',ledger)
        self.assertEqual(Path(orphan['output']+'.time').read_text(),'original evidence')

    def test_provenance_validation_does_not_invent_compiler_identity(self):
        run,out=self.clone();root=self.work;rid='fixture';mhash='manifest'
        binaries={run['precision']:dict(path=run['command'][0],sha256=a.digest(run['command'][0]))}
        manager.envelope(root/'campaign-provenance.json',dict(manifest_hash=mhash,plan_hash=a.PLAN_HASH,
            executables=binaries,repository_sha='b47d2876d2380b9f4caace05f6fe193a6f49e3cb',accepted_sources=a.ACCEPTED_SOURCE_HASHES))
        receipt=Path(str(out)+'.execution.json')
        record=dict(run_id=rid,manifest_hash=mhash,command=run['command'],status='completed',exit_code=0,
                    executable_sha256=binaries[run['precision']]['sha256'],started_utc='2026-10-17T00:00:00+00:00',
                    finished_utc='2026-10-17T00:00:01+00:00',wall_seconds=1.,completion_files=manager.fingerprints(run))
        manager.envelope(receipt,record)
        checks=manager.provenance_checks(root,run,rid,mhash)
        self.assertEqual(checks[0]['status'],'missing_provenance')
        self.assertEqual(checks[-1]['status'],'passed')
        bad=copy.deepcopy(record);bad['command'][bad['command'].index('--dt')+1]='.02'
        manager.envelope(receipt,bad)
        with self.assertRaisesRegex(a.Invalid,'command/run identity'):manager.provenance_checks(root,run,rid,mhash)

    def test_memory_evidence_missing_stable_and_growth(self):
        run=dict(output=str(self.work/'memory'))
        missing=a.memory_observation(run,{})
        self.assertTrue(any(g['status']=='insufficient_support' for g in missing['checks']))
        Path(run['output']+'.time').write_text('Maximum resident set size (kbytes): 108000\n')
        Path(run['output']+'.gpu.csv').write_text('timestamp, memory.used [MiB],production_observed\nnow, 145 MiB,1\nlater, 145 MiB,1\nlast, 145 MiB,1\n')
        monitor=Path(run['output']+'.monitor.csv')
        monitor.write_text('elapsed_seconds,cpu_rss_kib,production_observed\n0,100000,0\n1,108000,1\n2,108100,1\n3,108000,1\n')
        self.assertTrue(all(g['status']=='passed' for g in a.memory_observation(run,{})['checks']))
        monitor.write_text('elapsed_seconds,cpu_rss_kib,production_observed\n1,108000,1\n2,200000,1\n3,300000,1\n')
        self.assertTrue(any(g['status']=='failed' for g in a.memory_observation(run,{})['checks']))
        model=a.Chain.homogeneous(1);ref=a.equilibrium_reference(model,1,count=64)
        manager.envelope(self.work/'equilibrium-references.json',dict(analysis_version=manager.version(),plan_hash=a.PLAN_HASH,references={ref['key']:ref}))
        with self.assertRaisesRegex(a.Invalid,'count mismatch'):manager.reference_catalog(self.work)


if __name__=='__main__':
    if len(BINARIES)!=2:raise SystemExit('supply single and double binaries; no campaign run is authorized')
    unittest.main(verbosity=2)
