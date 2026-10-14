# Ee=6 formal qualified E2 acceptance at 4M — unselected

The user explicitly approved formal qualified acceptance of only
`F04_N010_RP080_EE06_EA04` for `production_initial_state`, exactly the three original
r001/r002/r003 absolute 4,000,000-step endpoints in the unchanged
[scientific assessment](../e2_ee6_4m_20261014/ASSESSMENT.md) and
[endpoint identities](../e2_ee6_4m_20261014/ENDPOINTS.md).

Starting local and remote `KremerGrest` both matched
`c736c27c062abeaa91e78369050db04c13ff7e7a`. The final commit is the Git commit
containing this new dossier and is reported in the task response. Dossier date:
14 October 2026, Europe/Madrid; the API records its precise UTC registration time.

The unchanged `kg_assoc_e2_registry.accept()` API created the new immutable record.
Its JSON was not manually edited. The existing schema, exclusive no-overwrite
creation and `exclusive_validate()` checks were used. No physical model, validator,
acceptance API, catalog implementation or frozen campaign file changed.

## Independent authentication

All scientific-dossier manifest/evidence bindings were checked before registration.
Each restart and chemical-sidecar hash was independently parsed from `ENDPOINTS.md`,
matched to its replica section and prefix, and checked against current bytes and the
scientific provenance. Source plan SHA256 is
`20eb13c5047cfce5a26646adb95839b4b575d232943b2b4bf7c37c49b0e623c6`.

Fresh read-only joint authentication checked frozen system/geometry/physics,
E1→E2 lineage and inventory, all original replicas and chemistry/requested/effective
MD seeds, approval, source/build/log/current executable hashes, completion receipts
and all listed outputs. Startup records match command/plan/approval/smoke hashes.
Fresh CPU numerical, accepted-event/network, restart and conformation validation
for all three continuous 0–4M histories exactly matches the original receipts and
scientific-review validation. The acceptance API independently reran endpoint and
history validation before writing. No GPU executable was run.

[REGISTRATION.json](REGISTRATION.json) binds the new acceptance, exact approved
endpoints, independent authentication, original immutable scientific dossier and
prior seven record hashes. Chemistry/MD/effective seeds are
420501/520082/3246776044, 420502/520083/3238407916 and 420503/520084/3263528676;
these remain bound through the source plan and formal-registration provenance.

## Qualifications retained in the formal record

- Full conformational and topological stationarity/decorrelation is unestablished;
  slow topology is not proven fully decorrelated.
- The downward 1M ensemble evolution is approximately 0.19% in Rg² and 0.25% in
  center–terminal R². r001 has the largest decrease; residual initialization bias
  cannot be excluded.
- The final 500k giant-component decrease reverses within the final 250k in all
  three histories, which does not prove global stationarity.
- Slow-shape sampling and block uncertainty remain limited. Some shifted exchange
  comparisons show small coordinated changes.
- Only the three original histories are independent replicates; zero-containing
  exploratory Student-t intervals do not establish stationarity.
- Historical E1 executable bytes were not independently reauthenticated. Current
  E2 executable/build/source/log provenance authenticates.
- Rejected reaction opportunities and inter-diagnostic coordinates were not
  reconstructed. The API's numerical qualification about exact coupled integrator
  invariance is preserved too.

## Eight formal records; no registry or production state

[RECORDS.json](RECORDS.json) is an immutable derived eight-record inventory snapshot,
not an active registry. The derived offline HTML/JSON/CSV catalog was refreshed
through the existing catalog generator and automatically recognizes the eighth
formal record. Its metadata view deliberately reports payload authentication as
deferred; actual independent payload authentication is bound separately here.

Catalog checks confirm zero registry views, zero selections, no selected registry,
missing endpoint selection and absent production authorization. No E2 registry
publication, activation, selection, production preparation/authorization/launch or
E2 extension occurred. No other system was accepted. The registry gate still fails
closed without an explicit registry. All prior seven acceptance records, existing
scientific reviews and simulation evidence remain byte-identical. Protected
`src/` and `examples/KG/` remain unchanged.

## Formal record and CPU checks

Record: `examples/KG_Assoc/kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE06_EA04_4M_qualified_20261014_v1.json`.

SHA256: `55fbe03556fcc3cd184bffbc43603b27726863bd618a28a06da7f97b399c3319`.

- r001: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE06/equilibrate_c6051f0ca57140819c10ae01e63036b5/r001/state`; absolute step **4,000,000**.
  - `state.restart.lammpsdat` SHA256: `65aac47ce222735e5ace2938f4c65c853c24895af7587fd469870518ef1e3de8`.
  - `state.assoc_restart` SHA256: `f88b7f7077e918da74059723b3949c65ac3e7f31c8fb5ed2f451d92f2955df4c`.
- r002: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE06/equilibrate_c6051f0ca57140819c10ae01e63036b5/r002/state`; absolute step **4,000,000**.
  - `state.restart.lammpsdat` SHA256: `fecca86a1b82fe281d4b3516913d8ce7c5971a6a0eb13f930c79c42c524ef08d`.
  - `state.assoc_restart` SHA256: `1d8e4c6eff0ac7865a597ea636a9ec61ada31cf004aba6ffb9198fed4d854767`.
- r003: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE06/equilibrate_c6051f0ca57140819c10ae01e63036b5/r003/state`; absolute step **4,000,000**.
  - `state.restart.lammpsdat` SHA256: `d8e7105b87c2eeedca36eb37aa57d44ac9fe0d628360db3c2d2436ff04957ae1`.
  - `state.assoc_restart` SHA256: `8b9f66345c79c86870e6b07a5fdfce65033e359fee2ecde4fcc7f35925d4a7c8`.

99 focused CPU tests passed: 95 across generic acceptance, catalog, E2-G1, joint review, continuous 4M review and recovery; four new exact Ee6 registration tests cover endpoint/review/permission bindings, qualification retention, exclusive no-overwrite, substitution rejection, unchanged prior evidence and unselected eighth-record recognition. Python compilation of the new test and unchanged acceptance/provenance/catalog modules passed.

An additional existing historical N40 catalog-count test was run and failed solely at its hard-coded global count of seven records (`8 != 7`, line 96). The newly approved eighth acceptance makes that assertion obsolete. It was left unchanged under the explicit no-source-code-changes restriction; the new current-catalog test checks eight records and zero selections. This is a test-maintenance limitation, not an endpoint/provenance or permission discrepancy. Logs are retained below.

Integrity checks confirmed all 1,866 pre-existing runtime/review files unchanged and exactly one new runtime file: this Ee6 acceptance. All seven previous formal hashes and the original scientific dossier remain intact. No active-registry directory exists and no new production metadata was created. Whitespace checks passed for the staged changes. No native compilation or executable rebuild was needed because no included native source changed.
