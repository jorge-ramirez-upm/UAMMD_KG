# Qualified Ee12 exact-20M acceptance registration

Formal qualified acceptance is registered for `F04_N010_RP080_EE12_EA04`,
exactly original r001/r002/r003 at absolute **20,000,000 MD steps**, exclusively
as `production_initial_state`. User authorization covers registration only.

Starting clean local/remote `KremerGrest` HEAD and approved scientific assessment:
`cb78880925b60c0777d3cba43fbb6222a62175e2`. Date: 2026-10-16.
The final Git SHA is the containing registration commit, reported after push.

Acceptance record: [F04_N010_RP080_EE12_EA04_20M_qualified_20261016_v1.json](../../kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE12_EA04_20M_qualified_20261016_v1.json).

SHA256: `bf8bb3144fc0dacd3047f86a87987df7100de0662a6d73ca9517a42804e11aac`.

Authority: [approved assessment](../e2_ee12_20m_20261016/ASSESSMENT.md) and
[exact endpoint/hash dossier](../e2_ee12_20m_20261016/ENDPOINTS.md).
The earlier [16M scientific hold](../e2_ee12_16m_20261015/ASSESSMENT.md) remains
immutable; its exact endpoints are not accepted or reinterpreted as accepted.

## Exact accepted pairs

All prefixes are under
`examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE12/equilibrate_553522b9ed9b4253a6b910d817ad65f8/`.
Each identity is `rNNN/state` at absolute 20M, with both payload hashes below.

| Replica | `state.restart.lammpsdat` SHA256 | `state.assoc_restart` SHA256 |
|---|---|---|
| r001 | `1771071181cdd88a72e882bf7449e728881c990231a4a9be84578a7f56a1d3a2` | `97540362878cd52537b6b7c816779682885e6528f4add7be09079ee61e2be34a` |
| r002 | `41fe6b3a1ae4aa639424fff0e2c8b304c21a53645ce0f66fdee3e66199a96d00` | `4ad3eb1977b69c3798546e942c290e9635f3b339a01b76ef08e967ef55bc1ec8` |
| r003 | `2db8093ea2009332e218469ca66d17117f8d052e96390ee3c07ca15c5bd7266b` | `40564a3d8eac898b6a518e551230198ae876bfe58acbfe8cf4679c15702cb06a` |

All eight output hashes per history, source-plan and completion-receipt bindings
are in the acceptance and [REGISTRATION.json](REGISTRATION.json). Both segments'
plans, all seeds and fresh validations are in
[AUTHENTICATED_SOURCE.json](AUTHENTICATED_SOURCE.json).

## Qualifications retained verbatim in the acceptance

User-approved qualified acceptance solely for production_initial_state of F04_N010_RP080_EE12_EA04, binding exactly original r001/r002/r003 endpoints at absolute 20000000 MD steps. Complete stationarity, structural decorrelation and absence of initialization bias have not been demonstrated and remain unproved. Suitability for production initialization does not certify equilibrium of every structural observable. Qualifications include common reduction in L1 parallel-bond multiplicity from 12–16M to 16–20M; residual r002 multiplicity evolution despite observed population returns and late plateau; r001's late distinct-degree and L1 changes; r003's intra/inter redistribution, changing isolated-star population and conformational offset; coherent late center–terminal contraction; replica-dependent structural offsets and incomplete slow-topology sampling; rare isolated-star residence and limited evidence of peripheral-state mixing; and possible residual initialization bias. Only three original histories are independent statistical units. Finite-window IATs, effective samples and 5/10/20-block uncertainties remain limited; zero-containing confidence intervals, stable occupancy and cancellation between replicas do not prove stationarity. Chemical partners, chemical seeds 420801/420802/420803, absolute steps and cumulative reaction counters continue through 16M. New requested MD seeds 520130/520131/520132 (effective 3381585552/3373217424/3398338192) create fresh streams with restored positions/velocities, initVelocities=false and internal_start_step=0: not bitwise MD continuation. No IAT, SEM or bond lifetime is stitched across 16M. Historical E1 and original 0–16M executable-byte authentication limitations remain: available lineage, inputs, outputs, source/build logs and recorded executable identities authenticate; historical executable bytes were not independently reauthenticated. Current extension executable bytes authenticate. Exact coupled-integrator equilibrium invariance is unproven. The earlier 16M scientific hold remains immutable historical evidence; those exact 16M states are not accepted or reinterpreted as accepted. No registry selection, activation or publication, production preparation, production authorization or trajectory launch is authorized by this registration.

## Authentication, inventory and exclusions

The unchanged `kg_assoc_e2_registry.accept` mechanism replayed the continuation
before exclusively creating the new JSON. All twelve acceptance records passed
`exclusive_validate`; the previous eleven retain their exact hashes.
[BOUNDARY.json](BOUNDARY.json) proves exact chemical partner-set, seed, absolute
step and cumulative-counter continuity at 16M and records both MD streams.
New requested MD seeds are 520130/520131/520132; effective seeds are
3381585552/3373217424/3398338192. This is not bitwise MD continuation.

[VALIDATION.md](VALIDATION.md) gives authentication, tests, reproduction and
integrity checks. [PRESERVED_EVIDENCE.json](PRESERVED_EVIDENCE.json) preserves
1,294 bindings, including all 1,258 inherited bindings and the approved 20M
dossier. Protected simulation outputs, frozen physics, prior reviews and all
eleven previous acceptances remain unchanged. No GPU executable was launched.

The inventory now has twelve qualified accepted systems among 23 campaign
systems; production authorization is absent for all 23. No registry is selected,
published or activated. No production preparation, authorization or launch occurred.
The catalog is an unselected metadata inventory; independent payload authentication
is provided by the exclusive validators and replay above.

| System | Accepted absolute step |
|---|---:|
| `F03_N010_RP080_EE08_EA04` | 8,000,000 |
| `F04_N010_RP020_EE08_EA04` | 6,000,000 |
| `F04_N010_RP040_EE08_EA04` | 8,000,000 |
| `F04_N010_RP060_EE08_EA04` | 6,000,000 |
| `F04_N010_RP080_EE04_EA04` | 2,000,000 |
| `F04_N010_RP080_EE06_EA04` | 4,000,000 |
| `F04_N010_RP080_EE08_EA04` | 8,000,000 |
| `F04_N010_RP080_EE10_EA04` | 12,000,000 |
| `F04_N010_RP080_EE12_EA04` | 20,000,000 |
| `F04_N020_RP080_EE08_EA04` | 6,000,000 |
| `F04_N040_RP080_EE08_EA04` | 8,000,000 |
| `F06_N010_RP080_EE08_EA04` | 6,000,000 |

Full immutable record paths/hashes: [RECORDS.json](RECORDS.json).
Read-only selection/authorization check: [CATALOG_CHECK.json](CATALOG_CHECK.json).
