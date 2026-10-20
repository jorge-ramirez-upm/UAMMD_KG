#!/usr/bin/env python3
"""CPU-only local-curvature timestep heuristic; not a convergence certificate."""
import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

from semiflexible_reference import Chain


def hessian(chain, positions):
    """Cartesian potential-energy Hessian for the unchanged open-chain model."""
    q = chain._bonds(positions)
    lengths = np.hypot.reduce(q, axis=1)
    if np.any(lengths == 0) or not np.all(np.isfinite(lengths)):
        raise ValueError('Hessian requires nonzero finite bonds')
    unit = q/lengths[:, None]
    eye = np.eye(3)
    result = np.zeros((3*(chain.n+1), 3*(chain.n+1)))

    def add(a, b, block):
        # q_a = r_(a+1)-r_a; scatter D_a^T block D_b, including free ends.
        for i, si in ((a, -1), (a+1, 1)):
            for j, sj in ((b, -1), (b+1, 1)):
                result[3*i:3*i+3, 3*j:3*j+3] += si*sj*block

    for i, (length, u) in enumerate(zip(lengths, unit)):
        ratio = chain.b0[i]/length
        add(i, i, chain.kb[i]*((1-ratio)*eye + ratio*np.outer(u, u)))
    for i, k in chain.active_angles or ():
        a, b = i-1, i
        u, v = unit[a], unit[b]
        cosine = u@v
        pu, pv = eye-np.outer(u, u), eye-np.outer(v, v)
        w, z = v-cosine*u, u-cosine*v
        aa = k/lengths[a]**2*(np.outer(w, u)+np.outer(u, w)+cosine*pu)
        bb = k/lengths[b]**2*(np.outer(z, v)+np.outer(v, z)+cosine*pv)
        ab = -k/(lengths[a]*lengths[b])*(pu@pv)
        add(a, a, aa)
        add(b, b, bb)
        add(a, b, ab)
        add(b, a, ab.T)
    if not np.all(np.isfinite(result)):
        raise ValueError('Hessian outside double precision range')
    return result


def internal_basis(n):
    """Orthonormal complement of the three rigid translations, no pinning."""
    incidence = np.zeros((n, n+1))
    incidence[np.arange(n), np.arange(n)] = -1
    incidence[np.arange(n), np.arange(n)+1] = 1
    contrasts, _ = np.linalg.qr(incidence.T, mode='reduced')
    return np.kron(contrasts, np.eye(3))


def spectrum(matrix, basis):
    dimension = matrix.shape[0]
    scale = max(1., float(np.linalg.norm(matrix, ord=np.inf)))
    tolerance = 128*np.finfo(float).eps*dimension*scale
    translations = np.tile(np.eye(3), (dimension//3, 1))/math.sqrt(dimension//3)
    residual = float(np.linalg.norm(matrix@translations, ord=2))
    if residual > tolerance or np.max(np.abs(matrix-matrix.T)) > tolerance:
        raise ValueError('Hessian translation/symmetry residual exceeds numerical tolerance')
    eigenvalues = np.linalg.eigvalsh(basis.T@matrix@basis)
    if not np.all(np.isfinite(eigenvalues)):
        raise ValueError('nonfinite Hessian spectrum')
    positive = eigenvalues[eigenvalues > tolerance]
    if not len(positive): raise ValueError('no resolved positive Hessian eigenvalue')
    resolved = np.abs(eigenvalues[np.abs(eigenvalues) > tolerance])
    condition = float(resolved.max()/resolved.min())
    return dict(lambda_max=float(positive[-1]), minimum_eigenvalue=float(eigenvalues[0]),
                negative_eigenvalues=eigenvalues[eigenvalues < -tolerance].tolist(),
                numerical_zero_modes=int(np.count_nonzero(np.abs(eigenvalues) <= tolerance)),
                eigenvalue_tolerance=tolerance, translation_residual=residual,
                resolved_absolute_condition=condition)


def distribution(values):
    return dict(zip(('median', 'q95', 'q99', 'maximum_observed'),
                    map(float, np.quantile(values, [.5, .95, .99, 1.], method='linear'))))


def preselect(n=8, kb=30., kappa=10., b0=1., zeta=1., configurations=100, seed=433201, c=.05):
    started = time.perf_counter()
    for name, value in dict(kb=kb, b0=b0, zeta=zeta, c=c).items():
        if not math.isfinite(value) or value <= 0: raise ValueError(f'{name} must be finite and positive')
    if configurations < 1 or int(configurations) != configurations:
        raise ValueError('configurations must be a positive integer')
    chain = Chain.homogeneous(n, kb=kb, kappa=kappa, b0=b0)
    harmonic_curvature = 4*kb + 16*kappa/b0**2
    if not math.isfinite(harmonic_curvature) or harmonic_curvature <= 0:
        raise ValueError('harmonic estimate outside double precision range')
    samples = chain.sample(configurations, np.random.default_rng(seed), kbt=1.)
    basis = internal_basis(n)
    records = []
    short, ill_conditioned = [], []
    for index, positions in enumerate(samples):
        item = spectrum(hessian(chain, positions), basis)
        lengths = np.hypot.reduce(np.diff(positions, axis=0), axis=1)
        item['minimum_bond_length'] = float(lengths.min())
        item['minimum_bond_over_b0'] = float(lengths.min()/b0)
        if item['minimum_bond_over_b0'] < .1: short.append(index)
        if item['resolved_absolute_condition'] > 1/math.sqrt(np.finfo(float).eps):
            ill_conditioned.append(index)
        records.append(item)
    maxima = distribution([item['lambda_max'] for item in records])
    dt = c*zeta/maxima['q99']
    harmonic_tau = zeta/harmonic_curvature
    if not all(math.isfinite(x) and x > 0 for x in (dt, harmonic_tau, c*harmonic_tau)):
        raise ValueError('timestep estimate outside double precision range')
    return dict(schema='semiflexible-timestep-preselector-v1',
                parameters=dict(N=n, kb=kb, kappa=kappa, b0=b0, zeta=zeta, kbt=1.,
                                configurations=configurations, seed=seed, c=c),
                method='exact equilibrium samples; analytic potential Hessian; float64 NumPy eigvalsh',
                harmonic_approximation=dict(curvature=harmonic_curvature, tau_est=harmonic_tau,
                                            dt_est=c*harmonic_tau, rigorous_bound=False),
                lambda_max_distribution=maxima, dt_suggested=dt,
                diagnostics=dict(configurations_with_negative_curvature=sum(bool(x['negative_eigenvalues']) for x in records),
                                 most_negative_eigenvalue=min(x['minimum_eigenvalue'] for x in records),
                                 minimum_observed_bond=min(x['minimum_bond_length'] for x in records),
                                 very_short_bond_indices=short, very_short_bond_definition='min bond / b0 < 0.1 (diagnostic only)',
                                 poorly_conditioned_indices=ill_conditioned,
                                 conditioning_definition='max(abs(lambda))/min(abs(lambda)) for |lambda| > tolerance; flag > 1/sqrt(eps)',
                                 observed_max_mode_dt_over_zeta=dt*maxima['maximum_observed']/zeta,
                                 coefficient_at_or_above_linear_em_stability_limit=c >= 2),
                numerical_modes=dict(translations_removed=3, rotations_removed=0,
                                     tolerance='128 * float64_eps * 3*(N+1) * max(1, ||H||_inf)',
                                     internal_zero_modes='retained; counted within +/- tolerance, excluded only from resolved condition ratio'),
                limitations=['H = d2U/dr2 is the energy Hessian; decay matrix is H/zeta and drift Jacobian is -H/zeta.',
                             'Rotations at nonstationary configurations need not be Hessian zero modes; all internal modes are retained.',
                             'A small-ensemble Q99 is uncertain and may miss rare short-bond or high-curvature configurations.',
                             'Negative eigenvalues are local downhill curvatures, not silently classified as stable modes.',
                             'Neither estimate guarantees nonlinear EM stability or accuracy; convergence thresholds remain unchanged.',
                             'Fastest local relaxation is not the global polymer relaxation time; c is not fitted to Stage 4A.4.'],
                configurations=records, elapsed_seconds=time.perf_counter()-started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--N', type=int, default=8, help='springs (N+1 free beads)')
    for name, default in (('kb', 30.), ('kappa', 10.), ('b0', 1.), ('zeta', 1.), ('c', .05)):
        parser.add_argument('--'+name, type=float, default=default)
    parser.add_argument('--configurations', type=int, default=100)
    parser.add_argument('--seed', type=int, default=433201)
    parser.add_argument('--report', type=Path, help='new JSON file; default stdout')
    args = parser.parse_args()
    if args.report and args.report.exists(): parser.error('refusing to overwrite report')
    try: result = preselect(args.N, args.kb, args.kappa, args.b0, args.zeta, args.configurations, args.seed, args.c)
    except (ValueError, OverflowError, np.linalg.LinAlgError) as error: parser.error(str(error))
    encoded = json.dumps(result, indent=2, allow_nan=False)+'\n'
    if args.report:
        with args.report.open('x') as stream: stream.write(encoded)
    else: print(encoded, end='')


if __name__ == '__main__': main()
