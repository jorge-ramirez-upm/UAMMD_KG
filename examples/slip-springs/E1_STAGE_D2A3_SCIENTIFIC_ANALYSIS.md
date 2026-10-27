# D2A.3 — scientific analysis preparation, results pending

27 October 2026. Starting local and actual remote `slip-springs` HEAD were
`5f9aa4daf35b4e4fd4df51b31bce34aa1aa09f68`, verified before modifications;
origin is `jorge-ramirez-upm/UAMMD_KG`. **No scientific reduction, analysis
script, test, simulation, build, benchmark or GPU program was executed.**
Consequently, this document specifies the analysis and its limits; it does
not report authenticated curve findings, completed figures or a final physical
interpretation. No synthetic or placeholder scientific results are supplied.

## Execution record and current evidence status

The user reports 8/8 completed runs, status
`completed_eight_runs_not_scientific_acceptance`, approximately 907.24 s wall,
205.5 MB recorded evidence, maximum child RSS 149196800 bytes and eight zero
exit codes. Direct inspection of the saved summary records those quantities;
this is not full independent authentication or a scientific reduction. The
original root remains read-only:

    /home/jramirez/UAMMD_KG-evidence/d2a3/exploratory-eight-v1

Two file-identity anchors were captured with read-only SHA-256 commands during
preparation, without executing an analysis script:

| Saved record | SHA-256 |
|---|---|
| summary.json | `6e8e95a86318a60644ce5164dc0725a6ad62aad922d39fabb95174831e9ceabc` |
| provenance/launch.json | `a8fa886971e56c8025e97587e494c732ed273fdc2a250dbda32de2f0520aa8a2` |

These seal the inspected snapshot for subsequent checks. They are not independent
execution attestation or proof that every reported measurement is physically
correct. The committed [manifest](e1_d2a3_config/manifest.json), its pinned hash
and preparation Git commit provide the prior configuration/tool identity.
The [campaign handoff](E1_STAGE_D2A3_CAMPAIGN_PREPARATION.md) describes the
saved-output and resource-measurement scope. The complete hash/schema closure
has **not** been executed in this milestone.

## One local command after independent review

Requires Linux, Git with the reviewed preparation commit available, Python3.10+,
NumPy and Matplotlib. No GPU, simulator binary or CUDA toolchain is needed for
this offline analysis. The code does not execute any script from the evidence
directory, call the simulator or query the GPU. From any working directory:

```sh
python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d2a3_analyze.py --run-reviewed-analysis --output /home/jramirez/UAMMD_KG-evidence/d2a3-analysis/exploratory-eight-v1-analysis-v1
```

The output directory must be new. It is outside both the original evidence and
the repository. Existing output is never overwritten/adopted; partial products
are retained on failure. The optional `--evidence` argument accepts a relocated
byte-identical evidence tree; the same identities and checks still apply.
There is no simulation or analysis on importing the module.

## Stage 1: authentication before scientific reduction

[e1_d2a3_analyze.py](e1_d2a3_analyze.py) will:

1. Inventory/hash every evidence file, rejecting symlinks and special files.
   Match the captured summary/launch anchors and the prior committed manifest,
   schedules and sidecar. Reject unexpected root/config/provenance/run entries.
2. Check source/tool/build identities against the reviewed Git preparation
   blobs and the saved build-settings receipt: d60982f physical executable,
   double precision, CUDA13.0.88/g++11.4.0 and sm_86. Recorded executable bytes
   and hash must match the frozen manifest. This checks recorded provenance;
   it does not reconstruct a build/runtime dependency closure or rerun a binary.
3. Require the exact A/B/C/D matrix and fixed eight IDs/seeds, two distinct
   whole-run replicas per cell, eight successful exits and consistent per-run
   process/receipt/summary records. Match complete recorded argv and GPU identity.
   Check recorded runtime, RSS, final byte counts and prelaunch headroom against
   the preparation limits, without inferring unrecorded monitoring samples.
4. Validate every run's receipt hash and its complete raw-file inventory against
   actual files. Reuse the unchanged trusted preparation validator for main/E1
   completion, parameter identity, physical CSV completeness, dynamic metadata,
   chain/replica IDs, finite values, clock and exact fine/coarse lag counts.
   Reparse JSON strictly, rejecting duplicate keys and nonfinite numbers.
5. Require 10001 dynamic frames at steps 0,100,...,1000000, scalar frames201,
   full-E1 frames11, snapshots2, shared_frames201 and extra_readbacks9800.
   Require 88 bins per chain/replica: levels0..9, deepest populated level10
   omitted. Rehash the whole evidence tree after authentication and again
   after analysis; input changes invalidate the derived products.

Only after this succeeds is `authentication.json` written, including the full
input byte/hash inventory and the bounded integrity claim. No physical curves
are reduced or plotted before that boundary. A hash/schema/nonfinite/missing
record failure aborts; no repair, filtering of bad records, replica substitution
or historical-evidence mutation is implemented.

`analysis_complete.json` is published last, with product hashes, analysis-code
and trusted validation-code identities, checkout SHA, package versions and
confirmed unchanged input bytes. A `FAILED.json`, missing completion file or
changed product/input hash invalidates the derived set. A pre-reduction
authentication marker alone does not certify later products. Original evidence
must remain available; this is not a replacement archive.

## Stage 2: physical and statistical summaries

Analysis uses the eight existing `replica_correlations.csv` files; it does not
reconstruct missing trajectories or introduce an observable. All twelve existing
exported quantities are retained, including absolute MSDs, symmetry reductions
and their differences. The four primary views are CM MSD, bead-16 absolute MSD,
directional C1 and P2 C2, as defined in the [approved design](E1_STAGE_D2A3_EXPLORATORY_DESIGN.md).

For every lag and quantity, preserve the two whole-run values and compute

    mean = (x1+x2)/2,
    descriptive SE = sample_std(x1,x2)/sqrt(2) = |x1-x2|/2.

No chain, monomer, time origin or lag bin increases R=2; SE has one variance
degree of freedom and is not a precise confidence interval. No confidence band
or confirmatory significance claim is created. Equal weights apply to whole-run
replica means; chain/symmetry averages were already formed within each run.

Fine support is lag<=0.15 with origin spacing one acquisition interval (0.01).
Coarse displacement estimates use point positions with last-position origin
decimation, phase b-1 and actual count `floor(10001/b)-ell`. Orientation uses
block means of instantaneous unit/rank-two features, without renormalization,
with triangular support of half-width `(b-1)*0.01`. Curves with the same nominal
lag therefore have different displacement/orientation smoothing. No lines are
drawn across different multi-tau levels as if their origin supports were identical.

Primary interpretation ends at 19.2 (63 origins/chain, not independent samples).
Lags above that, to 76.8 (four origins/chain), are descriptive weak-support tails.
These regions are fixed before reductions, not selected for favorable behavior.
Zero lag remains in numerical tables but is omitted from logarithmic axes.
If a nonzero-lag MSD is exactly zero, its unplottable logarithmic point is masked
only for display and explicitly listed in `plot_support.json`; all original
values remain in the curve table. Negative orientational values are preserved.

Bare-chain CM ratios use `g_CM/(6*t/33)` only for cells A and C at t>0. Export
both replica ratios, their equal-weight mean and descriptive SE. By the three
fixed lag regions, report ratio extrema, maximum absolute deviation from one
and maximum replica gap; these are descriptive across-lag summaries, not new
independent samples or pass/fail thresholds. No such law is imposed on E1.

MSD slopes use a centered three-point log stencil (accounting for unequal log
spacing) separately per replica, only
where all three MSD/time values are positive, all three belong to the same
multi-tau level, and the whole stencil lies in primary support. Record unavailable
edge/level-boundary/log-domain/weak-support cases with a reason, not zero.
Average valid replica slopes only afterward. No regression window, reptation
exponent or terminal diffusion coefficient is fitted.

For orientation, export the value at the primary endpoint, minimum sampled
primary value, and first sampled value at or below 0.5, if present. This is a
descriptive sampled half-level indicator, with prior sample/block width recorded;
it is not an interpolated relaxation time, exponential fit, proof of monotonic
decay or terminal decorrelation. Coarse-level smoothing qualifies every such
comparison. C1 and C2 are analyzed independently.

## Products the local command will generate

| Product | Content |
|---|---|
| authentication.json | Verified identities, evidence inventory, integrity scope |
| figure_1_cm_msd.png/.pdf | Log-log CM MSD, four cells, both replicas/mean and bare `6*t/33` line |
| figure_2_bead16_msd.png/.pdf | Log-log central-monomer absolute MSD |
| figure_3_c1.png/.pdf | Directional C1, log lag and linear ordinate |
| figure_4_c2.png/.pdf | P2 C2, log lag and linear ordinate retaining negative values |
| curves.csv | All original replica quantities, means, descriptive SE, lag/count/support, bare ratios |
| features.csv | Same fields at fixed lags 0.01,0.15,1.28,5.12,19.2,76.8; no fitted features |
| slopes.csv | Separate replica local slopes/mean/SE and availability reasons |
| bare_com_ratios_by_region.csv | Descriptive fine/coarse-primary/weak-tail deviations and replica differences |
| orientation_features.csv | Sampled half-level indicators and residual orientation, no fitted times |
| performance.csv / performance_by_cell.csv | Per-run timers, wall/RSS/bytes; cell runtime consistency |
| plot_support.json | Explicit display exclusions and support encodings |
| SCIENTIFIC_REVIEW.md | Actual numerical endpoints, computational summary and provisional review recommendation |
| analysis_complete.json | Final product hashes, source/package identity and unchanged-evidence check |

Figures use consistent accessible cell colors, thin solid/dashed replicas and
thick equal-weight means; circles indicate fine support, squares coarse support,
and shading/dotted means identify weak tails. PNGs are 300 dpi; PDFs preserve
vector curves and embedded TrueType fonts. This rendering is prepared but has
not been executed or visually inspected. Tables retain descriptive SE rather
than presenting narrow-looking R=2 confidence bands.

## Computational report scope

The local report will tabulate both child wall times per cell, their mean and
relative replica gap, stage wall, peak recorded child RSS and actual evidence
sizes. It will retain main initialization/integration/production/observation/
output timers, dynamics shared/extra readback, acquisition CPU and evaluation/CSV
timers, and E1 observer timers. Their scopes overlap; they are not added as
independent costs or used to claim an isolated observer overhead benchmark.
Prelaunch GPU free memory is not peak GPU usage. Current authenticated tree
bytes and the saved `campaign_bytes_before_final_summary` have different
accounting endpoints and are reported separately.

## Physical interpretation and next study: pending actual products

No observed dynamical ordering, subdiffusive regime, incomplete orientational
relaxation, plateau or diffusion coefficient is asserted from this preparation.
The local report supplies quantitative endpoints and a provisional recommendation:
if a replica/orientation quantity never reaches a sampled half-level in primary
support, prioritize reviewing longer supported records for those cells; otherwise
prioritize reviewing matched-cadence timestep sensitivity and decay shape.
These are reconnaissance rules, not scientific acceptance criteria. A half-level
crossing does not resolve the tail. Human review of actual figures and replica
agreement must decide whether early resolution, duration, timestep or replica
count is the next limitation. No subsequent simulation is authorized by that report.

When interpreting actual results, keep the observation separate from mechanism.
Anchors remain spatially fixed between renewal events; hopping changes attached
beads and canonical renewal can transfer constraints between chains. Bending
stiffness changes backbone configurations/forces. The matrix does not independently
vary these mechanisms, so it cannot attribute a shape change uniquely to hopping,
renewal, confinement or stiffness-related relaxation. No tube/reptation scaling
or constrained-chain nonzero asymptotic diffusion law is assumed. C1 and C2 can
have different decay shapes; no single-exponential model is imposed.

Sustained supported slopes, replica consistency, longer-horizon stability and
timestep comparisons would be needed before terminal claims. D1.6 remains
**scientifically closed with qualifications — finite-timestep equilibrium
preservation not confirmed**. Time-origin pooling can mix startup evolution
with later fluctuations; these curves cannot by themselves certify stationarity.
No relaxation scale is borrowed from unresolved D1.6 autocorrelation tails.

## Preparation record

Changes are confined to the new analysis script, this report, small
[unexecuted parser/arithmetic checks](tests/d2a3_analysis_regression.py), and
README/project-status links. Optional user check, not executed here:

```sh
python3 -B examples/slip-springs/tests/d2a3_analysis_regression.py
```

The checks use analytical scalar/stencil inputs, never campaign figures or
fabricated scientific results. They do not replace end-to-end authentication,
plot inspection or independent scientific review. No simulator, runner, accepted
adapter/correlator, D1.6 evidence, D2B design, model or frozen criteria changed.
Stop after preparation; return the authenticated products for scientific review.
