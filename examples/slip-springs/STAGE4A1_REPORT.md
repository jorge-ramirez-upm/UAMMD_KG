# Stage 4A.1 — semiflexible Hamiltonian and CPU reference

16 October 2026. Starting local HEAD and remote `refs/heads/slip-springs` both
verified as `a5dfe5f8ddf516e6f36bd9382646023228cf33d6` before editing. Repository:
`jorge-ramirez-upm/UAMMD_KG`, worktree `/tmp/UAMMD_KG-slip-springs`.
The explicit Stage 4A.1 task supersedes the historical stage prohibition in
AGENTS.md only for this CPU reference and assessment. Stage 4A.2 is not begun.

## Contract and Hamiltonian

`semiflexible_reference.py` requires Python 3 and NumPy (tested with Python 3.10,
NumPy 2.2.4). All coordinates, energies, forces and numerical predictions use
float64. It is separate from the Gaussian Rouse model and has no dynamics,
CUDA, excluded volume, periodic boundaries or slip-springs. Anchor bead zero
when sampling; the otherwise free translational partition factor is removed.

For N>=1 bonds and N+1 beads, q_i=r_(i+1)-r_i, l_i=|q_i|, u_i=q_i/l_i:

    U_s = (1/2) sum_[i=0..N-1] kb[i] (l_i-b0[i])^2
    U_b = sum_[i=1..N-1] kappa[i] (1-u_(i-1) dot u_i).

`b0` and `kb` each have N entries indexed by bond. `kappa` has **N+1 entries
indexed by bead**, with mandatory zero placeholders at 0 and N; only 1..N-1
are angles. This avoids an implicit one-index shift. Arrays can be heterogeneous;
`Chain.homogeneous(N,b0,kb,kappa)` fills them. Inputs are copied and marked
read-only. Do not mutate a Chain after construction; build another for different
parameters. `kbt` is an explicit prediction/sampling argument, default 1; energy
and force contain no temperature parameter.

Require finite b0>=0, kb>0, kappa>=0 and finite positions of shape (N+1,3).
Strict kb>0 guarantees a normalizable unconfined radial measure; kb=0 and
negative stiffnesses are rejected. N=1 has no bending. Zero-rest-length bonds
are allowed. At l=0 with b0>0 the stretching force is undefined and raises
ValueError. At l=0 with b0=0 its smooth force is -kb*q on the right bead.
An active bending angle incident to any zero-length bond raises ValueError.
Collapsed bonds at inactive angles need no orientation and are allowed if the
stretch term is smooth. The joint energy/force API rejects configurations with
undefined force even when their energy alone would exist. Nonfinite/unrepresentable
lengths or results are rejected. There is no angular regularization, length
cutoff, sine denominator or alternate angle convention.

## Cartesian force derivation

For any U(q), write g_j=partial U/partial q_j. Since
partial q_j/partial r_j=-I and partial q_j/partial r_(j+1)=I,

    F_0=g_0; F_j=g_j-g_(j-1) (1<=j<=N-1); F_N=-g_(N-1).

For stretching, g_j=kb[j](l_j-b0[j])u_j. Thus each bond adds +g_j to
its left bead and -g_j to its right bead: a stretched bond attracts.

For angle i define a=q_(i-1), b=q_i, u=a/|a|, v=b/|b|, c=u dot v.
Using partial u/partial a=(I-u*u^T)/|a| gives

    A = partial U_i/partial a = -kappa[i] (v-c*u)/|a|
    B = partial U_i/partial b = -kappa[i] (u-c*v)/|b|.

The three bead forces are **A, B-A, -B** on i-1, i, i+1. Contributions
from adjacent angles add. These expressions remain finite at parallel and
antiparallel nonzero bonds; both exactly collinear angle forces are zero
(the antiparallel state is an unstable stationary maximum). Near straight
chains energy is evaluated as kappa*|u-v|^2/2, mathematically the same potential,
to avoid cancellation of 1-c. No clipping is applied to the force cosine.

Translation leaves all bonds unchanged. Rotation preserves lengths and dot
products and rotates forces. Each contribution sums to zero. The angle torque
about its middle bead is -a cross A - b cross B=0; pair torques vanish because
g_j is parallel to q_j. These identities imply zero total internal force and
torque, up to floating-point cancellation. Tests use centered coordinates for
torque to avoid amplifying a roundoff net force with a large origin offset.

`stretch_energy_forces` and `bend_energy_forces` expose the terms independently.
`energy_forces` shares bond displacements, then uses stretching only when
`active_angles is None`. In this case it does not call `_bend`, allocate an
angular force buffer, calculate bond orientations, or normalize angles, and it
returns the actual stretching force array without copying or adding zeros.
Nonzero coefficients are compiled into a small active-angle tuple at construction;
heterogeneous zero entries are never evaluated. The test both compares bits with
the stretch result and replaces `_bend` with a failing sentinel, checking force
array identity too. Parameter arrays exist at setup; no bending workspace exists
on this force path. No integration loop is introduced in this milestone.

## Independent equilibrium predictions

The linear change from bead coordinates to (r_0,q_0,...,q_(N-1)) has unit
Jacobian. In spherical bond coordinates d^3q_i=l_i^2 dl_i dOmega_i.
The Boltzmann factor splits into a product of radial weights and an orientation
chain. The isolated open-chain joint density therefore factorizes into
independent radial laws

    p_i(l) = l^2 exp[-kb[i](l-b0[i])^2/(2*kbt)] / Z_i, l>0,

and an orientation density. All radial statistics, including independence of
different lengths, are independent of every bending coefficient. This statement
relies on free ends and absence of closure, boundary or other interactions.

Put x_i=kappa[i]/kbt. For a fixed preceding direction, integrate the next one:

    integral dOmega exp[-x_i(1-c)] = 4*pi*exp(-x_i)*sinh(x_i)/x_i.

This is independent of the preceding direction; at zero its limit is 4*pi.
Consequently u_0 is uniform on the sphere, azimuths are uniform, and each
conditional cosine has p(c)=x*exp[x(c-1)]/(1-exp(-2*x)), -1<=c<=1.
Differentiating log(sinh(x)/x) gives E[c]=L(x)=coth(x)-1/x, so
E[u_i dot u_j]=product_[h=i+1..j] L(x_h). In the homogeneous case it is
L(kappa/kbt)^(j-i), including the flexible limit (zero for positive separation).

`langevin` uses x/3-x^3/45+2*x^5/945-x^7/4725+2*x^9/93555 below 0.05,
1+2/expm1(2*x)-1/x through 350, and 1-1/x above 350. The omitted series
term is below 1.1e-20 at the small-x boundary; the large-x exponential correction
is below double precision. Only nonnegative finite x is accepted.

`radial_moments` integrates the density with 128-point Gauss-Legendre quadrature
in y=(l-b0)/sigma, sigma=sqrt(kbt/kb), over [-min(b0/sigma,12),12].
The l^2 weight is scaled to avoid large b0/sigma squaring. Gaussian tails with
polynomial factors through degree four beyond 12 contribute less than 1e-25
relative for this parameter domain, below double precision. This is numerical
quadrature, not a claim of exact evaluation for every representable input;
underflow/overflow of derived scales is rejected. Exact useful checks:

    b0=0: E[l]=2*sigma*sqrt(2/pi), E[l^2]=3*sigma^2.
    b0/sigma >> 1 (exponentially small boundary error):
      E[l]=(b0^3+3*b0*sigma^2)/(b0^2+sigma^2)
      E[l^2]=(b0^4+6*b0^2*sigma^2+3*sigma^4)/(b0^2+sigma^2).

With m_i=E[l_i] and v_i=E[l_i^2],

    E[Re^2] = sum_i v_i + 2 sum_[i<j] m_i*m_j product_[h=i+1..j] L(x_h).

For homogeneous parameters this reduces to N*v+2*m^2 sum_[s=1..N-1](N-s)L(x)^s.
The finite sum is used rather than a cancellation-prone closed expression near
L=1. General predictions use O(N^2) work, suitable for small CPU references.
Tests independently integrate radial weights on uniform grids with Simpson's
rule and integrate conditional polar cosines/azimuth for a heterogeneous
three-bond Re^2. Thus they do not merely repeat the Gauss quadrature or the
correlation-product algebra. Monte Carlo tests provide another independent check.

Numerical prediction examples at kBT=1 (values rounded for display):

| Parameters | Mean lengths | Mean-square lengths | Mean-square Re |
| --- | --- | --- | --- |
| N=4, b0=1, kb=30, kappa=0 | 1.06451613 each | 1.16451613 each | 4.6580645163 |
| N=4, b0=1, kb=30, kappa=2 | 1.06451613 each | 1.16451613 each | 9.9715798582 |
| b0=[0.4,1,2], kb=[3,10,5], kappa=[0,0.3,4,0] | [1.12380767,1.18183223,2.19047623] | [1.44952307,1.48183223,4.98095245] | 12.4303788388 |

## Direct equilibrium sampling and its correctness

Lengths are sampled before any orientations. For each bond set t=l/sigma,
a=b0/sigma and m=(a+sqrt(a^2+8))/2, the mode of t^2*exp[-(t-a)^2/2].
Use t=m+Normal(0,1); reject t<=0. Writing delta=t-m, the log target-to-envelope
ratio is

    2*[log(t/m)-(t-m)/m] <= 0.

This follows from m-a=2/m and log(z)<=z-1. Accept using this ratio, evaluated
with log1p(delta/m). The Gaussian is a valid envelope, including a=0;
no discretized radial CDF or missing Jacobian is involved. Vectorized rejection
has a fail-fast bound of 10000 rounds per bond, not an approximate fallback.

Generate u_0 by normalizing an isotropic Gaussian. For each next bond draw h
uniform on [0,1), phi uniform on [0,2*pi), and invert the exact cosine CDF:

    c = 1 + log[h+(1-h)*exp(-2*x)]/x, x>0; c=2*h-1 at x=0.

Use log1p/expm1 for small x and logaddexp otherwise. Above 350, exp(-2*x)
is negligible at double precision and log(h)/x avoids overflow; the h=0 endpoint
maps to c=-1. Roundoff excursions of sampled c are clipped to [-1,1]. A stable
orthonormal frame about the preceding direction supplies the azimuth. Zero
coefficients instead draw an independent isotropic Gaussian direction without
constructing an angular frame. Lengths
and orientations are independent, and the conditional normalizers do not depend
on the preceding orientation: sequential sampling gives the exact target measure
within double precision. Samples are independent chains, not a Markov trajectory.
Very stiff chains can have angular deviations below representable precision;
no sampler can resolve those in float64. Sample count is explicit and memory is
O(count*N); this is not a production simulation API.

## Actual checked-out UAMMD integration assessment (read-only)

Inspected `src/Interactor/BondedForces.cuh`, `BondedForces.cu`,
`AngularBondedForces.cuh`, `docs/Interactor/BondedForces.rst` and
`test/Bonds/AngularBond.cu`. Conclusions concern this checkout, not
UAMMD-structured. No upstream source or existing potential is changed.

* `BondedForces<BondType,particlesPerBond>` accepts local pair or three-body
  potentials. `AngularBondedForces<T>` is an alias for `BondedForces<T,3>`.
  Potential interface: `BondInfo`, `readBond(istream&)`, device
  `compute(current_index,indices,positions,Computables,BondInfo)` returning
  per-particle `ComputeType` force, energy, virial. The actual parameter names
  are `Parameters.file` and `.data`; some header comments/tests have stale
  `.readFile` usage. Existing angular tests are not evidence of current API use.
* `BondedType::Harmonic` has per-bond `k,r0` and gives the desired force with
  k=kb,r0=b0. `detail::harmonicEnergy` returns **k*(r-r0)^2/4 per endpoint**;
  the kernel visits both endpoints, so summed energy is the desired half-k
  potential. Do not double k because of that quarter. Harmonic applies its Box
  to displacements; default Box is nonperiodic. At zero length it returns an
  empty contribution, including energy, which is incompatible with the explicit
  CPU singular-geometry policy for b0>0. A future local wrapper/potential is
  needed if identical rejection/diagnostics are required there.
* `BondedType::Angular` uses forward bonds pos[1]-pos[0], pos[2]-pos[1], so
  straight is theta=0, not the supplementary interior angle pi. It clamps the
  cosine. General force amplitude is
  -2*k*(sin(theta/2)-sin(ang0/2))/sin(theta/2); for ang0=0 it explicitly uses
  -2*k. These forces correspond to **4*k*[sin(theta/2)-sin(ang0/2)]^2**,
  whereas the documentation states 2*k times that square. At ang0=0, actual
  forces therefore match kappa*(1-cos(theta)) with **k=kappa/2**.
  Its `ComputeType ct{}` only receives force: **energy and virial remain zero**.
  Thus it cannot supply the full requested Hamiltonian/observables unchanged.
  It also normalizes zero-length bonds without a rejection policy.
* Per-record BondInfo supports heterogeneous pair and angle coefficients.
  A future **local custom three-bead BondType** can implement exactly the
  derived potential, force, energy shares (one third each), error signaling and
  indexing on the existing generic launcher, without editing core. A new
  standalone CUDA launcher is not inherently required. The harmonic type is
  reusable at nonzero lengths; use a local pair type if consistent singular
  behavior is needed. No such GPU implementation is included here.
* The generic builder duplicates each interaction into every incident particle's
  adjacency list. The kernel maps stable IDs through `id2index`, computes and
  sums each particle's contributions privately, then adds to its force/energy/
  virial array once. No scatter atomic is needed within that kernel. Separate
  interactors write overlapping arrays with `+=`: sequence their launches and
  force clearing on one stream, or provide explicit event dependencies across
  streams. `sum` launches on the supplied stream; its destructor synchronizes
  the device. Future integration must complete forces from the old positions
  before updating coordinates, preserving the existing Rouse path separately.
* Preserve the zero-bending fast path by constructing **no angular interactor,
  device topology, scratch storage or angular launch** when all coefficients
  are exactly zero. For heterogeneous arrays, build only active angle records.
  Merely launching a kernel that multiplies normalized angles by zero violates
  the requirement. No GPU force or performance validation is claimed here.

## Validation and tolerances

Run `python3 examples/slip-springs/tests/test_semiflexible_reference.py`.
The suite has 12 deterministic/fixed-seed test methods and completes in under
one second on this host. Counts are at most 16000 independent short chains per
case; no time integration, equilibration or scientific production runs.

* Centered finite differences (step 2e-6) separately check stretch, bend and sum,
  homogeneous/heterogeneous coefficients, bent/near-straight/near-antiparallel
  geometry and kappa=1e-9..1000. Relative tolerance 2e-7, absolute tolerance
  max(2e-8,2e-10*max(kappa)) balances O(h^2) truncation and O(eps*U/h)
  cancellation. Near-folded kappa=1000 has a ~1.1e-7 cancellation floor in
  components whose true force is close to zero, motivating coefficient scaling.
* Rigid transformation force/energy tolerances 2e-13; net force 2e-14, torque
  3e-14 on O(1) geometries with moderate coefficients. Straight and folded
  energies/forces, endpoint signs and flexible-path identity are exact checks.
* Langevin versus 200001-point Simpson integration uses 3e-12 absolute tolerance,
  spanning zero, branch boundaries, x=1e-9..1000 and asymptotics at 1e12.
  Radial moments versus 40001-point Simpson and Maxwell/large-b0 identities use
  relative 3e-12 (exact identities 3e-13). Explicit orientation transfer
  integration for heterogeneous Re^2 uses absolute 2e-8 (coarser Simpson grid).
* Fixed seeds 4100+int(x), 4811 and 724 check bond moments, pairwise orientation
  correlations, isotropy, radial covariance and Re^2. Each mean has a six-SE
  tolerance plus 5e-4 floor; independent chains are the sample units. Two-sided
  empirical CDF distance is <0.025 for radial and conditional cosine laws at
  x=0,1e-6,3,1000. With n=16000, the DKW false-rejection bound is <4.2e-9
  per CDF check (quadrature error is negligible). Coupled seeds produce the
  same radial draws at kappa=0,2,1000: recovered lengths agree within 4e-15.
* Invalid shape, nonfinite/negative parameters, endpoint coefficients, zero
  thermal energy, empty sample request and degenerate bond behavior are checked.

Results: all 12 new tests pass (under one second). README's N=4, 1024-chain
example was executed: predicted Re^2=9.9715798582, sample mean=9.8673084008,
first-chain energy=6.5770175982; the example itself is illustrative, with
statistical acceptance supplied by the fixed-seed tests.

Existing bounded checks also passed on the RTX 3060 Ti (sm_86):

```sh
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
make -C examples/slip-springs check-lifetime
python3 -m py_compile examples/slip-springs/semiflexible_reference.py examples/slip-springs/tests/test_semiflexible_reference.py
git diff --check
```

Both precision targets reused existing up-to-date CUDA executables (no claim of
a fresh CUDA compilation). Each executed the CUDA smoke, Rouse force/stress/RNG
units, pipeline error/lifetime checks, correlator smoke, 4 theory + 2 streaming
theory + 4 stress + 3 CLI Python tests, six bounded streaming cases and 14 input
guards. Worker ASan/UBSan/LSan passed in both invocations; the separate lifetime
ASan/UBSan/LSan check passed 200 ownership cycles. Existing read-only KG
correlator `fscanf` warnings were emitted during sanitizer compilation.

A programmatic isolation audit checked changed tracked paths against both the
starting commit and historical Stage 0 source
`81fe5de9cd5ded849202eebab7c14e6bd35fb9ae`, plus all untracked and ignored
files. Every path is within `examples/slip-springs/`. The only modified existing
file is README; all existing scientific code, tests and build rules are unchanged.
New files: this report, the CPU module and its test. Generated artifacts stay in
local ignored build/cache directories. No production campaign was run.

## Limits and next-stage questions

There is no unresolved choice in the specified isolated-chain equilibrium
Hamiltonian. Future work must choose/validate a GPU singular-geometry diagnostic
policy, force implementation, overdamped discretization, timestep convergence
and any stress/virial definition before dynamics claims. These are Stage 4A.2
questions, not implicit authorization. Slip-spring kinetics remain entirely out
of scope. Neither existing validated science nor Rouse source/build behavior is
modified. Current runnable commands are in README's running section; the new
CPU reference has no separate single/double build because it always uses double.
