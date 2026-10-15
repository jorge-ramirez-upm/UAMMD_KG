# Stage 2A validation plan — fixed before stochastic execution

Preserve all Stage 1 gates and seeds. New stress gates use |residual| <=5 SE,
with across-independent-chain standard errors and reported approximate 95%
intervals. The planned stress family has fewer than 2500 checks (nominal
Gaussian union bound <0.0015). These CLT intervals are not exact coverage claims.
No tolerance or seed will be changed in response to a failed gate.

Deterministic GPU tests: N=1,4,8; straight chains on x/y/z, arbitrary 3D chains,
multiple chains, zero-length bonds, uniform translations including large exactly
representable translations. Compare all nine entries of a symmetric tensor
reconstructed from the six stored components against a CPU bond outer-product
loop. Tolerance 1e-11*(1+abs(reference)) for double accumulation of the stored
coordinates in both builds. Also assert translation invariance for exact integer
inputs. No full bead transfer is used by the simulator to compute stresses.

Independent CPU theory tests use the full free-end stiffness matrix and Wick's
identity, rather than the scalar mode implementation. Include nonstationary
origins that discriminate mean(square(covariance)) from square(mean(covariance)).
Test zero lag, nonzero lags, continuous equilibrium, normal-difference factor4,
and exact direct sums on synthetic data. Test preservation of independent
chain contributions and SE of paired channel differences.

Stress suite (both precisions):
- Initial equilibrium: N=8,32,100, 8192 independent chains, zero steps;
  seed=20262015+N+10000*precision_index (single=0, double=1).
- Evolved: N=8,32,100, h=0.01,0.005,0.0025; 2048 independent chains;
  seed=820000+100*N+dt_index+10000*precision_index. No discarded equilibration.
  stride=round(0.05/h), steps=64*stride, 65 frames, duration approximately3.2.
- All six deviatoric channels remain separate: xy,xz,yz,xx-yy,xx-zz,yy-zz.
  Scale the normal-difference products by1/4, not1/2. No channel averaging.
- Means of all shear/normal-difference channels should be0; diagonal means
  should be <sum_p lambda_p*v_p(origin)> (N initially).
- Second moments of each shear and each normalized normal difference should
  be <sum_p (lambda_p*v_p(origin))^2>, exactly N initially.
- Direct lags in sample intervals: 0,1,4,16,32 (times0,0.05,0.2,0.8,1.6).
  Compare all six normalized channels and all three raw diagonal correlations
  against exact nonstationary EM; report continuous references separately.
  Square mode covariances at EACH ORIGIN before averaging over origins.
- Isotropy: compare each of the other five normalized channels to xy at every
  lag, using the SE of their per-chain paired difference. Do not assume channels
  (especially the three dependent normal differences) are independent.
- Cross-precision comparisons: compare theory residuals of all six second
  moments and all six channels at the five lags, with combined independent SE.
- Timestep convergence: pool each channel's fractional second-moment bias
  across independent N cases with inverse-variance weights. Report the predicted
  EM bias and coarse-to-fine decrease with uncertainty for EACH channel. Gate
  pooled agreement within5 SE and positive decrease at >=1.96 SE; no averaging
  across channels. These measurements should resolve the leading O(h) bias.
- Retain per-chain lag contributions in NPZ in addition to the raw tensor CSV.
  Any failed gate blocks a success claim and must be investigated and recorded.

Timing tests: zero production steps with/without equilibration, positive
production with nonzero equilibration, non-divisible sampling stride, schema
units, null/N/A rates for zero steps, and exact arithmetic identities for ns
per bead/step from saved measured times. Initialization/equilibration and final
CSV flush/close must be outside the production interval. Metadata serialization
and terminal logging are telemetry overhead outside these measured intervals.
