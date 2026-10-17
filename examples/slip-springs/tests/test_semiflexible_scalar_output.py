"""Bounded scalar-profile replay, schema, operational and storage tests."""
import contextlib
import copy
import csv
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

import numpy as np
import semiflexible_stress_analysis as a
import semiflexible_scalar_schema as scalar
import semiflexible_stress_campaign as manager
import semiflexible_stress_profile as overlay
from semiflexible_stress_host import generate,write_parameters

BINS=[Path(p).resolve() for p in sys.argv[1:3]]
OLD=[Path(p).resolve() for p in sys.argv[3:5]]
sys.argv[1:]=[]


def table(path):
    return list(a.rows(path))


def change(path,mutation):
    with open(path,newline='') as f:
        reader=csv.DictReader(f);columns=reader.fieldnames;data=list(reader)
    mutation(data)
    with open(path,'w',newline='') as f:
        writer=csv.DictWriter(f,columns);writer.writeheader();writer.writerows(data)


class CompactChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='scalar-v1-bounded-');cls.root=Path(cls.temp.name);cls.serial=0;cls.pairs=[]
        cases=[(a.Chain.homogeneous(1,b0=0,kb=3,kappa=0),21,2),
               (a.Chain.homogeneous(2,kappa=2),40,2),
               (a.Chain([.8,1.2]*4,[20,40]*4,[0,0,2,0,10,0,2,0,0]),39,2),
               (a.Chain.homogeneous(8,kappa=10),48,4)]
        for binary in BINS:
            for model,steps,stride in cases:
                full=cls.run_case(binary,model,steps,stride,'full')
                compact=cls.run_case(binary,model,steps,stride,'compact')
                cls.pairs.append((full,compact))

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    @classmethod
    def run_case(cls,binary,model,steps,stride,mode,chains=6,initial=None,dump=True):
        cls.serial+=1;out=cls.root/f'run{cls.serial}';param=cls.root/f'p{cls.serial}.txt';write_parameters(param,model)
        cmd=[str(binary),'--output',str(out),'--parameters',str(param),'--springs',str(model.n),'--chains',str(chains),
             '--steps',str(steps),'--sample',str(stride),'--dt','.0001','--kbt','1.7','--seed','433501',
             '--stress-mode','stream','--stress-dump',str(int(dump)),'--stress-batch','7','--cpu-workers','2','--corr-levels','5','--corr-slots','8','--chain-density','.25']
        if mode=='compact':cmd+=['--scalar-output',mode]
        if initial is not None:
            path=cls.root/f'initial{cls.serial}.txt';np.savetxt(path,initial.reshape(-1,3));cmd+=['--initial',str(path)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        if result.returncode:raise RuntimeError(result.stderr)
        precision='single' if binary==BINS[0] or (OLD and binary==OLD[0]) else 'double'
        return dict(output=str(out),command=cmd,precision=precision,label='finite-test',phase='reference' if initial is None and dump else 'stream')

    def test_both_precision_equivalence_and_chain_summaries(self):
        for full,compact in self.pairs:
            f,c=Path(full['output']),Path(compact['output'])
            for name in ('initial.csv','final.csv','initial_bonds.csv','bond_statistics.csv','stress_samples.csv',
                         'stress_moments.csv','stress_correlations.csv','stress_correlations_raw.csv','parameters.txt'):
                self.assertEqual((f/name).read_bytes(),(c/name).read_bytes(),name)
            rf,rc=a.validate_run(full),a.validate_run(compact)
            for meta in ('metadata','stress_metadata'):
                for key,value in rf[meta].items():
                    if key.endswith('_seconds') or 'ns_per_bead_step' in key or key=='bead_updates_per_second':continue
                    self.assertEqual(value,rc[meta][key],key)
            data=table(f/'samples.csv');opts=a.options(full);half=int(opts['steps'])//2
            selected=scalar.selected_steps(int(opts['steps']),int(opts['sample']))
            self.assertEqual(table(c/'scalar_selected.csv'),[r for r in data if int(r['step']) in selected])
            summary=table(c/'scalar_statistics.csv')
            for chain,row in enumerate(summary):
                original=[r for r in data if int(r['chain'])==chain];window=[r for r in original if int(r['step'])>=half]
                self.assertEqual(float(row['min_length']),min(float(r['min_length']) for r in original))
                for field in ('re2','rg2')+tuple(k for k in original[0] if k.startswith('tangent')):
                    np.testing.assert_allclose(float(row['mean_'+field]),np.mean([float(r[field]) for r in window]),rtol=2e-14,atol=2e-14)
            self.assertFalse((c/'samples.csv').exists())

    def test_legacy_full_bytes_and_trajectory_prefixes(self):
        if OLD:
            model=a.Chain.homogeneous(2,kappa=2)
            for new,old in zip(BINS,OLD):
                f=self.run_case(new,model,24,3,'full');previous=self.run_case(old,model,24,3,'full')
                for path in Path(f['output']).iterdir():
                    if path.name not in ('metadata.json','stress_metadata.json'):
                        self.assertEqual(path.read_bytes(),(Path(previous['output'])/path.name).read_bytes(),path.name)
        for steps in (0,1,2,3,4,5):
            for binary in BINS:
                model=a.Chain.homogeneous(2,kappa=2)
                f=self.run_case(binary,model,steps,2,'full');c=self.run_case(binary,model,steps,2,'compact')
                self.assertEqual((Path(f['output'])/'final.csv').read_bytes(),(Path(c['output'])/'final.csv').read_bytes())

    def test_smooth_collapsed_gaussian_and_undefined_tangent(self):
        for binary in BINS:
            for n in (1,2):
                model=a.Chain.homogeneous(n,b0=0,kb=3,kappa=0);initial=np.zeros((6,n+1,3))
                f=self.run_case(binary,model,4,1,'full',initial=initial);c=self.run_case(binary,model,4,1,'compact',initial=initial)
                for name in ('final.csv','stress_samples.csv','bond_statistics.csv'):
                    self.assertEqual((Path(f['output'])/name).read_bytes(),(Path(c['output'])/name).read_bytes())
                self.assertEqual(a.load(Path(c['output'])/'stress_metadata.json')['bending_stress_launches'],0)
                first=table(Path(f['output'])/'stress_samples.csv')[0]
                self.assertTrue(all(float(first[k])==0 for k in a.CHANNELS))
                self.assertEqual((Path(c['output'])/'scalar_failure.json').exists(),n==2)
                if n==2:self.assertEqual(a.load(Path(c['output'])/'scalar_failure.json')['step'],0)
            failures=[]
            for mode in ('full','compact'):
                with self.assertRaises(RuntimeError) as error:
                    self.run_case(binary,a.Chain.homogeneous(2,b0=0,kb=3,kappa=2),4,1,mode,initial=np.zeros((6,3,3)))
                failures.append(str(error.exception))
            self.assertEqual(failures[0],failures[1])
            self.assertTrue(failures[0])

    def test_corruptions_and_no_cross_profile_acceptance(self):
        full,source=self.pairs[-1]
        with tempfile.TemporaryDirectory(dir=self.root) as temp:
            root=Path(temp)
            cases=[('scalar_statistics.csv',lambda d:d.pop(),'missing compact'),
                   ('scalar_statistics.csv',lambda d:d[1].update(chain='0'),'chain record'),
                   ('scalar_statistics.csv',lambda d:d[0].update(frames='2'),'coverage'),
                   ('scalar_statistics.csv',lambda d:d[0].update(final_half_frames='2'),'coverage'),
                   ('scalar_statistics.csv',lambda d:d[0].update(min_length='0.001'),'checksum'),
                   ('scalar_statistics.csv',lambda d:d[0].update(mean_re2='nan'),'mean_re2'),
                   ('scalar_selected.csv',lambda d:d.pop(),'missing selected'),
                   ('scalar_selected.csv',lambda d:d.reverse(),'selected scalar frame')]
            for index,(name,mutation,message) in enumerate(cases):
                out=root/str(index);shutil.copytree(source['output'],out);run=copy.deepcopy(source);run['output']=str(out)
                change(out/name,mutation)
                with self.assertRaisesRegex(a.Invalid,message):a.validate_run(run)
            for index,(key,value) in enumerate([('profile','full'),('schema','wrong'),('schema_sha256','0'*64),('frames',1),('schedule_hash','0'*16),('final_half_frames',2),('minimum_sampled_bond',.001)]):
                out=root/f'j{index}';shutil.copytree(source['output'],out);run=copy.deepcopy(source);run['output']=str(out)
                m=a.load(out/'scalar_metadata.json');m[key]=value;(out/'scalar_metadata.json').write_text(json.dumps(m))
                with self.assertRaises(a.Invalid):a.validate_run(run)
            out=root/'partial';shutil.copytree(source['output'],out);(out/'scalar_metadata.json').unlink();run=copy.deepcopy(source);run['output']=str(out)
            with self.assertRaises(FileNotFoundError):a.validate_run(run)
            wrong=copy.deepcopy(source);wrong['command']=wrong['command'][:-2]
            with self.assertRaisesRegex(a.Invalid,'full profile'):a.validate_run(wrong)
            cache=root/'cache';cache.mkdir();run=copy.deepcopy(source);run['execution_profile']='compact-fixture'
            with contextlib.redirect_stdout(io.StringIO()):manager.analyze(cache,[run],['same-id'],'same-manifest')
            with self.assertRaisesRegex(a.Invalid,'checkpoint execution profile'):manager.analyze(cache,[full],['same-id'],'same-manifest')

    def test_overlay_authentication_and_parent_immutability(self):
        with tempfile.TemporaryDirectory(dir=self.root) as temp:
            root=Path(temp);base=root/'parent';dest=root/'profile';build=BINS[0].parents[1]
            with contextlib.redirect_stdout(io.StringIO()):generate(base,build)
            before={p.name:a.digest(p) for p in base.iterdir() if p.is_file()}
            with contextlib.redirect_stdout(io.StringIO()):overlay.create(base,dest,build)
            manifest,ids,mhash=a.authenticate(dest);parent,pids,_=a.authenticate(base)
            self.assertEqual(len(manifest),282);self.assertEqual(sum(a.options(r)['scalar-output']=='compact' for r in manifest),174)
            self.assertTrue(set(ids).isdisjoint(pids))
            for r,original,pid in zip(manifest,parent,pids):
                self.assertEqual(r['parent_run_id'],pid)
                opts=a.options(r);old=a.options(original)
                self.assertEqual({k:v for k,v in opts.items() if k not in ('output','scalar-output')},{k:v for k,v in old.items() if k not in ('output','scalar-output')})
            self.assertEqual(before,{p.name:a.digest(p) for p in base.iterdir() if p.is_file()})
            corrupt=a.load(dest/'manifest.json');corrupt[0]['command'][corrupt[0]['command'].index('--steps')+1]='1'
            (dest/'manifest.json').write_text(json.dumps(corrupt))
            with self.assertRaisesRegex(a.Invalid,'derived scientific'):a.authenticate(dest)

    def test_bounded_output_allocations_and_timers(self):
        model=a.Chain.homogeneous(8,kappa=10);metrics=[]
        for binary in BINS:
            f=self.run_case(binary,model,400,1,'full',chains=128,dump=False);c=self.run_case(binary,model,400,1,'compact',chains=128,dump=False)
            rf,rc=a.validate_run(f),a.validate_run(c);fp,cp=Path(f['output']),Path(c['output'])
            fb=sum(p.stat().st_size for p in fp.iterdir());cb=sum(p.stat().st_size for p in cp.iterdir())
            self.assertLess(cb,.1*fb)
            self.assertEqual(rf['metadata']['device_bytes'],rc['metadata']['device_bytes'])
            self.assertEqual(rf['stress_metadata']['gpu_stress_bytes'],rc['stress_metadata']['gpu_stress_bytes'])
            m=a.load(cp/'scalar_metadata.json');self.assertEqual(m['serialized_rows'],5*128);self.assertEqual(m['gpu_bytes'],0)
            metrics.append(dict(precision=f['precision'],full_bytes=fb,compact_bytes=cb,full_scalar_bytes=(fp/'samples.csv').stat().st_size,
                compact_scalar_bytes=sum((cp/name).stat().st_size for name in ('scalar_selected.csv','scalar_statistics.csv','scalar_metadata.json')),
                full_rows=401*128,compact_rows=m['serialized_rows'],extra_host_bytes=m['host_bytes'],gpu_bytes=rf['metadata']['device_bytes']+rf['stress_metadata']['gpu_stress_bytes'],
                full_integration=rf['metadata']['integration_ns_per_bead_step'],compact_integration=rc['metadata']['integration_ns_per_bead_step'],
                full_overall=rf['metadata']['overall_ns_per_bead_step'],compact_overall=rc['metadata']['overall_ns_per_bead_step']))
        target=a.PROJECT/'build/scalar-v1-output-metrics.json';target.write_text(json.dumps(metrics,indent=2)+'\n')
        print('Tiny functional measurements only:',json.dumps(metrics))

    def test_receipt_stages_and_interrupted_postprocessing(self):
        source=self.pairs[-1][1]
        for stage in ('file_validation','hashing'):
            with tempfile.TemporaryDirectory(dir=self.root) as temp:
                root=Path(temp);run=copy.deepcopy(source);out=root/'run';run['output']=str(out)
                run['command'][run['command'].index('--output')+1]=str(out)
                fake=Mock();fake.poll.side_effect=[None,0];fake.returncode=0;fake.pid=os.getpid()
                def launch(*args,**kwargs):shutil.copytree(source['output'],out);return fake
                ledger=dict(executables={run['precision']:dict(sha256=a.digest(run['command'][0]))})
                patcher=patch.object(a,'validate_run',side_effect=KeyboardInterrupt) if stage=='file_validation' else patch.object(manager,'fingerprints',side_effect=KeyboardInterrupt)
                with patch.object(subprocess,'Popen',side_effect=launch),patch.object(manager,'command_output',return_value=dict(exit_code=0,stdout='now, 145 MiB\n')),patch.object(manager.time,'sleep'),patcher:
                    with self.assertRaises(KeyboardInterrupt):manager.execute_one(root,run,'fixture','manifest',ledger)
                r=manager.unenvelope(Path(str(out)+'.execution.json'))
                self.assertEqual(r['status'],'interrupted');self.assertEqual(r['stage'],stage);self.assertEqual(r['child_exit_code'],0)
                self.assertEqual(r['scalar_output'],'compact');self.assertEqual(r['error_type'],'KeyboardInterrupt')
                monitor=table(Path(str(out)+'.monitor.csv'));self.assertEqual(monitor[0]['production_observed'],'1')
        with tempfile.TemporaryDirectory(dir=self.root) as temp:
            root=Path(temp);run=copy.deepcopy(source);out=root/'completed';run.update(output=str(out),phase='stream')
            run['command'][run['command'].index('--output')+1]=str(out)
            fake=Mock();fake.poll.side_effect=[None,0];fake.returncode=0;fake.pid=os.getpid()
            def launch(*args,**kwargs):shutil.copytree(source['output'],out);return fake
            ledger=dict(executables={run['precision']:dict(sha256=a.digest(run['command'][0]))})
            with patch.object(subprocess,'Popen',side_effect=launch),patch.object(manager,'command_output',return_value=dict(exit_code=0,stdout='now, 145 MiB\n')),patch.object(manager.time,'sleep'):
                with contextlib.redirect_stdout(io.StringIO()):manager.execute_one(root,run,'fixture','manifest',ledger)
            receipt=manager.unenvelope(Path(str(out)+'.execution.json'))
            self.assertEqual(receipt['status'],'completed');self.assertIn('hashing_seconds',receipt)
            validate=a.validate_run;diagnostic={'mock_diagnostic':True}
            def choose(manifest,ids,diagnostic=False):return ({'mock_diagnostic':True},'diagnostic') if diagnostic else (run,'fixture')
            def check(item):return dict(checks=[],virial_statistics={}) if item==diagnostic else validate(item)
            with patch.object(manager,'pilot',side_effect=choose),patch.object(manager,'provenance_checks',return_value=[]),patch.object(a,'validate_run',side_effect=check):
                with contextlib.redirect_stdout(io.StringIO()):manager.pilot_report(root,[run],['fixture'])
            report=a.load(root/'pilot-readiness.json');meta=a.load(out/'metadata.json')
            self.assertEqual(report['serialized_scalar_rows'],30)
            self.assertAlmostEqual(report['estimated_same_system_production'][0]['estimated_production_seconds'],meta['production_wall_seconds'],places=12)


if __name__=='__main__':
    if len(BINS)!=2:raise SystemExit('supply single and double scalar-v1 binaries, optionally both legacy binaries')
    unittest.main(verbosity=2)
