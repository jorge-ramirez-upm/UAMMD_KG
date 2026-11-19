# Dormant non-associating production preparation

`nonassoc8_uninterrupted100m_20261119_v1` binds 24 exact 100M histories
(2.4 billion planned steps) in a separate dataset subtree under
`kg_assoc_100m/production_preparations/`. All production clocks start at zero.
Each history retains its E1 preparation seed and endpoint step as provenance and
uses a fresh requested/effective GJF stream. The reservation field
`chemistry_seed` reserves the shared integer namespace for compatibility with
the existing seed ledger. The native control path uses nu0=0 and performs no
reaction sweeps. Family pairing is recorded in the E1 acceptance records.

The Git-published `dormant_registry.log`, `plan.log`, and `reservation.log`
bind the accepted states, administrative/source hash map, preserved -O3 builds,
exact commands and destinations. The seed reservation is also visible to
the existing dataset seed scanner. Each isolated runtime directory contains
one immutable `run.json` bound to the plan hash. Status is dormant, with GPU
execution authorization false. Initial preparation requires a new campaign
identity and refuses existing files. The read-only check reconstructs every
command, checks build, source and E1 hashes, scans known seed ledgers, and
rejects extra files in the dormant run directories.

```bash
timeout 600 python3 examples/KG_Assoc/reviews/e1_qualification_20261119/QUALIFY.txt
timeout 600 python3 examples/KG_Assoc/reviews/nonassoc_preparation_20261119/CONTROL.txt check
timeout 600 python3 examples/KG_Assoc/reviews/nonassoc_preparation_20261119/TEST_CONTROL.txt
```

The control adapter reuses the associating adapter in a private Python namespace.
It reuses its immutable journals, native completion authentication, receipt
binding, authenticated skip, and preserved failure behavior. The exclusive
workflow lock covers launch preflight and execution. The control-specific
checks require an exact accepted E1 parent, direct non-associating argv, no
chemistry sweeps or candidate pairs, no event rows or temporary bonds, zero
temporary energy and counters, and identical final permanent topology, IDs and
box with valid positions and velocities. The existing endpoint validator checks
thermodynamic, topology, COM and bead output cadences. The established stress
reader checks six-channel G(t), every-step sampling and actual multi-tau
lag/count semantics, including 195 bins at 100M.

Launch requires a separate Git-committed activation binding and exact per-history
GPU approvals. This milestone publishes only the dormant preparation. The
activation gate fails before taking the lock or starting any process. After
future authorization, failed or interrupted attempts hold the batch. Any fresh
attempt or administrative reconciliation requires a separately reviewed identity
or recovery decision. The shared journal implementation retains its original
failure receipt and refuses automatic retry or overwrite. Native completion is
independently validated before a history can be skipped. Production is
uninterrupted and trajectories cannot be stitched or resumed.

## Compatibility before activation

The preserved optimized `kg_assoc_campaign_production_smoke` build comes
from the same native sources and CLI as the 100M binary. Its manifest records a
100,000-step compile-time cap, and both executable digests and transitive
native build dependencies are authenticated. The historical C1 100k
non-associating result took 21.06 seconds and observed zero reactions. Current
executable compatibility remains to be established on the qualified inputs.

Request separate bounded authorization for one 100k history for r001 of each of
the eight geometries, plus the registered RP060/r002 retry (nine runs). Use
the preserved smoke executable, fresh compatibility seeds, one isolated
destination per test, and a 600 s timeout per test. Use the planned direct
`--input ... --arms ... --narm ... --non-associating` command form with the smoke
binary, distinct seeds and fresh destinations. Example test objectives:

- F03 and F06 exercise functionality limits and permanent topology checks.
- RP020 and RP080/N40 exercise the largest particle counts, sparse/dense
  composition, runtime and output cost.
- RP060/r002 exercises exact registered-retry resolution and loaded velocities.
- All nine verify native provenance, zero chemistry, final geometry, 100,000
  stress samples and exact lag/count/normalization checks, 100 thermodynamic
  rows, 10 synchronized topology/COM frames, and one bead frame.

Review the bounded results before reserving more compatibility streams or
authorizing production. Runtime planning scenarios from the readiness dossier
are roughly 210–351 GPU-hours with about 450 GPU-hours budgeted including margin.
The shared-output estimate is 45.4 GB measured from analogous associating files,
with 50–65 GB working storage and 96 GiB provisioned for controls. Replace these
estimates with observed control throughput and file sizes after compatibility.

The E1 qualification carries finite-timestep and N=40 slow-mode limits. Neither
a compatible executable nor completed outputs establish stress convergence or
terminal relaxation. Preserve the accepted E1 files, E2 banks, completed
associating outputs and their 45 immutable records throughout compatibility
and publication. No native source, protected baseline, initial-state bytes or
historical production record is changed by this administrative milestone.
