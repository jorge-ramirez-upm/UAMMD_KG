"""Two five-step N3/M4 technical processes only; never a Phase A cell."""
import copy
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d13_phase_a as spec
import e1_d13_phase_a_auth as auth
import e1_d13_phase_a_runner as runner
import e1_d13_phase_a_analysis as analysis
BINARY=Path(sys.argv.pop(1)).resolve()


class TechnicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='d13-five-step-');cls.root=Path(cls.tmp.name)
        (cls.root/'config').mkdir();(cls.root/'runs').mkdir();(cls.root/'provenance').mkdir()
        cls.binary=cls.root/'provenance/semiflexible';shutil.copyfile(BINARY,cls.binary);cls.binary.chmod(0o500)
        cls.steps=[0,1,2,5];cls.snaps=[0,1,5]
        (cls.root/'config/full.steps').write_text('0 1 2 5\n');(cls.root/'config/snaps.steps').write_text('0 1 5\n')
        cls.specification={'id':'technical','cell':1,'replica':1,'N':3,'M':4,'Z':4,'kappa':10,'nu_hop':20000,
            'dt':'0.0001','steps':5,'sample':2,'seed':72103,'schedule':'full.steps','snapshots':'snaps.steps'}
        cls.items={}
        # Test-only safety caps, not proposed/approved Phase A budgets.
        cls.limits={'per_run_seconds':30,'aggregate_seconds':60,'per_run_output_bytes':16*1024**2,
            'aggregate_output_bytes':64*1024**2,'min_free_disk_bytes':1,'min_free_gpu_bytes':1,
            'min_available_host_bytes':1,'max_host_rss_bytes':4*1024**3}
        for profile in ('off','sparse'):
            run=dict(cls.specification,id='technical-'+profile,profile=profile)
            directory=cls.root/'runs'/run['id'];directory.mkdir()
            argv=spec.command(run,cls.binary,directory/'output',cls.root/'config')
            result=runner.shared.run_process(argv,directory,runner.shared.environment('/usr/local/cuda',spec.GPU_UUID),cls.limits,cls.root,time.monotonic())
            if result['status']!='exited':raise AssertionError((result,(directory/'stderr.log').read_text()))
            gpu=spec.load(directory/'output/metadata.json')['gpu']
            data=auth.validate_output(directory/'output',run,cls.steps,cls.snaps,gpu)
            receipt=dict(result,status='completed',run=run,command=argv,manifest_sha256='1'*64,
                build_receipt_sha256='2'*64,environment_sha256='3'*64,
                resources_before={'free_gpu_bytes':1,'free_disk_bytes':100*1024**2,'available_host_bytes':4*1024**3},
                output_files=data['files'],event_totals=data['event_totals'],
                logs={name:spec.file_record(directory/name) for name in ('stdout.log','stderr.log','process.json')})
            spec.atomic(directory/'execution.json',receipt)
            cls.items[profile]={'root':directory/'output','run':run,'receipt':receipt,'data':data}
        cls.gpu=gpu
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def clone(self,profile):
        item=self.items[profile];root=self.root/(self._testMethodName+'-'+profile)
        shutil.copytree(item['root'],root);return root
    def verify(self,root,profile,run=None):
        return auth.validate_output(root,run or self.items[profile]['run'],self.steps,self.snaps,self.gpu)
    def refresh(self,root):
        p=root/'equilibrium_complete.json';complete=spec.load(p)
        complete['files']={name:(root/name).stat().st_size for name in complete['files']}
        p.write_bytes(spec.encoded(complete))

    def test_valid_off_on_reconstruction_and_receipts(self):
        self.assertTrue(auth.compare_pair(self.items['off']['root'],self.items['sparse']['root'])['byte_identical'])
        for profile,item in self.items.items():
            data=self.verify(item['root'],profile)
            self.assertEqual(data['row_counts'],spec.row_counts(item['run'],self.steps,self.snaps))
            manifest={'schedules':{'full.steps':{'steps':self.steps},'snaps.steps':{'steps':self.snaps}}}
            ledger={'output_root':str(self.root),'manifest_sha256':'1'*64,'environment':{'gpu':{'name':self.gpu}}}
            approval={'output_root':str(self.root),'build_receipt_sha256':'2'*64,'environment_sha256':'3'*64,'limits':self.limits}
            authenticated=auth.base.authenticate_run(item['root'].parent,item['run'],manifest,ledger,approval,spec.digest(item['root'].parent/'execution.json'))
            self.assertEqual(authenticated['data']['files'],data['files'])
        self.assertFalse(any(p.name.startswith('equilibrium_') for p in self.items['off']['root'].iterdir()))
        with (self.items['sparse']['root']/'equilibrium_events.csv').open() as f:lines=f.read().splitlines()
        self.assertTrue(lines[-1].startswith('5,')) # final off regular cadence

    def test_missing_corrupt_optional_and_completion(self):
        for profile in ('off','sparse'):
            root=self.clone(profile);p=root/'final.csv';p.write_bytes(p.read_bytes().rsplit(b'\n',2)[0]+b'\n')
            with self.assertRaises((ValueError,AssertionError)):self.verify(root,profile)
        root=self.root/'missing-marker';shutil.copytree(self.items['sparse']['root'],root)
        (root/'equilibrium_complete.json').unlink()
        with self.assertRaises((OSError,ValueError)):self.verify(root,'sparse')
        root=self.root/'unexpected-marker';shutil.copytree(self.items['off']['root'],root)
        (root/'equilibrium_complete.json').write_text('{}')
        with self.assertRaises(ValueError):self.verify(root,'off')

    def test_inconsistent_counters_parameters_and_gpu(self):
        for profile in ('off','sparse'):
            root=self.clone(profile);p=root/'hopping_metadata.json';hop=spec.load(p);hop['attempts']+=1;p.write_bytes(spec.encoded(hop))
            if profile=='sparse':self.refresh(root)
            with self.assertRaises(ValueError):self.verify(root,profile)
            item=self.items[profile]
            with self.assertRaises(ValueError):self.verify(item['root'],profile,dict(item['run'],seed=item['run']['seed']+1))
            with self.assertRaises(ValueError):auth.validate_output(item['root'],item['run'],self.steps,self.snaps,'wrong GPU')

    def test_valid_numeric_corruption_rejected_by_receipt(self):
        item=self.items['off'];directory=self.root/'checksum-clone';shutil.copytree(item['root'].parent,directory)
        p=directory/'output/final.csv';p.write_bytes(p.read_bytes()[:-10]+b'\n')
        manifest={'schedules':{'full.steps':{'steps':self.steps},'snaps.steps':{'steps':self.snaps}}}
        ledger={'output_root':str(self.root),'manifest_sha256':'1'*64,'environment':{'gpu':{'name':self.gpu}}}
        approval={'output_root':str(self.root),'build_receipt_sha256':'2'*64,'environment_sha256':'3'*64,'limits':self.limits}
        with self.assertRaises(ValueError):auth.base.authenticate_run(directory,item['run'],manifest,ledger,approval,spec.digest(directory/'execution.json'))

    def test_pair_byte_identity_and_timing_exclusions(self):
        off=self.items['off']['root'];root=self.clone('sparse')
        p=root/'metadata.json';data=p.read_bytes();p.write_bytes(re.sub(rb'("production_wall_seconds":)[^,}]*',rb'\g<1>42',data))
        self.assertTrue(auth.compare_pair(off,root)['byte_identical'])
        p.write_bytes(re.sub(rb'("minimum_sampled_bond":)[^,}]*',rb'\g<1>42',data))
        with self.assertRaises(ValueError):auth.compare_pair(off,root)
        p.write_bytes(data);f=root/'final.csv';f.write_bytes(f.read_bytes()+b'\n')
        with self.assertRaises(ValueError):auth.compare_pair(off,root)

    def test_performance_reader_and_overlapping_timers(self):
        environment={'gpu':{'name':self.gpu,'uuid':spec.GPU_UUID}}
        for profile,item in self.items.items():
            metrics=analysis.process_metrics(item,environment,{'file':spec.file_record(self.binary)})
            meta=item['data']['metadata'];hop=spec.load(item['root']/'hopping_metadata.json')
            self.assertEqual(metrics['raw_output_bytes'],sum(p.stat().st_size for p in item['root'].iterdir()))
            self.assertEqual(metrics['raw_output_bytes'],sum(metrics['raw_output_bytes_by_category'].values()))
            self.assertEqual(metrics['production_wall_seconds_per_bd_step'],meta['production_wall_seconds']/5)
            self.assertEqual(metrics['attempts_per_production_wall_second'],hop['attempts']/meta['production_wall_seconds'])
            self.assertEqual(metrics['production_wall_seconds'],meta['production_wall_seconds'])
            self.assertIsNone(metrics['peak_gpu_bytes'])
            self.assertEqual(metrics['observer_transferred_bytes'] is None,profile=='off')
            self.assertGreater(metrics['peak_host_rss_bytes'],0)
            self.assertNotIn('summed_internal_seconds',metrics)
        item=copy.deepcopy(self.items['off']);item['receipt']['wall_seconds']=0
        with self.assertRaises(ValueError):analysis.process_metrics(item,environment,{})


if __name__=='__main__':unittest.main()
