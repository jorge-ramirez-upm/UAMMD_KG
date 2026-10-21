#!/usr/bin/env python3
"""Manual Phase B host handoff. No action, probe or simulation without a subcommand."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import e1_d14_phase_b as spec
import e1_d14_phase_b_runner as runner
import e1_d14_phase_b_analysis as science

MANIFEST = '1fdb92b972137276fda6f1fc0b057192b3ee8afcb5eb345efd8c27c15f557f9a'
BUILD = '79a9dca3f43e5982abe1e21c828d70ef008bc2e2026bf43e05e9bd05f289d7d5'
BINARY = '45876d8b61150b6259236d31e7a2d0f5f1418f710f444430b8fd4fbd4c8eb063'
ENVIRONMENT = '05e9f076948c5d562925dd24b9d9d47bc8611698516efea13808029ad5d8c79a'
LIMITS = dict(per_run_seconds=120, aggregate_seconds=3600,
              per_run_output_bytes=134217728, aggregate_output_bytes=1073741824,
              max_host_rss_bytes=2147483648, min_available_host_bytes=8589934592,
              min_free_gpu_bytes=4294967296, min_free_disk_bytes=10737418240)


def write(path, value):
    with Path(path).open('xb') as stream:
        stream.write(spec.encoded(value))


def check_anchors(bundle, sha):
    path = bundle/'anchors.json'
    spec.require(spec.digest(path) == sha, 'external anchors SHA256 mismatch')
    value = spec.load(path)
    spec.require(value['manifest_sha256'] == MANIFEST, 'wrong Phase B manifest')
    spec.require(value['helper_sha256'] == spec.digest(__file__), 'operator helper changed')
    spec.validate_manifest(spec.CONFIG/'manifest.json', MANIFEST)
    spec.require(value['bundle'] == str(bundle), 'bundle moved; do not relocate before execution/analysis')
    spec.require(spec.digest(bundle/'approval.json') == value['approval_sha256'], 'approval changed')
    spec.require(spec.digest(value['build_receipt']) == value['build_sha256'], 'build receipt changed')
    spec.require(spec.digest(bundle/'preflight.json') == value['preflight_sha256'], 'preflight changed')
    return value


def preflight_args(bundle, receipt, build_sha, approval_sha=None):
    return argparse.Namespace(manifest=spec.CONFIG/'manifest.json', manifest_sha256=MANIFEST,
        build_receipt=receipt, build_sha256=build_sha, gpu_uuid=spec.GPU_UUID,
        output_root=bundle/'campaign', approval=bundle/'approval.json' if approval_sha else None,
        approval_sha256=approval_sha, authorize_phase_b_execution=False)


def prepare(args):
    spec.require(args.write_approved_record, 'prepare requires --write-approved-record; no action taken')
    bundle = spec.output_path(args.bundle)
    receipt = args.build_receipt.resolve()
    spec.validate_manifest(spec.CONFIG/'manifest.json', MANIFEST)
    repository = spec.old.REPOSITORY
    head = spec.capture(['git','-C',repository,'rev-parse','HEAD'])
    branch = spec.capture(['git','-C',repository,'branch','--show-current'])
    remote = spec.capture(['git','-C',repository,'ls-remote','origin','refs/heads/slip-springs'])
    spec.require(branch == 'slip-springs' and remote.split() == [head,'refs/heads/slip-springs'],
                 'local/remote slip-springs HEAD mismatch')
    spec.require(not spec.capture(['git','-C',repository,'status','--porcelain']), 'preparation checkout is dirty')
    # Existing authentication verifies the complete dependency/toolchain/source closure live.
    build = runner.auth.validate_build(receipt, args.build_sha256,
                                     spec.load(spec.CONFIG/'manifest.json'), live=True)
    spec.require(build['binary']['file']['sha256'] == args.binary_sha256, 'unexpected executable')
    bundle.mkdir(parents=True, exist_ok=False)
    preliminary, *_ = runner.preflight(preflight_args(bundle, receipt, args.build_sha256))
    write(bundle/'initial-preflight.json', preliminary)
    spec.require(preliminary['blockers'] == ['independent approval and explicit resource budgets required'],
                 'preflight blocked; preserve this bundle and stop: '+str(preliminary['blockers']))
    spec.require(preliminary['environment_sha256'] == ENVIRONMENT, 'live environment differs from approved identity')
    approval = spec.load(spec.CONFIG/'approval.template.json')
    approval.update(execution_authorized=True,
        approval_reference='User-authorized Stage D1.4 Phase B; manual host execution only; exact eight-run scope',
        manifest_sha256=MANIFEST, build_receipt_sha256=args.build_sha256,
        environment_sha256=preliminary['environment_sha256'], gpu_uuid=spec.GPU_UUID,
        output_root=str(bundle/'campaign'), limits=LIMITS.copy())
    write(bundle/'approval.json', approval)
    approval_sha = spec.digest(bundle/'approval.json')
    final, *_ = runner.preflight(preflight_args(bundle, receipt, args.build_sha256, approval_sha))
    write(bundle/'preflight.json', final)
    spec.require(not final['blockers'], 'approved preflight blocked; stop: '+str(final['blockers']))
    value = dict(schema='e1-d14-manual-host-anchors-v1', bundle=str(bundle),
        manifest_sha256=MANIFEST, build_receipt=str(receipt), build_sha256=args.build_sha256,
        binary_sha256=args.binary_sha256, environment_sha256=ENVIRONMENT,
        approval_sha256=approval_sha, preflight_sha256=spec.digest(bundle/'preflight.json'),
        helper_sha256=spec.digest(__file__), operator_source_sha=head)
    write(bundle/'anchors.json', value)
    sha = spec.digest(bundle/'anchors.json')
    (bundle/'anchors.sha256').write_text(sha+'  anchors.json\n')
    print(json.dumps(dict(anchors_sha256=sha, approval_sha256=approval_sha,
                         next='Copy anchors_sha256 outside this bundle; execution requires a separate command.'), indent=2))


def command(bundle, anchors):
    return [sys.executable, str(spec.PROJECT/'e1_d14_phase_b_runner.py'), 'preflight',
        '--manifest', str(spec.CONFIG/'manifest.json'), '--manifest-sha256', MANIFEST,
        '--build-receipt', anchors['build_receipt'], '--build-sha256', anchors['build_sha256'],
        '--gpu-uuid', spec.GPU_UUID, '--output-root', str(bundle/'campaign'),
        '--approval', str(bundle/'approval.json'), '--approval-sha256', anchors['approval_sha256'],
        '--authorize-phase-b-execution']


def execute(args):
    spec.require(args.authorize_phase_b_execution, 'explicit --authorize-phase-b-execution required')
    bundle = args.bundle.resolve(); anchors = check_anchors(bundle, args.anchors_sha256)
    spec.require(not (bundle/'campaign').exists(), 'campaign root exists; no resume or rerun')
    argv = command(bundle, anchors)
    write(bundle/'execution-command.json', dict(argv=argv, started_utc=spec.utc(),
                                              anchors_sha256=args.anchors_sha256))
    print('Runner output: '+str(bundle/'runner.stdout.log')+'; errors: '+str(bundle/'runner.stderr.log'), flush=True)
    # Replace this process so the accepted runner directly owns signals and child supervision.
    with (bundle/'runner.stdout.log').open('xb') as out, (bundle/'runner.stderr.log').open('xb') as err:
        os.dup2(out.fileno(), 1); os.dup2(err.fileno(), 2)
        os.execv(sys.executable, argv)


def returned_completion(text):
    decoder = json.JSONDecoder(); records = []
    while text.strip():
        value, end = decoder.raw_decode(text.lstrip()); records.append(value)
        text = text.lstrip()[end:]
    spec.require(len(records) == 2 and records[0]['mode'] == 'read-only preflight'
        and not records[0]['blockers'] and records[1]['status'] == 'completed',
        'runner did not return successful preflight and cohort completion')
    return records[1]


def completion(args):
    bundle = args.bundle.resolve(); check_anchors(bundle, args.anchors_sha256)
    result = returned_completion((bundle/'runner.stdout.log').read_text())
    spec.require(result['root'] == str(bundle/'campaign'), 'wrong returned campaign root')
    spec.require(spec.digest(bundle/'campaign/campaign_complete.json') == result['completion_sha256'],
                 'returned completion differs from evidence')
    write(bundle/'external-completion.json', dict(result, anchors_sha256=args.anchors_sha256,
        runner_stdout=spec.file_record(bundle/'runner.stdout.log')))
    print(json.dumps(result, indent=2))
    print('Copy completion_sha256 outside this bundle BEFORE running analyze.')


def summary(result):
    lines = ['# Phase B exploratory handoff', '',
        'R=2 independent 64-chain replicas/cell. No scientific acceptance verdict; all IATs unresolved.', '',
        '| Cell | Observable | Reference | t=0 replica values | t=10 replica values | Late-minus-early replicas |',
        '|---|---|---:|---|---|---|']
    for cell, data in result['cells'].items():
        for key in ('re2','rg2','mean_r','mean_r2','connector_e2','A_joint','B_joint'):
            initial = data['time_resolved']['0']['metrics'][key]
            final = data['time_resolved']['10']['metrics'][key]
            drift = data['early_versus_late'][key]['paired_late_minus_early']['replica_values']
            values = lambda xs: ', '.join(format(x, '.8g') for x in xs)
            lines.append(f"| B{cell} | {key} | {initial['reference']:.8g} | {values(initial['replica_values'])} | {values(final['replica_values'])} | {values(drift)} |")
    lines += ['', 'The full analysis retains every supported time, weak R=2 intervals, tangent/connector CDF/',
              'occupancy/population/joint statistics, independent shared-time timestep contrasts and ACF support.',
              'These endpoint columns do not classify equilibrium preservation. Read the complete time-resolved analysis.', '']
    return '\n'.join(lines)


def analyze(args):
    bundle = args.bundle.resolve(); anchors = check_anchors(bundle, args.anchors_sha256)
    returned = spec.load(bundle/'external-completion.json')
    spec.require(returned['completion_sha256'] == args.completion_sha256
        and returned['anchors_sha256'] == args.anchors_sha256, 'external completion anchor mismatch')
    output = bundle/'analysis.json'
    result = science.analyze(argparse.Namespace(campaign=bundle/'campaign', output=output,
        manifest=spec.CONFIG/'manifest.json', manifest_sha256=MANIFEST,
        approval_sha256=anchors['approval_sha256'], completion_sha256=args.completion_sha256))
    # The accepted analyzer already authenticated twice; its output can exceed the small-receipt loader's 32 MiB cap.
    with output.open() as stream: data = json.load(stream)
    reply = bundle/'reply'; reply.mkdir(exist_ok=False)
    (reply/'summary.md').write_text(summary(data))
    campaign = bundle/'campaign'
    files = {str(p.relative_to(campaign)):spec.file_record(p) for p in sorted(campaign.rglob('*')) if p.is_file()}
    index = dict(schema='e1-d14-phase-b-return-index-v1', campaign=str(campaign),
        anchors_sha256=args.anchors_sha256, manifest_sha256=MANIFEST,
        approval_sha256=anchors['approval_sha256'], completion_sha256=args.completion_sha256,
        analysis_sha256=result['sha256'], campaign_files=files,
        summary=spec.file_record(reply/'summary.md'), helper_sha256=spec.digest(__file__))
    write(reply/'reference-index.json', index)
    members = {**{name:bundle/name for name in ('analysis.json','anchors.json','approval.json',
        'preflight.json','external-completion.json','execution-command.json','runner.stdout.log','runner.stderr.log')},
        'summary.md':reply/'summary.md', 'reference-index.json':reply/'reference-index.json'}
    if (bundle/'runner.exit-code.txt').is_file():
        members['runner.exit-code.txt'] = bundle/'runner.exit-code.txt'
    for name in ('manifest.json','build.json','campaign.json','status.json','campaign_complete.json','provenance/build.log'):
        members['campaign/'+name] = campaign/name
    for name in spec.load(spec.CONFIG/'manifest.json')['schedules']:
        members['campaign/config/'+name] = campaign/'config'/name
    for run in spec.load(spec.CONFIG/'manifest.json')['runs']:
        for name in ('execution.json','process.json','stdout.log','stderr.log',
                     'output/metadata.json','output/hopping_metadata.json',
                     'output/equilibrium_complete.json','output/equilibrium_schema.json','output/parameters.txt'):
            members['runs/'+run['id']+'/'+name] = campaign/'runs'/run['id']/name
    archive = bundle/'phase-b-return.tar.gz'
    with archive.open('xb') as stream:
        with tarfile.open(fileobj=stream, mode='w:gz') as tar:
            for name, path in members.items(): tar.add(path, arcname='phase-b-return/'+name, recursive=False)
    spec.require(spec.digest(output) == result['sha256'], 'analysis changed while packaging')
    print(json.dumps(dict(analysis_sha256=result['sha256'], completion_sha256=args.completion_sha256,
        return_archive=str(archive), return_archive_sha256=spec.digest(archive)), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='action')
    p = subs.add_parser('prepare', help='live authentication and separate external approval; never runs dynamics')
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--write-approved-record', action='store_true')
    p.add_argument('--build-receipt', type=Path, default=Path('/tmp/e1-d14-build/build.json'))
    p.add_argument('--build-sha256', default=BUILD); p.add_argument('--binary-sha256', default=BINARY)
    for name in ('execute','completion','analyze'):
        p = subs.add_parser(name); p.add_argument('--bundle', type=Path, required=True)
        p.add_argument('--anchors-sha256', required=True)
        if name == 'execute': p.add_argument('--authorize-phase-b-execution', action='store_true')
        if name == 'analyze': p.add_argument('--completion-sha256', required=True)
    args = parser.parse_args()
    if not args.action: parser.print_help(); return
    try: globals()[args.action](args)
    except (OSError, ValueError, KeyError, TypeError, AssertionError, subprocess.SubprocessError) as error:
        parser.exit(1, f'Host handoff refused; preserve evidence and do not retry: {error}\n')


if __name__ == '__main__': main()
