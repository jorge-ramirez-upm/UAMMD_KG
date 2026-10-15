#!/usr/bin/env python3
"""Exclusive tables and full-context plots from authenticated CPU review evidence."""
import argparse
import csv
import math
from pathlib import Path
import statistics

import reproduce_ee10 as review

NAMES = ('bound_fraction', 'intra', 'inter', 'L1', 'L2', 'mean_rg2',
         'mean_center_terminal_r2', 'largest_cluster_fraction', 'isolated_stars',
         'satellite_stars', 'mean_degree', 'second_degree_moment')


def main(directory):
    summary_path = directory / 'summary.json'
    summary = review.joint.campaign.load_json(summary_path)
    review.joint.require(summary['system']['system_id'] == review.SYSTEM, 'wrong system')
    destination = directory / 'WINDOWS.md'
    review.joint.require(not destination.exists(), 'immutable table already exists')
    lines = ['# Complete nonoverlapping context', '',
             'Means across three histories. Initial windows are retained preparation context.',
             'Unadjusted Student-t df=2 intervals below are descriptive, not stationarity tests.', '']
    for width in (500000, 1000000, 2000000):
        lines += [f'## {width:,}-step windows', '', '| Steps (M) | ' + ' | '.join(NAMES) + ' |',
                  '|---|' + '---:|' * len(NAMES)]
        for start in range(0, 8000000, width):
            windows = [next(w for w in r['windows'] if
                           (w['start_step_exclusive'], w['end_step_inclusive']) ==
                           (start, start + width)) for r in summary['records']]
            values = [statistics.mean(w['metrics'][name]['mean'] for w in windows) for name in NAMES]
            lines.append(f'| {start / 1e6:g}–{(start + width) / 1e6:g} | ' +
                         ' | '.join(f'{v:.7g}' for v in values) + ' |')
        lines.append('')
    lines += ['## Paired 4–6M → 6–8M changes', '',
              '| Observable | r001 | r002 | r003 | Mean ± 95% half-width |',
              '|---|---:|---:|---:|---:|']
    for contrast in summary['comparisons']:
        if contrast['early_steps'] != [4000000, 6000000] or contrast['late_steps'] != [6000000, 8000000]:
            continue
        lines.append('| ' + contrast['observable'] + ' | ' +
                     ' | '.join(f'{v:.7g}' for v in contrast['per_replica_changes']) +
                     f" | {contrast['mean']:.7g} ± {contrast['ci95_half_width']:.7g} |")
    with destination.open('x') as stream:
        stream.write('\n'.join(lines) + '\n')
    authentication = review.joint.campaign.load_json(Path(__file__).parent / 'AUTHENTICATION.json')
    reference = authentication['reference_record']
    compared = []
    sources = [summary_path, Path(__file__), Path(__file__).parent / 'AUTHENTICATION.json']
    for history, cached in zip(reference['record']['histories'], authentication['reference_windows']):
        review.joint.runner.check_hashes(history['sha256'])
        state = Path(history['prefix'] + '.state')
        _, rows = review.joint.segment.review.analysis.stationarity.read_state(state)
        selected = [r for r in rows if 6000000 < r['step'] <= 8000000]
        windows = cached['windows']
        review.joint.require(len(selected) == 2000 and
            [(w['start_step_exclusive'], w['end_step_inclusive']) for w in windows] ==
            [(a, a + 500000) for a in range(6000000, 8000000, 500000)],
            'qualified corrected Ee8 coverage differs')
        metrics = {name: statistics.mean(r[name] for r in selected) for name in NAMES
                   if name in selected[0]}
        for name, mean in metrics.items():
            if name in windows[0]['metrics']:
                review.joint.require(math.isclose(mean, statistics.mean(
                    w['metrics'][name]['mean'] for w in windows), rel_tol=1e-12, abs_tol=1e-12),
                    'frozen reference means differ from qualified raw state')
        counts = {name: sum(w['event_counts'][name] for w in windows)
                  for name in windows[0]['event_counts']}
        exposure = {name: sum(w['exposure'][name] for w in windows)
                    for name in windows[0]['exposure']}
        rates = {name: count / 20000 for name, count in counts.items()}
        for name in ('creations', 'breaks'):
            review.joint.require(counts[name] == rows[-1][name] - rows[0][name],
                                 'reference accepted-event counters differ')
        compared.append(dict(replica=history['replica'], metrics=metrics, activity=rates,
            event_counts=counts, exposure=exposure,
            population_normalized_rates=dict(
                creation_events_per_free_sticker_time=counts['creations'] / exposure['free_sticker_time'],
                rupture_events_per_active_bond_time=counts['breaks'] / exposure['active_bond_time'])))
        sources.append(state)
    review.joint.runner.exclusive_json(directory / 'EE8_COMPARISON.json', dict(
        system='F04_N010_RP080_EE08_EA04', interval=[6000000, 8000000],
        independent_units='three histories per Ee; no between-Ee pairing', records=compared,
        reference_record_sha256=reference['sha256'],
        scope='only qualified corrected Ee8; never defective historical windows',
        limitations='Ee8 neighbor counts/exposures reuse frozen authenticated corrected review; no fresh Ee8 graph replay',
        source_sha256=review.joint.runner.hash_files(sources)))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    groups = dict(chemistry=('bound_fraction', 'intra', 'inter', 'L1', 'L2'),
                  shape=('mean_rg2', 'mean_center_terminal_r2'),
                  network=('largest_cluster_fraction', 'isolated_stars', 'satellite_stars',
                           'mean_degree', 'second_degree_moment'),
                  late=('intra', 'L1', 'L2', 'largest_cluster_fraction', 'mean_rg2'),
                  multiplicity=('edges_m1', 'edges_m2', 'edges_m3', 'edges_m4'))
    histories = []
    for replica in (1, 2, 3):
        with (directory / f'r{replica:03d}_frames.csv').open() as stream:
            histories.append([{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)])
    for label, names in groups.items():
        target = directory / (label + '.png')
        review.joint.require(not target.exists(), 'immutable figure already exists')
        figure, axes = plt.subplots(len(names), 1, figsize=(10, 2.1 * len(names)), sharex=True)
        for axis, name in zip(axes, names):
            for replica, rows in enumerate(histories, 1):
                line, = axis.plot([r['step'] / 1e6 for r in rows if label != 'late' or r['step'] >= 6000000],
                                  [r[name] for r in rows if label != 'late' or r['step'] >= 6000000],
                                  alpha=.18, linewidth=.5)
                width = 250000 if label == 'late' else 500000
                boundaries = range(6000000 if label == 'late' else 0, 8000000, width)
                means = [statistics.mean(r[name] for r in rows if a < r['step'] <= a + width)
                         for a in boundaries]
                axis.plot([a / 1e6 + width / 2e6 for a in boundaries], means,
                          'o-', color=line.get_color(), label=f'r{replica:03d}: {width // 1000}k mean')
            if label != 'late':
                axis.axvspan(0, 1, color='gray', alpha=.1)
            axis.set_ylabel(name)
            axis.legend(fontsize=7)
        axes[-1].set_xlabel('Absolute MD step / million; shaded: initial chemical transient context')
        figure.tight_layout()
        figure.savefig(target, dpi=130)
        plt.close(figure)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
