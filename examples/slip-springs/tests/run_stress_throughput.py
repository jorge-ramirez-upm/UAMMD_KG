"""Bounded CPU Bank/CpuWorkers benchmark and independent direct-correlation checks.

Never imports a simulator, accesses campaign data, or changes production sources.
Artifacts are unique directories under build/stress-throughput. Each subprocess
has a <=120-second timeout; the suite has a 540-second execution budget.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import tempfile
import time

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
KG = PROJECT.parent / 'KG'
COLS = ['Cxy', 'Cxz', 'Cyz', 'Cxx_yy', 'Cxx_zz', 'Cyy_zz']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prescribed(frames, chains, pattern):
    f = (np.arange(frames) % 1024)[:, None]
    c = np.arange(chains)[None, :]
    a = ((f*17+c*13) % 101-50)/64.
    b = ((f*7+c*19) % 67-33)/64.
    if pattern == 1:
        a = np.broadcast_to((c % 11-5)/16., (frames, chains))
        b = np.full_like(a, .25)
    if pattern == 2:
        a = np.broadcast_to(np.where(f % 2, -.5, .5), (frames, chains))
        b = np.broadcast_to(np.where(f % 4 < 2, -.25, .25), (frames, chains))
    offset = (c % 11-5)/32.
    xx, yy, zz = 1+a+.5*b+offset, .5-.25*a+b, .25+.125*a-.5*b
    return np.stack([.125+a+.25*b+offset, -.25+.5*a-b, .375-.25*a+.75*b,
                     xx-yy, xx-zz, yy-zz], axis=-1)


def direct_check(path, frames, chains, slots, levels, pattern):
    """Independent complete-block/origin oracle, existing stress tolerance 3e-11."""
    data = prescribed(frames, chains, pattern)
    highest = min(levels-1, frames.bit_length()-1)
    grid = [(j, 1, frames-j) for j in range(min(slots, frames))]
    for level in range(1, highest):
        block = 2**level
        grid += [(j*block, block, frames//block-j)
                 for j in range(slots//2, min(slots, frames//block))]
    with open(path) as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(grid), 'missing/duplicate exported bins'
    maximum = 0.
    for row, (lag, block, origins) in zip(rows, grid):
        n = frames//block
        means = data[:n*block].reshape(n, block, chains, 6).mean(axis=1)
        offset = lag//block
        products = (means[offset:]*means[:n-offset]).mean(axis=0)
        h = products[:, :3].sum(axis=1)/5+products[:, 3:].sum(axis=1)/30
        expected = np.r_[products.mean(axis=0), products.std(axis=0, ddof=1)/np.sqrt(chains),
                         h.mean(), h.std(ddof=1)/np.sqrt(chains)]
        actual = np.array([float(row[k]) for k in COLS+[k+'_se' for k in COLS]+['g', 'g_se']])
        np.testing.assert_allclose(actual, expected, atol=3e-11, rtol=3e-11)
        maximum = max(maximum, float(np.max(np.abs(actual-expected))))
        assert float(row['lag_samples']) == lag and float(row['lag_time']) == lag
        assert int(row['block_samples']) == block
        assert int(row['pairs_per_chain']) == origins
        assert int(row['pairs_total']) == origins*chains
    return dict(bins=len(rows), maximum_absolute_error=maximum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmarks', action='store_true')
    args = parser.parse_args()
    start = time.monotonic()
    parent = PROJECT/'build/stress-throughput'
    parent.mkdir(parents=True, exist_ok=True)
    build = Path(tempfile.mkdtemp(prefix='run-', dir=parent))
    report = dict(status='running', directory=str(build), tests=[], measurements=[], skipped=[],
                  affinity=sorted(os.sched_getaffinity(0)), platform=platform.platform(),
                  compiler=subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
                  cpu_info=Path('/proc/cpuinfo').read_text().split('model name')[1].splitlines()[0],
                  load_start=os.getloadavg(), matrix_seed=433201,
                  source_hashes={os.path.relpath(p, PROJECT): digest(p) for p in
                                 [PROJECT/'stream_correlator.h', PROJECT/'cpu_workers.h',
                                  KG/'correlator.h', KG/'correlator.cpp',
                                  PROJECT/'tests/stress_throughput.cpp', Path(__file__)]})
    def save():
        (build/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    def checked(command, name, expect_failure=False):
        remaining = 540-(time.monotonic()-start)
        if remaining < 5:
            raise RuntimeError('suite execution budget exhausted; no shortened benchmarks substituted')
        begin = time.monotonic()
        with open(build/(name+'.log'), 'w') as log:
            cp = subprocess.run([str(x) for x in command], stdout=log, stderr=subprocess.STDOUT,
                                timeout=min(120, remaining))
        item = dict(name=name, command=[str(x) for x in command], exit_code=cp.returncode,
                    wall_seconds=time.monotonic()-begin, log_sha256=digest(build/(name+'.log')))
        report['tests'].append(item)
        if (cp.returncode == 0) == expect_failure:
            raise RuntimeError(f'unexpected exit status: {name}; inspect {build}')
        return (build/(name+'.log')).read_text()
    binary = build/'stress_throughput'
    def run(config, name, warm=0, frames=1027, pattern=0, budget=1 << 30):
        c, p, l, w, b = config
        prefix = build/name
        load = os.getloadavg()
        checked([binary, c, p, l, w, b, warm, frames, prefix, pattern, budget], name)
        result = json.loads(prefix.with_suffix('.json').read_text())
        assert result['total_frames'] == warm+frames
        assert result['bank_bytes'] <= budget <= 1 << 30
        result.update(name=name, load=load, correlation_sha256=digest(prefix.with_suffix('.csv')))
        return result
    try:
        checked(['g++', '-O2', '-std=c++17', '-Wall', '-Wextra', '-pedantic', '-pthread',
                 PROJECT/'tests/stress_throughput.cpp', KG/'correlator.cpp', '-o', binary], 'compile')
        report['binary_sha256'] = digest(binary)
        correctness = []
        for p, l in [(32, 20), (64, 24)]:
            hashes = set()
            for w in [1, 2, 4, 8]:
                for b in [32, 256, 1024]:
                    item = run((9, p, l, w, b), f'correct-{p}-{w}-{b}')
                    item['direct'] = direct_check(build/(item['name']+'.csv'), 1027, 9, p, l, 0)
                    hashes.add(item['correlation_sha256'])
                    correctness.append(item)
            assert len(hashes) == 1, 'worker/batch changes scientific results'
        for pattern in [1, 2]:
            item = run((9, 32, 20, 4, 32), f'pattern-{pattern}', frames=259, pattern=pattern)
            item['direct'] = direct_check(build/(item['name']+'.csv'), 259, 9, 32, 20, pattern)
            correctness.append(item)
        report['correctness'] = correctness
        checked([binary, 2048, 64, 24, 4, 256, 0, 1, build/'reject', 0, 1], 'reject-budget', True)
        checked([binary, 2049, 64, 24, 4, 256, 0, 1, build/'reject', 0, 1 << 30], 'reject-dimensions', True)
        # Existing unchanged worker regression; no CUDA or simulator is linked.
        workers = build/'existing_workers'
        checked(['g++', '-O2', '-std=c++17', '-pthread', PROJECT/'tests/cpu_workers.cpp',
                 KG/'correlator.cpp', '-o', workers], 'compile-existing-workers')
        checked([workers], 'existing-workers')
        print('PASS direct bins:', sum(x['direct']['bins'] for x in correctness), flush=True)
        if args.benchmarks:
            matrix = {(2048, 64, 24, w, b) for w in [1, 2, 4, 8] for b in [32, 256, 1024]}
            matrix |= {(2048, 32, 20, w, 256) for w in [1, 2, 4, 8]}
            matrix |= {(c, 64, 24, w, 256) for c in [256, 1024] for w in [1, 4, 8]}
            matrix |= {(2048, 64, 20, w, 256) for w in [1, 4]}
            matrix.add((2048, 32, 24, 4, 256))
            report['matrix'] = sorted(matrix)
            # Repeat in interleaved deterministic order; one child/bank at a time.
            work = [(cfg, rep) for cfg in sorted(matrix) for rep in range(3)]
            random.Random(433201).shuffle(work)
            hashes = {}
            for cfg, rep in work:
                name = 'bench-'+'-'.join(map(str, cfg))+f'-r{rep}'
                item = run(cfg, name, warm=1024, frames=1025)
                key = (cfg[0], cfg[1], cfg[2])
                if key in hashes:
                    assert item['correlation_sha256'] == hashes[key], 'matrix replay mismatch'
                hashes[key] = item['correlation_sha256']
                report['measurements'].append(item)
                save()
                print(name, round(item['chain_observations_per_second']/1e6, 3), 'M chain-obs/s', flush=True)
            candidates = [cfg for cfg in matrix if cfg[:3] == (2048, 64, 24)]
            def rate(cfg):
                return statistics.median(x['chain_observations_per_second'] for x in report['measurements']
                                         if tuple(x[k] for k in ['chains', 'slots', 'levels', 'workers', 'batch']) == cfg)
            chosen = max(candidates, key=rate)
            report['sustained_configuration'] = chosen
            report['sustained'] = []
            for rep in range(3):
                item = run(chosen, f'sustained-{rep}', warm=1024, frames=8193)
                report['sustained'].append(item)
                save()
                print('sustained', rep, round(item['chain_observations_per_second']/1e6, 3), flush=True)
            assert len({x['correlation_sha256'] for x in report['sustained']}) == 1
        report.update(status='passed', seconds=time.monotonic()-start, load_end=os.getloadavg())
    except Exception as error:
        report.update(status='failed', error=str(error), seconds=time.monotonic()-start)
        raise
    finally:
        save()
        print('Evidence:', build/'results.json', flush=True)


if __name__ == '__main__':
    main()
