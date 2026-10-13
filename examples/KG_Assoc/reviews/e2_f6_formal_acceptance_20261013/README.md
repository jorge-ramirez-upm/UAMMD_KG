# f=6 qualified formal E2 acceptance — unactivated

The user explicitly approved qualified formal scientific acceptance of
`F06_N010_RP080_EE08_EA04` for production initialization only, using exactly the
three hash-bound 6M endpoints in the original
[scientific decision dossier](../e2_f6_6m_20261013/DECISION.md).
Starting verified local/remote `KremerGrest` SHA:
`8def60d0d789108e6ea5880e443fd6d32430faa4`.

The original scientific review remains immutable historical evidence. This new
registration dossier supplements the earlier three formal acceptances without
editing or superseding them. No new equilibrium claim is inferred from registration.

## Canonical acceptance record

Created by the existing `kg_assoc_e2_registry.accept()` API with exclusive-file
creation, followed by `exclusive_validate()`. The record was not manually edited.
Only this new metadata JSON is added to Git within the otherwise ignored dataset.

Record: `examples/KG_Assoc/kg_assoc_100m/banks/e2_acceptance/F06_N010_RP080_EE08_EA04_6M_qualified_20261013_v1.json`.

SHA256: `81179644b404b3ab5a492ad60bba0d3d23502d0f5d7da4d058552fa9a5e714c0`.

Status: `accepted_with_qualification`. Permitted use:
`production_initial_state`. Permitted system: **only**
`F06_N010_RP080_EE08_EA04`. Source plan SHA256:
`fcbe320a4cba7af129f17475f7b09d46fb69239ad6cda9d28d63c988ce765d25`.

## Exact selected endpoints

Each is absolute step 6,000,000. Prefixes below are relative to
`examples/KG_Assoc/kg_assoc_100m/`:

- r001: `banks/e2_attempts/F06_N010_RP080_EE08/equilibrate_2092711490194045aa2036a7e00b4bd0/r001/state`; chemistry/MD/effective MD seeds `421101/520052/308502045`.
  `.restart.lammpsdat` SHA256: `8c1b89e5df342b817663d112aa2915fddf634cdd06d2c61e38c89d7584da1b52`.
  `.assoc_restart` SHA256: `1f96096faf35b9d743a76e815fe4f1af75961cff5f8daa22fad8091a0e4f3992`.
- r002: `banks/e2_attempts/F06_N010_RP080_EE08/equilibrate_2092711490194045aa2036a7e00b4bd0/r002/state`; chemistry/MD/effective MD seeds `421102/520053/300133917`.
  `.restart.lammpsdat` SHA256: `92b67aca1dadbb241409834f1a67c21a81c314ed271b94e8313aaefa03ecf42d`.
  `.assoc_restart` SHA256: `84ef7cd2bfc58bfc7b29a8e40b4571e9d6fb734937feb44482157b9390a21a32`.
- r003: `banks/e2_attempts/F06_N010_RP080_EE08/equilibrate_2092711490194045aa2036a7e00b4bd0/r003/state`; chemistry/MD/effective MD seeds `421103/520054/325254685`.
  `.restart.lammpsdat` SHA256: `d5952541ff336fb7cc72502c58429476cdee59fd1ed72df010f18147ce72ce27`.
  `.assoc_restart` SHA256: `b86d5585047774f0fdbd860b7709ccd384173cde152436182f4ae964cec3bb06`.

The canonical record binds all eight per-replica output payloads, completion
receipts and source plan; [REGISTRATION.json](REGISTRATION.json) also binds the
original scientific decision/evidence, exact endpoint set and all three earlier
acceptance-record hashes. No smoke, older endpoint, different replica or another
system is accepted.

## Scientific qualifications and authentication

- Slow topology decorrelation is unproven.
- Small shared increases in star Rg² (~0.14%) and center–terminal R² (~0.22%)
  remain explicit limitations.
- Possible intra/inter bond redistribution remains unresolved at small scale.
- The small increase in neighbor-loss activity (~0.57%) remains explicit.

Exploratory uncertainty does not prove stationarity or full topology mixing.
Formal acceptance is qualified production initialization, not production launch
permission. The numerical qualification regarding fixed-configuration chemistry
versus exact coupled-integrator invariance is preserved by the existing API.

All dossier hashes, exact r001/r002/r003 identities, plan/approval, original E1
parents, physics, chemical/MD seeds, completion receipts and pinned endpoint
payloads were independently authenticated before registration. The API then
revalidated all three full numerical, accepted-event, network and conformation
histories. Current source/build/log/executable hashes authenticate; no unavailable
historical-executable-byte limitation arose for this f=6 attempt. The historical
review-driver version is checked against the recorded code commit, while the
published joint review is separately bound to its exact driver hash.

## Catalog and execution boundary

The catalog recognizes this fourth formal acceptance with
`formal_acceptance_recorded_payload_deferred`, while retaining
`selection: missing`, absent production authorization and blocked production
eligibility. A fast catalog refresh remains metadata-level verification; it is
not a substitute for this registration's independent full payload validation.
The original recommendation and all earlier formal acceptances remain visible.

No registry publication, activation or active selection was performed. No
production preparation/authorization, GPU calculation, E2 extension or production
run was performed. The next scientific phase is equilibration of remaining
systems; this registration authorizes no such trajectory or production action.

## Verification results

```sh
PYTHONPATH=examples/KG_Assoc/campaign python3 -m unittest test_e2_acceptance test_joint_e2 test_catalog test_e2_recover test_run_e2 test_e2_g1 -q
```

**103 CPU tests passed.** New tests bind the immutable f=6 record to the exact
approved three-replica review, enforce the single permitted system/use, preserve
all scientific qualifications and absent-activation fields, and reject prefix,
step, seed or physical-parameter substitutions. Resolution without an explicit
registry fails closed. Existing no-overwrite and accidental-publication guards,
full-history review, catalog, recovery and wrapper regressions remain successful.

Python compilation and `git diff --check` pass. Existing binaries were reused
only for existing host seed/hash/initial-state tests. No native source/header or
simulation workflow changed; no CUDA rebuild or GPU test was needed. Existing
legacy validator unclosed-file `ResourceWarning` messages remain unchanged.

Final integrity checks confirm all 24 f=6 payload hashes, original scientific
review evidence and three earlier formal acceptance records are unchanged. The
canonical API-generated record and its committed copy are byte-identical.
A real catalog scan recognizes exactly the four approved systems, with no registry
views, selections or production authorization. Protected `src/` and
`examples/KG/`, original trajectories/restarts and historical provenance remain
unchanged. No other system was accepted.
