#!/usr/bin/env python3
"""Authenticated exploratory Phase B drift/ACF analysis, independent whole replicas."""
import argparse
from fractions import Fraction
import math
from pathlib import Path
import numpy as np

import e1_d14_phase_b as spec
import e1_d14_phase_b_auth as auth
import e1_d1_pilot_analysis as science
from e1_observer_check import Rows
from e1_d1_pilot import require

reference=science.reference
SHORT=('re2','rg2','mean_r','mean_r2','tangent1','tangent2','tangent3','tangent4')
T1=1/math.tan(math.pi*.025)


def time_key(step,dt):return str(Fraction(step)*Fraction(dt))


def backbone(rows,n):
    keys=('re2','rg2','mean_r','mean_r2')+tuple('tangent'+str(s) for s in (1,2,3,4) if s<n)
    return {key:float(np.mean([float(row[key]) for row in rows])) for key in keys}


def rates_between(events,boundaries,dt):
    """Every boundary must be an actual frame; sum intervening deltas, never interpolate."""
    require(boundaries==sorted(set(boundaries)) and boundaries and boundaries[0]==0,'invalid rate boundaries')
    require(events and [e['step'] for e in events]==sorted({e['step'] for e in events})
        and events[0]['step']==0 and events[-1]['step']==boundaries[-1],'invalid event sequence')
    require(set(boundaries)<={e['step'] for e in events},'unobserved rate boundary')
    sums={k:0 for k in auth.COUNTERS};result={};previous=0
    for event in events:
        require(set(event['counts'])==set(sums) and all(type(v) is int and v>=0 for v in event['counts'].values()),'invalid interval counts')
        if event['step']==0:require(not any(event['counts'].values()),'nonzero initial event counts')
        for key,value in event['counts'].items():sums[key]+=value
        step=event['step']
        if step in boundaries and step:
            duration=Fraction(step-previous)*Fraction(dt)
            result[step]={'duration_exact':str(duration),'counts':sums.copy(),
                         'metrics':{'rate_'+k:v/float(duration) for k,v in sums.items() if k!='batches'}}
            previous=step;sums={k:0 for k in sums}
    require(not any(sums.values()) and previous==boundaries[-1],'unconsumed event interval')
    return result


def reduce_replica(root,run,full_steps):
    root=Path(root);dt=float(run['dt']);chains=run['M'];z=run['Z'];n=run['N']
    require(full_steps==sorted(set(full_steps)) and full_steps[0]==0 and full_steps[-1]==run['steps'],'invalid full schedule')
    regular=list(range(0,run['steps']+1,run['sample']))
    series={};reader=Rows(root/'samples.csv')
    try:
        for step in regular:series[step]=backbone(reader.take(chains,step,dt),n)
        reader.finish()
    finally:reader.file.close()
    names=('backbone','tangents','chains','connectors','sites','events')
    readers={name:Rows(root/('equilibrium_'+name+'.csv')) for name in names}
    readers['samples']=Rows(root/'samples.csv')
    events=[];full={};seen=np.zeros(chains*(n+1),dtype=bool)
    try:
        for step in full_steps:
            readers['samples'].seek(step)
            bb=readers['samples' if step%run['sample']==0 else 'backbone'].take(chains,step,dt)
            tangent=readers['tangents'].take(chains if n>8 else 0,step,dt)
            population=readers['chains'].take(chains,step,dt);connector=readers['connectors'].take(z,step,dt)
            sites=readers['sites'].take(len(seen),step,dt);event=readers['events'].take(1,step,dt)[0]
            ids=[int(row['spring']) for row in sites];seen|=np.asarray(ids)>=0
            values=science.frame_statistics(run,bb,population,connector,ids,tangent)
            series.setdefault(step,{}).update(values);full[step]=dict(values)
            events.append({'step':step,'counts':{key:int(event[key]) for key in auth.COUNTERS}})
        for reader in readers.values():reader.finish()
    finally:
        for reader in readers.values():reader.file.close()
    shared=[s for s in full_steps if s!=1]
    intervals=rates_between(events,shared,run['dt'])
    for step,data in intervals.items():series[step].update(data['metrics'])
    spacing=spec.old.exact_step('0.5',run['dt'])
    uniform_bounds=list(range(0,run['steps']+1,spacing))
    # Tiny technical fixtures may not cover one .5 interval; no pretend ACF grid.
    uniform_rates=rates_between(events,uniform_bounds,run['dt']) if uniform_bounds[-1]==run['steps'] and len(uniform_bounds)>1 else {}
    targets=reference(n,chains,z,run['kappa'],run['nu_hop'])['targets']
    initial=series[0]
    individual={time_key(step,run['dt']):{'step':step,'time':step*dt,
        'diagnostic_only':step==1,'metrics':values,
        'deviation_from_reference':{k:v-targets[k] for k,v in values.items()},
        'change_from_initial':{k:v-initial[k] if k in initial else None for k,v in values.items()}}
        for step,values in sorted(series.items())}
    return {'run':run,'series':individual,'regular_scalar_times':[time_key(s,run['dt']) for s in regular],
        'full_e1_times':[time_key(s,run['dt']) for s in full_steps],
        'regular_e1_times':[time_key(s,run['dt']) for s in uniform_bounds] if uniform_bounds[-1]==run['steps'] else [],
        'regular_event_rates':{time_key(step,run['dt']):data for step,data in uniform_rates.items()},
        'event_intervals':{time_key(step,run['dt']):data for step,data in intervals.items()},
        'event_totals':{k:sum(e['counts'][k] for e in events) for k in auth.COUNTERS},
        'coverage':{'observed_site_fraction':float(seen.mean()),
            'observed_chain_fraction':float(seen.reshape(chains,n+1).any(axis=1).mean()),
            'site_ever_occupied':seen.astype(int).tolist(),'per_id_renewal_history':None},
        'reference':reference(n,chains,z,run['kappa'],run['nu_hop'])}


def summary(values,target=None):
    x=np.asarray(values,dtype=float)
    require(x.shape==(2,) and np.isfinite(x).all(),'exactly two finite replica estimators required')
    mean=float(x.mean());sd=float(x.std(ddof=1));se=sd/math.sqrt(2);half=T1*se
    result={'replicas':2,'replica_values':x.tolist(),'mean':mean,'replica_sd':sd,'standard_error':se,
            'pointwise_nominal_95_interval':[mean-half,mean+half],'zero_observed_replica_variance':sd==0}
    if target is not None:
        require(math.isfinite(target),'nonfinite reference')
        result.update(reference=target,difference_from_reference=mean-target,
                      difference_interval=[mean-half-target,mean+half-target])
    return result


def independent_contrast(fine,coarse):
    a,b=summary(fine),summary(coarse);difference=b['mean']-a['mean']
    se=math.hypot(a['standard_error'],b['standard_error'])
    return {'fine_replica_values':a['replica_values'],'coarse_replica_values':b['replica_values'],
        'coarse_minus_fine':difference,'standard_error':se,'pointwise_nominal_95_interval':[difference-T1*se,difference+T1*se],
        'method':'independent replica variances; t1 critical, no guaranteed coverage for two skewed replicas'}


def acf_diagnostic(times,values,spacing):
    t=[Fraction(s) for s in times];spacing=Fraction(spacing);x=np.asarray(values,dtype=float)
    require(len(t)==len(x) and np.isfinite(x).all() and spacing>0,'invalid ACF data')
    require(all(b-a==spacing for a,b in zip(t,t[1:])),'ACF requires an exact uniform grid')
    require(t==sorted(set(t)),'invalid ACF time order')
    # Remove a baseline before centering so constant noninteger series stay exactly zero.
    x=x-x[0] if len(x) else x
    variance=float(x.var(ddof=1)) if len(x)>1 else None;x=x-x.mean() if len(x) else x
    result={'samples':len(x),'spacing_exact':str(spacing),'available_time_support':float(t[-1]-t[0]) if t else 0.,
        'variance':variance,'tau_int':None,'unresolved_long_time_tail':True,'independent_samples_established':False}
    den=float(x@x)
    if len(x)<8 or den==0:return dict(result,status='insufficient support or zero variance',acf=[],lags=[])
    lags=list(range(1,min(20,len(x)//4)+1));acf=[float(x[:-k]@x[k:]/den) for k in lags]
    crossings=[k for k,v in zip(lags,acf) if v<.2]
    result.update(status='descriptive demeaned finite-series ACF; no reliable IAT',lags=lags,acf=acf,
        lag_times=[float(spacing*k) for k in lags],first_observed_below_0p2_lag=crossings[0] if crossings else None,
        decay_shape='below .2 within reported lags' if crossings else 'positive correlation persists over reported lags',
        decorrelation_assessment='Observed decay is descriptive; meaningful long-time decorrelation and stationarity remain unestablished.')
    return result


def window_comparison(replica,key):
    if key.startswith('rate_'):
        source={t:v['metrics'] for t,v in replica['regular_event_rates'].items()}
        early=[t for t in source if 0<Fraction(t)<=1];late=[t for t in source if 9<Fraction(t)<=10]
    else:
        times=replica['regular_scalar_times'] if key in SHORT else replica['regular_e1_times']
        source={t:replica['series'][t]['metrics'] for t in times}
        early=[t for t in source if 0<=Fraction(t)<=1];late=[t for t in source if 9<=Fraction(t)<=10]
    require(early and late and all(key in source[t] for t in early+late),'unsupported early/late diagnostic')
    a=float(np.mean([source[t][key] for t in early]));b=float(np.mean([source[t][key] for t in late]))
    return {'early_times':early,'late_times':late,'early_mean':a,'late_mean':b,'late_minus_early':b-a}


def replica_acf(replica):
    result={};initial=replica['series']['0']['metrics']
    for key in initial:
        times=replica['regular_scalar_times'] if key in SHORT else replica['regular_e1_times']
        spacing='0.1' if key in SHORT else '0.5'
        result[key]=acf_diagnostic(times,[replica['series'][t]['metrics'][key] for t in times],spacing)
    rates=replica['regular_event_rates'];times=sorted(rates,key=Fraction)
    if times:
        for key in rates[times[0]]['metrics']:
            result[key]=acf_diagnostic(times,[rates[t]['metrics'][key] for t in times],'0.5')
    return result


def aggregate(replicas,manifest):
    require(len(replicas)==8 and [r['run'] for r in replicas]==manifest['runs'],'complete ordered frozen eight-replica cohort required')
    cells={}
    for cell in range(1,5):
        group=[r for r in replicas if r['run']['cell']==cell]
        require([r['run']['replica'] for r in group]==[1,2] and len({r['run']['seed'] for r in group})==2,'independent R=2 cell required')
        targets=group[0]['reference']['targets'];times=sorted(group[0]['series'],key=Fraction)
        require(all(set(r['series'])==set(times) for r in group),'replica observation grids differ')
        by_time={}
        for time in times:
            keys=set(group[0]['series'][time]['metrics'])
            require(all(set(r['series'][time]['metrics'])==keys for r in group),'inconsistent supported observables')
            metrics={key:summary([r['series'][time]['metrics'][key] for r in group],targets[key]) for key in sorted(keys)}
            changes={key:summary([r['series'][time]['metrics'][key]-r['series']['0']['metrics'][key] for r in group])
                     if key in group[0]['series']['0']['metrics'] else None for key in sorted(keys)}
            by_time[time]={'time':float(Fraction(time)),'diagnostic_only':group[0]['series'][time]['diagnostic_only'],
                'metrics':metrics,'paired_change_from_initial':changes}
        keys=set().union(*(frame['metrics'] for frame in group[0]['series'].values()))
        windows={}
        for key in sorted(keys):
            individual=[window_comparison(r,key) for r in group]
            windows[key]={'replicas':individual,'early':summary([r['early_mean'] for r in individual],targets[key]),
                'late':summary([r['late_mean'] for r in individual],targets[key]),
                'paired_late_minus_early':summary([r['late_minus_early'] for r in individual])}
        temporal={key:{'minimum_replica_mean':min(v['metrics'][key]['mean'] for v in by_time.values() if key in v['metrics']),
            'maximum_replica_mean':max(v['metrics'][key]['mean'] for v in by_time.values() if key in v['metrics'])} for key in keys}
        cells[str(cell)]={'time_resolved':by_time,'early_versus_late':windows,'variation_across_times':temporal,
            'reference':group[0]['reference'],'acf_by_replica':{r['run']['id']:replica_acf(r) for r in group}}
    contrasts=[]
    for fine_cell in (1,3):
        fine=[r for r in replicas if r['run']['cell']==fine_cell];coarse=[r for r in replicas if r['run']['cell']==fine_cell+1]
        common=set(fine[0]['series'])&set(coarse[0]['series'])
        times={}
        for time in sorted(common,key=Fraction):
            if any(r['series'][time]['diagnostic_only'] for r in fine+coarse):continue
            keys=set.intersection(*(set(r['series'][time]['metrics']) for r in fine+coarse))
            times[time]={key:independent_contrast([r['series'][time]['metrics'][key] for r in fine],
                [r['series'][time]['metrics'][key] for r in coarse]) for key in sorted(keys)}
        contrasts.append({'fine_cell':fine_cell,'coarse_cell':fine_cell+1,'shared_physical_times':times})
    return {'schema':'e1-d14-phase-b-analysis-v1','scientific_acceptance':None,'independent_unit':'entire 64-chain replica',
        'uncertainty':'R=2, df=1 pointwise nominal intervals; no simultaneous/equivalence or guaranteed small-sample coverage',
        't1_critical':T1,'replicas':replicas,'cells':cells,'timestep_contrasts':contrasts,
        'limitations':['No burn-in removal from an exact-start preservation pilot.',
          'Rates are interval quantities, undefined at t=0; rate change-from-initial is null.',
          'Joint/slip metrics exist only on synchronous full E1 frames; no carry-forward.',
          'Frames/chains/components are not independent replicas; all IATs remain null.',
          'Scientific D0 margins unchanged; no automatic equilibrium acceptance or fitted reference.']}


def analyze(args):
    root=args.campaign.resolve();output=spec.output_path(args.output)
    require(not output.exists() and not output.is_relative_to(root),'analysis must be fresh and outside raw evidence')
    manifest,items=auth.authenticate_campaign(root,args.manifest,args.manifest_sha256,args.approval_sha256,args.completion_sha256)
    reduced=[reduce_replica(item['root'],item['run'],manifest['schedules'][item['run']['schedule']]['steps']) for item in items]
    result=aggregate(reduced,manifest)
    result['authentication']={'manifest_sha256':args.manifest_sha256,'approval_sha256':args.approval_sha256,
        'completion_sha256':args.completion_sha256,'analysis_sources':spec.tool_hashes()}
    result['costs']={'process_wall_seconds':sum(i['receipt']['wall_seconds'] for i in items),
        'raw_bytes':sum(sum(f['bytes'] for f in i['data']['files'].values()) for i in items),
        'max_host_rss_bytes':max(i['receipt']['max_rss_bytes'] for i in items)}
    auth.authenticate_campaign(root,args.manifest,args.manifest_sha256,args.approval_sha256,args.completion_sha256)
    with output.open('xb') as stream:stream.write(spec.encoded(result))
    return {'output':str(output),'sha256':spec.digest(output),'scientific_acceptance':None}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=spec.CONFIG/'manifest.json')
    for name in ('manifest-sha256','approval-sha256','completion-sha256'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    try:print(analyze(args))
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as error:parser.exit(1,f'Phase B analysis refused: {error}\n')
