#!/usr/bin/env python3
"""Compare static and kinetic Ea-series observables without frame pseudo-replication."""

import argparse
import json
from pathlib import Path


def load_json(path):
    with open(path, encoding='utf-8') as source:
        return json.load(source)


def interval(observation):
    half_width = observation.get('ci95_half_width')
    if half_width is None:
        return None
    return observation['mean'] - half_width, observation['mean'] + half_width


def compatibility(observations):
    intervals = [interval(observation) for observation in observations]
    if any(value is None for value in intervals):
        return 'INSUFFICIENT_REPLICA_UNCERTAINTY'
    lower = max(value[0] for value in intervals)
    upper = min(value[1] for value in intervals)
    return 'COMPATIBLE_INTERVALS' if lower <= upper else 'POSSIBLE_SYSTEMATIC_DEPENDENCE'


def compare(rows):
    static_names = sorted(set().union(*(row.get('static', {}) for row in rows)))
    kinetic_names = sorted(set().union(*(row.get('kinetic', {}) for row in rows)))
    static = {}
    for name in static_names:
        values = [row['static'][name] for row in rows if name in row.get('static', {})]
        static[name] = {'status': compatibility(values), 'by_Ea': [
            {'Ea': row['Ea'], **row['static'][name]} for row in rows if name in row.get('static', {})]}
    kinetic = {}
    for name in kinetic_names:
        kinetic[name] = {'by_Ea': [
            {'Ea': row['Ea'], **row['kinetic'][name]} for row in rows if name in row.get('kinetic', {})]}
    statuses = [value['status'] for value in static.values()]
    recommendation = ('PASS_CANDIDATE' if statuses and all(status == 'COMPATIBLE_INTERVALS'
                      for status in statuses) else 'REVIEW_REQUIRED')
    return {'static_observables': static, 'kinetic_observables': kinetic,
            'recommendation': recommendation,
            'interpretation': ('Replica-level CI compatibility is evidence to review, not a '
                               'proof of identical equilibrium distributions.')}


def self_test():
    rows = [
        {'Ea': 2.0, 'static': {'P_wrap_any': {'mean': .50, 'ci95_half_width': .08}},
         'kinetic': {'accepted_reaction_rate': {'mean': 2.0, 'ci95_half_width': .1}}},
        {'Ea': 4.0, 'static': {'P_wrap_any': {'mean': .54, 'ci95_half_width': .08}},
         'kinetic': {'accepted_reaction_rate': {'mean': 1.0, 'ci95_half_width': .1}}},
    ]
    result = compare(rows)
    assert result['static_observables']['P_wrap_any']['status'] == 'COMPATIBLE_INTERVALS'
    assert result['recommendation'] == 'PASS_CANDIDATE'
    rows[1]['static']['P_wrap_any'] = {'mean': .9, 'ci95_half_width': .02}
    assert compare(rows)['recommendation'] == 'REVIEW_REQUIRED'
    print('P4.8B EA_INVARIANCE SELF_TEST PASS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    if not arguments.input or not arguments.output:
        parser.error('--input and --output are required')
    rows = load_json(arguments.input)
    if not isinstance(rows, list) or not rows or any('Ea' not in row for row in rows):
        parser.error('--input must be a nonempty JSON list with Ea entries')
    output = compare(rows)
    with open(arguments.output, 'w', encoding='utf-8') as target:
        json.dump(output, target, indent=2)
        target.write('\n')


if __name__ == '__main__':
    main()
