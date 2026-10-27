# D1.6E — scientific decision and limitations

Preparation only, 27 October 2026. Independent review and user execution remain
pending. No tests, symbolic checks, quadrature or scientific computations ran.

The [independent derivation](E1_STAGE_D16E_FORCE_SQUARE_DERIVATION.md) starts
with the accepted nonlinear Hamiltonian, converts the bead Laplacian through
the chain incidence matrix, differentiates each energy term, and applies
equilibrium integration by parts. It agrees with the proposed formula:

    K_bb=T/(N+1)*{2*N*kb*(3-2*b0*A)
          +(N-1)*[8*kappa*C*B+2*kappa*(1+D)*A²]}.

Here A=<1/l>, B=<1/l²>, C=<cos(theta)>, D=<cos²(theta)> under the bare nonlinear
backbone law. The mixed adjacent-bond Hessian trace is essential: it contributes
+2*kappa*(1+c²)/(l*m) for each angle before averaging. Dropping it would produce
a different, incorrect force-square formula. No discrepancy with the proposed
formula was found. This is a mathematical derivation, not an executed symbolic
or numerical verification.

The small-length boundary is compatible with this second-moment identity:
the radial l² Jacobian makes inverse first/second moments finite, and excision
flux vanishes. Higher inverse moments can diverge; this does not establish the
stronger regularity required for the full-step weak remainder or invariant-law
expansion. Factoring translation out of the ensemble must not remove an end
bead's force from the Cartesian trace.

The default equilibrium joint law retains the bare backbone after integrating
Gaussian anchors and canonical occupied subsets. The coefficient is therefore

    K_EM=mu²*(K_bb+k_ss²*a_ss²),
    <(E_h-I)mean_live(e²)>_pi=h²*K_EM

for the **bead-only** EM substep in ideal arithmetic. For the complete BD then
jump step the D1.6D result is h²*K_EM+o(h²), conditional on its weak-domain
assumptions. Its unresolved jump/splitting remainder is not computed by finding
K_bb. The supplied D1.6B decimal coefficients remain unverified; the
[numerical verification document](E1_STAGE_D16E_NUMERICAL_VERIFICATION.md)
and [standalone code](tests/d16e_force_square.py) prepare independent quadrature,
normalization, refinement, tail and algebraic checks without running them.

Zero virtual stiffness is a useful algebraic check but not a finite-connector
canonical ensemble at fixed positive T. The normalized family requires
a_ss²=3*T/k_ss, which diverges as k_ss->0+ while its added force-square term
3*T*k_ss vanishes. Setting k_ss=0 with a_ss²=5 would invalidate the equilibrium
cancellation premise. K_bb exists without springs; a live-spring mean is
undefined at Z=0. These distinctions should be retained in independent review.

The exact equilibrium force-square expectation, its mobility-scaled contribution
to one-step drift, higher-order full-step error, finite-time propagation and
long-time stationary bias answer different questions. Positivity of K_EM does
not imply monotone transient growth or determine stationary bias sign. It
does not explain the negative post-selected D1.6C connector contrast. No new
statistical interpretation, equilibrium acceptance or numerical timestep
acceptance follows.

Recommendation: review the mixed derivative, endpoint metric, boundary-flux
argument and zero-stiffness caveat; then the user may execute the prepared
deterministic verification and return its actual records. Review any numerical
disagreement before taking further action. No source correction, simulation,
sampling, analysis rerun or campaign is proposed or authorized here. Accepted
scientific source, evidence and criteria remain unchanged.
