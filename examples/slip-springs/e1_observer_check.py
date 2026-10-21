#!/usr/bin/env python3
"""Bounded-memory structural and snapshot check; not Stage D scientific acceptance."""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


FILES = ('backbone', 'tangents', 'sites', 'connectors', 'chains', 'events', 'positions', 'attachments')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=3e-12, atol=3e-12)


class Rows:
    def __init__(self, path):
        self.file = path.open()
        self.rows = csv.DictReader(self.file)
        self.pending = next(self.rows, None)

    def pop(self):
        row = self.pending
        self.pending = next(self.rows, None)
        return row

    def seek(self, step):
        while self.pending is not None and int(self.pending['step']) < step:
            self.pop()

    def take(self, count, step, dt):
        result = []
        for _ in range(count):
            row = self.pop()
            require(row is not None, 'truncated observer frame')
            require(all(value is not None for value in row.values()) and None not in row,
                    'malformed CSV row')
            require(all(math.isfinite(float(v)) for v in row.values()), 'nonfinite diagnostic')
            require(row['step'] == str(step) and float(row['time']) == step * dt,
                    'inconsistent integer step/time')
            result.append(row)
        return result

    def finish(self):
        require(self.pending is None, 'unexpected extra observer row')


def verify(root):
    root = Path(root)
    complete = json.loads((root / 'equilibrium_complete.json').read_text())
    schema = json.loads((root / 'equilibrium_schema.json').read_text())
    require(complete['version'] == schema['version'] == 1 and complete['complete'] is True,
            'unsupported/incomplete observer schema')
    expected = {f'equilibrium_{kind}.csv' for kind in FILES} | {
        'equilibrium_schema.json', 'initial.csv', 'final.csv', 'metadata.json',
        'samples.csv', 'bond_statistics.csv', 'initial_bonds.csv'}
    optional = {'fixed_slip_springs.csv', 'slip_springs_initial.csv', 'slip_springs_final.csv', 'hopping_metadata.json'}
    require(expected <= set(complete['files']) <= expected | optional, 'incomplete file manifest')
    for name, size in complete['files'].items():
        require((root / name).stat().st_size == size, f'truncated/changed file: {name}')
    nframes, m, chains, z, dt, end = (schema[k] for k in (
        'expected_frames', 'beads_per_chain', 'chains', 'slip_count', 'dt', 'steps'))
    require(nframes == complete['frames'] and nframes >= 1, 'incomplete frame count')
    snapshots = schema['snapshot_steps']
    require(1 <= len(snapshots) <= 8 and snapshots[0] == 0 and snapshots[-1] == end
            and snapshots == sorted(set(snapshots)), 'invalid snapshot schedule')
    readers = {}
    try:
        readers = {kind: Rows(root / f'equilibrium_{kind}.csv') for kind in FILES}
        readers['samples'] = Rows(root / 'samples.csv')
        columns = {
            'backbone': 'step,time,chain,mean_r,mean_r2,re2,rg2,min_length' + ''.join(f',tangent{s}' for s in range(1,min(4,m-2)+1)),
            'tangents': 'step,time,chain' + ''.join(f',tangent{s}' for s in (8,16) if s<m-1),
            'sites': 'step,time,chain,bead,spring',
            'connectors': 'step,time,spring,chain,bead,ex,ey,ez,e2',
            'chains': 'step,time,chain,z,ex_sum,ey_sum,ez_sum,e2_sum',
            'events': 'step,time,previous_step,interval_time,batches,attempts,accepted,boundary,occupied,metropolis,renewal_proposed,renewal_accepted,renewal_occupied,renewal_same_chain,renewal_cross_chain',
            'positions': 'step,time,chain,bead,x,y,z',
            'attachments': 'step,time,spring,chain,bead,ax,ay,az,previous,next',
        }
        for kind, names in columns.items():
            require(readers[kind].rows.fieldnames == names.split(','), f'invalid {kind} schema')
        require(set(columns['backbone'].split(',')) <= set(readers['samples'].rows.fieldnames), 'incomplete legacy scalar schema')
        previous, totals, seen_snapshots = 0, {}, []
        for frame in range(nframes):
            ev = readers['events'].pop()
            require(ev is not None, 'missing event frame')
            step = int(ev['step'])
            require(ev['step'] == str(step) and (step == 0 if frame == 0 else step > previous)
                    and step <= end, 'invalid observer step sequence')
            require(float(ev['time']) == step * dt and int(ev['previous_step']) == previous
                    and float(ev['interval_time']) == (step - previous) * dt, 'invalid event interval')
            require(all(math.isfinite(float(v)) for v in ev.values()), 'nonfinite event record')
            counts = {k: int(v) for k, v in ev.items() if k not in ('step', 'time', 'previous_step', 'interval_time')}
            require(all(str(v) == ev[k] and v >= 0 for k, v in counts.items()), 'invalid counter')
            require(counts['attempts'] == sum(counts[k] for k in ('accepted', 'boundary', 'occupied', 'metropolis')),
                    'attempt counter identity')
            require(counts['renewal_proposed'] == counts['renewal_accepted'] + counts['renewal_occupied']
                    and counts['renewal_accepted'] == counts['renewal_same_chain'] + counts['renewal_cross_chain'],
                    'renewal counter identity')
            require(counts['batches'] <= step-previous, 'too many interval batches')
            require(counts['renewal_proposed'] == (counts['boundary'] if schema['canonical'] else 0),
                    'boundary counter semantics')
            if frame == 0:
                require(not any(counts.values()), 'nonzero initial interval')
            for k, v in counts.items():
                totals[k] = totals.get(k, 0) + v
            rows = {kind: readers[kind].take(count, step, dt) for kind, count in (
                ('sites', chains*m), ('connectors', z), ('chains', chains))}
            readers['samples'].seek(step)
            source = 'samples' if step % schema['legacy_sample_stride'] == 0 else 'backbone'
            rows['backbone'] = readers[source].take(chains, step, dt)
            long_rows = readers['tangents'].take(chains if m-1 > 8 else 0, step, dt)
            for kind in ('backbone', 'chains'):
                require([int(r['chain']) for r in rows[kind]] == list(range(chains)), 'chain row ordering')
            site_ids = []
            for i, r in enumerate(rows['sites']):
                require(int(r['chain']) == i//m and int(r['bead']) == i % m, 'site row ordering')
                site_ids.append(int(r['spring']))
            require(sorted(j for j in site_ids if j >= 0) == list(range(z))
                    and all(j >= -1 for j in site_ids), 'single occupancy/identity violation')
            connector = np.zeros((z, 3)); e2 = np.zeros(z); hosts = np.zeros(z, dtype=int)
            for j, r in enumerate(rows['connectors']):
                c, b = int(r['chain']), int(r['bead'])
                require(int(r['spring']) == j and 0 <= c < chains and 0 <= b < m
                        and site_ids[c*m+b] == j, 'connector/site mismatch')
                connector[j] = [float(r[k]) for k in ('ex', 'ey', 'ez')]
                e2[j] = float(r['e2']); hosts[j] = c
            close(e2, np.sum(connector**2, axis=1))
            populations = np.bincount(hosts, minlength=chains)
            require(sum(populations) == z, 'global population mismatch')
            for c, r in enumerate(rows['chains']):
                require(int(r['z']) == populations[c], 'chain population mismatch')
                close([float(r[k]) for k in ('ex_sum', 'ey_sum', 'ez_sum')], connector[hosts == c].sum(axis=0))
                close(float(r['e2_sum']), e2[hosts == c].sum())
            if step in snapshots:
                seen_snapshots.append(step)
                posrows = readers['positions'].take(chains*m, step, dt)
                arows = readers['attachments'].take(z, step, dt)
                require([(int(r['chain']), int(r['bead'])) for r in posrows] ==
                        [(i//m, i % m) for i in range(chains*m)], 'snapshot position order')
                r = np.array([[float(row[k]) for k in ('x', 'y', 'z')] for row in posrows]).reshape(chains, m, 3)
                for j, a in enumerate(arows):
                    c, b = int(a['chain']), int(a['bead'])
                    require(int(a['spring']) == j and 0 <= c < chains and 0 <= b < m
                            and site_ids[c*m+b] == j, 'snapshot attachment identity')
                    close(connector[j], r[c, b] - [float(a[k]) for k in ('ax', 'ay', 'az')])
                    chain_ids = [i for i in site_ids[c*m:(c+1)*m] if i >= 0]
                    index = chain_ids.index(j)
                    require(int(a['previous']) == (chain_ids[index-1] if index else -1)
                            and int(a['next']) == (chain_ids[index+1] if index+1 < len(chain_ids) else -1),
                            'snapshot contour links')
                q = np.diff(r, axis=1); length = np.linalg.norm(q, axis=2)
                require(np.all(length > 0), 'undefined snapshot tangent')
                tangent = q / length[:, :, None]
                for c, row in enumerate(rows['backbone']):
                    relative = r[c] - r[c, 0]
                    close([float(row[k]) for k in ('mean_r', 'mean_r2', 're2', 'rg2', 'min_length')],
                          [length[c].mean(), (length[c]**2).mean(), np.sum(relative[-1]**2),
                           np.mean(np.sum((relative-relative.mean(axis=0))**2, axis=1)), length[c].min()])
                    tangent_row = dict(row)
                    if long_rows:
                        require(int(long_rows[c]['chain']) == c, 'long tangent chain ordering')
                        tangent_row.update(long_rows[c])
                    for key in tangent_row:
                        if key.startswith('tangent'):
                            s = int(key[7:]); close(float(tangent_row[key]), np.mean(np.sum(tangent[c, :-s]*tangent[c, s:], axis=1)))
                # The paired snapshots reconstruct the same D0 joint numerators:
                # sum_c Re2_c*(Zc-Z/M) and sum_c Re2_c*(E2c-Zc*A2).
                # Target Re2/A2 and sigma_Z are supplied by future approved analysis.
            previous = step
        require(previous == end and seen_snapshots == snapshots, 'missing final frame/snapshot')
        for reader in readers.values():
            reader.finish()
        return {'frames': nframes, 'snapshots': len(snapshots), 'totals': totals}
    finally:
        for reader in readers.values():
            reader.file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.directory), sort_keys=True))
    except (OSError, ValueError, KeyError, AssertionError) as error:
        parser.exit(1, f'invalid E1 observer output: {error}\n')
