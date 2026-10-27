# D1.6 — scientific closure

27 October 2026. **SCIENTIFICALLY CLOSED WITH QUALIFICATIONS — EQUILIBRIUM
PRESERVATION NOT CONFIRMED.** This is not a passed equilibrium-preservation
acceptance test. Closure consolidates D1.6B–F; it does not alter D0 criteria or
grant timestep, ergodicity, terminal-dynamics or rheology acceptance.

Starting local and actual remote `slip-springs` HEAD were both
`8638c06de3b63c3f783311a874713deade933fc4`, checked before this documentation-only
work. The accepted scientific source remains
`0dea651b58171a72206774bcebb2f4c74960069b`.

## Scientific record and strength of conclusions

| Evidence class | Consolidated finding and boundary |
|---|---|
| Established theoretical properties | The canonical E1 joint measure has fixed Z, site exclusion, uniform occupied-site subsets and conditional Gaussian anchors. Integrating anchors recovers the bare nonlinear backbone. The intended connector moments are `<e²>=5` and `<e⁴>=125/3`. Inspected ideal hopping and renewal satisfy frozen-coordinate detailed balance; the continuous-time bead generator formally preserves the conditional Boltzmann law with the stated translation/domain conventions. |
| Mathematical identities checked by derivation | D1.6D gives the exact quadratic bead-only EM identity. D1.6E independently derives the nonlinear backbone force-square expectation, including the mixed adjacent-bond bending term, consistently with that identity. D1.6F checks operator order, adjoints and response signs and derives exact solvable-toy covariances and a general reversible counterexample. These analytical checks are distinct from executed numerical tests; the committed D1.6D–F regression specifications remain recorded as unexecuted. |
| Exploratory simulation observations | All sixteen D1.6B N32/M256/T100 runs completed, with four independent replicas per stiffness/timestep cell. Mean conformational dimensions were broadly reference compatible within exploratory uncertainty. The flexible-chain variance excess was not robustly established after statistical qualifications. The stiff/coarse connector decrease persisted after occupancy-weight standardization. |
| Unresolved | Finite-timestep equilibrium preservation, full-model stationary connector-bias sign and magnitude, sufficient temporal support, general mixing/ergodicity, and the full weak-expansion/invariant-response assumptions remain unestablished. |

The [D1.6B protocol](E1_STAGE_D16B_PROTOCOL_V1.md),
[D1.6C secondary audit protocol](E1_STAGE_D16C_PROTOCOL_V1.md),
[D1.6D decision/source audit](E1_STAGE_D16D_SCIENTIFIC_DECISION.md),
[D1.6E force-square derivation](E1_STAGE_D16E_FORCE_SQUARE_DERIVATION.md) and
[D1.6F decision](E1_STAGE_D16F_SCIENTIFIC_DECISION.md) retain their detailed
scope, provenance and limitations.

## Connector signal and statistical qualifications

For kappa=10 and dt=0.00025, the saved D1.6C narrow-window contrast
`[90,100] minus [0,10]` is

    Delta <e²> = -0.04461609579755588, approximately -0.04462,
    theoretical equilibrium <e²> = 5.

This is a change between finite-window averages, not a measured stationary
offset from 5. The saved occupancy-standardized change is approximately
-0.04348; it weakens a pure coarse-composition explanation without identifying
a mechanism. The original uncertainty unit is one whole independent replica:
R=4 per cell, not the number of chains, springs, frames or overlapping origins.
Contrasts were selected after viewing the same exploratory data. Nominal
intervals and multiplicity sensitivity do not establish controlled post-selection
familywise discovery. Autocorrelation tails/IAT support remain unresolved;
no relaxation time or independent temporal sample count is inferred. Two
timesteps establish neither convergence order nor a zero-timestep limit.

## Local defect, stationary response and implementation conclusion

For the all-live connector mean f, the known leading ideal EM equilibrium defect is

    <P_h f-f>_pi = h²*K_EM+o(h²),
    K_EM=mu²*[<|F_bb|²>_site+k_ss²*a_ss²] > 0.

The bead-only quadratic identity is exact; the complete BD-then-jump expansion
retains D1.6D's weak-domain assumptions and uncomputed remainder. This local
coefficient is not the stationary coefficient. The latter involves a full
Poisson equation or signed equilibrium cross-correlation integral and requires
stability, mixing and a justified invariant-measure expansion. **Neither its
sign nor its magnitude has been established for full E1.** General reversibility
and positive local drift do not fix that sign; positive harmonic-toy biases
cannot settle the nonlinear model. The negative D1.6C contrast is not explained
by the positive one-step coefficient and does not establish a stationary bias.

**No implementation defect has been identified in the inspected equilibrium
initialization, hopping or renewal rules.** Their ideal joint-law and reciprocal
transition structure are consistent with E1. This is a source-level conclusion,
not bit-exact finite-precision certification. Finite-timestep equilibrium
preservation has not been confirmed; rounding, numerical integration, weak-domain
and temporal/statistical qualifications remain.

## Closure decision and retained limitation

Recommend proceeding to dynamical characterization **without changing the
accepted simulator**, after review and separate authorization of the next
milestone. Carry timestep sensitivity forward as a limitation when interpreting
subsequent physical results: measured dynamics must not inherit an unearned
equilibrium-preservation, rate-independence or terminal-relaxation claim.
D1.6 closes the present investigation with those qualifications; it neither
resolves the anomaly's mechanism nor converts exploratory evidence into an
acceptance pass. No next-stage design or execution is initiated here.

This closure uses the previously authenticated D1.6B/C records identified in
D1.6D and the existing D1.6C detached return manifest. Original analysis SHA256:
`04570c0ccb3b06df0f9be265a2bde602f1c2dcce59c474af963ca8634a17652f`;
secondary payload SHA256:
`3437e7983d38d0b70d3f9a3e934b582a6a7322e14c489d1949312db5a4907861`.
Only saved records and documents were read; authentication and scientific
reducers were not rerun. No tests, simulations, builds, analyses, quadrature,
symbolic programs or GPU operations ran. Source, parameters, algorithms,
protocols, evidence, manifests and acceptance criteria remain unchanged.
Stop after closure for independent review.
