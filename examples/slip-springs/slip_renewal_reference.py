"""Independent CPU E1 jump process. No production CUDA or linked-list dependency.

Labeled stable slots give a constant Z! multiplicity versus the unordered E1
site measure. Sorting current sites reconstructs contour order after renewal.
"""
import itertools
import math
import operator
import numpy as np


class Canonical:
    def __init__(self, positions, beads_per_chain, ms2=2.4, kbt=1.):
        self.r = np.array(positions, dtype=float)
        self.m = operator.index(beads_per_chain)
        self.ms2, self.kbt = float(ms2), float(kbt)
        if (self.m < 2 or self.r.ndim != 2 or self.r.shape[1] != 3 or
                len(self.r) % self.m or not len(self.r) or not np.isfinite(self.r).all() or
                not math.isfinite(self.ms2) or self.ms2 <= 0 or not math.isfinite(self.kbt) or self.kbt <= 0):
            raise ValueError('invalid canonical model')
        self.chains = len(self.r)//self.m
        self.ends = tuple(c*self.m+b for c in range(self.chains) for b in (0,self.m-1))
        self.k = 3*self.kbt/self.ms2

    def check(self, sites, anchors):
        if len(set(sites)) != len(sites) or np.shape(anchors) != (len(sites),3):
            raise ValueError('population/occupancy/anchor mismatch')
        if any(not isinstance(s,(int,np.integer)) or not 0<=s<len(self.r) for s in sites):
            raise ValueError('invalid site')
        if not np.isfinite(anchors).all():raise ValueError('nonfinite anchor')

    def links(self, sites):
        previous, following = [-1]*len(sites),[-1]*len(sites)
        for c in range(self.chains):
            ids = sorted((j for j,s in enumerate(sites) if s//self.m==c),key=lambda j:sites[j])
            for p,j in enumerate(ids):
                if p:previous[j] = ids[p-1]
                if p+1<len(ids):following[j] = ids[p+1]
        return list(zip(previous,following))

    def log_g(self, anchor, site):
        return -1.5*math.log(2*math.pi*self.ms2/3)-1.5*np.sum((np.asarray(anchor)-self.r[site])**2)/self.ms2

    def log_density(self, sites, anchors):
        self.check(sites,anchors)
        return sum(self.log_g(a,s) for s,a in zip(sites,anchors))  # same combinatorial constant in each state

    def renewal(self, sites, anchors, j, destination, replacement):
        self.check(sites,anchors)
        if not 0<=j<len(sites) or sites[j] not in self.ends or destination not in self.ends:
            raise ValueError('renewal requires source/destination ends')
        if destination in sites:return tuple(sites),np.array(anchors,copy=True),5
        if np.shape(replacement)!=(3,) or not np.isfinite(replacement).all():
            raise ValueError('unrepresentable replacement')
        new_sites = tuple(destination if i==j else s for i,s in enumerate(sites))
        new_anchors = np.array(anchors,copy=True);new_anchors[j] = replacement
        self.check(new_sites,new_anchors)
        return new_sites,new_anchors,4

    def attempt(self, sites, anchors, j, direction, uniform, destination=None, replacement=None):
        self.check(sites,anchors)
        if not 0<=j<len(sites) or direction not in (-1,1) or not 0<uniform<1:
            raise ValueError('invalid proposal')
        source = sites[j];dest = source+direction
        if dest<0 or dest>=len(self.r) or dest//self.m!=source//self.m:
            return self.renewal(sites,anchors,j,destination,replacement)
        if dest in sites:return tuple(sites),np.array(anchors,copy=True),2
        old_energy = .5*self.k*np.sum((self.r[source]-anchors[j])**2)
        new_energy = .5*self.k*np.sum((self.r[dest]-anchors[j])**2)
        if uniform>=math.exp(-max(0.,(new_energy-old_energy)/self.kbt)):
            return tuple(sites),np.array(anchors,copy=True),3
        new_sites = tuple(dest if i==j else s for i,s in enumerate(sites))
        return new_sites,np.array(anchors,copy=True),0

    def initial(self, count, rng):
        sites = tuple(map(int,rng.choice(len(self.r),size=count,replace=False)))
        anchors = self.r[list(sites)]+math.sqrt(self.ms2/3)*rng.normal(size=(count,3))
        return sites,anchors

    def batch(self, sites, anchors, rate, dt, rng):
        k = rng.poisson(len(sites)*rate*dt)
        renewed = 0
        for _ in range(k):
            j = int(rng.integers(len(sites)));direction = 1 if rng.integers(2) else -1
            u = max(np.nextafter(0.,1.),rng.random())
            source = sites[j];dest = source+direction
            if dest<0 or dest>=len(self.r) or dest//self.m!=source//self.m:
                destination = int(rng.integers(self.chains))*self.m+(self.m-1 if rng.integers(2) else 0)
                replacement = None if destination in sites else self.r[destination]+math.sqrt(self.ms2/3)*rng.normal(size=3)
                sites,anchors,result = self.renewal(sites,anchors,j,destination,replacement)
                renewed += result==4
            else:sites,anchors,_ = self.attempt(sites,anchors,j,direction,u)
        return sites,anchors,k,renewed

    def integrated_generator(self, count, rate):
        """Exact occupancy quotient ONLY when all bead coordinates coincide.

        Then interior DeltaE=0 for every anchor; successful renewal samples
        the same site-independent Gaussian. Occupancy is a closed Markov chain.
        This is not an averaged generator for separated fixed bead positions.
        """
        if not np.all(self.r==self.r[0]):raise ValueError('coincident-coordinate quotient only')
        states = list(itertools.combinations(range(len(self.r)),count))
        lookup = {s:i for i,s in enumerate(states)}
        q = np.zeros((len(states),len(states)))
        for i,state in enumerate(states):
            for source in state:
                for direction in (-1,1):
                    dest = source+direction
                    outward = dest<0 or dest>=len(self.r) or dest//self.m!=source//self.m
                    proposals = [(y,rate/(4*self.chains)) for y in self.ends] if outward else [(dest,rate/2)]
                    for y,w in proposals:
                        if y in state:continue
                        proposed = tuple(sorted((set(state)-{source})|{y}))
                        q[i,lookup[proposed]] += w
            q[i,i] = -q[i].sum()
        return states,q


def hypergeometric(chains, beads, count):
    total = chains*beads
    return np.array([math.comb(beads,z)*math.comb(total-beads,count-z)/math.comb(total,count)
                     if 0<=count-z<=total-beads else 0 for z in range(beads+1)])
