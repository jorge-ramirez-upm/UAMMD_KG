"""Private bounded CPU reference worker. Invoke through e1_d16a2_local.py only."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import resource
import signal
import time

import numpy as np

import e1_d16a2_reference as ref
import e1_d16a2_local as control
from semiflexible_reference import Chain


def parent_guard(expected_pid):
    # Linux parent-death guard: losing the resource supervisor must stop draws.
    libc = ctypes.CDLL(None, use_errno=True)
    control.require(libc.prctl(1, signal.SIGKILL, 0, 0, 0) == 0, 'cannot install parent-death guard')
    control.require(expected_pid == os.getppid(), 'worker lost its authenticated local supervisor')


def run(root, kappa):
    session, project = control.checked(root)
    case = root/f'kappa-{kappa}'
    launch = control.load(case/'launch.json')
    parent_guard(launch['parent_pid'])
    control.require(launch['parent_pid'] == os.getppid() and launch['kappa'] == kappa,
                    'worker requires its authenticated local supervisor')
    control.approved(root, Path(launch['approval_path']), launch['approval_sha256'])
    control.require(control.proof(Path(__file__)) == session['sources']['e1_d16a2_sampling.py'], 'worker changed')
    control.write(case/'worker-started.json', {'schema': 'e1-d16a2-worker-start-v1', 'pid': os.getpid()})
    numerical = control.load(root/'numerical.json')
    chain = Chain.homogeneous(32, 1., 30., kappa)
    started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_FSIZE, (control.LIMITS['output_bytes'], control.LIMITS['output_bytes']))
    observed_peak = 0

    def progress(value):
        temporary = case/'progress.next'
        control.write(temporary, value)
        os.replace(temporary, case/'progress.json')

    def bounded():
        nonlocal observed_peak
        observed_peak = max(observed_peak, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        control.resource_require(observed_peak <= control.LIMITS['rss_bytes'], 'reference RSS limit exceeded')
        control.resource_require(time.monotonic()-started <= control.LIMITS['stiffness_seconds'], 'reference wall limit exceeded')
        control.resource_require(control.case_bytes(root, kappa) < control.LIMITS['output_bytes']-65536, 'reference output limit exceeded')
        control.resource_preflight(root)

    def phase(number, count, cuts=None):
        control.require(count % ref.BATCH == 0, 'partial batch prohibited')
        path = case/f'phase-{number}-xy.npy'
        control.require(not path.exists(), 'no overwrite/resume')
        scalar = np.lib.format.open_memmap(path, mode='w+', dtype=np.float64, shape=(count, 2))
        rows = []
        with (case/f'phase-{number}-batches.jsonl').open('x') as batch_file:
            for index in range(count//ref.BATCH):
                bounded()
                batch_started = time.monotonic()
                progress({'active': True, 'phase': number, 'batch': index, 'started_monotonic': batch_started})
                entropy = [721612000, kappa, number, index]
                seed = np.random.SeedSequence(entropy)
                rng = np.random.Generator(np.random.PCG64(seed))
                before = rng.bit_generator.state
                positions = chain.sample(ref.BATCH, rng, kbt=1.)
                with np.errstate(over='raise', invalid='raise', divide='raise'):
                    ref.require(positions.shape == (ref.BATCH, 33, 3) and np.isfinite(positions).all(),
                                    'nonfinite/incomplete accepted-sampler batch')
                    end = positions[:, -1]-positions[:, 0]
                    centered = positions-positions.mean(axis=1, keepdims=True)
                    xy = np.column_stack((np.sum(end*end, axis=1), np.mean(np.sum(centered*centered, axis=2), axis=1)))
                    ref.require(np.isfinite(xy).all() and (xy > 0).all(), 'nonfinite/degenerate chain observables')
                    scalar[index*ref.BATCH:(index+1)*ref.BATCH] = xy
                    row = ref.batch_summary(xy, cuts) if cuts is not None else {'count': ref.BATCH}
                    bonds = np.diff(positions, axis=1)
                    lengths = np.linalg.norm(bonds, axis=2)
                    ref.require((lengths > 0).all(), 'collapsed reference bond')
                    tangents = bonds/lengths[:, :, None]
                    row['sampler_diagnostics'] = {
                        'mean_radial': float(lengths.mean()), 'mean_radial2': float(np.mean(lengths**2)),
                        'tangent': {str(lag): float(np.mean(np.sum(tangents[:, :-lag]*tangents[:, lag:], axis=2)))
                                    for lag in (1, 2, 4, 8, 16)}}
                row.update(phase=number, batch=index, seed_entropy=entropy,
                           seed_generated_uint32=seed.generate_state(4).tolist(),
                           pcg64_before=before, pcg64_after=rng.bit_generator.state,
                           wall_seconds=time.monotonic()-batch_started)
                control.resource_require(row['wall_seconds'] <= control.LIMITS['batch_seconds'], 'batch time limit exceeded')
                batch_file.write(json.dumps(row, sort_keys=True, allow_nan=False, separators=(',', ':'))+'\n')
                batch_file.flush()
                rows.append(row)
                scalar.flush()
                bounded()
                control.resource_require(time.monotonic()-batch_started <= control.LIMITS['batch_seconds'],
                                'batch time limit exceeded including writes')
                progress({'active': False, 'phase': number, 'completed_batches': index+1})
        del scalar
        return np.load(path, mmap_mode='r', allow_pickle=False), rows

    calibration, calibration_rows = phase(1, ref.CALIBRATION)
    sorted_xy, quantiles = ref.freeze_quantiles(calibration)
    with (case/'calibration-sorted.npy').open('xb') as stream:
        np.save(stream, sorted_xy, allow_pickle=False)
    control.write(case/'quantiles.json', quantiles)
    pilot_xy, pilot_rows = phase(2, ref.PILOT, quantiles['cuts'])
    pilot = ref.inference(pilot_rows)
    selection = ref.select_size(pilot, numerical['flexible'] if kappa == 0 else None)
    control.write(case/'pilot-inference.json', pilot)
    control.write(case/'selection.json', selection)
    status = 'MOMENTS_PRECISION_UNRESOLVED'
    final = None
    assessment = {'schema': ref.SCHEMA, 'status': status, 'moments_status': status,
                  'cdf_status': 'CDF_PRECISION_UNRESOLVED', 'moments_accepted': False,
                  'cdf_precision_pass': False, 'consistency_status': 'NOT_ASSESSED',
                  'observables': [], 'final_assessment_performed': False,
                  'reason': 'no final size in frozen grid satisfies moment-only pilot prediction; no final draws'}
    if selection['selected_count'] is not None:
        final_xy, final_rows = phase(3, selection['selected_count'], quantiles['cuts'])
        final = ref.inference(final_rows)
        control.write(case/'final-inference.json', final)
        # A single preselected final sample is assessed once; no adaptive extension.
        assessment = ref.assess(final, numerical, kappa)
        status = assessment['status']
        exact_mean = numerical['size_means'][str(kappa)]['mean_X']
        variance = numerical['flexible']['var_X'] if kappa == 0 else final['estimate'][2]
        joint = ref.joint_variances(exact_mean, variance)
        variance_interval = ([variance-numerical['flexible_absolute_error_estimates']['var_X'],
                              variance+numerical['flexible_absolute_error_estimates']['var_X']]
                             if kappa == 0 else final['interval'][2])
        mean_error = numerical['size_mean_absolute_error_estimates'][str(kappa)]['mean_X']
        joint['v_f_interval'] = [max(0, variance_interval[0])/(exact_mean+mean_error)**2,
                                 max(0, variance_interval[1])/(exact_mean-mean_error)**2]
        joint['var_A_interval'] = [v/256 for v in joint['v_f_interval']]
        joint['var_B_interval'] = [2*v/(3*2048) for v in joint['v_f_interval']]
        control.write(case/'joint-null-law.json', joint)
    control.write(case/'assessment.json', assessment)
    bounded()
    control.write(case/'worker-result.json', {
        'schema': 'e1-d16a2-worker-result-v1',
        'status': status, 'kappa': kappa,
        'moments_status': assessment['moments_status'], 'cdf_status': assessment['cdf_status'],
        'moments_accepted': assessment['moments_accepted'],
        'primary_moment_reference': 'ANALYTICAL_EXACT' if kappa == 0 else 'INDEPENDENT_FINAL_SAMPLE_REQUIRES_ACCEPTANCE', 'selected_final_count': selection['selected_count'],
        'actual_counts': {'calibration': ref.CALIBRATION, 'pilot': ref.PILOT,
                          'final': final['count'] if final is not None else 0},
        'peak_host_rss_bytes': observed_peak, 'worker_wall_seconds': time.monotonic()-started,
        'config': control.proof(root/'config.json'), 'quantiles': control.proof(case/'quantiles.json'),
        'seed_ledger': 'phase-*-batches.jsonl: entropy, generated identity, before/after PCG64 states; zero-based batch indices',
        'interpretation': 'independent backbone reference only; not dynamical equilibrium preservation'})


def verify_saved(root, kappa):
    """Read-only local Stage C consistency analysis; no new random samples."""
    control.authenticate_case(root, kappa)
    case = root/f'kappa-{kappa}'
    numerical = control.load(root/'numerical.json')
    quantiles = control.load(case/'quantiles.json')
    calibration = np.load(case/'phase-1-xy.npy', mmap_mode='r', allow_pickle=False)
    sorted_xy, expected_quantiles = ref.freeze_quantiles(calibration)
    control.require(expected_quantiles == quantiles, 'calibration/cut identity mismatch')
    control.require(np.array_equal(sorted_xy, np.load(case/'calibration-sorted.npy', allow_pickle=False)), 'sorted calibration changed')
    result = control.load(case/'worker-result.json')
    phases = []
    for phase, count in ((1, ref.CALIBRATION), (2, ref.PILOT), (3, result['actual_counts']['final'])):
        if count == 0:
            continue
        xy = np.load(case/f'phase-{phase}-xy.npy', mmap_mode='r', allow_pickle=False)
        control.require(xy.shape == (count, 2) and xy.dtype == np.float64
                        and np.isfinite(xy).all() and (xy > 0).all(), 'scalar evidence invalid/incomplete')
        with (case/f'phase-{phase}-batches.jsonl').open() as stream:
            rows = [json.loads(line) for line in stream]
        control.require(len(rows) == count//ref.BATCH, 'batch coverage changed')
        for index, row in enumerate(rows):
            control.require(row['seed_entropy'] == [ref.SEED_NAMESPACE, kappa, phase, index], 'seed entropy changed')
            seed = np.random.SeedSequence([721612000, kappa, phase, index])
            expected_rng = np.random.Generator(np.random.PCG64(seed))
            control.require(seed.generate_state(4).tolist() == row['seed_generated_uint32']
                            and expected_rng.bit_generator.state == row['pcg64_before'], 'seed/RNG initial state mismatch')
            if phase != 1:
                expected = ref.batch_summary(xy[index*ref.BATCH:(index+1)*ref.BATCH], quantiles['cuts'])
                control.require(all(row[name] == value for name, value in expected.items()), 'batch sufficient statistics changed')
        if phase != 1:
            inferred = ref.inference(rows)
            filename = 'pilot-inference.json' if phase == 2 else 'final-inference.json'
            control.require(inferred == control.load(case/filename), 'inference not reproducible from batch statistics')
            if phase == 2:
                control.require(ref.select_size(inferred, numerical['flexible'] if kappa == 0 else None)
                                == control.load(case/'selection.json'), 'size-selection identity changed')
            else:
                control.require(ref.assess(inferred, numerical, kappa) == control.load(case/'assessment.json'), 'assessment changed')
        phases.append({'phase': phase, 'count': count, 'batches': len(rows)})
    return {'status': 'AUTHENTICATED_AND_RECOMPUTED', 'kappa': kappa, 'phases': phases,
            'completion': control.proof(case/'completion.json'), 'new_equilibrium_draws': 0,
            'qualification': 'recomputed from scalar evidence and batch sufficient statistics; no independent new scientific validation'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--kappa', type=int, choices=(0, 10), required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        run(root, args.kappa)
    except BaseException as error:
        case = root/f'kappa-{args.kappa}'
        if case.is_dir() and not (case/'worker-failure.json').exists():
            control.write(case/'worker-failure.json', {
                'schema': 'e1-d16a2-failure-v1',
                'status': ('AUTHENTICATION_FAILED' if not (case/'worker-started.json').exists() else
                           'RESOURCE_FAILED' if isinstance(error, control.ResourceFailure) else
                           'NUMERICAL_CONSISTENCY_FAILED' if isinstance(error, ref.NumericalConsistencyFailure)
                           else 'EXECUTION_FAILED'),
                'error': str(error) or type(error).__name__})
        raise
