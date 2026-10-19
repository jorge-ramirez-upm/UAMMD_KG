"""Bounded paired Gaussian-chain stress/multi-tau validation.

This is an isolated CPU fixture.  It generates the stationary linear Gaussian
EM mode process, forms the six prescribed deviatoric stress channels, and feeds
the identical observations to P=16,32,64 and 16x40 scalar multi-tau banks.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from multitau_estimator_audit import multi_tau  # noqa: E402


def modes(n):
    p = np.arange(1, n + 1)
    return 12.0 * np.sin(p * np.pi / (2.0 * (n + 1))) ** 2


def observations(n=8, frames=4096, chains=32, dt=2.5e-5, seed=433201):
    """Return identical six-channel stress observations for all hierarchies."""
    rng = np.random.default_rng(seed)
    lam = modes(n)
    a = 1.0 - lam * dt
    variance = 1.0 / (lam * (1.0 - lam * dt / 2.0))
    mode = np.empty((chains, n, 3), dtype=np.float64)
    mode[:] = rng.normal(size=mode.shape) * np.sqrt(variance)[None, :, None]
    out = np.empty((chains, frames, 6), dtype=np.float64)
    noise_scale = np.sqrt(variance * (1.0 - a * a))
    for t in range(frames):
        w = np.einsum('p,cpj,cpl->cjl', lam, mode, mode)
        out[:, t] = np.stack((w[:, 0, 1], w[:, 0, 2], w[:, 1, 2],
                              w[:, 0, 0] - w[:, 1, 1],
                              w[:, 0, 0] - w[:, 2, 2],
                              w[:, 1, 1] - w[:, 2, 2]), axis=1)
        if t + 1 < frames:
            mode = a[None, :, None] * mode + rng.normal(size=mode.shape) * noise_scale[None, :, None]
    return out, lam, a, variance


def h_values(channels):
    return channels[..., :3].sum(axis=-1) / 5.0 + channels[..., 3:].sum(axis=-1) / 30.0


def direct(x, lag):
    return np.mean(x[:, :-lag or None] * x[:, lag:], axis=1) if lag else np.mean(x * x, axis=1)


def block_reference(lam, a, variance, lag, width):
    """Exact stationary EM expectation for the H observable and block width."""
    offsets = lag + np.arange(width)[:, None] - np.arange(width)[None, :]
    decay = np.mean(a[:, None, None] ** (2 * np.abs(offsets)[None, :, :]), axis=(1, 2))
    return float(np.sum(lam * lam * variance * variance * decay))


def summarize(channels, lam, a, variance, configs):
    weights = np.array([1 / 5] * 3 + [1 / 30] * 3)
    result = []
    for slots, levels in configs:
        per_chain = [[multi_tau(channels[c, :, ch], slots, levels) for ch in range(6)]
                     for c in range(channels.shape[0])]
        reference_bins = per_chain[0][0]
        rows = []
        for index, (lag, _, pairs, width, level) in enumerate(reference_bins):
            values = np.array([sum(weights[ch] * per_chain[c][ch][index][1] for ch in range(6))
                               for c in range(channels.shape[0])])
            raw = np.array([sum(weights[ch] * direct(channels[c:c + 1, :, ch], lag)[0]
                                 for ch in range(6)) for c in range(channels.shape[0])])
            exact = float(np.mean(raw))
            complete = channels.shape[1] // width
            blocks = channels[:, :complete * width].reshape(channels.shape[0], complete, width, 6).mean(axis=2)
            block_empirical = np.array([sum(weights[ch] * direct(blocks[c:c + 1, :, ch], lag // width)[0]
                                             for ch in range(6))
                                        for c in range(channels.shape[0])])
            block_sample = float(np.mean(block_empirical))
            block = block_reference(lam, a, variance, lag, width)
            rows.append(dict(lag=lag, level=level, width=width, pairs=pairs,
                             value=float(values.mean()), chain_se=float(values.std(ddof=1) / np.sqrt(len(values))),
                             direct=float(exact), block=float(block), block_empirical=block_sample,
                             abs_direct=float(abs(values.mean() - exact)),
                             abs_block=float(abs(values.mean() - block_sample)),
                             theory_error=float(abs(block_sample - block))))
        terminal = rows[-1]
        result.append(dict(slots=slots, levels=levels, bins=len(rows), rows=rows,
                           terminal=terminal,
                           max_abs_block=max(r['abs_block'] for r in rows),
                           max_abs_direct=max(r['abs_direct'] for r in rows)))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--frames', type=int, default=4096)
    p.add_argument('--chains', type=int, default=32)
    p.add_argument('--springs', type=int, default=8)
    p.add_argument('--seed', type=int, default=433201)
    a = p.parse_args()
    if a.frames < 256 or a.chains < 2:
        p.error('use at least 256 frames and two independent chains')
    channels, lam, decay, variance = observations(n=a.springs, frames=a.frames, chains=a.chains, seed=a.seed)
    configs = ((16, 14), (32, 13), (64, 12), (16, 40))
    print(json.dumps(dict(model='stationary Gaussian EM stress', n=a.springs, dt=2.5e-5,
                          frames=a.frames, chains=a.chains, seed=a.seed,
                          configurations=summarize(channels, lam, decay, variance, configs)),
                   sort_keys=True))


if __name__ == '__main__':
    main()
