# D1.6F — invariant response of the BD-then-jump chain

Theoretical preparation only, 27 October 2026. No mathematical program,
quadrature, tests, symbolic software, builds or scientific computations ran.
Starting local and actual remote branch HEAD both:
`4973cf4c2178eef6fcd401e99cea9f23527ae64f`.

Source inspected: `semiflexible.cu:451–465`, `semiflexible.cuh:22–87`,
`slip_hopping.cuh:18–46,64–105`, `slip_renewal.cuh:13–125` and E1's canonical
measure. The four implementation files are unchanged from accepted scientific
SHA `0dea651b58171a72206774bcebb2f4c74960069b`. Historical lines are mapped in
[D1.6D's source trace](E1_STAGE_D16D_SOURCE_TRACE.md). No simulator change is made.

## 1. Backward operators, adjoints and the invariant perturbation

Let T=kBT, mu=1/zeta, D=mu*T, k=k_ss, v=T/k, and Z>0. Write B for the bead
diffusion generator at fixed occupied sites S and anchors A, J for the complete
frozen-R hopping/renewal generator, and L=B+J. On observables,

    B f=b_i*partial_i f+D*Delta_R f,  b=mu*F=-mu*grad_R U.

Repeated indices range over all bead Cartesian coordinates. J includes accepted
hops, Gaussian renewal densities, exclusion, reciprocal contour links and null
attempts. Ideal sequential Poisson batches implement Q_h=exp(hJ). B and J each
preserve the same ideal joint pi and are reversible on an appropriate common
domain; this is an ideal-arithmetic statement, not bit-exact CUDA balance.

The source updates beads, swaps the coordinate buffer, then processes the entire
jump batch at the updated coordinates. Thus backward operators compose as

    P_h=E_h Q_h,
    E_h=I+hB+h² C+o(h²),
    C f=(1/2)*b_i*b_j*partial_i partial_j f
         +D*b_i*partial_i Delta_R f+(D²/2)*Delta_R² f,
    P_h=I+hL+h² A2+o(h²),
    A2=C+BJ+J²/2.                                      (1)

The b coefficients in C are frozen when differentiating f. BJ applies J first
and B second, including derivatives of J's R-dependent coefficients. The
forward density operator is P_h*=Q_h* E_h*, so
A2*=C*+J*B*+(J*)²/2. Since B*pi=J*pi=0,

    A2*pi=C*pi,
    pi(P_h-I)f=h²*pi(C f)+o(h²).                       (2)

The formal modified generator is a different operator:

    h^(-1)log(P_h)=L+h D1+o(h),
    D1=A2-L²/2=C-B²/2+[B,J]/2.                         (3)

Its equilibrium source is also D1*pi=C*pi. Its action on nonequilibrium
observables is generally different from C and A2. Exact diffusion followed by
exact jumps would preserve pi for every h: the leading equilibrium defect here
comes from EM, with splitting affecting its propagation and higher orders.

Assume a differentiable invariant internal law pi_h=pi+h*eta+o(h), eta(1)=0.
Expanding pi_h P_h=pi_h gives

    eta L=-pi A2=-pi C,
    L*eta=-C*pi.                                       (4)

For F=f-pi(f), choose a centered Poisson solution L psi=F. Then

    a_f:=eta(f)=-pi(C psi),
    pi_h(f)-pi(f)=h*a_f+o(h).                           (5)

For reversible L define H=-L, and, if meaningful, s=(C*pi)/pi, so pi(s)=0.
If eta=r*pi, (4) becomes H r=s. Equivalently u=H^(-1)F=-psi and

    a_f=<s,H^(-1)F>_pi
       =int_0^infinity <s,exp(tL)F>_pi dt.              (6)

The signs in (4)–(6) agree: eta L=-pi C, L psi=F and H=-L. An adjoint-free
version of (6) is int_0^infinity pi[C exp(tL)F]dt, when that pairing exists.
It remains useful when s is only a distribution rather than an L² density.
No response integral is evaluated here.

## 2. Assumptions needed before using these formulas as a theorem

The measure, generator and invariant expansion must refer to the same state
space and convention. Specifically:

- Use the canonical fixed-Z, excluded-site target and either permutation-invariant
  observables or a consistent labelled lift. No extra contour-order weights.
- Remove translations from the unbounded laboratory measure consistently,
  shifting associated anchors with their chain. Laboratory bead positions have
  no normalized equilibrium law. Pinning a bead with unchanged lab noises would
  change the process. Empty chains and cross-chain renewal require the same
  quotient convention as the target; internal connector observables are valid.
- Establish a well-defined reversible continuous-time process, common weak
  domains, integrable pairings and boundary/no-flux conditions. Near collapsed
  bonds the angular forces are singular; Metropolis rates have derivative kinks.
  Finite second-force moments from D1.6E do not establish fourth derivatives,
  an L² source, or a uniform integrated weak expansion.
- Prove sufficient stability/existence for P_h, and weak remainders controlled
  under the measures/Poisson solutions being used. Ideal Gaussian EM can visit
  arbitrarily small bonds; production aborts are not an equilibrium conditioning
  procedure. Floating-point/RNG effects are additional to this expansion.
- Specify uniqueness or fix invariant sectors and their weights. Renewal-off,
  zero-rate, full occupancy and frozen-anchor limits have conserved sectors.
  A zero mode of H beyond constants requires compatibility and a specified
  inverse; a full-process ergodicity theorem is not available.
- Supply enough mixing/decay for the centered Poisson solution and correlation
  integral, and uniform control to exchange h->0 and t->infinity. A gap is one
  sufficient route, not an established property of E1. Existence of a finite-time
  weak expansion alone is insufficient for an invariant expansion.

Under these unproved full-model conditions (1)–(6) define a formal leading
response. Without them, they remain conditional representations, not a numerical
bias measurement or an established convergence order at the D1.6B timesteps.

## 3. A useful local density corrector and its limitations

For a smooth conservative potential with constant scalar mobility, integration
by parts in the EM weak defect yields the familiar local corrector, here derived
as the candidate to check against C*:

    g=mu/(4*T)*|grad_R U|²-(mu/2)*Delta_R U,
    C*pi=-B*(g*pi)=-pi*B g, hence s=-B g.               (7)

One can verify (7) by substituting b=-mu*grad U into C*, using
partial_i pi=-(partial_i U/T)*pi, and grouping the remaining terms as
-div_R[b*g*pi]+D*Delta_R(g*pi) with an overall minus sign. In one dimension
the coefficient of the highest fourth derivative agrees on both sides; the
two terms in g are needed for all lower derivatives. An additive constant in
g is irrelevant. Equation (7) is a local identity; it does not assert that
g*pi is the unique invariant correction when B has frozen-anchor sectors.

For the full coupled model let H_B=-B and H_J=-J, H=H_B+H_J. Formally,

    a_f=<H_B g,H^(-1)F>
       =<g,F>+<g,J H^(-1)F>.                           (8)

For f=mean_live(e²), Gaussian anchor integration gives an exact static pairing
of the candidate g with the centered observable:

    <g,F>=3*mu*T/2.                                    (9)

Indeed |grad_R U|²=sum_i |F_bb,i|²-2*k*sum_alpha e_alpha·F_bb,salpha
+k²*sum_alpha e_alpha², while Delta_R U=Delta_R U_bb+3*k*Z.
Backbone-only terms have zero covariance with F, odd connector terms integrate
to zero, and Var(sum e²)=6*Z*v² gives (9). Thus, subject to (7),(8)'s domains,

    a_f=3*mu*T/2+<g,J H^(-1)F>.                        (10)

This separates a known static term from a genuinely dynamical signed correction.
It does not give a lower bound: neither J nor g has the alignment with F needed
to bound the second term by zero or by -3*mu*T/2. See the reduced renewal toy
for a solvable case where the correction is negative but the total is positive.

For the actual nonlinear E1 potential, g contains inverse-square bond terms.
It can be integrable without being square integrable; applying B to it can
produce more singular distributions. Equations (7),(8),(10) therefore require
additional weak-domain justification and cannot be used as an unconditional
L² theorem for E1. The static Gaussian pairing (9) is finite under the already
established second-force integrability. No fourth-force-moment assumption is
silently imported. The [sign analysis](E1_STAGE_D16F_SIGN_ANALYSIS.md) provides
bounds only under explicit source/domain hypotheses.

## 4. One-step coefficients, provenance and temporal interpretation

D1.6E gives pi(C f)=K_EM>0 for the current all-live connector mean. The current
brief quotes K_EM=63.7354837900 and 161.2134885751 for kappa=0 and 10.
Those supplied values are treated as contextual prior coefficients, not new
calculations. The committed D1.6E preparation records its verifier as unexecuted;
this milestone neither reruns it nor independently authenticates any subsequent
numerical verification. No historical record is changed.

K_EM=<s,F> is the correlation integrand at t=0; a_f is its integral over time.
For exact initial pi, finite-time propagation is formally

    pi P_h^n f-pi f
      =h*int_0^t pi[C exp(sL)F]ds+o(h), t=n*h fixed.

The late-minus-early window contrast subtracts averages of this transient plus
sampling variation. It is not h*a_f, and may have a different sign. Hopping and
renewal change the response even though their leading equilibrium source cancels
from (2). The stationary sign/magnitude for full E1 remains unresolved.
