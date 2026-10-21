"""Bounded Stage C scientific gates, fixed before stochastic execution."""
from pathlib import Path
import math
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from slip_renewal_reference import Canonical,hypergeometric


class RenewalReference(unittest.TestCase):
    def test_pointwise_detailed_balance_same_and_cross_chain(self):
        model = Canonical([[.7*b+2*c,.2*b*b-c,.3*c] for c in range(3) for b in range(3)],3)
        sites = (0,1,5,7)
        anchors = model.r[list(sites)]+np.array([[.2,.4,-.8],[1,0,.3],[-1,.5,.4],[.3,.5,1]])
        rate = 2.7
        for j in (0,2):
            for destination in model.ends:
                replacement = model.r[destination]+[1.7,-.2,.9]
                after,new,result = model.renewal(sites,anchors,j,destination,replacement)
                if destination in sites:
                    self.assertEqual(result,5);self.assertEqual(after,sites)
                    np.testing.assert_array_equal(new,anchors)
                    continue
                self.assertEqual(result,4)
                reverse,old,_ = model.renewal(after,new,j,sites[j],anchors[j])
                self.assertEqual(reverse,sites);np.testing.assert_array_equal(old,anchors)
                log_forward = math.log(rate/(4*model.chains))+model.log_g(replacement,destination)
                log_reverse = math.log(rate/(4*model.chains))+model.log_g(anchors[j],sites[j])
                self.assertAlmostEqual(model.log_density(sites,anchors)+log_forward,
                                       model.log_density(after,new)+log_reverse,places=12)

    def test_exact_coincident_coordinate_generators_and_populations(self):
        for m in (2,3):
            model = Canonical(np.zeros((3*m,3)),m)
            states,q = model.integrated_generator(3,1.)
            self.assertEqual(len(states),math.comb(3*m,3))
            np.testing.assert_allclose(q,q.T,atol=1e-15)
            np.testing.assert_allclose(q.sum(axis=1),0,atol=1e-15)
            pi = np.full(len(states),1/len(states))
            np.testing.assert_allclose(pi@q,0,atol=1e-15)
            self.assertTrue(np.any(q>0))
            # Off-diagonal symmetry explicitly supplies reverse connections.
            self.assertTrue(np.array_equal(q>0,q.T>0))
            pop = np.bincount([sum(s<m for s in state) for state in states],minlength=m+1)/len(states)
            np.testing.assert_allclose(pop,hypergeometric(3,m,3),atol=1e-15)
            _,fast = model.integrated_generator(3,4.)
            np.testing.assert_allclose(fast,4*q,atol=1e-15)
            with self.assertRaises(ValueError):Canonical(np.arange(27).reshape(9,3),3).integrated_generator(3,1)

    def test_source_occupied_and_opposite_end_one_bond_cases(self):
        model = Canonical(np.zeros((4,3)),2)
        anchors = np.array([[.1,.2,.3]])
        sites,new,result = model.renewal((0,),anchors,0,0,[100,0,0])
        self.assertEqual((sites,result),((0,),5));np.testing.assert_array_equal(new,anchors)
        sites,new,result = model.renewal((0,),anchors,0,1,[100,0,0])
        self.assertEqual((sites,result),((1,),4))  # large uphill energy still permitted
        self.assertEqual(new[0,0],100)
        sites,new,result = model.renewal((0,1),np.zeros((2,3)),0,1,[1,2,3])
        self.assertEqual((sites,result),((0,1),5))

    def test_complete_cpu_process_preserves_annealed_measure(self):
        model = Canonical([[.6*b+2*c,.1*b*b-c,.2*c] for c in range(3) for b in range(3)],3)
        rng = np.random.default_rng(98127);n=4096;count=3
        target = hypergeometric(3,3,count)
        for rate in (.5,4.):
            occupancy=[];population=[];extensions=[];renewals=[]
            for _ in range(n):
                sites,anchors = model.initial(count,rng)
                sites,anchors,_,renewed = model.batch(sites,anchors,rate,2.,rng)
                population.append(sum(s<3 for s in sites));renewals.append(renewed)
                occupancy.append([i in sites for i in range(9)])
                extensions.append(np.mean(np.sum((model.r[list(sites)]-anchors)**2,axis=1)))
            observed = np.bincount(population,minlength=4)/n
            self.assertTrue(np.all(abs(observed-target)<6*np.sqrt(target*(1-target)/n)))
            actual = np.mean(occupancy,axis=0)
            self.assertTrue(np.all(abs(actual-count/9)<6*math.sqrt((count/9)*(1-count/9)/n)))
            self.assertLess(abs(np.mean(extensions)-model.ms2),6*np.std(extensions,ddof=1)/math.sqrt(n))
            expected_renewals = count*rate*2*(1/3)*(5/6)*(6/8)
            self.assertLess(abs(np.mean(renewals)-expected_renewals),6*np.std(renewals,ddof=1)/math.sqrt(n))
            print(f'CPU rate={rate} population={observed.tolist()} ms_extension={np.mean(extensions):.6g}')

if __name__=='__main__':unittest.main(verbosity=2)
