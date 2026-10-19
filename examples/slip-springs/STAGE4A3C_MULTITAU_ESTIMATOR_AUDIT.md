# Stage 4A.3c — Multi-Tau Estimator and Statistical Support Audit

This is a CPU-only audit of the existing KG multi-tau implementation.  It does
not change the correlator, the simulator, stress sampling, acceptance rules, or
any campaign artifact.  The executable fixtures are
`tests/multitau_estimator_audit.py` and
`tests/test_multitau_estimator_audit.py`.

## Reproduction

From the repository root:

```text
python3 examples/slip-springs/tests/test_multitau_estimator_audit.py
python3 examples/slip-springs/tests/test_stage4a3c_capacity_audit.py
python3 examples/slip-springs/tests/multitau_estimator_audit.py \
  --observations 2048 --repeats 2
```

The tests are independent scalar/NumPy CPU fixtures; no CUDA device or GPU
simulation is used.  The larger production-like run is intentionally bounded
because the reference Python recurrence is a transparent audit implementation,
not a performance benchmark.

## What the implementation estimates

Let `x_t` be the level-0 observations and let `m=2` be the decimation factor.
For complete blocks, level `k` contains block means

```text
y_k(q) = (1/m) sum_{a=0}^{m-1} y_{k-1}(m q + a),  y_0(q)=x_q.
```

At that level the ring buffer accumulates products of samples separated by
the exported ring offset `r`; the physical lag is `ell=r m^k`.  Thus a level-k
estimate is

```text
C_k(r) = [sum_q y_k(q)y_k(q+r)] / n_k(r),
```

where `n_k(r)` is the actual number of valid products accumulated in the ring.
Level zero exports all offsets.  Higher levels export offsets
`P/2 ... P-1`, because shorter lags are supplied by finer levels.  The deepest
populated level is deliberately not exported by `evaluate`; this is the
existing implementation's guard against an incompletely matured terminal
level.  A partial block in an accumulator is not forwarded, so incomplete
coarse blocks cannot silently become observations.

For comparison, the direct time-origin estimator is

```text
C_direct(ell) = 1/(N-ell) sum_{t=0}^{N-ell-1} x_t x_{t+ell}.
```

The multi-tau estimator is not, in general, this estimator evaluated at a
larger lag.  For a stationary process with covariance `C`, the expectation of
a complete block estimate is

```text
E[C_k(r)] = (1/m^(2k)) sum_{a,b=0}^{m^k-1} C(r m^k + b-a).
```

It is therefore the correlation of block-averaged observations.  The
instantaneous and block estimates agree only when the block width is small
relative to the physical variation being fitted (or for special processes).
Block means reduce high-frequency variance, but they also smooth and can bias
the apparent amplitude and shape of a relaxation when `m^k dt` approaches its
relaxation time.  Overlapping ring origins remain temporally correlated; `n_k`
is a product count, not an independent-sample count.

The four distinct counts used in this audit are:

| quantity | meaning |
|---|---|
| `N` | original stress observations |
| `N-ell` | raw instantaneous time-origin pairs at lag `ell` |
| `n_k(r)` | valid products of level-k block means (the exported `n`) |
| effective sample size | smaller quantity after temporal correlation; not inferred from `n_k` |

Independent simulated chains are the independent units used by the existing
chain-major bank for uncertainty estimates.  Many origins from one chain do
not replace independent chains.

## Deterministic and stochastic comparison

The fixture covers independent Gaussian noise, an AR(1) exponential process,
fast-plus-slow exponentials, a slowly decaying tail, and deterministic
sinusoidal stress.  It compares direct products with the exact direct
correlation of the same non-overlapping block means.  The following run used
2,048 observations and two independent realizations per process (the complete
printed output is produced by the command above):

| process | P×L | exported bins | final lag (samples) | final block width | final coarse pairs | max error vs block expectation |
|---|---:|---:|---:|---:|---:|---:|
| white | 16×16 | 72 | 1920 | 128 | 1 | 3.1×10⁻¹⁵ |
| white | 32×15 | 128 | 1984 | 64 | 1 | 3.1×10⁻¹⁵ |
| white | 64×14 | 224 | 2016 | 32 | 1 | 3.1×10⁻¹⁵ |
| exponential | 16×16 | 72 | 1920 | 128 | 1 | 3.3×10⁻¹⁵ |
| exponential | 32×15 | 128 | 1984 | 64 | 1 | 3.3×10⁻¹⁵ |
| exponential | 64×14 | 224 | 2016 | 32 | 1 | 3.3×10⁻¹⁵ |
| fast+slow | 16×16 | 72 | 1920 | 128 | 1 | 6.7×10⁻¹⁶ |
| tail | 16×16 | 72 | 1920 | 128 | 1 | 1.1×10⁻¹⁵ |
| deterministic | 16×16 | 72 | 1920 | 128 | 1 | 1.1×10⁻¹⁵ |

All omitted rows have the same conclusion: the maximum error against the
block-mean reference is at floating-point round-off, while the error against
the instantaneous reference grows when the block width is large.  For example,
the exponential fixture's maximum instantaneous-reference error was 0.249,
0.224 and 0.110 for 16×16, 32×15 and 64×14 respectively.  This is estimator
smoothing, not a transport or ordering error.  The unit fixture also checks
exact pair counts, deepest-level omission, finite output for every process, and
the incomplete-block rule.

The final exported bin in these short fixtures has one coarse pair despite the
underlying raw lag having 128, 64, or 32 possible origins.  This is a concrete
example of why pair counts must not be interpreted as independent statistical
replicates.

## Long-time support and the 16-origin rule

The capacity helper computes nominal lag reach, complete-block origins, and the
number of exported bins through the documented planning targets.  With the
existing Gaussian N=8 planning time (`4 tau = 5.528`) it gives minimum useful
levels P=16: L=15, P=32: L=14, and P=64: L=13; the corresponding numbers of
exported lag bins through that target are 140, 248, and 450.  For the N=32
planning scale (`4 tau = 2260`, based only on the documented rigid-rod scale,
not asserted to be the nonlinear relaxation time), P=16 has no configuration
meeting the 16-origin support gate in the available 4,000-time-unit fixture.
P=32 requires L=23 (396 bins through the target), while P=64 requires L=22
(737 bins).  These are mathematical capacity results, not evidence that the
rigid-rod time is the actual semiflexible relaxation time.

Sixteen coarse pairs are a conservative, fail-closed numerical-support rule:
below it, variance and sensitivity to individual origins can be extreme.  The
audit does **not** show that a bin with 15 pairs is mathematically invalid;
reliability also depends on block width, covariance time, amplitude, repeated
chains and the fitting objective.  Conversely, having 16 overlapping pairs is
not proof of 16 independent observations.  No evidence here justifies changing
the frozen rule, so it remains supported as a minimum reporting gate while its
scientific sufficiency remains conditional and unresolved.  Any proposed
amendment would need a separately versioned study with chain-level uncertainty
and physical fit validation.

## Implications for N=8, N=32, and 16×40

The traditional 16×40 hierarchy provides many redundant levels for a finite
trajectory; levels beyond the observation window still consume correlator
memory and update work.  It does not manufacture additional time origins.  For
N=8, P=16 with fewer levels can cover the Gaussian planning target, but its
coarsest useful bin must still satisfy the existing resolution criterion; P=32
or P=64 provides more bins and smaller widths.  For N=32, P=16 cannot meet the
documented long-lag/16-origin condition for the planning duration, regardless
of adding levels; P=32 or P=64 is mathematically capable under that planning
scale, subject to memory and actual relaxation-time confirmation.

The audit therefore separates four decisions: (1) lag reachability, (2)
block-averaging approximation error, (3) statistical uncertainty, and (4) the
frozen acceptance rules.  It does not select a production hierarchy and does
not treat the rigid-rod planning time of 565 as a measured nonlinear
relaxation time.

## Limitations and recommendation

The fixtures are scalar and CPU-only; they do not validate GPU transport or
semiflexible production trajectories.  AR processes are controlled examples,
not fitted physical chains.  Effective sample size is not estimated from a
single correlated series; the production chain-major bank should continue to
use independent chains for uncertainty and retain the existing diagnostics.

Recommendation: keep the 16-origin criterion and existing multi-tau mathematics
unchanged, report raw/coarse pair counts separately, and require a later
physical-chain study before relaxing the criterion or choosing between P=16,
32, and 64.  No production hierarchy is automatically authorized by this
audit.
