# E2 campaign inventory and next priorities — 14 October 2026

**Read-only advisory snapshot. No simulation, acceptance registration, registry selection or production authorization is requested or performed.**

Starting local and remote `KremerGrest` both verified at `e90d40d79cba3fd637f1301538a855b7021e04ff`. The frozen manifest exactly matches the code-expanded matrix: **23 conditions = 15 associating + 8 NONASSOC; 3 histories each; 8 geometries / 24 shared active E1 states**.

**Seven systems have qualified formal E2 acceptance; 16 do not. The 16 comprise five fresh associating banks, three higher-Ea C1 variants, and eight controls for which chemical E2 is not applicable. This is not a backlog of 16 equilibration simulations.** No active registry exists, and the catalog reports absent production authorization and blocked associating production eligibility for every system.

## Verification scope and source of truth

Checked the frozen manifest/protocol against the matrix, all 24 E1 snapshots via `original_e1()` (inventory hashes, active selections, completion/diagnostics and geometry/numerics), and all seven acceptance records via read-only `exclusive_validate()` (review/plan/completion bindings, every accepted payload hash, restart chemistry/step/seed and final geometry/association consistency). Recorded historical numerical/event/network/conformation validation is retained; full trajectory/event replay and historical executable reauthentication were **not** repeated for this inventory. No large production trajectories were scanned. Earlier dossiers document the scope of fresh executable authentication and unavailable historical bytes.

The existing catalog is a metadata view, not an acceptance authority. Its generic C1 coverage of multiple Ea conditions must not be read as target-Ea equilibration or permission. Files available here were inspected; no remote GPU process/liveness inspection was performed, so absence of a local attempt does not prove absence of an unimported host run.

| Frozen source | SHA256 |
|---|---|
| [manifest.json](../kg_assoc_100m/manifest.json) | `1a558720023e3475cdbf960456c56a5f64c9e8a3cc36f86f971aa01487ec1d00` |
| [campaign_protocol.json](../kg_assoc_100m/campaign_protocol.json) | `cafeae72732d9c0f7d6f2dd937dd603825622d468a7a9f0a8be3f3942e739592` |
| [campaign_protocol.json](../campaign/campaign_protocol.json) | `b459e2faf02283f5f5396d868a7726de115cc85b54dab77b9ea2bc6a09c14671` |
| [e2_remaining_inventory_20261011.json](../campaign/e2_remaining_inventory_20261011.json) | `e785248cc3dfdd95c1c0a94fdb5ce3c98f5811f458a5d894667379b939cd9737` |

## All 23 systems

Common physical settings: 1000 stars, 3 independent histories, T=1, dt=0.01, total bead density 0.85. Associating preparation uses Ea=4, nu0=20, Nevery=100, r_assoc=1.25, K=30, R0=1.5 and damping=2. Higher-Ea rows show the **target** Ea, not a new preparation allocation. NONASSOC disables temporary association; Ee/Ea are not applicable. Frozen 100M production targets are unchanged and unexecuted by this report.

Every row has **E1 3/3 authenticated** in its geometry; geometry/E1 paths are mapped below. `A#` identifies the exact authenticated three-state acceptance set below. All seven formal decisions permit only `production_initial_state` for their named Ea=4 condition; active selection is missing. Controls have no chemical E2 requirement, and no geometry-level E1 `validation.json` with formal accepted status was found for their production gate.

| System | f / N / rho_p | Ee / target Ea | Total beads | E1 | E2 execution observed here | Formal E2 / initialization | Unresolved issue |
|---|---|---|---:|---|---|---|---|
| `F03_N010_RP080_EE08_EA04` | 3 / 10 / 0.8 | 8 / 4 | 32938 | 3/3 | 3 × (6M + 2M extension), absolute 8M | Qualified A1; 8M | Recovered satellites; residual peripheral/shape uncertainty; 6M reseed. |
| `F03_N010_RP080_NONASSOC` | 3 / 10 / 0.8 | — / — | 32938 | 3/3 | Not applicable | None (E2 N/A); E1 states only | Separate formal E1 readiness/authorization remains unresolved; no chemical run needed. |
| `F04_N010_RP020_EE08_EA04` | 4 / 10 / 0.2 | 8 / 4 | 174250 | 3/3 | 3 × (2M + 2M + 2M), absolute 6M | Qualified A2; 6M | Recovered interrupted first segment; 4M hold reviewed at 6M; early population shift, slow L2. |
| `F04_N010_RP020_NONASSOC` | 4 / 10 / 0.2 | — / — | 174250 | 3/3 | Not applicable | None (E2 N/A); E1 states only | Separate formal E1 readiness/authorization remains unresolved; no chemical run needed. |
| `F04_N010_RP040_EE08_EA04` | 4 / 10 / 0.4 | 8 / 4 | 87125 | 3/3 | No ordinary E2 or condition-specific smoke plan found | None; authenticated E1 starts | Stationarity/turnover unknown; matched numerical smoke needed before long E2. |
| `F04_N010_RP040_NONASSOC` | 4 / 10 / 0.4 | — / — | 87125 | 3/3 | Not applicable | None (E2 N/A); E1 states only | Separate formal E1 readiness/authorization remains unresolved; no chemical run needed. |
| `F04_N010_RP060_EE08_EA04` | 4 / 10 / 0.6 | 8 / 4 | 58083 | 3/3 | No ordinary E2 or condition-specific smoke plan found | None; authenticated E1 starts | Stationarity/turnover unknown; matched numerical smoke needed before long E2. |
| `F04_N010_RP060_NONASSOC` | 4 / 10 / 0.6 | — / — | 58083 | 3/3 | Not applicable | None (E2 N/A); E1 states only | Separate formal E1 readiness/authorization remains unresolved; no chemical run needed. |
| `F04_N010_RP080_EE04_EA04` | 4 / 10 / 0.8 | 4 / 4 | 43563 | 3/3 | 3 × 2M validated receipts | Qualified A3; 2M | Qualified weak-bond reference; full topology decorrelation unproven. |
| `F04_N010_RP080_EE06_EA04` | 4 / 10 / 0.8 | 6 / 4 | 43563 | 3/3 | No ordinary E2 or condition-specific smoke plan found | None; authenticated E1 starts | Stationarity/turnover unknown; matched numerical smoke needed before long E2. |
| `F04_N010_RP080_EE08_EA04` | 4 / 10 / 0.8 | 8 / 4 | 43563 | 3/3 | 3 corrected 6–8M recoveries; absolute 8M | Qualified A4; 8M | Corrected C1 only; defective 6M ineligible; historical build limitations. |
| `F04_N010_RP080_EE08_EA06` | 4 / 10 / 0.8 | 8 / 6 | 43563 | 3/3 | No own long E2; corrected Ea4 donor | None; donor A4 not permitted for target | Explicit switch exists; separate target validation/qualification and acceptance required. |
| `F04_N010_RP080_EE08_EA08` | 4 / 10 / 0.8 | 8 / 8 | 43563 | 3/3 | No own long E2; corrected Ea4 donor; 10k switch smoke receipts | None; donor A4 not permitted for target | Explicit switch exists; separate target validation/qualification and acceptance required. |
| `F04_N010_RP080_EE08_EA10` | 4 / 10 / 0.8 | 8 / 10 | 43563 | 3/3 | No own long E2; corrected Ea4 donor | None; donor A4 not permitted for target | Explicit switch exists; separate target validation/qualification and acceptance required. |
| `F04_N010_RP080_EE10_EA04` | 4 / 10 / 0.8 | 10 / 4 | 43563 | 3/3 | No ordinary E2 or condition-specific smoke plan found | None; authenticated E1 starts | Stationarity/turnover unknown; matched numerical smoke needed before long E2. |
| `F04_N010_RP080_EE12_EA04` | 4 / 10 / 0.8 | 12 / 4 | 43563 | 3/3 | No ordinary E2 or condition-specific smoke plan found | None; authenticated E1 starts | Stationarity/turnover unknown; matched numerical smoke needed before long E2. |
| `F04_N010_RP080_NONASSOC` | 4 / 10 / 0.8 | — / — | 43563 | 3/3 | Not applicable | None (E2 N/A); E1 states only | Separate formal E1 readiness/authorization remains unresolved; no chemical run needed. |
| `F04_N020_RP080_EE08_EA04` | 4 / 20 / 0.8 | 8 / 4 | 86063 | 3/3 | 3 × 6M validated receipts | Qualified A5; 6M | Limited shape/intra/topology sampling; late peripheral and intra redistribution. |
| `F04_N020_RP080_NONASSOC` | 4 / 20 / 0.8 | — / — | 86063 | 3/3 | Not applicable | None (E2 N/A); E1 states only | Separate formal E1 readiness/authorization remains unresolved; no chemical run needed. |
| `F04_N040_RP080_EE08_EA04` | 4 / 40 / 0.8 | 8 / 4 | 171063 | 3/3 | 3 × 8M validated receipts | Qualified A6; 8M | Residual shifted partition/degree effects; rare satellites +~21%; limited slow sampling. |
| `F04_N040_RP080_NONASSOC` | 4 / 40 / 0.8 | — / — | 171063 | 3/3 | Not applicable | None (E2 N/A); E1 states only | Separate formal E1 readiness/authorization remains unresolved; no chemical run needed. |
| `F06_N010_RP080_EE08_EA04` | 6 / 10 / 0.8 | 8 / 4 | 64813 | 3/3 | 3 × 6M validated receipts | Qualified A7; 6M | Small shared shape, partition and neighbor-loss changes; topology mixing unproven. |
| `F06_N010_RP080_NONASSOC` | 6 / 10 / 0.8 | — / — | 64813 | 3/3 | Not applicable | None (E2 N/A); E1 states only | Separate formal E1 readiness/authorization remains unresolved; no chemical run needed. |

The sixteen rows marked **None** are exactly the remaining-system inventory: five fresh Ea4 rows, three Ea6/8/10 rows and eight NONASSOC rows. The latter eight are counted for completeness, not labeled scientific E2 failures.

## E1 mapping and exact accepted initialization identities

Paths below are relative to `examples/KG_Assoc/kg_assoc_100m/`. `{r001,r002,r003}` denotes exactly the three individually hashed histories, not arbitrary directory discovery. All same-geometry conditions share their E1 trio; comparisons branching from that same trio should retain history pairing, not count conditions as extra independent replicas. E1 seeds are 12001/12002/12003. Frozen hashes and completion identities are in the linked inventory.

| Geometry shared by table rows | Polymer / solvent / total beads | Active E1 prefixes |
|---|---:|---|
| `F03_N010_RP080` | 31000 / 1938 / 32938 | `banks/e1/F03_N010_RP080/{r001,r002,r003}/state.e1.lammpsdat` |
| `F04_N010_RP020` | 41000 / 133250 / 174250 | `banks/e1/F04_N010_RP020/{r001,r002,r003}/state.e1.lammpsdat` |
| `F04_N010_RP040` | 41000 / 46125 / 87125 | `banks/e1/F04_N010_RP040/{r001,r002,r003}/state.e1.lammpsdat` |
| `F04_N010_RP060` | 41000 / 17083 / 58083 | `banks/e1/F04_N010_RP060/{r001,r003}/state.e1.lammpsdat; r002 = banks/e1_retries/F04_N010_RP060/r002/attempt001/state.e1.lammpsdat` |
| `F04_N010_RP080` | 41000 / 2563 / 43563 | `banks/e1/F04_N010_RP080/{r001,r002,r003}/state.e1.lammpsdat` |
| `F04_N020_RP080` | 81000 / 5063 / 86063 | `banks/e1/F04_N020_RP080/{r001,r002,r003}/state.e1.lammpsdat` |
| `F04_N040_RP080` | 161000 / 10063 / 171063 | `banks/e1/F04_N040_RP080/{r001,r002,r003}/state.e1.lammpsdat` |
| `F06_N010_RP080` | 61000 / 3813 / 64813 | `banks/e1/F06_N010_RP080/{r001,r002,r003}/state.e1.lammpsdat` |

RP060/r002 uses only its frozen accepted-for-E2 retry; its failed original is preserved and excluded. E1 numerical readiness is not a formal E1 production acceptance. The [original E1 audit](../kg_assoc_100m/aggregate/e1/audit_20261010T154908Z_v1/REPORT.md) retains weaker N=40 slow-conformation evidence and the timestep-dependent GJF kinetic deficit; serialized velocities must not be silently rescaled. Chemical E2 acceptance does not replace a scientific review of a NONASSOC baseline. Shared E1 geometry does not permit sharing an equilibrated state across different Ee or densities.

| Set / system | Absolute step, each r001/r002/r003 | Exact endpoint prefix group | Immutable acceptance record / SHA256 |
|---|---:|---|---|
| A1 `F03_N010_RP080_EE08_EA04` | 8000000 | `banks/e2_attempts/F03_N010_RP080_EE08/equilibrate_9b51f865c4464eefb210188d802c0c5e/{r001,r002,r003}/state` | [F03_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json](../kg_assoc_100m/banks/e2_acceptance/F03_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json); `3c7633e7b42341af66c34a5b29ed86d0ae8bd2176cb401a7f35920be3d5ec13c` |
| A2 `F04_N010_RP020_EE08_EA04` | 6000000 | `banks/e2_attempts/F04_N010_RP020_EE08/equilibrate_13a6951adf16448cb5365a8b28e28427/{r001,r002,r003}/state` | [F04_N010_RP020_EE08_EA04_6M_qualified_20261013_v1.json](../kg_assoc_100m/banks/e2_acceptance/F04_N010_RP020_EE08_EA04_6M_qualified_20261013_v1.json); `20f7ed7ae7fb3b659b52caa3850d3fad3e3041268f19269007288a49fc6bc0c6` |
| A3 `F04_N010_RP080_EE04_EA04` | 2000000 | `banks/e2_attempts/F04_N010_RP080_EE04/equilibrate_5a06db30dfba406bacb8937f39e14eea/{r001,r002,r003}/state` | [F04_N010_RP080_EE04_EA04_2M_qualified_20261013_v1.json](../kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE04_EA04_2M_qualified_20261013_v1.json); `7f5cd4ba2ace52b0b8a62a54ffe63bebf62c1bf4a6d22bb330df97ce44e8bb6a` |
| A4 `F04_N010_RP080_EE08_EA04` | 8000000 | `banks/e2_extensions/C1_periodic_recovery_v1/{r001,r002,r003}/state` | [F04_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json](../kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE08_EA04_8M_qualified_20261013_v1.json); `525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22` |
| A5 `F04_N020_RP080_EE08_EA04` | 6000000 | `banks/e2_attempts/F04_N020_RP080_EE08/equilibrate_bdfe5dc30d87435899f6d2d21dc99fac/{r001,r002,r003}/state` | [F04_N020_RP080_EE08_EA04_6M_qualified_20261013_v1.json](../kg_assoc_100m/banks/e2_acceptance/F04_N020_RP080_EE08_EA04_6M_qualified_20261013_v1.json); `6ebb95dda283828342f7bd55fe2331e51e2a0477e70234e54e9631fd78bf7422` |
| A6 `F04_N040_RP080_EE08_EA04` | 8000000 | `banks/e2_attempts/F04_N040_RP080_EE08/equilibrate_0a6a37a1e8264ceabbeead5362d8423d/{r001,r002,r003}/state` | [F04_N040_RP080_EE08_EA04_8M_qualified_20261013_v1.json](../kg_assoc_100m/banks/e2_acceptance/F04_N040_RP080_EE08_EA04_8M_qualified_20261013_v1.json); `3d9f77c2c88219039e9abc4ef7e267b1ed71dd9cce17df4e7431f447bf4294f7` |
| A7 `F06_N010_RP080_EE08_EA04` | 6000000 | `banks/e2_attempts/F06_N010_RP080_EE08/equilibrate_2092711490194045aa2036a7e00b4bd0/{r001,r002,r003}/state` | [F06_N010_RP080_EE08_EA04_6M_qualified_20261013_v1.json](../kg_assoc_100m/banks/e2_acceptance/F06_N010_RP080_EE08_EA04_6M_qualified_20261013_v1.json); `81179644b404b3ab5a492ad60bba0d3d23502d0f5d7da4d058552fa9a5e714c0` |

Each linked record contains **individual restart and chemical-sidecar SHA256s**, physics, chemistry seeds, plan and completion hashes. Those bindings were freshly checked here for all 21 initialization states. Older dilute 2M/4M states, original f3 6M states, historical PBC-defective C1 6M states and all smoke endpoints remain unselected/ineligible under these records. A4 is corrected C1, not eight million steps of wholly corrected chemistry: its inherited 0–6M lineage was defective; only the separately preserved 6–8M recovery is corrected.

## Recommended next five fresh E2 conditions

**Proposed review checkpoints, not launch approval, guaranteed equilibration times or extension authorization.** Run the original three E1 histories sequentially for each condition, preserving their identities, frozen chemical seed map and fresh recorded MD seed allocation. Do not substitute accepted Ee=4/8 states as starts for another Ee. The wrapper already supports fresh Ea4 banks and matching capped smokes; none of these five has a condition-specific smoke receipt locally, so authenticated input/build checks and the matched short prerequisite are required before any separately authorized long run.

| Priority | System | Initial MD steps / history (estimate) | Review windows | Scientific purpose and justification |
|---:|---|---:|---|---|
| 1 | `F04_N010_RP080_EE06_EA04` | 4M | 500k checkpoint; joint 1M, 2M late mean and shifted comparisons | Bridge accepted Ee=4 (2M) and Ee=8 (corrected 8M). Isolates energetics at identical f/N/density. Four million is a first checkpoint, not an interpolation theorem; only one post-2M 2M interval exists, so longer comparisons may remain unresolved. |
| 2 | `F04_N010_RP040_EE08_EA04` | 6M | 500k checkpoint; nonoverlapping 1M and paired 2–4M/4–6M | Fill the largest interior concentration gap between accepted rho_p=0.2 and 0.8. The dilute 4M L2 hold lifted only after 6M motivates a direct late 2M comparison, not a universal duration. More solvent costs more per step than the dense reference. |
| 3 | `F04_N010_RP060_EE08_EA04` | 6M | Same 500k / 1M / 2M strategy | Completes density sweep with 0.2/0.4/0.6/0.8 at fixed f/N/Ee/Ea. Lower particle cost than rho_p=0.4; monitor percolation/peripheral redistribution independently of bulk chemistry. Exact retry parent for r002 is essential. |
| 4 | `F04_N010_RP080_EE10_EA04` | 6M | 500k checkpoint; 1M and 2M late comparisons, longer if poorly resolved | Extend the energy sweep beyond Ee=8 before the strongest-binding limit. Stronger bonds can fill quickly while renewing neighbors slowly; turnover, intra/inter partition and L1/L2 matter more than a flat bound fraction. |
| 5 | `F04_N010_RP080_EE12_EA04` | 8M | 500k checkpoint; 1M and 2M comparisons through 6–8M; review longer windows if IATs demand | Complete the five-point Ee sweep and probe the largest topology-memory risk. Eight million is a conservative first budget estimate, not an empirically established mixing time. Review Ee=10 first; revise the proposed allocation before launch if its turnover is much slower. |

For a three-condition commitment, choose priorities 1–3. Priorities 4–5 complete the association-strength sweep afterward; an earlier Ee=12 risk probe is a reasonable alternative if learning the worst-case cost matters more than filling intermediate points. The accepted f=3/4/6 and N=10/20/40 sweeps need no new geometry bank now. Arm/functionality comparisons already vary star/sticker densities at fixed bead density, so they cannot isolate arm length/valence alone. Density comparisons change box/solvent and star/sticker density; Ee comparisons preserve geometry and concentration.

All seven acceptances remain qualified: weak-bond preparation required only 2M in its reviewed case, while dilute/long-arm/functionality preparations needed 6–8M and sometimes a hold/extension. This heterogeneity argues against a uniform 2M or 8M rule. Active turnover is necessary evidence, not proof of structural equilibration. Assess populations, intra/inter, degree moments/distributions, giant/isolation/components/satellites, L1/L2, accepted bond/neighbor exchange and Rg²/terminal R². Retain the early unbound transient. Use the existing IAT and 5/10/20 blocking helpers and paired three-history exploratory uncertainty; zero-containing intervals do not prove stationarity. Any later restart has fresh MD seeds: compare means but do not stitch correlation/residence/stress/transport histories across reseeds. Extensions and formal acceptance require separate decisions.

## Cost: confirmed historical measurements versus extrapolations

Recorded receipts on **NVIDIA TITAN Xp, host titan**: dense Ee=4 2M histories took 541–545 s each; dilute rho_p=0.2 2M extension histories 1183–1187 s; f=3 6M histories 1403–1407 s; f=6 6M 2564–2588 s; N=20 6M 2277–2284 s; N=40 8M 4608–4615 s. These are recorded MD-plus-validation elapsed times, not isolated GPU-kernel benchmarks. Scientific joint-analysis overhead is additional. The old corrected C1 2M recovery receipt is ~592 s/history, a different build/workflow benchmark.

**Planning estimates for all three sequential histories, excluding build and extended scientific-review overhead:** Ee=6 4M ~0.8–1.3 h; rho_p=0.4 6M ~1.8–3 h; rho_p=0.6 6M ~1.3–2.2 h; Ee=10 6M ~1.2–2 h; Ee=12 8M ~1.5–3 h; combined ~6.6–11.5 h on comparable hardware. Ranges extrapolate dense/dilute receipt times and particle counts, not measured new-condition performance or equilibration duration. Different reaction/event burdens and hardware can change them. Longer scientific equilibration may dominate the budget; no automatic extension is budgeted or authorized.

## Higher-Ea variants and controls: separate decisions

`F04_N010_RP080_EE08_EA06`, `..._EA08`, `..._EA10` have authenticated corrected Ea4 donor endpoints A4, but A4 permits **only EA04**. No system-specific formal record or target-Ea long E2 exists here. The explicit parameter-switch implementation is present, and the Ea=8 10k smoke plan/three completion receipts are recorded at `banks/e2_attempts/F04_N010_RP080_EE08/smoke_3d9c9dd29c7f4b4a97357507cb488f0e/`; this is numerical evidence, not an accepted 8.01M initialization bank or demonstrated equilibrium invariance. Ea6/Ea10 lack matching switch smoke plans locally. Legacy C1 smokes and defective 6M banks are not such tests.

The approved chemistry rationale is that the common attempt factor cancels in the fixed-configuration forward/reverse Metropolis ratio; exact coupled-integrator invariance remains a numerical qualification, not a theorem. Recommend reviewing the supported switch/donor transfer and any missing capped validation/permission separately, rather than paying for three new high-Ea equilibration trajectories by default. The current fresh-equilibration CLI explicitly rejects higher-Ea and reference C1 long E2. This report neither broadens A4 nor authorizes switching, acceptance, registry selection or production.

Eight NONASSOC rows need no chemical equilibration; their shared E1 payloads are ready as recorded numerical preparation states. Their independent formal E1 production-readiness mechanism remains unresolved: the required geometry-level accepted `banks/e1/<geometry>/validation.json` records were absent here. Do not call them production-ready solely because snapshots exist.

## Coverage limits and CPU checks

The catalog reports 30 lineage-fork diagnostics (shared E1 histories/continuation and smoke branches are expected possibilities, not 30 demonstrated corruptions) and three outside-scope references in the historical f3 6M dossier pointing to an old `/tmp/UAMMD_KG_f3_review_20261013` worktree. These are retained provenance/navigation limitations; no path is silently rewritten, and the seven endpoint records passed independent authentication. The prepared C1 infrastructure-check placeholder is not a completed recovery. Directory existence, historical completion, smoke success, numerical validity, formal scientific acceptance, registry selection and production authorization remain distinct.

CPU checks performed: frozen manifest/protocol equality; 23/15/8/7/16 accounting; eight geometries and 24 active E1 states; seven immutable acceptance schemas/permissions, plans and all 21 endpoint payload bindings; absence of registry views/selections. **55 CPU tests passed** (`test_catalog`, `test_e2_acceptance`, `test_e2_n40_acceptance`). Markdown accounting checks confirm 23 unique system rows, seven accepted and sixteen unaccepted (eight E2-not-applicable controls); every relative evidence link resolves. Whitespace checks pass. No new analyzer, catalog implementation, frozen file or runtime data is changed; only this derived Markdown snapshot is added. No remote-host liveness or new-condition equilibration time is established by these checks.
