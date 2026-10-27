"""Prepared, UNEXECUTED tiny GPU integration checks; explicit separate review required.

No builds, benchmarks, campaign or historical analysis. Importing does not run.
Both binaries must be independently prepared with matching precision/toolchain.
The baseline must be from 0b177a62cf33bcd1143aba98cb83931fecbda9d1.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

# Only named measurement fields may differ; unknown differences fail.
MAIN_TIMING = {
    'initialization_seconds', 'integration_seconds', 'production_wall_seconds',
    'observation_seconds', 'recurrent_output_seconds', 'final_output_seconds',
    'force_and_diagnostic_wall_seconds', 'integration_ns_per_bead_step',
    'overall_ns_per_bead_step', 'bead_updates_per_second',
}
EQUILIBRIUM_TIMING = {'exclusive_seconds', 'observer_wall_seconds', 'transfer_seconds'}
DYNAMICS_TIMING = {
    'shared_readback_seconds', 'extra_readback_seconds',
    'acquisition_cpu_seconds', 'evaluation_csv_seconds',
}


def require(condition, why):
    if not condition:
        raise AssertionError(why)


def load(path):
    return json.loads(path.read_text())


def same_json(a, b, ignored):
    left, right = load(a), load(b)
    require(left.keys() == right.keys(), f'metadata schema mismatch: {a.name}')
    require(ignored <= left.keys(), f'expected timing fields absent: {a.name}')
    require({k: v for k, v in left.items() if k not in ignored} ==
            {k: v for k, v in right.items() if k not in ignored},
            f'physical/structural metadata mismatch: {a.name}')


def same_physics(a, b):
    left = {p.name for p in a.iterdir() if p.is_file()}
    right = {p.name for p in b.iterdir() if p.is_file()}
    require(left == right, 'legacy output file set changed')
    require({'initial.csv', 'final.csv', 'equilibrium_positions.csv',
             'equilibrium_attachments.csv', 'equilibrium_events.csv'} <= left,
            'joint-state/event evidence missing')
    for name in sorted(left):
        if name == 'metadata.json':
            same_json(a / name, b / name, MAIN_TIMING)
        elif name == 'equilibrium_complete.json':
            same_json(a / name, b / name, EQUILIBRIUM_TIMING)
        else:
            require((a / name).read_bytes() == (b / name).read_bytes(),
                    f'byte-identity mismatch: {name}')


def check_dynamics(run, z, kappa):
    root = run / 'dynamics'
    require(root.is_dir(), 'enabled output missing')
    require({p.name for p in root.iterdir()} ==
            {'metadata.json', 'chain_correlations.csv', 'replica_correlations.csv'},
            'unexpected/partial dynamical artifacts')
    m = load(root / 'metadata.json')
    require(m['complete'] and m['N'] == 32 and m['chains'] == 2 and m['replica'] == 77,
            'model dimensions/replica')
    require(m['selected_beads'] == [0, 8, 16, 24, 32], 'selected mapping')
    require((m['first_step'], m['stride'], m['frames'], m['last_step']) == (0, 3, 9, 24),
            'acquisition clock or initial frame')
    require((m['shared_frames'], m['extra_readbacks']) == (3, 6), 'shared/extra readback phase')
    frame_bytes = 66 * 4 * (m['precision_bits'] // 8)
    require(m['shared_readback_bytes'] == 3 * frame_bytes and m['extra_readback_bytes'] == 6 * frame_bytes,
            'full-coordinate readback accounting')
    physical = load(run / 'metadata.json')
    for key in ('precision_bits', 'dt', 'kbt', 'zeta', 'seed', 'slip_count', 'slip_ms2',
                'effective_mobility_step', 'effective_noise'):
        require(m[key] == physical[key], f'model metadata mismatch: {key}')
    if z:
        require(m['slip_effective_stiffness'] == physical['slip_effective_stiffness'],
                'rounded spring coefficient metadata')
    require(m['independent_replicas'] == 1 and m['standard_error'] is None,
            'single run invented uncertainty')
    require(m['slip_count'] == z and m['end_renewal_active'] == bool(z), 'active E1 metadata')
    require(m['b0'] == [1] * 32 and m['kb'] == [30] * 32 and
            m['kappa'] == [0] + [kappa] * 31 + [0], 'actual backbone coefficients')
    require('last-position decimation' in m['diffusion_semantics'] and
            'triangular lag support' in m['orientation_semantics'], 'support semantics')
    for filename, multiplier in [('chain_correlations.csv', 2), ('replica_correlations.csv', 1)]:
        with (root / filename).open() as stream:
            rows = list(csv.DictReader(stream))
        require(rows, 'empty correlation curves')
        for row in rows:
            require(int(row['replica']) == 77, 'CSV replica identity')
            lag, block = int(row['lag_samples']), int(row['decimation_samples'])
            require(int(row['lag_steps']) == 3 * lag and
                    int(row['origins_per_chain']) == 9 // block - lag // block and
                    int(row['diffusion_phase_samples']) == block - 1,
                    'exported lag/count convention')
        zero = [row for row in rows if int(row['lag_samples']) == 0]
        require(len(zero) == multiplier, 'initial fine zero-lag rows')
        for row in zero:
            require(all(float(row[key]) == 0 for key in
                        ('cm_msd', 'bead0_msd', 'bead8_msd', 'bead16_msd', 'bead24_msd', 'bead32_msd')),
                    'initial MSD not zero')
            require(abs(float(row['c1']) - 1) < 3e-11 and abs(float(row['c2']) - 1) < 3e-11,
                    'fine zero-lag direction normalization')
        require({row['chain'] for row in rows} == ({'0', '1'} if multiplier == 2 else {''}),
                'CSV immutable chain identity')
    return m


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-reviewed-tiny', action='store_true', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--baseline-binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    binary, baseline = args.binary.resolve(strict=True), args.baseline_binary.resolve(strict=True)
    require(binary != baseline and binary.read_bytes() != baseline.read_bytes(),
            'a separate pre-integration baseline executable is required')
    root = args.output.resolve()
    root.mkdir(parents=False, exist_ok=False)  # Permanent new output; never overwrite/cleanup.
    steps = root / 'steps.txt'
    steps.write_text('\n'.join(map(str, range(0, 25, 4))) + '\n')
    common = ['--springs', '32', '--chains', '2', '--dt', '.0001', '--steps', '24',
              '--sample', '4', '--seed', '4317', '--stress-mode', 'off',
              '--equilibrium-steps', str(steps), '--equilibrium-snapshots', str(steps)]

    def run(executable, label, physical, extra=(), success=True):
        target = root / label
        command = [str(executable), *common, *physical, '--output', str(target), *extra]
        with (root / (label + '.log')).open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        require((result.returncode == 0) == success, f'unexpected exit: {label}')
        if not success:
            require(not target.exists(), f'invalid configuration progressed to output/GPU setup: {label}')
        return target

    for case, (z, kappa) in enumerate(((0, 0), (32, 10))):
        physical = ['--slip-count', str(z), '--slip-ms2', '5', '--hop-rate', '10000',
                    '--end-renewal', '1', '--kappa', str(kappa)]
        base = run(baseline, f'c{case}-baseline', physical)
        off = run(binary, f'c{case}-off', physical)
        explicit = run(binary, f'c{case}-explicit-off', physical, ['--dynamics', '0'])
        enabled = ['--dynamics', '1', '--dynamics-stride', '3', '--dynamics-levels', '4',
                   '--dynamics-slots', '4', '--dynamics-m', '2', '--dynamics-replica', '77']
        on = run(binary, f'c{case}-on', physical, enabled)
        replay = run(binary, f'c{case}-replay', physical, enabled)
        for current in (off, explicit, on, replay):
            same_physics(base, current)
        require(not (off / 'dynamics').exists() and not (explicit / 'dynamics').exists(),
                'default-off allocated dynamic output')
        check_dynamics(on, z, kappa)
        check_dynamics(replay, z, kappa)
        for name in ('chain_correlations.csv', 'replica_correlations.csv'):
            require((on / 'dynamics' / name).read_bytes() == (replay / 'dynamics' / name).read_bytes(),
                    f'dynamic replay mismatch: {name}')
        same_json(on / 'dynamics/metadata.json', replay / 'dynamics/metadata.json', DYNAMICS_TIMING)

    invalid = [
        ['--dynamics', '2'],
        ['--dynamics', '1', '--springs', '8'],
        ['--dynamics', '1', '--dynamics-stride', '0'],
        ['--dynamics', '1', '--dynamics-levels', '0'],
        ['--dynamics', '1', '--dynamics-slots', '7'],
        ['--dynamics', '1', '--dynamics-mib', '0'],
        ['--dynamics', '1', '--dynamics-levels', '20', '--dynamics-slots', '64', '--dynamics-mib', '1'],
        ['--dynamics', '1', '--dynamics-output', '../escape'],
        ['--dynamics', '1', '--force-input', str(root / 'not-an-input')],
    ]
    for index, options in enumerate(invalid):
        run(binary, f'invalid-{index}', [], options, success=False)
    # Build provenance remains the caller's responsibility; hashes identify bytes only.
    (root / 'verification.json').write_text(json.dumps({
        'status': 'tiny_checks_completed', 'baseline_source_expected': '0b177a62cf33bcd1143aba98cb83931fecbda9d1',
        'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'baseline_binary_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
        'scope': 'two bounded fixtures, strict saved physical records and deterministic replay; not a scientific campaign',
    }, indent=2) + '\n')
    print('PASS tiny integration fixtures; no equilibrium or performance acceptance')


if __name__ == '__main__':
    main()
