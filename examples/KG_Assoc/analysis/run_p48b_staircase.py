#!/usr/bin/env python3
"""Fail-closed host driver for two-chain, downward P4.8b Ee scouting.

MD is run only with --execute.  The default prints the next action.
"""

import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

from plan_p48b_staircase_scout import OBSERVABLES, save_json, stationarity


BLOCK_STEPS = 100000
REEQUILIBRATION_BLOCKS = 5
MEASUREMENT_STEPS = 320000


def load_json(path):
    with open(path, encoding='utf-8') as source:
        return json.load(source)


def command_text(command):
    return ' '.join(command)


def final_state_observables(prefix):
    path = Path(prefix + '.state')
    with open(path, encoding='utf-8') as source:
        rows = [line.split() for line in source if line and not line.startswith('#')]
    if not rows:
        raise ValueError('{} has no state rows'.format(path))
    row = rows[-1]
    return {
        'temporary_bonds': float(row[3]), 'intra_bonds': float(row[6]),
        'inter_bonds': float(row[7]), 'mean_k_neighbor': float(row[13]),
        'largest_component_fraction': float(row[12]),
    }


def new_state(arguments):
    if arguments.delta_ee <= 0:
        raise ValueError('--delta-ee must be positive')
    return {
        'schema_version': 1,
        'system': arguments.system,
        'runner': arguments.runner,
        'analyzer': arguments.analyzer,
        'protocol': {'Ea': arguments.ea, 'nu0': arguments.nu0, 'Nevery': arguments.nevery,
                     'r_assoc': arguments.r_assoc, 'dt': arguments.dt,
                     'temperature': arguments.temperature, 'delta_Ee': arguments.delta_ee,
                     'block_steps': BLOCK_STEPS,
                     'reequilibration_steps': BLOCK_STEPS * REEQUILIBRATION_BLOCKS,
                     'measurement_steps': MEASUREMENT_STEPS,
                     'topology_every': arguments.topology_every,
                     'relative_drift_tolerance': arguments.relative_drift_tolerance},
        'chains': [{'id': 'chain1', 'seed': arguments.seed1, 'Ee': arguments.starting_ee,
                    'restart': arguments.parent1, 'history': []},
                   {'id': 'chain2', 'seed': arguments.seed2, 'Ee': arguments.starting_ee,
                    'restart': arguments.parent2, 'history': []}],
        'status': 'READY', 'bracket': None,
    }


def runner_command(state, parent, parent_ee, target_ee, output, block, switch):
    protocol = state['protocol']
    command = [state['runner'], '--restart-prefix', parent, '--output', output,
               '--steps', str(BLOCK_STEPS), '--temperature', str(protocol['temperature']),
               '--Ea', str(protocol['Ea']), '--nu0', str(protocol['nu0']),
               '--Nevery', str(protocol['Nevery']), '--r-assoc', str(protocol['r_assoc']),
               '--dt', str(protocol['dt']), '--diagnostic-every', str(protocol['topology_every']),
               '--com-every', str(protocol['topology_every']), '--frame-every', str(protocol['topology_every']),
               '--progress-every', str(BLOCK_STEPS), '--topology-only']
    if switch:
        command += ['--Ee', str(target_ee), '--continuation-ee-parent', str(parent_ee),
                    '--continuation-ee-target', str(target_ee), '--continuation-parent', parent,
                    '--continuation-direction', 'downward', '--continuation-stage', 'reequilibration',
                    '--reequilibration-steps', str(BLOCK_STEPS * REEQUILIBRATION_BLOCKS),
                    '--measurement-steps', str(MEASUREMENT_STEPS)]
    return command


def execute(command, enabled):
    print(command_text(command), file=sys.stderr, flush=True)
    if enabled:
        subprocess.run(command, check=True)


def analyze(state, prefixes, output_prefix, enabled):
    command = [sys.executable, state['analyzer'], '--system', state['system'],
               '--output-prefix', output_prefix, *prefixes]
    execute(command, enabled)
    if not enabled:
        return None
    return load_json(output_prefix + '.summary.json')


def clearly_high(summary):
    rows = summary['replica_summaries']
    ensemble = summary['ensemble_replica_statistics']['P_wrap_any']
    return all(row['P_wrap_any'] > .5 for row in rows) and (
        ensemble['mean'] - ensemble['ci95_half_width'] > .5)


def run_plateau(state, output_dir, enabled):
    if state['status'] != 'READY':
        raise ValueError('driver is not ready: {}'.format(state['status']))
    target = state['chains'][0]['Ee'] - state['protocol']['delta_Ee']
    if not math.isclose(state['chains'][1]['Ee'], state['chains'][0]['Ee'], abs_tol=1e-12):
        raise ValueError('chains are at different Ee; fail closed')
    output_dir = Path(output_dir)
    reeq_blocks = {}
    measurement_prefixes = []
    for chain in state['chains']:
        parent = chain['restart']
        blocks = []
        for block in range(1, REEQUILIBRATION_BLOCKS + 1):
            output = str(output_dir / '{}_ee{}_reeq_block{}'.format(
                chain['id'], str(target).replace('.', 'p'), block))
            execute(runner_command(state, parent, chain['Ee'], target, output, block, block == 1), enabled)
            if enabled:
                metrics = final_state_observables(output)
                block_summary = analyze(state, [output], output + '_p48', enabled)
                metrics['P_wrap_any'] = block_summary['replica_summaries'][0]['P_wrap_any']
                blocks.append(metrics)
            parent = output
        if enabled:
            reeq_blocks[chain['id']] = blocks
            gate = stationarity(blocks, {
                'min_reequilibration_blocks': REEQUILIBRATION_BLOCKS,
                'max_reequilibration_blocks': REEQUILIBRATION_BLOCKS,
                'relative_drift_tolerance': state['protocol']['relative_drift_tolerance']})
            if gate != 'ADMITTED':
                state['status'] = 'EQUILIBRATION_NOT_ESTABLISHED'
                state['failed_blocks'] = reeq_blocks
                return
        measurement = str(output_dir / '{}_ee{}_measurement'.format(
            chain['id'], str(target).replace('.', 'p')))
        command = runner_command(state, parent, target, target, measurement, 0, False)
        command[command.index('--steps') + 1] = str(MEASUREMENT_STEPS)
        execute(command, enabled)
        measurement_prefixes.append(measurement)
    if not enabled:
        return
    summary = analyze(state, measurement_prefixes,
                      str(output_dir / 'ee{}_percolation'.format(str(target).replace('.', 'p'))), enabled)
    record = {'Ee': target, 'reequilibration_blocks': reeq_blocks,
              'measurement_prefixes': measurement_prefixes, 'summary': summary,
              'clearly_high_both_chains': clearly_high(summary)}
    for chain, prefix in zip(state['chains'], measurement_prefixes):
        chain['Ee'] = target
        chain['restart'] = prefix
        chain['history'].append(record)
    if record['clearly_high_both_chains']:
        state['status'] = 'READY'
    else:
        state['status'] = 'STOPPED_NOT_HIGH'
        state['bracket'] = {'Ee_low': target,
                            'Ee_high': target + state['protocol']['delta_Ee'],
                            'final_Ee_50': False}


def self_test():
    parser = build_parser()
    args = parser.parse_args(['init', '--state', 'x', '--system', 'system', '--runner', 'runner',
                              '--analyzer', 'analyzer', '--parent1', 'a', '--parent2', 'b'])
    state = new_state(args)
    command = runner_command(state, 'a', 8.0, 7.5, 'out', 1, True)
    assert '--continuation-ee-target' in command and command[command.index('--Ee') + 1] == '7.5'
    assert state['protocol']['reequilibration_steps'] == 500000
    blocks = [{name: 1.0 for name in OBSERVABLES} for _ in range(5)]
    assert stationarity(blocks, {'min_reequilibration_blocks': 5,
                                 'max_reequilibration_blocks': 5,
                                 'relative_drift_tolerance': .05}) == 'ADMITTED'
    blocks[-1]['temporary_bonds'] = 2.0
    assert stationarity(blocks, {'min_reequilibration_blocks': 5,
                                 'max_reequilibration_blocks': 5,
                                 'relative_drift_tolerance': .05}) == 'NONSTATIONARY'
    print('P4.8B AUTOMATED STAIRCASE SELF_TEST PASS')


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    commands = parser.add_subparsers(dest='command')
    init = commands.add_parser('init')
    init.add_argument('--state', required=True, type=Path)
    init.add_argument('--system', required=True)
    init.add_argument('--runner', default='examples/KG_Assoc/kg_assoc_production')
    init.add_argument('--analyzer', default='examples/KG_Assoc/analysis/analyze_p48_percolation.py')
    init.add_argument('--parent1', required=True)
    init.add_argument('--parent2', required=True)
    init.add_argument('--seed1', type=int, default=12001)
    init.add_argument('--seed2', type=int, default=12002)
    init.add_argument('--starting-ee', type=float, default=8.0)
    init.add_argument('--delta-ee', type=float, default=.5)
    init.add_argument('--ea', type=float, default=4.0)
    init.add_argument('--nu0', type=float, default=20.0)
    init.add_argument('--nevery', type=int, default=100)
    init.add_argument('--r-assoc', type=float, default=1.25)
    init.add_argument('--dt', type=float, default=.01)
    init.add_argument('--temperature', type=float, default=1.0)
    init.add_argument('--topology-every', type=int, default=10000)
    init.add_argument('--relative-drift-tolerance', type=float, default=.05)
    run = commands.add_parser('run-next')
    run.add_argument('--state', required=True, type=Path)
    run.add_argument('--output-dir', required=True)
    run.add_argument('--execute', action='store_true')
    return parser


def main():
    parser = build_parser()
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if arguments.command == 'init':
        save_json(arguments.state, new_state(arguments))
        return
    state = load_json(arguments.state)
    run_plateau(state, arguments.output_dir, arguments.execute)
    if arguments.execute:
        save_json(arguments.state, state)


if __name__ == '__main__':
    main()
