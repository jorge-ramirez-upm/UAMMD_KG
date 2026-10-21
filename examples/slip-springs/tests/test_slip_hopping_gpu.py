"""Bounded Stage B tests: independent CPU oracle versus production CUDA hopping."""
import csv
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from slip_hopping_reference import Hopping
GPU = Path(sys.argv.pop(1)).resolve()
SIM = Path(sys.argv.pop(1)).resolve()
INT_MAX = 2**31-1


class GPUHopping(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='e1-stage-b-')
        self.root = Path(self.temp.name)
        self.serial = 0

    def tearDown(self):self.temp.cleanup()

    def execute(self, text):
        self.serial += 1
        source,target = self.root/f'in{self.serial}',self.root/f'out{self.serial}'
        source.write_text(text)
        result = subprocess.run([str(GPU),str(source),str(target)],capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        lines = target.read_text().splitlines()
        return int(lines[0]),lines[1:]

    def fixtures(self, model, cases, operations=None, rate=0, dt=.25, batches=0, corrupt=0):
        z = len(model.initial)
        operations = operations or [[] for _ in cases]
        op_count = len(operations[0])
        text = f'0 {len(cases)} {model.m} {len(model.r)} {z} {op_count} {batches} {z*rate*dt:.17g} {model.k:.17g} {model.kbt:.17g}\n'
        for i,(state,ops) in enumerate(zip(cases,operations)):
            self.assertEqual(len(ops),op_count)
            text += f'{71300+i} {corrupt}\n'
            text += ''.join(' '.join(f'{x:.17g}' for x in p)+'\n' for p in model.r)
            text += ''.join(f'{s} '+' '.join(f'{x:.17g}' for x in a)+'\n' for s,a in zip(state,model.a))
            text += ''.join(f'{j} {d} {u:.17g}\n' for j,d,u in ops)
        bits,lines = self.execute(text)
        self.assertEqual(int(lines.pop(0)),INT_MAX)
        self.assertEqual(len(lines),len(cases))
        parsed = []
        for line in lines:
            fields = line.split()
            self.assertEqual(len(fields),7+z+op_count+4*len(model.r))
            parsed.append((list(map(int,fields[:7])),tuple(map(int,fields[7:7+z])),
                           list(map(int,fields[7+z:7+z+op_count])),
                           np.array(list(map(float,fields[7+z+op_count:]))).reshape(-1,4)))
        return bits,parsed

    def model(self, sites=(0,2)):
        return Hopping([[0,0,0],[.8,.1,0],[1.7,0,.2],[2.8,0,0]],
                       [[.1,0,0],[2.5,0,0]][:len(sites)],sites,4,1.25,1.7)

    def test_every_enumerated_transition_acceptance_balance_and_force_relocation(self):
        for initial in ((0,), (0,2)):
            model = self.model(initial)
            states,_ = model.equilibrium()
            cases,operations = [],[]
            for state in states:
                for j in range(len(initial)):
                    for d in (-1,1):
                        dest = state[j]+d
                        uniforms = [.25,.75]
                        if 0<=dest<4 and dest not in state:
                            proposed = tuple(dest if i==j else s for i,s in enumerate(state))
                            p = math.exp(-max(0.,(model.energy(proposed)-model.energy(state))/model.kbt))
                            uniforms = [.5*p,.5*(1+p)] if p<1 else [.99]
                        for u in uniforms:
                            cases.append(state);operations.append([(j,d,u)])
            bits,actual = self.fixtures(model,cases,operations)
            stored = Hopping(model.r.astype(np.float32) if bits==32 else model.r,
                             model.a.astype(np.float32) if bits==32 else model.a,
                             initial,4,model.k,model.kbt)
            for state,ops,(stat,final,outcomes,force) in zip(cases,operations,actual):
                self.assertEqual(stat[0],INT_MAX)
                expected,result = stored.attempt(state,*ops[0])
                self.assertEqual((final,outcomes),(expected,[result]))
                expected_force = np.zeros_like(force)
                for j,s in enumerate(final):
                    displacement = stored.r[s]-stored.a[j]
                    expected_force[s,:3] = -stored.k*displacement
                    expected_force[s,3] = stored.k*np.dot(displacement,displacement)/2
                np.testing.assert_allclose(force,expected_force,atol=2e-6 if bits==32 else 2e-14,rtol=2e-6 if bits==32 else 2e-14)

    def test_repeated_selections_exclusion_order_populations_and_invariants(self):
        model = self.model()
        multi = Hopping(np.tile(model.r,(2,1)),np.tile(model.a,(2,1)),(0,2,4,6),4,1.25,1.7)
        ops = [(0,-1,.5),(0,1,1e-8),(0,1,.5),(1,1,1e-8),
               (0,1,1e-8),(2,1,1e-8),(2,1,.5),(3,1,1e-8)]
        _,result = self.fixtures(multi,[multi.initial],[ops])
        expected = multi.initial
        outcomes = []
        for op in ops:
            expected,outcome = multi.attempt(expected,*op);outcomes.append(outcome)
        self.assertEqual(result[0][1:3],(expected,outcomes))
        self.assertEqual(result[0][0][0],INT_MAX)
        _,bad = self.fixtures(model,[model.initial],corrupt=1)
        self.assertEqual(bad[0][0][0]%8,6)
        _,wrong_order = self.fixtures(model,[(2,0)])
        self.assertEqual(wrong_order[0][0][0]%8,6)
        full = Hopping(model.r[:2],model.a,(0,1),2,model.k,model.kbt)
        _,blocked = self.fixtures(full,[full.initial],rate=4,batches=8)
        stat,state,_,_ = blocked[0]
        self.assertEqual(state,full.initial)
        self.assertEqual(stat[3],0)
        self.assertEqual(stat[2],stat[4]+stat[5])
        # Fault injection: a nonfinite energy change must fail, never turn
        # overflow into automatic downhill acceptance or uphill rejection.
        huge = Hopping([[0,0,0],[1e300,0,0]],[[0,0,0]],(0,),2,1.25)
        _,invalid = self.fixtures(huge,[(0,)],[[(0,1,.5)]])
        self.assertEqual(invalid[0][0][0]%8,7)
        self.assertEqual(invalid[0][1],(0,))

    def test_poisson_statistics_small_large_means_and_invalid_budget(self):
        n = 8192
        for mean in (0.,.3,4.,64.,4096.):
            _,lines = self.execute(f'1 {n} {mean}\n')
            samples = np.array([list(map(int,line.split())) for line in lines])
            self.assertTrue(np.all(samples[:,1]==INT_MAX))
            x = samples[:,0]
            self.assertLessEqual(abs(x.mean()-mean),6*math.sqrt(mean/n)+1e-12)
            self.assertLessEqual(abs(x.var()-mean),6*math.sqrt((mean+2*mean**2)/n)+1e-12)
            if mean<5:
                p = math.exp(-mean)
                self.assertLessEqual(abs(np.mean(x==0)-p),6*math.sqrt(p*(1-p)/n)+1e-12)
        _,lines = self.execute('1 1 10001\n')
        self.assertEqual(int(lines[0].split()[1])%8,7)

    def test_event_budget_and_counter_overflow_are_fatal_without_truncation(self):
        maximum = 2**64-1
        for k,attempts,batches in ((100001,0,0),(10,maximum-5,0),(0,0,maximum)):
            _,lines = self.execute(f'2 {k} {attempts} {batches}\n')
            error,after_attempts,after_batches = map(int,lines[0].split())
            self.assertEqual(error%8,7)
            self.assertEqual((after_attempts,after_batches),(attempts,batches))
        _,lines = self.execute('2 100000 0 0\n')
        self.assertEqual(tuple(map(int,lines[0].split())),(INT_MAX,100000,1))

    def test_fixed_anchor_equilibrium_and_rate_dependent_kinetics(self):
        model = self.model()
        states,pi = model.equilibrium()
        rng = np.random.default_rng(71309)
        n,batches,dt = 8192,8,.25
        initial = rng.choice(len(states),size=n,p=pi)
        moved = []
        for rate in (.5,4.):
            _,result = self.fixtures(model,[states[i] for i in initial],rate=rate,dt=dt,batches=batches)
            final = np.array([states.index(row[1]) for row in result])
            stats = np.array([row[0] for row in result])
            self.assertTrue(np.all(stats[:,0]==INT_MAX))
            self.assertTrue(np.all(stats[:,1]==batches))
            self.assertTrue(np.all(stats[:,2]==stats[:,3:7].sum(axis=1)))
            observed = np.bincount(final,minlength=len(states))/n
            self.assertTrue(np.all(np.abs(observed-pi)<6*np.sqrt(pi*(1-pi)/n)),(rate,observed,pi))
            transition = model.transition(rate,batches*dt)
            expected_change = 1-np.dot(pi,np.diag(transition))
            changed = np.mean(final!=initial)
            self.assertLess(abs(changed-expected_change),6*math.sqrt(expected_change*(1-expected_change)/n))
            expected_attempts = len(model.initial)*rate*dt*batches
            self.assertLess(abs(stats[:,2].mean()-expected_attempts),6*math.sqrt(expected_attempts/n))
            moved.append(changed)
            # Transient oracle from a definite starting state, independent of
            # stationarity initialization and without an equilibration claim.
            _,transient = self.fixtures(model,[states[0]]*n,rate=rate,dt=dt,batches=batches)
            frequencies = np.bincount([states.index(row[1]) for row in transient],minlength=len(states))/n
            expected = transition[0]
            self.assertTrue(np.all(np.abs(frequencies-expected)<6*np.sqrt(expected*(1-expected)/n)+1e-12))
            print(f'GPU rate={rate} stationary_max_error={np.max(abs(observed-pi)):.6g} change={changed:.6g} predicted={expected_change:.6g}')
        self.assertGreater(moved[1],moved[0])
        self.assertGreater(np.ptp(pi),.1)  # fixed-anchor conditional law is not uniform

    def simulate(self,name,extra=(),expect=True):
        out = self.root/name
        cmd = [str(SIM),'--springs','3','--chains','2','--kappa','2','--steps','16',
               '--sample','2','--seed','4317','--dt','.0001','--output',str(out)] + list(extra)
        result = subprocess.run(cmd,capture_output=True,text=True,timeout=40)
        self.assertEqual(result.returncode==0,expect,result.stderr)
        return out,result

    def test_simulator_disabled_replay_and_final_anchor_identity(self):
        for z in (0,3):
            flags = [] if z==0 else ['--slip-count','3','--slip-ms2','2.4']
            base,_ = self.simulate(f'base{z}',flags)
            zero,_ = self.simulate(f'zero{z}',flags+['--hop-rate','0'])
            if not z:
                empty,_ = self.simulate('empty-rate',['--hop-rate','10000'])
            for filename in ('initial.csv','final.csv','samples.csv','initial_bonds.csv','bond_statistics.csv','parameters.txt'):
                self.assertEqual((base/filename).read_bytes(),(zero/filename).read_bytes())
                if not z:self.assertEqual((base/filename).read_bytes(),(empty/filename).read_bytes())
            self.assertFalse((zero/'hopping_metadata.json').exists())
        flags = ['--slip-count','3','--slip-ms2','2.4','--hop-rate','10000']
        a,_ = self.simulate('active',flags)
        b,_ = self.simulate('replay',flags)
        for filename in ('initial.csv','final.csv','samples.csv','slip_springs_initial.csv','slip_springs_final.csv','hopping_metadata.json'):
            self.assertEqual((a/filename).read_bytes(),(b/filename).read_bytes())
        self.assertEqual((a/'initial.csv').read_bytes(),(base/'initial.csv').read_bytes())
        def read(path):
            with path.open() as f:return list(csv.DictReader(f))
        initial,final = [read(a/f'slip_springs_{stage}.csv') for stage in ('initial','final')]
        self.assertEqual(len(initial),3);self.assertEqual(len(final),3)
        for old,new in zip(initial,final):
            for key in ('spring','chain','ax','ay','az'):self.assertEqual(old[key],new[key])
        for c in ('0','1'):
            beads = [int(r['bead']) for r in final if r['chain']==c]
            self.assertEqual(beads,sorted(set(beads)))
        stat = json.loads((a/'hopping_metadata.json').read_text())
        self.assertEqual(stat['batches'],16)
        self.assertGreater(stat['accepted'],0)
        self.assertEqual(stat['attempts'],sum(stat[k] for k in ('accepted','boundary_rejected','occupied_rejected','metropolis_rejected')))
        self.assertEqual(stat['poisson_mean'],3.)

    def test_bd_noise_isolation_and_next_step_force_relocation(self):
        flags = ['--slip-count','3','--slip-ms2','2.4']
        outputs = {}
        for steps in (1,2):
            for rate in (0,100000):
                out,_ = self.simulate(f'drift-{steps}-{rate}',flags+['--steps',str(steps),'--sample','1','--hop-rate',str(rate)])
                outputs[steps,rate] = out
        def records(path):
            with path.open() as f:return list(csv.DictReader(f))
        def coords(out):return np.array([[float(r[k]) for k in ('x','y','z')] for r in records(out/'final.csv')])
        self.assertEqual((outputs[1,0]/'final.csv').read_bytes(),(outputs[1,100000]/'final.csv').read_bytes())
        r1 = coords(outputs[1,0])
        meta = json.loads((outputs[1,0]/'metadata.json').read_text())
        forces = []
        for path in (outputs[1,0]/'fixed_slip_springs.csv',outputs[1,100000]/'slip_springs_final.csv'):
            force = np.zeros_like(r1)
            for row in records(path):
                i = int(row['chain'])*4+int(row['bead'])
                anchor = np.array([float(row[k]) for k in ('ax','ay','az')])
                force[i] = -meta['slip_effective_stiffness']*(r1[i]-anchor)
            forces.append(force)
        expected = meta['effective_mobility_step']*(forces[1]-forces[0])
        self.assertGreater(np.max(np.abs(expected)),1e-6)
        np.testing.assert_allclose(coords(outputs[2,100000])-coords(outputs[2,0]),expected,
                                   atol=5e-7 if meta['precision_bits']==32 else 3e-15,rtol=0)

    def test_cli_guards_and_active_stress_prohibition(self):
        for i,flags in enumerate((['--hop-rate','-1'],['--hop-rate','nan'],
                                   ['--slip-count','1','--slip-ms2','3','--hop-rate','1e308'],
                                   ['--slip-count','1','--slip-ms2','3','--hop-rate','1e-320'])):
            out,result = self.simulate(f'invalid{i}',flags,expect=False)
            self.assertFalse(out.exists(),result.stderr)
        for mode in ('diagnostic','stream','every-step'):
            self.simulate('stress'+mode,['--slip-count','1','--slip-ms2','3','--hop-rate','2','--stress-mode',mode],expect=False)

if __name__=='__main__':unittest.main(verbosity=2)
