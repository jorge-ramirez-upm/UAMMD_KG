#!/usr/bin/env python3
"""Quick Matplotlib inspection plots for KG_Assoc analysis CSV files."""

import argparse
import csv
import json
import math
import tempfile
from pathlib import Path


COMPONENTS = ('Gxy', 'Gxz', 'Gyz', 'GNxy', 'GNxz', 'GNyz')

TOPOLOGY_METRICS = {
    'inter_bonds': 'Inter-star temporary bonds',
    'intra_bonds': 'Intra-star temporary bonds',
    'mean_k_bond': r'$\langle k_{\mathrm{bond}}\rangle$',
    'mean_k_neighbor': r'$\langle k_{\mathrm{neighbor}}\rangle$',
    'isolated_fraction': 'Isolated-star fraction',
    'largest_component_fraction': 'Largest-component fraction',
    'mean_edge_multiplicity': 'Mean edge multiplicity',
}
TOPOLOGY_DEFAULT_METRICS = (
    'inter_bonds',
    'mean_k_neighbor',
    'isolated_fraction',
    'largest_component_fraction',
)
TOPOLOGY_DISTRIBUTIONS = {
    'degree-neighbor': (
        'degree_neighbor', r'$k_{\mathrm{neighbor}}$', 'Neighbor-degree distribution'),
    'degree-bond': (
        'degree_bond', r'$k_{\mathrm{bond}}$', 'Bond-degree distribution'),
    'multiplicity': (
        'edge_multiplicity', 'Edge multiplicity $m$', 'Edge-multiplicity distribution'),
    'clusters': ('cluster_sizes', 'Cluster size (component-weighted)',
                 'Component-weighted cluster-size distribution'),
}


def read_csv(path, required):
    try:
        with open(path, newline='', encoding='utf-8') as input_file:
            reader = csv.DictReader(input_file)
            if reader.fieldnames is None:
                raise ValueError('missing CSV header')
            missing = set(required) - set(reader.fieldnames)
            if missing:
                raise ValueError('missing required columns: {}'.format(', '.join(sorted(missing))))
            rows = list(reader)
    except OSError as error:
        raise ValueError(str(error)) from error
    if not rows:
        raise ValueError('CSV has no data rows')
    return rows


def column(rows, name):
    try:
        return [float(row[name]) for row in rows]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('column {} must contain numeric values'.format(name)) from error


def pyplot(headless):
    import matplotlib

    if headless:
        matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    return plt


def save_or_show(plt, figures, output, no_show, dpi, output_suffixes=None):
    for figure in figures:
        figure.tight_layout()
    if output:
        if output_suffixes is None:
            output_suffixes = [''] + ['.alpha'] * (len(figures) - 1)
        if len(output_suffixes) != len(figures):
            raise ValueError('output suffix count does not match figure count')
        path = Path(output)
        for figure, suffix in zip(figures, output_suffixes):
            target = path.with_name(path.stem + suffix + path.suffix)
            figure.savefig(target, dpi=dpi)
    if not no_show:
        plt.show()
    for figure in figures:
        plt.close(figure)


def apply_limits(axis, arguments):
    if axis.get_xscale() == 'log' and ((arguments.xmin is not None and arguments.xmin <= 0.0) or
                                       (arguments.xmax is not None and arguments.xmax <= 0.0)):
        raise ValueError('log-axis x limits must be positive')
    if axis.get_yscale() == 'log' and ((arguments.ymin is not None and arguments.ymin <= 0.0) or
                                       (arguments.ymax is not None and arguments.ymax <= 0.0)):
        raise ValueError('log-axis y limits must be positive')
    if arguments.xmin is not None or arguments.xmax is not None:
        axis.set_xlim(left=arguments.xmin, right=arguments.xmax)
    if arguments.ymin is not None or arguments.ymax is not None:
        axis.set_ylim(bottom=arguments.ymin, top=arguments.ymax)


def plot_fsqt(plt, arguments):
    rows = read_csv(arguments.file, ('q', 'lag_time', 'fsqt_mean'))
    q_values = sorted(set(column(rows, 'q')))
    requested = arguments.q or q_values
    selected = []
    for q_value in requested:
        matches = [q for q in q_values if math.isclose(q, q_value, rel_tol=1e-8, abs_tol=1e-12)]
        if not matches:
            raise ValueError('requested q={} is not present'.format(q_value))
        selected.append(matches[0])
    figure, axis = plt.subplots()
    for q_value in dict.fromkeys(selected):
        group = [row for row in rows if math.isclose(float(row['q']), q_value, rel_tol=1e-8)]
        axis.plot(column(group, 'lag_time'), column(group, 'fsqt_mean'),
                  label='q = {:.6g}'.format(q_value))
    axis.axhline(1.0 / math.e, color='0.5', linestyle='--', linewidth=1, label='1/e')
    axis.axhline(.5, color='0.5', linestyle=':', linewidth=1, label='0.5')
    axis.set(xlabel='t', ylabel='F_s(q,t)', xscale=arguments.xscale, yscale=arguments.yscale,
             title=arguments.title or 'Self intermediate scattering function')
    axis.legend()
    axis.grid(True, alpha=.25)
    apply_limits(axis, arguments)
    return [figure]


def symlog_threshold(values):
    magnitudes = sorted(abs(value) for value in values if value != 0.0 and math.isfinite(value))
    if not magnitudes:
        return 1.0
    return max(magnitudes[len(magnitudes) // 10], magnitudes[-1] * 1e-12)


def plot_rheology(plt, arguments):
    rows = read_csv(arguments.file, ('time', 'G'))
    time = column(rows, 'time')
    total = column(rows, 'G')
    figure, axis = plt.subplots()
    if arguments.positive_log:
        points = [(x, y) for x, y in zip(time, total) if x > 0.0 and y > 0.0]
        if not points:
            raise ValueError('no positive G(t) points for --positive-log')
        axis.plot(*zip(*points), label='G')
        axis.set(xscale='log', yscale='log')
    else:
        axis.plot(time, total, label='G')
        axis.set(xscale=arguments.xscale, yscale=arguments.yscale)
        if arguments.yscale == 'symlog':
            axis.set_yscale('symlog', linthresh=symlog_threshold(total))
    if arguments.components:
        missing = set(COMPONENTS) - set(rows[0])
        if missing:
            raise ValueError(
                'components requested but missing: {}'.format(', '.join(sorted(missing))))
        for component in COMPONENTS:
            axis.plot(time, column(rows, component), label=component)
    axis.set(xlabel='t', ylabel='G(t)', title=arguments.title or 'Relaxation modulus')
    axis.legend()
    axis.grid(True, alpha=.25)
    apply_limits(axis, arguments)
    return [figure]


def slope_guide(axis, points, exponent, label):
    start = max(len(points) * 2 // 3, 1)
    interval = points[start:]
    reference_time, reference_msd = interval[len(interval) // 2]
    guide_time = [point[0] for point in interval]
    guide_msd = [reference_msd * (time / reference_time) ** exponent for time in guide_time]
    axis.plot(guide_time, guide_msd, linestyle='--', linewidth=1, label=label, zorder=2)


def replica_msd_rows(path):
    rows = read_csv(path, ('replica', 'lag_time', 'msd'))
    replicas = {}
    for row in rows:
        replica = row['replica']
        replicas.setdefault(replica, []).append(row)
    return replicas


def plot_diffusion(plt, arguments):
    rows = read_csv(arguments.file, ('lag_time', 'msd_mean'))
    time = column(rows, 'lag_time')
    msd = column(rows, 'msd_mean')
    points = [(x, y) for x, y in zip(time, msd) if x > 0.0 and y > 0.0]
    if not points:
        raise ValueError('no positive time/MSD points for log-log plot')
    figure, axis = plt.subplots()
    if 'msd_sem' in rows[0] and not arguments.no_sem:
        sem = column(rows, 'msd_sem')
        band = [(x, y, error) for x, y, error in zip(time, msd, sem) if x > 0.0 and y > 0.0]
        band_time, band_msd, band_sem = zip(*band)
        lower = [max(y - error, float.fromhex('0x1.0p-1022'))
                 for y, error in zip(band_msd, band_sem)]
        axis.fill_between(band_time, lower, [y + error for y, error in zip(band_msd, band_sem)],
                          alpha=.15, zorder=0)
    axis.plot(*zip(*points), marker='o', markersize=3, linewidth=1.2, label='mean', zorder=3)
    if arguments.replicas:
        for index, replica in enumerate(replica_msd_rows(arguments.replicas).values()):
            replica_points = [(float(row['lag_time']), float(row['msd'])) for row in replica
                              if float(row['lag_time']) > 0.0 and float(row['msd']) > 0.0]
            if not replica_points:
                continue
            axis.plot(*zip(*replica_points), linewidth=.75, alpha=.3,
                      label='replicas' if index == 0 else '_nolegend_', zorder=1)
    if arguments.show_diffusive_guide:
        slope_guide(axis, points, 1.0, r'$t^1$')
    if arguments.show_subdiffusive_guide:
        slope_guide(axis, points, .5, r'$t^{1/2}$')
    axis.set(xlabel=r'$t$', ylabel=r'$\langle \Delta R_{\mathrm{CM}}^2(t) \rangle$',
             xscale=arguments.xscale, yscale=arguments.yscale,
             title=arguments.title or 'Star center-of-mass MSD')
    axis.minorticks_on()
    axis.margins(x=.04, y=.1)
    axis.legend()
    apply_limits(axis, arguments)
    figures = [figure]
    if arguments.alpha:
        if 'alpha' not in rows[0]:
            raise ValueError('alpha requested but CSV has no alpha column')
        alpha = column(rows, 'alpha')
        alpha_points = [(x, y) for x, y in zip(time, alpha) if x > 0.0 and math.isfinite(y)]
        if not alpha_points:
            raise ValueError('CSV has no finite alpha values')
        alpha_figure, alpha_axis = plt.subplots()
        alpha_axis.plot(*zip(*alpha_points), marker='o', markersize=3, linewidth=1.2,
                        label=r'$\alpha$')
        alpha_axis.axhline(1.0, color='0.5', linestyle='--', linewidth=1, label='alpha = 1')
        alpha_axis.axhspan(.9, 1.1, color='0.5', alpha=.1)
        alpha_values = [point[1] for point in alpha_points]
        if min(alpha_values) >= 0.0 and max(alpha_values) <= 1.5:
            alpha_axis.set_ylim(0.0, 1.5)
        else:
            span = max(alpha_values) - min(alpha_values)
            alpha_axis.set_ylim(min(0.0, min(alpha_values) - .1 * span),
                                max(1.5, max(alpha_values) + .1 * span))
        alpha_axis.set(xlabel=r'$t$', ylabel=r'$\alpha(t)=d\ln(\mathrm{MSD})/d\ln t$', xscale='log',
                       title=arguments.title or 'Local MSD slope')
        alpha_axis.minorticks_on()
        alpha_axis.legend()
        figures.append(alpha_figure)
    return figures


def topology_kind(rows):
    fields = set(rows[0])
    if {'time', 'inter_bonds', 'mean_k_neighbor'} <= fields:
        return 'frames'
    for kind, (field, _, _) in TOPOLOGY_DISTRIBUTIONS.items():
        if field in fields:
            return kind
    raise ValueError('unrecognized topology CSV schema')


def topology_aggregate_rows(rows):
    aggregate = [row for row in rows if row.get('replica') == 'all_frames']
    if not aggregate:
        raise ValueError('topology distribution has no all_frames aggregate rows')
    return aggregate


def plot_topology_frames(plt, rows, arguments):
    metrics = arguments.metric or TOPOLOGY_DEFAULT_METRICS
    missing = set(metrics) - set(rows[0])
    if missing:
        raise ValueError('unknown or unavailable topology metric: {}'.format(
            ', '.join(sorted(missing))))
    replicas = {}
    for row in rows:
        replicas.setdefault(row.get('replica', ''), []).append(row)
    figures = []
    suffixes = []
    for metric in metrics:
        figure, axis = plt.subplots()
        for replica, replica_rows in replicas.items():
            time = column(replica_rows, 'time')
            values = column(replica_rows, metric)
            plot_arguments = {'linewidth': 1.0}
            if len(replica_rows) <= 400:
                plot_arguments.update(marker='o', markersize=2.5)
            label = 'replica {}'.format(replica) if len(replicas) > 1 else None
            axis.plot(time, values, label=label, **plot_arguments)
        label = TOPOLOGY_METRICS.get(metric, metric)
        title = arguments.title or label
        axis.set(xlabel=r'$t$', ylabel=label, xscale=arguments.xscale or 'linear',
                 yscale=arguments.yscale or 'linear', title=title)
        if metric.endswith('_fraction'):
            values = column(rows, metric)
            if min(values) >= 0.0 and max(values) <= 1.0:
                axis.set_ylim(0.0, 1.0)
        if len(replicas) > 1:
            axis.legend()
        axis.margins(x=.03, y=.08)
        apply_limits(axis, arguments)
        figures.append(figure)
        suffixes.append('.{}'.format(metric))
    return figures, suffixes


def plot_topology_distribution(plt, rows, kind, arguments):
    field, xlabel, default_title = TOPOLOGY_DISTRIBUTIONS[kind]
    aggregate = topology_aggregate_rows(rows)
    values = column(aggregate, field)
    value_name = 'count' if arguments.counts else 'probability'
    heights = column(aggregate, value_name)
    figure, axis = plt.subplots()
    axis.bar(values, heights, width=.8)
    yscale = arguments.yscale or ('log' if kind == 'clusters' else 'linear')
    ylabel = 'Count' if arguments.counts else 'Probability'
    if kind == 'multiplicity' and not arguments.counts:
        ylabel = 'Probability among connected star pairs'
    axis.set(xlabel=xlabel, ylabel=ylabel, xscale=arguments.xscale or 'linear', yscale=yscale,
             title=arguments.title or default_title)
    axis.set_xticks(values)
    axis.margins(x=.03, y=.08)
    apply_limits(axis, arguments)
    return [figure], ['']


def plot_topology(plt, arguments):
    rows = read_csv(arguments.file, ())
    detected_kind = topology_kind(rows)
    kind = arguments.kind or detected_kind
    if kind != detected_kind:
        raise ValueError('--kind={} does not match this topology CSV schema ({})'.format(
            kind, detected_kind))
    if kind == 'frames':
        return plot_topology_frames(plt, rows, arguments)
    return plot_topology_distribution(plt, rows, kind, arguments)


def plot_p47(plt, arguments):
    summary_path = Path(arguments.file)
    prefix = summary_path.with_suffix('.summary.json') if summary_path.suffix != '.json' else summary_path
    figures = []
    mobility_path = prefix.with_name(prefix.name.replace('.summary', '.mobility_by_half_window'))
    mobility = read_csv(mobility_path, ('replica', 'type', 'half_window', 'mean_normalized_r2'))
    figure, axis = plt.subplots()
    for kind, label in (('multiplicity_only', 'multiplicity-only'), ('walking', 'walking'), ('hop', 'hopping')):
        group = [row for row in mobility if row['type'] == kind and row['replica'] != 'ensemble']
        if group:
            axis.plot(column(group, 'half_window'), column(group, 'mean_normalized_r2'),
                      marker='o', label=label)
    axis.axhline(1.0, color='0.5', linestyle='--')
    axis.set(xlabel='requested half-window', ylabel='mobility enhancement',
             title='P4.7b mobility by requested half-window')
    axis.legend(); axis.grid(True, alpha=.25); figures.append(figure)

    tail_path = prefix.with_name(prefix.name.replace('.summary', '.tail_by_half_window'))
    tail = read_csv(tail_path, ('replica', 'type', 'half_window', 'threshold',
                                'P_tail_given_class'))
    threshold = arguments.threshold
    figure, axis = plt.subplots()
    for kind, label in (('multiplicity_only', 'multiplicity-only'), ('walking', 'walking'), ('hop', 'hopping')):
        group = [row for row in tail if row['type'] == kind and row['threshold'] == threshold]
        if group:
            axis.plot(column(group, 'half_window'), column(group, 'P_tail_given_class'),
                      marker='o', label=label)
    axis.set(xlabel='requested half-window', ylabel='P(large displacement | class)',
             title='P4.7b {} tail enrichment'.format(threshold))
    axis.legend(); axis.grid(True, alpha=.25); figures.append(figure)

    displacement_path = prefix.with_name(prefix.name.replace('.summary', '.displacements'))
    rows = read_csv(displacement_path, ('type', 'total_lag', 'distance'))
    lag = arguments.lag or max(float(row['total_lag']) for row in rows)
    selected = [row for row in rows if math.isclose(float(row['total_lag']), lag)]
    figure, axis = plt.subplots()
    for kind, label in (('multiplicity_only', 'multiplicity-only'), ('walking', 'walking'), ('hop', 'hopping')):
        values = sorted(float(row['distance']) for row in selected if row['type'] == kind)
        if values:
            axis.step(values, [(len(values) - index) / len(values) for index in range(len(values))],
                      where='post', label=label)
    axis.set(xlabel='|Delta R|', ylabel='P(|Delta R| >= r)', yscale='log',
             title='P4.7b displacement CCDF, total lag {}'.format(lag))
    axis.legend(); axis.grid(True, alpha=.25); figures.append(figure)

    survival_path = prefix.with_name(prefix.name.replace('.summary', '.hop_duration_survival'))
    survival = read_csv(survival_path, ('duration', 'survival', 'replica'))
    figure, axis = plt.subplots()
    for replica in sorted(set(row['replica'] for row in survival)):
        group = [row for row in survival if row['replica'] == replica]
        axis.step(column(group, 'duration'), column(group, 'survival'), where='post',
                  label='replica {}'.format(replica))
    axis.set(xlabel='hop isolation duration', ylabel='survival', xscale='log', yscale='log',
             title='P4.7b hop-duration survival')
    axis.legend(); axis.grid(True, alpha=.25); figures.append(figure)
    return figures


def plot_p48(plt, arguments):
    frames = read_csv(arguments.file, ('time', 'any_wrap', 'n_wrap_dimensions',
                                       'largest_component_fraction'))
    figures = []
    figure, axis = plt.subplots()
    axis.plot(column(frames, 'time'), column(frames, 'n_wrap_dimensions'))
    axis.set(xlabel='time', ylabel='wrapping dimensions', yticks=(0, 1, 2, 3),
             title='Periodic wrapping state')
    axis.grid(True, alpha=.25); figures.append(figure)

    figure, axis = plt.subplots()
    axis.plot(column(frames, 'time'), column(frames, 'largest_component_fraction'))
    axis.set(xlabel='time', ylabel='largest-component fraction',
             title='Largest component and periodic wrapping')
    axis.grid(True, alpha=.25); figures.append(figure)

    summary_path = Path(arguments.file).with_name(Path(arguments.file).name.replace('.frames', '.summary'))
    with open(summary_path, encoding='utf-8') as source:
        summary = json.load(source)
    values = summary['ensemble_replica_statistics']
    names = ('P_wrap_any', 'P_wrap_x', 'P_wrap_y', 'P_wrap_z', 'P_wrap_xyz')
    figure, axis = plt.subplots()
    axis.bar(names, [values[name]['mean'] for name in names])
    axis.set(ylabel='fraction of frames', title='Periodic wrapping probabilities')
    axis.tick_params(axis='x', rotation=30)
    figures.append(figure)
    return figures


def self_test():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        fsqt = root / 'fsqt.csv'
        fsqt.write_text('q,lag_time,fsqt_mean\n0.1,1,1\n0.1,10,.8\n1,1,1\n1,10,.2\n')
        rheology = root / 'rheology.csv'
        rheology.write_text(
            'time,Gxy,Gxz,Gyz,GNxy,GNxz,GNyz,G\n'
            '0,1,1,1,1,1,1,1\n1,0.5,0.5,0.5,0.5,0.5,0.5,0.5\n2,-.1,-.1,-.1,-.1,-.1,-.1,-.1\n')
        diffusion = root / 'diffusion.csv'
        diffusion.write_text(
            'lag_time,msd_mean,msd_sem,alpha\n0,0,0,nan\n1,1,.1,.9\n10,10,.2,1\n')
        replicas = root / 'replicas.csv'
        replicas.write_text(
            'replica,lag_time,msd\n1,0,0\n1,1,.9\n1,10,9\n2,0,0\n2,1,1.1\n2,10,11\n')
        topology_frames = root / 'topology.frames.csv'
        topology_frames.write_text(
            'frame,time,inter_bonds,intra_bonds,mean_k_bond,mean_k_neighbor,'
            'isolated_fraction,largest_component_fraction,mean_edge_multiplicity,replica\n'
            '0,0,2,1,.4,.2,.8,.2,1,1\n'
            '1,10,3,1,.6,.3,.7,.3,1.1,1\n'
            '0,0,4,2,.8,.4,.6,.4,1.2,2\n'
            '1,10,5,2,1,.5,.5,.5,1.3,2\n')
        topology_neighbor = root / 'topology.degree_neighbor.csv'
        topology_neighbor.write_text(
            'replica,degree_neighbor,count,probability\n'
            'all_frames,0,20,.2\nall_frames,1,50,.5\nall_frames,2,30,.3\n')
        topology_bond = root / 'topology.degree_bond.csv'
        topology_bond.write_text(
            'replica,degree_bond,count,probability\n'
            'all_frames,0,10,.1\nall_frames,1,60,.6\nall_frames,2,30,.3\n')
        topology_multiplicity = root / 'topology.edge_multiplicity.csv'
        topology_multiplicity.write_text(
            'replica,edge_multiplicity,count,probability\n'
            'all_frames,1,90,.9\nall_frames,2,10,.1\n')
        topology_clusters = root / 'topology.cluster_sizes.csv'
        topology_clusters.write_text(
            'replica,cluster_sizes,count,probability\n'
            'all_frames,1,20,.2\nall_frames,2,10,.1\nall_frames,10,70,.7\n')
        plt = pyplot(True)
        fsqt_arguments = argparse.Namespace(
            file=fsqt, q=[.1], xscale='log', yscale='linear', title=None,
            xmin=None, xmax=None, ymin=None, ymax=None)
        save_or_show(plt, plot_fsqt(plt, fsqt_arguments), root / 'fsqt.png', True, 72)
        rheology_arguments = argparse.Namespace(
            file=rheology, components=True, positive_log=False, xscale='log', yscale='symlog',
            title=None, xmin=None, xmax=None, ymin=None, ymax=None)
        save_or_show(plt, plot_rheology(plt, rheology_arguments), root / 'rheology.png', True, 72)
        diffusion_arguments = argparse.Namespace(
            file=diffusion, alpha=True, show_diffusive_guide=True, xscale='log',
            yscale='log', title=None, show_subdiffusive_guide=True, replicas=replicas, no_sem=False,
            xmin=1.0, xmax=10.0, ymin=.5, ymax=20.0)
        save_or_show(
            plt, plot_diffusion(plt, diffusion_arguments), root / 'diffusion.png', True, 72)
        topology_arguments = argparse.Namespace(
            file=topology_frames, kind=None, metric=None, counts=False, xscale=None, yscale=None,
            title=None, xmin=None, xmax=None, ymin=None, ymax=None)
        topology_figures, topology_suffixes = plot_topology(plt, topology_arguments)
        save_or_show(plt, topology_figures, root / 'topology.png', True, 72, topology_suffixes)
        for topology_file in (
                topology_neighbor, topology_bond, topology_multiplicity, topology_clusters):
            topology_arguments.file = topology_file
            topology_figures, topology_suffixes = plot_topology(plt, topology_arguments)
            save_or_show(plt, topology_figures, root / '{}.png'.format(topology_file.stem), True, 72,
                         topology_suffixes)
        expected = (
            'fsqt.png', 'rheology.png', 'diffusion.png', 'diffusion.alpha.png',
            'topology.inter_bonds.png', 'topology.mean_k_neighbor.png',
            'topology.isolated_fraction.png', 'topology.largest_component_fraction.png',
            'topology.degree_neighbor.png', 'topology.degree_bond.png',
            'topology.edge_multiplicity.png', 'topology.cluster_sizes.png')
        for name in expected:
            if not (root / name).is_file():
                raise AssertionError('missing self-test image {}'.format(name))


def common_options(parser, xscale, yscale):
    parser.add_argument('file', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-show', action='store_true')
    parser.add_argument('--title')
    parser.add_argument('--xscale', choices=('linear', 'log'), default=xscale)
    parser.add_argument('--yscale', choices=('linear', 'log', 'symlog'), default=yscale)
    parser.add_argument('--xmin', type=float)
    parser.add_argument('--xmax', type=float)
    parser.add_argument('--ymin', type=float)
    parser.add_argument('--ymax', type=float)
    parser.add_argument('--dpi', type=int, default=150)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    commands = parser.add_subparsers(dest='command')
    fsqt_parser = commands.add_parser('fsqt')
    common_options(fsqt_parser, 'log', 'linear')
    fsqt_parser.add_argument('--q', type=float, nargs='+')
    rheology_parser = commands.add_parser('rheology')
    common_options(rheology_parser, 'log', 'symlog')
    rheology_parser.add_argument('--components', action='store_true')
    rheology_parser.add_argument('--positive-log', action='store_true')
    diffusion_parser = commands.add_parser('diffusion')
    common_options(diffusion_parser, 'log', 'log')
    diffusion_parser.add_argument('--alpha', action='store_true')
    diffusion_parser.add_argument('--show-diffusive-guide', action='store_true')
    diffusion_parser.add_argument('--show-subdiffusive-guide', action='store_true')
    diffusion_parser.add_argument('--replicas', type=Path)
    diffusion_parser.add_argument('--no-sem', action='store_true')
    topology_parser = commands.add_parser('topology')
    common_options(topology_parser, None, None)
    topology_parser.add_argument('--kind', choices=('frames',) + tuple(TOPOLOGY_DISTRIBUTIONS))
    topology_parser.add_argument('--metric', nargs='+')
    topology_parser.add_argument('--counts', action='store_true')
    p47_parser = commands.add_parser('p47')
    common_options(p47_parser, 'linear', 'linear')
    p47_parser.add_argument('--lag', type=float)
    p47_parser.add_argument('--threshold', choices=('q90', 'q95', 'q99'), default='q95')
    p48_parser = commands.add_parser('p48')
    common_options(p48_parser, 'linear', 'linear')
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        print('PLOT_ANALYSIS SELF_TEST PASS')
        return
    if not arguments.command:
        parser.error('choose fsqt, rheology, diffusion, topology, or p47')
    if arguments.dpi <= 0:
        parser.error('--dpi must be positive')
    try:
        plt = pyplot(arguments.no_show)
        if arguments.command == 'fsqt':
            figures = plot_fsqt(plt, arguments)
        elif arguments.command == 'rheology':
            figures = plot_rheology(plt, arguments)
        elif arguments.command == 'diffusion':
            figures = plot_diffusion(plt, arguments)
        elif arguments.command == 'p47':
            figures = plot_p47(plt, arguments)
        elif arguments.command == 'p48':
            figures = plot_p48(plt, arguments)
        else:
            figures, output_suffixes = plot_topology(plt, arguments)
            save_or_show(plt, figures, arguments.output, arguments.no_show, arguments.dpi,
                         output_suffixes)
            return
        save_or_show(plt, figures, arguments.output, arguments.no_show, arguments.dpi)
    except ValueError as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
