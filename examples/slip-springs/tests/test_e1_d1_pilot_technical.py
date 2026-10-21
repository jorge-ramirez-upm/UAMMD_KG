"""Five-step technical fixtures only; never the 64-chain pilot or its execution flag."""
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d1_pilot as spec
import e1_d1_pilot_auth as auth
import e1_d1_pilot_analysis as science
BINARY=Path(sys.argv.pop(1)).resolve()


class AuthenticationTechnicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='e1-d11-five-step-')
        cls.root=Path(cls.temp.name);(cls.root/'config').mkdir();(cls.root/'runs').mkdir();(cls.root/'provenance').mkdir()
        cls.binary=cls.root/'provenance/semiflexible';shutil.copyfile(BINARY,cls.binary);cls.binary.chmod(0o500)
        cls.steps=[0,1,2,5];cls.snapshots=[0,1,5]
        (cls.root/'config/technical.steps').write_bytes(spec.schedule_text(cls.steps))
        (cls.root/'config/technical.snapshots').write_bytes(spec.schedule_text(cls.snapshots))
        cls.run_spec={'id':'technical-only','cell':1,'replica':1,'N':3,'M':4,'Z':4,'kappa':10,'nu_hop':20000,
                 'dt':'0.0001','steps':5,'sample':2,'seed':72103,
                 'schedule':'technical.steps','snapshots':'technical.snapshots'}
        cls.directory=cls.root/'runs/technical-only';cls.directory.mkdir()
        output=cls.directory/'output'
        cls.argv=spec.command(cls.run_spec,cls.binary,output,cls.root/'config')
        result=subprocess.run(cls.argv,capture_output=True,text=True,timeout=30)
        if result.returncode:raise AssertionError(result.stderr)
        (cls.directory/'stdout.log').write_text(result.stdout);(cls.directory/'stderr.log').write_text(result.stderr)
        cls.gpu=spec.load(output/'metadata.json')['gpu']
        cls.proof=auth.validate_output(output,cls.run_spec,cls.steps,cls.snapshots,cls.gpu)
        cls.manifest={'schedules':{'technical.steps':{'steps':cls.steps},'technical.snapshots':{'steps':cls.snapshots}}}
        cls.ledger={'output_root':str(cls.root),'manifest_sha256':'1'*64,'environment':{'gpu':{'name':cls.gpu}}}
        cls.approval={'output_root':str(cls.root),'build_receipt_sha256':'2'*64,'environment_sha256':'3'*64,
                      'limits':{'per_run_seconds':30,'max_host_rss_bytes':1024**3,'per_run_output_bytes':16*1024**2,
                                'min_free_disk_bytes':1,'min_available_host_bytes':1,'min_free_gpu_bytes':1}}
        # Synthetic receipt only exercises the reader. It is not an execution
        # approval/build receipt and cannot pass the full pilot campaign gate.
        process={'status':'exited','exit_code':0,'wall_seconds':1.,'max_rss_bytes':1}
        spec.atomic(cls.directory/'process.json',process)
        receipt=dict(process,version=1,status='completed',command=cls.argv,run=cls.run_spec,
            manifest_sha256='1'*64,build_receipt_sha256='2'*64,environment_sha256='3'*64,
            output_files=cls.proof['files'],event_totals=cls.proof['event_totals'],
            resources_before={'free_disk_bytes':100*1024**2,'available_host_bytes':1024**3,'free_gpu_bytes':1024**2},
            logs={name:spec.file_record(cls.directory/name) for name in ('stdout.log','stderr.log','process.json')})
        spec.atomic(cls.directory/'execution.json',receipt);cls.receipt_sha=spec.digest(cls.directory/'execution.json')
        cls.off=cls.root/'off'
        off=spec.command(cls.run_spec,cls.binary,cls.off,cls.root/'config');off=off[:off.index('--equilibrium-steps')]
        result=subprocess.run(off,capture_output=True,text=True,timeout=30)
        if result.returncode:raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def clone(self):
        target=self.root/self._testMethodName;shutil.copytree(self.directory,target);return target
    def verify(self,directory,run=None,steps=None,gpu=None):
        return auth.validate_output(directory/'output',run or self.run_spec,steps or self.steps,self.snapshots,gpu or self.gpu)
    def refresh_sizes(self,directory):
        path=directory/'output/equilibrium_complete.json';value=spec.load(path)
        value['files']={name:(directory/'output'/name).stat().st_size for name in value['files']}
        path.write_bytes(spec.encoded(value))

    def test_authentication_exact_schedule_and_reduction(self):
        item=auth.authenticate_run(self.directory,self.run_spec,self.manifest,self.ledger,self.approval,self.receipt_sha)
        self.assertEqual(item['data']['row_counts'],spec.row_counts(self.run_spec,self.steps,self.snapshots))
        reduced=science.reduce_replica(item['root'],self.run_spec,self.steps,self.snapshots)
        self.assertEqual(set(reduced['shared']),{0,1})
        self.assertEqual(reduced['event_totals']['batches'],5)
        # Shared interval at .0005 includes BOTH earlier diagnostic intervals.
        self.assertAlmostEqual(reduced['shared'][1]['rate_attempts'],self.proof['event_totals']['attempts']/.0005)
        self.assertEqual(len(reduced['diagnostic_only']),2) # this technical fixture also has nonshared step 2

    def test_no_change_to_legacy_outputs(self):
        on=self.directory/'output'
        for path in self.off.iterdir():
            if path.name=='metadata.json':
                a=spec.load(path);keys=[k for k in a if 'seconds' in k or 'ns_per_bead_step' in k or k=='bead_updates_per_second']
                pattern=r'("(?:'+'|'.join(keys)+r')":)[^,}]*'
                self.assertEqual(re.sub(pattern,r'\1TIMING',path.read_text()),re.sub(pattern,r'\1TIMING',(on/path.name).read_text()))
            else:self.assertEqual(path.read_bytes(),(on/path.name).read_bytes(),path.name)

    def test_bad_parameter_seed_gpu_schema_and_schedule(self):
        for key,value in (('seed',self.run_spec['seed']+1),('kappa',0),('steps',6)):
            wrong=dict(self.run_spec,**{key:value})
            with self.assertRaises((ValueError,KeyError)):self.verify(self.directory,wrong)
        with self.assertRaises(ValueError):self.verify(self.directory,gpu='wrong GPU')
        with self.assertRaises(ValueError):self.verify(self.directory,steps=[0,1,3,5])
        directory=self.clone();path=directory/'output/equilibrium_schema.json';data=spec.load(path);data['version']=2;path.write_bytes(spec.encoded(data));self.refresh_sizes(directory)
        with self.assertRaises(ValueError):self.verify(directory)

    def test_corruption_truncation_missing_completion_and_symlinks(self):
        for i,name in enumerate(('equilibrium_complete.json','equilibrium_connectors.csv','samples.csv')):
            directory=self.root/(self._testMethodName+str(i));shutil.copytree(self.directory,directory)
            path=directory/'output'/name
            if i==0:path.unlink()
            else:path.write_bytes(path.read_bytes()[:-10])
            with self.assertRaises((OSError,ValueError,AssertionError)):self.verify(directory)
        directory=self.clone();path=directory/'output/initial.csv';original=path.read_bytes();path.unlink();target=self.root/'external-state';target.write_bytes(original);path.symlink_to(target)
        with self.assertRaises(ValueError):self.verify(directory)

    def test_duplicate_json_inconsistent_counters_and_missing_rows(self):
        directory=self.clone();path=directory/'output/hopping_metadata.json'
        text=path.read_text();path.write_text(text[:-2]+',"version":2}\n');self.refresh_sizes(directory)
        with self.assertRaises(ValueError):self.verify(directory)
        path.write_text(text);data=spec.load(path);data['attempts']+=1;path.write_bytes(spec.encoded(data));self.refresh_sizes(directory)
        with self.assertRaises(ValueError):self.verify(directory)
        path.write_text(text)
        csvpath=directory/'output/equilibrium_sites.csv';csvpath.write_bytes(csvpath.read_bytes().rsplit(b'\n',2)[0]+b'\n');self.refresh_sizes(directory)
        with self.assertRaises(ValueError):self.verify(directory)

    def test_receipt_checksum_and_interrupted_run_refusals(self):
        directory=self.clone();path=directory/'execution.json';record=spec.load(path);record['status']='interrupted';spec.atomic(path,record)
        with self.assertRaises(ValueError):auth.authenticate_run(directory,self.run_spec,self.manifest,self.ledger,self.approval,self.receipt_sha)
        with self.assertRaises(ValueError):auth.authenticate_run(directory,self.run_spec,self.manifest,self.ledger,self.approval,spec.digest(path))
        record['status']='completed';record['output_files']['initial.csv']['sha256']='0'*64;spec.atomic(path,record)
        with self.assertRaises(ValueError):auth.authenticate_run(directory,self.run_spec,self.manifest,self.ledger,self.approval,spec.digest(path))


if __name__=='__main__':unittest.main()
