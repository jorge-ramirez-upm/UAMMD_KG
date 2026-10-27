# D1.6F — Gaussian projections and solvable reduced models

Preparation only. All formulas are analytical, and all proposed regression tests
are unexecuted. No matrices, covariances, symbolic expressions or trajectories
were evaluated by software. Notation: T=kBT, mu=1/zeta, D=mu*T, k=k_ss,
v=T/k; the centered connector mean is F=Z^(-1)sum_alpha e_alpha²-3*v.

## 1. Exact Gaussian fiber identities for E1

Define Pi w=E_pi[w|R,S], integrating the independent e_alpha=r_salpha-a_alpha
with N(0,v*I3) density. Pi is an orthogonal conditional-expectation projection
in L²(pi). Then Pi F=0, Var_pi(F)=6*v²/Z, and for each component,

    Pi[e_alpha,j*w]=v*Pi[partial_(e_alpha,j) w],
    Pi[(e_alpha,j*e_alpha,k-v*delta_jk)*w]
       =v²*Pi[partial_(e_alpha,j) partial_(e_alpha,k) w]. (1)

These are Gaussian integration-by-parts identities under suitable fiber
regularity/integrability, not independence assertions about time evolution.
Summing the diagonal identities gives

    <F,w>_pi=(v²/Z)*E_pi[sum_alpha Delta_ealpha w].      (2)

Consequently a_f=<s,H^(-1)F> can be written, by reversibility, as
(v²/Z)*E[sum_alpha Delta_ealpha(H^(-1)s)] if that Poisson solution and its
fiber derivatives exist. This is an exact conditional representation under
stronger domain assumptions; it neither closes the equation nor gives a sign
without convexity of the relevant Poisson solution. Such convexity is unproved.

In (R,e) coordinates, bead derivatives in B at fixed laboratory anchors become

    grad_ri|A = grad_ri|e+sum_(alpha:salpha=i) grad_ealpha.

Thus static factorization pi_bb(R)*uniform(S)*product g_v(e) does not imply
that the dynamical generator separates into independent R and e operators.
In particular,

    B F=-2*mu*k*F+(2*mu/Z)*sum_alpha e_alpha·F_bb,salpha. (3)

The extra term has zero Gaussian fiber mean but is a nonzero fluctuating mode
depending on nonlinear backbone forces and attachment sites.

For J the exact live observable has interior contribution per allowed x->y

    (nu/2)*m(e,d)*[|e+d|²-|e|²],
    d=r_y-r_x, m(e,d)=min(1,exp[-(|e+d|²-|e|²)/(2*v)]),

and terminal renewal contribution per vacant terminal y

    nu/(4*M)*[3*v-|e|²].                               (4)

All destination checks use pre-event occupancy, and null attempts remain null.
Contour order introduces no anchor-dependent admissibility weight for a valid
neighbor hop. Rates and geometry in (4) prevent replacing J by one constant
connector damping rate in E1.

There is a useful exact instantaneous identity stronger than pi(JF)=0:

    Pi(BF)=0,     Pi(JF)=0,     Pi(LF)=0.               (5)

For a hop, g_v(e)*m(e,d)=min(g_v(e),g_v(e+d)). Reflection e->-d-e swaps the
two Gaussian factors and changes the sign of |e+d|²-|e|², making its integral
zero. For renewal the Gaussian integral of 3*v-|e|² is zero and availability
depends on S, not e. Other springs' Gaussian factors integrate to one.
Equation (3) similarly proves the Brownian part of (5).

Gaussian averaging also gives the instantaneous accepted-hop factor

    Pi[m(e,d)]=int min(g_v(e),g_v(e+d))de
              =2*Phi(-|d|/(2*sqrt(v))),                (6)

where Phi is the standard normal CDF; at d=0 this is one. It follows by dividing
the Gaussian overlap into the two separating half-spaces along d. This is an
analytic identity, not a quadrature calculation. These averaged rates can define
Pi J Pi on functions of R,S. They do not make the actual projected trajectory
a Markov process: conditional anchors after past dynamics are not necessarily
fresh Gaussian fibers at each time.

## 2. Why the Poisson projection does not close

Set Q=I-Pi, u=H^(-1)F and decompose u=p+q with p=Pi u, q=Q u. Formally,

    Pi H Pi*p+Pi H Q*q=0,
    Q H Pi*p+Q H Q*q=F.

If Pi H Pi has an appropriate centered inverse (or specified sector inverse),

    [Q H Q-Q H Pi*(Pi H Pi)^(-1)*Pi H Q]q=F,
    p=-(Pi H Pi)^(-1)*Pi H Q*q.                        (7)

This Schur-complement identity exposes the unresolved coupling rather than
eliminating it. Nullspaces and domains must be controlled before using the
inverse. The source pairing still contains both <Pi s,p> and <Q s,q>.

The particular fact Pi H F=0 in (5) does not imply Pi H q=0 for the unknown
Poisson solution q, nor Pi H^n F=0 for every n. Equation (3) generates
e·F_bb modes. Acting again introduces force derivatives, backbone geometry,
other occupied sites and higher connector powers. Metropolis's piecewise
exponential acceptance generates nonpolynomial functions, hence an unbounded
Gaussian-Hermite hierarchy in general. Renewal coefficients depend on the
terminal/vacancy process, which itself couples back to conformations and anchors.

Separating backbone, connector, occupancy and contour/renewal modes is therefore
an exact orthogonal bookkeeping scheme but not a proved finite closed dynamics.
No finite projection closure or sign inequality has been derived for full E1.
An adiabatic replacement of anchors or attachment rates by (6), or a Gaussian
backbone substitution, would be an approximation and a changed model.

## 3. Toy 1: one harmonic coordinate, fixed anchor

Take U(x)=k*x²/2, fixed anchor at zero, no backbone or jumps. Let lambda=mu*k.
EM gives x_next=(1-lambda*h)*x+sqrt(2*D*h)*xi, ideal xi~N(0,1).
For 0<lambda*h<2 its exact invariant variance is

    V_h=v/(1-lambda*h/2),
    V_h-v=h*(mu*T/2)+O(h²).

The exact initial-equilibrium one-step defect is lambda²*h²*v. Since
H(x²-v)=2*lambda*(x²-v), the Poisson response yields
lambda²*v/(2*lambda)=mu*T/2, with the same positive sign. In d independent
Cartesian directions multiply the defect and bias by d. This is a valid
sign result for this toy, with a known relaxation rate, not an E1 rate estimate.

## 4. Toy 2: harmonic backbone, fixed attached bead and anchor

Let x,y be two Brownian bead coordinates, both mobility mu, with

    U(x,y)=gamma*(x-y)²/2+k*x²/2, gamma,k>0,
    K=[[gamma+k,-gamma],[-gamma,gamma]].

The anchor on bead x is fixed at zero. K is positive definite, and the exact
Boltzmann covariance is Sigma0=T*K^(-1); in particular E[x²]=T/k. There is
no renewal, contour hopping or occupancy change, and this backbone is zero-
rest-length harmonic, not the nonlinear semiflexible backbone.

With A_h=I-mu*h*K, the discrete Lyapunov equation gives, for
0<mu*h*lambda_max(K)<2,

    Sigma_h=A_h*Sigma_h*A_h^T+2*mu*T*h*I,
    Sigma_h=T*K^(-1)*(I-mu*h*K/2)^(-1),
    Sigma_h-Sigma0=(mu*T*h/2)*(I-mu*h*K/2)^(-1)
                  =(mu*T*h/2)*I+O(h²).                 (8)

One verifies (8) by diagonalizing the real symmetric K and using Toy 1 per
normal mode, or by direct substitution in the Lyapunov equation. The difference
is positive definite. The attached connector x² has leading stationary bias
mu*T*h/2, independent of gamma, whereas its one-step coefficient is
mu²*T*(gamma+k), which increases with gamma.

More explicitly, with a=mu*h/2,

    E_h,stationary[x²]-T/k
      =(mu*T*h/2)*(1-a*gamma)
         /[1-a*(2*gamma+k)+a²*gamma*k].                (9)

The first-order response check is also exact at matrix level: the initial
covariance source is Q0=mu²*T*K, and the first-order stationary covariance
S1 solves mu*(K*S1+S1*K)=Q0. The solution S1=mu*T*I/2 agrees with (8).
Thus a larger one-step force-square coefficient need not imply a larger
first-order stationary connector coefficient even in a fully solvable system.

## 5. Toy 3: harmonic connector with independent Gaussian refresh

Add to Toy 1 a constant-rate rho>=0 heat-bath refresh of the anchor relative
to the current bead, so x=e is replaced by N(0,v). Between refreshes x follows
the harmonic OU diffusion. Both generators are reversible for the same Gaussian
law, and F=x²-v is an eigenfunction with decay rate 2*lambda+rho.

This is explicitly a toy: refreshing the same occupied site is not an allowed
E1 source-end proposal. E1 transfers only outward to a pre-event vacant end;
its terminal/vacancy-dependent rates, moving backbone, exclusion and Metropolis
hops are all absent here. The imposed rho is not identified with nu_hop.

For BD then the exact refresh batch, let q=exp(-rho*h). With probability q
there is no refresh; otherwise the final x is a fresh Gaussian. The stationary
variance solves

    V_h=q*[(1-lambda*h)²*V_h+2*D*h]+(1-q)*v,
    V_h-v=q*lambda²*h²*v/[1-q*(1-lambda*h)²].           (10)

A finite variance requires q*(1-lambda*h)²<1; the Toy 1 stability interval is
sufficient. The bias is positive and

    V_h-v=h*lambda²*v/(2*lambda+rho)+O(h²).            (11)

Its initial-equilibrium one-step defect is q*lambda²*h²*v, hence its leading
coefficient remains lambda²*v, independent of rho. The response formula gives
the same coefficient in (11) by dividing by the known eigenfunction decay
rate. Increasing rho suppresses this toy's stationary response while preserving
its leading local source. The d-dimensional connector mean has d times (10),(11).
No such monotonicity has been proved for general E1.

## 6. Restricted covariance positivity and why E1 is outside the proof

For a fixed quadratic potential U(z)=z^T K z/2, positive K and constant
symmetric mobility M, a bead EM step started at Sigma0=T*K^(-1) produces the
exact covariance defect h²*T*M*K*M, a positive semidefinite matrix. If subsequent
jumps are affine Gaussian maps chosen with state-independent probabilities,
with a common invariant Gaussian law, their covariance propagation maps
positive semidefinite defects to positive semidefinite defects.

If the combined second-moment recursion is stable, the stationary covariance
defect is the sum of propagated nonnegative source matrices. Every linear
connector's square then has nonnegative bias. Toy 3 is an instance of this
restricted mechanism. This argument requires a common finite Gaussian state
representation, affine maps, state-independent map-selection probabilities,
and a stable linear covariance recursion.

The actual E1 Metropolis accept/reject probability depends on positions and
anchors; the backbone force is nonlinear and singular near collapsed bonds;
the live connector changes its attachment/anchor; occupancy and order constrain
which maps are available. These conditions do not fit that positivity theorem.
Uniform attempt selection does not make accepted-map probabilities state
independent. The theorem supplies neither sign nor a finite covariance closure
for the actual simulator. Conversely, the finite-state counterexample in the
[sign analysis](E1_STAGE_D16F_SIGN_ANALYSIS.md) lacks these Gaussian-EM hypotheses.
Keeping these classes separate avoids either unjustified extrapolation.
