# KG_Assoc validation record

This record contains only executed and inspected checks. Generated `.events` and
`.summary` files are intentionally not versioned.

For the current project snapshot, frozen scientific choices, and next steps,
start with `PROJECT_STATE.md`, `SCIENTIFIC_DECISIONS.md`, and `ROADMAP.md`.

## P4.1 — production instrumentation (CLOSED)

`kg_assoc_production` is a separate production-oriented executable. Its
ordering is fixed as: advance one MD step; synchronize and update chemistry on
scheduled steps; then refresh WCA, permanent-FENE, and associating-FENE stress
caches and enqueue the buffered six-channel reduction. Thus the step's stress
and topology frame refer to the post-chemistry partner state. Stress excludes
step zero and contains exactly one sample for every advanced MD step.

It writes unwrapped star COM samples every 100 steps and synchronized COM and
topology frames every 10,000 steps. Molecular COMs are constructed relative to
one stable anchor bead using minimum-image bead displacements, then unwrapped
in time from successive minimum-image COM increments. The topology stream uses
`FRAME step time active_pairs` followed by original 1-based atom IDs and both
molecule IDs. Restart starts a new output segment; the P3 chemical state is
preserved, but image history is intentionally not claimed to be serialized.

Dedicated-host commands are provided in `scripts/run_p41_validation.sh` and
`scripts/benchmark_p41_short.sh`; `scripts/p42_rheology_pilot.template.sh` is
a non-executing P4.2 placeholder. These host checks, including real C1
restart-continuation and cadence/output inspection, passed on the dedicated
TITAN Xp host. No long production run was launched.

The P4.1 host scripts are fail-closed. `run_p41_validation.sh` requires a
chemically valid `.restart.lammpsdat` plus `.assoc_restart`, uses validation-
only 100-step COM/frame cadence, and checks the stress-sample provenance
(`step0_sampled=no` and one sample per advanced step), six finite correlator
channels, exact COM/frame cadence, parseable reciprocal topology frames, final
topology agreement, deterministic PBC temporal-unwrapping arithmetic, and a
short restart topology round trip. It ends with `P4.1_VALIDATION PASS` only
after every assertion passes. `benchmark_p41_short.sh` runs both drivers from
the same chemical restart and reports wall-time overhead and throughput loss.

The exact validated commands were:

```bash
INPUT=examples/KG_Assoc/systems/restart_bank/C1/C1_e2_s12001_t40000.restart.lammpsdat \
  examples/KG_Assoc/scripts/run_p41_validation.sh
INPUT=examples/KG_Assoc/systems/restart_bank/C1/C1_e2_s12001_t40000.restart.lammpsdat \
  examples/KG_Assoc/scripts/benchmark_p41_short.sh
```

The validation reported `stress_samples=20000`, `com_sample_steps=200`,
`com_rows=200000`, `synchronized_frames=200`, and `stars=1000`, ending with
`P4.1_VALIDATION PASS`. The one-step restart continuation performed zero
chemistry sweeps and preserved active temporary topology exactly. Its COM
output intentionally starts a new unwrapped segment because image history is
not serialized.

The controlled benchmark ended with `P4.1_BENCHMARK PASS`:

| run | wall seconds | particle-timesteps/s |
|---|---:|---:|
| baseline | 5.87473 | 1.48306e8 |
| production | 9.47309 | 9.19721e7 |

Relative wall-time overhead was `0.612515` (61.3%); relative throughput loss
was `0.379849` (38.0%).

## P4.2 — profiling and overhead decomposition (PENDING)

P4.2 began with profiling. A 2,000-step C1 Nsight Systems capture on the
dedicated TITAN Xp measured 2,001 baseline calls each to WCA, permanent FENE,
and associating FENE, versus 4,001 calls each in production. The duplicate
production pass came from re-evaluating all three interactors only to rebuild
stress caches after `forwardTime()`. GPU kernel time was approximately 243 ms
for baseline and 469 ms for production; this is consistent with the earlier
20,000-step controlled benchmark (61.3% wall-time overhead and 38.0%
throughput loss).

The P4.2 cache-reuse change preserves the frozen post-chemistry sampling
convention. Normal steps reduce the caches populated by the force pass. On a
chemistry step, only the associating-FENE cache is rebuilt after partner
updates; WCA and permanent-FENE topology is unchanged. The focused stress
regression checks force-populated caches against an explicit stress-only
recomputation and checks post-creation/break cached totals against a full
post-chemistry recomputation. The dedicated TITAN Xp P4.1 validation passed
after this change. The repeated 20,000-step benchmark measured 5.91834 s
(1.47214e8 particle-timesteps/s) for baseline and 7.61406 s (1.14428e8
particle-timesteps/s) for production: 28.652% wall-time overhead and 22.271%
throughput loss. This supersedes the pre-optimization overhead measurement.

The valid optimized 2,000-step profile reports 2,001 stress-aware WCA calls,
2,001 permanent-FENE calls, 2,021 associating-FENE calls, and 2,000 calls each
to the particle and partial stress-reduction kernels. Thus redundant full
interaction evaluation is removed. Device-host transfers are not dominant;
the remaining overhead is intrinsic stress-aware interaction work, every-step
stress reduction, and their launches/synchronization. Permanent FENE has the
largest intrinsic per-call penalty. Further optimization is deferred until a
bounded two-seed rheology pilot determines the required trajectory duration.

`scripts/run_p42_rheology_pilot.sh` runs 1,000,000 steps per independent C1
seed (12001 and 12002, both `t40000` bank states) with unchanged production
defaults. `analysis/analyze_p42_rheology_pilot.py` writes each six-channel
curve, their replica mean, and an explicit long-tail heuristic. A lag is
resolved when its two-seed SEM is at most `max(0.25*|mean G|, 0.05*|mean G(0)|)`.
The tail is called decayed only if at least three resolved bins in the latter
half of the lag range have a mean within their RMS SEM of zero. These are pilot
diagnostics, not fitted relaxation times or a final production prescription.

## P4.0 — associating-FENE stress tensor (CLOSED)

Starting HEAD was `0310794d75625e35f646173807879668f5af56d7` (`docs: record
Ponytail and code style workflow`), rather than the older P3 validation SHA
still named in the prior project-state record.

`AssociatingFENEInteractor` now caches diagonal and off-diagonal temporary
FENE stress per particle. For one active pair with `rij = rj-ri` and `fij` the
force on `i`, it stores `-rij tensor fij` on both endpoints. The KG reducer
therefore adds `+1/2` of the cache, exactly matching permanent FENE and giving
one physical pair contribution. The shifted bonded energy, including `Ee`, is
not part of this force or stress. The live partner array is the only temporary
topology input, so an active pair is included at every valid distance below
`R0=1.5`, independently of `r_assoc=1.25` and the WCA neighbor list.

The existing GPU-buffered KG reducer gained a three-interactor overload for
WCA, permanent FENE, and associating FENE; the original two-interactor API is
unchanged. No host loop over active associations or sampling-only device-host
synchronization was added to the production path.

The focused GPU regression was rebuilt and executed on NVIDIA TITAN Xp,
single-precision UAMMD:

```bash
make -B -C examples/KG_Assoc kg_assoc_stress_test
./examples/KG_Assoc/kg_assoc_stress_test
```

It passed `KG_ASSOC_STRESS_TEST PASS tensor, reversal, trace, decomposition,
kinetic topology`. The test establishes: zero temporary topology yields an
exact zero cache and the ordinary KG tensor; a non-axis-aligned temporary bond
matches an independent analytic calculation in all six channels; exchanging
endpoints leaves the physical tensor unchanged; its trace matches
`-rij dot fij / V`; the total is the independent kinetic + WCA + permanent
FENE + associating-FENE decomposition; and the asynchronous buffered reducer
matches the direct reducer. A deterministic kinetic loop formed and broke the
live temporary pair and confirmed finite active stress and no stale cache after
dissociation.

Existing focused checks and a short dynamic GPU smoke also passed:

```bash
make -B -C examples/KG_Assoc kg_assoc_dimer kg_assoc_stars kg_assoc_star_audit
./examples/KG_Assoc/kg_assoc_dimer --self-test
./examples/KG_Assoc/kg_assoc_k1 --self-test
./examples/KG_Assoc/kg_assoc_star_audit --self-test
./examples/KG_Assoc/kg_assoc_stars --self-test
./examples/KG_Assoc/kg_assoc_dimer --steps 200 --dt 0.005 --Nevery 1 \
  --Ea 0 --Ee 0 --nu0 1000 --r-assoc 1.25 --seed 9876 \
  --output /tmp/p40_dimer_0310794
```

The dimer smoke completed 200 kinetic updates with 6 accepted creations and
6 breaks. This is a topology/finite-value smoke, not a production rheology
run. P4.0 is closed. P4.1 must connect this validated three-term reducer to a
clean every-step production sampler and retain the existing six-channel
`Correlator6` estimator unchanged. P4.0 implementation commit:
`8e5d106854e285bb7c0fd8c9db8c4d8da1f18d21`.

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
explicit `--arms` and `--narm`; it performs limited-displacement DPD +
permanent FENE, uncapped DPD + permanent FENE, progressive DPD push-off, the
P2.1c final-amplitude DPD relaxation/hold stage, and WCA + permanent FENE Langevin
NVT.

Dynamic sticker association, association kinetics, associative bonds, and
chemical parameters are absent. Type-2 terminal stickers are ordinary KG beads
in E1. The final output is a normal LAMMPS data file containing only the input
permanent topology. Stage-4 diagnostics are machine-readable and contain:

```text
# step time e_bonded e_nonbonded e_kinetic e_total temperature pressure mean_rg2 mean_center_terminal_r2 min_permanent_bond max_permanent_bond
```

The executable self-test covers S0 audit integration, center and terminal
identification, synthetic-star `Rg^2`, a periodic-boundary-crossing star for
PBC-safe `Rg^2` and center-terminal distance, permanent-bond minimum and
maximum distance, and diagnostics formatting. E1 diagnostic calculations are
CPU-side only at the configured Stage-4 cadence (default 1,000 steps), never
every MD step.

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

### P2.1b: isolate the first Stage-4 failure

The current C1 reproducer is seed `12004` at `dt=0.002`; seed `12001` is the
passing control. For seed 12004, Stage-3 exit geometry was normal: temperature
`3.52666156484`, maximum speed `8.85591526699`, maximum permanent bond
`1.32768594207`, closest-pair distance `0.701904204381`, closest nonbonded-pair
distance `0.756670554632`, no pairs below `0.7`, 243 pairs below `0.8`, and
finite positions and velocities. Thus the available Stage-3 geometry does not
distinguish the later failure.

P2.1b adds separate CUDA synchronize/error checkpoints after WCA construction,
permanent-FENE construction, NVT construction, both interactor attachments,
each initial/post-step thermo reduction, conformation readback, and the first
NVT step. It reports every Stage-4 diagnostic field and its finite flag before
field validation, and adds a CPU, minimum-image, no-double-counting WCA energy
reference at Stage-4 entry. `--stage4-entry-diagnostic-only` runs E1 through
Stage 3, performs Stage-4 entry diagnostics and exactly one NVT step, then
exits without writing an E1 configuration.

The P2.1b CPU build/self-test and independent S0 audit build/self-test passed.
The executed reproducer shows that initial WCA/FENE thermo and the first NVT
step are finite, but a permanent FENE bond can exceed `R0` within roughly
10--20 Stage-4 steps, making bonded energy non-finite. This identifies a hot
transient on switching from the final DPD state to WCA, rather than an
unresolved severe overlap at the Stage-3 boundary. It is a diagnosis, not a
fix. `dt=0.002` remains a possible temporary stabilization timestep only.

### P2.1c: final DPD relaxation/hold and timestep-promotion diagnostics

P2.1c retains the P2.1a/P2.1b diagnostics and adds Stage 3b: an explicit final
DPD relaxation/hold segment after the Stage-3 ramp and before WCA. It uses the same
DPD implementation, target temperature 1, gamma 4.5, permanent FENE topology,
and final Stage-3 conservative amplitude (1000 for the default ten-loop ramp).
The operational default is `--stage3b-steps 20000`, sampled every
`--stage3b-diagnostic-every 500`; neither number is yet a scientific
equilibration criterion. Stage 3b is a final DPD relaxation/hold, not a cooling
stage: the measured temperature remains above 3 before WCA. There is no
automatic temperature-based early stop or minimum-bond threshold.

`--dt-dpd` controls Stages 1--3b and `--dt-wca` controls Stage 4. The legacy
`--dt` option sets both to the supplied value, preserving prior behavior.
`--stage4-promotion-test --promotion-steps N` runs short, fail-closed WCA
segments sequentially at `dt=0.002`, `0.005`, and `0.01`, with 1,000 steps at
each timestep, starting from the relaxed E1 state. It reports transition and
thermo/conformation diagnostics at
each segment boundary and checks every test step for CUDA errors, non-finite
thermo/particle state, and a permanent bond at or above `R0`; it writes no E1
configuration. This is a validation diagnostic, not a production trajectory.

For seed `12003`, `stage3b=1000` failed the promotion test, while `5000`,
`10000`, and `20000` passed. The conservative selection is `stage3b=20000`:
the local geometry is substantially safer at that length and the promotion
sequence `0.002 -> 0.005 -> 0.010` passes cleanly. The interpretation is that
Stage 3b primarily relaxes locally compressed configurations before WCA; it is
not being used as a temperature-cooling criterion.

The final robustness requirement was five independent CUDA runs, seeds
`12001--12005`, with `stage3b=20000` and 1,000 promotion steps at each of the
three timesteps. All five passed, so the C1 P2.1 transition protocol is closed.

Transition diagnostics now also report `min_permanent_bond` and
`min_permanent_bond_ids`, using the existing permanent-bond topology. No
automatic threshold is applied to that value.

**Future E2 chemistry note:**

> Active associative bonds may extend beyond the current chemical candidate
> cutoff r_assoc ≈ 1.12. In E2, verify that break eligibility for already-active
> bonds is not lost when bond length exceeds the formation-search cutoff.
> Formation and break neighbor criteria may need to be separated.

### P2.1d: staged WCA-strength ramp

Direct DPD-to-full-WCA activation remains non-robust even with the conservative
`stage3b=20000`. In the five-seed check, seed `12005` reached Stage-4 entry
with `closest_pair_distance=0.70715658846` for permanent-bond IDs
`23782,23783`, then failed after 17 steps at `dt=0.002` when that same bond
reached or exceeded FENE `R0`. Seed `12003` showed the same mechanism with an
initially highly compressed permanent bond. These are occasional compressed
permanent-bond configurations, not a change to chemistry or a scientific
equilibration criterion.

P2.1d adds an optional numerical preparation protocol, enabled by
`--wca-ramp`, after the final DPD relaxation/hold. At fixed `dt=0.002`, it
applies the existing WCA implementation through the fixed epsilon schedule
`0.01, 0.03, 0.10, 0.30, 1.00`, with the default `--wca-ramp-steps 500` at
each level. Each level reports transition and thermo diagnostics before and
after the segment; every step fails closed on CUDA errors, non-finite particle
state or thermo, or any permanent bond at or above `R0`. Diagnostics include
epsilon, temperature, speed, minimum and maximum permanent-bond lengths and
IDs, closest nonbonded pair, bonded/nonbonded/total energy, and finite-state
flags.

After the ramp's 500-step `epsilon=1.00`, `dt=0.002` segment, promotion mode
runs exactly 1,000 steps at `dt=0.005` and then 1,000 steps at `dt=0.010`.
There is no additional 1,000-step `dt=0.002` promotion block in ramp mode;
the ramp itself contributes 500 `dt=0.002` steps at each of the five epsilon
levels. The ramp is a numerical transition-preparation protocol, not
scientific equilibration.

The first validation targets were seeds `12003` and `12005`, with
`stage3b=20000`, 500 steps per epsilon, and the schedule above. Both passed;
the broader five-seed validation passed as the P2.1 closure. No automatic ramp
tuning is performed.

### P2.2: long C1 conformational equilibration and stationarity

P2.2 addresses conformational stationarity after the P2.1 transition, with
chemistry disabled. The normal long-run path performs the validated Stage 3b
relaxation/hold, WCA ramp, and 1,000-step promotions at `dt=0.005` and
`dt=0.010`, then continues at full WCA epsilon `1`, `dt=0.01`, and target
temperature `1` for the requested Stage-4 duration. Promotion-test mode is
not used for this run because it writes no E1 configuration.

The validated C1 condition is `A=4`, `Narm=10`, `Nstars=1000`,
`rho_total=0.85`, `rho_poly=0.8`, with chemistry disabled. Its preparation is
20,000 Stage-3b final DPD relaxation/hold steps, WCA epsilon
`0.01, 0.03, 0.10, 0.30, 1.00` with 500 steps per level at `dt=0.002`, then
1,000 steps at `dt=0.005` and 1,000 steps at `dt=0.010`, followed by full-WCA
Stage 4 at `dt=0.01`. Two independent runs, seeds `12001` and `12002`, each
used 2,000,000 Stage-4 steps. The default `--conformation-every 1000` gives
approximately 2,000 long-run samples; the cadence remains configurable.

The time-series diagnostics columns are:

```text
# step time e_bonded e_nonbonded e_kinetic e_total temperature pressure mean_rg2 mean_center_terminal_r2 min_permanent_bond max_permanent_bond
```

`analyze_e1_stationarity.py` reports sample count, time range, first-half and
second-half means, relative half-to-half differences, second-half linear
trends, equal contiguous block means, and trajectory-wide minimum/maximum
permanent-bond summaries for `mean_rg2`, `mean_center_terminal_r2`,
`temperature`, and `pressure`. It also estimates integrated autocorrelation
times for the two conformational observables using the initial-positive-
sequence sum of the normalized autocorrelation function, and reports when the
trajectory is too short or irregular for that estimate. The script is
diagnostic only: there is no automatic equilibrium stopping rule and no hard
E1 equilibrated PASS/FAIL criterion.

The latter portions of both replicas were conformationally stationary and
agreed closely:

| seed | second-half mean `Rg^2` | second-half mean center-terminal `r^2` | `tau_int(Rg^2)` | `tau_int(center-terminal r^2)` |
|---:|---:|---:|---:|---:|
| 12001 | 7.013572 | 15.587541 | 156.9 | 88.2 |
| 12002 | 7.012661 | 15.597365 | 132.9 | 89.7 |

Therefore C1 is conformationally stationary by the latter part of the runs,
and 2,000,000 Stage-4 steps is adopted as a conservative validated E1
duration for `Narm=10`. This is not claimed to be the minimum necessary
duration.

### P2.3: longer-arm E1 conformational equilibration plan

The C1 duration is not assumed sufficient for longer arms. The first checks are:

| case | input | condition |
|---|---|---|
| C5 | `systems/generated/Stars_NA4N20C1000rho0.85rhopoly0.8.lammpsdat` | `A=4`, `Narm=20`, `rho_poly=0.8`, `rho_total=0.85` |
| C6 | `systems/generated/Stars_NA4N40C1000rho0.85rhopoly0.8.lammpsdat` | `A=4`, `Narm=40`, `rho_poly=0.8`, `rho_total=0.85` |

For each chain length, use the validated C1 transition protocol, start with one
seed, and run Stage 4 long enough to assess stationarity rather than stability
alone. Use `analyze_e1_stationarity.py` to compare `mean_rg2`,
`mean_center_terminal_r2`, half-window differences, second-half trends, block
means, and autocorrelation times. Extend a run if those diagnostics do not
support stationarity. Only after stationarity is established should a second
seed be used for confirmation. No Stage-4 duration is frozen yet for C6.

#### C5 closure: `A=4`, `Narm=20`

C5 uses `Nstars=1000`, `rho_total=0.85`, `rho_poly=0.8`, and chemistry
disabled. Both seeds `12001` and `12002` used the validated C1 transition
protocol, followed by 2,000,000 Stage-4 steps at `dt=0.01`, sampling every
1,000 steps.

| seed | observable | first-half mean | second-half mean | relative difference | second-half slope | `tau_int` | effective samples |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12001 | `mean_rg2` | 14.2613032106 | 14.3777463343 | 0.00809884393619 | 3.45392227673e-08 | 706.193851464 | 14.1604178217 |
| 12001 | `mean_center_terminal_r2` | 32.5487535953 | 32.8527665215 | 0.00925379985913 | 2.97437458605e-07 | 505.007037985 | 19.8017042292 |
| 12002 | `mean_rg2` | 14.2182914157 | 14.3543360763 | 0.00947760034804 | 1.36606856841e-07 | 523.997165487 | 19.0840726983 |
| 12002 | `mean_center_terminal_r2` | 32.5165979833 | 32.7764793097 | 0.00792889693703 | 3.65643605274e-06 | 424.028863635 | 23.5833002361 |

The five equal contiguous block means were:

```text
seed 12001 mean_rg2:                 14.0365885489 14.4095719505 14.3818624071 14.3948195411 14.3747814147
seed 12001 mean_center_terminal_r2:  32.0814595689 32.8508741005 32.8456992120 32.8928080720 32.8329593386
seed 12002 mean_rg2:                 14.0666189155 14.3006004453 14.3739951715 14.3349072718 14.3554469258
seed 12002 mean_center_terminal_r2:  32.1696308543 32.7452689870 32.7629138772 32.7691885319 32.7856909820
```

Both replicas show an initial conformational transient, most visible in the
first block, followed by a consistent stationary plateau. The second-half
slopes are negligible compared with the equilibrium fluctuations, and the
independent replicas agree closely in their late-time means. Temperature and
pressure are stationary in both runs, and permanent-bond lengths remain safely
below FENE `R0=1.5`. The C5 conformational autocorrelation times are
substantially larger than the C1 `Narm=10` values, but 2,000,000 Stage-4 steps
is sufficient to reach a stationary final state for C5.

**P2.3 status:** C5 / `Narm=20`: **closed**. Adopt 2,000,000 Stage-4 steps at
`dt=0.01` as the conservative validated E1 duration for `Narm=20`; this is
not a demonstrated minimum. C6 was then validated independently below; the C5
duration was not assumed sufficient.

#### C6 closure: `A=4`, `Narm=40`

C6 uses `Nstars=1000`, `rho_total=0.85`, `rho_poly=0.8`, and chemistry
disabled. Both seeds `12001` and `12002` used the validated E1 transition
protocol, followed by 8,000,000 Stage-4 steps at `dt=0.01`, sampling every
1,000 steps.

| seed | observable | first-half mean | second-half mean | relative difference | second-half slope | `tau_int` | effective samples |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12001 | `mean_rg2` | 28.9209002098 | 29.4257261728 | 0.0171559389912 | 1.60550922204e-07 | 3363.95980836 | 11.890748486 |
| 12001 | `mean_center_terminal_r2` | 67.1824147446 | 68.1868406427 | 0.01473049475 | -1.29821673912e-06 | 2847.62106895 | 14.046812771 |
| 12002 | `mean_rg2` | 28.9946447173 | 29.4188962908 | 0.0144210567686 | 6.49197033686e-06 | 3667.47506737 | 10.9066862797 |
| 12002 | `mean_center_terminal_r2` | 67.3047573923 | 68.28162656 | 0.0143064718426 | -1.68960148121e-06 | 3004.27930445 | 13.3143412928 |

The five equal contiguous block means were:

```text
seed 12001 mean_rg2:                 28.2436603912 29.2971750134 29.5511345185 29.3024977243 29.4720983091
seed 12001 mean_center_terminal_r2:  65.8027504663 67.9746402867 68.5253564928 67.8238906915 68.2965005308
seed 12002 mean_rg2:                 28.2497643859 29.4110137467 29.3946684203 29.4802754923 29.4981304748
seed 12002 mean_center_terminal_r2:  65.7626446804 68.2615963060 68.2309644967 68.4506343997 68.2601199979
```

Both replicas show a pronounced initial conformational transient, especially
in the first block. The subsequent blocks are consistent with a stationary
plateau, and the second-half slopes are small compared with the equilibrium
fluctuations. The independent replicas agree very closely in their late-time
means. Temperature and pressure are stationary in both runs, and
permanent-bond lengths remain safely below FENE `R0=1.5`. C6 conformational
autocorrelation times are much larger than for `Narm=20`; the effective sample
counts are consequently modest, but this does not prevent establishing that
the final configurations are in a reproducible stationary regime.

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

## P3.0 — associating cutoff audit (CLOSED)

P3.0 is closed. The recommended/default E2 physical reaction cutoff is now
`r_assoc=1.25`, used identically for association creation and breaking. This
is a conservative engineering/scientific choice for the intended `Ee` range
through 16; it is not claimed to be mathematically unique or globally
optimal.
It does not change the default physical reaction cutoff. The concern is
kinetic, not mechanical: an active temporary FENE pair is evaluated directly
from the dynamic partner topology up to `R0=1.5`, independently of the WCA
cell-list cutoff and neighbor-list skin. In contrast, the physical
`r_assoc` gates both creation and breaking in the current LAMMPS-equivalent
kinetics. A bond beyond that radius stays mechanically active but cannot break
until it returns.

`kg_assoc_dimer --bonded-radial-audit` creates one permanent-for-the-audit
temporary bond, disables kinetic transitions, and samples its WCA+FENE radial
ensemble. Its `.cutoff_audit` output reports the maximum valid distance and,
at `2^(1/6)`, `1.15`, `1.20`, `1.25`, `1.30`, `1.40`, the active-bond fraction outside
the cutoff and the missing Metropolis break-propensity fraction. The latter is
the sampled form of `F_miss`; it calls the same `deltaU`, `rstar`, FENE, and
Metropolis helpers used by the kinetic update. Run the `Ee=4,6,8` audits and
compare them with the deterministic oracle:

```bash
for ee in 4 6 8; do
  ./examples/KG_Assoc/kg_assoc_dimer --bonded-radial-audit --Ee "$ee" \
    --steps 2000000 --audit-burnin 200000 --audit-sample 100 --seed 1701 \
    --output "p30_dimer_Ee${ee}"
done
python3 examples/KG_Assoc/analysis/analyze_cutoff_audit.py \
  'p30_dimer_Ee*.cutoff_audit'
```

The oracle integrates `r^2 exp[-(U_WCA+U_FENE)/T]` by transparent midpoint
quadrature on `(0,R0)`. It verifies decreasing tails and `F_miss` with cutoff,
the expected `Ee`-independent conditional radial distribution, agreement of
each sampled tail and `F_miss` with the reference, and rejection of an audit
that reaches `R0`. The default comparison allowance is the larger of 0.02 and
five independent-sample standard errors; it is deliberately reported rather
than used to retune physics.

K1 now accepts `--r-assoc`, records it in state metadata, keeps it in analyzer
condition keys, and prints active-bond distance diagnostics at every chemistry
sweep. The corresponding minimal sensitivity matrix is:

```bash
for ee in 4 6 8; do
  for cutoff in 1.122462048309373 1.15 1.20; do
    ./examples/KG_Assoc/kg_assoc_k1 --Ee "$ee" --r-assoc "$cutoff" \
      --output "p30_k1_Ee${ee}_r${cutoff}" --force
  done
done
python3 examples/KG_Assoc/analysis/analyze_k1.py 'p30_k1_*.state' \
  --summary p30_k1.csv
```

Report bound fraction from the state rows, creations, breaks, and both
`Keq_event`/`Keq_direct` from the analyzer. Compare only measured differences:
changing the physical transition region need not leave raw populations
invariant. No `Ea`, `Ee`, `nu0`, or `Nevery` compensation is part of P3.0, and
no final cutoff recommendation has yet been made.

### P3.0 cutoff-efficiency benchmark

The K1 executable now reports `wall_seconds`, `chemistry_sweeps`,
`total_candidate_pairs`, `mean_candidate_edges`, `creations`, `breaks`, and
`particle_timesteps_per_second`. The benchmark below keeps all K1 physics and
the three repetition seeds identical between the current cutoff and `1.25`.

```bash
make -C examples/KG_Assoc kg_assoc_k1
work=$(mktemp -d /tmp/p30_k1_benchmark.XXXXXX)
for cutoff in 1.122462048309373 1.25; do
  for rep in 1 2 3; do
    seed=$((510000 + rep))
    prefix="$work/k1_r${cutoff}_rep${rep}"
    printf 'r_assoc %.15g\n' "$cutoff" > "$prefix.log"
    ./examples/KG_Assoc/kg_assoc_k1 \
      --n 256 --rho .05 --push-steps 5000 --warmup 20000 \
      --steps 100000 --dt .005 --temperature 1 --nu0 20 \
      --Ea 4 --Ee 4 --Nevery 100 --sample 100 \
      --r-assoc "$cutoff" --seed "$seed" --output "$prefix" --force \
      >> "$prefix.log" 2>&1
  done
done
python3 examples/KG_Assoc/analysis/analyze_cutoff_benchmark.py \
  "$work"/*.log
```

The benchmark analyzer prints the requested per-cutoff means and relative wall
time, followed by the compact P3.0 decision table. The deterministic oracle
now also evaluates `Ee=12` and `Ee=16`. With the configured WCA+FENE
reference (`K=30`, `R0=1.5`, `T=1`), its current values are:

| cutoff | F_miss(Ee=8) | F_miss(Ee=12) | F_miss(Ee=16) |
|---:|---:|---:|---:|
| 1.1224620483 | 2.3362e-2 | 2.9239e-1 | 4.7589e-1 |
| 1.20 | 2.3261e-5 | 7.8957e-4 | 3.1930e-2 |
| 1.25 | 8.1071e-8 | 2.7519e-6 | 1.1128e-4 |

The matched benchmark results were:

| cutoff | mean wall seconds | relative wall time | mean candidate pairs/sweep | mean creations | mean breaks |
|---:|---:|---:|---:|---:|---:|
| 1.12246204831 | 4.40536 | 1.00000 | 30.6946667 | 425.0 | 400.3333333 |
| 1.25 | 4.46734 | 1.0140692 | 45.6943333 | 427.3333333 | 403.3333333 |

The candidate-pair count rises by approximately 49%, while total K1 wall time
rises by approximately 1.4% in this tested regime. The benchmark is
observational only; it did not optimize candidate construction. The executable
now emits `particle_timesteps_per_second`; the benchmark parser self-test
verifies that field is read and retained.

The separate-cutoff K1 equilibrium fits retain the existing detailed-balance
check, `d ln Keq / d Ee ≈ 1/T`, for each cutoff independently. No compensating
factor was introduced. Historical results below that used `r_assoc=2^(1/6)`
remain historical records and are not rewritten as 1.25 results.

P3.0 is therefore **CLOSED** with `r_assoc=1.25` frozen as the E2 default.

## P3.2 — chemically valid associating-star restart support (CLOSED)

`kg_assoc_stars` now writes an explicit restart pair:

```text
PREFIX.restart.lammpsdat
PREFIX.assoc_restart
```

The LAMMPS-data snapshot preserves positions, velocities, types, molecule IDs,
permanent bonds, and box dimensions. The versioned `KG_ASSOC_RESTART 1`
sidecar records the completed MD step, chemistry parameters and seed,
cumulative creations/breaks, and every active temporary sticker pair using
original 1-based atom IDs. Reload with `--restart-prefix PREFIX`; it is
mutually exclusive with `--input`.

Load rejects malformed schema/version, inconsistent counters, duplicate/self/
out-of-range partners, non-sticker partners, nonreciprocal mappings, and active
temporary FENE distances at or beyond `R0`. Thus the partner topology, `N_assoc`,
intra/inter counts, molecular graph, loop counts, components, largest cluster,
and distinct-neighbor degree are restored exactly at the boundary.

Chemistry acceptance is stateless and keyed by absolute MD step, retained in
the sidecar with its seed. The UAMMD NVT random stream has no exposed
serializable state, so it is re-seeded on reload. A restart therefore preserves
the physical microstate and chemical network exactly, but does not claim a
bitwise-identical post-restart trajectory.

A GPU C1 smoke test (`C1_smoke.e1.lammpsdat`) ran 20,000 fresh chemistry
steps, saved 1,736 active pairs, and reloaded them. A one-step reload retained
all 1,736 pair identities and unchanged cumulative counters; a further 200
steps maintained all chemical and FENE invariants. P3.2 is **CLOSED**. It does
not construct a production restart bank or implement rigorous PBC wrapping.

```bash
./kg_assoc_stars --input systems/e1_equilibrated/C1_long_s12001.e1.lammpsdat \
  --arms 4 --narm 10 --steps 2000000 --output C1_e2_segment
./kg_assoc_stars --restart-prefix C1_e2_segment --steps 2000000 \
  --output C1_e2_continued
```

## P3.3 — C1 E2 chemically valid restart bank (CLOSED)

The six-entry, untracked C1 bank was generated using the P3.2 restart pair,
not historical P3.1 permanent-only snapshots.
For each independent E1 seed (12001 and 12002), it runs once to `t=40,000`,
then continues through chemically valid restart pairs to `t=50,000` and
`t=60,000`. The resulting names are `C1_e2_sSEED_t40000`, `...t50000`, and
`...t60000`, each with `.restart.lammpsdat` and `.assoc_restart` under
`systems/restart_bank/C1/`.

The 10,000-time-unit spacing exceeds several measured slow topological
autocorrelation times. States within a seed are therefore described as
well-separated restart states, not independent replicas; the two E1 seeds are
the independent replicas. `analysis/validate_c1_restart_bank.py` fail-closes
on missing/malformed restart pairs, canonical-C1 parameter mismatches,
topology/partner/FENE invariants, incorrect labels/steps, and reports the
requested network observables and cross-bank mean/range. All six entries were
generated and validated on the dedicated host.

The validated bank is:

| state | bonds | bound fraction | `N_intra` | `N_inter` | `L1` | `L2` | largest-cluster fraction | mean degree | max active distance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| s12001 t40000 | 1781 | 0.8905 | 98 | 1683 | 46 | 36 | 0.997 | 3.274 | 1.078486980 |
| s12001 t50000 | 1779 | 0.8895 | 98 | 1681 | 29 | 36 | 0.997 | 3.304 | 1.104389084 |
| s12001 t60000 | 1770 | 0.8850 | 99 | 1671 | 31 | 31 | 0.996 | 3.280 | 1.097450460 |
| s12002 t40000 | 1764 | 0.8820 | 106 | 1658 | 37 | 29 | 0.996 | 3.242 | 1.095837922 |
| s12002 t50000 | 1786 | 0.8930 | 106 | 1680 | 35 | 33 | 0.998 | 3.290 | 1.100650908 |
| s12002 t60000 | 1790 | 0.8950 | 88 | 1702 | 41 | 44 | 1.000 | 3.322 | 1.082906394 |

Bank means and ranges are: bound fraction `0.889166667 [0.882,0.895]`,
`N_intra` `99.1666667 [88,106]`, `N_inter` `1679.16667 [1658,1702]`,
`L1` `36.5 [29,46]`, `L2` `34.8333333 [29,44]`, largest-cluster fraction
`0.997333333 [0.996,1.0]`, and mean degree `3.28533333 [3.242,3.322]`.
All six states satisfy the chemical/topological invariants and lie within the
P3.1 stationary regime; none is an obvious outlier. The instantaneous spread
of `L1`, `L2`, and `N_intra` is consistent with the slow fluctuations measured
in P3.1. The network remains almost fully connected, and every active-bond
distance is well below `r_assoc=1.25` and `R0=1.5`.

Continuation smokes from `C1_e2_s12001_t60000` and
`C1_e2_s12002_t60000` reloaded with `--restart-prefix`, ran 20,000 MD steps,
passed all chemistry/FENE invariants, and produced reloadable continuation
states. Thus these are chemically valid continuation points suitable as
initial conditions for later C1 production runs. Within-seed states are
well-separated restart states, not independent replicas; only the two seeds
are independent E1/E2 replicas.

## P3.1 — C1 E2 chemical/topological equilibration (CLOSED)

P3.1/C1 E2 is closed for the validated C1 condition. Two independently
E1-equilibrated configurations were continued with chemistry enabled:

| parameter | value |
|---|---:|
| `A` | 4 |
| `Narm` | 10 |
| `Nstars` | 1000 |
| `rho_total` / `rho_poly` | 0.85 / 0.8 |
| `T`, `dt` | 1, 0.01 |
| `Ea`, `Ee`, `nu0`, `Nevery` | 4, 8, 20, 100 |
| `r_assoc` | 1.25 |
| `diagnostic_every` | 1000 MD steps |
| replicas | seeds 12001 and 12002 |
| duration | 6,000,000 MD steps (`t=60,000`) |

Late-time second-half means and event balance were:

| observable | seed 12001 | seed 12002 |
|---|---:|---:|
| bound fraction | 0.8861278333 | 0.886436 |
| `N_intra` | 99.1056667 | 105.323 |
| `N_inter` | 1673.15 | 1667.549 |
| `L1` | 43.4816667 | 43.0906667 |
| `L2` | 33.1753333 | 32.038 |
| largest-cluster fraction | 0.9972976667 | 0.9969376667 |
| mean degree | 3.260016 | 3.249748 |
| creations / breaks | 37770 / 37786 | 37760 / 37767 |
| net bond change | -16 | -7 |
| maximum sampled active-bond distance | 1.2024667519 | 1.19947321283 |

The corresponding integrated autocorrelation times (physical time units) were:

| observable | seed 12001 | seed 12002 |
|---|---:|---:|
| bound fraction | 52.68 | 49.62 |
| `N_intra` | 1741.06 | 2772.68 |
| `N_inter` | 185.91 | 405.54 |
| `L1` | 2104.03 | 1720.92 |
| `L2` | 473.79 | 671.43 |
| largest-cluster fraction | 18.93 | 14.97 |
| mean degree | 228.80 | 457.64 |

Global chemistry is stationary in the second half of both replicas: creation
and break rates are essentially balanced. Bound fraction, inter-star bond
count, largest-cluster fraction, and mean degree agree closely between
replicas. `L1` is slow and strongly correlated, but its independent late-time
means agree closely. `L2` is also slower than global chemistry without a
consistent secular drift. `N_intra` is noisy and strongly correlated; its
fluctuations are consistent with a slow equilibrium observable rather than a
reproducible monotonic transient. The C1 network is almost fully connected.
Active temporary bonds remain below `r_assoc=1.25` in the sampled maxima and
well below FENE `R0=1.5`.

The validated C1 E2 duration is therefore **6,000,000 MD steps at `dt=0.01`**.
This is a conservative validated duration, not a demonstrated minimum.

The existing E2 diagnostic analyzer remains descriptive and fail-closed; no
automatic equilibrium threshold is implied by this closure. C5/C6 E2 remain
unvalidated. Rigorous PBC wrapping/percolation and production observables
remain pending.
