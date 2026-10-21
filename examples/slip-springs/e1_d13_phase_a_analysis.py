#!/usr/bin/env python3
"""Authenticated Phase A performance/output analysis; never equilibrium acceptance."""
import argparse
import math
from pathlib import Path

import e1_d13_phase_a as spec
import e1_d13_phase_a_auth as auth
from e1_d1_pilot import require, load, file_record


def categories(files):
    result={'legacy_backbone':0,'legacy_state':0,'spring_site_connector':0,
            'audit_snapshots':0,'observer_backbone':0,'metadata_provenance':0}
    for name,proof in files.items():
        size=proof['bytes'];require(type(size) is int and size>=0,'invalid output size')
        if name in ('samples.csv','initial_bonds.csv','bond_statistics.csv'):key='legacy_backbone'
        elif name in ('initial.csv','final.csv','fixed_slip_springs.csv','slip_springs_initial.csv','slip_springs_final.csv'):key='legacy_state'
        elif name in ('equilibrium_sites.csv','equilibrium_connectors.csv','equilibrium_chains.csv','equilibrium_events.csv'):key='spring_site_connector'
        elif name in ('equilibrium_positions.csv','equilibrium_attachments.csv'):key='audit_snapshots'
        elif name in ('equilibrium_backbone.csv','equilibrium_tangents.csv'):key='observer_backbone'
        else:key='metadata_provenance'
        result[key]+=size
    require(sum(result.values())==sum(p['bytes'] for p in files.values()),'output category sum mismatch')
    return result


def process_metrics(item,environment,binary):
    run=item['run'];root=item['root'];receipt=item['receipt'];meta=item['data']['metadata']
    observer=load(root/'equilibrium_complete.json') if run['profile']=='sparse' else None
    auth.timers(meta,observer)
    wall=receipt['wall_seconds'];rss=receipt['max_rss_bytes'];steps=run['steps']
    require(type(wall) in (int,float) and math.isfinite(wall) and wall>0,'invalid process wall time')
    require(type(rss) is int and rss>0 and steps>0,'invalid process RSS/steps')
    hop=load(root/'hopping_metadata.json');auth.counters(hop,run)
    files=item['data']['files'];logs={name:proof['bytes'] for name,proof in receipt['logs'].items()}
    return {'id':run['id'],'cell':run['cell'],'profile':run['profile'],'seed':run['seed'],
        'initialization_seconds':meta['initialization_seconds'],'integration_seconds':meta['integration_seconds'],
        'production_wall_seconds':meta['production_wall_seconds'],'process_wall_seconds':wall,
        'integration_seconds_per_bd_step':meta['integration_seconds']/steps,
        'production_wall_seconds_per_bd_step':meta['production_wall_seconds']/steps,
        'process_wall_seconds_per_bd_step':wall/steps,
        'attempts':hop['attempts'],'accepted_interior_hops':hop['accepted'],
        'renewals_proposed':hop['renewal_proposed'],'renewals_accepted':hop['renewal_accepted'],
        'renewals_same_chain':hop['renewal_same_chain'],'renewals_cross_chain':hop['renewal_cross_chain'],
        'attempts_per_production_wall_second':hop['attempts']/meta['production_wall_seconds'],
        'observer_exclusive_seconds':observer['exclusive_seconds'] if observer else None,
        'observer_wall_seconds':observer['observer_wall_seconds'] if observer else None,
        'observer_transfer_seconds':observer['transfer_seconds'] if observer else None,
        'observer_transferred_bytes':observer['transferred_bytes'] if observer else None,
        'raw_output_bytes_by_file':{name:proof['bytes'] for name,proof in files.items()},
        'raw_output_bytes_by_category':categories(files),'raw_output_bytes':sum(p['bytes'] for p in files.values()),
        'run_log_bytes_by_file':logs,'execution_receipt_bytes':file_record(root.parent/'execution.json')['bytes'],
        'peak_host_rss_bytes':rss,'explicit_device_array_bytes':meta['device_bytes'],
        'gpu_free_bytes_before':receipt['resources_before']['free_gpu_bytes'],
        'gpu_free_bytes_after':receipt.get('free_gpu_bytes_after'),'peak_gpu_bytes':None,
        'peak_gpu_note':'Not sampled; pre/post free-device snapshots are availability, not per-process peak use.',
        'internal_timer_scopes':{key:meta[key] for key in ('integration_timer_scope','observation_scope')},
        'other_recorded_timers':{key:meta[key] for key in spec.TIMING_FIELDS if key.endswith('seconds')},
        'environment_sha256':spec.identity(environment),'gpu':environment['gpu'],'executable':binary}


def summarize(manifest,items,ledger,build):
    require(len(items)==8 and [i['run'] for i in items]==manifest['runs'],'complete ordered eight-process Phase A cohort required')
    processes=[process_metrics(item,ledger['environment'],build['binary']) for item in items]
    by_id={p['id']:p for p in processes};pairs=[]
    for pair in manifest['pairing']:
        off,on=(by_id[pair[k]] for k in ('off','on'))
        keys=('initialization_seconds','integration_seconds','production_wall_seconds','process_wall_seconds','raw_output_bytes')
        pairs.append({'cell':pair['cell'],'seed':pair['seed'],'off':pair['off'],'on':pair['on'],
            'on_minus_off':{key:on[key]-off[key] for key in keys},
            'interpretation':'One paired replay only; descriptive differences, no confidence interval or precise speedup claim.'})
    return {'schema':'e1-d13-phase-a-analysis-v1','scientific_acceptance':None,
        'processes':processes,'pairs':pairs,'raw_output_bytes':sum(p['raw_output_bytes'] for p in processes),
        'limitations':['Four initializations, eight processes; no independent benchmark repetitions.',
          'No equilibrium, timestep, convergence, independence or rheology acceptance.',
          'Do not sum overlapping timers: CUDA integration includes force/diagnostic/host gaps; observer wall includes reductions/transfers.',
          'Production excludes initialization/final output; supervised process wall includes process startup/exit and polling granularity.',
          'No isolated hopping-kernel timing; throughput uses attempts divided by production wall.']}


def analyze(args):
    root=args.campaign.resolve();output=spec.output_path(args.output)
    require(not output.is_relative_to(root) and not output.exists(),'analysis output must be fresh and outside raw evidence')
    manifest,items=auth.authenticate_campaign(root,args.manifest,args.manifest_sha256,args.approval_sha256,args.completion_sha256)
    ledger=load(root/'campaign.json');build=load(root/'build.json')
    result=summarize(manifest,items,ledger,build)
    result['authentication']={'manifest_sha256':args.manifest_sha256,'approval_sha256':args.approval_sha256,
        'completion_sha256':args.completion_sha256,'build_receipt_sha256':ledger['build_receipt_sha256'],
        'environment':ledger['environment'],'source':build['source']}
    result['campaign_evidence_bytes']=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    result['shared_provenance_and_logs_bytes']=result['campaign_evidence_bytes']-result['raw_output_bytes']
    auth.authenticate_campaign(root,args.manifest,args.manifest_sha256,args.approval_sha256,args.completion_sha256)
    with output.open('xb') as stream:stream.write(spec.encoded(result))
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=spec.CONFIG/'manifest.json')
    for name in ('manifest-sha256','approval-sha256','completion-sha256'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    try:print(analyze(args))
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as error:parser.exit(1,f'Phase A analysis refused: {error}\n')
