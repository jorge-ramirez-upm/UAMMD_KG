# Joint E2 review

Read-only analysis; no MD and no automatic scientific acceptance.
Three independent histories; 1000000-step windows; first window includes the unbound transient.
IAT and 5/10/20-block sensitivity use existing validated analysis helpers.
No correlations, lifetimes or transport histories are stitched across MD reseeding.

| Observable | 1–2M mean | 2–3M mean | 3–4M mean | 4–5M mean | 5–6M mean | Late minus early (95% half-width) | Late minus previous |
|---|---:|---:|---:|---:|---:|---:|---:|
| bonds | 1344.541 | 1344.593 | 1343.232 | 1344.104 | 1344.786 | 0.2446667 ± 0.9172301 | 0.6816667 ± 3.519477 |
| bound_fraction | 0.8963609 | 0.8963953 | 0.8954882 | 0.8960696 | 0.896524 | 0.0001631111 ± 0.0006114867 | 0.0004544444 ± 0.002346318 |
| free | 310.9173 | 310.814 | 313.5353 | 311.7913 | 310.428 | -0.4893333 ± 1.83446 | -1.363333 ± 7.038955 |
| intra | 49.61067 | 55.75467 | 48.79633 | 50.04367 | 46.463 | -3.147667 ± 23.08958 | -3.580667 ± 16.17839 |
| inter | 1294.931 | 1288.838 | 1294.436 | 1294.061 | 1298.323 | 3.392333 ± 22.27541 | 4.262333 ± 14.01357 |
| largest_cluster_fraction | 0.989964 | 0.988 | 0.989617 | 0.9900793 | 0.9903457 | 0.0003816667 ± 0.004730759 | 0.0002663333 ± 0.003519512 |
| mean_degree | 2.561233 | 2.548886 | 2.563497 | 2.560926 | 2.56857 | 0.007336667 ± 0.04497588 | 0.007644 ± 0.03247365 |
| L1 | 14.402 | 14.43233 | 12.70667 | 13.63867 | 14.06133 | -0.3406667 ± 7.543693 | 0.4226667 ± 2.716592 |
| L2 | 8.672667 | 8.851 | 8.861667 | 8.794667 | 8.313 | -0.3596667 ± 4.374762 | -0.4816667 ± 0.4651046 |
| components | 8.785333 | 10.18767 | 8.952 | 8.643667 | 8.610667 | -0.1746667 ± 3.189471 | -0.033 ± 2.861907 |
| second_degree_moment | 6.997868 | 6.95214 | 7.006947 | 6.995919 | 7.028923 | 0.03105533 ± 0.1719863 | 0.033004 ± 0.1228097 |
| mean_rg2 | 6.331517 | 6.303907 | 6.347923 | 6.323516 | 6.339203 | 0.007685819 ± 0.09534369 | 0.01568661 ± 0.1152906 |
| mean_center_terminal_r2 | 15.52842 | 15.45997 | 15.55898 | 15.50857 | 15.55059 | 0.02216715 ± 0.2326231 | 0.04201699 ± 0.3260228 |
| temperature | 0.9790765 | 0.9789593 | 0.9790136 | 0.9789529 | 0.9790157 | -6.071255e-05 ± 0.0004643419 | 6.287163e-05 ± 0.000482485 |
| min_permanent_bond | 0.8609923 | 0.8609329 | 0.8607611 | 0.8609096 | 0.8609933 | 9.056499e-07 ± 5.487615e-05 | 8.36684e-05 ± 0.0007225808 |
| max_permanent_bond | 1.134404 | 1.135468 | 1.13425 | 1.134904 | 1.134546 | 0.0001424493 ± 0.001052412 | -0.0003581124 ± 0.000731736 |
| creations | 1.3652 | 1.360133 | 1.373967 | 1.358933 | 1.358567 | -0.006633333 ± 0.05515305 | -0.0003666667 ± 0.02509346 |
| breaks | 1.366067 | 1.3603 | 1.3736 | 1.359733 | 1.356833 | -0.009233333 ± 0.05246975 | -0.0029 ± 0.02759405 |
| neighbor_gains | 1.285033 | 1.276133 | 1.297867 | 1.279267 | 1.284867 | -0.0001666667 ± 0.08120265 | 0.0056 ± 0.03979519 |
| neighbor_losses | 1.286967 | 1.2759 | 1.2969 | 1.2804 | 1.283 | -0.003966667 ± 0.07673724 | 0.0026 ± 0.04250833 |

Intervals are exploratory, unadjusted for multiple observables. Excluding zero is a review flag,
not an automatic accept/reject rule. A wide interval is not proof of stationarity.
Inspect per-history trends, IAT resolution, block sensitivity and effect sizes in [summary.json](summary.json).
Slow topology is not proven fully decorrelated. Any acceptance is for production initialization only.
