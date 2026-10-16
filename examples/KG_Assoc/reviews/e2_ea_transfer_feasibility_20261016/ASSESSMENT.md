# Feasibility of the remaining Ea sweep

**Decision: reference-state transfer is potentially useful, but requires targeted
restart and coupled-sampler validation first.** The three accepted Ea=4, Ee=8
networks are valid physical/chemical starting states for Ea=6/8/10. Ea does not
enter their Hamiltonian. Reusing them is a defensible preparation strategy, not
certification that they are independent equilibrium draws of the new numerical
process. Do not automatically accept the three new systems or relabel the
reference acceptance. Prefer a staged transfer route, with a small independent-E1
comparison if the targeted validation leaves an initialization discrepancy.

Review date: 2026-10-16. Starting clean local and remote `KremerGrest` HEAD:
`bd77a09daa28791972810fc81ffc82b8a9024460`. Final SHA is the containing review
commit, reported after push. This review authorizes no implementation or run.

## What follows from the implementation

At fixed positions and an eligible pair, the actual code uses
`q = -expm1(-nu0 * exp(-Ea/T) * Nevery * dt)` times a Metropolis factor.
Forward/reverse probability ratio is `exp(-deltaU/T)` in the usual ideal-uniform
random-number model. Thus changing Ea changes both conditional probabilities
by the same exact q ratio, rather than the approximate Arrhenius factor.
A single-edge reversible update preserves the conditional Boltzmann distribution
over valence-one chemical matchings. Every state-independent ordered composition
of those updates preserves it too. Competing reactions do not by themselves
invalidate that conclusion: availability is re-read after each edge update.

This is stronger than simply observing a common activation factor, but narrower
than proving full MD/chemistry equilibrium invariance. Finite-step GJ MD is not a
Metropolis sampler; exact invariance for this anharmonic, topology-changing
Hamiltonian is unproved. The existing reference acceptance already carries that
qualification. Changing reaction cadence relative to MD motion can change the
numerical invariant distribution and the sampling of encounters, recrossings and
slow topology. The full chemical sweep includes multi-event probabilities and
is not uniformly multiplied by q. Physical-time trajectories are consequently
not exact clock-rescaled copies. Hash/finite-precision qualifications and the
conditional proof are detailed in [KINETICS.md](KINETICS.md).

The Ea switch leaves instantaneous energy and forces unchanged at fixed physical
and chemical state. Ee remains 8; shifted associating FENE, WCA, permanent bonds,
cutoffs, temperature, damping, geometry and density must all remain unchanged.
Partners must be loaded, not reconstructed from distance or erased. Reweighting
by Ea is unnecessary for the intended Hamiltonian. None of these facts removes
residual bias in the actual reference sample.

## Existing validation: useful support and its boundaries

The source of truth is local LAMMPS branch `feature/associating-stickers`, commit
`1c6faf70e94aef2389c208e8c80c60c084a96907`; both implementations use the same
finite-step factor, energy shift and sequential match/break semantics. Exact
reviewed source/evidence bytes are pinned in [SOURCE_SHA256.json](SOURCE_SHA256.json).

The validation hierarchy has existing analytic/static and dynamic dimer evidence,
K1 many-sticker results and star S2 results, inspected before proposing more star
validation. Existing dimer host regressions explicitly check paired probability
ratio and cutoff gating; the current review additionally compiles the frozen
host reaction loop with a host-only state adapter and tests 340 deterministic
ordered sweeps, both Metropolis branches and Ea guards. It constructs no CUDA
system. Enumeration of all chemical matchings in a four-sticker competing-edge
example verifies conditional Gibbs invariance for all six edge orders and four
barriers. This is a deterministic algorithm check, not new stochastic convergence
evidence or a test of the GPU force/device path.

Existing large K1 results at N=32768, rho=.05, Ee=4, nu0=20, dt=.005,
Nevery=100 give event equilibrium constants 2.61160, 2.61313, 2.61090,
2.61136, 2.60316 at Ea=2/3/4/5/6; there is one history per point. The independent
LAMMPS K1 report gives the Ee equilibrium slope about 0.984 at T=1. These
support the intended energetic semantics without establishing star topology
sampling or Ea=8/10 behavior. CSVs/reports and the LAMMPS implementation were
inspected; no K1 campaign is reproduced here.

The historical star S2 Ea=2/4/6 sweep had bound fractions
0.88914/0.88378/0.88513. Its archived command explicitly uses
`r_assoc=1.122462048309373`, versus current 1.25. It predates the corrected C1
periodic-candidate lineage. Treat its approximately invariant occupancy as
historical support only. Its single-history split-half pass does not establish
stationarity or topology invariance of the present three target systems.
Cadence-dependent lifetimes were already documented. The smaller validations
have actually been executed historically; their limited scope is not expanded
by this review.

## Reference identities and inherited limitations

Use only the three accepted corrected endpoints under
`banks/e2_extensions/C1_periodic_recovery_v1/r001..r003/state`, absolute 8M,
chemical seeds 22001/22002/22003. Exact pair hashes are in
[evidence/REFERENCE.json](evidence/REFERENCE.json). Their record permits only
`F04_N010_RP080_EE08_EA04` as `production_initial_state`; it does not permit any
higher-Ea system. Historical defective 6M banks remain ineligible as transferred
starts. They are read solely as original parents for replay authentication.

Fresh CPU validation reproduces the accepted corrected 6–8M numerical,
accepted-event and network history, including final partners/counters and output
hashes. It does not rerun the original whole preparation or restore unavailable
historical executable bytes. The accepted record explicitly retains less complete
historical source/build provenance and unavailable executable-byte evidence.

Reference qualification is initialization only: incomplete slow-topology
sampling/decorrelation, possible residual preparation bias and corrected-from-PBC-
defective historical lineage remain material. Complete stationarity, structural
decorrelation and absence of initialization bias have not been demonstrated.
All limitations carry into every derived preparation. New noise cannot turn a
biased parent into an unbiased equilibrium draw or remove a permanently trapped
motif instantly. Long-lived isolated states, L1/L2, loop/multiplicity populations
and replica structural offsets require explicit follow-up.

## Kinetic scale and cost

Rates below count events for the whole 1000-star system per physical time, with
dt=.01. The corrected 6–8M interval contains 20,000 physical-time units per
history. Distinct-neighbor events count 0-to-1 / 1-to-0 inter-star edges, not every
bond event. Fresh replay equals all four archived 500k-window counts.

| Observable | Mean | Exploratory 95% half-width, three histories |
|---|---:|---:|
| Accepted formation | 1.81950 | 0.00566 |
| Accepted breaking | 1.81848 | 0.00653 |
| Distinct-neighbor gain | 1.64923 | 0.01329 |
| Distinct-neighbor loss | 1.64718 | 0.01509 |

These df=2 intervals describe replica variation of observed interval rates;
they do not measure all slow-mode uncertainty or establish stationarity. Divide
by 1000 for events per star per physical time. Gains/losses and formations/breaks
are correlated observables, not independent validation samples.

| Ea | Exact q | q/q4 | Reciprocal factor | Projected break rate | Projected neighbor loss rate |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.3067140771 | 1 | 1 | 1.81848 | 1.64718 |
| 6 | 0.0483662585 | 0.15769168 | 6.34149 | 0.286760 | 0.259747 |
| 8 | 0.0066867958 | 0.02180140 | 45.86862 | 0.0396455 | 0.0359109 |
| 10 | 0.0009075865 | 0.00295906 | 337.94474 | 0.00538101 | 0.00487412 |

Only q and its ratios are exact algorithmic quantities (subject to numerical
rounding). Projected aggregate rates assume unchanged distributions of geometry,
availability, energies and sequential competition; this need not hold. q4 is
0.307, so the rare-attempt approximation is visibly imperfect. The simple
Arrhenius reciprocal factors would be 7.389/54.598/403.429, about 16.5–19.4% larger.
Neither scaling predicts a network relaxation time with controlled uncertainty.

A. **Existing E1 route.** Initially unbound E1 states are valid but have a large
chemical/network preparation transient. Matching the reaction opportunity of an
8M Ea4 history would cost about 50.7M/366.9M/2703.6M steps per history at
Ea6/8/10. These are scenario scales, not required durations, lower bounds or
predictions of assembly time: early free-sticker abundance differs greatly from
the accepted network and forward competition changes. The current planner also
blocks an ordinary unbound preparation of these same-bank target systems, so
retaining this route requires administrative support too.

B. **Reference transfer.** It avoids rebuilding an initially unbound network and
begins with the correct Hamiltonian and complete chemical state, subject to
inherited bias. It may save most of the initial assembly work. Additional
relaxation needed to address inherited slow modes remains unknown, and could
still scale severely with barrier. There is no basis for promising a particular
short equilibration duration or omitting relaxation at Ea10.

The three retained reference status receipts report 592.477/594.268/593.545 s
for 2M steps, host `titan`; retained stderr identifies NVIDIA TITAN Xp and single
precision. Proxy throughput is 296.715 s/M steps. The opportunity-matched
scenarios above would cost **12.54/90.73/668.49 GPU-hours for three histories**
respectively, about 771.8 GPU-hours in total. These are historical same-driver
throughput projections, not new benchmarks; hardware, outputs, build and workload
can change them. No cost for an unbenchmarked toy system is invented.

A common fixed minimum duration would mean radically different chemical exposure:
1M steps predicts about 2,597/359/49 neighbor losses at Ea6/8/10 across the whole
system, before accounting for feedback. A common mechanical settling/check interval
may be useful, but is insufficient as a chemical/topological criterion. Use
barrier-dependent event exposure and explicit paths/returns/block sensitivity,
not a time floor or a fixed event total as automatic acceptance.

## Independence, recommendation and smallest next step

For one target barrier, r001/r002/r003 inherit three distinct original histories;
with independent future streams they remain a defensible three-history ensemble.
This does not prove unbiased independent equilibrium sampling. Shared preparation
can impart common bias; distinct seeds provide operational stream separation,
not mathematical independence. Across Ea conditions, descendants of the same
reference replica are paired/correlated. There are three parent families, not
nine independent original preparations. Branching each parent several times
cannot increase the independent-parent count. Analyze contrasts by parent and
retain replica-specific paths; subsequent dynamics may reduce but not automatically
erase cross-branch correlations.

The smallest next work item is a separately authorized, narrowly scoped restart/
planner/validator change and CPU tests described in [PROTOCOL.md](PROTOCOL.md).
Do not modify kernels or manually edit/copy accepted sidecars into apparent new
acceptances. Following that change, a separately approved capped replay smoke
and event-exposure pilot should validate the changed streams, microstate fidelity,
Ea-dependent finite-step behavior and absence of a material new structural shift.
Use an Ea4 transferred/reseeded control to distinguish restart from barrier
changes. Existing K1/S2 evidence makes transfer promising, but is insufficient
for automatic adoption of the three higher-Ea starts.

An illustrative screening target of 200 distinct-neighbor losses per history
would take approximately 0.077M/0.557M/4.103M steps and **0.019/0.138/1.015
GPU-hours for the three histories** at each barrier, about 1.17 GPU-hours total,
plus controls/startup/oracle overhead. This is a modest kinetic screen, only
0.2 losses per star, and cannot prove slow-topology mixing or equilibrium
invariance. Use adaptive capped batches; actual observed rates determine the
next batch. Inconclusive physics evidence stays inconclusive; neither this event
budget nor broad confidence intervals can qualify endpoints automatically.
A small matched-cadence/timestep or simpler coupled-sampler comparison may be
needed before a star-scale claim if a barrier-dependent discrepancy appears.

No GPU calculation, smoke, extension, transfer implementation, additional
acceptance, registry action or production preparation/launch occurred. All twelve
formal acceptances and 1,312 inherited preserved bindings remain unchanged.
[VALIDATION.md](VALIDATION.md) records CPU checks and reproducibility.
