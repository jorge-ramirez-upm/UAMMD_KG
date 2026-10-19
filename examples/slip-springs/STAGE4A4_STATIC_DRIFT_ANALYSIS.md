# Stage 4A.4 — Static convergence and equilibrium drift analysis

Status: read-only analysis of the four completed N=8 double-precision screens in `/tmp/stage4a4-timestep-preflight.GkS8wI`. No simulation, output, model, or acceptance threshold was changed.

## Method and provenance

The analysis uses `tests/stage4a4_static_drift_analysis.py` and the exact independent-equilibrium reference reports created during the screen (65,536 reference chains, seed 440401). Each simulation has 512 chains, `T=20`, and scalar spacing 0.01. It averages each chain over `0 <= t < 10` and `10 < t <= 20`, omitting the common midpoint so both halves contain exactly 1,000 frames per chain. Chain means—not frames, bonds, or time origins—are the statistical clusters.

The reported drift SE is the SE of the within-chain second-minus-first difference. The cross-timestep SE is deliberately conservative and unpaired: within a kappa pair the initial-coordinate SHA-256 files are identical and seeds match, but different step counts do not establish a common Brownian path. The script records this identity but does not claim variance reduction from it. Mean per-chain lag-one correlations range from 0.50 to 0.98, directly confirming that successive scalar frames cannot be treated as independent.

Input scalar SHA-256 values are `0233e8…7f9ca` (kappa=0, small dt), `d729b2…69068` (kappa=0, large dt), `d7cd58…cae46` (kappa=10, small dt), and `32c902…d8ed` (kappa=10, large dt). The corresponding kappa=0 and kappa=10 exact-reference JSON hashes are `3a5326…251c7` and `4e767b…1231a`.

`F/S` below means first/second-half chain-cluster mean plus SE. `drift z` is `(S-F)/SE(S-F)`; `dt z` is the conservative large-minus-small second-half difference divided by unpaired SE. The reference’s own independent-chain SE is retained. The established 1% bond-moment and 2% size/tangent tolerance remains unchanged; a pass requires the pre-registered upper three-SE bound, not merely a small point estimate.

## kappa = 0

| observable | exact reference | dt=2.5e-5 F / S | dt=1e-3 F / S | drift z small / large | dt z |
|---|---:|---:|---:|---:|---:|
| mean r | 1.06454 ± .00025 | 1.06436 ± .00027 / 1.06512 ± .00028 | 1.06441 ± .00027 / 1.06451 ± .00026 | 2.04 / .30 | -1.61 |
| mean r² | 1.16456 ± .00053 | 1.16416 ± .00058 / 1.16586 ± .00059 | 1.16539 ± .00058 / 1.16553 ± .00057 | 2.10 / .20 | -.40 |
| Re² | 9.26876 ± .02796 | 9.04843 ± .14637 / 9.48176 ± .14451 | 9.12882 ± .14139 / 9.10074 ± .14448 | 2.22 / -.15 | -1.86 |
| Rg² | 1.72221 ± .00304 | 1.69518 ± .01657 / 1.74785 ± .01646 | 1.71172 ± .01620 / 1.70118 ± .01633 | 2.39 / -.50 | -2.01 |
| tangent(1) | -.00064 ± .00085 | -.00225 ± .00300 / .00375 ± .00298 | -.00106 ± .00297 / -.00363 ± .00285 | 1.49 / -.65 | -1.79 |
| tangent(2) | .00037 ± .00092 | -.00568 ± .00282 / .00343 ± .00293 | -.00221 ± .00299 / -.00513 ± .00295 | 2.29 / -.72 | -2.06 |
| tangent(3) | -.00138 ± .00101 | -.00471 ± .00302 / .00377 ± .00286 | -.00130 ± .00276 / -.00221 ± .00301 | 2.13 / -.23 | -1.44 |
| tangent(4) | -.00042 ± .00112 | -.00763 ± .00293 / -.00139 ± .00306 | -.00454 ± .00289 / -.00305 ± .00315 | 1.50 / .36 | -.38 |

Bond moments and tangents pass their registered bounds in both halves. `Re²` and `Rg²` are unresolved for both timesteps because 512 chain means leave the three-SE bound wider than the 2% criterion. The small-dt size drift is only 2.2--2.4 SE and reverses/no longer appears at `dt=1e-3`; that pattern does not support monotonic finite-timestep bias. The approximately two-SE cross-dt size/tangent differences are likewise not decisive under the conservative comparison. The flexible deviations are best described as finite-chain/finite-trajectory uncertainty, with a possible modest temporal fluctuation, not evidence that either timestep is statically accurate or inaccurate on size observables.

## kappa = 10

| observable | exact reference | dt=2.5e-5 F / S | dt=1e-3 F / S | drift z small / large | dt z |
|---|---:|---:|---:|---:|---:|
| mean r | 1.06447 ± .00024 | 1.06466 ± .00053 / 1.06501 ± .00054 | 1.06649 ± .00053 / 1.06689 ± .00051 | .46 / .56 | 2.53 |
| mean r² | 1.16430 ± .00052 | 1.16483 ± .00114 / 1.16556 ± .00115 | 1.16967 ± .00114 / 1.17048 ± .00110 | .44 / .53 | 3.10 |
| Re² | 56.33723 ± .04368 | 56.09790 ± .19401 / 56.19023 ± .18346 | 56.31636 ± .18052 / 56.40296 ± .17664 | .35 / .36 | .84 |
| Rg² | 6.42838 ± .00384 | 6.41430 ± .01498 / 6.42681 ± .01432 | 6.43564 ± .01417 / 6.44329 ± .01375 | .61 / .41 | .83 |
| tangent(1) | .89982 ± .00015 | .89950 ± .00034 / .89973 ± .00033 | .89686 ± .00031 / .89707 ± .00031 | .49 / .50 | -5.82 |
| tangent(2) | .80988 ± .00034 | .80824 ± .00122 / .80884 ± .00117 | .80740 ± .00112 / .80788 ± .00111 | .37 / .31 | -.60 |
| tangent(3) | .72887 ± .00059 | .72518 ± .00253 / .72648 ± .00240 | .72607 ± .00230 / .72641 ± .00228 | .39 / .11 | -.02 |
| tangent(4) | .65641 ± .00085 | .64999 ± .00402 / .65171 ± .00379 | .65268 ± .00366 / .65280 ± .00362 | .32 / .02 | .21 |

There is no detectable half-to-half equilibrium drift for kappa=10 (all absolute drift z below 0.7). In contrast, `dt=1e-3` persistently raises mean r by about 0.0024 and mean r² by about 0.0062 in the second half; the conservative cross-dt contrasts are 2.53 and 3.10 SE. Most notably tangent(1) is lower by `0.00265 ± 0.00046` (5.82 SE). This is measured timestep-dependent change, not an equilibration transient. Its magnitude is about 0.29% of the exact tangent(1), and its three-SE comparison with the exact equilibrium reference remains below the frozen 2% tolerance. All currently emitted kappa=10 means/tangents therefore pass the pre-registered static screen, while the effect must be carried into dynamic validation rather than described as absence of bias.

## Interpretation and next step

The four trajectories establish neither a final larger production timestep nor a need to reduce `dt=1e-3` immediately. For kappa=0, add independent-chain information (more chains or independent replicas at the same physical duration) before deciding size-observable static convergence; more scalar frames from the same chains are not the needed remedy. For kappa=10, the evidence supports proceeding to the bounded dynamic-timestep comparison of the existing protocol, explicitly testing whether the detectable local-tangent and bond-moment shifts propagate to short-time stress relaxation and the `H(0)/e` crossing.

Final static acceptance remains incomplete because the current output contract does not provide the required dynamic energy, local-angle-distribution, and end-to-end-distribution comparisons. That limitation is preserved rather than worked around by changing the simulator or weakening a threshold.
