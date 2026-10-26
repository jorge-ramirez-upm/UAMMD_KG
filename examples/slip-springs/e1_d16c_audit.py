"""Focused independent secondary audit. Same-data post-selection; never acceptance."""
from fractions import Fraction
from functools import partial
import gzip
import html
import math
from pathlib import Path

import numpy as np
from scipy.stats import t, chi2

import e1_d16c_spec as spec
from e1_d1_pilot import require, load, encoded, file_record
from e1_observer_check import Rows
from e1_d14_phase_b_analysis import rates_between, time_key
from e1_d16c_evidence import authenticate, analysis_metadata, verify_lock
from e1_d16b_analysis import canonical_population


QUALIFICATION='Same-data post-selection exploratory diagnostics; nominal intervals and Bonferroni sensitivity do not establish controlled post-selection FWER.'


def uncertainty(values,reference=None,other=None,numerical_error=0.,family_size=None):
    """One estimator per whole replica; independent cells never paired."""
    a=np.asarray(values,dtype=float)
    require(a.shape==(4,) and np.isfinite(a).all(),'four finite independent replica estimators required')
    mean=float(a.mean());v=float(a.var(ddof=1)/4);df=3.;point=mean
    result={'replica_values':a.tolist(),'replica_contributions_to_mean':(a/4).tolist(),
        'within_cell_replica_sd':float(a.std(ddof=1)),'leave_one_out_means':[(float(a.sum())-float(x))/3 for x in a]}
    if other is not None:
        b=np.asarray(other,dtype=float)
        require(b.shape==(4,) and np.isfinite(b).all(),'independent comparison requires four other replicas')
        vb=float(b.var(ddof=1)/4);point=mean-float(b.mean())
        df=(v+vb)**2/(v*v/3+vb*vb/3) if v+vb else 3.
        result.update(other_replica_values=b.tolist(),other_cell_replica_sd=float(b.std(ddof=1)),independent_variance_contributions=[v,vb]);v+=vb
    se=math.sqrt(v)
    intervals={}
    levels=[('pointwise_nominal',1)]
    if family_size is not None:
        require(family_size==6,'only the frozen six-primary sensitivity is specified')
        levels.append(('six_contrast_nominal_sensitivity',family_size))
    for label,size in levels:
        half=float(t.ppf(1-.025/(2*size),df))*se
        lo,hi=point-half,point+half
        if reference is not None:
            lo-=reference['interval'][1];hi-=reference['interval'][0]
        intervals[label]=[lo-numerical_error,hi+numerical_error]
    target=reference['estimate'] if reference is not None else 0.
    deviation=point-target
    signal=se>0 and (intervals['pointwise_nominal'][0]>0 or intervals['pointwise_nominal'][1]<0)
    result.update(estimate=point,difference=deviation,standard_error=se,degrees_of_freedom=df,
        intervals=intervals,reference=reference,reference_standard_error=reference.get('standard_error',0.) if reference else 0.,
        independent_combined_standard_error=math.sqrt(v+(reference.get('standard_error',0.)**2 if reference else 0.)),
        numerical_error_estimate=numerical_error,zero_observed_replica_dispersion=se==0,
        observed_deviation=deviation!=0.,outcome='POST_SELECTION_EXPLORATORY_SIGNAL' if signal else 'INSUFFICIENT_PRECISION_TO_RESOLVE_DEVIATION',
        qualification=QUALIFICATION,independent_unit='whole replica',scientific_acceptance=None)
    return result


def spatial_frame(rows,reference):
    x=np.array([float(r['re2']) for r in rows]);y=np.array([float(r['rg2']) for r in rows])
    require(len(x)==len(y)==256 and np.isfinite(x).all() and np.isfinite(y).all(),'complete M256 backbone frame required')
    mux,muy=reference['values']['re2']['estimate'],reference['values']['rg2']['estimate']
    covariance=np.cov(x,y,ddof=1)
    values={'re2':float(x.mean()),'rg2':float(y.mean()),'spatial_var_re2':float(covariance[0,0]),
        'spatial_var_rg2':float(covariance[1,1]),'cov_re2_rg2':float(covariance[0,1]),
        'reference_squared_re2':float(np.mean((x-mux)**2)),
        'reference_squared_rg2':float(np.mean((y-muy)**2)),
        'reference_cross_re2_rg2':float(np.mean((x-mux)*(y-muy))),
        'raw_re4':float(np.mean(x*x)),'raw_rg4':float(np.mean(y*y)),
        'max_chain_re2':float(x.max()),'top_chain_second_moment_fraction':float(np.max(x*x)/np.sum(x*x)),
        'mean_r':float(np.mean([float(r['mean_r']) for r in rows])),
        'mean_r2':float(np.mean([float(r['mean_r2']) for r in rows]))}
    values['spatial_centering_identity_residual']=(values['reference_squared_re2']-
        ((255/256)*values['spatial_var_re2']+(values['re2']-mux)**2))
    error=reference['values']['re2']['numerical_error']
    values['reference_centering_numerical_error_estimate']=2*abs(values['re2']-mux)*error+error*error
    return values,x,y


def occupancy_weighting(populations,squares,strata,reference_weights):
    z=np.asarray(populations,dtype=int);q=np.asarray(squares,dtype=float)
    require(z.shape==q.shape and np.all(z>=0) and np.isfinite(q).all()
            and np.all(q>=0) and z.sum()>0 and np.all(q[z==0]==0),'invalid population/connector scores')
    total=int(z.sum());groups=[]
    for (lo,hi),weight in zip(strata,reference_weights):
        mask=(z>=lo)&(z<=hi);count=int(z[mask].sum());numerator=float(q[mask].sum())
        groups.append({'population_range':[lo,hi],'springs':count,'chains':int(mask.sum()),'e2_sum':numerator,
            'connector_mean':numerator/count if count else None,'observed_spring_weight':count/total,'reference_spring_weight':weight})
    require(sum(g['springs'] for g in groups)==total,'occupancy strata incomplete')
    supported=all(g['springs']>0 or g['reference_spring_weight']==0 for g in groups)
    fixed=sum(g['reference_spring_weight']*g['connector_mean'] for g in groups) if supported else None
    return {'all_live_spring_mean':float(q.sum()/total),
        'equal_occupied_chain_mean':float(np.mean(q[z>0]/z[z>0])),
        'fixed_reference_weight_mean':fixed,'fixed_weight_support':supported,'strata':groups,
        'empty_chain_count':int(np.sum(z==0)),
        'by_exact_population':[{'z':k,'chains':int(np.sum(z==k)),'springs':int(z[z==k].sum()),
            'mean':float(q[z==k].sum()/(k*np.sum(z==k))) if k and np.any(z==k) else None} for k in range(34)]}


def window_weighting(frames,reference_weights):
    groups=[]
    for i,weight in enumerate(reference_weights):
        count=sum(f['strata'][i]['springs'] for f in frames)
        numerator=sum(f['strata'][i]['e2_sum'] for f in frames)
        groups.append({'springs':count,'mean':numerator/count if count else None,
                       'weight':count/(len(frames)*2048),'reference_weight':weight})
    supported=all(g['springs']>0 for g in groups)
    return {'groups':groups,'all_spring_mean':sum(g['weight']*(g['mean'] or 0.) for g in groups),
            'standardized_mean':sum(g['reference_weight']*g['mean'] for g in groups) if supported else None,
            'complete_stratum_support':supported,
            'qualification':'Pooled within-window sums retain every full frame; whole replicas remain uncertainty units.'}


def weight_decomposition(early,late):
    if not (early['complete_stratum_support'] and late['complete_stratum_support']):
        return {'status':'UNSUPPORTED_STRATUM','within':None,'composition':None}
    within=sum((a['weight']+b['weight'])/2*(b['mean']-a['mean']) for a,b in zip(early['groups'],late['groups']))
    composition=sum((a['mean']+b['mean'])/2*(b['weight']-a['weight']) for a,b in zip(early['groups'],late['groups']))
    delta=late['all_spring_mean']-early['all_spring_mean']
    return {'status':'DESCRIPTIVE_EXACT_DECOMPOSITION','within':within,'composition':composition,'observed_change':delta,
            'identity_residual':delta-within-composition,'causal_attribution':False}


def secondary_acf(times,values,spacing,baseline):
    x=np.asarray(values,dtype=float);times=[Fraction(s) for s in times];delta=Fraction(spacing)
    require(len(times)==len(x) and len(x)>=2 and np.isfinite(x).all()
            and times==sorted(set(times)) and all(b-a==delta for a,b in zip(times,times[1:])),'exact uniform ACF grid required')
    n=len(x);maximum=n//4;duration=float(times[-1]-times[0]);results={}
    if n<8:
        return {'estimators':{},'duration':duration,'samples':n,'spacing_exact':str(delta),'tau_int':None,
                'unresolved_tail':True,'failed_support':{'both':['INSUFFICIENT_ORIGIN_SUPPORT']},
                'horizon_failure':True,'stability_failure':False}
    shifted=x-x[0]
    for label,u in (('demeaned',shifted-shifted.mean()),('reference_centered',x-baseline)):
        den=float(u@u)
        if den<=0:
            results[label]={'status':'UNDEFINED_ZERO_VARIANCE','tau_int':None,'failed_support':['NORMALIZED_ACF_UNDEFINED']};continue
        correlation=np.correlate(u,u,mode='full')[n-1:n+maximum]
        fixed=(correlation/den).tolist()
        overlap=[float(np.mean(u[:-k]*u[k:])/(den/n)) for k in range(1,maximum+1)]
        partial=(float(delta)*(.5+np.cumsum(overlap))).tolist()
        caps=sorted({max(1,maximum//4),max(1,maximum//2),maximum})
        estimates=[partial[k-1] for k in caps];candidate=estimates[-1]
        failed=[]
        if candidate<=0:failed.append('NONPOSITIVE_PARTIAL_SUM')
        if candidate>0 and duration<50*candidate:failed.append('INSUFFICIENT_HORIZON_50_TAU')
        if candidate>0 and maximum*float(delta)<5*candidate:failed.append('LAG_SUPPORT_BELOW_5_TAU')
        if max(abs(v) for v in overlap[-min(3,len(overlap)):])>.1:failed.append('TAIL_NOT_SMALL_AT_AVAILABLE_LAGS')
        if max(estimates)-min(estimates)>.25*max(abs(candidate),float(delta)/2):failed.append('LAG_WINDOW_INSTABILITY')
        blocks={}
        for width in (2,4,8):
            count=n//width
            block_means=[float(x[i*width:(i+1)*width].mean()) for i in range(count)]
            blocks[str(width)]={'block_duration':width*float(delta),'complete_blocks':count,
                'block_means':block_means,
                'naive_block_SE_diagnostic':float(np.std(block_means,ddof=1)/math.sqrt(count)) if count>=2 else None,
                'unused_terminal_frames':n-count*width,'inference':'within-replica stability diagnostic, not independent uncertainty'}
        estimates_by_block=[b['naive_block_SE_diagnostic'] for b in blocks.values()]
        if any(b['complete_blocks']<4 for b in blocks.values()):failed.append('INSUFFICIENT_BLOCK_SUPPORT')
        if all(v is not None for v in estimates_by_block):
            low,high=min(estimates_by_block),max(estimates_by_block)
            if low==0 or high>2*low:failed.append('BLOCK_LENGTH_INSTABILITY_OR_ALIAS')
        halves=[]
        for part in (x[:n//2],x[n//2:]):
            v=part-part.mean() if label=='demeaned' else part-baseline
            denominator=float(v@v);cap=len(v)//4
            halves.append(float(delta)*(.5+sum(float(v[:-k]@v[k:]/denominator)*len(v)/(len(v)-k) for k in range(1,cap+1)))
                          if denominator>0 and cap else None)
        if any(v is None or abs(v-candidate)>.5*max(abs(candidate),float(delta)/2) for v in halves):failed.append('HALF_RECORD_INSTABILITY')
        results[label]={'status':'SUPPORT_CRITERIA_FAILED' if failed else 'NOMINAL_SUPPORT_CRITERIA_MET',
            'lags':list(range(maximum+1)),'lag_times':[k*float(delta) for k in range(maximum+1)],
            'origin_counts':[n-k for k in range(maximum+1)],'overlap_corrected_acf':[1.]+overlap,
            'fixed_denominator_crosscheck':fixed,'integrated_partial_sums':partial,'window_lags':caps,
            'window_partial_sums':estimates,'half_record_partial_sums':halves,'block_sensitivity':blocks,
            'candidate_partial_sum':candidate,'failed_support':failed,'tau_int':None}
    # This independent diagnostic does not promote a finite-record partial sum to a resolved IAT.
    centering={}
    if all('candidate_partial_sum' in r for r in results.values()):
        a,b=[results[k]['candidate_partial_sum'] for k in ('demeaned','reference_centered')]
        centering={'difference_in_terminal_partial_sum':a-b,
                   'relative_sensitivity_failed':abs(a-b)>.25*max(abs(a),abs(b),float(delta)/2)}
        if centering['relative_sensitivity_failed']:
            for entry in results.values():entry['failed_support'].append('CENTERING_INSTABILITY')
    failures={k:r.get('failed_support',[]) for k,r in results.items()}
    return {'estimators':results,'duration':duration,'samples':n,'spacing_exact':str(delta),'tau_int':None,
            'unresolved_tail':True,'failed_support':failures,'centering_sensitivity':centering,
            'horizon_failure':any('INSUFFICIENT_HORIZON_50_TAU' in f or 'LAG_SUPPORT_BELOW_5_TAU' in f for f in failures.values()),
            'stability_failure':any(any('INSTABILITY' in v for v in f) for f in failures.values()),
            'qualification':'No first-zero truncation; partial sums are not bounds; conditional stationarity and sub-cadence dynamics remain unresolved.'}


def reduce_replica(root,run,reference,protocol):
    import e1_d16b_spec as old_spec
    schedule=old_spec.schedule(run['dt']);dt=float(run['dt']);series={};reader=Rows(root/'samples.csv')
    try:
        for step in schedule['scalar']:
            values,_,_=spatial_frame(reader.take(256,step,dt),reference)
            series[time_key(step,run['dt'])]=values
        reader.finish()
    finally:reader.file.close()
    weights=[];pmf=canonical_population()['pmf']
    for low,high in protocol['occupancy_strata']:weights.append(sum(k*pmf[k]/8 for k in range(low,high+1)))
    full={};events=[]
    if run['kappa']==10:
        names=('backbone','chains','connectors','sites','events')
        readers={name:Rows(root/('equilibrium_'+name+'.csv')) for name in names};readers['samples']=Rows(root/'samples.csv')
        try:
            for step in schedule['full']:
                readers['samples'].seek(step)
                bb=readers['samples' if step%run['sample']==0 else 'backbone'].take(256,step,dt)
                values,x,y=spatial_frame(bb,reference)
                pop=readers['chains'].take(256,step,dt);con=readers['connectors'].take(2048,step,dt)
                sites=readers['sites'].take(8448,step,dt);event=readers['events'].take(1,step,dt)[0]
                z=np.array([int(row['z']) for row in pop]);q=np.array([float(row['e2_sum']) for row in pop])
                e2=np.array([float(row['e2']) for row in con]);require(z.sum()==2048,'canonical population violation')
                np.testing.assert_allclose(q.sum(),e2.sum(),rtol=3e-12,atol=3e-12)
                population=canonical_population();f=x/reference['values']['re2']['estimate']-1
                values.update(connector_e2=float(e2.mean()),connector_e4=float(np.mean(e2**2)),
                    A_joint=float(np.sum(f*(z-8))/(256*math.sqrt(population['variance']))),
                    B_joint=float(np.sum(f*(q-5*z))/(2048*5)),population_variance=float(np.mean((z-8)**2)),
                    population_connector_score_cov=float(np.cov(z,q-5*z,ddof=1)[0,1]))
                weighting=occupancy_weighting(z,q,protocol['occupancy_strata'],weights)
                occupied=np.array([int(row['spring'])>=0 for row in sites]).reshape(256,33)
                values.update(occupancy_ends=float(occupied[:,[0,32]].mean()),occupancy_interior=float(occupied[:,1:32].mean()),
                    occupied_chain_fraction=float(np.mean(z>0)),equal_occupied_chain_e2=weighting['equal_occupied_chain_mean'])
                cdf={str(p):float(np.mean(e2<=(5/3)*chi2.ppf(p,3))) for p in protocol['connector_CDF_probabilities']}
                full[time_key(step,run['dt'])]={'metrics':values,'connector_cdf':cdf,'weighting':weighting,'step':step}
                from e1_d16b_auth import COUNTERS
                events.append({'step':step,'counts':{key:int(event[key]) for key in COUNTERS}})
            for r in readers.values():r.finish()
        finally:
            for r in readers.values():r.file.close()
    regular_full=[time_key(s,run['dt']) for s in schedule['regular_full']]
    rate_records=rates_between(events,schedule['regular_full'],run['dt']) if events else {}
    windows={}
    for name,(lo,hi) in protocol['windows'].items():
        scalar_times=[key for key in series if Fraction(lo)<=Fraction(key)<=Fraction(hi)]
        require(len(scalar_times)==int((Fraction(hi)-Fraction(lo))*2)+1,'missing scalar window frame')
        entry={'scalar_times':scalar_times,'scalar':{key:float(np.mean([series[time][key] for time in scalar_times])) for key in series['0']},
               'temporal_variance_of_replica_mean':{key:float(np.var([series[time][key] for time in scalar_times],ddof=1)) for key in ('re2','rg2')}}
        if full:
            times=[key for key in regular_full if Fraction(lo)<=Fraction(key)<=Fraction(hi)]
            require(len(times)==int((Fraction(hi)-Fraction(lo))/2)+1,'missing E1 window frame')
            entry.update(full_times=times,full={key:float(np.mean([full[time]['metrics'][key] for time in times])) for key in full['0']['metrics']},
                connector_cdf={p:float(np.mean([full[time]['connector_cdf'][p] for time in times])) for p in full['0']['connector_cdf']},
                weighting=window_weighting([full[time]['weighting'] for time in times],weights))
            rate_times=[s for s in rate_records if Fraction(lo)<Fraction(s)*Fraction(run['dt'])<=Fraction(hi)]
            entry['event_rates']={key:float(np.mean([rate_records[s]['metrics'][key] for s in rate_times])) for key in next(iter(rate_records.values()))['metrics']}
        windows[name]=entry
    acfs={}
    for lo,hi in protocol['acf_segments']:
        entries={}
        for key in protocol['acf_metrics']:
            scalar=key in series['0'];source=series if scalar else {time:full[time]['metrics'] for time in regular_full} if full else {}
            if not source:continue
            times=[time for time in source if Fraction(lo)<=Fraction(time)<=Fraction(hi)]
            baseline=reference['values'].get(key,{}).get('estimate')
            if baseline is None:baseline={'connector_e2':5.,'A_joint':0.,'B_joint':0.,'population_variance':canonical_population()['variance']}[key]
            entries[key]=secondary_acf(times,[source[time][key] for time in times],'.5' if scalar else '2',baseline)
        acfs[lo+':'+hi]=entries
    return {'run':run,'scalar_series':series,'full_series':full,'windows':windows,'secondary_acf':acfs,
        'event_intervals':{time_key(s,run['dt']):v for s,v in rate_records.items()},
        'occupancy_change_decompositions':{a+'->'+b:weight_decomposition(windows[a]['weighting'],windows[b]['weighting'])
            for a,b in (('early','late'),('early_wide','late_wide'),('middle','late'))} if full else None}


def values(group,window,key,full=False):
    return [r['windows'][window]['full' if full else 'scalar'][key] for r in group]


def probability_summary(values,change=False):
    result=uncertainty(values)
    low,high=(-1.,1.) if change else (0.,1.)
    half=(high-low)*math.sqrt(math.log(2/.025)/8)
    mean=result['estimate'];result['replica_Hoeffding_interval']=[max(low,mean-half),min(high,mean+half)]
    result['outcome']='BOUNDED_PROBABILITY_DIAGNOSTIC_NO_POST_SELECTION_ACCEPTANCE'
    return result



def matched_times(fine,coarse):
    require(all(str(Fraction(key))==key for source in (fine,coarse) for key in source),
            'canonical exact physical-time keys required')
    return sorted(set(fine)&set(coarse),key=Fraction)


def aggregate(replicas,references,protocol,original_header):
    require(len(replicas)==16 and len({r['run']['seed'] for r in replicas})==16,'complete independent cohort required')
    groups={cell:[r for r in replicas if r['run']['cell']==cell] for cell in range(1,5)}
    require(all([r['run']['replica'] for r in group]==[1,2,3,4] for group in groups.values()),'R4 ordering/coverage failed')
    flex=groups[1];coarse=groups[4];fine=groups[3]
    a_reference=references['cases']['0']['values']['spatial_var_re2']
    primary_interval=partial(uncertainty,family_size=6)
    primary={
        'A_late_spatial_variance_minus_exact':primary_interval(values(flex,'late','spatial_var_re2'),a_reference),
        'A_spatial_variance_late_minus_early':primary_interval(np.subtract(values(flex,'late','spatial_var_re2'),values(flex,'early','spatial_var_re2'))),
        'B_connector_e2_late_minus_early':primary_interval(np.subtract(values(coarse,'late','connector_e2',True),values(coarse,'early','connector_e2',True))),
        'C_A_joint_coarse_minus_fine_late':primary_interval(values(coarse,'late','A_joint',True),other=values(fine,'late','A_joint',True)),
        'C_A_joint_change_contrast':primary_interval(np.subtract(values(coarse,'late','A_joint',True),values(coarse,'early','A_joint',True)),
            other=np.subtract(values(fine,'late','A_joint',True),values(fine,'early','A_joint',True)))}
    weighted=[r['windows']['late']['weighting']['standardized_mean']-r['windows']['early']['weighting']['standardized_mean']
        if all(r['windows'][w]['weighting']['standardized_mean'] is not None for w in ('early','late')) else None for r in coarse]
    primary['B_fixed_weight_connector_late_minus_early']=(primary_interval(weighted) if all(v is not None for v in weighted) else
        {'outcome':'INSUFFICIENT_STRATUM_SUPPORT','replica_values':weighted,'qualification':QUALIFICATION})
    require(set(primary)==set(protocol['primary_contrasts']),'primary follow-up family changed')
    flex_times={}
    for time in flex[0]['scalar_series']:
        v=[r['scalar_series'][time]['spatial_var_re2'] for r in flex]
        means=np.array([r['scalar_series'][time]['re2'] for r in flex])
        pooled=(255*sum(v)+256*float(np.sum((means-means.mean())**2)))/(1024-1)
        flex_times[time]={'spatial_variance':uncertainty(v,a_reference),
            'fractional_replica_contributions':[value/sum(v) for value in v] if sum(v)>0 else None,
            'null_independent_backbone_mean_variance':a_reference['estimate']/256,
            'replica_mean_design_effect_diagnostic':256*float(means.var(ddof=1))/a_reference['estimate'],
            'average_within_replica_spatial_variance':float(np.mean(v)),
            'pooled_1024_chain_sample_variance':pooled,'between_replica_mean_variance':float(means.var(ddof=1)),
            'qualification':'Pooling decomposition is descriptive; SE is across four spatial-variance estimators, not 1024 chains.'}
    windows={}
    for name in protocol['windows']:
        windows[name]={
            'A':{key:uncertainty(values(flex,name,key),references['cases']['0']['values'].get(
                {'cov_re2_rg2':'spatial_cov_re2_rg2'}.get(key,key)),
                numerical_error=max(values(flex,name,'reference_centering_numerical_error_estimate')) if key=='reference_squared_re2' else 0.) for key in
                ('re2','rg2','spatial_var_re2','reference_squared_re2','raw_re4','raw_rg4','cov_re2_rg2')},
            'B':{key:uncertainty(values(coarse,name,key,True)) for key in
                ('connector_e2','connector_e4','equal_occupied_chain_e2','occupied_chain_fraction','population_variance',
                 'occupancy_ends','occupancy_interior','population_connector_score_cov')},
            'B_connector_CDF':{p:probability_summary([r['windows'][name]['connector_cdf'][p] for r in coarse])
                               for p in coarse[0]['windows'][name]['connector_cdf']},
            'B_connector_CDF_change_from_early':{p:probability_summary([r['windows'][name]['connector_cdf'][p]-r['windows']['early']['connector_cdf'][p] for r in coarse],change=True)
                for p in coarse[0]['windows'][name]['connector_cdf']},
            'B_event_rates':{key:uncertainty([r['windows'][name]['event_rates'][key] for r in coarse])
                               for key in coarse[0]['windows'][name]['event_rates']},
            'C':{key:uncertainty(values(coarse,name,key,True),other=values(fine,name,key,True)) for key in
                ('A_joint','B_joint','re2','rg2','cov_re2_rg2','population_variance','connector_e2')}}
    matched=matched_times(fine[0]['full_series'],coarse[0]['full_series'])
    temporal_contrasts={time:{key:uncertainty([r['full_series'][time]['metrics'][key] for r in coarse],
        other=[r['full_series'][time]['metrics'][key] for r in fine]) for key in
        ('A_joint','B_joint','re2','rg2','population_variance','connector_e2')} for time in matched}
    mean_changes={}
    for cell,group in groups.items():
        mean_changes[str(cell)]={key:uncertainty(np.subtract(values(group,'late',key),values(group,'early',key))) for key in ('re2','rg2')}
    stability=[]
    for r in replicas:
        for segment,metrics in r['secondary_acf'].items():
            for metric,entry in metrics.items():
                stability.append({'run':r['run']['id'],'segment':segment,'metric':metric,
                    'horizon_failure':entry['horizon_failure'],'stability_failure':entry['stability_failure'],
                    'failed_support':entry['failed_support']})
    interpretation={
        'mean_stationarity':{'contrasts':mean_changes,'qualification':'A null-compatible change interval cannot prove stationarity or equivalence; broad R4 uncertainty remains.'},
        'conformational_fluctuations':{'level_outcome':primary['A_late_spatial_variance_minus_exact']['outcome'],
            'change_outcome':primary['A_spatial_variance_late_minus_early']['outcome'],
            'qualification':'A spatial variance level deviation is distinct from drift and from replica-to-replica estimator variance. Outlying replicas remain included.'},
        'joint_timestep_sensitivity':primary['C_A_joint_coarse_minus_fine_late']['outcome'],
        'temporal_support':stability,'resolved_IAT_claim':False,'R':4,
        'new_campaign_recommendation':None,
        'design_discriminators':[
            'A separately powered independent replica cohort tests whether rare conformational/replica contributions recur. More chains alone do not replace independent replicas.',
            'A separately approved finer dt at matched physical horizons can distinguish reproducible finite-dt sensitivity; current two levels do not establish convergence order.',
            'A longer horizon is informative if lag support is the limiting criterion; unstable centering/block estimates first require stationarity/support review. Denser cadence tests fast aliasing, not long tails.',
            'Occupancy composition and conditional connector changes must be separated using supported strata. The decomposition is descriptive, not causal.',
            'Any independent exploratory or confirmatory design needs a new frozen endpoint family, power/variance budget, seeds and explicit approval; no automatic M/R/T increase.']}
    return {'schema':'e1-d16c-secondary-audit-v1','status':'SECONDARY_EXPLORATORY_COMPLETE','scientific_acceptance':None,
        'post_selection_exploratory':True,'qualification':QUALIFICATION,'primary_followup':primary,
        'hierarchical_families':{'A':['A_late_spatial_variance_minus_exact','A_spatial_variance_late_minus_early'],
                               'B':['B_connector_e2_late_minus_early','B_fixed_weight_connector_late_minus_early'],
                               'C':['C_A_joint_coarse_minus_fine_late','C_A_joint_change_contrast']},
        'flexible_variance_time_resolved':flex_times,'predefined_window_sensitivity':windows,
        'matched_stiff_timestep_contrasts':temporal_contrasts,'replicas':replicas,'interpretation':interpretation,
        'original_D16B_summary_unchanged':original_header,
        'multiplicity':{'selected_primary_count':6,'original_flag_counts':original_header['outcome_counts'],
            'qualification':QUALIFICATION,'correlated_support_counts_are_independent_evidence':False,
            'minimum_two_sided_sign_flip_p_R4':2/16,
            'sign_flip_note':'Within-cell paired-time changes under a hypothetical sign-symmetric null only; no sign-flip test or timestep pairing performed.',
            'algebraic_redundancy':'Reference-centered second moments, sample spatial variances and mean shifts share the exact centering identity; raw fourth moments and covariance are associated diagnostics, not independent confirmations.'}}


def audit(output,authentication_path):
    import e1_d16b_auth as old_auth
    import e1_d16b_spec as old_spec
    from e1_d16b_references import import_moments
    output=spec.durable(output)
    require(not output.exists() and not output.is_relative_to(Path(spec.original()['root'])), 'fresh audit output outside originals required')
    authentication=authenticate()
    require(authentication==load(authentication_path),'Stage A original authentication identity changed')
    lock,root=verify_lock();protocol=load(spec.CONFIG/'protocol.json')
    launch=load(root/'launch.json');session=load(root/'session.json')
    manifest,items=old_auth.authenticate_campaign(root/'campaign',root/'campaign/manifest.json',session['manifest']['sha256'],
        launch['approval_sha256'],lock['completion_sha256'])
    references=import_moments()
    replicas=[reduce_replica(item['root'],item['run'],references['cases'][str(item['run']['kappa'])],protocol) for item in items]
    result=aggregate(replicas,references,protocol,authentication['header'])
    paths=[]
    for i in range(16):
        paths.append(('replicas',i,'run'))
        for segment in ('0:100','50:100'):
            for metric in protocol['acf_metrics']:paths.append(('replicas',i,'acf',segment,metric))
    _,original=analysis_metadata(paths)
    comparison={}
    for i,run in enumerate(manifest['runs']):
        require(original[('replicas',i,'run')]==run,'original replica identity changed')
        comparison[run['id']]={segment:{metric:original.get(('replicas',i,'acf',segment,metric))
            for metric in protocol['acf_metrics']} for segment in ('0:100','50:100')}
    result['original_D16B_ACF_records_unchanged']=comparison
    result['accepted_reference_evidence']=references
    result['provenance']={'schema':'e1-d16c-secondary-provenance-v1','sources':spec.tools(),
        'original_authentication':file_record(authentication_path),'original_analysis':lock['analysis_identity'],
        'original_completion_sha256':lock['completion_sha256'],'protocol':file_record(spec.CONFIG/'protocol.json'),
        'audit_session':file_record(output.parent.parent/'session.json'),
        'audit_approval':file_record(output.parent.parent/'reviewed-audit-approval.json'),
        'audit_environment':file_record(output.parent.parent/'environment.json'),
        'resources':file_record(spec.CONFIG/'resources.json')}
    require(authenticate()==authentication,'original evidence changed during secondary audit')
    result['figures']=figures(output.parent,result)
    with Path(output).open('xb') as stream:
        with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as zipped:zipped.write(encoded(result))
    return {'schema':'e1-d16c-audit-result-v1','status':result['status'],'scientific_acceptance':None,
        'payload':file_record(output),'provenance':result['provenance'],
        'primary_followup':result['primary_followup'],'post_selection_exploratory':True}



def figures(directory,result):
    """Standalone SVG diagnostic displays; lines join observed points only."""
    colors=('#2463a1','#d25132','#278354','#8d55a0')
    def save(name,panels):
        width=1200;columns=4;rows=(len(panels)+columns-1)//columns;height=rows*220+35
        parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
               '<rect width="100%" height="100%" fill="white"/>',
               '<text x="12" y="20" font-size="13">D1.6C secondary exploratory diagnostics; lines join observed points</text>']
        for i,(title,curves) in enumerate(panels):
            ox=10+(i%columns)*300;oy=40+(i//columns)*220
            data=[(x,y) for _,xs,ys in curves for x,y in zip(xs,ys) if math.isfinite(y)]
            if not data:continue
            xmin,xmax=min(x for x,y in data),max(x for x,y in data)
            ymin,ymax=min(y for x,y in data),max(y for x,y in data)
            if ymin==ymax:ymin-=1;ymax+=1
            if xmin==xmax:xmax=xmin+1
            parts.append(f'<text x="{ox}" y="{oy}" font-size="11">{html.escape(title)}</text>')
            parts.append(f'<path d="M{ox+42},{oy+12}v132h240" fill="none" stroke="#999"/>')
            for j,(label,xs,ys) in enumerate(curves):
                points=' '.join(f'{ox+42+240*(x-xmin)/(xmax-xmin):.3f},{oy+144-132*(y-ymin)/(ymax-ymin):.3f}' for x,y in zip(xs,ys))
                color=colors[j%4]
                parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="1"/>')
                parts.append(f'<text x="{ox+42}" y="{oy+160+12*j}" fill="{color}" font-size="9">{html.escape(label)}</text>')
            parts.append(f'<text x="{ox}" y="{oy+27}" font-size="9">{ymax:.3g}</text><text x="{ox}" y="{oy+144}" font-size="9">{ymin:.3g}</text>')
            parts.append(f'<text x="{ox+42}" y="{oy+156}" font-size="9">{xmin:g}</text><text x="{ox+257}" y="{oy+156}" font-size="9">{xmax:g} tau</text>')
        parts.append('</svg>')
        path=directory/name
        with path.open('x') as stream:stream.write(''.join(parts))
        return file_record(path)
    panels=[]
    for cell,key in ((1,'spatial_var_re2'),(1,'re2'),(4,'connector_e2'),(3,'A_joint'),(4,'A_joint')):
        curves=[]
        for replica in result['replicas']:
            if replica['run']['cell']!=cell:continue
            series=replica['scalar_series'] if key in replica['scalar_series']['0'] else {time:v['metrics'] for time,v in replica['full_series'].items()}
            times=sorted(series,key=Fraction)
            curves.append(('replica '+str(replica['run']['replica']),[float(Fraction(time)) for time in times],[series[time][key] for time in times]))
        panels.append((f'cell {cell}: {key}',curves))
    records={'audit-traces.svg':save('audit-traces.svg',panels)}
    for key in load(spec.CONFIG/'protocol.json')['acf_metrics']:
        panels=[]
        for replica in result['replicas']:
            for segment,metrics in replica['secondary_acf'].items():
                if key not in metrics:continue
                curves=[]
                for center,entry in metrics[key]['estimators'].items():
                    if 'lag_times' not in entry:continue
                    curves.append((center,entry['lag_times'],entry['overlap_corrected_acf']))
                    curves.append((center+' fixed-denominator',entry['lag_times'],entry['fixed_denominator_crosscheck']))
                original=result['original_D16B_ACF_records_unchanged'].get(replica['run']['id'],{}).get(segment,{}).get(key)
                if original and original.get('lag_times') and original.get('acf'):
                    curves.append(('original D16B demeaned',original['lag_times'],original['acf']))
                panels.append((replica['run']['id']+' '+segment,curves))
        name='audit-acf-'+key+'.svg';records[name]=save(name,panels)
    return records
