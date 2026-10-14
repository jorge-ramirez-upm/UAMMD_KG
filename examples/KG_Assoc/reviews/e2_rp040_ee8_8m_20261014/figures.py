#!/usr/bin/env python3
"""Full-context and late plots from authenticated joint frame exports."""
import argparse
import csv
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(directory):
    directory = Path(directory)
    paths = []
    for replica in (1, 2, 3):
        with (directory / f'r{replica:03d}_frames.csv').open() as stream:
            rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(stream)]
        if [int(r['step']) for r in rows] != list(range(0, 8000001, 1000)):
            raise ValueError('incomplete 0–8M context')
        paths.append(rows)
    groups = dict(chemistry=('bound_fraction', 'intra', 'inter', 'L1', 'L2', 'mean_degree'),
        shape=('mean_rg2', 'mean_center_terminal_r2'),
        periphery=('largest_cluster_fraction', 'components', 'isolated_stars',
                   'satellite_components', 'satellite_stars', 'second_degree_moment'),
        multiplicity=('edges_m1', 'edges_m2', 'edges_m3', 'edges_m4',
                      'stars_intra_loops_1', 'stars_intra_loops_2'),
        late=('L1', 'L2', 'mean_rg2', 'mean_center_terminal_r2', 'intra', 'inter',
              'largest_cluster_fraction'))
    for label, names in groups.items():
        destination = directory / (label + '.png')
        if destination.exists():
            raise ValueError('immutable figure already exists')
        fig, axes = plt.subplots(len(names), 1, figsize=(10, 2.2 * len(names)), sharex=True)
        start = 1000000 if label == 'late' else 0
        for axis, name in zip(axes, names):
            for replica, rows in enumerate(paths, 1):
                chosen = [r for r in rows if r['step'] >= start]
                line, = axis.plot([r['step'] / 1e6 for r in chosen], [r[name] for r in chosen],
                                  alpha=.2, linewidth=.5)
                means = [statistics.mean(r[name] for r in rows if a < r['step'] <= a + 500000)
                         for a in range(start, 8000000, 500000)]
                axis.plot([a / 1e6 + .25 for a in range(start, 8000000, 500000)], means,
                          'o-', color=line.get_color(), label=f'r{replica:03d}: 500k mean')
            axis.axvline(6, linestyle='--', color='black', alpha=.5)
            if start == 0:
                axis.axvspan(0, 1, color='gray', alpha=.1)
            axis.set_ylabel(name)
            axis.legend(fontsize=7, loc='best')
        axes[-1].set_xlabel('Absolute MD step / million; dashed: new MD stream at 6M')
        fig.tight_layout()
        fig.savefig(destination, dpi=140)
        plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
