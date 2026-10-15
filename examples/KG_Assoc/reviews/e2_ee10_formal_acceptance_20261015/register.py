"""Register only user-approved exact Ee10 12M endpoints; never publish a registry."""
import hashlib
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[4]
DOSSIER = Path(__file__).resolve().parent
REVIEW = REPO / 'examples/KG_Assoc/reviews/e2_ee10_12m_20261015'
sys.path[:0] = [str(REVIEW), str(REPO / 'examples/KG_Assoc/campaign')]
import reproduce_ee10_12m as scientific
import kg_assoc_e2_registry as registry
from catalog_model import Catalog

campaign = registry.campaign
e2 = registry.e2
ROOT = scientific.ROOT
SID = scientific.SYSTEM
APPROVED_SHA = '68d80f5b38e328e4522e012acc74d54022f510ab'
OUTPUT = ROOT / ('banks/e2_acceptance/'
    'F04_N010_RP080_EE10_EA04_12M_qualified_20261015_v1.json')
QUALIFICATION = (
    'User-approved qualified acceptance solely for production_initial_state of '
    'F04_N010_RP080_EE10_EA04, binding exactly original r001/r002/r003 endpoints '
    'at absolute 12000000 MD steps. Complete stationarity, structural decorrelation '
    'and absence of initialization bias have not been demonstrated. This acceptance '
    'permits initializing production, not asserting equilibrium of every slow structural '
    'observable. Incomplete slow-topology sampling and inadequate evidence for full '
    "structural decorrelation remain, including r002's large L1 excursion and elevated "
    "late mean, r003's late intra/inter redistribution and distinct-degree change, "
    'replica-level population and conformation offsets, shared conformational contraction '
    'relative to 6–8M, and possible residual initialization bias. Only three original '
    'histories are independent statistical units; finite-window IATs, effective samples, '
    'blocking sensitivity and rare-event sampling remain limited. Confidence intervals '
    'containing zero do not prove stationarity. Chemical partners, seeds, absolute steps '
    'and cumulative reaction counters continue through 8M; fresh requested MD seeds '
    '520118/520119/520120 (effective 3011452588/3003084460/2894249636) create new MD '
    'streams, not bitwise MD continuation. No IAT, SEM or bond lifetime is stitched '
    'across 8M. Historical E1 and original 0–8M executable bytes were not independently '
    'reauthenticated; available parents, inputs, outputs, source/build logs and recorded '
    'executable identities authenticate. Extension executable bytes authenticate. '
    'Exact coupled-integrator equilibrium invariance is unproven. The earlier 8M '
    'scientific hold remains immutable; those exact 8M states are not accepted. '
    'No registry selection, activation or publication, production preparation, '
    'production authorization or trajectory launch is authorized by this registration.'
)


def check_pins(provenance, text):
    sources = provenance['source_authentication']
    e2.require(len(sources) == 2, 'two authenticated segments required')
    pins = provenance['proposed_endpoints']
    e2.require([p['replica'] for p in pins] == [1, 2, 3], 'three exact identities required')
    for index, (pin, old, new) in enumerate(zip(pins, sources[0]['histories'],
                                              sources[1]['histories'])):
        entry = new['entry']
        ancestor = old['entry']
        e2.require(pin['end_step'] == 12000000 and entry['start_step'] == 8000000 and
                   ancestor['start_step'] == 0 and ancestor['end_step'] == 8000000 and
                   pin['prefix'] == str(scientific.ATTEMPTS[-1] / f"r{pin['replica']:03d}/state") and
                   all(pin[key] == entry[key] for key in
                       ('replica', 'end_step', 'chemistry_seed', 'md_seed', 'effective_md_seed')),
                   'exact 12M endpoint or seed mismatch')
        e2.require(entry['parent']['prefix'] == ancestor['output_prefix'] and
                   entry['chemistry_seed'] == ancestor['chemistry_seed'] == 420701 + index and
                   ancestor['md_seed'] == 520112 + index and entry['md_seed'] == 520118 + index and
                   entry['effective_md_seed'] == (3011452588, 3003084460, 2894249636)[index],
                   '8M parent or chemical/MD seed transition differs')
        section = text.split(f"## r{pin['replica']:03d}\n", 1)[1].split('\n## ', 1)[0]
        e2.require(pin['prefix'] in section and ancestor['output_prefix'] in section,
                   'endpoint or parent prefix differs from approved dossier')
        for step, prefix, hashes in (
                (12, pin['prefix'], pin['state_sha256']),
                (8, ancestor['output_prefix'], entry['parent']['sha256'])):
            for suffix in ('.restart.lammpsdat', '.assoc_restart'):
                digest = re.search(r'\| ' + str(step) + r'M `state' + re.escape(suffix) +
                                   r'` \| `([0-9a-f]{64})` \|', section).group(1)
                e2.require(hashes[prefix + suffix] == digest, 'approved endpoint hash differs')
                if step == 8:
                    e2.require(old['validation']['output_sha256'][suffix] == digest,
                               'original 8M output differs from parent')
                e2.check_hashes({prefix + suffix: digest})
    return pins


def boundary_proof(sources):
    result = []
    for old, new in zip(sources[0]['histories'], sources[1]['histories']):
        a, b = old['entry'], new['entry']
        metadata, pairs = e2.validation.analysis.restart.read_metadata(
            a['output_prefix'] + '.assoc_restart')
        _, initial = e2.validation.read_parent(b)
        _, old_rows = e2.validation.analysis.stationarity.read_state(a['output_prefix'] + '.state')
        _, new_rows = e2.validation.analysis.stationarity.read_state(b['output_prefix'] + '.state')
        fields = ('step', 'free', 'bonds', 'intra', 'inter', 'creations', 'breaks')
        state = {key: old_rows[-1][key] for key in fields}
        e2.require(state == {key: new_rows[0][key] for key in fields} and
                   initial['pairs'] == pairs and
                   initial['creations'] == state['creations'] and
                   initial['breaks'] == state['breaks'], '8M chemical boundary differs')
        result.append(dict(replica=b['replica'], parent_prefix=a['output_prefix'],
            parent_sha256=b['parent']['sha256'], absolute_step=8000000,
            chemistry_seed=int(metadata['seed']), chemical_state=state,
            partner_count=len(pairs), partner_pairs_sha256=hashlib.sha256(
                json.dumps(sorted(pairs), separators=(',', ':')).encode()).hexdigest(),
            partner_hash_encoding='SHA256 of JSON sorted pairs, compact separators, no newline',
            old_md_seed=a['md_seed'], new_md_seed=b['md_seed'],
            old_effective_md_seed=a['effective_md_seed'], new_effective_md_seed=b['effective_md_seed'],
            internal_start_step=0, initVelocities=False, bitwise_md_continuation=False))
    return result


def main():
    e2.require(campaign.git_sha() == APPROVED_SHA, 'approved assessment HEAD required')
    e2.require(not OUTPUT.exists(), 'immutable acceptance already exists')
    scientific.verify_inputs()
    preserved = campaign.load_json(DOSSIER / 'PRESERVED_EVIDENCE.json')
    e2.check_hashes(preserved)
    prior_index = campaign.load_json(REPO /
        'examples/KG_Assoc/reviews/e2_rp060_ee8_formal_acceptance_20261015/RECORDS.json')
    prior = {str(REPO / row['record']): row['sha256'] for row in prior_index['records']}
    e2.require(len(prior) == 10 and set(prior) ==
               {str(p) for p in (ROOT / 'banks/e2_acceptance').glob('*.json')},
               'exact ten prior acceptances required')
    e2.check_hashes(prior)
    provenance = campaign.load_json(REVIEW / 'evidence/provenance.json')
    fresh = campaign.load_json(DOSSIER / 'AUTHENTICATED_SOURCE.json')
    e2.require(fresh == provenance['source_authentication'],
               'fresh execution validation differs from approved scientific dossier')
    pins = check_pins(provenance, (REVIEW / 'ENDPOINTS.md').read_text())
    e2.exclusive_json(DOSSIER / 'BOUNDARY.json', boundary_proof(fresh))
    e2.require(not (ROOT / 'banks/e2_registry').exists(), 'unexpected registry')
    record = registry.accept(ROOT, OUTPUT, scientific.ATTEMPTS[-1],
        'User explicitly approved formal qualified Ee10 exact-12M registration, 2026-10-15',
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
    e2.require(len(rows) == len({r['system'] for r in rows}) == 11, 'exact eleven systems required')
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
        authenticated_segments_sha256=campaign.sha256(DOSSIER / 'AUTHENTICATED_SOURCE.json'),
        md_continuation='fresh MD streams; not bitwise continuation',
        accepted_absolute_step=12000000, historical_8m_hold_preserved=True,
        boundary_sha256=campaign.sha256(DOSSIER / 'BOUNDARY.json'),
        registry_activation=False, active_selection=False, registry_publication=False,
        production_preparation=False, production_authorization=False, trajectory_launched=False))
    graph = Catalog(REPO, ROOT).scan()
    accepted_refs = {'dataset:' + str((REPO / row['record']).relative_to(ROOT)): row['sha256']
                     for row in rows}
    e2.require(len(graph['acceptances']) == 11 and not graph['selections'] and
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
    print('Registered eleventh qualified acceptance:', OUTPUT, campaign.sha256(OUTPUT), flush=True)


if __name__ == '__main__':
    main()
