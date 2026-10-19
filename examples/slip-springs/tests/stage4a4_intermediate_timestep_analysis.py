#!/usr/bin/env python3
"""Read-only three-timestep Stage 4A.4 comparison after the medium runs exist."""
import argparse
import csv
import json
import math
from pathlib import Path

import stage4a4_dynamic_timestep_analysis as dynamic
import stage4a4_static_drift_analysis as static


def histogram(directory, reference_path):
    directory = Path(directory)
    reference = json.loads(Path(reference_path).read_text())
    chains, springs = 512, reference['springs']
    counts = [[0]*33 for _ in range(chains)]
    frames = None
    with (directory/'bond_statistics.csv').open(newline='') as handle:
        for row in csv.DictReader(handle):
            chain = int(row['chain']); current = int(row['frames'])
            if not 0 <= chain < chains: raise ValueError('invalid histogram chain')
            if frames is None: frames = current
            if current != frames: raise ValueError('nonuniform histogram frame count')
            for index in range(33): counts[chain][index] += int(row['bin'+str(index)])
    if frames is None: raise ValueError('missing bond histogram')
    denominator = frames * springs
    probability = [sum(row[index] for row in counts)/chains/denominator for index in range(33)]
    per_chain = [[row[index]/denominator for row in counts] for index in range(33)]
    reference_probability = reference['histogram']['probability'] + [max(0., 1-sum(reference['histogram']['probability']))]
    difference = [probability[index]-reference_probability[index] for index in range(33)]
    se = [math.sqrt(sum((value-sum(row)/chains)**2 for value in row)/(chains-1)/chains) for row in per_chain]
    return {'frames_per_bond': frames, 'probability': probability, 'reference_probability': reference_probability,
            'difference': difference, 'chain_se': se, 'total_variation': .5*sum(abs(value) for value in difference),
            'overflow_probability': probability[32]}


def cost(directory):
    metadata = json.loads((Path(directory)/'metadata.json').read_text())
    stress = json.loads((Path(directory)/'stress_metadata.json').read_text())
    return {key: metadata[key] for key in ('dt', 'steps', 'integration_seconds', 'production_wall_seconds',
                                            'integration_ns_per_bead_step', 'overall_ns_per_bead_step', 'device_bytes')}, {
        key: stress[key] for key in ('estimated_bytes', 'gpu_stress_seconds', 'stress_transfer_seconds',
                                      'cpu_correlation_seconds', 'producer_blocked_seconds')}


def analyze(small_dir, medium_dir, large_dir, small_ref, medium_ref, large_ref):
    directories = {'small': Path(small_dir), 'medium': Path(medium_dir), 'large': Path(large_dir)}
    references = {'small': Path(small_ref), 'medium': Path(medium_ref), 'large': Path(large_ref)}
    static_result = {name: static.run(directories[name], references[name]) for name in directories}
    dynamic_data = {name: dynamic.load(directories[name]) for name in directories}
    baseline = dynamic_data['small']['rows'][0]
    amplitude = {}
    for name in ('medium', 'large'):
        row = dynamic_data[name]['rows'][0]
        delta, se = row['H']-baseline['H'], math.hypot(row['H_se'], baseline['H_se'])
        amplitude[name] = {'large_minus_small': delta, 'unpaired_se': se,
                           'relative_change': delta/baseline['H'], 'relative_se': se/baseline['H'],
                           'prospective_only': 'No H(0) acceptance threshold is asserted by this analysis.'}
    return {'status': 'completed-input-analysis', 'static': static_result,
            'histograms': {name: histogram(directories[name], references[name]) for name in directories},
            'dynamic_vs_small': {'medium': dynamic.compare(dynamic_data['small'], dynamic_data['medium']),
                                 'large': dynamic.compare(dynamic_data['small'], dynamic_data['large'])},
            'h0_amplitude_prospective_diagnostic': amplitude,
            'cost': {name: dict(simulator=cost(directories[name])[0], stress=cost(directories[name])[1]) for name in directories}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('small', 'medium', 'large'):
        parser.add_argument('--'+name, type=Path, required=True)
        parser.add_argument('--'+name+'-reference', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): parser.error('refusing to overwrite report')
    args.report.write_text(json.dumps(analyze(args.small, args.medium, args.large, args.small_reference,
                                               args.medium_reference, args.large_reference), indent=2, sort_keys=True)+'\n')
    print(args.report)


if __name__ == '__main__': main()
