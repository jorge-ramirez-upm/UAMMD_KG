#!/usr/bin/env python3
"""Run only host tests and validation modes; never launch a simulation or CUDA context."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ASSOC = REPO / 'examples/KG_Assoc'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
build = args.build.resolve()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
env = dict(os.environ, PYTHONPATH=':'.join(str(ASSOC / x) for x in (
    'campaign', 'analysis', 'reviews/e2_rp040_ee8_6m_20261014',
    'reviews/e2_rp040_ee8_8m_20261014', 'reviews/e2_ea_transfer_gpu_diagnostic_retest_20261016')),
    PYTHONWARNINGS='ignore::ResourceWarning', KG_ASSOC_TRANSFER_HOST_EXE=str(build / 'kg_assoc_stars'))
prior = HERE.parent / 'e2_ea_transfer_gpu_diagnostic_retest_20261016'
modules = sorted(set(re.findall(r'\((test_\w+)\.', (prior / 'REGRESSION_TESTS.log').read_text())))
commands = [
    ('CANDIDATE_CPU_TESTS', [str(build / 'kg_assoc_candidates_test')]),
    ('NATIVE_HOST_SELF_TESTS', [str(build / 'kg_assoc_stars'), '--self-test']),
    ('SMOKE_HOST_SELF_TESTS', [str(build / 'kg_assoc_stars_candidate_smoke'), '--self-test']),
    ('REGRESSION_TESTS', [sys.executable, '-m', 'unittest', '-v', *modules]),
    ('TRANSFER_TESTS', [sys.executable, '-m', 'unittest', '-v', 'test_e2_transfer']),
    ('FORENSIC_TESTS', [sys.executable, '-m', 'unittest', '-v', 'test_diagnostic_analysis']),
]
for item in json.loads((prior / 'PREPARED.json').read_text()):
    plan = json.loads((Path(item['attempt']) / 'plan.json').read_text())
    for entry in plan['histories']:
        command = entry['command'].copy()
        command[0] = str(build / 'kg_assoc_stars_candidate_smoke')
        command[command.index('--output') + 1] = str(output / (plan['system']['system_id'] + f"_r{entry['replica']:03d}"))
        command.append('--validate-initial-state')
        commands.append((plan['system']['system_id'] + f"_r{entry['replica']:03d}_HOST_INIT", command))
results = []
for name, command in commands:
    command_env = env
    if name == 'FORENSIC_TESTS':
        # This historical suite imports its sibling reproduce.py by module name.
        command_env = dict(env, PYTHONPATH=str(prior) + ':' + env['PYTHONPATH'])
    with (output / (name + '.log')).open('x') as stream:
        process = subprocess.run(command, cwd=REPO, env=command_env,
                                 stdout=stream, stderr=subprocess.STDOUT)
    results.append(dict(name=name, argv=command, returncode=process.returncode))
    print(name, process.returncode, flush=True)
    if process.returncode:
        break
(output / 'CPU_CHECKS.log').write_text(json.dumps(results, indent=2) + '\n')
assert len(results) == len(commands) and all(row['returncode'] == 0 for row in results)
