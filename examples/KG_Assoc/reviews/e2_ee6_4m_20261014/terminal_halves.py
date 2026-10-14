#!/usr/bin/env python3
"""Read-only final 250k sensitivity from the authenticated compact frame exports."""
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'analysis'))
import analyze_e2_continuous4m_review as review


def main():
    base = Path(__file__).resolve().parent
    output = base / 'terminal_halves.json'
    review.joint.require(not output.exists(), 'immutable terminal sensitivity already exists')
    names = ('largest_cluster_fraction', 'components', 'isolated_stars',
             'satellite_components', 'satellite_stars') + review.continuous.SHAPES
    records = []
    sources = []
    for replica in (1, 2, 3):
        path = base / f'r{replica:03d}_frames.csv'
        sources.append(path)
        with path.open() as stream:
            rows = [{name: float(value) for name, value in row.items()}
                    for row in csv.DictReader(stream)]
        review.joint.require([r['step'] for r in rows] == list(range(0, 4000001, 1000)),
                             'complete 0–4M frame export required')
        for row in rows:
            fractions = [row[f'degree_{k}_fraction'] for k in range(5)]
            review.joint.require(abs(sum(fractions) - 1) < 1e-10 and
                abs(sum(k * x for k, x in enumerate(fractions)) - row['mean_degree']) < 1e-9 and
                abs(sum(k * k * x for k, x in enumerate(fractions)) -
                    row['second_degree_moment']) < 1e-9, 'degree identity differs')
            if row['step'] >= 1000000:
                review.joint.require(abs(row['components'] - 1 - row['isolated_stars'] -
                    row['satellite_components']) < 1e-9 and
                    abs(1000 * (1 - row['largest_cluster_fraction']) - row['isolated_stars'] -
                        row['satellite_stars']) < 1e-8, 'peripheral identity differs')
        windows = []
        for start, end in ((3500000, 3750000), (3750000, 4000000)):
            selected = [row for row in rows if start < row['step'] <= end]
            windows.append(dict(start_step_exclusive=start, end_step_inclusive=end,
                metrics={name: review.joint.segment.review.estimate(
                    [row[name] for row in selected], [row['time'] for row in selected])
                    for name in names}))
        records.append(dict(replica=replica, windows=windows))
    comparisons = [review.joint.compare(records, 'metrics', name, 0, 1) for name in names]
    review.joint.runner.exclusive_json(output, dict(records=records, comparisons=comparisons,
        automatic_acceptance=False, source_sha256=review.joint.runner.hash_files(sources +
            [Path(__file__)]), independent_units='three original histories; exploratory df=2',
        qualification='250k windows probe reversal only; low effective samples cannot prove mixing'))


if __name__ == '__main__':
    main()
