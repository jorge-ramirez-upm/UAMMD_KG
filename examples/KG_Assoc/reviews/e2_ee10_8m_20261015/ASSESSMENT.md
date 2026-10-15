# Ee10 at absolute 8M: scientific hold

**Hold qualified production initialization of the exact three 8M endpoints of
`F04_N010_RP080_EE10_EA04`.** The endpoints are numerically valid and authenticated,
but the late intra/inter redistribution remains unresolved, particularly in r001
and r002, and is accompanied by changing distinct coordination and peripheral
connectivity. Bounded excursions are also present; this is not proof that all
histories undergo one irreversible relaxation. The available paths do not yet
adequately distinguish that possibility from a settled late regime for these
exact endpoints. Stable total occupancy and zero-containing intervals do not
resolve the concern.

Propose **4M additional steps per original history, to absolute 12M**, with a
scientific checkpoint at 10M. This is a documented proposal only: no simulation,
extension plan, approval, acceptance, selection, activation or production operation
was created. Complete structural decorrelation is not an automatic requirement.

Review date: 2026-10-15, Europe/Madrid. Starting local/remote `KremerGrest` SHA:
`49ffc4006763e0409e06cc12cdd0dd7eba7d2fe7`; working tree initially clean.
The final SHA is the containing assessment commit, reported after push.

## Authenticated evidence and statistical units

Attempt: `equilibrate_fb8954dc860740d6b923759b2b21a703`; plan SHA256:
`489af3d03ca1d54a1c42515b59961fea7fa889378410b5ddac8b835bd8f06812`.
Fresh CPU validation passed for all three 0–8M histories: **8,001 frames each**,
54118/53832/53545 accepted events and 1932/1918/1921 final bonds. E1 parents,
active/frozen inventory, source/build/current executable bytes, commands, chemical
and MD/effective seeds, approval/smoke bindings, completion receipts and every
output hash authenticated. Stable permanent identities, reciprocal valence-one
partners, event replay, numerical diagnostics, network accounting, conformation
cadence and independent endpoint unwrapping passed. E1 parents begin with empty
chemistry; no input chemical sidecar is assumed. [ENDPOINTS.md](ENDPOINTS.md)
identifies every exact restart/sidecar pair and seed. Historical E1 executable
bytes remain unauthenticated independently; records and available input/output
bytes are authenticated.

All original frames, including the initially unbound step zero, remain exported.
Nonoverlapping **500k, 1M and 2M windows cover all 0–8M**. Late 250k windows and
shifted contrasts test sensitivity. Initial windows are preparation context, not
asserted stationary comparators. [WINDOWS.md](evidence/WINDOWS.md) gives complete
coarse context; [window estimates](evidence/window_estimates.csv) and
[summary](evidence/summary.json) preserve all replica estimates and contrasts.

Only the **three original histories** are independent statistical units. Paired
Student-t intervals have df=2; displayed ± values are 95% half-widths, not
equivalence bounds. Contrasts are exploratory, unadjusted and mutually correlated;
overlapping windows add no replication. IAT/SEM estimates are interval-local in
these continuous original MD streams. No window mean or block becomes another
independent history. Zero-containing confidence intervals never prove stationarity.

## Intra/inter redistribution: genuine late evolution, with counterevidence

| Three-history mean | 0–2M, transient retained | 2–4M | 4–6M | 6–8M |
|---|---:|---:|---:|---:|
| Total bonds | 1917.771 | 1920.787 | 1922.150 | 1920.772 |
| Intra bonds | 100.504 | 97.345 | 94.203 | 103.352 |
| Inter bonds | 1817.268 | 1823.442 | 1827.947 | 1817.420 |
| L1 parallel-bond pairs | 44.674 | 49.107 | 42.801 | 40.236 |
| L2 distinct-star triangles | 39.262 | 41.760 | 43.000 | 36.616 |
| Giant fraction | 0.998743 | 0.999166 | 0.999011 | 0.998206 |
| Rg² | 7.037064 | 7.035962 | 7.022437 | 7.047982 |
| Center–terminal R² | 15.905467 | 15.910231 | 15.868011 | 15.941257 |

The requested 4–6M → 6–8M intra changes reproduce as
**+14.569/+9.7505/+3.127**, mean **+9.149 ± 14.272**; inter changes are
**−16.1925/−11.7105/−3.679**, mean **−10.527 ± 15.751**. Total bonds change
only −1.379 ± 1.827 and late bound fraction is 0.960386. This occupancy stability
conceals a change in the partition of association and is not network equilibration.

This is not solely an unfortunate choice of 2M boundaries. The shifted
4.5–6.5M → 5.5–7.5M changes are intra +7.3745/+7.0745/+2.306 and inter
−7.8125/−8.5075/−2.140, preserving the shared direction. The 5–7M → 6–8M
intra changes are +10.687/+8.035/−1.7485; the last 1M contrast gives
**+12.409/+10.710/−7.268**. Thus r003 reverses, while r001/r002 retain the
late redistribution on several scales. Their 6–8M fitted intra slopes imply
+12.368/+10.189 bonds per million steps, versus −5.254 in r003; inter slopes
are −11.550/−9.917/+6.377 per million.

There is meaningful counterevidence to uninterrupted relaxation: the earlier
ensemble intra level declined from 100.5 through 97.3 to 94.2 before rising;
r003 traverses an early high-loop excursion and reverses again after 6.5–7M.
r002 is flattening: its last-1M intra slope is only +0.604 per million, and the
final-quarter mean changes −0.432. But r001's last-1M slope remains +12.791
and its successive late-quarter means end at 102.8, 104.5, 109.2, 111.9.
The exact r001 endpoint has 111 intra bonds. A bounded late regime remains
plausible; it has not yet been demonstrated convincingly enough in this coupled
population/coordination path. The hold reflects that unresolved material path,
not a universal percentage or sample-count threshold.

## Motifs and full bond-multiplicity distributions

L1 counts parallel **bond pairs**, not just multiply connected star pairs;
L2 counts distinct-star triangles. Full permanent-star pair distributions satisfy
inter = sum(m × edges_m) and L1 = sum(choose(m,2) × edges_m) at every frame.

| Bonds per distinct star pair | 4–6M mean pair count | 6–8M mean pair count |
|---|---:|---:|
| 1 | 1744.5290 | 1738.4072 |
| 2 | 40.6172 | 38.7772 |
| 3 | 0.7280 | 0.4862 |
| 4 | 0 | 0 |

All bins, including zeros, are retained. Zero quadruple-bin counts establish
neither physical exclusion nor adequate sampling. Late stars carrying 0/1/2
intra bonds average 898.045/100.558/1.397. Temporary connectivity never redefines
permanent-star membership. [Multiplicity paths](evidence/multiplicity.png) and
frame CSVs expose the rare triple populations and their replica differences.

r003 L1 means are **51.8345 → 41.949 → 33.6175** across 2–4M, 4–6M and 6–8M.
The primary −8.3315 consists of double-edge loss −7.1285 plus loss of 0.401
triple edges, contributing −1.203 to L1. However, the late 250k means reach a
minimum 27.696 at 6.5–6.75M, then climb to 40.500 in the final quarter; the exact
endpoint L1 is 45. Its last-1M slope is +11.537 per million. This is a substantial
reversal, not evidence of continued monotone multiplicity loss. Return of one
scalar at one endpoint does not establish multigraph equilibration.

r001/r002 primary L1 changes are only −0.2855/+0.9205. That apparent stability
hides composition changes: r001 doubles fall 2.4335 while triples rise 0.716;
r002 doubles rise 4.042 while triples fall 1.0405. The three-history primary
L1 difference is −2.566 ± 12.496. Broad cancellation must not conceal these paths.

r001 L2 has a clear rise-and-fall: **30.6355 → 42.354 → 52.2235 → 37.304**
across the four 2M windows. Its primary change is −14.9195, versus −4.740/+0.5065
in r002/r003; ensemble −6.384 ± 19.486. Its late-quarter means bottom near
30.068, rebound to 38.496 and end at 34.552. L2 therefore supports a large
conformational/network excursion, not persistent triangle loss everywhere.
The 6–7M → 7–8M L2 changes are −6.984/+1.900/+4.094. Motif reversals weaken
a simple common-drift interpretation but do not settle the slower loop partition.

## Giant component, satellites and coordination

All three primary giant fractions decline:
−0.0006775/−0.0009945/−0.0007425, mean **−0.0008048 ± 0.0004160** (rounding
of stored contrasts). This excludes zero in the exploratory paired comparison,
but is less than one star in the ensemble mean among 1000 stars, not loss of
bulk percolation. Late isolated-star means are 1.8675/2.012/0.7795; satellite-star
means are 0.099/0.004/0.619. The ensemble outside-giant increase is accounted for
almost entirely by isolation (+0.8038 stars), with satellites changing only
+0.001 star. Components, isolated stars and giant size are coupled quantities,
not independent corroborating tests.

The shared primary loss is not sustained uniformly: last-1M giant changes are
−0.001323/−0.001578/+0.001747. r003 recovers to an exact giant fraction of 1;
r002's final-quarter giant mean rises, but r001 continues downward to a final
giant fraction of 0.996. The final r001 satellite excursion also contributes:
satellite-star means rise 0.736 between its final quarters while isolated stars
fall 0.128. The ensemble decrease combines genuine r001/r002 peripheral change
with a reversing r003 excursion; it cannot be classified as sustained global
network deterioration or dismissed as settled noise.

Late distinct degree distributions (fractions of all permanent stars) are:

| Replica | degree 0 | degree 1 | degree 2 | degree 3 | degree 4 |
|---|---:|---:|---:|---:|---:|
| r001 | 0.001868 | 0.010807 | 0.104779 | 0.199340 | 0.683207 |
| r002 | 0.002012 | 0.011398 | 0.109596 | 0.193005 | 0.683988 |
| r003 | 0.000780 | 0.010929 | 0.103505 | 0.187833 | 0.696954 |

Primary mean-degree changes are −0.030382/−0.027343/+0.008503 and second-moment
changes −0.161058/−0.157848/+0.066523. Degree-4 fractions change
−0.009327/−0.015397/+0.011058. r001/r002 thus lose distinct coordination alongside
their inter-bond losses and intra gains; r003 reverses direction. These linked
changes strengthen the population concern without being independent observations.

## Conformations and exchange relative to qualified Ee8

Both shape observables are reconstructed using permanent-bond minimum-image
unwrapping. Primary Rg² changes are +0.019487/+0.010750/+0.046400 and terminal R²
changes +0.074867/+0.013908/+0.130963. Ensemble changes are +0.025546 ± 0.046161
and +0.073246 ± 0.145444. r003 occupies a higher shape level throughout 6–8M,
while r001 expands after 6M then contracts near the end. In the last 1M contrast,
Rg² falls in all histories (−0.033726/−0.017293/−0.003562); terminal R² changes
−0.076312/−0.049815/+0.029048. All final-quarter terminal R² differences are
negative. The evidence supports replica-specific offsets/excursions, not sustained
common swelling. Shapes do not independently establish a reason to extend, but
do not erase the loop/coordination concern. [Full shapes](evidence/shape.png)
and [late paths](evidence/late.png) retain these distinctions.

Only the qualified **corrected** Ee8 absolute-8M reference enters the comparison.
Its record and all payload hashes authenticate; frozen corrected-window statistics
match the inventory hashes, raw-state means and creation/break counter increments.
Historical defective C1 windows are excluded. Ee8 neighbor counts and event-time
exposures reuse that authenticated review rather than a new Ee8 graph replay.
The comparison uses the same f=4, N=10, density 0.8, Ea=4 and other physics except
Ee; histories are not paired across Ee. Equal equilibrium observables are not required.

| 6–8M ensemble mean | Qualified Ee8 | Ee10 |
|---|---:|---:|
| Bound fraction | 0.897003 | 0.960386 |
| Intra / inter bonds | 95.454 / 1698.551 | 103.352 / 1817.420 |
| Mean distinct degree | 3.318562 | 3.555341 |
| Giant fraction | 0.997694 | 0.998206 |
| Accepted creations / time | 1.81950 | 0.32813 |
| Accepted breaks / time | 1.81848 | 0.32808 |
| Distinct-neighbor gains / time | 1.64923 | 0.29688 |
| Distinct-neighbor losses / time | 1.64718 | 0.29747 |

Observed chemical and neighbor turnover is roughly **5.5 times slower** at Ee10,
despite higher occupancy and degree. Event-integrated creation rates per free-sticker
time are 0.002035–0.002139 versus 0.004409–0.004426 at Ee8; rupture rates per
active-bond time are 0.0001689–0.0001722 versus 0.001012–0.001016. These are
accepted, population-normalized events, not independent attempt frequencies or
proof of mixing. Equal creation/break rates do not equilibrate the intra/inter
partition. Ratios are descriptive; they are not a universal equilibration-time law.

The inspected LAMMPS reference is `feature/associating-stickers` at
`1c6faf70e94aef2389c208e8c80c60c084a96907`, with four implementation files
matching that commit and hash-bound in authentication. The implemented semantics
use `q = -expm1(-nu0 * exp(-Ea/T) * Nevery * dt)`, gate both reaction directions
by `r_assoc=1.25`, and retain existing shifted-FENE mechanics below R0=1.5 without
duplicating WCA. Ea controls the attempt scale; Ee changes energetic acceptance.
No alternative generic kinetics assumption is substituted.

## Slow-mode uncertainty and targeted proposal

| 6–8M observable | IAT, physical time (replica range) | Effective samples |
|---|---:|---:|
| Total bonds | 231–293 | 34–43 |
| Intra | 2788–3279 | 3.05–3.59 |
| Inter | 1280–1978 | 5.06–7.81 |
| L1 | 1077–2157 | 4.64–9.28 |
| L2 | 1225–1887 | 5.30–8.16 |
| Giant fraction | 2231–2647 | 3.78–4.48 |
| Rg² | 159–670 | 14.9–63.0 |

These first-nonpositive-lag estimates are finite-window heuristics, especially
fragile under drift. For intra populations, 5-block SEMs 3.629/3.126/1.934 shrink
to 20-block SEMs 1.701/1.510/0.977; IAT SEMs are 4.317/3.700/2.356.
r003 L1 blocking SEM falls 1.897 → 0.914, while r001 L2 falls 2.670 → 1.353.
No convincing block-size plateau is established for these slow modes. Shorter
windows can suppress the apparent IAT by demeaning a slowly changing state;
their larger nominal effective counts cannot prove equilibration. Constant bins
and sparse satellite events do not provide independent mixing evidence.

The proposed **8–12M continuation of all three original histories** would retain
500k/1M diagnostics and provide two nonoverlapping post-8M 2M windows, with review
at 10M and 12M. It targets observable late evolution, not complete structural
decorrelation. Specifically assess whether r001's loop gain and degree/giant loss
reverse or settle, whether r002's emerging plateau persists, whether r003's L1
recovery remains bounded and triples repopulate, and whether r001 L2 stays bounded
after its large excursion. Recompute complete multiplicity/degree/component
distributions, intra/inter populations, both shapes, accepted chemical and
neighbor turnover, interval-local IATs and 5/10/20-block sensitivity. Keep three
histories as the statistical units and retain all 0–8M context.

Compare 6–8M, 8–10M and 10–12M means and replica paths, shifted contrasts and
late-quarter slopes together. Evidence of bounded reversals/settling in the
linked chemistry/coordination path could support qualified initialization even
without complete decorrelation; continued directed changes warrant maintaining
the hold. No significance threshold or zero-containing interval automatically
accepts a checkpoint. A future restart uses the actual documented MD reseeding
semantics: preserve positions/velocities and chemistry/counters, record new MD
seeds and do not stitch IATs or SEMs across the 8M boundary. No such continuation
was prepared or run here.

The unresolved discrepancy is **scientific preparation**, not numerical integrity.
The ten prior qualified acceptances remain unchanged. [VALIDATION.md](VALIDATION.md)
records CPU checks and reproducibility; protected KG/src files, frozen physics,
simulation outputs and existing evidence were not modified.
