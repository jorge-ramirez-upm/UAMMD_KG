#!/usr/bin/env python3
"""D1.2 proposal generation/authentication only. No simulation execution interface."""
import argparse
from fractions import Fraction
import hashlib
import subprocess
from pathlib import Path

import e1_d1_pilot as old

START = 'c2fc9c537263b801ace93c9386bca4f62f6f7753'
PROJECT = Path(__file__).resolve().parent
CONFIG = PROJECT/'e1_d12_proposed_config'
CALIBRATION = PROJECT/'e1_d12_schema_calibration.json'
EARLY = ('0', '0.0005', '0.0025', '0.01', '0.05')
BUDGETS = ('per_run_seconds', 'aggregate_seconds', 'per_run_output_bytes',
           'aggregate_output_bytes', 'min_free_disk_bytes', 'min_free_gpu_bytes',
           'min_available_host_bytes', 'max_host_rss_bytes')
PHASES = {'A': ('0.25', 1, ((8, 0, 16, 10), (32, 10, 4, 100))),
          'B': ('10', 2, ((32, 0, 4, 100), (32, 10, 4, 100))),
          'C': ('100', 2, ((32, 0, 4, 100), (32, 10, 4, 100)))}


def schedules(horizon, dt):
    end = old.exact_step(horizon, dt)
    old.require(end >= old.exact_step('0.05', dt), 'horizon shorter than early set')
    stride = old.exact_step('0.1', dt)
    full_stride = old.exact_step('0.5', dt)
    shared = sorted({old.exact_step(t, dt) for t in EARLY} |
                    set(range(0, end+1, full_stride)) | {end})
    full = sorted(set(shared) | {1})
    snapshots = sorted({0, 1, old.exact_step('0.01', dt), end})
    old.require(len(snapshots) <= 8 and set(snapshots) <= set(full), 'invalid snapshots')
    return {'scalar_steps': list(range(0, end+1, stride)), 'legacy_stride': stride,
            'full_steps': full, 'shared_full_steps': shared,
            'diagnostic_only_steps': [1], 'snapshot_steps': snapshots}


def cells(phase):
    horizon, replicas, cases = PHASES[phase]
    result = []
    for cell, (case, dt) in enumerate(((case, dt) for case in cases for dt in old.TIMESTEPS), 1):
        n, kappa, ne, nu = case
        z = old.round_half_up(Fraction(64*n, ne))
        s = schedules(horizon, dt)
        profiles = ('off', 'sparse') if phase == 'A' else ('sparse',)
        for replica in range(1, replicas+1):
            # Phase A on/off pairs deliberately replay one physical seed.
            seed = 721200000 + 100000*('ABC'.index(phase)+1) + 100*cell + replica
            for profile in profiles:
                result.append({'id':f'{phase}-c{cell}-r{replica}-{profile}', 'cell':cell,
                    'replica':replica, 'profile':profile, 'N':n, 'M':64, 'kappa':kappa,
                    'Ne':ne, 'nu_hop':nu, 'Z':z, 'rho':str(Fraction(z,64*(n+1))),
                    'dt':dt, 'T':horizon, 'steps':old.exact_step(horizon,dt),
                    'sample':s['legacy_stride'], 'seed':seed,
                    'schedule':f'dt{dt}.full.steps', 'snapshots':f'dt{dt}.snapshots.steps'})
    return result


def preserved():
    frozen = subprocess.check_output(['git','-C',str(old.REPOSITORY),'ls-tree','-r','--name-only',
              START,'--','examples/slip-springs/e1_d1_pilot_config'],text=True).splitlines()
    paths = list(old.TOOL_FILES) + [p.removeprefix('examples/slip-springs/') for p in frozen]
    result = {}
    for name in paths:
        data = subprocess.check_output(['git','-C',str(old.REPOSITORY),
                    'show',START+':examples/slip-springs/'+name])
        sha = hashlib.sha256(data).hexdigest()
        old.require(old.digest(PROJECT/name) == sha, 'frozen D1.1 file changed: '+name)
        result[name] = sha
    return result


def projection(run, float_width=21):
    """Uncompressed CSV fields + commas/newlines; JSON/log allowances separate."""
    s = schedules(run['T'],run['dt'])
    full = s['full_steps'] if run['profile']=='sparse' else []
    snaps = s['snapshot_steps'] if full else []
    counts = old.row_counts(run, full, snaps)
    calibration = old.load(CALIBRATION)['files']
    integers = {'step','previous_step','chain','bead','bond','spring','previous','next','z','frames'}
    counters = {'batches','attempts','accepted','boundary','occupied','metropolis',
                'renewal_proposed','renewal_accepted','renewal_occupied','renewal_same_chain','renewal_cross_chain'}
    result = {}
    for name, count in counts.items():
        if not full and name.startswith('equilibrium_'):
            continue
        header = calibration[name]['header']
        if run['N']<=8:
            header = [k for k in header if k not in ('tangent8','tangent16')]
        widths = []
        for field in header:
            if field in counters:
                # Nominal whole-run counts intentionally overestimate an interval;
                # unsigned-64 width provides a second, conservative CSV envelope.
                bound = max(run['steps'],2*run['Z']*run['nu_hop']*Fraction(run['T'])+100)
                widths.append(20 if float_width==24 else len(str(int(bound))))
            elif (field in integers and not (field=='z' and name in ('initial.csv','final.csv','equilibrium_positions.csv'))) or field.startswith('bin'):
                bound = {'step':run['steps'],'previous_step':run['steps'],'chain':run['M']-1,
                    'bead':run['N'],'bond':run['N']-1,'spring':max(1,run['Z']-1),
                    'previous':max(1,run['Z']-1),'next':max(1,run['Z']-1),'z':run['N']+1,
                    'frames':len(s['scalar_steps'])}.get(field,len(s['scalar_steps']))
                widths.append(max(2 if field in ('spring','previous','next') else 1,len(str(bound))))
            else:
                widths.append(float_width)
        row_bytes = sum(widths)+len(header)
        result[name] = {'rows':count,'columns':len(header),'row_bytes':row_bytes,
                        'bytes':count*row_bytes+len(','.join(header))+1}
    groups = {'backbone':0,'spring_site_connector':0,'audit_snapshots':0,'legacy_endpoint':0}
    for name, record in result.items():
        if name in ('samples.csv','equilibrium_backbone.csv','equilibrium_tangents.csv',
                    'initial_bonds.csv','bond_statistics.csv'):
            group = 'backbone'
        elif name in ('equilibrium_sites.csv','equilibrium_connectors.csv','equilibrium_chains.csv','equilibrium_events.csv'):
            group = 'spring_site_connector'
        elif name in ('equilibrium_positions.csv','equilibrium_attachments.csv'):
            group = 'audit_snapshots'
        else:
            group = 'legacy_endpoint'
        groups[group] += record['bytes']
    return {'files':result,'groups':groups,'csv_bytes':sum(groups.values()),
            'per_run_json_receipts_logs_allowance_bytes':2*1024**2,
            'note':'Planning estimate, not a quota; binary/build/dependency evidence is campaign-wide.'}


def phase_plan(phase):
    horizon, replicas, _ = PHASES[phase]
    runs = cells(phase)
    estimates = []
    for r in runs:
        estimates.append({'id':r['id'], 'nominal':projection(r), 'wide':projection(r,24)})
    return {'schema':'e1-d12-proposal-v1','phase':phase,'execution_authorized':False,
            'not_an_executable_manifest':True,'required_prior_reviews':{'A':[], 'B':['A'], 'C':['A','B']}[phase],
            'T_candidate':horizon,'replicas_candidate':replicas,
            'frozen_execution_T':None,'frozen_execution_replicas':None,
            'approved_limits':{k:None for k in BUDGETS},
            'common':{'M':64,'b0':1,'kb':30,'kBT':1,'zeta':1,'A2':5,
                      'end_renewal':True,'stress':'off','precision':'double','scalar_output':'full'},
            'runs_proposed_for_review' if phase!='C' else 'planning_runs_not_selected':runs,
            'schedule_by_dt':{dt:schedules(horizon,dt) for dt in old.TIMESTEPS},
            'aggregate':{'processes':len(runs),'replica_bd_steps':sum(r['steps'] for r in runs),
                'bead_updates':sum(r['steps']*r['M']*(r['N']+1) for r in runs),
                'expected_hopping_attempts':sum(int(r['Z']*r['nu_hop']*Fraction(horizon)) for r in runs),
                'nominal_csv_bytes':sum(x['nominal']['csv_bytes'] for x in estimates),
                'wide_csv_bytes':sum(x['wide']['csv_bytes'] for x in estimates),
                'json_receipts_logs_allowance_bytes':len(runs)*2*1024**2,
                'shared_build_provenance_allowance_bytes':64*1024**2,
                'runtime_seconds':None}, 'storage_by_run':estimates}


def payloads():
    result = {}
    for phase in PHASES:
        plan = phase_plan(phase)
        result[f'phase-{phase}/proposal.json'] = old.encoded(plan)
        for dt,s in plan['schedule_by_dt'].items():
            for kind,key in (('scalar','scalar_steps'),('full','full_steps'),('snapshots','snapshot_steps')):
                result[f'phase-{phase}/dt{dt}.{kind}.steps'] = old.schedule_text(s[key])
    source_hashes = old.source_hashes()
    for name, sha in source_hashes.items():
        old.require(old.digest(PROJECT/name)==sha, 'accepted source changed: '+name)
    index = {'schema':'e1-d12-design-v1','execution_authorized':False,'starting_sha':START,
             'accepted_simulator_sha':old.ACCEPTED_SHA, 'repository':old.REPOSITORY_ID,
             'preserved_d11_sha256':preserved(),'accepted_source_sha256':source_hashes,
             'generator_sha256':old.digest(Path(__file__)), 'calibration_sha256':old.digest(CALIBRATION),
             'target_gpu':'NVIDIA GeForce RTX 3060 Ti','target_cuda':'13',
             'files':{name:hashlib.sha256(data).hexdigest() for name,data in result.items()},
             'execution_blockers':['No phase authorization or resource budgets.',
                'D1.1 runner/analysis reject this schema; separately reviewed D1.2 adapter required.',
                'C horizon and replica count require A/B evidence and a new frozen execution manifest.']}
    result['design.json'] = old.encoded(index)
    return result


def freeze(destination):
    destination = old.output_path(destination)
    data = payloads()
    destination.mkdir(parents=True,exist_ok=False)
    for name,body in data.items():
        p=destination/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    return old.digest(destination/'design.json')


def check(directory, expected_sha):
    directory=Path(directory)
    old.require(old.digest(directory/'design.json')==expected_sha,'design trust anchor mismatch')
    expected=payloads()
    old.require(not directory.is_symlink() and all(not p.is_symlink() for p in directory.rglob('*')),
                'symlink in proposed configuration')
    actual={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}
    old.require(actual==set(expected),'missing/unexpected configuration files')
    for name,data in expected.items():
        p=directory/name
        old.require(not p.is_symlink() and p.read_bytes()==data,'proposal changed: '+name)
    return {'authenticated':True,'execution_authorized':False,'files':len(expected),'sha256':expected_sha}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze',type=Path);group.add_argument('--check',type=Path)
    parser.add_argument('--sha256')
    args=parser.parse_args()
    if args.freeze:
        print(freeze(args.freeze))
    else:
        if not args.sha256:
            parser.error('--sha256 is required for --check')
        print(old.encoded(check(args.check,args.sha256)).decode(),end='')


if __name__=='__main__':
    main()
