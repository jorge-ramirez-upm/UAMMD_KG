#!/usr/bin/env python3
"""Read-only evidence audit; does not launch, register, select or activate anything."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def check(mapping, relative=False):
    for name, expected in mapping.items():
        path = REPO/name if relative else Path(name)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    return len(mapping)


def verify():
    preserved = check(json.loads((HERE/'BASELINE_SHA256.json').read_text()))
    campaign = check(json.loads((HERE/'NEW_OUTPUTS_SHA256.json').read_text()))
    scoped = check(json.loads((HERE/'INTEGRITY.json').read_text())['sha256'], relative=True)
    records = json.loads((HERE/'PREFLIGHT.json').read_text())['acceptance_records']
    assert len(records) == 12
    for row in records:
        check({row['record']: row['sha256']}, relative=True)
    report = json.loads((HERE/'RESULTS.json').read_text())
    assert report['additional_MD_steps'] == report['candidate_oracle_sweeps_executed'] == 0
    assert report['started_histories'] == report['device_readbacks_executed'] == 1
    assert report['unstarted_histories'] == 11 and report['native_readback_passes'] == 0
    return dict(preserved_bindings=preserved,new_campaign_bindings=campaign,
                scoped_files=scoped,unchanged_acceptances=12,additional_MD_steps=0,
                gpu_decision='failed_hold',existing_sources_changed=0)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, sort_keys=True))
