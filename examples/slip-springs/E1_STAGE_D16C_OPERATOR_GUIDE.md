# D1.6C local handoff — preserve originals, repair return, then audit

Preparation only. Codex has not run tests, builds, GPU work, authentication,
repackaging, simulations, reference draws or analyses. These commands are for
local execution. No new GPU campaign is authorized or supported here.

Do not rerun the old D1.6B `results` command. The existing16-run cohort and
`analysis-1793017379881834465/analysis.json.gz` remain immutable. New work goes
only into a fresh sibling `/home/jramirez/UAMMD_KG-evidence/d16c/` root. Use the
permanent checkout `/home/jramirez/UAMMD_KG-slip-springs-dev`; no persistent
checkout, fixture, output or evidence is placed under `/tmp` or `/var/tmp`.

## Stage A — existing evidence authentication and packaging verification

Requires Linux, Git/network, Python>=3.10, NumPy/SciPy (the inherited authenticator requires the recorded Python executable,
`/usr/bin/python3.10` on this host), and the complete original
D1.6B/D1.6A.2 evidence closures at their recorded durable paths. No CUDA build,
GPU query, simulation or rerun of original scientific estimators occurs.

```bash
python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d16c_local.py existing \
  --evidence-parent /home/jramirez/UAMMD_KG-evidence/d16c
```

This creates a fresh `d16c-existing-*` root and pinned preparation checkout,
captures the scientific Python environment, runs only the new deterministic
mathematical/control tests, authenticates the existing raw cohort/reference/
source/approval/completion closure, checks the saved gzip/JSON and exact28,386,811
bytes/SHA256, and copies that entire compressed scientific payload without changes.
It never regenerates original scientific results. All sources, manifests,
original inventories/receipts and authentication dependencies remain bound.

The program prints `D16C_ROOT=...` and three `UPLOAD` paths. Set the actual root:

```bash
export D16C_ROOT=/home/jramirez/UAMMD_KG-evidence/d16c/d16c-existing-REPLACE
export D16C_TOOL="$D16C_ROOT/preparation/examples/slip-springs/e1_d16c_local.py"
```

Upload **all three** files:

1. `$D16C_ROOT/stage-a/returns/d16c-existing-metadata.tar.gz`
2. `$D16C_ROOT/stage-a/returns/d16b-original-analysis.json.gz`
3. `$D16C_ROOT/stage-a/returns/return-manifest.json`

The third file gives exact sizes and SHA256 for both payloads and completed
worker resource accounting. The metadata archive additionally contains internal
`SHA256SUMS`, original evidence/raw-file inventories and source/approval/result
identities, test logs and a false audit-approval template. The scientific payload
is byte-identical to the original file; it is not truncated, filtered or rounded.
Its required SHA256 is
`04570c0ccb3b06df0f9be265a2bde602f1c2dcce59c474af963ca8634a17652f`.

Stop and return these files for independent scientific/provenance review.
Stage A's completion does not authorize the secondary audit. No ChatGPT/Codex
session needs to remain open. Full old evidence stays untouched locally.

If a stage fails, it preserves its attempt, logs and partial new outputs and
prints two diagnostic uploads instead: `d16c-failure-metadata.tar.gz` and
`SHA256SUMS` from its new failure-return directory. Return those rather than
claiming a completed D1.6C return. They identify a D1.6C failure, not a failed
original GPU campaign. A failure before root creation can only appear on the
terminal. No automatic retry, restart, quota expansion or data dropping occurs.

## Stage B — separately reviewed, explicitly authorized secondary audit

Only after independent review of Stage A may a new explicit read-only audit
approval be returned. No approval is issued by this implementation. The reviewer
copies `audit-approval-template.json` and changes only:

- `audit_authorized` to true;
- `review_reference` to a nonempty independent review identifier;
- `stage_a_metadata_sha256` to the reviewed metadata archive SHA256 from the
  Stage A detached return manifest.

The unchanged fields bind the new session/source closure, authenticated original
analysis/cohort, protocol/windows/contrast family, resource contract, environment,
Stage A readiness binding and fixed new output location. The false template is
included inside the Stage A archive; the archive hash is supplied afterward to
avoid a circular self-hash. The reviewer supplies the approval JSON's externally
trusted SHA256. An arbitrary self-hashed file or any previous GPU/reference
approval grants no audit authority. Approval formatting may vary; exact bytes
must match its supplied digest and parsed fields must match the contract.

```bash
export D16C_APPROVAL=/absolute/durable/path/reviewed-d16c-audit-approval.json
export D16C_APPROVAL_SHA256=REPLACE_WITH_REVIEWED_SHA256
```

After that separate approval, invoke once:

```bash
python3 -B "$D16C_TOOL" audit --root "$D16C_ROOT" \
  --approval "$D16C_APPROVAL" --approval-sha256 "$D16C_APPROVAL_SHA256" \
  --execute-reviewed-audit
```

This is CPU read-only postprocessing of the existing trajectories and accepted
references. It writes only `stage-b/` and new D1.6C control records. An immutable
audit-attempt and worker marker consume the invocation before scientific work.
Failed or interrupted work is preserved, never resumed or retried automatically.
There is no simulation/reference-sampling/build/preflight command in this workflow.

The new scientific protocol fixes six post-selected contrasts and narrow/wide
early/middle/late windows. It retains all four replicas, full connector weighting
and support diagnostics, matched-time independent timestep contrasts, original
selected ACF records plus independent cross-checks, complete uncertainty and
standalone SVG displays. No unresolved tail becomes zero IAT. The original
analysis and conclusions remain separately identified and unchanged.

## Stage C — return the new audit and provenance

After B finishes successfully:

```bash
python3 -B "$D16C_TOOL" return-audit --root "$D16C_ROOT"
```

This reauthenticates inputs and the completed secondary outputs and copies the
new compressed audit without recomputing it. Upload all three printed files:

1. `$D16C_ROOT/stage-c/returns/d16c-audit-metadata.tar.gz`
2. `$D16C_ROOT/stage-c/returns/d16c-secondary-audit.json.gz`
3. `$D16C_ROOT/stage-c/returns/return-manifest.json`

Metadata includes original authentication/inventories, separate audit approval,
source/protocol/resource/completion identities, process records and SVG trace/ACF
figures. The full new scientific JSON includes replica vectors, window/weighting/
multiplicity diagnostics, finite-lag sums, failed support criteria, original selected
ACF records, accepted-reference uncertainty/covariance and conditional planning
interpretation. Large raw CSVs/coordinates/binaries remain local with verified
hashes. Preserve the entire new root and all original evidence locally.

## Resource limits and interpretation

Frozen in `e1_d16c_config/resources.json`:

| Stage | Wall limit | Child host RSS | Stage output |
|---|---:|---:|---:|
| A including local setup/tests/authentication/packaging | 1,800 s | 4 GiB authentication worker | 192 MiB worker outputs |
| Deterministic tests within A | 120 s | 1 GiB | 64 MiB test logs/records |
| B secondary audit including reauthentication | 3,600 s | 4 GiB | 512 MiB |
| C audit return authentication/packaging | 900 s | 4 GiB | 192 MiB |

Maintain2 GiB free disk plus the stage output quota before launch; test scope
has a1 GiB disk floor. Checkout/build-free source storage and durable fixture
scratch are separate from worker-output quotas. Only a preparation checkout is
created; no scientific source build is needed. Environment-capture subprocesses
have180 s timeouts. Stage timers reserve their elapsed setup/environment time
before delegating workers; recorded caps are not automatic retry allowances.
The supervisor enforces wall, RSS, file/output size and disk headroom, with
parent-death/process-group termination and50 ms polling. This is not hard-real-time
resource enforcement. Exceeded limits cannot produce successful stage completion.

Metadata payloads are bounded at16 MiB and each full compressed scientific payload
at64 MiB. Streaming JSON authentication also caps decompressed input at1.5 Gi
characters, strings at1 MiB and nesting at64. Over-limit input stops visibly;
no partial scientific data is presented as a complete return. The checksum
manifest is not a digital signature against wholesale evidence replacement.

R4 uncertainty and same-data post-selection limit every new scientific signal.
Nominal pointwise intervals and six-contrast Bonferroni sensitivity do not yield
controlled post-selection FWER. Wide/null-compatible intervals do not prove
stationarity, preservation or equivalence. Stiff backbone CDF precision remains
unresolved. There is no automatic equilibrium acceptance or recommendation to
increase M, R or T, and no new campaign follows from this audit.
