#!/usr/bin/env python3
"""Recheck dossier, preserved bytes, execution receipts and qualified neighbors on CPU."""
from pathlib import Path

import reproduce_rp060 as review


def main():
    directory = Path(__file__).parent
    runner = review.joint.runner
    load = review.joint.campaign.load_json
    preserved = load(directory / 'PRESERVED_SHA256.json')
    runner.check_hashes(preserved)
    authentication = load(directory / 'AUTHENTICATION.json')
    plan = runner.check_plan(review.ROOT, review.ATTEMPT)
    review.joint.require(review.joint.campaign.sha256(review.ATTEMPT / 'plan.json') ==
                         review.PLAN_HASH, 'wrong exact plan')
    for entry, witness in zip(plan['histories'], authentication['histories']):
        started = load(Path(entry['output_prefix']).parent / 'started.json')
        review.joint.require(started == witness['started'] and
                             started['command'] == entry['command'] and
                             started['plan_sha256'] == review.PLAN_HASH and
                             started['approval_sha256'] ==
                             review.joint.campaign.sha256(review.ATTEMPT / 'approval.json'),
                             'execution receipt differs')
        runner.check_hashes(started['smoke_sha256'])
        parent = runner.original_e1(review.ROOT, entry['system'], entry['replica'])
        review.joint.require(parent == entry['parent'], 'active E1 parent differs')
    for neighbor in authentication['neighbors']:
        runner.check_hashes({neighbor['path']: neighbor['sha256']})
        record = load(neighbor['path'])
        review.joint.require(record == neighbor['record'] and
                             record['status'] == 'accepted_with_qualification' and
                             record['permitted_use'] == 'production_initial_state',
                             'qualified neighbor identity differs')
        runner.check_hashes({record['evidence']: record['evidence_sha256']})
        for history in record['histories']:
            runner.check_hashes(history['sha256'])
    runner.check_hashes(authentication['lammps']['source_sha256'])
    runner.check_hashes(load(directory / 'evidence/provenance.json')['source_sha256'])
    integrity = directory / 'INTEGRITY.json'
    if integrity.exists():
        runner.check_hashes({str(directory / name): digest
                            for name, digest in load(integrity)['sha256'].items()})
    print(f'CPU authentication and preservation passed: {len(preserved)} preexisting files')


if __name__ == '__main__':
    main()
