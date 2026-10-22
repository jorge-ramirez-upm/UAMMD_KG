# D1.5 — self-contained local execution handoff

**Preparation only. No benchmark, T=1 pilot or T=100 exploration is authorized.**
No tests, builds, GPU probes, reference sampling or simulations were executed
when preparing this handoff. The new workflow itself awaits local execution.
It delegates to the frozen D1.5 tools; it is not another scientific runner or
analyzer. A readiness success means **ready for independent review**, not
scientific acceptance or execution permission.

Starting preparation: `7a2d75a4f55976f1f36d5880c81e7e6a3ec8edda`.
Accepted scientific source: `0dea651b58171a72206774bcebb2f4c74960069b`.
Benchmark manifest SHA256:
`4c6805221db1ddf3d3ffaa6ae62f2f890150b6c967214be97642546941454dc9`.
The authority remains the committed
[preparation report](E1_STAGE_D15_LARGER_SYSTEM_PREPARATION_V1.md), manifest and
original [operator guide](E1_STAGE_D15_OPERATOR_GUIDE_V1.md). Their bytes,
scientific implementation, D0 tolerances and historical evidence are unchanged.
Use this shorter operational handoff for the **T=.1 benchmark only**.

## Stage A — Local readiness

**Run on your Linux workstation.** This stage performs CPU tests, one fresh
CUDA build, the two existing nine-step technical GPU fixtures, then a read-only
GPU/environment preflight. It never authorizes or launches the benchmark.
The projection calculation is metadata arithmetic, not equilibrium sampling.

Requirements: clean `slip-springs` checkout matching the current remote HEAD,
GitHub read access already configured noninteractively, Python 3.10+ with NumPy,
the accepted CUDA 13 installation at `/usr/local/cuda`, `/usr/bin/g++`, the
pinned RTX 3060 Ti UUID
`GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274`, and durable free disk space.
Other GPUs/toolchains need separate review; there is no identity bypass.
Nothing is installed or downloaded automatically.

The current development checkout is separate from the main checkout, whose
unrelated KG work must be preserved. Run this absolute command from any directory:

```bash
python3 /tmp/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d15_local.py readiness \
  --evidence-parent /home/jramirez/UAMMD_KG-evidence/d15 \
  --cuda-home /usr/local/cuda
```

If you use another workstation/checkout, change only the absolute entry-script
and durable evidence-parent paths. Do not switch or clean a dirty main checkout.
The script checks origin, branch, clean status, ancestry and live remote HEAD;
it does not fetch/merge/update an out-of-date checkout automatically. It creates
a unique `readiness-*` directory and detached `preparation/` and `source/`
worktrees there. Subsequent commands use this durable preparation copy, not
`/tmp`. Preserve the main repository's Git common directory as well as this root.
Durability of the chosen filesystem, capacity and backup policy remain operator
responsibilities; the script rejects the usual temporary directories.

It prints `D15_ROOT=/home/jramirez/UAMMD_KG-evidence/d15/readiness-...` immediately.
Copy **that one actual path** into a new shell as follows (replace the example):

```bash
export D15_ROOT=/home/jramirez/UAMMD_KG-evidence/d15/readiness-REPLACE_WITH_PRINTED_SUFFIX
```

Stages and individual exit codes are retained under `logs/`. Sequence:

1. Verify Git/manifest identities; create fresh durable worktrees.
2. Recalculate projections without execution; byte-compare with the frozen file.
3. Run `test_e1_d15_local.py`, `test_e1_d15_preparation.py`,
   `test_e1_d14_phase_b.py`, `test_e1_d13_phase_a.py`, `test_e1_d12_plan.py`,
   and `test_e1_d1_pilot.py`, each limited to 120 seconds.
4. Delegate a fresh double-precision CUDA13/sm86 build to `e1_d15_host.py build`.
   The outer bound is 480 seconds; existing inner dependency/compilation bounds
   remain unchanged. No adopted/no-op build can pass.
5. Run only `test_e1_d14_phase_b_technical.py` with the **required positional
   executable path**, bounded to 120 seconds. These are N3/M4 and N17/M2,
   nine-step technical fixtures, not M256 benchmark cells.
6. Read-only preflight, bounded to 180 seconds, with no approval or execution
   flag. Its sole permissible blocker is
   `independent approval and explicit resource budgets required`. Exit code 0
   alone is insufficient. Other blockers fail readiness.
7. Write `readiness.json`, command/identity proofs, false review/approval drafts
   on success, and a small return archive even on ordinary failure/interruption.

Each failed command stops the sequence without retries. Preserve failed evidence;
start a new Stage A only after reviewing/correcting the cause. Force-kill, machine
shutdown or full disk may prevent automatic packaging; the command below can
package the evidence that survived without rerunning anything. Do not infer a
pass from an existing log or partial build receipt.

**Read-only with respect to existing evidence; creates a fresh archive only:**

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" package \
  --root "$D15_ROOT" --kind readiness
```

If failure preceded creation of `preparation/`, run `package` using the original
entry-script path instead. No build, test, probe or simulation runs in `package`.
Stage A already packages automatically; this command makes an additional fresh
archive without overwriting the first.

Expected output:
`$D15_ROOT/returns/readiness-return-<unique>.tar.gz` and the adjacent
`.tar.gz.sha256`. Send **one matching archive and checksum file**, plus any
terminal error if packaging failed. Inside are `SUMMARY.txt`, test status/logs,
full build receipt and binary SHA256 (never the executable), preflight/environment
identity, frozen manifest, preparation revision/script identities, readiness
errors, `contents.json` and `SHA256SUMS`. Logs exceeding 64 KiB contain labeled
head/tail excerpts with the full original file's size/hash. JSON receipts are
complete. The uncompressed payload is capped at 8 MiB; oversized mandatory
evidence stops packaging rather than being silently dropped. The original full
evidence stays locally at its absolute paths. Checksums establish byte identity,
not an independent signature or approval.

## Stage B — Benchmark execution

**STOP for separate review of the readiness archive.** Nothing in Stage A
grants this authorization. Do not run Stage B until a reviewer explicitly
approves the exact four-cell scope, machine/build identities and all eight
resource budgets.

| Cell | M | N | kappa | dt | T | Z | Seed |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 256 | 32 | 0 | .0001 | .1 | 2048 | 721510101 |
| 2 | 256 | 32 | 0 | .00025 | .1 | 2048 | 721510201 |
| 3 | 256 | 32 | 10 | .0001 | .1 | 2048 | 721510301 |
| 4 | 256 | 32 | 10 | .00025 | .1 | 2048 | 721510401 |

This table documents the frozen manifest, not an alternative input file.
Common parameters/commands/schedules are taken directly from that manifest:
Ne=4, A2=5, nu_hop=100, kb=30, kBT=zeta=1, exact E1 initialization, renewal on,
stress off. The utility offers no duration, seed, cell or manifest override.

On readiness success the script fills the identities and all artifact paths/
digests in `readiness-review.DRAFT.json`. The independent reviewer makes a
**separate external copy**, inspects the evidence, supplies `review_reference`
and only then decides whether to set `all_local_preparation_checks_reviewed=true`.
Do not edit the collected evidence or original drafts.

To collect this reviewed record's pointer/hash into a still-false approval draft
(preparation only, **no execution**):

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" approval-draft \
  --root "$D15_ROOT" --review /absolute/path/to/independently-reviewed-readiness.json
```

The resulting `benchmark-approval.LINKED-DRAFT.json` still has
`execution_authorized=false`, null decision reference and null limits. A reviewer
must make a separate external approved copy, retain the exact readiness pointer,
set an independent `approval_reference`, and explicitly approve:
`per_run_seconds`, `aggregate_seconds`, `per_run_output_bytes`,
`aggregate_output_bytes`, `min_free_disk_bytes`, `min_free_gpu_bytes`,
`max_host_rss_bytes`, `min_available_host_bytes`. Existing ceilings remain
120 seconds/run, 3600 seconds/cohort and 5 GiB output; these are ceilings,
**not approved budgets**. `benchmark_review` must remain null. Only the reviewer
may set `execution_authorized=true` and supply the independently trusted SHA256
of that exact approved file. Keep the review/approval and their referenced
artifacts permanently at the approved absolute paths.

**Actual benchmark execution, after separate approval only:**

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" benchmark \
  --root "$D15_ROOT" \
  --approval /absolute/path/to/independently-approved-benchmark.json \
  --approval-sha256 REPLACE_WITH_INDEPENDENTLY_TRUSTED_APPROVAL_SHA256 \
  --execute-reviewed-benchmark
```

Do not substitute a just-calculated digest of an unreviewed file for the trusted
approval anchor. No helper in this handoff creates a true approval.
The wrapper invokes the existing frozen host runner, which rechecks the manifest,
source/build/dependency/runtime/GPU identities, reviews, all resource/headroom
limits, fresh output root, per-run schemas/counters/receipts and whole cohort.
There are exactly four sequential benchmark processes, no automatic retry,
resume or alternate seed. Output is `$D15_ROOT/benchmark-campaign/`. A launch
record also prevents relaunch after early failure; do not delete it to retry.
The outer watchdog is the approved cohort budget plus 600 seconds for bounded
preflight/authentication/cleanup; it does **not** enlarge the inner simulation
budget. Per-run polling/resource limits remain the existing runner's limits.

The completion SHA is captured only from the successful authenticated runner
return, not inferred by hashing an unverified completion marker. Preserve
`benchmark-launch.json`, `benchmark-result.json` and the original full cohort.
T=1 and T=100 are unapproved and have no entry point in this utility.

## Stage C — Return results

**Authentication and summary only; no simulation:**

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" summarize \
  --root "$D15_ROOT"
```

This delegates whole-cohort authentication and summary to the unchanged D1.5
host, bounded to 600 seconds, then creates
`$D15_ROOT/returns/benchmark-return-<unique>.tar.gz` and its `.sha256` file.
The archive includes the four-run performance summary, observer and event
timings/rates, output sizes, host RSS and GPU headroom observations, per-run and
approval/completion identities, and full-evidence references/hashes. It excludes
raw CSV histories and executable binaries. Nested timers are not additive;
GPU peak usage is not measured. The M64 comparison uses the existing hash-bound
Phase A timing record (stiff N32 only), not newly authenticated M64 raw evidence.
Different durations/sampling make this a descriptive cost comparison, not a
measured scaling law. No new scientific acceptance is inferred.

To repackage an existing authenticated summary, or package failed/incomplete
execution evidence **without claiming a successful cohort**:

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" package \
  --root "$D15_ROOT" --kind benchmark
```

Packaging checks saved summary/anchor byte identities but does not rerun full
raw-evidence authentication. Run `summarize` again if a fresh full authentication
is needed; it creates a new report rather than overwriting one.
Send the printed archive and its matching `.sha256` file to ChatGPT. Retain all
full local evidence/worktrees and externally trusted approval/completion anchors.
The archives contain local paths and GPU/build identifiers for review; inspect
them before uploading. No credentials or inherited environment dump is collected.

## Operational corrections and remaining review

The original frozen tools/guide remain unchanged. This additive workflow fixes
temporary evidence paths, cross-shell variable dependence, manual digest copying,
the required tiny-test binary argument, insufficient outer build timeout,
preflight exit-code ambiguity, execution's two-JSON stdout, and missing failure/
compact packaging. New wrapper checks are supplied for local execution, not
claimed passed. Only static review was performed for this preparation.

Remaining gates: actual local CPU/tiny GPU results; fresh compilation/dependency
proof; exact GPU/toolchain/runtime compatibility; review of readiness evidence;
explicit eight-budget/headroom decisions and separate benchmark authorization;
then review of authenticated four-run results. No D0 tolerance, frozen manifest,
scientific kernel, initializer, RNG, observer or prior evidence was changed.
