#!/usr/bin/env python3
"""Exclusive tables and full-context plots from authenticated CPU review evidence."""
import argparse
import csv
import math
from pathlib import Path
import statistics

import reproduce_ee10_12m as review

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
        for start, end in ((6000000, 8000000), (8000000, 10000000),
                           (10000000, 12000000), (8000000, 12000000),
                           (11000000, 12000000)):
            # Descriptive covariance is also kept inside an actual MD segment.
            review.joint.require(not start < 8000000 < end, 'correlation crosses reseeding')
            for width in (1000, 250000, 500000):
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
        for start in range(0, 12000000, width):
            windows = [next(w for w in r['windows'] if
                           (w['start_step_exclusive'], w['end_step_inclusive']) ==
                           (start, start + width)) for r in summary['records']]
            values = [statistics.mean(w['metrics'][name]['mean'] for w in windows) for name in NAMES]
            lines.append(f'| {start / 1e6:g}–{(start + width) / 1e6:g} | ' +
                         ' | '.join(f'{v:.7g}' for v in values) + ' |')
        lines.append('')
    lines += ['## Paired 8–10M → 10–12M changes', '',
              '| Observable | r001 | r002 | r003 | Mean ± 95% half-width |',
              '|---|---:|---:|---:|---:|']
    for contrast in summary['comparisons']:
        if contrast['early_steps'] != [8000000, 10000000] or contrast['late_steps'] != [10000000, 12000000]:
            continue
        lines.append('| ' + contrast['observable'] + ' | ' +
                     ' | '.join(f'{v:.7g}' for v in contrast['per_replica_changes']) +
                     f" | {contrast['mean']:.7g} ± {contrast['ci95_half_width']:.7g} |")
    with destination.open('x') as stream:
        stream.write('\n'.join(lines) + '\n')
    old_comparison = review.OLD_REVIEW / 'evidence/EE8_COMPARISON.json'
    reference = review.joint.campaign.load_json(old_comparison)
    review.joint.runner.check_hashes({str(review.OLD_REVIEW / n): h for n, h in
        review.joint.campaign.load_json(review.OLD_REVIEW / 'INTEGRITY.json')['sha256'].items()})
    review.joint.runner.exclusive_json(directory / 'EE8_COMPARISON.json', dict(reference,
        reused_reference_source=str(old_comparison),
        reused_reference_sha256=review.joint.campaign.sha256(old_comparison)))
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
    write_correlations(histories, directory)
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
                boundaries = range(8000000 if label == 'late' else 0, 12000000, width)
                means = [statistics.mean(r[name] for r in rows if a < r['step'] <= a + width)
                         for a in boundaries]
                axis.plot([a / 1e6 + width / 2e6 for a in boundaries], means,
                          'o-', color=line.get_color(), label=f'r{replica:03d}: {width // 1000}k mean')
            if label != 'late':
                axis.axvspan(0, 1, color='gray', alpha=.1)
            axis.axvline(8, color='black', linestyle='--', alpha=.5)
            axis.set_ylabel(name)
            axis.legend(fontsize=7)
        axes[-1].set_xlabel('Absolute MD step / million; dashed: new MD stream at 8M; shaded: preparation context')
        figure.tight_layout()
        figure.savefig(target, dpi=130)
        plt.close(figure)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
