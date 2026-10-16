# Exact execution and provenance

Launch source SHA: `83910377c98049170aacd4bd42dfef434dd6e44e`.
Native build source SHA: `f086be92f42ca49e3a394b6e522e0c2da27c40a1`.
Build: `examples/KG_Assoc/kg_assoc_100m/builds/readback_rounding_cpu_20261016_v2`.
Build manifest SHA256: `c9ea28fa53e713460e00ad021285d1bd2843dd537245d38bd9efd97e09ce6be9`.
GPU: NVIDIA TITAN Xp, GPU-8170bfc5-0914-1b23-e2b6-fdb85300a2b6; driver 580.178.04; host titan.
The native MD loop reports wall_seconds=7.83516. Source/build/plan and per-file
SHA256 maps are retained in PLAN.log, COMPLETION.log and EXECUTION_METADATA.log.
PREFLIGHT.log is the initial pre-selector authentication record; PLAN.log binds
the final authorized selector source and prepared scope.

| History | Start | End | Additional MD | Outcome |
|---|---:|---:|---:|---|
| Ea4 reseeded control r001 | 8000000 | 8010000 | 10000 | Validated single endpoint |
| r002/r003 | — | — | 0 executed | Empty directories; no activity observations |
| Ea6/Ea8/Ea10 | — | — | 0 executed | No new branch attempt or execution |

The unsupported zero-step path was diagnosed from native/planner checks. No normal
executable semantics were changed to permit it. Preparation used the existing
derived planner, then the explicitly authorized selector, with one plan-bound
e2_derived_smoke approval restricted to replica 1 and exactly 10000 steps.
The unchanged triplet verifier is not claimed passed; only r001 has complete.json.

The parent acceptance SHA256 is
`525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22`.
Parent prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_extensions/C1_periodic_recovery_v1/r001/state`.
Snapshot SHA256: `09e1a9f5329a2be06e28112c5bc53e399f54c7aba74369684f12968f68d6b21b`.
Sidecar SHA256: `9eb4e566d96f0080d9a03677e5d23d231ce389193c71a57f68c58f22035e9ecc`.
Its complete qualified provenance and source-file hashes are embedded in the plan.

New chemical seed: 820401 (parent 22001). Requested MD seed: 830401; effective
MD seed: 106569476, host-queried and runtime-confirmed. The immutable new policy is
`banks/e2_seed_reservations/ea4_r001_gpu_diagnostic_20261016_v1.json` (SEED_RESERVATIONS.log).
All 24 chemical/requested-MD IDs and twelve effective MD values are mutually
distinct and checked against existing plans/sidecars/state headers and all older
reservation sets. Only r001 is authorized; the other format-required rows are
reservation bookkeeping. Retire the entire set; never recycle its unused rows.

Physics stays Ea=4, Ee=8, T=1, nu0=20, Nevery=100, dt=.01, r_assoc=1.25, damping=2,
K=30, R0=1.5, original 37.145 box lengths and topology. IDs, types, unit masses,
40,000 permanent bonds and all reciprocal initial chemistry pairs are inherited.
The corrected cutoff contract and repaired expected-velocity materialization
remain unchanged. All physical evolution uses the existing authenticated binary.

| Identity | SHA256 |
|---|---|
| Plan | `beb204468c20f8089079ff5c8f6a4334cb4523867c960e8d663a6101fca1f4da` |
| Scoped approval | `0df4f28fdb05f8e08e97594e838061f8d81a25febd8fdefb167e767413604859` |
| Complete receipt | `fe8301255ae36cb4e0296a8f6c377565bb369428465d4a1d4ef318eb6bc395b1` |
| Actual initial device readback | `b55c2c5bea29a2980b1bd91407deebfd07028d07060c69cfba48fecb6b8233ee` |
| kg_assoc_candidates_test | `5209be4ec14f549c8ccd9f2dc8bbfac20905077b26940372f668fd7167357111` |
| kg_assoc_stars | `c4317aaed224f3c49d1ef65a40b336e71cc5800e7c3f5fd2ff5a50ad9a6ebfc8` |
| kg_assoc_stars_candidate_smoke | `a44da467cb470a16e768a0a1633e689fa41570ff3e6ba6dfdedcbf1be1421ef4` |
| Endpoint/output .restart.lammpsdat | `8b731c5c7bb3efeba5b8a6bf9954def8ba6e41aa846841e7ab71b8368d6af6ce` |
| Endpoint/output .assoc_restart | `8b0279dfb6c2b1961e94ad2ef8469344502eb9724bfe0f2f6020083be0633112` |
| Endpoint/output .events | `42eec6865684c64e01f39eeebd28587bc2bfc17f349b2bb89f396060190c4d2f` |
| Endpoint/output .candidate_validation.tsv | `c1ea854e1ff7e73619db2a495d20aedf5cd15111d74b0af7f8066af5129d821d` |
| Endpoint/output .numerics.tsv | `338a0d8d13c35726bacb830a1b8ad87bae8118d11f09690f41ee143b4bc21fe5` |

The readback was written and checked before the first forwardTime. The unchanged
official Python reader independently validates every stored expected/actual value
against the parent float32/PBC representation and authenticates the embedded build.
All candidate comparisons are host all-pairs checks on live GPU-evolved positions,
with no tolerance enlargement, candidate mutation or production predicate change.
There was no mismatch file, failed retry, alternate seed, second GPU launch or
post-smoke continuation. All outputs and completion receipts remain at the original
ignored dataset paths and are bound by ARTIFACTS.sha256. AUTHORIZATION.log records
the user instruction and follow-up selector authorization; reviewer text is an
audit record of that instruction, not an independently supplied external signature.
