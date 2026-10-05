# Associating-star equilibration and production plan

This document is the planning specification for the next associating-star
phase. P2 has implemented E1 conformational-equilibration infrastructure only;
E1 scientific equilibration lengths remain unvalidated. E2, topology analysis,
restart support, and new production simulations remain unimplemented:

```text
external star generator
    -> E1 conformational equilibration
    -> E2 chemical/topological equilibration
    -> validated restart bank
    -> long multipurpose production trajectories
    -> topology + percolation + diffusion + rheology + bond dynamics
```

## P3.0 — associating cutoff audit (CLOSED)

Before any E2 chemistry or star-production work changes `r_assoc`, P3.0 uses
only the dimer and K1 validation systems. This is intentionally separate from
the E1-validated star preparation workflow. The temporary associating FENE
force is topology-driven and remains evaluated to `R0`; neither the WCA force
cutoff nor its neighbor-list skin determines whether that force exists.
`r_assoc` instead defines the physical kinetic candidate region for both
formation and breaking, matching the current LAMMPS reference implementation.
Thus a stretched active bond outside `r_assoc` remains mechanically safe but
temporarily has zero break-transition probability.

The audit records radial tails, maximum active-bond distance, and the omitted
Metropolis break-propensity `F_miss`, rather than using only tail population.
It also runs the K1 `Ee={4,6,8}` and
`r_assoc={2^(1/6),1.15,1.20}` sensitivity matrix without changing the already
validated kinetic parameters. P3.0 simple-system results were inspected before
freezing the E2 cutoff. No production workflow is instrumented or changed by
this milestone.

The efficiency extension compares `r_assoc=2^(1/6)` with `1.25` under the
same K1 conditions and three matched seeds. It records wall time, chemistry
sweeps, total and mean candidate sticker pairs, event counts, and particle
timesteps per second. This is measurement only: candidate construction is not
optimized and the production default is unchanged. The resulting relative
wall-time/candidate-cost measurements are combined with deterministic
`F_miss` values at `Ee=8,12,16` in the P3.0 decision table documented in
`VALIDATION.md`. P3.0 is now closed: `r_assoc=1.25` is frozen as the
recommended/default E2 reaction cutoff for both creation and breaking. This is
a conservative choice for the intended range through `Ee=16`, not a claim of
mathematical uniqueness or global optimality. Temporary FENE mechanics remain
topology-based up to `R0=1.5`, independent of the WCA neighbor-list range.

### P3.1 — C1 E2 chemical/topological equilibration (CLOSED)

P3.1/C1 E2 is closed for `A=4`, `Narm=10`, `Nstars=1000`,
`rho_total=.85`, `rho_poly=.8`, `T=1`, `dt=.01`, `Ea=4`, `Ee=8`, `nu0=20`,
`Nevery=100`, `r_assoc=1.25`, and diagnostics every 1000 MD steps. Two
independently E1-equilibrated configurations (seeds 12001 and 12002) each ran
6,000,000 MD steps, or total E2 time 60,000.

Both replicas show stationary late-time chemistry with balanced creation and
break rates. Their bound fraction, inter-star bond count, largest-cluster
fraction, and distinct-neighbor mean degree agree closely. `L1` is slow and
strongly correlated but has nearly identical late-time means across replicas;
`L2` is also slow without a consistent secular drift. `N_intra` is noisy and
strongly correlated, consistent with a slow equilibrium observable rather than
a reproducible monotonic transient. The molecular network is nearly fully
connected, and sampled active bonds remain below `1.25` and well below
`R0=1.5`.

The validated C1 E2 duration is **6,000,000 MD steps at `dt=.01`**. This is a
conservative validated duration, not a demonstrated minimum. C5/C6 E2 remain
unvalidated; chemical restart-bank support and rigorous PBC
wrapping/percolation remain pending. The final permanent configuration and
active temporary bonds are written separately, but the current format cannot
reload temporary partner state; a chemically valid restart is required before
restart-bank construction or long production continuation.

### P3.2 — chemically valid restart support (CLOSED)

The previous temporary-bond listing has been replaced for continuation by an
explicit pair, `PREFIX.restart.lammpsdat` and `PREFIX.assoc_restart`. The
versioned sidecar stores the completed step, all chemistry settings and seed,
cumulative events, and canonical temporary sticker pairs. `--restart-prefix
PREFIX` reloads that pair and is intentionally incompatible with `--input`.
The loader fail-closes on malformed partners or state and verifies active FENE
distances below `R0`; force evaluation remains partner-topology based.

The UAMMD NVT RNG state cannot be serialized through the current API and is
re-seeded on reload. Consequently the restart boundary state/network is exact,
and chemistry retains its absolute-step hash schedule, but bitwise trajectory
continuation is not claimed. A short C1 GPU save/reload smoke recovered all
1,736 saved temporary-pair identities and continued with invariants intact.
This closes P3.2 but does not construct the production restart bank; C5/C6 E2
and rigorous wrapping/percolation remain pending.

## 1. Scientific motivation

A stationary bonded fraction alone does not certify equilibrium. The network
can retain slower topological memory in `N_intra`, `N_inter`, primary-loop count
`L1`, secondary-loop count `L2`, distinct-neighbor degree statistics,
cluster-size distribution, largest-cluster fraction, and wrapping/percolation
state.

The protocol must therefore distinguish:

1. conformational equilibration;
2. chemical equilibration;
3. topological equilibration;
4. statistical independence of production restarts.

The restart bank is intended to avoid repeating expensive equilibration before
long runs for topology, diffusion, `G(t)`, bond dynamics, and
percolation/finite-size scaling.

## 2. E1 — conformational equilibration with chemistry disabled

E1 starts from star configurations generated externally by the user's C++ star
generator. Dynamic sticker association is disabled: stickers behave only as
terminal KG beads, while the permanent star topology remains active. E1 should
follow the philosophy of `examples/KG/kg_uammd_equilibrate.cu`:

1. DPD + FENE with displacement limiting;
2. DPD + FENE without a displacement cap;
3. progressive DPD push-off;
4. final DPD relaxation/hold at the final Stage-3 conservative amplitude;
5. full WCA + FENE with Langevin NVT.

The current default Stage-4 duration must not be assumed sufficient for every
arm length. Future E1 validation should inspect energy, pressure, temperature,
maximum permanent-bond extension, star `Rg^2`, and useful arm/end-to-center
size measures, especially for `N=20` and `N=40`. E1 output is a chemically
unassociated, conformationally equilibrated configuration suitable for E2.

P2 provides `kg_assoc_star_equilibrate`, which performs the S0 topology audit,
the four stages above, and infrequent PBC-safe Stage-4 conformation diagnostics.
It writes a permanent-topology-only LAMMPS data file. This is implementation
infrastructure, not evidence that any C1--C6 condition is scientifically
equilibrated.

Intermittent failures have been observed on entry to Stage 4 WCA, including at
reduced timestep. P2.1a adds CPU-side transition diagnostics after each Stage-3
loop and immediately before Stage 4 to identify the state presented to WCA.
It does not change the equilibration protocol or claim that the failure is
solved.

P2.1b isolates Stage-4 construction, attachment, first thermo/conformation
evaluation, and first NVT step with explicit CUDA checkpoints. The reproducible
C1 seed `12004` failure and passing control seed `12001` are diagnostic cases,
not a protocol change. P2.1b establishes that the Stage-3 state is geometrically
normal and that initial WCA/FENE thermo and the first NVT step are finite, but a
permanent FENE bond can exceed `R0` within roughly 10--20 WCA steps. This is a
hot-transition failure, not evidence of a severe Stage-3 overlap.

P2.1c adds a configurable Stage-3b final DPD relaxation/hold at the final
Stage-3 conservative amplitude (currently 1000), retaining DPD target
temperature 1 and gamma 4.5 before WCA is enabled. Its conservative default is
20,000 steps with transition diagnostics every 500 steps. The measured
temperature remains above 3 before WCA, so this is documented as relaxation of
locally compressed configurations rather than cooling. For seed `12003`, 1,000
steps failed the promotion test, while 5,000, 10,000, and 20,000 passed; 20,000
was selected conservatively because the local geometry is substantially safer.
The promotion test remains 1,000 steps at each of `dt=0.002`, `0.005`, and
`0.010`, in that order. DPD and WCA timesteps can be set separately. Final E1
acceptance requires a 5/5 CUDA robustness test for seeds `12001--12005` at
20,000 Stage-3b steps; it is pending on hosts without a CUDA device.

Transition diagnostics include the minimum permanent-bond length and its atom
IDs, using the existing permanent-bond topology. No automatic minimum-bond
threshold is introduced.

**Future E2 chemistry note:**

> Active associative bonds may extend beyond the current chemical candidate
> cutoff r_assoc ≈ 1.12. In E2, verify that break eligibility for already-active
> bonds is not lost when bond length exceeds the formation-search cutoff.
> Formation and break neighbor criteria may need to be separated.

### P2.1d — staged WCA-strength transition preparation

Direct DPD-to-full-WCA activation remains non-robust even with
`stage3b=20000`. In the five-seed check, seed `12005` entered Stage 4 with
`closest_pair_distance=0.70715658846` for permanent-bond IDs `23782,23783`
and failed after 17 steps at `dt=0.002` when that same permanent bond reached
or exceeded FENE `R0`. Seed `12003` showed the same initially compressed-bond
mechanism. The issue is the abrupt WCA-strength transition, not chemistry.

P2.1d therefore adds the optional `--wca-ramp` numerical preparation protocol.
It uses the existing WCA implementation at fixed `dt=0.002` with epsilon
`0.01, 0.03, 0.10, 0.30, 1.00`, defaulting to 500 steps per epsilon via
`--wca-ramp-steps 500`. It leaves sigma, FENE parameters, DPD parameters, and
the target temperature unchanged. Each epsilon segment has before/after
transition and thermo diagnostics and fails closed on CUDA errors, non-finite
state/thermo, or permanent-bond length at or above `R0`.

After the ramp completes its 500 steps at full epsilon and `dt=0.002`, the
promotion test runs 1,000 steps at `dt=0.005` and 1,000 at `dt=0.010`; there
is no second 1,000-step `dt=0.002` block in ramp mode. This is a numerical
transition-preparation protocol, not scientific equilibration. Seeds `12003`
and `12005` passed first, followed by the broader five-seed validation
`12001--12005`; P2.1 is closed. Ramp tuning is not automated.

### P2.2 — long C1 conformational equilibration and stationarity

P2.1 is closed for the C1 transition protocol: the final DPD relaxation/hold
uses 20,000 steps, the WCA epsilon ramp is
`0.01, 0.03, 0.10, 0.30, 1.00` at `dt=0.002` with 500 steps per level, and
the subsequent promotion is 1,000 steps at `dt=0.005` followed by 1,000 steps
at `dt=0.010`; seeds `12001--12005` passed. P2.2 does not change that
transition.

P2.2 measures conformational equilibration with chemistry disabled. The
validated C1 condition is `A=4`, `Narm=10`, `Nstars=1000`, `rho_total=0.85`,
`rho_poly=0.8`. Its preparation is 20,000 Stage-3b final DPD relaxation/hold
steps, WCA epsilon `0.01, 0.03, 0.10, 0.30, 1.00` with 500 steps per level at
`dt=0.002`, then 1,000 steps at `dt=0.005` and 1,000 steps at `dt=0.010`,
followed by full-WCA Stage 4 at `dt=0.01`. Two independent runs, seeds
`12001` and `12002`, each used 2,000,000 Stage-4 steps. The normal long-run
path writes an E1 configuration; promotion-test mode is not used because it
intentionally writes no E1 configuration.

The long-run diagnostics record step, time, bonded/nonbonded/kinetic/total
energy, temperature, pressure, `mean_rg2`, `mean_center_terminal_r2`,
`min_permanent_bond`, and `max_permanent_bond`.
`analyze_e1_stationarity.py` reports first/second-half means and relative
differences, second-half linear trends, equal contiguous block means, and
trajectory-wide permanent-bond extrema. It estimates integrated
autocorrelation times for the two conformational observables with an
initial-positive-sequence autocorrelation sum and reports insufficient or
nonuniform data explicitly. These are diagnostic metrics only; no automatic
equilibrium stopping criterion is introduced.

The latter portions of both replicas were conformationally stationary and
agreed closely:

| seed | second-half mean `Rg^2` | second-half mean center-terminal `r^2` | `tau_int(Rg^2)` | `tau_int(center-terminal r^2)` |
|---:|---:|---:|---:|---:|
| 12001 | 7.013572 | 15.587541 | 156.9 | 88.2 |
| 12002 | 7.012661 | 15.597365 | 132.9 | 89.7 |

C1 is therefore conformationally stationary by the latter part of the runs.
The conservative validated E1 duration for `Narm=10` is 2,000,000 Stage-4
steps; this is not claimed to be the minimum necessary duration. Chemistry,
restart support, topology analysis, percolation, rheology, MSD, production
correlation, and finite-size scaling remain outside P2.2.

### P2.3 — longer-arm E1 conformational equilibration

The C1 duration is not assumed sufficient for longer arms. Validate:

| case | generated input | condition |
|---|---|---|
| C5 | `systems/generated/Stars_NA4N20C1000rho0.85rhopoly0.8.lammpsdat` | `A=4`, `Narm=20`, `rho_poly=0.8`, `rho_total=0.85` |
| C6 | `systems/generated/Stars_NA4N40C1000rho0.85rhopoly0.8.lammpsdat` | `A=4`, `Narm=40`, `rho_poly=0.8`, `rho_total=0.85` |

Use the same validated transition protocol as C1. Start with one seed per chain
length and run Stage 4 long enough to assess stationarity, not merely numerical
stability. Use `analyze_e1_stationarity.py` to compare `mean_rg2`,
`mean_center_terminal_r2`, trends, block means, and autocorrelation times;
extend if needed. Only after stationarity is established should a second seed
confirm each chain length. The C5 and C6 closures are recorded below.

#### C5 closure: `A=4`, `Narm=20`

C5 uses `Nstars=1000`, `rho_total=0.85`, `rho_poly=0.8`, and chemistry
disabled. Seeds `12001` and `12002` each used the validated C1 transition
protocol, 2,000,000 Stage-4 steps at `dt=0.01`, and conformation sampling every
1,000 steps.

| seed | observable | first-half mean | second-half mean | relative difference | second-half slope | `tau_int` | effective samples |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12001 | `mean_rg2` | 14.2613032106 | 14.3777463343 | 0.00809884393619 | 3.45392227673e-08 | 706.193851464 | 14.1604178217 |
| 12001 | `mean_center_terminal_r2` | 32.5487535953 | 32.8527665215 | 0.00925379985913 | 2.97437458605e-07 | 505.007037985 | 19.8017042292 |
| 12002 | `mean_rg2` | 14.2182914157 | 14.3543360763 | 0.00947760034804 | 1.36606856841e-07 | 523.997165487 | 19.0840726983 |
| 12002 | `mean_center_terminal_r2` | 32.5165979833 | 32.7764793097 | 0.00792889693703 | 3.65643605274e-06 | 424.028863635 | 23.5833002361 |

The five block means were:

```text
seed 12001 mean_rg2:                 14.0365885489 14.4095719505 14.3818624071 14.3948195411 14.3747814147
seed 12001 mean_center_terminal_r2:  32.0814595689 32.8508741005 32.8456992120 32.8928080720 32.8329593386
seed 12002 mean_rg2:                 14.0666189155 14.3006004453 14.3739951715 14.3349072718 14.3554469258
seed 12002 mean_center_terminal_r2:  32.1696308543 32.7452689870 32.7629138772 32.7691885319 32.7856909820
```

Both replicas show an initial conformational transient, most visible in the
first block, followed by a stationary plateau. The later blocks are
consistent, second-half slopes are negligible compared with equilibrium
fluctuations, and the independent replicas agree closely in their late-time
means. Temperature and pressure are stationary in both runs, and permanent
bond lengths remain safely below FENE `R0=1.5`. C5 autocorrelation times are
substantially larger than for C1 `Narm=10`, but 2,000,000 Stage-4 steps is
sufficient to reach a stationary final state for C5.

**P2.3 status:** C5 / `Narm=20`: **closed**. Adopt 2,000,000 Stage-4 steps at
`dt=0.01` as the conservative validated E1 duration for `Narm=20`; this is
not a demonstrated minimum. C6 was then validated independently below; the C5
duration was not assumed sufficient.

#### C6 closure: `A=4`, `Narm=40`

C6 uses `Nstars=1000`, `rho_total=0.85`, `rho_poly=0.8`, and chemistry
disabled. Seeds `12001` and `12002` each used the validated E1 transition
protocol, 8,000,000 Stage-4 steps at `dt=0.01`, and conformation sampling every
1,000 steps.

| seed | observable | first-half mean | second-half mean | relative difference | second-half slope | `tau_int` | effective samples |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12001 | `mean_rg2` | 28.9209002098 | 29.4257261728 | 0.0171559389912 | 1.60550922204e-07 | 3363.95980836 | 11.890748486 |
| 12001 | `mean_center_terminal_r2` | 67.1824147446 | 68.1868406427 | 0.01473049475 | -1.29821673912e-06 | 2847.62106895 | 14.046812771 |
| 12002 | `mean_rg2` | 28.9946447173 | 29.4188962908 | 0.0144210567686 | 6.49197033686e-06 | 3667.47506737 | 10.9066862797 |
| 12002 | `mean_center_terminal_r2` | 67.3047573923 | 68.28162656 | 0.0143064718426 | -1.68960148121e-06 | 3004.27930445 | 13.3143412928 |

The five block means were:

```text
seed 12001 mean_rg2:                 28.2436603912 29.2971750134 29.5511345185 29.3024977243 29.4720983091
seed 12001 mean_center_terminal_r2:  65.8027504663 67.9746402867 68.5253564928 67.8238906915 68.2965005308
seed 12002 mean_rg2:                 28.2497643859 29.4110137467 29.3946684203 29.4802754923 29.4981304748
seed 12002 mean_center_terminal_r2:  65.7626446804 68.2615963060 68.2309644967 68.4506343997 68.2601199979
```

Both replicas show a pronounced initial conformational transient, especially
in the first block. The subsequent blocks are consistent with a stationary
plateau, the second-half slopes are small compared with equilibrium
fluctuations, and the independent replicas agree very closely in their
late-time means. Temperature and pressure are stationary in both runs, and
permanent-bond lengths remain safely below FENE `R0=1.5`. C6 autocorrelation
times are much larger than for `Narm=20`; effective sample counts are modest,
but this does not prevent establishing a reproducible stationary regime for
the final configurations.

Adopt 8,000,000 Stage-4 steps at `dt=0.01` as the conservative validated E1
duration for `Narm=40`; this is not a demonstrated minimum.

**P2.3 closure:** C5 / `Narm=20`: **closed**; C6 / `Narm=40`: **closed**;
P2.3: **closed**. The validated E1 Stage-4 durations are:

```text
Narm=10 -> 2,000,000 steps
Narm=20 -> 2,000,000 steps
Narm=40 -> 8,000,000 steps
```

These three validated points do not establish a general scaling law. They only
support the qualitative observation that conformational relaxation becomes
substantially slower as arm length increases.

## 3. E2 — chemical and topological equilibration

E2 starts from E1 output and activates the validated reversible-association
dynamics from S1/S2. The canonical chemistry is currently:

| Parameter | Value |
|---|---:|
| `T` | 1 |
| `dt` | 0.01 |
| `Ea` | 4, unless intentionally varied |
| `nu0` | 20 |
| `Nevery` | 100 |

`Nevery=100` is the S2 production cost/accuracy compromise: equilibrium bonded
fraction is sufficiently converged, while fine lifetime statistics retain
finite-cadence bias. E2 should initially start from `N_assoc=0`, making the
initial chemical state explicit.

At minimum, E2 time series should include bonded-sticker fraction, `N_assoc`,
`N_intra`, `N_inter`, `L1`, `L2`, distinct intermolecular neighbors per star,
degree-distribution moments, cluster-size distribution, largest-cluster
fraction, and wrapping indicators once implemented.

No automatic “equilibrated” stopping criterion is specified yet. First collect
the time series and determine empirically which observable is slowest.

## 4. Equilibration diagnostics

For each relevant observable `A(t)`, future analysis should estimate drift and
stationarity, first-half versus second-half consistency, the autocorrelation
function, integrated autocorrelation time `tau_int`, and effective sample size.
Define conceptually:

```text
tau_slow = max(tau_int over the slow topological observables)
```

The production boundary should be set only after all monitored observables are
stationary, slow topological observables have decorrelated, and different
initial-condition histories agree within uncertainty. Multipliers such as
`5--10 tau_slow` are working hypotheses to test, not frozen rules.

## 5. Strong equilibration validation

For selected conditions near important network regimes, compare deliberately
different histories:

- initially unassociated network;
- strongly associated or preconnected restart;
- independent equilibrated restart.

The histories should converge to the same stationary distributions, within
uncertainty, for bonded fraction, `N_intra`/`N_inter`, `L1`/`L2`, degree
statistics, largest-cluster fraction, and wrapping probability. This test is
intended to expose metastability and protocol-dependent topology.

## 6. Restart-bank design

A scientifically valid restart is more than a coordinate file. It must preserve
positions, velocities, simulation box, atom and molecule identities, permanent
KG topology, active associative bonds, PBC image metadata for associative bonds
once wrapping support exists, simulation parameters, reproducibility-relevant
RNG/provenance information, source Git SHA, source seed, absolute timestep and
simulation time, checksums, and validation metadata.

Associative bonds must remain distinguishable from permanent KG bonds on reload;
they must not be merged into the permanent topology. A provisional layout is:

```text
CONDITION.restart.lammpsdat
CONDITION.restart.assoc
CONDITION.restart.json
```

This naming/layout is provisional until implementation. The eventual production
executable must restore both particle state and associative-network state
without resetting `N_assoc` to zero.

## 7. Independent restart selection

Frequent lightweight topology samples may be correlated and should be handled
with autocorrelation or blocking analysis. Full restart snapshots intended as
independent production seeds must be much more widely separated. A provisional
spacing is of order `5--10 tau_slow`, pending measurement of `tau_slow`.
The eventual target is several statistically independent restarts per main
thermodynamic condition; roughly 5--10 is a planning number, not a hard
requirement.

## 8. Multipurpose production trajectories

Long MD trajectories should be reused for multiple observables rather than
duplicated. One production trajectory should support topology, cluster
statistics, percolation, MSD/diffusion, bond survival and lifetime statistics,
hopping/walking analysis, and rheology.

For rheology, `G(t)` should use the existing Correlator infrastructure,
following `kg_uammd`; raw stress tensors need not be dumped continuously.
Different observables may use different output cadences, and expensive
full-particle snapshots should remain sparse.

## 9. Offline-first topology philosophy

Topology analysis should be primarily post-processing to preserve MD efficiency.
Runtime should record only the minimal information needed to reconstruct the
network. Intended offline observables are self versus inter bonds,
distinct-neighbor degree, `P(k)`, `L1`, `L2`, connected components,
cluster-size distribution, largest-cluster fraction, Molloy--Reed diagnostics,
and wrapping in x/y/z/any/all directions.

The only extra runtime metadata currently anticipated for rigorous wrapping is
PBC image/winding information associated with each newly created associative
bond. This is a future implementation item, not part of this commit.

## 10. Percolation strategy

The primary percolation definition is periodic wrapping, or nonzero winding, of
the molecular network. The historical comparison is largest-cluster fraction
`> 0.4`. That 40% rule remains only a historical thesis proxy, not the rigorous
definition.

Quantitative critical-point estimates should use finite-size scaling of
wrapping probability and related cluster observables, including:

- `P_wrap`;
- largest-cluster fraction;
- finite-cluster mean size or susceptibility;
- cluster-size distribution;
- dimensionless moment ratios or Binder-like observables.

Potential scientific controls are `Ee/T`, `rho_m`, arm length `N`, and arm
functionality `A`. Once convergence is established, `Ea`, `nu0`, and `Nevery`
are kinetic/numerical controls, not equilibrium phase-diagram coordinates.

## 11. Development / pipeline-validation matrix

This is a development and pipeline-validation matrix, not the final paper or
finite-size-scaling campaign. Use `Nstars = 1000` initially.

| ID | `A` | `N` | `rho_m` | `rho_total` | `Ee` | `Ea` | Purpose |
|---|---:|---:|---:|---:|---:|---:|---|
| C1 | 4 | 10 | 0.8 | 0.85 | 8 | 4 | canonical strongly associated case |
| C2 | 4 | 10 | 0.8 | 0.85 | 4 | 4 | weaker association |
| C3 | 4 | 10 | 0.4 | 0.85 | 6 | 4 | intermediate-connectivity regime |
| C4 | 4 | 10 | 0.2 | 0.85 | 8 | 4 | dilute / self-bond-rich regime |
| C5 | 4 | 20 | 0.8 | 0.85 | 8 | 4 | arm-length effect |
| C6 | 4 | 40 | 0.8 | 0.85 | 8 | 4 | long-arm equilibration stress test |

## 12. Near-term implementation order

These are planning labels for this phase, not externally established
milestones:

1. **P1** — planning document only;
2. **P2** — E1 star conformational equilibration infrastructure;
3. **P3** — E2 chemical/topological equilibration infrastructure;
4. **P4** — restart format and reload validation;
5. **P5** — offline topology analyzer and autocorrelation diagnostics;
6. **P6** — validate the full pipeline on C1;
7. **P7** — extend to C2--C6;
8. **P8** — define the finite-size-scaling campaign;
9. **P9** — long multipurpose production trajectories.

## 13. Explicit exclusions for this commit

This documentation commit does not modify `kg_assoc_stars.cu`,
`kg_uammd_equilibrate.cu`, `examples/KG/*`, or `src/*`. It does not implement
wrapping, topology analysis, restart support, E1, or E2; launch simulations;
start finite-size scaling; or change S2 validation results.
