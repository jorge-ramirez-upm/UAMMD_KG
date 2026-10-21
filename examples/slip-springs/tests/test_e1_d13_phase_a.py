"""Synthetic/CPU checks only. Never launches a Phase A process."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d13_phase_a as spec
import e1_d13_phase_a_auth as auth
import e1_d13_phase_a_runner as runner
import e1_d13_phase_a_analysis as analysis
import e1_d1_pilot_runner as original_runner


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='d13-unit-');self.root=Path(self.tmp.name)
        self.config=self.root/'config';self.sha=spec.freeze(self.config)
        self.manifest=spec.validate_manifest(self.config/'manifest.json',self.sha)
    def tearDown(self):self.tmp.cleanup()

    def test_matrix_pairing_commands_and_reproduction(self):
        m=self.manifest;self.assertEqual(len(m['runs']),8);self.assertEqual(len(m['pairing']),4)
        self.assertEqual(len({r['seed'] for r in m['runs']}),4)
        self.assertEqual({(r['N'],r['kappa'],r['Ne'],r['nu_hop'],r['dt']) for r in m['runs']},
                         {(8,0,16,10,'0.0001'),(8,0,16,10,'0.00025'),(32,10,4,100,'0.0001'),(32,10,4,100,'0.00025')})
        self.assertEqual(spec.estimates(m)['replica_bd_steps'],14000)
        for pair in m['pairing']:
            runs=[r for r in m['runs'] if r['cell']==pair['cell']]
            self.assertEqual([r['profile'] for r in runs],['off','sparse'])
            self.assertEqual([r['seed'] for r in runs],[pair['seed']]*2)
        for r in m['runs']:
            s=spec.design.schedules('0.25',r['dt'])
            self.assertEqual(len(s['scalar_steps']),3);self.assertEqual(len(s['full_steps']),7)
            self.assertNotEqual(r['steps']%r['sample'],0)
            self.assertEqual(s['full_steps'][-1],r['steps']);self.assertEqual(len(s['snapshot_steps']),4)
            argv=spec.command(r,'binary','out','cfg')
            self.assertEqual('--equilibrium-steps' in argv,r['profile']=='sparse')
            self.assertEqual(argv,[x.replace('{binary}','binary').replace('{output}','out').replace('{config}','cfg') for x in m['argument_templates'][r['id']]])
        self.assertFalse(m['execution_authorized']);self.assertTrue(all(v is None for v in m['approved_limits'].values()))
        approval=spec.load(self.config/'approval.template.json');self.assertFalse(approval['execution_authorized'])
        self.assertTrue(all(v is None for v in approval['limits'].values()))
        other=self.root/'other';self.assertEqual(spec.freeze(other),self.sha)
        for p in self.config.iterdir():self.assertEqual(p.read_bytes(),(other/p.name).read_bytes())
        self.assertEqual(spec.digest(spec.CONFIG/'manifest.json'),self.sha)
        with self.assertRaises(FileExistsError):spec.freeze(self.config)

    def test_frozen_inputs_and_phase_b_or_extra_run_refusal(self):
        for alter in ('matrix','extra','phase','source','tools'):
            m=copy.deepcopy(self.manifest)
            if alter=='matrix':m['runs'][0]['N']=32
            elif alter=='extra':m['runs'].append(copy.deepcopy(m['runs'][0]))
            elif alter=='phase':m['campaign']='phase-B'
            elif alter=='source':m['accepted_source_sha']='0'*40
            else:m['preparation_sources']['e1_d13_phase_a.py']='0'*64
            p=self.config/'changed.json';p.write_bytes(spec.encoded(m))
            with self.assertRaises(ValueError):spec.validate_manifest(p,spec.digest(p))
        p=self.config/'dt0.0001.full.steps';p.write_text('0 1 2500\n')
        with self.assertRaises(ValueError):spec.validate_manifest(self.config/'manifest.json',self.sha)
        self.assertEqual(spec.old.digest(spec.old.CONFIG/'manifest.json'),'a14612088cab809f101c22c5c60c1879a136e9383305980864c014cae899dc2f')
        self.assertTrue(spec.design.check(spec.design.CONFIG,spec.DESIGN_SHA)['authenticated'])

    def test_readonly_authorization_and_limits(self):
        args=argparse.Namespace(manifest=self.config/'manifest.json',manifest_sha256=self.sha,build_receipt=None,
            build_sha256=None,approval=None,approval_sha256=None,gpu_uuid=None,output_root=self.root/'not-created',
            authorize_phase_a_execution=False)
        with patch.object(spec,'validate_manifest',return_value=self.manifest),patch.object(runner,'host_inventory',return_value={}),patch.object(subprocess,'Popen',side_effect=AssertionError('no launch')):
            summary,m,b,a,l=runner.preflight(args)
            self.assertTrue(summary['blockers']);self.assertFalse(summary['execution_authorized'])
            self.assertEqual(len(summary['commands']),8)
            with self.assertRaises(ValueError):runner.execute(args,summary,m,b,a,l)
        self.assertFalse(args.output_root.exists())
        approval=spec.load(self.config/'approval.template.json')
        with self.assertRaises(ValueError):runner.shared.validate_approval(approval,self.sha,'b'*64,self.root,'e'*64)
        with self.assertRaises(ValueError):spec.validate_limits(approval['limits'])
        limits={k:1 for k in approval['limits']};limits['per_run_seconds']=121
        with self.assertRaises(ValueError):spec.validate_limits(limits)
        # Private bindings leave the original frozen module's globals untouched.
        self.assertIs(original_runner.spec,spec.old)
        self.assertIsNot(runner.shared,original_runner)

    def build_record(self):
        root=self.root/'build';(root/'bin').mkdir(parents=True);cuda=self.root/'cuda';(cuda/'bin').mkdir(parents=True)
        files={'binary':root/'bin/semiflexible','log':root/'build.log','nvcc':cuda/'bin/nvcc',
               'cxx':self.root/'cxx','runtime_library':self.root/'runtime'}
        for p in files.values():p.write_text('NONEXECUTABLE SYNTHETIC READER PROOF ONLY')
        source={'path':'/synthetic/source','repository':spec.REPOSITORY_ID,'sha':spec.ACCEPTED_SHA,
                'origin':'git@github.com:jorge-ramirez-upm/UAMMD_KG.git'}
        value={'version':1,'status':'completed','exit_code':0,'compilation_observed':True,
            'manifest_sha256':self.sha,'source':source,'precision_bits':64,
            'preparation_sources':self.manifest['preparation_sources'],'architecture':'sm_86','build_root':str(root),
            'cuda_home':str(cuda),'dependencies':{str(files['cxx']):spec.file_record(files['cxx'])},
            'linker_libraries':{str(files['runtime_library']):spec.file_record(files['runtime_library'])}}
        for key,p in files.items():value[key]={'path':str(p),'file':spec.file_record(p),'version':'release 13.0 synthetic'}
        value['command']=auth.base.build_command(source['path'],root,cuda,files['cxx'],'sm_86')
        path=root/'build.json';path.write_bytes(spec.encoded(value));return path,value

    def test_wrong_build_source_executable_compiler_and_manifest(self):
        p,value=self.build_record()
        self.assertEqual(auth.validate_build(p,spec.digest(p),self.manifest),value)
        for key in ('source','manifest','architecture','precision'):
            bad=copy.deepcopy(value)
            if key=='source':bad['source']['sha']='0'*40
            elif key=='manifest':bad['manifest_sha256']='0'*64
            elif key=='architecture':bad['architecture']='sm_75'
            else:bad['precision_bits']=32
            p.write_bytes(spec.encoded(bad))
            with self.assertRaises(ValueError):auth.validate_build(p,spec.digest(p),self.manifest)
        p.write_bytes(spec.encoded(value))
        with patch.object(spec,'source_identity',return_value=value['source']):
            self.assertEqual(auth.validate_build(p,spec.digest(p),self.manifest,live=True),value)
            Path(value['binary']['path']).write_text('changed executable')
            with self.assertRaises(ValueError):auth.validate_build(p,spec.digest(p),self.manifest,live=True)
        with self.assertRaises(ValueError):spec.source_identity(spec.old.REPOSITORY)

    def test_wrong_gpu_environment_runtime(self):
        _,build=self.build_record()
        environment={'gpu':{'name':'NVIDIA GeForce RTX 3060 Ti','compute_capability':'8.6','uuid':spec.GPU_UUID},
            'runtime_version':13000,'driver_api_version':13000,'runtime_library':build['runtime_library']['file'],
            'environment':auth.expected_environment(build['cuda_home'],spec.GPU_UUID)}
        approval={'gpu_uuid':spec.GPU_UUID};auth.validate_environment(environment,build,approval)
        for field in ('uuid','name','compute_capability','runtime','environment','library'):
            bad=copy.deepcopy(environment)
            if field in bad['gpu']:bad['gpu'][field]='wrong'
            elif field=='runtime':bad['runtime_version']=12000
            elif field=='environment':bad['environment']['CUDA_VISIBLE_DEVICES']='0'
            else:bad['runtime_library']={'bytes':0,'sha256':'0'*64}
            with self.assertRaises(ValueError):auth.validate_environment(bad,build,approval)

    def test_timers_counters_and_size_aggregation(self):
        meta={k:1. for k in spec.TIMING_FIELDS};auth.timers(meta)
        meta['observation_seconds']=0;auth.timers(meta)
        for value in (0,-1,float('nan'),float('inf'),None,'1',True):
            bad=dict(meta,production_wall_seconds=value)
            with self.assertRaises(ValueError):auth.timers(bad)
        for key in ('observation_seconds','bead_updates_per_second'):
            bad=dict(meta,**{key:-1})
            with self.assertRaises(ValueError):auth.timers(bad)
        hop={k:0 for k in auth.COUNTERS};hop.update(batches=5,attempts=10,accepted=6,outward_proposals=2,
            occupied_rejected=1,metropolis_rejected=1,renewal_proposed=2,renewal_accepted=1,
            renewal_occupied_rejected=1,renewal_cross_chain=1)
        auth.counters(hop,{'steps':5})
        for key in ('attempts','renewal_accepted','renewal_cross_chain','batches'):
            with self.assertRaises(ValueError):auth.counters(dict(hop,**{key:hop[key]+1}),{'steps':5})
        files={name:{'bytes':i+1} for i,name in enumerate(auth.base.RAW_FILES)}
        groups=analysis.categories(files);self.assertEqual(sum(groups.values()),sum(p['bytes'] for p in files.values()))
        self.assertGreater(groups['audit_snapshots'],0)

    def cohort(self):
        # Synthetic reader test only: no executable, real build, approval or raw trajectory.
        root=self.root/'cohort';root.mkdir()
        for directory in ('config','runs','provenance'):(root/directory).mkdir()
        shutil.copyfile(self.config/'manifest.json',root/'manifest.json')
        for name in self.manifest['schedules']:shutil.copyfile(self.config/name,root/'config'/name)
        for name in ('semiflexible','build.log'):(root/'provenance'/name).write_text('NONEXECUTABLE SYNTHETIC PROOF')
        (root/'build.json').write_text('{}')
        for r in self.manifest['runs']:(root/'runs'/r['id']).mkdir()
        build={'source':{'repository':spec.REPOSITORY_ID,'sha':spec.ACCEPTED_SHA},
               'binary':{'file':spec.file_record(root/'provenance/semiflexible')},
               'log':{'file':spec.file_record(root/'provenance/build.log')},'cuda_home':'/synthetic/cuda','runtime_library':{'file':{'bytes':1,'sha256':'0'*64}}}
        environment={'gpu':{'uuid':spec.GPU_UUID,'name':'NVIDIA GeForce RTX 3060 Ti','compute_capability':'8.6'},
            'runtime_version':13000,'driver_api_version':13000,'runtime_library':build['runtime_library']['file'],'environment':auth.expected_environment(build['cuda_home'],spec.GPU_UUID)}
        approval=spec.load(self.config/'approval.template.json')
        approval.update(execution_authorized=True,approval_reference='SYNTHETIC READER MOCK ONLY',output_root=str(root),
            build_receipt_sha256=spec.digest(root/'build.json'),gpu_uuid=spec.GPU_UUID,environment_sha256=spec.identity(environment))
        approval['limits']={k:1 for k in approval['limits']};approval['limits'].update(per_run_output_bytes=1024**2,aggregate_output_bytes=1024**2)
        spec.atomic(root/'approval.json',approval)
        ledger={'version':1,'campaign':self.manifest['campaign'],'manifest_sha256':self.sha,'approval_sha256':spec.digest(root/'approval.json'),
            'environment':environment,'environment_sha256':approval['environment_sha256'],'output_root':str(root),
            'preparation_sources':self.manifest['preparation_sources'],'limits':approval['limits'],'started_utc':'2026-01-01T00:00:00+00:00',
            'source':build['source'],'build_receipt_sha256':approval['build_receipt_sha256']}
        spec.atomic(root/'campaign.json',ledger)
        status={'version':1,'status':'completed','completed_run_ids':[r['id'] for r in self.manifest['runs']],'wall_seconds':.5}
        spec.atomic(root/'status.json',status)
        final={'version':1,'status':'completed','campaign_sha256':spec.digest(root/'campaign.json'),'status_sha256':spec.digest(root/'status.json'),
               'run_ids':status['completed_run_ids'],'receipts':{r['id']:'0'*64 for r in self.manifest['runs']}}
        spec.atomic(root/'campaign_complete.json',final)
        return root,build

    def test_cohort_completion_identity_and_pair_gates(self):
        root,build=self.cohort()
        def item(directory,run,*args):
            return {'run':run,'root':directory/'output','receipt':{'started_utc':'2026-01-01T00:00:00+00:00',
                    'ended_utc':'2026-01-01T00:00:00+00:00','wall_seconds':.001,'max_rss_bytes':1}}
        def verify():return auth.authenticate_campaign(root,self.config/'manifest.json',self.sha,spec.digest(root/'approval.json'),spec.digest(root/'campaign_complete.json'))
        with patch.object(auth,'validate_build',return_value=build),patch.object(auth.base,'validate_build',return_value=build),patch.object(auth.base,'authenticate_run',side_effect=item),patch.object(auth,'compare_pair',return_value={'byte_identical':True}) as pairs:
            _,items=verify();self.assertEqual(len(items),8);self.assertEqual(pairs.call_count,4)
            with patch.object(auth,'compare_pair',side_effect=ValueError('physical mismatch')):
                with self.assertRaises(ValueError):verify()
            archived=root/'provenance/semiflexible';data=archived.read_bytes();archived.write_text('corrupt')
            with self.assertRaises(ValueError):verify()
            archived.write_bytes(data)
            ledger_path=root/'campaign.json';ledger_bytes=ledger_path.read_bytes()
            ledger=load(ledger_path);ledger['environment']['gpu']['name']='incorrect GPU';spec.atomic(ledger_path,ledger)
            final=load(root/'campaign_complete.json');final['campaign_sha256']=spec.digest(ledger_path);spec.atomic(root/'campaign_complete.json',final)
            with self.assertRaises(ValueError):verify()
            ledger_path.write_bytes(ledger_bytes);final['campaign_sha256']=spec.digest(ledger_path);spec.atomic(root/'campaign_complete.json',final)
            folder=root/'runs'/self.manifest['runs'][0]['id'];folder.rmdir()
            with self.assertRaises(ValueError):verify()
            folder.mkdir();status=load(root/'status.json');status['status']='interrupted';spec.atomic(root/'status.json',status)
            final=load(root/'campaign_complete.json');final['status_sha256']=spec.digest(root/'status.json');spec.atomic(root/'campaign_complete.json',final)
            with self.assertRaises(ValueError):verify()
            (root/'campaign_complete.json').unlink()
            with self.assertRaises(OSError):verify()

    def test_aggregation_is_descriptive_and_requires_all_eight(self):
        items=[{'run':r} for r in self.manifest['runs']]
        def metric(item,*args):
            r=item['run'];value=2 if r['profile']=='sparse' else 1
            return dict(id=r['id'],cell=r['cell'],profile=r['profile'],seed=r['seed'],
                initialization_seconds=value,integration_seconds=value,production_wall_seconds=value,
                process_wall_seconds=value,raw_output_bytes=10*value)
        with patch.object(analysis,'process_metrics',side_effect=metric):
            result=analysis.summarize(self.manifest,items,{'environment':{}},{'binary':{}})
            self.assertEqual(len(result['pairs']),4);self.assertEqual(result['raw_output_bytes'],120)
            self.assertIsNone(result['scientific_acceptance'])
            for pair in result['pairs']:
                self.assertEqual(pair['on_minus_off']['process_wall_seconds'],1)
                self.assertEqual(pair['on_minus_off']['raw_output_bytes'],10)
            with self.assertRaises(ValueError):analysis.summarize(self.manifest,items[:-1],{}, {})
            with self.assertRaises(ValueError):analysis.summarize(self.manifest,items[:7]+items[:1],{}, {})

    def test_mocked_execution_completion_gate_and_interrupt(self):
        # All child calls are mocked. The synthetic binary is nonexecutable.
        path,build=self.build_record()
        environment={'gpu':{'uuid':spec.GPU_UUID,'name':'NVIDIA GeForce RTX 3060 Ti','compute_capability':'8.6'},
            'runtime_version':13000,'driver_api_version':13000,'runtime_library':build['runtime_library']['file'],
            'environment':auth.expected_environment(build['cuda_home'],spec.GPU_UUID)}
        limits={k:1 for k in spec.design.BUDGETS};limits.update(per_run_seconds=30,aggregate_seconds=60,
            per_run_output_bytes=16*1024**2,aggregate_output_bytes=64*1024**2,max_host_rss_bytes=1000,min_available_host_bytes=1000)
        resources={'free_disk_bytes':128*1024**2,'available_host_bytes':1000,'free_gpu_bytes':1000}
        for mode in ('interrupt','bad-pair','success'):
            root=self.root/mode;approval_path=self.root/(mode+'-mock-approval.json')
            approval={'version':1,'execution_authorized':True,'approval_reference':'NONEXECUTABLE SYNTHETIC SUPERVISOR MOCK ONLY',
                'manifest_sha256':self.sha,'build_receipt_sha256':spec.digest(path),'environment_sha256':spec.identity(environment),
                'output_root':str(root),'gpu_uuid':spec.GPU_UUID,'limits':limits}
            spec.atomic(approval_path,approval)
            args=argparse.Namespace(authorize_phase_a_execution=True,manifest=self.config/'manifest.json',manifest_sha256=self.sha,
                output_root=root,approval=approval_path,approval_sha256=spec.digest(approval_path),build_receipt=path,build_sha256=spec.digest(path))
            summary={'blockers':[],'environment':environment,'environment_sha256':spec.identity(environment)}
            def child(argv,directory,*unused):
                for name in ('stdout.log','stderr.log'):(directory/name).write_text('synthetic child only')
                value={'status':'interrupted' if mode=='interrupt' else 'exited','exit_code':0,'wall_seconds':.001,'max_rss_bytes':100}
                spec.atomic(directory/'process.json',value)
                if mode=='interrupt':raise KeyboardInterrupt('synthetic interruption')
                return value
            with patch.object(auth,'validate_build',return_value=build),patch.object(runner,'machine',return_value=(environment,1000)),\
                 patch.object(runner.shared,'resource_check',return_value=resources),patch.object(runner.shared,'run_process',side_effect=child) as process,\
                 patch.object(auth,'validate_output',return_value={'files':{},'event_totals':{}}),\
                 patch.object(auth.base,'authenticate_run',return_value={}),\
                 patch.object(auth,'compare_pair',side_effect=ValueError('synthetic pair mismatch') if mode=='bad-pair' else None) as pairs:
                if mode=='success':
                    result=runner.execute(args,summary,self.manifest,build,approval,limits)
                    self.assertEqual(result['status'],'completed');self.assertEqual(process.call_count,8);self.assertEqual(pairs.call_count,4)
                    self.assertTrue((root/'campaign_complete.json').exists())
                else:
                    with self.assertRaises(KeyboardInterrupt if mode=='interrupt' else ValueError):
                        runner.execute(args,summary,self.manifest,build,approval,limits)
                    self.assertFalse((root/'campaign_complete.json').exists())
                    self.assertEqual(spec.load(root/'status.json')['status'],'interrupted' if mode=='interrupt' else 'failed')
                    self.assertEqual(process.call_count,1 if mode=='interrupt' else 8)
                    self.assertEqual(pairs.call_count,0 if mode=='interrupt' else 1)

    def test_analysis_publication_reauthenticates_and_refuses_overwrite(self):
        root,build=self.cohort();spec.atomic(root/'build.json',build)
        args=argparse.Namespace(campaign=root,output=self.root/'analysis.json',manifest=self.config/'manifest.json',
            manifest_sha256=self.sha,approval_sha256='a'*64,completion_sha256='c'*64)
        # Raw readers, metrics and cohort gates have separate independent tests.
        with patch.object(auth,'authenticate_campaign',return_value=(self.manifest,[])) as authenticate,\
             patch.object(analysis,'summarize',return_value={'raw_output_bytes':0,'scientific_acceptance':None}):
            self.assertEqual(analysis.analyze(args),args.output)
            self.assertEqual(authenticate.call_count,2)
            self.assertEqual(spec.load(args.output)['authentication']['completion_sha256'],'c'*64)
            with self.assertRaises(ValueError):analysis.analyze(args)
        args.output=root/'inside-raw.json'
        with self.assertRaises(ValueError):analysis.analyze(args)

    def test_incomplete_analysis_creates_nothing(self):
        args=argparse.Namespace(campaign=self.root/'missing',output=self.root/'analysis.json',
            manifest=self.config/'manifest.json',manifest_sha256=self.sha,approval_sha256='0'*64,completion_sha256='0'*64)
        with self.assertRaises((OSError,ValueError)):analysis.analyze(args)
        self.assertFalse(args.output.exists())


load=spec.load
if __name__=='__main__':unittest.main()
