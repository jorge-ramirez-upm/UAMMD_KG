# Stage 2A — GPU configurational stress and direct-lag validation

15 October 2026, Europe/Madrid. Stage 2A's predeclared scientific gates passed.
Stage 2B and later stages remain unimplemented and unauthorized.

## Provenance, scope and files

Fetched and independently verified origin/slip-springs before implementation:
**359a8e5a06af651218492a3cf66c95af104b1785**. Development stayed on slip-springs
in /tmp/UAMMD_KG-slip-springs, preserving the original checkout and its unrelated
KG changes. Final commit SHA/push status are supplied in the handoff (a commit
cannot contain its own SHA). No PR or merge is requested.

Modified: AGENTS.md, README.md, Makefile, rouse.cu, rouse.cuh, validate.py,
tests/rouse_tests.cu, tests/test_cli.py.
Added: stress.py, tests/test_stress.py, tests/STAGE2A_VALIDATION_PLAN.md,
STAGE2A_REPORT.md. All twelve paths are inside examples/slip-springs/.
Historical reports and the original Stage 0 smoke sources are unchanged.
UAMMD, KG and KG_Assoc remain read-only; no existing application was rebuilt.
The existing Stage 0 Correlator6 smoke remains a regression, but no Correlator6
or multi-tau integration was added to the simulator or stress analysis.

## Stress implementation and exact references

The existing per-chain GPU observation kernel accumulates the six components
xx,yy,zz,xy,xz,yz of S_ab=3 sum_i q_ia*q_ib, using double bond differences,
products and sums in both coordinate precisions. Coordinates are promoted
before bond subtraction. This preserves precision available in stored values;
it cannot recover coordinate information already lost in float. The Rouse
update, RNG and initialization routines are unchanged. There is no periodic
Box, minimum-image operation, kinetic stress or volume/density factor.

Only the per-chain Observation structure is transferred to the CPU. All six
raw tensor components are appended to samples.csv; the original columns retain
their names/order. validate.py only extracts its existing CSV loader for reuse.

For stiffness K=3L with orthonormal internal modes X_p, the chain tensor is
S_ab=sum_p lambda_p X_pa X_pb. Independent Cartesian Gaussian modes have
E[X_pa(n)^2]=v_p(n). At lag ell their covariance is v_p(n)*a_p^ell.
Wick contraction at each origin gives

    C_xy_EM(ell) = mean_n sum_p [lambda_p*v_p(n)*a_p^ell]^2
    C_(xx-yy)_EM(ell)/4 = C_xy_EM(ell)
    C_xx_EM(ell) = mean_n {m(n)*m(n+ell) + 2 sum_p [lambda_p*v_p(n)*a_p^ell]^2}
    m(n) = sum_p lambda_p*v_p(n).

Here lambda_p=12 sin^2(p*pi/[2(N+1)]), a_p=1-lambda_p*h,
v_p*=1/[lambda_p*(1-lambda_p*h/2)], and
v_p(n)=v_p*+(1/lambda_p-v_p*)*a_p^(2n). Origins include optional equilibration
steps, and h is the actual precision-rounded timestep recorded in metadata.
The origin-dependent square is taken BEFORE the origin mean. Tests explicitly
distinguish this from squaring the averaged covariance.

At continuous equilibrium, lambda_p*v_p=1 and a_p^ell is replaced by
exp(-lambda_p*t). Thus C_xy(t)=sum_p exp(-2 lambda_p*t), shear means are zero,
shear second moments are N, normal-difference second moments are4N, diagonal
means are N and raw diagonal correlations are N^2+2C_xy(t). These expressions
are derived and tested against full-matrix Gaussian/Wick calculations, not just
against another scalar mode implementation.

stress.py keeps xy,xz,yz,xx-yy,xx-zz,yy-zz separate. It represents normal
differences divided by 2 before forming products, yielding exactly 1/4 on their
raw correlations. Raw normal values/errors/references are also saved. Products
are uncentered; raw diagonals include their nonzero mean product. There is no
channel average. Isotropy uses the SE of each channel's paired per-chain
difference from xy, accounting for statistical dependence among channels.

Multiple time origins are averaged within each chain, then independent chains
supply the SE and approximate 95% interval. Overlapping origins are never
counted as independent replicates. stress_chain_contributions.npz retains
normalized contributions with axes(lag,chain,channel), raw diagonal contributions,
lag_steps, origins_per_lag, channel names and explicit chain IDs. Raw tensors
remain in CSV so every statistic can be reconstructed.

## Gates and scientific results

The plan in tests/STAGE2A_VALIDATION_PLAN.md was written before execution.
All stress gates use absolute residual <=5 SE; the planned family has fewer
than 2500 checks, with a nominal Gaussian union bound <0.0015. Actual intervals
use chain-cluster CLT estimates and are approximate; this does not imply every
individual 95% interval contains theory. No seeds/thresholds were changed.

- Initial equilibrium: N=8,32,100; 8192 independent chains; zero steps;
  dt0.005; seed20262015+N+10000*precision_index.
- Evolved: N=8,32,100; dt0.01,0.005,0.0025; 2048 independent chains;
  stride=round(0.05/dt); 64*stride steps; 65 frames; duration approximately 3.2;
  seed820000+100N+dt_index+10000*precision_index; equilibration0.
- precision_index=0/1 for float/double; dt_index=0/1/2 in the order above.
- Five direct lags: 0,1,4,16,32 sample intervals, approximately 0,0.05,0.2,0.8,1.6.
  All six normalized stress channels and three raw diagonals are checked.
- Per-channel convergence pools only independent N cases; correlated channels
  are never pooled. Coarse-to-fine bias decrease must exceed 1.96 combined SE,
  with pooled agreement against EM within 5 SE.

All **2076** stress gates passed. Maximum |z| among moments, means, direct
correlations and paired isotropy tests was **2.911**. All **324** cross-precision
residual comparisons passed; their maximum |z| was **2.648**. No scientific
failure occurred. All tested samples were finite with no collapsed bonds.

Tables report estimate +/- one SE; approximate 95% intervals are estimate
+/-1.96 SE, also saved per result in stress_analysis.json. D_ab denotes S_aa-S_bb.

### Initial moments

Each normalized moment below has exact reference N. Raw normal-difference moments and SEs are four times the displayed values (exact 4N). All nine mean-stress checks per case also passed.

| bits | N | Sxy² | Sxz² | Syz² | Dxy²/4 | Dxz²/4 | Dyz²/4 |
|---|---|---|---|---|---|---|---|
| 32 | 8 | 8.10777 +/- 0.15471 | 8.14423 +/- 0.15385 | 8.06349 +/- 0.15424 | 8.08667 +/- 0.14262 | 8.18746 +/- 0.14957 | 8.07959 +/- 0.14745 |
| 32 | 32 | 31.86057 +/- 0.52819 | 32.30486 +/- 0.53263 | 31.93532 +/- 0.52113 | 31.98294 +/- 0.52939 | 32.40466 +/- 0.52820 | 32.43836 +/- 0.51940 |
| 32 | 100 | 95.81245 +/- 1.53285 | 99.41079 +/- 1.54614 | 99.68324 +/- 1.54375 | 97.61096 +/- 1.51185 | 100.37675 +/- 1.59655 | 98.30332 +/- 1.57510 |
| 64 | 8 | 8.02430 +/- 0.15334 | 8.24870 +/- 0.14834 | 7.96796 +/- 0.14520 | 8.07591 +/- 0.15405 | 8.02596 +/- 0.14397 | 8.04125 +/- 0.14954 |
| 64 | 32 | 31.69897 +/- 0.52036 | 32.01936 +/- 0.52660 | 31.37485 +/- 0.50315 | 30.67716 +/- 0.49497 | 31.43047 +/- 0.51343 | 31.55152 +/- 0.51601 |
| 64 | 100 | 99.25259 +/- 1.59772 | 100.00994 +/- 1.56693 | 100.89191 +/- 1.61467 | 97.79311 +/- 1.56812 | 99.14102 +/- 1.57519 | 99.56813 +/- 1.58338 |

### Evolved moments and finite-step bias

Each six-channel row is compared with its exact transient EM second-moment reference. The same reference applies to all normalized channels. Continuous equilibrium would give N.

Shears:

| bits | N | h | EM reference | Sxy² | Sxz² | Syz² |
|---|---|---|---|---|---|---|
| 32 | 8 | 0.01 | 8.49622 | 8.40581 +/- 0.07125 | 8.46009 +/- 0.07079 | 8.44938 +/- 0.07235 |
| 32 | 8 | 0.005 | 8.23969 | 8.07460 +/- 0.06750 | 8.23230 +/- 0.07191 | 8.18480 +/- 0.06869 |
| 32 | 8 | 0.0025 | 8.11784 | 8.15569 +/- 0.07509 | 8.14555 +/- 0.07439 | 8.15646 +/- 0.08121 |
| 32 | 32 | 0.01 | 33.99123 | 34.05038 +/- 0.25458 | 34.02453 +/- 0.25674 | 33.63979 +/- 0.25748 |
| 32 | 32 | 0.005 | 32.96074 | 33.40789 +/- 0.26891 | 32.89803 +/- 0.24300 | 32.77464 +/- 0.25754 |
| 32 | 32 | 0.0025 | 32.47209 | 32.18568 +/- 0.24159 | 32.52118 +/- 0.24906 | 32.60379 +/- 0.25432 |
| 32 | 100 | 0.01 | 106.22719 | 106.17295 +/- 0.75949 | 106.77759 +/- 0.78408 | 106.66938 +/- 0.73829 |
| 32 | 100 | 0.005 | 103.00375 | 102.62993 +/- 0.74959 | 102.07745 +/- 0.73849 | 102.71517 +/- 0.73929 |
| 32 | 100 | 0.0025 | 101.47581 | 101.77241 +/- 0.75632 | 102.15302 +/- 0.73802 | 101.17111 +/- 0.74053 |
| 64 | 8 | 0.01 | 8.49622 | 8.47085 +/- 0.07561 | 8.47496 +/- 0.07711 | 8.48013 +/- 0.07073 |
| 64 | 8 | 0.005 | 8.23969 | 8.26235 +/- 0.07554 | 8.24251 +/- 0.06994 | 8.32005 +/- 0.07056 |
| 64 | 8 | 0.0025 | 8.11784 | 8.20154 +/- 0.07282 | 8.06571 +/- 0.07160 | 8.16362 +/- 0.07120 |
| 64 | 32 | 0.01 | 33.99123 | 34.17783 +/- 0.24888 | 33.82147 +/- 0.27643 | 34.07559 +/- 0.26803 |
| 64 | 32 | 0.005 | 32.96074 | 33.21506 +/- 0.26013 | 32.95749 +/- 0.25342 | 33.32465 +/- 0.25592 |
| 64 | 32 | 0.0025 | 32.47209 | 32.35522 +/- 0.25422 | 32.47551 +/- 0.24396 | 32.41189 +/- 0.25633 |
| 64 | 100 | 0.01 | 106.22719 | 105.43234 +/- 0.74005 | 105.07041 +/- 0.72184 | 105.12643 +/- 0.76112 |
| 64 | 100 | 0.005 | 103.00375 | 103.02889 +/- 0.70654 | 102.04748 +/- 0.75653 | 102.96095 +/- 0.76070 |
| 64 | 100 | 0.0025 | 101.47581 | 102.06944 +/- 0.76781 | 101.81223 +/- 0.76980 | 101.46588 +/- 0.74833 |

Normal differences, normalized by4:

| bits | N | h | EM reference | Dxy²/4 | Dxz²/4 | Dyz²/4 |
|---|---|---|---|---|---|---|
| 32 | 8 | 0.01 | 8.49622 | 8.33879 +/- 0.06826 | 8.40970 +/- 0.06898 | 8.41637 +/- 0.06772 |
| 32 | 8 | 0.005 | 8.23969 | 8.07995 +/- 0.06925 | 8.13789 +/- 0.07053 | 8.15837 +/- 0.07095 |
| 32 | 8 | 0.0025 | 8.11784 | 8.04164 +/- 0.07224 | 8.19709 +/- 0.07824 | 8.18229 +/- 0.07412 |
| 32 | 32 | 0.01 | 33.99123 | 34.29650 +/- 0.26170 | 34.36231 +/- 0.26252 | 33.87433 +/- 0.24957 |
| 32 | 32 | 0.005 | 32.96074 | 33.09126 +/- 0.25333 | 33.14201 +/- 0.25826 | 33.08154 +/- 0.26275 |
| 32 | 32 | 0.0025 | 32.47209 | 32.77392 +/- 0.25057 | 32.34846 +/- 0.24935 | 32.64990 +/- 0.24946 |
| 32 | 100 | 0.01 | 106.22719 | 108.31185 +/- 0.76871 | 107.01949 +/- 0.77454 | 106.28155 +/- 0.74155 |
| 32 | 100 | 0.005 | 103.00375 | 102.17034 +/- 0.74876 | 102.64188 +/- 0.75341 | 103.51060 +/- 0.74473 |
| 32 | 100 | 0.0025 | 101.47581 | 101.01128 +/- 0.71301 | 100.96407 +/- 0.74609 | 102.38165 +/- 0.77683 |
| 64 | 8 | 0.01 | 8.49622 | 8.44371 +/- 0.07264 | 8.40425 +/- 0.06989 | 8.47549 +/- 0.07257 |
| 64 | 8 | 0.005 | 8.23969 | 8.14088 +/- 0.07119 | 8.14703 +/- 0.06980 | 8.18421 +/- 0.06831 |
| 64 | 8 | 0.0025 | 8.11784 | 8.03255 +/- 0.06535 | 7.97903 +/- 0.06889 | 8.09742 +/- 0.07116 |
| 64 | 32 | 0.01 | 33.99123 | 34.10052 +/- 0.25722 | 34.13599 +/- 0.26061 | 33.71641 +/- 0.25037 |
| 64 | 32 | 0.005 | 32.96074 | 32.73451 +/- 0.25469 | 32.88016 +/- 0.25164 | 32.48202 +/- 0.23903 |
| 64 | 32 | 0.0025 | 32.47209 | 33.21562 +/- 0.25545 | 32.81585 +/- 0.26309 | 32.44565 +/- 0.25390 |
| 64 | 100 | 0.01 | 106.22719 | 106.03421 +/- 0.72702 | 105.28805 +/- 0.73604 | 105.20784 +/- 0.73708 |
| 64 | 100 | 0.005 | 103.00375 | 102.68013 +/- 0.72892 | 102.19431 +/- 0.70470 | 103.63491 +/- 0.73275 |
| 64 | 100 | 0.0025 | 101.47581 | 100.21633 +/- 0.72381 | 101.20845 +/- 0.74300 | 100.58596 +/- 0.73824 |

### Direct relaxation at nonzero lags

Sxy correlation shown as estimate +/- SE (exact transient EM reference). Zero lag is the Sxy² table above. All other five normalized channels and all raw diagonal correlations passed at every listed lag; their full values and paired-channel checks are in each stress_analysis.json. Continuous references are saved separately.

| bits | N | h | t≈0.05 | t≈0.2 | t≈0.8 | t≈1.6 |
|---|---|---|---|---|---|---|
| 32 | 8 | 0.01 | 4.78241 +/- 0.06673 (4.86712) | 1.90055 +/- 0.05938 (1.98699) | 0.57736 +/- 0.05183 (0.67454) | 0.30962 +/- 0.05405 (0.32497) |
| 32 | 8 | 0.005 | 4.64434 +/- 0.06258 (4.80493) | 1.88150 +/- 0.05677 (1.98638) | 0.55822 +/- 0.05049 (0.67473) | 0.22244 +/- 0.05133 (0.32519) |
| 32 | 8 | 0.0025 | 4.81451 +/- 0.07041 (4.77405) | 2.01577 +/- 0.06287 (1.98597) | 0.72935 +/- 0.05557 (0.67482) | 0.37452 +/- 0.05578 (0.32530) |
| 32 | 32 | 0.01 | 19.59326 +/- 0.24241 (19.59854) | 8.36992 +/- 0.22596 (8.62790) | 3.80048 +/- 0.22436 (3.80652) | 2.67713 +/- 0.22990 (2.52302) |
| 32 | 32 | 0.005 | 19.76032 +/- 0.25745 (19.36192) | 8.85484 +/- 0.24101 (8.62668) | 4.06468 +/- 0.23298 (3.80727) | 2.73364 +/- 0.25009 (2.52385) |
| 32 | 32 | 0.0025 | 18.93096 +/- 0.23265 (19.24426) | 8.34766 +/- 0.22141 (8.62568) | 3.59781 +/- 0.21825 (3.80764) | 2.33039 +/- 0.22519 (2.52426) |
| 32 | 100 | 0.01 | 61.40474 +/- 0.72324 (61.33763) | 27.89538 +/- 0.68089 (27.44390) | 13.53133 +/- 0.68139 (12.68057) | 8.61763 +/- 0.72115 (8.75226) |
| 32 | 100 | 0.005 | 60.45710 +/- 0.72502 (60.60677) | 27.87150 +/- 0.67112 (27.44092) | 11.71379 +/- 0.64763 (12.68286) | 8.03962 +/- 0.70135 (8.75480) |
| 32 | 100 | 0.0025 | 60.86573 +/- 0.73636 (60.24321) | 28.15739 +/- 0.68780 (27.43823) | 12.63672 +/- 0.66740 (12.68399) | 8.94566 +/- 0.72712 (8.75607) |
| 64 | 8 | 0.01 | 4.84702 +/- 0.07083 (4.86712) | 1.98662 +/- 0.06250 (1.98699) | 0.69448 +/- 0.05486 (0.67454) | 0.32515 +/- 0.05642 (0.32497) |
| 64 | 8 | 0.005 | 4.81259 +/- 0.07006 (4.80493) | 2.00107 +/- 0.06235 (1.98638) | 0.73660 +/- 0.05645 (0.67473) | 0.30998 +/- 0.05693 (0.32519) |
| 64 | 8 | 0.0025 | 4.84953 +/- 0.06877 (4.77405) | 2.06924 +/- 0.06132 (1.98597) | 0.62248 +/- 0.05407 (0.67482) | 0.36811 +/- 0.05514 (0.32530) |
| 64 | 32 | 0.01 | 19.77107 +/- 0.23611 (19.59854) | 8.65590 +/- 0.22180 (8.62790) | 3.72129 +/- 0.22143 (3.80652) | 2.71603 +/- 0.23493 (2.52302) |
| 64 | 32 | 0.005 | 19.56011 +/- 0.24921 (19.36192) | 8.79171 +/- 0.23471 (8.62668) | 3.87408 +/- 0.22629 (3.80727) | 2.43081 +/- 0.24382 (2.52385) |
| 64 | 32 | 0.0025 | 19.05094 +/- 0.24328 (19.24426) | 8.49099 +/- 0.22345 (8.62568) | 3.50093 +/- 0.21020 (3.80764) | 2.17527 +/- 0.23271 (2.52426) |
| 64 | 100 | 0.01 | 60.89061 +/- 0.71519 (61.33763) | 26.89078 +/- 0.68998 (27.44390) | 13.07951 +/- 0.70402 (12.68057) | 9.24608 +/- 0.70864 (8.75226) |
| 64 | 100 | 0.005 | 60.47366 +/- 0.67702 (60.60677) | 27.40175 +/- 0.63183 (27.44092) | 12.45002 +/- 0.64389 (12.68286) | 8.69273 +/- 0.67718 (8.75480) |
| 64 | 100 | 0.0025 | 60.67415 +/- 0.74504 (60.24321) | 28.18944 +/- 0.70293 (27.43823) | 13.54521 +/- 0.67960 (12.68399) | 9.15036 +/- 0.71760 (8.75607) |

### Timestep convergence, with channels kept separate

Fractional bias of the second moment relative to continuous equilibrium N, pooled across independent N cases. Exact transient EM predicts approximately6.219%,3.001%,1.475% as h decreases; exact channel-specific weighting and predictions are retained in summary.json.

| bits | channel | h0.01 bias +/- SE | h0.005 bias +/- SE | h0.0025 bias +/- SE | decrease Z |
|---|---|---|---|---|---|
| 32 | xy | 0.05951 +/- 0.00468 | 0.02656 +/- 0.00466 | 0.01364 +/- 0.00464 | 6.960 |
| 32 | xz | 0.06326 +/- 0.00474 | 0.02553 +/- 0.00456 | 0.01884 +/- 0.00464 | 6.700 |
| 32 | yz | 0.05871 +/- 0.00466 | 0.02503 +/- 0.00460 | 0.01604 +/- 0.00478 | 6.392 |
| 32 | xx-yy | 0.06712 +/- 0.00468 | 0.02258 +/- 0.00461 | 0.01362 +/- 0.00455 | 8.191 |
| 32 | xx-zz | 0.06572 +/- 0.00472 | 0.02695 +/- 0.00467 | 0.01359 +/- 0.00472 | 7.813 |
| 32 | yy-zz | 0.05829 +/- 0.00454 | 0.03041 +/- 0.00468 | 0.02226 +/- 0.00473 | 5.497 |
| 64 | xy | 0.06036 +/- 0.00466 | 0.03340 +/- 0.00464 | 0.01852 +/- 0.00472 | 6.307 |
| 64 | xz | 0.05478 +/- 0.00480 | 0.02648 +/- 0.00464 | 0.01426 +/- 0.00463 | 6.071 |
| 64 | yz | 0.05817 +/- 0.00475 | 0.03656 +/- 0.00467 | 0.01564 +/- 0.00466 | 6.391 |
| 64 | xx-yy | 0.06083 +/- 0.00464 | 0.02306 +/- 0.00460 | 0.01403 +/- 0.00448 | 7.257 |
| 64 | xx-zz | 0.05670 +/- 0.00463 | 0.02282 +/- 0.00450 | 0.01209 +/- 0.00464 | 6.804 |
| 64 | yy-zz | 0.05453 +/- 0.00462 | 0.02512 +/- 0.00446 | 0.01030 +/- 0.00462 | 6.772 |

All twelve channels/precisions resolve the coarse-to-fine decrease at **5.497–8.191 SE**. This is integration bias, not evidence of a floating-point defect. Continuous and EM references are not interchangeable for evolved stresses.

## Permanent measured performance

The final report printed by every successful simulation includes chains, N,
beads/chain, total beads, production steps/physical time, GPU seconds,
integration ns/bead/step and bead updates/s, production wall seconds and overall
ns/bead/step, sampling/recurrent transfer, recurrent CSV and final data-output
seconds, initialization and optional equilibration wall/GPU seconds.

Timing schema2 defines the denominator as total_beads*production_steps. GPU
seconds are measured by CUDA events around integration chunks, including launch
gaps between events, excluding sampling and the host synchronization wait.
Production wall time includes synchronization, the initial observation,
subsequent sampling/D2H and recurrent CSV formatting/writing. It excludes
System/CUDA context initialization, all other initialization, equilibration and
final CSV flush/close. Initialization includes measured System/context time,
which is also saved separately. Final-data timing is the actual CSV flush/close;
most CSV I/O occurs recurrently and is disclosed separately rather than hidden.
Metadata serialization/closing, terminal logging and shutdown are telemetry or
teardown outside these intervals. Buffered OS I/O is measured, not fsync-backed
disk durability. Stage 1's broader schema1 timing scopes remain historical.

integration_ns_per_bead_step=1e9*update_seconds/(total_beads*production_steps),
overall_ns_per_bead_step uses production_seconds with the same denominator.
The reciprocal GPU throughput uses actual measured update_seconds. Zero-step
runs, including those with optional equilibration, have update_seconds=0 and
null/N/A integration/overall costs and throughput, with sampling and equilibration
still reported. Tests verify these cases and the rate arithmetic identities.

Measured on RTX 3060 Ti, CUDA 13.0.88, driver 580.178.04, g++ 11.4.0, NumPy 2.2.4. The fixed probe has N31, C2048, 65,536 beads, 2000 steps, h0.005, sample2000, seed991027. Short examples have N8, C256, 2304 beads, 200 steps, h0.005, sample10 and seeds240008/240009; moderate has N32, C512, 16,896 beads, 20,000 steps, h0.005, sample20, seed240032. All have equilibration0.

| case | bits | GPU seconds | GPU ns/bead/step | bead updates/s | production seconds | overall ns/bead/step | sampling/D2H seconds | recurrent CSV seconds | final flush seconds |
|---|---|---|---|---|---|---|---|---|---|
| probe | 32 | 0.00867629 | 0.066195 | 1.510692e+10 | 0.02731647 | 0.208408 | 0.00036423 | 0.01826945 | 0.00001281 |
| probe | 64 | 0.18575142 | 1.417171 | 7.056312e+08 | 0.20424017 | 1.558229 | 0.00034562 | 0.01813853 | 0.00001245 |
| short | 32 | 0.00051155 | 1.110139 | 9.007882e+08 | 0.02395038 | 51.975655 | 0.00123723 | 0.02212232 | 0.00001193 |
| short | 64 | 0.00322778 | 7.004722 | 1.427608e+08 | 0.02650995 | 57.530276 | 0.00112604 | 0.02207797 | 0.00001164 |
| moderate | 32 | 0.05638595 | 0.166862 | 5.992982e+09 | 2.58482453 | 7.649220 | 0.16883457 | 2.35564907 | 0.00001428 |

These are bounded measured examples, not Stage 3 optimization or a production benchmark. Small ensembles are cache/launch sensitive. Recurrent CSV dominates the short/moderate float wall time; GPU-only throughput does not describe end-to-end efficiency. The probe explicit device storage is2,949,376/5,046,528 bytes for float/double; cudaMemGetInfo deltas were6,291,456/8,388,608 bytes, including allocator granularity and internal storage.

The tested fresh example parent was `/tmp/rouse-stage2a-examples.qzujwI`; its single/, double/ and moderate/ children contain all generated results. Exact copied README commands with mktemp make subsequent invocations choose fresh paths and preserve no-overwrite behavior.

## Execution evidence and regression preservation

Both precision builds compiled and executed all quick tests: preserved Stage 0
smokes, Stage 1 force/noise/observation tests, new GPU stress oracles, CPU
matrix/Wick/direct-sum/NPZ tests and CLI replay/error/timing tests. Deterministic
stress inputs cover N1,4,8, axes x/y/z, arbitrary3D, four chains, zero bonds and
exact integer translations of1,048,576. All nine entries of the reconstructed
symmetric tensor agree with an independent CPU bond outer-product loop; the
simulator itself never transfers bead coordinates for stress calculation.

The full Stage 1 suite was rerun with its original seeds and thresholds: all
**225 gates passed**, and every numerical result (dimensions, dynamics and
precision comparisons, excluding timing metadata) matches the historical
/tmp/rouse-stage1-validation-final/summary.json **exactly**. This is stronger
than merely passing new tolerances. The update, force, Philox and equilibrium
initialization code was not changed. Stage 0's existing Correlator6 smoke was
preserved; its historical leak is unchanged and irrelevant to this direct-lag
stress path.

CUDA 13 compute-sanitizer memcheck was run on N8 float and N1 double, C16,
h0.005, 17 production steps, sample4, equil3, seeds240001/240002. Both reported
**0 errors**. Initial sandbox restrictions prevented git metadata writes and
GPU visibility; authorized execution outside the sandbox allowed the required
fetch and all actual GPU tests. No unexecuted GPU check is counted as passing.

Final scientific artifacts/logs:

- /tmp/rouse-stage2a-stress-validation/summary.json: all 2076 stress gates,
  per-run CSV, metadata, stress_analysis.json and independent contributions.
- /tmp/rouse-stage2a-stage1-regression/summary.json: all 225 Rouse regressions
  and measured fixed-size performance probes.
- /tmp/stage2a-stress-suite.log, /tmp/stage2a-stage1-suite.log.
- /tmp/stage2a-check-single.log, /tmp/stage2a-check-double.log.
- /tmp/stage2a-memcheck-single.log, /tmp/stage2a-memcheck-double.log.
- /tmp/stage2a-tested-{single,double,moderate}.log: tested examples and final
  performance reports. The fresh output parent is also recorded in
  /tmp/stage2a-tested-example-root.txt.

Raw results are generated artifacts, not committed bulk data; fixed seeds and
commands reproduce the numerical results on the same build/device. Existing
build/stage2a-* example artifacts from the initial command checks were retained
rather than overwritten. No scientific test failed and no acceptance tolerance
was altered after observing results. The negative synthetic estimator fixture
is intentionally non-Gaussian and checks failure classification, not physics.

## Limits and Stage 2B recommendation

The predeclared stress study tests early/intermediate lags through approximately
1.6 tau_0 for N8,32,100. It does not resolve the far late-time stress tail of
N100; its exact slow-mode dynamics were separately preserved by Stage 1's much
longer regression. Sampling/analysis loads bounded chain histories into RAM;
there is no multi-tau or streaming stress correlation. Stress columns and extra
reductions increase sampling/output overhead, measured without modifying the
physical update. Both precision configurations pass the same theory checks;
no pathwise float/double identity is required. Unwrapped coordinates can still
lose bond/increment precision at much larger absolute coordinates than those
tested (maximum around 26.4 in the stress suite). Double stress reductions do
not solve arbitrarily long-run coordinate drift.

**Stage 2B is scientifically justified after review and explicit authorization.**
The per-chain stress, six-channel normalization and direct-lag reference provide
an independent baseline for validating Correlator6. Its memory lifecycle,
coarse-lag block averaging and deepest-level export still need separate handling
as recorded in Stage 0. No relaxation modulus, volume/density normalization,
Correlator6 runtime integration or Stage 2B work is claimed here.

All tracked changes, untracked files and ignored build artifacts must pass a
programmatic prefix audit against the starting SHA and historical source base
before commit. Final audit/commit/push results are supplied in the handoff.

## Reproduce and run the current simulator

From the slip-springs worktree root; these commands target the RTX 3060 Ti.
Use fresh validation output paths when rerunning suites.

```sh
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
python3 examples/slip-springs/validate.py suite /tmp/rouse-stage1-regression-new
python3 examples/slip-springs/stress.py suite /tmp/rouse-stage2a-validation-new
```

Short and moderately long examples, with every physical/run parameter explicit:

```sh
STRESS_EXAMPLES=$(mktemp -d /tmp/rouse-stage2a-examples.XXXXXX)
examples/slip-springs/build/single/rouse --springs 8 --chains 256 --dt 0.005 --steps 200 --sample 10 --equil 0 --seed 240008 --output "$STRESS_EXAMPLES/single"
examples/slip-springs/build/double/rouse --springs 8 --chains 256 --dt 0.005 --steps 200 --sample 10 --equil 0 --seed 240009 --output "$STRESS_EXAMPLES/double"
examples/slip-springs/build/single/rouse --springs 32 --chains 512 --dt 0.005 --steps 20000 --sample 20 --equil 0 --seed 240032 --output "$STRESS_EXAMPLES/moderate"
python3 examples/slip-springs/stress.py analyze "$STRESS_EXAMPLES/moderate"
ls "$STRESS_EXAMPLES/moderate/"
```
