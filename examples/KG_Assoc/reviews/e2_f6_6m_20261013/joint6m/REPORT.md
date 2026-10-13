# Joint E2 review

Read-only analysis; no MD and no automatic scientific acceptance.
Three independent histories; 1000000-step windows; first window includes the unbound transient.
IAT and 5/10/20-block sensitivity use existing validated analysis helpers.
No correlations, lifetimes or transport histories are stitched across MD reseeding.

| Observable | 1–2M mean | 2–3M mean | 3–4M mean | 4–5M mean | 5–6M mean | Late minus early (95% half-width) | Late minus previous |
|---|---:|---:|---:|---:|---:|---:|---:|
| bonds | 2693.016 | 2693.217 | 2693.213 | 2693.673 | 2692.94 | -0.076 ± 4.269869 | -0.733 ± 4.500066 |
| bound_fraction | 0.8976721 | 0.8977389 | 0.8977378 | 0.8978911 | 0.8976468 | -2.533333e-05 ± 0.00142329 | -0.0002443333 ± 0.001500022 |
| free | 613.9673 | 613.5667 | 613.5733 | 612.6533 | 614.1193 | 0.152 ± 8.539738 | 1.466 ± 9.000133 |
| intra | 210.227 | 210.6403 | 216.3853 | 209.285 | 205.9423 | -4.284667 ± 17.13547 | -3.342667 ± 26.98507 |
| inter | 2482.789 | 2482.576 | 2476.828 | 2484.388 | 2486.998 | 4.208667 ± 16.93663 | 2.609667 ± 29.29264 |
| largest_cluster_fraction | 0.9998153 | 0.9998077 | 0.999801 | 0.9998193 | 0.999818 | 2.666667e-06 ± 0.0003000843 | -1.333333e-06 ± 0.0002010524 |
| mean_degree | 4.697865 | 4.691786 | 4.680957 | 4.700425 | 4.695573 | -0.002291333 ± 0.04262092 | -0.004851333 ± 0.05629958 |
| L1 | 138.5473 | 140.0657 | 140.5357 | 138.3433 | 143.711 | 5.163667 ± 9.590513 | 5.367667 ± 1.272588 |
| L2 | 169.8773 | 170.0103 | 167.4903 | 166.364 | 166.6403 | -3.237 ± 24.69916 | 0.2763333 ± 31.84553 |
| components | 1.182 | 1.191333 | 1.199 | 1.180667 | 1.180333 | -0.001666667 ± 0.3057082 | -0.0003333333 ± 0.1978808 |
| second_degree_moment | 23.21732 | 23.16115 | 23.05661 | 23.22666 | 23.17689 | -0.04042467 ± 0.3923815 | -0.049772 ± 0.4485166 |
| mean_rg2 | 7.980036 | 7.981601 | 7.970616 | 7.985403 | 7.989257 | 0.009221257 ± 0.06712227 | 0.003853821 ± 0.03004979 |
| mean_center_terminal_r2 | 16.57991 | 16.57178 | 16.55176 | 16.59318 | 16.60292 | 0.0230054 ± 0.1647097 | 0.009732804 ± 0.0904182 |
| temperature | 0.9789515 | 0.9787666 | 0.9789243 | 0.9788689 | 0.9788256 | -0.0001259098 ± 0.0005895636 | -4.326557e-05 ± 0.0001415658 |
| min_permanent_bond | 0.8578366 | 0.8580034 | 0.858053 | 0.8582136 | 0.8581138 | 0.0002771689 ± 0.0001571798 | -9.984859e-05 ± 0.0001505984 |
| max_permanent_bond | 1.144005 | 1.143995 | 1.14362 | 1.143566 | 1.143545 | -0.0004597414 ± 0.0009889276 | -2.097195e-05 ± 0.002606937 |
| creations | 2.7384 | 2.743033 | 2.739767 | 2.744667 | 2.753967 | 0.01556667 ± 0.05983921 | 0.0093 ± 0.06077293 |
| breaks | 2.740833 | 2.743333 | 2.7404 | 2.743133 | 2.7544 | 0.01356667 ± 0.06399394 | 0.01126667 ± 0.05825883 |
| neighbor_gains | 2.2576 | 2.259367 | 2.247733 | 2.268833 | 2.2623 | 0.0047 ± 0.04782012 | -0.006533333 ± 0.05746148 |
| neighbor_losses | 2.2611 | 2.258933 | 2.247967 | 2.267367 | 2.2651 | 0.004 ± 0.05183463 | -0.002266667 ± 0.04430511 |

Intervals are exploratory, unadjusted for multiple observables. Excluding zero is a review flag,
not an automatic accept/reject rule. A wide interval is not proof of stationarity.
Inspect per-history trends, IAT resolution, block sensitivity and effect sizes in [summary.json](summary.json).
Slow topology is not proven fully decorrelated. Any acceptance is for production initialization only.
