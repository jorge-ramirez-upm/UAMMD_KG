"""Exploratory T100 analysis: whole-replica inference, no equilibrium pass."""
from collections import Counter
from fractions import Fraction
from functools import lru_cache
import gzip
import math
from pathlib import Path

import numpy as np
from scipy.stats import t, chi2

import e1_d16b_spec as spec
import e1_d16b_auth as auth
import e1_d1_pilot_analysis as science
from e1_d14_phase_b_analysis import rates_between, time_key, SHORT
from e1_observer_check import Rows
from e1_d1_pilot import require, load, encoded, file_record

ALPHA = .025


@lru_cache(maxsize=16)
def canonical_population(chains=256,n=32,z=2048):
    sites=chains*(n+1);m=n+1
    require(chains>1 and 0<=z<=sites,'invalid canonical population')
    denominator=math.comb(sites,z)
    numerators=[math.comb(m,k)*math.comb(sites-m,z-k) if 0<=z-k<=sites-m else 0 for k in range(m+1)]
    require(sum(numerators)==denominator,'finite-M normalization failed')
    rho=z/sites;variance=m*rho*(1-rho)*(sites-m)/(sites-1)
    return {'pmf':[v/denominator for v in numerators],'mean':z/chains,'variance':variance,
            'cross_chain_covariance':-variance/(chains-1),'site_probability':rho,
            'distinct_site_covariance':-rho*(1-rho)/(sites-1)}


def context_margin(key,target):
    if key in ('re2','rg2'):return .02*abs(target)
    if key in ('mean_r','mean_r2'):return .01*abs(target)
    if key.startswith('tangent') or key in ('A_joint','B_joint') or '_cdf[' in key or key.startswith('cdf_'):return .02
    if key=='connector_e2':return .02*5
    if key.startswith('connector_mean_'):return .05*math.sqrt(5/3)
    if key.startswith(('connector_second_','connector_variance_unbiased_','connector_cross_')):return .02*5/3
    if key.startswith('occupancy['):return min(.01,.10*8/33)
    if key.startswith('rate_'):return .05*abs(target) if target else None
    return None  # No new D0 variance/fourth-moment criterion is invented.


def bounded_range(key):
    if key.startswith('change_'):
        return (-1.,1.) if bounded_range(key[7:]) is not None else None
    if key.startswith(('occupancy[','population_pmf[','population_cdf[','cdf_')) or '_cdf[' in key or key=='population_multiple':
        return (0.,1.)
    return None


def bounded_metric(key):
    return bounded_range(key) is not None


def summary(values,reference=None,key='',numerical_error=0.):
    x=np.asarray(values,dtype=float)
    require(x.shape==(4,) and np.isfinite(x).all(),'exactly four finite whole-replica estimators required')
    mean=float(x.mean());sd=float(x.std(ddof=1));se=sd/2
    half=float(t.ppf(1-ALPHA/2,3))*se
    nominal=[mean-half,mean+half]
    interval=nominal
    if bounded_metric(key):
        low,high=bounded_range(key)
        h=(high-low)*math.sqrt(math.log(2/ALPHA)/(2*len(x)))
        interval=[max(low,mean-h),min(high,mean+h)]
    result={'replica_values':x.tolist(),'mean':mean,'standard_error':se,'replica_sd':sd,
            'trajectory_interval':interval,'nominal_t_interval':nominal,'trajectory_alpha':ALPHA,
            'zero_observed_replica_dispersion':sd==0,
            'leave_one_replica_out_means':[(float(x.sum())-float(v))/3 for v in x],
            'uncertainty_method':'replica Hoeffding for bounded probabilities; otherwise nominal R4 t3'}
    if reference is not None:
        lo,hi=reference['interval'];target=reference['estimate']
        diff=[interval[0]-hi-numerical_error,interval[1]-lo+numerical_error]
        margin=context_margin(key,target)
        statuses=['STATISTICALLY_DETECTABLE_DEVIATION' if diff[0]>0 or diff[1]<0
                  else 'REFERENCE_CONSISTENT_WITHIN_EXPLORATORY_UNCERTAINTY']
        width=max(mean-target-diff[0],diff[1]-(mean-target))
        if sd==0 and not bounded_metric(key):
            statuses=['INSUFFICIENT_INDEPENDENT_REPLICA_PRECISION','ZERO_OBSERVED_REPLICA_DISPERSION']
        if key=='population_mean':
            statuses=['EXACT_CONSERVATION_DIAGNOSTIC']
        if key!='population_mean' and (sd==0 or (margin is not None and width>margin)):statuses.append('INSUFFICIENT_INDEPENDENT_REPLICA_PRECISION')
        if reference.get('precision_status')=='CDF_PRECISION_UNRESOLVED':statuses.append('REFERENCE_CDF_PRECISION_UNRESOLVED')
        statuses=list(dict.fromkeys(statuses))
        result.update(reference=reference,difference_from_reference=mean-target,difference_interval=diff,
            independent_combined_standard_error=math.hypot(se,reference['standard_error']),
            numerical_centering_error_bound=numerical_error,contextual_D0_margin=margin,outcomes=statuses,
            coverage='pointwise nominal >=95% via .025 trajectory + .025 stored reference family; no simultaneous campaign guarantee or D0 acceptance')
    return result


def independent_contrast(fine,coarse,key=''):
    a,b=np.asarray(fine,dtype=float),np.asarray(coarse,dtype=float)
    require(a.shape==b.shape==(4,) and np.isfinite(a).all() and np.isfinite(b).all(),'independent R4 cells required')
    va,vb=float(a.var(ddof=1)/4),float(b.var(ddof=1)/4)
    se=math.sqrt(va+vb);difference=float(b.mean()-a.mean())
    df=(va+vb)**2/(va**2/3+vb**2/3) if va+vb else None
    half=float(t.ppf(1-ALPHA/2,df))*se if df else 0.
    nominal=[difference-half,difference+half]
    interval=nominal
    if bounded_metric(key):
        low,high=bounded_range(key);width=high-low
        h=2*width*math.sqrt(math.log(4/ALPHA)/8)
        interval=[max(-width,difference-h),min(width,difference+h)]
    return {'fine_replica_values':a.tolist(),'coarse_replica_values':b.tolist(),'coarse_minus_fine':difference,
        'standard_error':se,'fine_variance_contribution':va,'coarse_variance_contribution':vb,
        'welch_df':df,'interval':interval,'nominal_welch_interval':nominal,
        'outcomes':(['FINITE_TIMESTEP_DIFFERENCE_DETECTED'] if (df is not None or bounded_metric(key)) and (interval[0]>0 or interval[1]<0) else [])+
                   (['INSUFFICIENT_INDEPENDENT_REPLICA_PRECISION'] if df is None else []),
        'qualification':'independent cells, pointwise exploratory; shared reference cancels; two dt levels establish no convergence order'}


def acf_core(values,spacing,center=None):
    x=np.asarray(values,dtype=float)
    require(x.ndim in (1,2) and len(x)>0 and np.isfinite(x).all(),'invalid temporal series')
    if x.ndim==1:x=x[:,None]
    count=len(x);duration=(count-1)*spacing
    # Fixed-label columns are averaged INSIDE one replica, never new clusters.
    if center is None:
        shifted=x-x[0];u=shifted-shifted.mean(axis=0)
    else:u=x-center
    den=float(np.mean(u*u))
    result={'samples':count,'fixed_labels':x.shape[1],'duration':duration,'spacing':spacing,
        'tau_int':None,'partial_tau_int':None,'unresolved_tail':True,'lags':[], 'acf':[],
        'origin_counts':[],'independent_temporal_samples_established':False}
    if count<8 or den<=0:return dict(result,status='UNDEFINED_ZERO_VARIANCE_OR_INSUFFICIENT_SUPPORT')
    lags=list(range(1,count//4+1))
    rho=[float(np.mean(u[:-lag]*u[lag:])/den) for lag in lags]
    partial=spacing*(.5+np.cumsum(rho))
    positive_end=0;terminated=False
    extended=[1.]+rho
    for j in range(0,len(extended)-1,2):
        if extended[j]+extended[j+1]<=0:
            terminated=True;break
        positive_end=j+1
    candidate=float(spacing*(.5+sum(rho[:positive_end])))
    # Positive-sequence and self-consistent-window tests are diagnostics, not coverage proofs.
    windows=[j for j in lags if j>=2 and j*spacing>=5*max(float(partial[j-1]),spacing/2)]
    w=windows[0] if windows else None
    stable=False
    if w and positive_end and terminated:
        compare=float(partial[max(0,w-3)])
        tau=float(partial[w-1])
        stable=(tau>0 and duration>=50*tau and w*spacing<=duration/4
                and abs(tau-compare)<=.2*max(tau,spacing/2)
                and abs(tau-candidate)<=.2*max(tau,spacing/2))
    result.update(status='DESCRIPTIVE_FINITE_RECORD_ACF',lags=lags,acf=rho,
        lag_times=[lag*spacing for lag in lags],origin_counts=[count-lag for lag in lags],
        partial_tau_int=partial.tolist(),positive_sequence_candidate=candidate,
        positive_sequence_terminated=terminated,self_consistent_window=w,
        candidate_tau_int=float(partial[w-1]) if stable else None)
    # Within-replica half-record stability is required in addition to tail diagnostics.
    if stable and count>=32:
        halves=[acf_core(x[:count//2],spacing,center),acf_core(x[count//2:],spacing,center)]
        candidates=[a.get('positive_sequence_candidate') for a in halves]
        result['half_record_candidates']=candidates
        tau=result['candidate_tau_int']
        if (all(v is not None and v>0 and abs(v-tau)<=.5*tau for v in candidates)
                and all(h.get('positive_sequence_terminated',False) for h in halves)):
            result.update(tau_int=tau,unresolved_tail=False,status='NOMINAL_IAT_DIAGNOSTIC_SUPPORTED')
    return result


def acf_diagnostic(times,values,spacing,target=None):
    times=[Fraction(v) for v in times];delta=Fraction(spacing)
    require(len(times)==len(values) and times==sorted(set(times))
            and all(b-a==delta for a,b in zip(times,times[1:])),'ACF needs actual exact uniform times')
    result=acf_core(values,float(delta))
    if target is not None:
        baseline=acf_core(values,float(delta),target)
        result['equilibrium_centered_sensitivity']=baseline
        a,b=result.get('tau_int'),baseline.get('tau_int')
        if a is None or b is None or abs(a-b)>.25*max(a,b):
            result.update(tau_int=None,unresolved_tail=True,status='CENTERING_SENSITIVITY_UNRESOLVED')
    result['spacing_exact']=str(delta)
    result['fast_dynamics_below_spacing_unresolved']=True
    result['qualification']='conditional stationarity diagnostic; finite partial sums are not rigorous lower bounds; no zero-IAT imputation'
    return result


def frame_backbone(rows,reference):
    xy=np.asarray([[float(row[k]) for k in ('re2','rg2')] for row in rows])
    require(xy.shape==(256,2),'chain-resolved M256 frame required')
    values={key:float(np.mean([float(r[key]) for r in rows])) for key in SHORT}
    cov=np.cov(xy,rowvar=False,ddof=1)
    values.update(spatial_var_re2=float(cov[0,0]),spatial_var_rg2=float(cov[1,1]),
        spatial_cov_re2_rg2=float(cov[0,1]),raw_re4=float(np.mean(xy[:,0]**2)),raw_rg4=float(np.mean(xy[:,1]**2)))
    means=np.array([reference['values'][key]['estimate'] for key in ('re2','rg2')]);centered=xy-means
    values.update(reference_squared_re2=float(np.mean(centered[:,0]**2)),
        reference_squared_rg2=float(np.mean(centered[:,1]**2)),
        reference_cross_re2_rg2=float(np.mean(centered[:,0]*centered[:,1])))
    errors=np.array([reference['values'][key]['numerical_error'] for key in ('re2','rg2')])
    deviations=np.abs(xy.mean(axis=0)-means)
    err={'reference_squared_re2':float(2*deviations[0]*errors[0]+errors[0]**2),
         'reference_squared_rg2':float(2*deviations[1]*errors[1]+errors[1]**2),
         'reference_cross_re2_rg2':float(deviations[0]*errors[1]+deviations[1]*errors[0]+errors[0]*errors[1])}
    for column,name in enumerate(('X','Y')):
        for p,cut in zip(science.PROBABILITIES,reference['cuts'][column]):
            values[f'cdf_{name}_{p:g}']=float(np.mean(xy[:,column]<=cut))
    return values,err,xy


def reduce_replica(root,run,reference):
    root=Path(root);schedule=spec.schedule(run['dt']);dt=float(run['dt'])
    regular=schedule['scalar'];full=schedule['full'];series={};chain_xy={}
    reader=Rows(root/'samples.csv')
    try:
        for step in regular:
            bb=reader.take(256,step,dt)
            values,errors,xy=frame_backbone(bb,reference)
            series[step]={'metrics':values,'numerical_errors':errors};chain_xy[step]=xy
        reader.finish()
    finally:reader.file.close()
    readers={name:Rows(root/('equilibrium_'+name+'.csv')) for name in
             ('backbone','tangents','chains','connectors','sites','events')}
    readers['samples']=Rows(root/'samples.csv')
    events=[];populations=[];connector_scores=[];seen=np.zeros(8448,dtype=bool)
    for step in full:
        try:
            readers['samples'].seek(step)
            bb=readers['samples' if step%run['sample']==0 else 'backbone'].take(256,step,dt)
            tangent=readers['tangents'].take(256,step,dt)
            pop=readers['chains'].take(256,step,dt);con=readers['connectors'].take(2048,step,dt)
            sites=readers['sites'].take(8448,step,dt);event=readers['events'].take(1,step,dt)[0]
            ids=[int(row['spring']) for row in sites];seen|=np.asarray(ids)>=0
            values=science.frame_statistics(run,bb,pop,con,ids,tangent)
            backbone,errors,xy=frame_backbone(bb,reference);values.update(backbone)
            zc=np.asarray([int(r['z']) for r in pop]);e2c=np.asarray([float(r['e2_sum']) for r in pop])
            f=xy[:,0]/reference['values']['re2']['estimate']-1
            sigma=math.sqrt(canonical_population()['variance'])
            values['A_joint']=float(np.sum(f*(zc-8))/(256*sigma))
            values['B_joint']=float(np.sum(f*(e2c-5*zc))/(2048*5))
            e2=np.asarray([float(r['e2']) for r in con])
            values.update(connector_e4=float(np.mean(e2**2)),connector_radial_mean=float(np.mean(np.sqrt(e2))),
                          population_multiple=float(np.mean(zc>=2)))
            series[step]={'metrics':values,'numerical_errors':errors};chain_xy[step]=xy
            populations.append(zc);connector_scores.append(e2c-5*zc)
            events.append({'step':step,'counts':{k:int(event[k]) for k in auth.COUNTERS}})
        except BaseException:
            for reader in readers.values():reader.file.close()
            raise
    try:
        for reader in readers.values():reader.finish()
    finally:
        for reader in readers.values():reader.file.close()
    shared_intervals=rates_between(events,[s for s in full if s!=1],run['dt'])
    regular_rates=rates_between(events,schedule['regular_full'],run['dt'])
    for step,record in shared_intervals.items():series[step]['metrics'].update(record['metrics'])
    temporal={}
    scalar_keys=set(series[regular[1]]['metrics'])
    initial=series[0]['metrics']
    for start,end in ((0,100),(50,100)):
        segment={}
        for key in initial:
            grid=regular if key in scalar_keys else schedule['regular_full']
            grid=[s for s in grid if start<=Fraction(s)*Fraction(run['dt'])<=end]
            times=[time_key(s,run['dt']) for s in grid]
            target=reference['values'].get(key,{}).get('estimate')
            if target is None:target=science.reference(32,256,2048,run['kappa'],100)['targets'].get(key)
            segment[key]=acf_diagnostic(times,[series[s]['metrics'][key] for s in grid],'.5' if key in scalar_keys else '2',target)
        for col,name in enumerate(('re2_fixed_label','rg2_fixed_label')):
            grid=[s for s in regular if start<=Fraction(s)*Fraction(run['dt'])<=end]
            target=reference['values']['re2' if col==0 else 'rg2']['estimate']
            segment[name]=acf_diagnostic([time_key(s,run['dt']) for s in grid],
                [chain_xy[s][:,col] for s in grid],'.5',target)
        indices=[i for i,s in enumerate(full) if s in schedule['regular_full'] and start<=Fraction(s)*Fraction(run['dt'])<=end]
        times=[time_key(full[i],run['dt']) for i in indices]
        segment['population_fixed_label']=acf_diagnostic(times,[populations[i] for i in indices],'2',8.)
        segment['connector_score_fixed_chain']=acf_diagnostic(times,[connector_scores[i] for i in indices],'2',0.)
        rate_steps=[s for s in regular_rates if start<Fraction(s)*Fraction(run['dt'])<=end]
        for key in next(iter(regular_rates.values()))['metrics']:
            segment[key]=acf_diagnostic([time_key(s,run['dt']) for s in rate_steps],
                [regular_rates[s]['metrics'][key] for s in rate_steps],'2')
        temporal[f'{start}:{end}']=segment
    return {'run':run,'series':{time_key(s,run['dt']):dict(v,step=s,time=float(Fraction(s)*Fraction(run['dt'])),
                diagnostic_only=s==1) for s,v in sorted(series.items())},
        'regular_scalar_times':[time_key(s,run['dt']) for s in regular],
        'regular_e1_times':[time_key(s,run['dt']) for s in schedule['regular_full']],
        'regular_event_rates':{time_key(s,run['dt']):v for s,v in regular_rates.items()},
        'event_intervals':{time_key(s,run['dt']):v for s,v in rates_between(events,full,run['dt']).items()},
        'event_totals':{k:sum(e['counts'][k] for e in events) for k in auth.COUNTERS},
        'coverage':{'site_ever_occupied':seen.astype(int).tolist(),'observed_site_fraction':float(seen.mean())},
        'acf':temporal}


def targets_for(run,reference):
    targets={k:{'estimate':v,'interval':[v,v],'standard_error':0.,'numerical_error':0.,'source':'ANALYTICAL'}
             for k,v in science.reference(32,256,2048,run['kappa'],100)['targets'].items()}
    targets.update(reference['values'])
    # Carry recorded radial numerical errors instead of treating quadrature as exact.
    radial=reference['radial']
    for key,p in (('mean_r','1'),('mean_r2','2')):
        value=radial['moments'][p];error=radial['errors'][p]
        targets[key]=dict(estimate=value,interval=[value-error,value+error],standard_error=0.,numerical_error=error,source='ANALYTICAL')
    canonical=canonical_population()
    targets.update(connector_e4={'estimate':125/3,'interval':[125/3]*2,'standard_error':0.},
        connector_radial_mean={'estimate':2*math.sqrt(10/(3*math.pi)),
                              'interval':[2*math.sqrt(10/(3*math.pi))]*2,'standard_error':0.},
        population_multiple={'estimate':1-sum(canonical['pmf'][:2]),
                             'interval':[1-sum(canonical['pmf'][:2])]*2,'standard_error':0.})
    return targets


def window_values(replica,key,early):
    lo,hi=(0,10) if early else (90,100)
    if key.startswith('rate_'):
        source={t:r['metrics'] for t,r in replica['regular_event_rates'].items()}
        times=[t for t in source if lo<Fraction(t)<=hi]
    else:
        source={t:r['metrics'] for t,r in replica['series'].items()}
        # Scalar observables are present at all scalar frames; extras never enter window means.
        grid=replica['regular_scalar_times'] if all(key in source[t] for t in replica['regular_scalar_times']) else replica['regular_e1_times']
        times=[t for t in grid if lo<=Fraction(t)<=hi]
    require(times and all(key in source[t] for t in times),'missing predeclared window frames')
    return {'times':times,'mean':float(np.mean([source[t][key] for t in times]))}


def matched_times(fine,coarse):
    return [time for time in sorted(set(fine['series'])&set(coarse['series']),key=Fraction)
            if not (fine['series'][time]['diagnostic_only'] or coarse['series'][time]['diagnostic_only'])]


def aggregate(replicas,manifest,references):
    require(len(replicas)==16 and [r['run'] for r in replicas]==manifest['runs'],'incomplete ordered cohort; no full scientific result')
    cells={}
    for cell in range(1,5):
        group=[r for r in replicas if r['run']['cell']==cell]
        require([r['run']['replica'] for r in group]==[1,2,3,4],'independent R4 cell required')
        reference=references['cases'][str(group[0]['run']['kappa'])]
        targets=targets_for(group[0]['run'],reference)
        times=list(group[0]['series'])
        require(all(list(r['series'])==times for r in group),'replica frames differ')
        by_time={}
        for time in times:
            keys=set(group[0]['series'][time]['metrics'])
            require(all(set(r['series'][time]['metrics'])==keys for r in group),'inconsistent observable support')
            by_time[time]={}
            for key in sorted(keys):
                values=[r['series'][time]['metrics'][key] for r in group]
                error=max(r['series'][time]['numerical_errors'].get(key,0.) for r in group)
                by_time[time][key]={'against_reference':summary(values,targets[key],key,error),
                    'paired_change_from_initial':summary([v-r['series']['0']['metrics'][key] for v,r in zip(values,group)],
                        {'estimate':0.,'interval':[0.,0.],'standard_error':0.},key='change_'+key,numerical_error=error+max(r['series']['0']['numerical_errors'].get(key,0.) for r in group))
                    if key in group[0]['series']['0']['metrics'] else None}
        keys=sorted(set().union(*(r['metrics'] for r in group[0]['series'].values())))
        windows={}
        for key in keys:
            early=[window_values(r,key,True) for r in group];late=[window_values(r,key,False) for r in group]
            error=max(v for r in group for frame in r['series'].values()
                      for v in [frame['numerical_errors'].get(key,0.)])
            windows[key]={'early_times':early[0]['times'],'late_times':late[0]['times'],
                'early':summary([v['mean'] for v in early],targets[key],key,error),
                'late':summary([v['mean'] for v in late],targets[key],key,error),
                'paired_late_minus_initial':summary([v['mean']-r['series']['0']['metrics'][key] for v,r in zip(late,group)],
                    {'estimate':0.,'interval':[0.,0.],'standard_error':0.},key='change_'+key,numerical_error=2*error)
                    if key in group[0]['series']['0']['metrics'] else None,
                'paired_late_minus_early':summary([b['mean']-a['mean'] for a,b in zip(early,late)],
                    {'estimate':0.,'interval':[0.,0.],'standard_error':0.},key='change_'+key,numerical_error=2*error)}
        design_effect={}
        for time,metrics in by_time.items():
            design_effect[time]={}
            for key,var in (('re2','spatial_var_re2'),('rg2','spatial_var_rg2')):
                sd=metrics[key]['against_reference']['replica_sd']
                vref=reference['values'][var]
                lo,hi=vref['interval']
                require(lo>0,'positive variance-reference interval required')
                design_effect[time][key]={'estimate':256*sd**2/vref['estimate'],
                    'nominal_interval':[256*3*sd**2/float(chi2.ppf(1-ALPHA/2,3))/hi,
                                        256*3*sd**2/float(chi2.ppf(ALPHA/2,3))/lo],
                    'qualification':'R4 Gaussian-replica variance approximation with stored reference bounds; not guaranteed coverage'}
        acf_support={}
        for segment in group[0]['acf']:
            acf_support[segment]={}
            for key in group[0]['acf'][segment]:
                entries=[r['acf'][segment][key] for r in group]
                tau=[a['tau_int'] for a in entries]
                acf_support[segment][key]={'replica_tau_int':tau,
                    'resolved_replicas':sum(v is not None for v in tau),
                    'replica_candidate_tau_int':[a.get('candidate_tau_int') for a in entries],
                    'all_replica_support_demonstrated':all(v is not None for v in tau),
                    'qualification':'R4 diagnostics only; no replacement of unresolved replicas by zero or resolved-only averaging'}
        cells[str(cell)]={'acf_replica_support':acf_support,'spatial_design_effect':design_effect,'time_resolved':by_time,'windows':windows,
            'reference_cdf_status':reference['cdf_status'], 'reference_moments_status':reference['moments_status']}
    contrasts=[]
    for cell in (1,3):
        fine=[r for r in replicas if r['run']['cell']==cell];coarse=[r for r in replicas if r['run']['cell']==cell+1]
        data={}
        for time in matched_times(fine[0],coarse[0]):
            keys=set.intersection(*(set(r['series'][time]['metrics']) for r in fine+coarse))
            data[time]={key:independent_contrast([r['series'][time]['metrics'][key] for r in fine],
                        [r['series'][time]['metrics'][key] for r in coarse],key) for key in sorted(keys)}
        window_contrasts={}
        for key in sorted(set(cells[str(cell)]['windows']) & set(cells[str(cell+1)]['windows'])):
            f=cells[str(cell)]['windows'][key];c=cells[str(cell+1)]['windows'][key]
            require(f['early_times']==c['early_times'] and f['late_times']==c['late_times'], 'unmatched timestep windows')
            window_contrasts[key]={window:independent_contrast(f[window]['replica_values'],c[window]['replica_values'],
                    'change_'+key if window.startswith('paired_') else key)
                for window in ('early','late','paired_late_minus_initial','paired_late_minus_early')
                if f[window] is not None and c[window] is not None}
        contrasts.append({'fine_cell':cell,'coarse_cell':cell+1,'shared_physical_times':data,
                          'matched_window_contrasts':window_contrasts})
    unresolved=sum(a['unresolved_tail'] and a['status']!='UNDEFINED_ZERO_VARIANCE_OR_INSUFFICIENT_SUPPORT' for r in replicas for segment in r['acf'].values() for a in segment.values())
    counts=Counter()
    for cell in cells.values():
        for frame in cell['time_resolved'].values():
            for metric in frame.values():
                for statement in metric.values():
                    if statement is not None:counts.update(statement.get('outcomes',[]))
        for window in cell['windows'].values():
            for key in ('early','late','paired_late_minus_initial','paired_late_minus_early'):
                if window[key] is not None:counts.update(window[key].get('outcomes',[]))
    for contrast in contrasts:
        for frame in contrast['shared_physical_times'].values():
            for metric in frame.values():counts.update(metric['outcomes'])
        for window in contrast['matched_window_contrasts'].values():
            for metric in window.values():counts.update(metric['outcomes'])
    if unresolved:counts.update(['AUTOCORRELATION_TAIL_UNRESOLVED','INSUFFICIENT_TIME_HORIZON'])
    return {'schema':'e1-d16b-exploratory-analysis-v1','scientific_acceptance':None,
        'status':'EXPLORATORY_COMPLETE','independent_clusters':4,'independent_unit':'whole M256 replica',
        'cells':cells,'replicas':replicas,'timestep_contrasts':contrasts,
        'outcomes':sorted(counts),'outcome_counts':dict(counts),
        'confirmatory_planning':{'status':'INDEPENDENT_DESIGN_REVIEW_REQUIRED',
            'replica_variance_and_window_inputs_available':True,'unresolved_acf_diagnostics':unresolved,
            'stiff_CDF_reference_precision':'UNRESOLVED','execution_authorized':False,
            'qualification':'T100/R4 supplies exploratory power/horizon inputs; no automatic simultaneous power, independent temporal sample gain or confirmatory design acceptance'},
        'unresolved_acf_diagnostics':unresolved,'canonical_reference':canonical_population(),
        'reference_covariance_and_intervals':references,
        'limitations':['R4 nominal pointwise inference, no campaign-wide detection guarantee or D0 equivalence pass.',
            'Spatial sample variance estimates marginal variance minus cross-chain covariance under exchangeability.',
            'Reference-centered squared deviations include mean drift squared.',
            'Unresolved stiff CDF precision is retained, never accepted distributional calibration.',
            'No burn-in removed; ACF stationarity is conditional, fast dynamics below cadence unresolved.',
            'Accepted/renewal events are not independent observations; exact mean population is conservation only.',
            'Two dt levels establish neither convergence order nor the zero-dt limit.']}


def analyze(root,output,approval_sha,completion_sha):
    root=spec.durable(root);output=spec.output_path(output)
    require(not output.exists() and not output.is_relative_to(root),'fresh analysis outside raw cohort required')
    manifest,items=auth.authenticate_campaign(root,spec.CONFIG/'manifest.json',spec.digest(spec.CONFIG/'manifest.json'),approval_sha,completion_sha)
    from e1_d16b_references import import_moments
    references=import_moments()
    require(references==load(root.parent/'references.json'),'reviewed reference import changed')
    replicas=[reduce_replica(i['root'],i['run'],references['cases'][str(i['run']['kappa'])]) for i in items]
    result=aggregate(replicas,manifest,references)
    result['authentication']={'manifest':file_record(spec.CONFIG/'manifest.json'),
        'approval':file_record(root/'approval.json'),'completion':file_record(root/'campaign_complete.json'),
        'sources':spec.tool_hashes(),'raw_receipts':{i['run']['id']:file_record(i['root'].parent/'execution.json') for i in items}}
    # Authenticate again after reading; never accept changed inputs.
    auth.authenticate_campaign(root,spec.CONFIG/'manifest.json',spec.digest(spec.CONFIG/'manifest.json'),approval_sha,completion_sha)
    with output.open('xb') as stream:
        with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as zipped:zipped.write(encoded(result))
    return {'status':'EXPLORATORY_COMPLETE','scientific_acceptance':None,'output':str(output),'file':file_record(output),
            'outcomes':result['outcomes'],'outcome_counts':result['outcome_counts'],
            'confirmatory_planning':result['confirmatory_planning'],
            'unresolved_acf_diagnostics':result['unresolved_acf_diagnostics']}
