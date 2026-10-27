# D1.6D — discrete-time stationarity analysis

Analytical preparation only; all proposed mathematical tests are unexecuted.
Use the [audit](E1_STAGE_D16D_THEORETICAL_AUDIT.md) for the measure, source rules,
translation convention and distinction between ideal and rounded arithmetic.
Here h=dt, T=kBT, mu=1/zeta, D=mu*T, b=mu*F, and Z>0.

## 1. Operator order and its exact invariant-measure implication

Operators below are backward operators on observables. Let E_h be one
Euler–Maruyama bead update with fixed attachments/anchors. Let Q_h=exp(hJ)
be the exact frozen-coordinate hopping/renewal semigroup implemented ideally
by the sequential Poisson batch. Because the bead update happens first,

    P_h f = E_h Q_h f.

The R dependence inside J is evaluated at the updated coordinates by this
composition. Reversing the operators would describe a different algorithm.
The jump batch includes all repeated attempts, rejections, attachment moves
and anchor replacements, not only the first accepted event.

Both exact subgenerators preserve the same joint pi: pi B=pi J=0. Therefore
pi exp(hB) exp(hJ)=pi for every h for which these semigroups are defined.
Lie splitting of these *exact* invariant substeps is not itself an equilibrium
bias mechanism, though it changes dynamics and need not be reversible. In this
scheme splitting transports the Euler–Maruyama defect. Nonreversibility of a
split finite-h step is not proof of an incorrect invariant measure.

There is an exact useful defect identity (ideal Q_h):

    pi(P_h-I)f = pi(E_h-I)Q_h f,

since pi(Q_h-I)f=0. It cannot generally be simplified to pi(E_h-I)f at finite h:
the jump substep can respond to the off-equilibrium distribution made by E_h.

## 2. Local weak expansion

For sufficiently smooth f, sufficiently integrable coefficients/derivatives,
and an expansion justified under pi, independent Gaussian increments give

    E_h = I+hB+h² C+o(h²),
    B = b_i partial_i + D Delta,
    C f = (1/2)b_i b_j partial_i partial_j f
          + D b_i partial_i Delta f + (D²/2) Delta² f.

Repeated Cartesian indices run over all bead coordinates. Coefficients in C
are frozen at the initial state; differentiating them in this expression would
incorrectly replace EM by the exact diffusion. Expand Q_h separately:

    P_h=I+hL+h² A+o(h²),
    L=B+J,
    A=C+BJ+(1/2)J².

BJ means apply J to the observable first, then B, including derivatives of the
coordinate-dependent rates and replacement densities. Consequently

    pi(P_h f-f)=h*pi(Lf)+h²*pi(Af)+o(h²)
               =h²*pi(Cf)+o(h²).

The O(h) Brownian and jump means vanish individually. The mean cross term
pi(BJf) and pure jump term pi(J²f) also vanish if Jf lies in the appropriate
weak-generator domain. Their pointwise values generally do not vanish.
No positive/negative sign is presumed for pi(Cf) for a general observable.

Equivalently define the formal modified generator

    L_h=L+h D1+o(h),
    D1=A-(1/2)L² = [C-(1/2)B²] + (1/2)[B,J].

Here [B,J]=BJ-JB. With E=C-B²/2, the diffusion defect is

    E f = -(1/2)[(b·grad)b+D Delta b]·grad f
          -D sum_(i,j) (partial_i b_j) partial_i partial_j f.

For conservative drift these involve force derivatives/Hessians and higher
potential derivatives. Since pi B=pi J=0, pi D1=pi E=pi C. Thus the commutator
has zero leading equilibrium source even though it affects propagated
observables and later-order corrections. A force-derivative expression is not
a numerical evaluation of its nonlinear equilibrium expectations.

These expansions are formal for the full model until domain/remainder conditions
are justified. Finite-rest-length radial forces and bending are singular at zero
bond length; the Hamiltonian does not put a hard wall away from small lengths.
Metropolis rates have derivative kinks at zero energy change. A naive globally
smooth Taylor theorem cannot be applied across those surfaces. A weak/distributional
integration by parts must include interface terms, or an adequate weak-domain
argument must be supplied. Gaussian unbounded proposals, rare near-singular
states, numerical aborts, and uniform integrability also need control. The exact
quadratic EM identity below does not require four force derivatives, but its
combination with Q_h still needs first-order weak consistency on Jf. We do not
claim a proved O(h³) remainder or invariant-measure expansion for this system.

## 3. Connector observable on the complete state

Let f_alpha(X)=|r_(s_alpha)-a_alpha|² for the *current* state of ID alpha, and
fbar=Z^(-1) sum_alpha f_alpha. A renewal changes both its site and anchor.
For a fully exchangeable labelled equilibrium lift the following individual
formula holds; for actual site-sorted initial IDs use the permutation-invariant
fbar. It is invalid to track a permanently frozen original bead-anchor pair
through attachment changes and call it the live connector observable.

For one EM substep with this attachment fixed,

    (E_h-I)f_alpha = h[2 e_alpha·b_(s_alpha)+6D]
                      +h² |b_(s_alpha)|².                 (1)

This is exact in ideal Gaussian arithmetic. Brownian fluctuations of all other
beads do not enter this quadratic directly. For the mean, sum (1)/Z.
By integration by parts or conditional connector Gaussians,

    pi[e_alpha·F_(s_alpha)]=-3T,
    pi(B fbar)=0,
    pi(E_h-I)fbar=h²*mu²*pi[sum_alpha |F_(s_alpha)|²/Z].     (2)

For (2), F=F_bb-k e; conditional on R,S, e has zero mean and E[e²]=A2. Thus

    pi[sum_alpha |F_(s_alpha)|²/Z]
       = (1/L) sum_sites pi_bb[|F_bb,site|²] + k²*A2.       (3)

The force is the *total* bead force; omitting backbone-force variance is wrong.
The remaining nonlinear backbone force-square expectation has not been evaluated.
The backbone force has a finite second moment at finite N and positive kb: each stretching force
is bounded by kb*(l+b0), and each angular-force contribution by a finite constant
times kappa/l. The equilibrium radial density behaves as l² near zero and has
Gaussian tails, so E[l²] and E[1/l²] are finite. Finite sums and Cauchy–Schwarz
then bound the total force square. This does not establish all derivative moments
or the weak consistency/remainder needed for a rigorous expansion; higher inverse
powers of l can be nonintegrable.

The explicit jump generator for a single ID is

    J f_alpha(X)
      = sum_admissible_adjacent_y (nu/2)*accept_(x,y)
          * (|r_y-a_alpha|²-f_alpha)
        + 1_(x terminal) sum_(vacant terminal_y)
          nu/(4M) * (A2-f_alpha).                         (4)

The sum is over *pre-event* vacant ends; source-end proposals are null. Renewal
uses the Gaussian expectation of the new quadratic, not zero extension, not the
old anchor at a new bead, and not a persistent pair's extension. Other IDs'
events leave f_alpha unchanged at that event. They do affect future rates.
For fbar sum (4)/Z. Exclusion and the state-dependent link-validity domain apply
to every hop. The ideal Poisson batch includes all powers of this joint J.

Detailed balance implies pi J fbar=0; it does not imply (4)=0 for each state.
At order h², the batch's equilibrium pure-jump and cross means are zero as in
section 2. Combining (2) with that expansion gives the derived, conditional result

    pi(P_h fbar-fbar)
      = h²*mu²*[(1/L) sum_sites pi_bb |F_bb,site|²+k²*A2]
        +o(h²).                                         (5)

The coefficient is strictly positive for k>0, under the assumptions specified
above. This sign was derived, not assumed. It is independent of nu at this order
for fixed finite nu as h->0. This is not an expansion uniform in nu->infinity
or in a rate chosen proportional to 1/h. At finite h the jump batch can change
the coefficient's effect through higher-order/nonuniform contributions. A
negative late-minus-early empirical contrast is not the one-step quantity (5),
and is neither explained nor ruled out by its positive leading sign.

For other observables, such as backbone dimensions, f has different derivatives;
there is no common positive drift theorem. For e⁴ at a fixed current attachment,

    C(e⁴)=4*(e·b_s)²+2*e²*|b_s|²+40D*(e·b_s)+60D².

The live-observable jump difference is |r_y-a|⁴-e⁴ for a hop and, after integrating
the replacement anchor, 15*(T/k)²-e⁴ for renewal. The same operator-domain
qualifications apply. Its target 125/3 does not make its drift identical to e².

## 4. Transient accumulation versus invariant-distribution perturbation

Let d_h=pi(P_h-I), a signed-measure defect. Starting from exact pi,

    pi P_h^n f-pi f = sum_(j=0)^(n-1) d_h P_h^j f.        (6)

Repeatedly multiplying the initial drift by n is generally incorrect. The
defect acts on propagated observables, and those can change sign. With justified
weak convergence and uniform remainder bounds, n*h=t fixed gives formally

    pi P_h^n f-pi f
      = h int_0^t pi[C exp(sL)(f-pi f)] ds +o(h).         (7)

An initial O(h²) per-step drift can therefore accumulate to an O(h) finite-time
transient at fixed physical time. Neither monotonicity nor a particular late-time
sign follows. Nonexact initialization adds an initial-distribution transient.
Window averages such as D1.6C's [90,100] minus [0,10] are differences of temporal
averages of (7), plus sampling variation; they are not pi_h f-pi f.

If, additionally, P_h has a unique stable invariant internal law, the ideal
process is sufficiently mixing, and a regular expansion pi_h=pi+h*eta+o(h)
exists uniformly enough to exchange time and h limits, then

    eta(1)=0,
    L*eta = -A*pi = -C*pi,
    eta(L psi)=-pi(C psi).

For a centered Poisson solution L psi=f-pi f,

    pi_h f-pi f = -h*pi(C psi)+o(h)
                = h int_0^infinity pi[C exp(tL)(f-pi f)]dt+o(h).  (8)

In the second form use psi=-int_0^infinity exp(tL)(f-pi f)dt and adequate decay.
If c=(C*pi)/pi is well-defined with appropriate boundary/domain conditions, the
integrand can be written E_pi[c(X_0)(f(X_t)-pi f)], a signed equilibrium
correlation. Its time integral has no established sign for fbar in this model.
The Poisson equation, force statistics and correlation integral are unresolved;
none was computed. Slow sectors can amplify the response. Full occupancy or
other invariant sectors invalidate unqualified uniqueness/mixing assumptions.

The expected O(h) stationary bias is consequently a conditional asymptotic
prediction, not a demonstrated convergence order at the two D1.6B timesteps.
Finite-time accuracy does not alone imply long-time accuracy. The unbounded
laboratory translations themselves have no invariant probability law; (8)
concerns internal observables with the translation convention already specified.

## 5. Harmonic toy and finite precision

Toy only: d independent coordinates in U=k|x|²/2 with a fixed anchor, no nonlinear
backbone and no hopping. Set a=mu*k, v=T/k. Then

    x_next=(1-a*h)x+sqrt(2D*h)*normal,
    E_pi[|x_next|²-|x|²]=d*a²*h²*v,
    v_h = v/(1-a*h/2),  provided 0<a*h<2,
    E[|x_n|²]=d*v_h+(1-a*h)^(2n)*d*(v-v_h).

This toy has positive one-step and stationary variance bias. It checks the
operator coefficients and distinction in time scaling; it supplies no sign
proof for the full nonlinear, relinking/renewing joint system. Outside the toy's
stability interval a finite invariant variance does not exist.

Actual floating-point/RNG execution has additional errors: k rounding versus
input anchor variance, mobility/noise rounding, finite-bit proposal distributions,
coordinate cancellation and acceptance arithmetic. They are not automatically
O(h²) and can dominate an arbitrarily small-h asymptotic at fixed precision.
No measurements or quantitative error budget for these effects were made. Keep
ideal mathematical detailed balance, truncation bias and finite-precision effects
separate in interpreting any later approved verification.
