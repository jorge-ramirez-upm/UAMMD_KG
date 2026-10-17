# Stage 4A.3a — semiflexible configurational stress theory and CPU validation

17 October 2026 (Europe/Madrid). Derivation and bounded CPU verification complete;
**independent review is required before Stage 4A.3b**, which is not authorized.
No GPU stress, dynamics, multi-tau, stress-relaxation simulation or slip-springs.

## Provenance, scope and API

Fetched `origin/slip-springs`, verified live remote/fetched branch/local HEAD at
`9a22534840f5714d6e177fee26ecfe21adb083cc`, and verified a clean worktree before
editing. All changes are under `examples/slip-springs/`. New files are
`semiflexible_stress_reference.py`, `tests/test_semiflexible_stress.py` and this
report; README, ROADMAP and AGENTS contain the documentation changes. The
accepted Rouse/semiflexible simulators, RNGs, original CPU reference, existing
tests, build rules, acceptance archives and frozen plans are unchanged.

The new NumPy module reuses `semiflexible_reference.Chain` for parameter/indexing
validation, bond-coordinate validation and independent equilibrium samples.
It does not replace existing force or integration infrastructure. The mathematical
stress calculation is separate, permitting comparisons with the existing forces.
All reference calculations and returned arrays use float64.

`virials(chain, positions)` returns a dictionary with `stretch`, `bend`, `total`
(3x3 arrays) and total-tensor `symmetric`, `shears`, `normal_differences` arrays.
**These are unnormalized virials W=V*sigma, with energy units**, not intensive
stress. No volume, density or temperature is silently assigned. The model has
N bond-indexed b0/kb entries and N+1 bead-indexed kappa entries with zero
endpoints, exactly as Stage 4A.1. Finite kb>0,b0>=0,kappa>=0 and finite (N+1,3)
positions are required. Scalar components retain the Rouse observation ordering:

| Output | Ordering |
| --- | --- |
| symmetric | xx, yy, zz, xy, xz, yz |
| shears | xy, xz, yz |
| normal_differences | xx-yy, xx-zz, yy-zz |
| concatenated raw deviatoric channels | xy, xz, yz, xx-yy, xx-zz, yy-zz |

`components(W)` extracts raw entries and differences; it does not average
W_ab with W_ba, subtract the trace or assert that an arbitrary supplied matrix
is physical. Symmetry/trace checks inspect the complete raw physical tensor.
`bending_angle_virial(a,b,kappa)` exposes individual angle contributions.

## Affine derivative, signs and force virial

Let F=I+epsilon, q_i=r_(i+1)-r_i, g_i=partial U/partial q_i and
q'_i=F*q_i. Then delta q_(i,alpha)=epsilon_(alpha,beta)*q_(i,beta), so

    delta U = sum_i g_i dot (epsilon*q_i)
            = W:epsilon,   W=sum_i g_i outer q_i,
    sigma_conf = W/V.

The first tensor index is the energy-gradient/force component and the second
is the displacement component. This is the **positive affine-energy derivative**
convention. A stretched spring gives positive axial W. It differs in sign from
sum(F_bead outer position). For coordinate arrays stored as rows, the correct
test deformation is `r @ (I+h*E).T`, and W:E is an elementwise contraction.

Because F_0=g_0,F_j=g_j-g_(j-1),F_N=-g_(N-1), telescoping gives

    W = -sum_j F_j outer (r_j-r_ref).

The reference point cancels through sum_j F_j=0, so this is translation
independent. Rotational invariance gives zero antisymmetric affine derivative
and a symmetric tensor. Finite rigid rotation Q preserves energy and gives
W(Qr)=Q*W(r)*Q^T. The bead-force test uses the unchanged independent Stage 4A.1
force methods, not gradients recovered from this new tensor implementation.

## Stretching contribution

For l_i=|q_i| and u_i=q_i/l_i,

    g_i^s=kb[i]*(l_i-b0[i])*u_i,
    W_s=sum_i kb[i]*(l_i-b0[i])*(q_i outer q_i)/l_i.

This is symmetric but generally has nonzero trace, including negative values
for compressed individual bonds. At l=0,b0=0 the smooth quadratic limit is
kb*q=0 and its virial is zero. At l=0,b0>0 the relevant Cartesian gradient is
undefined and raises ValueError. The implementation checks length, gradient,
energy and tensor finiteness, mirroring the reference's physical/numerical
restrictions without force cutoffs or a substitute potential.

## Bending contribution: two independent derivations

For internal bead i define a=q_(i-1),b=q_i,u=a/|a|,v=b/|b|,c=u dot v.
The orientation derivative partial u/partial a=(I-u*u^T)/|a| gives

    A=partial U_i/partial a=-kappa[i]*(v-c*u)/|a|,
    B=partial U_i/partial b=-kappa[i]*(u-c*v)/|b|,
    W_b,i=A outer a+B outer b.

This is the primary implementation. It computes no bead forces, acos or angular
regularization. It checks individual active-angle energies/gradients/tensors
for nonfinite results. Active zero-length bonds are rejected.

Independently, write the deformed cosine using the metric M=F^T*F:

    c(F) = (a^T M b)/sqrt[(a^T M a)*(b^T M b)].

At F=I, delta M=epsilon+epsilon^T. Differentiating this scalar quotient yields

    delta c = u^T*(epsilon+epsilon^T)*v
              -(c/2)*[u^T*(epsilon+epsilon^T)*u
                       +v^T*(epsilon+epsilon^T)*v].

Since delta U_i=-kappa[i]*delta c, the independent length-free expression is

    W_b,i=kappa[i]*[c*(u outer u+v outer v)
                    -(u outer v+v outer u)].

This second expression is implemented separately in the tests and never calls
the force routine or the A/B implementation. It proves for **each angle**:

* W_b,i is symmetric: the two mixed dyadics occur as a transpose pair.
* Tr W_b,i=kappa[i]*(2c-2c)=0: bending is homogeneous of degree zero under
  isotropic dilation. It contributes no instantaneous hydrostatic virial.
* Rescaling either forward bond by a positive scalar leaves this tensor
  unchanged. Parallel and antiparallel nonzero bonds have zero bending tensor,
  consistent with stationary angular energy at both extrema.

These are identities of the unmodified tensor, not postprocessing constraints.
Tests check the small floating-point residuals before any channel extraction.
Although the metric form cancels inverse lengths analytically, it is not used
to hide undefined or numerically overflowing gradients in the primary reference.
Tiny active lengths can remain a numerical limitation, as in the force model.

When all kappa entries are exactly zero, `virials` never invokes its bending
routine or angle evaluator. The required zero bend-output array is the only
zero-result allocation; no angular geometry or per-angle scratch is constructed.
Mixed inactive angles are skipped using the reference's existing active list.
An inactive collapsed bond is allowed when its stretch is smooth. Sentinel-call
and collapsed-inactive-angle tests verify absence of angular evaluation.

## Equilibrium identities: hydrostatic is not zero

Use unconfined bond coordinates with the free translation factored out. The
Jacobian of (r_0,q_0,...,q_(N-1)) relative to bead coordinates is unity. For any
finite positive kBT, Cartesian integration by parts gives

    0=integral partial_[q_i,alpha]
       [q_j,beta*exp(-U/kBT)] dq,
    <g_i,alpha*q_j,beta>=kBT*delta_ij*delta_alpha,beta.

Gaussian radial tails from kb>0 eliminate the boundary at infinity. A small
sphere around an excluded collapsed orientation has vanishing boundary measure
(the area and explicit q factor supply O(l^3)); the orientation energy is bounded.
Thus isolated singular points do not invalidate this equilibrium identity.
Summing i=j establishes the finite-N open-chain result

    <W_total>=N*kBT*I,   <Tr W_total>=3*N*kBT.

The radial factorization of Stage 4A.1 provides a second route. Integrating
partial_r[r^3*exp(-kb*(r-b0)^2/(2*kBT))] over r>0 yields

    <kb*(r-b0)*r>=3*kBT.

Each marginal direction is isotropic, independent of radial lengths, including
heterogeneous stiffness. Therefore <W_s,i>=kBT*I, <W_s>=N*kBT*I. Each W_b,i
has an isotropic ensemble mean proportional to I, and its trace is identically
zero, hence <W_b,i>=0. Mean shear and all three mean normal differences vanish
for stretching, bending and total separately. Their fluctuations need not vanish
or be statistically independent.

For a formal ideal solution of C freely translating chains in a specified V,
the positive configurational mean is C*N*kBT/V*I. Including the usual ideal
bead thermal/osmotic term, the tensile-sign total polymer stress is

    sigma_polymer = sigma_conf - [C*(N+1)*kBT/V]*I,
    <sigma_polymer>=-[C*kBT/V]*I,   pressure=C*kBT/V.

Equivalently the translational molecular partition factor is V^C, yielding
ideal **chain**, not bead, osmotic pressure. The isotropic bead term is conceptual
thermal/osmotic stress in overdamped dynamics; explicit bead velocities are
not required. This relation assumes free internal statistics and freely
translating chains, not a confining wall correction or an assigned melt density.
The simulator itself provides neither V nor a physical number density. Solvent
stress and kinetic/solvent relaxation contributions are outside this milestone.

## Intensive stress and future Green–Kubo normalization

For C independent identically distributed chains and externally specified V,

    sigma(t)=(1/V)*sum_c W_c(t),
    delta W_c=W_c-<W_c>,   n_chain=C/V.

Independent-chain connected cross-covariances vanish. Thus the stated
configurational shear relaxation function becomes

    G(t)=V/(kBT)*<delta sigma_xy(t)*delta sigma_xy(0)>
        =n_chain/(kBT)*<delta W_xy(t)*delta W_xy(0)>_one_chain.

Use per-chain covariances then average over chains; an ensemble-mean W covariance
would introduce an extra 1/C unless explicitly compensated. No bead-density
factor belongs here. Hydrostatic means are nonzero; use connected quantities.
In an isotropic equilibrium system the shear/normal-difference means are zero,
so their raw products have the same expectation as connected products. Isotropic
ideal thermal stress cancels from these deviatoric channels.

For any isotropic symmetric rank-two tensor process,

    <delta W_ab(t)*delta W_cd(0)>
       =A(t)*delta_ab*delta_cd
        +B(t)*(delta_ac*delta_bd+delta_ad*delta_bc).

Each shear covariance is B and each normal-difference covariance is 4B.
Consequently the unchanged six-channel isotropic combination

    H(t)=(C_xy+C_xz+C_yz)/5
          +(C_xx-yy+C_xx-zz+C_yy-zz)/30

is exactly B(t) in expectation when C are covariances of **raw W**. This result
requires isotropy and tensor symmetry, not Gaussian chains or pairwise forces;
it applies to the nonlinear semiflexible model including bending. Algebraically,
for symmetric S,T the same weighted channel products equal
S_dev:T_dev/10. That invariant projector identity is also tested independently.
The normal differences remain RAW; no factor1/4 is introduced into the pipeline.
The older Stage 2A convention with quarter-normalized normal products is distinct.

Temperature factors must be explicit:

    G(t)=n_chain*H(t)/(kBT),
    g(t)=G(t)/(n_chain*kBT)=H(t)/(kBT)^2.

Equivalently, use W/kBT channels and the existing 1/5,1/30 weights directly to
obtain dimensionless g. The validated Rouse implementation uses kBT=1 and raw
W=3*sum(q outer q), so its existing combination is numerically g without any
change. This CPU reference returns dimensional W for arbitrary kBT sampling;
blindly calling a raw-W covariance g at nonunit temperature would be incorrect.
No arbitrary volume, physical melt modulus or stress correlation is implemented.

Future correlations must use the **total** W_s+W_b: its autocovariance contains
stretch/stretch, bend/bend and both cross terms. The sum of separately computed
autocovariances alone is not generally the full answer. Radial/angular energy
factorization does not make these tensor processes independent. None of this
static derivation specifies a nonlinear relaxation spectrum or reuses Gaussian
Rouse mode predictions for the finite-rest-length dynamics.

## Bounded verification results and tolerances

The new suite has **11 passing tests**, completing in about 4.3 seconds locally
(Python 3.10, NumPy 2.2.4). Five equilibrium cases use 8192 independent chains
each; no dynamics, correlated origins, GPU work or production simulations run.
Cases cover N=1,2,4 deterministic edges, homogeneous/heterogeneous parameters,
zero bending, zero-rest-length quadratics, inactive/active collapsed bonds,
invalid/nonfinite inputs, nearly straight/antiparallel geometry and kappa up to
1000. No existing tolerance was changed.

* Affine finite differences separately test stretching, bending and total on
  all nine basis entries, uniaxial strain, isotropic dilation, symmetric shear,
  antisymmetric rotation and an arbitrary nonsymmetric E. With h=2e-6, tolerance
  is `2e-9*S*max(1,||E||)+3e-7*|W:E|`, S=max(1,|U|,max kb,max kappa). This
  combines centered-difference truncation with coefficient/energy-scaled
  subtraction error, particularly near stationary high-kappa configurations.
* Individual gradient-dyadic/metric tensors agree within absolute
  `1e-14*max(1,kappa)` and relative 2e-13. Raw symmetry uses that absolute scale;
  trace uses three times it. Translation/rotation tests use absolute 3e-13 and
  relative 2e-13 on the moderate-coefficient configurations. Independent
  bead-force virials for three reference points use relative 2e-12 and absolute
  `3e-13*max(1,max kb,max kappa)` to allow accumulation/reference-point roundoff.
* Maxwell/smooth zero bonds, known stretched one-bond W and a right-angle
  two-bond bending tensor have direct exact checks. The Gaussian b0=0,kb=3
  limit recovers the existing Rouse tensor. Fixed-grid Simpson integration
  independently verifies <kb*(r-b0)*r>=3*kBT with absolute 1e-10*kBT tolerance.
* Every equilibrium tensor entry and all six deviatoric means of Ws,Wb,Wtotal
  are checked against targets with six independent-chain SE plus 2e-12 numerical
  floor. The floor handles deterministic zero channels, not statistical bias.
  Fixed seeds are 43110..43114. No origins or correlated channels are counted as
  independent samples. Maximum absolute standardized residual in each case:

| Case | N | kBT | Bending | Target diagonal <Ws> | Measured diagonal <Ws> | Max absolute z |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| 0 | 1 | 1.7 | none | 1.7 | [1.664264,1.746735,1.708394] | 1.9577 |
| 1 | 3 | 1 | kappa0 | 3 | [2.959760,2.994555,2.996138] | 1.5742 |
| 2 | 3 | 1 | kappa2 | 3 | [2.999410,3.013392,3.005659] | 1.9530 |
| 3 | 3 | 1.7 | kappa10 | 5.1 | [4.951603,4.954927,5.090228] | 1.7915 |
| 4 | 4 | 0.7 | heterogeneous | 2.8 | [2.779495,2.847840,2.842154] | 1.6359 |

Case4 uses b0=[0.7,1,0,1.2],kb=[3,7,2,11],kappa=[0,0.1,0,8,0]. Mean Wb is
consistent with zero separately, and its per-configuration trace is checked
before channel extraction. These short ensembles test the static reference;
they are not an acceptance campaign for future GPU stress or relaxation.

The unchanged Stage 4A.1 CPU suite passes all **12** tests. Existing Rouse CPU
suites pass **4** theory, **2** streaming-theory and **4** stress tests. Python
compilation and scope/whitespace checks pass. GPU suites were not rerun for this
CPU-only milestone; their source/tests, accepted binaries/build rules and archived
acceptance evidence are untouched. No full scientific campaign was rerun.

## Review boundary and remaining questions

The stated static model fixes the stress/sign/normalization without an unresolved
Hamiltonian choice. Numerical cancellation, huge coefficients or very small
active bonds can still exceed float64/reference gradient range and are reported
rather than regularized. Finite-difference tolerances do not guarantee arbitrary
parameter ranges. External chain density remains an explicit physical input.
Future GPU stress sampling must reproduce the complete angular virial and be
independently checked against this reference; future finite-dt stress statistics
and relaxation need separate validation. This work establishes neither measured
convergence order nor a physical melt modulus.

Stage 4A.3b cannot begin until independent review of this derivation and its
tests, plus separate implementation authorization. The UAMMD reuse roadmap
remains in force. AGENTS now explicitly defers any work expected to exceed
10 minutes to the dedicated user-run Linux host; all execution here was bounded
well below that limit. No long run is needed to review this milestone.

From the repository root:

```sh
timeout 120s python3 examples/slip-springs/tests/test_semiflexible_stress.py
python3 examples/slip-springs/tests/test_semiflexible_reference.py
python3 examples/slip-springs/tests/test_theory.py
python3 examples/slip-springs/tests/test_stream_theory.py
python3 examples/slip-springs/tests/test_stress.py
```
