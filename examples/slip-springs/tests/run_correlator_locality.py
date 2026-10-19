"""Bounded frame-major versus chain-major stress-correlator experiment.

This only builds the test-only traversal prototype.  It never links CUDA or a
simulator, accesses campaign data, or writes outside its ignored build folder.
"""
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

from run_stress_throughput import COLS, KG, PROJECT, digest, direct_check


def main():
    started = time.monotonic()
    parent = PROJECT / 'build/correlator-locality'
    parent.mkdir(parents=True, exist_ok=True)
    build = Path(tempfile.mkdtemp(prefix='run-', dir=parent))
    report = dict(status='running', directory=str(build), tests=[], correctness=[],
                  measurements=[], sustained=[], skipped=[], matrix_seed=433202,
                  affinity=sorted(os.sched_getaffinity(0)), platform=platform.platform(),
                  compiler=subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
                  cpu_info=Path('/proc/cpuinfo').read_text().split('model name')[1].splitlines()[0],
                  load_start=os.getloadavg(),
                  source_hashes={os.path.relpath(path, PROJECT): digest(path) for path in
                                 [PROJECT/'stream_correlator.h', PROJECT/'cpu_workers.h',
                                  KG/'correlator.h', KG/'correlator.cpp',
                                  PROJECT/'tests/chain_major_correlator.h',
                                  PROJECT/'tests/stress_throughput.cpp', Path(__file__)]})

    def save():
        (build/'results.json').write_text(json.dumps(report, indent=2)+'\n')

    def checked(command, name, fail=False):
        remaining = 540 - (time.monotonic() - started)
        if remaining < 5:
            raise RuntimeError('suite execution budget exhausted; no case was shortened')
        began = time.monotonic()
        with open(build/(name+'.log'), 'w') as log:
            completed = subprocess.run([str(value) for value in command], stdout=log,
                                       stderr=subprocess.STDOUT, timeout=min(120, remaining))
        item = dict(name=name, command=[str(value) for value in command],
                    exit_code=completed.returncode, wall_seconds=time.monotonic()-began,
                    log_sha256=digest(build/(name+'.log')))
        report['tests'].append(item)
        if (completed.returncode == 0) == fail:
            raise RuntimeError(f'unexpected exit status for {name}; inspect {build}')
        return (build/(name+'.log')).read_text()

    binary = build/'stress_throughput'

    def run(config, traversal, name, warm=0, frames=1027, pattern=0):
        chains, slots, levels, workers, batch = config
        prefix = build/name
        checked([binary, chains, slots, levels, workers, batch, warm, frames,
                 prefix, pattern, 1 << 30, traversal], name)
        result = json.loads(prefix.with_suffix('.json').read_text())
        assert result['traversal'] == traversal
        assert result['total_frames'] == warm + frames
        assert result['bank_bytes'] < 1 << 30
        result.update(name=name, load=os.getloadavg(),
                      correlation_sha256=digest(prefix.with_suffix('.csv')))
        return result

    try:
        checked(['g++', '-O2', '-std=c++17', '-Wall', '-Wextra', '-pedantic', '-pthread',
                 PROJECT/'tests/stress_throughput.cpp', KG/'correlator.cpp', '-o', binary], 'compile')
        report['binary_sha256'] = digest(binary)

        # Exact, direct-oracle validation across both traversal orders, all
        # requested batch sizes and worker counts.  Frame output is the reference.
        for slots, levels in [(32, 20), (64, 24)]:
            for workers in [1, 2, 4, 8]:
                for batch in [32, 256, 1024]:
                    config = (9, slots, levels, workers, batch)
                    frame = run(config, 'frame', f'correct-frame-{slots}-{workers}-{batch}')
                    chain = run(config, 'chain', f'correct-chain-{slots}-{workers}-{batch}')
                    direct = direct_check(build/(frame['name']+'.csv'), 1027, 9, slots, levels, 0)
                    assert (build/(frame['name']+'.csv')).read_bytes() == (build/(chain['name']+'.csv')).read_bytes()
                    report['correctness'].append(dict(config=config, frame=frame, chain=chain, direct=direct))
        for pattern in [1, 2]:
            config = (9, 64, 24, 4, 32)
            frame = run(config, 'frame', f'pattern-frame-{pattern}', frames=259, pattern=pattern)
            chain = run(config, 'chain', f'pattern-chain-{pattern}', frames=259, pattern=pattern)
            direct = direct_check(build/(frame['name']+'.csv'), 259, 9, 64, 24, pattern)
            assert (build/(frame['name']+'.csv')).read_bytes() == (build/(chain['name']+'.csv')).read_bytes()
            report['correctness'].append(dict(config=config, pattern=pattern, frame=frame, chain=chain, direct=direct))

        # Includes every requested C/P/batch range while concentrating repetitions
        # on the 2048-chain candidate needed for the every-step pipeline.
        matrix = {(2048, 64, 24, workers, batch)
                  for workers in [1, 4, 8] for batch in [32, 256, 1024]}
        matrix |= {(2048, 32, 20, workers, 256) for workers in [1, 2, 4, 8]}
        matrix |= {(chains, slots, levels, workers, 256)
                   for chains in [256, 1024] for slots, levels in [(32, 20), (64, 24)]
                   for workers in [1, 4, 8]}
        matrix.add((2048, 64, 20, 4, 256))
        report['matrix'] = sorted(matrix)
        work = [(config, traversal, repeat) for config in sorted(matrix)
                for traversal in ['frame', 'chain']
                for repeat in range(3 if config[0] == 2048 else 2)]
        random.Random(433202).shuffle(work)
        hashes = {}
        for config, traversal, repeat in work:
            name = 'bench-'+'-'.join(map(str, config))+f'-{traversal}-r{repeat}'
            item = run(config, traversal, name, warm=1024, frames=1025)
            key = (config[:3], traversal)
            if key in hashes:
                assert hashes[key] == item['correlation_sha256'], 'replay changed correlation output'
            hashes[key] = item['correlation_sha256']
            report['measurements'].append(item)
            save()
            print(name, round(item['chain_observations_per_second']/1e6, 3), 'M chain-obs/s', flush=True)

        # Every matching frame/chain matrix output must still be exact.
        by_identity = {}
        for item in report['measurements']:
            key = tuple(item[field] for field in ['chains', 'slots', 'levels', 'workers', 'batch'])
            by_identity.setdefault(key, {})[item['traversal']] = item['correlation_sha256']
        for value in by_identity.values():
            assert value['frame'] == value['chain'], 'traversal changed output'

        target = (2048, 64, 24, 8, 256)
        for traversal in ['frame', 'chain']:
            for repeat in range(3):
                item = run(target, traversal, f'sustained-{traversal}-{repeat}', warm=1024, frames=8193)
                report['sustained'].append(item); save()
                print('sustained', traversal, repeat,
                      round(item['chain_observations_per_second']/1e6, 3), 'M chain-obs/s', flush=True)
        assert len({item['correlation_sha256'] for item in report['sustained']}) == 1
        report.update(status='passed', seconds=time.monotonic()-started, load_end=os.getloadavg())
    except Exception as error:
        report.update(status='failed', error=str(error), seconds=time.monotonic()-started)
        raise
    finally:
        save()
        print('Evidence:', build/'results.json', flush=True)


if __name__ == '__main__':
    main()
