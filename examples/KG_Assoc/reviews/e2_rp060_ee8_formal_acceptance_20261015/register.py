"""Register only user-approved exact RP060 Ee8 6M endpoints; never publish a registry."""
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[4]
DOSSIER = Path(__file__).resolve().parent
REVIEW = REPO / 'examples/KG_Assoc/reviews/e2_rp060_ee8_6m_20261014'
sys.path[:0] = [str(REVIEW), str(REPO / 'examples/KG_Assoc/campaign')]
import reproduce_rp060 as scientific
import validate_rp060 as authentication
import kg_assoc_e2_registry as registry
from catalog_model import Catalog

campaign = registry.campaign
e2 = registry.e2
ROOT = scientific.ROOT
SID = scientific.SYSTEM
APPROVED_SHA = 'bc8bda0c2e9616d2fc0c28b4b45b06fe9cebe0fc'
OUTPUT = ROOT / ('banks/e2_acceptance/'
    'F04_N010_RP060_EE08_EA04_6M_qualified_20261015_v1.json')
QUALIFICATION = (
    'User-approved qualified acceptance solely for production_initial_state of '
    'F04_N010_RP060_EE08_EA04, binding exactly original r001/r002/r003 endpoints '
    'at absolute 6000000 MD steps. Complete stationarity, structural decorrelation '
    'and absence of initialization bias have not been demonstrated. Late intra/inter '
    'association redistribution, poorly resolved L1 multiplicity fluctuations and '
    "r003's late conformational excursion remain. Possible residual initialization "
    'bias and incomplete slow-topology sampling cannot be excluded. Rare bond '
    'multiplicities and satellite populations, finite-window IATs, effective samples '
    'and blocking uncertainties remain limited; only three original histories are '
    'independent statistical units. Confidence intervals containing zero do not prove '
    'stationarity. r002 descends from accepted active E1 retry attempt001, not its '
    'original failed preparation. Historical E1 executable bytes were not independently '
    'reauthenticated; E1 provenance records and available input/output bytes were '
    'authenticated. Exact coupled-integrator equilibrium invariance is unproven. '
    'No registry selection, activation or publication, production preparation, '
    'production authorization or trajectory launch is authorized by this registration.'
)


def check_pins(provenance, text):
    pins = provenance['proposed_endpoints']
    e2.require([p['replica'] for p in pins] == [1, 2, 3], 'three exact identities required')
    for pin, history in zip(pins, provenance['validated_histories']):
        entry = history['entry']
        e2.require(pin['end_step'] == 6000000 and entry['start_step'] == 0 and
                   pin['prefix'] == str(scientific.ATTEMPT / f"r{pin['replica']:03d}/state") and
                   all(pin[key] == entry[key] for key in
                       ('replica', 'end_step', 'chemistry_seed', 'md_seed', 'effective_md_seed')),
                   'exact 6M endpoint or seed mismatch')
        section = text.split(f"## r{pin['replica']:03d}\n", 1)[1].split('\n## ', 1)[0]
        e2.require(pin['prefix'] in section, 'endpoint prefix differs from approved dossier')
        for suffix in ('.restart.lammpsdat', '.assoc_restart'):
            digest = re.search(r'\| `state' + re.escape(suffix) +
                               r'` \| `([0-9a-f]{64})` \|', section).group(1)
            e2.require(pin['state_sha256'][pin['prefix'] + suffix] == digest,
                       'approved endpoint hash differs')
            e2.check_hashes({pin['prefix'] + suffix: digest})
    retry = provenance['validated_histories'][1]['entry']['parent']
    expected = ROOT / 'banks/e1_retries/F04_N010_RP060/r002/attempt001/state.e1.lammpsdat'
    e2.require(retry['snapshot'] == str(expected) and retry['sha256'][str(expected)] ==
               'a0f0c654f729e81fb84d7ded27e3d57348d2596452e1a89390f002c7a11188cb',
               'r002 must descend from accepted E1 retry attempt001')
    return pins


def main():
    e2.require(campaign.git_sha() == APPROVED_SHA, 'approved assessment HEAD required')
    e2.require(not OUTPUT.exists(), 'immutable acceptance already exists')
    authentication.main()
    preserved = campaign.load_json(DOSSIER / 'PRESERVED_EVIDENCE.json')
    e2.check_hashes(preserved)
    prior_index = campaign.load_json(REPO /
        'examples/KG_Assoc/reviews/e2_rp040_ee8_formal_acceptance_20261014/RECORDS.json')
    prior = {str(REPO / row['record']): row['sha256'] for row in prior_index['records']}
    e2.require(len(prior) == 9 and set(prior) ==
               {str(p) for p in (ROOT / 'banks/e2_acceptance').glob('*.json')},
               'exact nine prior acceptances required')
    e2.check_hashes(prior)
    provenance = campaign.load_json(REVIEW / 'evidence/provenance.json')
    fresh = campaign.load_json(DOSSIER / 'AUTHENTICATED_SOURCE.json')
    e2.require(fresh['plan'] == provenance['source_plan'] and
               fresh['histories'] == provenance['validated_histories'] and
               fresh['build_authentication_scope'] == 'current_binary_hashes_authenticated',
               'fresh execution validation differs from approved scientific dossier')
    pins = check_pins(provenance, (REVIEW / 'ENDPOINTS.md').read_text())
    e2.require(not (ROOT / 'banks/e2_registry').exists(), 'unexpected registry')
    record = registry.accept(ROOT, OUTPUT, scientific.ATTEMPT,
        'User explicitly approved formal qualified RP060 Ee8 exact-6M registration, 2026-10-15',
        REVIEW / 'ASSESSMENT.md', [SID], QUALIFICATION)
    for entry, pin in zip(record['histories'], pins):
        e2.require(entry['prefix'] == pin['prefix'] and entry['end_step'] == pin['end_step'] and
                   all(entry['sha256'][name] == digest
                       for name, digest in pin['state_sha256'].items()), 'formal binding differs')
    rows = []
    for path in sorted((ROOT / 'banks/e2_acceptance').glob('*.json')):
        accepted = campaign.load_json(path)
        registry.exclusive_validate(accepted, [e2.system_by_id(s) for s in accepted['permitted_systems']])
        rows.append(dict(record=str(path.relative_to(REPO)), sha256=campaign.sha256(path),
            system=accepted['permitted_systems'][0], status=accepted['status'],
            end_step=accepted['histories'][0]['end_step']))
    e2.require(len(rows) == len({r['system'] for r in rows}) == 10, 'exact ten systems required')
    e2.check_hashes(prior)
    e2.check_hashes(preserved)
    e2.exclusive_json(DOSSIER / 'RECORDS.json', dict(records=rows,
        registry_activation=False, production_authorization=False))
    e2.exclusive_json(DOSSIER / 'REGISTRATION.json', dict(schema_version=1,
        starting_git_sha=APPROVED_SHA, acceptance=str(OUTPUT.relative_to(REPO)),
        acceptance_sha256=campaign.sha256(OUTPUT), selected_endpoints=pins,
        prior_acceptance_sha256=prior, scientific_assessment_sha=APPROVED_SHA,
        scientific_dossier_sha256=e2.hash_files([REVIEW / 'ASSESSMENT.md', REVIEW / 'ENDPOINTS.md',
                                                REVIEW / 'INTEGRITY.json']),
        registry_activation=False, active_selection=False, registry_publication=False,
        production_preparation=False, production_authorization=False, trajectory_launched=False))
    graph = Catalog(REPO, ROOT).scan()
    accepted_refs = {'dataset:' + str((REPO / row['record']).relative_to(ROOT)): row['sha256']
                     for row in rows}
    e2.require(len(graph['acceptances']) == 10 and not graph['selections'] and
               {r['source'] for r in graph['acceptances']} == set(accepted_refs) and
               all(r['metadata_eligible'] for r in graph['acceptances']) and
               not graph['registry_views'] and graph['selected_registry'] is None and
               all(s['production_authorization'] == 'absent' for s in graph['systems']),
               'acceptance catalog or exclusion state differs')
    e2.exclusive_json(DOSSIER / 'CATALOG_CHECK.json', dict(
        acceptances=[dict(source=r['source'], sha256=accepted_refs[r['source']])
                     for r in graph['acceptances']],
        selections=graph['selections'], registry_views=graph['registry_views'],
        selected_registry=graph['selected_registry'],
        systems=[dict(system_id=s['system_id'], scientific=s['scientific'],
                      selection=s['selection'], production_authorization=s['production_authorization'])
                 for s in graph['systems']]))
    print('Registered tenth qualified acceptance:', OUTPUT, campaign.sha256(OUTPUT), flush=True)


if __name__ == '__main__':
    main()
