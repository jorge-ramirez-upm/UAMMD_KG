# Semiflexible-chain project status

D2A.2 status, 27 October 2026: **BOUNDED TECHNICAL ACCEPTANCE**, based on
user-reported CPU correctness, sanitizer and allocation-failure passes, the
corrected metadata regression pass, and the double-precision tiny GPU verifier
pass. Enabled/disabled saved physical records agreed and dynamical correlation
replay passed in the two tested configurations. This does not compare all
intermediate states or establish long-time dynamics, equilibrium preservation
or performance acceptance. See the [implementation/verification record](E1_STAGE_D2A2_IMPLEMENTATION_REPORT.md)
and [acceptance scope and D2A.3 proposal](E1_STAGE_D2A3_EXPLORATORY_DESIGN.md).
The latter specifies eight exploratory runs across four cells. The
[complete eight-run preparation](E1_STAGE_D2A3_CAMPAIGN_PREPARATION.md) freezes
seeds, schedules, executable identity and resource limits; the user selected
all eight serially without mandatory intermediate review after the first.
**Independent preparation review precedes the user's explicit launch.**
No D2A.3 run has begun in Codex.

D2A.3 execution update: the user reports eight successful runs, approximately
907.24 s campaign wall time, 205.5 MB recorded evidence and peak child RSS
149196800 bytes. Saved summary/provenance records were inspected read-only;
full independent authentication and scientific reductions have not been run.
The [scientific analysis preparation](E1_STAGE_D2A3_SCIENTIFIC_ANALYSIS.md)
provides the user's offline authentication/analysis command. Physical conclusions,
four figures and a next-study decision remain pending authenticated products
and review. This is not scientific dynamics or equilibrium acceptance.

D1.6 status, 27 October 2026: **SCIENTIFICALLY CLOSED WITH QUALIFICATIONS —
EQUILIBRIUM PRESERVATION NOT CONFIRMED**. The
[scientific closure](E1_STAGE_D16_SCIENTIFIC_CLOSURE.md) consolidates D1.6B–F;
it is not a passed equilibrium-preservation acceptance test. No implementation
defect was identified in the inspected equilibrium initialization, hopping or
renewal rules. Full-model stationary connector-bias sign and magnitude remain
unestablished. Proceed toward dynamical characterization with the accepted
simulator unchanged, retaining timestep sensitivity as an interpretation
limitation; review and separate authorization precede the next milestone.

This repository is a validated backbone for a future slip-spring model. Its long-term objective is to study semiflexible chains with dynamically introduced, moved, and removed slip-springs while retaining an independently testable polymer reference. Development-only E1 Stage A fixed-attachment harmonic slip-springs are implemented and independently audited; Stages B/C nearest-neighbor Metropolis hopping and end renewal are implemented with bounded detailed-balance and equilibrium verification. Slip-spring rheology and terminal dynamics remain unvalidated. See [the audit](E1_STAGE_A_AUDIT.md) and [Stage C report](E1_STAGE_C_REPORT.md).

The present backbone uses an open chain with **N bonds and N+1 beads**, free ends, unwrapped coordinates, no excluded volume, no hydrodynamics, no periodic wrapping, and independent chains. The finite-rest-length Hamiltonian, exact equilibrium initializer, overdamped Euler–Maruyama update, GPU observations, configurational stress, and CPU reference tools are implemented under this directory. The original Gaussian Rouse path remains available and unchanged.

| Area | Status | Evidence and boundary |
|---|---|---|
| Rouse reference, dimensions, diffusion, stress relaxation | Completed/validated for tested matrix | Stage 1/2A/2B/2B.1 reports and archived N100 results; hardware-specific performance only |
| Nonlinear finite-rest-length semiflexible backbone | Validated for the frozen Stage 4A.2 campaign | 204 user-executed experiments, zero automated statistical failures; no universal stiffness, timestep, or N guarantee |
| GPU six-channel stress and streaming implementation | Implementation and bounded verification complete; scientific host campaign remains separate | Stage 4A.3A/B reports and frozen 4A.3C plan; no slip-spring interaction |
| GPU computational measurements | Validated only for recorded hosts/configurations | Stage 4A.3C benchmark and execution reports; overlapping timers are not additive |
| Timestep convergence, N=8 and N=32 | Provisional/unresolved | Stage 4A.4 reports and external N32 recovery receipts; missing diagnostics and exact-lag limitations remain |
| Hessian/local-mode timestep preselector | Heuristic tool, software-tested | Stage 4A.5 report; no stability or accuracy guarantee |
| Energy/distribution static diagnostics for Stage 4A.4 | Unresolved | Existing scalar outputs do not provide all required energy, angle, end-to-end, or full-contour distributions |
| Terminal nonlinear relaxation | Unresolved | T=20 timestep studies are short-time comparisons, not terminal campaigns |
| E1 canonical slip-spring equilibrium and fixed attachments | Design frozen; Stages A/B accepted, Stage C hopping/renewal bounded checks passed | [EQUILIBRIUM_MODEL_E1.md](EQUILIBRIUM_MODEL_E1.md), [Stage A audit](E1_STAGE_A_AUDIT.md), [Stage B report](E1_STAGE_B_REPORT.md), [Stage C report](E1_STAGE_C_REPORT.md); no Brownian timestep acceptance or rheology validation |
| E1 D1.6B–F scientific investigation | Scientifically closed with qualifications; equilibrium preservation not confirmed | [Scientific closure](E1_STAGE_D16_SCIENTIFIC_CLOSURE.md); completed exploratory cohort and theoretical audit, not an equilibrium-preservation acceptance pass |
| D2A.1 CPU observables / D2A.2 read-only acquisition | Bounded technical acceptance on user-reported verification | [D2A.1 report](E1_STAGE_D2A1_IMPLEMENTATION_REPORT.md), [D2A.2 report](E1_STAGE_D2A2_IMPLEMENTATION_REPORT.md), [current acceptance scope](E1_STAGE_D2A3_EXPLORATORY_DESIGN.md#d2a2-bounded-technical-closure); no terminal-dynamics or performance acceptance |
| D2A.3 exploratory dynamical study | Eight-run completion reported by user; independent authentication and scientific interpretation pending | [Approved design](E1_STAGE_D2A3_EXPLORATORY_DESIGN.md), [campaign preparation](E1_STAGE_D2A3_CAMPAIGN_PREPARATION.md), [offline analysis handoff](E1_STAGE_D2A3_SCIENTIFIC_ANALYSIS.md); analysis code unexecuted in Codex |

The D1.0–D1.4 paragraphs below are historical stage snapshots; their preparation-
time authorization/execution statements do not supersede the completed D1.6B
cohort or the current D1.6 closure classification.

E1 Stage D1.0's read-only equilibrium observer has bounded technical acceptance
under the user's Stage D1.1 instruction. Stage D1.1 prepares a frozen proposed
8-cell/32-replica pilot, exact schedules, a gated serial runner, independent
SHA256 authentication and exploratory replica analysis; see
[E1_STAGE_D1_PILOT_PREPARATION.md](E1_STAGE_D1_PILOT_PREPARATION.md).
**No scientific pilot or D2 run has been authorized or executed.** The committed
approval template is false with null resource budgets. Scientific accuracy,
feasibility and production timestep acceptance remain unresolved.

D1.2 prepares a separate long-time/sparse-observation proposal; see
[E1_STAGE_D1_LONG_TIME_PILOT.md](E1_STAGE_D1_LONG_TIME_PILOT.md). Existing scalar
and full-E1 schedules are already independent, so dynamics/observer code stays
unchanged. Phase A benchmarking, Phase B T10 exploration and conditional Phase C
T100+ preservation require distinct reviewed manifests and resource approval.
Frozen authorization templates remain false/null; D1.1/D1.2 files/hashes remain unchanged. D1.3 now supplies the Phase A-only execution/authentication/benchmark-analysis
adapter with bounded technical checks and live read-only preflight; see
[E1_STAGE_D13_PHASE_A_PREPARATION.md](E1_STAGE_D13_PHASE_A_PREPARATION.md).
The user subsequently authorized exactly eight sequential Phase A benchmark
processes under explicit resource limits. They completed with four byte-identical
physical replay pairs and successful independent authentication; see
[E1_STAGE_D13_PHASE_A_RESULTS.md](E1_STAGE_D13_PHASE_A_RESULTS.md). Campaign wall
was 16.35 s and evidence 10.43 MiB on the recorded host. No scientific equilibrium
acceptance is established; repetitions, B/C and D2 remain unauthorized.

D1.4 now prepares the distinct Phase B four-cell/two-replica T10 manifest,
gated runner and independently authenticated drift/ACF analysis; see
[E1_STAGE_D14_PHASE_B_PREPARATION.md](E1_STAGE_D14_PHASE_B_PREPARATION.md).
Fresh accepted-source CUDA13 compilation, read-only GPU preflight, CPU/synthetic
regressions and two tiny nine-step fixtures passed. No Phase B scientific run
was executed, and no Phase B approval exists: execution budgets remain null.
R=2 uncertainty is weak, all IATs remain unresolved, and no scientific accuracy
or timestep acceptance is inferred. Accepted simulator/observer and historical
frozen evidence remain unchanged.

The current numerical reference choices are `kBT=1`, `zeta=1`, `b0=1`, `kb=30`, double precision for scientific validation, and typically `seed=433201` for timestep studies. Interior `kappa` is nonnegative and endpoint entries are zero. The baseline timestep in Stage 4A.4 was `2.5e-5`; `5e-4` and `1e-3` were comparison candidates, not silently promoted production values.

The recorded CPU stress benchmark reached 1.938 million chain observations per second (946.2 complete frames/s) in its selected largest-bank median. A separate archived GPU measurement reported 1.943 ns/bead/step integration-only and 2.384 ns/bead/step overall for its tested N=8 configuration. These are measurements of named hosts and configurations, not portable performance guarantees; GPU stress, transfer, CPU-worker, output, and wall scopes overlap and must not be added.

The authoritative sources are the committed reports, source, tests, and frozen plans in `examples/slip-springs/`. Large GPU trajectories and some analysis receipts were generated on an external host and are not committed here; their paths, hashes, and limitations are stated in the corresponding reports. E1 fixes the canonical state space and proposed kinetics. Stage A covers only fixed attachments, annealed initialization and harmonic forces; Stage B adds fixed-anchor hopping within fixed chain-population/order sectors. Stage C adds globally canonical end renewal under the current authorization; per-chain populations may fluctuate. This does not establish a general ergodicity theorem or terminal relaxation acceptance.
