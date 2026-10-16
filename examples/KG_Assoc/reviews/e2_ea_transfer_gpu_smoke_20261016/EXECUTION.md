# Execution provenance and exact identities

User authority is recorded in AUTHORIZATION.json. Each immutable plan has an
explicit `e2_derived_smoke` approval binding its exact SHA256, recorded user authority,
10,000-step history ceiling and 120,000 aggregate ceiling. Approvals and plans were
validated before any MD. The clean starting local and remote SHA matched
`2f961789c1bb18bba13f911cf7687222595f7649`.

## Established workflow and deviations

All four inspections and preparations used `kg_assoc_e2_transfer.inspect/prepare`,
with the pinned acceptance, default immutable reservation file and the authenticated
out-of-tree build. Launches used `kg_assoc_e2.launch(execute=True, approval=...)`.
The same API entry points back the documented CLIs. No direct simulator launch or
alternate authorization path was used. Plan preparation performs host-only initial
state checks before creating empty replica directories. Each replica launch repeats
live source, executable, parent and approval authentication.

Execution order was Ea4, Ea6, Ea8; the Ea8 r001 exception aborted the serial
orchestrator. The required deviation from the twelve-history proposal is five
unexecuted histories and one incomplete history. They were not resumed or replaced.
All twelve reserved rows are now claimed by their immutable plans, including the
unstarted ones. They must not be silently reclaimed for another attempt.

Raw MD outputs remain in the ignored campaign dataset, as in earlier reviews.
EXECUTION_METADATA.json contains parsed copies of all four actual plans and
approvals, six completion receipts, one incomplete receipt, seven start/environment
records and the five empty-directory states. NEW_OUTPUTS_SHA256.json binds all
106 new campaign artifact files, including the exact raw metadata bytes.
RESULTS.json contains all twelve histories’ identities, seeds, ancestry and statuses,
with full numerical detail for the six completions and censored Ea8 data.

## Build identity

Build directory: `examples/KG_Assoc/kg_assoc_100m/builds/ea_reference_transfer_cpu_20261016_v1`.
Manifest SHA256: `6d04459efe40df2698e5f40a6ad67d922fe31b5fc49ba16e9450f2290ced5446`.
Build Git SHA: `523f49be292d32c48ad216103b126341ba337159` (ancestor of starting HEAD).
All 591 source bindings, executable hashes and build logs authenticated before
planning/execution. No rebuild was required and no campaign executable was replaced.

| Executable | SHA256 |
|---|---|
| `kg_assoc_candidates_test` | `275d03f2706842082fa5419fcf063621ad647c31216cbfbe84d850b6abf41182` |
| `kg_assoc_stars` | `fcf7fc296e4cfa16f8178b174287a2c4ec7dac2bf8d9c8cad975bf72412b5a1a` |
| `kg_assoc_stars_candidate_smoke` | `bc67902ecbf9ee61ba5d3955f63648c284a648d5406c474a0d18209ab09eb578` |

GPU: NVIDIA TITAN Xp, UUID `GPU-8170bfc5-0914-1b23-e2b6-fdb85300a2b6`,
driver 580.178.04, host `titan`. Per-history runtime environment and requested/
effective MD streams are recorded in immutable logs and receipt snapshots.

## Exact parent pairs

Only the qualified corrected-C1 Ea4/Ee8 record is eligible:
`banks/e2_acceptance/F04_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json`.
SHA256: `525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22`.
Its scope remains production_initial_state for the reference system only.
Full qualification text and historical executable-authentication limits are retained
in every history’s lineage. Original defective historical C1 endpoints were not used.

Parent prefixes below are relative to `examples/KG_Assoc/kg_assoc_100m/`.

### r001

Prefix: `banks/e2_extensions/C1_periodic_recovery_v1/r001/state`.
Absolute step 8,000,000; old chemical seed 22001; inherited
creations 119665, breaks 117882, bonds 1783.

* `.restart.lammpsdat` SHA256: `09e1a9f5329a2be06e28112c5bc53e399f54c7aba74369684f12968f68d6b21b`.
* `.assoc_restart` SHA256: `9eb4e566d96f0080d9a03677e5d23d231ce389193c71a57f68c58f22035e9ecc`.

### r002

Prefix: `banks/e2_extensions/C1_periodic_recovery_v1/r002/state`.
Absolute step 8,000,000; old chemical seed 22002; inherited
creations 120242, breaks 118455, bonds 1787.

* `.restart.lammpsdat` SHA256: `ae1599f3d2ffcfd333058b2867bbc7ba897b7dccd84e8b2e7a2996aaa6df3c5b`.
* `.assoc_restart` SHA256: `7fd18a27d4d989881397b33b94ffe92de21a05c1e318f8236586b737ee697674`.

### r003

Prefix: `banks/e2_extensions/C1_periodic_recovery_v1/r003/state`.
Absolute step 8,000,000; old chemical seed 22003; inherited
creations 119059, breaks 117256, bonds 1803.

* `.restart.lammpsdat` SHA256: `10a7885b6e704258dee322e4c310f26bfe921b586e769a477600d515ef888e2a`.
* `.assoc_restart` SHA256: `8a260fd5a6e5b3408ba71e10ccb2e47437cf61691036e5c82fcf1c9ac058427c`.

## All twelve planned identities

Target/full SID and replica are part of each derived branch ID. Every attempt is
a direct child of `banks/e2_attempts/F04_N010_RP080_EE08/`, named
`derived_<FULL_SYSTEM_ID>_gpu_smoke_20261016_v1`. Replica prefix is `r00r/state`.
All parents start at absolute 8M; branch age and inherited counter offsets are
explicit, with no synthetic creation/break events. Chemistry partners persist;
only Ea and designated random streams change. GJ internal state resets and all
histories are **non-bitwise continuations**. T, Ee, density/box, mechanical and
reaction parameters remain those in the authenticated parent and frozen protocol.

| Ea | Replica | Chemical seed | Requested MD seed | Effective MD seed | Status |
|---|---|---:|---:|---:|---|
| 4 | r001 | 620401 | 630401 | 2030347387 | validated |
| 4 | r002 | 620402 | 630402 | 2038756481 | validated |
| 4 | r003 | 620403 | 630403 | 2047165567 | validated |
| 6 | r001 | 620601 | 630601 | 1562010781 | validated |
| 6 | r002 | 620602 | 630602 | 1570419871 | validated |
| 6 | r003 | 620603 | 630603 | 1578828961 | validated |
| 8 | r001 | 620801 | 630801 | 2357264817 | failed |
| 8 | r002 | 620802 | 630802 | 2348896689 | not_executed |
| 8 | r003 | 620803 | 630803 | 2340528561 | not_executed |
| 10 | r001 | 621001 | 631001 | 2964726433 | not_executed |
| 10 | r002 | 621002 | 631002 | 2956358305 | not_executed |
| 10 | r003 | 621003 | 631003 | 2947990177 | not_executed |

## Numerically completed smoke output pairs

These six endpoints are **smoke outputs, not qualified production initial states**.
Their absolute step is 8,010,000. No scientific acceptance or formal registration
was performed. No endpoint exists for the failed or unexecuted histories.

### Ea4 r001

Prefix: `banks/e2_attempts/F04_N010_RP080_EE08/derived_F04_N010_RP080_EE08_EA04_gpu_smoke_20261016_v1/r001/state`.

* `.restart.lammpsdat` SHA256: `36ba2629e5fbcbf956f58918e3b9f4712d553434eb8ef8c3e0990c2cffa303ac`.
* `.assoc_restart` SHA256: `8ac771b3788fd81447379800f3cc20e34f78fd2c9e5e27dfa69b5520ccef5388`.

### Ea4 r002

Prefix: `banks/e2_attempts/F04_N010_RP080_EE08/derived_F04_N010_RP080_EE08_EA04_gpu_smoke_20261016_v1/r002/state`.

* `.restart.lammpsdat` SHA256: `44487ef783bcf80328b4b228093ee6a4e6b968284d41e17acbd8dcbfc2545e22`.
* `.assoc_restart` SHA256: `9da421785fb949dc00cd6fee7bed99aa1e39636752d2067d710b76ea507d37c6`.

### Ea4 r003

Prefix: `banks/e2_attempts/F04_N010_RP080_EE08/derived_F04_N010_RP080_EE08_EA04_gpu_smoke_20261016_v1/r003/state`.

* `.restart.lammpsdat` SHA256: `aeeaf92cc26f7e241ae0608b77ad1589e63cb62c171ec8ef39755fcf3ec7f8c9`.
* `.assoc_restart` SHA256: `a8fae3d3ec0cc456d2e5bae1f1ea5609f3f5f6bb5f187a13e27a5a42503307b2`.

### Ea6 r001

Prefix: `banks/e2_attempts/F04_N010_RP080_EE08/derived_F04_N010_RP080_EE08_EA06_gpu_smoke_20261016_v1/r001/state`.

* `.restart.lammpsdat` SHA256: `5d6e051be0406d37c3b15dd1af09f46db31c64e207bd937e64aeeb7ccc07f9af`.
* `.assoc_restart` SHA256: `2f31abfb0a357a74834c83346a40d4d228921ec88f0b983afba69ecec7900d9d`.

### Ea6 r002

Prefix: `banks/e2_attempts/F04_N010_RP080_EE08/derived_F04_N010_RP080_EE08_EA06_gpu_smoke_20261016_v1/r002/state`.

* `.restart.lammpsdat` SHA256: `d6502be49d495da1bb5a2df62b29d0295f6e0ace857d4d4c451fcd2e36a6d976`.
* `.assoc_restart` SHA256: `9efe657a69463b13e4b61c1858a73b0a215ca9d0c9da62fdd05d519d5198876b`.

### Ea6 r003

Prefix: `banks/e2_attempts/F04_N010_RP080_EE08/derived_F04_N010_RP080_EE08_EA06_gpu_smoke_20261016_v1/r003/state`.

* `.restart.lammpsdat` SHA256: `c8e23ca9cc728006a22030528e695c95a88e2dbac53d3a3fe685e99a4f6f94d8`.
* `.assoc_restart` SHA256: `816f486940b8565a6cc39b124d319c6cd56b0e8feef9c149f5afb11f1fdd5852`.

## Evidence limitations

Raw trajectories and binary executables are not placed in Git. Reproduction of
CPU replay needs this dataset and the bound immutable outputs. The Git dossier
preserves their identities and parsed receipts, not replacement physical evidence.
The failed history has no final restart, chemical sidecar, final geometry/velocity
check or completion marker. Its saved diagnostic endpoint is 8,007,000; inferred
failure at 8,007,100 is identified explicitly. No pair/distance dump exists for
that failure. No independent full per-particle initial GPU readback was emitted.
Those omissions remain validation limitations; no absent measurements are invented.
