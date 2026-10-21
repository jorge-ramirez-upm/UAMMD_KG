#!/usr/bin/env python3
"""Independent, read-only D1 manifest/build/raw-output authentication."""
import argparse
import csv
import datetime
import math
from pathlib import Path
import re

import e1_d1_pilot as spec
from e1_d1_pilot import Invalid, require, load, digest, file_record
from e1_observer_check import verify as check_observer

RAW_FILES = {
    'parameters.txt', 'initial.csv', 'final.csv', 'samples.csv', 'initial_bonds.csv',
    'bond_statistics.csv', 'fixed_slip_springs.csv', 'slip_springs_initial.csv',
    'slip_springs_final.csv', 'hopping_metadata.json', 'metadata.json',
    'equilibrium_schema.json', 'equilibrium_complete.json',
} | {'equilibrium_'+kind+'.csv' for kind in (
    'backbone', 'tangents', 'sites', 'connectors', 'chains', 'events', 'positions', 'attachments')}
COUNTERS = ('batches', 'attempts', 'accepted', 'boundary', 'occupied', 'metropolis',
            'renewal_proposed', 'renewal_accepted', 'renewal_occupied',
            'renewal_same_chain', 'renewal_cross_chain')
SIDECAR_COUNTERS = ('batches', 'attempts', 'accepted', 'outward_proposals',
                    'occupied_rejected', 'metropolis_rejected', 'renewal_proposed',
                    'renewal_accepted', 'renewal_occupied_rejected',
                    'renewal_same_chain', 'renewal_cross_chain')


def rows(path):
    csv.field_size_limit(4096)
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames and len(set(reader.fieldnames)) == len(reader.fieldnames), 'invalid CSV header')
        for row in reader:
            require(None not in row and all(v is not None and len(v) <= 128 for v in row.values()), 'malformed CSV row')
            require(all(math.isfinite(float(v)) for v in row.values()), 'nonfinite CSV data')
            yield row


def integer(value):
    require(re.fullmatch(r'-?(0|[1-9][0-9]*)', value) is not None, 'noncanonical integer field')
    return int(value)


def inventory(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'missing/nonregular output directory')
    require({p.name for p in root.iterdir()} == RAW_FILES, 'unexpected/missing output files')
    return {name: file_record(root/name) for name in sorted(RAW_FILES)}


def validate_output(root, run, observation_steps, snapshots, gpu_name):
    """Generic small-fixture entry point; campaign entry separately fixes all 32 runs."""
    root = Path(root); before = inventory(root)
    meta, schema, hop, complete = [load(root/name) for name in (
        'metadata.json', 'equilibrium_schema.json', 'hopping_metadata.json', 'equilibrium_complete.json')]
    dt = float(run['dt']); n, m, chains, z = run['N'], run['N']+1, run['M'], run['Z']
    require(observation_steps == sorted(set(observation_steps)) and observation_steps[0] == 0
            and observation_steps[-1] == run['steps'], 'invalid expected observation schedule')
    expected_schema = {'version': 1, 'phase': 'initial before dynamics; otherwise after BD and complete jump batch',
                       'dt': dt, 'legacy_sample_stride': run['sample'], 'steps': run['steps'],
                       'chains': chains, 'beads_per_chain': m, 'slip_count': z, 'canonical': True,
                       'expected_frames': len(observation_steps), 'snapshot_steps': snapshots}
    require(spec.encoded(schema) == spec.encoded(expected_schema) and complete['version'] == 1 and complete['complete'] is True,
            'schema/phase/parameter/snapshot mismatch')
    require(set(complete['files']) == RAW_FILES-{'parameters.txt', 'equilibrium_complete.json'}, 'completion file set mismatch')
    for name, size in complete['files'].items():
        require(type(size) is int and size == before[name]['bytes'], 'completion file size mismatch')
    expected_meta = {'model': 'finite-rest-length-Kratky-Porod', 'timer_version': 1,
        'precision_bits': 64, 'gpu': gpu_name, 'chains': chains, 'springs': n, 'beads_per_chain': m,
        'total_beads': chains*m, 'dt': dt, 'effective_mobility_step': dt,
        'effective_noise': math.sqrt(2*dt), 'steps': run['steps'], 'production_time': run['steps']*dt,
        'sample': run['sample'], 'seed': run['seed'], 'rng_domain': 3, 'kbt': 1, 'zeta': 1,
        'active_angles': n-1 if run['kappa'] else 0, 'slip_count': z, 'slip_ms2': 5,
        'slip_effective_stiffness': .6, 'slip_initialization_rng_domain': 340247,
        'slip_mode': 'canonical-renewal-development', 'stretch_launches': run['steps']+2,
        'bending_launches': run['steps']+2 if run['kappa'] else 0,
        'slip_launches': run['steps']+2, 'update_launches': run['steps'],
        'initialization_method': 'CPU-direct-equilibrium'}
    for key, value in expected_meta.items():
        require(key in meta and meta[key] == value, 'simulation parameter/metadata mismatch: '+key)
    for key, value in meta.items():
        if isinstance(value, (int, float)):
            require(math.isfinite(value), 'nonfinite metadata')
            if key.endswith('seconds'):
                require(value >= 0, 'negative timer')
    require(meta['minimum_sampled_bond'] > 0, 'invalid minimum bond')
    parameters = [float(v) for v in (root/'parameters.txt').read_text().split()]
    require(parameters == [n]+[v for _ in range(n) for v in (1., 30.)]+[0.]+[float(run['kappa'])]*(n-1)+[0.],
            'effective backbone parameters mismatch')
    expected_hop = {'version': 2, 'rate': run['nu_hop'], 'poisson_mean': z*run['nu_hop']*dt,
        'interval_bd_steps': 1, 'splitting': 'BD then hopping at new coordinates',
        'rng_subsequence_base': 1 << 61, 'max_mean': 10000, 'max_events_per_batch': 100000,
        'end_renewal': True, 'renewal_rng_subsequence_base': 3 << 61,
        'renewal_component_variance': 5/3, 'batches': run['steps']}
    for key, value in expected_hop.items():
        require(hop.get(key) == value, 'hopping provenance mismatch: '+key)
    for key in SIDECAR_COUNTERS:
        require(type(hop[key]) is int and hop[key] >= 0, 'invalid cumulative counter')
    counts = spec.row_counts(run, observation_steps, snapshots)
    regular = list(range(0, run['steps']+1, run['sample']))
    frame_steps = {
        'samples.csv': regular,
        'equilibrium_backbone.csv': [s for s in observation_steps if s % run['sample']],
        'equilibrium_tangents.csv': observation_steps if n>8 else [],
        'equilibrium_sites.csv': observation_steps, 'equilibrium_connectors.csv': observation_steps,
        'equilibrium_chains.csv': observation_steps, 'equilibrium_events.csv': observation_steps,
        'equilibrium_positions.csv': snapshots, 'equilibrium_attachments.csv': snapshots,
    }
    per_frame = {'samples.csv': chains, 'equilibrium_backbone.csv': chains,
                 'equilibrium_tangents.csv': chains, 'equilibrium_sites.csv': chains*m,
                 'equilibrium_connectors.csv': z, 'equilibrium_chains.csv': chains,
                 'equilibrium_events.csv': 1, 'equilibrium_positions.csv': chains*m,
                 'equilibrium_attachments.csv': z}
    for name, expected_count in counts.items():
        seen = 0
        for i, row in enumerate(rows(root/name)):
            require(i < expected_count, 'extra record: '+name)
            if name in frame_steps:
                step = frame_steps[name][i//per_frame[name]]
                require(integer(row['step']) == step and float(row['time']) == step*dt, 'observation schedule mismatch: '+name)
                if name in ('samples.csv', 'equilibrium_backbone.csv', 'equilibrium_tangents.csv', 'equilibrium_chains.csv'):
                    require(integer(row['chain']) == i % chains, 'chain row identity mismatch')
            elif name == 'bond_statistics.csv':
                require(integer(row['chain']) == i//n and integer(row['bond']) == i % n, 'bond identity mismatch')
                frames = sum(s >= run['steps']//2 for s in regular)
                require(integer(row['frames']) == frames and sum(integer(row['bin'+str(b)]) for b in range(33)) == frames,
                        'bond frame/histogram count mismatch')
            seen += 1
        require(seen == expected_count, 'missing record: '+name)
    observed = check_observer(root)
    for key, sidecar in zip(COUNTERS, SIDECAR_COUNTERS):
        require(observed['totals'][key] == hop[sidecar], 'interval/cumulative counter mismatch: '+key)
    require(complete['frames'] == len(observation_steps), 'incomplete frame count')
    # The old checker reconstructs selected states. Also link its endpoint states
    # to legacy coordinate/anchor files, independently of directory names.
    positions = {s: [] for s in (0, run['steps'])}
    for row in rows(root/'equilibrium_positions.csv'):
        s = integer(row['step'])
        if s in positions:
            positions[s].append({k: row[k] for k in ('chain', 'bead', 'x', 'y', 'z')})
    anchors = {s: [] for s in positions}
    for row in rows(root/'equilibrium_attachments.csv'):
        s = integer(row['step'])
        if s in anchors:
            anchors[s].append({k: row[k] for k in ('spring', 'chain', 'bead', 'ax', 'ay', 'az')})
    for s, phase in ((0, 'initial'), (run['steps'], 'final')):
        require(positions[s] == list(rows(root/(phase+'.csv'))), 'legacy/snapshot coordinate mismatch')
        require(anchors[s] == list(rows(root/('slip_springs_'+phase+'.csv'))), 'legacy/snapshot spring mismatch')
    require(before == inventory(root), 'raw data changed during authentication')
    return {'files': before, 'row_counts': counts, 'event_totals': observed['totals'],
            'duration': run['steps']*dt, 'metadata': meta}


def validate_build(path, expected_sha, manifest, live=False):
    require(digest(path) == expected_sha, 'build receipt SHA256 mismatch')
    build = load(path)
    require(type(build['version']) is int and build['version'] == 1 and build['status'] == 'completed' and build['exit_code'] == 0 and build['compilation_observed'] is True,
            'incomplete build receipt')
    require(build['manifest_sha256'] == spec.identity(manifest) and build['source']['sha'] == spec.ACCEPTED_SHA
            and build['source']['repository'] == spec.REPOSITORY_ID and build['precision_bits'] == 64,
            'build source/manifest/precision mismatch')
    require(build['preparation_sources'] == manifest['preparation_sources'], 'build tool identities changed')
    require(re.fullmatch(r'sm_[0-9]+', build['architecture']) is not None, 'invalid GPU build architecture')
    require(build['binary']['path']==str(Path(build['build_root'])/'bin/semiflexible')
            and build['log']['path']==str(Path(build['build_root'])/'build.log')
            and build['nvcc']['path']==str(Path(build['cuda_home'])/'bin/nvcc'), 'build target/compiler path mismatch')
    for key in ('binary', 'log', 'nvcc', 'cxx', 'runtime_library'):
        require(set(build[key]['file']) == {'bytes', 'sha256'} and len(build[key]['file']['sha256']) == 64,
                'missing compiler/executable identity')
        if live:
            require(file_record(build[key]['path']) == build[key]['file'], 'build file changed: '+key)
    require(isinstance(build['dependencies'],dict) and build['dependencies'], 'missing build dependency closure')
    require(build['nvcc']['version'] and build['cxx']['version'] and build['linker_libraries'], 'missing toolchain proof')
    require(build['command'] == build_command(build['source']['path'], build['build_root'],
                                             build['cuda_home'], build['cxx']['path'], build['architecture']),
            'unexpected build command/flags')
    if live:
        require(spec.source_identity(build['source']['path']) == build['source'], 'source identity changed')
        for name, proof in build['dependencies'].items():
            require(file_record(name) == proof, 'build dependency changed: '+name)
        for name, proof in build['linker_libraries'].items():
            require(file_record(name) == proof, 'runtime link library changed: '+name)
    return build


def build_command(source, root, cuda, cxx, arch):
    return ['/usr/bin/make', '-C', str(Path(source)/'examples/slip-springs'), 'semiflexible',
            'PRECISION=double', 'CUDA_HOME='+str(cuda), 'CUDA_ARCH='+arch, 'CXX='+str(cxx),
            'GPU_BUILD='+str(Path(root)/'bin'), 'BUILD='+str(Path(root)/'cpu'),
            'CPPFLAGS=', 'NVCCFLAGS=-O2 -std=c++17 --extended-lambda', 'LDLIBS=']


def authenticate_run(directory, run, manifest, ledger, approval, expected_receipt_sha):
    directory=Path(directory)
    receipt = load(directory/'execution.json')
    require(expected_receipt_sha == digest(directory/'execution.json'), 'execution receipt changed')
    original = Path(ledger['output_root']);require(original.is_absolute() and approval['output_root'] == str(original), 'output root approval mismatch')
    expected_command = spec.command(run, original/'provenance/semiflexible', original/'runs'/run['id']/'output', original/'config')
    require(receipt['status'] == 'completed' and receipt['exit_code'] == 0 and receipt['command'] == expected_command,
            'failed/interrupted/incorrect command')
    require(receipt['run'] == run and receipt['manifest_sha256'] == ledger['manifest_sha256']
            and receipt['build_receipt_sha256'] == approval['build_receipt_sha256']
            and receipt['environment_sha256'] == approval['environment_sha256'], 'replica identity mismatch')
    for name in ('stdout.log', 'stderr.log','process.json'):
        require(file_record(directory/name) == receipt['logs'][name], 'execution log changed')
    process=load(directory/'process.json')
    require(process['status']=='exited' and process['exit_code']==0
            and all(process[k]==receipt[k] for k in ('wall_seconds','max_rss_bytes')), 'process result mismatch')
    data = validate_output(directory/'output', run, manifest['schedules'][run['schedule']]['steps'],
                           manifest['schedules'][run['snapshots']]['steps'], ledger['environment']['gpu']['name'])
    require(data['files'] == receipt['output_files'] and data['event_totals'] == receipt['event_totals'], 'raw checksum/event receipt mismatch')
    require(0 < receipt['wall_seconds'] <= approval['limits']['per_run_seconds']
            and 0 < receipt['max_rss_bytes'] <= approval['limits']['max_host_rss_bytes'], 'missing/excessive runtime/resource evidence')
    resources=receipt['resources_before'];limits=approval['limits']
    require(resources['free_disk_bytes']>=limits['min_free_disk_bytes']+limits['per_run_output_bytes']
            and resources['available_host_bytes']>=limits['min_available_host_bytes']
            and resources['free_gpu_bytes']>=limits['min_free_gpu_bytes'],'prelaunch resources below approval')
    require({p.name for p in directory.iterdir()}=={'execution.json','stdout.log','stderr.log','process.json','output'}, 'unexpected run evidence')
    require(sum(p.stat().st_size for p in directory.rglob('*') if p.is_file())<=approval['limits']['per_run_output_bytes'],'per-run output size limit')
    return {'run':run,'root':directory/'output','receipt':receipt,'data':data}


def authenticate_campaign(root, manifest_path, manifest_sha, approval_sha, completion_sha=None):
    root = Path(root)
    require(isinstance(completion_sha,str) and re.fullmatch(r'[0-9a-f]{64}',completion_sha), 'externally recorded completion SHA256 required')
    require(digest(root/'campaign_complete.json')==completion_sha,'campaign completion SHA256 mismatch')
    manifest = spec.validate_manifest(manifest_path, manifest_sha)
    require(isinstance(approval_sha, str) and len(approval_sha) == 64, 'trusted approval SHA256 required')
    require(digest(root/'approval.json') == approval_sha, 'approval SHA256 mismatch')
    approval = load(root/'approval.json'); ledger = load(root/'campaign.json'); final = load(root/'campaign_complete.json'); status = load(root/'status.json')
    spec.validate_limits(approval['limits'])
    require(approval['execution_authorized'] is True and approval['approval_reference'], 'execution was not approved')
    require(approval['manifest_sha256'] == manifest_sha and ledger['manifest_sha256'] == manifest_sha,
            'campaign manifest mismatch')
    require(ledger['preparation_sources']==manifest['preparation_sources'] and ledger['limits']==approval['limits'], 'campaign tool/budget identity mismatch')
    require(ledger['approval_sha256'] == approval_sha and ledger['campaign'] == manifest['campaign'], 'campaign identity mismatch')
    require(ledger['version'] == final['version'] == status['version'] == 1 and status['status'] == 'completed'
            and status['completed_run_ids'] == [r['id'] for r in manifest['runs']]
            and final['status_sha256'] == digest(root/'status.json'), 'failed/interrupted/changed status')
    require(final['status'] == 'completed' and final['run_ids'] == [r['id'] for r in manifest['runs']], 'incomplete/interrupted campaign')
    require(final['campaign_sha256'] == digest(root/'campaign.json'), 'campaign ledger changed')
    require(digest(root/'manifest.json') == manifest_sha, 'archived manifest mismatch')
    for name, record in manifest['schedules'].items():
        require(digest(root/'config'/name) == record['sha256'], 'archived schedule changed')
    build = validate_build(root/'build.json', approval['build_receipt_sha256'], manifest)
    require(ledger['source']==build['source'] and ledger['build_receipt_sha256']==approval['build_receipt_sha256'], 'campaign source/build mismatch')
    require(file_record(root/'provenance/semiflexible') == build['binary']['file']
            and file_record(root/'provenance/build.log') == build['log']['file'], 'archived executable/build transcript changed')
    require(spec.identity(ledger['environment']) == approval['environment_sha256'] == ledger['environment_sha256'],
            'runtime environment identity mismatch')
    require(ledger['environment']['gpu']['uuid'] == approval['gpu_uuid'], 'GPU identity mismatch')
    require({p.name for p in (root/'runs').iterdir()} == {r['id'] for r in manifest['runs']}, 'missing/unexpected replicas')
    authenticated = []; previous_end = datetime.datetime.fromisoformat(ledger['started_utc']); elapsed = 0.
    for run in manifest['runs']:
        item=authenticate_run(root/'runs'/run['id'],run,manifest,ledger,approval,final['receipts'][run['id']])
        receipt=item['receipt']
        started=datetime.datetime.fromisoformat(receipt['started_utc']);ended=datetime.datetime.fromisoformat(receipt['ended_utc'])
        require(previous_end.tzinfo is not None and started.tzinfo is not None and ended.tzinfo is not None
                and previous_end <= started <= ended, 'invalid/nonsequential execution times')
        previous_end=ended;elapsed+=receipt['wall_seconds']
        authenticated.append(item)
    require(elapsed <= status['wall_seconds'] <= approval['limits']['aggregate_seconds'], 'aggregate duration limit/inconsistency')
    total_bytes=0
    for path in root.rglob('*'):
        require(not path.is_symlink(),'symlink in campaign evidence')
        if path.is_file():total_bytes+=path.stat().st_size
    require(total_bytes<=approval['limits']['aggregate_output_bytes'],'aggregate output size limit')
    return manifest, authenticated


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=spec.CONFIG/'manifest.json')
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--completion-sha256', required=True)
    args = parser.parse_args()
    try:
        _, runs = authenticate_campaign(args.campaign, args.manifest, args.manifest_sha256, args.approval_sha256,args.completion_sha256)
        print('Authenticated complete D1 pilot:', len(runs), 'independent replicas; no scientific acceptance inferred')
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
        parser.exit(1, f'authentication refused: {error}\n')
