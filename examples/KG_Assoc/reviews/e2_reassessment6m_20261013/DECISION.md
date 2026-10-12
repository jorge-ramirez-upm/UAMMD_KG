# Dilute E2 reassessment through 6M — proposed scientific decision

System: `F04_N010_RP020_EE08_EA04`. Starting and verified remote SHA:
`30a8e7e415e07bfd69975cfb518e23157f791bd4`, branch `KremerGrest`.

**Recommendation: qualified acceptance of the three 6M endpoints for production
initialization.** The earlier material-drift hold can reasonably be lifted for
these endpoints, subject to user review and separate formal registration.
This is a documented recommendation, not formal acceptance, active-registry
selection or production authorization. Slow topology is not proven fully
decorrelated. The original 4M hold and all original evidence remain preserved.

## Authentication and scope

All nine replica segments (0–2M, 2–4M, 4–6M) were independently CPU revalidated
using the existing numerical/event/network/conformation validator. Plans and
approvals, source identities, build records and logs, parent states, completion
hashes, absolute steps, endpoint state counts, event replay and conformation
outputs passed. Replica identities remain r001/r002/r003, not nine independent
histories. The original recovered 0–2M lineage is retained, including its original
failure evidence; no receipt, plan or result was rewritten.

Historic executables were rebuilt in place. Their original bytes are unavailable
for fresh hashing: the 0–2M and 2–4M plans still bind the authenticated historic
build manifests, source and log hashes and declared executable identities.
Current executable bytes are authenticated against the 4–6M plan/build. This
limitation is explicit; it is not a claim that old binary bytes were reauthenticated.
The evolving read-only review driver's historic versions are checked against
Git blobs; all other scientifically relevant source hashes are checked strictly.
No launch, recovery or numerical-validation checks were changed.

The already generated 4–6M review's report/config hashes and plan/source bindings
were checked. [provenance.json](provenance.json) preserves all nine validation
payload hashes, lineage, original commits, seeds, build scope and precise endpoints.
[analysis_config.json](joint6m/analysis_config.json) binds this new analysis and
its sources; [summary.json](joint6m/summary.json) contains full estimates.

## Method and restart boundaries

The complete 0–6M sequence is retained. The initial unbound 0–1M interval is
transient context, excluded from stationary-window contrasts. The 1–2M window is
an early comparator, not retrospectively certified equilibrium. The later 2–6M
sequence is the candidate approximately stationary preparation regime.

Non-overlapping 1M windows use the existing IAT and 5/10/20-block uncertainty
helpers. Published, hash-authenticated 0–4M estimates are reused byte-for-byte as
statistical inputs, while their raw outputs are freshly revalidated. New 1M and
2M estimates are computed for 4–6M. Longer windows are 2–4M and 4–6M separately;
none crosses a restart. Paired ensemble differences use three history means and
Student-t df=2. Windows/segments are never additional independent replicas.
All displayed intervals are exploratory 95% intervals, unadjusted for multiple
comparisons; their overlap with zero does not prove stationarity.

MD seeds are (520034,520035,520036), then (520040,520041,520042), then
(520046,520047,520048). Chemical seeds remain (420101,420102,420103).
Effective MD seeds and state continuity are recorded/verified at 2M and 4M.
No autocorrelation, residence-time, stress or transport history is stitched
through these independently reseeded boundaries. Accepted-event increments and
neighbor turnover are reconstructed within each segment from its initial graph;
these are activity diagnostics, not bond-lifetime or transport measurements.

## What changes between the 4M and 6M assessments?

| Replica / observable | 1–2M | 2–3M | 3–4M | 4–5M | 5–6M |
|---|---:|---:|---:|---:|---:|
| r001 L2 | 37.192 | 36.654 | 33.804 | 38.095 | 34.350 |
| r002 L2 | 38.249 | 37.719 | 35.755 | 37.324 | 33.612 |
| r003 L2 | 36.367 | 34.895 | 34.136 | 36.601 | 37.546 |
| Mean L2 | 37.269 | 36.423 | 34.565 | 37.340 | 35.169 |
| Mean L1 | 65.311 | 68.708 | 66.789 | 65.769 | 64.268 |
| Mean bonds | 1578.488 | 1580.907 | 1582.672 | 1581.004 | 1582.398 |

At 4M every history showed declining L2. From 3–4M to 4–5M all three rebound;
the next interval declines in two histories and rises in the third. The coherent
monotonic decline is therefore not sustained. Relative to 1–2M, the latest L2
changes are −2.842, −4.637, +1.179: paired mean −2.100 ± 7.399. The earlier
4M change was −2.704 ± 1.507. L1's latest-minus-early difference is
−1.043 ± 15.511. These wide intervals cannot exclude appreciable slow drift.

A small bond-population shift *is* resolved between 1–2M and 5–6M:
+3.909 ± 3.064 bonds (~0.25%; bound fraction +0.1955 ± 0.1532 percentage
points). It cautions against calling the early comparator fully equilibrated.
The later 1M bond means fluctuate rather than increase monotonically; the
longer 4–6M minus 2–4M bond contrast is −0.0888 ± 0.4232. Thus this offset
does not establish continuing late chemical relaxation, but remains evidence
of early preparation history. No observable is discarded to obtain acceptance.

## Longer, boundary-respecting contrasts

4–6M minus 2–4M, paired across the same three histories:

| Observable | Difference ± 95% half-width |
|---|---:|
| L1 | -2.73 ± 6.94287 |
| L2 | 0.760833 ± 4.78006 |
| bonds | -0.0888333 ± 0.42317 |
| components | -0.1345 ± 6.42127 |
| inter | 2.3695 ± 14.7255 |
| intra | -2.45833 ± 15.0966 |
| largest_cluster_fraction | -0.000181 ± 0.00950981 |
| mean_center_terminal_r2 | 0.0187313 ± 0.0297756 |
| mean_degree | 0.00902433 ± 0.0258919 |
| mean_rg2 | 0.00589846 ± 0.02236 |
| second_degree_moment | 0.0498427 ± 0.0941509 |
| breaks | -0.00376667 ± 0.0168905 |
| creations | -0.0056 ± 0.0145387 |
| neighbor_gains | -0.00193333 ± 0.0193963 |
| neighbor_losses | -5e-05 ± 0.0189507 |

The topology/population/conformation contrasts have mixed replica directions
or small effects; the shared early L2 decline is no longer accompanied by a
sustained chemical, conformational or connectivity change. Largest-cluster
fractions remain about 0.964–0.968, mean degree 2.535–2.558, and degree second
moment 7.44–7.56. Intra/inter populations fluctuate without a continued shared
partition drift. Star Rg² remains about 7.990–8.012; center–terminal R² about
18.135–18.195. Creation/break rates remain around 1.47–1.48 per MD time unit
and distinct-star neighbor gains/losses around 1.13–1.14; ongoing turnover
argues against kinetic arrest, without proving topology mixing. Full per-window
values, paired contrasts and replica estimates are in [REPORT.md](joint6m/REPORT.md).

## Correlation limits and interpretation

The new 1M L2 windows have estimated effective sample counts 7.2–17.1;
L1 windows 6.7–18.6. In the 4–6M windows, L2 effective counts are
11.6/23.3/21.1; L1 14.5/5.8/17.9. The r002 long-window L1 IAT estimate is
1725 MD time units, compared with 20,000 units of observation. These are
finite-window estimates, not guarantees of independent topology samples.
For r002 4–6M L1, IAT SEM is 3.67 while 5/10/20-block SEMs are
3.40/2.36/1.81. Such sensitivity warns against treating small blocks as
independent or relying on an apparently precise drift test. Local slopes in
4–6M have mixed signs across replicas for both L1 and L2; they remain
descriptive diagnostics, not additional independent significance tests.

The rebound, mixed later replica changes, boundary-respecting long-window
comparisons and continued chemical activity make stationary slow fluctuations
a reasonable explanation of the earlier L2 decline. They do not rule out slower
aging, subtle initialization bias or longer topology modes. Only three independent
histories are available, and the candidate interval was selected after inspecting
the evidence. No arbitrary numerical threshold or nonsignificant-difference
acceptance rule is used. Qualified initialization is justified by the combined
finite evidence, not by proof of asymptotic equilibrium or full decorrelation.

## Proposed endpoints and next decision

Exactly these three 6M states are proposed (prefixes relative to the dataset):

- r001: `banks/e2_attempts/F04_N010_RP020_EE08/equilibrate_13a6951adf16448cb5365a8b28e28427/r001/state` (absolute step 6,000,000).
  `state.assoc_restart` SHA256: `89e752e6105d515028de92f72b38153e833060255fe0f1088439088f4cd74931`.
  `state.final_associations` SHA256: `14f26d5df3d7c2f3e759379a745e03d5ee5a08996d60b055ceb0dbf510f45ae4`.
  `state.final_permanent.lammpsdat` SHA256: `c07e24920f99aefa75b0bbf406930dfca166ec0a8427031dbc66744fb3e8e8ac`.
  `state.restart.lammpsdat` SHA256: `344e231f96eb8b1ec318de27f912a351d0c5175dd0b5de858612bed57f6cc6b7`.
  `state.state` SHA256: `a33260bfe5c85818ab84d1919f3e5d3b98c4c95174d30d2054753c454e90b31b`.
- r002: `banks/e2_attempts/F04_N010_RP020_EE08/equilibrate_13a6951adf16448cb5365a8b28e28427/r002/state` (absolute step 6,000,000).
  `state.assoc_restart` SHA256: `a0d1bd92fcc46618d7be660964aab65317e9367ef56e3f28540de033780b1462`.
  `state.final_associations` SHA256: `7f0a7444d60f8447769a311628f52b295bf539ed83640d38320b4246f8dc064c`.
  `state.final_permanent.lammpsdat` SHA256: `c7e13020a7e06476b08bf7fac68eeba539a3da6b66606e589439f81ed700df52`.
  `state.restart.lammpsdat` SHA256: `7c3867e607778534b359a1b7856cfda970bdd183e9585d67f26ddeb14e519534`.
  `state.state` SHA256: `eebb956301c1b031be47ef1c9dd0442a4d3b2828905e8c8e8fa031e740b1b491`.
- r003: `banks/e2_attempts/F04_N010_RP020_EE08/equilibrate_13a6951adf16448cb5365a8b28e28427/r003/state` (absolute step 6,000,000).
  `state.assoc_restart` SHA256: `806437cbcc1dd35f85d06b0cf063f0f832f5998b63dc51f38cc61445a90d325b`.
  `state.final_associations` SHA256: `12a932cfa66e1ecd617c1b6ad453a16c28e1a4b35ba2515d4fe1d7ade5b743fc`.
  `state.final_permanent.lammpsdat` SHA256: `5e7fe886855b2b0d0b26629b0f3e1a60de17f700798962582a8dd4348d5035b4`.
  `state.restart.lammpsdat` SHA256: `54d3d5c156aae4c5bbf7a4ecb21fd29548e339fa19ea2030e8c90dc6171fd9fc`.
  `state.state` SHA256: `0a1cedcdbfc773805afd14584476cd11c801c704118ba310f51671a914412af8`.

The new documented decision explicitly hash-binds and supersedes the *dilute
system's documented 4M hold* for this recommendation only. It leaves the other
systems' decisions, all old documents and any formal registry entries unchanged.
Catalog status is `qualified_acceptance_recommended_not_registered`; production
selection remains absent. Approval required next: endorse or reject this qualified
6M initialization recommendation and, if endorsed, separately authorize preparation
of formal acceptance records for these exact endpoints. Registry activation and
production launch require their own authorization. No further run is proposed here.
