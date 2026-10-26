# D1.6C v1 — existing-evidence repair and independent secondary audit

Preparation only. No tests, authentication jobs, repackaging, builds, simulations,
reference draws or scientific analysis ran in Codex. The completed D1.6B campaign
and its original exploratory analysis are immutable inputs. A packaging-cap failure
is not a failed GPU campaign. Nothing here launches GPU work or changes E1, its
accepted observer/initializer/RNG/transitions, frozen D1.6B analysis or D0 margins.

## Original identities and read-only boundary

Original root:
`/home/jramirez/UAMMD_KG-evidence/d16b/d16b-readiness-vjzdjbjn`.
Original analysis: `analysis-1793017379881834465/analysis.json.gz`;
exact recorded size28,386,811 bytes; recorded/user-supplied SHA256:
`04570c0ccb3b06df0f9be265a2bde602f1c2dcce59c474af963ca8634a17652f`.
Original completion SHA256:
`afde6f5e10d41cc02b6b1ebcc91a8ac03dc806044aa3d60d797831caf4056b68`.
The saved result reports `EXPLORATORY_COMPLETE`; all16 runs completed, with
recorded local campaign wall2131.6879526209996 seconds. These are existing records,
not newly reproduced or authenticated scientific measurements in this preparation.

`e1_d16c_config/original-lock.json` captures these identities and small original
source/session/configuration/approval/build/completion/analysis-result metadata.
Local Stage A verifies exact bytes and full existing raw/receipt inventories with
the unchanged D1.6B authenticator. It validates the archived source, all16 members,
seeds, schedules, approvals, completion, reference import and saved-analysis
provenance. A bounded strict streaming JSON reader inspects the whole gzip/JSON
structure and CRC while materializing only authentication/summary fields. Duplicate
keys, nonfinite numbers, malformed/truncated JSON, oversize input and mismatched
identities fail. It never reruns the original reducers, aggregation or estimator.

The original analysis's embedded manifest/approval/completion/source identities
and all16 raw receipt hashes must match the authenticated cohort. Its saved
summary must match both original result records. Reference source/configuration/
approval/completion identities and full recorded intervals/covariance remain
required; no manual rounded reference substitutes or new reference draws are used.
The original stiff backbone CDF precision remains unresolved.

No original artifact is edited, replaced, truncated, moved or rewritten. Inventories
of original evidence and raw files are carried forward with their paths/sizes/hashes;
original receipt/inventory bytes are copied into metadata. Large raw CSV, coordinates
and executables remain local and are never embedded. New outputs live only in a
fresh sibling D1.6C durable root with its own pinned preparation worktree.

## Packaging repair

Stage A produces three files in its new `stage-a/returns/` directory:

- `d16c-existing-metadata.tar.gz`: compact provenance, original metadata/receipts,
  inventories, local verification logs, frozen new protocol/resources, source
  identities and a false secondary-audit approval template.
- `d16b-original-analysis.json.gz`: a byte-for-byte copy of the entire original
  compressed analysis; no decompression/reserialization, filtering or rounding.
- `return-manifest.json`: SHA256 and exact size for both payloads, completed bounded
  worker resource record and context. It is finalized by the supervisor after the
  worker exits, avoiding a self-referential archive/resource hash.

The archive contains internal `SHA256SUMS` and a binding to the complete scientific
payload. Metadata is capped at16 MiB uncompressed; a separate scientific payload
is capped at64 MiB. This independently versioned two-payload scheme preserves the
old D1.6B16 MiB rule unchanged. Missing/corrupt/incomplete evidence yields a D1.6C
failure record, not a reclassification of original GPU completion. Caps stop with
preserved outputs; data are never silently omitted to fit. Checksums detect changes,
not adversarial wholesale replacement or a digital signature.

## Prespecified, post-selected scientific follow-up

The user's reported anomalies select this follow-up after observing D1.6B. Its
six primary contrasts are explicitly **same-data post-selection exploratory**:

1. Cell1 (kappa0,fine dt) late spatial Var(Re²) minus its analytical reference.
2. Cell1 late-minus-early spatial Var(Re²).
3. Cell4 (kappa10,coarse dt) late-minus-early all-live-spring mean e².
4. Cell4 late-minus-early occupancy-standardized connector mean.
5. Stiff coarse-minus-fine A_joint in the late window, using independent cells.
6. Coarse-minus-fine contrast of each stiff replica's own late-minus-early A_joint.

Freeze narrow early/middle/late windows [0,10]/[40,50]/[90,100], and wider
sensitivity windows [0,20]/[40,60]/[80,100]. Use actual regular scalar .5/full2
grids with exact rational time keys. Endpoint frames are included in static
window means. Rate bins are wholly inside windows with open left endpoints.
Irregular early full frames are retained in stiff traces and exact shared-time
contrasts but never overweight window averages or enter uniform ACFs.

All16 scalar trajectories enter the audit. Full spring/population/site/event
reductions focus on all eight stiff replicas; the complete original analysis
for every cell is returned unchanged in A. All four replicas in each relevant
cell remain present. No outlying replica, chain, frame or unfavorable endpoint
is excluded. Missing expected frames abort the audit rather than changing weights.

### Conformational anomaly

For every replica retain Re²/Rg² means, spatial variances, covariance, raw fourth
length moments, exact-reference-centered squared/cross deviations, bond moments,
maximum-chain/tail contribution diagnostics and the spatial-centering identity:

    mean_c[(X_c-mu)^2] = (255/256)*s_X² + (mean_c[X_c]-mu)^2.

Thus a reference-centered squared deviation can include mean drift. Temporal
variance of a replica's mean, between-replica mean variability and instantaneous
spatial variance are separate quantities. The cell1 time-resolved panel reports
individual contributions s_r²/4 and fractional contributions, average within-replica
variance and the exact pooled1024-chain descriptive decomposition. The uncertainty
unit is still one whole replica, never1024 pooled chains or all time frames.
Window sensitivity links spatial variance, reference-centered deviations, raw
fourth moments, Re²/Rg² covariance and means without counting algebraically related
diagnostics as independent confirmations. Analytical numerical error estimates
retain their original engineering, non-certified qualification.

### Connector anomaly and occupancy weighting

Every live spring contributes at every full frame. Retain connector e²/e⁴,
nine analytic chi-square radial-CDF evaluations, chain populations, contour
end/interior occupancy, accepted-hop/renewal interval rates and joint scores.
Compare the all-spring mean with equal occupied-chain weighting, explicitly
conditioning the latter on nonempty chains. They answer different questions.

Prespecified population strata are1–5,6–9,10–33 springs/chain. Reference spring
weights are sum_z z P_canonical(Z_c=z)/8 within each stratum. The full finite-M
canonical hypergeometric law is retained, including empty/multiply occupied chains.
Fixed-weight connector means use these reference weights and observed within-stratum
means. Missing positive-weight strata yield null/insufficient support; weights are
never renormalized over favorable observed bins. Fine-grained z=0..33 support and
conditional means are retained, including unsupported categories.

Within a window, aggregate all frame numerators/counts before forming group means;
constant total Z makes this consistent with uniformly averaged all-spring means.
The exact symmetric decomposition is:

    Delta E2 = sum_g .5*(w_L+w_E)*(mu_L-mu_E)
             + sum_g .5*(mu_L+mu_E)*(w_L-w_E).

It separates within-stratum and composition contributions descriptively, not
causally. Coarse strata do not eliminate residual composition variation inside
strata. Replica-level changes, CDF changes, occupancy/population relationships
and rate changes are retained without IID connector/frame error bars.

### Stiff A_joint contrast

Keep original score formulas and exact analytical size-mean normalization. Show
individual scores, within-cell dispersion, both independent-cell variance terms,
shared-time trajectories, associated conformation/population/connector statistics
and all six predefined windows. Independently seeded timestep replicas are never
paired. Shared references cancel in dt contrasts. Two timesteps establish neither
convergence order nor a zero-dt limit.

### Temporal support and independent cross-check

For selected means/fluctuations/connector/joint/population observables, report
per-replica ACFs over [0,100] and [50,100], with actual spacing/origin counts,
quarter-record lag support, two centerings, finite-lag integrated partial sums,
three lag caps, half-record sensitivity and2/4/8-frame block means. Incomplete
terminal blocks are explicitly counted and used only as stability diagnostics;
all frames remain in the scientific means/trajectories.

The new direct-product overlap-corrected estimate is checked against independent
`numpy.correlate` fixed-denominator products. Sample centering uses a baseline
subtraction to avoid spurious variance for constant floating-point series. Saved
original D1.6B ACF records for the selected observables are extracted unchanged
and displayed alongside the separately identified new diagnostics.

Report failures of duration>=50*candidate, available lag>=5*candidate, small terminal
tail, <=25% lag-cap/centering stability and <=50% half-record stability.
Block SE ratios above2 (or zero/aliased estimates) and fewer than four complete
blocks are explicit stability/support diagnostics, never replica uncertainty. Negative/nonpositive
partial sums and zero variance are explicit. Failed horizon support is distinguished
from unstable centering/block/window estimates where possible. All new IAT fields
remain null: these finite-record cross-checks do not upgrade an unresolved tail
to a resolved relaxation time. There is no first-zero truncation, zero-IAT imputation
or conversion into independent temporal sample counts. Standalone SVG displays
show individual traces and per-replica ACFs; lines join observed points only.

## Replica inference, multiplicity and interpretation

Each window is reduced inside each independent replica first. Use R4 nominal t3
intervals, or Welch uncertainty with both independent-cell contributions. Source
reference intervals expand level-difference intervals; numerical centering errors
are carried separately. Probability diagnostics retain bounded replica Hoeffding
intervals. Zero observed replica dispersion is flagged and cannot establish a
resolved signal. Keep replica contributions and leave-one-out means, not selective
leave-one-out acceptance tests.

Trajectory alpha=.025 retains the D1.6B allocation against stored .025 reference
families. Only the six primary contrasts receive a nominal Bonferroni critical-value
sensitivity. Supporting diagnostics stay pointwise. **Neither establishes controlled
post-selection family-wise error on these same discovery trajectories.** R4 CLT,
heavy-tail and variance-estimation limitations remain. The2/16 minimum two-sided
sign-flip resolution for hypothetical within-cell symmetric R4 changes is a
limitation, not a performed test or a timestep pairing scheme.

Original counts of thousands of correlated flags remain original bookkeeping,
not independent anomaly evidence. Organize evidence in three anomaly families;
several diagnostics can identify the same fluctuation. A nominal signal, observed
deviation, broad precision, insufficient horizon, unresolved tail and numerical/
provenance/resource failure remain distinguishable. No automatic equilibrium pass.

The generated interpretation ties mean changes, fluctuation level versus drift,
joint/timestep contrasts, occupancy decomposition and temporal support to their
uncertainties. It does not claim that null-compatible intervals prove stationarity.
Design alternatives are conditional discriminators: independently seeded replication
for rare fluctuations, a separately approved finer dt for reproducible timestep
sensitivity, or increased horizon/cadence only for the support deficiency it can
address. No automatic M/R/T recommendation or new campaign follows. Confirmation
requires new independent data and a separately powered, frozen comparison family.
