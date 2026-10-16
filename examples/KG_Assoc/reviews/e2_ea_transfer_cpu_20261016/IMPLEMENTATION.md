# CPU implementation of Ea reference-state transfer

The explicit derived-preparation path is implemented for
`F04_N010_RP080_EE08_EA06`, `..._EA08`, `..._EA10`, plus a separately marked
Ea4 reseeded reference control. This milestone validates infrastructure only.
It neither executes derived dynamics nor establishes equilibrium invariance or
scientific acceptance at higher barriers.

Starting clean local/remote `KremerGrest` HEAD:
`283ac81058fe49a75ea0c75e44e443c1ff9928e1`. Date: 2026-10-16, Europe/Madrid.
The final SHA is the containing implementation/dossier history, reported after push.
Authority: [feasibility assessment](../e2_ea_transfer_feasibility_20261016/ASSESSMENT.md)
and [scientific protocol](../e2_ea_transfer_feasibility_20261016/PROTOCOL.md).
Those historical documents remain unchanged.

## Implemented behavior

The native `kg_assoc_stars` restart front end accepts an explicit chemical
reseed only with a validated Ea4-to-Ea6/8/10 switch, matching old seed, distinct
positive new seed, fresh MD seed and full branch identity. A same-Ea4 control
requires its own explicit marker. Ordinary restart seed behavior is preserved.
The existing Ea-switch helper, reaction kernel, force law, candidate search and
integrator parameters are unchanged. Unsupported switches, missing markers,
wrong parent/target identity, altered physical parameters, invalid partner state,
invalid counters and output reuse are rejected.

New native options are `--reseed-chemistry-from OLD`, `--derived-branch-id ID`,
`--reference-control`, and `--validate-initial-state`. The last returns before
System/ParticleData construction, output streams or any MD step. It validates
the decoded initial state and prints physical/chemical comparison fingerprints,
parent/child seeds and inherited counters. Fingerprints are comparison checks,
not cryptographic authentication. SHA256 parent authentication belongs to the
planner/validators. Native `--md-seed-info` remains host-only.

`campaign/kg_assoc_e2_transfer.py` implements inspection and immutable preparation.
It pins the reference acceptance SHA256
`525a1834494d88c8f5eae919d87bdcaa6d372e875acd340d1be66b124165ef22`, verifies its
restricted scope and outputs, and accepts only the exact corrected-C1 8M pairs
under `banks/e2_extensions/C1_periodic_recovery_v1/r001..r003/state`.
Original defective 6M endpoints are never eligible transfer starts.
The existing C1 reader authenticates their historical parent evidence without
executing an oracle or changing the accepted files.

Derived plans remain E2-G1 records with an explicit
`lineage_mode=Ea_reference_transfer_v1`. Each history records full target SID,
Ea, original replica, unique attempt/branch ID, exact parent/acceptance hashes,
old/new chemical seeds, requested/effective MD seeds, inherited counter offsets,
branch origin, reservation-file identity and inherited reference qualification.
Absolute step starts at 8,000,000; physical time is step*.01; branch age starts
at zero. Cumulative creation/break counts and every partner are preserved;
there are no synthetic initialization events. Output sidecars keep the validated
version-1 physical/chemical format and store actual target Ea, child seed,
absolute completion step and cumulative counters. Additional lineage is bound
in plan, state/event headers and completion/acceptance provenance.

The same data and unchanged loader feed the original positions, velocities,
particle/molecule identities, box and permanent topology into the simulation.
CPU comparison fingerprints use the loader's single-precision/PBC representation.
They match ordinary restart fingerprints for all twelve target/control branches.
Device loading and dynamical behavior still require a separately approved GPU
smoke. GJ local step/noise memory resets: this is not bitwise MD continuation.
Do not stitch IATs, SEMs, lifetimes, stress or transport across this boundary.

## Stream reservations and later phases

`campaign/e2_transfer_seeds_v1.json` reserves twelve chemical and twelve requested
MD streams, including independent controls. All 24 requested identities are
distinct; all twelve effective 32-bit MD seeds are distinct and checked against
existing plans, acceptances, reservations and legacy state/sidecar evidence.
Native seed queries agree with the Python effective-seed calculation.

| Branch | Chemical seeds, r001/r002/r003 | Requested MD seeds |
|---|---|---|
| Ea4 control | 620401 / 620402 / 620403 | 630401 / 630402 / 630403 |
| Ea6 | 620601 / 620602 / 620603 | 630601 / 630602 / 630603 |
| Ea8 | 620801 / 620802 / 620803 | 630801 / 630802 / 630803 |
| Ea10 | 621001 / 621002 / 621003 | 631001 / 631002 / 631003 |

Reservations are consumed by a prepared immutable attempt, not by inspection.
Failed or used attempts cannot be overwritten or silently reclaim a reservation.
The global E2 preparation lock protects concurrent preparation. For a later
separately authorized phase, provide a NEW reservation JSON under
`DATASET/banks/e2_seed_reservations/` via `--seed-reservations`. It must have the
same twelve target/control identities and fresh collision-free streams. Never
edit an existing reservation set. Plans and standalone lineage validation bind
the selected file and its SHA256, so an older smoke keeps its original stream
identity when a later ordinary branch reserves different streams. Ordinary MD
allocation also avoids all these reserved effective seeds. Same-condition
extensions retain chemistry through authenticated ancestry and use fresh MD noise.
Distinct seeds are an operational independence policy, not proof of PRNG
independence; there remain three original parent families across barriers.

## CPU-only dry-run inspection

From repository root, this command prints exact parents, target physics, seeds,
branch identity and prospective command without creating an attempt or running
an executable:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_e2_transfer.py inspect \
  --dataset-root examples/KG_Assoc/kg_assoc_100m \
  --system F04_N010_RP080_EE08_EA06 \
  --output examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE08/derived_F04_N010_RP080_EE08_EA06_inspection \
  --steps 10000
```

Use the other exact target SIDs for Ea8/10. For a control use the reference
Ea4 SID and `--control`. [INSPECTION.json](INSPECTION.json) contains all four
read-only inspections, nine targets and three controls, with complete hashes and
parameters. None of the listed attempt directories exists. Without build evidence,
commands use the canonical executable path only as a preview; the preserved old
binaries must not be used for new transfers.

## Build, preparation and execution gates

The new `kg_assoc_e2.py build --out-of-tree` action forces compilation into a
NEW dataset build directory, preserving every existing executable. It builds only
the three E2 targets, records exact compiler commands/logs, source/executable
hashes and Git SHA, and performs no GPU calculation. Normal in-place builds and
ordinary preparation retain their established behavior.

Derived `prepare` requires a clean committed tree, an authenticated out-of-tree
build, exact scientific evidence and unused reservations. It performs host-only
initial-state and effective-seed checks before writing a plan, three empty replica
directories and an unsigned approval example. This milestone exercises preparation
only inside temporary CPU test roots; no real campaign attempt is prepared.

Existing E2 launch/verify machinery recognizes the new lineage. Execution requires
an explicit plan-bound `e2_derived_smoke` or `e2_derived_segment` approval; a legacy,
missing or unsigned approval cannot authorize it. A smoke is capped at 10k steps.
An ordinary segment additionally requires matching completed capped-smoke evidence
for the same code, parents and target physics. Separate smoke/segment streams are
permitted only through explicit derived lineage and distinct reservations.
No launch command is provided or executed in this dossier.

Acceptance readers and schemas preserve full derived lineage, require exact target
system scope and qualification, and reject controls as production initial states.
No acceptance is created by planning or numerical validation. Catalog output
retains branch ancestry/explicit reseed metadata and fork diagnostics rather than
counting descendants as additional independent preparations.

## Readiness and limits

CPU implementation gates pass. The next permissible scientific calculation is a
separately authorized capped GPU smoke using an authenticated committed build;
no such calculation is authorized or performed here. The post-commit CPU build
receipt, when present, is recorded separately in BUILD_RESULTS.md so the build's
source manifest remains immutable.

GPU candidate-oracle behavior after the new restart, device state restoration,
numerical trajectories, coupled-sampler invariance and slow-topology relaxation
remain untested by this milestone. Reference initialization bias, incomplete
structural decorrelation, corrected historical lineage and historical executable
limitations remain qualifications. The twelve accepted systems remain twelve;
there is no registry selection, production preparation or launch.

[VALIDATION.md](VALIDATION.md) gives tests, authentication and reproducibility.
