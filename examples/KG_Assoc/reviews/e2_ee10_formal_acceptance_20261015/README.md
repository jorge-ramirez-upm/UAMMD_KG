# Formal qualified Ee10 acceptance at absolute 12M

User authorization on 2026-10-15 permits formal registration only. Exactly r001,
r002 and r003 of `F04_N010_RP080_EE10_EA04`, at absolute **12,000,000 MD steps**,
are now `accepted_with_qualification`, exclusively for `production_initial_state`.

Starting clean local and remote `KremerGrest` HEAD and approved scientific commit:
`68d80f5b38e328e4522e012acc74d54022f510ab`. The final Git SHA is the containing
registration commit, reported after push. The record's `publisher_git_sha` identifies
the approved HEAD at registration, before committing this new dossier.

Record: [F04_N010_RP080_EE10_EA04_12M_qualified_20261015_v1.json](../../kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE10_EA04_12M_qualified_20261015_v1.json).
SHA256: `9f8bd5598c8fc847fd11abc5217b0390055b7d8ace1764018e4fa3140c8c15aa`.

The record binds all three exact restart/chemistry-sidecar pairs, eight output
payloads per history, completion receipts and the extension plan. Exact endpoint
and parent hashes remain in the approved [ENDPOINTS.md](../e2_ee10_12m_20261015/ENDPOINTS.md)
and [REGISTRATION.json](REGISTRATION.json). The immutable scientific evidence is
[ASSESSMENT.md](../e2_ee10_12m_20261015/ASSESSMENT.md), committed at the starting SHA.
No scientific decision or earlier dossier was edited.

Extension plan SHA256:
`9ceb3ce52582e1e781ee36072b4018254dca0f663f58a73edb3111093322f28a`.
Original 0–8M attempt: `equilibrate_fb8954dc860740d6b923759b2b21a703`.
Accepted 8–12M continuation: `equilibrate_18d492ee0f4b4a7d98ca32e39ce8f95a`.

## Qualifications carried into the formal record

Complete stationarity, structural decorrelation and absence of initialization bias
have not been demonstrated. Acceptance permits initializing production; it does
not assert equilibrium of every slow structural observable. Qualifications include
incomplete slow-topology sampling, r002's large L1 excursion and elevated late
mean, r003's late intra/inter redistribution and distinct-degree change, replica
population/conformation offsets, shared conformational contraction relative to
6–8M and possible residual initialization bias. Only the three original histories
are independent statistical units. Zero-containing intervals do not prove stationarity.

Historical E1 and original 0–8M executable bytes cannot be independently
reauthenticated. Available parent/input/output bytes, recorded executable identities,
source/build evidence and the earlier immutable reviews authenticate; current
extension executable bytes authenticate. These historical limitations persist.
Exact coupled-integrator equilibrium invariance remains unproven.

The earlier [8M scientific hold](../e2_ee10_8m_20261015/ASSESSMENT.md) remains
unchanged. Its exact 8M states are **not accepted** by this registration.

## Boundary authentication

Fresh read-only CPU validation replayed all six segments and matched the approved
provenance exactly. Original histories each have 8,001 samples and
54,118 / 53,832 / 53,545 accepted events. Extensions each have 4,001 samples and
25,674 / 25,653 / 25,903 accepted events; final bonds are 1,926 / 1,915 / 1,926.
Numerical, event, permanent-identity, graph and conformation checks passed.

All three 8M parent pairs match the original outputs and the continuation plan.
Chemical partners, absolute step, chemical seed and cumulative creation/break
counters continue. [BOUNDARY.json](BOUNDARY.json) records parent file hashes,
canonical partner-set digests, counters and both requested/effective MD seeds.

| Replica | Chemical seed | MD seed old → new | Effective MD seed old → new | 8M creations / breaks |
|---|---:|---|---|---|
| r001 | 420701 | 520112 → 520118 | 2961194660 → 3011452588 | 28025 / 26093 |
| r002 | 420702 | 520113 → 520119 | 2952826532 → 3003084460 | 27875 / 25957 |
| r003 | 420703 | 520114 → 520120 | 2977947300 → 2894249636 | 27733 / 25812 |

A fresh GJ integrator restores positions and velocities with `initVelocities=false`
and `internal_start_step=0`, using a new MD random stream. This is **not bitwise
MD continuation**. No IAT, SEM or bond lifetime is stitched through the 8M boundary.
[AUTHENTICATED_SOURCE.json](AUTHENTICATED_SOURCE.json) preserves both full plans,
build authentication scopes, parent/seed identities and fresh validation receipts.

## Acceptance inventory and exclusions

Eleven distinct systems now have immutable qualified E2 acceptances. All ten
previous record hashes remain identical; all 1,098 preserved file bindings pass.
The catalog reports no registry views, selections or active registry, and no
production authorization. No GPU calculation, equilibration, registry publication,
selection or activation, production preparation, authorization or launch occurred.
[RECORDS.json](RECORDS.json) and [CATALOG_CHECK.json](CATALOG_CHECK.json) record the
full inventory and absence of downstream authorization.

| System | Absolute accepted steps |
|---|---:|
| `F03_N010_RP080_EE08_EA04` | 8,000,000 |
| `F04_N010_RP020_EE08_EA04` | 6,000,000 |
| `F04_N010_RP040_EE08_EA04` | 8,000,000 |
| `F04_N010_RP060_EE08_EA04` | 6,000,000 |
| `F04_N010_RP080_EE04_EA04` | 2,000,000 |
| `F04_N010_RP080_EE06_EA04` | 4,000,000 |
| `F04_N010_RP080_EE08_EA04` | 8,000,000 |
| `F04_N010_RP080_EE10_EA04` | 12,000,000 |
| `F04_N020_RP080_EE08_EA04` | 6,000,000 |
| `F04_N040_RP080_EE08_EA04` | 8,000,000 |
| `F06_N010_RP080_EE08_EA04` | 6,000,000 |

Only the new acceptance JSON and this registration dossier are added. Frozen
physics, simulation outputs, `examples/KG/`, `src/`, protected evidence, earlier
assessments and all previous acceptance records remain unchanged.

## Reproduction and integrity

[register.py](register.py) uses the unchanged `kg_assoc_e2_registry.accept` mechanism;
it requires the approved starting HEAD and rejects an existing acceptance before
writing anything. The API freshly replayed the continuation before creating the
record. Re-running registration is intentionally forbidden by immutable-file guards.

To repeat read-only authentication into a **new** file from the repository root:

```bash
PYTHONWARNINGS=ignore::ResourceWarning python3 \
  examples/KG_Assoc/reviews/e2_ee10_formal_acceptance_20261015/authenticate.py \
  --output /tmp/NEW_ee10_registration_authentication.json
```

Its decoded JSON must equal `AUTHENTICATED_SOURCE.json`. This authenticates all
six segments without recreating the formal acceptance or running an executable.
[VALIDATION.md](VALIDATION.md) gives CPU test commands and results.
`INTEGRITY.json` binds the new acceptance record and every dossier artifact
except itself; the containing Git commit binds the manifest itself.
