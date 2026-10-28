#!/usr/bin/env python3
"""Prepared sustained timing preflight; run locally only after independent review."""
import argparse
import math
from pathlib import Path
import shutil
import signal
import time

from e1_d1_pilot import atomic, capture, file_record, load, require
from e1_d1_pilot_runner import environment, host_available, run_process, tree_bytes
from e1_d2a3_run import PHYSICAL, SPRINGS, gpu_state, inventory, matches

PROJECT = Path(__file__).resolve().parent
REPO = PROJECT.parents[1]
SOURCE = 'd622e0cc34d4019358bebad5ce8a86e64c265351'
BINARY_SHA = '54dc84a9aac35fd6574ce6e2890a6c8a0f545743fdc2bbd32bc0a70863dcf9ce'
DEFAULT_BINARY = PROJECT / 'build/d2a5-review-v1/double/semiflexible'
DEFAULT_CHECK = Path('/home/jramirez/UAMMD_KG-evidence/d2a5/bounded-v1/summary.json')
GPU = 'GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274'
LIMITS = dict(per_run_seconds=1800, aggregate_seconds=3900,
              max_host_rss_bytes=2*1024**3, per_run_output_bytes=128*1024**2,
              aggregate_output_bytes=512*1024**2, min_free_disk_bytes=10*1024**3)
TIMERS = ('initialization_seconds', 'integration_seconds', 'production_wall_seconds',
          'observation_seconds', 'recurrent_output_seconds', 'final_output_seconds',
          'force_and_diagnostic_wall_seconds')
DYNAMIC_TIMERS = ('shared_readback_seconds', 'extra_readback_seconds',
                  'acquisition_cpu_seconds', 'evaluation_csv_seconds')


def command(binary, directory, n, steps):
    return [str(binary), '--springs', str(n), '--chains', '256', '--steps', str(steps),
            '--dt', '.0001', '--sample', str(steps), '--seed', '73350501',
            '--kappa', '10', '--kb', '30', '--b0', '1', '--kbt', '1', '--zeta', '1',
            '--slip-count', str(256*n//4), '--slip-ms2', '5', '--hop-rate', '100',
            '--end-renewal', '1', '--stress-mode', 'off',
            '--equilibrium-steps', str(directory/'endpoints.steps'),
            '--equilibrium-snapshots', str(directory/'endpoints.steps'),
            '--dynamics', '1', '--dynamics-stride', '100', '--dynamics-levels', '15',
            '--dynamics-slots', '16', '--dynamics-m', '2', '--dynamics-mib', '256',
            '--dynamics-replica', '9077', '--output', str(directory/'output')]


def measurements(output, n, steps, child_seconds):
    physical = load(output/'metadata.json')
    dynamics = load(output/'dynamics/metadata.json')
    complete = load(output/'equilibrium_complete.json')
    matches(physical, dict(precision_bits=64, springs=n, chains=256, beads_per_chain=n+1,
                          total_beads=256*(n+1), dt=.0001, steps=steps, sample=steps,
                          kbt=1, zeta=1, slip_count=256*n//4, slip_ms2=5,
                          seed=73350501, active_angles=n-1, update_launches=steps,
                          slip_mode='canonical-renewal-development'), 'physical completion')
    matches(dynamics, dict(complete=True, precision_bits=64, N=n, chains=256,
                          integration_steps=steps, frames=steps//100+1,
                          first_step=0, last_step=steps, stride=100, dt=.0001,
                          correlator_levels=15, correlator_slots=16, correlator_m=2,
                          end_renewal_active=True, hop_rate=100, replica=9077,
                          shared_frames=2, extra_readbacks=steps//100-1), 'dynamics completion')
    matches(dynamics, dict(b0=[1]*n, kb=[30]*n, kappa=[0]+[10]*(n-1)+[0]), 'coefficients')
    require(complete['complete'] is True and complete['frames'] == 2, 'endpoint completion')
    require(set(complete['files']) == (PHYSICAL | SPRINGS) -
            {'parameters.txt', 'equilibrium_complete.json'}, 'physical completion inventory')
    for name, size in complete['files'].items():
        require(Path(name).name == name and (output/name).stat().st_size == size,
                'incomplete physical output: '+name)
    require(0 < dynamics['conservative_observer_estimate_bytes'] <=
            dynamics['memory_budget_bytes'] == 256*1024**2, 'observer budget')
    timers = {key: physical[key] for key in TIMERS}
    acquisition = {key: dynamics[key] for key in DYNAMIC_TIMERS}
    require(all(isinstance(v, (float, int)) and math.isfinite(v) and v >= 0
                for v in [*timers.values(), *acquisition.values()]), 'invalid timing')
    production = physical['production_wall_seconds']
    require(production > 0 and physical['integration_seconds'] > 0, 'empty production timer')
    return dict(actual_integration_steps=physical['steps'], physical_timers=timers,
                dynamics_timers=acquisition, production_steps_per_second=steps/production,
                child_steps_per_second=steps/child_seconds,
                child_minus_production_seconds=child_seconds-production,
                integration_timer_scope=physical['integration_timer_scope'],
                dynamics_timer_scope=dynamics['timer_scope'],
                device_array_accounting_bytes=physical['device_bytes'],
                gpu_peak_memory_bytes=None,
                readback_bytes={k: dynamics[k] for k in
                                ('shared_readback_bytes', 'extra_readback_bytes')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-reviewed-preflight', action='store_true', required=True)
    parser.add_argument('--steps', type=int, choices=(100000, 1000000), default=100000)
    parser.add_argument('--binary', type=Path, default=DEFAULT_BINARY)
    parser.add_argument('--correctness-summary', type=Path, default=DEFAULT_CHECK)
    parser.add_argument('--build-provenance', type=Path, action='append', default=[],
                        help='Existing build log/settings to preserve; never generates a build')
    parser.add_argument('--gpu-uuid', default=GPU)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    binary_record = file_record(binary)
    require(binary_record['sha256'] == BINARY_SHA, 'unverified executable')
    correctness = load(args.correctness_summary)
    require(correctness['status'] == 'bounded_checks_completed' and
            correctness['binary'] == binary_record, 'verified same-binary correctness required')
    require(capture(['git', '-C', REPO, 'branch', '--show-current']) == 'slip-springs', 'branch')
    capture(['git', '-C', REPO, 'merge-base', '--is-ancestor', SOURCE, 'HEAD'])
    root = args.output.resolve()
    require(not root.is_relative_to(REPO) and
            not any(root.is_relative_to(Path(p)) for p in ('/tmp', '/var/tmp', '/run', '/dev/shm')),
            'permanent evidence outside repository required')
    require(not root.exists(), 'refusing existing output directory')
    root.parent.mkdir(parents=True, exist_ok=True)
    require(shutil.disk_usage(root.parent).free >= 11*1024**3, 'initial disk floor plus allowance')
    require(host_available() >= 8*1024**3, '8 GiB host/cgroup headroom required')
    env = environment('/usr/local/cuda-13.0', args.gpu_uuid)
    root.mkdir(exist_ok=False)
    start = time.monotonic()
    summary = dict(status='preparing', source_sha=SOURCE, binary=binary_record,
                   limits=LIMITS, steps_per_configuration=args.steps, run_records=[])
    try:
        provenance = root/'provenance'
        provenance.mkdir()
        # Preserve existing records, without inferring a compiler invocation from them.
        evidence = [args.correctness_summary, binary.with_suffix('.d'),
                    PROJECT/'Makefile', *args.build_provenance]
        for index, path in enumerate(evidence):
            target = provenance/f'{index}-{path.name}'
            shutil.copyfile(path, target)
            require(file_record(path) == file_record(target), 'provenance copy mismatch')
        (provenance/'source-tree.txt').write_text(capture(
            ['git', '-C', REPO, 'ls-tree', '-r', SOURCE])+'\n')
        (provenance/'preparation-head.txt').write_text(capture(
            ['git', '-C', REPO, 'rev-parse', 'HEAD'])+'\n')
        for name in ('e1_d2a5_preflight.py', 'e1_d1_pilot.py', 'e1_d1_pilot_runner.py',
                     'e1_d1_pilot_auth.py', 'e1_d2a3_run.py'):
            shutil.copyfile(PROJECT/name, provenance/name)
        summary['provenance'] = inventory(provenance)
        summary['build_provenance_scope'] = (
            'Pinned verified binary and implementation SHA; retained dependency file and source Makefile. '
            'No new build; historical compiler invocation is not independently established by these records. '
            'Additional supplied build records are retained verbatim.')
        atomic(root/'summary.json', summary)
        for n in (64, 128):
            directory = root/f'n{n}'
            directory.mkdir(exist_ok=False)
            record = dict(N=n, M=256, kappa=10, Z=256*n//4, status='preparing',
                          resource_limit_violations=[], gpu_peak_memory_bytes=None)
            summary['run_records'].append(record)
            run_start = time.monotonic()
            try:
                require(file_record(binary) == binary_record, 'executable identity changed')
                require(host_available() >= 8*1024**3, 'insufficient host/cgroup headroom')
                require(shutil.disk_usage(root).free >= LIMITS['min_free_disk_bytes']+
                        LIMITS['per_run_output_bytes'], 'insufficient disk headroom')
                gpu = gpu_state({'gpu_uuid': args.gpu_uuid}, env)
                record['gpu_before'] = gpu  # Device-wide launch headroom, never peak memory.
                require(gpu['free_bytes'] >= 1024**3, 'insufficient GPU launch headroom')
                (directory/'endpoints.steps').write_text(f'0\n{args.steps}\n')
                argv = command(binary, directory, n, args.steps)
                atomic(directory/'command.json', dict(argv=argv, environment=env))
                atomic(root/'summary.json', summary)
                process = run_process(argv, directory, env, LIMITS, root, start)
                record['process'] = process
                if process['status'] not in ('exited', 'application_failure'):
                    record['resource_limit_violations'].append(process['status'])
                require(process['status'] == 'exited' and process['exit_code'] == 0,
                        'child failed: '+process['status'])
                require(file_record(binary) == binary_record, 'executable changed during run')
                record.update(measurements(directory/'output', n, args.steps, process['wall_seconds']))
                record['output_files'] = inventory(directory/'output')
                record['output_bytes'] = tree_bytes(directory/'output')
                if tree_bytes(directory) > LIMITS['per_run_output_bytes']:
                    record['resource_limit_violations'].append('per_run_output_limit')
                if shutil.disk_usage(root).free < LIMITS['min_free_disk_bytes']:
                    record['resource_limit_violations'].append('disk_headroom_limit')
                require(not record['resource_limit_violations'], 'post-run resource limit')
                record['status'] = 'completed_timing_only'
            except BaseException as error:
                record.update(status='failed', error=str(error))
                if (directory/'process.json').exists():
                    record['process'] = load(directory/'process.json')
                raise
            finally:
                record['total_elapsed_seconds'] = time.monotonic()-run_start
                record['run_directory_bytes_before_receipt'] = tree_bytes(directory)
                atomic(directory/'receipt.json', record)
            atomic(root/'summary.json', summary)
        summary['status'] = 'completed_two_configurations_not_scientific_acceptance'
    except BaseException as error:
        summary.update(status='failed', error=str(error))
        raise
    finally:
        summary['total_elapsed_seconds'] = time.monotonic()-start
        summary['evidence_bytes_before_summary'] = tree_bytes(root)
        violations = summary.setdefault('resource_limit_violations', [])
        for violated, label in (
            (summary['total_elapsed_seconds'] > LIMITS['aggregate_seconds'], 'aggregate_timeout'),
            (tree_bytes(root) > LIMITS['aggregate_output_bytes'], 'aggregate_output_limit'),
            (shutil.disk_usage(root).free < LIMITS['min_free_disk_bytes'], 'disk_headroom_limit')):
            if violated:
                violations.append(label)
        if violations:
            summary['status'] = 'failed'
        atomic(root/'summary.json', summary)
    require(summary['status'] != 'failed', 'final resource limit exceeded')


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    main()
