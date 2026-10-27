# D1.6E — implementation and limitations report

Prepared 27 October 2026 in the permanent development checkout
`/home/jramirez/UAMMD_KG-slip-springs-dev`, branch `slip-springs`.
Starting local and actual remote HEAD both:
`f9acc55a3060aa0a016305fc25d655518528c7f8`, verified with `git ls-remote`
before work. No newer committed remote work was present at that check.

## Files and result

| File | Contents |
|---|---|
| [Force-square derivation](E1_STAGE_D16E_FORCE_SQUARE_DERIVATION.md) | Independent Cartesian derivatives, incidence metric, integration by parts, exact equilibrium averaging, dimensions and limiting cases. |
| [Numerical verification preparation](E1_STAGE_D16E_NUMERICAL_VERIFICATION.md) | Fixed cohort, separate quadrature/closed paths, normalization, tail bounds, stability and convergence checks; supplied values explicitly unverified. |
| [Standalone verification](tests/d16e_force_square.py) | Explicit quadrature, mathematical-test and optional SymPy actions; **all unexecuted**. |
| [Scientific decision](E1_STAGE_D16E_SCIENTIFIC_DECISION.md) | Agreement with the proposed formula, supported interpretation and remaining review/execution gate. |
| [README](README.md) | Links and preparation-only execution status in the current-simulator section. |
| This report | Implementation scope and limitations. |

The derivation agrees with the proposed force-square formula. The shared-middle-
bead mixed derivative supplies the positive 2*kappa*(1+D)*A² contribution after
averaging. Zero spring stiffness requires distinguishing algebraic force removal
from a normalized E1 ensemble, which has no finite connector variance at k_ss=0.
Numerical agreement with the supplied decimals is **not established**.

## What ran and what did not

Only read-only source/document inspection, file preparation and Git/repository
housekeeping were performed. No tests (including previous D1.6D tests), test
imports/discovery, symbolic differentiation programs, quadrature scripts,
builds, preflights, GPU queries, simulations, sampling, reference recalculations,
scientific analyses or other scientific computations were executed. Mathematical
derivations were written analytically; code was reviewed as text. No numerical
results or passing verification claims were fabricated. Future commands in the
verification document are for the user after independent review.

Accepted scientific source and D1.6D records remain unchanged. Source inspection
and Git comparison covered `semiflexible.cuh/.cu`, `fixed_slip_springs.h` and
`semiflexible_slipspring.cuh` against scientific SHA
`0dea651b58171a72206774bcebb2f4c74960069b`. No production source, RNG, integration,
jump rule, initialization, observer, evidence, manifest, approved source hash or
acceptance criterion was changed. All new work remains in `examples/slip-springs/`;
no persistent files were placed in `/tmp` or `/var/tmp`.

The verifier uses the standard library and an optional SymPy import only for
explicit symbolic execution. No dependencies were installed or added to project
configuration. No Makefile, campaign, launcher or execution infrastructure was
introduced. Its non-discovery filename avoids adding it to ordinary test suites;
direct invocation requires an explicit action. Git hooks are disabled for the
commit/push invocations to prevent implicit tests or other prohibited execution.

## Remaining limits

Analytic agreement does not verify the quadrature implementation, compiled CUDA
arithmetic or bit-exact force-square expectations. The numerical comparison
budgets are proposed engineering checks, with no certified interval error bound.
The optional symbolic simplification is also unexecuted. No change to historical
reference accuracy or D0 tolerances is implied.

The derivation proves finiteness of the needed second-force moment within the
stated canonical measure. It does not resolve all weak-domain assumptions for
the full-step remainder, dynamics at singularities, ergodicity, transient
propagation, finite-precision effects or long-time stationary bias. No inference
about the negative D1.6C contrast follows from the positive local coefficient.

Repository-only scope/ancestry/whitespace checks precede the normal non-force
push. The final commit SHA and remote verification are supplied in the handoff,
avoiding a self-referential commit identity in this report. Stop after preparation
for independent review; user execution of the explicit verification commands
remains the next computational step.
