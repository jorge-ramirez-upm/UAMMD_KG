# Stage 4A.3c — Analytical Multi-Tau Resolution Study

This is a deterministic CPU-only resolution study. It evaluates the exact
stationary Gaussian Euler–Maruyama stress correlation and the exact correlation
of the block-averaged observations emitted by the existing multi-tau hierarchy.
No stochastic trajectory, GPU simulation, production executable, or frozen
campaign was run.

## Reproduction

```text
python3 -m unittest discover -s examples/slip-springs/tests \
  -p 'test_analytical_multitau_resolution.py'
python3 examples/slip-springs/tests/analytical_multitau_resolution.py
```

The calculation is implemented in
`tests/analytical_multitau_resolution.py`. It uses stable geometric sums and
never constructs a block-width-by-block-width matrix. The tests also verify
the exact width-one limit and finite-support lag construction.

## Reference and timescales

For `M=N+1`, the free-end Gaussian spectrum is

```text
lambda_p = 12 sin^2[p pi/(2M)],  p=1,...,N.
```

With `h=0.000025`, `a_p=1-lambda_p h` and
`v_p=1/(lambda_p(1-lambda_p h/2))`, the stationary six-channel isotropic
stress correlation is

```text
H(n) = sum_p lambda_p^2 v_p^2 a_p^(2n).
```

The channel normalization is independently retained as
`(Cxy+Cxz+Cyz)/5 + (Cxx_yy+Cxx_zz+Cyy_zz)/30`; normal-difference channels
carry their full Wick factor. For a block width `B=2^k` and nominal lag `ell`,
the exact exported-bin value is

```text
H_B(ell) = sum_p lambda_p^2 v_p^2 a_p^(2ell)
           * mean_u(a_p^(-2u)) * mean_v(a_p^(2v)),
```

with `u,v=0,...,B-1`. This is evaluated with geometric-series ratios, including
the positive-lag coarse bins; no instantaneous approximation is made.

The slowest Gaussian stress time is `tau=1/(2 lambda_1)`:

| model | tau | 4 tau | 10 tau |
|---|---:|---:|---:|
| N=8 | 1.381809895 | 5.527239580 | 13.81809895 |
| N=32 | 18.40369002 | 73.61476006 | 184.0369002 |

The N=32 value is derived from the Gaussian mode spectrum. It is not the
nonlinear rigid-rod planning estimate of 565.

## Hierarchy and finite-support protocol

The common analytical horizon is 10 tau. The corresponding every-step frame
counts are 552,725 for N=8 and 7,361,478 for N=32 (including step zero).
Configurations are P=16,L=24; P=32,L=23; P=64,L=22, plus historical P=16,L=40.
The level-40 reference is intentionally retained even though the finite
observation window cannot populate most of those levels.

The lag grid follows the implementation exactly: level zero exports offsets
0..P-1, coarser levels export P/2..P-1, and the deepest populated level is not
exported. Incomplete blocks are not forwarded. “Supported” below means the
existing conservative condition of at least 16 complete coarse-level origins;
nominal reach without that condition is not treated as scientific support. The
origin count for a bin at offset `j` and width `B` is exactly
`floor(frames/B)-j`; it is not the count of the level's terminal offset.

## N=8 results

| hierarchy | exported bins to 10 tau | bins to 4 tau | max width / tau through 4 tau | max lag gap / tau through 4 tau | supported max lag |
|---|---:|---:|---:|---:|---:|
| 16×24 | 128 | 126 | 0.2964 | 0.2964 | 6.144 |
| 32×23 | 242 | 235 | 0.1482 | 0.1482 | 6.9632 |
| 64×22 | 468 | 438 | 0.0741 | 0.0741 | 10.4448 |
| 16×40 | 128 | 126 | 0.2964 | 0.2964 | 6.144 |

The maximum normalized systematic block error through 4 tau (normalized by
`max(H(ell),H(0))`, avoiding unstable tail ratios) was 4.46e-4, 1.11e-4,
and 2.78e-5 for P=16, 32, and 64. The corresponding values through 10 tau
are reported by the reproducible JSON output and remain deterministic; no
sampling uncertainty is present. A relative error normalized by `H(ell)` is
also computed per bin by the fixture, but is intentionally not used in the
terminal tail summary because it diverges as H approaches zero.

A log-linear terminal diagnostic fit over tau..4 tau gave relaxation times
1.3668 (P=16), 1.3625 (P=32), and 1.3626 (P=64), versus the exact 1.3818.
The instantaneous-grid fits were 1.3632, 1.3615, and 1.3624. These are
diagnostic fit sensitivities, not new acceptance thresholds. P=16 has fewer
terminal points and a coarser maximum gap; P=32 and P=64 materially improve
lag density even though the block bias is already small through 4 tau.

## N=32 results

| hierarchy | exported bins to 10 tau | bins to 4 tau | max width / tau through 4 tau | max lag gap / tau through 4 tau | supported max lag |
|---|---:|---:|---:|---:|---:|
| 16×24 | 157 | 156 | 0.3561 | 0.3561 | 78.6432 |
| 32×23 | 304 | 295 | 0.1781 | 0.1781 | 101.5808 |
| 64×22 | 585 | 557 | 0.0890 | 0.0890 | 131.0720 |
| 16×40 | 157 | 156 | 0.3561 | 0.3561 | 78.6432 |

Maximum normalized block error through 4 tau was 4.37e-4, 1.09e-4, and
2.73e-5 for P=16, 32, and 64. Terminal log-linear diagnostics gave 18.2705,
18.1989, and 18.1756 versus the exact 18.4037. The P=16 horizon does not
provide 16-origin support all the way to 10 tau: its supported lag ends at
78.64, below 184.04. P=32 and P=64 extend farther, but their 16-origin
supported limits are still 101.58 and 131.07; the nominal 10-tau endpoint has
fewer supported origins.

## Interpretation

Three effects are separate:

1. **Block averaging:** deterministic and small through 4 tau for these
   configurations, but P=16's coarsest bins are wider and its error is about
   four times P=32's and sixteen times P=64's.
2. **Lag spacing:** P=16 has only 126/156 bins through 4 tau and a maximum
   normalized gap of 0.296/0.356. P=32 halves that spacing; P=64 halves it
   again. This directly affects terminal-fit stability even when pointwise
   block bias is small.
3. **Finite support:** the 16-origin rule removes late nominal bins. P=16 is
   unable to support the full N=32 10-tau endpoint at the stated duration;
   adding levels cannot manufacture origins.

The same analytical expression being evaluated for each hierarchy does not
make them numerically equivalent: they sample different block widths and lag
grids. Conversely, these calculations contain no stochastic uncertainty,
chain-to-chain uncertainty, or uncertainty in the physical nonlinear
relaxation time. Those questions require separate physical-chain validation.

## Conclusion

For Gaussian N=8, P=16 is analytically adequate for reaching 4 tau and has
16-origin support slightly beyond that point, but P=32 is a more comfortable
minimum for terminal fitting because it supplies roughly twice the lag density
and halves the coarse-bin width. P=64 adds resolution but with diminishing
deterministic benefit through 4 tau. For Gaussian N=32, P=16 has adequate
mathematical coverage to 4 tau but only reaches 4.27 tau with 16 origins;
P=32 reaches 5.52 tau and is the minimum defensible choice among these
candidates for provisional engineering, with P=64 preferred only if its memory
cost is explicitly justified by later physical uncertainty analysis. None of
the tested finite horizons supports 10 tau under the 16-origin rule.

These are analytical diagnostics, not a production hierarchy authorization.
The frozen 16-origin criterion and all scientific thresholds remain unchanged.
