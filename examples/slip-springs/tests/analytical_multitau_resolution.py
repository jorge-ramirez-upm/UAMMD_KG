"""Analytical Gaussian stress resolution audit; no trajectories are generated."""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from stage4a3c_capacity_audit import hierarchy  # noqa: E402

DT = 2.5e-5


def spectrum(n, dt=DT):
    p = np.arange(1, n + 1, dtype=float)
    lam = 12 * np.sin(p * np.pi / (2 * (n + 1))) ** 2
    a = 1 - lam * dt
    v = 1 / (lam * (1 - lam * dt / 2))
    return lam, a, v


def geometric(q, count):
    """Stable mean of q**j, j=0..count-1."""
    if count == 1:
        return 1.0
    logq = math.log(q)
    if abs(logq) < 1e-8:
        return float(np.expm1(count * logq) / (count * np.expm1(logq)))
    return float(np.expm1(count * logq) / (count * np.expm1(logq)))


def instantaneous(lam, a, v, lag):
    return float(np.sum(lam * lam * v * v * (a * a) ** lag))


def block_average(lam, a, v, lag, width):
    q = a * a
    factor = np.array([geometric(float(x), width) * geometric(float(1 / x), width) for x in q])
    return float(np.sum(lam * lam * v * v * q ** lag * factor))


def fit_tau(rows, values, target_tau):
    points = [(r['lag_time'], values[i]) for i, r in enumerate(rows)
              if target_tau <= r['lag_time'] <= 4 * target_tau and values[i] > 0]
    if len(points) < 2:
        return None, len(points)
    x = np.array([p[0] for p in points]); y = np.log(np.array([p[1] for p in points]))
    slope = float(np.polyfit(x, y, 1)[0])
    return (-1 / slope if slope < 0 else None), len(points)


def analyze(n, duration_multiple=10, dt=DT):
    lam, a, v = spectrum(n, dt)
    tau = 1 / (2 * lam[0])
    frames = int(math.ceil(duration_multiple * tau / dt)) + 1
    configs = ((16, 24), (32, 23), (64, 22), (16, 40))
    out = []
    for slots, levels in configs:
        rows = hierarchy(slots, levels, frames, dt)
        exported = []
        for row in rows:
            complete_blocks = frames // row['block_samples']
            for j in range(row['bins']):
                offset = j if row['level'] == 0 else slots // 2 + j
                lag = offset * row['block_samples']
                if lag * dt > duration_multiple * tau:
                    continue
                inst = instantaneous(lam, a, v, lag)
                block = block_average(lam, a, v, lag, row['block_samples'])
                exported.append(dict(level=row['level'], lag=lag, lag_time=lag * dt,
                                     width=row['block_samples'], block_time=row['block_time'],
                                     offset=offset, origins=complete_blocks - offset,
                                     instantaneous=inst,
                                     block=block, abs_error=abs(block - inst),
                                     normalized_error=abs(block - inst) / max(inst, 1e-12),
                                     scale_error=abs(block - inst) / max(inst, instantaneous(lam, a, v, 0), 1e-12)))
        values_i = np.array([r['instantaneous'] for r in exported]); values_b = np.array([r['block'] for r in exported])
        support4 = [r for r in exported if r['lag_time'] <= 4 * tau and r['origins'] >= 16]
        support10 = [r for r in exported if r['lag_time'] <= 10 * tau and r['origins'] >= 16]
        lags4 = sorted(r['lag_time'] for r in support4)
        max_gap4 = max((b - a for a, b in zip(lags4, lags4[1:])), default=0.0)
        max_width = max(r['width'] for r in exported)
        supported = [r for r in exported if r['origins'] >= 16]
        out.append(dict(slots=slots, levels=levels, frames=frames, nominal_lag=rows[-1]['nominal_lag_time'],
                        supported_lag=max(r['lag_time'] for r in supported) if supported else None, bins=len(exported),
                        bins_4tau=len(support4), bins_10tau=len(support10),
                        max_width=max_width, max_width_over_tau=max_width * dt / tau,
                        max_width_4tau=max(r['width'] for r in support4),
                        max_width_4tau_over_tau=max(r['width'] for r in support4) * dt / tau,
                        max_gap_4tau=max_gap4, max_gap_4tau_over_tau=max_gap4 / tau,
                        max_scale_error=max(r['scale_error'] for r in exported),
                        max_error_4tau=max(r['scale_error'] for r in support4),
                        max_error_10tau=max(r['scale_error'] for r in support10),
                        tau_fit_instant=fit_tau(exported, values_i, tau),
                        tau_fit_block=fit_tau(exported, values_b, tau),
                        terminal=exported[-1],
                        origin_counts=[dict(level=r['level'], offset=r['offset'], origins=r['origins'],
                                            width=r['width']) for r in exported]))
    return dict(n=n, dt=dt, tau=tau, ten_tau=10 * tau, frames=frames, configurations=out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--duration-multiple', type=float, default=10)
    a = p.parse_args()
    print(json.dumps(dict(n8=analyze(8, a.duration_multiple), n32=analyze(32, a.duration_multiple)), sort_keys=True))


if __name__ == '__main__':
    main()
