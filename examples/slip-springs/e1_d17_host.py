#!/usr/bin/env python3
"""D1.7 preparation and explicitly approved Stage-A execution; no build or Stage B action."""
import os
for _pool in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_pool] = '2'
import argparse
import fcntl
import math
from pathlib import Path
import shutil
import signal
import time

import e1_d17_spec as spec
from e1_d1_pilot import require, load, file_record, digest, atomic, utc, capture
import e1_d16b_auth as historical
import e1_d1_pilot_runner as supervisor
from e1_observer_check import verify
from e1_d2a5_validate import csv_rows


def write(path, value):
    require(not path.exists(), 'refuse existing artifact: '+str(path))
    atomic(path, value)


def validate_output(root, run, manifest, gpu):
    full = spec.schedules(manifest)[run['schedule']]
    snapshots = [0, run['steps']]
    if run['Z']:
        return historical.validate_output(root, run, full, snapshots, gpu)
    # Existing canonical validator requires Z>0. Bind the bare path explicitly.
    files = spec.snapshot(root)
    expected = historical.base.RAW_FILES - {'hopping_metadata.json', 'fixed_slip_springs.csv',
        'slip_springs_initial.csv', 'slip_springs_final.csv'}
    require(set(files) == expected, 'bare output inventory')
    meta, schema, complete = [load(root/name) for name in
        ('metadata.json', 'equilibrium_schema.json', 'equilibrium_complete.json')]
    dt = float(run['dt'])
    fields = dict(model='finite-rest-length-Kratky-Porod', precision_bits=64, gpu=gpu,
        chains=256, springs=32, beads_per_chain=33, total_beads=8448, dt=dt, kbt=1, zeta=1,
        steps=run['steps'], production_time=100, sample=run['sample'], seed=run['seed'],
        active_angles=31, slip_count=0, slip_ms2=None, slip_effective_stiffness=None,
        slip_mode='disabled', slip_launches=0, update_launches=run['steps'],
        stretch_launches=run['steps']+2, bending_launches=run['steps']+2,
        initialization_method='CPU-direct-equilibrium', rng_domain=3,
        effective_mobility_step=dt, effective_noise=math.sqrt(2*dt), timer_version=1)
    require(all(meta.get(k) == v for k, v in fields.items()), 'bare physical identity')
    require(schema == dict(version=1, phase='initial before dynamics; otherwise after BD and complete jump batch',
        dt=dt, legacy_sample_stride=run['sample'], steps=run['steps'], chains=256, beads_per_chain=33,
        slip_count=0, canonical=False, expected_frames=51, snapshot_steps=snapshots), 'bare E1 schema')
    require(complete['complete'] is True and complete['frames'] == 51 and
        set(complete['files']) == expected-{'parameters.txt', 'equilibrium_complete.json'}, 'bare completion closure')
    require(all(files[name]['bytes'] == size for name, size in complete['files'].items()), 'completion sizes')
    require(list(map(float, (root/'parameters.txt').read_text().split())) ==
        [32]+[1.,30.]*32+[0.]+[10.]*31+[0.], 'backbone parameters')
    counts = spec.old_counts(run, full, snapshots)
    counts = {k:v for k,v in counts.items() if k in expected}
    for name, count in counts.items():
        seen = 0
        for i, row in enumerate(csv_rows(root/name)):
            require(i < count, 'extra row: '+name)
            if name == 'samples.csv':
                step = i//256*run['sample']
                require(row['step'] == str(step) and row['chain'] == str(i%256) and
                        float(row['time']) == step*dt, 'scalar schedule/order')
            if name == 'equilibrium_events.csv':
                require(row['step'] == str(full[i]), 'E1 schedule')
            if name == 'bond_statistics.csv':
                bins = [int(row[f'bin{k}']) for k in range(33)]
                require(row['chain'] == str(i//32) and row['bond'] == str(i%32) and
                    int(row['frames']) == 101 and min(bins) >= 0 and sum(bins) == 101, 'bond histogram support')
            seen += 1
        require(seen == count, 'missing rows: '+name)
    context = verify(root)
    require(not any(context['totals'].values()), 'bare events must be zero')
    with (root/'equilibrium_positions.csv').open(newline='') as stream:
        import csv
        positions = list(csv.DictReader(stream))
    for offset, phase in ((0,'initial'), (8448,'final')):
        legacy = list(csv_rows(root/f'{phase}.csv'))
        require(len(legacy) == 8448 and all(all(row[k] == joint[k] for k in ('chain','bead','x','y','z'))
            for row,joint in zip(legacy, positions[offset:offset+8448])), 'endpoint snapshot identity')
    historical.accepted.timers(meta, complete)
    require(spec.snapshot(root) == files, 'output changed during validation')
    return dict(files=files, row_counts=counts, event_totals=context['totals'], duration=100, metadata=meta)


def check_build(proof, sha, executable, manifest):
    spec.regular_path(Path(proof).absolute())
    spec.regular_path(Path(executable).absolute())
    require(digest(proof) == sha == manifest['historical_build_sha256'], 'pinned historical build receipt')
    build = historical.validate_build(proof, sha, load(spec.PROJECT/'e1_d16b_config/manifest.json'), live=False)
    require(build['source']['sha'] == manifest['source_sha'] and
        build['binary']['file'] == file_record(executable) == manifest['executable'], 'accepted executable/source identity')
    return build


def prepare(root, executable, proof, proof_sha):
    root = spec.output_path(root)
    manifest = spec.candidate()
    # Only the archived D1.6 binary is read; no production checkout traversal or no-op build.
    for path in (executable, proof):
        require(not Path(path).absolute().is_relative_to(Path('/home/jramirez/UAMMD_KG-slip-springs-dev')),
                'production checkout is protected')
    build = check_build(proof, proof_sha, executable, manifest)
    require(capture(['git','-C',spec.PROJECT,'branch','--show-current']) == 'validation/d17-equilibrium-dt', 'wrong branch')
    require(not capture(['git','-C',spec.PROJECT,'status','--porcelain']), 'commit preparation before freezing')
    root.mkdir(parents=True, exist_ok=False)
    try:
        for name in ('config','provenance'):
            (root/name).mkdir()
        shutil.copyfile(executable, root/'provenance/semiflexible')
        (root/'provenance/semiflexible').chmod(0o500)
        shutil.copyfile(proof, root/'provenance/historical-build.json')
        # Preserve build log and accepted source/dependency/runtime records without rebuilding.
        require(file_record(spec.regular_path(Path(build['log']['path']))) == build['log']['file'], 'historical build log')
        shutil.copyfile(build['log']['path'], root/'provenance/historical-build.log')
        for path, record in build['dependencies'].items():
            require(not Path(path).is_relative_to(Path('/home/jramirez/UAMMD_KG-slip-springs-dev')), 'protected dependency')
            require(file_record(spec.regular_path(Path(path))) == record, 'historical source/dependency identity')
        from e1_d1_pilot import ACCEPTED_FILES, source_hashes
        accepted_hashes = source_hashes()
        for name in ACCEPTED_FILES:
            original = spec.regular_path(Path(build['source']['path'])/'examples/slip-springs'/name)
            require(digest(original) == accepted_hashes[name], 'accepted scientific source changed')
            target = root/'provenance/accepted-source'/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(original,target)
        for name in ('runtime_library',):
            require(file_record(spec.regular_path(Path(build[name]['path']))) == build[name]['file'], 'runtime changed')
        for path, record in build['linker_libraries'].items():
            require(file_record(spec.regular_path(Path(path))) == record, 'linked library changed')
        sources = spec.tool_records()
        for name in sources:
            target = root/'provenance/tools'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(spec.PROJECT/name, target)
        for name, values in spec.schedules(manifest).items():
            (root/'config'/name).write_bytes(spec.schedule_text(values))
        write(root/'seed-audit.json', spec.seed_audit(manifest, [spec.PROJECT, spec.EVIDENCE], root))
        prepared = dict(candidate=manifest, runs=spec.runs(manifest), schedules=spec.schedules(manifest),
            source_files=sources, checkout_head=capture(['git','-C',spec.PROJECT,'rev-parse','HEAD']),
            executable=file_record(root/'provenance/semiflexible'), historical_build=file_record(proof),
            source=build['source'], stage='A', execution_authorized=False, stage_b_authorized=False)
        write(root/'manifest.json', prepared)
        inventory = spec.snapshot(root)
        write(root/'readiness.json', dict(status='PREPARED_FOR_INDEPENDENT_REVIEW_NOT_EXECUTION', utc=utc(),
            manifest=file_record(root/'manifest.json'), input_inventory=inventory, seed_audit=file_record(root/'seed-audit.json')))
        write(root/'approval-template.json', approval_template(root))
    except BaseException as error:
        write(root/'PREPARATION_FAILED.json', dict(error=str(error)))
        raise


def checked(root):
    root = spec.output_path(root)
    require(not (root/'PREPARATION_FAILED.json').exists(), 'failed preparation')
    prepared = load(root/'manifest.json')
    require(prepared['candidate'] == spec.candidate() and prepared['runs'] == spec.runs(prepared['candidate']) and
            prepared['schedules'] == spec.schedules(prepared['candidate']) and
            prepared['stage'] == 'A' and prepared['execution_authorized'] is False and
            prepared['stage_b_authorized'] is False and prepared['source_files'] == spec.tool_records(), 'prepared contract changed')
    readiness = load(root/'readiness.json')
    require(file_record(root/'manifest.json') == readiness['manifest'], 'manifest changed since readiness')
    for name, record in readiness['input_inventory'].items():
        require(file_record(spec.regular_path(root/name)) == record, 'readiness input changed: '+name)
    check_build(root/'provenance/historical-build.json', prepared['candidate']['historical_build_sha256'],
                root/'provenance/semiflexible', prepared['candidate'])
    return prepared


def approval_template(root):
    return dict(schema='d17-stage-a-only-v1', stage='A', execution_authorized=False,
        stage_b_authorized=False, independent_review_reference=None,
        manifest=file_record(root/'manifest.json'), readiness=file_record(root/'readiness.json'),
        output_root=str(root), limits=load(root/'manifest.json')['candidate']['limits'])


def validate_approval(root, path, sha):
    require(file_record(path)['sha256'] == sha, 'trusted approval SHA256 required')
    value, template = load(path), approval_template(root)
    require(load(root/'approval-template.json') == template, 'approval template changed')
    reference = value.get('independent_review_reference')
    require(isinstance(reference,str) and reference.strip(), 'independent review reference required')
    require(value == dict(template, execution_authorized=True, independent_review_reference=reference),
            'approval must authorize exactly this Stage-A packet; Stage B forbidden')
    return value


def run(root, approval_path, approval_sha, explicit):
    require(explicit, 'explicit --execute-reviewed-stage-a required')
    root = spec.output_path(root)
    prepared = checked(root)
    approval = validate_approval(root, approval_path, approval_sha)
    require(not (root/'execution-attempt.json').exists(), 'no retries, resume or adoption')
    start = time.monotonic()
    manifest = prepared['candidate']
    limits = manifest['limits']
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Stage-A interrupted or wall deadline reached')
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGALRM):
        signal.signal(sig, interrupted)
    signal.alarm(limits['aggregate_seconds'])
    write(root/'execution-attempt.json', dict(utc=utc(), approval=value_record(approval_path), manifest=value_record(root/'manifest.json')))
    write(root/'approval.json', approval)
    status = dict(status='running', completed_runs=[], started_utc=utc())
    atomic(root/'status.json', status)
    lock_path = spec.BASE/'.stage-a-gpu.lock'
    fd = os.open(lock_path, os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        build = load(root/'provenance/historical-build.json')
        stable, free = supervisor.machine(build, manifest['gpu_uuid'])
        require(stable['runtime_library'] == build['runtime_library']['file'] and
            stable['runtime_version']//1000 == 13 and stable['driver_api_version'] >= 13000, 'unreviewed CUDA runtime')
        require(shutil.disk_usage(root).free >= limits['min_free_disk_bytes']+2*limits['aggregate_output_bytes'], 'initial disk budget')
        write(root/'environment.json', stable)
        (root/'runs').mkdir()
        for item in prepared['runs']:
            checked(root)
            require(spec.tool_records() == prepared['source_files'] and
                file_record(root/'provenance/semiflexible') == manifest['executable'], 'code/executable changed')
            now, free = supervisor.machine(build, manifest['gpu_uuid'])
            require(now == stable, 'runtime environment changed')
            resources = supervisor.resource_check(root, limits, free)
            directory = root/'runs'/item['id']
            directory.mkdir()
            write(directory/'launch.json', dict(run=item, argv=spec.command(item, root),
                manifest=file_record(root/'manifest.json'), resources=resources, utc=utc()))
            stage_start = time.monotonic()
            process = supervisor.run_process(spec.command(item, root), directory,
                supervisor.environment(build['cuda_home'], manifest['gpu_uuid']), limits, root, start)
            require(process['status'] == 'exited' and process['exit_code'] == 0, 'child failed: '+str(process))
            validation = validate_output(directory/'output', item, manifest, stable['gpu']['name'])
            require(time.monotonic()-stage_start <= limits['per_run_seconds'], 'child plus validation deadline')
            require(supervisor.tree_bytes(directory) <= limits['per_run_output_bytes'], 'per-run output budget')
            write(directory/'receipt.json', dict(run=item, process=process, validation=validation,
                files=spec.snapshot(directory), stage_wall_seconds=time.monotonic()-stage_start, utc=utc()))
            require(supervisor.tree_bytes(directory) <= limits['per_run_output_bytes'], 'receipt output budget')
            status['completed_runs'].append(item['id'])
            atomic(root/'status.json', status)
        require(time.monotonic()-start <= limits['aggregate_seconds'] and
            supervisor.tree_bytes(root) <= limits['aggregate_output_bytes'], 'aggregate budget')
        # Revalidate frozen preparation and receipts before issuing completion.
        checked(root)
        for item in prepared['runs']:
            directory = root/'runs'/item['id']
            receipt = load(directory/'receipt.json')
            require({k:v for k,v in spec.snapshot(directory).items() if k != 'receipt.json'} == receipt['files'],
                    'run changed before cohort completion')
        require(time.monotonic()-start <= limits['aggregate_seconds'], 'final closure wall budget')
        status.update(status='completed_stage_a_not_scientific_acceptance', ended_utc=utc(), wall_seconds=time.monotonic()-start)
        atomic(root/'status.json', status)
        write(root/'complete.json', dict(status=file_record(root/'status.json'), manifest=file_record(root/'manifest.json'),
            approval=file_record(root/'approval.json'), environment=file_record(root/'environment.json'),
            receipts={r['id']:file_record(root/'runs'/r['id']/'receipt.json') for r in prepared['runs']}))
    except BaseException as error:
        status.update(status='FAILED_OR_INTERRUPTED', error=f'{type(error).__name__}: {error}', ended_utc=utc())
        atomic(root/'status.json', status)
        raise
    finally:
        os.close(fd)
        signal.alarm(0)


def value_record(path):
    return dict(path=str(path), file=file_record(path))


def authenticate(root, completion_sha):
    prepared = checked(root)
    require(digest(root/'complete.json') == completion_sha, 'externally retained completion SHA256 required')
    complete = load(root/'complete.json')
    for name in ('status','manifest','approval','environment'):
        require(file_record(root/(name+'.json')) == complete[name], 'completion identity: '+name)
    validate_approval(root, root/'approval.json', complete['approval']['sha256'])
    status = load(root/'status.json')
    ids = [r['id'] for r in prepared['runs']]
    require(status['status'] == 'completed_stage_a_not_scientific_acceptance' and status['completed_runs'] == ids
        and set(complete['receipts']) == set(ids) and {p.name for p in (root/'runs').iterdir()} == set(ids), 'complete 24-run cohort required')
    require(0 < status['wall_seconds'] <= prepared['candidate']['limits']['aggregate_seconds'] and
        supervisor.tree_bytes(root) <= prepared['candidate']['limits']['aggregate_output_bytes'], 'aggregate resource receipt')
    stamps = spec.input_stamps(root)
    before = spec.snapshot(root)
    require(spec.input_stamps(root) == stamps, 'input changed during hashing')
    gpu = load(root/'environment.json')['gpu']['name']
    for item in prepared['runs']:
        directory = root/'runs'/item['id']
        prefix = 'runs/'+item['id']+'/'
        require(before[prefix+'receipt.json'] == complete['receipts'][item['id']], 'receipt changed')
        receipt = load(directory/'receipt.json')
        require(receipt['run'] == item and receipt['process'] == load(directory/'process.json') and
            receipt['process']['status'] == 'exited' and receipt['process']['exit_code'] == 0, 'run process identity')
        limits = prepared['candidate']['limits']
        require(0 < receipt['stage_wall_seconds'] <= limits['per_run_seconds'] and
            0 < receipt['process']['wall_seconds'] <= limits['per_run_seconds'] and
            0 < receipt['process']['max_rss_bytes'] <= limits['max_host_rss_bytes'] and
            supervisor.tree_bytes(directory) <= limits['per_run_output_bytes'], 'run resource receipt')
        launch = load(directory/'launch.json')
        require(launch['run'] == item and launch['argv'] == spec.command(item, root) and
            launch['manifest'] == complete['manifest'], 'launch identity')
        require({k[len(prefix):]:v for k,v in before.items() if k.startswith(prefix) and k != prefix+'receipt.json'}
            == receipt['files'], 'run hash/size closure')
        require(validate_output(directory/'output', item, prepared['candidate'], gpu) == receipt['validation'], 'numerical revalidation')
    require(spec.input_stamps(root) == stamps, 'inputs changed during authentication')
    return prepared, before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--executable', type=Path, required=True)
    p.add_argument('--build-proof', type=Path, required=True)
    p.add_argument('--build-proof-sha256', required=True)
    p = sub.add_parser('run')
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--approval', type=Path, required=True)
    p.add_argument('--approval-sha256', required=True)
    p.add_argument('--execute-reviewed-stage-a', action='store_true', required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.root, args.executable, args.build_proof, args.build_proof_sha256)
    else:
        run(args.root, args.approval, args.approval_sha256, args.execute_reviewed_stage_a)


if __name__ == '__main__':
    main()
