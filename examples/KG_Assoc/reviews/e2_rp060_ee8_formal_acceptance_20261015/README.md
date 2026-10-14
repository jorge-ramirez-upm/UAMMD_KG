# RP060 Ee8 qualified 6M acceptance — unselected

The user explicitly authorized formal qualified E2 acceptance registration for
`F04_N010_RP060_EE08_EA04` solely as `production_initial_state`, binding exactly
r001/r002/r003 at absolute **6,000,000 MD steps** in the approved
[scientific assessment](../e2_rp060_ee8_6m_20261014/ASSESSMENT.md) and
[endpoint/hash dossier](../e2_rp060_ee8_6m_20261014/ENDPOINTS.md).
Approval covers registration only. This task implements that authorization and
creates no production selection, registry, activation or production permission.

Starting local/remote HEAD and assessment commit:
`bc8bda0c2e9616d2fc0c28b4b45b06fe9cebe0fc` (`KremerGrest`, initially clean).
The final SHA is the containing registration commit, reported after push.
Registered 2026-10-15, Europe/Madrid; the record timestamp is stored in UTC.

## Immutable record

Path: `examples/KG_Assoc/kg_assoc_100m/banks/e2_acceptance/F04_N010_RP060_EE08_EA04_6M_qualified_20261015_v1.json`.
SHA256: `487d34970243d2f85d74b092e715b48d95e5cc099c03ba251d9817335b443b09`.

Status: `accepted_with_qualification`. Permitted use: `production_initial_state`.
Permitted system: **only** `F04_N010_RP060_EE08_EA04`.
Attempt: `equilibrate_92296b2a776e4d7191107126faf376bd`.
Plan SHA256: `b7b2fccab78d289518b7d477096eb3307affda61798dcc94ddd62911c8d900e5`.

The unchanged `kg_assoc_e2_registry.accept()` mechanism created the record
exclusively and independently revalidated the source before writing. All ten
acceptances passed the unchanged `exclusive_validate()` checks. The previous nine
records retain their exact hashes. No existing acceptance or scientific dossier
was rewritten. `register.py` is the archival one-use registration helper; it
rejects an existing record and requires the approved assessment HEAD.

## Exact endpoint pairs

All prefixes below are under the specified attempt, ending in `r00N/state`.
Each pair is `state.restart.lammpsdat` plus `state.assoc_restart`; the full hashes
and all original output bindings are retained in [REGISTRATION.json](REGISTRATION.json).

| Replica | Absolute step | Chemistry / MD / effective MD seeds |
|---|---:|---|
| r001 | 6,000,000 | 420301 / 520106 / 3045021384 |
| r002 | 6,000,000 | 420302 / 520107 / 3036653256 |
| r003 | 6,000,000 | 420303 / 520108 / 3061774024 |

r002 descends from the accepted active E1 retry `attempt001`, with snapshot SHA256
`a0f0c654f729e81fb84d7ded27e3d57348d2596452e1a89390f002c7a11188cb`.
The original failed E1 preparation remains preserved and is not a parent.
Fresh validation, active/frozen E1 inventory, commands, approval/smoke bindings,
build/executable provenance, completion receipts and all output hashes agree
with the approved assessment. [AUTHENTICATED_SOURCE.json](AUTHENTICATED_SOURCE.json)
preserves the fresh matching validation and build identity.

## Qualifications preserved in the acceptance

- Late intra/inter association redistribution.
- Poorly resolved L1 multiplicity fluctuations.
- r003's late conformational excursion.
- Possible residual initialization bias and incomplete slow-topology sampling.
- Historical E1 executable bytes not independently reauthenticated; provenance
  records and available input/output bytes authenticated.

**Complete stationarity, structural decorrelation and absence of initialization
bias have not been demonstrated.** Rare multiplicities/satellites, finite-window
IATs, effective samples and blocking uncertainty remain limited; only three
histories are independent statistical units. Zero-containing confidence intervals
do not prove stationarity. Exact coupled-integrator equilibrium invariance remains
unproven. These qualifications are in the immutable record itself.

## Updated acceptance inventory

| Qualified accepted system | Absolute MD steps |
|---|---:|
| F03_N010_RP080_EE08_EA04 | 8,000,000 |
| F04_N010_RP020_EE08_EA04 | 6,000,000 |
| F04_N010_RP040_EE08_EA04 | 8,000,000 |
| F04_N010_RP060_EE08_EA04 | 6,000,000 |
| F04_N010_RP080_EE04_EA04 | 2,000,000 |
| F04_N010_RP080_EE06_EA04 | 4,000,000 |
| F04_N010_RP080_EE08_EA04 | 8,000,000 |
| F04_N020_RP080_EE08_EA04 | 6,000,000 |
| F04_N040_RP080_EE08_EA04 | 8,000,000 |
| F06_N010_RP080_EE08_EA04 | 6,000,000 |

**Ten qualified formal acceptances, all unselected.**
[RECORDS.json](RECORDS.json) binds every record digest, and
[CATALOG_CHECK.json](CATALOG_CHECK.json) records ten metadata-eligible acceptances,
zero selections, zero registry views, no selected registry and absent production
authorization for every campaign system. The catalog metadata view is supplemented
by the independent payload authentication performed here.

[VALIDATION.md](VALIDATION.md) records CPU tests, integrity checks and limitations.
772 preexisting evidence files remain unchanged, including the prior nine
acceptance records, approved review, frozen campaign tests, simulation outputs and
protected `examples/KG/` and `src/` files. Only the new acceptance record and this
new documentation/test directory are added. No GPU calculation, further E2,
production-registry publication/selection/activation, 100M production preparation,
production authorization or trajectory launch occurred.
