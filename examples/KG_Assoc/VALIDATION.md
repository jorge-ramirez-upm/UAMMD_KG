# KG_Assoc validation record

This record contains only executed and inspected checks. Generated `.events` and
`.summary` files are intentionally not versioned.

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
