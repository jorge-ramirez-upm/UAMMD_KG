"""Positive affine-energy derivative virials W=V*sigma, always float64.

Reuses the unchanged Stage 4A.1 Chain parameters and coordinate validation.
No volume, density, dynamics or correlation estimator is defined here.
See STAGE4A3A_REPORT.md for derivations and explicit kBT normalization.
"""
import math

import numpy as np


SYMMETRIC_ORDER = ('xx', 'yy', 'zz', 'xy', 'xz', 'yz')
SHEAR_ORDER = ('xy', 'xz', 'yz')
NORMAL_ORDER = ('xx-yy', 'xx-zz', 'yy-zz')
DEVIATORIC_ORDER = SHEAR_ORDER + NORMAL_ORDER


def _finite(tensor):
    if not np.all(np.isfinite(tensor)):
        raise ValueError('virial outside double precision range')
    return tensor


def components(tensor):
    """Extract raw entries, without symmetrizing or projecting out the trace.

    symmetric: xx,yy,zz,xy,xz,yz (Rouse observation ordering).
    shears: xy,xz,yz; normal_differences: xx-yy,xx-zz,yy-zz.
    Concatenating the latter two gives the Rouse six RAW correlator channels.
    The caller must check symmetry on the full physical tensor separately.
    """
    w = np.asarray(tensor, dtype=np.float64)
    if w.shape != (3, 3):
        raise ValueError('virial must have shape (3,3)')
    _finite(w)
    symmetric = np.array([w[0, 0], w[1, 1], w[2, 2], w[0, 1], w[0, 2], w[1, 2]])
    normal = _finite(np.array([w[0, 0]-w[1, 1], w[0, 0]-w[2, 2], w[1, 1]-w[2, 2]]))
    return {'symmetric': symmetric, 'shears': symmetric[3:].copy(), 'normal_differences': normal}


def bending_angle_virial(a, b, kappa):
    """One angle's A outer a + B outer b, not a repaired/projected tensor.

    Zero kappa returns zero without orientation/length calculations; active
    angles require finite, nonzero bonds. a,b are forward consecutive bonds.
    """
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if a.shape != (3,) or b.shape != (3,) or not np.all(np.isfinite([a, b])):
        raise ValueError('angle bonds must be finite three-vectors')
    kappa = float(kappa)
    if not math.isfinite(kappa) or kappa < 0:
        raise ValueError('kappa must be finite and nonnegative')
    if kappa == 0:
        return np.zeros((3, 3))
    la, lb = np.hypot.reduce(a), np.hypot.reduce(b)
    if not (0 < la < np.inf and 0 < lb < np.inf):
        raise ValueError('active bending angle requires nonzero finite bond lengths')
    u, v = a/la, b/lb
    c = np.dot(u, v)
    # Mirror the energy/force reference numerical domain, even if W stays finite.
    _finite(0.5*kappa*np.dot(u-v, u-v))
    A, B = -kappa/la*(v-c*u), -kappa/lb*(u-c*v)
    if not np.all(np.isfinite([A, B])):
        raise ValueError('bending gradient outside double precision range')
    return _finite(np.outer(A, a) + np.outer(B, b))


def _bending(q, active_angles):
    result = np.zeros((3, 3))
    for i, k in active_angles:
        result += bending_angle_virial(q[i-1], q[i], k)
    return _finite(result)


def virials(chain, positions):
    """Return stretch, bend, total (3x3), plus total-tensor component arrays.

    chain is an unchanged semiflexible_reference.Chain with N bond-indexed
    b0/kb and N+1 bead-indexed kappa (zero endpoints). No normalization by V.
    Undefined stretch/angle gradients raise ValueError, as in Stage 4A.1.
    A zero bend tensor is a required output, not angular scratch/geometry.
    """
    q = chain._bonds(positions)
    lengths = np.hypot.reduce(q, axis=1)
    if not np.all(np.isfinite(lengths)):
        raise ValueError('bond length overflow')
    if np.any((lengths == 0) & (chain.b0 != 0)):
        raise ValueError('stretch gradient undefined at zero length with nonzero b0')
    _finite(0.5*np.dot(chain.kb, (lengths-chain.b0)**2))
    # Same Cartesian gradient and smooth zero-rest-length limit as Stage 4A.1.
    factor = chain.kb*(1-np.divide(chain.b0, lengths, out=np.zeros_like(lengths), where=lengths != 0))
    gradient = factor[:, None]*q
    if not np.all(np.isfinite(gradient)):
        raise ValueError('stretch gradient outside double precision range')
    stretch = _finite(gradient.T @ q)
    bend = np.zeros((3, 3)) if chain.active_angles is None else _bending(q, chain.active_angles)
    total = _finite(stretch+bend)
    return {'stretch': stretch, 'bend': bend, 'total': total, **components(total)}
