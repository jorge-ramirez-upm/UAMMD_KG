# Associating-star equilibration and production plan

This document is the planning specification for the next associating-star
phase. It defines a reusable pipeline, without implementing E1, E2, topology
analysis, restart support, or new simulations:

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
4. full WCA + FENE with Langevin NVT.

The current default Stage-4 duration must not be assumed sufficient for every
arm length. Future E1 validation should inspect energy, pressure, temperature,
maximum permanent-bond extension, star `Rg^2`, and useful arm/end-to-center
size measures, especially for `N=20` and `N=40`. E1 output is a chemically
unassociated, conformationally equilibrated configuration suitable for E2.

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
