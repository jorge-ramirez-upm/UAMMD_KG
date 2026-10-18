"""CPU-only correctness, sanitizers, unchanged stress regressions and bounded benchmarks.

All binaries/logs are private artifacts in build/orientation-cpu. No Makefile,
CUDA executable, campaign, or scientific output is used or overwritten.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import unittest

PROJECT = Path(__file__).resolve().parents[1]
KG = PROJECT.parent / 'KG'
BUILD = PROJECT / 'build/orientation-cpu'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmarks', action='store_true', help='also run 36 isolated, fixed-size CPU measurements')
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    report = dict(platform=platform.platform(), compiler=subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
                  cpu_affinity_count=len(os.sched_getaffinity(0)), tests=[], benchmarks=[])
    report['source_hashes'] = {str(p): digest(p) for p in
        (PROJECT/'orientation_correlator.h', PROJECT/'tests/orientation_cpu.cpp',
         PROJECT/'tests/orientation_allocation_failure.cpp', Path(__file__), KG/'correlator.h', KG/'correlator.cpp')}

    def checked(command, name, timeout=60, env=None):
        start = time.perf_counter()
        with open(BUILD/(name+'.log'), 'w') as log:
            cp = subprocess.run([str(x) for x in command], stdout=log, stderr=subprocess.STDOUT, timeout=timeout, env=env)
        item = dict(name=name, command=[str(x) for x in command], seconds=time.perf_counter()-start,
                    exit_code=cp.returncode, log_sha256=digest(BUILD/(name+'.log')))
        report['tests'].append(item)
        if cp.returncode:
            raise RuntimeError(f'{name} failed ({cp.returncode}); inspect {BUILD/(name+".log")}')
        return (BUILD/(name+'.log')).read_text()

    def compile_(source, name, sanitized=False):
        flags = ['-std=c++17', '-Wall', '-Wextra', '-pedantic', '-pthread']
        flags += ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitized else ['-O2']
        if source.name == 'orientation_allocation_failure.cpp':
            flags += ['-Wl,--wrap=_Znwm', '-Wl,--wrap=_Znam']
        binary = BUILD/name
        checked(['g++', *flags, '-I', KG, source, KG/'correlator.cpp', '-o', binary], 'build-'+name)
        return binary

    try:
        unit = compile_(PROJECT/'tests/orientation_cpu.cpp', 'orientation_cpu')
        fault = compile_(PROJECT/'tests/orientation_allocation_failure.cpp', 'allocation_failure')
        print(checked([unit], 'correctness', timeout=90).strip())
        print(checked([fault], 'allocation-failure', timeout=90).strip())
        sanitized = compile_(PROJECT/'tests/orientation_cpu.cpp', 'orientation_asan', True)
        fault_san = compile_(PROJECT/'tests/orientation_allocation_failure.cpp', 'allocation_failure_asan', True)
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        print(checked([sanitized], 'correctness-asan-ubsan-lsan', timeout=120, env=env).strip())
        print(checked([fault_san], 'failure-asan-ubsan-lsan', timeout=120, env=env).strip())

        # These existing CPU sources and their thresholds are compiled unchanged.
        smoke = compile_(PROJECT/'correlator_smoke.cpp', 'stress_smoke')
        print(checked([smoke], 'existing-stress-smoke').strip())
        for name, source in [('stress_lifetime', 'stream_lifetime.cpp'), ('stress_workers', 'cpu_workers.cpp')]:
            binary = compile_(PROJECT/'tests'/source, name, True)
            print(checked([binary], 'existing-'+name, timeout=120, env=env).strip())
        fixture = compile_(PROJECT/'tests/semiflexible_stress_correlator.cpp', 'stress_fixture')
        import numpy as np
        saved_argv = sys.argv
        try:
            sys.argv = ['cpu-stress-reference', 'unused-gpu-binary', str(fixture)]
            spec = importlib.util.spec_from_file_location('existing_stress_oracle', PROJECT/'tests/test_semiflexible_stress_gpu.py')
            oracle = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(oracle)
        finally:
            sys.argv = saved_argv
        with tempfile.TemporaryDirectory(prefix='stress-regression-', dir=BUILD) as folder:
            root = Path(folder)
            for kind in range(3):
                values = np.empty((129,7,6))
                for f in range(129):
                    for c in range(7):
                        for k in range(6):
                            values[f,c,k] = (k+1)*.2 if kind == 0 else np.sin(.17*f+.23*c+.31*k)+(0 if kind == 1 else .7)
                source = root/f'input-{kind}.txt'
                with open(source, 'w') as out:
                    out.write('7 129\n')
                    np.savetxt(out, values.reshape(-1,6), fmt='%.17g')
                previous = None
                for workers,batch in ((1,1),(2,7),(4,32)):
                    output = root/f'k{kind}-w{workers}-b{batch}'
                    checked([fixture, source, output, 5, 8, 2, workers, batch, 1.7, .25, 1], f'stress-direct-{kind}-{workers}-{batch}')
                    oracle.check_direct(unittest.TestCase(), values, output/'stress_correlations.csv', .125, 1.7, .25)
                    actual = (output/'stress_correlations.csv').read_bytes()
                    if previous is not None and actual != previous:
                        raise AssertionError('existing stress worker/batch replay changed')
                    previous = actual
        print('PASS existing stress direct oracle: 9 synthetic worker/batch cases, all bins/channels/paired SE')

        if args.benchmarks:
            for chains in (64,512,2048):
                for slots in (32,64):
                    for second in (0,1):
                        for repeat in range(3):
                            name=f'bench-c{chains}-p{slots}-r{second}-{repeat}'
                            item=json.loads(checked([unit, '--benchmark', chains, slots, second], name))
                            item['repeat']=repeat;report['benchmarks'].append(item)
            groups={}
            for item in report['benchmarks']:
                groups.setdefault((item['chains'],item['slots'],item['second_rank']),[]).append(item)
            report['benchmark_medians']=[]
            for key,items in groups.items():
                result=dict(chains=key[0],slots=key[1],second_rank=key[2])
                for metric in items[0]:
                    if metric not in ('chains','slots','second_rank','repeat'):
                        result[metric]=statistics.median(x[metric] for x in items)
                result['throughput_min']=min(x['observations_per_second'] for x in items)
                result['throughput_max']=max(x['observations_per_second'] for x in items)
                report['benchmark_medians'].append(result)
                print('BENCH',json.dumps(result,sort_keys=True))
            report['memory_cycles']=json.loads(checked([unit, '--memory-cycles'], 'large-memory-cycles'))
        report['binary_sha256']=digest(unit)
        report['status']='passed'
    except BaseException as e:
        report.update(status='failed',error=repr(e))
        raise
    finally:
        (BUILD/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS CPU-only suite; report:', BUILD/'results.json')


if __name__ == '__main__':
    main()
