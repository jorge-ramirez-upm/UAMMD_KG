# Phase B manual host execution and return package v1

This handoff follows the user's final instruction: **prepare scripts only; do not
run the campaign here**. No new build, preflight, test, trajectory, executable
approval record, completion record or scientific result was generated for this
handoff. The new helper and its tests have been inspected but **not executed**.
The results report will be written after the user returns authenticated evidence.

The existing frozen Phase B runner, authentication, analyzer, manifest, schedules,
simulator and observer are unchanged. The accepted manifest SHA256 remains
`1fdb92b972137276fda6f1fc0b057192b3ee8afcb5eb345efd8c27c15f557f9a`.
See [the preparation report](E1_STAGE_D14_PHASE_B_PREPARATION.md) for scientific
definitions, exact targets, historical tests and build identities. The separate
operator helper is not a new scientific adapter and is not added to frozen hashes;
its own SHA256 and source commit are recorded in the external handoff anchors.

## What will run, only when you request it

Exactly eight sequential runs: N32, M64, Z512, Ne4, nu_hop100, T10,
kb30, b0=kBT=zeta=1, A2=5, double precision, renewal on, stress off.

| Cell | kappa | dt | Steps/replica | Seeds |
|---|---:|---:|---:|---|
| B1 | 0 | .0001 | 100000 | 721400101, 721400102 |
| B2 | 0 | .00025 | 40000 | 721400201, 721400202 |
| B3 | 10 | .0001 | 100000 | 721400301, 721400302 |
| B4 | 10 | .00025 | 40000 | 721400401, 721400402 |

Total: 560000 BD steps; expected 4096000 attempts. Independent exact-equilibrium
initializations; no shared seeds/configurations. The committed schedules supply
101 regular backbone frames, 26 E1 frames, four audit snapshots per run. The
timestep-specific first-step frames remain diagnostics, not shared-time samples.
No alternative schedule, interpolation, extra run, retry, B/C transition or D2
experiment is provided by this helper.

The helper has separate `prepare`, `execute`, `completion` and `analyze` commands.
No arguments just displays help; nothing probes the GPU or starts a process.
Only `execute --authorize-phase-b-execution` can invoke the accepted scientific
runner. `prepare` needs an explicit `--write-approved-record` and never runs
dynamics. Use the exact commands below on the approved RTX3060Ti Linux host.

## 1. Select the repository and a durable fresh evidence location

Run from the updated `slip-springs` checkout containing this guide/helper. Keep
the checkout clean. The remote starting HEAD was verified as
`c3ddfaca8160ee1c7bc58b3cd29b2f91e12eeccd`. The helper will compare local and
remote branch HEAD again during preparation. No live GPU-host preflight was
performed for this handoff.

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
E1_HOST="$PWD/examples/slip-springs/e1_d14_phase_b_host.py"
E1_BUNDLE="$HOME/e1-evidence/phase-b-v1"
```

Choose a different fresh name before starting if that bundle already exists.
Keep it on durable storage with the approved free space; `/tmp` may be cleared.
The helper creates the bundle and refuses overwrites. Raw outputs go in its
`campaign/` child. Approval, preflight, anchors and logs live outside that raw
child. Do not move or edit evidence, the checkout or build paths during execution
or analysis. Maintain a separate backup after completion.

Optional CPU-only checks of the newly supplied helper, **not run by Codex**:

```bash
timeout 120s python3 examples/slip-springs/tests/test_e1_d14_phase_b_host.py -v
```

These four tests check exact limits, Phase B-only argv, explicit gate refusals,
completion parsing and summary retention of individual replicas. They do not
launch simulations or validate scientific results.
Earlier frozen D1.4 technical-test evidence is in the preparation report; it
does not constitute a passing result for this new handoff script.

## 2. Authenticate the build/host and create the external approval

The default build receipt is `/tmp/e1-d14-build/build.json`, expected SHA256
`79a9dca3f43e5982abe1e21c828d70ef008bc2e2026bf43e05e9bd05f289d7d5`;
binary SHA256 is
`45876d8b61150b6259236d31e7a2d0f5f1418f710f444430b8fd4fbd4c8eb063`.
The clean scientific checkout is `/tmp/e1-d11-source` at
`0dea651b58171a72206774bcebb2f4c74960069b`.

```bash
python3 "$E1_HOST" prepare --bundle "$E1_BUNDLE" --write-approved-record
```

This checks the frozen configuration, live source/dependency/compiler/library/
binary closure, local/remote preparation HEAD and expected GPU/runtime identities.
It creates a true external approval using the user's exact authorization, then
runs a second read-only preflight that must have zero blockers. It never starts
a trajectory. Expected UUID is `GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274`;
expected environment SHA256 is
`05e9f076948c5d562925dd24b9d9d47bc8611698516efea13808029ad5d8c79a`.

All eight approved values are hardcoded in the operator helper and preserved in
the external approval, with no changes to frozen configuration:

| Field | Value |
|---|---:|
| per_run_seconds | 120 |
| aggregate_seconds | 3600 |
| per_run_output_bytes | 134217728 |
| aggregate_output_bytes | 1073741824 |
| max_host_rss_bytes | 2147483648 |
| min_available_host_bytes | 8589934592 |
| min_free_gpu_bytes | 4294967296 |
| min_free_disk_bytes | 10737418240 |

Preparation prints `anchors_sha256` and `approval_sha256`. **Copy both literal
values into a separate note/message outside the evidence bundle.** Set:

```bash
E1_ANCHORS_SHA='PASTE_THE_PRINTED_anchors_sha256_HERE'
```

Do not read an unverified digest from a changed file as its own trust anchor.
Any blocker means stop and send the error/preflight. Do not bypass, edit limits
or start a different campaign to work around it. A failed preparation bundle
is preserved, not automatically reused.

If the old build or `/tmp` source checkout is missing, stop before execution.
A new authenticated build is permitted by the user, using the frozen runner:

```bash
timeout 300s python3 examples/slip-springs/e1_d14_phase_b_runner.py build \
  --source-tree /PATH/TO/CLEAN/ACCEPTED/SOURCE --build-root /FRESH/BUILD/ROOT \
  --cuda-home /usr/local/cuda --arch sm_86 --cxx /usr/bin/g++
```

The source path must already be a clean accepted checkout with its correct
repository origin; the build root must not exist. Preserve the returned receipt
and binary SHA256. With a new fresh bundle, pass `--build-receipt PATH`,
`--build-sha256 PRINTED_RECEIPT_SHA` and `--binary-sha256 PRINTED_BINARY_SHA` to
`prepare`. This still checks the full live closure and approved environment.
The helper does not rebuild or change identities automatically.

## 3. Execute once

Only this next command starts the scientific campaign. Run it in a stable
terminal session. The helper replaces itself with the accepted runner, preserving
its signal/process-group supervision, serial order, resource checks and failure
receipts. It redirects console output to the two external runner log files and
prints those paths before starting.

```bash
if python3 "$E1_HOST" execute --bundle "$E1_BUNDLE" \
    --anchors-sha256 "$E1_ANCHORS_SHA" --authorize-phase-b-execution; then
  printf '0\n' > "$E1_BUNDLE/runner.exit-code.txt"
else
  e1_exit_code=$?
  printf '%s\n' "$e1_exit_code" > "$E1_BUNDLE/runner.exit-code.txt"
  tail -n 40 "$E1_BUNDLE/runner.stderr.log"
  echo 'STOP: preserve this evidence; do not resume, rerun or analyze partial data.'
fi
```

Proceed only after exit code zero. To view progress from a separate terminal,
read `campaign/status.json` and `runner.stderr.log`; do not alter them. The
runner may spend time authenticating output between trajectories. Estimates
in the preparation report are planning proxies; exact limits are never enlarged.
No automatic retry or additional simulation is authorized by this runbook.

## 4. Record the returned completion hash externally

After successful execution only:

```bash
python3 "$E1_HOST" completion --bundle "$E1_BUNDLE" --anchors-sha256 "$E1_ANCHORS_SHA"
```

This requires both the successful runner preflight and the returned completion
JSON in its log, checks the returned root and marker digest, and writes
`external-completion.json` outside raw evidence. It does not certify scientific
acceptance. **Copy the printed completion_sha256 into the separate note/message
before analysis**, then set:

```bash
E1_COMPLETION_SHA='PASTE_THE_PRINTED_completion_sha256_HERE'
```

Never fabricate a completion record from a partial directory or a failed runner.
The separate analyzer reauthenticates every member of the full eight-run cohort.

## 5. Authenticate, analyze and package

```bash
python3 "$E1_HOST" analyze --bundle "$E1_BUNDLE" \
  --anchors-sha256 "$E1_ANCHORS_SHA" --completion-sha256 "$E1_COMPLETION_SHA"
```

This calls the **unchanged accepted analysis adapter**, which authenticates all
eight runs before reduction and again before publication. It writes `analysis.json`
outside raw evidence, a readable `reply/summary.md`, and `reply/reference-index.json`.
It packages these plus the frozen manifest/schedules, build log, per-run
process/exit/resource receipts, timing/counter/schema metadata and logs
into `phase-b-return.tar.gz`. No raw CSV, executable or particle trajectory is
included in that return archive. Every raw campaign file has a size/SHA256 entry
in the reference index. Original raw data and binaries remain preserved locally.
The archive supports interpretation and provenance review; full independent raw
authentication still requires access to the preserved campaign and build closure.
The helper prints the analysis and archive SHA256 values. Save them in your
separate note as well. Analysis/package failures stop without overwriting or
silently adopting existing outputs; send the error for review instead of retrying.

The complete JSON contains individual replica series, exact-reference deviations,
within-replica changes, predefined early/late summaries, shared-time independent
timestep contrasts, tangents, connector moments/CDFs, occupancy/population
diagnostics, both joint statistics and preliminary ACFs. R=2 intervals are weak;
frames/chains/springs are not additional independent replicas. All IATs remain
unresolved. The short human summary's initial/final columns are for navigation;
they are not an endpoint-only equilibrium verdict.

## What to send back to Codex or ChatGPT

On success, upload **`phase-b-return.tar.gz`**, and paste this filled-in text:

```text
Stage D1.4 Phase B: exactly eight runs, no retries/additional simulations.
Repository/operator commit: [anchors.json operator_source_sha]
Evidence path: [absolute E1_BUNDLE/campaign]
Manifest SHA256: 1fdb92b972137276fda6f1fc0b057192b3ee8afcb5eb345efd8c27c15f557f9a
Anchors SHA256: [...]
Approval SHA256: [...]
Completion SHA256: [...]
Analysis SHA256: [...]
Return archive SHA256: [...]
Runner exit code: 0
Please assess drift across all times, exact-reference discrepancies, individual
replica behavior, shared-time timestep contrasts and ACF support. R=2 is weak;
do not issue an equivalence/preservation pass or launch Phase C/D2.
```

The compressed analysis should be much smaller than the full JSON; actual size
is not yet measured. If upload limits intervene, send `reply/summary.md` and
`reply/reference-index.json` first, plus the pasted trust anchors, then provide
the full analysis/provenance archive in a subsequent upload. The small summary
alone cannot support all scientific interpretation or independent authentication.

On failure, send the exact command, exit code/error, both runner logs if created,
preflight JSON, external approval/anchors, `campaign/status.json` if present,
and the failed run's `execution.json`, `process.json`, `stdout.log` and `stderr.log`
where available. State explicitly that the cohort is incomplete; no successful
completion/analysis should exist. Preserve the entire raw root locally.

No Phase C, D2, long-time mixing, terminal relaxation, reptation, viscosity or
rheological conclusion is authorized by these commands.
