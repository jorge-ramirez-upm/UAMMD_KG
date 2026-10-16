#!/usr/bin/env python3
"""Read-only final preservation, dossier, artifact and current build authentication."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from verify_preservation import verify, REPO
import kg_assoc_e2 as e2

report = verify()
for name in ('INTEGRITY.sha256', 'ARTIFACTS.sha256'):
    mapping = json.loads((HERE / name).read_text())
    e2.check_hashes(mapping)
    report[name] = len(mapping)
build = REPO / 'examples/KG_Assoc/kg_assoc_100m/builds/readback_rounding_cpu_20261016_v1'
e2.check_build(build)
report['current_build_authenticated'] = True
print(json.dumps(report, indent=2, sort_keys=True))
