# Timestep selection

The initial `dt=2.5e-5` choice was a conservative reference baseline: it makes the finite-rest-length stretching scale and the singular angular length scale small per update while leaving room to measure bias. It is a comparison baseline, not a proof that larger values are inaccurate.

Stage 4A.4 used 512 independent chains, seed 433201, exact equilibrium initialization, double precision, every-step six-channel stress, and T=20. N=8 comparisons found that `dt=1e-3` passed available κ=0 fixed-lag and crossing checks, while κ=10 remained unresolved at the crossing criterion. The measured H(0) changes from `2.5e-5` to `1e-3` were approximately `+0.708 ± 0.071` (κ=0) and `+0.808 ± 0.173` (κ=10), separate amplitude diagnostics rather than an unapproved acceptance gate.

The recovered N=32 analyses compare `2.5e-5` with `5e-4`. At κ=0, H(0) changed by `+1.320 ± 0.241` (+1.31%); at κ=10, by `+2.430 ± 0.990` (+2.23%). The exact 0.01 fixed-lag gate passed for both. The nearest exported baseline bins for 0.05 and 0.10 are 0.0496 and 0.0992, so exact-lag gates remain unresolved rather than being replaced by interpolation. The first crossing passed for κ=0 and was unresolved for κ=10. Available bond moments, tangent correlations, and histogram total variation passed; global size (`R_e²`, `R_g²`) and some stationarity decisions remained unresolved. Both overall N32 classifications remain unresolved.

Statistical significance and scientific tolerance answer different questions. A nonzero H(0) difference can be many standard errors from zero while still lacking an approved amplitude threshold. Conversely, a fixed-lag difference can be statistically uncertain without being evidence of acceptable convergence. The established gates are retained: static 1%/2% limits with three-SE uncertainty, fixed-lag `|ΔH|+3SE <= 0.05 H_baseline(0)`, and a 10% crossing rule with conservative uncertainty. No threshold was fitted to these outcomes.

The analytical local estimate is

`tau_min ≈ zeta/(4 kb + 16 kappa/b0²)`.

It is a harmonic approximation, not a rigorous nonlinear stability or accuracy bound. The Stage 4A.5 CPU preselector samples exact equilibrium configurations, evaluates the actual potential Hessian, removes only translational zero modes using a numerical tolerance, retains rotations and reports negative curvature, then uses

`dt_trial = c zeta / Q99(lambda_max)`,

with default `c=0.05`. For the recorded N=8, κ=10, 100-sample report, Q99 was 187.950 and `dt_trial=2.6603e-4`; the harmonic estimate was `1.7857e-4`. 76/100 configurations had significant negative curvature. This is a local-curvature screening heuristic; Q99 is sample-limited, and neither formula guarantees global nonlinear Euler–Maruyama stability, equilibrium accuracy, or terminal dynamics.

Use the preselector as follows:

```sh
cd /tmp/UAMMD_KG-slip-springs-dev
OPENBLAS_NUM_THREADS=1 python3 examples/slip-springs/timestep_preselector.py \
  --N 8 --kb 30 --kappa 10 --b0 1 --zeta 1 \
  --configurations 100 --seed 433201 --c 0.05 \
  --report /tmp/timestep-preselector.json
```

Its measured N=8 example took about 0.047 s excluding import/startup on the development host. The dense CPU Hessian is intended for small chains, not a new campaign.

Full acceptance still requires the unavailable or unresolved energy components, angle and end-to-end distributions, global-size precision, first/second-half stationarity, and exact shared physical lags. A first crossing is not terminal relaxation. No production timestep has been authorized by these studies.
