#!/usr/bin/env python3
"""Frozen D1 pilot specification and small provenance helpers. Never runs dynamics."""
import argparse
import datetime
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parent
REPOSITORY = PROJECT.parents[1]
ACCEPTED_SHA = '0dea651b58171a72206774bcebb2f4c74960069b'
REPOSITORY_ID = 'github.com/jorge-ramirez-upm/UAMMD_KG'
CONFIG = PROJECT / 'e1_d1_pilot_config'
BASE_CASES = ((8, 0, 16, 10), (8, 10, 4, 100), (32, 0, 4, 100), (32, 10, 16, 10))
TIMESTEPS = ('0.0001', '0.00025')
ACCEPTED_FILES = (
    'semiflexible.cu', 'semiflexible.cuh', 'semiflexible_slipspring.cuh',
    'fixed_slip_springs.h', 'slip_hopping.h', 'slip_hopping.cuh', 'slip_renewal.cuh',
    'e1_equilibrium_observer.h', 'e1_observer_check.py', 'semiflexible_reference.py',
    'semiflexible_scalar_output.h', 'semiflexible_stress.cuh', 'semiflexible_stress_stream.h',
    'stream_correlator.h', 'cpu_workers.h', 'tests/chain_major_correlator.h', 'Makefile',
    'EQUILIBRIUM_MODEL_E1.md', 'E1_STAGE_D_VALIDATION_PROTOCOL.md',
    'E1_STAGE_D_TIMESTEP_SCREENING.md', 'E1_STAGE_D1_OBSERVER_REPORT.md',
)
TOOL_FILES = ('e1_d1_pilot.py', 'e1_d1_pilot_auth.py', 'e1_d1_pilot_runner.py',
              'e1_d1_pilot_analysis.py')


class Invalid(ValueError):
    pass


def require(ok, why):
    if not ok:
        raise Invalid(why)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def identity(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    require(Path(path).stat().st_size <= 32*1024*1024, 'JSON file exceeds bounded size')
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(Invalid('nonfinite JSON: '+x)))


def output_path(path, protected_source=None):
    path=Path(path).resolve()
    if protected_source is not None:
        require(not path.is_relative_to(Path(protected_source).resolve()),'output must stay outside the pinned source checkout')
    for parent in (path,*path.parents):
        marker=parent/'.git'
        if marker.is_file() or (marker.is_dir() and (marker/'HEAD').is_file()):
            require(parent==REPOSITORY and path.is_relative_to(PROJECT),
                    'repository writes must stay under this examples/slip-springs project')
            break
    return path


def atomic(path, value):
    path = Path(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.'+path.name, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(encoded(value)); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def capture(argv, cwd=None, env=None, timeout=20):
    p = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True,
                       text=True, timeout=timeout)
    require(p.returncode == 0, f'command failed: {argv}: {p.stderr.strip()}')
    return p.stdout.strip()


def file_record(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'missing/nonregular/symlink file: '+str(path))
    before = path.stat()
    value = {'bytes': before.st_size, 'sha256': digest(path)}
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_ino) ==
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_ino), 'file changed while hashing')
    return value


def shared_ticks():
    # One tick = .0005. Dense through .01; late spacing .005 through .25.
    return list(range(21)) + list(range(30, 501, 10))


def exact_step(time, dt):
    step = Fraction(time) / Fraction(dt)
    require(step.denominator == 1 and step >= 0, 'unrepresentable observation time')
    return int(step)


def schedule(dt):
    shared = [exact_step(Fraction(t, 2000), dt) for t in shared_ticks()]
    steps = sorted(set(shared) | {1})
    snapshots = sorted({0, 1} | {exact_step(t, dt) for t in ('0.0005', '0.01', '0.05', '0.25')})
    return {'steps': steps, 'shared_steps': shared, 'diagnostic_only_steps': [1],
            'snapshot_steps': snapshots, 'legacy_stride': exact_step('0.005', dt)}


def schedule_text(steps):
    return ''.join(str(s)+'\n' for s in steps).encode()


def schedule_name(dt, snapshots=False):
    return 'snapshots-'*snapshots + 'dt'+dt+'.steps'


def round_half_up(value):
    value = Fraction(value)
    return (2*value.numerator + value.denominator)//(2*value.denominator)


def source_hashes():
    return {name: hashlib.sha256(subprocess.check_output(
        ['git', '-C', str(REPOSITORY), 'show', ACCEPTED_SHA+':examples/slip-springs/'+name])).hexdigest()
            for name in ACCEPTED_FILES}


def tool_hashes():
    return {name: digest(PROJECT/name) for name in TOOL_FILES}


def proposed_manifest():
    schedules = {}
    for dt in TIMESTEPS:
        s = schedule(dt)
        for snapshots in (False, True):
            name = schedule_name(dt, snapshots)
            values = s['snapshot_steps'] if snapshots else s['steps']
            schedules[name] = {'sha256': hashlib.sha256(schedule_text(values)).hexdigest(), 'steps': values}
    runs = []
    for base, (n, kappa, ne, nu) in enumerate(BASE_CASES):
        for level, dt in enumerate(TIMESTEPS):
            cell = 2*base+level+1
            z = round_half_up(Fraction(64*n, ne)); rho = Fraction(z, 64*(n+1))
            for replica in range(1, 5):
                runs.append({'id': f'cell{cell:02d}-replica{replica:02d}', 'cell': cell,
                             'replica': replica, 'seed': 620261000+100*cell+replica,
                             'N': n, 'kappa': kappa, 'Ne': ne, 'nu_hop': nu, 'M': 64,
                             'Z': z, 'rho': {'numerator': rho.numerator, 'denominator': rho.denominator},
                             'dt': dt, 'steps': exact_step('0.25', dt),
                             'sample': schedule(dt)['legacy_stride'],
                             'schedule': schedule_name(dt), 'snapshots': schedule_name(dt, True)})
    return {'version': 1, 'campaign': 'e1-stage-d1-pilot-v1',
            'purpose': 'exploratory feasibility, replica variance and timestep sensitivity; no equivalence decision',
            'repository': REPOSITORY_ID, 'accepted_source_sha': ACCEPTED_SHA,
            'accepted_sources': source_hashes(), 'preparation_sources': tool_hashes(),
            'common': {'b0': 1, 'kb': 30, 'kbt': 1, 'zeta': 1, 'A2': 5, 'T': '0.25',
                       'precision_bits': 64, 'end_renewal': True, 'stress': 'off', 'scalar_output': 'full'},
            'pairing': 'independent across every cell and replica; no shared initial states',
            'shared_time_ticks': shared_ticks(), 'tick_duration': '0.0005',
            'schedules': schedules, 'runs': runs,
            'execution_authorized': False,
            'd0_candidate_caps': {'per_run_seconds': 120, 'aggregate_seconds': 3600,
                                  'aggregate_output_bytes': 5*1024**3},
            'approved_limits': None}


def validate_manifest(path, expected_hash):
    require(isinstance(expected_hash, str) and len(expected_hash) == 64, 'explicit trusted manifest SHA256 required')
    require(digest(path) == expected_hash, 'manifest SHA256 mismatch')
    manifest = load(path)
    require(encoded(manifest) == encoded(proposed_manifest()), 'manifest differs from frozen matrix, source identities or tool identities')
    for name, record in manifest['schedules'].items():
        target = Path(path).parent/name
        require(target.read_bytes() == schedule_text(record['steps']) and digest(target) == record['sha256'],
                'schedule identity/content mismatch: '+name)
    require(len(manifest['runs']) == 32 and len({r['seed'] for r in manifest['runs']}) == 32,
            '32 independent replica seeds required')
    return manifest


def command(run, binary, output, config):
    return [str(binary), '--output', str(output), '--springs', str(run['N']), '--chains', str(run['M']),
            '--b0', '1', '--kb', '30', '--kappa', str(run['kappa']), '--kbt', '1', '--zeta', '1',
            '--dt', run['dt'], '--steps', str(run['steps']), '--sample', str(run['sample']),
            '--seed', str(run['seed']), '--slip-count', str(run['Z']), '--slip-ms2', '5',
            '--hop-rate', str(run['nu_hop']), '--end-renewal', '1', '--stress-mode', 'off',
            '--scalar-output', 'full', '--equilibrium-steps', str(Path(config)/run['schedule']),
            '--equilibrium-snapshots', str(Path(config)/run['snapshots'])]


def source_identity(source):
    source = Path(source).resolve()
    require(capture(['git', '-C', source, 'rev-parse', 'HEAD']) == ACCEPTED_SHA, 'source HEAD is not accepted D1.0')
    require(not capture(['git', '-C', source, 'status', '--porcelain', '--untracked-files=all']), 'source tree is dirty')
    origin = capture(['git', '-C', source, 'remote', 'get-url', 'origin'])
    require(origin in ('git@github.com:jorge-ramirez-upm/UAMMD_KG.git',
                       'https://github.com/jorge-ramirez-upm/UAMMD_KG.git'), 'repository origin mismatch')
    for name, sha in source_hashes().items():
        require(digest(source/'examples/slip-springs'/name) == sha, 'accepted source changed: '+name)
    return {'repository': REPOSITORY_ID, 'sha': ACCEPTED_SHA, 'origin': origin, 'path': str(source)}


def row_counts(run, observation_steps=None, snapshot_steps=None):
    s = schedule(run['dt'])
    observations = s['steps'] if observation_steps is None else observation_steps
    snapshots = s['snapshot_steps'] if snapshot_steps is None else snapshot_steps
    f = len(observations); m = run['M']; l = m*(run['N']+1); z = run['Z']
    regular = run['steps']//run['sample']+1
    extra = sum(step % run['sample'] != 0 for step in observations); snaps = len(snapshots)
    return {'samples.csv': m*regular, 'equilibrium_backbone.csv': m*extra,
            'equilibrium_tangents.csv': m*f if run['N']>8 else 0,
            'equilibrium_sites.csv': l*f, 'equilibrium_connectors.csv': z*f,
            'equilibrium_chains.csv': m*f, 'equilibrium_events.csv': f,
            'equilibrium_positions.csv': l*snaps, 'equilibrium_attachments.csv': z*snaps,
            'initial.csv': l, 'final.csv': l, 'initial_bonds.csv': m*run['N'],
            'bond_statistics.csv': m*run['N'], 'fixed_slip_springs.csv': z,
            'slip_springs_initial.csv': z, 'slip_springs_final.csv': z}


def state_estimate(run):
    # Accepted D1.0 explicit allocation formulas, double precision; no CUDA
    # context, allocator, stream buffers, compiler local/register or RSS claim.
    m=run['N']+1;l=run['M']*m;z=run['Z'];n=run['N']
    return {'device_array_bytes':132*l+48*z+16*n+(8*m if run['kappa'] else 0)+92,
            'legacy_workspace_estimate_bytes':1356*l+96*z+88,
            'observer_vector_bytes':40*(run['M']+z)+8*l}


def estimates(manifest):
    runs = manifest['runs']
    return {'runs': len(runs), 'cells': 8, 'replica_bd_steps': sum(r['steps'] for r in runs),
            'bead_updates': sum(r['steps']*r['M']*(r['N']+1) for r in runs),
            'expected_attempts': sum(r['Z']*r['nu_hop']*.25 for r in runs),
            'csv_rows': sum(sum(row_counts(r).values()) for r in runs),
            'csv_planning_bytes_at_256_per_row': 256*sum(sum(row_counts(r).values()) for r in runs),
            'state_by_cell':{str(r['cell']):state_estimate(r) for r in runs if r['replica']==1},
            'runtime_seconds': None, 'note': 'CSV byte assumption excludes headers/JSON/logs; no compression or linear runtime guarantee'}


def validate_limits(limits):
    keys={'per_run_seconds','aggregate_seconds','per_run_output_bytes','aggregate_output_bytes',
          'min_free_disk_bytes','min_free_gpu_bytes','max_host_rss_bytes','min_available_host_bytes'}
    require(isinstance(limits,dict) and set(limits)==keys,'missing resource budgets')
    require(all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in limits.values()),'explicit positive approved resource budgets required')
    require(all(type(v) is int for k,v in limits.items() if k.endswith('bytes')),'byte budgets must be integers')
    require(limits['per_run_seconds']<=120 and limits['aggregate_seconds']<=3600 and limits['aggregate_output_bytes']<=5*1024**3,
            'budget exceeds D0 candidate caps; separate amendment required')
    require(limits['per_run_seconds']<=limits['aggregate_seconds'] and limits['per_run_output_bytes']<=limits['aggregate_output_bytes']
            and limits['max_host_rss_bytes']<=limits['min_available_host_bytes'],'inconsistent approved resource budgets')
    return limits


def freeze(destination):
    destination = output_path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    manifest = proposed_manifest()
    (destination/'manifest.json').write_bytes(encoded(manifest))
    for name, entry in manifest['schedules'].items():
        (destination/name).write_bytes(schedule_text(entry['steps']))
    sha = digest(destination/'manifest.json')
    (destination/'manifest.sha256').write_text(sha+'  manifest.json\n')
    approval = {'version': 1, 'execution_authorized': False, 'approval_reference': None,
                'manifest_sha256': sha, 'build_receipt_sha256': None, 'environment_sha256': None,
                'output_root': None, 'gpu_uuid': None,
                'limits': {key: None for key in ('per_run_seconds', 'aggregate_seconds',
                    'per_run_output_bytes', 'aggregate_output_bytes', 'min_free_disk_bytes',
                    'min_free_gpu_bytes', 'max_host_rss_bytes', 'min_available_host_bytes')}}
    (destination/'approval.template.json').write_bytes(encoded(approval))
    return sha


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path, help='write a NEW proposed config directory; no authorization')
    args = parser.parse_args()
    print(freeze(args.freeze) if args.freeze else json.dumps(estimates(proposed_manifest()), indent=2))
