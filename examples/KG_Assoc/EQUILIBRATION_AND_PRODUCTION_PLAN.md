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
transition-preparation protocol, not scientific equilibration. First validate
only seeds `12003` and `12005`; if both pass, broader five-seed validation is
the next manual step. Ramp tuning is not automated.

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
