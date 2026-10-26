# D1.6A.2 scientific implementation report

Status: preparation implemented; all tests and calculations unexecuted in Codex.
The actual development starting HEAD was `d2ebfa1632e36d8ef1f6e31f3b098273fee982ef`,
the filesystem-policy commit directly after the requested
`144cef60aebb322afe4e2de37c81d3017a4f2f41`. Branch history is preserved.

## Immutable predecessor and implementation scope

The user-reported original D1.6A outcomes for kappa=0 and kappa=10 were both
`REFERENCE_PRECISION_UNRESOLVED`: calibration and sizing completed, no final
reference draws, and no execution/resource failures. These historical outcomes
remain unchanged. No old sampling evidence is loaded by D1.6A.2. Previous
outcomes motivate the protocol revision; they do not supply confirmatory data,
pilot estimates, thresholds, seed choices or final estimates.

All additions are under `examples/slip-springs/`. Original source, tests,
contracts, accepted CPU sampler, simulator, CUDA, initialization, RNG physics,
hopping/renewal, observers and D0 tolerances are unchanged. Scientific evidence
under `/home/jramirez/UAMMD_KG-evidence/` was not modified. The old operator
guide is retained as frozen history; the new guide uses the permanent checkout.

New files and responsibilities:

- `e1_d16a2_reference.py`: independent confidence allocation, moment-only sizing,
  separate M/C assessments, full per-observable reporting and planned seed audit.
- `e1_d16a2_sampling.py`: separate three-phase worker, ledger, result schema and
  read-only saved-evidence replay. Uses the unchanged accepted `Chain.sample`.
- `e1_d16a2_local.py`: versioned readiness/approval/supervisor/results packaging,
  attempt consumption and resource/authentication failure reporting.
- `e1_d16a2_config.json`: frozen standalone protocol configuration.
- `e1_d16a2_schemas.json`: JSON Schema definitions for inference, selection,
  assessment, worker results, completion and approvals. Python authenticators
  additionally enforce cross-file identities, counts and status invariants;
  no new JSON Schema runtime dependency is required.
- `e1_d16a2_preserved_sources.json`: SHA256 pins for immutable D1.6A source,
  tests, contracts, accepted sampler and reused supervisor helper dependency.
- `tests/test_e1_d16a2_*.py`: prepared deterministic inference and control tests.
- `E1_STAGE_D16A2_LOCAL_EXECUTION_HANDOFF.md`: executable local A/B/C handoff.

Proven deterministic radial recurrence, independent quadrature, exact flexible
moments, analytical means, stable central merging, batch summaries and quantile
calibration are imported from the frozen D1.6A module without changing its
interfaces or outcomes. The inference implementation retains its stable
central-moment delta method and whole-batch delete-one jackknife; only the new
module's confidence allocation and reporting differ. The versioned worker and
supervisor retain the original resource mechanics without monkey-patching the
old workflow or adding a second simulator/sampler implementation.

## Frozen simultaneous confidence accounting

The original alpha=.05 allocation over 50 quantities (25 per stiffness) is
replaced, for D1.6A.2 only, by an explicit total alpha=.05 split:

| Family | Quantities across both stiffnesses | Alpha | Two-sided tail per interval |
|---|---:|---:|---:|
| M | 14 = 2 × (2 means + 5 primary moments) | .025 | .025/(2×14) |
| C | 36 = 2 × 18 frozen-cut probabilities | .025 | .025/(2×36) |

Bonferroni allocates the whole nominal error budget across families and both
stiffnesses without requiring independence of observables or families. No
observable is dropped. Within M, two analytical-mean consistency diagnostics
remain in the simultaneous family along with Var(Re²), Var(Rg²), Cov(Re²,Rg²),
E[Re⁴] and E[Rg⁴]. Student-t critical values use independent batches minus one
degree of freedom. The mean intervals have no added precision target; their
analytical consistency checks remain mandatory. The five precision gates use
≤5% relative half-width for variances/raw fourth-length moments, and
≤.05 sqrt(Var(Re²) Var(Rg²)) for covariance. Kappa=0 uses the exact analytical
scales; kappa=10 uses final point-estimate scales, as in D1.6A.

M intervals remain **nominal** delta-method/batch-CLT intervals, not guaranteed
finite-sample confidence bounds for high moments. Splitting alpha does not
remove that limitation. C uses exact two-sided Clopper–Pearson binomial
intervals at each frozen cut with the allocated tails. Final samples are
independent of calibration and sizing: conditional on the calibration cuts
(and the independently selected final count), C's simultaneous coverage is
valid, hence also unconditionally over these independent phases. Calibration
rank intervals retain their separately labeled diagnostic 95%/18 adjustment;
they are not an extra confirmatory family and are not a guarantee that the
population probabilities equal the calibration quantile labels.

Every C precision gate retains the original ≤.005 requirement. Half-width is
the larger endpoint distance from the point estimate, retaining the conservative
original convention for asymmetric binomial intervals. Estimates, batch delta
SEs, whole-batch jackknife SEs, simultaneous intervals, half-widths, targets and
decisions are reported for every observable; means are explicitly marked
`ANALYTICAL_MEAN_DIAGNOSTIC` for precision. Covariance matrices, W-batch moments,
eighth-length/tail diagnostics and numerical errors remain available for review.

## Independent selection, seeds and final decisions

Calibration=65,536, sizing pilot=8,192, batch=512, final grid=
16,384 / 32,768 / 65,536 / 131,072 / 262,144 / 524,288. The pilot predicts only
the five M precision gates with factor-two SE safety inflation and the
conservative 31-df M critical value throughout the grid. The smallest passing
count is frozen in `selection.json` before any final draw. C uncertainty cannot
change it. A zero/nonfinite M pilot SE fails visibly; C pilot SE does not drive
selection. No count qualifies → both families unresolved, no final assessment
and zero final draws. No grid extensions or favorable-result-based retries exist.

New entropy is `[721612000,kappa,phase,batch_index]`, with phases 1/2/3 and
zero-based batches. Local readiness expands all 2,336 maximum-grid new identities
and all 2,336 excluded original `[721610000,...]` identities, checking duplicate
entropy, generated uint32[4] identity and initial PCG64 state/increment. This
audit is prepared, **not executed in Codex**. The seed-audit record is separately
bound into the new approval. Distinct seeds are conventional independent-stream
construction, not a mathematical nonoverlap proof. Every executed batch records
entropy, identity, before/after PCG64 states and timing. Old evidence is never
used to audit by reading its samples; old planned identities come from the frozen
protocol specification.

Final phase data alone determine one final assessment. Calibration/pilot are
excluded. Fresh exclusive case/worker/attempt records prevent resumption and
reassessment; deterministic Stage C replay only compares saved decisions.
No new count, seed or cut can be selected after seeing final results.

`moments_status` is independently `MOMENTS_PRECISION_RESOLVED_NOMINAL` or
`MOMENTS_PRECISION_UNRESOLVED`; `cdf_status` is independently
`CDF_PRECISION_RESOLVED_NOMINAL` or `CDF_PRECISION_UNRESOLVED`. Mathematical
consistency includes positive conformational variances, positive-semidefinite
covariance, finite diagnostics, analytical means at both kappas, and all exact
kappa=0 moments including variances/covariance. Entire deterministic numerical
error bands must lie inside nominal sampling intervals. Analytical disagreement
sets `NUMERICAL_CONSISTENCY_FAILED` and `moments_accepted=false` even when M
precision alone passes. CI agreement is a consistency diagnostic, never proof of
exact sampling correctness. Invalid/unstable numerical inputs checked by the versioned inference and worker
stop with a numerical consistency failure and diagnostic error text; other
unclassified worker exceptions remain execution failures.

The supervisor accepts M only if precision and consistency pass. Unresolved C
does not raise a generic reference failure or fail the results command when
both M cases succeed; its unresolved status remains in worker, assessment,
completion, results and archive summary records. Failed/unresolved M cannot be
accepted. `RESOURCE_FAILED`, `AUTHENTICATION_FAILED` and `EXECUTION_FAILED`
are distinct operational failures; their raw records are preserved. Failed
pre-run attempts retain an attempt/error record even if no case was launched.
Missing or interrupted cases remain incomplete rather than inferred successes.

At kappa=0, exact analytical moments remain the primary reference and sampling
is independent consistency validation. At kappa=10, sampled moments cannot be
used as accepted references unless the independent final sample passes M and
consistency. Joint-null-law quantities retain the original analytical mean and
variance propagation diagnostics; unresolved/unaccepted outputs confer no
reference acceptance.

## Resource controls, authentication and unexecuted verification

Per stiffness caps are unchanged: 30 s/batch, 1,200 s supervised total, 1 GiB
host RSS, 16 MiB output, three phases, maximum 598,016 draws. Supervisor polling,
process-group termination, Linux parent-death kill, worker RSS/time/output
checks, OS file-size limit, headroom floors and no automatic retries remain.
The preexisting bounded-helper timing scopes are documented in the handoff.
The preparation checkout and evidence root must be durable, outside temporary
storage. Readiness captures source and dependency hashes; strict JSON and
nonoverwriting writes reject ambiguous or replaced metadata. New approval binds
the exact new readiness and seed audit, and original approval schemas fail.

Tests prepared for local execution cover separate gates in both directions,
M-pass/C-unresolved supervisor success, all retained observables, analytical
inconsistency, family alpha arithmetic and exact interval tails, C-independent
sample selection, stable merging/delta covariance/jackknife reproducibility,
maximum seed expansion and forced collision, unauthorized/old approval rejection,
immutable source hashes, resource/headroom failures, parent death guard,
nonoverwrite/exact-once case consumption, launch-failure preservation, compact
archive member hashes and active-case packaging refusal. Constructed arrays and
mock processes are used; tests draw no equilibrium configurations.

No tests, builds, numerical quadrature, seed expansion, simulations, reference
sampling, benchmarks or GPU preflights were run by Codex. Source/Git inspection
and diff checks support preparation provenance only; there is no scientific
acceptance or claim that local readiness has passed. All executable verification
belongs to the local workflow and independent evidence review. No GPU/T100/D2,
stress/rheology, D0 changes or dynamical equilibrium-preservation claim follows.

Exact local Stage A command:

```bash
python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d16a2_local.py readiness \
  --evidence-parent /home/jramirez/UAMMD_KG-evidence/d16a2
```
