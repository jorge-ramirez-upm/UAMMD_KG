# Non-associating compatibility review and production activation

**PASS for the exact 24 qualified E1 production starts.** Nine authorized
100k runs provided authentic native completions and passed independent
numerical replay. Eight have ordinary receipts. F03/r001 alone retains its
original numerical failure journal and the published reconciliation for the
campaign-mode thermo parser defect. The original failure was reproduced and
the replay matched that reconciliation byte for byte at the record level.
No compatibility history was rerun or substituted.

The review authenticated each exact approval, E1 input, command, executable,
requested and effective seed, native atomic completion and output hashes.
It independently replayed the endpoint and format validators and compared the
results with the original receipts. Every test recorded 100 finite thermo
samples, ten synchronized COM/topology frames, one full-bead frame, and the
final state. The checks cover stable particle/box/permanent topology identity,
bead coordinates, finite final positions and velocities, and FENE geometry.

Empty direct-E1 partner state and `nu0=0` follow from the authenticated
native control path. Each test had zero observed chemistry sweeps, creations,
ruptures, final temporary bonds and temporary energy. The same authenticated
implementation excludes reversible stress by construction with no active
partners. There is no independently measured reversible stress component,
GPU initial-state readback, independent force/stress comparison or candidate
oracle. The recorded six finite channels, actual 116 lag bins, exact counts
and 100,000 samples per test passed the same `Correlator6(40,16,2)` convention
as associating production. The combined estimator
`G=(Gxy+Gxz+Gyz)/(5T)+(GNxy+GNxz+GNyz)/(30T)` passed reconstruction with
the volume factor already included in the channels.

[Measured output, throughput, and validation status](TIMINGS.csv)
and [exact compatibility output and journal hashes](COMPATIBILITY.sha256)
are available for all nine tests. No native warning or error lines were
found. F03/r001's reconciliation is an administrative qualification of
its first validator failure. The failure remains in the dataset.

## Performance and storage

| Geometry | Control 100k seconds | Matching associating 100M mean hours | Linear control estimate, hours per 100M |
|---|---:|---:|---:|
| F03_N010_RP080 | 17.5270 | 7.866 | 4.869 |
| F04_N010_RP020 | 72.0605 | 23.726 | 20.017 |
| F04_N010_RP040 | 36.3607 | 13.879 | 10.100 |
| F04_N010_RP060 | 26.3856 / 26.5251 | 11.255 | 7.349 |
| F04_N010_RP080 | 21.3333 | 9.984 | 5.926 |
| F04_N020_RP080 | 36.8858 | 14.049 | 10.246 |
| F04_N040_RP080 | 66.0438 | 21.992 | 18.346 |
| F06_N010_RP080 | 30.1264 | 14.392 | 8.368 |

The principal sustained reference is the completed 24-trajectory
associating subset with matching geometry and EE08/EA04, totaling
**351.4 hours**. Linear extrapolation of the control smoke rates gives
**255.7 hours** sequentially. These are budgeting scenarios rather than
measured bounds. Reserve roughly **400 hours** including operational
margin, with the two largest geometries accounting for much of that time.
Differences in short and long windows, initialization, thermal behavior,
overhead, and I/O make a precise speedup unsupported.

The nine short outputs total about 147 MB, including snapshots and
headers that occur only once per trajectory. Long-run shared output from
the matching associating histories gives the better estimate for disk:
**45.4 GB** across 24 controls, with **50–65 GB** working allocation.
The driver requires **96 GiB free before each new trajectory**. Check
filesystem usage during the campaign and preserve all results. At review
the dataset filesystem showed about 647 GiB available.
[Reproducible estimates](RESOURCES.csv)

## Exact administrative activation

`nonassoc8_uninterrupted100m_20261119_v1_activation_20261119_v1` binds
the original [24-history dormant plan](../nonassoc_preparation_20261119/plan.log),
the 24 qualified E1 states and eight formal acceptance records, the
original requested/effective seeds and family pairing, the preserved native
100M build and its source map, the complete compatibility review and the
corrected control validator. The plan and dormant registry retain their
original bytes. The separate [activation](ACTIVATION.log) records the active
execution authority. [Approval index](APPROVAL_INDEX.csv) gives each immutable
approval's identity, SHA256, requested/effective seed and exact native argv.
Each approved output directory was pristine except for its original run record.

The driver reuses the E1-aware control adapter and checks the original
plan, approval, source, build, E1 and output bindings before each history.
It uses the just-validated chemistry parser and the existing independent
numerical verifier for 100M stress samples and 195 lag bins. Every native
run uses the original fixed 100M executable, preserved WCA and permanent
FENE, GJF T=1/friction=0.5/dt=0.01, disabled reversible association and
unchanged microscopic stress, output formats and cadence.

## Run on titan

From the original repository root on `KremerGrest`:

```bash
git pull --ff-only origin KremerGrest
timeout 600 python3 examples/KG_Assoc/reviews/nonassoc_activation_20261119/DRIVER.txt --check
python3 -u examples/KG_Assoc/reviews/nonassoc_activation_20261119/DRIVER.txt --execute
```

Run `--execute` manually in a persistent terminal. It runs sequentially
under the existing exclusive workflow lock. The lightweight monitor reads
journal markers without repeatedly hashing completed output:

```bash
python3 examples/KG_Assoc/reviews/nonassoc_activation_20261119/DRIVER.txt --status
```

`receipt_present` is a marker. Use `--check` to authenticate receipts and
output hashes. An interrupted, failed, inconsistent, or pending native
history holds the batch. Preserve the existing directory, logs, and
journals. If a process might have survived a host failure, inspect host
processes first. There is no automatic recovery, restart or retry.
Rerunning `--execute` skips only independently validated and reauthenticated
completions and refuses any unresolved failure.

## Scientific scope and preservation

N=40 may retain slow collective conformational relaxation. Nonlinear
finite-timestep accuracy remains unresolved, and ten historical E1
families lack contemporaneous input and executable hashes. These controls
start directly from E1. The matched associating production histories
start from qualified E2 endpoints and share their E1 preparation families.
Compatibility and numerical completion provide no equilibrium,
terminal relaxation, or viscosity certification.

Starting SHA `3899a57fa22de3cc88af882bfbb0b2d5cab63640`. Replay and
preservation logs record zero GPU/MD work by Codex, all 45 associating
histories and 5,536 historical bindings, all 24 exact E1 states, all nine
compatibility outputs and original journals, and the preserved dormant
preparation. Changes are scoped to this activation dossier.

Reproduce the compatibility review from the repository root with a fresh
directory and a clean checkout:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/nonassoc_activation_20261119/REVIEW.txt work/nonassoc_compatibility_replay_new
```
