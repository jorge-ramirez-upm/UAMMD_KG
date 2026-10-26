# User-run 45-history production campaign

These commands are for the user on `titan`. Codex must not execute `--execute`.
The sole authorized campaign is `assoc15_uninterrupted100m_20261023_v1`:
15 systems, the original three families each, 45 sequential uninterrupted 100M
histories (4.5 billion total steps). No additional history, seed, extension or retry
is authorized. Review ACTIVATION.log, EXECUTION_PLAN.log and approvals/ first.

Use the original evidence workspace; Git alone cannot restore the accepted parent
bank, historical outputs or authenticated executables. No source rebuild is needed
or authorized by this administrative change. A rebuilt binary with a different hash
requires separate review. A clean committed checkout is required.

```bash
cd /home/jramirez/UAMMD_KG
git switch KremerGrest
git pull --ff-only origin KremerGrest
```

If this host lacks the newly published registry, install its exact archived bytes
using this idempotent CPU-only command. It refuses to overwrite a differing file:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/production_activation_20261026/RESTORE.txt
```

Read-only preflight, status and complete preservation audit:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/production_activation_20261026/DRIVER_V2.txt --check
timeout 600 python3 examples/KG_Assoc/reviews/production_activation_20261026/DRIVER_V2.txt --status
timeout 600 python3 examples/KG_Assoc/reviews/production_activation_20261026/VERIFY.txt
df -h /home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m
```

All checks must pass before the user launches. The preflight must initially show
45 prepared histories. Both additional certifications stay `not_performed` under
the approved compatibility decision; they are not PASS. Ea10 retains its original
qualification, including the unresolved r003 triangle/conformation regime.

The exact user-only launch command (run in a persistent terminal on `titan`):

```bash
python3 -u examples/KG_Assoc/reviews/production_activation_20261026/DRIVER_V2.txt --execute
```

Do not add a timeout to the production command. Keep this terminal alive. The
exclusive workflow lock prevents concurrent launches. The driver authenticates
all 45 histories first, runs them sequentially, independently validates every
completion and stops on the first failure. Each native command is fixed verbatim
in EXECUTION_PLAN.log; the user must not invoke binaries directly to bypass journals.
Existing planning files remain immutable. All six stress channels, combined G(t),
lag/count grid and Correlator6(40,16,2) every-step sampling remain unchanged.

Monitor from another terminal with the read-only `--status` command above. Native
progress is in each exact output directory's stdout.log/stderr.log; do not edit
these files. Native-finished status is a hold until independent validation succeeds.
After launch exits, repeat `--check`, `--status` and VERIFY.txt. Completion requires
45 `validated_complete` or `recovered_complete` statuses and zero prepared histories.
The verifier reauthenticates receipts, native journals and every output payload.

## Interruption and recovery

Ctrl-C/SIGTERM terminates and waits for the native child, preserving the attempt.
SIGKILL, power loss or shell loss may leave a surviving child: inspect processes
before any administrative action. Never delete lock files, journals or partial
outputs to force a rerun. This executable has no suitable full MD/correlator
checkpoint; there is no bitwise continuation or authorized restart. Incomplete
histories require a separate decision and fresh identities; none are prepared here.

Repeating `--execute` skips only completions whose outputs and immutable receipts
reauthenticate. Any partial, failed, corrupted or pending-native history stops the
whole preflight. Numerical, chemistry, provenance and native failures cannot be
administratively recovered. Never reclassify or edit a failure journal.

Only a native-complete history whose post-run administration failed can use this
separately authenticated CPU-only recovery action. Substitute the exact approved
system and replica after reviewing its started/native_finished/failure journals:

```bash
python3 examples/KG_Assoc/reviews/production_activation_20261026/DRIVER_V2.txt --recover F03_N010_RP080_EE08_EA04 --replica 1
```

This command never launches MD. It independently revalidates all outputs, preserves
the original failure bytes, creates recovery.json and validated_binding.json, and
is idempotent. Missing native_finished evidence requires forensic review and is
never synthesized. Original sources, executable, approval and outputs must match.

## Resources

The fifteen measured compatibility timings sum to 669.8404 seconds. Linear scaling
to 45 production histories gives 2,009,521 seconds (23.26 days) of integration;
per-history estimates and reference output sizes are in RESOURCES.csv. Startup,
validation, hashing and I/O add time. Short-run extrapolation cannot guarantee
100M performance, long-time numerical stability or scientific convergence.

Scaling measured streamed outputs gives about 152.76 GB across the campaign, plus
about 0.47 GB of fixed final-state references, expanded stress grids and journals.
Chemical event rates and text widths can change. Provision at least 384 GiB free
(412.32 GB), monitor actual usage and retain additional operational headroom. The
driver requires that conservative free-space allowance before starting and before
each next trajectory; it never interrupts a running trajectory merely to reclaim
storage. No raw stress trajectories are introduced. Publication-host free space is
recorded in RESOURCE_REPORT.log; `--check` measures the actual launch filesystem.
