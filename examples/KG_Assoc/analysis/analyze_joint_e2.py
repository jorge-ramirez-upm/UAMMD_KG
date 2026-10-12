#!/usr/bin/env python3
"""Read-only paired, correlation-aware review across authenticated E2 segments."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'campaign'))
import kg_assoc_e2 as runner
import analyze_e2_segment as segment

require = runner.require
campaign = runner.campaign


def authenticate(root, attempts):
    segments = []
    for attempt in attempts:
        attempt = runner.inside(root, attempt)
        plan = runner.check_plan(root, attempt)
        require(plan['smoke'] is False, 'smokes are not equilibrium histories')
        runner.approval_record(attempt / 'approval.json', attempt / 'plan.json', 'e2_segment')
        runner.check_hashes(runner.scientific_source_hashes(plan['source_sha256']))
        runner.check_hashes(plan['executable_sha256'])
        if plan.get('build'):
            runner.check_hashes(plan['build']['executable_sha256'])
            runner.check_hashes(plan['build']['build_log_sha256'])
        histories = []
        for entry in plan['histories']:
            receipt_path = Path(entry['output_prefix']).parent / 'complete.json'
            receipt = campaign.load_json(receipt_path)
            require(receipt['status'] == 'validated' and receipt['plan_sha256'] ==
                    campaign.sha256(attempt / 'plan.json') and receipt['end_step'] == entry['end_step'],
                    'completion identity differs')
            runner.check_hashes(receipt['output_sha256'])
            rows, events, result = runner.validation.validate(entry)
            histories.append(dict(entry=entry, rows=rows, events=events, validation=result))
        segments.append(dict(attempt=str(attempt), plan=plan, histories=histories))
    return segments


def check_lineage(segments):
    require(segments, 'no segments')
    for source in segments:
        require(source['plan']['smoke'] is False and
                [h['entry']['replica'] for h in source['histories']] == [1, 2, 3],
                'three ordinary independent histories required')
    segments = sorted(segments, key=lambda s: s['histories'][0]['entry']['start_step'])
    require(all(h['entry']['start_step'] == 0 for h in segments[0]['histories']),
            'joint checkpoint must include the histories from absolute step zero')
    for previous, current in zip(segments, segments[1:]):
        require(current['plan']['parent_attempt'] == previous['attempt'] and
                current['plan']['system'] == previous['plan']['system'], 'unrelated segment lineage')
        for old, new in zip(previous['histories'], current['histories']):
            a, b = old['entry'], new['entry']
            require(a['replica'] == b['replica'] and a['end_step'] == b['start_step'] and
                    a['chemistry_seed'] == b['chemistry_seed'] and a['physics'] == b['physics'] and
                    a['md_seed'] != b['md_seed'] and a['effective_md_seed'] != b['effective_md_seed'] and
                    b['parent']['prefix'] == a['output_prefix'], 'step/physics/seed/parent transition differs')
            for key in ('free', 'bonds', 'intra', 'inter', 'L1', 'L2', 'components', 'largest_size', 'creations', 'breaks'):
                require(old['rows'][-1][key] == new['rows'][0][key], 'boundary state mismatch: ' + key)
    return segments


def compare(records, category, name, early, late):
    changes = [r['windows'][late][category][name]['mean'] -
               r['windows'][early][category][name]['mean'] for r in records]
    statistics = segment.review.analysis.dynamics.replica_statistics(changes)
    return dict(category=category, observable=name, early_window=early, late_window=late,
                per_replica_changes=changes, **statistics,
                excludes_zero=abs(statistics['mean']) > statistics['ci95_half_width'])


def summarize(segments, window_steps=1000000):
    segments = check_lineage(segments)
    records = []
    for index, replica in enumerate((1, 2, 3)):
        windows = []
        for source in segments:
            history = source['histories'][index]
            entry = history['entry']
            require(entry['replica'] == replica and (entry['end_step'] - entry['start_step']) % window_steps == 0,
                    'window/replica coverage mismatch')
            for start in range(entry['start_step'], entry['end_step'], window_steps):
                window = segment.review.window(history['rows'], history['events'], start, start + window_steps,
                    stickers=entry['system']['f'] * entry['system']['number_of_stars'],
                    dt=entry['physics']['dt'], stars=entry['system']['number_of_stars'], metrics=segment.METRICS)
                window['segment'] = source['attempt']
                for category in ('metrics', 'activity'):
                    for metric in window[category].values():
                        constant = len(set(metric['blocks'])) == 1 and metric['sem_estimate'] == 0
                        metric['constant_not_mixing_evidence'] = constant
                        metric['resolution_warning'] |= constant or metric['effective_samples_estimate'] < 10
                windows.append(window)
        records.append(dict(replica=replica, windows=windows))
    count = len(records[0]['windows'])
    require(count == 4, 'joint checkpoint requires exactly four analysis windows')
    comparisons = []
    ensembles = []
    for category in ('metrics', 'activity'):
        for name in records[0]['windows'][0][category]:
            for early, late in ((1, count - 1), (count - 2, count - 1), (1, count - 2)):
                comparisons.append(compare(records, category, name, early, late))
            for index in range(count):
                means = [r['windows'][index][category][name]['mean'] for r in records]
                ensembles.append(dict(category=category, observable=name, window=index,
                    **segment.review.analysis.dynamics.replica_statistics(means)))
    long_windows = []
    for index, replica in enumerate((1, 2, 3)):
        history = segments[-1]['histories'][index]
        entry = history['entry']
        long_windows.append(dict(replica=replica, window=segment.review.window(
            history['rows'], history['events'], entry['start_step'], entry['end_step'],
            stickers=entry['system']['f'] * entry['system']['number_of_stars'], dt=entry['physics']['dt'],
            stars=entry['system']['number_of_stars'], metrics=segment.METRICS)))
    return dict(schema_version=1, system=segments[-1]['plan']['system'], records=records,
                late_segment_long_windows=long_windows,
                comparisons=comparisons, ensembles=ensembles, automatic_acceptance=False,
                scientific_status='review_required', windows_steps=window_steps,
                transient='first window retained as transient context, not a stationary comparator',
                boundary_policy='no window or IAT crosses an independently reseeded segment boundary',
                independent_units='three histories; paired differences, Student-t df=2',
                qualification='Slow topology is not proven fully decorrelated; initialization only, no production authorization')


def write_report(summary, output):
    output.mkdir(parents=True, exist_ok=False)
    runner.exclusive_json(output / 'summary.json', summary)
    lines = ['# Joint E2 review', '', 'Read-only analysis; no MD and no automatic scientific acceptance.',
             f"Three independent histories; {summary['windows_steps']}-step windows; first window includes the unbound transient.",
             'IAT and 5/10/20-block sensitivity use existing validated analysis helpers.',
             'No correlations, lifetimes or transport histories are stitched across MD reseeding.', '',
             '| Observable | 1–2M mean | 2–3M mean | 3–4M mean | 3–4M minus 1–2M (95% half-width) | Late minus previous |',
             '|---|---:|---:|---:|---:|---:|']
    for category in ('metrics', 'activity'):
        names = summary['records'][0]['windows'][1][category]
        for name in names:
            means = [next(e for e in summary['ensembles'] if e['category'] == category and
                          e['observable'] == name and e['window'] == i)['mean'] for i in (1, 2, 3)]
            changes = [next(c for c in summary['comparisons'] if c['category'] == category and
                            c['observable'] == name and c['early_window'] == i and c['late_window'] == 3)
                       for i in (1, 2)]
            lines.append('| ' + name + ' | ' + ' | '.join(f'{m:.7g}' for m in means) + ' | ' +
                         ' | '.join(f"{c['mean']:.7g} ± {c['ci95_half_width']:.7g}" for c in changes) + ' |')
    lines += ['', 'Intervals are exploratory, unadjusted for multiple observables. Excluding zero is a review flag,',
              'not an automatic accept/reject rule. A wide interval is not proof of stationarity.',
              'Inspect per-history trends, IAT resolution, block sensitivity and effect sizes in [summary.json](summary.json).',
              'Slow topology is not proven fully decorrelated. Any acceptance is for production initialization only.', '']
    (output / 'REPORT.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', required=True, type=Path)
    parser.add_argument('--attempt', required=True, nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    results = authenticate(args.dataset_root.resolve(), [p.resolve() for p in args.attempt])
    output = args.output.resolve()
    write_report(summarize(results), output)
    sources = {}
    for result in results:
        attempt = Path(result['attempt'])
        sources.update(runner.hash_files([attempt / 'plan.json', attempt / 'approval.json'] +
            [attempt / f'r{r:03d}/complete.json' for r in (1, 2, 3)]))
    runner.exclusive_json(output / 'analysis_config.json', dict(schema_version=1,
        analyzer_git_sha=campaign.git_sha(), analyzer_sha256=campaign.sha256(Path(__file__)),
        source_sha256=sources, attempts=[s['attempt'] for s in results], window_steps=1000000,
        scope='full_payload_event_network_conformation_authentication',
        md_boundary_policy='no_across_boundary_IAT_or_lifetimes'))


if __name__ == '__main__':
    main()
