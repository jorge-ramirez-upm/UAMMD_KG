"""Independent Phase A authentication and exact paired replay gate."""
import math
from pathlib import Path
import re
import sys

import e1_d13_phase_a as spec
from e1_d13_reuse import bind
from e1_d1_pilot_runner import environment as expected_environment
from e1_d1_pilot import require, load, digest, file_record

base=bind('auth',spec)
_on_output=base.validate_output
_build=base.validate_build
LEGACY=base.RAW_FILES-{n for n in base.RAW_FILES if n.startswith('equilibrium_')}
COUNTERS=base.SIDECAR_COUNTERS


def inventory(root,profile):
    root=Path(root);expected=base.RAW_FILES if profile=='sparse' else LEGACY
    require(root.is_dir() and not root.is_symlink() and {p.name for p in root.iterdir()}==expected,
            'missing/unexpected profile output files')
    return {name:file_record(root/name) for name in sorted(expected)}


def timers(meta,observer=None):
    for key in spec.TIMING_FIELDS:
        value=meta[key]
        require(type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid timing/rate: '+key)
    for key in ('initialization_seconds','integration_seconds','production_wall_seconds','final_output_seconds'):
        require(meta[key]>0,'zero required timing: '+key)
    if observer is not None:
        for key in ('exclusive_seconds','observer_wall_seconds','transfer_seconds'):
            require(type(observer[key]) in (int,float) and math.isfinite(observer[key]) and observer[key]>=0,'invalid observer timing')
        for key in ('transferred_bytes','extra_device_bytes','reduction_workspace_bytes','transient_workspace_bytes'):
            require(type(observer[key]) is int and observer[key]>=0,'invalid observer memory/transfer evidence')


def counters(hop,run):
    for key in COUNTERS:
        require(type(hop[key]) is int and 0<=hop[key]<2**64,'invalid event counter: '+key)
    require(hop['batches']==run['steps'],'incorrect hopping batch count')
    require(hop['attempts']==sum(hop[k] for k in ('accepted','outward_proposals','occupied_rejected','metropolis_rejected')),'attempt identity')
    require(hop['renewal_proposed']==hop['outward_proposals']==hop['renewal_accepted']+hop['renewal_occupied_rejected'],'renewal proposal identity')
    require(hop['renewal_accepted']==hop['renewal_same_chain']+hop['renewal_cross_chain'],'renewal transfer identity')


def off_output(root,run,gpu):
    before=inventory(root,'off');meta=load(root/'metadata.json');hop=load(root/'hopping_metadata.json')
    n=run['N'];m=n+1;chains=run['M'];dt=float(run['dt'])
    expected={'model':'finite-rest-length-Kratky-Porod','timer_version':1,'precision_bits':64,
        'gpu':gpu,'chains':chains,'springs':n,'beads_per_chain':m,'total_beads':chains*m,
        'dt':dt,'effective_mobility_step':dt,'effective_noise':math.sqrt(2*dt),'steps':run['steps'],
        'production_time':run['steps']*dt,'sample':run['sample'],'seed':run['seed'],'rng_domain':3,
        'kbt':1,'zeta':1,'active_angles':n-1 if run['kappa'] else 0,'slip_count':run['Z'],
        'slip_ms2':5,'slip_effective_stiffness':.6,'slip_initialization_rng_domain':340247,
        'slip_mode':'canonical-renewal-development','initialization_method':'CPU-direct-equilibrium',
        'stretch_launches':run['steps']+2,'bending_launches':run['steps']+2 if run['kappa'] else 0,
        'slip_launches':run['steps']+2,'update_launches':run['steps']}
    require(all(meta.get(k)==v for k,v in expected.items()),'off physical parameter/metadata mismatch')
    require(all(not isinstance(v,(int,float)) or math.isfinite(v) for v in meta.values())
            and meta['minimum_sampled_bond']>0,'nonfinite/invalid off metadata')
    params=[float(v) for v in (root/'parameters.txt').read_text().split()]
    require(params==[n]+[v for _ in range(n) for v in (1.,30.)]+[0.]+[float(run['kappa'])]*(n-1)+[0.],'off backbone parameters mismatch')
    expected_hop={'version':2,'rate':run['nu_hop'],'poisson_mean':run['Z']*run['nu_hop']*dt,
        'interval_bd_steps':1,'splitting':'BD then hopping at new coordinates',
        'rng_subsequence_base':1<<61,'max_mean':10000,'max_events_per_batch':100000,
        'end_renewal':True,'renewal_rng_subsequence_base':3<<61,'renewal_component_variance':5/3}
    require(all(hop.get(k)==v for k,v in expected_hop.items()),'off jump provenance mismatch')
    counters(hop,run);counts=spec.row_counts(run,[],[])
    calibration=load(spec.design.CALIBRATION)['files']
    regular=list(range(0,run['steps']+1,run['sample']))
    for name,count in counts.items():
        header=[k for k in calibration[name]['header'] if not k.startswith('tangent') or int(k[7:])<n]
        with (root/name).open() as stream:require(stream.readline().strip()==','.join(header),'legacy CSV schema mismatch: '+name)
        seen=0;sites=set();ids=set()
        for i,row in enumerate(base.rows(root/name)):
            require(i<count,'extra legacy record');seen+=1
            if name=='samples.csv':
                step=regular[i//chains]
                require(base.integer(row['step'])==step and float(row['time'])==step*dt and base.integer(row['chain'])==i%chains,'off scalar schedule/identity')
            elif name in ('initial.csv','final.csv','initial_bonds.csv','bond_statistics.csv'):
                width=n if 'bond' in name else m;index='bond' if 'bond' in name else 'bead'
                require(base.integer(row['chain'])==i//width and base.integer(row[index])==i%width,'off coordinate/bond identity')
                if name=='bond_statistics.csv':
                    frames=sum(s>=run['steps']//2 for s in regular)
                    require(base.integer(row['frames'])==frames and sum(base.integer(row['bin'+str(b)]) for b in range(33))==frames,'off bond histogram count')
            elif name in ('fixed_slip_springs.csv','slip_springs_initial.csv','slip_springs_final.csv'):
                c,b=base.integer(row['chain']),base.integer(row['bead'])
                require(0<=c<chains and 0<=b<m and (c,b) not in sites,'off occupancy identity');sites.add((c,b))
                if 'spring' in row:
                    require(base.integer(row['spring'])==i and i not in ids,'off spring identity');ids.add(i)
        require(seen==count,'missing legacy record: '+name)
    require(inventory(root,'off')==before,'off files changed during authentication')
    return {'files':before,'row_counts':counts,'event_totals':{k:hop[v] for k,v in zip(base.COUNTERS,COUNTERS)},
            'duration':run['steps']*dt,'metadata':meta}


def validate_output(root,run,observation_steps,snapshots,gpu_name):
    root=Path(root)
    require(run['profile'] in ('off','sparse'),'invalid observer profile')
    data=_on_output(root,run,observation_steps,snapshots,gpu_name) if run['profile']=='sparse' else off_output(root,run,gpu_name)
    complete=load(root/'equilibrium_complete.json') if run['profile']=='sparse' else None
    timers(data['metadata'],complete);counters(load(root/'hopping_metadata.json'),run)
    return data


def masked_metadata(path):
    data=path.read_bytes();value=load(path);timers(value)
    for key in spec.TIMING_FIELDS:
        pattern=rb'("'+key.encode()+rb'":)[^,}]*'
        data,count=re.subn(pattern,rb'\1TIMING',data)
        require(count==1,'missing/duplicate timing field')
    return data


def compare_pair(off,on):
    off,on=Path(off),Path(on)
    a,b=inventory(off,'off'),inventory(on,'sparse')
    for name in LEGACY-{'metadata.json'}:
        require(a[name]==b[name],'paired physical/legacy byte mismatch: '+name)
    require(masked_metadata(off/'metadata.json')==masked_metadata(on/'metadata.json'),'paired non-timing metadata bytes differ')
    return {'byte_identical':True,'legacy_files':sorted(LEGACY), 'timing_fields_excluded':list(spec.TIMING_FIELDS)}


def validate_build(path,sha,manifest,live=False):
    built=_build(path,sha,manifest,live)
    require(built['architecture']=='sm_86' and 'release 13.' in built['nvcc']['version'],'Phase A CUDA13/sm86 build required')
    require(built['source']['origin'] in ('git@github.com:jorge-ramirez-upm/UAMMD_KG.git','https://github.com/jorge-ramirez-upm/UAMMD_KG.git'),'incorrect build repository origin')
    return built


base.validate_output=validate_output
base.validate_build=validate_build


def validate_environment(environment,build,approval):
    gpu=environment['gpu'];target={'name':'NVIDIA GeForce RTX 3060 Ti','compute_capability':'8.6','uuid':spec.GPU_UUID}
    require(all(gpu[k]==v for k,v in target.items()) and gpu['uuid']==approval['gpu_uuid'],'incorrect Phase A GPU identity')
    require(type(environment['runtime_version']) is int and environment['runtime_version']//1000==13,'CUDA13 runtime required')
    require(environment['runtime_library']==build['runtime_library']['file'],'runtime/build library mismatch')
    require(type(environment['driver_api_version']) is int and environment['driver_api_version']>=13000,'CUDA13-compatible driver required')
    require(environment['environment']==expected_environment(build['cuda_home'],gpu['uuid']),'GPU/execution environment mismatch')


def authenticate_campaign(root,manifest_path,manifest_sha,approval_sha,completion_sha):
    root=Path(root)
    manifest,items=base.authenticate_campaign(root,manifest_path,manifest_sha,approval_sha,completion_sha)
    approval=load(root/'approval.json');ledger=load(root/'campaign.json')
    build=validate_build(root/'build.json',approval['build_receipt_sha256'],manifest)
    require(set(approval)=={'version','execution_authorized','approval_reference','manifest_sha256',
        'build_receipt_sha256','environment_sha256','output_root','gpu_uuid','limits'} and type(approval['version']) is int and approval['version']==1
        and isinstance(approval['approval_reference'],str) and approval['approval_reference'].strip(),'invalid approval schema')
    require(ledger['output_root']==approval['output_root'],'approved root mismatch')
    validate_environment(ledger['environment'],build,approval)
    for item in items:
        receipt=item['receipt']
        require(type(receipt['wall_seconds']) in (int,float) and math.isfinite(receipt['wall_seconds'])
            and receipt['wall_seconds']>0 and type(receipt['max_rss_bytes']) is int
            and receipt['max_rss_bytes']>0,'invalid process timing/RSS evidence')
    by_id={item['run']['id']:item for item in items}
    for pair in manifest['pairing']:compare_pair(by_id[pair['off']]['root'],by_id[pair['on']]['root'])
    return manifest,items
