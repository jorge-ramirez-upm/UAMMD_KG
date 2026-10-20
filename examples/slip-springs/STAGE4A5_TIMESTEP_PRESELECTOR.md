# Stage 4A.5 — CPU timestep preselector

`timestep_preselector.py` provides a conservative starting heuristic for timestep
screening, not a timestep acceptance decision. It uses only NumPy and the unchanged
`semiflexible_reference.Chain.sample` exact-equilibrium sampler at kBT=1. Default:
N=8 springs (9 free beads), kb=30, κ=10, b0=zeta=1, 100 independent configurations,
seed 433201 and c=0.05. No Stage 4A.4 result is used to choose or fit c.

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
OPENBLAS_NUM_THREADS=1 python3 examples/slip-springs/timestep_preselector.py \
  --N 8 --kb 30 --kappa 10 --b0 1 --zeta 1 \
  --configurations 100 --seed 433201 --c 0.05
```

JSON goes to stdout; `--report /absolute/new/report.json` saves a new file and
refuses overwrite. The parent directory must exist. N, configuration count and
seed are integers; N/count must be positive, seed nonnegative. kb, b0, zeta and c
must be finite and positive; κ must be finite and nonnegative. This preselector
requires b0>0 even though the underlying reference also permits b0=0. It does not
modify any initializer, force, integrator, correlator or validation threshold.

The two estimates use the same coefficient:

```
harmonic curvature = 4*kb + 16*kappa/b0**2
harmonic tau_est   = zeta / harmonic curvature
harmonic dt_est    = c * tau_est
dt_suggested      = c * zeta / Q99(lambda_max)
```

The first is a **harmonic local-mode approximation**, not a rigorous bound for
arbitrary nonlinear configurations. The second uses the 99th percentile of the
largest resolved positive potential-Hessian eigenvalue in each configuration.
Median, Q95, Q99 and maximum observed are reported using NumPy's linear sample
quantiles. Q99 from 100 samples is uncertain and can miss rare high curvatures.
Neither estimate guarantees stability, an error bound or equilibrium accuracy.
The largest observed mode's `dt*lambda/zeta` is also reported. For a fixed positive
scalar harmonic mode EM requires this quantity <2; that condition alone does not
certify this nonlinear system. c>=2 is flagged, rather than silently capped.

The code differentiates the actual potential analytically:
`U = sum kb/2*(|q|-b0)^2 + sum kappa*(1-u·v)`. For each bond the Cartesian
stretch block is `kb*((1-b0/l)*I + (b0/l)*u*u.T)`. Angular second derivatives include
both tangent-projector and inverse-length terms. Bond blocks scatter through
`q_i=r_(i+1)-r_i` into a symmetric energy Hessian H with open ends. This is
**H=d²U/dr²**; the overdamped decay matrix is H/zeta and the drift Jacobian is
−H/zeta. The fastest positive local mode is unrelated to a terminal/global
polymer relaxation time.

Three normalized translation vectors must satisfy the numerical residual test
before projection into their orthonormal complement. The tolerance is
`128*float64_eps*3*(N+1)*max(1, ||H||_inf)`. The same tolerance classifies residual
internal eigenvalues as positive, negative or numerically zero. Only translations
are projected out; all internal modes remain in the eigendecomposition. No
rotational modes are removed. At a stationary straight chain rotations are null
directions; away from stationarity `H*(Omega*r)=Omega*grad(U)` need not vanish.
The tests verify both facts, translational invariance, rotation covariance and
finite free-end spectra, including the one-bond boundary case.

Each sampled configuration retains its largest positive eigenvalue, **all
significant negative eigenvalues**, minimum eigenvalue, numerical-zero count,
translation residual, tolerance, minimum bond length and condition diagnostic.
Nonstationary equilibrium configurations can have negative curvature; they are
not minima, and no configuration is filtered out on that basis. Collapsed bonds
or nonfinite Hessians fail explicitly. Minimum bond/b0 <0.1 flags a very short
bond. The absolute nonzero spectral condition ratio excludes only eigenvalues
inside the numerical tolerance and flags values >1/sqrt(float64_eps). These are
diagnostic flags, not scientific acceptance thresholds; symmetry zeros and poor
conditioning are reported separately. No bond regularization is applied.

CPU verification:

```bash
OPENBLAS_NUM_THREADS=1 timeout 120s python3 -m unittest discover \
  -s examples/slip-springs/tests -p test_timestep_preselector.py -v
```

Seven focused tests cover central finite differences of existing forces for
flexible, semiflexible and heterogeneous chains, invariances/boundaries, negative
curvature, short/ill-conditioned bonds, quantiles, scaling, reproducibility and
CLI validation/overwrite refusal. The utility uses dense matrices: per sample
storage is O(N²), eigendecomposition O(N³). It is intended for small chains such
as N=8/32; this is not a Hessian-analysis framework or a new validation campaign.
One BLAS thread avoids excessive thread startup costs for these small matrices.

A tested N=8, κ=10 default-size example took 0.047 s (sampler plus Hessian analysis;
excludes Python/import startup) on the development host. Largest-positive
curvature median/Q95/Q99/max were 136.5354/176.3262/187.9499/191.4852, giving
`dt_suggested=0.0002660283` versus harmonic `dt_est=0.0001785714`. There were 76/100
configurations with significant negative curvature, minimum eigenvalue −8.88235;
minimum bond length was 0.51810. No short-bond or conditioning flags fired.
These measurements describe this sample only and do not authorize a timestep.
