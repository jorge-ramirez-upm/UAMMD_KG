# f=3 E2 joint scientific assessment through 6M

**Recommendation: further E2 equilibration before scientific acceptance; place
the 6M endpoints on scientific hold.** A coherent peripheral-network mean shift
remains unresolved, even though the bulk chemical populations are stable. This
is not proof of irreversible drift or failure of the numerical model. The hold
asks whether a concrete population change stabilizes or reverses, not for proof
of complete topology decorrelation. No formal acceptance, active selection,
production authorization or new trajectory is created by this assessment.

Starting verified local/remote `KremerGrest` SHA:
`5640a03b22a72f6be009538dca565a2a343e66ed`. System
`F03_N010_RP080_EE08_EA04`; source plan
`banks/e2_attempts/F03_N010_RP080_EE08/equilibrate_bb4106da56cf4e7e888fb4ef8aa73e7c/plan.json`,
SHA256 `b302c55f01ccff0b49638db240f70e47f50e0e7bec1fda17df24a7195b714cad`.

## Authentication and independent units

All original E1 parent identities/hashes, plans/approval, replica coverage,
physical parameters, chemical/MD seeds, completion receipts and exact endpoint
payloads authenticate. All three 6M histories were independently revalidated
numerically and by complete accepted-event, network and conformation replay.
Current source/build/log/executable hashes authenticate; historical versions of
the evolving read-only review driver are checked against recorded Git blobs.
There is no missing-historic-executable-byte limitation for this f=3 attempt.
The original checkpoint input/config/report hashes also authenticate and its
files remain unchanged at `aggregate/e2/review_a7fffec7157e4dc08c40bd87b369c9eb/`.
Full provenance and endpoint/output hashes are in [provenance.json](provenance.json).

Each history is one continuous 0–6M trajectory with no intermediate restart or
MD reseed. Analysis cuts are not restart boundaries. Three original histories
are the independent statistical units; stars, frames, windows and overlapping
contrasts are not additional replicas. Paired changes use Student-t df=2,
exploratory 95% intervals, unadjusted for multiple comparisons. No significant
or nonsignificant difference is an automatic acceptance/rejection rule.

The complete initially unbound 0–1M transient is retained as context. Early 1–2M
and the common 2–3M connectivity dip are not retrospectively certified stationary.
The primary comparison remains the requested 2–4M versus 4–6M; later 3–6M
intervals provide a candidate preparation regime, selected retrospectively rather
than by a frozen automated rule. All IAT/block estimates are computed within one
continuous history/window, never stitched or averaged between windows.

## Complete 1M history means

Rates are accepted events per MD time unit (`dt=0.01`). Neighbor turnover counts
unique inter-star edges, not individual inter-star bonds. L1 counts parallel
inter-star bond pairs, L2 distinct-star triangles. Conformations use the existing
permanent-bond minimum-image unwrapping definition.

| Observable | 0–1M context | 1–2M | 2–3M | 3–4M | 4–5M | 5–6M |
|---|---:|---:|---:|---:|---:|---:|
| bonds | 1341.258 | 1344.541 | 1344.593 | 1343.232 | 1344.104 | 1344.786 |
| bound_fraction | 0.894172 | 0.8963609 | 0.8963953 | 0.8954882 | 0.8960696 | 0.896524 |
| intra | 48.941 | 49.61067 | 55.75467 | 48.79633 | 50.04367 | 46.463 |
| inter | 1292.317 | 1294.931 | 1288.838 | 1294.436 | 1294.061 | 1298.323 |
| mean_degree | 2.559309 | 2.561233 | 2.548886 | 2.563497 | 2.560926 | 2.56857 |
| second_degree_moment | 6.992614 | 6.997868 | 6.95214 | 7.006947 | 6.995919 | 7.028923 |
| components | 9.764333 | 8.785333 | 10.18767 | 8.952 | 8.643667 | 8.610667 |
| largest_cluster_fraction | 0.9877367 | 0.989964 | 0.988 | 0.989617 | 0.9900793 | 0.9903457 |
| L1 | 12.77733 | 14.402 | 14.43233 | 12.70667 | 13.63867 | 14.06133 |
| L2 | 8.528333 | 8.672667 | 8.851 | 8.861667 | 8.794667 | 8.313 |
| mean_rg2 | 6.323986 | 6.331517 | 6.303907 | 6.347923 | 6.323516 | 6.339203 |
| mean_center_terminal_r2 | 15.50425 | 15.52842 | 15.45997 | 15.55898 | 15.50857 | 15.55059 |
| creations | 1.506533 | 1.3652 | 1.360133 | 1.373967 | 1.358933 | 1.358567 |
| breaks | 1.371667 | 1.366067 | 1.3603 | 1.3736 | 1.359733 | 1.356833 |
| neighbor_gains | 1.427033 | 1.285033 | 1.276133 | 1.297867 | 1.279267 | 1.284867 |
| neighbor_losses | 1.297867 | 1.286967 | 1.2759 | 1.2969 | 1.2804 | 1.283 |

## Replica-level connectivity and L2 paths

| History / observable | 0–1M | 1–2M | 2–3M | 3–4M | 4–5M | 5–6M |
|---|---:|---:|---:|---:|---:|---:|
| r001 largest_cluster_fraction | 0.986826 | 0.98884 | 0.987974 | 0.990088 | 0.989456 | 0.991261 |
| r002 largest_cluster_fraction | 0.988589 | 0.991382 | 0.988656 | 0.989216 | 0.990054 | 0.990032 |
| r003 largest_cluster_fraction | 0.987795 | 0.98967 | 0.98737 | 0.989547 | 0.990728 | 0.989744 |
| r001 components | 10.69 | 9.437 | 10.291 | 8.836 | 9.267 | 7.962 |
| r002 components | 9.042 | 7.856 | 9.94 | 8.908 | 8.682 | 8.948 |
| r003 components | 9.561 | 9.063 | 10.332 | 9.112 | 7.982 | 8.922 |
| r001 L2 | 9.583 | 8.335 | 7.821 | 9.169 | 8.239 | 7.694 |
| r002 L2 | 9.104 | 10.642 | 8.925 | 8.861 | 8.95 | 8.679 |
| r003 L2 | 6.898 | 7.041 | 9.807 | 8.555 | 9.195 | 8.566 |

## Paired 4–6M minus 2–4M contrasts

| Observable | r001 / r002 / r003 changes | Mean ± 95% half-width |
|---|---|---:|
| bonds | +1.3825 / +0.0195 / +0.1955 | +0.5325 ± 1.841796 |
| bound_fraction | +0.0009216667 / +1.3e-05 / +0.0001303333 | +0.000355 ± 0.001227864 |
| intra | -5.974 / +0.184 / -6.2765 | -4.022167 ± 9.057365 |
| inter | +7.3565 / -0.1645 / +6.472 | +4.554667 ± 10.21256 |
| mean_degree | +0.017911 / -0.002085 / +0.009843 | +0.008556333 ± 0.0249922 |
| second_degree_moment | +0.075666 / -0.010037 / +0.033005 | +0.032878 ± 0.106458 |
| components | -0.949 / -0.609 / -1.27 | -0.9426667 ± 0.8211868 |
| largest_cluster_fraction | +0.0013275 / +0.001107 / +0.0017775 | +0.001404 ± 0.0008489815 |
| L1 | -1.623 / +0.861 / +1.6035 | +0.2805 ± 4.197951 |
| L2 | -0.5285 / -0.0785 / -0.3005 | -0.3025 ± 0.5589927 |
| mean_rg2 | +0.008945209 / +0.01707761 / -0.009689897 | +0.005444307 ± 0.03409224 |
| mean_center_terminal_r2 | +0.03783627 / +0.04182706 / -0.01935987 | +0.02010115 ± 0.085045 |
| creations | -0.0171 / -0.01175 / +0.00395 | -0.0083 ± 0.02718081 |
| breaks | -0.01795 / -0.01205 / +0.004 | -0.008666667 ± 0.02822058 |
| neighbor_gains | -0.0065 / -0.01285 / +0.00455 | -0.004933333 ± 0.02187499 |
| neighbor_losses | -0.0076 / -0.0113 / +0.0048 | -0.0047 ± 0.02094962 |

The supplied preliminary connectivity differences are reproduced: largest-cluster
fraction +0.001404 ± 0.000849 and components −0.9427 ± 0.8212, with identical
signs across all histories. These are not erased by wider alternative intervals.
Largest-cluster growth is 0.1404 percentage points, or **1.404 stars** out of
1,000. The mean population outside the giant changes from 11.1915 to 9.7875
stars, a **12.5% relative decrease**; mean components fall 9.570 to 8.627
(~9.9%). The effects cannot be dismissed merely as small whole-system fractions.
Both observables describe related peripheral-network changes, not two independent
confirmations. L2 changes −0.3025 ± 0.5590 with all three negative signs in this
particular contrast; L1 and degree moments have mixed replica changes.

## Sensitivity to reasonable window choices

Alternative means are duration-weighted combinations of exactly tiled 1M means.
Only independent-history paired uncertainty is estimated here; **no SEM or IAT
is combined between windows**. Correlation/block evidence is given separately.

| Observable | Early → late | Replica signs | Difference ± 95% half-width |
|---|---|---|---:|
| largest_cluster_fraction | 1–3M → 3–5M | + / − / + | +0.0008661667 ± 0.002707959 |
| L2 | 1–3M → 3–5M | + / − / + | +0.06633333 ± 2.043329 |
| components | 1–3M → 3–5M | − / − / − | -0.6886667 ± 1.328169 |
| largest_cluster_fraction | 1–3M → 4–6M | + / + / + | +0.0012305 ± 0.002612216 |
| L2 | 1–3M → 4–6M | − / − / + | -0.208 ± 1.782842 |
| components | 1–3M → 4–6M | − / − / − | -0.8593333 ± 1.670289 |
| largest_cluster_fraction | 2–4M → 4–6M | + / + / + | +0.001404 ± 0.0008489815 |
| L2 | 2–4M → 4–6M | − / − / − | -0.3025 ± 0.5589927 |
| components | 2–4M → 4–6M | − / − / − | -0.9426667 ± 0.8211868 |
| largest_cluster_fraction | 2–3M → 3–4M | + / + / + | +0.001617 ± 0.002275482 |
| L2 | 2–3M → 3–4M | + / − / − | +0.01066667 ± 3.233633 |
| components | 2–3M → 3–4M | − / − / − | -1.235667 ± 0.5265176 |
| largest_cluster_fraction | 3–4M → 5–6M | + / + / + | +0.0007286667 ± 0.001226831 |
| L2 | 3–4M → 5–6M | − / − / + | -0.5486667 ± 2.007373 |
| components | 3–4M → 5–6M | − / + / − | -0.3413333 ± 1.181107 |
| largest_cluster_fraction | 4–5M → 5–6M | + / − / − | +0.0002663333 ± 0.003519512 |
| L2 | 4–5M → 5–6M | − / − / − | -0.4816667 ± 0.4651046 |
| components | 4–5M → 5–6M | − / + / + | -0.033 ± 2.861907 |
| largest_cluster_fraction | 3–5M → 4–6M | + / + / + | +0.0003643333 ± 0.0006134157 |
| L2 | 3–5M → 4–6M | − / − / + | -0.2743333 ± 1.003687 |
| components | 3–5M → 4–6M | − / + / − | -0.1706667 ± 0.5905535 |
| largest_cluster_fraction | 2–5M → 3–6M | + / + / + | +0.0007818889 ± 0.0007915226 |
| L2 | 2–5M → 3–6M | − / − / − | -0.1793333 ± 0.5065702 |
| components | 2–5M → 3–6M | − / − / − | -0.5256667 ± 0.5664007 |

The connectivity difference partly reflects the common 2–3M dip: all histories
have a smaller giant and more components there than at 3–4M. Later comparisons
attenuate the shift. For 3–4M versus 5–6M, largest-cluster growth is still positive
in every history (+0.000729 ± 0.001227), but the component changes are no longer
all negative. In the final 4–5M versus 5–6M contrast, giant growth is positive
only in r001; components rise in r002/r003. Thus the common primary difference
is not a persistent common-sign latest trend. Losing significance under shorter
windows alone would not establish this; the actual reversal of replica directions
and nonmonotonic full paths are the additional evidence.

The overlapping 3–5M versus 4–6M contrast equals half of the 3–4M versus 5–6M
change, so it is not a new independent confirmation. The shifted 3M contrasts
also attenuate connectivity changes while retaining positive giant-growth signs.
A small residual connectivity drift remains possible. Window sensitivity is an
exploratory diagnostic, not permission to search for an acceptable p-value.

Latest L2 does decline in all three histories: −0.4817 ± 0.4651 for 5–6M minus
4–5M, an exploratory interval excluding zero. This flag is retained. Earlier
1M/shifted comparisons have mixed signs and the full L2 paths are nonmonotonic;
the evidence does not establish a sustained common triangle-decay process.
Another numerical diagnostic, maximum permanent-bond length, shifts slightly
(−0.0001337 ± 0.0000361); both windows pass the unchanged numerical/FENE guards.
All observables and flags remain in [summary.json](joint6m/summary.json), not just
those supporting the recommendation.

## Full distinct-neighbor degree distribution

The unchanged validated graph replay was instrumented only to capture its returned
`neighbor_degree` histogram at every original diagnostic; it returns the graph
unchanged and restores the callback afterward. This separates distinct neighbors
from bond incidence and preserves parallel edges/intra-star bonds correctly.
Fractions average within each history before any paired comparison. Neither
1,000 stars nor thousands of frames supply binomial independent-sample errors.

| Distinct neighbors k | 2–4M fraction | 4–6M fraction | Replica changes | Paired change ± 95% half-width |
|---|---:|---:|---|---:|
| 0 | 0.006658833 | 0.006123833 | -0.0005215 / -0.0001635 / -0.00092 | -0.000535 ± 0.0009401497 |
| 1 | 0.079316 | 0.07596917 | -0.00538 / +0.0006845 / -0.005345 | -0.003346833 ± 0.008673523 |
| 2 | 0.2651998 | 0.2649422 | -0.0055865 / +0.0012065 / +0.003607 | -0.0002576667 ± 0.0118464 |
| 3 | 0.6488253 | 0.6529648 | +0.011488 / -0.0017275 / +0.002658 | +0.0041395 ± 0.01672247 |

The isolated-star fraction decreases by 0.000535 ± 0.000940 (0.535 stars),
with all primary signs negative. Subtracting this within each paired history,
rather than combining unrelated SEMs, reveals the more specific signal:

| Peripheral quantity | 2–4M mean | 4–6M mean | Paired change ± 95% half-width |
|---|---:|---:|---:|
| Non-singleton satellite components | 1.9110 | 1.5033 | −0.4077 ± 0.1261 |
| Stars in non-singleton satellites | 4.5327 | 3.6637 | −0.8690 ± 0.1726 |

The satellite-component changes are −0.4275/−0.4455/−0.3500 in the three
histories: a coherent **21.3% relative decrease**. Satellite-star count decreases
about **19.2%**. These derived quantities are correlated with giant fraction and
component count, not independent confirmations; subtracting isolates preserves
that covariance in each history. A nonisolated giant is verified at every retained
diagnostic. Definitions are `components - 1 - isolated_stars` and
`outside_giant_stars - isolated_stars`; no combined-window IAT or SEM is invented.
See [peripheral_population.json](peripheral_population.json).

This strengthens the concern beyond a small global fraction or a change in
isolated vertices alone. r001's satellite count declines in each 1M window
from 2–3M onward (2.011/1.604/1.517/1.243); r002 declines through 3–6M
(2.175/1.622/1.364). r003 rebounds late (1.542/1.533/1.741), so it is not a
universal monotonic law. The latest paired satellite change is −0.108 ± 0.680,
with two negative signs and one positive. Shifting overlapping 3M windows from
2–5M to 3–6M gives −0.1997 ± 0.1899 with all three negative signs, but this is
algebraically one-third of the 2–3M to 5–6M contrast, not independent evidence.
Earlier shifted windows also have mixed directions. Both stationary rare-cluster
fluctuations and continuing structural redistribution remain possible.

Degree-one changes are mixed, with slow uncertainty in some histories. Full 1M
fractions, endpoint histograms and fresh 2M IAT/block estimates are preserved in
[degree_distribution.json](degree_distribution.json). No star or frame is counted
as an independent replica.

## Correlation, blocking and possible relaxation

| Window | History / mode | IAT time | Effective samples | IAT SEM | Block SEM 5 / 10 / 20 |
|---|---|---:|---:|---:|---|
| 2–4M | r001 largest_cluster_fraction | 418.159 | 23.9143 | 0.000900637 | 0.0010012 / 0.000780703 / 0.000588297 |
| 2–4M | r001 components | 381.827 | 26.1899 | 0.58894 | 0.674952 / 0.544377 / 0.398275 |
| 2–4M | r001 L1 | 751.341 | 13.3095 | 0.905189 | 0.760573 / 0.813661 / 0.637715 |
| 2–4M | r001 L2 | 560.803 | 17.8316 | 0.554869 | 0.515866 / 0.443205 / 0.353014 |
| 2–4M | r001 intra | 555.53 | 18.0008 | 1.26357 | 1.38879 / 1.20108 / 1.03273 |
| 2–4M | r001 inter | 223.547 | 44.7334 | 1.49317 | 1.70949 / 1.42701 / 1.24963 |
| 2–4M | r002 largest_cluster_fraction | 182.456 | 54.8076 | 0.00056674 | 0.000604225 / 0.000568137 / 0.000466445 |
| 2–4M | r002 components | 274.867 | 36.3813 | 0.474499 | 0.555609 / 0.46342 / 0.364542 |
| 2–4M | r002 L1 | 1539.72 | 6.49467 | 1.73989 | 1.81097 / 1.21897 / 0.917082 |
| 2–4M | r002 L2 | 344.332 | 29.0417 | 0.452693 | 0.534674 / 0.432477 / 0.376818 |
| 2–4M | r002 intra | 1788.82 | 5.59028 | 3.15192 | 3.14226 / 2.20527 / 1.59336 |
| 2–4M | r002 inter | 448.101 | 22.3164 | 2.34007 | 2.56929 / 2.02003 / 1.64536 |
| 2–4M | r003 largest_cluster_fraction | 258.801 | 38.6398 | 0.000711547 | 0.000725837 / 0.000619978 / 0.000573583 |
| 2–4M | r003 components | 317.663 | 31.4799 | 0.505175 | 0.472394 / 0.415297 / 0.371795 |
| 2–4M | r003 L1 | 363.094 | 27.5411 | 0.505153 | 0.622994 / 0.542179 / 0.457138 |
| 2–4M | r003 L2 | 416.314 | 24.0203 | 0.566485 | 0.397077 / 0.559993 / 0.448153 |
| 2–4M | r003 intra | 1991.01 | 5.02258 | 4.11219 | 3.58436 / 2.80197 / 2.00862 |
| 2–4M | r003 inter | 1147.42 | 8.71523 | 3.87264 | 3.09088 / 2.55678 / 1.92511 |
| 4–6M | r001 largest_cluster_fraction | 399.737 | 25.0165 | 0.000831567 | 0.000857761 / 0.000681068 / 0.00053428 |
| 4–6M | r001 components | 277.856 | 35.9898 | 0.479735 | 0.592397 / 0.494651 / 0.412541 |
| 4–6M | r001 L1 | 803.36 | 12.4477 | 1.00627 | 0.960686 / 0.95793 / 0.699073 |
| 4–6M | r001 L2 | 483.48 | 20.6834 | 0.647565 | 0.713915 / 0.656313 / 0.555671 |
| 4–6M | r001 intra | 2066.43 | 4.83927 | 3.86363 | 3.58697 / 2.51999 / 1.81857 |
| 4–6M | r001 inter | 1085.78 | 9.20998 | 4.04356 | 3.87345 / 2.65654 / 1.92616 |
| 4–6M | r002 largest_cluster_fraction | 200.167 | 49.9582 | 0.000543866 | 0.000741979 / 0.000548289 / 0.000445013 |
| 4–6M | r002 components | 120.521 | 82.9729 | 0.286903 | 0.498508 / 0.357274 / 0.281045 |
| 4–6M | r002 L1 | 1356.85 | 7.37003 | 1.59349 | 1.37451 / 1.12408 / 0.877175 |
| 4–6M | r002 L2 | 980.232 | 10.2017 | 1.0291 | 1.06997 / 0.805732 / 0.638321 |
| 4–6M | r002 intra | 1315.82 | 7.59982 | 2.26409 | 2.36895 / 1.77291 / 1.32128 |
| 4–6M | r002 inter | 567.88 | 17.6094 | 2.61223 | 2.59241 / 2.1009 / 1.57556 |
| 4–6M | r003 largest_cluster_fraction | 284.72 | 35.1222 | 0.000670933 | 0.000637039 / 0.000619113 / 0.000456355 |
| 4–6M | r003 components | 290.547 | 34.4179 | 0.44699 | 0.387006 / 0.435011 / 0.331102 |
| 4–6M | r003 L1 | 590.956 | 16.9217 | 0.848294 | 0.862868 / 0.852336 / 0.652391 |
| 4–6M | r003 L2 | 322.727 | 30.9859 | 0.490378 | 0.678377 / 0.565783 / 0.454271 |
| 4–6M | r003 intra | 500.041 | 19.9984 | 1.03113 | 0.959687 / 1.09886 / 0.869814 |
| 4–6M | r003 inter | 90.2036 | 110.86 | 0.887563 | 0.783417 / 0.991207 / 0.892592 |

Late largest-cluster effective counts are about 25/50/35 and components about
36/83/34. Individual-window IAT SEMs for giant fraction (0.00083/0.00054/0.00067)
are comparable to the paired shifts; these within-window estimates and the df=2
between-history interval answer different questions and must not be naively
added, averaged or treated as additional evidence. Late r002 L1 has only 7.4
effective samples; late r001 intra 4.8 and inter 9.2. r001 intra IAT SEM 3.86
versus block SEMs 3.59/2.52/1.82 demonstrates misleading precision from small
blocks. Early r002/r003 intra estimates also have only about five effective samples.
Late degree-one support is about 7.7/13.9/65.8; isolated-star support about
47/94/52. Complete per-degree blocking sensitivities are in the degree artifact.

An IAT SEM describes uncertainty of a stationary mean *if* that interpretation
is appropriate. It does not prove stationarity, distinguish aging by itself or
make a finite-window trend harmless. In particular, late r001 intra falls while
inter rises; r002 changes oppositely, and r003 shows a smaller repartitioning.
Those slow excursions may be unresolved relaxation or stationary fluctuations.
They remain a qualification. Conformation changes are small with mixed signs:
Rg² +0.00544 ± 0.03409; center–terminal R² +0.02010 ± 0.08504. Total populations
and bound fraction remain near plateau, and accepted bond/neighbor exchange
continues without a common arrest or chemical buildup signature.

## Functionality context, not acceptance criteria

All conditions below have N=10, rho_p=0.8, Ee=8, Ea=4 and 1,000 stars; sticker
counts, total bead counts and box sizes differ. f=4 uses **corrected C1 6–8M only**,
never defective historical statistics; its corrected-from-defective lineage and
qualified acceptance are retained. f=6 uses accepted 4–6M statistics. These are
recorded qualified initialization references, not unqualified equilibrium standards.

| Context | Stickers | Bound fraction | Largest-cluster fraction | Mean degree | L1 | L2 | Creations / 1,000 stickers / time |
|---|---:|---:|---:|---:|---:|---:|---:|
| f3 4–6M | 3000 | 0.8962968 | 0.9902125 | 2.564748 | 13.85 | 8.553833 | 0.4529167 |
| corrected_C1_f4_6to8M | 4000 | 0.8970025 | 0.997694 | 3.318562 | 39.64567 | 33.39383 | 0.454875 |
| accepted_f6_4to6M | 6000 | 0.8977689 | 0.9998187 | 4.697999 | 141.0272 | 166.5022 | 0.4582194 |

Similar bound fractions support a consistent chemistry context without implying
identical geometry-dependent equilibrium ensembles. Lower functionality allows
fewer distinct neighbors and different loop/branch structure; f=3 has more
peripheral stars and its connectivity statistics are more visibly affected by
a few attachments/detachments. Raw bond/loop/rate counts must not be compared as
if sticker counts or network capacities were equal. Different run lengths and
C1's corrected lineage preclude transferring equilibration times or acceptance
thresholds. Context source hashes are in [functionality_context.json](functionality_context.json).

## Recommendation and limitations

The coherent satellite deficit (roughly 21% of this rare population), accompanying
giant/component changes, late L2 decrease, slow repartitioning and continuing
satellite loss in two histories justify **a scientific hold and one further
review checkpoint**. This judgment combines physical effect sizes, replica paths,
window sensitivity and correlation limitations. It does not reject initialization
solely because an exploratory interval excludes zero or impose a numerical
acceptance threshold. Bulk populations, activity and conformations appear well
prepared; they do not independently settle the peripheral-network question.

A stationary-fluctuation explanation remains plausible: late directions are mixed,
signals depend on windows and only three independent histories are available.
The evidence does not prove persistent aging, an equilibrium failure or numerical
instability. Conversely, attenuated or nonsignificant alternative differences do
not resolve the earlier shared shift. IAT uncertainties cannot by themselves
turn slow trajectories into demonstrated stationary samples. The additional
checkpoint should test whether the satellite population and connectivity means
plateau/rebound or continue shifting, while checking chemical/degree/L1/L2 and
conformation evidence jointly. Complete decorrelation of every mode is not required.

**Proposed next scientific checkpoint:** extend each original history by 2M steps
from its authenticated 6M endpoint to absolute 8M, if separately authorized by the
user. This duration is a first review checkpoint, not a guarantee of equilibrium
or an automatic stopping/acceptance criterion. Preserve chemistry seed identity,
allocate fresh recorded MD seeds through the existing extension mechanism, and
analyze 6–8M separately across that genuine MD-reseed boundary; do not stitch IAT,
residence, stress or transport histories across it. No extension plan, approval
record, launch command or simulation has been generated in this task.

## Exact reviewed endpoints and next decision

Prefixes are relative to `examples/KG_Assoc/kg_assoc_100m/`:

- r001: `banks/e2_attempts/F03_N010_RP080_EE08/equilibrate_bb4106da56cf4e7e888fb4ef8aa73e7c/r001/state`; absolute step 6,000,000; chemistry/MD/effective MD seeds `420001/520058/224804373`.
  `.restart.lammpsdat` SHA256: `78e0761f345384981dd693115243165a1c95123434d8727485fd17b6a29c8266`.
  `.assoc_restart` SHA256: `070a071f7afa5209ba0d131e8818b48132f5c4ce2ef2fb342bb4ef9c7e74bfdb`.
- r002: `banks/e2_attempts/F03_N010_RP080_EE08/equilibrate_bb4106da56cf4e7e888fb4ef8aa73e7c/r002/state`; absolute step 6,000,000; chemistry/MD/effective MD seeds `420002/520059/216436245`.
  `.restart.lammpsdat` SHA256: `22307f458b1ff2cdecb6561a6e314a4dca4e51cdd3791582d46bc51a016911a6`.
  `.assoc_restart` SHA256: `aa64efd4547d9ff60b08024c96be184cf18a30077179f1306017243d7b6676de`.
- r003: `banks/e2_attempts/F03_N010_RP080_EE08/equilibrate_bb4106da56cf4e7e888fb4ef8aa73e7c/r003/state`; absolute step 6,000,000; chemistry/MD/effective MD seeds `420003/520060/241557021`.
  `.restart.lammpsdat` SHA256: `ed9d634aba94ea4af1d535891446ddb7aa1139c8f144fcf599e1ac7c1653dc3e`.
  `.assoc_restart` SHA256: `826f6496008867c139728ebc3b39c68c2bbc5bdce6f36c6c3fa14ca3a9bda2d4`.

All are absolute 6,000,000 steps, T=1, dt=0.01, f=3, N=10, Ee=8 and Ea=4,
with all other parameters frozen in the authenticated plan. These are this attempt's
r001/r002/r003 reviewed states, not scientifically accepted production starts.

**Next user decision:** whether to authorize the proposed additional 2M E2
checkpoint per original history (6–8M). Until a further scientific review resolves
the hold, no formal acceptance of these 6M states is recommended. Registry
activation, production preparation/launch and any other condition remain
unapproved and outside this recommendation.
