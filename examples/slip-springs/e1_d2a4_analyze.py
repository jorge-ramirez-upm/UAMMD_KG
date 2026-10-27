#!/usr/bin/env python3
"""Prepared D2A.4 offline analysis; no reduction, test or simulation on import."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from e1_d1_pilot import file_record, require
from e1_d2a3_analyze import (DEFAULT_EVIDENCE, D3_PROFILE, QUANTITIES,
                            analysis_main, git_blob, load, mean_se, snapshot, write_csv)

PROFILE = {
    'name': 'D2A.4', 'preparation_sha': '6371ca7e420bb7e94c07bbdc1b1de182ddb0cadc',
    'summary_sha': '80a9867f4cecd31162073afde1e1c1697e5a790d9c8443b612003bb5b652e17f',
    'launch_sha': '03831b050663a9e709dd1a781668643d945c12590b73da9dd4ac370066d62d04',
    'manifest_sha': '697f0f3be4841221d5b109e0376f4de9da63f239db6f088e5b128da0d4d438fc',
    'config': 'e1_d2a4_config', 'replicas': 3, 'word': 'twelve',
    'evidence': '/home/jramirez/UAMMD_KG-evidence/d2a4/long-t1000-twelve-v1',
    'primary_samples': 18432, 'maximum_samples': 90112, 'T': 1000,
    'features': (1, 15, 128, 512, 1920, 7680, 18432, 90112),
    'endpoint_key': 'value_at_primary_end',
}
HISTORICAL_COMPLETE_SHA = '07a14d5b04630ddfddd0362d8d704390544e4461c65bc3857192e1c1d1d2bca5'
PRIMARY_QUANTITIES = ('cm_msd', 'bead16_msd', 'c1', 'c2')


def alignment_key(row):
    """Match endpoint/filter support, deliberately excluding unequal origin counts."""
    return (row['cell'], *[int(row[k]) for k in ('lag_samples', 'lag_steps',
            'decimation_samples', 'diffusion_phase_samples', 'orientation_block_samples')])


def authenticate_history(root):
    """Validate existing products/inputs; never rerun or overwrite D2A.3 analysis."""
    before = snapshot(root)
    require(before['analysis_complete.json']['sha256'] == HISTORICAL_COMPLETE_SHA,
            'historical analysis completion snapshot changed')
    complete = load(root / 'analysis_complete.json')
    require(complete['status'] == 'exploratory_analysis_completed_for_review' and
            complete['evidence_unchanged_after_analysis'] is True and
            complete['scientific_acceptance'] is False, 'historical completion status')
    require({k: v for k, v in before.items() if k != 'analysis_complete.json'} == complete['products'],
            'historical product hash/file closure')
    for name, record in [('e1_d2a3_analyze.py', complete['code']),
                         ('e1_d2a3_run.py', complete['validation_code'])]:
        blob = git_blob(name, complete['analysis_checkout_head'])
        require(record == {'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()},
                f'historical source identity: {name}')
    authentication = load(root / 'authentication.json')
    require(authentication['status'] == 'authenticated_before_reduction' and
            authentication['manifest_sha256'] == D3_PROFILE['manifest_sha'] and
            authentication['summary_anchor'] == D3_PROFILE['summary_sha'] and
            authentication['launch_anchor'] == D3_PROFILE['launch_sha'], 'historical authentication anchors')
    require(not DEFAULT_EVIDENCE.is_symlink(), 'symlink historical input root')
    raw = DEFAULT_EVIDENCE.resolve(strict=True)
    inputs = snapshot(raw)
    require(inputs == authentication['input_inventory'], 'historical raw input hash closure')
    manifest = load(raw / 'config/manifest.json')
    require(inputs['config/manifest.json']['sha256'] == D3_PROFILE['manifest_sha'], 'historical manifest')
    with (root / 'curves.csv').open(newline='') as f:
        rows = list(csv.DictReader(f))
    require(len(rows) == 352 and len({alignment_key(r) for r in rows}) == 352,
            'historical curve inventory/support uniqueness')
    for row in rows:
        require(row['cell'] in ('A', 'B', 'C', 'D') and row['region'] in ('fine', 'coarse_primary', 'weak_tail'),
                'historical cell/region')
        for q in QUANTITIES:
            require(all(np.isfinite(float(row[q + suffix])) for suffix in ('_r1', '_r2', '_mean', '_se_R2')),
                    'nonfinite historical curve')
    require(snapshot(root) == before, 'historical products changed during authentication')
    return {'analysis_root': str(root), 'evidence_root': str(raw), 'analysis_inventory': before,
            'input_inventory': inputs, 'manifest': manifest, 'rows': rows,
            'scope': 'prior completed products and unchanged authenticated inputs; no regeneration or physical attestation'}


def compare_history(cells, history, out):
    newer = json.loads(git_blob('e1_d2a4_config/manifest.json', PROFILE['preparation_sha']))
    older = history['manifest']
    require(older['executable']['sha256'] == newer['executable']['sha256'], 'comparison physical binary changed')
    require(not ({r['seed'] for r in older['runs']} & {r['seed'] for r in newer['runs']}),
            'comparison requires distinct unpaired seeds')
    excluded = {'--steps', '--seed', '--dynamics-replica', '--output', '--equilibrium-steps',
                '--equilibrium-snapshots', '--dynamics-levels'}
    for cell in 'ABCD':
        options = []
        for manifest in (older, newer):
            args = next(r['argv'] for r in manifest['runs'] if r['cell'] == cell)
            options.append({k: v for k, v in zip(args[1::2], args[2::2]) if k not in excluded})
        require(options[0] == options[1], f'non-duration model/cadence mismatch: {cell}')
    # Existing reduced values are used directly. No historical fit or reduction reruns.
    index = {}
    for cell, data in cells.items():
        mean, se = mean_se(data['values'])
        for i, support in enumerate(data['rows']):
            row = {'cell': cell, **support}
            key = alignment_key(row)
            require(key not in index, 'duplicate D2A.4 comparison support')
            index[key] = (data, i, mean, se)
    result = []
    for old in history['rows']:
        key = alignment_key(old)
        require(key in index, 'historical lag/filter missing from current overlap')
        data, i, mean, se = index[key]
        require(float(old['lag_time']) == data['time'][i] and
                float(old['orientation_block_duration']) == float(data['rows'][i]['orientation_block_duration']),
                'comparison time/filter width mismatch')
        for q in PRIMARY_QUANTITIES:
            j = QUANTITIES.index(q)
            row = {'cell': old['cell'], 'quantity': q, 'lag_samples': key[1], 'lag_time': data['time'][i],
                   'decimation_samples': key[3], 'orientation_block_duration': old['orientation_block_duration'],
                   'old_origins_per_chain': int(old['origins_per_chain']),
                   'new_origins_per_chain': int(data['rows'][i]['origins_per_chain']),
                   'old_region': old['region'], 'new_region': data['regions'][i],
                   'primary_in_both': old['region'] != 'weak_tail' and data['regions'][i] != 'weak_tail',
                   'old_r1': float(old[q + '_r1']), 'old_r2': float(old[q + '_r2']),
                   'old_mean': float(old[q + '_mean']), 'old_se_R2': float(old[q + '_se_R2']),
                   'new_r1': data['values'][0, i, j], 'new_r2': data['values'][1, i, j],
                   'new_r3': data['values'][2, i, j], 'new_mean': mean[i, j], 'new_se_R3': se[i, j],
                   'new_mean_minus_old_mean': mean[i, j] - float(old[q + '_mean'])}
            result.append(row)
    require(len(result) == 1408, 'incomplete four-quantity historical overlap')
    write_csv(out / 'comparison_d2a3.csv', result)
    return result


def scientific_report(out, summary, inventory, features, performance, orientation, cells, comparison):
    lines = ['# D2A.4 — authenticated descriptive analysis for scientific review', '',
             'Generated after evidence authentication; not an equilibrium or terminal-dynamics acceptance.',
             'R=3 whole runs per cell; descriptive SE has two variance degrees of freedom.', '',
             f"Recorded campaign wall: {summary['wall_seconds']:.6f} s; peak child RSS: {summary['max_child_rss_bytes']} bytes.",
             f"Authenticated current evidence: {sum(v['bytes'] for v in inventory.values())} bytes.",
             f"Recorded pre-final-summary bytes: {summary['campaign_bytes_before_final_summary']} (different accounting endpoint).", '',
             '## Computational measurements', '',
             '| Cell | child wall r1 / r2 / r3 (s) | mean (s) | range / mean (%) | peak RSS (bytes) | evidence (bytes) |',
             '|---|---|---|---|---|---|']
    for p in performance:
        times = ' / '.join(f"{p[f'child_wall_r{r}_seconds']:.3f}" for r in (1, 2, 3))
        lines.append(f"| {p['cell']} | {times} | {p['mean_child_wall_seconds']:.3f} | "
                     f"{p['absolute_gap_percent_of_mean']:.3f} | {p['max_recorded_child_rss_bytes']} | {p['recorded_cell_bytes']} |")
    lines += ['', 'All available timers are retained in performance.csv. Timers overlap: do not add',
              'them as independent costs. No isolated observer benchmark or peak GPU memory was measured.',
              'N32 runtime informs planning, not a measured N64 extrapolation.', '',
              '## Primary endpoint: nominal lag 184.32, 39 origins per chain', '',
              'The orientation block duration here is 20.48 (triangular half-width 20.47).',
              'MSD uses point endpoints with decimated origins. These are different filters.', '',
              '| Cell | quantity | r1 | r2 | r3 | mean | descriptive SE |', '|---|---|---|---|---|---|---|']
    endpoints = {r['cell']: r for r in features if int(r['lag_samples']) == 18432}
    for cell, point in endpoints.items():
        for q in PRIMARY_QUANTITIES:
            values = ' | '.join(f"{point[q + f'_r{r}']:.6g}" for r in (1, 2, 3))
            lines.append(f"| {cell} | {q} | {values} | {point[q+'_mean']:.6g} | {point[q+'_se_R3']:.3g} |")
    lines += ['', '## Bare COM consistency, without a pass/fail tolerance', '',
              'Ratios to 6t/33 by the fixed regions (extrema over correlated lag bins, not confidence limits):', '',
              '| Cell | region | replica | min ratio | max ratio |', '|---|---|---|---|---|']
    with (out / 'bare_com_ratios_by_region.csv').open(newline='') as f:
        for p in csv.DictReader(f):
            for r in (1, 2, 3):
                lines.append(f"| {p['cell']} | {p['region']} | {r} | {float(p[f'r{r}_min_ratio']):.6g} | {float(p[f'r{r}_max_ratio']):.6g} |")
    lines += ['', 'Use the replica spreads and Figure 1 to assess bare translational consistency.',
              'No reference diffusion law is imposed on E1, and no new rejection threshold is assigned.', '',
              '## Local MSD slopes and supported regimes', '',
              'Last available three-point stencil in primary support, reported without fitting:', '',
              '| Cell | quantity | lag | alpha r1 | alpha r2 | alpha r3 |', '|---|---|---|---|---|---|']
    with (out / 'slopes.csv').open(newline='') as f:
        slope_rows = list(csv.DictReader(f))
    for cell in 'ABCD':
        for q in ('cm_msd', 'bead16_msd'):
            valid = [r for r in slope_rows if r['cell'] == cell and r['quantity'] == q
                     and all(r[f'stencil_status_r{k}'] == 'available_same_level_stencil' for k in (1, 2, 3))]
            if valid:
                p = valid[-1]
                values = ' | '.join(f"{float(p[f'alpha_r{k}']):.5g}" for k in (1, 2, 3))
                lines.append(f"| {cell} | {q} | {float(p['lag_time']):.6g} | {values} |")
    lines += ['', 'Inspect all same-level stencils in slopes.csv to distinguish short/intermediate behavior.',
              'One late stencil near one does not establish a diffusive regime. A range of monomer',
              'slopes below one is a finite-window observation, not a reptation exponent or asymptotic law.',
              'Unavailable boundary/weak/log-domain slopes are retained with reasons, never set to zero.', '',
              '## Translational and orientational contrasts', '',
              'Sample means at the primary endpoint, E1 minus bare (descriptive differences, not discoveries):', '']
    for bare, constrained in (('A', 'B'), ('C', 'D')):
        differences = ', '.join(f"{q}: {endpoints[constrained][q+'_mean']-endpoints[bare][q+'_mean']:.6g}" for q in PRIMARY_QUANTITIES)
        lines.append(f'- {constrained} minus {bare}: {differences}.')
    lines += ['', 'Stiff minus flexible orientation residuals at this endpoint:', '']
    for flexible, stiff in (('A', 'C'), ('B', 'D')):
        lines.append(f"- {stiff} minus {flexible}: C1={endpoints[stiff]['c1_mean']-endpoints[flexible]['c1_mean']:.6g}; "
                     f"C2={endpoints[stiff]['c2_mean']-endpoints[flexible]['c2_mean']:.6g}.")
    lines += ['', 'Residuals, three-replica agreement and the complete decay shapes determine whether decay',
              'is substantial in the primary window. There is no imposed single-exponential model.', '',
              '| Run | quantity | first sampled lag at/below half | residual at primary endpoint |', '|---|---|---|---|']
    for p in orientation:
        crossing = p['first_sample_at_or_below_half_in_primary']
        text = f'{crossing:.6g}' if crossing != '' else 'not observed in primary'
        lines.append(f"| {p['run']} | {p['quantity']} | {text} | {p['value_at_primary_end']:.6g} |")
    lines += ['', 'A sampled half-level crossing is not a fitted relaxation time, nor a certificate of terminal',
              'decorrelation. Sparse lags through 901.12 include a one-origin endpoint and are descriptive.', '',
              '## T100 versus T1000 comparison', '']
    if comparison is None:
        lines += ['Historical comparison was explicitly disabled; no historical agreement is claimed.']
    else:
        lines += ['comparison_d2a3.csv contains all 88 matched bins per cell for the four primary quantities.',
                  'It preserves old R2/new R3 values, separate SEs and unequal counts/primary flags.',
                  'Match uses integer lag and block/phase support, with no interpolation or equality test.',
                  'Overlapping weak T100 bins may become primary T1000 bins; that is not equivalent support.',
                  'Changed means can reflect longer origin averaging, independent replicas or nonstationarity.',
                  'Use the actual curves and per-cohort spreads to assess persistence of apparent regimes.']
    lines += ['', '## Mechanisms, qualifications and next development', '',
              'Spatially fixed anchors between renewals can restrict translation; attachment hopping changes',
              'the coupled bead and canonical renewal can transfer constraints. Bending alters backbone',
              'configuration and relaxation. These are candidate mechanisms, not effects separately',
              'identified by this four-cell comparison. Translational and orientational responses can',
              'differ; the numerical contrasts above remain observations rather than causal attribution.', '',
              'Whether the window is sufficient must be assessed from supported slope ranges, residual',
              'orientation, replica consistency and time-horizon comparison. Do not infer nonzero',
              'constrained terminal diffusion, reptation scaling or quantitative entanglement length.',
              'D1.6 remains scientifically closed with qualifications: finite-step equilibrium preservation',
              'was not confirmed. Startup drift and timestep sensitivity remain possible limitations.',
              'There is no G(t), stress-correlation analysis or rheology inference here.', '',
              'After review of these actual products, the next development milestone is D2A.5: N64 with',
              'M256 and Z4096 for constrained cells, preserving Z/(M*N)=1/4, three whole-run replicas.',
              'T2000 is provisional; reassess it using N32 supported relaxation and unresolved tails.',
              'If N32 relaxation remains unresolved, report that before choosing N64 duration. This',
              'analysis does not implement longer-chain support or authorize any new simulation.', '']
    (out / 'SCIENTIFIC_REVIEW.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    analysis_main(PROFILE, scientific_report, authenticate_history, compare_history, __file__)
