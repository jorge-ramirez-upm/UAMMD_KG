# Stage 4A.4 — Dynamic timestep validation from existing trajectories

Status: read-only comparison of the four completed N=8, `T=20`, double-precision trajectories in `/tmp/stage4a4-timestep-preflight.GkS8wI`. No simulation or production code was changed.

## Method

`tests/stage4a4_dynamic_timestep_analysis.py` reads only `stress_metadata.json` and `stress_correlations.csv`. It verifies the established six-channel isotropic convention,

`H=(Cxy+Cxz+Cyz)/5+(Cxx_yy+Cxx_zz+Cyy_zz)/30`,

uses the exported chain-cluster `H_se`, and does not interpret the overlapping multi-tau origins as independent observations. Across timesteps it propagates errors as unpaired. The matching initial-coordinate hashes and seed are recorded evidence of common initialization, but different timestep indices do not establish a common Brownian path.

At 0.01 the selected bins are exact. At requested 0.05 and 0.10 the small-timestep hierarchy supplies 0.0496 and 0.0992 respectively; these offsets are within half of the exported block width (0.0016 and 0.0032). No interpolation was used. The large-timestep lags are exact. Thus the small block-average width differs modestly from the large one, is disclosed below, and is not mislabelled as an instantaneous-correlation discrepancy.

The prior duration-200 small-timestep outputs were inspected only for provenance: they reuse the same initial coordinates and seed and their correlations accumulate over the full `T=200`. They are neither independent replicas nor equal-duration comparators, so they were not used in a gate.

## Equilibrium amplitude and fixed-lag gates

The gate is the prospective rule `|H_large-H_small|+3 SE_unpaired <= 0.05 H_small(0)`. Normalized values use conservative independent propagation of lag and zero-lag SE. All origin counts are per chain.

### kappa = 0

`H(0)` is `25.1333 ± 0.0501` (small dt) and `25.8412 ± 0.0497` (large dt): an amplitude increase of `0.7079 ± 0.0705` (10.0 unpaired SE). This is a real stress-variance difference, distinct from relaxation shape.

| target | small H / H/H0 | large H / H/H0 | small / large actual lag; width; origins | `|ΔH|+3SE` / gate | result |
|---:|---:|---:|---:|---:|---|
| .01 | 14.6857 / .58431 | 14.8071 / .57300 | .0100/.0100; .0004/.0010; 49975/19991 | .3309 / 1.2567 | pass |
| .05 | 5.2273 / .20798 | 5.1781 / .20038 | .0496/.0500; .0016/.0020; 12469/9975 | .2367 / 1.2567 | pass |
| .10 | 3.3564 / .13354 | 3.3502 / .12965 | .0992/.1000; .0032/.0040; 6219/4975 | .1732 / 1.2567 | pass |

The normalized large-minus-small differences are `-.01131 ± .00318`, `-.00760 ± .00252`, and `-.00390 ± .00222`; the shape is slightly faster at the large timestep, but the specified raw-correlation gate passes at all lags.

The linear 1/e crossings are 0.022079 (small) and 0.021193 (large), a difference of -0.000886 (-4.0%). Conservative three-SE intervals are [0.021772, 0.022385] and [0.020908, 0.021483]. The conservative difference bound is 0.001483, below the 10% allowance 0.002208: **pass**.

### kappa = 10

`H(0)` is `27.0735 ± 0.1218` (small dt) and `27.8815 ± 0.1223` (large dt): an amplitude increase of `0.8079 ± 0.1727` (4.68 unpaired SE).

| target | small H / H/H0 | large H / H/H0 | small / large actual lag; width; origins | `|ΔH|+3SE` / gate | result |
|---:|---:|---:|---:|---:|---|
| .01 | 20.4244 / .75441 | 20.7347 / .74367 | .0100/.0100; .0004/.0010; 49975/19991 | .8258 / 1.3537 | pass |
| .05 | 13.4646 / .49734 | 13.6036 / .48791 | .0496/.0500; .0016/.0020; 12469/9975 | .6400 / 1.3537 | pass |
| .10 | 9.9748 / .36843 | 10.0711 / .36121 | .0992/.1000; .0032/.0040; 6219/4975 | .5768 / 1.3537 | pass |

The normalized differences are `-.01073 ± .00783`, `-.00943 ± .00682`, and `-.00722 ± .00627`. Therefore the detected static tangent(1) shift does not produce a resolved fixed-lag shape change under this conservative analysis. It does coincide with a resolved variance increase and a central tendency toward faster normalized relaxation.

The 1/e crossings are 0.099493 (small) and 0.096516 (large), a central difference of -0.002978 (-3.0%). Their three-SE intervals are [0.095596, 0.103500] and [0.092724, 0.100383]. The conservative difference bound is 0.010851, which exceeds the 10% allowance 0.009949: **unresolved**, not pass. Both crossings are bracketed and have thousands of coarse origins per chain, but their chain-level uncertainty prevents the prescribed accuracy conclusion.

## Six-channel contributions

Each cell is the weighted contribution `w_i*(C_i large-C_i small) ±` its conservative unpaired SE. Component errors are correlated, so they must not be quadrature-summed; the directly exported `H_se` above is used for the gate.

### kappa = 0

| channel contribution | H(0) | .01 | .05 | .10 |
|---|---:|---:|---:|---:|
| Cxy/5 | +.1133 ± .0277 | -.0009 ± .0255 | -.0265 ± .0220 | -.0173 ± .0204 |
| Cxz/5 | +.1264 ± .0263 | +.0099 ± .0244 | -.0175 ± .0213 | -.0151 ± .0201 |
| Cyz/5 | +.1461 ± .0268 | +.0215 ± .0246 | -.0202 ± .0211 | +.0009 ± .0193 |
| Cxx_yy/30 | +.1024 ± .0180 | +.0204 ± .0164 | -.0055 ± .0137 | +.0008 ± .0126 |
| Cxx_zz/30 | +.1139 ± .0177 | +.0425 ± .0160 | +.0139 ± .0137 | +.0225 ± .0125 |
| Cyy_zz/30 | +.1058 ± .0179 | +.0280 ± .0166 | +.0066 ± .0141 | +.0021 ± .0133 |

### kappa = 10

| channel contribution | H(0) | .01 | .05 | .10 |
|---|---:|---:|---:|---:|
| Cxy/5 | +.1851 ± .1168 | +.0823 ± .1089 | +.0444 ± .0940 | +.0280 ± .0819 |
| Cxz/5 | +.0421 ± .1223 | -.0544 ± .1139 | -.0928 ± .0975 | -.0810 ± .0838 |
| Cyz/5 | +.1939 ± .1112 | +.0947 ± .1033 | +.0594 ± .0881 | +.0475 ± .0757 |
| Cxx_yy/30 | +.1527 ± .0797 | +.0828 ± .0745 | +.0574 ± .0645 | +.0479 ± .0560 |
| Cxx_zz/30 | +.0816 ± .0759 | +.0207 ± .0706 | +.0087 ± .0606 | +.0045 ± .0526 |
| Cyy_zz/30 | +.1526 ± .0783 | +.0842 ± .0731 | +.0620 ± .0630 | +.0495 ± .0547 |

## Decision

For **kappa=0**, `dt=1e-3` is **dynamically acceptable within the stated tolerances** for the available `T=20` comparison: all fixed-lag gates and the conservative crossing gate pass. This does not erase the independent static `R_e²`/`R_g²` uncertainty.

For **kappa=10**, `dt=1e-3` is **unresolved**. All fixed-lag gates pass, and the static tangent shift has no resolved fixed-lag shape consequence, but the prescribed conservative 1/e crossing comparison cannot pass. The measured `H(0)` change should also be retained as a real amplitude effect rather than normalized away.

Selecting a production timestep still requires the missing static energy/distribution diagnostics, and for kappa=10 enough independent chains or replicas to narrow the crossing uncertainty. No threshold was changed after observing these data.
