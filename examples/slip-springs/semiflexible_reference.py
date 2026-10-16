"""Double precision open-chain reference; no dynamics or UAMMD dependency.

b0/kb use bond indices 0..N-1. kappa uses bead indices 0..N,
with zero endpoints; only kappa[1:N] represents physical angles.
See STAGE4A1_REPORT.md for derivations, numerical limits and sampling proof.
"""

import math
import operator

import numpy as np
from numpy.polynomial.legendre import leggauss


def _positive(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def langevin(x):
    """L(x)=coth(x)-1/x for finite x >= 0, including its limit at zero."""
    x = float(x)
    if not math.isfinite(x) or x < 0:
        raise ValueError("x must be finite and nonnegative")
    if x < 0.05:
        z = x * x
        return x * (1/3 + z * (-1/45 + z * (2/945 + z * (-1/4725 + z * 2/93555))))
    if x > 350:
        return 1 - 1/x
    return 1 + 2/math.expm1(2*x) - 1/x


def radial_moments(b0, kb, kbt=1.0, order=128):
    """Return <r>, <r^2> by Gaussian quadrature of the radial density.

    Integrate y=(r-b0)/sigma over [-min(b0/sigma,12),12]. The omitted
    Gaussian tail is negligible at ordinary double precision (see report).
    """
    b0 = float(b0)
    if not math.isfinite(b0) or b0 < 0:
        raise ValueError("b0 must be finite and nonnegative")
    sigma = math.sqrt(_positive(kbt, "kbt") / _positive(kb, "kb"))
    if not math.isfinite(sigma) or sigma == 0:
        raise ValueError("thermal length outside double precision range")
    a = b0 / sigma
    if not math.isfinite(a):
        raise ValueError("b0/sigma outside double precision range")
    order = operator.index(order)
    if order < 16:
        raise ValueError("quadrature order must be at least 16")
    nodes, weights = leggauss(order)
    lo, hi = -min(a, 12.0), 12.0
    y = (lo + hi)/2 + (hi - lo)/2 * nodes
    r = b0 + sigma*y
    scaled_r = 1 + y/a if a > 1 else a + y
    w = weights * scaled_r**2 * np.exp(-y*y/2)
    result = np.array([np.dot(w, r), np.dot(w, r*r)]) / w.sum()
    if not np.all(np.isfinite(result)):
        raise ValueError("radial moments outside double precision range")
    return tuple(result)


class Chain:
    """Immutable parameters; kappa endpoints must be zero, kb strictly positive.

    Strictly positive kb ensures a normalizable radial equilibrium measure.
    b0=0 is allowed and has a smooth stretching force at a collapsed bond.
    """

    def __init__(self, b0, kb, kappa):
        arrays = [np.array(v, dtype=np.float64, copy=True) for v in (b0, kb, kappa)]
        self.b0, self.kb, self.kappa = arrays
        if any(v.ndim != 1 or not np.all(np.isfinite(v)) for v in arrays):
            raise ValueError("parameters must be finite one-dimensional arrays")
        self.n = len(self.b0)
        if self.n < 1 or self.kb.shape != (self.n,) or self.kappa.shape != (self.n+1,):
            raise ValueError("require N>=1, N b0/kb entries and N+1 bead-indexed kappa entries")
        if (np.any(self.b0 < 0) or np.any(self.kb <= 0) or np.any(self.kappa < 0)
                or self.kappa[0] != 0 or self.kappa[-1] != 0):
            raise ValueError("require b0>=0, kb>0, kappa>=0 and zero kappa endpoints")
        for v in arrays:
            v.flags.writeable = False
        # No bending geometry/cache/buffer exists for the flexible path.
        self.active_angles = tuple((i, float(k)) for i, k in enumerate(self.kappa) if k != 0) or None

    @classmethod
    def homogeneous(cls, n, b0=1.0, kb=30.0, kappa=0.0):
        n = operator.index(n)
        if n < 1:
            raise ValueError("n must be positive")
        kappa = float(kappa)
        if not math.isfinite(kappa) or kappa < 0:
            raise ValueError("kappa must be finite and nonnegative")
        bends = np.full(n+1, kappa)
        bends[[0, -1]] = 0
        return cls(np.full(n, b0), np.full(n, kb), bends)

    def _bonds(self, positions):
        r = np.asarray(positions, dtype=np.float64)
        if r.shape != (self.n+1, 3) or not np.all(np.isfinite(r)):
            raise ValueError("positions must be finite with shape (N+1,3)")
        q = np.diff(r, axis=0)
        if not np.all(np.isfinite(q)):
            raise ValueError("bond displacement overflow")
        return q

    def _stretch(self, q):
        lengths = np.hypot.reduce(q, axis=1)
        if not np.all(np.isfinite(lengths)):
            raise ValueError("bond length overflow")
        if np.any((lengths == 0) & (self.b0 != 0)):
            raise ValueError("stretch force undefined at zero length with nonzero b0")
        factor = self.kb * (1 - np.divide(self.b0, lengths, out=np.zeros_like(lengths), where=lengths != 0))
        gradient = factor[:, None] * q
        forces = np.zeros((self.n+1, 3))
        forces[:-1] += gradient
        forces[1:] -= gradient
        energy = 0.5 * np.dot(self.kb, (lengths-self.b0)**2)
        if not np.isfinite(energy) or not np.all(np.isfinite(forces)):
            raise ValueError("stretch energy/force outside double precision range")
        return float(energy), forces

    def _bend(self, q):
        forces = np.zeros((self.n+1, 3))
        energy = 0.0
        for i, k in self.active_angles or ():
            a, b = q[i-1], q[i]
            la, lb = np.hypot.reduce(a), np.hypot.reduce(b)
            if not (0 < la < np.inf and 0 < lb < np.inf):
                raise ValueError("active bending angle requires nonzero finite bond lengths")
            u, v = a/la, b/lb
            c = np.dot(u, v)
            # Equivalent to k*(1-c), avoiding cancellation near straight chains.
            energy += 0.5*k*np.dot(u-v, u-v)
            da = -k/la * (v-c*u)
            db = -k/lb * (u-c*v)
            forces[i-1] += da
            forces[i] += db-da
            forces[i+1] -= db
        if not np.isfinite(energy) or not np.all(np.isfinite(forces)):
            raise ValueError("bend energy/force outside double precision range")
        return float(energy), forces

    def stretch_energy_forces(self, positions):
        return self._stretch(self._bonds(positions))

    def bend_energy_forces(self, positions):
        return self._bend(self._bonds(positions))

    def energy_forces(self, positions):
        q = self._bonds(positions)
        energy, forces = self._stretch(q)
        if self.active_angles is not None:
            eb, fb = self._bend(q)
            energy += eb
            forces += fb
        return energy, forces

    def equilibrium_predictions(self, kbt=1.0):
        kbt = _positive(kbt, "kbt")
        moments = np.array([radial_moments(b, k, kbt) for b, k in zip(self.b0, self.kb)])
        rho = np.array([langevin(k/kbt) for k in self.kappa[1:-1]])
        re2 = moments[:, 1].sum()
        for i in range(self.n):
            correlation = 1.0
            for j in range(i+1, self.n):
                correlation *= rho[j-1]
                re2 += 2*moments[i, 0]*moments[j, 0]*correlation
        return {"mean_r": moments[:, 0], "mean_r2": moments[:, 1], "re2": float(re2)}

    def sample(self, count, rng, kbt=1.0):
        """Independent equilibrium chains, anchored at bead zero; shape (count,N+1,3).

        rng is a numpy.random.Generator. No time step or equilibration is used.
        Length generation precedes orientation draws, enabling coupled tests.
        """
        count = operator.index(count)
        if count < 1:
            raise ValueError("count must be positive")
        kbt = _positive(kbt, "kbt")
        lengths = np.empty((count, self.n))
        for i in range(self.n):
            sigma = math.sqrt(kbt/self.kb[i])
            a = self.b0[i]/sigma if sigma > 0 else math.inf
            if not math.isfinite(a):
                raise ValueError("thermal length outside double precision range")
            mode = a/2 + math.hypot(a, math.sqrt(8))/2
            pending = np.arange(count)
            for _ in range(10000):
                delta = rng.normal(size=len(pending))
                t = mode + delta
                valid = t > 0
                log_accept = np.full(len(t), -np.inf)
                z = delta[valid]/mode
                log_accept[valid] = 2*(np.log1p(z)-z)
                accepted = np.log(rng.random(len(t))) < log_accept
                lengths[pending[accepted], i] = sigma*t[accepted]
                pending = pending[~accepted]
                if not len(pending):
                    break
            else:
                raise RuntimeError("radial rejection sampler exceeded bounded retry limit")
        if not np.all(np.isfinite(lengths)) or np.any(lengths <= 0):
            raise ValueError("sampled lengths outside double precision range")
        q = np.empty((count, self.n, 3))
        directions = rng.normal(size=(count, 3))
        directions /= np.linalg.norm(directions, axis=1)[:, None]
        q[:, 0] = lengths[:, 0, None]*directions
        for i in range(1, self.n):
            x = self.kappa[i]/kbt
            if not math.isfinite(x):
                raise ValueError("kappa/kbt outside double precision range")
            if x == 0:
                directions = rng.normal(size=(count, 3))
                directions /= np.linalg.norm(directions, axis=1)[:, None]
                q[:, i] = lengths[:, i, None]*directions
                continue
            h = rng.random(count)
            if x < 0.05:
                c = 1 + np.log1p((1-h)*np.expm1(-2*x))/x
            elif x > 350:
                with np.errstate(divide="ignore"):
                    c = 1 + np.log(h)/x
            else:
                with np.errstate(divide="ignore"):
                    c = 1 + np.logaddexp(np.log(h), np.log1p(-h)-2*x)/x
            c = np.clip(c, -1, 1)  # Roundoff only; no angular regularization.
            axis = np.zeros_like(directions)
            axis[np.arange(count), np.argmin(np.abs(directions), axis=1)] = 1
            e1 = np.cross(directions, axis)
            e1 /= np.linalg.norm(e1, axis=1)[:, None]
            e2 = np.cross(directions, e1)
            phi = rng.uniform(0, 2*np.pi, count)
            directions = (c[:, None]*directions + np.sqrt((1-c)*(1+c))[:, None]
                          * (np.cos(phi)[:, None]*e1 + np.sin(phi)[:, None]*e2))
            q[:, i] = lengths[:, i, None]*directions
        result = np.zeros((count, self.n+1, 3))
        result[:, 1:] = np.cumsum(q, axis=1)
        if not np.all(np.isfinite(result)):
            raise ValueError("sampled positions outside double precision range")
        return result
