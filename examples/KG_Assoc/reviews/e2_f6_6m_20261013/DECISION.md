# f=6 E2 scientific joint review through 6M

**Recommendation: qualified acceptance of the three 6M endpoints for production
initialization**, subject to separate user approval and formal registration.
Slow network-topology decorrelation is not fully demonstrated. This recommendation
creates no formal acceptance, active registry selection or production authorization.

System: `F06_N010_RP080_EE08_EA04`; starting local and remote `KremerGrest`
SHA `a292d97efb12e81910908d1c06d7f6ee420fef17`. The exact source plan is
`banks/e2_attempts/F06_N010_RP080_EE08/equilibrate_2092711490194045aa2036a7e00b4bd0/plan.json`,
SHA256 `fcbe320a4cba7af129f17475f7b09d46fb69239ad6cda9d28d63c988ce765d25`.

## Authentication and method

All three original E1 identities, E2 plans/approval, parent hashes, replica/seed
coverage, completion receipts, numerical data, every accepted chemical event,
network reconstruction, conformation data and endpoint payloads were independently
CPU revalidated with the existing tools. Scientific source/build/log and current
executable hashes authenticate. No historical-executable-byte limitation arose
for this f=6 attempt. The evolving read-only joint review driver is authenticated
at the source commit recorded in the original plan; this report's driver is
separately bound by its exact SHA256 in the new analysis config.

The original 500k-window review's input/config/report hashes and plan association
also authenticate. It remains unchanged in
`aggregate/e2/review_070ba7342fa445c7ba0d36de8d75cd54/`. The full validation,
lineage and precise output hashes are in [provenance.json](provenance.json).

Each replica has one continuous 0–6M E2 trajectory, with no intermediate MD
reseed, extension or algorithm change. Cuts at 1M, 2M and 4M are analysis
boundaries only. Statistics use non-overlapping 1M windows and separate 2–4M /
4–6M 2M windows within that continuous trajectory. The full 0–1M interval retains
the initially unbound association transient as context; 1–2M remains an early
comparator, not retrospectively certified stationary. The candidate late
preparation interval is 2–6M. No trajectory fragments or stars are treated as
additional independent replicas; paired differences use three histories with
Student-t df=2. IAT and 5/10/20-block sensitivity use the unchanged validated
helpers. All intervals are exploratory 95% intervals, unadjusted for the many
observable/window comparisons. Nonsignificance does not establish stationarity.

## Complete history, ensemble window means

The initial state is unbound (6,000 free stickers). First-window means average
the evolving transient, rather than the instantaneous step-zero state. Rates
below are accepted events per MD time unit (`dt=0.01`); distinct-neighbor turnover
counts unique inter-star edges rather than individual inter-star bonds. L1 counts
parallel inter-star bond pairs; L2 distinct-star triangles. Conformations use
permanent-bond minimum-image unwrapping. Temperature and bond-length diagnostics
are also retained in [REPORT.md](joint6m/REPORT.md) and the full summary.

| Observable | 0–1M context | 1–2M | 2–3M | 3–4M | 4–5M | 5–6M |
|---|---:|---:|---:|---:|---:|---:|
| bonds | 2686.779 | 2693.016 | 2693.217 | 2693.213 | 2693.673 | 2692.94 |
| bound_fraction | 0.8955929 | 0.8976721 | 0.8977389 | 0.8977378 | 0.8978911 | 0.8976468 |
| intra | 211.712 | 210.227 | 210.6403 | 216.3853 | 209.285 | 205.9423 |
| inter | 2475.067 | 2482.789 | 2482.576 | 2476.828 | 2484.388 | 2486.998 |
| mean_degree | 4.679317 | 4.697865 | 4.691786 | 4.680957 | 4.700425 | 4.695573 |
| second_degree_moment | 23.06732 | 23.21732 | 23.16115 | 23.05661 | 23.22666 | 23.17689 |
| components | 1.307333 | 1.182 | 1.191333 | 1.199 | 1.180667 | 1.180333 |
| largest_cluster_fraction | 0.9996653 | 0.9998153 | 0.9998077 | 0.999801 | 0.9998193 | 0.999818 |
| L1 | 139.5903 | 138.5473 | 140.0657 | 140.5357 | 138.3433 | 143.711 |
| L2 | 168.1067 | 169.8773 | 170.0103 | 167.4903 | 166.364 | 166.6403 |
| mean_rg2 | 7.976423 | 7.980036 | 7.981601 | 7.970616 | 7.985403 | 7.989257 |
| mean_center_terminal_r2 | 16.56886 | 16.57991 | 16.57178 | 16.55176 | 16.59318 | 16.60292 |
| creations | 3.014267 | 2.7384 | 2.743033 | 2.739767 | 2.744667 | 2.753967 |
| breaks | 2.743133 | 2.740833 | 2.743333 | 2.7404 | 2.743133 | 2.7544 |
| neighbor_gains | 2.494967 | 2.2576 | 2.259367 | 2.247733 | 2.268833 | 2.2623 |
| neighbor_losses | 2.2575 | 2.2611 | 2.258933 | 2.247967 | 2.267367 | 2.2651 |

## Paired longer-window contrasts

4–6M minus 2–4M; the three changes are r001/r002/r003, not independent windows:

| Observable | Replica changes | Paired mean ± 95% half-width |
|---|---|---:|
| bonds | +0.0955 / +2.3265 / -2.1465 | +0.09183333 ± 5.556228 |
| bound_fraction | +3.18333e-05 / +0.0007755 / -0.0007155 | +3.061111e-05 ± 0.001852076 |
| intra | -10.1985 / -8.036 / +0.537 | -5.899167 ± 14.10555 |
| inter | +10.294 / +10.3625 / -2.6835 | +5.991 ± 18.66338 |
| mean_degree | +0.02036 / +0.031626 / -0.017103 | +0.01162767 ± 0.06337834 |
| second_degree_moment | +0.157755 / +0.274675 / -0.153733 | +0.092899 ± 0.5501453 |
| components | -0.005 / -0.035 / -0.004 | -0.01466667 ± 0.0437648 |
| largest_cluster_fraction | +2.5e-06 / +3.65e-05 / +4e-06 | +1.433333e-05 ± 4.772797e-05 |
| L1 | +0.6745 / -5.8035 / +7.3085 | +0.7265 ± 16.28771 |
| L2 | -4.271 / +5.1385 / -7.612 | -2.248167 ± 16.42535 |
| mean_rg2 | +0.016333 / +0.0145528 / +0.00277853 | +0.01122144 ± 0.01829904 |
| mean_center_terminal_r2 | +0.0515265 / +0.0465205 / +0.0107872 | +0.03627806 ± 0.05519488 |
| creations | -0.006 / +0.00405 / +0.0257 | +0.007916667 ± 0.04024596 |
| breaks | -0.0046 / +0.0017 / +0.0236 | +0.0069 ± 0.0367724 |
| neighbor_gains | +0.0046 / +0.0224 / +0.00905 | +0.01201667 ± 0.02301345 |
| neighbor_losses | +0.0088 / +0.018 / +0.01155 | +0.01278333 ± 0.01173198 |

## Interpretation of conformation and bond repartitioning

The late increase is real as a descriptive change in the chosen means:
Rg² rises by about 0.01122 (~0.14%) and center–terminal R² by 0.03628 (~0.22%).
Both changes have positive signs in all three histories. The paired intervals
are ±0.01830 and ±0.05519 respectively; these do not exclude appreciable modest
drift. They must not be rewritten as evidence of no change.

However, the complete histories do not show a shared monotonic increase.
r002's Rg² is 8.0113 at 1–2M, 7.9716 at 3–4M and 7.9896 at 5–6M;
r003 fluctuates 7.9582/7.9875/7.9722/7.9865/7.9788 through 1–6M.
r001 shows the clearest late rise (7.9681 to 7.9829 to 7.9993 over 3–6M),
while r003 declines in the latest 1M interval. Arm diagnostics show analogous
excursions, with latest decreases in r002 and r003. The long-window increase
is small relative to these within-history excursions and does not represent a
uniform continuing trend across the entire candidate interval. This supports
stationary slow fluctuations as a reasonable explanation, without proving it.

Intra bonds shift by −5.899 ± 14.106 and inter bonds by +5.991 ± 18.663.
r001/r002 lose about 10.20/8.04 intra bonds while r003 changes +0.54.
Total bond count changes only +0.0918 ± 5.556, so the signal is predominantly
repartitioning rather than continuing association buildup. The partition means
are nonmonotonic: r002 intra rises from 204.47 to 226.55 between 2–3M and 3–4M
before falling to 199.96 at 5–6M; r001 falls then rebounds in the latest window.
The data are compatible with slow exchange fluctuations but leave some residual
initialization-dependent repartitioning unresolved.

L1 changes +0.727 ± 16.288 with mixed replica signs; L2 −2.248 ± 16.425,
also with mixed signs. The latest 1M L2 shifts in opposite directions for r001
and r002; no coherent structural descent or growth is shared by all histories.
Connectivity is essentially a system-spanning network already; nearly constant
largest-cluster fraction and component counts are insensitive to some slow
internal rearrangements and cannot prove mixing. Degree and second-moment
statistics provide additional stable distribution diagnostics, not independent
replicas or substitutes for motif relaxation.

Creation/rupture activity remains about 2.74–2.76 per MD time unit, with distinct
neighbor gains/losses around 2.25–2.27. This demonstrates ongoing accepted bond
and neighbor exchange rather than kinetic arrest. Neighbor-loss activity rises
+0.01278 ± 0.01173 (~0.57%); its exploratory interval excludes zero. This small
resolved change is retained, not ignored as inconvenient. Gain activity also
increases descriptively (+0.01202 ± 0.02301), and creation/rupture changes have
mixed replica signs. These rate changes do not establish sustained population
or network growth. Activity rates are not bond residence-time, stress or transport
measurements, and do not prove replacement of every slow structural mode.

## Correlation and blocking limitations

Tool IAT estimates are in MD time units and effective counts are estimates for
window means. Block sensitivity compares 5/10/20 blocks within each window;
smaller blocks can remain correlated. These are diagnostic resolution flags,
not arbitrary scientific acceptance thresholds.

| Window | Replica | Mode | IAT time | Effective samples | IAT SEM | Block SEM 5 / 10 / 20 |
|---|---|---|---:|---:|---:|---|
| 2–4M | r001 | L1 | 460.56 | 21.713 | 2.2118 | 2.4311 / 2.1473 / 1.9404 |
| 2–4M | r001 | L2 | 739.29 | 13.526 | 3.7311 | 3.6313 / 3.35 / 2.6773 |
| 2–4M | r001 | intra | 968.48 | 10.325 | 2.7199 | 2.7526 / 1.9961 / 1.5746 |
| 2–4M | r001 | inter | 454.68 | 21.994 | 2.7583 | 3.1528 / 2.1188 / 1.722 |
| 2–4M | r001 | mean_rg2 | 332.28 | 30.095 | 0.0071293 | 0.0069127 / 0.0070894 / 0.0052769 |
| 2–4M | r001 | mean_center_terminal_r2 | 196.51 | 50.887 | 0.015093 | 0.015895 / 0.014814 / 0.011266 |
| 2–4M | r002 | L1 | 621.57 | 16.088 | 2.7324 | 3.0732 / 2.3231 / 1.9457 |
| 2–4M | r002 | L2 | 1284.5 | 7.7852 | 4.7162 | 4.0915 / 3.3052 / 2.4289 |
| 2–4M | r002 | intra | 1959.3 | 5.104 | 6.971 | 5.9387 / 4.5593 / 3.3733 |
| 2–4M | r002 | inter | 1453.1 | 6.8818 | 7.4823 | 6.7067 / 5.1168 / 3.6443 |
| 2–4M | r002 | mean_rg2 | 332.31 | 30.092 | 0.0077934 | 0.0059857 / 0.0071034 / 0.0056025 |
| 2–4M | r002 | mean_center_terminal_r2 | 374.8 | 26.681 | 0.023272 | 0.019079 / 0.020996 / 0.016057 |
| 2–4M | r003 | L1 | 309.46 | 32.314 | 1.4623 | 1.472 / 1.3934 / 1.2816 |
| 2–4M | r003 | L2 | 449.36 | 22.254 | 2.778 | 3.4242 / 3.0004 / 2.433 |
| 2–4M | r003 | intra | 1017.6 | 9.8266 | 4.0484 | 4.6123 / 3.3926 / 2.6223 |
| 2–4M | r003 | inter | 631.14 | 15.844 | 3.949 | 4.4716 / 3.5525 / 2.6067 |
| 2–4M | r003 | mean_rg2 | 572.99 | 17.452 | 0.010174 | 0.010525 / 0.0074249 / 0.0057851 |
| 2–4M | r003 | mean_center_terminal_r2 | 515.74 | 19.389 | 0.027305 | 0.025973 / 0.019847 / 0.015858 |
| 4–6M | r001 | L1 | 903.65 | 11.066 | 4.8042 | 5.4563 / 4.1104 / 3.2532 |
| 4–6M | r001 | L2 | 984.6 | 10.156 | 4.5639 | 4.2809 / 3.8214 / 2.873 |
| 4–6M | r001 | intra | 600.19 | 16.662 | 2.6354 | 2.5415 / 2.1603 / 2.1589 |
| 4–6M | r001 | inter | 333.6 | 29.976 | 2.8036 | 2.9515 / 2.4585 / 2.3905 |
| 4–6M | r001 | mean_rg2 | 603.54 | 16.569 | 0.0099327 | 0.0094148 / 0.0069134 / 0.0050776 |
| 4–6M | r001 | mean_center_terminal_r2 | 583.54 | 17.137 | 0.029137 | 0.026207 / 0.019038 / 0.015867 |
| 4–6M | r002 | L1 | 670.15 | 14.922 | 2.5023 | 2.7821 / 2.0209 / 1.6975 |
| 4–6M | r002 | L2 | 817.59 | 12.231 | 3.4372 | 2.7778 / 2.6084 / 2.1546 |
| 4–6M | r002 | intra | 917.24 | 10.902 | 3.6331 | 2.8892 / 3.3301 / 2.4824 |
| 4–6M | r002 | inter | 492.67 | 20.298 | 3.8696 | 3.095 / 3.8086 / 2.8522 |
| 4–6M | r002 | mean_rg2 | 366.81 | 27.262 | 0.0080932 | 0.0081314 / 0.0079954 / 0.0059499 |
| 4–6M | r002 | mean_center_terminal_r2 | 421.48 | 23.726 | 0.025878 | 0.027646 / 0.023578 / 0.018348 |
| 4–6M | r003 | L1 | 531.77 | 18.805 | 2.6477 | 2.5887 / 2.5852 / 2.05 |
| 4–6M | r003 | L2 | 278.3 | 35.933 | 2.0935 | 2.5518 / 2 / 1.9621 |
| 4–6M | r003 | intra | 660.51 | 15.14 | 3.189 | 3.2931 / 3.3246 / 2.5126 |
| 4–6M | r003 | inter | 329.02 | 30.393 | 3.1044 | 2.9278 / 3.2275 / 2.7235 |
| 4–6M | r003 | mean_rg2 | 153.09 | 65.323 | 0.0048059 | 0.0042229 / 0.0055294 / 0.0045881 |
| 4–6M | r003 | mean_center_terminal_r2 | 141.79 | 70.524 | 0.012527 | 0.0059989 / 0.013262 / 0.011085 |

The slowest early mode is r002 intra at 2–4M: IAT about 1,959 time units,
only 5.1 estimated effective samples, and IAT SEM 6.97 versus 5/10/20-block
SEMs 5.94/4.56/3.37. r002 inter and L2 also have limited early effective support
(6.9 and 7.8). In the late 4–6M window the L1/L2 effective counts span about
10.2–35.9; intra 10.9–16.7 and inter 20.3–30.4. Late conformational counts span
16.6–70.5. This improves the assessment beyond 500k windows but does not
establish full mixing. For r001 late L1, IAT SEM is 4.80 versus block SEMs
5.46/4.11/3.25; small-block precision can be misleading.

Finite-window IAT estimates are sensitive to truncation and slow modes. Three
independent histories provide broad paired intervals and weak power for small
systematic changes. Window choice was made with knowledge of earlier plots;
all contrasts remain exploratory. Complete topology decorrelation, asymptotic
stationarity, absence of aging and absence of initialization bias are not proven.
The combined evidence—population plateau, nonmonotonic replica paths, mixed
motif changes, active turnover, stable connectivity/degree statistics and small
conformation/repartitioning effects—supports **qualified initialization** rather
than an unqualified equilibrium claim. No numerical threshold or nonsignificant
difference is used as an automatic acceptance rule. Further equilibration is
not recommended solely to prove full topological decorrelation for this purpose;
no continuation is authorized by this review.

## Exact proposed endpoints

Prefixes are relative to `examples/KG_Assoc/kg_assoc_100m/`:

- r001: `banks/e2_attempts/F06_N010_RP080_EE08/equilibrate_2092711490194045aa2036a7e00b4bd0/r001/state`; step 6,000,000; chemistry/MD/effective MD seeds `421101/520052/308502045`.
  `.restart.lammpsdat` SHA256: `8c1b89e5df342b817663d112aa2915fddf634cdd06d2c61e38c89d7584da1b52`.
  `.assoc_restart` SHA256: `1f96096faf35b9d743a76e815fe4f1af75961cff5f8daa22fad8091a0e4f3992`.
- r002: `banks/e2_attempts/F06_N010_RP080_EE08/equilibrate_2092711490194045aa2036a7e00b4bd0/r002/state`; step 6,000,000; chemistry/MD/effective MD seeds `421102/520053/300133917`.
  `.restart.lammpsdat` SHA256: `92b67aca1dadbb241409834f1a67c21a81c314ed271b94e8313aaefa03ecf42d`.
  `.assoc_restart` SHA256: `84ef7cd2bfc58bfc7b29a8e40b4571e9d6fb734937feb44482157b9390a21a32`.
- r003: `banks/e2_attempts/F06_N010_RP080_EE08/equilibrate_2092711490194045aa2036a7e00b4bd0/r003/state`; step 6,000,000; chemistry/MD/effective MD seeds `421103/520054/325254685`.
  `.restart.lammpsdat` SHA256: `d5952541ff336fb7cc72502c58429476cdee59fd1ed72df010f18147ce72ce27`.
  `.assoc_restart` SHA256: `b86d5585047774f0fdbd860b7709ccd384173cde152436182f4ae964cec3bb06`.

All endpoints are absolute step 6,000,000 with T=1, dt=0.01, Ea=4, Ee=8,
f=6 and N=10; all other physical parameters remain frozen in the source plan.
No smoke state or another attempt is proposed. User approval is required before
formal scientific acceptance registration. Registry activation and production
launch would be separate subsequent authorizations.
