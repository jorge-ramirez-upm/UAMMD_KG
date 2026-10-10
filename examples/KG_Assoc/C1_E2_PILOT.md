# Fresh C1 E2 pilot

Infrastructure prepared; **three 6M trajectories remain unexecuted**. The user
scientifically accepted all 24 E1 histories with the retained N=40 qualification.
This pilot uses only the three N=10 C1 banks, not earlier C1 E2 snapshots.
Other E2, production and the P4.8 search remain unauthorized.

## Audited specification

| Parameter | Frozen value |
|---|---:|
| Stars / functionality / arm length | 1000 / 4 / 10 |
| Polymer / solvent / total beads | 41000 / 2563 / 43563 |
| Polymer / actual total density | 0.8 / 0.8500097561 |
| Box volume / cubic side | 51250 / approximately 37.145 |
| T / dt / damping time / actual friction | 1 / 0.01 / 2 / 0.5 |
| Ea / Ee / nu0 / Nevery / r_assoc | 4 / 8 / 20 / 100 / 1.25 |
| FENE K / R0; WCA epsilon / sigma / skin | 30 / 1.5; 1 / 1 / 0.4 |
| Duration / E2 physical time | 6000000 steps / 60000 |
| E1 seeds / new E2 MD and chemistry seeds | 12001–12003 / 22001–22003 |

The existing integer-rounded solvent convention is retained. `kg_assoc_stars`
loads E1 positions and velocities unchanged (`initVelocities=false`) and uses
validated standard KG/WCA/FENE and GJF NVT, **not DPD**. Temperature uses the
same numerical velocities and `2K/(3N)` convention as E1; its small timestep
offset is not a new thermostat-failure threshold. Geometry/topology/density,
finite positions/velocities and permanent bond lengths are checked before use.

Fresh processes start with no temporary bonds and E2 step/time zero; parent
E1 time is provenance, not added to the E2 clock. Reactions run after every
100th MD step, first at step 100 (60000 sweeps total). Exact attempt probability
is `-expm1(-20*exp(-4)*100*0.01)`, about 0.307. Existing candidate ordering,
acceptance, reciprocal valence-one state and shifted-FENE semantics are
unchanged. Both reactions are gated by r_assoc; active bonds remain mechanically
active up to R0. The local LAMMPS reference on `feature/associating-stickers`,
SHA `1c6faf70e94aef2389c208e8c80c60c084a96907`, was inspected. No physics or
reaction algorithm was changed.

Independent units are three distinct accepted E1 preparation histories with
separate E2 processes/seeds. MD and chemistry retain separate existing RNG
mechanisms with the recorded replica seed. Multiple snapshots are not replicas.

## Commands from the repository root

Rebuild after pulling: UAMMD is header-based. Python plotting needs matplotlib.
Set the dataset path for the dedicated host; plan/prepare never launch MD.

```bash
export DATASET_ROOT="$(pwd)/examples/KG_Assoc/kg_assoc_100m"
make -C examples/KG_Assoc kg_assoc_stars
python3 examples/KG_Assoc/campaign/kg_assoc_c1_e2.py plan \
  --dataset-root "$DATASET_ROOT" --replicas 1,2,3 \
  --output "$DATASET_ROOT/aggregate/e2/C1_pilot_plan_$(date -u +%Y%m%dT%H%M%S)"
export E1_REVIEW="$(pwd)/examples/KG_Assoc/C1_E2_PILOT.md"
python3 examples/KG_Assoc/campaign/kg_assoc_c1_e2.py prepare \
  --dataset-root "$DATASET_ROOT" --replicas 1,2,3 --e1-review "$E1_REVIEW"
python3 examples/KG_Assoc/campaign/kg_assoc_c1_e2.py launch \
  --dataset-root "$DATASET_ROOT" --replicas 1,2,3
```

Use retained **scientific acceptance** evidence, not merely numerical completion.
This document records the user's explicit acceptance above and may be used as
its retained statement. The supporting audit remains at
`aggregate/e1/audit_20261010T154908Z_v1/REPORT.md`; keep both records. Alternatively
point E1_REVIEW to a separate retained signed acceptance file. Preparation hashes
the evidence, E1 parents and executable.
The last command is a read-only dry-run. **After explicit authorization only**:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_c1_e2.py launch \
  --dataset-root "$DATASET_ROOT" --replicas 1 --execute
python3 examples/KG_Assoc/campaign/kg_assoc_c1_e2.py launch \
  --dataset-root "$DATASET_ROOT" --replicas 2 --execute
python3 examples/KG_Assoc/campaign/kg_assoc_c1_e2.py launch \
  --dataset-root "$DATASET_ROOT" --replicas 3 --execute
python3 examples/KG_Assoc/campaign/kg_assoc_c1_e2.py status --dataset-root "$DATASET_ROOT"
python3 examples/KG_Assoc/campaign/kg_assoc_c1_e2.py verify --dataset-root "$DATASET_ROOT"
```

Run sequentially, or select `--replicas 1,2,3` in one execution command for
sequential runs. An exclusive pilot lock prevents overlapping launches. Failure
stops the sequence immediately and preserves incomplete artifacts. A killed
process can leave a running record/stale lock: investigate the recorded host/PID,
never remove it blindly. No automatic retry, continuation or acceptance exists.
Preparation refuses nonempty destinations; launch permits only the recorded
unused prepared bank with unchanged input, executable and review hashes.
Neither launcher passes `--force` or loads a historical E2 restart.

## Scientific outputs and analysis

Outputs: `banks/e2/F04_N010_RP080_EE08/r001`, `r002`, `r003`. `.state` retains
the validated 21-column chemistry/network stream. New `.numerics.tsv` adds
synchronized kinetic energy, temperature and min/max permanent-bond lengths.
Both sample at zero and every 1000 steps: exactly 6001 rows. Permanent bonds
are scanned **only at diagnostics**, never every MD step. Invalid extension
remains a hard failure. Existing finite-coordinate/velocity, reciprocal-partner
and temporary-geometry checks remain at reaction/diagnostic checks. Active
geometry maxima/tail fractions are cumulative sampled observations, not
instantaneous or window-local quantities; they do not certify unsampled steps.

`.events` stores every accepted reaction in order, absolute E2 steps and stable
1-based atom/molecule IDs; event time is `step*0.01`. Final
`.restart.lammpsdat` includes positions, velocities and permanent topology;
`.assoc_restart` records parameters, seed, completed step, counters and partners.
`.final_permanent.lammpsdat` and `.final_associations` are archival mirrors.
Chemically valid restart loading is retained; existing RNG reseeding is **not
bitwise continuation**. The fresh pilot does not continue old E2 trajectories.

The completion gate requires success/marker, all seven scientific files, exact
cadence/steps, numerical validity, event-count/partner reconstruction, final
mirror consistency, loaded/final velocities and effective NVT parameter logs.
`complete.json` retains file hashes. Completion is numerical, never scientific
equilibrium acceptance. After all three complete:

```bash
python3 examples/KG_Assoc/analysis/analyze_c1_e2_pilot.py \
  --dataset-root "$DATASET_ROOT" \
  --output "$DATASET_ROOT/aggregate/e2/C1_pilot_$(date -u +%Y%m%dT%H%M%S)"
```

This writes per-replica JSON/CSV, three equal `(0,2M]`, `(2M,4M]`, `(4M,6M]`
window tables, creation/rupture and distinct-neighbor gain/loss rates, time-series,
block-mean and numerical plots, replica/historical comparisons, configuration,
provenance and `REPORT.md`. It reconstructs every sampled network using the
validated P4.5/P4.6 utilities. Parallel bonds change distinct-neighbor counts
only when multiplicity crosses zero. L1 counts pairs of parallel inter-star
bonds; L2 counts distinct-star triangles, not graph cycle rank.

The reused E2 IAT estimator uses biased autocovariance stopped at the first
nonpositive lag. SEM uses variance/effective-count estimates; constant series
have undefined temporal uncertainty, not certified zero uncertainty. Ten
contiguous blocks/window and 30 overall give 2000-time-unit fine blocks.
Historical intra/L1 IATs are approximately 1700–2800: fine blocks are not
independent and estimated IATs can miss slow tails. Three replica means are
the independent units for SEM and 95% Student-t intervals (two degrees of freedom).

The committed P3.1 comparison records accepted historical **last-3M** means,
event counts/rates and selected IATs from VALIDATION.md with source SHA. New
late means cover **last-2M**, explicitly different windows. Optional repeated
`--historical-state /path/to/complete.state` adds hashed C1-compatible raw-history
summaries. No continuation segments or independent histories are stitched.
Historical values are evidence, not pass/fail targets. Numerical validity,
chemical stationarity, network stationarity, replica agreement and final
acceptance require separate review. No arbitrary universal threshold, lifetime
fit or transport inference is introduced; 6M adequacy must be reviewed.

## Validation and resources

```bash
python3 examples/KG_Assoc/campaign/test_c1_e2_pilot.py
python3 examples/KG_Assoc/campaign/test_campaign.py
python3 examples/KG_Assoc/campaign/test_e1.py
examples/KG_Assoc/kg_assoc_stars --self-test
examples/KG_Assoc/kg_assoc_dimer --self-test
```

Deterministic tests cover frozen CLI, dry-run side effects, overwrite/incomplete
guards, failure stop, event accounting, parallel-edge/triangle reconstruction,
window boundaries, full-output validation and reproducible tables/plots. Offline
fixtures deliberately overlap particles: **never use them as MD configurations**.

The implementation host has no working NVIDIA driver. GPU smoke is **pending**;
on the dedicated host use this explicitly short tool (10000 steps/replica,
new aggregate directory, never pilot banks):

```bash
python3 examples/KG_Assoc/campaign/validate_c1_e2_smoke.py \
  --dataset-root "$DATASET_ROOT" --replicas 1,2,3 \
  --output "$DATASET_ROOT/aggregate/e2/C1_pilot_smoke_$(date -u +%Y%m%dT%H%M%S)" --execute
```

It checks event/network reconstruction, cadence, restart/mirrors, loaded E1
velocities, effective KG parameters and source integrity, and records wall
time/bytes with provisional 6M scaling. This is not a stationarity test.

Provisional time: prior 100k C1 production smoke took about 35 seconds on
TITAN Xp, implying **35 minutes/replica, 1.75 GPU-hours total** by linear
scaling. E2 CPU/chemistry overhead differs; measure the short E2 smoke first.
This is not measured E2 timing or an upper bound. Historical 1M E2 files
measure 0.93 MB events, 0.11 MB state and two 3.83 MB snapshots. Scaling streams
to 6M plus numerics gives roughly **15–30 MB/replica, 45–90 MB total**;
reserve **250 MB** for logs/plots/margin. No per-step stress or full-bead
trajectory is required for this equilibration pilot.
