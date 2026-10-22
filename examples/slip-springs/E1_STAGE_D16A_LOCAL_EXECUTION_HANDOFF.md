# D1.6A — independent CPU equilibrium reference: local handoff

**IMPLEMENTED, UNEXECUTED — awaiting local readiness and independent review.**
No test, quadrature, reference draw, build, GPU query or simulation was executed
in Codex. These commands are for your Linux workstation. They do not authorize
any GPU trajectory, T100 campaign, D2 or rheology.

Authority: the unchanged [D1.6 reference contract](E1_STAGE_D16_REFERENCE_MOMENTS_V1.md),
[scientific design](E1_STAGE_D16_SCIENTIFIC_DESIGN_V1.md) and
[resource proposals](E1_STAGE_D16_RESOURCE_PLAN_V1.md).
Implementation and limitations: [D1.6A report](E1_STAGE_D16A_IMPLEMENTATION_REPORT.md).

## Stage A — readiness, then return two files

Requires Linux, Git/network access, Python >=3.10 and compatible installed
NumPy/SciPy. SciPy provides Student-t, binomial and beta inverse CDFs. There is
no dependency download, CUDA build, GPU access or equilibrium sampling in A.
Missing dependencies produce a failure packet; resolve them separately and
review before a fresh readiness attempt. Do not alter an existing evidence root.

Run from any working directory, using the clean `slip-springs` development
checkout (not the unrelated, possibly dirty `KremerGrest` checkout):

```bash
python3 -B /tmp/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d16a_local.py readiness \
  --evidence-parent /home/jramirez/UAMMD_KG-evidence/d16a
```

This fetches and checks the exact branch revision, requires a clean worktree,
and creates a fresh durable directory and detached preparation checkout.
It records dependency/library hashes, runs only the new deterministic CPU
tests (including a complete planned-seed identity collision check), performs
the radial recurrence/quadrature and accepted-reference consistency checks,
and checks CPU RAM/disk headroom. CPU tests and numerical checks each have a
120-second timeout. Git commands are bounded; nothing waits for manual input.
The tests use constructed data, not `Chain.sample`. No reference phases start.

It prints `D16A_ROOT=...` and two `UPLOAD ...` paths. Keep the absolute root:

```bash
export D16A_ROOT=/home/jramirez/UAMMD_KG-evidence/d16a/d16a-readiness-REPLACE
export D16A_TOOL="$D16A_ROOT/preparation/examples/slip-springs/e1_d16a_local.py"
```

Upload exactly these two files, including on a failed readiness:

1. `$D16A_ROOT/returns/d16a-readiness-return-<UTC timestamp>.tar.gz`
2. That same file with the suffix `.sha256` appended.

They contain `SUMMARY.md`, readiness status/errors, CPU test logs/exit codes,
analytic moments, numerical error diagnostics, source/dependency identities,
configuration, a **false** approval template and a SHA256 inventory. When
failure happens before checkout/dependency capture, unavailable items remain
explicitly absent; the error packet is not readiness acceptance. Failure to
create the durable directory itself can only be reported on the terminal.

A successful A means **READY FOR REVIEW**, not permission to sample. Stop and
send the two files. Do not edit the template to grant yourself implicit approval.
No need to keep a terminal open or leave Codex waiting.

To repackage existing readiness evidence only (no tests or sampling):

```bash
python3 -B "$D16A_TOOL" package-readiness --root "$D16A_ROOT"
```

This makes a new nonoverwriting packet. If checkout itself failed, use the
automatically generated failure packet; a pinned tool does not yet exist.

## Stage B — separately approved, bounded reference calculations

**Do not run B until the A packet has been independently reviewed and an
approval record has been returned.** The reviewer must approve the exact false
template by supplying a separate JSON record, changing only
`execution_authorized` to true and adding a nonempty `review_reference`.
The record binds the source, root, numerical results, environment, configuration,
both stiffnesses and all limits. Obtain its trusted SHA256 from that review;
computing a digest of an arbitrary unreviewed file does not confer authorization.
No approval is created by these utilities or by this implementation task.

First an optional read-only freshness check; it never starts sampling:

```bash
python3 -B "$D16A_TOOL" preflight --root "$D16A_ROOT"
```

After separate approval, set these two values from the review:

```bash
export D16A_APPROVAL=/absolute/path/to/reviewed-d16a-reference-approval.json
export D16A_APPROVAL_SHA256=REPLACE_WITH_REVIEWED_SHA256
```

Exactly one independent calculation per stiffness, sequentially, with no
automatic retry or continuation. Run the second command only if the first has
finished. An unresolved first case does not authorize retrying it; return its
evidence. The other stiffness has a separate single-use case and can still be
explicitly requested under the same reviewed two-case authorization.

```bash
python3 -B "$D16A_TOOL" run --root "$D16A_ROOT" --kappa 0 \
  --approval "$D16A_APPROVAL" --approval-sha256 "$D16A_APPROVAL_SHA256" \
  --execute-reviewed-reference
```

```bash
python3 -B "$D16A_TOOL" run --root "$D16A_ROOT" --kappa 10 \
  --approval "$D16A_APPROVAL" --approval-sha256 "$D16A_APPROVAL_SHA256" \
  --execute-reviewed-reference
```

Each command rechecks live CPU headroom and exact dependency identities, then
uses only the unchanged accepted CPU sampler. No trajectory input is accepted.
Each batch has 512 chains and a fresh PCG64 seed namespace. Calibration (65536)
and sizing (8192) are excluded from final estimation. The final sample size is
chosen once from the frozen grid, or the calculation stops unresolved before
any final draw. Final precision is assessed exactly once. A failed assessment
does not cause additional draws. No case can be overwritten or resumed.

Limits per stiffness: 30 s/batch; 1200 s including supervised worker and post-run
authentication; 1 GiB conservative worker-plus-supervisor RSS high-water sum;
16 MiB case output including stiffness-specific metadata/logs. CPU-reference
headroom floors: 2 GiB available RAM and 1 GiB free disk, also checked while
running. These additional conservative headroom guards are explicitly part of
this reference workflow, not an enlargement of D1.5 or authorization for GPU
work. Single-thread BLAS/OpenMP is requested. The supervisor polls every 50 ms;
the worker additionally checks OS RSS high-water and whole-batch elapsed time.
Actual observations and any enforcement failure are retained. Readiness,
pre-run environment hashing and final packet creation are separately timed in
logs and lie outside the reference-worker computation; each delegated command
has its own bounded timeout.

The conservative sizing rule can exhaust the grid, particularly at central
CDF cuts. **UNRESOLVED is a valid outcome**, never a reason to increase the cap,
change seed or loosen the precision rule. New sampling after failure needs a
new reviewed protocol/seed allocation, not another invocation in a new folder.

## Stage C — authenticate existing results and package

This command performs read-only analysis of existing scalar/batch evidence,
without generating new equilibrium samples. It checks complete file inventories,
approval bindings, batch/seed coverage, exact counts, calibration cuts, sufficient
statistics and reproducibility of sizing, inference and assessment. It records
missing or failed cases explicitly and packages them too. Each numerical
authentication child has a 120-second timeout.

```bash
python3 -B "$D16A_TOOL" results --root "$D16A_ROOT"
```

Upload the two newly printed files:

1. `returns/d16a-results-return-<UTC timestamp>.tar.gz`
2. Its `.tar.gz.sha256` sidecar.

The packet contains the actual independent final confidence intervals,
delta and whole-batch jackknife uncertainties, covariance matrices, CDF results,
frozen cuts and calibration-rank intervals, selection predictions, complete
executed seed/RNG ledger and batch sufficient statistics, copied reviewed
approvals, completion/resource records and SHA256 inventories. It omits the
scalar `.npy` files and all particle coordinates/executables; the scalar files'
absolute paths, sizes and hashes remain in `contents.json`. Preserve the full
root, preparation checkout and all `.npy` files locally. Do not move the root.
Packets stop rather than exceed 8 MiB uncompressed; oversized packets are a
workflow blocker, never an excuse to discard unfavorable scientific evidence.

`PRECISION_RESOLVED_NOMINAL` is reference-quality bookkeeping under nominal
batch-CLT intervals, pending review of high moments, tail stability and
delta/jackknife differences. It does not establish dynamical equilibrium
preservation, exact CLT coverage, or confirmatory coverage for a later campaign.
No long-time simulation or additional stage follows automatically.
