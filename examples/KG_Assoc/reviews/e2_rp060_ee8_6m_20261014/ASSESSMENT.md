# RP060, Ee8: scientific assessment at absolute 6M

**Recommend qualified acceptance of exactly r001/r002/r003 at 6,000,000 steps
solely as `production_initial_state` for `F04_N010_RP060_EE08_EA04`.** Further E2
is not warranted by the combined evidence for this restricted use. Complete
stationarity, slow-topology decorrelation and freedom from initialization bias
are not established. This recommendation registers no acceptance, selects no
endpoint and authorizes no production. The observed late chemical redistribution
and r003 excursion remain qualifications, not evidence silently discarded.

Review began 2026-10-14 and finished 2026-10-15 (Europe/Madrid). Starting HEAD:
`01ecb1bc0abd072c705096b778e28d611e0a81d7`, branch `KremerGrest`. The final SHA
is the commit containing this immutable dossier, reported with the push result.
Only this new review directory changes.

## Authenticated scope and method

The specified attempt `equilibrate_92296b2a776e4d7191107126faf376bd` authenticates
against plan SHA256 `b7b2fccab78d289518b7d477096eb3307affda61798dcc94ddd62911c8d900e5`.
All three histories passed fresh CPU numerical, event, graph, endpoint and
conformation validation: 6,001 samples each and 211200/209838/211013 accepted
events. Source/build manifests, current executable bytes, build logs, commands,
seeds, approvals, smoke bindings, completion receipts and output hashes checked.
r002 starts from the accepted active E1 **retry attempt001**, not the failed
original. Its snapshot hash agrees with the active map and frozen inventory.
E1 parents contain no chemical sidecar; all three start with empty chemistry.
Final sidecars agree with reciprocal stable-ID event replay and absolute counters.
See [exact identities and hashes](ENDPOINTS.md) and [authentication](AUTHENTICATION.json).

The reference semantics were inspected in the local LAMMPS
`feature/associating-stickers` checkout at
`1c6faf70e94aef2389c208e8c80c60c084a96907`; the four implementation files are
hash-bound in authentication. Both reaction directions require candidates inside
`r_assoc=1.25`; existing bonds remain mechanically active below `R0=1.5`.
Association adds shifted FENE without another WCA contribution. The exact
finite-step attempt probability uses Ea=4, Ee=8, T=1, nu0=20, Nevery=100,
dt=0.01. Accepted rates below are observed event rates, not independent attempts
or a measure of complete network mixing. Ea sets the attempt scale; Ee enters
the energetic acceptance factor. Exact coupled-integrator equilibrium invariance
is not established by this assessment. No physics or CUDA source changed.

The **entire 0–6M context** is retained in frame exports and nonoverlapping
500k, 1M and 2M tables, including early paired contrasts. Step zero has no bonds;
the first/second 500k ensemble bound fractions are 0.873213/0.879770, and
satellite-star means fall from 2.524 to 0.525. Early windows describe preparation,
not a stationary baseline. No initial chemistry transient was removed.
[Complete tables](evidence/WINDOWS.md), [estimates](evidence/window_estimates.csv)
and [summary](evidence/summary.json) retain every replica, interval and uncertainty.

## Multiplicity and chemical populations

The coarse evolution is:

| Three-history mean | 0–2M, including transient | 2–4M | 4–6M |
|---|---:|---:|---:|
| Total bonds | 1756.383 | 1761.086 | 1761.413 |
| Intra bonds | 105.161 | 111.163 | 107.140 |
| Inter bonds | 1651.222 | 1649.923 | 1654.273 |
| L1 parallel-bond pairs | 45.595 | 43.576 | 45.272 |
| L2 distinct-star triangles | 36.364 | 35.207 | 36.597 |
| Rg² | 7.309596 | 7.300300 | 7.300831 |
| Center–terminal R² | 16.541645 | 16.512194 | 16.517953 |

L1 changes from 2–4M to 4–6M are +0.4395/+4.464/+0.184, ensemble
**+1.696 ± 5.964** (paired 95% half-width). The preceding 2M change was negative
in every replica. From 4–5M to 5–6M, L1 changes −7.555/+5.391/+6.432; final
500k changes +0.514/−0.350/+0.606. r001's late fall and r002/r003's rises are
real, but do not form a common sustained direction. This supports a bounded
fluctuating late level with poorly sampled slow modes, not proven motif equilibrium.

L2 increases in all three histories in the primary contrast (+0.460/+2.373/+1.338,
mean **+1.390 ± 2.379**) and the last 1M contrast (+0.378/+1.897/+1.571).
Those shared increases cannot be erased by broad intervals. However, final-quarter
changes are −4.440/−0.516/−10.468, and 4–6M remains within the earlier 500k/1M
triangle range. r003's 5.5–5.75M triangle spike reverses in 5.75–6M. Combined
paths favor fluctuations over uninterrupted triangle accumulation.

Full inter-star distributions count **distinct permanent-star pairs**, including
all allowed bond multiplicities. At every frame,
inter = sum(m × edges_m) and L1 = sum(choose(m,2) × edges_m).

| Bonds per distinct star pair | 2–4M mean pair count | 4–6M mean pair count |
|---|---:|---:|
| 1 | 1564.0700 | 1564.9075 |
| 2 | 42.2768 | 44.0982 |
| 3 | 0.4330 | 0.3868 |
| 4 | 0 | 0.00217 |

The quadruple state is actually observed in r002 at 13 sampled frames in 4–6M;
the other histories' zero counts are not proof of exclusion or mixing. Double-pair
changes +0.936/+4.200/+0.328 dominate the primary L1 increase; triples change
−0.1655/+0.075/−0.048. The late parallel-edge fraction is about 0.02765.
Intra-loop distributions are also retained: late means of stars carrying 0/1/2
intra bonds are 893.746/105.369/0.886. [Multiplicity paths](evidence/multiplicity.png)
show the coupled fluctuations rather than a single hidden mean.

Primary intra changes are **+3.3035/−7.173/−8.2005** and inter changes
**−4.375/+9.4615/+7.9645**. r001 therefore differs materially in direction from
r002/r003. Total bond change is +0.327 ± 4.346; this stable total does not prove
stationarity of the intra/inter partition. More concerning, all three have
4–5M → 5–6M intra losses −5.339/−3.890/−2.718 (mean **−3.982 ± 3.262**) and
inter gains +5.625/+4.222/+2.921 (**+4.256 ± 3.360**). All late-2M intra slopes
are negative. This is retained evidence of redistribution. It is not a persistent
common change across the earlier 2M windows: r001 rises between those windows,
and its final quarter rebounds by 9.676 intra bonds. r002/r003 continue losing
intra population late. The residual is a qualification for initialization and
future interpretation of loop-sensitive observables, not a claim of exact balance.

## r003 conformation and graph connectivity

Rg² and center–terminal R² use permanent-bond minimum-image unwrapping; the final
snapshot is independently reconstructed. Primary shape changes are
−0.01311/−0.01318/+0.02788 in Rg² and −0.03880/−0.02220/+0.07827 in terminal R².
Their means are +0.000531 ± 0.058847 and +0.005759 ± 0.157365. These opposite
replica changes do not establish shared expansion or contraction.

r003's Rg² means at 4–5M, 5–5.5M and 5.5–6M are
7.316800, 7.287574 and 7.350457; terminal R² values are
16.546001, 16.488689 and 16.663193. Thus the last 500k excursion is substantial
relative to its preceding window, but the 4–5M → 5–6M changes are only
+0.002215/+0.029941. Final-quarter means rise from 7.322081/16.582739 to
7.378833/16.743646; both final-quarter fitted slopes turn negative. The exact 6M
endpoint is 7.304349/16.479480. Endpoint return alone is not stationarity evidence:
the last 100k means remain elevated at 7.365976/16.750204. The excursion lies
within the observed post-1M frame range, and the coarse paths show recurrent
expansions/contractions, including r001. It remains a sampling qualification,
not a numerical anomaly or demonstrated sustained conformational relaxation.
[Full shape paths](evidence/shape.png) preserve this distinction.

The late giant fraction is 0.996894, with 2.6825 isolated stars and 0.4237
non-singleton satellite stars among 1000 permanent stars. Satellite components
average 0.1983. Primary giant changes +0.000625/+0.0000235/−0.000408 are mixed;
isolated changes −0.589/−0.011/+0.644 are likewise mixed. All three satellite
populations decline in the primary contrast, by only 0.036/0.0125/0.236 stars;
r002/r003 rebound in the next 1M contrast. No common progressive erosion or
growth of bulk connectivity is evident. These quantities are coupled by graph
identities and are not independent confirming tests.

Late distinct-degree fractions for degrees 0/1/2/3/4 are
0.002683/0.031527/0.164851/0.346199/0.454741. Primary mean-degree changes
−0.009960/+0.010184/+0.015465 and second-moment changes
−0.061388/+0.049721/+0.078837 are mixed. Degree-1 falls in every history in
the shifted 3–5M → 4–6M comparison; it is retained, but degree-4 changes have
mixed signs and the final-quarter degree-4 change is −/−/+.
Bulk/peripheral coordination therefore does not show a single continuing drift.

## Kinetics, uncertainty and density comparison

Late accepted creations/breaks average **1.74038/1.73982 per physical time**;
distinct-neighbor gains/losses average **1.54635/1.54515**. Primary paired changes
are −0.00125 ± 0.03450, −0.00170 ± 0.03387, +0.000017 ± 0.02514 and
−0.00133 ± 0.02998 respectively, with mixed replica signs. Event-integrated
exposures give creation rates per free-sticker time of 0.00364–0.00366 and
rupture rates per active-bond time of 0.000980–0.000992. Reaction activity and
neighbor turnover persist; they do not certify mixing of collective slow modes.

Each interval has its own first-nonpositive-lag IAT and 5/10/20-block SEM estimate.
**The three histories are the independent units**, with paired Student-t df=2
uncertainties. No frames, blocks or windows are promoted to independent replicas.
Overlapping contrasts are descriptive sensitivity checks, not extra replication;
all intervals are exploratory/unadjusted. Zero-containing intervals are never
treated as proof of stationarity or equivalence.

| 4–6M observable | IAT, physical time (replica range) | Effective samples (range) |
|---|---:|---:|
| Total bonds | 80–112 | 90–125 |
| L1 | 1113–1480 | 6.8–9.0 |
| L2 | 281–545 | 18–36 |
| Intra | 608–832 | 12–16 |
| Rg² | 169–561 | 18–59 |
| Terminal R² | 125–506 | 20–80 |

L1 blocking SEM ranges are 1.248–1.978, 1.116–1.721 and 1.319–2.043 across
20/10/5 blocks, versus IAT SEMs 2.445/2.047/2.551. Slow-mode uncertainty does
not stabilize at one block size. r003's 5–6M shape IATs are 870/777, giving only
5.75/6.44 effective samples; its Rg² blocking SEM changes from 0.01891 (5 blocks)
to 0.00999 (20). Short final-quarter estimates, although much smaller, cannot
certify sampling of the longer excursion. Finite-window IATs can miss even slower
relaxation and are unreliable stationary interpretations during drift/transients.
Constant distributions have explicit nonmixing flags; their nominal effective
sample counts must not be interpreted physically.

The **qualified 8M** RP040 and RP080 records, endpoint payload hashes and matching
f=4, N=10, Ee=8, Ea=4 parameters authenticated. Compare their qualified 6–8M raw
means with RP060 4–6M, without requiring equal density-dependent observables:

| Observable | RP040 | RP060 | RP080 |
|---|---:|---:|---:|
| Bound fraction | 0.852854 | 0.880706 | 0.897003 |
| Intra bonds | 144.355 | 107.140 | 95.454 |
| Inter bonds | 1561.353 | 1654.273 | 1698.551 |
| Mean distinct degree | 3.02276 | 3.21879 | 3.31856 |
| Giant fraction | 0.992580 | 0.996894 | 0.997694 |
| L1 | 50.372 | 45.272 | 39.646 |
| L2 | 36.742 | 36.597 | 33.394 |

RP060 has a plausible intermediate density dependence. L2 need not interpolate
linearly. RP040's earlier 6M hold involved shared motif evolution later qualified
after reversal at 8M; RP060's current L1 paths already have mixed late directions.
Neighbor acceptance is context, not a stopping rule or equilibrium proof for RP060.
Only corrected RP080 recovery values enter; defective historical C1 windows are
excluded. Neighbor trajectories were not freshly replayed in this task, and
comparable RP080 shape diagnostics are unavailable in these raw scalar files.

## Decision and remaining limits

The recommendation rests on stable total chemistry, recurrent motif reversals,
opposite primary intra/inter and shape changes, bounded coarse conformations,
persistent exchange and stable bulk connectivity together. It does **not** rest
on confidence intervals including zero. Common late intra/inter redistribution,
poorly resolved L1 modes, rare multiplicities/satellites and r003's excursion mean
loop-sensitive, topology-sensitive and early-production observables may retain
initialization bias. Equilibrium inference from subsequent production must assess
that separately. Those limits do not presently demonstrate a material failure of
the exact endpoints for qualified initialization alone. No additional E2 is
proposed or launched; no GPU operation, formal registration, registry selection,
activation or production preparation is performed.

[CPU validation and reproduction](VALIDATION.md) document checks and limitations.
Protected `examples/KG/`, `src/`, frozen campaign files, simulation outputs,
accepted E2 records and existing evidence are unchanged.
