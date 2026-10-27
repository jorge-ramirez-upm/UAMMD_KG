# D1.6D — implementation and limitations

Prepared 27 October 2026 in the permanent development checkout
`/home/jramirez/UAMMD_KG-slip-springs-dev`, branch `slip-springs`.
Starting local and actual remote HEAD:
`d6924acbed63d9facc667cd8e72a73e61d597676`. Remote was queried with
`git ls-remote origin refs/heads/slip-springs` before audit work. No newer
committed remote work was present. Two existing untracked audit/analysis drafts
were retained, source-checked and completed.

## Deliverables

| File | Purpose |
|---|---|
| [THEORETICAL_AUDIT](E1_STAGE_D16D_THEORETICAL_AUDIT.md) | Normalized canonical measure, translations/identities, joint initialization, detailed balance, forces/generator and precision qualifications. |
| [SOURCE_TRACE](E1_STAGE_D16D_SOURCE_TRACE.md) | Exact accepted SHA, functions and line ranges for all rules and observation phase. |
| [DISCRETE_TIME_ANALYSIS](E1_STAGE_D16D_DISCRETE_TIME_ANALYSIS.md) | Operator order, EM defect, live-observable jumps, small-h cancellations, response/Poisson formulas and harmonic toy. |
| [SCIENTIFIC_DECISION](E1_STAGE_D16D_SCIENTIFIC_DECISION.md) | Supported conclusions, H1–H4 comparison, unresolved assumptions and future discriminators. |
| [Mathematical specifications](tests/d16d_math_regression.py) | Standalone deterministic tests, **UNEXECUTED**; excluded from ordinary `test_*.py` discovery and no build-target changes. |
| [README](README.md) | Audit links and explicit preparation/review gate in the current-simulator section. |
| This report | Scope, provenance, execution status and practical limits. |

## Execution status and limits

No unit/integration tests, Python test import/discovery, builds, simulations,
GPU queries/preflights, numerical sampling/Monte Carlo, reference recalculations,
scientific reducers/analyses, or computational experiments ran. Python was used
only to read stored JSON/gzip interpretation records and for repository/document
housekeeping; none of the prepared test formulas was evaluated. Historical
reports were read as prior evidence. D1.6C authentication/statistics were not
rerun. No persistent work was placed in `/tmp` or `/var/tmp`.

Verification in this milestone means source/document inspection and Git scope,
whitespace, ancestry and changed-path checks only; it is not a scientific test
pass. The eight traced scientific files are unchanged from accepted scientific
source `0dea651b58171a72206774bcebb2f4c74960069b`. All accepted simulator,
initialization, RNG, hopping/renewal, observer and integration code remains
unchanged, along with results, D0 tolerances, evidence, approved hashes and
manifests. No execution infrastructure, dependencies or campaign was added.

The mathematical tests cover exact quadratic energy derivatives, Metropolis
ratios, exclusion/order reciprocity, Gaussian renewal density reciprocity,
same-chain/cross-chain link cases, occupancy/label factors, analytic Gaussian
normalization/moments and exact harmonic moment identities. Their normalization
case uses the Gaussian integral theorem; it is not independent numerical
integration. They neither execute CUDA nor establish compiled-source correctness.
No test results are claimed. The harmonic moment recurrence is a proposed exact
algebra check, not a simulation or a proof for the nonlinear model.

Formal invariance does not prove mixing. Weak/domain and invariant-measure
expansions need further mathematical justification around singular bond forces
and Metropolis interfaces. Nonlinear backbone force statistics and the response
integral were not evaluated. Rounded stiffness versus input anchor variance is
a source-level precision qualification with no established empirical magnitude.
The post-selected R4 connector signal does not determine a mechanism.

The final commit SHA and push outcome are reported in the handoff rather than
embedded self-referentially in this report. Publication uses a normal push that
preserves branch history. Stop after preparation: independent review and
separate authorization must precede local computational verification, new
scientific execution or changes to accepted source. The only new future command
is the explicit mathematical-test command in its file docstring; **do not run it
as part of D1.6D preparation**. Existing simulator commands remain unchanged.
