#!/usr/bin/env python3
"""Read-only audit of historical and new smoke evidence; does not authorize execution."""
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / 'examples/KG_Assoc/campaign'))
import kg_assoc_e2 as e2


def verify():
    preserved = json.loads((HERE / 'BASELINE_SHA256.json').read_text())
    outputs = json.loads((HERE / 'NEW_OUTPUTS_SHA256.json').read_text())
    e2.check_hashes(preserved)
    e2.check_hashes(outputs)
    dossier = json.loads((HERE / 'INTEGRITY.json').read_text())['sha256']
    e2.check_hashes({str(REPO / name): digest for name, digest in dossier.items()})
    build = REPO / 'examples/KG_Assoc/kg_assoc_100m/builds/ea_reference_transfer_cpu_20261016_v1'
    manifest = build / 'manifest.json'
    assert e2.campaign.sha256(manifest) == '6d04459efe40df2698e5f40a6ad67d922fe31b5fc49ba16e9450f2290ced5446'
    record = e2.campaign.load_json(manifest)
    # Historical source bytes remain valid; additional review files are not a new live-build approval.
    for field in ('source_sha256', 'executable_sha256', 'build_log_sha256'):
        e2.check_hashes(record[field])
    root = REPO / 'examples/KG_Assoc/kg_assoc_100m'
    assert len(list((root / 'banks/e2_acceptance').glob('*.json'))) == 12
    return dict(preserved_bindings=len(preserved), new_output_bindings=len(outputs),
                dossier_bindings=len(dossier), build_source_bindings=len(record['source_sha256']),
                acceptance_records=12, status='all_bound_bytes_unchanged')


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, sort_keys=True))
