# E1 D1.6 v1 — reference moments and independent local computation plan

**DESIGN ONLY. No reference draws or numerical reference calculation ran.**
This is a derivation and a proposed bounded local procedure, not an executed
sampler, approved reference ensemble or change to the accepted initializer.
See [scientific design](E1_STAGE_D16_SCIENTIFIC_DESIGN_V1.md) and
[resource plan](E1_STAGE_D16_RESOURCE_PLAN_V1.md) for scope and approval gates.

## 1. Actual target and radial moments

Use N bonds, m=N+1 beads, M chains. The accepted energy is

    U_bb = sum_i kb/2 (ell_i-b0)^2 + sum_i kappa (1-u_i.u_(i+1)),
    b0=1, kb=30, kBT=1, N=32.

E1 integrates the anchors and uniform occupied-site sets out of the backbone
marginal. Thus reference backbone statistics are independent of M, Z, dt and
nu_hop. References can be shared across cells without sharing trajectory RNGs.
Lengths are independent of orientations and of each other; for kappa>0 the
orientations along a chain are correlated. Translation is irrelevant to these
internal observables; the CPU reference anchors bead 0 at zero.

Put a=kb/(2kBT)=15, b=b0, and

    I_j = integral_0^infinity r^j exp[-a(r-b)^2] dr,
    mu_p = E[ell^p] = I_(p+2)/I_2.

The r^2 Jacobian is essential. In particular mu4=I6/I2, not the fourth
moment of an unweighted normal radius, nor (5/3)*mu2^2.
An independent half-line integration-by-parts reference is

    I0 = sqrt(pi)/(2 sqrt(a)) * erfc(-sqrt(a)*b),
    I1 = b I0 + exp(-a b^2)/(2a),
    I_j = b I_(j-1) + (j-1)/(2a) I_(j-2),  j>=2.

The boundary contribution in I1 must be retained. This recurrence is positive
at these parameters and includes the finite lower boundary exactly; replacing
the half-line integral by a whole-line Gaussian is not the prescribed law.
I2,I3,I4,I6 give normalization, mu1,mu2,mu4. I10 supplies mu8 if needed for
uncertainty diagnostics. No numerical values of these integrals are asserted here.

Local verification must compare this recurrence with independent radial
quadrature at orders 128,256,512, with an explicit tail estimate. The accepted
`semiflexible_reference.radial_moments` computes only mu1,mu2 and truncates the
scaled Gaussian integration at 12 thermal lengths; it must remain unchanged.
Extend the *separate reference calculation*, not that accepted function, to
higher moments. Proposed numerical error budget: relative error <=1e-10 for
positive moments/size means, with cancellation errors bounded separately for
variances/covariances. Refinement agreement alone is not a proof of a tail bound.
Retain the existing <1e-11 absolute 128/256 refinement check for mu1,mu2;
the additional numerical error budget does not replace or relax that check.

## 2. Flexible chains: fourth moments without a Gaussian-chain substitution

For kappa=0, q_i=ell_i u_i are independent isotropic vectors. Their tensors are

    E[q_ia q_ib] = (mu2/3) delta_ab,
    E[q_ia q_ib q_ic q_id]
      = (mu4/15)(delta_ab delta_cd + delta_ac delta_bd + delta_ad delta_bc).

Define X=Re^2=|sum_i q_i|^2, Y=Rg^2 and, with i,j=1,...,N,

    A_ij = min(i,j)*(m-max(i,j))/m^2,
    Y = sum_ij A_ij q_i.q_j.

For symmetric deterministic matrices B,C define Q_B=sum_ij B_ij q_i.q_j.
Expanding products and cancelling disconnected terms gives

    E[Q_B] = mu2 tr(B),
    Cov(Q_B,Q_C)
      = (mu4-mu2^2) sum_i B_ii C_ii
        + (4 mu2^2/3) sum_(i<j) B_ij C_ij
      = (2 mu2^2/3) tr(BC)
        + (mu4-5 mu2^2/3) sum_i B_ii C_ii.

To see the coefficient 4/3, the off-diagonal contribution is
2 sum_(i<j) B_ij q_i.q_j; E[(q_i.q_j)^2]=mu2^2/3.
Distinct unordered pairs have zero covariance, even if they share one bond,
because the unpaired isotropic vector has zero mean. Diagonal/off-diagonal
covariances vanish for the same reason. This proves the result using the
actual radial second/fourth moments, with no Wick assumption for a single bond.

Take B=J (all ones) for X and B=A for Y. Define

    t = tr(A) = (m^2-1)/(6m),
    d = sum_i A_ii^2 = (m^4-1)/(30m^3),
    h = tr(A^2) = (m^2-1)*(2m^2+7)/(180m^2),
    s = sum_ij A_ij = (m^2-1)/12.

Then the requested reference formulas are

    E[X] = N mu2,
    E[Y] = t mu2,
    Var(X) = N*(mu4-mu2^2) + (2/3)*N*(N-1)*mu2^2,
    Var(Y) = (2/3)*mu2^2*h + (mu4-5*mu2^2/3)*d,
    Cov(X,Y) = t*(mu4-mu2^2) + (2/3)*mu2^2*(s-t)
             = t*[mu4+(N-4)*mu2^2/3],
    E[X^2] = N*mu4 + (5/3)*N*(N-1)*mu2^2,
    E[Y^2] = Var(Y) + (t*mu2)^2,
    E[XY] = Cov(X,Y) + N*t*mu2^2.

Here E[X^2]=E[Re^4] and E[Y^2]=E[Rg^4]. Fourth moments *of X or Y*
are eighth-order length quantities and enter precision estimates for variances;
do not confuse these two uses of “fourth moment”.

Hand consistency checks for the later independent implementation:

- N=1 implies Y=X/4, Var(Y)=Var(X)/16, Cov(X,Y)=Var(X)/4.
- Fixed lengths imply mu4=mu2^2 and
  E[Re^4]=(5N^2-2N)*mu2^2/3.
- Artificial Gaussian-vector moments mu4=5mu2^2/3 remove the single-bond
  cumulant term. This is an algebra check only, not the E1 physical reference.
- Direct finite sums for t,d,h,s must agree with the closed forms. Preserve
  nonnegative variance and a positive-semidefinite 2x2 covariance matrix.

## 3. Stiff chains: exact means and independent variance estimates

For x=kappa/kBT=10, the accepted orientation transition is proportional to
exp(x u_i.u_(i+1)), with a uniform first direction. Let

    c = coth(x)-1/x,
    B(k) = k mu2 + 2 mu1^2 sum_(s=1)^(k-1) (k-s)c^s.

For either stiffness (c=0 for kappa=0), exact means are

    E[X]=B(N),
    E[Y]=sum_(k=1)^N (m-k) B(k)/m^2,
    E[u_i.u_(i+s)]=c^s.

These means are quadrature/analytic targets, preferable to unnecessarily noisy
Monte Carlo means. The kappa=0 covariance formulas above **do not** extend by
replacing N with an effective Gaussian length at kappa=10.

Use unchanged `semiflexible_reference.Chain.homogeneous(32,1,30,kappa)` and
`Chain.sample(count,rng,kbt=1)` for independent equilibrium configurations.
It independently samples radial lengths by rejection, then the exact Markov
orientation sequence. It uses neither time integration nor CUDA production RNG.
Its maximum radial retry count remains an error path, never a reason to drop a
chain and continue. Archive the accepted sampler source hash and NumPy version.
Agreement with mu1,mu2, size means and c^s audits its implementation; sharing the
target derivation with the GPU initializer is not an independent proof by itself.

An optional independent fourth-order angular transfer calculation can validate
stiff variances: expand ordered tangent products using the isotropic transition
operator, with eigenvalues E[P_l(cos theta)]; l=1 gives c and l=2 gives
1-3c/x. Four tangent factors require intermediate angular orders up to 2.
Combine repeated radial indices with mu1..mu4 and contract with J or A twice.
This is a proposed cross-check, not an implemented/evaluated reference here.

## 4. Bounded local reference procedure proposed for review

No sampler/launcher is introduced in D1.6. The following specifies a reproducible
local implementation contract for separate approval; it is not a command to run
a missing utility. No dynamic trajectory or reference draw is authorized by
committing this plan.

| Item | Fixed proposal |
|---|---|
| Physical cases | N32, b0=1,kb30,kBT1, kappa0 and10 only |
| Precision / generator | float64; explicit NumPy PCG64 generator |
| Seed construction | SeedSequence([721610000,kappa,phase,batch_index]); record generated identities |
| Phase identifiers | 1 quantile calibration, 2 sizing pilot, 3 final reference |
| Batch size | 512 independent chains; a fresh child seed for every batch |
| Calibration | 65536 draws/kappa, excluded from moment/reference evaluation |
| Sizing pilot | 8192 draws/kappa, excluded from final reference estimates |
| Final sample sizes | one of 16384,32768,65536,131072,262144,524288 per kappa |
| Proposed caps, NOT approved | 30 s/batch, 1200 s total/kappa, 1 GiB RSS, 16 MiB output/kappa |
| Maximum draws | 598016/kappa across all phases; 1196032 over both kappas |

Seed namespaces are distinct from D1.5 simulation/reference proposals. Before
implementation approval, audit the full seed ledger for collisions; no claim
of mathematical independence of arbitrary pseudorandom streams is implied.
Do not share sample arrays, random states or selection decisions with trajectory
data, and never use trajectory outcomes to refine this reference.

Algorithm:

1. Verify the sampler/code/parameter identities and analytic/quadrature checks.
   Create a fresh external evidence directory; refuse overwrite/resume.
2. Phase 1 generates only X,Y and freezes thresholds at probabilities
   .01,.05,.10,.25,.50,.75,.90,.95,.99, separately for X and Y. Store the two
   sorted scalar arrays (about 1 MiB/kappa), thresholds and rank/binomial
   uncertainty. Do not retain chain coordinates or introduce GPU work.
3. Phase 2 computes the per-chain vector
   W=(X,Y,X^2,Y^2,XY, eighteen CDF indicators), along with finite/high-moment
   diagnostics. Retain batch sums and covariance, using stable central-moment
   merging rather than subtracting large nearly equal raw sums blindly.
4. Use pilot uncertainty to choose the **one fixed final size**, never to choose
   tolerances. Allocate nominal family alpha=.05 over 50 reference quantities
   (per kappa: two means, two variances, covariance, two raw fourth-length
   moments, eighteen CDF values). Use the conservative t critical for at least
   32 final batches; multiply pilot SE predictions by a predeclared factor 2.
   Predicted half-width at S is c_ref*2*SE_pilot*sqrt(8192/S), after the
   appropriate delta-method transform. Select the smallest listed S predicted
   to meet every applicable precision target below. If none fits, stop with
   REFERENCE PRECISION UNRESOLVED; do not silently draw past the cap.
5. Phase 3 uses new independent batches and the selected fixed size. Estimate
   Var(X),Var(Y),Cov(X,Y) with the finite-S unbiased factors, and E[X^2],E[Y^2].
   Compute covariance of mean W across independent batches. Delta-method
   gradients on the first five W components are (-2 E[X],0,1,0,0) and
   (0,-2 E[Y],0,1,0), with zeros on all CDF components;
   covariance has gradient (-E[Y],-E[X],0,0,1). Include the finite-S factor.
   Use whole-batch jackknife as a robustness check and record discrepancies.
   Batch-t/delta intervals are nominal CLT approximations, not exact tail bounds.
6. At frozen thresholds, use the independent evaluation sample to estimate
   F_ref(q_hat) with Bonferroni-adjusted binomial intervals. The target is that
   evaluated probability, **not automatically the nominal calibration quantile**.
   This accounts for threshold error without reusing the calibration sample.
7. Perform exactly one final precision assessment. Analytic size means remain
   the primary targets; Monte Carlo means are independent consistency checks.
   Require the analytic means and the kappa0 analytic variances/covariance/raw
   fourth-length moments to lie within their nominal simultaneous reference
   intervals; otherwise flag consistency unresolved and stop for review.
   If numerical consistency, sample completeness or precision fails, stop and
   report it. No optional repeated successful-looking confidence intervals.

Proposed final precision targets (reference quality, not changes to D0):

- Relative simultaneous interval half-width <=5% for each variance and each
  raw fourth-length moment. Use analytic kappa0 values as the primary references.
- Covariance half-width <=.05*sqrt(Var(X)*Var(Y)); do not divide by a possibly
  small covariance to decide precision.
- Each evaluated reference CDF half-width <=.005 (one quarter of D0's .02).
- Deterministic mean/numerical reference error within the budget in section 1.
  If a future mean target cannot be analytic, its simultaneous half-width must
  be <=.0025 times that target, rather than spending the simulation's margin.

A failed final assessment is unresolved, even if the pilot predicted success.
Any refinement uses a new reviewed version/seed allocation. Separating pilot
and final samples avoids adaptive-size selection on the final moment estimates.
Inspect high-moment/batch stability before relying on nominal CLT intervals;
precision formulas alone do not validate skew-tail approximations.
The nominal .05 reference-quality family is not an automatic confirmatory
error bound. A future confirmation must recompute interval coverage under its
allocated reference alpha and reassess precision, or propagate independent
reference covariance in a jointly calibrated simultaneous procedure.

Return artifacts: configuration/seed ledger, code and dependency hashes,
analytic moments, all batch sufficient statistics, covariance matrices, quantile
calibration/evaluation identities, actual counts, numerical and statistical
uncertainties, resource/stop status, human summary and SHA256 inventory. Preserve
full reference evidence locally; a compact upload can omit the sorted scalar
arrays if it includes their paths/sizes/hashes. Independent references are not
additional scientific replicas of the dynamics.

## 5. Useful exact-E1 joint-score variance checks

Let f=X/E[X]-1 and v_f=Var(X)/E[X]^2. With the existing A_joint/B_joint
definitions, exact E1 factorization yields, at a **single independent E1 frame**,

    E[A_joint]=E[B_joint]=0,
    Var(A_joint)=v_f/M,
    Var(B_joint)=2*v_f/(3Z),
    Cov(A_joint,B_joint)=0.

For A, cross-chain terms vanish because independent backbone f's have mean
zero, despite hypergeometric population coupling. For B, conditional connector
square-sum variance on chain c is (2/3)*A2^2*Z_c. This also makes its covariance
with the population score zero. Zero covariance does not establish independence
of the two scores or their time histories. These are null-law reference/power
checks, not permission to impose chain independence on evolved data.
