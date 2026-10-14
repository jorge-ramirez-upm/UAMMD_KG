#!/usr/bin/env python3
"""Late-window zoom supplement; original full-transient figures remain preserved."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent
names = ('largest_cluster_fraction', 'components', 'isolated_stars',
         'satellite_components', 'satellite_stars', 'mean_rg2', 'mean_center_terminal_r2')
output = base / 'late_paths.png'
assert not output.exists(), 'immutable figure already exists'
summary = json.loads((base / 'summary.json').read_text())
fig, axes = plt.subplots(len(names), 1, figsize=(11, 2.3 * len(names)), sharex=True)
for history in summary['records']:
    with (base / f"r{history['replica']:03d}_frames.csv").open() as stream:
        rows = [{key: float(value) for key, value in row.items()} for row in csv.DictReader(stream)]
    rows = [row for row in rows if row['step'] >= 1000000]
    assert len(rows) == 3001
    windows = [w for w in history['windows'] if w['start_step_exclusive'] >= 1000000]
    for axis, name in zip(axes, names):
        line, = axis.plot([row['step'] / 1e6 for row in rows], [row[name] for row in rows],
                          alpha=.25, linewidth=.5)
        axis.plot([(w['start_step_exclusive'] + 250000) / 1e6 for w in windows],
                  [w['metrics'][name]['mean'] for w in windows], 'o-',
                  color=line.get_color(), label=f"r{history['replica']:03d}: 500k mean")
        axis.set_ylabel(name)
        axis.legend(fontsize=7, loc='best')
axes[-1].set_xlabel('Absolute MD step / million; late zoom, full transient in companion figures')
fig.tight_layout()
fig.savefig(output, dpi=140)
plt.close(fig)
