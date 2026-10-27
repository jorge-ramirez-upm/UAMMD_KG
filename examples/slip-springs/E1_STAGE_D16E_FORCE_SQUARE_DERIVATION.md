# D1.6E — independent backbone force-square derivation

Preparation only, 27 October 2026. No symbolic program, tests, quadrature,
builds, sampling, simulations or scientific analyses were executed. Numerical
verification remains pending independent review and user execution.

Starting local and actual remote `slip-springs` HEAD:
`f9acc55a3060aa0a016305fc25d655518528c7f8`. The remote was queried before work.
The accepted Hamiltonian and forces were inspected in `semiflexible.cuh`,
lines 22–68, at scientific source
`0dea651b58171a72206774bcebb2f4c74960069b`; those kernels and the relevant host
coefficient/initialization/integration code are unchanged at starting HEAD.
See the [D1.6D source trace](E1_STAGE_D16D_SOURCE_TRACE.md).

## 1. Start from the implemented Hamiltonian and bead derivatives

For one open chain with N bonds and N+1 beads, let

    q_i=r_(i+1)-r_i, l_i=|q_i|, u_i=q_i/l_i, c_i=u_i·u_(i+1),
    U_bb=sum_(i=0)^(N-1) kb/2*(l_i-b0)²
         +sum_(i=0)^(N-2) kappa*(1-c_i).

Write T=kBT, beta=1/T. Assume N>=1, kb>0, T>0, b0>=0 and finite kappa>=0.
The source stores the stretch coefficients as (b0,kb); its angular energy is
kappa*(1-c), not kappa*c² or kappa*theta². The three angular forces are A,B-A,-B,
where A=grad_q U_angle and B=grad_p U_angle. Energy is distributed over beads
for bookkeeping without altering this total Hamiltonian.

The incidence rule gives

    grad_r0=-grad_q0,
    grad_rj=grad_q(j-1)-grad_qj,             1<=j<=N-1,
    grad_rN=grad_q(N-1),
    Delta_R=2 sum_i Delta_qi
            -2 sum_(i=0)^(N-2) grad_qi·grad_q(i+1).       (1)

Equivalently G is the bond-space tridiagonal metric with diagonal 2 and nearest
off-diagonals -1, and Delta_R=div_q(G grad_q). The off-diagonal coefficient -2
is essential: the middle bead of two adjacent bonds moves both bonds in opposite
directions. Bead 0 may be fixed to define the ensemble's translation gauge, but
its force is still included in Delta_R and in the sum of bead force squares.
Replacing (1) by the Laplacian of N independently diffusing bonds is incorrect.

## 2. Cartesian stretching Laplacian

For V(l)=kb*(l-b0)²/2 in three dimensions, at l>0,

    grad_q V=kb*(l-b0)*u,
    Delta_q V=V''(l)+2*V'(l)/l=kb*(3-2*b0/l).

A stretch term depends on only one bond, so every mixed bond derivative of that
term is zero. Its two bead endpoints each contribute Delta_q V. Thus

    Delta_R V=2*kb*(3-2*b0/l).                         (2)

At b0>0 the pointwise expression diverges at zero length; no finite value is
assigned there. The weak integral is nevertheless finite as discussed below.
At b0=0 the Cartesian energy is smooth and (2)=6*kb everywhere.

## 3. Cartesian bending Laplacians, including the mixed term

For adjacent bonds q=l*u and p=m*v, write c=u·v. For l,m>0,

    partial u_a / partial q_b = (delta_ab-u_a*u_b)/l,
    partial v_a / partial p_b = (delta_ab-v_a*v_b)/m,
    grad_q c=(v-c*u)/l,
    Delta_q c=-2*c/l²,       Delta_p c=-2*c/m².          (3)

The last two follow either by differentiating the displayed gradient or from
the degree-one spherical harmonic u·v on the unit sphere. Independently, the
full mixed Cartesian Hessian is

    partial_q_a partial_p_b c
      = [delta_ab-u_a*u_b-v_a*v_b+c*u_a*v_b]/(l*m).

Taking its trace gives

    grad_q·grad_p c
      = tr[(I-u*u^T)(I-v*v^T)]/(l*m)
      = (3-1-1+c²)/(l*m)=(1+c²)/(l*m).                 (4)

Consequently W=kappa*(1-c) has

    Delta_q W=2*kappa*c/l²,
    Delta_p W=2*kappa*c/m²,
    grad_q·grad_p W=-kappa*(1+c²)/(l*m).

Its three bead Laplacians are respectively

    left:   Delta_q W,
    middle: Delta_q W+Delta_p W-2*grad_q·grad_p W,
    right:  Delta_p W.

Adding them, without discarding the shared-middle-bead term, yields

    Delta_R W=4*kappa*c*(1/l²+1/m²)
              +2*kappa*(1+c²)/(l*m).                  (5)

There are no mixed second derivatives with nonadjacent bonds for a single
angle, nor derivatives joining separate additive energy terms. This does not
say that force-square cross terms vanish: equilibrium integration by parts
accounts for all of them through the full Boltzmann weight.

## 4. Equilibrium integration by parts and its domain

Factor out the chain translation and use Cartesian bond measure dq with density
rho=Z_bb^(-1)*exp(-U_bb/T). The bead-to-(translation,bonds) transformation has
unit Jacobian. For the constant metric G from (1),

    div_q[rho*G*grad_q U_bb]
      =rho*[Delta_R U_bb
             -beta*(grad_q U_bb)^T G*(grad_q U_bb)].

The quadratic form is exactly sum_(j=0)^N |grad_rj U_bb|², including end beads.
Vanishing boundary flux therefore gives

    sum_j <|F_bb,j|²>_bb = T*<Delta_R U_bb>_bb.          (6)

This is the square of each bead's **total** backbone force before summing;
it is neither the square of the net chain force (which is zero) nor the sum of
squares of separately isolated stretch/angle contributions.

To justify (6), first excise balls l_i<epsilon and truncate large bond lengths.
For finite parameters, angular energies are bounded. Near a collapsed bond,
grad U has at worst O(1/l) terms; the area of its three-dimensional excision
sphere is O(epsilon²), so its integrated flux vanishes at least as O(epsilon),
with other inverse-length terms integrable over their own bond variables.
The radial stretching singularity is weaker. Simultaneous small lengths can
be handled by successive excisions and domination by sums of 1/l_i² and
1/(l_i*l_j). Gaussian radial tails remove outer boundary terms. In particular,

    p(l)=O(l²) near zero,
    <l^(-1)> and <l^(-2)> are finite,
    <l^(-p)> diverges at zero for p>=3.

All terms in (2),(5), and the total force square are absolutely integrable.
Weak first/second derivatives carry no additional delta mass at collapsed bonds:
the small-sphere flux vanishes despite the angle's direction-dependent limit.
These statements require finite N, positive temperature/stiffness, the open-chain
canonical measure and the translation convention above. They do not prove
well-posedness/mixing of a singular SDE or finiteness of higher force derivatives.
Zero temperature, rigid fixed-length constraints, and pinning a bead as a change
to the dynamics are different limits, not assumed in (6).

## 5. Exact equilibrium averaging, independent of a proposed final formula

The Cartesian Jacobian factors as product l_i² dl_i dOmega_i. Bond lengths are
independent with

    p(l)=l² exp[-a*(l-b0)²]/I2,  a=kb/(2*T),
    In=int_0^infinity l^n exp[-a*(l-b0)²] dl,
    A=<1/l>=I1/I2,       B=<1/l²>=I0/I2.                (7)

The open-chain angular Markov law has a uniform first direction and conditional
adjacent-cosine density proportional to exp(x*c) on [-1,1], x=kappa/T. It is
independent of all lengths. Integrating the remaining open chain gives a
normalizing constant independent of the current orientation, so every adjacent
pair has these same cosine moments. Independence of successive cosines is not
needed for (5). Set

    C=<c>=coth(x)-1/x,
    D=<c²>=1-2*C/x,       x>0,
    C(0)=0,              D(0)=1/3.                      (8)

The second formula follows from integrating
d[(1-c²)*exp(x*c)]/dc over [-1,1], whose boundary values are zero.
Length factorization now gives <c/l²>=C*B and
<(1+c²)/(l*m)>=(1+D)*A². Summing N copies of (2), N-1 copies of (5), and using
(6), the **uniform bead-site mean** is

    K_bb := <|F_bb|²>_site
      = T/(N+1) * {2*N*kb*(3-2*b0*A)
          +(N-1)*[8*kappa*C*B+2*kappa*(1+D)*A²]}.       (9)

Thus the independently derived result **agrees with the proposed formula**.
No missing angle, endpoint, or mixed-derivative factor was identified. Although
individual pointwise Laplacian contributions can be negative, (6) makes the
averaged full expression nonnegative. Identical independent chains have the
same site mean; neither chain count nor canonical spring density multiplies it.

Useful independent radial identities follow directly from half-line integration:

    I0=sqrt(pi)/(2*sqrt(a))*erfc(-sqrt(a)*b0),
    I1=b0*I0+exp(-a*b0²)/(2*a),
    I2=b0*I1+I0/(2*a),
    kb*<(l-b0)²>=T*(3-2*b0*A).                         (10)

The finite-lower-boundary term in I1 must be retained. These are analytic
identities, not numerical evaluations performed in this milestone.

## 6. Limiting cases and physical dimensions

- kappa=0: the angle contribution vanishes exactly; no cancellation or division
  by x is needed. Independent isotropic stretch bonds also give
  K_bb=2*N*kb²*<(l-b0)²>/(N+1), agreeing with (9),(10).
- N=1: no angles; both bead forces are present. N=0 is outside this derivation.
- b0=0,kappa=0: A=2*sqrt(a/pi), B=2*a, and
  K_bb=6*N*kb*T/(N+1), the Gaussian-bond result. This is a limiting algebra
  check, not a Gaussian substitution for the D1.6B backbone.
- x->0: C=x/3-x³/45+2*x⁵/945+..., and
  D=1/3+2*x²/45-4*x⁴/945+...; the angle contribution tends to zero continuously.
- x->infinity at fixed T: C->1, D->1. For finite large kappa, the angle term
  grows approximately as kappa*[8*B+4*A²] per angle. This is not the force law
  of an exactly constrained rod.

With length L, energy E and time t: kb has E/L², kappa and T have E,
A has 1/L and B has 1/L². Every term in braces in (9) has E/L² and K_bb has
E²/L², the units of force squared. Mobility mu=1/zeta has L²/(E*t), so
mu²*K_bb has L²/t² and h²*mu²*K_bb is a mean-square length.

## 7. Connection to D1.6D and the zero virtual-stiffness caveat

Let a_ss²>0 and k_ss=3*T/a_ss², as required by normalized annealed Gaussian
anchors. In that joint law e is conditionally independent of the backbone
force at its uniformly occupied site and <e>=0, <e²>=a_ss². Hence

    <|F_total|²>_occupied = K_bb+k_ss²*a_ss²,
    K_EM=mu²*(K_bb+k_ss²*a_ss²).                        (11)

For the bead-only EM substep with each current attachment/anchor fixed,

    (E_h-I)e²=h*(2*mu*e·F_total+6*mu*T)
                  +h²*mu²*|F_total|²,
    <(E_h-I)mean_live(e²)>_pi=h²*K_EM.                 (12)

Equation (12) is an exact quadratic Gaussian identity, subject to finite second
force moments, in ideal arithmetic. Including the live-site hopping/renewal
batch restores the distinction: D1.6D obtains h²*K_EM+o(h²), conditional on its
weak-domain/remainder assumptions. Evaluating (9) does not prove those assumptions
or evaluate the remainder. For D1.6B, mu=T=1 and a_ss²=5, so
k_ss=3/5 and its force-square addition is 9/5. The previously supplied decimal
coefficients are external comparison values only; no decimals were calculated.

An explicit closed specialization, requiring no unresolved equilibrium averages,
is obtained by defining

    H=sqrt(pi)/(2*sqrt(15))*erfc(-sqrt(15)), E=exp(-15),
    V=(31*H+E)/30,
    A=(H+E/30)/V, B=H/V,
    C10=coth(10)-1/10, D10=1-C10/5.

Then the two total coefficients at these parameters are exactly

    K_EM,0 = (1920/33)*(3-2*A)+9/5,
    K_EM,10 = K_EM,0+(31/33)*[80*C10*B+20*(1+D10)*A²].

These are analytic expressions, not evaluated decimal outputs. The standalone
code uses the general integral formulas as its independent calculation path.

Zero *virtual* spring stiffness needs care. Algebraically removing the virtual
force sets the k_ss²*a_ss² term in (11) to zero and leaves the backbone term.
The consistent normalized family k_ss->0+ at fixed T has
a_ss²=3*T/k_ss->infinity and k_ss²*a_ss²=3*T*k_ss->0. At k_ss=0 itself there is
no normalizable annealed anchor law over all space and no finite equilibrium
connector second moment. Holding a_ss²=5 while setting k_ss=0 is not the E1
target; the O(h) equilibrium cancellation in (12) cannot be asserted for an
arbitrarily chosen finite anchor law then. If Z=0, a mean over live springs is
undefined, although K_bb remains well defined. Proposed zero-stiffness tests
check algebraic force removal and the one-sided limit, not an impossible
zero-k canonical connector ensemble.
No uniformity of the h expansion as k_ss->0+ is claimed.

The exact equilibrium expectation K_bb, the coefficient K_EM, the full-step
uncomputed remainder, finite-time transient changes, and long-time invariant
response are distinct. In particular the positive coefficient explains neither
the sign nor magnitude of the negative D1.6C late-minus-early contrast. See the
[decision](E1_STAGE_D16E_SCIENTIFIC_DECISION.md) and
[unexecuted verification plan](E1_STAGE_D16E_NUMERICAL_VERIFICATION.md).
