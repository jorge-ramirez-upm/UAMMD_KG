# Remaining corrected-chemistry E2 campaign — proposal for review

Prepared 11 October 2026 on `KremerGrest`, starting HEAD
`c70111a88c2a1084fb8839322ae4ee2a237fed31` (also final HEAD; no commit made).
**No MD, E2 recovery, smoke simulation or production is authorized or launched
by this document.** Only documentation and a frozen inventory are added.

## Evidence and present state

The actual dataset is `examples/KG_Assoc/kg_assoc_100m/`. Its manifest and
protocol match the code-expanded matrix: **15 associating conditions, eight
NONASSOC controls, eight E1 geometries and 12 distinct geometry/Ee E2 banks**.
After C1, there are **11 fresh E2 banks / 33 starting histories**, plus three
remaining Ea variants whose reuse of C1 is conditional. Controls require no E2.
Three histories of each geometry have different state hashes and stochastic
seeds, but share their original external geometry. Conditions branching from
the same E1 histories are paired across conditions, not extra independent
replicas.

Read evidence:

- `aggregate/e1/review_20261010T135200_586153Z/inventory.json`: all 24 active
  E1 histories completed and numerically valid. RP060/r002 resolves to its retry.
- `aggregate/e1/audit_20261010T154908Z_v1/REPORT.md`: states are reasonable E2
  preparation inputs, with weaker slow-mode evidence for N=40. The on-site GJF
  kinetic deficit must not be removed by velocity rescaling. Nonlinear timestep
  accuracy remains a separate scientific question.
- `banks/e2_extensions/C1_periodic_recovery_v1/{plan.json,r00*/status.json}`,
  `aggregate/e2/C1_fresh_md_smoke_v1/`, and
  `aggregate/e2/C1_recovery_review_v1/{summary.json,analysis_config.json}`:
  all three corrected segments validated, ending at absolute E2 step 8M.
  Chemistry seeds 22001–22003 and fresh MD seeds 32001–32003 were retained.
- The user's present review provisionally accepts these **8M** C1 endpoints for
  subsequent production, qualified by slow network-topology relaxation. This
  decision supersedes the earlier pending-execution prose in `C1_E2_RECOVERY.md`
  for this proposal. Automated records still say `review_required`; they have
  not been edited or promoted to accepted banks here.

Last corrected C1 windows `(7.5M,8M]` give bound fractions
0.89636/0.89782/0.89638, intra bonds 92.372/97.274/91.586, L1
41.086/44.226/38.362 and L2 32.528/34.314/33.572. Creation/break counts are
9190/9199, 9062/9073 and 9076/9076 over 5000 physical time units, with continuing
distinct-neighbor gains/losses. However, inferred effective temporal samples
are only 4.3–8.5 for intra bonds, 6.1–17.7 for L1 and 5.3–16.8 for L2.
The recovered chemistry is active; global population stability does not certify
all slow topology. The defective 0–6M histories are historical context, never
the equilibrium target or part of a corrected stationarity window.

Validation hierarchy was inspected before proposing these star runs:
`VALIDATION.md` records executed static-dimer, dynamic-dimer D1, large-N K1
cadence/frequency/density/Ee results and S2 star validation. D1 Ea=4 had only
15 transitions, a smoke-level kinetic check; K1 documents the stronger
many-sticker evidence. The corrected periodic-search oracle and retained
fresh-MD GPU smoke add implementation evidence, not equilibrium evidence for
new conditions. Historical association-dependent conclusions retain the
qualification in `PERIODIC_CANDIDATES.md`.

## Complete inventory and E1 mapping

The committed [frozen inventory](campaign/e2_remaining_inventory_20261011.json)
contains all 15 system IDs, all 24 actual E1 state paths, state SHA256s,
preparation SHAs, completion-record paths, geometry counts, corrected C1
provenance and a checksum inventory of preserved data/reports. Paths in its
E1 entries are relative to the dataset root.

For the following table, each ordinary start is exactly
`banks/e1/<geometry>/r001/state.e1.lammpsdat`, `r002/state.e1.lammpsdat` and
`r003/state.e1.lammpsdat`, with E1 seeds 12001/12002/12003 respectively.
The only exception is RP060/r002, whose actual start is
`banks/e1_retries/F04_N010_RP060/r002/attempt001/state.e1.lammpsdat`.
The failed original RP060/r002 is preserved and never selected.

| E1 geometry (three starts above) | Polymer / solvent / total beads | Remaining E2 targets: suffix added to geometry |
|---|---:|---|
| F04_N010_RP080 | 41000 / 2563 / 43563 | EE04_EA04, EE06_EA04, EE10_EA04, EE12_EA04; EE08_EA06, EE08_EA08, EE08_EA10 conditional C1 reuse |
| F04_N010_RP020 | 41000 / 133250 / 174250 | EE08_EA04 |
| F04_N010_RP040 | 41000 / 46125 / 87125 | EE08_EA04 |
| F04_N010_RP060 | 41000 / 17083 / 58083 | EE08_EA04 |
| F04_N020_RP080 | 81000 / 5063 / 86063 | EE08_EA04 |
| F04_N040_RP080 | 161000 / 10063 / 171063 | EE08_EA04 |
| F03_N010_RP080 | 31000 / 1938 / 32938 | EE08_EA04 |
| F06_N010_RP080 | 61000 / 3813 / 64813 | EE08_EA04 |

The prepared reference is `F04_N010_RP080_EE08_EA04`, using
`banks/e2_extensions/C1_periodic_recovery_v1/r001..r003/state`, rather than
`banks/e2/F04_N010_RP080_EE08/r001..r003/state` at defective 6M.
All 11 other E2 bank locations are empty/unexecuted in the inspected dataset.

All seven reference-geometry chemical conditions share the *same* three E1
starts. Ee=4/6/8/10/12 require separate chemical equilibration; equilibrating
one Ee never prepares another. Ea=4/6/8/10 at Ee=8 share the intended equilibrium
energy but differ in kinetics. Existing bank keys omit Ea, so they do not
themselves establish that sharing is justified. Different concentration means
a different box and solvent population even at identical f/N. Different f/N
means different permanent geometry and sticker density; do not transplant C1
coordinates to these banks.

## Frozen chemistry and expected slow processes

Use T=1, dt=.01, nu0=20, Nevery=100, r_assoc=1.25, damping=2 (NVT friction .5),
K=30, R0=1.5, 1000 stars and total density .85; preserve each E1 serialized box
and its documented rounding. Fresh E2 starts load E1 velocities unchanged,
start with zero temporary bonds and step zero. **Proposed preparation Ea=4**
for all fresh banks; retain each target Ee. No ramps, compensating nu0, cutoff
changes or altered chemistry are proposed.

The local scientific reference inspected is
`/home/jramirez/lammps`, branch `feature/associating-stickers`, SHA
`1c6faf70e94aef2389c208e8c80c60c084a96907`, specifically
`src/ASSOCIATING/fix_associating_kinetics.{cpp,h}` and
`pair_associating.{cpp,h}`, with file hashes in the inventory. Its unrelated
analysis worktree changes were not touched. `bench/associating/dimer_kinetics/`
reference results were also inspected; its reported slopes are finite-run
measurements, not imposed universal rates. GitHub page access and read-only
remote SHA checks failed (cache miss / DNS unavailable), so the latest remote
reference tip is **not verified**. Recheck it before approving execution.

The implemented rule is
`q = -expm1(-nu0 * exp(-Ea/T) * Nevery * dt)` with pair-ordered Metropolis
acceptance using `delta_u = U_FENE(r)-U_FENE(rstar)-Ee`. Both creation and
breaking require distance **strictly below r_assoc**, while an existing bond
continues to exert shifted FENE forces to R0. WCA is included once. Invalid
FENE states fail rather than being clamped. Preserve stable IDs and reciprocal
valence-one partners.

At the proposed cadence, q for Ea=4/6/8/10 is approximately
.306714/.048366/.006687/.000908. Relative to Ea=4, equal eligible-candidate
attempt counts cost about 1/6.34/45.9/338 times as much MD. These are attempt
ratios, **not measured equilibration times**. Diffusion, mechanical relaxation,
eligible bound-distance visits, rebinding and network rearrangements matter.

- Increasing Ee favors bonds and usually suppresses rupture at comparable
  distance. Ee=10/12 can fill rapidly yet retain topology for much longer.
  Many creations do not demonstrate turnover; measure neighbor replacements
  and loop relaxation as well as breaks.
- Increasing Ea slows both reaction directions without changing the intended
  equilibrium energy. Ea=4 preparation avoids paying those attempt ratios,
  but finite-step coupled MD/reaction invariance must be reviewed for this
  corrected star system before transferring states to higher Ea.
- Dilution reduces inter-star encounters and may increase intra-star competition
  and fragment the network. It need not monotonically shorten relaxation. RP020
  is also the largest solvent-rich N=10 simulation, with four times C1 beads.
- Longer arms change contact geometry, sticker concentration and conformational
  relaxation. At fixed rho_p, sticker density is `f*rho_p/(1+f*N)`; N=20/40
  reduce it while adding slow arm/collective modes. E1 N=40 Rg² IAT was roughly
  3900–4700 time units, versus 80–115 for C1; E2 may be slower still.
- Functionality changes valence per molecule (not per sticker), loops, distinct
  neighbors and connectivity. f=6 can remain connected while exchanging many
  bonds; f=3 may be more sensitive to connectivity fluctuations. Neither
  direction has a validated equilibration-time multiplier.

## Proposed sequence and adaptive budget

Run one condition's three histories sequentially on the dedicated GPU, review
them jointly, then advance. All new banks start from their own E1 states.
C1's 8M acceptance is context, not a universal minimum duration.

| Wave | Order / representatives | Purpose and initial allocation per history |
|---|---|---|
| A | F04_N010_RP080_EE04, then F04_N010_RP020_EE08 | Contrast weak bonds with strong-bond dilute encounters; 2M each, first review only |
| B | F04_N010_RP080_EE06, F04_N010_RP040_EE08, F03_N010_RP080_EE08 | Resolve intermediate chemistry/concentration and low functionality; 2M each |
| B risk probes | F04_N010_RP080_EE12, then F04_N040_RP080_EE08 | Establish strong-bond turnover and long-arm resource/slow-mode limits early; 2M and 4M respectively, no automatic acceptance |
| C | F04_N010_RP080_EE10, F04_N010_RP060_EE08, F06_N010_RP080_EE08, F04_N020_RP080_EE08 | Fill intervening conditions using reviewed probe evidence; initially 2M each, adjust before execution |
| D, conditional | C1 EE08 at Ea=6/8/10 | Review bank sharing; if invariance is insufficient, separately scope corrected comparisons or physical-Ea E2 banks |

Every ID in the sequence has production suffix EA04 except wave D. This covers
all 11 fresh banks. Initial allocations are checkpoints for review, not promises
of equilibrium. Preserve initially unbound starts to avoid unknowingly borrowing
an already connected, wrong-Ee network. A bidirectional/alternative-network
initialization test is a possible later convergence diagnostic if path memory
persists; it is outside this proposed initial allocation.

Collect state/numerical diagnostics every 1000 steps (10 time units) and every
accepted reaction event. Review 500k-step windows (5000 time units), then grow
windows to 1M/2M or longer when topology correlation requires it. Discard the
initial filling/conformational transient explicitly and retain it in the archive.
Choose window size from the slowest credible observable, not total bonds alone.
Request additional 2M segments, or 4M for slow conditions, only after review;
revisit the budget at cumulative 8M and 16M. These are review ceilings, not
automatic stop/accept rules. No unresolved condition proceeds to production.

## Adaptive stopping and acceptance

Numerical validity is mandatory before any statistical interpretation: full
requested step/sweep coverage, synchronized step/time, exact parent and parameter
hashes, finite positions/velocities and energies where recorded, permanent and
temporary bond distances below R0, reciprocal partners, and complete ordered
event replay. Reconstructed free/bound populations, intra/inter bonds, counters,
components, largest component, distinct degree and L1/L2 must match diagnostics
and the final restart mirrors. A numerical failure stops the condition and
retains the failed attempt; it is not a stationarity failure to average away.

The joint scientific review should include:

1. Bound/free stickers, total/intra/inter bonds, connected components, largest
   component fraction, mean and second moment of distinct-neighbor degree,
   degree/component distributions reconstructed from events, and L1/L2. L1
   counts `m*(m-1)/2` parallel inter-star bond pairs; L2 counts simple molecular
   triangles. Neither is a synonym for intra-star bonds or all graph cycles.
2. Accepted creations/ruptures and distinct-neighbor gains/losses, per physical
   time and per exact event-integrated free-sticker/active-bond exposure. Separate
   intra/inter turnover where possible using existing molecule identities. Zero
   activity or rapid same-neighbor rebinding must not masquerade as mixing.
   Balance must satisfy the observed population change, but balance alone does
   not pass. No candidate acceptance probability can be inferred from these
   denominators; rejection opportunities are not recorded.
3. Consecutive late-window means, within-window blocks, late slopes and paired
   last-minus-previous changes across the same three histories. Use the existing
   first-nonpositive-lag IAT estimator and 5/10/20-block SEM sensitivity, then
   replica-level Student-t summaries (df=2). Frames/events are not independent
   uncertainty units. Failure to detect drift with a broad interval is not an
   equivalence result; define scientifically useful precision before approval.
4. Recompute on longer windows and late halves/quarters. As a proposed resolution
   warning, require review windows to span at least about 20 credible IATs
   (`Neff ~ 10`), preferably more for acceptance, and block durations several
   IATs long. If ten blocks cannot satisfy that, grow the window rather than
   trusting their SEM. This is a resolution diagnostic, not a theorem or a
   universal pass threshold. Truncated IAT can miss long tails; constant or
   saturated L1/L2/connectivity does not prove mixing.
5. Independent-history compatibility in both means and distributions, continued
   chemical/network activity, no common late drift, and precision sufficient to
   exclude consequential remaining changes. Inspect the slowest history and
   metric; do not accept the ensemble while one history remains unresolved.
   Low populations use absolute counts/uncertainty, avoiding unstable percentages.
6. Conformational stationarity for long arms, plus stable numerical temperature
   and bond extrema. GJF on-site temperature near .98 is not itself failure.
   Saturated largest-cluster fraction cannot substitute for intramolecular or
   network relaxation. Physical periodic wrapping is a distinct observable from
   ordinary graph connectivity.

Outcome labels should distinguish `numerically_valid`,
`equilibration_not_established`, `equilibrium_prepared_with_qualification` and
`accepted_for_named_use`. Qualified acceptance explicitly names the remaining
slow observable, supporting windows, precision and permitted use. Final state
selection is the endpoint of each accepted history; do not cherry-pick frames
by topology or count windows as additional replicas. Adaptive repeated review
is exploratory and requires recorded decisions; its confidence intervals are
not sequentially calibrated formal hypothesis tests.

## Reuse and implementation decisions before execution

Reuse `kg_assoc_campaign.py` for matrix expansion, geometry checking and active
E1 resolution; `kg_assoc_e1.check_snapshot` for numeric/geometry checks;
`analyze_e2_stationarity.py` for parsing, trends, IAT and blocks;
`analyze_c1_e2_pilot.replay` for inherited event/network reconstruction;
`analyze_p45_topology.py` for graph definitions; and the exposure/activity and
replica-statistics helpers in `analyze_c1_recovery.py` and
`analyze_p46_bond_dynamics.py`. Keep the corrected independent candidate oracle
as host preflight and capped smoke instrumentation, not an all-pairs operation
in ordinary MD. Use the authenticated recovery launcher's hash-bound plan,
nonoverwrite lock, fail-fast status and explicit authorization pattern.

The current infrastructure is **not yet a general authenticated adaptive E2
runner**. Resolve these concrete gaps in a separately reviewed implementation:

- Parameterize validators by the selected system, parent, start/end step, sticker
  and bead counts, physics and effective seeds. The segment validator still
  demands C1, parent step 6M, 43563 beads and seeds 2200X/3200X; the recovery
  analysis uses 4000 stickers, .01, four fixed windows and defective C1 parents.
  Reuse their logic without passing non-C1 data through C1 constants.
- Generalize an immutable attempt directory such as
  `banks/e2_attempts/<bank>/attempt001/segment001/r00X/state`; create each segment
  exclusively, preserve failed outputs, prohibit `--force`, and validate all
  three parents before launching. The generic runner does not provide the full
  recovery authentication or scientific acceptance checks. Its validation action
  writes bank reports; do not invoke it on historical banks for this proposal.
- Freeze a distinct per-bank/per-history chemistry seed map and per-segment MD
  seed map, recording effective 32-bit MD kernel seeds and checking collisions
  with C1 and other segments. The generic seed 2200X repeats across conditions;
  decide explicitly whether to use common random numbers or distinct streams.
  Recommended policy: distinct new condition streams, unchanged chemistry seed
  within a continued history, fresh MD noise at each restart, no velocity
  resampling. Resets preserve stochastic preparation, not bitwise continuity.
- Same-parameter E2 restart restores Ee/Ea from its sidecar; CLI overrides do
  not change those parameters. Do not assume a recovery can silently switch
  Ee/Ea. Wave D comparisons need a reviewed explicit parameter-switch path or
  fresh physical-Ea E2 runs. Analytic reversibility and older K1/S2 evidence
  motivate sharing but do not alone certify corrected full-star invariance.
- E2 currently writes scalar state/numerics/events and final coordinates, without
  time-resolved bead/COM conformations. Event replay supplies topology but not
  Rg²/arm modes or periodic winding translations. Prefer a small E2 diagnostic
  addition using validated PBC-safe structural helpers for Rg² and terminal R²,
  especially N=20/40, before their execution. Endpoint structure from
  `analyze_campaign_structure.py` cannot establish time stationarity. If adding
  synchronized topology/COM output for wrapping is desired, review its cost
  separately; the existing periodic analyzer requires both streams.
- Add a reviewed immutable active-E2 selection record for final accepted segment
  prefixes and qualified human evidence. Production preparation currently selects
  the original `banks/e2/<bank>/r00X/state`, with no active-E2 resolver. It would
  pick the defective C1 6M state; never relabel/copy 8M outputs over that bank.
  No `validation.json` acceptance record presently exists for these E1 banks,
  and C1 recovery status remains `review_required`. Formal provenance/acceptance
  publication must reference the user's decision and the E1 audit before launch
  or later production preparation; it must not fabricate a past decision.

Any included CUDA/header change requires rebuilding affected executables and
new hash-pinned validation. Retained C1 smoke does not validate a changed binary
or different geometry. After implementation, run deterministic fixtures for
non-C1 counts, inherited partners, absolute event cadence, effective seeds,
tampering and exclusive attempts before separately authorized capped GPU tests
and any long run. No generic percentage gate from the old percolation scout is
borrowed for this campaign.

## GPU and storage estimate

The measured corrected ordinary C1 2M segments took
592.477/594.268/593.545 seconds on host `titan`, averaging 593.430 seconds
(about 9.89 minutes per history). Use this measured correction-era ordinary
runtime rather than the older defective 6M timing or CPU-heavy oracle smoke.
This is retained evidence, not a new benchmark. The campaign's TITAN Xp identity
should be reconfirmed along with driver/CUDA/compiler/device details at launch.

For a first estimate, scale linearly with **total beads**, including solvent.
The 11 fresh banks total 19.4795 C1 bead-count equivalents per history.

| Allocation for all 33 fresh histories | Estimated serial GPU time |
|---|---:|
| 2M each | 9.63 h |
| Initial proposal: 2M each, except N=40 at 4M | 11.57 h |
| 6M each (planning scenario only) | 28.90 h |
| 16M each (planning scenario only) | 77.07 h |
| Additional 2M for all three histories of one C1-size bank | 0.495 h |
| Additional 2M for all three N=40 histories | 1.94 h |

Budget **40–100 GPU-hours initially** for a 6–16M scenario with scheduling and
validation margin, subject to revision after probes. Very strong bonds or slow
arms may exceed it. Linear scaling omits chemistry/network cost, neighbor-list
behavior, I/O and host validation; f=6 is especially not calibrated. Benchmark
ordinary segment throughput for RP020 and N=40 during authorized probes.
Host replay/analysis time is additional and may dominate a review pause.
Physical-Ea preparation of the three C1 variants is excluded from these totals;
attempt-count scaling alone would make it very expensive and is not a schedule.

Actual C1 recovery outputs are about 10.26 MB/history for 2M, including two final
particle mirrors, ~73k events, 2001 scalar/numerical rows and logs. Fixed snapshot
cost scales with beads, while event cost scales with activity/stickers, not
solvent. An uninterrupted 6M for 33 histories is roughly **0.8–1.2 GB** under
C1-like activity. Retaining each 2M segment adds repeated final mirrors; estimate
**1.5–2.5 GB at 6M**, **4–7 GB at 16M**, and reserve **10 GB new space**, or
**20 GB with a separate verified archival copy and analysis margin**. Larger
event activity and any new coordinate streams require recalculation.
No production bead trajectory, stress stream or 100M output is included.
Existing data/archive space is additional and must remain available.

## Immutable provenance and review decisions

The inventory pins existing E1 originals/retries, old E2, corrected recovery,
smokes, scientific reports, manifest/inputs and prior audited historical data.
It includes path, size and SHA256; it is a frozen observation, not retrospective
proof for historical missing input hashes. Recheck against it before/after future
preparation and launches. SHA256 detects changes; use an archival read-only copy
or storage snapshot for enforcement, without modifying originals or their modes.
Never overwrite a state, command/completion record, report or active-state map.
New plans, execution authorizations, segments, reviews and acceptance revisions
receive exclusive versioned names and parent hashes. No automated retry/resume
may hide an incomplete attempt.

Record committed code SHA and clean status, source/dependency hashes, build argv,
compiler/CUDA and GPU/driver identity, executable hashes, full argv, all parameters,
source E1 completion record and retry resolution, chemistry/MD/effective seeds,
absolute step range, restart/RNG/image policy, wall time, output hashes, analyzer
SHA/configuration and signed reviewer/date/use/qualification. Across restart
boundaries validate partner/counter continuity but do not stitch lifetimes,
transport or stress histories. Segment review windows remain separately labeled;
if longer stationarity evidence is assembled, document the MD-reseed boundaries
and test sensitivity to them rather than treating reset segments as uninterrupted.

Review is needed on Ea=4 preparation and higher-Ea C1 sharing, initial wave/order
and resource ceilings, precision targets for slow topology, conformational
instrumentation (especially N=40), whether wrapping is required, immutable
active-E2/acceptance publication, seed allocation and latest reference SHA.
These are proposed scientific/implementation decisions, not execution consent.

## Checks for this planning task

The actual manifest/protocol and all 24 E1 completion records were inspected;
the active retry was resolved, distinct endpoint hashes checked, C1 raw hashes
and corrected review sources authenticated, and reference kinetics/force semantics
compared with the planned frozen model. Offline C1 recovery verification passed
(exit 0) for all three retained segments; the campaign fixture suite passed
**31 tests** in 74.880 seconds. These are deterministic/fixture checks, not
statistical convergence tests. Existing restart-parser ResourceWarnings were
nonfatal. All 24 E1 snapshot/diagnostic review hashes and **93** prior pinned
historical data hashes matched. The inventory pins **506 files / 594,671,885
bytes** and was rechecked after documentation.
Only this document and `campaign/e2_remaining_inventory_20261011.json` changed.
No executable/source change requires a rebuild. Protected `src/*` and
`examples/KG/*` were not modified. No GPU or statistical convergence experiment
was run; new conditions' equilibration times remain unmeasured.
