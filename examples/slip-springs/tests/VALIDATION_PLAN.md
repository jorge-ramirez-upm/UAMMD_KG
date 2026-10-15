# Stage 1 acceptance plan (written before statistical execution)

No thresholds are to be selected from observed results. Use fixed seeds and
independent chains as the statistical units. All overlapping time origins of a
chain remain in the same cluster. Report standard errors and 95% intervals;
use an absolute standardized residual <=5 for the automated family of physics
checks. This conservative multiple-check gate covers fewer than 300 planned
checks; under Gaussian sampling its nominal family false rejection probability
is below 0.0002. It is not an accuracy guarantee or proof of RNG independence.

- Deterministic GPU forces versus an independent CPU pair-bond accumulation:
  constant chains, straight chains, arbitrary small shapes, N=1,2,8, three
  independent chains, free ends, zero net force, translation invariance, and
  one zero-temperature GPU update. Roundoff tolerance: 3e-6 relative/absolute
  for float, 1e-13 for double, on these bounded inputs.
- RNG: 131072 independent IDs, all three components; mean 0, second moment 1,
  fourth moment 3, component, adjacent-ID and consecutive-step products 0.
  Fixed 6-standard-error gates use Gaussian moments (fourth-moment variance96).
  Replay, ID permutation and counters beyond 2^32 are deterministic checks.
- Initialization: N=8,32,100, 8192 independent chains, seed 20261015+N,
  zero steps. Check bond q^2, Ree^2 and Rg^2 with 5 SE using across-chain SE.
- Dynamics/timestep study: N=8,32,100, dt=0.01,0.005,0.0025, both precisions,
  512 independent chains each. Seed=710000+100*N+dt_index+10000*precision_index.
  Start at exact continuous equilibrium; run at least 1.25 tau1, sample about
  32 intervals/tau1, with no discarded equilibration. Compare dimensions to
  the EXACT nonstationary EM covariance starting from variance1/lambda, not
  only the stationary limit. Report continuous and stationary EM references.
- CM: multiple-origin direct MSD at about tau1/4 and tau1/2, compare D=1/(N+1).
- End-to-end: ratio of mean dot product to origin-matched mean Ree^2, at about
  tau1/4 and tau1/2. Exact finite-N odd-mode amplitudes and the actual initial
  covariance/time-step are used. Also report the continuous-time curve.
- Slowest mode: orthonormal cosine mode p=1, same ratio at about tau1/2;
  infer tau=-lag/log(C1). Use chain-cluster delta-method SE, compare the
  exact EM tau=-dt/log(1-lambda1*dt) and report continuous tau=1/lambda1.
- Convergence: combine dimension residuals against continuous theory across
  independent N cases, separately for each precision and timestep; compare
  measured positive bias to exact finite-step predicted bias and its SE.
  Do not demand monotone individual noisy points. Report how strongly the
  data resolve the expected decrease, including unresolved trends.
- Single/double: independent seeds, same theory, and differences using combined
  chain SEs. No requirement for identical trajectories.
- Require finite sampled observables, no collapsed sampled bonds, and maximum
  coordinate spacing / sqrt(2dt) <0.01 in these runs. This monitors the tested
  coordinate range only; it cannot certify arbitrarily long trajectories.

A failed check blocks the Stage 1 success claim until investigated. Further
runs are allowed to diagnose a failure, but original results must be retained.
Performance is a separate small run, not a criterion in these scientific gates.
