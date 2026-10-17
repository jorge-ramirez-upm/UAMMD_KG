# Execution identities, authorization and step accounting

Starting source SHA: `e85441dec103659ced660933e5d8df410b92c353`.
Launch source SHA: `dd83add6eab03c795fc5343764af23410ebdc736`.
Preserved native build source SHA: `f086be92f42ca49e3a394b6e522e0c2da27c40a1`.
Build directory: `examples/KG_Assoc/kg_assoc_100m/builds/readback_rounding_cpu_20261016_v2`.
Manifest SHA256: `c9ea28fa53e713460e00ad021285d1bd2843dd537245d38bd9efd97e09ce6be9`.
Compiler: NVCC 12.8 / GCC 11.2, production -O3 single-precision build.
All original executable hashes and build logs remain unchanged. No included native
file changed; the established checker authenticates the administrative-only source
transition without rebuilding or replacing historical binaries.

| Executable | SHA256 |
|---|---|
| kg_assoc_candidates_test | `5209be4ec14f549c8ccd9f2dc8bbfac20905077b26940372f668fd7167357111` |
| kg_assoc_stars | `c4317aaed224f3c49d1ef65a40b336e71cc5800e7c3f5fd2ff5a50ad9a6ebfc8` |
| kg_assoc_stars_candidate_smoke | `a44da467cb470a16e768a0a1633e689fa41570ff3e6ba6dfdedcbf1be1421ef4` |

New dataset work: `aggregate/e2/ea_transfer_remaining_smoke_20261017_v1`.
New bank attempts share `banks/e2_attempts/F04_N010_RP080_EE08/` and use
`derived_F04_N010_RP080_EE08_EA{04,06,08,10}_remaining_smoke_20261017_v1`.
All selected starts are exact original parents at 8,000,000, not smoke endpoints.
All selected endpoints are 8,010,000; branch physical duration is 100. The single
historical r001 record retains its distinct `single_r001_gpu_diagnostic_20261016_v1`
attempt, source SHA 83910377c98049170aacd4bd42dfef434dd6e44e and seeds.
It contributes zero new execution steps.

The existing derived planner produced four full three-entry plans and twelve
host-only initialization/effective-seed probes. Only eleven entries had approval.
The new Ea4 r001 directory remains empty. Scoped approvals bind the immutable
plan hash, selector_scope=Ea_transfer_remaining_smoke_v1, full system ID, exact
sorted replica subset, maximum_additional_MD_steps_per_history=10000, and selected
aggregate maximum_additional_MD_steps=20000 or 30000. The scope is validated
before launch and before each started history. Omitting the selector rejects these
approvals; simultaneous legacy/new selectors and unauthorized identities reject.

| Branch | Selected replicas | Plan SHA256 | Approval SHA256 |
|---|---|---|---|
| F04_N010_RP080_EE08_EA04 | [2, 3] | `e080866731b67724b5db582d867152065edb8d8ebb45edc3b0158e166378a0cb` | `6a8ba9a6992f7fe5877a9ef0148b98eb7e15262d9a17ad32279b2e605fbef17f` |
| F04_N010_RP080_EE08_EA06 | [1, 2, 3] | `325e990e437f2c286a58a9c4b2c14e0d7ba9669b5ebeac336e51a15f22d044bd` | `b829de8be2cf4a1cedecb685ef0a2179ace9fe132449a23751f45b1f6b8b332b` |
| F04_N010_RP080_EE08_EA08 | [1, 2, 3] | `067b6e2716ac2f8af6d32ea2431a9f112dd73a43f3143f6dd9e7f5a2d8d78484` | `d0f4cbfd8c682410926adc399efbcf20d08d85b6b6a97f1d83b34fc9ca009948` |
| F04_N010_RP080_EE08_EA10 | [1, 2, 3] | `87ea9f4ce3eb9b3cc1419f10f0135bb44aab5a7059435941b1789d612dea5e1e` | `a5e5b72a1113b7bac1e75dff6ffa3c7fb4967aa8939f56e382b5860d85f7cb92` |

The controlled driver first authenticates all four plans, the clean committed
source, unchanged build, empty output paths and exact 110,000-step total cap.
It calls the established launcher sequentially for these explicit subsets. Any
exception aborts the outer loop and preserves a stop record without retry or
subsequent launch. Native and offline validators must both pass before a per-history
complete receipt is written. The driver records completion only after receipts
validate. This campaign reached ALL_ELEVEN_PASS; no stop or mismatch file exists.
CAMPAIGN_RESULT.log records 110,000 new steps. The old historical 10,000 steps
produce 120,000 combined-evidence steps and 1,200 comparisons, with 1,100 new.

The reference acceptance SHA256 is
`525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22`.
Each parent prefix is `banks/e2_extensions/C1_periodic_recovery_v1/rNNN/state`.
The qualification is carried verbatim in each plan, not replaced by the smoke.

| Family | Restart SHA256 | Sidecar SHA256 | Old chemistry seed | Initial creations / breaks |
|---|---|---|---:|---|
| r001 | `09e1a9f5329a2be06e28112c5bc53e399f54c7aba74369684f12968f68d6b21b` | `9eb4e566d96f0080d9a03677e5d23d231ce389193c71a57f68c58f22035e9ecc` | 22001 | 119665 / 117882 |
| r002 | `ae1599f3d2ffcfd333058b2867bbc7ba897b7dccd84e8b2e7a2996aaa6df3c5b` | `7fd18a27d4d989881397b33b94ffe92de21a05c1e318f8236586b737ee697674` | 22002 | 120242 / 118455 |
| r003 | `10a7885b6e704258dee322e4c310f26bfe921b586e769a477600d515ef888e2a` | `8a260fd5a6e5b3408ba71e10ccb2e47437cf61691036e5c82fcf1c9ac058427c` | 22003 | 119059 / 117256 |

New immutable policy:
`banks/e2_seed_reservations/ea_transfer_remaining_smoke_20261017_v1.json`.
Policy SHA256: `88bbece88d3d33a2784fe6417731fef944a683c5526a76afb82e60fec71fb28f`.
Distinct seeds are an operational stream policy, not proof of PRNG independence.
All requested chemical/MD IDs and effective MD streams are fresh, noncolliding
against prior plans, sidecars, state headers and every reservation set. The twelve
rows satisfy the existing schema; the new control r001 row is reserved bookkeeping
only and has no execution authority. Retire the entire set; never reclaim that row.
No seed from either failed campaign or the prior completed diagnostic was reused.

| Ea | Replica | Provenance | Chemistry seed | Requested MD seed | Effective MD seed | Readback SHA256 |
|---|---|---|---:|---:|---:|---|
| 4 | r001 | existing_Ea4_r001 | 820401 | 830401 | 106569476 | `b55c2c5bea29a2980b1bd91407deebfd07028d07060c69cfba48fecb6b8233ee` |
| 4 | r002 | new_remaining_smoke | 920402 | 930402 | 934681700 | `2324f62fe1b46a58f608c5044bfce7fb0d49412d59212b6a9a765e9e1282857c` |
| 4 | r003 | new_remaining_smoke | 920403 | 930403 | 943082596 | `4f35ef9e8de664a760903482db7b294a5bc0d6e6cb73f3495208c2162d6234e9` |
| 6 | r001 | new_remaining_smoke | 920601 | 930601 | 492096596 | `c97c3edc23edf21dea37fe8df72ae014126b8a80954d27719c41238085fd25fc` |
| 6 | r002 | new_remaining_smoke | 920602 | 930602 | 466893908 | `454d507f835af4476c3d84bc2b22efc15a273771e8865eeed0623748c892f0ca` |
| 6 | r003 | new_remaining_smoke | 920603 | 930603 | 475294804 | `35d34a66d0281bd7dc3133bbb09b5bb5da5a184fb1f22c00657dc217b849c6a5` |
| 8 | r001 | new_remaining_smoke | 920801 | 930801 | 1636906630 | `c8a05bbfaf4d30501c722c87cb941389f2992c1826aaa722dd7f37208a873991` |
| 8 | r002 | new_remaining_smoke | 920802 | 930802 | 1611703942 | `28ae9d11272d13c7240537eb5a47935714e5c3804f491c83aa97a57e978c9fe3` |
| 8 | r003 | new_remaining_smoke | 920803 | 930803 | 1620104838 | `6d45814f95213de475d6021d72cae5014e440863505c8100104b374d03c49d56` |
| 10 | r001 | new_remaining_smoke | 921001 | 931001 | 3337559126 | `10a515dc2a526e3dc41e29bde58d5d3e37276946d70563c6202efacb4c3a8f45` |
| 10 | r002 | new_remaining_smoke | 921002 | 931002 | 3312356438 | `9c0fabd50d9794be6c23fafd0021e12d4567040569272f161352c06ee42d32eb` |
| 10 | r003 | new_remaining_smoke | 921003 | 931003 | 3320757334 | `d50376ea9df8d4973611b83df3a6771198d6fe09bfaf9fb51aef8c42428d8a2d` |

The GPU is the authenticated NVIDIA TITAN Xp on host titan; per-history environment
and stdout/stderr are archived. Actual readback compares every position, velocity,
stable ID/type and partner before the first MD step. Runtime counters, reaction
cadence and effective seed are verified from state/event headers, sidecar and logs.
Coordinates are compared under the documented float32/PBC representation; exact
velocity comparison is unchanged. Parent partners are reciprocal, so exact device
partner equality preserves valence one. Molecule labels are host metadata and
cumulative reaction counters are host accounting, not independently copied GPU
properties. Permanent topology is authenticated on input and endpoint; no separate
GPU bond-table dump is claimed.

The production candidate predicate remains real-first subtraction, double
nearbyint image reduction and strict rsq < 1.5625. The independent oracle is
host-side and actually executes on synchronized GPU-evolved positions each sweep.
Its source/search arithmetic, reaction probabilities, force laws, loader, integrator
and all frozen physics are unchanged. Only Ea and the explicitly approved fresh
streams differ from their parents; Ee=8, T=1, nu0=20, dt=.01, Nevery=100,
r_assoc=1.25, damping=2, K=30, R0=1.5 and the original box stay fixed.

HISTORIES.csv and RESULTS.log contain exact parent, plan, approval, build, source,
seed and per-output identities, including complete-receipt hashes. PLAN_EAxx.log
and APPROVAL_EAxx.log copy original metadata bytes. All large raw particle files
remain at their original ignored dataset locations, hash-bound by ARTIFACTS.sha256.
AUTHORIZATION.log records the explicit user instruction; reviewer fields record
that authority, not an independently provided external scientific signature.
No scientific acceptance, registry publication or production authority is implied.
