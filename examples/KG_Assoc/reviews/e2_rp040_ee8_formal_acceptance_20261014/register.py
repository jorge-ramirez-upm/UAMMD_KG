"""Register only the user-approved exact RP040 Ee8 8M endpoints; never activate."""
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[4]
DOSSIER = Path(__file__).resolve().parent
REVIEW = REPO / 'examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014'
sys.path[:0] = [str(REVIEW), str(REPO / 'examples/KG_Assoc/campaign')]
import reproduce_joint as scientific
import kg_assoc_e2_registry as registry

campaign = scientific.joint.campaign
e2 = registry.e2
ROOT = scientific.ROOT
SID = 'F04_N010_RP040_EE08_EA04'
OUTPUT = ROOT / ('banks/e2_acceptance/'
    'F04_N010_RP040_EE08_EA04_8M_qualified_20261014_v1.json')
QUALIFICATION = (
    'Qualified solely for production_initial_state of F04_N010_RP040_EE08_EA04, '
    'exact original r001/r002/r003 absolute-8M endpoints. Complete stationarity and '
    'full structural decorrelation have not been demonstrated. Unresolved r002 L1 '
    'slow-mode sampling and its late negative path remain; possible history-specific '
    'initialization bias and r002 conformational offset cannot be excluded. Earlier '
    'multiplicity and association-population offsets remain. The common final-250k '
    'peripheral-network excursion has no observed post-8M reversal. Slow-mode IATs, '
    'effective samples and 5/10/20-block uncertainties are limited. The authenticated '
    'MD-reseeding boundary at 6M restores positions/velocities and chemistry but starts '
    'a new MD random stream; no stitched IAT or SEM across that boundary is valid. '
    'Only three original histories are independent statistical replicates; exploratory '
    'paired Student-t intervals containing zero do not prove stationarity. Historical '
    'E1 executable bytes were not independently reauthenticated; rejected reaction '
    'opportunities and inter-diagnostic coordinates were not reconstructed. No registry '
    'selection, activation or publication, production preparation, authorization or launch.'
)


def main():
    e2.require(campaign.git_sha() == 'a8d5c2353de2ee3545be7ae850ea6a1956394881',
               'registration requires the approved assessment commit')
    e2.require(not OUTPUT.exists(), 'immutable acceptance already exists')
    provenance = campaign.load_json(REVIEW / 'evidence/provenance.json')
    integrity = campaign.load_json(REVIEW / 'INTEGRITY.json')
    e2.check_hashes({str(REVIEW / n): h for n, h in integrity['artifact_sha256'].items()})
    e2.check_hashes(provenance['source_sha256'])
    prior_index = campaign.load_json(REPO /
        'examples/KG_Assoc/reviews/e2_ee6_formal_acceptance_20261014/RECORDS.json')
    prior = {str(REPO / r['record']): r['sha256'] for r in prior_index['records']}
    e2.require(set(prior) == {str(p) for p in (ROOT / 'banks/e2_acceptance').glob('*.json')}
               and len(prior) == 8, 'exact eight prior records required')
    e2.check_hashes(prior)
    preserved = campaign.load_json(REVIEW / 'PRESERVED_SHA256.json')
    preserved.update({str(p.relative_to(REPO)): campaign.sha256(p)
        for p in REVIEW.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
    e2.check_hashes({str(REPO / p): h for p, h in preserved.items()})
    text = (REVIEW / 'ENDPOINTS.md').read_text()
    pins = provenance['proposed_endpoints']
    e2.require([p['replica'] for p in pins] == [1, 2, 3], 'three original identities required')
    for pin in pins:
        section = text.split(f"## r{pin['replica']:03d}/state\n", 1)[1].split('\n## ', 1)[0]
        e2.require(pin['end_step'] == 8000000 and pin['prefix'] in section,
                   'wrong absolute step or prefix')
        for label, suffix in [('restart', '.restart.lammpsdat'),
                              ('chemical-sidecar', '.assoc_restart')]:
            digest = re.search(r'8M ' + label + r' SHA256: `([0-9a-f]{64})`', section).group(1)
            e2.require(pin['state_sha256'][pin['prefix'] + suffix] == digest,
                       'ENDPOINTS.md hash differs')
            e2.check_hashes({pin['prefix'] + suffix: digest})
    print('Review, eight prior records and exact ENDPOINTS.md payloads verified.', flush=True)
    sources = scientific.authenticate()
    scientific.joint.check_lineage(sources)
    for source, recorded in zip(sources, provenance['source_authentication']):
        e2.require(source['plan'] == recorded['plan'], 'source plan identity changed')
        for history, old in zip(source['histories'], recorded['histories']):
            e2.require(history['entry'] == old['entry'] and history['validation'] == old['validation'],
                       'fresh lineage/numerical/event validation differs from scientific review')
    print('All six source segments freshly authenticated and revalidated.', flush=True)
    e2.require(not (ROOT / 'banks/e2_registry').exists(), 'unexpected active registry')
    record = registry.accept(ROOT, OUTPUT, scientific.ATTEMPTS[-1],
        'User explicitly approved qualified RP040 Ee8 absolute-8M acceptance, 2026-10-14',
        REVIEW / 'ASSESSMENT.md', [SID], QUALIFICATION)
    for entry, pin in zip(record['histories'], pins):
        e2.require(entry['prefix'] == pin['prefix'] and entry['end_step'] == pin['end_step'] and
            all(entry['sha256'][n] == h for n, h in pin['state_sha256'].items()),
            'formal endpoint binding differs')
    rows = []
    for path in sorted((ROOT / 'banks/e2_acceptance').glob('*.json')):
        r = campaign.load_json(path)
        registry.exclusive_validate(r, [e2.system_by_id(s) for s in r['permitted_systems']])
        rows.append(dict(record=str(path.relative_to(REPO)), sha256=campaign.sha256(path),
            system=r['permitted_systems'][0], status=r['status'], end_step=r['histories'][0]['end_step']))
    e2.require(len(rows) == 9 and len({r['system'] for r in rows}) == 9,
               'exact nine distinct accepted systems required')
    e2.check_hashes(prior)
    e2.check_hashes({str(REPO / p): h for p, h in preserved.items()})
    e2.exclusive_json(DOSSIER / 'PRESERVED_EVIDENCE.json', preserved)
    e2.exclusive_json(DOSSIER / 'RECORDS.json', dict(records=rows,
        registry_activation=False, production_authorization=False))
    e2.exclusive_json(DOSSIER / 'REGISTRATION.json', dict(
        schema_version=1, starting_git_sha=campaign.git_sha(),
        acceptance=str(OUTPUT.relative_to(REPO)), acceptance_sha256=campaign.sha256(OUTPUT),
        scientific_assessment=str(REVIEW / 'ASSESSMENT.md'), selected_endpoints=pins,
        prior_acceptance_sha256=prior,
        scientific_dossier_sha256={str(REVIEW / n): h for n, h in integrity['artifact_sha256'].items()},
        authenticated_sources=[dict(plan=s['plan'], build_authentication_scope=s['build_authentication_scope'],
            histories=[dict(entry=h['entry'], validation=h['validation']) for h in s['histories']])
            for s in sources],
        registry_activation=False, active_selection=False, registry_publication=False,
        production_preparation=False, production_authorization=False, trajectory_launched=False))
    print('Registered and authenticated exact ninth acceptance:', OUTPUT, campaign.sha256(OUTPUT), flush=True)


if __name__ == '__main__':
    main()
