#!/usr/bin/env python3
"""Authenticate protected bytes, historical source transitions and all formal acceptances."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
START = 'b8f518d49c9b00f7d957bc42fcaf0a34a9317c82'
CHANGED = {'examples/KG_Assoc/' + name for name in (
    'kg_assoc_stars.cu', 'kg_assoc_validation_evidence.cuh', 'kg_assoc_validation_tests.cuh')}
sys.path.insert(0, str(REPO / 'examples/KG_Assoc/campaign'))
import kg_assoc_e2 as e2
import kg_assoc_e2_registry as registry


def verify():
    baseline = json.loads((HERE / 'BASELINE_SHA256.json').read_text())
    preserved = 0
    transitions = {}
    for name, expected in baseline.items():
        path = Path(name)
        relative = str(path.relative_to(REPO))
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if relative in CHANGED:
            original = subprocess.check_output(['git', 'show', START + ':' + relative], cwd=REPO)
            assert hashlib.sha256(original).hexdigest() == expected
            transitions[relative] = dict(before=expected, after=actual)
        else:
            assert actual == expected, name
            preserved += 1
    assert set(transitions) == CHANGED
    prior = HERE.parent / 'e2_ea_transfer_gpu_diagnostic_retest_20261016'
    records = json.loads((prior / 'PREFLIGHT.json').read_text())['acceptance_records']
    assert len(records) == 12
    for item in records:
        path = REPO / item['record']
        assert e2.campaign.sha256(path) == item['sha256']
        registry.exclusive_validate(e2.campaign.load_json(path), [e2.system_by_id(item['system'])])
    return dict(starting_sha=START, preserved_bindings=preserved, source_transitions=transitions,
                formal_acceptances_validated=len(records), GPU_calls=0, additional_MD_steps=0)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, sort_keys=True))
