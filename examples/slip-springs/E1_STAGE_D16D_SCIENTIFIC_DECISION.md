# D1.6D — scientific decision and review gate

Preparation only, 27 October 2026. **No simulator correction or new execution is
authorized by this audit.** Independent review comes next. See the complete
[measure/transition audit](E1_STAGE_D16D_THEORETICAL_AUDIT.md),
[source trace](E1_STAGE_D16D_SOURCE_TRACE.md) and
[discrete-time derivation](E1_STAGE_D16D_DISCRETE_TIME_ANALYSIS.md).

## Supported conclusions

1. The ideal canonical E1 target has fixed Z, site exclusion, uniform occupied
   subsets, and conditional independent Gaussian anchors. Integrating anchors
   gives the bare nonlinear semiflexible backbone. The intended connector
   moments are exactly 5 and 125/3 for A2=5. Uniformity is annealed, not conditional
   on frozen anchors. Ordered links add bookkeeping, not contour-gap weights.
2. The inspected random initializer samples that complete physical joint law
   in ideal arithmetic, including the requisite bead–anchor dependence. Its
   initially sorted IDs are not an exchangeable labelled draw; live-spring means
   are permutation invariant. Provided coordinates bypass the backbone draw.
3. Interior hopping and Gaussian end renewal obey frozen-R detailed balance on
   valid states in ideal arithmetic. Same-chain opposite-end transfers have
   reciprocal links and rates. Adding an ordinary energy Metropolis factor to
   renewal would generally break balance; no such change is recommended.
4. Stretch, bend and virtual-spring forces match the Hamiltonian on their defined
   domain. The corresponding continuous-time overdamped generator formally
   preserves the conditional Boltzmann density with the stated translation and
   boundary conventions. This does not establish well-posedness or ergodicity.
5. The finite-h EM/jump chain need not preserve the target. Under the documented
   weak-domain assumptions its first-order equilibrium drift cancels. For the
   all-live e² mean the leading one-step defect is positive h²*mu² times the mean
   occupied-bead total-force square. The jump and cross terms have zero
   equilibrium mean at this order. Exact diffusion/jump substeps would each
   preserve the target; their splitting alone would introduce no equilibrium
   defect. EM is the leading ideal arithmetic source here.
6. A stationary O(h) response is a conditional prediction requiring stability,
   mixing and a regular invariant-measure expansion. Its sign involves an
   unresolved Poisson equation/correlation integral. A positive one-step defect
   does not fix that sign or the sign of finite-window changes.

## Relation to the existing observations

The saved D1.6C result records stiff/coarse late-minus-early connector change
-0.04461609579755588, with nominal pointwise interval
[-0.058173047571152464,-0.031059144023959286]. Fixed occupancy-stratum weights
give -0.043483643333029454. These are quoted existing results, not recalculations.
The population adjustment weakens a pure coarse-composition explanation but
cannot isolate a mechanism or eliminate within-stratum composition effects.

The saved flexible late spatial-variance level is above its analytical reference
pointwise, but its six-contrast sensitivity includes zero, and the change interval
also includes zero. Mean conformational dimensions are broadly reference
compatible within exploratory uncertainty; this is not equivalence. IAT support
remains unresolved. Four replicas, same-data post-selection, correlated
diagnostics and two timestep levels prevent confirmation of any mechanism.
Neither nominal intervals nor their sensitivity establish post-selection FWER.

## Competing explanations

| Hypothesis | Support from this audit | Counterarguments / limits | Unresolved assumptions | Most discriminating future test, only after separate approval |
|---|---|---|---|---|
| H1: finite-timestep bias | EM has an explicit equilibrium defect; generic stationary response can be O(h). Coupling to nonlinear backbone forces and jumps enters propagated response. | The positive local coefficient does not explain the negative window change by itself. Two dt levels establish no asymptotic order or stationary limit. | Uniform weak expansion despite small-length singularities/rate kinks; stability, invariant internal law, mixing; force/correlation expectations and finite-precision budget. | Independently seeded, prespecified matched-physical-time refinement with at least one further dt, powered replica uncertainty, resolved transient and stationary support; distinguish initial one-step defect from long-time level response. |
| H2: incorrect joint initialization | A wrong conditional bead–anchor dependence could leave separate marginals correct and still create transients; finite precision and imported coordinates qualify exactness. | Actual default recipe samples backbone, uniform subset and anchors centered on those same beads; no ideal physical-joint-law defect found. Sorted IDs do not bias all-live mean. | Recipe and stored-state consistency for any supplied coordinates; rounding/PRNG limitations; finite-sample deviations from an ensemble draw. | Independently reviewed direct joint-identity checks at t0 and, if later authorized, an independent joint-state initializer with identical declared target; compare conditional scores rather than separate marginals only. |
| H3: jump detailed-balance violation | A state-dependent normalization over occupied/vacant ends, wrong reverse links, or omitted anchor proposal ratio would be mechanisms. | None is present in the inspected ideal rule. All-end proposals retain null attempts; Gaussian proposal cancels renewal energy ratio; valid same-chain relinking is reciprocal. | Bit-exact execution, rare aborts, all-state accessibility and finite-bit anchor/proposal laws are not mathematical density identities. | First independently review the prepared deterministic reciprocity cases; separately authorized direct production-kernel scripted checks at frozen separated R would distinguish implementation arithmetic from the proven ideal kernel. |
| H4: statistical/temporal support | R4, unresolved tails and post-selection leave finite-replica/slow-mode explanations open even for an invariant process. | All four stiff/coarse changes share a negative sign and the occupancy adjustment retains it; these deserve investigation, not dismissal. | Actual fluctuation tails, effective physical horizon, selection effects and power; absence of resolved IAT is not a measured relaxation time. | A new independent, separately powered and frozen replica cohort; horizon extension only if a reviewed support analysis identifies unresolved slow tails, cadence refinement only for temporal aliasing. |

The hypotheses can coexist. Coherent direction is a descriptive feature, not a
confirmatory sign test. Matching an ensemble moment is neither detailed balance
nor an ergodicity proof. Failed temporal support does not establish bias, and a
null-compatible difference does not establish stationarity.

## Unresolved questions and recommendation

Independent review should first check the normalized labelled/unlabelled measure,
translation quotient under renewal, reciprocal same-chain relinking, operator
order, and the h² cancellation/domain assumptions. It should assess whether a
weak expansion survives singular forces and Metropolis interfaces; second-force
moments alone do not prove this. General accessibility with renewal, relaxation
support, the nonlinear response integral and precision error magnitudes remain
unresolved. No expectation values were numerically evaluated.

Prepared tests in [tests/d16d_math_regression.py](tests/d16d_math_regression.py)
are **UNEXECUTED**, standalone mathematical specifications. Review them before
separately authorizing any local verification. They do not call the accepted
simulator, and harmonic toys prove nothing about full-system bias magnitude/sign.
Preserve the renewal rule, accepted scientific code, D0 tolerances and all
evidence. Choose subsequent work only after independent scientific review; this
milestone schedules no runs, references, analyses or campaigns.
