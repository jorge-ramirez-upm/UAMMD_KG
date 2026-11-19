#!/usr/bin/env python3
"""Prepared CPU-only Stage-A precision analysis; never launches simulations or Stage B."""
import os
for _pool in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS',
              'BLIS_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_pool] = '2'
os.environ['OMP_THREAD_LIMIT'] = '2'
import argparse
import csv
import math
from pathlib import Path
import sys
import numpy as np
from scipy.stats import t, chi2, norm

import e1_d17_spec as spec
import e1_d17_host as host
import e1_d2a5_n64_statics as reuse
from e1_d16b_analysis import acf_diagnostic
from e1_d1_pilot import require, load, utc
from e1_d2a3_analyze import write_csv, write_json


def summary(values, alpha=.05, bounds=None):
    x = np.asarray(values, dtype=float)
    require(x.shape == (4,) and np.isfinite(x).all(), 'exactly four independent finite run estimates')
    mean, sd = float(x.mean()), float(x.std(ddof=1))
    se = sd/2
    half = float(t.ppf(1-alpha/2,3))*se
    interval = [mean-half,mean+half] if sd else None
    if bounds is not None:
        lo, hi = bounds
        require(np.all((lo <= x) & (x <= hi)), 'bounded estimator outside its range')
        half = (hi-lo)*math.sqrt(math.log(2/alpha)/8)
        interval = [max(lo,mean-half), min(hi,mean+half)]
    return dict(values=x.tolist(), mean=mean, sd=sd, se=se, interval=interval, alpha=alpha,
        zero_observed_dispersion=sd == 0, loo=[float(np.delete(x,i).mean()) for i in range(4)])


def contrast(left, right, alpha=.05):
    a, b = summary(left), summary(right)
    va, vb = a['se']**2, b['se']**2
    se = math.sqrt(va+vb)
    df = (va+vb)**2/(va*va/3+vb*vb/3) if se else None
    delta = b['mean']-a['mean']
    half = float(t.ppf(1-alpha/2,df))*se if df else None
    return dict(left_values=a['values'], right_values=b['values'], difference=delta, se=se, df=df,
        interval=[delta-half,delta+half] if half is not None else None,
        loo=[float(np.delete(right,j).mean()-np.delete(left,i).mean()) for i in range(4) for j in range(4)])


def references():
    low, high = [reuse.reference_targets(10, order, 32) for order in (128,256)]
    require(abs(low['mean_r']-high['mean_r']) < 1e-11 and abs(low['mean_r2']-high['mean_r2']) < 1e-11,
            'radial quadrature sensitivity gate')
    target = dict(high, connector_e2=5., connector_e4=125/3)
    target.update(population_mean=8., population_variance=reuse.canonical_population()['variance'])
    for axis in 'xyz':
        target['connector_mean_'+axis] = 0.
        target['connector_second_'+axis] = 5/3
        target['connector_cov_'+axis+axis] = 5/3
    for pair in ('xy','xz','yz'):
        target['connector_cross_'+pair] = 0.
        target['connector_cov_'+pair] = 0.
    law = reuse.canonical_population(chains=256,n=32,z=2048)
    target['population_multiple'] = 1-sum(law['pmf'][:2])
    for k in range(34):
        target[f'population_pmf_{k}'] = law['pmf'][k]
        target[f'population_cdf_{k}'] = sum(law['pmf'][:k+1])
    for k in range(33):
        target[f'occupancy_{k}'] = law['site_probability']
    return dict(targets=target, numerical_sensitivity={k:abs(high[k]-low[k]) for k in high},
        canonical_law=law, qualification='Analytical N32 nonlinear means; quadrature refinement is engineering sensitivity, not a certified interval. No sampled-reference uncertainty imported.')


def read_run(root, run, manifest):
    directory = root/'runs'/run['id']/'output'
    scalar_header = 'step,time,chain,mean_r,mean_r2,re2,rg2,cm_msd,monomer_msd,min_length,tangent1,tangent2,tangent3,tangent4'.split(',')
    scalar = [(tm,reuse.backbone(rows,32)) for tm,rows in spec.frames(directory/'samples.csv',scalar_header,
        256,range(0,run['steps']+1,run['sample']),run['dt'])]
    headers = dict(tangents='step,time,chain,tangent8,tangent16',
        chains='step,time,chain,z,ex_sum,ey_sum,ez_sum,e2_sum',
        connectors='step,time,spring,chain,bead,ex,ey,ez,e2',sites='step,time,chain,bead,spring')
    full_steps = spec.schedules(manifest)[run['schedule']]
    counts = dict(tangents=256, chains=256, connectors=run['Z'],sites=8448)
    readers = [spec.frames(directory/f'equilibrium_{key}.csv',columns.split(','),counts[key],full_steps,run['dt'])
               for key,columns in headers.items()]
    full = []
    import itertools
    for joint in itertools.zip_longest(*readers):
        require(all(v is not None for v in joint) and len({v[0] for v in joint}) == 1, 'full grid mismatch')
        tangent,pop,con,sites = [v[1] for v in joint]
        if run['Z']:
            values = reuse.context(con,pop,sites,tangent,32)
            for i,a in enumerate('xyz'):
                for j,b in enumerate('xyz'[i:],i):
                    moment = values['connector_second_'+a] if i == j else values['connector_cross_'+a+b]
                    values['connector_cov_'+a+b] = run['Z']/(run['Z']-1)*(moment-values['connector_mean_'+a]*values['connector_mean_'+b])
        else:
            values = {k:float(np.mean([float(r[k]) for r in tangent])) for k in ('tangent8','tangent16')}
        full.append((joint[0][0],values))
    bins = np.zeros(33,dtype=np.int64)
    with (directory/'bond_statistics.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            bins += [int(row[f'bin{k}']) for k in range(33)]
    with (directory/'equilibrium_events.csv').open(newline='') as stream:
        events = list(csv.DictReader(stream))  # Only 51 interval records, not a raw history.
    receipt = load(root/'runs'/run['id']/'receipt.json')
    return dict(scalar=scalar,full=full,events=events,bond_histogram=(bins/bins.sum()).tolist(),
        metadata=load(directory/'metadata.json'),process=load(root/'runs'/run['id']/'process.json'),
        output_bytes=sum(v['bytes'] for v in receipt['validation']['files'].values()),stage_wall_seconds=receipt['stage_wall_seconds'])


def window(series, quantity, bounds):
    chosen = [(tm,row[quantity]) for tm,row in series if bounds[0] <= tm <= bounds[1]]
    require(bool(chosen),'unsupported window')
    return dict(value=float(np.mean([v for _,v in chosen])), frames=len(chosen),
                first=chosen[0][0],last=chosen[-1][0])


def tables(out, manifest, runs, data, refs):
    traces, windows, acfs, costs, histograms, events = [], [], {}, [], [], []
    for run in runs:
        identity = run['id']
        record = data[identity]
        acfs[identity] = {}
        for grid,spacing in (('scalar',.5),('full',2.)):
            series = record[grid]
            for q in series[0][1]:
                for tm,row in series:
                    traces.append(dict(run=identity,cell=run['cell'],grid=grid,time=tm,quantity=q,value=row[q],
                                       target=refs['targets'].get(q)))
                for name,bounds in manifest['windows'].items():
                    windows.append(dict(run=identity,cell=run['cell'],grid=grid,quantity=q,window=name,
                                        **window(series,q,bounds)))
                if q in manifest['primary'] or q in ('connector_e4','population_variance','tangent8','tangent16'):
                    acfs[identity][q] = {}
                    for segment,start in (('post_initial',spacing),('late_half',50.)):
                        selected = [(tm,row[q]) for tm,row in series if tm >= start]
                        result = acf_diagnostic([str(tm) for tm,_ in selected], [v for _,v in selected],
                                                str(spacing),refs['targets'].get(q))
                        tau = result['tau_int']
                        result['conditional_effective_frames'] = min(len(selected),len(selected)*spacing/(2*tau)) if tau else None
                        result['stationarity_status'] = 'REQUIRES_INDEPENDENT_WINDOW_AND_TAIL_REVIEW'
                        acfs[identity][q][segment] = result
        meta = record['metadata']
        process = record['process']
        costs.append(dict(run=identity,cell=run['cell'],dt=run['dt'],steps=run['steps'],
            integration_seconds=meta['integration_seconds'],production_wall_seconds=meta['production_wall_seconds'],
            initialization_seconds=meta['initialization_seconds'],final_output_seconds=meta['final_output_seconds'],
            process_wall_seconds=process.get('wall_seconds'),peak_host_rss_bytes=process.get('max_rss_bytes'),
            output_bytes=record['output_bytes'],stage_wall_seconds=record['stage_wall_seconds'],
            integration_timer_scope=meta['integration_timer_scope']))
        for k,value in enumerate(record['bond_histogram']):
            histograms.append(dict(run=identity,cell=run['cell'],bin=k,probability=value,start=50,end=100,frames=101))
        for event in record['events']:
            duration = float(event['interval_time'])
            for key in host.historical.COUNTERS:
                events.append(dict(run=identity,cell=run['cell'],start=int(event['previous_step'])*float(run['dt']),
                    end=float(event['time']),quantity=key,count=int(event[key]),
                    rate=int(event[key])/duration if duration else None))
    comparisons, drifts, precision = [], [], []
    for cell in manifest['cells']:
        ids = [r['id'] for r in runs if r['cell'] == cell['id']]
        for prototype in [w for w in windows if w['run'] == ids[0]]:
            q,name,grid = prototype['quantity'],prototype['window'],prototype['grid']
            values = [next(w['value'] for w in windows if w['run'] == identity and w['quantity'] == q and
                           w['window'] == name and w['grid'] == grid) for identity in ids]
            primary = q in manifest['primary'] and name == 'late'
            alpha = .05/27 if primary else .05
            bounds = reuse.bounded(q)
            estimate = summary(values,alpha,bounds)
            target = refs['targets'].get(q)
            err = refs['numerical_sensitivity'].get(q,0.)
            interval = estimate['interval']
            difference_interval = [interval[0]-target-err,interval[1]-target+err] if interval is not None and target is not None else None
            decision = ('NO_REFERENCE' if target is None else 'CONSERVATION_ONLY' if q == 'population_mean' else
                'INSUFFICIENT_PRECISION_ZERO_DISPERSION' if interval is None else
                'TARGET_DEPARTURE_IN_FINITE_WINDOW' if difference_interval[0] > 0 or difference_interval[1] < 0 else
                'TARGET_COMPATIBLE_NOT_EQUIVALENCE')
            comparisons.append(dict(cell=cell['id'],dt=cell['dt'],Z=cell['Z'],quantity=q,grid=grid,window=name,
                primary_late=primary,target=target,numerical_sensitivity=err,
                difference_from_target=estimate['mean']-target if target is not None else None,
                difference_interval=difference_interval,decision=decision,**estimate))
            if primary:
                planning = manifest['planning_sensitivity'][q]
                sensitivity = planning.get('absolute',planning.get('relative',0)*abs(target))
                sd_upper = estimate['sd']*math.sqrt(3/float(chi2.ppf(.025,3))) if estimate['sd'] else None
                require_count = max(4,math.ceil((float(norm.ppf(.975))*sd_upper/sensitivity)**2)) if sd_upper else None
                supported = [not acfs[i][q]['late_half']['unresolved_tail'] for i in ids]
                precision.append(dict(cell=cell['id'],quantity=q,planning_sensitivity=sensitivity,
                    simultaneous_halfwidth=(interval[1]-interval[0])/2+err if interval else None,
                    nominal_halfwidth=float(t.ppf(.975,3))*estimate['se']+err if estimate['sd'] else None,
                    gaussian_sd_upper95=sd_upper,approx_R_for_95_mean_halfwidth=require_count,
                    late_half_IAT_supported=supported,
                    status='PILOT_FOR_INDEPENDENT_REVIEW_NO_STAGE_B_AUTHORIZATION'))
        for grid in ('scalar','full'):
            for q in data[ids[0]][grid][0][1]:
                for early,late in (('initial','late'),('early','middle'),('middle','late'),('early','late')):
                    values = [window(data[i][grid],q,manifest['windows'][late])['value']-
                              window(data[i][grid],q,manifest['windows'][early])['value'] for i in ids]
                    bounds = (-1,1) if reuse.bounded(q) else None
                    drifts.append(dict(cell=cell['id'],quantity=q,grid=grid,contrast=f'{late}-{early}',
                                       **summary(values,bounds=bounds)))
    dt_contrasts, bare_contrasts = [], []
    for q in manifest['primary']:
        for z in (0,2048):
            if q == 'connector_e2' and not z:
                continue
            selected = [r for r in comparisons if r['Z'] == z and r['quantity'] == q and r['window'] == 'late']
            selected.sort(key=lambda r:float(r['dt']))
            import itertools
            for fine,coarse in itertools.combinations(selected,2):
                estimate = contrast(fine['values'],coarse['values'])
                delta_h = float(coarse['dt'])-float(fine['dt'])
                dt_contrasts.append(dict(quantity=q,Z=z,fine_dt=fine['dt'],coarse_dt=coarse['dt'],
                    finite_difference_per_dt=estimate['difference']/delta_h,
                    interpretation='EXPLORATORY_FINITE_WINDOW_CONTRAST_NOT_STATIONARY_CONVERGENCE_ORDER',**estimate))
        if q != 'connector_e2':
            for dt in ('0.00005','0.0001','0.00025'):
                selected = {r['Z']:r for r in comparisons if r['dt'] == dt and r['quantity'] == q and r['window'] == 'late'}
                bare_contrasts.append(dict(quantity=q,dt=dt,**contrast(selected[0]['values'],selected[2048]['values'])))
    require(sum(r['primary_late'] for r in comparisons) == manifest['primary_late_target_family'], 'primary-family closure')
    for name,rows in (('traces',traces),('run_windows',windows),('target_comparisons',comparisons),('drift',drifts),
                      ('precision',precision),('dt_contrasts',dt_contrasts),('constrained_minus_bare',bare_contrasts),
                      ('costs',costs),('bond_histograms',histograms),('event_intervals',events)):
        write_csv(out/(name+'.csv'),rows)
    write_json(out/'autocorrelation.json',acfs)
    return comparisons,precision


def figures(out, comparisons, data, manifest, refs):
    os.environ['MPLCONFIGDIR'] = str(out/'matplotlib-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for q in manifest['primary']:
        fig,axes = plt.subplots(1,2,figsize=(10,4))
        for cell in manifest['cells']:
            if q == 'connector_e2' and not cell['Z']:
                continue
            row = next(r for r in comparisons if r['cell'] == cell['id'] and r['quantity'] == q and r['window'] == 'late')
            color = 'C1' if cell['Z'] else 'C0'
            interval = row['interval']
            axes[0].errorbar(float(cell['dt']),row['mean']-row['target'],
                yerr=None if interval is None else [[row['mean']-interval[0]],[interval[1]-row['mean']]],
                color=color,fmt='o',label=cell['id'])
            grid = 'full' if q == 'connector_e2' else 'scalar'
            for run in spec.runs(manifest):
                if run['cell'] != cell['id']:
                    continue
                series = data[run['id']][grid]
                axes[1].plot([tm for tm,_ in series[1:]],[v[q]-refs['targets'][q] for _,v in series[1:]],
                    lw=.6,alpha=.35,color=color)
                axes[1].scatter([0],[series[0][1][q]-refs['targets'][q]],facecolors='none',edgecolors=color,s=12)
        for ax in axes:
            ax.axhline(0,color='black',ls=':',lw=.7)
        axes[0].set(xlabel='dt',ylabel='late mean minus target',title=q+'; nominal family intervals')
        axes[0].legend(fontsize=6)
        axes[1].set(xlabel='physical time (initial frame: open circles)',ylabel='run mean minus target')
        fig.tight_layout()
        fig.savefig(out/(q+'.png'),dpi=200)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--completion-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    root,out = spec.output_path(args.root),spec.output_path(args.output)
    require(not out.is_relative_to(root) and not root.is_relative_to(out), 'analysis and campaign must be disjoint')
    require(os.getpriority(os.PRIO_PROCESS,0) == 19,'launch with nice -n 19 ionice -c 3')
    out.mkdir(parents=True,exist_ok=False)
    try:
        sources = spec.tool_records()
        prepared,before = host.authenticate(root,args.completion_sha256)
        manifest,runs = prepared['candidate'],prepared['runs']
        write_json(out/'authentication.json',dict(completion_sha256=args.completion_sha256,
            input_inventory=before,scope='Recorded source/executable/receipt/schema identity; not independent execution attestation.'))
        refs = references()
        write_json(out/'references.json',refs)
        data = {r['id']:read_run(root,r,manifest) for r in runs}
        # The original process records remain in the authentication inventory.
        comparisons,precision = tables(out,manifest,runs,data,refs)
        figures(out,comparisons,data,manifest,refs)
        review = (
            '# D1.7 Stage-A precision review\n\nEQUILIBRIUM PRESERVATION NOT CONFIRMED. Stage B remains unauthorized.\n\n'
            'Inspect target_comparisons.csv (27 prespecified late tests, nominal Bonferroni family sensitivity), '
            'dt_contrasts.csv and constrained_minus_bare.csv (exploratory unpaired Welch intervals), '
            'drift.csv, autocorrelation.json and precision.csv together. Finite-window target departure '
            'is not a stationary bias. Stability alone is not correctness; unresolved IAT tails stay null.\n\n'
            'R4 normal/CLT assumptions qualify interval coverage. No equivalence margin was adopted. '
            'Zero run dispersion cannot certify precision. R sizing is a Gaussian mean-halfwidth scenario '
            'using a very uncertain R4 SD bound, not power for a trend, future budget or authorization. '
            'More replicas cannot repair an unsupported time horizon.\n\n'
            'Constant, O(dt) and O(dt²) responses remain candidate hypotheses. With three dt levels, '
            'a three-parameter polynomial in cell means is saturated and supplies no independent lack-of-fit '
            'test of higher-order terms. No dt=0 extrapolation or convergence order is reported. '
            'Review stationarity, achieved precision and effect size before selecting Stage-B R/T/models.\n')
        review += '\n| cell | primary | nominal 95% halfwidth | planning sensitivity | late-half IAT supported (R4) |\n'
        review += '|---|---|---|---|---|\n'
        for row in precision:
            review += f"| {row['cell']} | {row['quantity']} | {row['nominal_halfwidth']} | {row['planning_sensitivity']} | {row['late_half_IAT_supported']} |\n"
        review += '\nPlanning sensitivities are proposed resolutions, not equivalence margins.\n'
        (out/'SCIENTIFIC_REVIEW.md').write_text(review)
        require(spec.snapshot(root) == before and spec.tool_records() == sources,'inputs or analysis tools changed')
        write_json(out/'provenance.json',dict(status='STAGE_A_DESCRIPTIVE_COMPLETE_FOR_REVIEW',scientific_acceptance=False,
            stage_b_authorized=False,utc=utc(),sources=sources,python=sys.version,numpy=np.__version__,
            scipy=__import__('scipy').__version__,matplotlib=__import__('matplotlib').__version__,
            input_unchanged=True,argv=sys.argv))
        write_json(out/'result_inventory.json',spec.snapshot(out))
    except BaseException as error:
        write_json(out/'FAILED.json',dict(status='ALL_PRODUCTS_INVALID',error=f'{type(error).__name__}: {error}'))
        raise


if __name__ == '__main__':
    main()
