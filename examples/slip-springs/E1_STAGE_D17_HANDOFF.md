# D1.7 implementation and operator handoff — preparation only

Read the [scientific protocol](E1_STAGE_D17_PROTOCOL.md) before interpreting
this packet. No build, test, benchmark, preparation job, pilot or analysis was
executed in Codex. All commands below require independent review first.

The original draft is preserved in Git history at starting commit
`da1b720da5b8e59352f8db13e249c0b289f4f3e1`. This completion adds:

- `e1_d17_manifest.json` and its SHA256 file: candidate matrix, seeds, physical
  contract, schedules, primary family, planning sensitivities and resource limits.
- `e1_d17_spec.py`: rational schedules, commands, bounded frame reader, metadata
  seed audit and path restrictions. Physical parameters are held fixed; only h,
  BD step count and observation step indices vary between timestep cells.
- `e1_d17_host.py`: CPU preparation, approval gate, existing process supervisor,
  authentication and serial Stage-A-only runner. There is no build function.
- `e1_d17_analyze.py`: CPU reduction with R4/LOO and unpaired uncertainty, analytical
  references, target comparisons, dt/bare contrasts, temporal support, cost and
  precision diagnostics, plots and review. No dt=0 fit or stationary acceptance.
- `tests/d17_regression.py`: synthetic CPU regression specifications, unexecuted.

The selected binary is the archived accepted D1.6B executable, SHA256
`cdfc04f4c943843fd4ad6cdcab1c1267ad0bb012abfce4fdd3be78b64cc6032f`,
2,709,792 bytes, from source `0dea651b58171a72206774bcebb2f4c74960069b`.
Its original build proof is pinned to SHA256
`2ca6541ffd7c5bc205a207ee0f465276e7a357c8c8783d6d466963e557a5f6a8`
as recorded in the existing D1.6C original lock. Preparation validates it using
the existing D1.6B build validator, copies only into the fresh D1.7 root, checks
the historical log/dependency/library identities, and archives the accepted
scientific sources plus analysis tools. It never rebuilds, runs or changes the
old binary or accesses the protected production checkout. No binary was copied
during Codex preparation. Missing or changed old source/runtime dependencies
block readiness and require review, not substitution of a new executable.

The source comparison and historical build record are provenance, not an
independent proof of compiler arithmetic or physical execution. Compared with
D2A.5, this uses the earlier accepted D1.6B executable, no dynamics acquisition,
N32 and shorter duration. Compared with D1.6B stiff cells, source/executable,
physical parameters, exact initializer, T100 and regular cadence are preserved;
seeds differ, bare controls and fine dt are new, extra early frames and .01/50
coordinate audits are omitted, windows differ, inference is prespecified and
there is no post-selected primary family. The older [-0.04462] contrast is not
an independent estimate of the new late target offset or a planning margin.

The old constrained numerical validator is reused unchanged. It supports the
fine dt via its explicit exact schedule interface. A small bare-specific branch
binds the disabled metadata/schema/file inventory and regular clocks, checks
bond counts and endpoint correspondence, and reuses the same structural E1
checker. Initial backbone/anchor/site initialization method and parameters are
verified in metadata, with structural snapshot checks at0/T. This verifies
stored identities, not the statistical exactness of a single initialized draw.
Receipt SHA256/size closure binds every run, including logs, argv and exit status.
Complete24/24 receipts and an externally retained completion SHA are required
before reduction; inputs and analysis sources are rehashed after reduction.
Legacy validators hash during revalidation: multiple streaming I/O passes are
deliberate, with no full raw dataset loaded in memory.

Preparation's seed audit scans available JSON/JSONL/Python/Markdown/text under
the example and evidence root. It records file identities and exclusions: source/
build/preparation copies, regression directories, compressed data and raw CSVs.
The current session and seed-declaring candidate/protocol are excluded. Missing
or unreadable scoped files fail visibly. No guarantee is made about inaccessible
or compressed external seed use. The reviewer must reserve the proposed seeds;
the scan is not a global atomic reservation mechanism.

The runner requires a separate Stage-A approval, matching prepared manifest,
readiness, limits and root, plus an explicit execution flag. `stage_b_authorized`
must remain false. It rechecks frozen schedules/tools/binary before each member,
records environment and UUID, checks GPU idleness and resource floors, and uses
the existing supervised POSIX child with parent-death kill, process-group stop,
wall/RSS/disk/output guards and original timing definitions. A separate D1.7
GPU lock prevents duplicate D1.7 runners; it does not coordinate unrelated tools.
A whole-command alarm also bounds validation; checks are not hard-real-time.
Failure preserves status/receipts and consumes the one-shot attempt. No retry,
resume, replacement replica or automatic duration extension is supported.

The CPU analyzer retains frame averages and small diagnostics only. Two numerical
threads are set before imports; launch at nice19/idle I/O. It emits per-run
initial/windows/traces,27 primary late-target comparisons with numerical
sensitivity, conservative bounded-probability diagnostics, exploratory independent
dt/bare differences, drift, ACF, histograms, events and timing/peak RSS tables.
Connector covariances use Z/(Z−1) spatial centering correction. Temporal ACFs use
post-initial and late-half regular records, both sample and target centering;
conditional effective-frame counts never replace R4. No unsupported IAT is set
to zero. Drift significance is exploratory, not a stationarity test certificate.

`precision.csv` reports achieved nominal and primary-family halfwidths against
the proposed planning sensitivities. It includes a Gaussian SD upper bound from
R4 (chi-square3, two-sided95% construction) and an approximate normal mean-CI
replica-count scenario. This is deliberately qualified: it is not a trend-power
calculation, a guarantee about future variance, a Stage-B budget or a command.
Stage-B planning must evaluate independent dt-contrast variance, stationarity,
model alternatives and sensitivity to individual runs, not just that scenario.
Constant, h and h² models remain hypotheses; a three-parameter fit to three cell
means is saturated and cannot check higher-order departures. No fit is enabled
automatically, even if nominal intervals happen to be small.

## Proposed local commands — execute only after independent review

No command below has been executed in Codex. Review the committed code and
candidate sensitivities/resources first. Use fresh durable roots; existing roots
are refused and are never deleted by the tools. No command launches Stage B.

CPU-only synthetic verification (no historical evidence or GPU access):

```bash
cd /home/jramirez/UAMMD_KG-d2a5-analysis-dev
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  nice -n 19 ionice -c 3 timeout 600s \
  python3 examples/slip-springs/tests/d17_regression.py \
  --output /home/jramirez/UAMMD_KG-evidence/d17/regression-v1
```

The suite specifies exact grids/row counts and physical rates, seed collision
rejection on synthetic metadata, malformed/truncated/nonfinite frames, source/
build-input digest rejection, path/symlink/overwrite guards, R4/LOO/Welch and
zero-dispersion handling, analytical-reference construction, unresolved ACFs,
table/plot generation and rejection of changed/partial receipts and unauthorized
Stage-B approval. Physical output and historical build checks are mocked in the
synthetic cohort test. This does not replace real complete-output revalidation
or prove compiled bare/constrained behavior; those remain integration questions.

CPU preparation of a fresh pilot packet using the archived D1.6B binary:

```bash
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  nice -n 19 ionice -c 3 \
  python3 examples/slip-springs/e1_d17_host.py prepare \
  --root /home/jramirez/UAMMD_KG-evidence/d17/pilot-v1 \
  --executable /home/jramirez/UAMMD_KG-evidence/d16b/d16b-readiness-vjzdjbjn/campaign/provenance/semiflexible \
  --build-proof /home/jramirez/UAMMD_KG-evidence/d16b/d16b-readiness-vjzdjbjn/campaign/build.json \
  --build-proof-sha256 2ca6541ffd7c5bc205a207ee0f465276e7a357c8c8783d6d466963e557a5f6a8
```

Return `manifest.json`, `readiness.json`, `seed-audit.json`,
`approval-template.json` and regression/PASS.json for independent review.
Only after explicit authorization, save a separate `reviewed-approval.json`
under d17 with exactly the template fields, `execution_authorized=true`, a
nonempty `independent_review_reference`, and `stage_b_authorized=false`.
The tools do not manufacture approval. Retain its SHA256 independently.

Stage-A command after that approval, substituting the approved file digest:

```bash
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  nice -n 19 ionice -c 3 \
  python3 examples/slip-springs/e1_d17_host.py run \
  --root /home/jramirez/UAMMD_KG-evidence/d17/pilot-v1 \
  --approval /home/jramirez/UAMMD_KG-evidence/d17/reviewed-approval.json \
  --approval-sha256 TRUSTED_APPROVAL_SHA256 --execute-reviewed-stage-a
```

After numerical completion, retain `sha256sum` of pilot-v1/complete.json
independently. CPU-only analysis, substituting that completion digest:

```bash
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  nice -n 19 ionice -c 3 \
  python3 examples/slip-springs/e1_d17_analyze.py \
  --root /home/jramirez/UAMMD_KG-evidence/d17/pilot-v1 \
  --completion-sha256 TRUSTED_COMPLETION_SHA256 \
  --output /home/jramirez/UAMMD_KG-evidence/d17/analysis-v1
```

The analysis root is disjoint from the campaign. Provenance and final output
inventory must exist and FAILED.json must be absent. Return the review,
authentication/provenance/inventory, primary contrasts, precision and ACF/drift
evidence. A failure invalidates products and requires review of a fresh version;
there is no overwrite/resume path.

Unresolved before execution: independent code/regression review, actual unchanged
historical dependency/runtime availability, scoped seed reservation, adequacy of
T100 for slow stiff-backbone modes, and acceptance of proposed precision targets
and resource caps. The first pilot may demonstrate inadequate temporal support;
do not extend it automatically. A subsequent reviewed design must choose R/T,
any scientifically justified equivalence margins and identifiable dt models.
No test, preparation command, build, benchmark, analysis or simulation was run
in Codex. Stop for independent review before any execution. Stage B remains
unauthorized, and EQUILIBRIUM PRESERVATION NOT CONFIRMED remains the scientific status.
