#!/usr/bin/env python3
"""Reproduce the optimized host defect and repair using immutable parent/device evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ASSOC = REPO / 'examples/KG_Assoc'
sys.path.insert(0, str(ASSOC / 'campaign'))
import kg_assoc_e2 as e2


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    prior = HERE.parent / 'e2_ea_transfer_gpu_diagnostic_retest_20261016'
    e2.check_hashes(json.loads((prior / 'NEW_OUTPUTS_SHA256.json').read_text()))
    report = json.loads((prior / 'RESULTS.json').read_text())
    entry = report['histories'][0]
    assert entry['status'] == 'failed_before_MD' and entry['Ea'] == 4 and entry['replica'] == 1
    e2.check_hashes(entry['parent']['sha256'])
    parent = e2.campaign.parse_lammps_data(entry['parent']['snapshot'])
    saved = Path(entry['device_audit']['recorded_header']['executable'])  # Authenticated separately.
    assert digest(saved) == json.loads((saved.parent / 'manifest.json').read_text())['executable_sha256'][str(saved)]
    saved = Path(entry['attempt']) / 'r001/state.initial_device_validation.tsv'
    assert digest(saved) == entry['device_audit']['sha256']
    fixture = output / 'parent_float32.tsv'
    with fixture.open('x') as stream:
        stream.write(entry['device_audit']['recorded_header']['box'].replace(',', ' ') + '\n')
        for particle_id, velocity in sorted(parent['velocities'].items()):
            represented = [struct.unpack('f', struct.pack('f', x))[0] for x in velocity]
            stream.write(' '.join(map(str, [particle_id - 1, *velocity, *represented])) + '\n')
    command = shlex.split(subprocess.check_output(
        ['make', '-n', '-B', 'kg_assoc_stars_candidate_smoke'], cwd=ASSOC, text=True).strip())
    command[command.index('kg_assoc_stars.cu')] = str(HERE / 'rounding_probe.cu')
    command[command.index('-o') + 1] = str(output / 'rounding_probe')
    with (output / 'compile.log').open('x') as stream:
        subprocess.run(command, cwd=ASSOC, stdout=stream, stderr=subprocess.STDOUT, check=True)
    run = [str(output / 'rounding_probe'), str(fixture), str(saved), str(output / 'corrected_host_replay.tsv')]
    result = subprocess.run(run, text=True, capture_output=True)
    (output / 'probe.log').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stderr
    # Independently check every corrected expected and saved actual value after serialization.
    rows = [x.split() for x in (output / 'corrected_host_replay.tsv').read_text().splitlines()
            if x.startswith('particle ')]
    assert len(rows) == 43563
    for row in rows:
        values = parent['velocities'][int(row[1]) + 1]
        expected = [struct.unpack('f', struct.pack('f', x))[0] for x in values]
        assert list(map(float, row[14:17])) == list(map(float, row[17:20])) == expected
    evidence = dict(compile_argv=command, run_argv=run, stdout=result.stdout,
                    parent=entry['parent'], saved_readback=str(saved), saved_readback_sha256=digest(saved),
                    particles=len(rows), exact_components=3 * len(rows), GPU_calls=0,
                    artifact_sha256={str(p): digest(p) for p in output.iterdir() if p.is_file()},
                    probe_source_sha256=digest(HERE / 'rounding_probe.cu'))
    (output / 'PROBE.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
    print(result.stdout, end='')


if __name__ == '__main__':
    main()
