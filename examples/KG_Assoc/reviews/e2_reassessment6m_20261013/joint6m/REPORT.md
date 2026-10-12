# Joint E2 review

Read-only analysis; no MD and no automatic scientific acceptance.
Three independent histories; 1000000-step windows; first window includes the unbound transient.
IAT and 5/10/20-block sensitivity use existing validated analysis helpers.
No correlations, lifetimes or transport histories are stitched across MD reseeding.

| Observable | 1–2M mean | 2–3M mean | 3–4M mean | 4–5M mean | 5–6M mean | Late minus early (95% half-width) | Late minus previous |
|---|---:|---:|---:|---:|---:|---:|---:|
| L1 | 65.31133 | 68.708 | 66.78933 | 65.769 | 64.26833 | -1.043 ± 15.51093 | -1.500667 ± 20.99892 |
| L2 | 37.26933 | 36.42267 | 34.565 | 37.34 | 35.16933 | -2.1 ± 7.398736 | -2.170667 ± 6.703482 |
| bonds | 1578.488 | 1580.907 | 1582.672 | 1581.004 | 1582.398 | 3.909333 ± 3.063781 | 1.394 ± 8.293368 |
| bound_fraction | 0.7892442 | 0.7904533 | 0.7913362 | 0.7905018 | 0.7911988 | 0.001954667 ± 0.00153189 | 0.000697 ± 0.004146684 |
| components | 25.682 | 28.626 | 25.60367 | 27.232 | 26.72867 | 1.046667 ± 5.836964 | -0.5033333 ± 1.703159 |
| free | 843.0233 | 838.1867 | 834.6553 | 837.9927 | 835.2047 | -7.818667 ± 6.127561 | -2.788 ± 16.58674 |
| inter | 1340.885 | 1335.108 | 1342.992 | 1343.906 | 1338.933 | -1.952333 ± 23.46415 | -4.973 ± 20.58539 |
| intra | 237.603 | 245.799 | 239.68 | 237.0977 | 243.4647 | 5.861667 ± 20.88283 | 6.367 ± 22.45929 |
| largest_cluster_fraction | 0.9674547 | 0.9639287 | 0.9680737 | 0.965682 | 0.9659583 | -0.001496333 ± 0.008721726 | 0.0002763333 ± 0.00205491 |
| max_permanent_bond | 1.136303 | 1.136134 | 1.13661 | 1.136435 | 1.136441 | 0.0001380049 ± 0.0002980688 | 6.657907e-06 ± 0.0008831995 |
| mean_center_terminal_r2 | 18.19475 | 18.13488 | 18.18454 | 18.18593 | 18.17095 | -0.02379405 ± 0.04032015 | -0.01497422 ± 0.06009179 |
| mean_degree | 2.55382 | 2.534916 | 2.556053 | 2.558185 | 2.550833 | -0.002987333 ± 0.05765084 | -0.007352667 ± 0.07727048 |
| mean_rg2 | 8.011595 | 7.990339 | 8.009634 | 8.006007 | 8.005764 | -0.005830818 ± 0.01668571 | -0.0002422651 ± 0.01922693 |
| min_permanent_bond | 0.8589352 | 0.8591197 | 0.8590046 | 0.8591115 | 0.8591386 | 0.0002034445 ± 0.0003575342 | 2.710436e-05 ± 0.001305568 |
| second_degree_moment | 7.516384 | 7.437363 | 7.533736 | 7.556187 | 7.514598 | -0.001786 ± 0.2656647 | -0.04158867 ± 0.3820813 |
| temperature | 0.9884418 | 0.9884472 | 0.9884061 | 0.9885083 | 0.9884462 | 4.348148e-06 ± 0.0001784652 | -6.21602e-05 ± 0.0004961678 |
| breaks | 1.480933 | 1.478433 | 1.4821 | 1.483067 | 1.469933 | -0.011 ± 0.04273062 | -0.01313333 ± 0.0542271 |
| creations | 1.480433 | 1.481 | 1.482433 | 1.4816 | 1.470633 | -0.0098 ± 0.0463374 | -0.01096667 ± 0.05649089 |
| neighbor_gains | 1.136033 | 1.1353 | 1.137533 | 1.136667 | 1.1323 | -0.003733333 ± 0.05463982 | -0.004366667 ± 0.01812262 |
| neighbor_losses | 1.137533 | 1.1322 | 1.137167 | 1.137567 | 1.1317 | -0.005833333 ± 0.05099211 | -0.005866667 ± 0.02273859 |

Intervals are exploratory, unadjusted for multiple observables. Excluding zero is a review flag,
not an automatic accept/reject rule. A wide interval is not proof of stationarity.
Inspect per-history trends, IAT resolution, block sensitivity and effect sizes in [summary.json](summary.json).
Slow topology is not proven fully decorrelated. Any acceptance is for production initialization only.
