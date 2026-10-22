# D1.5 v1 — manual Linux-host handoff

**PREPARATION ONLY. NO PILOT IS AUTHORIZED.** These commands were NOT executed
in Codex: no build, test, GPU probe, benchmark or trajectory is claimed to pass.
Run them only on the dedicated Linux host after reviewing this preparation.
Do not launch the benchmark or pilot until its separate execution approval is
explicitly given. A command-line flag or a copied template is not authorization.

The accepted CUDA13/sm86/RTX3060Ti identity remains pinned by the older verifier.
Different GPU/toolchain/source identities fail closed and need separate review;
there is no override switch. Python3.10+/NumPy and accepted build dependencies
must already exist; scripts do not download/install anything.

## 1. Local setup and offline readiness checks

From a clean up-to-date slip-springs development worktree. The scientific source
worktree is separately pinned; do not replace or reuse a queued campaign's binary.
New paths must not exist. Keep this shell's variables and all logs/evidence.

```bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
D15_PROJECT=$(realpath examples/slip-springs)
D15_ROOT=$(mktemp -d /tmp/e1-d15-local.XXXXXX)
D15_BENCH="$D15_PROJECT/e1_d15_config/benchmark/manifest.json"
D15_BENCH_SHA=4c6805221db1ddf3d3ffaa6ae62f2f890150b6c967214be97642546941454dc9
D15_PILOT="$D15_PROJECT/e1_d15_config/pilot/manifest.json"
D15_PILOT_SHA=05f7f06141899d139b9e3fda3f740c92b0fe2b6894b280434ffe48b04c643c69
printf 'Keep evidence: %s\n' "$D15_ROOT"
git rev-parse HEAD > "$D15_ROOT/preparation-commit.txt"
git worktree add --detach "$D15_ROOT/source" 0dea651b58171a72206774bcebb2f4c74960069b
# Pure metadata projection, no sampling/simulator/build. Refuses overwrite.
python3 "$D15_PROJECT/e1_d15_prepare.py" --project "$D15_ROOT/projections.json"
cmp "$D15_PROJECT/e1_d15_projections.json" "$D15_ROOT/projections.json"
# These tests are supplied for local execution, not claimed as passed in Codex.
timeout 120s python3 "$D15_PROJECT/tests/test_e1_d15_preparation.py" > "$D15_ROOT/preparation-checks.log" 2>&1
timeout 120s python3 "$D15_PROJECT/tests/test_e1_d14_phase_b.py" > "$D15_ROOT/phase-b-cpu-regression.log" 2>&1
timeout 120s python3 "$D15_PROJECT/tests/test_e1_d13_phase_a.py" > "$D15_ROOT/phase-a-cpu-regression.log" 2>&1
timeout 120s python3 "$D15_PROJECT/tests/test_e1_d12_plan.py" > "$D15_ROOT/planning-regression.log" 2>&1
```

Inspect the logs and exit status. A failed check stops readiness; do not loosen
thresholds or claim passed checks from the existence of a log. Offline new tests
exercise schedules, row counts, seeds, immutability/nonoverwrite, malformed
reviews, missing authorization, non-executable T100 and resource projections.
They do not establish simulator science or comprehensive security correctness.

## 2. Fresh authenticated benchmark build and tiny host fixtures

These are explicit LOCAL commands, not simulation authorization. The source,
compiler,1914-style dependency closure (actual count recorded), runtime, linked
libraries and executable get fresh proofs. A prior Phase A/B build receipt
cannot be relabeled with a D1.5 manifest. No-op/adopted builds are refused.

```bash
timeout 300s python3 "$D15_PROJECT/e1_d15_host.py" build \
  --manifest "$D15_BENCH" --manifest-sha256 "$D15_BENCH_SHA" \
  --source-tree "$D15_ROOT/source" --build-root "$D15_ROOT/benchmark-build" \
  --cuda-home /usr/local/cuda --arch sm_86 --cxx /usr/bin/g++ \
  > "$D15_ROOT/benchmark-build-result.json"
D15_BUILD_SHA=$(sha256sum "$D15_ROOT/benchmark-build/build.json" | cut -d' ' -f1)
# Two existing nine-step technical fixtures, never a scientific campaign.
timeout 120s python3 "$D15_PROJECT/tests/test_e1_d14_phase_b_technical.py" \
  "$D15_ROOT/benchmark-build/bin/semiflexible" > "$D15_ROOT/tiny-gpu-checks.log" 2>&1
# Read-only live identity/resource inspection, no approval or output root created.
python3 "$D15_PROJECT/e1_d15_host.py" preflight \
  --manifest "$D15_BENCH" --manifest-sha256 "$D15_BENCH_SHA" \
  --build-receipt "$D15_ROOT/benchmark-build/build.json" --build-sha256 "$D15_BUILD_SHA" \
  --gpu-uuid GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 \
  --output-root "$D15_ROOT/benchmark-campaign" > "$D15_ROOT/benchmark-unapproved-preflight.json"
```

The unapproved preflight intentionally reports blockers and execution_authorized
false. Read-only exit0 is not permission to execute. It may report host/GPU
availability, not approved budgets. Copying a template alone cannot clear gates.

## 3. STOP — independent readiness and benchmark authorization review

No script here writes an authorized approval. Keep templates false/null in Git.
The reviewer must inspect the actual local checks/build/environment/preflight
and separately approve only the four benchmark runs: N32,M256,Z2048,Ne4,A2=5,
nu100,kb30,kBT=zeta1, kappas0/10,dt.0001/.00025,T.1, one replica/cell,
seeds721510101/201/301/401. No T1 or T100 authorization follows from this.

After that explicit decision, independently create outside the repository:

1. A readiness review following e1_d15_readiness.template.json. Bind the exact
   benchmark manifest SHA, fresh build-receipt SHA, review reference and actual
   check artifacts. `artifacts` maps each absolute log path to
   `{"bytes": N, "sha256": "externally recorded digest"}`. Include the offline,
   old CPU and tiny GPU logs, build result and preflight. Set the reviewed boolean
   true only after review, not via an automatic helper.
2. A separate approval based on config/benchmark/approval.template.json. It has
   the original nine fields PLUS readiness_review and benchmark_review. The
   readiness pointer is `{"path":"/absolute/readiness.json","sha256":"..."}`;
   benchmark_review must be null at this stage. Bind this exact manifest, build,
   live environment SHA from preflight, GPU UUID and fresh absolute output root.
   Supply all eight positive numeric budgets and an independent decision reference.
   Only the reviewer can set execution_authorized true for the approved scope.

The older120s/run,3600s/cohort,5GiB output operational caps remain enforced.
Per-run/aggregate output, minimum free disk/GPU/host bytes and maximum child RSS
all need explicit values; use measured readiness and conservative projections,
not this document as authorization. Suggested planning checks: the four benchmark
CSV envelopes total111.3MB plus logs/provenance; review whether a128MiB/run,
1GiB/cohort,2GiB child-RSS,8GiB available-host,4GiB GPU-free,10GiB disk-free
proposal is appropriate. These historical-size values are **not approved limits**.
Time limits must be separately reviewed; no runtime is measured at M256 yet.

Preserve the independent approval/readiness SHA anchors outside raw evidence.
The approval SHA binds review pointers; their artifacts must remain at the
approved absolute paths. No automatic resume/adoption after partial failure.

## 4. Benchmark execution — ONLY after the preceding explicit authorization

Set these paths/hashes from the independent reviewed records. This example
cannot run with empty/unset values and never generates approval itself.

```bash
: "${D15_APPROVAL:?set independent benchmark approval absolute path}"
: "${D15_APPROVAL_SHA:?set independently recorded benchmark approval SHA256}"
python3 "$D15_PROJECT/e1_d15_host.py" preflight \
  --manifest "$D15_BENCH" --manifest-sha256 "$D15_BENCH_SHA" \
  --build-receipt "$D15_ROOT/benchmark-build/build.json" --build-sha256 "$D15_BUILD_SHA" \
  --approval "$D15_APPROVAL" --approval-sha256 "$D15_APPROVAL_SHA" \
  --gpu-uuid GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 \
  --output-root "$D15_ROOT/benchmark-campaign" --authorize-d15-local-execution \
  > "$D15_ROOT/benchmark-execution-result.json"
```

This invokes exactly four serial processes. It enforces fresh output roots,
source/binary/dependency/GPU/environment identities, approved resource limits,
per-file RLIMIT_FSIZE, process-group supervision, raw schemas/counts/counters
and complete-cohort authentication. Polling may overshoot limits between samples;
authentication/bookkeeping cost is separate. Interruptions preserve failed/partial
evidence and cannot be resumed. No output can be promoted from a filename alone.

Record the returned completion SHA externally, only after success and reviewer
inspection; do not compute/trust it solely from an unverified marker file.
Then authenticate and summarize:

```bash
: "${D15_COMPLETION_SHA:?set successful benchmark returned completion SHA256}"
python3 "$D15_PROJECT/e1_d15_host.py" summarize \
  --manifest "$D15_BENCH" --manifest-sha256 "$D15_BENCH_SHA" \
  --root "$D15_ROOT/benchmark-campaign" --approval-sha256 "$D15_APPROVAL_SHA" \
  --completion-sha256 "$D15_COMPLETION_SHA" --report "$D15_ROOT/benchmark-summary.json"
```

Review all four integration/overall ns/bead/step values, production/child/init/
final output costs, observer transfers/CPU time, raw rows/bytes, event rates,
RSS and headroom. Nested timer intervals are not additive. No equilibrium or
scientific timestep gate is supplied by this performance summary. A single
short observation per cell does not estimate variance or throughput precision.

## 5. STOP — review benchmark before any bounded observation pilot

T1 remains blocked until an independent benchmark review has:

- schema e1-d15-benchmark-review-v1 (see the false template);
- nonempty independent review_reference;
- exact approved_pilot_manifest_sha256;
- resource_and_observation_suitability_reviewed=true only after reviewing results;
- absolute benchmark_root and its externally trusted manifest, approval and
  completion SHA256s (all four runs must authenticate again).

The T1 pilot is NOT Phase B and is not accepted by the frozen Phase B analysis.
Its four independent runs use N32,M256,Z2048,Ne4,A2=5,nu100,kb30,kBT=zeta1,
kappas0/10,dt.0001/.00025,T1,one replica/cell,seeds721520101/201/301/401;
scalar0,.5,1;7 full E1 frames and4 audits. Data remain exploratory raw evidence.

Only if separately authorized, make a fresh pilot-manifest-bound build and run
the same local readiness checks on that build. Create NEW independent readiness
and execution approvals, with the benchmark_review pointer now populated. The
benchmark's true approval must not be reused as pilot approval.

```bash
# LOCAL ONLY, after an explicit decision to prepare the gated T1 pilot build.
timeout 300s python3 "$D15_PROJECT/e1_d15_host.py" build \
  --manifest "$D15_PILOT" --manifest-sha256 "$D15_PILOT_SHA" \
  --source-tree "$D15_ROOT/source" --build-root "$D15_ROOT/pilot-build" \
  --cuda-home /usr/local/cuda --arch sm_86 --cxx /usr/bin/g++ \
  > "$D15_ROOT/pilot-build-result.json"
D15_PILOT_BUILD_SHA=$(sha256sum "$D15_ROOT/pilot-build/build.json" | cut -d' ' -f1)
timeout 120s python3 "$D15_PROJECT/tests/test_e1_d14_phase_b_technical.py" \
  "$D15_ROOT/pilot-build/bin/semiflexible" > "$D15_ROOT/pilot-tiny-gpu-checks.log" 2>&1
# Read-only pilot identity/resource evidence for independent approval review.
python3 "$D15_PROJECT/e1_d15_host.py" preflight \
  --manifest "$D15_PILOT" --manifest-sha256 "$D15_PILOT_SHA" \
  --build-receipt "$D15_ROOT/pilot-build/build.json" --build-sha256 "$D15_PILOT_BUILD_SHA" \
  --gpu-uuid GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 \
  --output-root "$D15_ROOT/pilot-campaign" > "$D15_ROOT/pilot-unapproved-preflight.json"
# STOP here for the separate readiness/benchmark/scientific/resource review.
```

No execution of the following block is authorized by this handoff:

```bash
: "${D15_PILOT_APPROVAL:?set separately authorized pilot approval absolute path}"
: "${D15_PILOT_APPROVAL_SHA:?set externally recorded pilot approval SHA256}"
python3 "$D15_PROJECT/e1_d15_host.py" preflight \
  --manifest "$D15_PILOT" --manifest-sha256 "$D15_PILOT_SHA" \
  --build-receipt "$D15_ROOT/pilot-build/build.json" --build-sha256 "$D15_PILOT_BUILD_SHA" \
  --approval "$D15_PILOT_APPROVAL" --approval-sha256 "$D15_PILOT_APPROVAL_SHA" \
  --gpu-uuid GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 \
  --output-root "$D15_ROOT/pilot-campaign" --authorize-d15-local-execution \
  > "$D15_ROOT/pilot-execution-result.json"
: "${D15_PILOT_COMPLETION_SHA:?set successful pilot returned completion SHA256}"
python3 "$D15_PROJECT/e1_d15_host.py" summarize \
  --manifest "$D15_PILOT" --manifest-sha256 "$D15_PILOT_SHA" \
  --root "$D15_ROOT/pilot-campaign" --approval-sha256 "$D15_PILOT_APPROVAL_SHA" \
  --completion-sha256 "$D15_PILOT_COMPLETION_SHA" --report "$D15_ROOT/pilot-summary.json"
```

Retain raw chain-resolved data for ensemble means, variances and synchronous
joints. Do not divide uncertainties by the number of successive frames or feed
these four single-replica cells to an R2/R4 confirmatory analyzer. No supported T100 or
larger-M execution entry point exists here: those are non-executable proposals.
Any failure preserves the root and stops; choose no automatic alternate seed,
retry, resume, changed tolerance, thinned data or enlarged budget.
