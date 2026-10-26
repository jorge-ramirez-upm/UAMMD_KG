# D1.6B implementation and limitations report

Preparation-only revision. Actual starting local and freshly fetched remote
`slip-springs` HEAD was `e533e0412476c3e98875d9518afae42d75273928`; it equals the
last reviewed SHA and ancestry was checked before editing. Final commit identity
is supplied in the handoff response. All new source and changes are confined to
`examples/slip-springs/` in the permanent development checkout.

No test, build, GPU preflight, benchmark, trajectory, reference sampling or
scientific analysis job was executed in Codex. The implementation and tests are
unexecuted preparation, not evidence that local readiness or science passed.
Source reads, Git operations, provenance-identity capture and source-file authoring
are the only work performed. Existing scientific evidence was inspected read-only.
No files were written to old D1.5/D1.6A/D1.6A.2 roots or temporary checkouts.

## Files and boundaries

New scientific/operational documents:

- `E1_STAGE_D16B_PROTOCOL_V1.md`: frozen cohort/seeds/schedules, reference import,
  exploratory estimators, confidence qualifications and interpretation.
- `E1_STAGE_D16B_RESOURCE_AMENDMENT_V1.md`: new proposed caps, scope and overhead,
  schema-derived output envelope and independent approval boundary.
- `E1_STAGE_D16B_OPERATOR_GUIDE.md`: exact persistent-path Stage A/B/C commands,
  independent approval procedure and two-file return instructions.
- This implementation/limitations report.

New implementation:

- `e1_d16b_spec.py`: candidate validation, rational schedules, all16 seeds,
  accepted-source/tool closure, durable paths and independently versioned limits.
- `e1_d16b_references.py`: read-only full-closure reference/performance imports,
  primary analytical versus sampled moments, recorded intervals/covariance and
  retained CDF-precision status.
- `e1_d16b_auth.py`: new readiness/approval contract, source/build/runtime/raw
  authentication and complete-cohort checks. It reuses schema-generic accepted
  helpers through isolated bindings, following the existing repository pattern.
- `e1_d16b_host.py`: fresh accepted-source double compilation, read-only preflight,
  durable GPU lock, explicitly approved sequential cohort, bounded output
  authentication and preserved failure/completion receipts.
- `e1_d16b_local.py`: self-contained local A/B/C commands, dependency/environment
  snapshots, exclusive launch/attempt records, bounded analysis and compact returns.
- `e1_d16b_analysis.py`: separate long-time exploratory analysis; no mutation of
  the Phase B analyzer and no automatic equilibrium pass.
- `tests/test_e1_d16b.py`: prepared deterministic mathematical/control tests.

New configuration directory `e1_d16b_config/`:

- `manifest.json` and `manifest.sha256`: false-authority, non-executable candidate.
- Six `dt*.scalar/full/snapshots.steps` files: exact schedules.
- `resources.json`: proposed versioned resource amendment; approval remains false.
- `reference-lock.json`: reviewed D1.6A.2 evidence identities and review basis.
- `performance-lock.json`: archived M256 D1.5 planning identities.

README's current-simulator section links the new preparation handoff and permanent
checkout. Existing model/build/example commands remain unchanged. Their previous
validation claims are not extended to this revision. The existing `AGENTS.md`,
accepted model/CUDA/CPU sampler/RNG/observer/initialization/hopping/renewal, D0
margins, old tests and frozen configurations/results retain their contents.

## Scientific choices and consistency

This implements the primary D1.6 design without changing M,R,T, physical parameters,
timesteps or the never executed D1.5 T100 seed list. The separate audit amendment
uses0,.01,50,100, preserves the five early full frames and retains exact201/51/56/206
scalar/regular-full/total-full/union counts. Full raw chain/spring/site/identity
records stay local. Every expected row count is checked by the new specification
and unchanged raw/snapshot validators. There is no interpolation or unsynchronized
joint inference.

D1.6A.2 source/config/approval/completion/results identities are captured from
existing files. These preparation pins are not a fresh computational authentication
or independent review: local Stage A must authenticate the full raw/batch closure
before importing numerical values. The user's current instruction establishes
that the moment families were previously independently reviewed. No manual rounded
variance/covariance from chat is used as a numerical input. Both exact size means
and flexible moments stay analytical; stiff higher moments retain their independent
sampling intervals and full covariance/jackknife diagnostics. Stiff CDF precision
stays unresolved in the import, analysis, outcomes and packet.

The new analysis preserves whole replicas as independent units, including time
windows and paired changes. R4 t/Welch and Gaussian-replica variance intervals
are nominal diagnostics, not guaranteed high-moment coverage. Bounded probability
and bounded-change inference has a replica Hoeffding fallback. Independent
reference intervals expand trajectory difference intervals rather than being
spent as extra physical tolerance. The .025 trajectory/.025 recorded-family
allocation has only pointwise nominal coverage across comparisons; it establishes
no simultaneous campaign discovery or equivalence family. Shared references
cancel from matched-dt contrasts. The exact source of every reference, recorded
uncertainty and numerical centering error remains visible. Original numerical error estimates
retain their engineering qualification; they are not certified interval arithmetic.

ACFs use physical regular grids, actual lag/origin support, whole/late segments,
fixed-label within-replica diagnostics, two centerings, positive-pair/self-consistent
window checks and half-record sensitivity. Event ACFs use actual regular-bin
rates. Undefined conserved/zero-variance series differ from slow unresolved tails.
Unsupported IATs remain null with partial sums and support; they are never zero
or converted into an independent temporal sample count. IAT checks are conservative
heuristics conditional on stationarity. A finite supported candidate is not a
proof of mixing or absence of drift. Independent replica support is reported
without discarding unfavorable replicas.

Operational completeness, provenance failure, statistical deviation, precision,
CDF reference quality and correlation support are separate. Numerical/provenance
or resource failure produces no valid full-cohort physical inference. A partial
campaign returns its failure/identity records and stays scientifically incomplete.
Several exploratory scientific outcomes can coexist. No code emits a confirmatory
D0 equilibrium pass or claims dynamical-preservation correctness from static
reference agreement.

## Proposed resources and enforcement

The unchanged D1.6 format envelope is115,192,412 CSV bytes/run and1,843,078,592
bytes/cohort before metadata. New proposed caps are600 s/run stage,14400 s/outer
cohort command,2 GiB scientific/authentication child RSS,8 GiB available host,
4 GiB free GPU,256 MiB/run,4 GiB aggregate output and10 GiB maintained disk floor.
Initial free disk must cover the floor plus two aggregate quotas:18 GiB, with
separate source/build/reference provisioning. Local readiness reauthenticates
M256 D1.5 measurements; ~34.3 min gross-production projection is only planning.
No old cap is bypassed or enlarged: new orchestration uses its own exact resource
validator and review contract. Schema-generic process/output primitives are reused.

The output-authentication child is limited to the remaining600 s run-stage
budget. Its records count against256 MiB along with the scientific run. The
outer14400 s timer also covers prelaunch and final authentication. A launch and
attempt are exclusive and consumed before scientific execution; failures cannot
resume or retry. Linux parent-death guards cover the local/host/GPU supervisor
chain. Abrupt orphan markers block further actions pending review. Polling and
termination are not hard real-time guarantees; exceeded limits prevent success.
Stage C separately has7200 s/4 GiB/256 MiB, and packaging has32 MiB payload and
16 MiB/member limits. The compressed analysis is embedded; raw CSV/binaries remain
local with hash inventories. Packaging never silently discards oversized evidence.

## Prepared tests and remaining dependencies

New tests cover all16 frozen seeds/physical cells; rational schedules/row counts/
audit placement; immutable old T100 status/hash; new caps versus unchanged old
validator; durable paths; exact small finite-M occupancy and analytic connector
CDF/moments; R4 and independent-cell uncertainty; sampled-reference bounds and
unresolved CDF status; correlated/dispersed constructed series, unresolved/constant
ACFs and exact timestep/window matching; reference corruption/non-PSD covariance;
false/old/wrong-SHA approvals; incomplete cohorts/missing frames/strict JSON;
nonoverwrite, simulated supervisor failure preservation/no second invocation;
and archive checksums/raw omission/active-root refusal. Mathematical fixtures
are in memory or explicitly labeled non-production fixtures in durable scratch.
The unchanged nine-step technical suite supplies the local GPU schema/audit/raw
reader check; no production trajectory fixture is fabricated.

All those tests remain unexecuted. The next dependency is local readiness on
the recorded CUDA13/sm86 host with full original evidence available and sufficient
resources. The tiny-fixture flag requires the operator's existing independent
local readiness-scope authorization; it is not issued here. After A, a new
independent scientific/resource/readiness review and explicit approval are still
mandatory before a single T100 member. No approval record with true authority is
created by this preparation. Missing evidence, unsupported environment, test/build
failure or insufficient resources blocks B. The scientific results and actual
analysis/archive cost/size remain unknown until local execution.

No D2, T100 trial, benchmark, new reference calculation, stress/rheology or
accepted-dynamics modification is included. Existing scientific evidence remains
unchanged, and no conclusion about preservation, terminal time, timestep order
or zero-timestep behavior is asserted.

Exact local Stage A command:

```bash
python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d16b_local.py readiness \
  --evidence-parent /home/jramirez/UAMMD_KG-evidence/d16b \
  --cuda-home /usr/local/cuda \
  --authorize-tiny-readiness-fixtures
```

Return `d16b-readiness-return-<UTC timestamp>.tar.gz` and its `.tar.gz.sha256`
sidecar from the printed durable root's `returns/` directory.
