# f=3 qualified formal E2 acceptance at 8M — unactivated

The user explicitly approved qualified formal scientific acceptance of `F03_N010_RP080_EE08_EA04` for **production initialization only**, using exactly r001/r002/r003 at absolute step 8,000,000 documented in the [immutable 8M scientific dossier](../e2_f3_8m_20261013/DECISION.md). This is explicit user approval, not acceptance inferred from a recommendation.

Starting local and remote `KremerGrest`: `f4bc81b2d7ed3ac5ee8f306c7000f532c7406656`.

## Immutable record and exact endpoint bindings

The unchanged established `kg_assoc_e2_registry.accept()` API created the record with exclusive file creation, followed by `exclusive_validate()`. The JSON was not manually edited. Only this new metadata file is added to the otherwise ignored dataset.

Record: `examples/KG_Assoc/kg_assoc_100m/banks/e2_acceptance/F03_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json`.
SHA256: `3c7633e7b42341af66c34a5b29ed86d0ae8bd2176cb401a7f35920be3d5ec13c`.

Status: `accepted_with_qualification`; permitted use: `production_initial_state`; permitted system: **only** `F03_N010_RP080_EE08_EA04`. Source extension plan SHA256: `fd2a6b8a0bd6def0ce11e45d9afe4369111b10a7249a162ef7b21d78e81546cd`.

Prefixes below are relative to `examples/KG_Assoc/kg_assoc_100m/`. Every endpoint is absolute step **8,000,000**, never the earlier 6M state or a smoke state.

- r001: `banks/e2_attempts/F03_N010_RP080_EE08/equilibrate_9b51f865c4464eefb210188d802c0c5e/r001/state`; chemistry/MD/effective MD seeds `420001/520064/3900917504`.
  - Restart SHA256: `5dfa1939b337e0b1a4a141c44afb4f2657732fb05b34e187407c6a680f08f45b`.
  - Chemical sidecar SHA256: `cdd854a8c0b9958bfcdc6b519b10d9fdcfb13b1696340fdc13806fad891b4af5`.
- r002: `banks/e2_attempts/F03_N010_RP080_EE08/equilibrate_9b51f865c4464eefb210188d802c0c5e/r002/state`; chemistry/MD/effective MD seeds `420002/520065/3892549376`.
  - Restart SHA256: `cb8308e455417f775245f7fb4ee878d9ae9def8222a8670640eff129263f4435`.
  - Chemical sidecar SHA256: `38fc604eee6caa73f7010bb73562a9f6f950653f99bb1c840fd7ab97012d48ed`.
- r003: `banks/e2_attempts/F03_N010_RP080_EE08/equilibrate_9b51f865c4464eefb210188d802c0c5e/r003/state`; chemistry/MD/effective MD seeds `420003/520066/3917670144`.
  - Restart SHA256: `73c3b7a5de5b755e444e01b14de10a2655ed06fd94a678d8656db8f53df00889`.
  - Chemical sidecar SHA256: `dce66610085a0c6bc695da4bb1e7d987bec3ca799513e0a78bbf2fe582e18257`.

## Authentication and surviving evidence

Fresh CPU authentication covers the complete E1 → 0–6M → 6–8M lineage. The original E1 snapshots/completions/diagnostics match the frozen active inventory. Both E2 plans, approvals, replica identities, physical parameters, seed identities, parent/output/receipt hashes and exact absolute-step boundaries authenticate. All six segment/replica combinations pass independent existing numerical, accepted-event/network and conformation revalidation, with the three original histories preserved as the statistical units. The acceptance API additionally revalidates the selected extension and binds every output payload, completion receipt and source plan. [REGISTRATION.json](REGISTRATION.json) freezes these checks and the original scientific dossier hashes.

Current extension scientific sources, build manifest/logs and executable bytes authenticate. Original 0–6M historical executable bytes are unavailable for direct reauthentication; their recorded digests, source versions, authenticated build manifests/logs, code commits, E1/parent payloads, completion receipts and freshly validated numerical/event/network/conformation outputs survive. No missing executable is silently substituted or described as freshly reauthenticated.

## Preserved scientific qualifications

- Slow network-topology decorrelation remains unproven.
- Satellite populations recovered after the earlier decline, but their stationary distribution is not precisely determined.
- Small isolation, degree-distribution and conformational changes remain.
- Original historical executable bytes have the limitation stated above.
- At 6M, MD seeds change from 520058/520059/520060 to 520064/520065/520066; chemistry seeds remain 420001/420002/420003. Do not stitch correlations, residence, stress or transport histories across this boundary.

The [original 6M scientific hold](../e2_f3_6m_20261013/DECISION.md) and [8M recommendation](../e2_f3_8m_20261013/DECISION.md) remain byte-identical historical evidence. This formal registration supersedes the 6M recommendation for the system by accepting only the precise reviewed 8M states. Earlier 6M states, smokes and all other unapproved systems remain ineligible. No new scientific equilibration claim is added by registration.

## Five formal acceptances, no active endpoint selection

[RECORDS.json](RECORDS.json) is the new immutable five-record snapshot. The earlier [three-system registration](../e2_formal_acceptance_20261013/README.md) and [f=6 registration](../e2_f6_formal_acceptance_20261013/README.md) remain unchanged.

| System | Absolute endpoint step | Record SHA256 |
|---|---:|---|
| F03_N010_RP080_EE08_EA04 | 8000000 | `3c7633e7b42341af66c34a5b29ed86d0ae8bd2176cb401a7f35920be3d5ec13c` |
| F04_N010_RP020_EE08_EA04 | 6000000 | `20f7ed7ae7fb3b659b52caa3850d3fad3e3041268f19269007288a49fc6bc0c6` |
| F04_N010_RP080_EE04_EA04 | 2000000 | `7f5cd4ba2ace52b0b8a62a54ffe63bebf62c1bf4a6d22bb330df97ce44e8bb6a` |
| F04_N010_RP080_EE08_EA04 | 8000000 | `525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22` |
| F06_N010_RP080_EE08_EA04 | 6000000 | `81179644b404b3ab5a492ad60bba0d3d23502d0f5d7da4d058552fa9a5e714c0` |

The catalog automatically recognizes five qualified formal records, exposing `formal_acceptance_recorded_payload_deferred` for f=3 while keeping `selection: missing`, `production_authorization: absent` and production eligibility blocked. The historical hold remains visible with explicit documented supersession. A routine catalog refresh remains metadata-level verification; it is not deep payload authentication. No catalog source logic or simulation workflow changed.

No `publish()` was called. No active registry was published, activated or selected. No production preparation, launch authorization, GPU calculation, further equilibration or production run occurred. Registry activation and production authorization require separate explicit user decisions. The next scientific phase remains equilibration of the remaining systems.

## Regression and integrity verification

**117 CPU tests passed:**

```sh
PYTHONPATH=examples/KG_Assoc/campaign python3 -m unittest test_e2_acceptance test_joint_e2 test_catalog test_e2_recover test_run_e2 test_e2_g1 test_e2_satellite_continuation test_e2_window_sensitivity test_e2_peripheral_network -q
```

Tests cover approved endpoint/hash binding, exactly r001/r002/r003 at 8M, preservation of the four existing acceptance bytes, all qualifications, immutable/no-overwrite behavior, 6M/smoke/seed/physics/replica substitution rejection and fail-closed resolution without an explicitly selected registry. Existing joint, satellite, catalog, recovery and wrapper tests remain included.

Python compilation and diff whitespace checks pass. No native code changed; no executable rebuild or GPU validation is required. Existing legacy restart reader ResourceWarnings remain unchanged. Original scientific dossier hashes and all recorded parent/output hashes are checked again before commit. Protected `src/` and `examples/KG/`, historical reviews, simulation data and four prior acceptance records remain unchanged.
