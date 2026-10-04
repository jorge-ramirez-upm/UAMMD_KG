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
`4f9d04d292cbff92daa876fed5af4f06cc88e420`. **S0: PASS.**

## S1: associating-star MD smoke integration

Starting repository SHA: `02b3f6b34d01673406edfaf73faf421db43650e4`.

S1 adds `kg_assoc_stars`, which imports the supplied equilibrated star file,
runs the S0 topology audit before creating UAMMD state, extracts reactive
particles exclusively from `type == 2`, and keeps permanent KG FENE bonds
separate from transient associating FENE bonds. Event IDs are original 1-based
LAMMPS atom IDs. Supplied `Velocities` were intended to be retained:
`createParticleDataFromLammps` reads them and S1 sets
`initVelocities = false`.

The targets were rebuilt from scratch and focused non-GPU checks executed:

```bash
make -B -C examples/KG_Assoc kg_assoc_star_audit kg_assoc_stars
./examples/KG_Assoc/kg_assoc_star_audit --self-test
./examples/KG_Assoc/kg_assoc_stars --self-test
./examples/KG_Assoc/kg_assoc_star_audit \
  --input examples/KG/Stars/Stars_NA4N10C1000rho0.85rhopoly0.8.equilibrated.lammpsdat \
  --arms 4 --narm 10
```

Both self-tests passed. The S1 self-test covers type-2 sticker extraction,
sticker-subset candidate generation, intra/inter molecule classification,
state-count invariants, rejection of non-sticker transient endpoints, and
rejection of a transient/permanent bond conflict. The actual input audit
passed with 43,563 total atoms, 41,000 polymer beads, 4,000 stickers, 2,563
solvent beads, 1,000 stars, 40,000 permanent bonds, total density
`0.849995628364`, and polymer density `0.799986703462`.

The complete audited input header/physical record was: total atoms 43,563;
polymer beads 41,000; stickers 4,000; solvent beads 2,563; stars 1,000;
permanent bonds 40,000; box lengths `37.145 37.145 37.145`; volume
`51250.8518236`; total bead density `0.849995628364`; polymer bead density
`0.799986703462`.

The canonical GPU-host S1 invocation was:

```bash
./examples/KG_Assoc/kg_assoc_stars \
  --input examples/KG/Stars/Stars_NA4N10C1000rho0.85rhopoly0.8.equilibrated.lammpsdat \
  --arms 4 --narm 10 --steps 100000 --dt 0.01 --temperature 1 \
  --Ea 4 --Ee 8 --nu0 20 --Nevery 100 --r-assoc 1.122462048309373 \
  --damp 2 --seed 12345 --output /tmp/s1_smoke
```

It completed the requested 100,000 MD steps and ended with
`STAR_ASSOCIATION_SMOKE PASS`. The observed integration diagnostics were:

| Quantity | Observed |
|---|---:|
| Total timesteps | 100000 |
| Wall time (s) | 26.7021 |
| Particle timesteps/s | 1.63144e+08 |
| Chemistry sweeps | 1000 |
| Mean candidate sticker pairs/sweep | 1957 |
| Creations | 3457 |
| Breaks | 1683 |
| Final associating bonds | 1774 |
| Final intra-star bonds | 93 |
| Final inter-star bonds | 1681 |

The final state record was at timestep 100,000, time 1000, with 452 free
stickers, 1,774 associating bonds, 3,457 creations, 1,683 breaks, 93 intra-star
bonds, and 1,681 inter-star bonds. The explicitly verified state invariants
were:

```text
N_free + 2*N_assoc = 452 + 2*1774 = 4000
N_assoc = creations - breaks = 3457 - 1683 = 1774
N_assoc = N_intra + N_inter = 93 + 1681 = 1774
```

The inspected event output had 5,142 lines: two header lines and 5,140 events,
equal to 3,457 creations plus 1,683 breaks. The state output had 1,003 lines:
two header lines and 1,001 state records. The run reported no invalid
associating-FENE event; permanent bonds remained at 40,000, transient endpoints
remained terminal stickers, and all runtime state invariants held.

This is an integration/smoke validation only. The final bonded fraction and
intra/inter populations are not equilibrium-validated quantities. In
particular, `Nevery=100` at `dt=0.01` has not yet been cadence-convergence
validated for the star system. **S1: PASS.**

## S2: quantitative star-equilibrium and kinetic validation

Starting repository SHA: `f6f7ba29c5dc8ecb41416c4285b0b7faf1e8fa7a`.

S2 infrastructure was prepared at commit
`cb3eed7ee613e904f89844ed4d830266dfafdbe2`. The CUDA campaign was executed
manually on the CUDA host, outside Codex. The S1 star executable records full
provenance in both state and event headers: input file, star dimensions,
particle/sticker/permanent-bond counts, physical and chemistry parameters, seed,
requested steps, and original 1-based LAMMPS event-ID convention. Its state
footer records chemistry sweeps and cumulative candidate-sticker pairs.

`analysis/analyze_s2.py` is a CPU-only, fail-closed analyzer. It validates
required state/event provenance agreement; reconstructs valence-one transient
bond histories; reproduces state-file bond counts; reports post-burn-in
populations, event rates, complete lifetimes and censoring, finite-step attempt
rate, and the prescribed two-half stationarity diagnostic. It rejects missing
metadata, duplicate creation, invalid breakage, double valence, and state/event
disagreement. Its focused self-test passed:

```bash
python3 examples/KG_Assoc/analysis/analyze_s2.py --self-test
```

The staged CUDA launcher is `s2/run_s2_campaign.sh`. It accepts input and
output paths as arguments, writes exact per-run command/log files, and refuses
to overwrite results without `--force`. Gates were analyzed separately. The
campaign comprised 15 GPU runs: three canonical replicas, five cadence points,
three `Ea` points, and four `Ee` points.

S2 validates stationary bonded populations, replicate reproducibility,
chemistry-cadence convergence, `Ea` as primarily kinetic control, `Ee` as
equilibrium association-strength control, and simple bond-lifetime diagnostics.
It does not validate detailed loop topology, cluster connectivity, percolation,
MSD/diffusion, hopping/walking, stress, `G(t)`, or viscosity. Those questions
remain outside S2 and are not advanced here.

### Gate A: canonical replicate reproducibility

Condition: `Ee=8`, `Ea=4`, `Nevery=100`, `nu0=20`, `T=1`, `dt=0.01`, 500,000
MD steps, 50% burn-in, and seeds 12001, 12002, and 12003.

| Seed | Mean `N_assoc` | Bonded fraction | Mean `N_intra` | Mean `N_inter` | Creation rate | Break rate | Candidate pairs/sweep | Stationarity difference | Drift slope | Complete lifetimes | Mean lifetime | Median lifetime |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12001 | 1770.825270 | 0.885412635 | 87.212715 | 1683.612555 | 1.5476 | 1.5484 | 1900.5246 | 0.006597032 | -3.6378e-06 | 8004 | 820.9690 | 586.0 |
| 12002 | 1762.323471 | 0.881161735 | 82.033587 | 1680.289884 | 1.5780 | 1.5784 | 1895.0286 | 0.003739575 | -2.5101e-06 | 8186 | 808.8473 | 575.0 |
| 12003 | 1781.361455 | 0.890680728 | 100.954818 | 1680.406637 | 1.5672 | 1.5688 | 1910.8832 | 0.000043838 | -2.3606e-07 | 7988 | 834.0463 | 598.0 |

All three runs passed stationarity. The bonded-fraction span was
`0.0095189924`, below the predeclared reproducibility criterion of `0.02`.
Creation and break rates were balanced in every replica. **Gate A: PASS.**
Stationarity: **PASS**. Replica reproducibility: **PASS**. Creation/break
balance: **PASS**.

### Gate B: chemistry cadence

Common condition: `Ee=8`, `Ea=4`, `nu0=20`, `T=1`, `dt=0.01`, seed 12100, and
500,000 MD steps.

| `Nevery` | `delta_t_chem` | Attempt rate | Bonded fraction | Creation rate | Break rate | Mean complete lifetime | Median complete lifetime | Stationarity difference |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.1 | 0.359684703 | 0.885067497 | 1.8336 | 1.8320 | 731.7841 | 523.2 | 0.003217597 |
| 20 | 0.2 | 0.353216049 | 0.888721542 | 1.7764 | 1.7700 | 736.0038 | 508.1 | 0.004253695 |
| 50 | 0.5 | 0.334724140 | 0.883755549 | 1.7188 | 1.7268 | 778.6910 | 544.0 | 0.006088280 |
| 100 | 1.0 | 0.306714077 | 0.887820472 | 1.6164 | 1.6088 | 804.7487 | 559.0 | 0.000470355 |
| 200 | 2.0 | 0.259677315 | 0.887013989 | 1.3128 | 1.3020 | 937.7381 | 676.0 | 0.003679481 |

For `Nevery=20, 50, 100`, the bonded-fraction range was
`0.0049659934`, below the predeclared `0.01` criterion. `Nevery=200` also
remained consistent in equilibrium population. **Gate B equilibrium
convergence: PASS.**

Complete-bond lifetime statistics retain finite-cadence dependence: relative
to `Nevery=10--20`, `Nevery=100` gives lifetime measures higher by several
percent to about 10%. Thus **Gate B kinetic convergence retains finite cadence
bias**. `Nevery=100` is retained as a deliberate production cost/accuracy
compromise: it is sufficiently converged for equilibrium and operational
kinetics, but is not the zero-cadence-limit value and is not exact for fine
lifetime estimation.

### Gate C: `Ea` control

Common condition: `Ee=8`, `Nevery=100`, `nu0=20`, `T=1`, `dt=0.01`, and seed
12200.

| `Ea` | Bonded fraction | Creation rate | Break rate | Mean complete lifetime | Median complete lifetime | Stationarity difference |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.8891411435 | 4.6192 | 4.6272 | 330.1302 | 222.0 | 0.002998688 |
| 4 | 0.8837822871 | 1.6080 | 1.6200 | 828.9444 | 585.0 | 0.001445596 |
| 6 | 0.8851315737 | 0.2528 | 0.2510 | 3194.1472 | 2599.0 | 0.004866574 |

All runs passed stationarity. The bonded-fraction span was `0.0053588565`,
below the predeclared `0.02` criterion. The stationary association population
was approximately invariant with `Ea`, while kinetics slowed strongly and
complete bond lifetimes increased strongly as `Ea` increased. **Gate C: PASS.**
No precise Arrhenius law is fitted or claimed from these three points.

### Gate D: `Ee` control

Common condition: `Ea=4`, `Nevery=100`, `nu0=20`, `T=1`, `dt=0.01`, and seed
12300.

| `Ee` | Bonded fraction | Mean `N_assoc` | Intra fraction | Creation rate | Break rate | Mean complete lifetime | Median complete lifetime | Stationarity difference |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.1437121152 | 287.4242 | 0.054657426 | 20.2540 | 20.2592 | 12.4329 | 8.0 | 0.000198551 |
| 4 | 0.4330143942 | 866.0288 | 0.051902081 | 18.2828 | 18.2640 | 43.1969 | 27.0 | 0.000051968 |
| 6 | 0.7287976809 | 1457.5954 | 0.052589718 | 6.5492 | 6.5548 | 190.9305 | 124.0 | 0.001061013 |
| 8 | 0.8878282687 | 1775.6565 | 0.052182702 | 1.5800 | 1.5812 | 827.5301 | 593.0 | 0.004342002 |

All points passed stationarity. The stationary bonded fraction increased
strictly monotonically, `0.1437 -> 0.4330 -> 0.7288 -> 0.8878`, while bond
turnover decreased and complete lifetimes increased with `Ee`. **Gate D: PASS.**
The approximately 5% intra-bond fraction is descriptive only; detailed network
topology interpretation is deferred to S3. No relation of the form
`ln Keq = Ee/T + constant` is imposed or claimed for the full star system,
whose tethering, intramolecular association, connectivity constraints, and
saturation prevent direct transfer of the K1 simple-fluid concentration
quotient.

Across S2, complete-lifetime summaries exclude right-censored bonds that remain
active at trajectory end. Their means and medians are comparative kinetic
diagnostics, not unbiased estimators of the full lifetime distribution, and are
not overinterpreted.

**S2: PASS.** Canonical replicas were stationary and reproducible; equilibrium
bonded fraction converged through `Nevery=100`; `Nevery=100` was retained as a
production cost/accuracy compromise; `Ea` changed kinetics strongly while
stationary association remained nearly unchanged; `Ee` strongly and
monotonically increased association; and lifetime statistics showed the
expected qualitative trends subject to censoring and finite-cadence caveats.

S2 closure is documentation-only after the manually executed GPU campaign.
The resulting documentation-only commit SHA is reported with this closure.

## P2 / E1: conformational-equilibration infrastructure

P2 adds `kg_assoc_star_equilibrate`, an E1-only star conformational
equilibrator. Before dynamics it runs the S0 permanent-topology audit using
explicit `--arms` and `--narm`; it then performs the established four-stage KG
procedure: limited-displacement DPD + permanent FENE, uncapped DPD + permanent
FENE, progressive DPD push-off, and WCA + permanent FENE Langevin NVT.

Dynamic sticker association, association kinetics, associative bonds, and
chemical parameters are absent. Type-2 terminal stickers are ordinary KG beads
in E1. The final output is a normal LAMMPS data file containing only the input
permanent topology. Stage-4 diagnostics are machine-readable and contain:

```text
# step time e_bonded e_nonbonded e_kinetic e_total temperature pressure mean_rg2 mean_center_terminal_r2 max_permanent_bond
```

The executable self-test covers S0 audit integration, center and terminal
identification, synthetic-star `Rg^2`, a periodic-boundary-crossing star for
PBC-safe `Rg^2` and center-terminal distance, permanent-bond maximum distance,
and diagnostics formatting. E1 diagnostic calculations are CPU-side only at
the configured Stage-4 cadence (default 10,000 steps), never every MD step.

This is implementation validation, not scientific equilibration validation.
E1 infrastructure is implemented; E1 scientific equilibration lengths and the
equilibration of C1--C6 remain unestablished pending executed diagnostics.

Starting P2 SHA: `6e24d4ef349f47622132b71803292d3d50f5c89b`. The focused
builds and deterministic checks passed:

```bash
make -B -C examples/KG_Assoc kg_assoc_star_equilibrate
./examples/KG_Assoc/kg_assoc_star_equilibrate --self-test
make -B -C examples/KG_Assoc kg_assoc_star_audit
./examples/KG_Assoc/kg_assoc_star_audit --self-test
make -B -C examples/KG_Assoc kg_assoc_stars
./examples/KG_Assoc/kg_assoc_stars --self-test
```

The local C1 generated input was present and its CPU-only S0 audit passed with
43,563 atoms, 1,000 stars, 4,000 stickers, and 40,000 permanent bonds. A
minimal all-four-stage C1 smoke invocation was attempted, but this Codex host
has no CUDA-capable device (`CUDA error 100` during UAMMD initialization).
Consequently no real-input E1 dynamics, diagnostic file, or final E1 file was
produced here. The production-CUDA-host smoke test remains required. **E1
infrastructure: implemented and CPU self-tested; GPU smoke test pending.**

### P2.1a: Stage-3 to Stage-4 transition diagnostics

Intermittent failures have been observed exactly on entry to Stage 4 WCA, even
with `dt=0.002`. P2.1a adds diagnostics only; it does not alter Stage-3 DPD
push-off, Stage-4 WCA, their parameters, or their lengths, and does not claim
the failure is solved.

After every Stage-3 loop and once immediately before Stage 4, the executable
records a CPU-side, minimum-image report in stdout and as an E1-diagnostics
comment. It includes step, loop index, DPD amplitude, kinetic temperature,
maximum speed, maximum permanent-bond length and IDs, global closest-pair
distance with IDs/types/molecule IDs, counts of all pairs below `0.5`, `0.6`,
`0.7`, and `0.8`, and finite-state flags. Those pair counts and the global
closest pair include permanent bonded neighbors; a second closest-pair value
excludes permanent KG neighbors. The diagnostic fails cleanly for non-finite
positions or velocities and for a permanent bond at or above FENE `R0`; it has
no arbitrary pair-distance failure threshold.

`--seed INTEGER` now reseeds UAMMD immediately after system construction and
before DPD/NVT construction, so their stochastic seeds are reproducible. When
omitted, the prior UAMMD default seeding remains in use. The selected seed is
recorded in stdout, E1 diagnostics metadata, and the final LAMMPS producer
comment. The deterministic self-test covers closest-pair detection, threshold
counts, maximum speed, maximum-bond identity, finite-state rejection, and
permanent-neighbor exclusion. GPU transition results remain pending execution
on a CUDA-capable host.

The P2.1a rebuild and deterministic E1 self-test passed; the independent S0
audit rebuild and self-test also passed. No real transition diagnostic was run
because this Codex host has no CUDA-capable device.

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
