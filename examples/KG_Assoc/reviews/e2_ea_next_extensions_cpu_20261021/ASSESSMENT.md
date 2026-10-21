# CPU-only preparation: Ea8 40M--48M and Ea10 56M--88M

Starting clean local/remote `KremerGrest` SHA:
`88ccd6fee6e783bf6897ccdd96969e73b496a4bf`. Review date: 2026-10-21.

## Prepared scope and scientific purpose

**Six histories are prepared. GPU execution is not authorized. No MD step was integrated.**
Campaign identity: **`manual_ea_extensions_48m_88m_v1`**. The immutable preparation state is
`kg_assoc_100m/aggregate/e2/manual_ea_extensions_48m_88m_v1/state.json`, SHA256
`c50c5e531f8c0557d7034690085a6c6dabd40931255637511e7cacb29545c08b`.

| System | Replicas | Start | Additional steps each | Endpoint | 500k windows each |
|---|---|---:|---:|---:|---:|
| F04_N010_RP080_EE08_EA08 | r001--r003 | 40M | 8M | 48M | 16 |
| F04_N010_RP080_EE08_EA10 | r001--r003 | 56M | 32M | 88M | 64 |

The prospective completed-trajectory total is 120M steps; separately recorded interrupted work is
not hidden in that total. These are two immutable three-replica plans with six unique history/output
directories. No extra replica or Ea4 control is prepared.

The joint review `e2_ea_extensions_joint_20261021` holds both systems scientifically. Ea8 requires
testing r002's late intra/shape/coordination redistribution, r001 multiplicity excursions, and r003
peripheral/multiplicity changes. Ea10 requires testing r001 multiplicity/shape drift, r002 triangle
redistribution and slow identity-specific connectivity/residence. Preparation does not remove these
holds. The intended future review retains all earlier evidence and the three paired original Ea4
families; neither completion nor similar ensemble means will automatically qualify endpoints.

## Exact parent authentication

All six exact restart/sidecar pairs in the joint review's ENDPOINTS.csv authenticate, including their
receipt hashes, start/end accounting, chemistry seeds and cumulative counters. The review's integrity
root is pinned as `bdc800e35620c5e41022101b3c96d5e91638062865da6f581c615bbad205e701`.
The historical durable state is hash-bound to that review, and its six jobs exactly match the reviewed
lineages. The complete preparation/execution/source-authorization chains and approved source map
are checked against immutable Git blobs at the reviewed source commit, with Git ancestry verified.
Historical build/source evidence is checked in its committed context, not against a later front end.

The authenticated parent receipt validation objects match the independently replayed joint review:
all six device-readback payloads, 1,440,000 oracle sweeps and complete accepted-event/counter evidence.
Output hashes, predecessor hashes, reservations, build logs and executable identities are rechecked.
This is authentication of existing numerical evidence; it is not a new GPU readback or oracle run.

Ea8 r001 uses its authoritative `validation_recovery.json`, SHA256
`91a4fa743735a515353d592213d0ee67cf9e2208ca31dc29cfda4b002aaa5091`, with its original
`incomplete.json` SHA256 `14772d19744e253097b4376195210f9591eb6c85df0a012b0ad25f60c46b017c`
and `recovered_complete` state preserved. No ordinary completion receipt is demanded or synthesized.
Invalid recovered lineage, incomplete status or substituted endpoint hashes fail closed.

PARENTS_AND_CHILDREN.csv gives all six exact parent pairs, inherited counters, parent receipts,
planned output prefixes, seeds, approvals and SHA256s. PLANS.log and PREPARATION.tar.gz retain
byte copies of the exact new plans, preparation approvals, source bindings, reservations, state
and build metadata. Originals remain in their separate immutable dataset locations.

## New attempts and random streams

| Ea | New plan container | Plan SHA256 |
|---:|---|---|
| 8 | `extension_F04_N010_RP080_EE08_EA08_next_cfb25731e8b442f0b2019eb0b6699cb7` | `52fb04671910f2cc63ac71fce4958068f6e6ee05c2c0c4828b1477ea7fffd3bb` |
| 10 | `extension_F04_N010_RP080_EE08_EA10_next_85928c3ef15c4e06bab10493394a7e25` | `827db432d0abc3f660a16bd6746c9089c47b2daeaf39a73ec5a75906985fae06` |

Each has r001/r002/r003 subdirectories, all empty after preparation and tests. Each replica has a
separate immutable preparation-only approval with `GPU_execution_authorized=false` and its exact
replica, plan, start/end and step cap. Six additional source-binding records authenticate the exact
prepared source map; their legacy `execution_approval_sha256` field binds the GPU-disabled
preparation approval. These source records provide no GPU authority. No execution approval file
has been created. A later milestone must publish new immutable execution approvals and source
bindings rather than editing the preparation records or state.

| Ea | Replica | Inherited chemical seed | Fresh requested MD seed | Effective MD seed | Inherited creations / breaks |
|---:|---|---:|---:|---:|---:|
| 8 | r001 | 1220801 | 1331016 | 1328681519 | 132319 / 130526 |
| 8 | r002 | 1220802 | 1331017 | 1337082417 | 132884 / 131091 |
| 8 | r003 | 1220803 | 1331018 | 1345417779 | 131825 / 130034 |
| 10 | r001 | 1321001 | 1331019 | 1353818677 | 122182 / 120407 |
| 10 | r002 | 1321002 | 1331020 | 1295045167 | 122807 / 121015 |
| 10 | r003 | 1321003 | 1331021 | 1303446065 | 121676 / 119877 |

Two new immutable MD-reservation identities match the plan-container names and use the new scope
`Ea_transfer_40M_56M_extensions_v1`. Both requested and effective streams were checked against
all historical plans, consumed and reserved streams, held attempts, and policy reservations. No
chemical stream was reseeded. Connectivity, counters and absolute-step chemistry keys are inherited.
Fresh GJ noise makes each new segment non-bitwise; lifetime, correlation and SEM origins must not
cross the 40M/56M boundaries. The child mode is explicitly `Ea_reviewed_extension_v2`.

## Native and administrative implementation

The former executable rejects these exact step ranges. The minimal native addition is a guarded
`--e2-reviewed-extension` flag accepting only Ea8 40M+8M and Ea10 56M+32M, with the same fixed
physics, seed-family and parent-state checks as the original extension. Mixed flags, physical
overrides, wrong parent steps, wrong seeds and wrong durations are rejected. The existing 24M
flag keeps its original scope. NATIVE_SCOPE.patch shows the complete native change: argument
guarding, parent-step selection and lineage labeling only. The physical restart loader, device
initialization, force/reaction/search/integrator implementations and RNG algorithms are unchanged.

The new administrative planner authenticates reviewed parents, including recovered receipts. It
reuses existing reservation, command, readback, event-replay, numeric and launch helpers. The shared
launcher dispatches the new mode to that planner and forces the independent oracle/readback path
through the existing validator. Pre-run, immediate-launch and post-run checks receive the same
authorized source map. The immutable source-authorization file itself is now hash-bound in the
start receipt and checked again after native PASS. Unapproved source evolution fails closed.

The native code sets the same extension dispatcher flag used by the corrected initial readback.
Its exact comparison body and dispatcher header remain unchanged. The optimized executable's
CPU spy reports `INITIAL_READBACK_CALL_PATH_V2 CPU_ONLY cases=4 fail_stop=3`. This proves the
compiled dispatch/fail-stop contract, not actual GPU execution in this milestone. A later authorized
trajectory must produce genuine exact initial GPU readback before its first integrated MD step;
missing evidence cannot be substituted by host initialization.

## New authenticated build

Directory: `kg_assoc_100m/builds/ea_extensions_48m_88m_20261021_v1`.
Source/build commit: `64070a327d320ac2fb6984adbc002036e396721d`.
Forced out-of-tree optimized compilation completed in **73.904 s**, NVCC 12.8.93 / GCC 11.2.0,
with `-O3`; no historical executable was replaced.

| Executable | SHA256 |
|---|---|
| kg_assoc_stars | `2ea4b95ca045b40d61b749f8004d8f9a31178a3dc96ad1e414e57b06d150d0b7` |
| kg_assoc_stars_candidate_smoke | `6331c034d8ddb494be616770f2bcc56f5a5fb644f5cb30838e593d259eaf451d` |
| kg_assoc_candidates_test | `70280144fcd484660ffe74e442b63e20faf830d7b6bf4b81857f8d68c6ec1ab3` |

BUILD.log binds the full source map, compile commands, executable digests, compiler versions and
build logs. The planner rejects the old build for these scopes even though it remains valid historical
evidence. All six host-only initializations passed with inherited particles, physical/chemical
fingerprints, seeds and counters; those fingerprints are comparison aids, not authentication hashes.

## CPU verification and recovery policy

Established E2 suite: **189/189 passed**. Focused next-extension/legacy/readback/preparation suite:
**58 tests, 57 passed and 1 existing skip**. Transfer suite: **14/14 passed**, using the new host
executable. Real prepared-plan checks: **7/7 passed**. Interruption/hold/skip tests: **5/5 passed**.
These suites overlap; their counts should not be summed as unique cases. Logs are included.

Two additional ordinary strict parent replays passed using the new historical-lineage wiring:
the recovered Ea8 r001 parent (160,000 sweeps) and ordinary Ea10 r001 parent (320,000 sweeps).
Each reproduced its exact receipt validation, including the original GPU-readback artifact,
accepted-event replay, numerical checks and endpoint consistency. These CPU replays integrate no MD.

Coverage includes exact ranges and selections; false preparation approval rejection before launch;
identical pre/post authorized source maps; authorization-file tampering after a mocked native PASS;
missing readback; invalid recovered lineage; source-map/ancestry violations; old/mismatched builds;
duplicate requested/effective MD streams; substituted parent pairs; duplicate output paths; isolated
unselected directories; immutable-state preparation idempotence; host-native positive and negative
cases; ordinary restart and legacy-mode compatibility; and the compiled CPU readback/candidate probes.
An initial legacy host-test fixture correctly hit the output-reuse guard; its probe now uses an empty
temporary prefix. The historical output was never modified.

The frozen preparation state is never rewritten by execution. A separate runtime journal may later
track replacements. Completed independently validated histories are skipped. Running histories
cannot launch twice. A true partial history is preserved, its lower/upper step overhead recorded,
and a fresh CPU-only attempt allocated from the same exact parent with new streams. The replacement
requires a new explicit plan-bound GPU approval before any launch. Native-PASS administrative
validation exceptions, missing device evidence, candidate mismatches and numerical/provenance
failures remain held; none is silently classified as a retry. Recovery of such a completion needs
an explicit authenticated CPU recovery, not another MD trajectory.

All assistant computations were CPU-only and individually bounded by 600 s. New MD steps: **0**.
No synthetic device evidence was created in any real attempt. No GPU approval, scientific acceptance
or production action was performed.

## Preservation and handoff status

The before/after audit verifies **3,626 historical file bindings unchanged**, including all thirteen
formal acceptances and their payloads, previous campaign states/plans/approvals/reservations,
the six current endpoints, Ea8 r001 failure/recovery, earlier dossiers and historical builds.
The new preparation/source/build audit contains **689 bindings**. No `src/*` or `examples/KG/*`
file changed; frozen physics and numerical algorithms were not altered.

The six prepared histories are ready for a separate execution-authorization decision. There is no
unresolved CPU preparation failure. Actual GPU dispatch, readback and numerical evolution of these
new segments remain unexecuted. See RUN_YOURSELF.md for read-only commands and the explicitly
unauthorized eventual execution command. Scientific review after execution must use the 500k
partitions plus 1M/2M/4M/8M sensitivity, retain each original parent family and prior segment, and
resolve the specific held modes before considering any qualified acceptance.
