# D1.6D — theoretical equilibrium audit

Preparation only, 27 October 2026. No tests, builds, simulations, GPU preflights,
reference calculations, numerical sampling or scientific analyses were executed.
Independent review must precede verification or any simulator change. This audit
changes no accepted source, scientific evidence, hashes, manifests or D0 margins.

Starting local and actual remote `slip-springs` HEAD both:
`d6924acbed63d9facc667cd8e72a73e61d597676` (remote queried before work).
Scientific source inspected with `git show` at
`0dea651b58171a72206774bcebb2f4c74960069b`; the eight traced scientific files
are byte-identical at starting HEAD. See [source trace](E1_STAGE_D16D_SOURCE_TRACE.md),
[discrete-time derivation](E1_STAGE_D16D_DISCRETE_TIME_ANALYSIS.md),
[decision](E1_STAGE_D16D_SCIENTIFIC_DECISION.md) and
[implementation/limitations](E1_STAGE_D16D_IMPLEMENTATION_REPORT.md).

## 1. Authorities and evidentiary status

Authorities read: [E1](EQUILIBRIUM_MODEL_E1.md), [A audit](E1_STAGE_A_AUDIT.md),
[B report](E1_STAGE_B_REPORT.md), [C report](E1_STAGE_C_REPORT.md),
[D0](E1_STAGE_D_VALIDATION_PROTOCOL.md),
[D1.6 design](E1_STAGE_D16_SCIENTIFIC_DESIGN_V1.md),
[reference derivation](E1_STAGE_D16_REFERENCE_MOMENTS_V1.md),
[B exploratory protocol](E1_STAGE_D16B_PROTOCOL_V1.md),
[C secondary protocol](E1_STAGE_D16C_PROTOCOL_V1.md), and actual accepted source.
Historical tests in A/B/C are historical evidence, not tests performed here.

Existing D1.6C saved result and interpretation were read at
`/home/jramirez/UAMMD_KG-evidence/d16c/d16c-existing-jw_xnbfc/stage-b/`:
`audit-result.json` and `secondary-audit.json.gz` (only stored records were read,
not reducers or authentication jobs). The detached Stage C return manifest records
secondary payload SHA256
`3437e7983d38d0b70d3f9a3e934b582a6a7322e14c489d1949312db5a4907861`,
size 2,005,504 bytes; original analysis SHA256
`04570c0ccb3b06df0f9be265a2bde602f1c2dcce59c474af963ca8634a17652f`.
These identify the previously authenticated interpretation; this milestone does
not independently rerun its authentication or reproduce its statistics.
The two audit/analysis drafts already present as untracked files at session start
were retained and checked against the source; their presence is not evidence of
previously completed D1.6D verification.

Below, **source** means an inspected rule; **derivation** means ideal real-arithmetic
mathematics with stated assumptions; **existing evidence** means prior supplied or
saved observations; **unresolved** means no conclusion has been established.

## 2. Normalized target, identities and translations

Write T=kBT, beta=1/T, m=N+1, L=Mm, k=k_ss=3T/A2, and 0<=Z<=L.
The Hamiltonian is

    U(R,S,A)=U_bb(R)+(k/2) sum_(x in S) |r_x-a_x|²,
    U_bb=sum_b kb_b/2 (|q_b|-b0_b)²
         +sum_angles kappa_a (1-u_(a-1)·u_a).

Use counting measure on unordered Z-element subsets of the L sites, and Lebesgue
measure for one three-dimensional anchor at each occupied site. Site exclusion
is a hard state-space constraint, not an energy approximation. Let dR_int be
Cartesian bond-coordinate measure with each chain's translation factored out.
Define Z_bb=int exp(-beta U_bb) dR_int, finite for kb>0 and finite N. With

    G=(2*pi*T/k)^(3/2),
    g(a|r)=G^(-1) exp[-k|a-r|²/(2T)],

For completeness, with each chain's bead 0 translation removed, its explicit
bare partition function in Cartesian bond measure is

    Z_bb,c = (4*pi)^N * product_b I_b * product_angles H(kappa_a/T),
    I_b = int_0^infinity l² exp[-kb_b*(l-b0_b)²/(2T)] dl,
    H(x)=exp(-x)*sinh(x)/x,  H(0)=1,
    Z_bb=product_c Z_bb,c.

This follows by integrating the first orientation over 4*pi and each subsequent
orientation conditionally over 4*pi*H(x). The change from beads to bead-0 plus
bonds has unit Jacobian. These are unevaluated exact integrals, not newly
computed reference values.

one has the explicitly normalized density

    pi(R,S,A) = exp(-beta U)/(Z_bb*C(L,Z)*G^Z)
              = pi_bb(R)/C(L,Z) * product_(x in S) g(a_x|r_x).

The canonical constraint fixes Z exactly; there is no fugacity, Poisson population
law or independently occupied-site approximation. The partition function contains
C(L,Z) and the constant anchor integral G^Z. Integrating anchors gives 1 for each
conditional factor, then summing subsets gives pi_bb(R). Thus S is uniform and
independent of R in the annealed marginal, despite energetic site preferences
conditional on fixed anchors.

For named identities alpha=1,...,Z, sites are injective assignments. A symmetric
labelled lift has density pi_bb/[(L)_Z] times product g, where
(L)_Z=Z!*C(L,Z). Equivalently the labelled partition function has an extra Z!;
a 1/Z! reference-measure convention cancels it. Links are uniquely determined by
current contour order and contribute no degeneracy. Do not insert Z_c! factors
per chain or extra weights for contour gaps. Those would change the target.

The actual initializer assigns IDs in increasing global site order. It therefore
samples the unlabelled physical target but not the fully exchangeable labelled
lift at time zero. ID-sensitive observables can have label-history transients;
all-live means and the observer's physical state are invariant to ID permutations.
Renewal retains a storage ID but replaces its anchor and inserts it at the new
contour extreme. An ID is not a permanent contour rank across lifetimes.

There is no normalized equilibrium density over all unbounded laboratory bead
translations. One may divide out translations separately for each chain, shifting
that chain's currently associated anchors with its beads. Bead 0=0 is a gauge for
initialization/integration of the ensemble, not a bead pinned during dynamics.
The projected process includes the corresponding shifts of relative anchors;
one must not fix bead 0 and retain independent lab-frame bead noises unchanged.
Alternatively use the translation-invariant sigma-finite lab measure and take
expectations only of the internal observables considered here. All integrations
by parts below use that convention with decaying internal-coordinate tails.
Conditioned on fixed laboratory anchors, a chain with at least one anchor has
confined translation; an empty chain still has a free translation. Conditional
Boltzmann stationarity for empty chains is correspondingly modulo translation.
No center-of-mass or laboratory-position equilibrium assertion is made.

At fixed R,S the anchors are independent g(a|r_site). Hence e=r_site-a has
independent components N(0,v), v=T/k=A2/3, independent of R,S in these variables:

    E[e²]=3v=A2,
    E[e⁴]=3*(3v²)+2*3*v²=15v²=5*A2²/3.

For A2=5 these are 5 and 125/3. The fourth moment is of the radial squared
length squared, not a single Cartesian fourth moment. For example
P(site occupied)=Z/L and
P(Z_c=z)=C(m,z) C(L-m,Z-z)/C(L,Z).
These are annealed results. At fixed R,A, the distribution over admissible
assignments is proportional to exp[-beta sum_alpha E_alpha(s_alpha)], with
exclusion and any fixed-order sector; it is not uniform or a product of independent
per-spring site probabilities. At fixed S,A, bead conformations follow the full
conditional Hamiltonian, not the bare-backbone marginal.

## 3. Interior hopping: frozen-coordinate detailed balance

**Source:** K is drawn by exponential interarrivals with mean Z*nu*h. Each event
selects one ID uniformly with replacement and a sign with probability 1/2.
For an adjacent vacant site y on the same chain, anchor a unchanged,

    q(x->y)=nu/2,
    d=beta*k/2 * (r_y-r_x)·[(r_y-a)+(r_x-a)],
    w(X,Y)=(nu/2)*min(1,exp(-d)).

The reverse has the same q, change -d and ratio w(X,Y)/w(Y,X)=exp(-d)=pi(Y)/pi(X).
Only one spring energy changes; bead coordinates and backbone energy do not.
Source evaluates d using double intermediates on stored `real` positions and
anchors, the same rounded stiffness as the force, and input T. Its log-uniform
comparison avoids exponent overflow; downhill and zero changes accept.

For nearest-neighbor steps with single occupancy, a vacant destination cannot
pass a valid predecessor or successor: there is no intervening integer site.
The source checks links and aborts an inconsistent ordering rather than silently
rejecting an otherwise valid state. The reverse restores a now-vacant source
with the same neighboring IDs. Occupied targets are null attempts; both exclusion
and preserved contour order define reciprocal allowed edges. Outward boundary
attempts are null in Stage B and renewal proposals when enabled. There is no
redrawing until success or renormalizing over permitted directions/IDs.

The global Poisson construction is uniformization of J=Z*nu*(K_event-I):
exp(hJ)=sum_n exp(-Z*nu*h)(Z*nu*h)^n K_event^n/n!. Self attempts are retained.
Selection without replacement, synchronous sweeps or conditioning counts on
acceptance would be different kernels. Event/mean/retry limits abort, do not
clip or replace counts. Mathematical statements concern the ideal nonaborting
kernel, not a distribution conditioned on absence of an abort.

With renewal off, anchors, chain populations, chain membership and per-chain
ID order are conserved sectors. Detailed balance holds for pi restricted to
such sectors, as well as for a stationary mixture of sectors. This is not an
ergodicity theorem or a claim of a bare backbone marginal conditional on anchors.

## 4. End renewal: complete rate density

A spring at occupied terminal x attempts outward at nu/2. The source selects a
chain among all M and one of its two ends, independently and uniformly. A candidate
end y must be vacant in the pre-event state. For distinct ends x,y,

    w(X,dY)/da_new = nu/(4M) * g(a_new|r_y).

The reverse is the same ID's outward move from y to x, now vacant, with old
anchor proposed from g(a_old|r_x):

    w(Y,dX)/da_old = nu/(4M) * g(a_old|r_x),
    pi(Y)/pi(X) = g(a_new|r_y)/g(a_old|r_x).

Thus pi(X)w(X,dY)=pi(Y)w(Y,dX). The proposal ratio already supplies the full
energy ratio. The Metropolis-Hastings ratio is exactly one for a permitted
proposal; acceptance one is the specified rule. Detailed balance alone could
also permit an additional symmetric slowdown, but no energy correction is
required. An extra ordinary Metropolis energy factor would generally destroy
this equality and is not recommended.

Source-end selection is not uniform among currently occupied ends: it follows
uniform ID/direction attempts, so each occupied end has rate nu/2. Destination
selection is not uniform among vacant ends: all 2M ends are proposed with
occupied proposals rejected. These distinctions prevent hidden state-dependent
normalization factors. The source itself is occupied until the check; a proposal
back to it is rejected, not a refresh of its anchor.

For same-chain opposite-end transfers, y is vacant and x becomes vacant. The
source is necessarily a contour extreme. Unlinking it, finding the destination
extreme while excluding its ID, and inserting there preserves a valid ordered
list. The reverse performs the inverse relinking. This applies to a singleton
and to an extreme with other springs in the middle. No additional ID-rank
restriction remains after renewal. An occupied opposite end rejects without
mutation. The implemented N>=1 gives two distinct ends; a one-bead chain is not
the supported geometry. Full occupancy has no hops or renewals; frozen anchors
are then an explicit nonergodic case. With vacancies and renewal, broader
accessibility is plausible but not proved for all parameters/configurations.

**Conclusion:** ideal hopping and renewal satisfy detailed balance on the valid
frozen-R state space, including link bookkeeping, with the normalized E1 measure
or its appropriate sector restriction. This does not establish bit-exact
finite-precision detailed balance or mixing of the full coupled model.

## 5. Forces and the continuous Brownian generator

For a stretching bond q=r_right-r_left, l=|q|, u=q/l,

    grad_q U_st=kb*(l-b0)*u,
    F_left=+grad_q U_st, F_right=-grad_q U_st.

The source matches this nonlinear finite-rest-length law. Each bead receives
half the bond energy, summing to kb*(l-b0)²/2. At l=0,b0>0 the force is undefined
and the source aborts. For b0=0 it uses the regular limiting force kb*q.

For consecutive bonds qa,qb, unit vectors u,v and c=u·v, put

    A=grad_qa U_bend=-kappa/|qa|*(v-c*u),
    B=grad_qb U_bend=-kappa/|qb|*(u-c*v).

For the three beads the forces are A, B-A, -B. Source matches them, and adds
kappa*|u-v|²/6 to each bead: the total is kappa*(1-c). Inactive angles bypass
normalization; active zero-length bonds abort. Spring force is -k*(r_site-a),
with energy k*e²/2 added once on its occupied bead. There is no extra factor
from sharing spring energy. Stretch overwrites forces, bend adds, spring adds.
No source-level sign, coefficient or energy-counting discrepancy was found.

Let mu=1/zeta, D=T/zeta, b_i=mu F_i. The update uses h/zeta and sqrt(2*T*h/zeta),
independent bead/component normals with stable bead RNG identities and old/new
buffers. Its continuous-time counterpart at fixed S,A is

    dR=b(R,S,A)dt+sqrt(2D)dW,
    Bf=sum_i [b_i·grad_i f+D*Delta_i f],
    B* rho=-sum_i div_i(b_i*rho)+D*sum_i Delta_i rho.

Since F_i=-grad_i U and grad_i rho=-beta rho grad_i U, the probability current
b_i*rho-D*grad_i rho vanishes for rho proportional to exp(-beta U).
With appropriate tails, translation convention and no flux through excluded
singular sets, B* pi=0. Frozen-R detailed balance gives J* pi=0, so
(B*+J*)pi=0. This is formal continuous-time invariance, not discrete-time accuracy
or a theorem about uniqueness, finite-time mixing or singular SDE well-posedness.

## 6. Precision and initialization qualifications

Forces, positions and stored anchors use `real`; bending geometry and force
arithmetic use that precision. Hopping uses wider double arithmetic on those
stored values. The host computes k using a long-double intermediate then rounds
once to `real`; initialization and renewal instead use sigma=sqrt(input A2)/sqrt(3).
Thus the ideal Gaussian variance input A2/3 differs in general from T/k_rounded.
There is a real coefficient-rounding inconsistency relative to a single exact
rounded-coefficient Hamiltonian, even before anchor quantization. It is a precision
qualification, not a demonstrated explanation of D1.6C. Double does not eliminate
it. Anchor-coordinate addition/storage can lose small displacements at large
positions; float/double normal algorithms differ. Mobility and noise are rounded
separately. Finite-bit RNGs are not continuous densities. No quantitative bound or
measured rounding contribution is established here, and no source change follows.

In ideal arithmetic the initializer samples the complete unlabelled joint law:

1. Radial bond density is proportional to l² exp[-kb(l-b0)²/(2T)], including the
   three-dimensional Jacobian. In units t=l/sigma, a=b0/sigma, its rejection
   sampler proposes t=t_mode+normal with t_mode=(a+sqrt(a²+8))/2. The log target/
   envelope ratio is 2[log(t/t_mode)-(t-t_mode)/t_mode], exactly the source test.
2. Initial orientation is uniform; subsequent cosines have density proportional
   to exp[(kappa/T)*cosine] on [-1,1], with uniform azimuth. Its normalization is
   independent of the previous orientation, so a sequential open-chain draw
   samples the whole bare-backbone law. Lengths and orientations separate.
3. An independently domain-seeded shuffle chooses the uniform Z-site subset.
   Conditional independent anchor normals are centered on those actual bead
   positions. Consequently correct marginals are accompanied by the required
   conditional dependence. Links/IDs are then constructed from the same sites.

PRNG domain separation is the intended independence construction, not a theorem
of independent real random variables for a fixed deterministic seed. The angular
formula caps an exponential argument at 350 in its large-x branch, another
finite-precision approximation (at kappa/T=10 that cap is inactive). Radial retry
limits abort; supplied coordinate files bypass the equilibrium draw. The exact
joint-law conclusion applies to the intended random draw/default initializer,
not arbitrary supplied conformations or bit-exact normality. No H2 source defect
in the D1.6B recipe was identified. See the decision for unresolved alternatives.
