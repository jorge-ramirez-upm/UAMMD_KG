#!/usr/bin/env python3
"""Persistent, non-executing adaptive Ee planner for finite-box wrapping."""

import argparse
import csv
import json
import math
import statistics
import tempfile
from pathlib import Path


SCHEMA_VERSION = 1
CLASSIFICATIONS = (
    'CLEARLY_NONPERCOLATED',
    'INTERMEDIATE',
    'CLEARLY_PERCOLATED',
    'INSUFFICIENT_SAMPLING',
)
RUN_CLASSES = ('screening', 'threshold')
SOURCES = ('fresh', 'continuation')
STATIONARITY = ('ADMITTED', 'NONSTATIONARY', 'UNKNOWN')
EA_STATUS = ('REQUIRED', 'PASS', 'FAIL', 'NOT_REQUIRED')


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


def ee_key(value):
    return format(float(value), '.12g')


def default_protocol(arguments):
    return {
        'target_probability': arguments.target_probability,
        'delta_ee_target': arguments.delta_ee_target,
        'probability_tolerance': arguments.probability_tolerance,
        'max_evaluations': arguments.max_evaluations,
        'expansion_step': arguments.expansion_step,
        'min_replicas': arguments.min_replicas,
        'Ea_search': arguments.ea_search,
        'Ea_physical': arguments.ea_physical,
        'nu0': arguments.nu0,
        'reaction_geometry': arguments.reaction_geometry,
        'ea_invariance_status': 'REQUIRED',
        'ea_validation_values': [],
        'run_classes': {
            'screening': {'replicas': arguments.screening_replicas,
                          'production_steps': arguments.screening_steps,
                          'topology_every': arguments.topology_every},
            'threshold': {'replicas': arguments.threshold_replicas,
                          'production_steps': arguments.threshold_steps,
                          'topology_every': arguments.topology_every},
        },
    }


def new_state(arguments):
    return {
        'schema_version': SCHEMA_VERSION,
        'system': {
            'system_label': arguments.system_label,
            'arms_per_star': arguments.arms,
            'arm_length': arguments.arm_length,
            'polymer_density': arguments.polymer_density,
            'total_density': arguments.total_density,
            'number_of_stars': arguments.number_of_stars,
            'temperature': arguments.temperature,
            'box_generation_protocol': arguments.box_generation_protocol,
        },
        'protocol': default_protocol(arguments),
        'initial_bounds': {'Ee_low': arguments.ee_low, 'Ee_high': arguments.ee_high},
        'trials': [],
        'notes': ['Ee_50 is a finite-box operational P_wrap crossing, not a critical point.'],
    }


def validate_state(state):
    if state.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('unsupported search state schema')
    if state['protocol']['ea_invariance_status'] not in EA_STATUS:
        raise ValueError('invalid Ea-invariance status')
    seen = set()
    for trial in state['trials']:
        key = ee_key(trial['Ee'])
        if key in seen:
            raise ValueError('duplicate Ee trial {}'.format(key))
        seen.add(key)


def classify_trial(trial, protocol):
    if trial['equilibration_status'] != 'ADMITTED':
        return 'INSUFFICIENT_SAMPLING'
    if trial['replica_count'] < protocol['min_replicas']:
        return 'INSUFFICIENT_SAMPLING'
    uncertainty = trial.get('P_wrap_any_ci95_half_width')
    if uncertainty is None:
        return 'INSUFFICIENT_SAMPLING'
    target = protocol['target_probability']
    lower = trial['P_wrap_any'] - uncertainty
    upper = trial['P_wrap_any'] + uncertainty
    if upper < target:
        return 'CLEARLY_NONPERCOLATED'
    if lower > target:
        return 'CLEARLY_PERCOLATED'
    return 'INTERMEDIATE'


def refresh_classifications(state):
    for trial in state['trials']:
        trial['classification'] = classify_trial(trial, state['protocol'])


def scientific_validation_status(state):
    protocol = state['protocol']
    if math.isclose(protocol['Ea_search'], protocol['Ea_physical'], abs_tol=1e-12):
        return 'Ea_search equals Ea_physical'
    status = protocol['ea_invariance_status']
    if status == 'PASS':
        return 'accelerated Ea validated'
    return 'accelerated Ea scientifically unvalidated ({})'.format(status)


def admitted_trials(state):
    return [trial for trial in state['trials']
            if trial['classification'] in ('CLEARLY_NONPERCOLATED', 'CLEARLY_PERCOLATED')]


def bracket(state):
    below = [trial for trial in admitted_trials(state)
             if trial['classification'] == 'CLEARLY_NONPERCOLATED']
    above = [trial for trial in admitted_trials(state)
             if trial['classification'] == 'CLEARLY_PERCOLATED']
    if not below or not above:
        return None
    return max(below, key=lambda trial: trial['Ee']), min(above, key=lambda trial: trial['Ee'])


def recommended_source(state, target_ee):
    candidates = [trial for trial in state['trials']
                  if trial['equilibration_status'] == 'ADMITTED' and
                  trial.get('restart_path')]
    if not candidates:
        return {'source': 'fresh', 'continuation_parent': None}
    parent = min(candidates, key=lambda trial: abs(trial['Ee'] - target_ee))
    return {'source': 'continuation', 'continuation_parent': {
        'system_label': state['system']['system_label'],
        'Ee_parent': parent['Ee'],
        'seed': parent.get('seed'),
        'restart_path': parent['restart_path'],
        'completed_steps': parent.get('completed_steps'),
        'completed_time': parent.get('completed_time'),
        'parent_sha256': parent.get('restart_sha256'),
    }}


def recommendation(state):
    refresh_classifications(state)
    protocol = state['protocol']
    if len(state['trials']) >= protocol['max_evaluations']:
        return {'status': 'MAX_EVALUATIONS_REACHED'}
    target = protocol['target_probability']
    for trial in state['trials']:
        if (trial['classification'] == 'INTERMEDIATE' and
                abs(trial['P_wrap_any'] - target) <= protocol['probability_tolerance']):
            return {'status': 'TARGET_PROBABILITY_REACHED', 'trial': trial}
    current = bracket(state)
    if current:
        low, high = current
        width = high['Ee'] - low['Ee']
        if width <= protocol['delta_ee_target']:
            return {'status': 'BRACKET_WIDTH_REACHED', 'low': low, 'high': high}
        next_ee = (low['Ee'] + high['Ee']) / 2.0
        return {'status': 'REFINE_BRACKET', 'Ee': next_ee, 'low': low, 'high': high,
                **recommended_source(state, next_ee)}
    trials = state['trials']
    if not trials:
        return {'status': 'EVALUATE_INITIAL_LOW', 'Ee': state['initial_bounds']['Ee_low'],
                **recommended_source(state, state['initial_bounds']['Ee_low'])}
    initial_high = state['initial_bounds']['Ee_high']
    if not any(math.isclose(trial['Ee'], initial_high, abs_tol=1e-12) for trial in trials):
        return {'status': 'EVALUATE_INITIAL_HIGH', 'Ee': initial_high,
                **recommended_source(state, initial_high)}
    clear_below = [trial for trial in trials if trial['classification'] == 'CLEARLY_NONPERCOLATED']
    clear_above = [trial for trial in trials if trial['classification'] == 'CLEARLY_PERCOLATED']
    if clear_below and not clear_above:
        next_ee = max(trial['Ee'] for trial in trials) + protocol['expansion_step']
        return {'status': 'EXPAND_UPWARD', 'Ee': next_ee, **recommended_source(state, next_ee)}
    if clear_above and not clear_below:
        next_ee = min(trial['Ee'] for trial in trials) - protocol['expansion_step']
        return {'status': 'EXPAND_DOWNWARD', 'Ee': next_ee, **recommended_source(state, next_ee)}
    return {'status': 'NEED_THRESHOLD_SAMPLING'}


def summary_metric(summary, name):
    value = summary['ensemble_replica_statistics'].get(name)
    return value['mean'] if value else None, value.get('ci95_half_width') if value else None


def register_trial(state, arguments):
    trial = {
        'Ee': arguments.ee,
        'run_class': arguments.run_class,
        'source': arguments.source,
        'replica_count': arguments.replica_count,
        'production_duration': arguments.production_duration,
        'equilibration_status': arguments.equilibration_status,
        'stationarity_blocks': load_json(arguments.stationarity_blocks)
        if arguments.stationarity_blocks else None,
        'continuation_parent': load_json(arguments.continuation_parent)
        if arguments.continuation_parent else None,
        'restart_path': arguments.restart_path,
        'restart_sha256': arguments.restart_sha256,
        'seed': arguments.seed,
        'completed_steps': arguments.completed_steps,
        'completed_time': arguments.completed_time,
        'provenance_paths': arguments.provenance_path or [],
    }
    if arguments.summary:
        summary = load_json(arguments.summary)
        trial['replica_count'] = len(summary.get('replica_summaries', []))
        for metric in ('P_wrap_any', 'P_wrap_xyz', 'mean_wrapping_fraction',
                       'mean_largest_component_fraction', 'mean_finite_cluster_susceptibility'):
            mean, ci = summary_metric(summary, metric)
            trial[metric] = mean
            if metric == 'P_wrap_any':
                trial['P_wrap_any_ci95_half_width'] = ci
        trial['analysis_summary'] = str(arguments.summary)
    else:
        trial.update({
            'P_wrap_any': arguments.p_wrap_any,
            'P_wrap_any_ci95_half_width': arguments.p_wrap_ci95,
            'P_wrap_xyz': arguments.p_wrap_xyz,
            'mean_wrapping_fraction': arguments.wrapping_fraction,
            'mean_largest_component_fraction': arguments.largest_component_fraction,
            'mean_finite_cluster_susceptibility': arguments.finite_susceptibility,
        })
    if trial['P_wrap_any'] is None:
        raise ValueError('a P_wrap_any summary or --p-wrap-any is required')
    if any(math.isclose(existing['Ee'], trial['Ee'], abs_tol=1e-12)
           for existing in state['trials']):
        raise ValueError('duplicate Ee trial {}'.format(ee_key(trial['Ee'])))
    state['trials'].append(trial)
    refresh_classifications(state)


def update_index(state_path, state, index_path=None):
    index_path = Path(index_path) if index_path else Path(state_path).parents[1] / 'search_index.csv'
    rows = []
    if index_path.exists():
        with open(index_path, newline='', encoding='utf-8') as source:
            rows = list(csv.DictReader(source))
    label = state['system']['system_label']
    rows = [row for row in rows if row['system_label'] != label]
    current = bracket(state)
    recommendation_state = recommendation(state)['status']
    rows.append({
        'system_label': label,
        'arms_per_star': state['system']['arms_per_star'],
        'arm_length': state['system']['arm_length'],
        'polymer_density': state['system']['polymer_density'],
        'Ee_low': current[0]['Ee'] if current else '',
        'Ee_high': current[1]['Ee'] if current else '',
        'Ee_50_estimate': (current[0]['Ee'] + current[1]['Ee']) / 2.0 if current else '',
        'status': recommendation_state,
        'state_path': str(state_path),
    })
    fields = list(rows[0])
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, 'w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def neighbor_proposal(state, index_path):
    if not Path(index_path).exists():
        return None
    with open(index_path, newline='', encoding='utf-8') as source:
        rows = list(csv.DictReader(source))
    candidates = [row for row in rows if row.get('Ee_50_estimate')]
    if not candidates:
        return None
    system = state['system']
    def rank(row):
        same_arms = row['arms_per_star'] == str(system['arms_per_star'])
        same_length = row['arm_length'] == str(system['arm_length'])
        density_distance = abs(float(row['polymer_density']) - system['polymer_density'])
        return (0 if same_arms and same_length else 1 if same_arms else 2,
                density_distance, abs(int(row['arm_length']) - system['arm_length']))
    best = min(candidates, key=rank)
    return {'neighbor_system': best['system_label'], 'Ee_low': float(best['Ee_low']),
            'Ee_high': float(best['Ee_high']), 'Ee_50_estimate': float(best['Ee_50_estimate']),
            'heuristic_only': True}


def print_report(state, index_path=None):
    refresh_classifications(state)
    system = state['system']
    print('System: {}'.format(system['system_label']))
    print('Target: P_wrap_any = {}'.format(state['protocol']['target_probability']))
    print('Ea validation: {}'.format(scientific_validation_status(state)))
    print()
    print('Ee       P_wrap_any   CI95       class                     source')
    for trial in sorted(state['trials'], key=lambda value: value['Ee']):
        ci = trial.get('P_wrap_any_ci95_half_width')
        print('{:<8.4g} {:<12.6g} {:<10} {:<25} {}'.format(
            trial['Ee'], trial['P_wrap_any'], '' if ci is None else '{:.3g}'.format(ci),
            trial['classification'], trial['source']))
    current = bracket(state)
    if current:
        print('\nCurrent bracket: [{:.6g}, {:.6g}]'.format(current[0]['Ee'], current[1]['Ee']))
    proposal = recommendation(state)
    print('Next action: {}'.format(proposal['status']))
    if 'Ee' in proposal:
        print('Suggested Ee: {:.12g}'.format(proposal['Ee']))
        print('Suggested initialization: {}'.format(proposal.get('source', 'fresh')))
    if index_path:
        neighbor = neighbor_proposal(state, index_path)
        if neighbor:
            print('Neighbor proposal (heuristic only): {} [{:.6g}, {:.6g}]'.format(
                neighbor['neighbor_system'], neighbor['Ee_low'], neighbor['Ee_high']))


def write_trial_request(path, state):
    proposal = recommendation(state)
    if 'Ee' not in proposal:
        raise ValueError('no new Ee trial is currently recommended')
    request = {
        'run_class': 'screening',
        'Ee_target': proposal['Ee'],
        'Ea_search': state['protocol']['Ea_search'],
        'nu0': state['protocol']['nu0'],
        'reaction_geometry': state['protocol']['reaction_geometry'],
        'continuation': proposal.get('continuation_parent'),
        're_equilibration_required': True,
        'stationarity_observables': ['P_wrap_any', 'temporary_bonds', 'inter_bonds',
                                     'intra_bonds', 'mean_k_neighbor',
                                     'largest_component_fraction'],
        'note': 'Request only. No MD command is launched by this planner.',
    }
    save_json(path, request)


def self_test():
    parser = argparse.ArgumentParser()
    parser.add_argument('--system-label', default='test')
    parser.add_argument('--arms', type=int, default=4)
    parser.add_argument('--arm-length', type=int, default=10)
    parser.add_argument('--polymer-density', type=float, default=.8)
    parser.add_argument('--total-density', type=float, default=.85)
    parser.add_argument('--number-of-stars', type=int, default=1000)
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--box-generation-protocol', default='test')
    parser.add_argument('--target-probability', type=float, default=.5)
    parser.add_argument('--delta-ee-target', type=float, default=.5)
    parser.add_argument('--probability-tolerance', type=float, default=.02)
    parser.add_argument('--max-evaluations', type=int, default=20)
    parser.add_argument('--expansion-step', type=float, default=1.0)
    parser.add_argument('--min-replicas', type=int, default=2)
    parser.add_argument('--ea-search', type=float, default=2.0)
    parser.add_argument('--ea-physical', type=float, default=4.0)
    parser.add_argument('--nu0', type=float, default=20.0)
    parser.add_argument('--reaction-geometry', default='test')
    parser.add_argument('--screening-replicas', type=int, default=2)
    parser.add_argument('--threshold-replicas', type=int, default=5)
    parser.add_argument('--screening-steps', type=int, default=1000)
    parser.add_argument('--threshold-steps', type=int, default=2000)
    parser.add_argument('--topology-every', type=int, default=100)
    parser.add_argument('--ee-low', type=float, default=4.0)
    parser.add_argument('--ee-high', type=float, default=8.0)
    arguments = parser.parse_args([])
    state = new_state(arguments)
    assert recommendation(state)['status'] == 'EVALUATE_INITIAL_LOW'
    for ee, probability in ((4.0, .1), (8.0, .9)):
        state['trials'].append({'Ee': ee, 'P_wrap_any': probability,
                                'P_wrap_any_ci95_half_width': .05, 'replica_count': 3,
                                'equilibration_status': 'ADMITTED', 'source': 'fresh'})
    refresh_classifications(state)
    assert recommendation(state)['status'] == 'REFINE_BRACKET'
    assert recommendation(state)['Ee'] == 6.0
    state['trials'].append({'Ee': 6.0, 'P_wrap_any': .3, 'P_wrap_any_ci95_half_width': .05,
                            'replica_count': 3, 'equilibration_status': 'ADMITTED', 'source': 'continuation'})
    refresh_classifications(state)
    assert bracket(state)[0]['Ee'] == 6.0
    state['trials'][-1]['P_wrap_any'] = .7
    refresh_classifications(state)
    assert bracket(state)[1]['Ee'] == 6.0
    state['trials'][-1]['equilibration_status'] = 'NONSTATIONARY'
    refresh_classifications(state)
    assert state['trials'][-1]['classification'] == 'INSUFFICIENT_SAMPLING'
    upward = new_state(arguments)
    for ee in (4.0, 8.0):
        upward['trials'].append({'Ee': ee, 'P_wrap_any': .1,
                                 'P_wrap_any_ci95_half_width': .02, 'replica_count': 3,
                                 'equilibration_status': 'ADMITTED', 'source': 'fresh'})
    refresh_classifications(upward)
    assert recommendation(upward)['status'] == 'EXPAND_UPWARD'
    downward = new_state(arguments)
    for ee in (4.0, 8.0):
        downward['trials'].append({'Ee': ee, 'P_wrap_any': .9,
                                   'P_wrap_any_ci95_half_width': .02, 'replica_count': 3,
                                   'equilibration_status': 'ADMITTED', 'source': 'fresh'})
    refresh_classifications(downward)
    assert recommendation(downward)['status'] == 'EXPAND_DOWNWARD'
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'search_state.json'
        save_json(path, state)
        restored = load_json(path)
        validate_state(restored)
        assert scientific_validation_status(restored).startswith('accelerated Ea scientifically unvalidated')
        write_trial_request(Path(directory) / 'request.json', restored)
        index = Path(directory) / 'search_index.csv'
        update_index(path, restored, index)
        assert neighbor_proposal(restored, index)['neighbor_system'] == 'test'
        restored['trials'][0]['restart_path'] = 'restart-at-Ee4'
        assert recommended_source(restored, 5.0)['source'] == 'continuation'
        try:
            register_trial(restored, argparse.Namespace(
                ee=4.0, run_class='screening', source='fresh', replica_count=3,
                production_duration=0.0, equilibration_status='ADMITTED',
                stationarity_blocks=None, continuation_parent=None, restart_path=None,
                restart_sha256=None, seed=None, completed_steps=None, completed_time=None,
                provenance_path=None, summary=None, p_wrap_any=.2, p_wrap_ci95=.02,
                p_wrap_xyz=None, wrapping_fraction=None, largest_component_fraction=None,
                finite_susceptibility=None))
        except ValueError:
            pass
        else:
            raise AssertionError('duplicate Ee trial accepted')
    print('P4.8B SEARCH SELF_TEST PASS')


def add_common_system_arguments(parser):
    parser.add_argument('--system-label', required=True)
    parser.add_argument('--arms', type=int, required=True)
    parser.add_argument('--arm-length', type=int, required=True)
    parser.add_argument('--polymer-density', type=float, required=True)
    parser.add_argument('--total-density', type=float, required=True)
    parser.add_argument('--number-of-stars', type=int, required=True)
    parser.add_argument('--temperature', type=float, required=True)
    parser.add_argument('--box-generation-protocol', required=True)
    parser.add_argument('--ee-low', type=float, required=True)
    parser.add_argument('--ee-high', type=float, required=True)
    parser.add_argument('--ea-search', type=float, required=True)
    parser.add_argument('--ea-physical', type=float, required=True)
    parser.add_argument('--nu0', type=float, required=True)
    parser.add_argument('--reaction-geometry', required=True)
    parser.add_argument('--target-probability', type=float, default=.5)
    parser.add_argument('--delta-ee-target', type=float, default=.5)
    parser.add_argument('--probability-tolerance', type=float, default=.05)
    parser.add_argument('--max-evaluations', type=int, default=20)
    parser.add_argument('--expansion-step', type=float, default=1.0)
    parser.add_argument('--min-replicas', type=int, default=2)
    parser.add_argument('--screening-replicas', type=int, default=2)
    parser.add_argument('--threshold-replicas', type=int, default=5)
    parser.add_argument('--screening-steps', type=int, default=0)
    parser.add_argument('--threshold-steps', type=int, default=0)
    parser.add_argument('--topology-every', type=int, default=10000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    commands = parser.add_subparsers(dest='command')
    init = commands.add_parser('init')
    init.add_argument('--state', required=True, type=Path)
    add_common_system_arguments(init)
    register = commands.add_parser('register')
    register.add_argument('--state', required=True, type=Path)
    register.add_argument('--ee', type=float, required=True)
    register.add_argument('--summary', type=Path)
    register.add_argument('--p-wrap-any', type=float)
    register.add_argument('--p-wrap-ci95', type=float)
    register.add_argument('--p-wrap-xyz', type=float)
    register.add_argument('--wrapping-fraction', type=float)
    register.add_argument('--largest-component-fraction', type=float)
    register.add_argument('--finite-susceptibility', type=float)
    register.add_argument('--replica-count', type=int, default=0)
    register.add_argument('--production-duration', type=float, default=0.0)
    register.add_argument('--run-class', choices=RUN_CLASSES, default='screening')
    register.add_argument('--source', choices=SOURCES, default='fresh')
    register.add_argument('--equilibration-status', choices=STATIONARITY, default='UNKNOWN')
    register.add_argument('--stationarity-blocks', type=Path)
    register.add_argument('--continuation-parent', type=Path)
    register.add_argument('--restart-path')
    register.add_argument('--restart-sha256')
    register.add_argument('--seed', type=int)
    register.add_argument('--completed-steps', type=int)
    register.add_argument('--completed-time', type=float)
    register.add_argument('--provenance-path', action='append')
    register.add_argument('--index', type=Path)
    report = commands.add_parser('report')
    report.add_argument('--state', required=True, type=Path)
    report.add_argument('--index', type=Path)
    request = commands.add_parser('write-request')
    request.add_argument('--state', required=True, type=Path)
    request.add_argument('--output', required=True, type=Path)
    validate_ea = commands.add_parser('set-ea-validation')
    validate_ea.add_argument('--state', required=True, type=Path)
    validate_ea.add_argument('--status', choices=EA_STATUS, required=True)
    validate_ea.add_argument('--values', type=float, nargs='*', default=[])
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if not arguments.command:
        parser.error('choose init, register, report, write-request, or set-ea-validation')
    if arguments.command == 'init':
        if arguments.ee_high <= arguments.ee_low:
            parser.error('--ee-high must exceed --ee-low')
        state = new_state(arguments)
        save_json(arguments.state, state)
        update_index(arguments.state, state)
    else:
        state = load_json(arguments.state)
        validate_state(state)
        if arguments.command == 'register':
            register_trial(state, arguments)
            save_json(arguments.state, state)
            update_index(arguments.state, state, arguments.index)
        elif arguments.command == 'report':
            print_report(state, arguments.index)
        elif arguments.command == 'write-request':
            write_trial_request(arguments.output, state)
        else:
            state['protocol']['ea_invariance_status'] = arguments.status
            state['protocol']['ea_validation_values'] = arguments.values
            save_json(arguments.state, state)


if __name__ == '__main__':
    main()
