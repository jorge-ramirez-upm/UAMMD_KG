"""Read-only Stage B nonlinear stress-correlation summary."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


COLS = ('Cxy', 'Cxz', 'Cyz', 'Cxx_yy', 'Cxx_zz', 'Cyy_zz')
WEIGHTS = (1 / 5, 1 / 5, 1 / 5, 1 / 30, 1 / 30, 1 / 30)


def fail(message):
    raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid(frames, levels, slots, m):
    highest, width = 0, 1
    while highest + 1 < levels and width * m <= frames:
        highest += 1
        width *= m
    result = [(j, 1, frames - j) for j in range(min(slots, frames))]
    for level in range(1, highest):
        block = m ** level
        result += [(j * block, block, frames // block - j)
                   for j in range(slots // m, min(slots, frames // block))]
    return result


def terminal(rows):
    result = {'status': 'insufficient_support'}
    if len(rows) < 3 or rows[0]['H'] <= 6 * rows[0]['H_se']:
        return dict(result, reason='zero-lag amplitude unresolved')
    time = [r['lag_time'] for r in rows]
    value = [r['H'] for r in rows]
    error = [r['H_se'] for r in rows]

    def crossing(series, target):
        for i in range(1, len(series)):
            if series[i] <= target < series[i - 1]:
                return time[i - 1] + (time[i] - time[i - 1]) * (series[i - 1] - target) / (series[i - 1] - series[i])
        return None

    tau = crossing(value, value[0] / math.e)
    low = crossing([x - 6 * y for x, y in zip(value, error)], (value[0] + 6 * error[0]) / math.e)
    high = crossing([x + 6 * y for x, y in zip(value, error)], (value[0] - 6 * error[0]) / math.e)
    result.update(tau_e=tau, tau_bounds=[low, high])
    if tau is None or low is None or high is None or low <= 0 or high < low:
        return dict(result, reason='first-crossing uncertainty not resolved within acquisition')
    supported = [i for i, r in enumerate(rows) if r['pairs_per_chain'] >= 16 and r['block_time'] <= tau / 4]
    if not supported or 2 * tau > max(time[i] for i in supported):
        return dict(result, reason='no supported bin near twice tau_e')
    near = min(supported, key=lambda i: abs(time[i] - 2 * tau))
    late = [i for i in supported if time[i] > 4 * tau]
    result.update(positive_lag=time[near], positive_offset=time[near] - 2 * tau,
                  positive_signal=value[near], positive_se=error[near],
                  positive_origins=rows[near]['pairs_per_chain'], positive_block_time=rows[near]['block_time'])
    if not late:
        return dict(result, reason='no supported bin beyond four tau_e')
    terminal_index = next((i for i in late if abs(value[i]) / value[0] <= .1 + 6 * error[i] / value[0]), None)
    if value[near] <= 3 * error[near]:
        return dict(result, reason='positive signal near twice tau_e unresolved')
    if terminal_index is None:
        return dict(result, status='failed', reason='supported late bins do not satisfy terminal threshold')
    return dict(result, status='passed', late_lag=time[terminal_index],
                late_ratio=abs(value[terminal_index]) / value[0],
                late_origins=rows[terminal_index]['pairs_per_chain'],
                late_block_time=rows[terminal_index]['block_time'])


def analyze(directory):
    directory = Path(directory)
    meta = json.loads((directory / 'metadata.json').read_text())
    stress = json.loads((directory / 'stress_metadata.json').read_text())
    if stress.get('mode') != 'every-step':
        fail('Stage B requires every-step stress metadata')
    if stress['frames'] != meta['steps'] + 1:
        fail('every-step frame count must include step zero')
    rows = []
    with (directory / 'stress_correlations.csv').open(newline='') as handle:
        for raw in csv.DictReader(handle):
            item = {key: float(raw[key]) for key in ('lag_samples', 'lag_time', 'block_samples', 'H', 'H_se', 'pairs_per_chain', 'pairs_total') + COLS}
            item['lag_samples'] = int(item['lag_samples'])
            item['block_samples'] = int(item['block_samples'])
            item['pairs_per_chain'] = int(item['pairs_per_chain'])
            item['pairs_total'] = int(item['pairs_total'])
            item['block_time'] = item['block_samples'] * stress['spacing']
            expected = sum(item[key] * weight for key, weight in zip(COLS, WEIGHTS))
            if not math.isclose(item['H'], expected, rel_tol=3e-11, abs_tol=3e-11):
                fail('isotropic H disagrees with six-channel convention')
            item['H_from_channels'] = expected
            rows.append(item)
    expected = grid(stress['frames'], stress['levels'], stress['slots'], stress['coarsening'])
    if len(rows) != len(expected):
        fail('missing, duplicate, or unexpected multi-tau bins')
    for row, (lag, block, origins) in zip(rows, expected):
        if (row['lag_samples'], row['block_samples'], row['pairs_per_chain']) != (lag, block, origins):
            fail('lag/block/origin count disagrees with correlator convention')
        if row['pairs_total'] != origins * meta['chains']:
            fail('pairs_total disagrees with independent-chain count')
        if not math.isclose(row['lag_time'], lag * stress['spacing'], rel_tol=1e-12, abs_tol=1e-12):
            fail('lag time disagrees with every-step spacing')
    return dict(status='exploratory_single_replica', independent_chain_clusters=meta['chains'],
                independent_replicas=1, metadata=dict(steps=meta['steps'], dt=meta['dt'], chains=meta['chains'],
                springs=meta['springs'], seed=meta['seed'], stress_frames=stress['frames'], spacing=stress['spacing'],
                levels=stress['levels'], slots=stress['slots'], coarsening=stress['coarsening']),
                correlation_sha256=digest(directory / 'stress_correlations.csv'), bins=rows,
                supported_bin_count=sum(r['pairs_per_chain'] >= 16 for r in rows), terminal=terminal(rows),
                limitation='512 chains provide cluster uncertainty, not independent replica confirmation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('refusing to overwrite report')
    result = analyze(args.run_directory)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(args.report)


if __name__ == '__main__':
    main()
