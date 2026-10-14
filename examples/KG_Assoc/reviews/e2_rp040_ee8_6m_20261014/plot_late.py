#!/usr/bin/env python3
"""Plot authenticated exported frames, preserving the full-transient figures."""
import csv
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(directory):
    directory = Path(directory)
    destination = directory / 'late_paths.png'
    if destination.exists():
        raise ValueError('immutable figure already exists')
    names = ('mean_rg2', 'mean_center_terminal_r2', 'intra', 'inter', 'L1',
             'largest_cluster_fraction', 'isolated_stars', 'satellite_stars')
    fig, axes = plt.subplots(len(names), 1, figsize=(10, 18), sharex=True)
    for replica in (1, 2, 3):
        with (directory / f'r{replica:03d}_frames.csv').open() as stream:
            rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(stream)]
        if [int(r['step']) for r in rows] != list(range(0, 6000001, 1000)):
            raise ValueError('incomplete replica coverage')
        selected = [r for r in rows if r['step'] >= 1000000]
        for axis, name in zip(axes, names):
            line, = axis.plot([r['step'] / 1e6 for r in selected], [r[name] for r in selected],
                              alpha=.17, linewidth=.5)
            means = [statistics.mean(r[name] for r in rows if start < r['step'] <= start + 500000)
                     for start in range(1000000, 6000000, 500000)]
            axis.plot([1.25 + .5 * i for i in range(10)], means, 'o-',
                      color=line.get_color(), label=f'r{replica:03d}: 500k mean')
            axis.set_ylabel(name)
    for axis in axes:
        axis.legend(fontsize=7, loc='best')
    axes[-1].set_xlabel('Absolute MD step / million; initial 0–1M remains in full figures')
    fig.tight_layout()
    fig.savefig(destination, dpi=140)
    plt.close(fig)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    main(parser.parse_args().directory)
