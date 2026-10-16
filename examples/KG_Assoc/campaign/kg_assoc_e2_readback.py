"""CPU audit of validation-only initial device evidence; never invokes an executable."""
import json
import math
from pathlib import Path
import re
import struct

import kg_assoc_campaign as campaign


def require(condition, message):
    if not condition:
        raise ValueError('initial device readback: ' + message)


def represented_position(position, bounds):
    def real(value):
        return struct.unpack('f', struct.pack('f', value))[0]
    result = []
    for axis, coordinate in zip('xyz', position):
        lo, hi = bounds[axis]
        length = real(hi - lo)
        center = real(.5 * (lo + hi))
        value = real(real(coordinate) - center)
        offset = math.floor(real(real(value * real(-1.0 / length)) + real(.5)))
        result.append(real(value + real(offset * length)))
    return result


def check(path, entry, parent, initial_pairs):
    lines = Path(path).read_text().splitlines()
    header = '\n'.join(line for line in lines if line.startswith('#') and not line.startswith('# build '))
    fields = dict(re.findall(r'\b(\w+)=([^\s]+)', header))
    for key, expected in dict(validation_evidence_version='1', initial_device_readback_version='1',
            branch_age='0', mapping_valid='1', readback_pass='1', real_bytes='4', rounding_mode='0',
            absolute_step=str(entry['start_step']), chemistry_sweep='0',
            branch=entry['lineage']['branch_id'], max_position_mic_error='0', max_velocity_error='0').items():
        require(fields.get(key) == expected, key + ' differs')
    executable = Path(entry['command'][0]).resolve()
    manifest_path = executable.parent / 'manifest.json'
    require(Path(fields['executable']).resolve() == executable and
            Path(fields['build_manifest']).resolve() == manifest_path, 'build paths differ')
    build = campaign.load_json(manifest_path)
    recorded_build = json.loads('\n'.join(line[len('# build '):] for line in lines
                                         if line.startswith('# build ')))
    require(recorded_build == build and build['executable_sha256'][str(executable)] ==
            campaign.sha256(executable), 'build identity differs')
    partners = {particle: -1 for particle in parent['atoms']}
    for first, second in initial_pairs:
        partners[first], partners[second] = second - 1, first - 1
    rows = [line.split() for line in lines if line.startswith('particle ')]
    require(len(rows) == len(parent['atoms']) == int(fields['particles']), 'particle count differs')
    lengths = [hi - lo for lo, hi in (parent['bounds'][axis] for axis in 'xyz')]
    for zero_id, row in enumerate(rows):
        require(len(row) == 20, 'malformed particle row')
        expected_id, actual_id, molecule, kind = map(int, row[1:5])
        actual_kind = float(row[5])
        expected_partner, actual_partner = map(int, row[6:8])
        particle = zero_id + 1
        require(expected_id == actual_id == zero_id and
                (molecule, kind) == parent['atoms'][particle] and kind == actual_kind,
                'particle identity differs')
        require(expected_partner == actual_partner == partners[particle], 'chemical partner differs')
        values = list(map(float, row[8:]))
        require(all(math.isfinite(value) for value in values), 'nonfinite state')
        require(values[:3] == represented_position(parent['positions'][particle], parent['bounds']),
                'expected coordinates differ from authenticated input representation')
        expected_velocity = [struct.unpack('f', struct.pack('f', value))[0]
                             for value in parent['velocities'][particle]]
        require(values[6:9] == values[9:] == expected_velocity, 'velocity differs')
        for expected, actual, length in zip(values[:3], values[3:6], lengths):
            delta = actual - expected
            require(delta - length * round(delta / length) == 0, 'device coordinates differ')
    return dict(status='valid', particles=len(rows), sha256=campaign.sha256(Path(path)))
