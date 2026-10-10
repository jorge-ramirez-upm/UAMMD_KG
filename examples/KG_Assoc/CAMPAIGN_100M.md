# Associating-star 100M campaign

## Production policy

Each replica is one uninterrupted 100,000,000-step trajectory at `dt=0.01`.
Production has no checkpoint, continuation, recovery, or resume mode. The
executable reads an E2 pair only as its initial condition and never writes a
reloadable production state. A run is complete only when its atomically
committed `run.complete.json` reports exactly 100,000,000 steps. Otherwise the
campaign tools classify it as incomplete and will not resume it.

Existing E1/E2 formats and loaders remain unchanged. E1 banks are shared by
systems with the same `(f,N,rho_p)`. Accepted E2 banks are keyed by
`(f,N,rho_p,Ee)` and may be shared across production `Ea` values only after
equilibrium-invariance evidence is accepted. The standalone correlator
serialization utility remains tested but is unused by campaign production.

## Matrix and dataset

`campaign/campaign_protocol.json` expands to 15 associating systems and eight
`NONASSOC` controls, each with replicas `r001`--`r003`. List them with:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py list
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py list --group association
```

Initialize a new empty external root:

```bash
export DATASET_ROOT=/absolute/path/to/kg_assoc_100m
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py init \
  --dataset-root "$DATASET_ROOT"
```

Place externally generated configurations at exactly:

```text
$DATASET_ROOT/inputs/F03_N010_RP080/initial.lammpsdat
$DATASET_ROOT/inputs/F04_N010_RP020/initial.lammpsdat
$DATASET_ROOT/inputs/F04_N010_RP040/initial.lammpsdat
$DATASET_ROOT/inputs/F04_N010_RP060/initial.lammpsdat
$DATASET_ROOT/inputs/F04_N010_RP080/initial.lammpsdat
$DATASET_ROOT/inputs/F04_N020_RP080/initial.lammpsdat
$DATASET_ROOT/inputs/F04_N040_RP080/initial.lammpsdat
$DATASET_ROOT/inputs/F06_N010_RP080/initial.lammpsdat
```

No missing input is generated. Validate atom/molecule IDs, star topology,
functionality, terminal stickers, permanent bonds, bead types, solvent count,
box volume, and densities:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py validate-inputs \
  --dataset-root "$DATASET_ROOT"
```

## Build and equilibration

UAMMD is header-based; rebuild after included `.cu`/`.cuh` changes:

```bash
make -C examples/KG_Assoc \
  kg_assoc_star_equilibrate kg_assoc_stars kg_assoc_campaign_production
```

Commands are dry-run unless `--execute` is present. Prepare three independent
E1 histories in the shared geometry bank:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py equilibrate \
  --dataset-root "$DATASET_ROOT" --stage e1 \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3 --execute

python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py validate-equilibration \
  --dataset-root "$DATASET_ROOT" --stage e1 \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3

python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py accept-equilibration \
  --dataset-root "$DATASET_ROOT" --stage e1 \
  --bank-id F04_N010_RP080 --evidence /absolute/path/e1_review.md
```

The known conservative Stage-4 durations are used for `N=10,20,40`; they do
not automatically accept new density/functionality geometries.

New E1 preparation uses `dt_dpd=0.002` throughout Stages 1--3b and effective
DPD gamma `4.5`, target temperature `1`, with the existing amplitude ramp.
Final KG integration stays at `dt_wca=0.01`. The E1 executable records and
checks the stored DPD gamma and stochastic-force amplitude for each segment.
The periodic transition diagnostics remain mandatory; no per-step bond scan
has been added. Existing completed banks remain accepted and retain their
original preparation histories.

Before restarting the failed RP060 seed 12002, run the isolated short test on
a GPU host:

```bash
bash examples/KG_Assoc/scripts/validate_e1_rp060_short.sh
```

It retains all outputs and timing in a new `/tmp/kg_e1_rp060_s12002.*`
directory, runs 71,400 DPD preparation steps and 4,500 WCA ramp/promotion
steps, and writes no E1 bank. Inspect its diagnostics and compare timing
before scheduling more E1 work. GPU trajectory validation and benchmarking
of the corrected gamma remain pending on the development host.

E2 duration is explicit; no universal duration is invented. For validated C1:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py equilibrate \
  --dataset-root "$DATASET_ROOT" --stage e2 \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3 \
  --steps 6000000 --equilibration-ea 4 --execute

python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py validate-equilibration \
  --dataset-root "$DATASET_ROOT" --stage e2 \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3

python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py accept-equilibration \
  --dataset-root "$DATASET_ROOT" --stage e2 \
  --bank-id F04_N010_RP080_EE08 --evidence /absolute/path/e2_review.md
```

An accelerated E2 `Ea` may be requested with `--equilibration-ea`, but its bank
must not be accepted until same-`Ee` static/network distributions agree at
replica-level uncertainty. E1/E2 storage and E2 state loading are equilibration
capabilities, not production continuation.

## Prepare, launch, and verify production

Preparation verifies accepted banks, geometry, E2 metadata, valence-one state,
event counters, and target `Ee`; it never starts MD:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py prepare-production \
  --dataset-root "$DATASET_ROOT" \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3
```

Review the dry-run and later launch when authorized:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py launch-production \
  --dataset-root "$DATASET_ROOT" \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3

python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py launch-production \
  --dataset-root "$DATASET_ROOT" \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3 --execute
```

The direct associating command is:

```bash
examples/KG_Assoc/kg_assoc_campaign_production \
  --equilibrated-prefix "$DATASET_ROOT/banks/e2/F04_N010_RP080_EE08/r001/state" \
  --Ea 4 --Ee 8 --seed 701001 \
  --output "$DATASET_ROOT/systems/F04_N010_RP080_EE08_EA04/production/r001/run"
```

A control starts from accepted E1:

```bash
examples/KG_Assoc/kg_assoc_campaign_production \
  --input "$DATASET_ROOT/banks/e1/F04_N010_RP080/r001/state.e1.lammpsdat" \
  --arms 4 --narm 10 --seed 701601 --non-associating \
  --output "$DATASET_ROOT/systems/F04_N010_RP080_NONASSOC/production/r001/run"
```

Status and integrity checks are:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py status \
  --dataset-root "$DATASET_ROOT" --group association

python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py verify-production \
  --dataset-root "$DATASET_ROOT" \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3
```

An interrupted attempt is `incomplete`; there is no resume command. Preserve
its directory for provenance and explicitly prepare a fresh attempt.

## Outputs and conventions

For prefix `run` the executable writes:

- `run.thermo.tsv`: 100,000 samples at 1,000-step cadence;
- `run.stress_correlator`: six channels sampled every step with raw support;
- `run.com_trajectory` and `run.topology`: 10,000 synchronized frames;
- `run.beads.bin`: 1,000 full-bead frames;
- `run.events`: every accepted event with absolute step/time and stable IDs;
- `run.final.lammpsdat` and `run.final_associations`: archival final state;
- `run.complete.json`: atomically committed success marker.

Temporary energy is `U_FENE(r)-U_FENE(rstar)-Ee` per active bond; no WCA term
is duplicated. Permanent energy follows the validated convention assigning the
bonded-pair WCA correction to the permanent bonded component.

`run.beads.bin` is little-endian schema version 2. Its header stores magic,
version, atom/bond counts, box bounds, stable `(atom_id,molecule_id,type)`
arrays, and the permanent bond list needed for graph-based PBC unwrapping.
Frames store a marker, absolute step/time, and stable-ID-ordered wrapped
`float32 xyz`; the box reconstructs PBC. COM coordinates are unwrapped within
the single uninterrupted production run.

## Analysis and aggregation

Analyses require three complete replicas and a new version directory, which is
never silently overwritten:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py analyze \
  --dataset-root "$DATASET_ROOT" \
  --system F04_N010_RP080_EE08_EA04 \
  --analysis topology --version v1 --execute
```

Available analyses are `topology`, `bond_dynamics`, `walking_hopping`,
`percolation`, `rheology`, `com_msd`, `fsqt`, and `structure`. The last reports
PBC-safe star `Rg^2`. Aggregate scalar summaries with:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py aggregate \
  --dataset-root "$DATASET_ROOT"
```

Replicas remain the uncertainty units; partial attempts are never stitched.

## Resource envelope

The 100,000-step C1 smoke took about 35 seconds on the available TITAN Xp,
consistent with roughly 9.7 GPU-hours for one 100M C1 trajectory. Particle
counts span about 33k--174k, so roughly 1,200 GPU-hours for 69 replicas remains
a provisional linear estimate. Binary bead coordinates are about 65 GB;
COM/topology/events/analysis and margin motivate 150--250 GB. Benchmark small
and large geometries before scheduling; these are estimates, not production
measurements.
