#!/usr/bin/env python3
"""Independent finite-rest-length equilibrium reference for Stage 4A.4.

Samples are exact independent chains from ``semiflexible_reference``; no
integrator, GPU code, or time-step is involved.  Reported standard errors use
chains (not bonds or overlapping time origins) as statistical clusters.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain


def summary(values):
    values = np.asarray(values, dtype=float)
    return {'mean': float(values.mean()),
            'se': float(values.std(ddof=1) / math.sqrt(len(values)))}


def reference(springs, kappa, chains, seed, bins=32, chunk=256):
    model = Chain.homogeneous(springs, b0=1., kb=30., kappa=kappa)
    rng = np.random.default_rng(seed)
    limit = 1. + 8. / math.sqrt(30.)
    all_values = {key: [] for key in ('mean_r', 'mean_r2', 're2', 'rg2',
                                      'end_to_end', 'stretch_energy', 'bend_energy')}
    tangent = {str(s): [] for s in range(1, min(4, springs - 1) + 1)}
    histograms = []
    angle_cosines = []
    bond_variances = []
    for start in range(0, chains, chunk):
        positions = model.sample(min(chunk, chains-start), rng)
        bonds = np.diff(positions, axis=1)
        lengths = np.linalg.norm(bonds, axis=2)
        unit = bonds / lengths[..., None]
        ee = positions[:, -1] - positions[:, 0]
        centered = positions - positions.mean(axis=1, keepdims=True)
        stretch = .5 * 30. * np.square(lengths - 1.).sum(axis=1)
        bend = (kappa * (1. - (unit[:, :-1] * unit[:, 1:]).sum(axis=2))).sum(axis=1) if springs > 1 else np.zeros(len(positions))
        values = {'mean_r': lengths.mean(axis=1), 'mean_r2': np.square(lengths).mean(axis=1),
                  're2': np.square(ee).sum(axis=1), 'rg2': np.square(centered).sum(axis=(1, 2))/(springs+1),
                  'end_to_end': np.linalg.norm(ee, axis=1), 'stretch_energy': stretch, 'bend_energy': bend}
        for key, value in values.items(): all_values[key].append(value)
        bond_variances.append(lengths.var(axis=1, ddof=1))
        for s in range(1, min(4, springs-1)+1):
            tangent[str(s)].append((unit[:, :-s] * unit[:, s:]).sum(axis=2).mean(axis=1))
        histograms.append(np.array([np.histogram(row, bins=bins, range=(0, limit))[0] for row in lengths]))
        if springs > 1: angle_cosines.append((unit[:, :-1] * unit[:, 1:]).sum(axis=2).mean(axis=1))
    all_values = {key: np.concatenate(value) for key, value in all_values.items()}
    histograms = np.concatenate(histograms)
    # A histogram probability for each chain retains the independent-chain SE.
    probabilities = histograms / springs
    result = {'method': 'exact-independent-equilibrium-sampling', 'chains': chains, 'seed': seed,
              'springs': springs, 'kappa': kappa, 'kbt': 1., 'kb': 30., 'b0': 1.,
              'histogram': {'maximum': limit, 'bins': bins,
                            'probability': probabilities.mean(axis=0).tolist(),
                            'se': (probabilities.std(axis=0, ddof=1)/math.sqrt(chains)).tolist()},
              'observables': {key: summary(value) for key, value in all_values.items()},
              'orientation_correlation': {key: summary(np.concatenate(value)) for key, value in tangent.items()},
              'local_angle_cosine': summary(np.concatenate(angle_cosines)) if angle_cosines else None}
    # ddof=1 makes each independent chain an unbiased estimator of the
    # homogeneous bond-length variance; it is not an origin count.
    result['observables']['bond_variance'] = summary(np.concatenate(bond_variances))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--springs', type=int, required=True)
    parser.add_argument('--kappa', type=float, required=True)
    parser.add_argument('--chains', type=int, default=65536)
    parser.add_argument('--seed', type=int, default=440401)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): parser.error('refusing to overwrite report')
    if args.springs < 2 or args.chains < 2: parser.error('need at least two chains and two springs')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(reference(args.springs, args.kappa, args.chains, args.seed), indent=2, sort_keys=True)+'\n')
    print(args.report)


if __name__ == '__main__': main()
