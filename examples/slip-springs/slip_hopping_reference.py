"""Independent CPU E1 hopping reference; no CUDA/production hopping dependency.

States contain stable spring IDs in initial contour order. Chain populations and
anchor identities are fixed; outward events are null events, never renewal.
"""
import itertools
import math
import operator
import numpy as np


class Hopping:
    def __init__(self, positions, anchors, sites, beads_per_chain, stiffness, kbt=1):
        self.r = np.asarray(positions, dtype=float)
        self.a = np.asarray(anchors, dtype=float)
        self.initial = tuple(sites)
        self.m = operator.index(beads_per_chain)
        self.k = float(stiffness)
        self.kbt = float(kbt)
        if (self.m < 2 or self.r.ndim != 2 or self.r.shape[1] != 3 or
                len(self.r) % self.m or self.a.shape != (len(sites), 3) or
                not np.all(np.isfinite(self.r)) or not np.all(np.isfinite(self.a)) or
                not math.isfinite(self.k) or self.k <= 0 or
                not math.isfinite(self.kbt) or self.kbt <= 0):
            raise ValueError('invalid hopping reference parameters')
        if any(not isinstance(s, (int, np.integer)) or s < 0 or s >= len(self.r) for s in sites):
            raise ValueError('invalid site')
        self.chains = tuple(s // self.m for s in sites)
        self.check(self.initial)

    def check(self, state):
        if len(state) != len(self.initial) or len(set(state)) != len(state):
            raise ValueError('population or exclusion violation')
        for j, s in enumerate(state):
            if s < 0 or s >= len(self.r) or s // self.m != self.chains[j]:
                raise ValueError('chain population violation')
            for i in range(j):
                if self.chains[i] == self.chains[j] and state[i] >= s:
                    raise ValueError('order violation')

    def energy(self, state):
        self.check(state)
        return .5 * self.k * np.sum((self.r[list(state)] - self.a)**2)

    def attempt(self, state, spring, direction, uniform):
        self.check(state)
        if not 0 <= spring < len(state) or direction not in (-1, 1) or not 0 < uniform < 1:
            raise ValueError('invalid proposal')
        dest = state[spring] + direction
        if dest // self.m != self.chains[spring]:
            return state, 1  # boundary
        if dest in state:
            return state, 2  # exclusion; vacant adjacent moves cannot overtake
        proposed = tuple(dest if i == spring else s for i, s in enumerate(state))
        self.check(proposed)
        change = (self.energy(proposed) - self.energy(state)) / self.kbt
        if change <= 0 or uniform < math.exp(-change):
            return proposed, 0
        return state, 3

    def states(self):
        groups = [([j for j, c in enumerate(self.chains) if c == chain], chain)
                  for chain in sorted(set(self.chains))]
        choices = [list(itertools.combinations(range(c*self.m, (c+1)*self.m), len(ids)))
                   for ids, c in groups]
        result = []
        for combination in itertools.product(*choices):
            state = [None] * len(self.initial)
            for (ids, _), values in zip(groups, combination):
                for j, s in zip(ids, values):
                    state[j] = s
            result.append(tuple(state))
        return result

    def equilibrium(self):
        states = self.states()
        energy = np.array([self.energy(s)/self.kbt for s in states])
        weights = np.exp(-(energy-energy.min()))
        return states, weights/weights.sum()

    def generator(self, rate):
        if not math.isfinite(rate) or rate < 0:
            raise ValueError('invalid rate')
        states, _ = self.equilibrium()
        lookup = {s: i for i, s in enumerate(states)}
        q = np.zeros((len(states), len(states)))
        for i, state in enumerate(states):
            for j in range(len(state)):
                for direction in (-1, 1):
                    dest = state[j]+direction
                    if dest // self.m != self.chains[j] or dest in state:
                        continue
                    proposed = tuple(dest if p == j else s for p, s in enumerate(state))
                    self.check(proposed)
                    q[i, lookup[proposed]] += rate/2 * math.exp(-max(0.,
                        (self.energy(proposed)-self.energy(state))/self.kbt))
            q[i, i] = -q[i].sum()
        return q

    def transition(self, rate, time):
        _, pi = self.equilibrium()
        root = np.sqrt(pi)
        symmetric = root[:, None]*self.generator(rate)/root[None, :]
        values, vectors = np.linalg.eigh(symmetric)
        return ((vectors*np.exp(time*values)) @ vectors.T)*root[None, :]/root[:, None]

    def batch(self, state, rate, dt, rng):
        k = rng.poisson(len(state)*rate*dt)
        outcomes = [0, 0, 0, 0]
        for _ in range(k):
            j = int(rng.integers(len(state)))
            direction = 1 if rng.integers(2) else -1
            u = 1-rng.random()  # the zero endpoint has probability below practical tests
            if u == 1:
                u = np.nextafter(1., 0.)
            state, result = self.attempt(state, j, direction, u)
            outcomes[result] += 1
        return state, k, outcomes
