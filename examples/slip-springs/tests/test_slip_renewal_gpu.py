"""Stage C bounded acceptance: independent CPU densities, enumeration and clusters."""
import csv
import io
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from slip_renewal_reference import Canonical,hypergeometric
GPU=Path(sys.argv.pop(1)).resolve();SIM=Path(sys.argv.pop(1)).resolve()
INT_MAX=2**31-1


class RenewalGPU(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='e1-stage-c-');self.root=Path(self.temp.name);self.serial=0
    def tearDown(self):self.temp.cleanup()

    def fixtures(self,model,cases,operations=None,rate=0,dt=.25,batches=0):
        n=len(cases);z=len(cases[0][0]);operations=operations or [[] for _ in cases]
        ops=len(operations[0]);text=io.StringIO()
        text.write(f'{n} {model.m} {len(model.r)} {z} {ops} {batches} {z*rate*dt:.17g} {model.ms2:.17g} {model.kbt:.17g}\n')
        positions=''.join(' '.join(f'{x:.17g}' for x in r)+'\n' for r in model.r)
        for i,((sites,anchors),events) in enumerate(zip(cases,operations)):
            self.assertEqual(len(events),ops)
            text.write(f'{99100+i}\n'+positions)
            for s,a in zip(sites,anchors):text.write(f'{s} '+' '.join(f'{x:.17g}' for x in a)+'\n')
            for kind,j,d,u,dest,a in events:
                text.write(f'{kind} {j} {d} {u:.17g} {dest} '+' '.join(f'{x:.17g}' for x in a)+'\n')
        self.serial+=1;source=self.root/f'in{self.serial}';target=self.root/f'out{self.serial}'
        source.write_text(text.getvalue())
        result=subprocess.run([str(GPU),str(source),str(target)],capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        raw=target.read_bytes();lines=raw.decode().splitlines();bits=int(lines.pop(0))
        self.assertEqual(int(lines.pop(0)),INT_MAX);self.assertEqual(len(lines),n)
        rows=[]
        for line in lines:
            fields=line.split();self.assertEqual(len(fields),12+7*z+ops+4*len(model.r))
            state=np.array(list(map(float,fields[12:12+7*z]))).reshape(z,7)
            rows.append((np.array(list(map(int,fields[:12]))),tuple(state[:,0].astype(int)),
                         state[:,4:7],state[:,1:4].astype(int),
                         list(map(int,fields[12+7*z:12+7*z+ops])),
                         np.array(list(map(float,fields[12+7*z+ops:]))).reshape(-1,4)))
        return bits,rows,raw

    def model(self,m=3,chains=3,coincident=False):
        return Canonical(np.zeros((m*chains,3)) if coincident else
                         [[.7*b+2*c,.1*b*b-c,.2*c] for c in range(chains) for b in range(m)],m)

    def check_state(self,model,row):
        stat,sites,anchors,links,_,force=row
        self.assertEqual(stat[0],INT_MAX)
        model.check(sites,anchors)
        expected=np.array([[s//model.m,p,n] for s,(p,n) in zip(sites,model.links(sites))])
        np.testing.assert_array_equal(links,expected)

    def test_exhaustive_transfers_and_independent_density_balance(self):
        for m,chains,z in ((2,1,1),(2,1,2),(2,2,2),(3,3,3)):
            model=self.model(m,chains);cases=[];operations=[]
            for occupied in itertools.combinations(range(m*chains),z):
                sites=occupied[::-1]  # IDs deliberately not in contour order
                anchors=model.r[list(sites)]+np.arange(z)[:,None]*.1+[.2,-.3,.4]
                for j,source in enumerate(sites):
                    if source not in model.ends:continue
                    for dest in model.ends:
                        candidate=model.r[dest]+[1.7,-.8,.3]
                        cases.append((sites,anchors));operations.append([(1,j,0,.5,dest,candidate)])
            bits,actual,_=self.fixtures(model,cases,operations)
            dtype=np.float32 if bits==32 else np.float64
            stored=Canonical(model.r.astype(dtype),m,model.ms2,model.kbt)
            for (sites,a),ops,row in zip(cases,operations,actual):
                j,dest,candidate=ops[0][1],ops[0][4],np.asarray(ops[0][5],dtype=dtype).astype(float)
                a=a.astype(dtype).astype(float)
                after,new,outcome=stored.renewal(sites,a,j,dest,candidate)
                self.check_state(stored,row)
                self.assertEqual(row[1],after);np.testing.assert_array_equal(row[2],new)
                self.assertEqual(row[4],[outcome])
                if outcome==4:
                    lhs=stored.log_density(sites,a)+stored.log_g(candidate,dest)
                    rhs=stored.log_density(after,new)+stored.log_g(a[j],sites[j])
                    self.assertAlmostEqual(lhs,rhs,places=12)
                expected=np.zeros_like(row[5]);k=float(dtype(stored.k))
                for site,anchor in zip(after,new):
                    d=stored.r[site]-anchor;expected[site,:3]=-k*d;expected[site,3]=.5*k*np.dot(d,d)
                np.testing.assert_allclose(row[5],expected,atol=2e-6 if bits==32 else 5e-14,rtol=3e-6 if bits==32 else 5e-14)

    def test_sequential_repeated_id_empty_chain_links_and_transaction_failure(self):
        model=self.model();sites=(0,1,5,8);anchors=model.r[list(sites)]+[.1,.2,.3]
        ops=[(1,0,0,.5,6,[4.1,-1.8,.7]),(0,0,1,1e-12,0,[0,0,0]),
             (1,2,0,.5,2,[1.5,.5,.1]),(1,3,0,.5,3,[2.1,-.8,.3]),
             (0,0,-1,1e-12,0,[0,0,0]),(1,0,0,.5,5,[3.5,-.5,.6]),
             (1,2,0,.5,0,[1000,-1000,300]),(1,3,0,.5,3,[7,8,9])]
        bits,result,_=self.fixtures(model,[(sites,anchors)],[ops]);dtype=np.float32 if bits==32 else np.float64
        current=sites;a=anchors.astype(dtype).astype(float);stored=Canonical(model.r.astype(dtype),3)
        outcomes=[]
        for kind,j,d,u,dest,candidate in ops:
            if kind:current,a,outcome=stored.renewal(current,a,j,dest,np.asarray(candidate,dtype=dtype).astype(float))
            else:current,a,outcome=stored.attempt(current,a,j,d,u)
            outcomes.append(outcome)
        self.check_state(stored,result[0]);self.assertEqual(result[0][1],current)
        np.testing.assert_array_equal(result[0][2],a);self.assertEqual(result[0][4],outcomes)
        for dest,expected_error,outcome in ((0,INT_MAX,5),(3,7,6)):
            _,bad,_=self.fixtures(model,[(sites,anchors)],[[(3,0,0,.5,dest,[0,0,0])]])
            self.assertEqual(bad[0][0][0] if expected_error==INT_MAX else bad[0][0][0]%8,expected_error)
            self.assertEqual(bad[0][1],sites);np.testing.assert_array_equal(bad[0][2],anchors.astype(dtype))
            self.assertEqual(bad[0][4],[outcome])

    def test_fresh_gaussian_anchors_and_uniform_destination_proposals(self):
        model=self.model();n=16384;initial=((0,),model.r[[0]]+[.1,.2,.3])
        bits,rows,_=self.fixtures(model,[initial]*n,[[(2,0,0,.5,0,[0,0,0])]]*n)
        sites=np.array([r[1][0] for r in rows]);expected=n/len(model.ends)
        for end in model.ends:
            self.assertLess(abs(np.count_nonzero(sites==end)-expected),6*math.sqrt(n/6*(1-1/6)))
        good=np.array([r[4][0]==4 for r in rows]);self.assertTrue(np.any(~good))
        dtype=np.float32 if bits==32 else np.float64
        displacement=np.array([r[2][0] for r in rows])[good]-model.r.astype(dtype)[sites[good]]
        count=len(displacement);variance=model.ms2/3
        self.assertTrue(np.all(abs(displacement.mean(axis=0))<6*math.sqrt(variance/count)))
        self.assertTrue(np.all(abs(np.mean(displacement**2,axis=0)-variance)<6*variance*math.sqrt(2/count)))
        norm2=np.sum(displacement**2,axis=1)
        self.assertLess(abs(norm2.mean()-model.ms2),6*norm2.std(ddof=1)/math.sqrt(count))
        self.assertLess(abs(np.mean(displacement[:,0]*displacement[:,1])),6*variance/math.sqrt(count))
        print(f'fresh anchors n={count} mean_square={norm2.mean():.7g}')

    def test_full_process_canonical_populations_occupancy_connectors_and_rates(self):
        model=self.model();rng=np.random.default_rng(98131);n=8192;z=3;batches=8;dt=.25
        cases=[model.initial(z,rng) for _ in range(n)];target=hypergeometric(3,3,z);kinetics=[]
        initial_pop=np.array([sum(s<3 for s in sites) for sites,_ in cases])
        for rate in (.5,4.):
            bits,rows,_=self.fixtures(model,cases,rate=rate,dt=dt,batches=batches)
            pop=np.array([sum(s<3 for s in row[1]) for row in rows])
            frequencies=np.bincount(pop,minlength=4)/n
            self.assertTrue(np.all(abs(frequencies-target)<6*np.sqrt(target*(1-target)/n)))
            self.assertTrue(np.any(pop!=initial_pop))
            occupied=np.array([[s in row[1] for s in range(9)] for row in rows])
            self.assertTrue(np.all(abs(occupied.mean(axis=0)-z/9)<6*math.sqrt((z/9)*(1-z/9)/n)))
            dtype=np.float32 if bits==32 else np.float64
            extension=np.array([np.mean(np.sum((model.r.astype(dtype)[list(row[1])]-row[2])**2,axis=1)) for row in rows])
            self.assertLess(abs(extension.mean()-model.ms2),6*extension.std(ddof=1)/math.sqrt(n))
            stat=np.array([row[0] for row in rows]);mean_k=z*rate*dt*batches
            self.assertTrue(np.all(stat[:,0]==INT_MAX));self.assertTrue(np.all(stat[:,1]==batches))
            self.assertTrue(np.all(stat[:,2]==stat[:,3:7].sum(axis=1)))
            self.assertTrue(np.all(stat[:,7]==stat[:,4]));self.assertTrue(np.all(stat[:,7]==stat[:,8]+stat[:,9]))
            self.assertTrue(np.all(stat[:,8]==stat[:,10]+stat[:,11]))
            self.assertLess(abs(stat[:,2].mean()-mean_k),6*math.sqrt(mean_k/n))
            expected=mean_k/3*(5/6)*(6/8)
            self.assertLess(abs(stat[:,8].mean()-expected),6*stat[:,8].std(ddof=1)/math.sqrt(n))
            for row in rows:self.check_state(model,row)
            kinetics.append(stat[:,8].mean())
            print(f'GPU rate={rate} population={frequencies.tolist()} ms_extension={extension.mean():.7g} renewals={kinetics[-1]:.7g} target={expected:.7g}')
        self.assertGreater(kinetics[1],kinetics[0])

    def test_exact_reduced_generator_transients_and_replay(self):
        model=self.model(coincident=True);z=3;n=8192;batches=8;dt=.25
        states,q=model.integrated_generator(z,1.);lookup={s:i for i,s in enumerate(states)}
        values,vectors=np.linalg.eigh(q);rng=np.random.default_rng(98132)
        cases=[((0,1,2),math.sqrt(model.ms2/3)*rng.normal(size=(z,3))) for _ in range(n)]
        moved=[]
        for rate in (.5,4.):
            _,rows,raw=self.fixtures(model,cases,rate=rate,dt=dt,batches=batches)
            expected=((vectors*np.exp(values*rate*batches*dt))@vectors.T)[lookup[(0,1,2)]]
            actual=np.bincount([lookup[tuple(sorted(r[1]))] for r in rows],minlength=len(states))/n
            tolerance=6*np.sqrt(np.maximum(0,expected*(1-expected))/n)+2/n
            self.assertTrue(np.all(abs(actual-expected)<tolerance))
            moved.append(1-actual[lookup[(0,1,2)]])
            if rate==.5:
                _,_,again=self.fixtures(model,cases,rate=rate,dt=dt,batches=batches)
                self.assertEqual(raw,again)
        self.assertGreater(moved[1],moved[0])

    def simulate(self,name,extra=(),expect=True):
        out=self.root/name
        cmd=[str(SIM),'--springs','3','--chains','2','--kappa','2','--steps','2','--sample','1',
             '--seed','4317','--dt','.0001','--output',str(out)]+list(extra)
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=40)
        self.assertEqual(result.returncode==0,expect,result.stderr)
        return out,result

    def test_simulator_limits_replay_stress_and_renewed_force(self):
        files=('initial.csv','final.csv','samples.csv','parameters.txt','initial_bonds.csv','bond_statistics.csv')
        for z,rate in ((0,0),(0,10000),(3,0),(3,10000)):
            flags=['--hop-rate',str(rate),'--slip-count',str(z)]+(['--slip-ms2','2.4'] if z else [])
            base,_=self.simulate(f'base-{z}-{rate}',flags)
            zero,_=self.simulate(f'zero-{z}-{rate}',flags+['--end-renewal','0'])
            for name in files:self.assertEqual((base/name).read_bytes(),(zero/name).read_bytes())
            if not z or rate==0:
                inactive,_=self.simulate(f'inactive-{z}-{rate}',flags+['--end-renewal','1'])
                for name in files:self.assertEqual((base/name).read_bytes(),(inactive/name).read_bytes())
        flags=['--slip-count','3','--slip-ms2','2.4','--hop-rate','200000']
        outputs={}
        for steps in (1,2):
            for enabled in (0,1):
                out,_=self.simulate(f'force-{steps}-{enabled}',flags+['--steps',str(steps),'--end-renewal',str(enabled)])
                outputs[steps,enabled]=out
        def records(path):
            with path.open() as f:return list(csv.DictReader(f))
        def coords(out):return np.array([[float(r[k]) for k in ('x','y','z')] for r in records(out/'final.csv')])
        self.assertEqual((outputs[1,0]/'final.csv').read_bytes(),(outputs[1,1]/'final.csv').read_bytes())
        r1=coords(outputs[1,0]);forces=[];meta=json.loads((outputs[1,0]/'metadata.json').read_text())
        for enabled in (0,1):
            force=np.zeros_like(r1)
            for row in records(outputs[1,enabled]/'slip_springs_final.csv'):
                i=int(row['chain'])*4+int(row['bead']);anchor=np.array([float(row[k]) for k in ('ax','ay','az')])
                force[i]=-meta['slip_effective_stiffness']*(r1[i]-anchor)
            forces.append(force)
        expected=meta['effective_mobility_step']*(forces[1]-forces[0])
        self.assertGreater(np.max(abs(expected)),1e-6)
        np.testing.assert_allclose(coords(outputs[2,1])-coords(outputs[2,0]),expected,rtol=0,
                                   atol=5e-7 if meta['precision_bits']==32 else 3e-15)
        active=outputs[2,1];replay,_=self.simulate('replay',flags+['--end-renewal','1'])
        for name in files+('slip_springs_final.csv','hopping_metadata.json'):
            self.assertEqual((active/name).read_bytes(),(replay/name).read_bytes())
        stat=json.loads((active/'hopping_metadata.json').read_text())
        self.assertTrue(stat['end_renewal']);self.assertGreater(stat['renewal_accepted'],0)
        self.assertEqual(stat['renewal_proposed'],stat['outward_proposals'])
        self.assertEqual(stat['renewal_proposed'],stat['renewal_accepted']+stat['renewal_occupied_rejected'])
        self.assertEqual(stat['renewal_accepted'],stat['renewal_same_chain']+stat['renewal_cross_chain'])
        for mode in ('diagnostic','stream','every-step'):
            self.simulate('stress-'+mode,flags+['--end-renewal','1','--stress-mode',mode],expect=False)
        for value in ('2','-1','nan'):
            out,_=self.simulate('invalid-'+value,['--end-renewal',value],expect=False)
            self.assertFalse(out.exists())

if __name__=='__main__':unittest.main(verbosity=2)
