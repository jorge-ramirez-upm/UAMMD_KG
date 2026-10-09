# Associating-star 100M campaign infrastructure

## Status and production gate

The fixed 23-system matrix, external dataset layout, input validator, strict
production entry point, and exact six-channel multi-tau serialization primitive
are implemented. Long production is **not yet authorized**. The following
remaining items are scientific acceptance gates, not optional polish:

1. integrate the correlator serializer, particle state, COM unwrap state, and
   output cursors into the two-slot atomic checkpoint transaction;
2. resolve the UAMMD NVT random-state limitation described below;
3. add the requested decomposed thermodynamic table and full-bead trajectory;
4. run the deterministic and short GPU validation matrix.

The campaign CLI therefore prepares no production automatically and currently
has no production-launch subcommand.

## Frozen campaign

`campaign/campaign_protocol.json` is the machine-readable source of truth. It
expands to 15 associating conditions and eight `NONASSOC` controls. Every
physical system has three independent replicas and exactly 100,000,000
production steps at `dt=0.01`. The shared reference is represented once and
retains all five applicable group labels.

System IDs have the form:

```text
F04_N010_RP080_EE08_EA04
F04_N010_RP080_NONASSOC
```

The ID describes physics, never a replica. Replicas are `r001`, `r002`, and
`r003` below the physical system.

## External inputs and dataset creation

Create a new, empty external dataset root:

```bash
DATASET_ROOT=/absolute/path/to/kg_assoc_100m
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py init \
  --dataset-root "$DATASET_ROOT"
```

This writes one exact requirements file for each of the eight distinct
architecture/density geometries. Place the independently generated LAMMPS
`full`-style files at:

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

No tool generates a substitute when a file is absent. Validate all eight:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py validate-inputs \
  --dataset-root "$DATASET_ROOT"
```

The validator checks atom IDs, molecule IDs, star count, functionality, arm
beads, terminal stickers, connected permanent topology, polymer/solvent bead
counts, box volume, and polymer/total densities. It writes a SHA-256 validation
record next to each input.

Useful matrix queries are non-executing:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py list
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py list --group association
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py list \
  --system F04_N010_RP080_EE08_EA04
```

## E1/E2 provenance and independence

Use three separately generated/configured stochastic preparations per geometry.
Snapshots from one continuous E1 or E2 path are not independent replicas.
Each restart-bank replica must contain:

```text
restart_bank/r001/state.restart.lammpsdat
restart_bank/r001/state.assoc_restart        # associating systems only
restart_bank/r001/e1_provenance.json
restart_bank/r001/e2_provenance.json         # associating systems only
```

E1 may be referenced by all chemistry conditions sharing `(f,N,rho_p)`. E2
may be shared by conditions differing only in `Ea` only after same-`Ee`
equilibrium-invariance validation is accepted. Validated conservative E1
Stage-4 durations exist for `f=4`, `rho_p=0.8`, and `N=10,20,40`; other
functionality/density geometries require their own stationarity evidence.
Only C1 currently has an accepted E2 duration. No general duration is inferred.

After validated restart-bank entries are installed, prepare run manifests:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py prepare-production \
  --dataset-root "$DATASET_ROOT" \
  --system F04_N010_RP080_EE08_EA04 --replicas 1,2,3
```

This command never starts MD.

## Production command after the gate is closed

Build whenever any included `.cu` or `.cuh` changes:

```bash
make -C examples/KG_Assoc kg_assoc_campaign_production
```

The eventual per-replica command is intentionally narrow:

```bash
examples/KG_Assoc/kg_assoc_campaign_production \
  --restart-prefix "$DATASET_ROOT/systems/F04_N010_RP080_EE08_EA04/restart_bank/r001/state" \
  --output "$DATASET_ROOT/systems/F04_N010_RP080_EE08_EA04/production/r001/run" \
  --seed 800001
```

For a control, use its validated permanent-only E1 state:

```bash
examples/KG_Assoc/kg_assoc_campaign_production \
  --input "$DATASET_ROOT/systems/F04_N010_RP080_NONASSOC/restart_bank/r001/state.restart.lammpsdat" \
  --arms 4 --narm 10 --seed 700001 --non-associating \
  --output "$DATASET_ROOT/systems/F04_N010_RP080_NONASSOC/production/r001/run"
```

These commands are recorded now for interface review; do not execute them
until the production gate above is closed.

## Restart decision requiring approval

The multi-tau state can be restored exactly; its deterministic round-trip and
continued-sampling regression test passes. UAMMD's current Verlet NVT API does
not expose the thermostat RNG stream. Existing restart semantics therefore
restore positions, velocities, permanent and temporary topology, absolute
chemistry schedule and counters, but re-seed the thermostat stream. This is a
valid new stochastic continuation from the checkpoint microstate, not a
bitwise replay of an uninterrupted trajectory.

Before checkpoint integration proceeds, approve one of:

1. accept this scientifically equivalent stochastic-continuation definition,
   with exact observable/correlator continuity; or
2. authorize a narrowly scoped `src/*` API change exposing NVT RNG state for
   bitwise continuation.

No `src/*` change has been made.

## Offline analysis

The unified dispatcher is dry-run unless `--execute` is supplied:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py analyze topology -- ARGS
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py analyze bond_dynamics -- ARGS
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py analyze walking_hopping -- ARGS
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py analyze percolation -- ARGS
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py analyze rheology -- ARGS
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py analyze com_msd -- ARGS
python3 examples/KG_Assoc/campaign/kg_assoc_campaign.py analyze fsqt -- ARGS
```

Structural `Rg` orchestration remains to be added because no existing P4
analyzer provides that production estimator.

## First resource envelope

The five C1 32M runs measured about 3.1--3.2 GPU-hours each on the dedicated
TITAN Xp, implying roughly 9.9 GPU-hours for one 100M C1 replica before new I/O
overhead. Particle counts span 32,938--174,250, so a linear particle-count
projection puts the full 69-replica matrix near 1,200 GPU-hours. This is a
planning estimate, not a benchmark; chemistry, architecture, density, and I/O
change throughput. The required representative small/large smoke benchmarks
must replace it before scheduling.

At 32 bytes per bead frame, 1,000 full-bead frames give about 167 GB across
the full matrix. COM trajectories contribute roughly 20--25 GB before
compression; topology, events, checkpoints, and analysis products motivate a
conservative 250--350 GB allocation. Exact storage estimates require measuring
the final binary schema and event rates. No performance or storage result has
been fabricated for untested hardware.
