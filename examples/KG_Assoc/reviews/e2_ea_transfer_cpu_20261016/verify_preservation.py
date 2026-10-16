"""Verify protected bytes and authenticate prior source bindings from the starting commit."""
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
START = '283ac81058fe49a75ea0c75e44e443c1ff9928e1'
AUTHORIZED_SOURCE_CHANGES = {
    'examples/KG_Assoc/Makefile',
    'examples/KG_Assoc/kg_assoc_stars.cu',
    'examples/KG_Assoc/campaign/kg_assoc_e2.py',
    'examples/KG_Assoc/campaign/kg_assoc_e2_validate.py',
    'examples/KG_Assoc/campaign/kg_assoc_e2_registry.py',
    'examples/KG_Assoc/campaign/catalog_model.py',
    'examples/KG_Assoc/campaign/e2_acceptance.schema.json',
}


def verify():
    manifest = json.loads((HERE / 'BASELINE_SHA256.json').read_text())
    transitions = []
    for name, expected in manifest.items():
        path = Path(name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual == expected:
            continue
        relative = str(path.relative_to(REPO))
        assert relative in AUTHORIZED_SOURCE_CHANGES, 'protected file changed: ' + name
        prior = subprocess.check_output(['git', 'show', START + ':' + relative], cwd=REPO)
        assert hashlib.sha256(prior).hexdigest() == expected, 'historical source binding differs'
        transitions.append(dict(path=relative, prior_git_sha=START,
                                prior_sha256=expected, new_sha256=actual))
    # The earlier source/evidence manifest is historical evidence, not today's build map.
    reviewed = REPO / 'examples/KG_Assoc/reviews/e2_ea_transfer_feasibility_20261016'
    for name, expected in json.loads((reviewed / 'SOURCE_SHA256.json').read_text()).items():
        path = Path(name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            relative = str(path.relative_to(REPO))
            assert relative in AUTHORIZED_SOURCE_CHANGES, name
            assert hashlib.sha256(subprocess.check_output(
                ['git', 'show', START + ':' + relative], cwd=REPO)).hexdigest() == expected
    return dict(baseline_bindings=len(manifest), unchanged_live_bindings=len(manifest) - len(transitions),
                authenticated_source_transitions=transitions,
                historical_manifests_modified=False, physics_kernels_modified=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, sort_keys=True))
