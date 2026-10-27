# D1.6F — sign analysis, counterexample and conditional bounds

Theoretical preparation only. All algebra below is an analytical derivation;
no matrix, symbolic, numerical, test or scientific program was executed.
Notation follows the [invariant-response derivation](E1_STAGE_D16F_INVARIANT_RESPONSE.md):
F=f-pi(f), H=-L, source s=(C*pi)/pi, and a_f=<s,H^(-1)F> when defined.

## 1. What reversibility supplies, and what it does not

For a reversible ideal generator, H is nonnegative self-adjoint on its domain.
On the centered space its spectral resolution, if the inverse pairing exists,
gives

    K_f=<s,F>=int_(0,infinity) d<s,E_lambda F>,
    a_f=int_(0,infinity) lambda^(-1) d<s,E_lambda F>.    (1)

For discrete modes this is sum_n s_n*F_n/lambda_n. Reversibility makes
lambda_n positive, but the **mixed** spectral weights s_n*F_n may have either
sign. Positive sum_n s_n*F_n does not imply positive sum_n s_n*F_n/lambda_n.
Equivalently, the integrand <s,exp(tL)F> may become negative at longer times
despite being positive at t=0. There is no autocorrelation-positivity argument
for a cross-correlation of different functions.

Sufficient extra conditions would include s=c*F with c>=0, nonnegative mixed
spectral measure, or an exact eigenfunction F of H with positive K_f. In the
last case a_f=K_f/lambda. None has been proved for the nonlinear E1 live connector
observable. Nonnegative f itself is not such a condition: centering changes it,
and even a squared observable can exhibit the counterexample below.

## 2. Rigorous finite-state counterexample

This example disproves an inference based only on ideal reversibility,
first-order consistency, positivity of a squared observable and positive local
equilibrium defect. It is **not** EM of a potential, has no Gaussian anchors,
and is not a counterexample to any theorem requiring E1's particular kernels.

Take three states with uniform pi=(1,1,1)/3 and reversible generator

    L=(1/3)*[[-5, 4, 1],
              [4,-8, 4],
              [1, 4,-5]].

All off-diagonals are positive and rows sum to zero. The centered orthogonal
vectors u=(1,0,-1), v=(1,-2,1) satisfy L*u=-2*u and L*v=-4*v, with squared
pi norms 2/3 and 2. Choose

    f=(4,0,2), pi(f)=2, F=u+v,
    s=-2*u+v=(-1,-2,3),
    D0_ij=s_j/3, and P_h=I+h*L+h²*D0.

The observable is a square, f=e² with e=(2,0,sqrt(2)). For 0<h<=1/4, P_h is
a stochastic irreducible matrix: row sums are one; off-diagonals are
h*(L_ij+h*s_j/3)>0; diagonals are positive (the smallest is at least 7/24).
Thus this is a genuine family of Markov kernels with ideal generator L,
not an arbitrary signed evolution. Since pi*D0=s/3,

    pi(P_h-I)f=h²*<s,F>=(2/3)*h²>0.                   (2)

Yet the exact invariant probability is

    pi_h,j=(1+h*r_j)/3,
    r=H^(-1)s=-u+v/4=(-3/4,-1/2,5/4).

To check exactly, r*L=-s, and every probability row vector p satisfies
p*D0=s/3. Hence pi_h*(L+h*D0)=0. The components above are positive over the
stated h range and sum to one. The stationary observable is therefore exactly

    pi_h(f)=2-h/6,       a_f=-1/6<0.                  (3)

The equilibrium response integrand is explicitly

    <s,exp(tL)F>=-(4/3)*exp(-2*t)+2*exp(-4*t).

Its value at zero is 2/3, while its time integral is -2/3+1/2=-1/6. This supplies
both the Poisson and spectral/correlation checks without computation. For this
P_h, A2=D0 and the modified generator correction is D0-L²/2; the equilibrium
source remains s. Confusing these two operators is unnecessary to the example.

This shows **reversibility alone cannot settle the E1 question**. It does not
show that negative stationary connector bias occurs in E1, nor in the more
restricted class of linear Gaussian EM systems, which has additional positivity.

## 3. Additional E1 Gaussian information and the remaining obstruction

For E1 the source is specifically the bead EM defect, not the arbitrary D0
above. The conditional Gaussian identity in the companion derivation gives,
formally with the local density corrector g,

    a_f=3*mu*T/2+<g,J H^(-1)F>.                        (4)

This is stronger structure than the finite-state example possesses. The jump
term includes correlations between the Poisson solution and energy-dependent
contour acceptance, changing occupied sites and Gaussian renewal. No inequality
fixing its sign or bounding its negative magnitude by 3*mu*T/2 has been
established. Self-adjointness of J only gives <w,Jw><=0 for identical arguments,
not a sign for <g,J H^(-1)F>.

Thus neither sign is established for full E1. A negative sign is not excluded
by the general response framework, but its realization within E1 remains an
open question. The positive fixed-anchor harmonic and renewal toys below
demonstrate restricted positive cases; they do not prove a nonlinear E1 theorem.
The local-corrector identities also retain their weak-domain caveats near
collapsed backbone bonds.

## 4. Conditional bounds

If centered H has spectral gap lambda_gap>0 and s,F belong to L²(pi), then

    |a_f| <= ||s||_2*||F||_2/lambda_gap.                (5)

This follows from ||H^(-1)F||_2<=||F||_2/lambda_gap and Cauchy–Schwarz.
More generally a finite energy-dual pairing gives

    |a_f| <= ||H^(-1/2)s||_2*||H^(-1/2)F||_2.         (6)

The same conclusion follows from an independently justified integrable
cross-correlation envelope: if |<s,exp(tL)F>|<=G(t), then |a_f|<=int G.
Without a gap one can still use a suitable Poisson/coercivity estimate, but it
must be proved in a norm in which the source acts continuously. None is supplied
for full E1 by this milestone. In particular, second-force integrability does
not imply an L² EM source: derivatives of inverse-length forces are more singular.
Even the square integrability of g in (4) is not assured.

The centered all-live connector mean has the exact static norm

    ||F||_2²=6*v²/Z=2*(a_ss²)²/(3*Z).

This follows from independent Gaussian connectors conditional on R,S and fixed
Z, and remains true after annealed averaging. It supplies one factor in (5),
not the source norm or a relaxation scale. K_EM=<s,F> gives only one projection
of s, not an upper bound on its norm or its inverse-generator response.

Consequently no useful numeric full-model bound follows from the known K_EM
alone. No relaxation time is imported from unresolved D1.6C ACF/IAT records.
Slow sectors or low eigenvalues can amplify a signed response even when its
initial defect is modest. If the inverse diverges, (1) may fail to define a
finite coefficient and the assumed invariant expansion itself needs revision.

## 5. Rates, stiffness and comparison of timesteps

At fixed finite rates, the equilibrium source in (2) of the response derivation
does not depend on jump rate, but H does. Formally for J=nu*J0,
H_nu=H_B+nu*H_J0, and fixed s,F,

    d a_f/d nu=-<s,H_nu^(-1) H_J0 H_nu^(-1)F>.         (7)

This has no fixed sign for a mixed source/observable pairing. The monotone
decrease available for <F,H_nu^(-1)F> does not transfer to a_f. Renewal-off
or nu->0 can introduce new invariant sectors, while nu->infinity can be
singular because J alone freezes R. Neither limit is proved uniform here.

Increasing backbone stiffness changes force derivatives/source statistics and
the complete relaxation operator. Larger K_EM at kappa=10 does not imply a
larger stationary coefficient, its sign, or a proportional increase. The
coupled harmonic toy shows explicitly how one-step and stationary dependencies
can differ.

If the same E1 internal invariant family exists and admits a regular first-order
expansion at both timestep values, then

    pi_hc(f)-pi_hf(f)=(hc-hf)*a_f+o(hc)+o(hf).

An asymptotic ratio of biases equal to hc/hf requires a nonzero common a_f,
both timesteps in that regime and controlled remainders. If a_f=0, a higher
order or nonregular term may dominate. The two existing timestep levels alone
establish none of these facts, and finite-window contrasts are not invariant
level contrasts.
