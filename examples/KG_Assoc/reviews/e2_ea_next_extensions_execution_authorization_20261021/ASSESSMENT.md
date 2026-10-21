# Execution authorization: Ea8 48M and Ea10 88M

Starting local and remote `KremerGrest` HEAD:
`4c5e6b5b4e9f14e7c379251d4e81331c15a2b3fb`; starting tree clean.
Review date: 2026-10-21. **Authorization publication only; zero assistant GPU
launches and zero new MD steps.** Both systems remain scientifically held.

## Exact authorization

Six new immutable execution approvals and six new immutable source authorizations
are published for `manual_ea_extensions_48m_88m_v1`. The existing plans,
preparation-only approvals, reservations and immutable state were not edited or
recreated. The six original output directories remain empty.

| System | Replicas | Absolute interval | Maximum additional steps/history | Completed budget |
|---|---|---|---:|---:|
| F04_N010_RP080_EE08_EA08 | r001--r003 | 40M--48M | 8,000,000 | 24,000,000 |
| F04_N010_RP080_EE08_EA10 | r001--r003 | 56M--88M | 32,000,000 | 96,000,000 |

Total completed-trajectory cap: **120,000,000 MD steps**. Interruption overhead
must be recorded separately. A replacement requires a new plan-bound execution
approval; these six records do not authorize another attempt or a further extension.

The two existing attempt containers under
`kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE08/` are:

- `extension_F04_N010_RP080_EE08_EA08_next_cfb25731e8b442f0b2019eb0b6699cb7`,
  plan SHA256 `52fb04671910f2cc63ac71fce4958068f6e6ee05c2c0c4828b1477ea7fffd3bb`.
- `extension_F04_N010_RP080_EE08_EA10_next_85928c3ef15c4e06bab10493394a7e25`,
  plan SHA256 `827db432d0abc3f660a16bd6746c9089c47b2daeaf39a73ec5a75906985fae06`.

Each approval is `approval_rNNN_execution.json`, accompanied by
`approval_rNNN_execution_sources.json`. APPROVALS.log gives all absolute paths,
preparation/plan hashes, execution/source hashes, caps and seeds. HISTORIES.csv
joins these with all exact parent restart/sidecar/receipt identities, branch IDs,
inherited counters, reservation identities and output prefixes. APPROVALS.tar.gz
contains byte-exact copies of the twelve newly published records;
APPROVAL_BINDINGS.sha256 pins their original files. No historical record is replaced.

Every execution approval binds the exact original preparation approval, system,
single replica, plan, start/end, per-history step cap, executable hashes, build
manifest, parent hashes and explicit user authorization evidence. Preparation
approvals retain `GPU_execution_authorized=false`; the separate execution approvals
set it true. The immutable preparation state also retains its original false flag.
This does not prevent execution: the existing runner explicitly selects the new
execution approval and source authorization when execution is requested.

## Parent, seed and native authentication

The existing preparation's strict reconstruction authenticates all six reviewed
40M/56M parents, their complete source/build/approval ancestry, accepted events,
oracle evidence, completion receipts, restart/sidecar hashes and inherited counters.
This milestone authenticates existing numerical evidence; it does not claim new
GPU readback or new trajectory replay. No new streams were allocated.

Ea8 r001 retains its authoritative `recovered_complete` provenance and recovery
record SHA256 `91a4fa743735a515353d592213d0ee67cf9e2208ca31dc29cfda4b002aaa5091`.
Its original failure SHA256 remains
`14772d19744e253097b4376195210f9591eb6c85df0a012b0ad25f60c46b017c`.
No ordinary complete receipt is fabricated for this parent. Invalid recovery lineage
is rejected by the same tested planner.

Inherited chemical seeds remain 1220801--1220803 (Ea8) and 1321001--1321003 (Ea10).
Prepared requested MD seeds remain 1331016--1331021; their six effective values,
freshness reservations and exact inherited counters are in HISTORIES.csv. The
existing 500k diagnostic partitions remain 16 windows/history for Ea8 and 64 for
Ea10. Fresh GJ noise means non-bitwise segment continuation; dynamical origins
must not cross the 40M/56M boundary.

The unchanged optimized build is
`kg_assoc_100m/builds/ea_extensions_48m_88m_20261021_v1`, NVCC 12.8.93 / GCC 11.2.0,
`-O3`, original source/build commit `64070a327d320ac2fb6984adbc002036e396721d`.
Build-manifest SHA256:
`70adcf286b89ba50fb2d7275b7d2e7d0044c503cef86ab828eaf4d71b990173b`.

| Executable | SHA256 |
|---|---|
| kg_assoc_stars_candidate_smoke (selected for all six) | `6331c034d8ddb494be616770f2bcc56f5a5fb644f5cb30838e593d259eaf451d` |
| kg_assoc_stars | `2ea4b95ca045b40d61b749f8004d8f9a31178a3dc96ad1e414e57b06d150d0b7` |
| kg_assoc_candidates_test | `70280144fcd484660ffe74e442b63e20faf830d7b6bf4b81857f8d68c6ec1ab3` |

No executable rebuild or native/production administrative source change is needed.
The authenticated build gate checks the corrected pre-MD dispatcher and runs its
CPU-only compiled spy: `INITIAL_READBACK_CALL_PATH_V2 CPU_ONLY cases=4 fail_stop=3`.
This proves the compiled call-path contract, not that a new GPU readback occurred.
Each future completed trajectory must supply genuine exact device evidence.

## Same source identity before and after native PASS

All six source authorizations permit **no overrides**: `source_sha256_overrides={}`.
The exact 665-entry prepared source map equals `e2.sources()`. Canonical JSON
(sorted keys, separators comma/colon) map SHA256:
`c1fc5064d4725855179eb9ed3119b9b2a5e94773d50cbe109701637a40043762`.
Plan Git ancestry remains mandatory. Adding this review does not change any mapped
source. No future administrative or physics hash is broadly whitelisted.

The runner's preparation and execution authentication use the exact same map;
the shared launcher passes that map to initial, immediate pre-launch and both
post-native-PASS live-source checks. It loads the source record only once, hashes
its exact bytes, binds that hash in started.json, and checks it again before launch
and after native PASS. Each source record also binds the exact execution-approval
hash; the new committed inventory independently pins all twelve records.

Temporary mocked-native regressions observe every live-code call and require
identical authorized maps, reject source-record mutation after native PASS, and
reject tampered approval/plan hashes, wrong replicas/systems/caps, missing/extra
source files, physics changes and nonancestor commits. Actual real-plan read-only
authentication passes for all six at descendant documentation commits. Final
clean-tree authentication is repeated after the final commit; the resulting full
Git SHA and local/remote agreement are reported in the milestone handoff.

Device readback, strict candidate oracle, chemistry continuity/event/counter replay,
numerical geometry checks and final restart/sidecar validation remain mandatory.
The independent validator forces the full extension validation path even though
the plan is an ordinary extension rather than a short smoke. The runner independently
replays successful receipts before skipping completions. Native PASS followed by
an administrative error is held and cannot become an automatic MD retry. Genuine
partial work is preserved and its fresh CPU-only replacement requires separate
approval. No synthetic evidence was written in any real output directory.

## CPU checks and preservation

| Check | Result |
|---|---|
| New real authorization/source checks + next-extension + lifecycle CPU suite | 29 passed |
| Established shared E2 regression suite | 189 passed |
| Current-policy transfer/extension/readback compatibility suite | 53 cases: 52 passed, 1 historical pre-execution skip |
| Read-only execution preflight and status | Both passed; all six original histories `prepared` |
| Historical protection | All 3,626 bindings unchanged |
| Existing preparation/source/build protection | All 689 bindings unchanged |
| Formal scientific acceptances and protected payloads | All 13 unchanged and authenticated |

Thus the selected current-policy suites contain **270 passing tests and one
historical skip**. All assistant jobs used an outer timeout of 600 s or less;
the longest test suite took 88.148 s. AUTHORIZATION_TESTS.log, E2_REGRESSION.log
and COMPATIBILITY_TESTS.log retain the actual outcomes. Logs containing native-PASS
or “ALL SIX ... VALIDATED” messages inside unit tests refer only to temporary
mocked/synthetic fixtures; the six real directories remain empty.

The first broad compatibility invocation also ran two obsolete historical tests
that expected `classify(..., recover=True)` to promote a native-PASS result through
generic recovery. Both failed because the already established runner requires
explicit `--recover-ea8-r001`; it correctly rejects generic promotion before calling
the validator. HISTORICAL_COMPATIBILITY.log preserves that original result
(53 cases: 50 passed, one skipped, two errors). The affected historical test and
runner bytes are unchanged from the starting SHA. COMPATIBILITY_DRIVER.txt
preserves those tests and replaces their superseded expectations in the selected
suite with two stricter negative regressions: missing evidence and an available
validator both remain held, with no output mutation, complete receipt or MD launch.
This is not a relaxed gate or a production recovery change. Existing ResourceWarnings
from the historical sidecar reader are retained in the original compatibility log.
There is no unresolved failure in the authorized six-history path.

PREFLIGHT_DRIVER.txt is read-only and audits the new execution records, archive
and inventories before authenticating all six through the real runner. It checks
the exact source map and Git ancestry at its invocation's HEAD. Its `--check` and
`--status` modes were both exercised. The older historical preparation verifier's
“no execution records yet” assertion is intentionally no longer applicable; it
was run successfully before publication and remains preserved unchanged.

INTEGRITY.sha256 binds this dossier's reviewed artifacts, including the authorization
inventory, archive, full tables, reproducible drivers and CPU evidence. The existing
preparation's INTEGRITY.sha256 binds its earlier review. The new records are archived
as metadata only; no large trajectory is copied or changed. No `src/*`,
`examples/KG/*`, physical kernel, numerical validator, RNG implementation or
production launcher source was modified. All changes are confined to this new
review dossier plus the twelve separately authorized immutable dataset records.

## User handoff and scientific boundary

Use RUN_YOURSELF.md for exact read-only preflight/status and controlled user-run
execution commands on `titan`. The user runs the original runner's `--execute`;
the assistant did not invoke it against the real campaign. Preparation publication
is not repeated, and no output folder must be deleted or overwritten.

Both systems remain on scientific hold. After execution, review all histories with
the existing 500k windows and coarsened sensitivity, preserve paired original Ea4
families and distinct GJ segments, and resolve the specified replica-specific modes.
Numerical completion alone does not confer scientific acceptance, equilibrium
invariance, slow-mode decorrelation, another extension, registry authority or production.
