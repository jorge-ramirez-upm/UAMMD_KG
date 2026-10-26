# D1.6B local operator guide

Preparation only. No test, build, GPU preflight, benchmark, simulation, reference
sampling or scientific analysis was executed by Codex. These commands are for
local execution. The T100 campaign remains unauthorized pending independent
readiness review and explicit user approval.

Use the permanent development checkout. Keep all new evidence in the separate
`/home/jramirez/UAMMD_KG-evidence/d16b/` namespace. Existing D1.5 and D1.6A.2
roots are read-only inputs; never relocate or edit them. All source worktrees,
builds, fixtures, logs and new raw trajectories use durable paths. No command
below creates a persistent checkout or evidence under `/tmp` or `/var/tmp`.

## Stage A — local readiness, then return two files

Prerequisites: Linux, clean fetched `slip-springs`, Git/network, Python>=3.10,
NumPy/SciPy, CUDA13, g++, and the recorded RTX3060Ti GPU UUID. The existing full
D1.5 and D1.6A.2 evidence closures named by the committed locks must be available
at their original durable absolute paths. Missing evidence is a readiness blocker;
do not substitute the rounded reference numbers from chat or rerun references.

The explicit tiny-fixture flag affirms the operator's existing local readiness
scope authorization for the unchanged N3/M4 and N17/M2 nine-step fixtures. It
never approves an M256/T100 member. If that small scope is not independently
authorized under the existing readiness rules, obtain that authorization before
using the flag. This implementation issues no authorization or approval.

Exact local Stage A command:

```bash
python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d16b_local.py readiness \
  --evidence-parent /home/jramirez/UAMMD_KG-evidence/d16b \
  --cuda-home /usr/local/cuda \
  --authorize-tiny-readiness-fixtures
```

A fresh `d16b-readiness-*` directory contains a pinned preparation worktree and
a separate accepted scientific source worktree. The command runs deterministic
new tests, authenticates/imports references and performance evidence, compiles a
fresh double binary with explicit source/dependency/toolchain receipts, runs
only the existing tiny technical fixtures and read-only GPU/resource checks,
and captures the Python/scientific environment. No T100 command is invoked.
The exact time/resource bounds are in the resource amendment. No package or
compiler dependency is installed automatically.

It prints `D16B_ROOT=...` and two `UPLOAD` paths. Set the root to the actual
printed value and use its pinned utility for all subsequent stages:

```bash
export D16B_ROOT=/home/jramirez/UAMMD_KG-evidence/d16b/d16b-readiness-REPLACE
export D16B_TOOL="$D16B_ROOT/preparation/examples/slip-springs/e1_d16b_local.py"
```

Upload exactly these two files, including when readiness fails:

1. `$D16B_ROOT/returns/d16b-readiness-return-<UTC timestamp>.tar.gz`
2. The same path with `.sha256` appended.

The archive contains readiness/error records, deterministic-test/build/tiny-fixture
logs, source and dependency/environment identities, imported moment/CDF reference
uncertainty and covariance, performance provenance, resource observations and a
false approval template if readiness succeeded. It inventories omitted binary/raw
files and their full paths. A failure before root creation can only be reported
on the terminal; later failures are preserved and packaged where possible.

`READY_FOR_INDEPENDENT_REVIEW` is not permission to simulate. Stop and return
both files for review. No Codex session needs to remain open. Repackage existing
readiness evidence without tests/builds/GPU work using:

```bash
python3 -B "$D16B_TOOL" package-readiness --root "$D16B_ROOT"
```

## Stage B — new review/approval, then explicit local T100 execution

Do not run B until the new readiness, scientific protocol and resource amendment
have been independently reviewed and explicit execution approval returned. The
reviewer must approve the exact `approval-template.json`, changing only:

- `execution_authorized`: true;
- `independent_readiness_reviewed`: true;
- `approval_reference`: a nonempty review identifier.

All other fields bind the exact manifest/seeds/schedules, analysis protocol,
source/build/executable/environment/readiness, imported reference/performance
identities, GPU, root and proposed limits. The separate approval must use the
same canonical JSON encoding (sorted keys, two-space indentation, final newline)
as the template. The reviewer returns the approval JSON and its externally
trusted SHA256. Hashing an arbitrary unreviewed file does not approve it.
No old D1.5, D1.6A or D1.6A.2 approval confers this authority.

After that separate review, set the supplied path and trusted SHA256:

```bash
export D16B_APPROVAL=/absolute/durable/path/reviewed-d16b-approval.json
export D16B_APPROVAL_SHA256=REPLACE_WITH_REVIEWED_SHA256
```

Execute the cohort **once**:

```bash
python3 -B "$D16B_TOOL" run --root "$D16B_ROOT" \
  --approval "$D16B_APPROVAL" --approval-sha256 "$D16B_APPROVAL_SHA256" \
  --execute-reviewed-t100
```

This rechecks readiness/source/dependency/environment/reference identities and
headroom, consumes immutable launch/attempt records and executes the sixteen
manifest members sequentially. Each scientific child and its bounded output
authentication share600 s. The whole cohort subprocess is bounded by14,400 s,
including prelaunch and final authentication. The other limits are2 GiB child
RSS,8 GiB available host,4 GiB free GPU,256 MiB/run,4 GiB aggregate output and
10 GiB maintained disk floor; initial free disk must be>=18 GiB plus separate
source/build/reference provisioning. Actual checks and failures are retained.

There is no retry, restart, resume, replacement seed, adoption of an old output,
automatic extension or automatic new run. Preserve partial raw outputs and the
failure/launch/process/status records. If a supervisor is abruptly lost, an
orphan `execution-running.json` blocks packaging/execution; do not delete it to
resume. Report that interruption for independent review. A normally recorded
partial failure can proceed to C to return its incomplete evidence.

Stage B does not create an automatic scientific result or acceptance. It reports
only completion identity or preserved failure. Stage C returns its evidence.

## Stage C — authenticated local analysis and return

```bash
python3 -B "$D16B_TOOL" results --root "$D16B_ROOT"
```

The new analyzer runs only against a complete authenticated cohort. It checks
raw hashes/receipts, approvals, source/build/environment and reference identities;
streams one replica/frame at a time; analyzes the frozen windows, matched times,
whole-replica uncertainty, canonical distributions and temporal support; then
reauthenticates the inputs. It performs no simulation or reference sampling.
A fresh analysis directory preserves each explicitly requested analysis result.
Its7200 s/4 GiB RSS/256 MiB output limits are separate from GPU execution.
Partial or corrupt evidence yields an incomplete/failure packet and no full-cohort
scientific inference. The command exits nonzero for such failures; return the
packet, not a modified status file.

Upload the two newly printed files:

1. `$D16B_ROOT/returns/d16b-results-return-<UTC timestamp>.tar.gz`
2. Its `.tar.gz.sha256` sidecar.

The archive contains compressed scientific analysis, replica traces/estimators,
reference-relative differences and uncertainty, paired changes, matched-dt
contrasts, exact population/connector reference descriptions, ACF support and
unresolved-tail flags, source/configuration/approval/completion/resource identities
and raw-file inventories. It omits raw CSVs and binaries. Preserve the full root,
preparation/source worktrees and all raw trajectories locally. Internal
`SHA256SUMS` plus the archive sidecar detect changes; they are not signatures
against wholesale adversarial replacement. Packaging stops at32 MiB payload
or16 MiB/member without discarding unfavorable evidence.

Expect several outcomes to coexist. R4 intervals are exploratory; zero dispersion
or unresolved autocorrelation tails cannot establish precision/mixing. Stiff CDF
precision remains unresolved even when moment references are accepted. No result
is a confirmatory D0 pass, dynamical-preservation proof, ergodicity acceptance,
convergence-order measurement, zero-dt extrapolation or authorization for more work.
