#!/usr/bin/env python3
"""Exclusive tables and full-context plots from authenticated CPU review evidence."""
import argparse
import csv
import math
from pathlib import Path
import statistics

import reproduce_ee12 as review

NAMES = ('bound_fraction', 'intra', 'inter', 'L1', 'L2', 'mean_rg2',
         'mean_center_terminal_r2', 'largest_cluster_fraction', 'isolated_stars',
         'satellite_stars', 'mean_degree', 'second_degree_moment')


CORRELATION_PAIRS = (('intra', 'inter'), ('intra', 'mean_degree'),
    ('intra', 'largest_cluster_fraction'), ('L1', 'L2'), ('L1', 'mean_degree'),
    ('L1', 'intra'), ('isolated_stars', 'stars_intra_loops_2'),
    ('L1', 'edges_m2'), ('L1', 'edges_m3'), ('intra', 'mean_rg2'),
    ('intra', 'mean_center_terminal_r2'), ('intra', 'stars_intra_loops_2'))


def pearson(first, second):
    review.joint.require(len(first) == len(second) and len(first) > 1, 'correlation coverage differs')
    a, b = statistics.mean(first), statistics.mean(second)
    variance_a = sum((x - a) ** 2 for x in first)
    variance_b = sum((y - b) ** 2 for y in second)
    if variance_a == 0 or variance_b == 0:
        return None
    return sum((x - a) * (y - b) for x, y in zip(first, second)) / math.sqrt(variance_a * variance_b)


def write_correlations(histories, directory):
    records = []
    for replica, rows in enumerate(histories, 1):
        by_step = {int(row['step']): row for row in rows}
        for start, end in ((4000000, 8000000), (8000000, 12000000),
                           (12000000, 16000000), (8000000, 16000000),
                           (12000000, 14000000), (14000000, 16000000),
                           (15000000, 16000000)):
            for width in (1000, 250000, 500000):
                if (end - start) // width < 4:
                    continue
                selected = [{name: statistics.mean(by_step[step][name] for step in
                    range(boundary + 1000, boundary + width + 1, 1000))
                    for name in {n for pair in CORRELATION_PAIRS for n in pair}}
                    for boundary in range(start, end, width)]
                for first, second in CORRELATION_PAIRS:
                    records.append(dict(replica=replica, start_step=start, end_step=end,
                        bin_steps=width, bins=len(selected), first=first, second=second,
                        pearson=pearson([r[first] for r in selected], [r[second] for r in selected])))
    review.joint.runner.exclusive_json(directory / 'CORRELATIONS.json', dict(records=records,
        independent_units='three original histories only',
        interpretation='descriptive within-replica covariance; no frame/block p-values or independent-sample claims; population and degree identities induce correlations'))


def write_replica_table(summary, directory):
    lines = ['# Replica-level complete 0–16M context', '',
             'Each width tiles the complete path. Step zero remains in frame exports.',
             'Early windows are preparation context, not certified stationary.', '']
    for width in review.WIDTHS:
        lines += [f'## {width:,}-step windows', '',
                  '| Replica | Steps (M) | ' + ' | '.join(NAMES) + ' |',
                  '|---|---|' + '---:|' * len(NAMES)]
        for record in summary['records']:
            for start in range(0, 16000000, width):
                window = next(w for w in record['windows'] if
                    (w['start_step_exclusive'], w['end_step_inclusive']) == (start, start + width))
                lines.append(f"| r{record['replica']:03d} | {start / 1e6:g}–{(start + width) / 1e6:g} | " +
                    ' | '.join(f"{window['metrics'][name]['mean']:.8g}" for name in NAMES) + ' |')
    with (directory / 'REPLICA_WINDOWS.md').open('x') as stream:
        stream.write('\n'.join(lines) + '\n')


def write_late_diagnostics(summary, directory):
    names = ('intra', 'inter', 'L1', 'L2', 'mean_degree', 'mean_rg2',
             'mean_center_terminal_r2', 'largest_cluster_fraction')
    lines = ['# Late paired contrasts and local uncertainty', '',
             'Three original histories only; df=2 exploratory intervals. Overlapping contrasts are correlated.',
             'Slope units below are change per million MD steps. IAT units are physical time.', '',
             '| Interval (M) | Observable | r001 change | r002 change | r003 change | Mean ± 95% half-width |',
             '|---|---|---:|---:|---:|---:|']
    for c in summary['comparisons']:
        if c['observable'] not in names or c['early_steps'][0] < 8000000:
            continue
        label = '–'.join(f'{v / 1e6:g}' for v in c['early_steps']) + ' → ' + '–'.join(
            f'{v / 1e6:g}' for v in c['late_steps'])
        lines.append('| ' + label + ' | ' + c['observable'] + ' | ' +
            ' | '.join(f'{v:.8g}' for v in c['per_replica_changes']) +
            f" | {c['mean']:.8g} ± {c['ci95_half_width']:.8g} |")
    lines += ['', '| Replica | Interval (M) | Observable | Slope/M | IAT | Effective samples | IAT SEM | 5 / 10 / 20-block SEM | Constant flag |',
              '|---|---|---|---:|---:|---:|---:|---|---|']
    for record in summary['records']:
        for w in record['windows']:
            start, end = w['start_step_exclusive'], w['end_step_inclusive']
            if (start, end) not in ((8000000, 12000000), (12000000, 16000000),
                    (12000000, 14000000), (14000000, 16000000), (15000000, 16000000)):
                continue
            for name in names:
                value = w['metrics'][name]
                constant = value['constant_not_mixing_evidence']
                effective = 'unresolved' if constant else f"{value['effective_samples_estimate']:.6g}"
                block = ' / '.join(f"{value['blocking_sem_sensitivity'][str(k)]:.6g}" for k in (5, 10, 20))
                lines.append(f"| r{record['replica']:03d} | {start/1e6:g}–{end/1e6:g} | {name} | " +
                    f"{value['slope'] * 10000:.7g} | {value['tau_time']:.7g} | {effective} | " +
                    f"{value['sem_estimate']:.7g} | {block} | {constant} |")
    with (directory / 'LATE_DIAGNOSTICS.md').open('x') as stream:
        stream.write('\n'.join(lines) + '\n')
    names = tuple(f'edges_m{k}' for k in range(1, 5)) + tuple(
        f'stars_intra_loops_{k}' for k in range(3)) + tuple(
        f'degree_{k}_fraction' for k in range(5)) + ('isolated_stars', 'satellite_stars', 'satellite_components')
    lines = ['# Full multiplicity, intra-loop, distinct-degree and peripheral distributions', '',
        'Means in nonoverlapping 4M windows; all smaller windows are in summary.json/window_estimates.csv.', '',
        '| Replica | Interval (M) | ' + ' | '.join(names) + ' |', '|---|---|' + '---:|' * len(names)]
    for record in summary['records']:
        for start in range(0, 16000000, 4000000):
            w = next(w for w in record['windows'] if
                (w['start_step_exclusive'], w['end_step_inclusive']) == (start, start + 4000000))
            lines.append(f"| r{record['replica']:03d} | {start/1e6:g}–{start/1e6+4:g} | " +
                ' | '.join(f"{w['metrics'][name]['mean']:.8g}" for name in names) + ' |')
    with (directory / 'NETWORK_DISTRIBUTIONS.md').open('x') as stream:
        stream.write('\n'.join(lines) + '\n')


def write_reference(directory, summary):
    root = Path(__file__).parent
    reference_dir = review.REPOSITORY / 'examples/KG_Assoc/reviews/e2_ee10_12m_20261015'
    integrity = review.joint.campaign.load_json(reference_dir / 'INTEGRITY.json')
    review.joint.runner.check_hashes({str(reference_dir / p): h for p, h in integrity['sha256'].items()})
    reference_summary = review.joint.campaign.load_json(reference_dir / 'evidence/summary.json')
    authentication = review.joint.campaign.load_json(root / 'AUTHENTICATION.json')
    reference = authentication['reference_record']
    result = []
    for accepted, record in zip(reference['record']['histories'], reference_summary['records']):
        review.joint.require(accepted['replica'] == record['replica'], 'reference replica differs')
        review.joint.runner.check_hashes(accepted['sha256'])
        _, rows = review.joint.segment.review.analysis.stationarity.read_state(accepted['prefix'] + '.state')
        window = next(w for w in record['windows'] if
            (w['start_step_exclusive'], w['end_step_inclusive']) == (10000000, 12000000))
        selected = [row for row in rows if 10000000 < row['step'] <= 12000000]
        for name in NAMES:
            if name in selected[0]:
                review.joint.require(math.isclose(statistics.mean(row[name] for row in selected),
                    window['metrics'][name]['mean'], rel_tol=1e-12, abs_tol=1e-12),
                    'qualified Ee10 reference state differs')
        for name in ('creations', 'breaks'):
            boundary = next(row for row in rows if row['step'] == 10000000)
            review.joint.require(window['event_counts'][name] == rows[-1][name] - boundary[name],
                                 'qualified Ee10 event counters differ')
        result.append(dict(replica=record['replica'], window=window))
    review.joint.runner.exclusive_json(directory / 'EE10_COMPARISON.json', dict(
        system='F04_N010_RP080_EE10_EA04', interval=[10000000, 12000000], records=result,
        reference_record_sha256=reference['sha256'], reference_record=reference['path'],
        independent_units='three original histories per Ee; descriptive comparison, no between-Ee pairing',
        limitations='same E1 geometries; different chemical/MD streams; qualified Ee10 also has unresolved slow topology; reference neighbor counts/exposures reuse authenticated frozen review, no new reference replay',
        source_sha256=review.joint.runner.hash_files([reference_dir / 'evidence/summary.json',
            reference_dir / 'INTEGRITY.json', root / 'AUTHENTICATION.json', Path(__file__)])))


def isolation_spells(stars, atom_to_star, events, end):
    """Exact inter-bond isolation intervals, including sub-diagnostic excursions."""
    degree = dict.fromkeys(stars, 0)
    since = dict.fromkeys(stars, 0)
    spells = []
    for step, kind, pair in events:
        first, second = (atom_to_star[atom] for atom in pair)
        if first == second:
            continue
        for star in (first, second):
            if kind == 'C':
                if degree[star] == 0:
                    spells.append(dict(star=star, start=since.pop(star), end=step,
                                       right_censored=False))
                degree[star] += 1
            else:
                degree[star] -= 1
                review.joint.require(degree[star] >= 0, 'negative inter-bond degree')
                if degree[star] == 0:
                    since[star] = step
    spells.extend(dict(star=star, start=start, end=end, right_censored=True)
                  for star, start in since.items())
    return spells


def write_isolation(directory, histories):
    provenance = review.joint.campaign.load_json(directory / 'provenance.json')
    records = []
    for history, frames in zip(provenance['validated_histories'], histories):
        entry = history['entry']
        system, _ = review.joint.runner.validation.read_parent(entry)
        _, events = review.joint.segment.review.analysis.dynamics.read_events(
            entry['output_prefix'] + '.events', system)
        spells = isolation_spells(system['stars'], system['atom_to_star'], events, 16000000)
        # Integrate exact residence over each interval rather than treating frames as trials.
        intervals = []
        for start, end in ((4000000, 8000000), (8000000, 12000000),
                           (12000000, 16000000), (14000000, 16000000)):
            overlaps = [dict(spell, overlap_steps=max(0, min(end, spell['end']) -
                                                      max(start, spell['start']))) for spell in spells]
            overlaps = [spell for spell in overlaps if spell['overlap_steps'] > 0]
            intervals.append(dict(start_step=start, end_step=end,
                time_averaged_isolated_stars=sum(spell['overlap_steps'] for spell in overlaps) / (end - start),
                unique_isolated_stars=sorted({spell['star'] for spell in overlaps}),
                continuously_isolated_stars=sorted(spell['star'] for spell in overlaps
                    if spell['start'] <= start and spell['end'] >= end),
                spells=overlaps))
        # Independent sampled counts agree with the validated graph frames.
        for frame in frames:
            step = int(frame['step'])
            isolated = sum(spell['start'] <= step < spell['end'] or
                           spell['right_censored'] and step == spell['end'] for spell in spells)
            review.joint.require(isolated == frame['isolated_stars'], 'isolation replay differs')
        records.append(dict(replica=entry['replica'], intervals=intervals))
    review.joint.runner.exclusive_json(directory / 'ISOLATION.json', dict(records=records,
        definitions='inter-star bond-degree zero; exact event-time residence, right-censored at 16M; zero-duration intermediate states carry no residence; not an independent stationarity test'))


def main(directory):
    summary_path = directory / 'summary.json'
    summary = review.joint.campaign.load_json(summary_path)
    review.joint.require(summary['system']['system_id'] == review.SYSTEM, 'wrong system')
    destination = directory / 'WINDOWS.md'
    review.joint.require(not destination.exists(), 'immutable table already exists')
    lines = ['# Complete nonoverlapping context', '',
             'Means across three histories. Initial windows are retained preparation context.',
             'Unadjusted Student-t df=2 intervals below are descriptive, not stationarity tests.', '']
    for width in review.WIDTHS:
        lines += [f'## {width:,}-step windows', '', '| Steps (M) | ' + ' | '.join(NAMES) + ' |',
                  '|---|' + '---:|' * len(NAMES)]
        for start in range(0, 16000000, width):
            windows = [next(w for w in r['windows'] if
                           (w['start_step_exclusive'], w['end_step_inclusive']) ==
                           (start, start + width)) for r in summary['records']]
            values = [statistics.mean(w['metrics'][name]['mean'] for w in windows) for name in NAMES]
            lines.append(f'| {start / 1e6:g}–{(start + width) / 1e6:g} | ' +
                         ' | '.join(f'{v:.7g}' for v in values) + ' |')
        lines.append('')
    lines += ['## Paired 8–12M → 12–16M changes', '',
              '| Observable | r001 | r002 | r003 | Mean ± 95% half-width |',
              '|---|---:|---:|---:|---:|']
    for contrast in summary['comparisons']:
        if contrast['early_steps'] != [8000000, 12000000] or contrast['late_steps'] != [12000000, 16000000]:
            continue
        lines.append('| ' + contrast['observable'] + ' | ' +
                     ' | '.join(f'{v:.7g}' for v in contrast['per_replica_changes']) +
                     f" | {contrast['mean']:.7g} ± {contrast['ci95_half_width']:.7g} |")
    write_replica_table(summary, directory)
    write_late_diagnostics(summary, directory)
    with destination.open('x') as stream:
        stream.write('\n'.join(lines) + '\n')
    write_reference(directory, summary)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    groups = dict(chemistry=('bound_fraction', 'intra', 'inter', 'L1', 'L2'),
                  shape=('mean_rg2', 'mean_center_terminal_r2'),
                  network=('largest_cluster_fraction', 'isolated_stars', 'satellite_stars',
                           'mean_degree', 'second_degree_moment'),
                  late=('intra', 'inter', 'mean_degree', 'L1', 'L2', 'mean_rg2'),
                  multiplicity=('edges_m1', 'edges_m2', 'edges_m3', 'edges_m4'))
    histories = []
    for replica in (1, 2, 3):
        with (directory / f'r{replica:03d}_frames.csv').open() as stream:
            histories.append([{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)])
    write_correlations(histories, directory)
    write_isolation(directory, histories)
    for label, names in groups.items():
        target = directory / (label + '.png')
        review.joint.require(not target.exists(), 'immutable figure already exists')
        figure, axes = plt.subplots(len(names), 1, figsize=(10, 2.1 * len(names)), sharex=True)
        for axis, name in zip(axes, names):
            for replica, rows in enumerate(histories, 1):
                line, = axis.plot([r['step'] / 1e6 for r in rows if label != 'late' or r['step'] >= 8000000],
                                  [r[name] for r in rows if label != 'late' or r['step'] >= 8000000],
                                  alpha=.18, linewidth=.5)
                width = 250000 if label == 'late' else 500000
                boundaries = range(8000000 if label == 'late' else 0, 16000000, width)
                means = [statistics.mean(r[name] for r in rows if a < r['step'] <= a + width)
                         for a in boundaries]
                axis.plot([a / 1e6 + width / 2e6 for a in boundaries], means,
                          'o-', color=line.get_color(), label=f'r{replica:03d}: {width // 1000}k mean')
            if label != 'late':
                axis.axvspan(0, 1, color='gray', alpha=.1)
            axis.set_ylabel(name)
            axis.legend(fontsize=7)
        axes[-1].set_xlabel('Absolute MD step / million; continuous MD stream; shaded: preparation context')
        figure.tight_layout()
        figure.savefig(target, dpi=130)
        plt.close(figure)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
