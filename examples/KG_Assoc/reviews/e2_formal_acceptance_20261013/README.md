# Formal qualified E2 scientific acceptance — unactivated

The user explicitly approved formal scientific acceptance for production
initialization only for the three systems below. This task's authorization is
recorded as explicit user approval, not inferred from the earlier recommendations.
Starting local/remote `KremerGrest` SHA:
`eaaef7b8dffb57c11b9749021ecf9ede7e3a1a3f`.

Records are created by the supported `kg_assoc_e2_registry.accept()` API, using
exclusive output files, and validated by `exclusive_validate()`. No `publish()` or
`resolve()` activation is performed. Only the three metadata acceptance files are
added to Git within the otherwise ignored dataset. No simulation payload or old
record is edited, copied into Git or promoted by directory existence.

| Approved system | Selected endpoint interval | Scientific evidence |
|---|---|---|
| F04_N010_RP080_EE04_EA04 | three 2M endpoints | [2M/C1 review decision](../e2_acceptance_20261012/DECISION.md) |
| F04_N010_RP020_EE08_EA04 | exactly three hash-bound 6M endpoints | [6M reassessment](../e2_reassessment6m_20261013/DECISION.md) |
| F04_N010_RP080_EE08_EA04 | three corrected 8M endpoints | [corrected C1 review decision](../e2_acceptance_20261012/DECISION.md) |

All records are `accepted_with_qualification`, permit only
`production_initial_state` and name only the approved Ea=4 system. They do not
permit higher-Ea conditions, another chemistry/geometry, smoke endpoints, older
2M/4M dilute states, or historical defective C1 states. Endpoint prefixes,
steps, physical parameters, chemical seeds, payload/completion hashes and
source plans are included individually in each record. MD reseed boundaries
remain in their original source plans and the fresh authentication dossier.

## Qualifications and available authentication

Slow network-topology decorrelation has not been fully demonstrated in any of
these preparations. Acceptance is qualified initialization, not proof of full
asymptotic equilibrium or permission to launch production. The dilute system's
earlier small bond-population shift remains part of its scientific qualification.
C1 retains its corrected-from-PBC-defective historical lineage: the old 6M
trajectories are authenticated as parents only and remain ineligible endpoints.

Fresh CPU validation uses the existing numerical, chemical-event/network and,
where present, conformation validators. Plans, parent states, replica identities,
steps, inherited chemistry seeds, independently reseeded MD boundaries, receipt
hashes and scientific review evidence are checked. The full dilute 0–6M lineage
is revalidated rather than relabeled as nine independent histories.

Older executable bytes were rebuilt in place and are unavailable for fresh
hashing. Their authenticated immutable plan/build records, recorded digests,
source/build-log evidence and original code commits are preserved, with the
historic-byte limitation explicit. The current dilute 4–6M executable bytes are
freshly authenticated. C1's legacy plan provides its original code SHA, declared
executable digests and a Git-authenticated Makefile; it has less comprehensive
build-source provenance than E2-G1. This is a stated limitation, not a claim that
missing executable bytes or unrecorded build information were recovered.

## Catalog and execution boundaries

Formal acceptance, active selection and production authorization are independent.
The catalog exposes valid formal record references in
`formal_acceptance_records`, records scientific status as
`formal_acceptance_recorded_payload_deferred`, and continues to report
`selection: missing`, `production_authorization: absent` and blocked production
eligibility. Its routine refresh remains a metadata view; this dossier's fresh
payload authentication does not make every subsequent catalog refresh a deep
validation. Earlier documented recommendations/holds remain visible.

No active registry is created or selected. No production launch authorization,
GPU calculation, additional equilibration or production run is performed.
Any future registry activation requires separate explicit user authorization;
production launch is a further independent action.

## Regression verification

The CPU suite covers immutable/no-overwrite acceptance, exactly three selected
histories, source identity and receipt/payload tampering, smoke exclusion,
defective C1 exclusion, explicit registry requirement, and a formal record
without activation or production authorization. Existing joint-review, catalog,
recovery, wrapper and E2-G1 CPU tests remain in the suite. Existing binaries are
reused only for host seed queries, hash checks and host-only initial-state tests;
no native simulation code or executable is rebuilt or changed.

## Exact records and selected states

All record paths below are relative to the repository. SHA256 digests bind the
unchanged canonical record bytes in `banks/e2_acceptance/`.

| Record | SHA256 |
|---|---|
| [F04_N010_RP080_EE04_EA04_2M_qualified_20261013_v1.json](../../kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE04_EA04_2M_qualified_20261013_v1.json) | `7f5cd4ba2ace52b0b8a62a54ffe63bebf62c1bf4a6d22bb330df97ce44e8bb6a` |
| [F04_N010_RP020_EE08_EA04_6M_qualified_20261013_v1.json](../../kg_assoc_100m/banks/e2_acceptance/F04_N010_RP020_EE08_EA04_6M_qualified_20261013_v1.json) | `20f7ed7ae7fb3b659b52caa3850d3fad3e3041268f19269007288a49fc6bc0c6` |
| [F04_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json](../../kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json) | `525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22` |

Accepted prefixes are relative to `examples/KG_Assoc/kg_assoc_100m/`:

**F04_N010_RP080_EE04_EA04**, absolute step 2,000,000:

- r001: `banks/e2_attempts/F04_N010_RP080_EE04/equilibrate_5a06db30dfba406bacb8937f39e14eea/r001/state`; chemical seed `420401`.
- r002: `banks/e2_attempts/F04_N010_RP080_EE04/equilibrate_5a06db30dfba406bacb8937f39e14eea/r002/state`; chemical seed `420402`.
- r003: `banks/e2_attempts/F04_N010_RP080_EE04/equilibrate_5a06db30dfba406bacb8937f39e14eea/r003/state`; chemical seed `420403`.

**F04_N010_RP020_EE08_EA04**, absolute step 6,000,000:

- r001: `banks/e2_attempts/F04_N010_RP020_EE08/equilibrate_13a6951adf16448cb5365a8b28e28427/r001/state`; chemical seed `420101`.
- r002: `banks/e2_attempts/F04_N010_RP020_EE08/equilibrate_13a6951adf16448cb5365a8b28e28427/r002/state`; chemical seed `420102`.
- r003: `banks/e2_attempts/F04_N010_RP020_EE08/equilibrate_13a6951adf16448cb5365a8b28e28427/r003/state`; chemical seed `420103`.

**F04_N010_RP080_EE08_EA04**, absolute step 8,000,000:

- r001: `banks/e2_extensions/C1_periodic_recovery_v1/r001/state`; chemical seed `22001`.
- r002: `banks/e2_extensions/C1_periodic_recovery_v1/r002/state`; chemical seed `22002`.
- r003: `banks/e2_extensions/C1_periodic_recovery_v1/r003/state`; chemical seed `22003`.

The individual snapshot/sidecar hashes and all bound completion/source hashes
are listed in the canonical records and [RECORDS.json](RECORDS.json). Fresh
authentication evidence is in [AUTHENTICATION.json](AUTHENTICATION.json).

## Completed checks

```sh
PYTHONPATH=examples/KG_Assoc/campaign python3 -m unittest test_e2_acceptance test_joint_e2 test_catalog test_e2_recover test_run_e2 test_e2_g1 -q
```

**99 CPU tests passed.** Python compilation and `git diff --check` also pass.
The new committed-record test binds all three record hashes to this index,
checks exact permitted systems/steps/replicas and the dilute review's pinned
endpoint identities, and retains the corrected-C1 provenance requirement.
Existing legacy validator `ResourceWarning` messages about unclosed input files
remain unchanged.

A real-data catalog scan finds exactly these three valid formal acceptances,
zero registry views/selections and absent production authorization for every
system. Production eligibility remains blocked for the three accepted systems.
All 126 checked original payload/provenance hash bindings remain intact; both
prior scientific dossiers are byte-identical to the starting Git commit.
The canonical API-generated record files and their committed copies are
byte-identical. Protected `src/`, `examples/KG/`, all native simulation sources,
existing trajectories/restarts and historical records are unchanged.
