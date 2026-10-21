#!/usr/bin/env python3
"""Exploratory D1 replica statistics. No equivalence/pass decisions or fitted targets."""
import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
from numpy.polynomial.legendre import leggauss
import e1_d1_pilot as spec
import e1_d1_pilot_auth as auth
from e1_d1_pilot import require
from e1_observer_check import Rows
from semiflexible_reference import radial_moments, langevin


def chi3_cdf(x):
    require(math.isfinite(x) and x >= 0, 'invalid chi-square argument')
    return math.erf(math.sqrt(x/2))-math.sqrt(2*x/math.pi)*math.exp(-x/2)


@lru_cache(maxsize=9)
def chi3_quantile(p):
    lo, hi = 0., 100.
    for _ in range(90):
        mid = (lo+hi)/2
        if chi3_cdf(mid) < p: lo = mid
        else: hi = mid
    return (lo+hi)/2


PROBABILITIES = (.01, .05, .10, .25, .50, .75, .90, .95, .99)


def radial_overlap(order):
    nodes, weights = leggauss(order); sigma = 1/math.sqrt(30)
    lo, hi = -math.sqrt(30), 12.
    y = (lo+hi)/2+(hi-lo)*nodes/2; length = 1+sigma*y
    w = weights*length**2*np.exp(-y*y/2)
    return float(np.dot(w, [math.erfc(l/(2*math.sqrt(2)*math.sqrt(5/3))) for l in length])/w.sum())


@lru_cache(maxsize=16)
def reference(n, chains, z, kappa, rate):
    require(n>0 and chains>1 and 0<z<chains*(n+1), 'nondegenerate canonical reference required')
    mu1, mu2 = radial_moments(1,30,order=128)
    refined = radial_moments(1,30,order=256)
    require(max(abs(a-b) for a,b in zip((mu1,mu2),refined)) < 1e-11, 'radial quadrature refinement unresolved')
    h = langevin(kappa)
    b = [0.] + [d*mu2+2*mu1**2*sum((d-s)*h**s for s in range(1,d)) for d in range(1,n+1)]
    m=n+1; total=chains*m; rho=z/total
    denominator=math.comb(total,z)
    numerators=[math.comb(m,k)*math.comb(total-m,z-k) if 0<=z-k<=total-m else 0 for k in range(m+1)]
    require(sum(numerators)==denominator, 'hypergeometric normalization identity failed')
    population=[value/denominator for value in numerators]
    var=m*rho*(1-rho)*(total-m)/(total-1)
    targets={'mean_r':mu1,'mean_r2':mu2,'re2':b[n],
             'rg2':sum((m-d)*b[d] for d in range(1,n+1))/m**2,
             'connector_e2':5.,'population_mean':z/chains,'population_variance':var,
             'A_joint':0.,'B_joint':0.}
    for s in (1,2,3,4,8,16):
        if s<n: targets['tangent'+str(s)]=h**s
    for d in 'xyz':
        targets['connector_mean_'+d]=0.;targets['connector_second_'+d]=5/3
        targets['connector_variance_unbiased_'+d]=5/3
    for pair in ('xy','xz','yz'): targets['connector_cross_'+pair]=0.
    for i in range(m): targets[f'occupancy[{i}]']=rho
    for k,p in enumerate(population):
        targets[f'population_pmf[{k}]']=p;targets[f'population_cdf[{k}]']=sum(population[:k+1])
    for p in PROBABILITIES:
        targets[f'connector_e2_cdf[{p}]']=p
        for d in 'xyz': targets[f'connector_{d}_cdf[{p}]']=p
    overlap=radial_overlap(128)
    require(abs(overlap-radial_overlap(256)) < 1e-11, 'rate quadrature refinement unresolved')
    vacancy=(total-z)/(total-1); outward=z*rate/m
    renewal=outward*(2*chains-1)/(2*chains)*vacancy
    hop=z*rate*n/m*vacancy*overlap
    rates={'attempts':z*rate,'accepted':hop,'boundary':outward,
           'occupied':z*rate*n/m*(1-vacancy),'metropolis':z*rate*n/m*vacancy*(1-overlap),
           'renewal_proposed':outward,'renewal_accepted':renewal,'renewal_occupied':outward-renewal,
           'renewal_same_chain':outward/(2*chains)*vacancy,
           'renewal_cross_chain':outward*(chains-1)/chains*vacancy}
    targets.update({'rate_'+key:value for key,value in rates.items()})
    return {'targets':targets,'mu1':mu1,'mu2':mu2,'h':h,'sigma_Z':math.sqrt(var),
            'population_pmf':population,'radial_refinement_max_abs':max(abs(a-b) for a,b in zip((mu1,mu2),refined)),
            'reference_note':'finite-chain analytical equilibrium; rates are ideal continuous-time, not finite-dt acceptance gates'}


def frame_statistics(run, backbone, population, connectors, site_ids, long_tangents):
    chains,n,z=run['M'],run['N'],run['Z']; ref=reference(n,chains,z,run['kappa'],run['nu_hop'])
    result={key:float(np.mean([float(row[key]) for row in backbone])) for key in
            ('re2','rg2','mean_r','mean_r2')}
    for s in (1,2,3,4,8,16):
        if s<n:
            source=backbone if s<=4 else long_tangents
            result['tangent'+str(s)]=float(np.mean([float(row['tangent'+str(s)]) for row in source]))
    e=np.asarray([[float(row[k]) for k in ('ex','ey','ez')] for row in connectors])
    e2=np.asarray([float(row['e2']) for row in connectors])
    require(e.shape==(z,3), 'connector count mismatch')
    result['connector_e2']=float(e2.mean())
    for d,name in enumerate('xyz'):
        result['connector_mean_'+name]=float(e[:,d].mean())
        result['connector_second_'+name]=float(np.mean(e[:,d]**2))
        result['connector_variance_unbiased_'+name]=float(e[:,d].var(ddof=1)) if z>1 else None
    for i,j in ((0,1),(0,2),(1,2)):
        result['connector_cross_'+'xyz'[i]+'xyz'[j]]=float(np.mean(e[:,i]*e[:,j]))
    for p in PROBABILITIES:
        result[f'connector_e2_cdf[{p}]']=float(np.mean(e2<=5*chi3_quantile(p)/3))
        cut=math.sqrt(5/3)*NormalDist().inv_cdf(p)
        for d,name in enumerate('xyz'):result[f'connector_{name}_cdf[{p}]']=float(np.mean(e[:,d]<=cut))
    populations=np.array([int(row['z']) for row in population]); squared=np.array([float(row['e2_sum']) for row in population])
    require(populations.sum()==z, 'population conservation failure')
    result['population_mean']=float(populations.mean())
    result['population_variance']=float(np.mean((populations-z/chains)**2))
    for k in range(n+2):
        result[f'population_pmf[{k}]']=float(np.mean(populations==k))
        result[f'population_cdf[{k}]']=float(np.mean(populations<=k))
    occupied=np.asarray(site_ids).reshape(chains,n+1)>=0
    for i,p in enumerate(occupied.mean(axis=0)):result[f'occupancy[{i}]']=float(p)
    f=np.array([float(row['re2'])/ref['targets']['re2']-1 for row in backbone])
    result['A_joint']=float(np.sum(f*(populations-z/chains))/(chains*ref['sigma_Z']))
    result['B_joint']=float(np.sum(f*(squared-5*populations))/(z*5))
    return result


def reduce_replica(output, run, schedule, snapshots):
    readers={name:Rows(output/('equilibrium_'+name+'.csv')) for name in
             ('backbone','tangents','chains','connectors','sites','events')}
    readers['samples']=Rows(output/'samples.csv')
    shared=set(spec.schedule(run['dt'])['shared_steps'])
    results={}; diagnostic=[]; seen=np.zeros(run['M']*(run['N']+1),dtype=bool)
    accumulated={k:0 for k in auth.COUNTERS}; totals=accumulated.copy(); previous_shared=0
    try:
        for step in schedule:
            dt=float(run['dt']); chains=run['M']; z=run['Z']
            readers['samples'].seek(step)
            bb=readers['samples' if step%run['sample']==0 else 'backbone'].take(chains,step,dt)
            tangent=readers['tangents'].take(chains if run['N']>8 else 0,step,dt)
            pop=readers['chains'].take(chains,step,dt);con=readers['connectors'].take(z,step,dt)
            sites=readers['sites'].take(len(seen),step,dt); events=readers['events'].take(1,step,dt)[0]
            ids=[int(row['spring']) for row in sites];seen|=np.array(ids)>=0
            values=frame_statistics(run,bb,pop,con,ids,tangent)
            counts={key:int(events[key]) for key in auth.COUNTERS}
            for key in counts:accumulated[key]+=counts[key];totals[key]+=counts[key]
            if step in shared:
                duration=(step-previous_shared)*dt
                if duration>0:
                    values.update({'rate_'+key:accumulated[key]/duration for key in counts if key!='batches'})
                tick=spec.exact_step(step*spec.Fraction(run['dt']), '0.0005')
                results[tick]=values;previous_shared=step;accumulated={k:0 for k in counts}
            else:
                diagnostic.append({'step':step,'time':step*dt,'metrics':values,'interval_counts':counts,
                                   'note':'timestep-specific first update; excluded from shared-time contrasts'})
        return {'run':run,'shared':results,'diagnostic_only':diagnostic,'event_totals':totals,
                'coverage':{'observed_site_fraction':float(seen.mean()),
                            'observed_chain_fraction':float(seen.reshape(chains,run['N']+1).any(axis=1).mean()),
                            'site_ever_occupied':seen.astype(int).tolist(),
                            'per_id_renewal_coverage':None,
                            'note':'coverage at scheduled frames only; counts do not determine per-ID renewal or independent samples'}}
    finally:
        for reader in readers.values():reader.file.close()


def student_t3_critical():
    # Invert F_3(t)=1/2+[atan(t/sqrt(3))+sqrt(3)t/(t²+3)]/pi.
    lo,hi=0.,20.
    for _ in range(80):
        mid=(lo+hi)/2
        cdf=.5+(math.atan(mid/math.sqrt(3))+math.sqrt(3)*mid/(mid*mid+3))/math.pi
        if cdf<.975:lo=mid
        else:hi=mid
    return (lo+hi)/2


T3=student_t3_critical()


def summary(values, target=None):
    values=np.asarray(values,dtype=float)
    require(values.shape==(4,) and np.isfinite(values).all(), 'exactly four finite replica estimators required')
    mean=float(values.mean());sd=float(values.std(ddof=1));se=sd/2;half=T3*se
    result={'replicas':4,'mean':mean,'replica_sd':sd,'standard_error':se,
            'exploratory_pointwise_95_interval':[mean-half,mean+half],
            'zero_observed_replica_variance':sd==0}
    if target is not None:result.update(reference=target,difference_from_reference=mean-target)
    return result


def independent_contrast(fine, coarse):
    a,b=summary(fine),summary(coarse);difference=b['mean']-a['mean']
    se=math.sqrt(a['standard_error']**2+b['standard_error']**2)
    return {'coarse_minus_fine':difference,'standard_error':se,
            'exploratory_pointwise_95_interval':[difference-T3*se,difference+T3*se],
            'method':'independent replica variances; t3 critical conservative relative to normal/Welch df>=3, not guaranteed small-sample coverage'}


def acf_diagnostic(values):
    x=np.asarray(values,dtype=float);x=x-x.mean();den=float(x@x)
    if len(x)<8 or den==0:return {'status':'insufficient/zero-variance series','samples':len(x),'tau_int':None}
    return {'status':'descriptive only; stationarity and IAT unsupported over T=.25',
            'samples':len(x),'spacing':.005,'lags':list(range(1,min(10,len(x)//4)+1)),
            'acf':[float(x[:-lag]@x[lag:]/den) for lag in range(1,min(10,len(x)//4)+1)],
            'tau_int':None,'note':'temporal frames are correlated; no extra replica count or reliable mixing-time inference'}


def aggregate(replicas):
    require(len(replicas)==32 and len({r['run']['id'] for r in replicas})==32, 'complete 32-replica pilot required')
    cells={}; contrasts=[]; coverage=[]
    for cell in range(1,9):
        group=sorted((r for r in replicas if r['run']['cell']==cell),key=lambda r:r['run']['replica'])
        require([r['run']['replica'] for r in group]==[1,2,3,4], 'missing/duplicate replica')
        run=group[0]['run'];target=reference(run['N'],run['M'],run['Z'],run['kappa'],run['nu_hop'])['targets']
        require(all(set(r['shared'])==set(spec.shared_ticks()) for r in group), 'missing shared times')
        by_time={}
        for tick in spec.shared_ticks():
            keys=set(group[0]['shared'][tick]);require(all(set(r['shared'][tick])==keys for r in group), 'inconsistent metrics')
            metrics={key:summary([r['shared'][tick][key] for r in group],target[key]) for key in sorted(keys)}
            initial=set(group[0]['shared'][0])
            changes={key:summary([r['shared'][tick][key]-r['shared'][0][key] for r in group]) for key in sorted(keys&initial)}
            by_time[str(tick)]={'time':tick*.0005,'metrics':metrics,'paired_change_from_initial':changes}
        late=[tick for tick in spec.shared_ticks() if tick>=20]
        acf={r['run']['id']:{key:acf_diagnostic([r['shared'][t][key] for t in late]) for key in
                            ('re2','rg2','connector_e2','A_joint','B_joint')} for r in group}
        temporal={key:{'minimum_replica_mean':min(by_time[str(t)]['metrics'][key]['mean'] for t in spec.shared_ticks()),
                       'maximum_replica_mean':max(by_time[str(t)]['metrics'][key]['mean'] for t in spec.shared_ticks())}
                  for key in group[0]['shared'][0]}
        cells[str(cell)]={'parameters':run,'shared_times':by_time,'variation_across_times':temporal,
                         'late_acf_by_replica':acf,'reference':reference(run['N'],run['M'],run['Z'],run['kappa'],run['nu_hop']),
                         'diagnostic_first_steps':[{'run_id':r['run']['id'],'frames':r['diagnostic_only']} for r in group]}
        coverage.extend({'run_id':r['run']['id'],'coverage':r['coverage'],'event_counts':r['event_totals']} for r in group)
    for fine_cell in (1,3,5,7):
        fine=sorted((r for r in replicas if r['run']['cell']==fine_cell),key=lambda r:r['run']['replica'])
        coarse=sorted((r for r in replicas if r['run']['cell']==fine_cell+1),key=lambda r:r['run']['replica'])
        times={}
        for tick in spec.shared_ticks():
            keys=set(fine[0]['shared'][tick])&set(coarse[0]['shared'][tick])
            times[str(tick)]={'time':tick*.0005,'metrics':{key:independent_contrast(
                [r['shared'][tick][key] for r in fine],[r['shared'][tick][key] for r in coarse]) for key in sorted(keys)}}
        contrasts.append({'fine_cell':fine_cell,'coarse_cell':fine_cell+1,'shared_times':times})
    return {'version':1,'classification':'exploratory only; no scientific equivalence/pass decision',
            'independent_unit':'one entire separately seeded 64-chain replica',
            'uncertainty':'pointwise nominal t3 intervals across four replicas; no simultaneous coverage; distributional assumptions may fail',
            'pairing':'across times within replica only; all cross-dt comparisons independent',
            'cells':cells,'timestep_contrasts':contrasts,'coverage_and_events':coverage,
            'limitations':['four replicas cannot establish precise tails, reliable autocorrelation times or equivalence',
                          'fixed selected snapshot coverage only; per-ID renewal history is unavailable',
                          'scientific D0 margins unchanged; no fitted targets or size CDF reference ensemble']}


def analyze(args):
    manifest,runs=auth.authenticate_campaign(args.campaign,args.manifest,args.manifest_sha256,args.approval_sha256,args.completion_sha256)
    reduced=[reduce_replica(r['root'],r['run'],manifest['schedules'][r['run']['schedule']]['steps'],
                            manifest['schedules'][r['run']['snapshots']]['steps']) for r in runs]
    result=aggregate(reduced)
    result['authentication']={'manifest_sha256':args.manifest_sha256,'approval_sha256':args.approval_sha256,
        'campaign_complete_sha256':args.completion_sha256,
        'analysis_sources':spec.tool_hashes(),'python':__import__('sys').version,'numpy':np.__version__}
    result['costs']={'actual_run_wall_seconds':sum(r['receipt']['wall_seconds'] for r in runs),
        'actual_raw_bytes':sum(sum(p['bytes'] for p in r['data']['files'].values()) for r in runs),
        'max_observed_host_rss_bytes':max(r['receipt']['max_rss_bytes'] for r in runs),
        'planning_estimates':spec.estimates(manifest)}
    # Authenticate again before publication; caches/mtime shortcuts are not used.
    auth.authenticate_campaign(args.campaign,args.manifest,args.manifest_sha256,args.approval_sha256,args.completion_sha256)
    require(not args.output.resolve().is_relative_to(args.campaign.resolve()), 'analysis must not modify raw evidence root')
    spec.output_path(args.output)
    with args.output.open('xb') as stream:stream.write(spec.encoded(result))
    return {'output':str(args.output),'sha256':spec.digest(args.output),'classification':result['classification']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=spec.CONFIG/'manifest.json')
    parser.add_argument('--manifest-sha256',required=True);parser.add_argument('--campaign',type=Path,required=True)
    parser.add_argument('--completion-sha256',required=True)
    parser.add_argument('--approval-sha256',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(analyze(args),indent=2))
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as error:parser.exit(1,f'analysis refused: {error}\n')
