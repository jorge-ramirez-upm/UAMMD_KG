"""CPU-only D1.2 proposal tests. No execution or authorization interface."""
from fractions import Fraction
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import e1_d12_plan as plan
import e1_d1_pilot as old


class PlanningTests(unittest.TestCase):
    def test_schedules_exact_and_shared(self):
        for horizon in ('0.25','10','100'):
            shared=[]
            for dt in old.TIMESTEPS:
                s=plan.schedules(horizon,dt);end=old.exact_step(horizon,dt)
                for key in ('scalar_steps','full_steps','snapshot_steps'):
                    self.assertEqual(s[key],sorted(set(s[key])))
                    self.assertEqual(s[key][0],0);self.assertLessEqual(s[key][-1],end)
                self.assertEqual(s['full_steps'][-1],end)
                self.assertEqual(s['snapshot_steps'][-1],end)
                self.assertTrue(set(s['snapshot_steps'])<=set(s['full_steps']))
                self.assertEqual(len(s['snapshot_steps']),4)
                self.assertEqual(s['legacy_stride']*Fraction(dt),Fraction('0.1'))
                self.assertEqual(s['diagnostic_only_steps'],[1])
                shared.append([step*Fraction(dt) for step in s['shared_full_steps']])
                if horizon!='0.25':
                    self.assertEqual(len(s['scalar_steps']),int(horizon)*10+1)
                    self.assertEqual(len(s['full_steps']),int(horizon)*2+6)
                    self.assertEqual(len(set(s['scalar_steps'])&set(s['full_steps'])),int(horizon)*2+1)
            self.assertEqual(*shared)
        for dt in old.TIMESTEPS:
            with self.assertRaises(ValueError):plan.schedules('0.10003',dt)
        with self.assertRaises(ValueError):old.exact_step('0.0001','0.00025')

    def test_matrices_seeds_pairing_and_no_permission(self):
        physical_seeds=set()
        for phase in 'ABC':
            p=plan.phase_plan(phase)
            self.assertFalse(p['execution_authorized']);self.assertTrue(p['not_an_executable_manifest'])
            self.assertTrue(all(v is None for v in p['approved_limits'].values()))
            self.assertIsNone(p['frozen_execution_T']);self.assertIsNone(p['frozen_execution_replicas'])
            runs=plan.cells(phase);self.assertEqual(len(runs),8)
            seeds={r['seed'] for r in runs}
            self.assertFalse(seeds&physical_seeds);physical_seeds|=seeds
            self.assertEqual(len(seeds),4 if phase=='A' else 8)
            for r in runs:
                self.assertEqual(r['Z'],old.round_half_up(Fraction(r['M']*r['N'],r['Ne'])))
                self.assertEqual(Fraction(r['rho']),Fraction(r['Z'],r['M']*(r['N']+1)))
                self.assertEqual(r['steps']*Fraction(r['dt']),Fraction(r['T']))
        self.assertEqual({(r['N'],r['kappa'],r['Ne'],r['nu_hop']) for r in plan.cells('B')},
                         {(32,0,4,100),(32,10,4,100)})
        self.assertEqual(plan.phase_plan('B')['aggregate']['replica_bd_steps'],560000)
        self.assertEqual(plan.phase_plan('B')['aggregate']['expected_hopping_attempts'],4096000)

    def test_serialized_projection_fields_and_counts(self):
        r=plan.cells('B')[0];p=plan.projection(r);wide=plan.projection(r,24)
        self.assertEqual(p['files']['initial.csv']['row_bytes'],2+2+3*21+5)
        self.assertEqual(p['files']['equilibrium_positions.csv']['row_bytes'],6+21+2+2+3*21+7)
        self.assertEqual(p['files']['samples.csv']['columns'],14)
        self.assertEqual(p['files']['equilibrium_backbone.csv']['columns'],12)
        self.assertEqual(p['files']['equilibrium_tangents.csv']['columns'],5)
        self.assertEqual(p['files']['equilibrium_events.csv']['columns'],15)
        self.assertEqual(p['files']['bond_statistics.csv']['columns'],38)
        self.assertEqual(p['files']['samples.csv']['rows'],64*101)
        self.assertEqual(p['files']['equilibrium_sites.csv']['rows'],2112*26)
        self.assertEqual(p['files']['equilibrium_connectors.csv']['rows'],512*26)
        self.assertEqual(p['files']['equilibrium_backbone.csv']['rows'],64*5)
        self.assertEqual(p['files']['equilibrium_positions.csv']['rows'],2112*4)
        self.assertGreater(wide['csv_bytes'],p['csv_bytes'])
        self.assertEqual(p['csv_bytes'],sum(f['bytes'] for f in p['files'].values()))
        off=plan.projection(plan.cells('A')[0])
        self.assertFalse(any(name.startswith('equilibrium_') for name in off['files']))
        for phase in 'BC':
            a=plan.phase_plan(phase)['aggregate']
            self.assertLess(a['wide_csv_bytes']+a['json_receipts_logs_allowance_bytes']+
                            a['shared_build_provenance_allowance_bytes'],3*1024**3//4)
        # 24 ASCII characters accommodate every finite IEEE double formatted at precision17.
        for value in (-sys.float_info.max,sys.float_info.max,sys.float_info.min,-1e-300):
            self.assertLessEqual(len(format(value,'.17g')),24)

    def test_preservation_and_deterministic_generation(self):
        frozen=plan.preserved()
        self.assertEqual(frozen['e1_d1_pilot_config/manifest.json'],
                         'a14612088cab809f101c22c5c60c1879a136e9383305980864c014cae899dc2f')
        self.assertEqual(plan.payloads(),plan.payloads())
        for name,sha in old.source_hashes().items():self.assertEqual(old.digest(old.PROJECT/name),sha)

    def test_authentication_refuses_changes_and_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='d12-plan-') as tmp:
            root=Path(tmp)/'config';sha=plan.freeze(root)
            self.assertTrue(plan.check(root,sha)['authenticated'])
            with self.assertRaises(FileExistsError):plan.freeze(root)
            with self.assertRaises(ValueError):plan.check(root,'0'*64)
            f=root/'phase-B/dt0.0001.full.steps';data=f.read_bytes();f.write_bytes(data+b'2\n')
            with self.assertRaises(ValueError):plan.check(root,sha)
            f.write_bytes(data);f.unlink()
            with self.assertRaises(ValueError):plan.check(root,sha)
            f.write_bytes(data);(root/'unexpected').write_text('extra')
            with self.assertRaises(ValueError):plan.check(root,sha)
            (root/'unexpected').unlink();outside=Path(tmp)/'outside';outside.write_bytes(data)
            f.unlink();f.symlink_to(outside)
            with self.assertRaises(ValueError):plan.check(root,sha)

    def test_no_execution_switch_or_frozen_runner_compatibility(self):
        p=subprocess.run([sys.executable,str(plan.PROJECT/'e1_d12_plan.py'),
                          '--authorize-pilot-execution'],capture_output=True,timeout=10)
        self.assertNotEqual(p.returncode,0)
        with self.assertRaises(ValueError):
            old.validate_manifest(plan.CONFIG/'design.json',old.digest(plan.CONFIG/'design.json'))


if __name__=='__main__':unittest.main()
