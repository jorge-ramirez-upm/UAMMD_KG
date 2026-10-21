# E1 Stage D0.1 — bounded CPU timestep screening

21 October 2026; source `31643cef8838a22b38267338f124f558274b39dd`, branch
`slip-springs`, expected starting SHA verified; tracked working tree initially
clean. This accompanies the [D0.1 protocol](E1_STAGE_D_VALIDATION_PROTOCOL.md).

Recommend primary finer/coarser **1e-4 / 2.5e-4**, reserved finer **5e-5** for
approved ambiguity/refinement checks, and **5e-4** only as a separately approved
exploratory level. **This screening reveals no reason to reject 2.5e-4 from the
upcoming pilot.** None of these timesteps is validated or frozen for production.

## Method and results

The unchanged, existing tested CPU preselector drew 100 independent exact
backbone equilibrium configurations per case (600 total), with kb=30,b0=1,
kBT=zeta=1 and c=.05. Distinct deterministic seeds are `433201+100*N+kappa`;
these are independent RNG streams without trajectory burn-in or GPU RNG reuse.
The accepted `Chain.sample` law has radial density proportional to
ell² exp[-30(ell-1)²/2] and conditional orientations proportional to
exp[kappa*u.v]. No random slip-spring simulator or new dynamics was used.
Float64 analytic potential Hessians use open ends, remove only three
translations, retain internal/rotational modes and negative curvatures, and
use the existing numerical tolerance. Quantiles use NumPy's linear method.
No correctness defect was identified; source and tests remain unchanged.

| N | kappa | Seed | Median lambda+max | Q95 | Q99 | Max observed | Suggested dt=.05/Q99 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0 | 434001 | 96.4597 | 104.1624 | 105.2183 | 105.5958 | 0.0004752025 |
| 8 | 2 | 434003 | 104.0740 | 110.6237 | 111.7604 | 113.0859 | 0.00044738558 |
| 8 | 10 | 434011 | 142.7145 | 171.9350 | 180.6345 | 191.7341 | 0.00027680204 |
| 32 | 0 | 436401 | 101.9837 | 107.9931 | 109.9360 | 110.4920 | 0.00045481008 |
| 32 | 2 | 436403 | 108.7545 | 112.4332 | 113.8473 | 114.1579 | 0.0004391846 |
| 32 | 10 | 436411 | 160.5312 | 194.3675 | 216.3254 | 222.6975 | 0.00023113331 |

Here lambda+max denotes the largest resolved positive curvature per configuration.

| N | kappa | Configurations with negative curvature /100 | Most negative eigenvalue | Shortest bond | Short-bond / conditioning flags | Analysis seconds |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0 | 100 | -65.45874 | 0.457338 | 0 / 0 | 0.0228 |
| 8 | 2 | 93 | -30.25620 | 0.496853 | 0 / 0 | 0.0524 |
| 8 | 10 | 80 | -6.40731 | 0.518572 | 0 / 0 | 0.0520 |
| 32 | 0 | 100 | -72.68498 | 0.454694 | 0 / 0 | 0.0747 |
| 32 | 2 | 100 | -53.61359 | 0.491738 | 0 / 0 | 0.2061 |
| 32 | 10 | 100 | -9.92035 | 0.401016 | 0 / 0 | 0.2038 |

Short-bond flags mean min(ell)/b0<.1; conditioning flags use the existing
resolved-absolute spectral ratio >1/sqrt(float64 epsilon). Negative local
curvatures at nonstationary equilibrium configurations are retained, not
classified as stable harmonic modes or discarded. No collapsed/nonfinite or
translation/symmetry failure occurred. Timings exclude Python/import startup;
total sampler/Hessian time was about 0.612 s, not a simulation runtime benchmark.

## Dimensionless local screen and slip-spring increment

The table gives **bare** q=dt*Q99(lambda_max)/zeta, separately from accuracy.

| N | kappa | Primary 1e-4 | Primary 2.5e-4 | Reserved 5e-5 | Exploratory 5e-4 |
|---:|---:|---:|---:|---:|---:|
| 8 | 0 | 0.010522 | 0.026305 | 0.005261 | 0.052609 |
| 8 | 2 | 0.011176 | 0.027940 | 0.005588 | 0.055880 |
| 8 | 10 | 0.018063 | 0.045159 | 0.009032 | 0.090317 |
| 32 | 0 | 0.010994 | 0.027484 | 0.005497 | 0.054968 |
| 32 | 2 | 0.011385 | 0.028462 | 0.005692 | 0.056924 |
| 32 | 10 | 0.021633 | 0.054081 | 0.010816 | 0.108163 |

At A2=5, k_ss=3kBT/A2=.6. For fixed anchors and attachments H_ss is
positive semidefinite with occupied-bead diagonal blocks .6*I3. Single
occupancy implies ||H_ss||<=.6 and, by the symmetric eigenvalue inequality,

```text
lambda_max(H_bb+H_ss) <= lambda_max(H_bb)+.6.
```

Thus an upper screening estimate at the sampled Q99 is Q99+.6; add respectively
**.000060, .000150, .000030, .000300** to the four q columns. This is a
pointwise positional-Hessian bound, hence also a quantile upper bound under
the same backbone marginal; it is not a confidence bound on the population Q99.
It does not establish stability of stochastic hopping/renewal or equilibrium
accuracy. No force/Hessian change or spring-state sampling is required.
Applying the bound to the maximum observed backbone curvature gives
q<=.0558244 at primary coarser dt,
and q<=.111649 at exploratory dt, both for N32,kappa10. These samples cannot
exclude rare singular short-bond configurations.

At 2.5e-4, N32,kappa10 has bare q=.054081, slightly above the unchanged
heuristic c=.05 (suggested dt=.000231133); c is not an acceptance threshold.
All six local positive-mode screens remain far below the fixed harmonic EM
limit q<2. The harmonic approximation 4kb+16kappa/b0² gives curvatures
120/152/280 for kappa0/2/10, and suggested dt .000416667/.000328947/.000178571.
It too is a heuristic, not a rigorous nonlinear bound. No sample expansion
beyond 100 per case was needed or authorized.

## Accuracy and efficiency assessment

For an isolated fixed positive harmonic mode, EM has stationary variance
(kBT/lambda)/(1-q/2), relative excess q/(2-q). Evaluating this illustration at
lambda=sampled Q99+.6 gives percentages below; these are **not measured biases
or upper error bounds for nonlinear equilibrium observables**.

| N | kappa | Primary 1e-4 | Primary 2.5e-4 | Reserved 5e-5 | Exploratory 5e-4 |
|---:|---:|---:|---:|---:|---:|
| 8 | 0 | 0.532% | 1.340% | 0.265% | 2.717% |
| 8 | 2 | 0.565% | 1.425% | 0.282% | 2.890% |
| 8 | 10 | 0.914% | 2.318% | 0.455% | 4.746% |
| 32 | 0 | 0.556% | 1.401% | 0.277% | 2.842% |
| 32 | 2 | 0.576% | 1.451% | 0.287% | 2.945% |
| 32 | 10 | 1.097% | 2.787% | 0.545% | 5.734% |

The stiff primary-coarser illustrations exceed 2%, and even some finer
illustrations exceed a 1% bond-moment margin; fastest-mode variance is not the
same observable. This motivates matched D1 comparisons and the reserved
reference, without changing any scientific margin or declaring failure from
this illustration. Local stability, static equilibrium accuracy and dynamical
accuracy require distinct evidence; no terminal-time claim follows.

Prior [backbone evidence](TIMESTEP_SELECTION.md), preserved unchanged, supports
considering larger steps but cannot validate E1. N8 at 1e-3 passed available
kappa0 dynamic gates; kappa10 crossing was unresolved. N32 at 5e-4 passed
available bond/tangent/histogram checks and exact .01 fixed-lag checks at
kappa0/10, while global sizes, some stationarity and other exact lags remained
unresolved. H(0) shifts were +1.31%/+2.23%; kappa10 crossing was unresolved.
There is no comparable prior kappa2 acceptance and no inherited active-spring
acceptance. The exploratory 5e-4 has roughly twice the primary-coarser q and
larger harmonic bias; it should not replace the primary pair on this evidence.

For every system at fixed physical duration T:

| dt | BD steps at T=.25 | BD steps at T=2 | Fewer steps versus old finer 2.5e-5 / old coarser 5e-5 |
|---:|---:|---:|---:|
| 1e-4 | 2500 | 20000 | 4x / 2x |
| 2.5e-4 | 1000 | 8000 | 10x / 5x |
| 5e-5 | 5000 | 40000 | 2x / 1x |
| 5e-4 | 500 | 4000 | 20x / 10x |

The amended 32-run T=.25 pilot would require 56000 replica BD steps versus
240000, 76.7% fewer. This is planning arithmetic, not execution authorization.
Expected hopping attempts per unit physical time remain **Z*nu_hop** and total
attempts Z*nu_hop*T. Larger dt increases attempts per batch, not fewer events
per physical duration; primary maximum mean is 12.8/step, exploratory 25.6.
Serial event costs, renewal destination scans and fixed-physical-cadence
observations/output may dominate, so BD step savings do not imply proportional
wall-time savings. No new GPU timing or scientific trajectory was run.

The protocol explicitly replaces old nonrepresentable shared early times with
.0005 and supplies exact integer schedules for all candidates. Step-1 frames
remain timestep-specific diagnostics. All existing scientific margins and
historical results are preserved; only the numerical proposals are amended.

## Executed commands, provenance and limits

From `/tmp/UAMMD_KG-slip-springs-dev` (Linux x86_64, Python 3.10.12,
NumPy 2.2.4; one OpenBLAS thread):

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 -m unittest discover -s examples/slip-springs/tests -p test_timestep_preselector.py -v
mkdir -p /tmp/e1-d01-screening-20261021
for n in 8 32; do
  for k in 0 2 10; do
    seed=$((433201 + 100*n + k))
    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 120s python3 examples/slip-springs/timestep_preselector.py --N "$n" --kb 30 --kappa "$k" --b0 1 --zeta 1 --configurations 100 --seed "$seed" --c 0.05 --report "/tmp/e1-d01-screening-20261021/N${n}-k${k}.json" || exit
  done
done
```

All seven existing tests passed in .206 s; all six CLI runs exited zero.
Documentation checks: `git diff --check` passed; exact rational arithmetic
verified all four integer schedules; section 7 statistical rules/margins are
byte-identical to starting HEAD. Programmatic isolation checks against the
Stage0 source `81fe5de9cd5ded849202eebab7c14e6bd35fb9ae` found all 407 changed
tracked paths, one new untracked report and 4050 pre-existing ignored paths
inside `examples/slip-springs/`; only the two requested documents changed in
D0.1. Existing generated evidence was preserved.

The
JSON files retain per-configuration spectra/diagnostics locally in the stated
`/tmp` directory; the tables above are the committed summary. Reports refuse
overwrite; reproduce into a fresh directory. Deterministic seeds reproduce
samples, with possible last-bit library differences; elapsed time is variable.

Q99 from 100 samples is tail-limited (linear interpolation near the two largest
observations); no population-tail confidence guarantee is asserted. Coupled
finite-step preservation, long-horizon drift, rate sensitivity, equilibration,
static and dynamical accuracy, and actual runtime remain unresolved. No observer,
GPU run, pilot, production timestep freeze or code/test modification occurred.
