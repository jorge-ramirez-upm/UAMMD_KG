# f=4, N=20 qualified formal E2 acceptance at 6M — unactivated

The user explicitly approved qualified formal scientific acceptance of `F04_N020_RP080_EE08_EA04` for **production initialization only**, using exactly r001/r002/r003 at absolute step 6,000,000 documented in the [immutable scientific dossier](../e2_n20_6m_20261013/DECISION.md). Authorization is explicit user approval, not inferred from a scientific recommendation.

Starting verified local/remote `KremerGrest`: `27654bb4f4ce9e11b58528719d68c349c3ccad76`.

## Immutable acceptance record

The unchanged established `kg_assoc_e2_registry.accept()` API created this record with exclusive file creation, followed by `exclusive_validate()`. Its JSON was not manually edited. Only the new metadata record is added to the otherwise ignored dataset.

Record: `examples/KG_Assoc/kg_assoc_100m/banks/e2_acceptance/F04_N020_RP080_EE08_EA04_6M_qualified_20261013_v1.json`.
SHA256: `6ebb95dda283828342f7bd55fe2331e51e2a0477e70234e54e9631fd78bf7422`.

Status: `accepted_with_qualification`; permitted use: `production_initial_state`; permitted system: **only** `F04_N020_RP080_EE08_EA04`. Source-plan SHA256: `085a6a56f004ef6c5d21d2d0fa0a9277e51e8c97c96312eaf34e2067de5e5b90`.

## Exact approved endpoints

All three are absolute **6,000,000**. Prefixes below are relative to `examples/KG_Assoc/kg_assoc_100m/`; no earlier, smoke or other-attempt state is permitted.

- r001: `banks/e2_attempts/F04_N020_RP080_EE08/equilibrate_bdfe5dc30d87435899f6d2d21dc99fac/r001/state`; chemistry/MD/effective MD seeds `420901/520070/3951175424`.
  - Restart SHA256: `290af8505bd3fe5b39b391fc9bd5ddffa5b9229ef36930d1c89e0cc5a3a5618f`.
  - Chemical sidecar SHA256: `a871ff27c1f9af22a4c534b6542e2287f9d0ad61973c91a8d2fa583c16f09406`.
- r002: `banks/e2_attempts/F04_N020_RP080_EE08/equilibrate_bdfe5dc30d87435899f6d2d21dc99fac/r002/state`; chemistry/MD/effective MD seeds `420902/520071/3942807296`.
  - Restart SHA256: `d74f5e21323b5989693a300046fdeb98ca463cc2032cae43f18ad25d3fa49752`.
  - Chemical sidecar SHA256: `2c8ba79d5431c1b7d7dad0a1d22541777434aa6950f165886794525cb2513265`.
- r003: `banks/e2_attempts/F04_N020_RP080_EE08/equilibrate_bdfe5dc30d87435899f6d2d21dc99fac/r003/state`; chemistry/MD/effective MD seeds `420903/520072/3833972496`.
  - Restart SHA256: `21677b64503c4447c00c2d428c3d98d87d423cfc4c6e3ff19c8a41d32c6d2e3b`.
  - Chemical sidecar SHA256: `5ebda1164d8345debcb02a4c35a3b3aaf24e9c6a699d6c9542514cf339a19553`.

## Authentication and scientific qualifications

Fresh CPU authentication verifies E1 → E2: frozen active E1 snapshots, completion records and diagnostics; replica/particle/sticker identities; plan/approval and physical parameters; chemical/MD seeds; current source/build/log/executable hashes; completion receipts and endpoint payloads. All three continuous 0–6M histories pass existing numerical, accepted-event/network and conformation validation. The acceptance API separately revalidates the selected attempt and binds every output payload, completion receipt and source plan. No unavailable-historical-binary limitation applies to this N=20 attempt. T=1, dt=0.01, Ea=4, Ee=8 and all frozen geometry/physical parameters are unchanged. Exact evidence is in [REGISTRATION.json](REGISTRATION.json).

- Full conformational stationarity and slow topology decorrelation are not demonstrated.
- The original 2–4M versus 4–6M conformational expansion is not sustained across alternative comparisons.
- Conformational effective sampling is limited; three histories remain the statistical units.
- The giant-cluster fraction has a small shared late decrease, with possible peripheral-connectivity redistribution.
- Slow L1/L2 and intra/inter modes remain incompletely resolved.
- Late intra-star associations show a shared decrease in the final 500k interval.
- Comparing N=20 with N=10 changes star/sticker number densities as well as arm length at fixed polymer bead density.
- Small shared neighbor-turnover changes remain; overlapping windows and time blocks are not additional replicas.

The original review, figures, source authentication and simulation files remain byte-identical. Registration adds no new equilibration claim, universal threshold or permission to launch production.

## Six formal acceptances; no registry selection or production permission

[RECORDS.json](RECORDS.json) is a new immutable six-record snapshot. The earlier [three-system](../e2_formal_acceptance_20261013/README.md), [f=6](../e2_f6_formal_acceptance_20261013/README.md) and [f=3](../e2_f3_formal_acceptance_20261013/README.md) registration dossiers are historical and unchanged. None of the five prior records is modified or superseded.

| System | Absolute endpoint step | Acceptance SHA256 |
|---|---:|---|
| F03_N010_RP080_EE08_EA04 | 8000000 | `3c7633e7b42341af66c34a5b29ed86d0ae8bd2176cb401a7f35920be3d5ec13c` |
| F04_N010_RP020_EE08_EA04 | 6000000 | `20f7ed7ae7fb3b659b52caa3850d3fad3e3041268f19269007288a49fc6bc0c6` |
| F04_N010_RP080_EE04_EA04 | 2000000 | `7f5cd4ba2ace52b0b8a62a54ffe63bebf62c1bf4a6d22bb330df97ce44e8bb6a` |
| F04_N010_RP080_EE08_EA04 | 8000000 | `525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22` |
| F04_N020_RP080_EE08_EA04 | 6000000 | `6ebb95dda283828342f7bd55fe2331e51e2a0477e70234e54e9631fd78bf7422` |
| F06_N010_RP080_EE08_EA04 | 6000000 | `81179644b404b3ab5a492ad60bba0d3d23502d0f5d7da4d058552fa9a5e714c0` |

The catalog automatically recognizes six formal records. N=20 scientific status is `formal_acceptance_recorded_payload_deferred`, while `selection: missing`, `production_authorization: absent` and blocked production eligibility remain. A fast catalog refresh is still metadata-level verification; it does not perform this dossier’s full payload authentication. No catalog source or simulation workflow change was necessary.

No `publish()` was called. No registry was published, activated or selected. No GPU calculation, further equilibration, production preparation/authorization or launch occurred. Registry activation and production authorization are separate future decisions requiring explicit approval. Other unapproved systems gain no eligibility.

## Verification

**124 CPU tests passed:**

```sh
PYTHONPATH=examples/KG_Assoc/campaign python3 -m unittest test_e2_acceptance test_joint_e2 test_catalog test_e2_recover test_run_e2 test_e2_g1 test_e2_satellite_continuation test_e2_window_sensitivity test_e2_peripheral_network test_e2_continuous_review -q
```

Tests cover immutable endpoint/hash bindings, exact approved replica/step/attempt selection, qualifications, five-record preservation, no-overwrite behavior, earlier/smoke/other-attempt/seed/geometry substitution rejection and fail-closed resolution without an explicit registry.

Python compilation and diff whitespace checks pass. Existing legacy restart-reader ResourceWarnings remain unchanged. No native source/header changed; no executable rebuild or GPU validation was required. Final integrity checks reauthenticate approved payloads, E1 bindings and scientific dossier hashes and compare the five prior acceptance bytes to Git. Protected `src/` and `examples/KG/`, historical reviews, simulation data and previous formal acceptances are unchanged.
