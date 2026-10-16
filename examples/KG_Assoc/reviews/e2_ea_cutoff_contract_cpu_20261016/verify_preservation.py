#!/usr/bin/env python3
"""Authenticate protected bytes and old source identities without rewriting old manifests."""
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
START = '2f5c991bd354eb3c599f8cb2fed36ed2b5c9f6d2'
AUTHORIZED = {
    'examples/KG_Assoc/Makefile',
    'examples/KG_Assoc/kg_assoc_stars.cu',
    'examples/KG_Assoc/kg_assoc_candidate_oracle.cuh',
    'examples/KG_Assoc/kg_assoc_candidates_test.cu',
    'examples/KG_Assoc/campaign/kg_assoc_e2_validate.py',
    'examples/KG_Assoc/campaign/test_e2_transfer.py',
}


def verify():
    baseline = json.loads((HERE / 'BASELINE_SHA256.json').read_text())
    transitions = []
    for name, expected in baseline.items():
        path = Path(name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual == expected:
            continue
        relative = str(path.relative_to(REPO))
        assert relative in AUTHORIZED, 'protected evidence changed: ' + name
        prior = subprocess.check_output(['git', 'show', START + ':' + relative], cwd=REPO)
        assert hashlib.sha256(prior).hexdigest() == expected, 'historical source identity differs'
        transitions.append(dict(path=relative, historical_git_sha=START,
                                prior_sha256=expected, current_sha256=actual))
    return dict(preserved_bindings=len(baseline), unchanged_live_bindings=len(baseline)-len(transitions),
                authenticated_source_transitions=transitions,
                simulation_candidate_search_changed=False, frozen_physics_changed=False,
                prior_dossiers_and_acceptance_records_changed=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, sort_keys=True))
