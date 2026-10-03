# KG_Assoc validation record

This record contains only executed and inspected checks. Generated `.events` and
`.summary` files are intentionally not versioned.

## S0: star-input import and permanent-topology audit

Starting repository SHA: `227893355f30662ff49e6ab09f3f4d4cf12e70fa`.

The S0 audit is a host-side import and graph-validation tool only; it does not
create reversible bonds or run MD. It reuses `examples/KG/kg_lammps_io.cuh`.
That parser retains LAMMPS atom and bond IDs as 1-based values, so the audit
checks each bond ID before explicitly converting it to its zero-based vector
index. The audited input uses `Atoms # bond` records with trailing image flags;
the existing parser reads the required `id molecule type x y z` fields and
retains molecule/type metadata by atom ID. It assumes contiguous atom IDs from
1 through the header atom count and orthorhombic `xlo/xhi`, `ylo/yhi`, and
`zlo/zhi` bounds.

The affected executable was rebuilt from scratch and checked with:

```bash
rm -f examples/KG_Assoc/kg_assoc_star_audit
make -C examples/KG_Assoc kg_assoc_star_audit
./examples/KG_Assoc/kg_assoc_star_audit --self-test
./examples/KG_Assoc/kg_assoc_star_audit \
  --input examples/KG/Stars/Stars_NA4N10C1000rho0.85rhopoly0.8.equilibrated.lammpsdat \
  --arms 4 --narm 10
```

The real externally generated, equilibrated input remains untracked. Its audit
reported:

| Quantity | Observed |
|---|---:|
| Total atoms | 43563 |
| Polymer beads | 41000 |
| Stickers | 4000 |
| Solvent beads | 2563 |
| Stars | 1000 |
| Permanent bonds | 40000 |
| Box lengths | 37.145, 37.145, 37.145 |
| Volume | 51250.8518236 |
| Total bead density | 0.849995628364 |
| Polymer bead density | 0.799986703462 |

The program ended with `STAR_TOPOLOGY_AUDIT PASS`. It validated one center of
degree four per molecule, four type-2 terminal stickers, type-1 non-terminals,
four independent arms of graph distance ten, 41 beads/star, 40 bonds/star,
and all global type/molecule/bond constraints.

`--self-test` also executed graph-level rejection cases for a wrong terminal
sticker count, wrong arm length, permanent inter-star bond, bond involving
solvent, invalid zero 1-based bond ID, non-terminal type-2 bead, and
cycle/extra permanent bond. It ended with
`STAR_TOPOLOGY_AUDIT SELF_TEST PASS malformed graph rejections`.

Files added: `kg_assoc_star_topology.cuh`, `kg_assoc_star_audit.cu`.
Files changed: `Makefile`, this validation record. Final repository SHA:
`227893355f30662ff49e6ab09f3f4d4cf12e70fa`. **S0: PASS.**

## Analytical/self-test

```bash
make -C examples/KG_Assoc clean
make -C examples/KG_Assoc
./examples/KG_Assoc/kg_assoc_dimer --self-test
```

Result: `SELF_TEST PASS actual-interactor and static-kinetics regressions`.
The test directly exercises the interactor energy expression at `r=0.8, r*,
1.1, 1.2`, verifies `E(r*)=-Ee`, the `-DeltaEe` energy shift, force
independence from `Ee`, numerical energy derivatives, finite behavior at
`r=1.49 < R0=1.5`, and rejection at `r=R0`. It also checks two-state detailed
balance, reciprocal state/event alternation, and the kinetic cutoff semantics.

## D0: fixed-distance kinetics (CPU-only)

The primary run was:

```bash
./examples/KG_Assoc/kg_assoc_dimer --static --distance 0.960897198959 \
  --steps 1000000 --dt 0.005 --temperature 1 --Ee 2 --Ea 2 --nu0 20 \
  --Nevery 10 --r-assoc 1.122462048 --seed 1234 --output static_rstar
```

This is 100,000 kinetic sweeps at `r=r*`. Observed versus exact Markov-chain
theory was:

| Quantity | Observed | Theory | Relative difference |
|---|---:|---:|---:|
| `Pf` | 0.1259124 | 0.1265770 | -0.53% |
| `Pb` | 0.0172496 | 0.0171303 | +0.70% |
| Bound fraction | 0.879450 | 0.880797 | -0.15% |
| Mean free sweeps | 7.9420 | 7.9003 | +0.53% |
| Mean bound sweeps | 57.9011 | 58.3760 | -0.81% |

There were 1,518 complete free and 1,517 complete bound episodes; terminal
episodes were censored. A second executed `r=1.1` run had only 18 creation and
18 break events, so its 29--38% deviations in rare-event free-state measures
are consistent with limited counting statistics, not used as a precision test.

Cutoff regression, executed with an initially bound dimer:

```bash
./examples/KG_Assoc/kg_assoc_dimer --static --initial-bound --distance 1.20 \
  --r-assoc 1.122462048 --steps 100000 --Nevery 10 --output static_cutoff_bound
```

For 10,000 sweeps (`r_assoc < r < R0`), creations and breaks were both zero and
the bound fraction was exactly one. This confirms the LAMMPS-equivalent rule:
the pair remains mechanically bound but has no breaking candidate outside the
chemical cutoff. **D0: PASS.**

## D1: dynamic dimer

Executed dynamic outputs used 2,000,000 MD steps and `Nevery=10` (200,000
kinetic updates), as recorded by their summaries/event timesteps. The retained
run names encode the varied parameters; the generated dynamic summaries did
not retain full argv or seed, so those values are not reconstructed here.

The output-evidenced invocation forms were:

```bash
./examples/KG_Assoc/kg_assoc_dimer --steps 2000000 --Nevery 10 \
  --Ee 2 --Ea 2 --output dyn_Ee2_Ea2
./examples/KG_Assoc/kg_assoc_dimer --steps 2000000 --Nevery 10 \
  --Ee 4 --Ea 2 --output dyn_Ee4_Ea2
./examples/KG_Assoc/kg_assoc_dimer --steps 2000000 --Nevery 10 \
  --Ee 2 --Ea 4 --output dyn_Ee2_Ea4
```

These record the options evidenced by the output names and counters; they are
not claimed to be complete historical argv transcripts.

| Output | `Ee` | `Ea` | Creations / breaks | Bound fraction | Mean bond distance |
|---|---:|---:|---:|---:|---:|
| `dyn_Ee2_Ea2` | 2 | 2 | 100 / 100 | 0.011070 | 0.9700603 |
| `dyn_Ee4_Ea2` | 4 | 2 | 203 / 203 | 0.076465 | 0.9701920 |
| `dyn_Ee2_Ea4` | 2 | 4 | 15 / 15 | 0.013450 | 0.9695530 |

At fixed `Ea=2`, use the two-state population odds rather than raw bound
fractions: `p_bound/p_free` was 0.0111939 at `Ee=2` and 0.0827960 at `Ee=4`.
Their ratio is 7.39652, versus `exp((4-2)/T)=exp(2)=7.38906` at `T=1`
(+0.10%). This is the dynamic `e^(DeltaEe/T)` population-ratio check.

The `Ea=4` run has only 15 transitions and is a smoke-level equilibrium check,
not a precise lifetime comparison. Dynamic trajectories also depend on WCA
encounters and diffusion, unlike D0; no claim of bitwise identity or a
production-rate estimate is made. **D1: PASS** for the executed dimer smoke
and population-ratio checks.

## K1 chemistry-cadence validation

This large-N study used `Nparticles=32768`, `rho=.05`, `T=1`, `dt=.005`,
`Ea=4`, `Ee=4`, `nu0=20`, and 1,000,000 production steps. The tested cadence
values were `Nevery=10, 20, 50, 100, 200`.

For a chemistry interval `delta_t_chem = Nevery * dt`, the finite-step attempt
probability and attempt rate are

```text
q = 1 - exp(-nu0 * exp(-Ea / T) * delta_t_chem)
attempt_rate = q / delta_t_chem
kf_over_attempt_rate = kf_event / attempt_rate
kb_over_attempt_rate = kb_event / attempt_rate
```

The analyzer recomputed the following values from the existing state files:

| Nevery | kf_event | kb_event | Keq_event | Keq_direct | attempt_rate | kf/attempt_rate | kb/attempt_rate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.10412056 | 0.04000258 | 2.60284635 | 2.60724712 | 0.36297854 | 0.28685046 | 0.11020645 |
| 20 | 0.10316503 | 0.03955188 | 2.60834718 | 2.61157971 | 0.35968470 | 0.28682074 | 0.10996264 |
| 50 | 0.10025815 | 0.03844315 | 2.60795856 | 2.61308558 | 0.35004015 | 0.28641899 | 0.10982498 |
| 100 | 0.09604601 | 0.03678649 | 2.61090418 | 2.61113737 | 0.33472414 | 0.28694079 | 0.10990093 |
| 200 | 0.08795005 | 0.03325300 | 2.64487537 | 2.65200896 | 0.30671408 | 0.28674931 | 0.10841695 |

`Nevery=10, 20, 50, 100` form an essentially converged plateau in both
equilibrium estimators around `Keq=2.61`. The normalized forward rate is
essentially cadence-independent over the full range. The normalized backward
rate is stable through `Nevery=100`, then decreases slightly at 200; the two
equilibrium estimators rise by about 1.5% at that cadence. This is consistent
with coarse chemistry sampling missing some short-lived scission-eligible
visits inside `r_assoc`, because the current LAMMPS-equivalent rule permits a
bound pair to attempt breaking only while `r < r_assoc`. It is an observed,
mechanistically consistent explanation, not a mathematical proof.

**Cadence selection: `Nevery=100`.** It lies in the converged plateau while
being substantially cheaper than more frequent chemistry updates.

## K1 attempt-frequency validation

This sweep used `Nparticles=32768`, `rho=.05`, `T=1`, `dt=.005`, `Ea=4`,
`Ee=4`, `Nevery=100`, 10,000 push-off steps, and 1,000,000 production steps.
The tested attempt frequencies were `nu0=1, 5, 10, 20, 40, 80`.

For `delta_t_chem = Nevery * dt`, results are normalized by the finite-step
attempt rate

```text
attempt_rate = [1 - exp(-nu0 * exp(-Ea / T) * delta_t_chem)] / delta_t_chem
```

| nu0 | attempt rate | kf/attempt rate | kb/attempt rate | Keq_event | Keq_direct |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.01823203 | 0.28407465 | 0.10883294 | 2.61018991 | 2.62265844 |
| 5 | 0.08951319 | 0.28712050 | 0.10956651 | 2.62051325 | 2.63077671 |
| 10 | 0.17502008 | 0.28683658 | 0.10982789 | 2.61169171 | 2.61779028 |
| 20 | 0.33472414 | 0.28694079 | 0.10990093 | 2.61090418 | 2.61113737 |
| 40 | 0.61342815 | 0.28617245 | 0.10978480 | 2.60666738 | 2.61409046 |
| 80 | 1.03870926 | 0.28673440 | 0.10966855 | 2.61455463 | 2.61538826 |

Varying `nu0` by a factor of 80 leaves the equilibrium estimators essentially
unchanged. Both normalized rates collapse closely, showing that `nu0` changes
the kinetic timescale without materially changing equilibrium over this range.
The agreement also validates the finite-step `1-exp(-x)` probability outside
the strictly linear `q≈x` regime. The `nu0=1` point has fewer events, hence
somewhat noisier direct-equilibrium statistics, but remains consistent with
the same behavior.

## K1 density validation

This sweep used `Nparticles=32768`, `nu0=20`, `T=1`, `dt=.005`, `Ea=4`,
`Ee=4`, `Nevery=100`, 10,000 push-off steps, and 1,000,000 production steps.

| rho | kf_event | kb_event | kf/attempt rate | kb/attempt rate | Keq_event | Keq_direct |
|---:|---:|---:|---:|---:|---:|---:|
| 0.025 | 0.09275978 | 0.03695000 | 0.27712306 | 0.11038940 | 2.51041368 | 2.50593768 |
| 0.05 | 0.09604601 | 0.03678649 | 0.28694079 | 0.10990093 | 2.61090418 | 2.61113737 |
| 0.10 | 0.10291174 | 0.03647331 | 0.30745239 | 0.10896527 | 2.82156310 | 2.82490854 |
| 0.20 | 0.11996749 | 0.03590049 | 0.35840704 | 0.10725397 | 3.34166697 | 3.34115629 |

The density dependence is real and systematic: the normalized forward rate
increases strongly with `rho`, whereas the normalized backward rate decreases
only weakly. Consequently, the concentration-based equilibrium quotient rises
from about 2.51 at `rho=.025` to about 3.34 at `rho=.20`. `Keq_event` and
`Keq_direct` agree closely at every density, so this is not an estimator
inconsistency. It is consistent with density-dependent spatial correlations
and encounter statistics from WCA interactions and the finite reaction region
`r < r_assoc`, not evidence of detailed-balance violation or a derivation of
activity coefficients.

The two sweeps distinguish the controls: `nu0` changes kinetics while leaving
equilibrium nearly invariant, whereas `rho` changes the measured
concentration quotient through local structure and encounter statistics.

## K1 density--bond-energy validation

The completed rho x Ee grid used `Nparticles=32768`, `T=1`, `dt=.005`,
`Ea=4`, `nu0=20`, `Nevery=100`, 10,000 push-off steps, and 1,000,000
production steps. It covered `rho = .025, .05, .10, .20` and
`Ee = 2, 4, 6, 8`. For each density, ordinary least squares was applied to
the four points in `ln(Keq)` versus `Ee`:

```text
ln Keq_event  = slope_event  * Ee + intercept_event
ln Keq_direct = slope_direct * Ee + intercept_direct
```

| rho | slope_event | intercept_event | slope_direct | intercept_direct |
|---:|---:|---:|---:|---:|
| 0.025 | 1.0001594860614984 | -3.0790039325611183 | 1.0025413755490662 | -3.0916112863374394 |
| 0.05  | 1.0021062802892722 | -3.0493665102625087 | 1.0023667221541834 | -3.050123851983667 |
| 0.10  | 0.9998182348561215 | -2.9620421016586302 | 0.9994143941773397 | -2.958617426526996 |
| 0.20  | 1.0012722852267193 | -2.799185039223762 | 1.0022814481914666 | -2.802322363403988 |

At `T=1`, all slopes remain extremely close to the expected Boltzmann slope
of one. Thus, over this tested range,

```text
ln Keq(rho, Ee) ~= Ee / T + C(rho)
Keq(rho, Ee) ~= A(rho) * exp(Ee / T),  A(rho) = exp(C(rho))
```

`Ee` controls the expected Boltzmann dependence, while density mainly changes
the intercept/prefactor. Event-based and population-based estimators remain
mutually consistent across the grid, supporting detailed-balance consistency
of the algorithm. The density dependence is that of a concentration-based
quotient in an interacting, non-ideal fluid; it is not evidence against
microscopic reversibility. The event-fit intercepts give descriptive
prefactors of approximately `A=.046, .0474, .0518, .0608` at increasing
density, respectively. These values are not proposed as a universal scaling
law for the intercept versus density.

The largest `exposure_relative_difference` occurs at the strongly bonded,
highest-density point, `rho=.20, Ee=8`, at approximately `3.62e-3`, compared
with typical values near `5e-5` elsewhere. This remains small, does not spoil
the close `Keq_event`/`Keq_direct` agreement, and is retained as a diagnostic
of the most extreme state rather than a validity failure.

## K1 validation status

The K1 associating-particle implementation has now been checked through static
dimer detailed balance; dynamic dimer equilibrium and kinetics; small-N
historical reference behavior; large-N size convergence; `Ee` dependence;
separation of `Ea` kinetics from equilibrium; chemistry cadence `Nevery`;
attempt frequency `nu0`; density `rho`; and combined `rho x Ee` behavior.

K1 is sufficiently validated to proceed to the full associating-star system.
This status covers the K1 chemistry implementation and its coupling to the
simple associating fluid, not the full polymer-network or rheology pipeline.
