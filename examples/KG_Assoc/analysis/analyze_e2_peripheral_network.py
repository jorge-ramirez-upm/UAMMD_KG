#!/usr/bin/env python3
"""Paired peripheral-network means from authenticated joint and degree summaries."""
import argparse
from pathlib import Path
import analyze_e2_window_sensitivity as sensitivity

joint = sensitivity.joint


def summarize(summary, degrees):
    joint.require([r['replica'] for r in summary['records']] == [1, 2, 3] and
                  [r['replica'] for r in degrees['records']] == [1, 2, 3], 'replica coverage differs')
    stars = summary['system']['number_of_stars']
    records = []
    for history, degree in zip(summary['records'], degrees['records']):
        windows = []
        joint.require(len(history['windows']) == len(degree['windows']), 'window coverage differs')
        for w, d in zip(history['windows'], degree['windows']):
            joint.require(all(w[k] == d[k] for k in
                          ('start_step_exclusive', 'end_step_inclusive', 'segment')), 'window identities differ')
            if w['start_step_exclusive'] < summary['windows_steps']:
                continue
            isolated = stars * d['metrics']['degree_0_fraction']['mean']
            outside = stars * (1 - w['metrics']['largest_cluster_fraction']['mean'])
            satellites = w['metrics']['components']['mean'] - 1 - isolated
            satellite_stars = outside - isolated
            joint.require(satellites >= -1e-9 and satellite_stars >= -1e-9,
                          'nonisolated giant/peripheral identities inconsistent')
            windows.append(dict(start_step_exclusive=w['start_step_exclusive'],
                end_step_inclusive=w['end_step_inclusive'], segment=w['segment'], activity={},
                metrics={'isolated_stars': dict(mean=isolated), 'outside_giant_stars': dict(mean=outside),
                         'satellite_components': dict(mean=satellites),
                         'satellite_stars': dict(mean=satellite_stars)}))
        records.append(dict(replica=history['replica'], windows=windows))
    result = sensitivity.summarize(dict(records=records, windows_steps=summary['windows_steps']))
    result.update(stage='E2_peripheral_network_means', records=records,
        definitions='late giant is nonisolated; satellites = components - 1 - isolated; satellite stars = outside giant - isolated',
        limitation='derived observables are correlated; paired changes preserve covariance; no new IAT or combined-window SEM is imputed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--degrees', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = summarize(joint.campaign.load_json(args.summary), joint.campaign.load_json(args.degrees))
    result['source_sha256'] = joint.runner.hash_files([args.summary, args.degrees, Path(__file__)])
    joint.runner.exclusive_json(args.output, result)


if __name__ == '__main__':
    main()
