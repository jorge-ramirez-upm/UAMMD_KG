#!/usr/bin/env python3
"""Plan and record piecewise-constant Ee continuation scouts.

This tool only writes JSON requests and state.  It never starts MD.
"""

import argparse
import json
import math
import tempfile
from pathlib import Path


SCHEMA_VERSION = 1
OBSERVABLES = (
    'temporary_bonds', 'inter_bonds', 'intra_bonds', 'mean_k_neighbor',
    'largest_component_fraction', 'P_wrap_any')


def load_json(path):
    with open(path, encoding='utf-8') as source:
        return json.load(source)


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with open(temporary, 'w', encoding='utf-8') as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write('\n')
    temporary.replace(path)


def close(left, right):
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def new_state(arguments):
    return {
        'schema_version': SCHEMA_VERSION,
        'system': {
            'system_label': arguments.system_label,
            'N_A': arguments.arms,
            'N': arguments.arm_length,
            'rho_polymer': arguments.polymer_density,
            'temperature': arguments.temperature,
            'number_of_stars': arguments.number_of_stars,
            'reaction_geometry': arguments.reaction_geometry,
        },
        'protocol': {
            'Ea': arguments.ea,
            'Ea_physical': arguments.ea_physical,
            'Ea_invariance_status': arguments.ea_invariance_status,
            'nu0': arguments.nu0,
            'Nevery': arguments.nevery,
            'r_assoc': arguments.r_assoc,
            'dt': arguments.dt,
            'delta_Ee': arguments.delta_ee,
            'topology_every': arguments.topology_every,
            'block_steps': arguments.block_steps,
            'min_reequilibration_blocks': arguments.min_blocks,
            'max_reequilibration_blocks': arguments.max_blocks,
            'measurement_steps': arguments.measurement_steps,
            'relative_drift_tolerance': arguments.relative_drift_tolerance,
        },
        'scouts': [],
        'scout_brackets': [],
        'notes': [
            'Each Ee is piecewise constant. Continuation is initialization only.',
            'A staircase bracket is a scout result, not a final Ee_50 estimate.',
        ],
    }


def validate_state(state):
    if state.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('unsupported staircase state schema')
    protocol = state['protocol']
    if protocol['delta_Ee'] <= 0 or protocol['min_reequilibration_blocks'] <= 0:
        raise ValueError('invalid staircase protocol')
    if protocol['max_reequilibration_blocks'] < protocol['min_reequilibration_blocks']:
        raise ValueError('maximum re-equilibration blocks is smaller than minimum')
    seen = set()
    for scout in state['scouts']:
        if scout['staircase_id'] in seen:
            raise ValueError('duplicate staircase ID')
        seen.add(scout['staircase_id'])


def require_physical_ea(state):
    protocol = state['protocol']
    if close(protocol['Ea'], protocol['Ea_physical']):
        return
    if protocol['Ea_invariance_status'] != 'PASS':
        raise ValueError('accelerated Ea_search is blocked until Ea-invariance is PASS')


def add_scout(state, arguments):
    require_physical_ea(state)
    if any(item['staircase_id'] == arguments.staircase_id for item in state['scouts']):
        raise ValueError('duplicate staircase ID {}'.format(arguments.staircase_id))
    if arguments.direction not in ('downward', 'upward'):
        raise ValueError('invalid continuation direction')
    state['scouts'].append({
        'staircase_id': arguments.staircase_id,
        'replica_id': arguments.replica_id,
        'direction': arguments.direction,
        'starting_Ee': arguments.starting_ee,
        'current_Ee': arguments.starting_ee,
        'parent_restart': arguments.parent_restart,
        'parent_seed': arguments.parent_seed,
        'plateaus': [],
        'stop_descending': False,
    })


def find_scout(state, staircase_id):
    for scout in state['scouts']:
        if scout['staircase_id'] == staircase_id:
            return scout
    raise ValueError('unknown staircase ID {}'.format(staircase_id))


def next_target(state, scout):
    if scout['stop_descending'] and scout['direction'] == 'downward':
        raise ValueError('scout has a rough bracket; do not descend automatically')
    delta = state['protocol']['delta_Ee']
    return scout['current_Ee'] - delta if scout['direction'] == 'downward' else scout['current_Ee'] + delta


def next_request(state, staircase_id, output_prefix):
    require_physical_ea(state)
    scout = find_scout(state, staircase_id)
    target = next_target(state, scout)
    parent_restart = scout['parent_restart'] if not scout['plateaus'] else scout['plateaus'][-1]['output_restart']
    if not parent_restart:
        raise ValueError('a concrete parent restart is required')
    protocol = state['protocol']
    chemistry = {key: protocol[key] for key in ('Ea', 'nu0', 'Nevery', 'r_assoc', 'dt')}
    runner_arguments = [
        '--restart-prefix', parent_restart,
        '--output', output_prefix,
        '--steps', str(protocol['block_steps']),
        '--temperature', str(state['system']['temperature']),
        '--Ea', str(chemistry['Ea']),
        '--nu0', str(chemistry['nu0']),
        '--Nevery', str(chemistry['Nevery']),
        '--r-assoc', str(chemistry['r_assoc']),
        '--dt', str(chemistry['dt']),
        '--Ee', str(target),
        '--continuation-ee-parent', str(scout['current_Ee']),
        '--continuation-ee-target', str(target),
        '--continuation-parent', parent_restart,
        '--continuation-direction', scout['direction'],
        '--continuation-stage', 'reequilibration',
        '--reequilibration-steps', str(protocol['block_steps']),
        '--measurement-steps', str(protocol['measurement_steps']),
        '--diagnostic-every', str(protocol['topology_every']),
        '--progress-every', str(protocol['block_steps']),
        '--com-every', str(protocol['topology_every']),
        '--frame-every', str(protocol['topology_every']),
        '--topology-only',
    ]
    return {
        'kind': 'P4.8b_staircase_plateau_request',
        'staircase_id': scout['staircase_id'],
        'replica_id': scout['replica_id'],
        'continuation_parent': {'restart_path': parent_restart, 'Ee_parent': scout['current_Ee'],
                                'seed': scout['parent_seed']},
        'continuation_direction': scout['direction'],
        'Ee_target': target,
        'chemistry': chemistry,
        'topology_every': protocol['topology_every'],
        'topology_only': True,
        'reequilibration': {
            'block_steps': protocol['block_steps'],
            'min_blocks': protocol['min_reequilibration_blocks'],
            'max_blocks': protocol['max_reequilibration_blocks'],
            'stationarity_observables': list(OBSERVABLES),
        },
        'measurement_steps': protocol['measurement_steps'],
        'output_prefix': output_prefix,
        'runner_arguments_for_first_reequilibration_block': runner_arguments,
        'note': 'Request only: run re-equilibration blocks first. Measurement is forbidden until admitted.',
    }


def stationarity(blocks, protocol):
    if len(blocks) < protocol['min_reequilibration_blocks']:
        return 'PENDING'
    recent = blocks[-protocol['min_reequilibration_blocks']:]
    for name in OBSERVABLES:
        values = [block[name] for block in recent]
        scale = max(1.0, abs(sum(values) / len(values)))
        if max(values) - min(values) > protocol['relative_drift_tolerance'] * scale:
            return 'NONSTATIONARY' if len(blocks) >= protocol['max_reequilibration_blocks'] else 'EXTEND'
    return 'ADMITTED'


def scout_classification(probability, uncertainty):
    if uncertainty is None:
        return 'INTERMEDIATE_WRAPPING'
    if probability - uncertainty > .5:
        return 'HIGH_WRAPPING'
    if probability + uncertainty < .5:
        return 'LOW_WRAPPING'
    return 'INTERMEDIATE_WRAPPING'


def register_plateau(state, arguments):
    scout = find_scout(state, arguments.staircase_id)
    blocks = load_json(arguments.blocks)
    status = stationarity(blocks, state['protocol'])
    if status != 'ADMITTED':
        return status
    if not arguments.output_restart:
        raise ValueError('an admitted plateau must retain an output restart')
    classification = scout_classification(arguments.p_wrap_any, arguments.p_wrap_ci95)
    plateau = {
        'Ee': arguments.ee,
        'parent_Ee': scout['current_Ee'],
        'parent_restart': scout['parent_restart'] if not scout['plateaus'] else scout['plateaus'][-1]['output_restart'],
        'continuation_direction': scout['direction'],
        'reequilibration_blocks': len(blocks),
        'reequilibration_duration': len(blocks) * state['protocol']['block_steps'],
        'stationarity_status': status,
        'measurement_duration': arguments.measurement_steps,
        'P_wrap_any': arguments.p_wrap_any,
        'P_wrap_any_ci95_half_width': arguments.p_wrap_ci95,
        'P_wrap_xyz': arguments.p_wrap_xyz,
        'wrapping_fraction': arguments.wrapping_fraction,
        'largest_component_fraction': arguments.largest_component_fraction,
        'finite_cluster_susceptibility': arguments.finite_susceptibility,
        'bond_observables': arguments.bond_observables,
        'output_restart': arguments.output_restart,
        'classification': classification,
    }
    previous = scout['plateaus'][-1] if scout['plateaus'] else None
    scout['plateaus'].append(plateau)
    scout['current_Ee'] = arguments.ee
    if previous and previous['classification'] == 'HIGH_WRAPPING' and classification != 'HIGH_WRAPPING':
        state['scout_brackets'].append({
            'staircase_id': scout['staircase_id'], 'Ee_low': plateau['Ee'],
            'Ee_high': previous['Ee'], 'source': 'downward_scout', 'final_Ee_50': False,
        })
        if scout['direction'] == 'downward':
            scout['stop_descending'] = True
    if previous and previous['classification'] == 'INTERMEDIATE_WRAPPING' and classification == 'LOW_WRAPPING':
        state['scout_brackets'].append({
            'staircase_id': scout['staircase_id'], 'Ee_low': plateau['Ee'],
            'Ee_high': previous['Ee'], 'source': 'downward_scout', 'final_Ee_50': False,
        })
        if scout['direction'] == 'downward':
            scout['stop_descending'] = True
    return status


def confirmation_request(state):
    if not state['scout_brackets']:
        raise ValueError('no scout bracket is available')
    bracket = state['scout_brackets'][-1]
    low = bracket['Ee_low']
    high = bracket['Ee_high']
    return {'kind': 'P4.8b_fixed_Ee_confirmation_request', 'source_bracket': bracket,
            'Ee_values': [low, (low + high) / 2.0, high], 'independent_replicas_required': True,
            'note': 'Use the fixed-Ee planner for final replica-level Ee_50 inference.'}


def self_test():
    parser = build_parser()
    base = parser.parse_args(['init', '--state', 'x', '--system-label', 'C1', '--arms', '4',
                              '--arm-length', '10', '--polymer-density', '.8', '--temperature', '1',
                              '--number-of-stars', '1000', '--reaction-geometry', 'test', '--ea', '4',
                              '--ea-physical', '4', '--nu0', '20', '--nevery', '100', '--r-assoc', '1.25',
                              '--dt', '.01'])
    state = new_state(base)
    for identifier in ('down-1', 'down-2'):
        add_scout(state, argparse.Namespace(staircase_id=identifier, replica_id=identifier,
                                             direction='downward', starting_ee=8.0,
                                             parent_restart=identifier + '.restart', parent_seed=1))
    request = next_request(state, 'down-1', 'out')
    assert request['Ee_target'] == 7.5 and request['continuation_parent']['Ee_parent'] == 8.0
    assert request['chemistry']['Ea'] == 4 and request['topology_only']
    assert '--temperature' in request['runner_arguments_for_first_reequilibration_block']
    stable = [{name: 1.0 for name in OBSERVABLES} for _ in range(2)]
    drifting = [{name: float(index) for name in OBSERVABLES} for index in range(3)]
    assert stationarity(stable, state['protocol']) == 'ADMITTED'
    assert stationarity(drifting, state['protocol']) == 'EXTEND'
    with tempfile.TemporaryDirectory() as directory:
        blocks = Path(directory) / 'blocks.json'
        save_json(blocks, stable)
        args = argparse.Namespace(staircase_id='down-1', blocks=blocks, ee=7.5,
                                  output_restart='7.5.restart', measurement_steps=100,
                                  p_wrap_any=.5, p_wrap_ci95=.1, p_wrap_xyz=.4,
                                  wrapping_fraction=.5, largest_component_fraction=.5,
                                  finite_susceptibility=2.0, bond_observables={})
        assert register_plateau(state, args) == 'ADMITTED'
        state['scouts'][0]['plateaus'][-1]['classification'] = 'HIGH_WRAPPING'
        args.ee = 7.0
        args.output_restart = '7.restart'
        args.p_wrap_any = .2
        assert register_plateau(state, args) == 'ADMITTED'
        assert state['scouts'][0]['stop_descending']
        assert confirmation_request(state)['Ee_values'] == [7.0, 7.25, 7.5]
        path = Path(directory) / 'state.json'
        save_json(path, state)
        validate_state(load_json(path))
    accelerated = new_state(base)
    accelerated['protocol']['Ea'] = 2.0
    try:
        add_scout(accelerated, argparse.Namespace(staircase_id='bad', replica_id='bad', direction='downward', starting_ee=8.0, parent_restart='x', parent_seed=1))
    except ValueError:
        pass
    else:
        raise AssertionError('unvalidated accelerated Ea was accepted')
    print('P4.8B STAIRCASE SELF_TEST PASS')


def add_init_arguments(parser):
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--system-label', required=True)
    parser.add_argument('--arms', type=int, required=True)
    parser.add_argument('--arm-length', type=int, required=True)
    parser.add_argument('--polymer-density', type=float, required=True)
    parser.add_argument('--temperature', type=float, required=True)
    parser.add_argument('--number-of-stars', type=int, required=True)
    parser.add_argument('--reaction-geometry', required=True)
    parser.add_argument('--ea', type=float, required=True)
    parser.add_argument('--ea-physical', type=float, required=True)
    parser.add_argument('--ea-invariance-status', choices=('REQUIRED', 'PASS'), default='REQUIRED')
    parser.add_argument('--nu0', type=float, required=True)
    parser.add_argument('--nevery', type=int, required=True)
    parser.add_argument('--r-assoc', type=float, required=True)
    parser.add_argument('--dt', type=float, required=True)
    parser.add_argument('--delta-ee', type=float, default=.5)
    parser.add_argument('--topology-every', type=int, default=10000)
    parser.add_argument('--block-steps', type=int, default=100000)
    parser.add_argument('--min-blocks', type=int, default=2)
    parser.add_argument('--max-blocks', type=int, default=6)
    parser.add_argument('--measurement-steps', type=int, default=320000)
    parser.add_argument('--relative-drift-tolerance', type=float, default=.05)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    commands = parser.add_subparsers(dest='command')
    init = commands.add_parser('init')
    add_init_arguments(init)
    add = commands.add_parser('add-scout')
    add.add_argument('--state', required=True, type=Path)
    add.add_argument('--staircase-id', required=True)
    add.add_argument('--replica-id', required=True)
    add.add_argument('--direction', choices=('downward', 'upward'), default='downward')
    add.add_argument('--starting-ee', type=float, required=True)
    add.add_argument('--parent-restart', required=True)
    add.add_argument('--parent-seed', type=int)
    request = commands.add_parser('write-next-request')
    request.add_argument('--state', required=True, type=Path)
    request.add_argument('--staircase-id', required=True)
    request.add_argument('--output-prefix', required=True)
    request.add_argument('--output', required=True, type=Path)
    register = commands.add_parser('register-plateau')
    register.add_argument('--state', required=True, type=Path)
    register.add_argument('--staircase-id', required=True)
    register.add_argument('--blocks', type=Path, required=True)
    register.add_argument('--ee', type=float, required=True)
    register.add_argument('--output-restart', required=True)
    register.add_argument('--measurement-steps', type=int, required=True)
    register.add_argument('--p-wrap-any', type=float, required=True)
    register.add_argument('--p-wrap-ci95', type=float)
    register.add_argument('--p-wrap-xyz', type=float, required=True)
    register.add_argument('--wrapping-fraction', type=float, required=True)
    register.add_argument('--largest-component-fraction', type=float, required=True)
    register.add_argument('--finite-susceptibility', type=float)
    register.add_argument('--bond-observables', type=json.loads, default={})
    confirm = commands.add_parser('write-confirmation-request')
    confirm.add_argument('--state', required=True, type=Path)
    confirm.add_argument('--output', required=True, type=Path)
    report = commands.add_parser('report')
    report.add_argument('--state', required=True, type=Path)
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
    validate_state(state)
    if arguments.command == 'add-scout':
        add_scout(state, arguments)
        save_json(arguments.state, state)
    elif arguments.command == 'write-next-request':
        save_json(arguments.output, next_request(state, arguments.staircase_id, arguments.output_prefix))
    elif arguments.command == 'register-plateau':
        print('stationarity={}'.format(register_plateau(state, arguments)))
        save_json(arguments.state, state)
    elif arguments.command == 'write-confirmation-request':
        save_json(arguments.output, confirmation_request(state))
    elif arguments.command == 'report':
        for scout in state['scouts']:
            print('{} {} Ee={} plateaus={} stop={}'.format(
                scout['staircase_id'], scout['direction'], scout['current_Ee'],
                len(scout['plateaus']), scout['stop_descending']))
        for bracket in state['scout_brackets']:
            print('scout bracket [{Ee_low}, {Ee_high}] (not final Ee_50)'.format(**bracket))
    else:
        parser.error('choose init, add-scout, write-next-request, register-plateau, report, or write-confirmation-request')


if __name__ == '__main__':
    main()
