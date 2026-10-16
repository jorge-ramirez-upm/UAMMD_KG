#!/usr/bin/env python3
"""Exclusive tables and full-context plots from authenticated CPU review evidence."""
import argparse
import csv
import collections
import math
from pathlib import Path
import statistics

import reproduce_ee12_20m as review
import sys
sys.path.insert(0, str(review.OLD_REVIEW))
import tabulate_ee12 as original_tables

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
        for start, end in ((12000000, 16000000), (16000000, 20000000),
                           (16000000, 18000000), (18000000, 20000000),
                           (19000000, 20000000)):
            review.joint.require(not start < 16000000 < end, 'correlation crosses MD reseeding')
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
    lines = ['# Replica-level complete 0–20M context', '',
             'Each width tiles the complete path. Step zero remains in frame exports.',
             'Early windows are preparation context, not certified stationary.', '']
    for width in review.WIDTHS:
        lines += [f'## {width:,}-step windows', '',
                  '| Replica | Steps (M) | ' + ' | '.join(NAMES) + ' |',
                  '|---|---|' + '---:|' * len(NAMES)]
        for record in summary['records']:
            for start in range(0, 20000000, width):
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
        if c['observable'] not in names or c['early_steps'][0] < 12000000:
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
            if (start, end) not in ((12000000, 16000000), (16000000, 20000000),
                    (16000000, 18000000), (18000000, 20000000), (19000000, 20000000)):
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
        for start in range(0, 20000000, 4000000):
            w = next(w for w in record['windows'] if
                (w['start_step_exclusive'], w['end_step_inclusive']) == (start, start + 4000000))
            lines.append(f"| r{record['replica']:03d} | {start/1e6:g}–{start/1e6+4:g} | " +
                ' | '.join(f"{w['metrics'][name]['mean']:.8g}" for name in names) + ' |')
    with (directory / 'NETWORK_DISTRIBUTIONS.md').open('x') as stream:
        stream.write('\n'.join(lines) + '\n')


def write_reference(directory, summary):
    original_tables.write_reference(directory, summary)


def write_isolation(directory, histories):
    provenance = review.joint.campaign.load_json(directory / 'provenance.json')
    records = []
    for index, frames in enumerate(histories):
        sources = provenance['source_authentication']
        first = sources[0]['histories'][index]['entry']
        system, initial = review.joint.runner.validation.read_parent(first)
        review.joint.require(not initial['pairs'], 'initial history must be chemically unbound')
        events = []
        for source in sources:
            entry = source['histories'][index]['entry']
            _, segment_events = review.joint.segment.review.analysis.dynamics.read_events(
                entry['output_prefix'] + '.events', system)
            events.extend(segment_events)
        spells = original_tables.isolation_spells(system['stars'], system['atom_to_star'], events, 20000000)
        intervals = []
        for start, end in ((12000000, 16000000), (16000000, 20000000),
                           (16000000, 18000000), (18000000, 20000000), (19000000, 20000000)):
            overlaps = [dict(spell, crosses_md_reseeding=spell['start'] < 16000000 < spell['end'],
                overlap_steps=max(0, min(end, spell['end']) - max(start, spell['start']))) for spell in spells]
            overlaps = [spell for spell in overlaps if spell['overlap_steps'] > 0]
            intervals.append(dict(start_step=start, end_step=end,
                time_averaged_isolated_stars=sum(spell['overlap_steps'] for spell in overlaps) / (end - start),
                unique_isolated_stars=sorted({spell['star'] for spell in overlaps}),
                continuously_isolated_stars=sorted(spell['star'] for spell in overlaps
                    if spell['start'] <= start and spell['end'] >= end), spells=overlaps))
        for frame in frames:
            step = int(frame['step'])
            isolated = sum(spell['start'] <= step < spell['end'] or
                           spell['right_censored'] and step == spell['end'] for spell in spells)
            review.joint.require(isolated == frame['isolated_stars'], 'isolation replay differs')
        records.append(dict(replica=index + 1, intervals=intervals))
    review.joint.runner.exclusive_json(directory / 'ISOLATION.json', dict(records=records,
        definitions='exact observed inter-bond degree-zero residence; chemical event identity is authenticated across 16M; crossing residence is labeled, not a stitched bond lifetime, IAT or stationary lifetime estimate'))


def satellite_topologies(directory, captured):
    """Replay inter-edge multiplicities and intra counts at rare peripheral samples."""
    provenance = review.joint.campaign.load_json(directory / 'provenance.json')
    records = []
    for index, record in enumerate(captured['records']):
        first = provenance['source_authentication'][0]['histories'][index]['entry']
        system, _ = review.joint.runner.validation.read_parent(first)
        events = []
        for source in provenance['source_authentication']:
            entry = source['histories'][index]['entry']
            _, segment_events = review.joint.segment.review.analysis.dynamics.read_events(
                entry['output_prefix'] + '.events', system)
            events.extend(segment_events)
        cursor = 0
        edges, intra = collections.Counter(), collections.Counter()
        observations = []
        for frame in record['frames']:
            while cursor < len(events) and events[cursor][0] <= frame['step']:
                _, kind, pair = events[cursor]
                stars = tuple(sorted(system['atom_to_star'][atom] for atom in pair))
                counter, key = (intra, stars[0]) if stars[0] == stars[1] else (edges, stars)
                counter[key] += 1 if kind == 'C' else -1
                review.joint.require(counter[key] >= 0, 'negative peripheral bond count')
                cursor += 1
            if frame['step'] < 12000000 or not frame['satellites']:
                continue
            for component in frame['satellites']:
                members = set(component)
                observations.append(dict(step=frame['step'], stars=component,
                    inter_edges=[list(pair) + [multiplicity] for pair, multiplicity in sorted(edges.items())
                                 if multiplicity and set(pair) <= members],
                    intra_loops={str(star): intra[star] for star in component}))
        records.append(dict(replica=index + 1, observations=observations))
    review.joint.runner.exclusive_json(directory / 'SATELLITE_TOPOLOGY.json', dict(records=records,
        scope='exact accepted-event edge/loop state at sampled satellite frames, from 12M onward'))


def write_satellite_episodes(directory, histories):
    captured = review.joint.campaign.load_json(directory / 'PERIPHERAL_FRAMES.json')
    satellite_topologies(directory, captured)
    records = []
    for record, frames in zip(captured['records'], histories):
        review.joint.require([r['step'] for r in record['frames']] == [r['step'] for r in frames],
                            'peripheral frame coverage differs')
        for row, values in zip(record['frames'], frames):
            review.joint.require(len(row['isolated']) == values['isolated_stars'] and
                len(row['satellites']) == values['satellite_components'] and
                sum(len(c) for c in row['satellites']) == values['satellite_stars'],
                'satellite identity/count mismatch')
        periods = []
        for start, end in ((12000000, 16000000), (16000000, 20000000),
                           (16000000, 18000000), (18000000, 20000000), (19000000, 20000000)):
            selected = [r for r in record['frames'] if start < r['step'] <= end]
            occurrences = {}
            for row in selected:
                for component in row['satellites']:
                    occurrences.setdefault(tuple(component), []).append(row['step'])
            episodes = []
            for stars, steps in sorted(occurrences.items()):
                runs = [[steps[0]]]
                for step in steps[1:]:
                    if step != runs[-1][-1] + 1000:
                        runs.append([])
                    runs[-1].append(step)
                episodes.extend(dict(stars=stars, first_sample=run[0], last_sample=run[-1],
                    samples=len(run), right_censored_at_interval_end=run[-1] == end,
                    observed_sample_span_steps=run[-1] - run[0]) for run in runs)
            periods.append(dict(start_step=start, end_step=end,
                sampled_mean_satellite_stars=sum(sum(len(c) for c in row['satellites'])
                                                 for row in selected) / len(selected),
                sampled_frames_with_satellites=sum(bool(row['satellites']) for row in selected),
                episodes=episodes))
        records.append(dict(replica=record['replica'], intervals=periods))
    review.joint.runner.exclusive_json(directory / 'SATELLITES.json', dict(records=records,
        scope='1000-step sampled identities and runs; transition times lie between frames; no exact satellite residence or lifetime distribution claimed'))


def write_periphery_table(directory):
    isolated = review.joint.campaign.load_json(directory / 'ISOLATION.json')
    satellites = review.joint.campaign.load_json(directory / 'SATELLITES.json')
    lines = ['# Isolated identities, observed residence and sampled satellite components', '',
        'Exact isolation residence uses the chemically continuous accepted-event history.',
        'Satellite identities are sampled every 1000 steps; no lifetime fit or IAT crosses 16M.', '',
        '| Replica | Interval (M) | Time-mean isolates | Continuously isolated IDs | Sample-mean satellite stars | Frames with satellites |',
        '|---|---|---:|---|---:|---:|']
    for a, b in zip(isolated['records'], satellites['records']):
        for isolation, satellite in zip(a['intervals'], b['intervals']):
            start, end = isolation['start_step'], isolation['end_step']
            lines.append(f"| r{a['replica']:03d} | {start/1e6:g}–{end/1e6:g} | " +
                f"{isolation['time_averaged_isolated_stars']:.8g} | " +
                ', '.join(map(str, isolation['continuously_isolated_stars'])) +
                f" | {satellite['sampled_mean_satellite_stars']:.8g} | " +
                f"{satellite['sampled_frames_with_satellites']} |")
    lines += ['', '## All observed isolation spells overlapping 18–20M', '',
              '| Replica | Star | First isolated step | Last step / censor | Crosses 16M |',
              '|---|---:|---:|---|---|']
    for record in isolated['records']:
        window = next(w for w in record['intervals'] if w['start_step'] == 18000000)
        for spell in window['spells']:
            lines.append(f"| r{record['replica']:03d} | {spell['star']} | {spell['start']} | " +
                f"{spell['end']} / {'right-censored' if spell['right_censored'] else 'observed exit'} | " +
                f"{spell['crosses_md_reseeding']} |")
    with (directory / 'PERIPHERY.md').open('x') as stream:
        stream.write('\n'.join(lines) + '\n')


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
        for start in range(0, 20000000, width):
            windows = [next(w for w in r['windows'] if
                           (w['start_step_exclusive'], w['end_step_inclusive']) ==
                           (start, start + width)) for r in summary['records']]
            values = [statistics.mean(w['metrics'][name]['mean'] for w in windows) for name in NAMES]
            lines.append(f'| {start / 1e6:g}–{(start + width) / 1e6:g} | ' +
                         ' | '.join(f'{v:.7g}' for v in values) + ' |')
        lines.append('')
    lines += ['## Paired 12–16M → 16–20M changes', '',
              '| Observable | r001 | r002 | r003 | Mean ± 95% half-width |',
              '|---|---:|---:|---:|---:|']
    for contrast in summary['comparisons']:
        if contrast['early_steps'] != [12000000, 16000000] or contrast['late_steps'] != [16000000, 20000000]:
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
                  late=('intra', 'inter', 'mean_degree', 'L1', 'L2', 'largest_cluster_fraction', 'mean_rg2'),
                  multiplicity=('edges_m1', 'edges_m2', 'edges_m3', 'edges_m4'))
    histories = []
    for replica in (1, 2, 3):
        with (directory / f'r{replica:03d}_frames.csv').open() as stream:
            histories.append([{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)])
    write_correlations(histories, directory)
    write_isolation(directory, histories)
    write_satellite_episodes(directory, histories)
    write_periphery_table(directory)
    for label, names in groups.items():
        target = directory / (label + '.png')
        review.joint.require(not target.exists(), 'immutable figure already exists')
        figure, axes = plt.subplots(len(names), 1, figsize=(10, 2.1 * len(names)), sharex=True)
        for axis, name in zip(axes, names):
            for replica, rows in enumerate(histories, 1):
                line, = axis.plot([r['step'] / 1e6 for r in rows if label != 'late' or r['step'] >= 12000000],
                                  [r[name] for r in rows if label != 'late' or r['step'] >= 12000000],
                                  alpha=.18, linewidth=.5)
                width = 250000 if label == 'late' else 500000
                boundaries = range(12000000 if label == 'late' else 0, 20000000, width)
                means = [statistics.mean(r[name] for r in rows if a < r['step'] <= a + width)
                         for a in boundaries]
                axis.plot([a / 1e6 + width / 2e6 for a in boundaries], means,
                          'o-', color=line.get_color(), label=f'r{replica:03d}: {width // 1000}k mean')
            if label != 'late':
                axis.axvspan(0, 1, color='gray', alpha=.1)
            axis.axvline(16, color='black', linestyle='--', alpha=.5)
            axis.set_ylabel(name)
            axis.legend(fontsize=7)
        axes[-1].set_xlabel('Absolute MD step / million; dashed: new MD stream at 16M; shaded: preparation context')
        figure.tight_layout()
        figure.savefig(target, dpi=130)
        plt.close(figure)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
