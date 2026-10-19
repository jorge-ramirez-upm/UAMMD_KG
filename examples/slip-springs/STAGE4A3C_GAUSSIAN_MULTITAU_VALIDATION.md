# Stage 4A.3c — Gaussian-Chain Validation of Multi-Tau Stress Correlations

This bounded CPU study compares the existing multi-tau hierarchy with a
controlled stationary Gaussian-chain reference. It does not modify shared
correlators, stress definitions, dynamics, production algorithms, frozen
campaigns, or acceptance thresholds. No GPU or long scientific trajectory was
run.

## Reproducible fixtures and provenance

The isolated implementation is `tests/gaussian_multitau_validation.py`; its
unit checks are in `tests/test_gaussian_multitau_validation.py`.

```text
python3 -m unittest discover -s examples/slip-springs/tests -p 'test_gaussian_multitau_validation.py'
python3 examples/slip-springs/tests/gaussian_multitau_validation.py --springs 8 --frames 2048 --chains 16 --seed 433201
python3 examples/slip-springs/tests/gaussian_multitau_validation.py --springs 32 --frames 1024 --chains 16 --seed 433201
```

Both runs use `dt=0.000025`, stationary linear Gaussian Euler–Maruyama modes,
and exactly the same generated observations for all four configurations:
16×14, 32×13, 64×12, and the reference 16×40. The 16×40 output is identical
to 16×14 on these finite trajectories because levels beyond the populated
observation window cannot emit additional bins.

The N=8 comparison used 2,048 observations per chain and 16 independent
chains. The N=32 check used 1,024 observations per chain and 16 chains as a
bounded feasibility/behavior check; it is not a long-lag relaxation study.

## Analytical Gaussian reference

For `M=N+1`, the free-end Gaussian chain has internal eigenvalues

```text
lambda_p = 12 sin^2[p pi/(2M)], p=1,...,N.
```

At stationary EM timestep `h`, mode `p` has multiplier `a_p=1-lambda_p h`
and variance `v_p=1/(lambda_p(1-lambda_p h/2))`. The prescribed six channels
are formed from the complete configurational virial

```text
W_ab = sum_p lambda_p X_{p,a} X_{p,b},
```

in the existing order `xy,xz,yz,xx-yy,xx-zz,yy-zz`. The fixture retains all
three stretching/shear channels, all three normal-difference channels, and
their cross terms. Production's scalar isotropic combination is applied only
after each channel's correlation is accumulated:

```text
H = (Cxy+Cxz+Cyz)/5 + (Cxx_yy+Cxx_zz+Cyy_zz)/30.
```

For the Gaussian harmonic model, Wick's theorem gives the exact instantaneous
reference

```text
H(ell) = sum_p lambda_p^2 v_p^2 a_p^(2 ell).
```

This is a controlled Gaussian harmonic model, not the finite-rest-length
nonlinear semiflexible model. No nonlinear relaxation time was fitted or
substituted for the established Gaussian mode times.

For a multi-tau level with block width `B=2^k` and nominal lag `ell`, the exact
reference for what that estimator measures is

```text
H_B(ell) = sum_p lambda_p^2 v_p^2
           [1/B^2 sum_{u,v=0}^{B-1} a_p^(2 |ell+v-u|)].
```

The fixture also computes a direct time-origin estimate from the same six
channels and compares it with both references. Thus predictable block
averaging is separated from finite-chain statistical error.

## Numerical results

The following are from the N=8, 2,048-frame, 16-chain run. `pairs` is the
per-chain coarse pair count in the terminal exported bin; it is not an
independent sample count.

| hierarchy | exported bins | terminal lag | terminal width | terminal pairs | terminal H | block-reference H | chain SE |
|---|---:|---:|---:|---:|---:|---:|---:|
| 16×14 | 72 | 1,920 | 128 | 1 | 5.456 | 4.831 | 1.340 |
| 32×13 | 128 | 1,984 | 64 | 1 | 5.418 | 4.761 | 1.338 |
| 64×12 | 224 | 2,016 | 32 | 1 | 5.414 | 4.727 | 1.355 |
| 16×40 | 72 | 1,920 | 128 | 1 | 5.456 | 4.831 | 1.340 |

The maximum implementation-versus-empirical-block estimate error was below
`4e-15` for every hierarchy. This validates recurrence, channel weighting,
frame ordering, and final partial-block handling. The terminal analytical
block-reference discrepancy is 0.625, 0.657, and 0.688 for P=16, 32, and 64,
respectively, while the corresponding chain SE is about 1.34. This is finite
trajectory uncertainty, not evidence that the recurrence is biased.

At the earliest bins the N=8 P=16 estimate was `8.178` at lag zero versus the
exact stationary value `8.001`; its chain SE was `0.979`. The analytical block
value decreases as the block width grows, demonstrating the expected
resolution/bias tradeoff. The maximum paired hierarchy differences over
common exported lags were 0.0085 (P=32 versus P=16) and 0.0125 (P=64 versus
P=16), both below 0.08, a diagnostic 1% of the equal-time analytical scale.
This magnitude comparison is reported for context and is not a new acceptance
threshold. The configurations are not declared scientifically equivalent
solely from these broad confidence intervals.

The bounded N=32 check produced the same recurrence agreement (below `3e-14`),
with terminal widths 64, 32, and 16 for P=16, 32, and 64. Its terminal chain
SE was 7.98, 7.91, and 7.79, respectively; it has insufficient duration to
support a physical N=32 relaxation conclusion.

## Statistical interpretation

Each chain is one independent statistical cluster. Within a chain, raw
time-origin products and multi-tau coarse origins overlap in their underlying
trajectory and are correlated. The reported SE is the standard error across
the 16 independent chains, not `1/sqrt(pairs)`. Pairing all hierarchies on
identical observations makes their differences low-noise, but does not turn
the hierarchy comparison into additional independent trajectories.

The direct estimator is useful at bounded lags, while the block reference is
the correct numerical target at coarse levels. A mismatch to the instantaneous
formula at large block width is therefore expected and should not be labeled a
transport or implementation failure. Conversely, matching the block formula
does not establish adequate physical resolution when `B*dt` is comparable to
a relaxation time.

## Scientific decision

For this controlled N=8 finite trajectory, P=16, 32, and 64 preserve the same
relaxation information within the observed paired statistical spread, while
P=32/P=64 provide denser long-lag bins and smaller terminal block widths. The
traditional 16×40 setting is redundant for this duration and has the same
effective output as 16×14. It does not create extra origins or improve
terminal statistical support.

This evidence is insufficient to authorize a production hierarchy: the N=32
fixture is deliberately short, and the N=8 terminal bins have only one coarse
pair per chain. The frozen 16-origin criterion is unchanged; results below it
are diagnostic only. A later physical-chain validation must assess fit
stability, supported positive correlation beyond the required relaxation times,
and chain-level uncertainty before treating P=16 as practically equivalent for
the long-lag scientific decision.

The smallest additional validation is a user-host bounded Gaussian/N=32 run
with the same seed and channel-preserving paired design, at least 16 supported
coarse origins in the fitting region and enough independent chains to reduce
the terminal chain SE. No GPU command is required for the current audit.
