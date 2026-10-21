"""Tiny nine-step fixtures only: N3/M4 flexible and N17/M2 stiff, never Phase B cells."""
import csv
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d14_phase_b as spec
import e1_d14_phase_b_auth as auth
import e1_d14_phase_b_runner as runner
import e1_d14_phase_b_analysis as analysis
BINARY=Path(sys.argv.pop(1)).resolve()


def rows(path):
    with path.open() as f:return list(csv.DictReader(f))


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='d14-nine-step-');cls.root=Path(cls.tmp.name)
        (cls.root/'config').mkdir();(cls.root/'runs').mkdir();(cls.root/'provenance').mkdir()
        cls.binary=cls.root/'provenance/semiflexible';shutil.copyfile(BINARY,cls.binary);cls.binary.chmod(0o500)
        cls.full=[0,1,5,9];cls.snaps=[0,5,9]
        (cls.root/'config/full.steps').write_text('0 1 5 9\n');(cls.root/'config/snaps.steps').write_text('0 5 9\n')
        # Technical safety caps only, not executable Phase B approval budgets.
        cls.limits={'per_run_seconds':30,'aggregate_seconds':60,'per_run_output_bytes':16*1024**2,
            'aggregate_output_bytes':64*1024**2,'min_free_disk_bytes':1,'min_free_gpu_bytes':1,
            'min_available_host_bytes':1,'max_host_rss_bytes':4*1024**3}
        cls.items=[]
        for n,chains,kappa in ((3,4,0),(17,2,10)):
            run={'id':f'technical-N{n}','cell':1,'replica':1,'N':n,'M':chains,'Z':4,'kappa':kappa,
                'nu_hop':20000,'dt':'0.0001','steps':9,'sample':2,'seed':72141,'profile':'sparse',
                'schedule':'full.steps','snapshots':'snaps.steps'}
            directory=cls.root/'runs'/run['id'];directory.mkdir()
            argv=spec.command(run,cls.binary,directory/'output',cls.root/'config')
            result=runner.shared.run_process(argv,directory,runner.shared.environment('/usr/local/cuda',spec.GPU_UUID),cls.limits,cls.root,time.monotonic())
            if result['status']!='exited':raise AssertionError((result,(directory/'stderr.log').read_text()))
            gpu=spec.load(directory/'output/metadata.json')['gpu']
            proof=auth.validate_output(directory/'output',run,cls.full,cls.snaps,gpu)
            receipt=dict(result,status='completed',run=run,command=argv,manifest_sha256='1'*64,
                build_receipt_sha256='2'*64,environment_sha256='3'*64,
                resources_before={'free_gpu_bytes':1,'free_disk_bytes':128*1024**2,'available_host_bytes':4*1024**3},
                output_files=proof['files'],event_totals=proof['event_totals'],
                logs={name:spec.file_record(directory/name) for name in ('stdout.log','stderr.log','process.json')})
            spec.atomic(directory/'execution.json',receipt)
            cls.items.append({'root':directory/'output','run':run,'data':proof,'receipt':receipt,
                'reduced':analysis.reduce_replica(directory/'output',run,cls.full)})
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_backbone_only_and_synchronized_joint_support(self):
        for item in self.items:
            result=item['reduced'];series=result['series']
            self.assertEqual(len(result['regular_scalar_times']),5)
            self.assertEqual(len(result['full_e1_times']),4)
            self.assertNotIn('A_joint',series['1/5000']['metrics'])
            self.assertNotIn('connector_e2',series['1/5000']['metrics'])
            self.assertIn('A_joint',series['1/2000']['metrics'])
            self.assertEqual(series['9/10000']['step'],9)
            self.assertEqual(result['regular_event_rates'],{}) # no fictitious .5-time support
            self.assertTrue(series['1/10000']['diagnostic_only'])
            if item['run']['N']==17:
                self.assertIn('tangent16',series['1/2000']['metrics'])
                self.assertNotIn('tangent16',series['1/5000']['metrics'])

    def test_independent_snapshot_reconstruction(self):
        for item in self.items:
            root=item['root'];run=item['run'];m=run['N']+1;chains=run['M'];z=run['Z']
            positions=rows(root/'equilibrium_positions.csv');attachments=rows(root/'equilibrium_attachments.csv')
            ref=analysis.reference(run['N'],chains,z,run['kappa'],run['nu_hop'])
            for step in self.snaps:
                r=np.array([[float(row[k]) for k in ('x','y','z')] for row in positions if int(row['step'])==step]).reshape(chains,m,3)
                q=np.diff(r,axis=1);length=np.linalg.norm(q,axis=2)
                re2=np.sum((r[:,-1]-r[:,0])**2,axis=1);rg2=np.mean(np.sum((r-r.mean(axis=1)[:,None])**2,axis=2),axis=1)
                values=item['reduced']['series'][analysis.time_key(step,run['dt'])]['metrics']
                np.testing.assert_allclose([values['re2'],values['rg2'],values['mean_r'],values['mean_r2']],
                    [re2.mean(),rg2.mean(),length.mean(),np.mean(length**2)],rtol=3e-12,atol=3e-12)
                for sep in (1,2,3,4,8,16):
                    if sep<run['N']:
                        tangent=np.mean(np.sum(q[:,:-sep]*q[:,sep:],axis=2)/(length[:,:-sep]*length[:,sep:]))
                        self.assertAlmostEqual(values['tangent'+str(sep)],tangent,places=12)
                spring=[a for a in attachments if int(a['step'])==step]
                e=np.array([r[int(a['chain']),int(a['bead'])]-np.array([float(a[k]) for k in ('ax','ay','az')]) for a in spring])
                e2=np.sum(e*e,axis=1);population=np.bincount([int(a['chain']) for a in spring],minlength=chains)
                squares=np.bincount([int(a['chain']) for a in spring],weights=e2,minlength=chains)
                f=re2/ref['targets']['re2']-1
                self.assertAlmostEqual(values['connector_e2'],e2.mean(),places=12)
                self.assertAlmostEqual(values['A_joint'],np.sum(f*(population-z/chains))/(chains*ref['sigma_Z']),places=12)
                self.assertAlmostEqual(values['B_joint'],np.sum(f*(squares-5*population))/(z*5),places=12)
                self.assertEqual(population.sum(),z)
                self.assertEqual(len({(a['chain'],a['bead']) for a in spring}),z)

    def test_event_rebinning_receipts_and_initial_measurement(self):
        for item in self.items:
            result=item['reduced'];run=item['run'];root=item['root']
            self.assertEqual(result['event_totals'],item['data']['event_totals'])
            raw=rows(root/'equilibrium_events.csv')
            first=sum(int(row['attempts']) for row in raw if int(row['step']) in (1,5))
            self.assertEqual(result['event_intervals']['1/2000']['counts']['attempts'],first)
            self.assertEqual(result['event_intervals']['1/2000']['metrics']['rate_attempts'],first/.0005)
            initial=rows(root/'initial.csv');r=np.array([[float(a[k]) for k in ('x','y','z')] for a in initial]).reshape(run['M'],run['N']+1,3)
            self.assertAlmostEqual(result['series']['0']['metrics']['re2'],np.mean(np.sum((r[:,-1]-r[:,0])**2,axis=1)),places=12)
            manifest={'schedules':{'full.steps':{'steps':self.full},'snaps.steps':{'steps':self.snaps}}}
            ledger={'output_root':str(self.root),'manifest_sha256':'1'*64,'environment':{'gpu':{'name':item['data']['metadata']['gpu']}}}
            approval={'output_root':str(self.root),'build_receipt_sha256':'2'*64,'environment_sha256':'3'*64,'limits':self.limits}
            actual=auth.base.authenticate_run(root.parent,run,manifest,ledger,approval,spec.digest(root.parent/'execution.json'))
            self.assertEqual(actual['data']['files'],item['data']['files'])

    def test_corrupted_scalar_only_data_and_missing_completion_refused(self):
        item=self.items[0];copy=self.root/'corrupt';shutil.copytree(item['root'].parent,copy)
        path=copy/'output/samples.csv';data=path.read_text();lines=data.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('2,'):
                fields=line.split(',');fields[5]=str(float(fields[5])+1);lines[i]=','.join(fields);break
        path.write_text('\n'.join(lines)+'\n')
        # Completion sizes alone cannot authenticate an arbitrary finite numeric alteration.
        # Receipt SHA256 binds every scalar-only row, even after sizes are replaced.
        complete=spec.load(copy/'output/equilibrium_complete.json')
        complete['files']={name:(copy/'output'/name).stat().st_size for name in complete['files']}
        spec.atomic(copy/'output/equilibrium_complete.json',complete)
        manifest={'schedules':{'full.steps':{'steps':self.full},'snaps.steps':{'steps':self.snaps}}}
        ledger={'output_root':str(self.root),'manifest_sha256':'1'*64,'environment':{'gpu':{'name':item['data']['metadata']['gpu']}}}
        approval={'output_root':str(self.root),'build_receipt_sha256':'2'*64,'environment_sha256':'3'*64,'limits':self.limits}
        with self.assertRaises(ValueError):auth.base.authenticate_run(copy,item['run'],manifest,ledger,approval,spec.digest(copy/'execution.json'))
        (copy/'output/equilibrium_complete.json').unlink()
        with self.assertRaises((ValueError,OSError)):auth.validate_output(copy/'output',item['run'],self.full,self.snaps,item['data']['metadata']['gpu'])


if __name__=='__main__':unittest.main()
