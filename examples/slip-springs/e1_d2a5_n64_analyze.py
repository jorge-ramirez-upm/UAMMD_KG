#!/usr/bin/env python3
"""CPU-only N64 analysis preparation. Execute only after independent review.

Never imports evidence code, launches children, or walks the campaign root.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from e1_d1_pilot import file_record, require
from e1_d2a3_analyze import (COLORS, PROJECT, SUPPORT, authenticate as authenticate_n32,
                            load, local_slopes, mean_se, read_replicas, snapshot,
                            utc, write_csv, write_json)
from e1_d2a4_analyze import PROFILE as N32_PROFILE, alignment_key
from e1_d2a5_production import MANIFEST_SHA
from e1_d2a5_validate import curve_header, validate_output

EVIDENCE = Path('/home/jramirez/UAMMD_KG-evidence/d2a5/production-n64-n128-r3-v1')
OUTPUT = Path('/home/jramirez/UAMMD_KG-evidence/d2a5-analysis/n64-v1')
IDS = [f'n64-{c}-r{r}' for c in 'ABCD' for r in (1, 2, 3)]
QUANTITIES = ('cm_msd', 'bead32_msd', 'c1', 'c2')
CONFIG = PROJECT / 'e1_d2a5_production_config'


def regular_path(path):
    """Reject symlinked ancestors too, before any traversal or output creation."""
    require(path.is_absolute(), f'absolute path required: {path}')
    require(all(not p.is_symlink() for p in (path, *path.parents)), f'symlink path: {path}')
    return path


def stamp(path):
    s = path.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def selected_inventory(root, immutable):
    """Only named immutable files and twelve explicit N64 subtrees; never runs/*."""
    result, stamps = {}, {}
    def capture(rel):
        path = regular_path(root / rel)
        before = stamp(path)
        result[rel] = file_record(path)
        require(stamp(path) == before, f'input changed: {path}')
        stamps[rel] = before
    for rel in immutable:
        capture(rel)
    for run_id in IDS:
        directory = regular_path(root / 'runs' / run_id)
        require(directory.is_dir(), f'missing run directory: {directory}')
        for path in sorted(directory.rglob('*')):
            regular_path(path)
            require(path.is_file() or path.is_dir(), f'special evidence file: {path}')
            if path.is_file():
                capture(str(path.relative_to(root)))
    return {'files': result, 'stamps': stamps}


def completed_records(summary):
    require(summary['manifest_sha256'] == MANIFEST_SHA, 'summary manifest identity')
    require(all(summary['completed_runs'].count(i) == 1 for i in IDS), 'twelve completed N64 identities required')
    records = [r for r in summary['run_records'] if r['id'] in IDS]
    require(len(records) == 12 and {r['id'] for r in records} == set(IDS), 'N64 summary record closure')
    return {r['id']: r for r in records}


def authenticate(root):
    regular_path(root)
    # Read mutable summary exactly once. Retain its bytes, never rehash/reopen it.
    raw_summary = regular_path(root / 'summary.json').read_bytes()
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'duplicate summary key: {key}')
            result[key] = value
        return result
    summary = json.loads(raw_summary, object_pairs_hook=unique_pairs)
    json.dumps(summary, allow_nan=False)
    records = completed_records(summary)
    require(file_record(CONFIG / 'manifest.json')['sha256'] == MANIFEST_SHA, 'local frozen manifest')
    manifest = load(CONFIG / 'manifest.json')
    require(regular_path(root / 'config/manifest.json').read_bytes() == (CONFIG / 'manifest.json').read_bytes(),
            'archived frozen manifest identity')
    runs = [r for r in manifest['runs'] if r['N'] == 64]
    require([r['id'] for r in runs] == IDS, 'exact N64 manifest cohort')
    require(len({r['seed'] for r in runs}) == len({r['replica_id'] for r in runs}) == 12,
            'independent seeds/replica IDs')
    immutable = ['config/manifest.json', 'config/manifest.sha256', 'provenance/launch.json']
    immutable += [f'config/{n}' for n in ('n64-equilibrium.steps', 'n64-snapshots.steps')]
    immutable += [f'provenance/{n}' for n in manifest['tools']]
    before = selected_inventory(root, immutable)
    files = before['files']
    require(files['config/manifest.json']['sha256'] == MANIFEST_SHA, 'manifest changed before capture')
    require((root / 'config/manifest.sha256').read_bytes() == (CONFIG / 'manifest.sha256').read_bytes(),
            'manifest checksum record')
    for name in ('n64-equilibrium.steps', 'n64-snapshots.steps'):
        require(files[f'config/{name}'] == manifest['schedules'][name], f'N64 schedule identity: {name}')
    for name, record in manifest['tools'].items():
        require(files[f'provenance/{name}'] == file_record(PROJECT / name) == record,
                f'frozen archived/local helper identity: {name}')
    launch = load(root / 'provenance/launch.json')
    require(launch['manifest_sha256'] == MANIFEST_SHA and
            launch['implementation_sha'] == manifest['implementation_sha'] and
            launch['executable'] == manifest['executable'], 'recorded launch/source/executable identity')
    for run in runs:
        require(run['M'] == 256 and run['Z'] == (4096 if run['cell'] in 'BD' else 0) and
                run['kappa'] == (10 if run['cell'] in 'CD' else 0), 'N64 physical matrix')
        e = run['expected']
        require((e['N'], e['T'], e['dt'], e['stride'], e['levels'], e['slots'], e['m'],
                 e['dynamics_frames'], e['exported_bins_per_chain']) ==
                (64, 10000, .0001, 100, 19, 16, 2, 1000001, 143), 'N64 acquisition')
        run_id = run['id']
        directory = root / 'runs' / run_id
        prefix = f'runs/{run_id}/'
        record = records[run_id]
        require(files[prefix + 'receipt.json'] == record['receipt'], f'receipt anchor: {run_id}')
        receipt = load(directory / 'receipt.json')
        require(receipt['id'] == run_id and receipt['manifest_sha256'] == MANIFEST_SHA, 'receipt identity')
        actual = {k[len(prefix):]: v for k, v in files.items()
                  if k.startswith(prefix) and k != prefix + 'receipt.json'}
        require(actual == receipt['files'], f'complete receipt hash/size closure: {run_id}')
        require(sum(v['bytes'] for k, v in files.items() if k.startswith(prefix)) == record['output_bytes'],
                f'summary run byte count: {run_id}')
        process = load(directory / 'process.json')
        require(process == receipt['process'] == record['process'] and
                process['exit_code'] == 0 and process['status'] == 'exited', f'successful process: {run_id}')
        run_launch = load(directory / 'launch.json')
        require(run_launch['argv'] == run['argv'] and run_launch['seed'] == run['seed'] and
                run_launch['replica_id'] == run['replica_id'] and
                run_launch['gpu']['uuid'] == manifest['gpu_uuid'], 'original CLI/seed/replica/GPU')
        require(load(directory / 'output/metadata.json')['gpu'] == run_launch['gpu']['name'], 'recorded GPU name')
        # Uses only this directory, never the manifest's absolute output/executable paths.
        require(validate_output(directory / 'output', run) == receipt['validation'], 'completion revalidation')
    require(selected_inventory(root, immutable) == before, 'N64 evidence changed during authentication')
    return manifest, runs, immutable, before, {
        'status': 'authenticated_before_reduction', 'utc': utc(), 'manifest_sha256': MANIFEST_SHA,
        'summary_read_once_sha256': hashlib.sha256(raw_summary).hexdigest(),
        'summary_read_once_bytes': len(raw_summary), 'completed_n64_records': records,
        'input_inventory': before,
        'scope': 'Twelve N64 receipts and files; recorded frozen source/executable identity. '
                 'No N128 directory, live executable, production checkout or prerequisites traversed. '
                 'Summary/progress changes allowed. Checksums are not independent execution attestation.',
        'compiler_provenance': manifest['compiler_provenance']}


def read_cells(root, manifest, runs):
    cells = {}
    grid = manifest['supports']['64']['grid']
    for cell in 'ABCD':
        selected = [r for r in runs if r['cell'] == cell]
        replicas = []
        for run in selected:
            with (root / 'runs' / run['id'] / 'output/dynamics/replica_correlations.csv').open(newline='') as stream:
                reader = csv.DictReader(stream)
                require(reader.fieldnames == curve_header(64), 'N64 column labels')
                replicas.append(list(reader))
        anchor = [[r[k] for k in SUPPORT] for r in replicas[0]]
        require(len(anchor) == len(grid) == 143 and all(
            [[r[k] for k in SUPPORT] for r in rows] == anchor for rows in replicas), 'replica support equality')
        for row, support in zip(replicas[0], grid):
            for key in ('lag_samples', 'lag_steps', 'origins_per_chain'):
                require(row[key] == str(support[key]), f'frozen integer support: {key}')
            require(row['decimation_samples'] == str(support['block_samples']), 'frozen block support')
        values = np.array([[[float(row[q]) for q in QUANTITIES] for row in rows] for rows in replicas])
        require(np.isfinite(values).all() and (values[:, :, :2] >= 0).all(), 'finite/nonnegative MSD')
        regions = [('fine' if p['block_samples'] == 1 else 'coarse_primary') if p['primary']
                   else 'weak_tail' for p in grid]
        cells[cell] = dict(runs=selected, rows=replicas[0], values=values, regions=regions,
                           blocks=np.array([p['block_samples'] for p in grid]),
                           time=np.array([float(r['lag_time']) for r in replicas[0]]))
    return cells


def numerical_tables(out, cells):
    curves, slopes, bare, orientation, terminal = [], [], [], [], []
    for cell, d in cells.items():
        mean, se = mean_se(d['values'])
        primary = np.array([r != 'weak_tail' for r in d['regions']])
        positive = d['time'] > 0
        for i, support in enumerate(d['rows']):
            row = dict(cell=cell, **{k: support[k] for k in SUPPORT}, region=d['regions'][i])
            for j, q in enumerate(QUANTITIES):
                row.update({q + f'_r{r+1}': d['values'][r, i, j] for r in range(3)})
                row.update({q + '_mean': mean[i, j], q + '_se_R3': se[i, j]})
            curves.append(row)
            if cell in 'AC' and positive[i]:
                ratios = d['values'][:, i, 0] / (6 * d['time'][i] / 65)
                avg, error = mean_se(ratios)
                bare.append(dict(cell=cell, lag_samples=int(support['lag_samples']), lag_time=d['time'][i],
                                 region=d['regions'][i], reference=6*d['time'][i]/65,
                                 **{f'ratio_r{r+1}': ratios[r] for r in range(3)},
                                 ratio_mean=avg, ratio_se_R3=error))
        for j, q in enumerate(QUANTITIES[:2]):
            alpha, reasons = local_slopes(d['time'], d['values'][:, :, j], d['blocks'], d['regions'])
            for i, statuses in enumerate(reasons):
                valid = all(s == 'available_same_level_stencil' for s in statuses)
                avg, error = mean_se(alpha[:, i]) if valid else ('', '')
                slopes.append(dict(cell=cell, quantity=q, lag_samples=int(d['rows'][i]['lag_samples']),
                    lag_time=d['time'][i], block_samples=int(d['blocks'][i]), region=d['regions'][i],
                    **{f'status_r{r+1}': statuses[r] for r in range(3)},
                    **{f'alpha_r{r+1}': alpha[r, i] if statuses[r] == 'available_same_level_stencil' else '' for r in range(3)},
                    alpha_mean=avg, alpha_se_R3=error))
            # All supported same-level windows (>=3 interior stencils), no result-selected fit.
            for block in np.unique(d['blocks']):
                mask = primary & positive & (d['blocks'] == block)
                ii = np.flatnonzero(mask)
                interior = [i for i in ii if all(s == 'available_same_level_stencil' for s in reasons[i])]
                if len(interior) < 3:
                    continue
                for r in range(3):
                    diffusion = d['values'][r, ii, j] / (6 * d['time'][ii])
                    endpoint = ii[-1]
                    terminal.append(dict(cell=cell, run=d['runs'][r]['id'], quantity=q,
                        block_samples=int(block), start_time=d['time'][ii[0]], end_time=d['time'][endpoint],
                        time_ratio=d['time'][endpoint]/d['time'][ii[0]], bins=len(ii),
                        slope_stencils=len(interior), min_origins=min(int(d['rows'][i]['origins_per_chain']) for i in ii),
                        slope_min=alpha[r, interior].min(), slope_max=alpha[r, interior].max(),
                        effective_D_min=diffusion.min(), effective_D_max=diffusion.max(),
                        effective_D_max_over_min=diffusion.max()/diffusion.min() if diffusion.min() > 0 else '',
                        c1_at_end=d['values'][r, endpoint, 2], c2_at_end=d['values'][r, endpoint, 3],
                        assessment='descriptive_supported_window_requires_review_no_terminal_acceptance'))
        ii = np.flatnonzero(primary & positive)
        for j, q in ((2, 'c1'), (3, 'c2')):
            for r in range(3):
                y = d['values'][r, :, j]
                below = [i for i in ii if y[i] <= .5]
                orientation.append(dict(cell=cell, run=d['runs'][r]['id'], quantity=q,
                    first_sample_at_or_below_half=d['time'][below[0]] if below else '',
                    crossing_status='sampled_no_fit' if below else 'not_observed_in_primary',
                    primary_end_time=d['time'][ii[-1]], residual_at_primary_end=y[ii[-1]],
                    primary_end_block_duration=d['rows'][ii[-1]]['orientation_block_duration'],
                    primary_min=y[ii].min(), primary_max=y[ii].max()))
    for name, rows in [('curves', curves), ('slopes', slopes), ('bare_com', bare),
                       ('orientation', orientation), ('terminal_windows', terminal)]:
        write_csv(out / (name + '.csv'), rows)
    return terminal, orientation


def compare_n32(out, cells, old_cells, old_manifest, runs):
    from e1_d2a3_run import QUANTITIES as OLD_QUANTITIES
    require(not ({r['seed'] for r in runs} & {r['seed'] for r in old_manifest['runs']}), 'unpaired comparison seeds')
    rows = []
    for cell, newer in cells.items():
        older = old_cells[cell]
        # Both validators authenticate the same endpoint/block semantics. Check model/cadence
        # options, allowing precisely the documented chain-length, duration and output changes.
        excluded = {'--springs', '--slip-count', '--steps', '--seed', '--dynamics-replica', '--output',
                    '--sample', '--equilibrium-steps', '--equilibrium-snapshots', '--dynamics-levels',
                    '--dynamics-mib'}
        flags = []
        for run in (older['runs'][0], newer['runs'][0]):
            flags.append({k: v for k, v in zip(run['argv'][1::2], run['argv'][2::2]) if k not in excluded})
        require(flags[0] == flags[1], f'N32/N64 physical/cadence compatibility: {cell}')
        index = {alignment_key(dict(cell=cell, **p)): i for i, p in enumerate(newer['rows'])}
        om, os = mean_se(older['values'])
        nm, ns = mean_se(newer['values'])
        for oi, support in enumerate(older['rows']):
            key = alignment_key(dict(cell=cell, **support))
            if key not in index:
                continue
            ni = index[key]
            for j, q in enumerate(QUANTITIES):
                old_q = 'bead16_msd' if q == 'bead32_msd' else q
                oj = OLD_QUANTITIES.index(old_q)
                rows.append(dict(cell=cell, quantity=q, n32_quantity=old_q,
                    **{k: support[k] for k in SUPPORT if k != 'origins_per_chain'},
                    n32_origins=int(support['origins_per_chain']),
                    n64_origins=int(newer['rows'][ni]['origins_per_chain']),
                    n32_region=older['regions'][oi], n64_region=newer['regions'][ni],
                    primary_in_both=older['regions'][oi] != 'weak_tail' and newer['regions'][ni] != 'weak_tail',
                    **{f'n32_r{r+1}': older['values'][r, oi, oj] for r in range(3)},
                    **{f'n64_r{r+1}': newer['values'][r, ni, j] for r in range(3)},
                    n32_mean=om[oi, oj], n32_se_R3=os[oi, oj], n64_mean=nm[ni, j], n64_se_R3=ns[ni, j],
                    n64_minus_n32=nm[ni, j]-om[oi, oj], n32_T=1000, n64_T=10000,
                    n32_N=32, n64_N=64, n32_Z=2048 if cell in 'BD' else 0, n64_Z=4096 if cell in 'BD' else 0))
    require(len(rows) == sum(len(d['rows']) for d in old_cells.values()) * 4, 'complete compatible N32 overlap')
    write_csv(out / 'comparison_n32_n64.csv', rows)


def figures(out, cells):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    omissions = []
    for number, q in enumerate(QUANTITIES, 1):
        fig, ax = plt.subplots(figsize=(7.2, 5.2))
        ax.set_xscale('log')
        if q.endswith('msd'):
            ax.set_yscale('log')
        else:
            ax.axhline(0, color='.5', linewidth=.6)
        ax.axvspan(1966.08, 9175.04, color='.92')
        for cell, d in cells.items():
            y = d['values'][:, :, QUANTITIES.index(q)]
            mean, _ = mean_se(y)
            weak = np.array([r == 'weak_tail' for r in d['regions']])
            for block in np.unique(d['blocks']):
                for tail in (False, True):
                    mask = (d['blocks'] == block) & (d['time'] > 0) & (weak == tail)
                    if not mask.any():
                        continue
                    for r in range(3):
                        if q.endswith('msd'):
                            omissions.extend(dict(cell=cell, quantity=q, replica=r+1, lag_time=float(t))
                                             for t in d['time'][mask][y[r, mask] <= 0])
                        yy = np.ma.masked_less_equal(y[r, mask], 0) if q.endswith('msd') else y[r, mask]
                        ax.plot(d['time'][mask], yy, color=COLORS[cell], ls=('-', '--', '-.')[r], lw=.6, alpha=.4)
                    yy = np.ma.masked_less_equal(mean[mask], 0) if q.endswith('msd') else mean[mask]
                    ax.plot(d['time'][mask], yy, color=COLORS[cell], ls=':' if tail else '-', lw=1.7)
        handles = [Line2D([], [], color=COLORS[c], label=f'{c}: kappa={10 if c in "CD" else 0}, Z={4096 if c in "BD" else 0}') for c in 'ABCD']
        if q == 'cm_msd':
            t = np.array([.01, 9175.04])
            ax.plot(t, 6*t/65, color='black', ls='-.', lw=1)
            handles.append(Line2D([], [], color='black', ls='-.', label='Bare reference 6t/65'))
        ax.legend(handles=handles, frameon=False, fontsize=8)
        ax.set(xlabel='Lag (model time)', ylabel=q, title=f'D2A.5 N64: {q}')
        ax.grid(alpha=.15)
        fig.text(.12, .035, 'Thin solid/dashed/dash-dot: independent replicas; thick: equal-weight mean.\n'
                 'Gray/dotted: weak support. Segments stop at multi-tau boundaries.\n'
                 'N=64 bonds (65 beads), M=256, T=10000; zero lag omitted; no confidence band.', fontsize=8)
        fig.subplots_adjust(bottom=.23)
        for ext in ('png', 'pdf'):
            fig.savefig(out / f'figure_{number}_{q}.{ext}', dpi=300)
        plt.close(fig)
    write_json(out / 'plot_support.json', dict(zero_lag_omitted_from_log_x=True,
        nonpositive_msd_omissions=omissions, raw_values_preserved_in_curves=True,
        multi_tau_levels_never_joined=True, primary_last_lag_samples=196608,
        weak_tail_last_lag_samples=917504))
    return matplotlib.__version__


def report(out, windows, orientation):
    lines = ['# N64 descriptive scientific review', '',
        'R=3 independent whole runs/cell; equal-weight means and descriptive SE (two variance degrees of freedom).',
        'Chains, overlapping origins, monomers and lag bins are not additional replicas.', '',
        'Primary support is taken from frozen integer manifest fields: lag<=1966.08 and >=32 origins/chain.',
        'The endpoint has 49 origins/chain. The 9175.04 tail has one origin and cannot establish terminal motion.',
        'MSD uses last-position decimation; C1 and rank-two C2 use block-averaged fine features without renormalization.',
        'Orientation values are triangular-filter correlations, not point values at the nominal lag.', '',
        '## Supported interval diagnostics', '',
        'terminal_windows.csv retains every eligible same-level supported interval with at least three interior',
        'slope stencils, separately per replica and for COM and central-bead MSD. D_eff=g/(6t) is a diagnostic,',
        'not a fitted terminal coefficient. Compare min/max D_eff and slopes across adjacent intervals and all replicas.',
        'Same-level intervals span less than a decade; no single interval or endpoint establishes sustained diffusion.',
        'Assess COM slopes approaching one, D_eff stability, central-bead recovery, and both orientation residuals together.',
        'No numerical terminal-acceptance threshold or reptation fit is imposed. Terminal relaxation remains unresolved',
        'until independent inspection finds a sustained supported range and agreement across the three runs.', '',
        '| Cell | latest eligible window | quantity | replica | alpha min/max | D_eff min/max |',
        '|---|---|---|---|---|---|']
    for cell in 'ABCD':
        for q in QUANTITIES[:2]:
            selected = [w for w in windows if w['cell'] == cell and w['quantity'] == q]
            end = max(w['end_time'] for w in selected)
            for w in selected:
                if w['end_time'] == end:
                    lines.append(f"| {cell} | {w['start_time']:.6g}–{end:.6g} | {q} | {w['run']} | "
                                 f"{w['slope_min']:.4g}/{w['slope_max']:.4g} | {w['effective_D_min']:.4g}/{w['effective_D_max']:.4g} |")
    lines += ['', '## Orientational residuals', '',
              '| Run | quantity | residual at primary end | first sampled half-level crossing |',
              '|---|---|---|---|']
    for p in orientation:
        lines.append(f"| {p['run']} | {p['quantity']} | {p['residual_at_primary_end']:.6g} | {p['first_sample_at_or_below_half']} |")
    lines += ['', 'A half-level crossing is not a fitted relaxation time or proof of substantial terminal decorrelation.',
        'Inspect full decay and replica spread; a single small residual can be sampling noise.', '',
        '## Controls and chain-length comparison', '',
        'bare_com.csv gives ratios to 6t/65 only for A/C; no constrained diffusion reference is imposed.',
        'comparison_n32_n64.csv uses independently authenticated D2A.4 N32 raw results and exact integer lag,',
        'decimation, phase and orientation-block matches. Central beads are 16/32 respectively.',
        'N32 T=1000 versus N64 T=10000 changes origin counts and support; compare primary_in_both first.',
        'N changes 32→64, constrained Z changes 2048→4096 at fixed Z/(M*N)=1/4; M=256 and dt/stride are unchanged.',
        'Report translational and orientational differences separately. Two lengths do not establish asymptotic scaling.',
        'Matched filters do not make different observation durations or independent seeds numerically equivalent.', '',
        'D1.6 equilibrium preservation remains qualified; startup drift, timestep error and nonstationarity are unresolved.',
        'No rheology, terminal acceptance, entanglement-length estimate or new simulation is authorized by these products.', '']
    (out / 'SCIENTIFIC_REVIEW.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-reviewed-analysis', action='store_true', required=True)
    parser.add_argument('--d2a4-evidence', type=Path, default=Path(N32_PROFILE['evidence']))
    args = parser.parse_args()
    root, out = regular_path(EVIDENCE), regular_path(OUTPUT / 'analysis')
    old_root = regular_path(args.d2a4_evidence).resolve(strict=True)
    require(old_root == Path(N32_PROFILE['evidence']), 'use the pinned D2A.4 campaign')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=False)
    try:
        source_names = ('e1_d2a5_n64_analyze.py', 'e1_d2a3_analyze.py', 'e1_d2a4_analyze.py',
                        'e1_d2a5_validate.py', 'e1_d2a3_run.py', 'e1_d2a5_production.py')
        source_files = {name: file_record(PROJECT / name) for name in source_names}
        manifest, runs, immutable, before, auth = authenticate(root)
        old_manifest, _, old_before = authenticate_n32(old_root, N32_PROFILE)
        write_json(out / 'authentication.json', auth)
        write_json(out / 'n32_authentication.json', dict(manifest_sha256=N32_PROFILE['manifest_sha'],
                                                       input_inventory=old_before, root=str(old_root)))
        cells = read_cells(root, manifest, runs)
        old_cells = read_replicas(old_root, old_manifest, N32_PROFILE)
        windows, orientation = numerical_tables(out, cells)
        compare_n32(out, cells, old_cells, old_manifest, runs)
        version = figures(out, cells)
        report(out, windows, orientation)
        require(selected_inventory(root, immutable) == before, 'N64 input changed; all analysis invalid')
        require(snapshot(old_root) == old_before, 'N32 input changed; all analysis invalid')
        require({name: file_record(PROJECT / name) for name in source_names} == source_files,
                'analysis sources changed; all analysis invalid')
        write_json(out / 'analysis_complete.json', dict(status='descriptive_analysis_for_independent_review',
            utc=utc(), scientific_acceptance=False, n64_evidence_unchanged=True, n32_evidence_unchanged=True,
            analysis_checkout_head=subprocess.run(['git', '-C', str(PROJECT), 'rev-parse', 'HEAD'],
                check=True, capture_output=True, text=True).stdout.strip(),
            source_files=source_files, numpy=np.__version__,
            matplotlib=version, products=snapshot(out)))
    except BaseException as error:
        write_json(out / 'FAILED.json', dict(status='all_products_invalid', utc=utc(),
                                           error=f'{type(error).__name__}: {error}'))
        raise


if __name__ == '__main__':
    main()
