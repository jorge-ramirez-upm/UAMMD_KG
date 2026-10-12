# Joint E2 review

Read-only analysis; no MD and no automatic scientific acceptance.
Three independent histories; 1000000-step windows; first window includes the unbound transient.
IAT and 5/10/20-block sensitivity use existing validated analysis helpers.
No correlations, lifetimes or transport histories are stitched across MD reseeding.

| Observable | 1–2M mean | 2–3M mean | 3–4M mean | 3–4M minus 1–2M (95% half-width) | Late minus previous |
|---|---:|---:|---:|---:|---:|
| bonds | 1578.488 | 1580.907 | 1582.672 | 4.184 ± 6.680697 | 1.765667 ± 6.167634 |
| bound_fraction | 0.7892442 | 0.7904533 | 0.7913362 | 0.002092 ± 0.003340349 | 0.0008828333 ± 0.003083817 |
| free | 843.0233 | 838.1867 | 834.6553 | -8.368 ± 13.36139 | -3.531333 ± 12.33527 |
| intra | 237.603 | 245.799 | 239.68 | 2.077 ± 12.60211 | -6.119 ± 11.42882 |
| inter | 1340.885 | 1335.108 | 1342.992 | 2.107 ± 16.32486 | 7.884667 ± 9.733577 |
| largest_cluster_fraction | 0.9674547 | 0.9639287 | 0.9680737 | 0.000619 ± 0.008536519 | 0.004145 ± 0.01004988 |
| mean_degree | 2.55382 | 2.534916 | 2.556053 | 0.002233333 ± 0.05076446 | 0.02113733 ± 0.01848193 |
| L1 | 65.31133 | 68.708 | 66.78933 | 1.478 ± 10.93854 | -1.918667 ± 16.10145 |
| L2 | 37.26933 | 36.42267 | 34.565 | -2.704333 ± 1.506751 | -1.857667 ± 2.607431 |
| components | 25.682 | 28.626 | 25.60367 | -0.07833333 ± 6.469358 | -3.022333 ± 6.913791 |
| second_degree_moment | 7.516384 | 7.437363 | 7.533736 | 0.017352 ± 0.2836202 | 0.09637267 ± 0.08990841 |
| mean_rg2 | 8.011595 | 7.990339 | 8.009634 | -0.001960653 ± 0.02302258 | 0.01929498 ± 0.03251629 |
| mean_center_terminal_r2 | 18.19475 | 18.13488 | 18.18454 | -0.01020735 ± 0.04125575 | 0.04966187 ± 0.08354553 |
| temperature | 0.9884418 | 0.9884472 | 0.9884061 | -3.569725e-05 ± 0.0001341101 | -4.108879e-05 ± 0.0003012916 |
| min_permanent_bond | 0.8589352 | 0.8591197 | 0.8590046 | 6.940332e-05 ± 0.000885405 | -0.0001150711 ± 0.0005485 |
| max_permanent_bond | 1.136303 | 1.136134 | 1.13661 | 0.0003069015 ± 0.0008018526 | 0.0004768158 ± 0.001487949 |
| creations | 1.480433 | 1.481 | 1.482433 | 0.002 ± 0.02447168 | 0.001433333 ± 0.05147219 |
| breaks | 1.480933 | 1.478433 | 1.4821 | 0.001166667 ± 0.02641044 | 0.003666667 ± 0.05633827 |
| neighbor_gains | 1.136033 | 1.1353 | 1.137533 | 0.0015 ± 0.05086284 | 0.002233333 ± 0.06621418 |
| neighbor_losses | 1.137533 | 1.1322 | 1.137167 | -0.0003666667 ± 0.04700742 | 0.004966667 ± 0.07050109 |

Intervals are exploratory, unadjusted for multiple observables. Excluding zero is a review flag,
not an automatic accept/reject rule. A wide interval is not proof of stationarity.
Inspect per-history trends, IAT resolution, block sensitivity and effect sizes in [summary.json](summary.json).
Slow topology is not proven fully decorrelated. Any acceptance is for production initialization only.
