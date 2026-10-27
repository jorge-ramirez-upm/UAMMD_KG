#!/usr/bin/env python3
"""Prepared D2A.3 serial runner. Execution requires --execute-reviewed-eight.

No simulation on import. Uses the existing Linux child supervisor unchanged.
This validates acquisition completeness and resources, not scientific dynamics.
"""
import argparse
import csv
import fcntl
import itertools
import json
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import sys
import time

from e1_d1_pilot import atomic, capture, digest, file_record, require, utc
from e1_d1_pilot_runner import environment, host_available, resource_check, run_process, tree_bytes

PROJECT = Path(__file__).resolve().parent
CONFIG = PROJECT / 'e1_d2a3_config'
MANIFEST_SHA = '21fd5168be99823e0dccb9af0e83a03a0467b46c50ea79b9fa0bc1d3772fe1cb'
QUANTITIES = ['cm_msd', 'bead0_msd', 'bead8_msd', 'bead16_msd', 'bead24_msd',
              'bead32_msd', 'end_msd', 'quarter_msd', 'end_msd_difference',
              'quarter_msd_difference', 'c1', 'c2']
HEADER = ['replica', 'chain', 'lag_samples', 'lag_steps', 'lag_time',
          'origins_per_chain', 'decimation_samples', 'diffusion_phase_samples',
          'orientation_block_samples', 'orientation_block_duration', *QUANTITIES]
PHYSICAL = {'parameters.txt', 'initial.csv', 'final.csv', 'samples.csv',
            'initial_bonds.csv', 'bond_statistics.csv', 'metadata.json',
            'equilibrium_schema.json', 'equilibrium_complete.json'} | {
                'equilibrium_' + kind + '.csv' for kind in
                ('backbone', 'tangents', 'sites', 'connectors', 'chains',
                 'events', 'positions', 'attachments')}
SPRINGS = {'fixed_slip_springs.csv', 'slip_springs_initial.csv',
           'slip_springs_final.csv', 'hopping_metadata.json'}


def load(path):
    def reject(value):
        raise ValueError(f'nonfinite JSON value: {path}: {value}')
    value = json.loads(path.read_text(), parse_constant=reject)
    json.dumps(value, allow_nan=False)  # Also reject numeric overflow such as 1e999.
    return value


def matches(actual, expected, label):
    for key, value in expected.items():
        require(key in actual and actual[key] == value, f'{label}: {key} mismatch')


def inventory(root):
    tree_bytes(root)  # Reject symlinks, including symlinked directories.
    return {str(p.relative_to(root)): file_record(p)
            for p in sorted(root.rglob('*')) if p.is_file()}


def curves(path, replica, chains):
    # For F=10001, L11/P16/m2: deepest populated level 10 is not exported.
    grid = [(ell, 1) for ell in range(16)] + [
        (ell * 2**k, 2**k) for k in range(1, 10) for ell in range(8, 16)]
    expected = itertools.product(chains, grid)
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == HEADER, f'correlation header mismatch: {path}')
        count = 0
        for row, support in itertools.zip_longest(reader, expected):
            require(row is not None and support is not None, f'correlation row count: {path}')
            chain, (lag, block) = support
            require(set(row) == set(HEADER) and row['chain'] == chain,
                    f'correlation chain/row mismatch: {path}')
            require(all(v is not None and math.isfinite(float(v))
                        for k, v in row.items() if k != 'chain'), f'nonfinite correlation: {path}')
            integers = {'replica': replica, 'lag_samples': lag, 'lag_steps': lag * 100,
                        'origins_per_chain': 10001 // block - lag // block,
                        'decimation_samples': block, 'diffusion_phase_samples': block - 1,
                        'orientation_block_samples': block}
            require(all(int(row[k]) == v for k, v in integers.items()),
                    f'correlation clock/count support: {path}')
            require(float(row['lag_time']) == (lag * 100) * 0.0001 and
                    float(row['orientation_block_duration']) == (block * 100) * 0.0001,
                    f'correlation lag time/block width: {path}')
            count += 1
    return count


def validate_output(root, run):
    """Completion/identity validation only; no curve fitting or scientific inference."""
    z, kappa, seed = run['Z'], run['kappa'], run['seed']
    physical = PHYSICAL | (SPRINGS if z else set())
    require({p.name for p in root.iterdir()} == physical | {'dynamics'}, 'output inventory')
    require(all((root / name).is_file() for name in physical), 'missing physical file')
    complete = load(root / 'equilibrium_complete.json')
    require(complete.get('complete') is True, 'physical completion flag')
    matches(complete, {'version': 1, 'complete': True, 'frames': 11}, 'physical completion')
    require(set(complete['files']) == physical - {'parameters.txt', 'equilibrium_complete.json'},
            'physical completion inventory')
    for name, size in complete['files'].items():
        require(type(size) is int and size == (root / name).stat().st_size,
                f'physical completion size: {name}')
    main = load(root / 'metadata.json')
    matches(main, {'model': 'finite-rest-length-Kratky-Porod', 'precision_bits': 64,
                   'timer_version': 1, 'springs': 32, 'chains': 256, 'beads_per_chain': 33,
                   'total_beads': 8448, 'dt': 0.0001, 'kbt': 1, 'zeta': 1,
                   'steps': 1000000, 'production_time': 100, 'sample': 5000, 'seed': seed,
                   'slip_count': z, 'slip_ms2': 5 if z else None, 'rng_domain': 3,
                   'slip_effective_stiffness': 0.6 if z else None,
                   'active_angles': 31 if kappa else 0,
                   'slip_mode': 'canonical-renewal-development' if z else 'disabled',
                   'initialization_method': 'CPU-direct-equilibrium'}, 'main metadata')
    require(list(map(float, (root / 'parameters.txt').read_text().split())) ==
            [32] + [1, 30] * 32 + [0] + [kappa] * 31 + [0], 'physical parameters file')
    matches(load(root / 'equilibrium_schema.json'), {
        'version': 1, 'phase': 'initial before dynamics; otherwise after BD and complete jump batch',
        'dt': 0.0001, 'legacy_sample_stride': 5000, 'steps': 1000000, 'chains': 256,
        'beads_per_chain': 33, 'slip_count': z, 'canonical': bool(z), 'expected_frames': 11,
        'snapshot_steps': [0, 1000000]}, 'equilibrium schema')
    if z:
        matches(load(root / 'hopping_metadata.json'),
                {'version': 2, 'rate': 100, 'interval_bd_steps': 1, 'end_renewal': True,
                 'batches': 1000000}, 'hopping identity')
    dynamics = root / 'dynamics'
    require({p.name for p in dynamics.iterdir()} ==
            {'metadata.json', 'chain_correlations.csv', 'replica_correlations.csv'},
            'incomplete/extra dynamical artifacts')
    m = load(dynamics / 'metadata.json')
    require(m.get('complete') is True, 'dynamical completion flag')
    matches(m, {'version': 1, 'complete': True, 'replica': run['replica_id'],
                'N': 32, 'chains': 256, 'beads_per_chain': 33, 'precision_bits': 64,
                'seed': seed, 'dt': 0.0001, 'kbt': 1, 'zeta': 1,
                'selected_beads': [0, 8, 16, 24, 32], 'first_step': 0, 'stride': 100,
                'integration_steps': 1000000, 'frames': 10001, 'last_step': 1000000,
                'correlator_levels': 11, 'correlator_slots': 16, 'correlator_m': 2,
                'memory_budget_bytes': 256 * 1024**2, 'shared_frames': 201,
                'extra_readbacks': 9800, 'shared_readback_bytes': 201 * 270336,
                'extra_readback_bytes': 9800 * 270336, 'deepest_populated_level_omitted': True,
                'incomplete_blocks_promoted': False, 'diffusion_point_width_samples': 1,
                'independent_replicas': 1, 'standard_error': None,
                'slip_count': z, 'slip_ms2': 5 if z else None,
                'slip_effective_stiffness': 0.6 if z else 0, 'hop_rate': 100,
                'end_renewal_requested': bool(z), 'end_renewal_active': bool(z),
                'initialization': 'CPU-direct-equilibrium', 'b0': [1] * 32,
                'kb': [30] * 32, 'kappa': [0] + [kappa] * 31 + [0],
                'initial_phase': 'initialized state before first BD update, after initial force/state validation',
                'phase': 'after BD, coordinate-buffer swap and entire hopping/end-renewal batch',
                'coordinates': 'unwrapped Cartesian; immutable flat chain-contiguous IDs',
                'diffusion_semantics': 'direct displacement; last-position decimation; point width=1; origin stride=b; phase=b-1',
                'orientation_semantics': 'unit/features formed at fine frames then averaged in blocks b; no block renormalization; triangular lag support'},
            'dynamical metadata')
    for key in ('effective_mobility_step', 'effective_noise'):
        require(m[key] == main[key], f'physical/dynamical {key} mismatch')
    rows = {name: curves(dynamics / name, run['replica_id'], chains) for name, chains in (
        ('chain_correlations.csv', map(str, range(256))), ('replica_correlations.csv', ['']))}
    # Sparse physical context: counts only, no new scientific interpretation.
    expected_rows = {'initial.csv': 8448, 'final.csv': 8448, 'samples.csv': 201 * 256,
                     'initial_bonds.csv': 8192, 'bond_statistics.csv': 8192,
                     'equilibrium_positions.csv': 2 * 8448,
                     'equilibrium_attachments.csv': 2 * z, 'equilibrium_events.csv': 11,
                     'equilibrium_sites.csv': 11 * 8448, 'equilibrium_connectors.csv': 11 * z,
                     'equilibrium_chains.csv': 11 * 256, 'equilibrium_tangents.csv': 11 * 256,
                     'equilibrium_backbone.csv': 0}  # These full frames reuse scalar rows.
    if z:
        expected_rows.update({name: z for name in SPRINGS if name.endswith('.csv')})
    for name, expected in expected_rows.items():
        with (root / name).open(newline='') as stream:
            reader = csv.DictReader(stream)
            require(reader.fieldnames is not None, f'missing CSV header: {name}')
            actual = 0
            for row in reader:
                require(None not in row and all(v is not None and math.isfinite(float(v))
                                                for v in row.values()), f'invalid context row: {name}')
                actual += 1
            require(actual == expected, f'context row count: {name}')
    return {'status': 'complete_identity_and_acquisition', 'curve_rows': rows,
            'scope': 'completeness/model/grid/finite-values only; no scientific acceptance'}


def gpu_state(manifest, env):
    uuid = manifest['gpu_uuid']
    fields = list(csv.reader(capture([
        'nvidia-smi', '-i', uuid,
        '--query-gpu=uuid,name,driver_version,compute_cap,memory.total,memory.free',
        '--format=csv,noheader,nounits'], env=env, timeout=10).splitlines()))
    require(len(fields) == 1 and len(fields[0]) == 6, 'ambiguous GPU query')
    actual, name, driver, arch, total, free = map(str.strip, fields[0])
    require(actual == uuid and arch == '8.6', 'GPU UUID/architecture mismatch')
    apps = capture(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                    '--format=csv,noheader,nounits'], env=env, timeout=10)
    require(not any(line.split(',')[0].strip() == uuid for line in apps.splitlines()),
            'GPU already has a compute process')
    return {'uuid': uuid, 'name': name, 'driver': driver, 'compute_capability': arch,
            'total_bytes': int(float(total) * 1024**2), 'free_bytes': int(float(free) * 1024**2)}


def identities(manifest):
    for name, expected in manifest['supervisor_dependencies'].items():
        require(digest(PROJECT / name) == expected, f'supervisor dependency changed: {name}')
    require(digest(manifest['executable']['path']) == manifest['executable']['sha256'],
            'executable hash mismatch')
    require(digest(manifest['build_provenance']['path']) == manifest['build_provenance']['sha256'],
            'build provenance hash mismatch')
    source = manifest['source']
    require(capture(['git', '-C', source['path'], 'rev-parse', 'HEAD']) == source['sha'], 'source SHA')
    require(not capture(['git', '-C', source['path'], 'status', '--porcelain']), 'dirty compiled source')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-reviewed-eight', action='store_true', required=True)
    parser.parse_args()
    start = time.monotonic()
    overall_deadline = start + 7200
    def interrupted(signum, frame):
        raise InterruptedError(f'signal {signum}: deadline or operator interruption')
    for sig in (signal.SIGALRM, signal.SIGTERM):
        signal.signal(sig, interrupted)
    def arm(deadline):
        remaining = deadline - time.monotonic()
        require(remaining > 0, 'campaign/run deadline exceeded')
        signal.setitimer(signal.ITIMER_REAL, remaining)
    arm(overall_deadline)
    manifest = load(CONFIG / 'manifest.json')
    require(digest(CONFIG / 'manifest.json') == MANIFEST_SHA, 'frozen manifest changed')
    require((CONFIG / 'manifest.sha256').read_text().split()[0] == MANIFEST_SHA, 'manifest sidecar')
    root = Path(manifest['output_root'])
    require(not root.exists() and not root.is_symlink(), 'refusing to overwrite/adopt campaign root')
    root.parent.mkdir(parents=True, exist_ok=True)
    lockdir = root.parent / '.locks'
    lockdir.mkdir(exist_ok=True)
    fd = os.open(lockdir / (manifest['gpu_uuid'] + '.lock'),
                 os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        root.mkdir()
        summary = {'status': 'preparing', 'started_utc': utc(), 'manifest_sha256': MANIFEST_SHA,
                   'completed_runs': [], 'run_records': [], 'failed_run': None}
        directory = None
        try:
            atomic(root / 'summary.json', summary)
            config = root / 'config'
            config.mkdir()
            for name, expected in manifest['schedules'].items():
                require(digest(CONFIG / name) == expected['sha256'], f'schedule changed: {name}')
                shutil.copyfile(CONFIG / name, config / name)
            shutil.copyfile(CONFIG / 'manifest.json', config / 'manifest.json')
            shutil.copyfile(CONFIG / 'manifest.sha256', config / 'manifest.sha256')
            for path in config.iterdir():
                path.chmod(0o444)
            (root / 'runs').mkdir()
            provenance = root / 'provenance'
            provenance.mkdir()
            # Preserve this runner and its imported supervisor/helper dependency closure.
            names = ['e1_d2a3_run.py', 'e1_d1_pilot_runner.py', 'e1_d1_pilot.py',
                     'e1_d1_pilot_auth.py', 'e1_observer_check.py']
            for name in names:
                shutil.copyfile(PROJECT / name, provenance / name)
            require(not capture(['git', '-C', PROJECT, 'status', '--porcelain']), 'dirty preparation checkout')
            identities(manifest)
            shutil.copyfile(manifest['build_provenance']['path'], provenance / 'build-settings.json')
            env = environment(manifest['toolchain']['CUDA_HOME'], manifest['gpu_uuid'])
            atomic(provenance / 'launch.json', {
                'preparation_sha': capture(['git', '-C', PROJECT, 'rev-parse', 'HEAD']),
                'manifest_sha256': MANIFEST_SHA, 'executable': file_record(manifest['executable']['path']),
                'platform': platform.platform(), 'python': sys.version,
                'cpu_affinity': sorted(os.sched_getaffinity(0)), 'child_environment': env,
                'tool_files': inventory(provenance), 'config_files': inventory(config),
                'limits': manifest['limits'],
                'execution_choice': 'all eight sequentially without intermediate confirmation'})
            limits = manifest['limits']
            require(shutil.disk_usage(root).free >= limits['initial_free_disk_bytes'], 'initial 18 GiB disk allowance')
            for run in manifest['runs']:
                directory = None
                summary['failed_run'] = run['id']
                run_start = time.monotonic()
                arm(min(overall_deadline, run_start + limits['per_run_seconds']))
                identities(manifest)
                require(digest(config / 'manifest.json') == MANIFEST_SHA, 'copied manifest changed')
                for name, expected in manifest['schedules'].items():
                    require(digest(config / name) == expected['sha256'], f'copied schedule changed: {name}')
                directory = root / 'runs' / run['id']
                directory.mkdir()
                gpu = gpu_state(manifest, env)
                atomic(directory / 'preflight.json', {
                    'utc': utc(), 'gpu': gpu, 'available_host_bytes': host_available(),
                    'free_disk_bytes': shutil.disk_usage(root).free})
                before = resource_check(root, limits, gpu['free_bytes'])
                atomic(directory / 'launch.json', {'utc': utc(), 'argv': run['argv'],
                                                   'gpu': gpu, 'resources': before})
                # Historical supervisor is schema-generic here: no old campaign execution path.
                process = run_process(run['argv'], directory, env, limits, root, start)
                require(process['status'] == 'exited' and process['exit_code'] == 0,
                        f"{run['id']}: {process['status']}")
                validation = validate_output(Path(run['output']), run)
                require(load(Path(run['output']) / 'metadata.json')['gpu'] == gpu['name'], 'executed GPU identity')
                identities(manifest)
                hashes = inventory(directory)
                atomic(directory / 'receipt.json', {'validation': validation, 'files': hashes,
                                                    'process': process, 'finished_utc': utc()})
                record = {'id': run['id'], 'process': process, 'output_bytes': tree_bytes(directory),
                          'stage_wall_seconds': time.monotonic() - run_start,
                          'disk_free_after_bytes': shutil.disk_usage(root).free,
                          'receipt': file_record(directory / 'receipt.json')}
                require(record['output_bytes'] <= limits['per_run_output_bytes'], 'run output cap after validation')
                require(record['disk_free_after_bytes'] >= limits['min_free_disk_bytes'], 'disk floor after run')
                summary['run_records'].append(record)
                summary['completed_runs'].append(run['id'])
                summary['status'] = 'running'
                atomic(root / 'summary.json', summary)
                require(tree_bytes(root) <= limits['aggregate_output_bytes'], 'campaign output cap')
                arm(overall_deadline)
                print(f"Completed {run['id']} ({len(summary['completed_runs'])}/8)", flush=True)
            summary['failed_run'] = None
            summary['status'] = 'completed_eight_runs_not_scientific_acceptance'
            summary['finished_utc'] = utc()
            summary['wall_seconds'] = time.monotonic() - start
            summary['max_child_rss_bytes'] = max(r['process']['max_rss_bytes'] for r in summary['run_records'])
            summary['child_wall_seconds_sum'] = sum(r['process']['wall_seconds'] for r in summary['run_records'])
            summary['gpu_peak_memory_bytes'] = None  # Launch headroom is not a peak measurement.
            summary['campaign_bytes_before_final_summary'] = tree_bytes(root)
            atomic(root / 'summary.json', summary)
            require(tree_bytes(root) <= limits['aggregate_output_bytes'], 'final campaign output cap')
        except BaseException as error:
            signal.setitimer(signal.ITIMER_REAL, 0)
            summary.update(status='stopped', error=f'{type(error).__name__}: {error}',
                           finished_utc=utc(), wall_seconds=time.monotonic() - start)
            if directory is not None:
                summary['partial_run_directory'] = str(directory)
                try:
                    # Bound emergency hashing; preserve raw evidence even if hashing fails.
                    signal.setitimer(signal.ITIMER_REAL, 10)
                    summary['partial_run_bytes'] = tree_bytes(directory)
                    if (directory / 'process.json').is_file():
                        summary['failed_process'] = load(directory / 'process.json')
                    atomic(directory / 'failure.json', {'utc': utc(), 'error': summary['error'],
                                                        'files': inventory(directory)})
                except BaseException as receipt_error:
                    summary['failure_inventory_error'] = str(receipt_error)
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
            atomic(root / 'summary.json', summary)
            raise
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    print(f'Campaign complete; resource summary: {root / "summary.json"}')


if __name__ == '__main__':
    main()
