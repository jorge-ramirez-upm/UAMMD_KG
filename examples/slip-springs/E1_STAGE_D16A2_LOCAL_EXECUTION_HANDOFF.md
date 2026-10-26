# D1.6A.2 — separate moment and CDF reference precision gates

Preparation only. Codex has not executed tests, numerical checks, seed expansion,
preflights, sampling, simulations, builds or benchmarks. All commands below are
for local execution. Full protocol and limitations are in
[E1_STAGE_D16A2_IMPLEMENTATION_REPORT.md](E1_STAGE_D16A2_IMPLEMENTATION_REPORT.md).

Use the permanent development checkout
`/home/jramirez/UAMMD_KG-slip-springs-dev`. Preserve existing evidence under
`/home/jramirez/UAMMD_KG-evidence/` unchanged. New evidence belongs in the separate
`d16a2` directory. Never place checkouts, evidence or retained fixtures in `/tmp`.

## Stage A — readiness, then independent review

Requires Linux, Git/network, Python >=3.10 and installed NumPy/SciPy. No dependency
installation, build, GPU query or equilibrium draw occurs in Stage A. Run:

```bash
python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d16a2_local.py readiness \
  --evidence-parent /home/jramirez/UAMMD_KG-evidence/d16a2
```

The utility fetches `origin/slip-springs`, requires clean HEAD equal to that
branch, checks ancestry from `144cef60aebb322afe4e2de37c81d3017a4f2f41`, and
creates a fresh durable root with its own detached preparation worktree.
It authenticates preserved source contracts and the accepted sampler; records
Python, NumPy/SciPy, imported dependencies, libraries and host identities; runs
only `test_e1_d16a2_*.py`; performs the original deterministic analytical and
quadrature checks; audits all 4,672 maximum-grid old/new seed identities and
initial PCG64 states without drawing configurations; and checks CPU RAM/disk
headroom. Test, numerical and seed-audit subprocesses each have a 120 s timeout.
All logs and failures are retained. Each readiness root is nonoverwriting.

The program prints `D16A2_ROOT=...` and exactly two `UPLOAD` paths. Set the root
to the actual printed value:

```bash
export D16A2_ROOT=/home/jramirez/UAMMD_KG-evidence/d16a2/d16a2-readiness-REPLACE
export D16A2_TOOL="$D16A2_ROOT/preparation/examples/slip-springs/e1_d16a2_local.py"
```

Return these two files, even if readiness failed:

1. `$D16A2_ROOT/returns/d16a2-readiness-return-<UTC timestamp>.tar.gz`
2. The same path with `.sha256` appended.

The archive includes configuration, source/environment hashes, numerical error
estimates, test logs, seed audit, readiness status and a false approval template.
`READY_FOR_REVIEW` grants no sampling authority. Stop for independent review;
no terminal or Codex session needs to stay open. A failure before directory
creation is reported on the terminal. A failure before checkout still produces
a packet when possible; unavailable records remain explicitly absent.

Optional repackage of an existing readiness root, without rerunning checks:

```bash
python3 -B "$D16A2_TOOL" package-readiness --root "$D16A2_ROOT"
```

## Stage B — new approval, then one calculation per stiffness

Do not execute B until the Stage A packet has been independently reviewed and a
new explicit D1.6A.2 approval record returned. Prior D1.6A approvals are rejected.
The reviewer must supply a copy of `approval-template.json` changing only
`execution_authorized` to true and `review_reference` to a nonempty review
identifier, plus its trusted SHA256. This binds the exact root, sources,
configuration, environment, numerical checks, seed audit and resource limits.
Computing an arbitrary file's digest does not authorize it. The implementation
never issues an approval.

Optional read-only freshness check (no draws):

```bash
python3 -B "$D16A2_TOOL" preflight --root "$D16A2_ROOT"
```

After the separate approval, fill in the reviewer-supplied values:

```bash
export D16A2_APPROVAL=/absolute/durable/path/reviewed-d16a2-approval.json
export D16A2_APPROVAL_SHA256=REPLACE_WITH_REVIEWED_SHA256
```

Run each command once, sequentially:

```bash
python3 -B "$D16A2_TOOL" run --root "$D16A2_ROOT" --kappa 0 \
  --approval "$D16A2_APPROVAL" --approval-sha256 "$D16A2_APPROVAL_SHA256" \
  --execute-reviewed-reference
```

```bash
python3 -B "$D16A2_TOOL" run --root "$D16A2_ROOT" --kappa 10 \
  --approval "$D16A2_APPROVAL" --approval-sha256 "$D16A2_APPROVAL_SHA256" \
  --execute-reviewed-reference
```

The second case may be explicitly requested after the first finishes under the
same reviewed two-case approval, including if the first is unresolved. No retry,
restart, resume or new-root rerun of an unsuccessful calculation is authorized.
An attempt marker is consumed before pre-run checks; failures before draws also
require review. An orphaned running marker blocks further execution/packaging;
preserve it and report the interruption. Never delete a marker to resume.

Each case draws 65,536 independent calibration configurations, freezes 18 cuts,
and draws an independent 8,192-configuration sizing pilot. Only Family M pilot
uncertainty selects one final count from
16,384 / 32,768 / 65,536 / 131,072 / 262,144 / 524,288, using the unchanged
factor-two SE safety multiplier. Calibration and pilot data never enter final
estimates. If no count passes the M prediction, no final draws occur. Otherwise
one independent final sample is drawn and assessed once. CDF uncertainty never
increases the selected count or triggers more draws.

Per stiffness the original caps remain: 30 s/batch, 1,200 s total supervised
calculation including post-run authentication, 1 GiB conservative combined
worker/supervisor RSS high-water sum, 16 MiB case output, 512 chains/batch,
and at most 598,016 draws over three phases. RAM/disk headroom floors remain
2 GiB available host RAM and 1 GiB free disk. Supervisor polling is 50 ms;
whole-batch time and worker RSS high-water are also checked. Readiness, pre-run
environment authentication and return packaging are separately bounded/logged;
they are outside the supervised reference calculation. This is unchanged from
D1.6A. No resource cap is enlarged.

A command succeeds operationally when Family M passes precision and numerical
consistency, even if C is `CDF_PRECISION_UNRESOLVED`. That C result is explicitly
unresolved distributional reference precision, never distributional validation.
M failure/unresolved status or numerical inconsistency remains a nonzero result.
Preserve all evidence and continue to C; do not retry.

## Stage C — authenticate saved evidence, then return two files

```bash
python3 -B "$D16A2_TOOL" results --root "$D16A2_ROOT"
```

No new draws occur. The utility authenticates approval/source bindings, complete
inventories, counts, seed identities, sufficient statistics, frozen cuts and
saved inference. Read-only deterministic replay compares the original decisions;
it does not issue a new statistical assessment or select another count.
Each replay subprocess has a 120 s timeout. Missing, failed and unresolved cases
remain visible. Authentication failure is distinct from statistical imprecision.

Return the two newly printed files:

1. `$D16A2_ROOT/returns/d16a2-results-return-<UTC timestamp>.tar.gz`
2. Its `.tar.gz.sha256` sidecar.

Stage B has no separate review upload: its complete records are returned by C.
Both families' outcomes, all 25 estimates/SEs/intervals/precision decisions,
delta covariance and batch-jackknife diagnostics, frozen cuts, calibration
uncertainty, pilot selection, complete batch sufficient statistics/seed states,
approvals, resources and completion records are included. The packet omits
scalar `.npy` files and the preparation checkout, but inventories their relevant
raw-file hashes, sizes and full local paths. Preserve the entire root locally.
The allowlist archive has an 8 MiB uncompressed cap; exceeding it stops packaging
without discarding evidence. Internal `SHA256SUMS` and external sidecars detect
changes; they are not signatures against adversarial wholesale replacement.

For kappa=0, analytical moments remain primary exact references and sampling is
consistency validation. Kappa=10 requires an accepted independent final sample.
All M intervals remain nominal batch-t/delta CLT statements, subject to review
of high moments and delta/jackknife stability. CI agreement proves neither exact
sampler correctness nor dynamical equilibrium preservation. No GPU simulation,
T100 campaign, D2, stress, rheology or subsequent campaign is authorized.
