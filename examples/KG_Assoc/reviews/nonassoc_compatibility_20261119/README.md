# Nine bounded non-associating GPU compatibility tests

Campaign `nonassoc8_compat100k_20261119_v1` authorizes a user-run batch on
`titan` of exactly nine fresh 100,000-step trajectories, 900,000 MD steps
total. It covers r001 of each of the eight accepted geometries and the registered
`F04_N010_RP060_NONASSOC_r002` retry. See [TEST_INDEX.csv](TEST_INDEX.csv)
for all nine identities, exact input paths and hashes, formal acceptance identities,
requested and effective GJF seeds, native commands, and approval SHA256s.
[PLAN.log](PLAN.log), [AUTHORITY.log](AUTHORITY.log), [SOURCE.log](SOURCE.log)
and the individual files under `approvals/` are the execution authority.
The separate validation seed reservation is published at
`banks/production_validation_seed_reservations/nonassoc8_compat100k_20261119_v1.json`
under the dataset root. Its chemistry seed field reserves a shared seed namespace
only. All tests disable the chemistry path.

Starting SHA `c94f50f438ec2c6402b3fd69af5706661cc7e488`. The publication SHA
is the commit containing this dossier. The native executable is the preserved
optimized `kg_assoc_campaign_production_smoke` under
`kg_assoc_100m/builds/production_100m_preserved_20261023_v1/`, SHA256
`e1a00204f8753b4e513e6817169f40ec4aca0854decf52553550aaf25756d6d7`.
Its build is bound to historical source commit
`c1e0b5d472dbf0c5e09274f8079cd92a92d7d3dd`, `-O3`, and compile-time
`KG_ASSOC_CAMPAIGN_STEPS="100000"`. The driver rechecks the build,
transitive source dependencies, committed authority, and exact native argv.
The CPU parser accepted the control flags through its E2-only validation guard
and rejected a runtime `--steps` override. No rebuild is needed.

## Run manually on titan

From the original authenticated workspace at `/home/jramirez/UAMMD_KG`,
update the branch and verify without launching:

```bash
git switch KremerGrest
git pull --ff-only origin KremerGrest
timeout 600 python3 examples/KG_Assoc/reviews/nonassoc_compatibility_20261119/DRIVER.txt --check
timeout 600 python3 examples/KG_Assoc/reviews/nonassoc_compatibility_20261119/DRIVER.txt --status
```

Then run this single user-only command in a persistent terminal:

```bash
python3 -u examples/KG_Assoc/reviews/nonassoc_compatibility_20261119/DRIVER.txt --execute
```

The exclusive workflow lock serializes the batch. The driver starts each native
test with a 600 s wall-time limit and 10 s termination grace. It checks the full
batch before starting and stops at the first failure. Repeating the command
skips only independently validated completions whose output hashes and journals
still authenticate. The isolated output root is
`kg_assoc_100m/validation_outputs/nonassoc8_compat100k_20261119_v1`.
The dormant control history manifests and reserved production seeds are bound
separately and cannot be selected by this driver. The nine prepared directories
each contain only their immutable `run.json` before launch. Use `--status`
after execution or between runs. It authenticates existing completion receipts
and reports a running history without an authenticated native finish as held.

Reserve at least **1 GiB** free on the dataset filesystem. Per test, expect
100 thermodynamic rows, 10 synchronized COM/topology frames, one full-bead
frame, final coordinates and velocities, empty association/event data, one
6-channel correlator with **100,000 samples and 116 lag bins**, and the native
atomic completion record. Keep stdout/stderr and all immutable journals.
The source artifact and output hash checks are CPU work outside the native timeout.

## Preservation and recovery

On timeout, interrupt or failure, retain every output and journal. The shared
adapter records failures and refuses automatic retry or overwrite. If a host
failure or SIGKILL may have left a child running, inspect processes on titan
before considering administrative action. Stop on any numerical, provenance
or native execution failure and preserve the attempt for review.

For a genuinely native-complete test held by an administrative interruption
only, verify the exact identity with `--status`. For example, to reconcile
the registered retry's test if its journal meets the recovery conditions:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/nonassoc_compatibility_20261119/DRIVER.txt --recover F04_N010_RP060_NONASSOC_r002
```

Recovery requires authenticated original started/native-finished evidence
with exit 0, atomic completion, exact endpoints and matching native hashes.
The original adapter rejects numerical, provenance and native failures and
creates an immutable recovery receipt only after repeating independent output
validation. Recovery starts zero MD steps. A missing native-finished journal,
missing outputs or failed validation requires forensic review.

## What the results establish

Independent checks cover exact accepted E1 input binding and geometry, initial
on-disk velocities, stable IDs/types and permanent bonds, final numerical
geometry and available velocities, finite thermodynamic output, bead identity
and finite bead coordinates, and all output cadences. The current executable
reports zero chemistry sweeps, candidate pairs, temporary bonds and temporary
association energy. The control branch leaves the initial partner set empty,
so there are no reversible force or stress contributions by construction.
The executable reports the total microscopic stress and does not expose a
separately measured reversible stress tensor.

The unchanged six-channel estimator is
`G=(Gxy+Gxz+Gyz)/(5T)+(GNxy+GNxz+GNyz)/(30T)`, with channel volume factors
already included. Every-step sampling, `Correlator6(40,16,2)`, finite channel
values, combined G(t), the actual lag grid, and exact pair counts are checked.
Initial GPU-state readback, an independent force/stress comparison and a
candidate oracle are unperformed. The CPU parser probe provides no particle
readback. Candidate searching is deliberately disabled. Historical C1 100k
control evidence remains historical.

Before production activation, require all nine independently validated
completions and receipts, review measured timings and storage, and inspect
the source/seed/geometry/chemistry/stress results, including RP060/r002.
Preserve the N=40 and timestep qualifications. The bounded results address
compatibility, not terminal relaxation or viscosity convergence. A separate
authorization and immutable production activation are required for the 24
prepared 100M histories.
