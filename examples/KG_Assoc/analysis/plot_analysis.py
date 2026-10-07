#!/usr/bin/env python3
"""Quick Matplotlib inspection plots for KG_Assoc analysis CSV files."""

import argparse
import csv
import math
import tempfile
from pathlib import Path


COMPONENTS = ('Gxy', 'Gxz', 'Gyz', 'GNxy', 'GNxz', 'GNyz')


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


def save_or_show(plt, figures, output, no_show, dpi):
    for figure in figures:
        figure.tight_layout()
    if output:
        figures[0].savefig(output, dpi=dpi)
        if len(figures) > 1:
            path = Path(output)
            alpha_path = path.with_name(path.stem + '.alpha' + path.suffix)
            figures[1].savefig(alpha_path, dpi=dpi)
    if not no_show:
        plt.show()
    for figure in figures:
        plt.close(figure)


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
    return [figure]


def plot_diffusion(plt, arguments):
    rows = read_csv(arguments.file, ('lag_time', 'msd_mean'))
    time = column(rows, 'lag_time')
    msd = column(rows, 'msd_mean')
    points = [(x, y) for x, y in zip(time, msd) if x > 0.0 and y > 0.0]
    if not points:
        raise ValueError('no positive time/MSD points for log-log plot')
    figure, axis = plt.subplots()
    axis.plot(*zip(*points), label='MSD')
    if 'msd_sem' in rows[0]:
        sem = column(rows, 'msd_sem')
        lower = [max(y - error, float.fromhex('0x1.0p-1022')) for y, error in zip(msd, sem)]
        axis.fill_between(time, lower, [y + error for y, error in zip(msd, sem)], alpha=.2)
    if arguments.show_diffusive_guide:
        index = len(points) // 2
        reference_time, reference_msd = points[index]
        guide = [reference_msd * x / reference_time for x, _ in points]
        axis.plot([x for x, _ in points], guide, linestyle='--', label='t^1 guide')
    axis.set(xlabel='t', ylabel='MSD(t)', xscale=arguments.xscale, yscale=arguments.yscale,
             title=arguments.title or 'Star center-of-mass MSD')
    axis.legend()
    axis.grid(True, alpha=.25)
    figures = [figure]
    if arguments.alpha:
        if 'alpha' not in rows[0]:
            raise ValueError('alpha requested but CSV has no alpha column')
        alpha = column(rows, 'alpha')
        alpha_points = [(x, y) for x, y in zip(time, alpha) if x > 0.0 and math.isfinite(y)]
        if not alpha_points:
            raise ValueError('CSV has no finite alpha values')
        alpha_figure, alpha_axis = plt.subplots()
        alpha_axis.plot(*zip(*alpha_points), label='alpha')
        alpha_axis.axhline(1.0, color='0.5', linestyle='--', linewidth=1, label='alpha = 1')
        alpha_axis.axhspan(.9, 1.1, color='0.5', alpha=.1)
        alpha_axis.set(xlabel='t', ylabel='alpha(t)', xscale='log',
                       title=arguments.title or 'Local MSD slope')
        alpha_axis.legend()
        alpha_axis.grid(True, alpha=.25)
        figures.append(alpha_figure)
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
        plt = pyplot(True)
        fsqt_arguments = argparse.Namespace(file=fsqt, q=[.1], xscale='log', yscale='linear',
                                            title=None)
        save_or_show(plt, plot_fsqt(plt, fsqt_arguments), root / 'fsqt.png', True, 72)
        rheology_arguments = argparse.Namespace(file=rheology, components=True, positive_log=False,
                                                xscale='log', yscale='symlog', title=None)
        save_or_show(plt, plot_rheology(plt, rheology_arguments), root / 'rheology.png', True, 72)
        diffusion_arguments = argparse.Namespace(
            file=diffusion, alpha=True, show_diffusive_guide=True, xscale='log',
            yscale='log', title=None)
        save_or_show(
            plt, plot_diffusion(plt, diffusion_arguments), root / 'diffusion.png', True, 72)
        for name in ('fsqt.png', 'rheology.png', 'diffusion.png', 'diffusion.alpha.png'):
            if not (root / name).is_file():
                raise AssertionError('missing self-test image {}'.format(name))


def common_options(parser, xscale, yscale):
    parser.add_argument('file', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-show', action='store_true')
    parser.add_argument('--title')
    parser.add_argument('--xscale', choices=('linear', 'log'), default=xscale)
    parser.add_argument('--yscale', choices=('linear', 'log', 'symlog'), default=yscale)
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
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        print('PLOT_ANALYSIS SELF_TEST PASS')
        return
    if not arguments.command:
        parser.error('choose fsqt, rheology, or diffusion')
    if arguments.dpi <= 0:
        parser.error('--dpi must be positive')
    try:
        plt = pyplot(arguments.no_show)
        if arguments.command == 'fsqt':
            figures = plot_fsqt(plt, arguments)
        elif arguments.command == 'rheology':
            figures = plot_rheology(plt, arguments)
        else:
            figures = plot_diffusion(plt, arguments)
        save_or_show(plt, figures, arguments.output, arguments.no_show, arguments.dpi)
    except ValueError as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
