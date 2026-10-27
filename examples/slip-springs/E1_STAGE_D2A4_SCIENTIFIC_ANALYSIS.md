# D2A.4 — scientific analysis preparation; results await local execution

27 October 2026. Starting local and actual remote `slip-springs` HEAD were
`6371ca7e420bb7e94c07bbdc1b1de182ddb0cadc`, verified before edits; repository
origin is `jorge-ramirez-upm/UAMMD_KG`. **No analysis script, reduction, test,
simulation, build, benchmark or GPU program ran in Codex.** No figure or
hypothetical scientific result was generated. This report is the preparation
and interpretation contract; physical findings await authenticated products.

## Evidence and integrity anchors

The user reports12 successful exits, status
`completed_twelve_runs_not_scientific_acceptance`, wall13515.86144873 s,
peak child RSS163524608 bytes,1620796912 bytes before final summary, and
failed_run=null. The saved summary contains these records. Reading it is not
a complete independent authentication or scientific reduction.

Original evidence, never written by the analysis:

    /home/jramirez/UAMMD_KG-evidence/d2a4/long-t1000-twelve-v1

Read-only file-hash anchors captured during preparation:

| Record | SHA-256 |
|---|---|
| D2A.4 frozen manifest | `697f0f3be4841221d5b109e0376f4de9da63f239db6f088e5b128da0d4d438fc` |
| D2A.4 summary.json | `80a9867f4cecd31162073afde1e1c1697e5a790d9c8443b612003bb5b652e17f` |
| D2A.4 provenance/launch.json | `03831b050663a9e709dd1a781668643d945c12590b73da9dd4ac370066d62d04` |
| Existing D2A.3 analysis_complete.json | `07a14d5b04630ddfddd0362d8d704390544e4461c65bc3857192e1c1d1d2bca5` |

These capture the inspected snapshots, not an independent attestation that a
particular binary executed correctly. The prior committed manifest/tool source,
recorded build identity and receipt hash closure supply the remaining integrity
checks. D2A.4 source/binary remain d60982f / double precision; no rebuild or
GPU/environment probe is required by this offline command.

## One local analysis command after independent review

Linux, Python3.10+, NumPy, Matplotlib and Git history containing the reviewed
commits are required. The command reads saved files only; it does not execute
code from an evidence directory, run the simulator or calculate stress/G(t).

```sh
python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d2a4_analyze.py --run-reviewed-analysis --output /home/jramirez/UAMMD_KG-evidence/d2a4-analysis/long-t1000-twelve-v1-analysis-v1
```

The destination must be absent. It is outside the repository, D2A.4 evidence,
D2A.3 evidence and prior products. Existing or symlink output is rejected;
all prior trees must be disjoint from the destination, including ancestor paths.
No overwrite, repair, resume or automatic removal is provided. Failed partial
products remain marked invalid; a different attempt requires a fresh destination.

Default comparison reads existing products at
`/home/jramirez/UAMMD_KG-evidence/d2a3-analysis/exploratory-eight-v1-analysis-v1`
and their original input tree. `--d2a3-analysis PATH` can select a byte-identical
relocated prior product directory. Missing/changed historical data abort the
default command. To deliberately perform D2A.4-only analysis, add
`--without-d2a3-comparison`; that omission is recorded, never silently inferred.
The default D2A.4 evidence path may be overridden with `--evidence PATH` for a
byte-identical relocated copy. The comparison still needs the original D2A.3
raw tree; no historical analysis is regenerated.

## Reuse and authentication boundary

The existing [D2A.3 analysis](e1_d2a3_analyze.py) now supplies small shared
functions with explicit cohort parameters. Its direct entry point retains
D2A.3 anchors, two replicas, T100 support and R2 table naming. R2 numerical
formulas remain unchanged. [D2A.4 analysis](e1_d2a4_analyze.py) supplies the
three-replica profile, historical comparison and long-duration review report.
It does not duplicate the authentication/plotting/reduction pipeline. Existing
D2A.3 products and original Git source remain intact; new code does not rerun
or overwrite them. No campaign runner/validator, accepted observer or KG math changed.

Before means, slopes or figures, the command will:

1. Hash the complete D2A.4 file inventory; reject symlinks/special files and
   missing/extra root, config, provenance or run records. Match manifest and
   schedules to the frozen6371ca7 Git blobs and captured summary/launch anchors.
2. Authenticate source/tool/build/executable records: compiler/precision flags,
   accepted source SHA and binary hash, exact12 IDs/seeds/argv, GPU identity,
   process exit/status, per-run receipt hashes and all raw file byte/hash records.
   Check recorded resource fields against the frozen limits, without inventing
   unrecorded peak GPU memory or continuous monitoring samples.
3. Reuse the unchanged completion validator for the exact N32/M256/kappa/Z
   matrix, physical/E1 and dynamical completion, stored coefficients, snapshots,
   100001 acquisition frames, scalar2001/full-E1 eleven/snapshot two counts,
   116 ordered lag bins, exact counts, integer clocks, decimation phase/block
   widths, expected CSV structure and finite values. Parse JSON strictly and
   reject duplicate keys/nonfinite numbers. No bad records are discarded.
4. For the default comparison, check the captured historical completion hash,
   every prior product against that marker, its analysis/validator source hashes
   against the recorded Git commit, and all original inputs against its prior
   authentication inventory. Confirm physical binary/settings and disjoint seeds
   between cohorts. This verifies existing products/inputs, not a rerun of R2
   scientific reductions or independent physical correctness attestation.
5. Rehash D2A.4 after authentication and after analysis; also rehash historical
   inputs/products after the comparison. Any change aborts and invalidates the
   new products. Only successful authentication publishes authentication.json;
   analysis_complete.json is published last with product/source/package hashes.

Require valid analysis_complete.json, no FAILED.json, and unchanged recorded
input/product hashes. A pre-reduction authentication marker alone does not
certify subsequent figures. Abrupt interruption/I/O failure can leave incomplete
products; their absence of valid closure remains failure. Authentication proves
bounded consistency with captured records and committed identities, not the
correctness of the physical model, recorded execution or numerical algorithms.

## Statistical and estimator definitions

Every existing replica-level quantity is retained: CM and selected absolute
monomer MSDs, end/quarter means/differences, directional C1 and rank-two/P2 C2.
There are no internal MSDs, new dynamic observables, stress channels or fitted
terminal coefficients. The two orientational quantities are analyzed separately.

For each bin and quantity, preserve x1,x2,x3 and compute

    mean = (x1+x2+x3)/3,
    SE = sample_std(x1,x2,x3; ddof=1)/sqrt(3).

The unit is an independent whole-run replica. R3 has only two variance degrees
of freedom; SE is descriptive, not a precise confidence interval. Chains,
monomers, correlated origins and lag bins are not extra replicas. Missing/
nonfinite inputs abort; a one-replica SE is never reported as zero.

Support classification uses integer lag_samples, never a floating timestamp
comparison: fine0..15, coarse primary through18432 (nominal184.32) with count>=32,
and weak tail beyond to90112 (nominal901.12). The primary endpoint has39 origins
per chain; the final bin has one. The [resource/support derivation](E1_STAGE_D2A4_RESOURCE_PLAN.md)
explains deepest-level omission and the partial last exported level.

MSD is a direct displacement on last-position-decimated endpoints with phase
b-1. Orientation instead correlates complete block means of instantaneous
unit-vector/rank-two features, without renormalizing them; triangular lag
half-width is(b-1)*0.01. The last primary orientation bin has block duration20.48
and half-width20.47. Equal nominal times are not identical temporal filters.
Line segments never bridge level or primary/tail boundaries.

Local log slopes use the established centered three-point derivative accounting
for unequal log spacing. Each replica is computed separately, only for positive
MSD/time, one common multi-tau level and fully primary support. Invalid edges,
level crossings, weak stencils and log domains retain separate per-replica
reasons; available other-replica slopes are not removed. Mean/SE is available
only when all three slopes exist. No slope-fitting window or scaling exponent
is chosen after seeing favorable data.

Bare ratios g_CM/(6t/33) apply only to A and C and t>0. Preserve each replica,
mean and SE. Fixed-region extrema/deviations and replica gaps are descriptive
over correlated lags, not new independent samples or acceptance thresholds.
The same law is not imposed on E1 constrained chains.

## Scientific products prepared, not generated here

| Product | Content |
|---|---|
| authentication.json | D2A.4 identities, complete input byte/hash inventory and integrity scope |
| historical_authentication.json | Existing D2A.3 product/input closure, when comparison is enabled |
| figure_1_cm_msd.png/.pdf | Four cells, three replicas/mean, log-log CM MSD and bare6t/33 line |
| figure_2_bead16_msd.png/.pdf | Absolute central-monomer MSD, log-log |
| figure_3_c1.png/.pdf | Log lag, linear directional C1 |
| figure_4_c2.png/.pdf | Log lag, linear P2 C2 retaining negative values |
| curves.csv | All existing quantities, r1/r2/r3, mean/SE_R3, support and bare reference ratios |
| features.csv | Fixed sampled lags0.01,0.15,1.28,5.12,19.2,76.8,184.32,901.12 |
| slopes.csv | Separate local slopes, descriptive mean/SE_R3, unavailable classifications |
| bare_com_ratios_by_region.csv | Fine/coarse-primary/weak-tail deviations, all three replicas |
| orientation_features.csv | Sampled half-level indicator, minimum primary sample, residual at primary endpoint |
| performance.csv / performance_by_cell.csv | Individual wall/stage/RSS/bytes/timers and per-cell runtime range/mean |
| comparison_d2a3.csv | All88 overlapping bins/cell for four quantities, oldR2/newR3 means/SE/replicas/counts |
| plot_support.json | Integer support boundaries and any zero-MSD logarithmic-display masks |
| SCIENTIFIC_REVIEW.md | Actual endpoint/contrast/slope/performance tables and qualified interpretation checklist |
| analysis_complete.json | Final products, analysis entry/shared-code/validator identity and unchanged-input check |

The four figures retain the D2A.3 cell colors. Thin solid/dashed/dash-dot lines
identify the three replicas; thick lines identify means. Fine circles, coarse
squares, shaded/dotted weak tails and support gaps avoid implying homogeneous
filters. No R3 confidence bands. PNGs are300 dpi and PDFs retain vector curves/
embedded fonts. Rendering has not been executed or visually inspected here.
Lag zero is retained numerically but cannot appear on a log lag axis. Exact
zero MSD at positive lag is masked for logarithmic display only and explicitly
recorded, never replaced; signed C1/C2 values are not clipped.

## Historical comparison and interpretation

The join uses cell, integer lag/step, decimation period/phase and orientation
block size, then checks time/block duration separately. Counts deliberately
differ with record length. All88 D2A.3 bins must have matching filters among
D2A.4's116; the extra D2A.4 lags remain in the full curve tables. No interpolation,
forced numerical agreement, pseudo-pairing or historical regeneration occurs.
The comparison identifies primary support in each cohort separately. Former
T100 weak-tail bins can become T1000 primary bins; their errors/filter origins
are not equivalent. Changed curves can reflect longer origin averaging,
independent finite trajectories or nonstationarity; the table does not identify
which explanation holds or present per-bin differences as confirmatory tests.

The generated review will show actual primary-endpoint replicas/SEs, bare ratio
deviations by fixed region, last available primary slope stencils and sampled
C1/C2 half-level indicators. The last valid derivative need not be at184.32:
level-boundary and weak-neighbor exclusions are preserved. Sampled half-level
crossings are not fitted relaxation times or proof of monotonic/single-exponential
decay. Residuals, replica agreement and full shapes must determine whether decay
is substantial and the N32 window is sufficient; sparse tail points cannot.

Report observed endpoint differences (E1 minus bare at each stiffness, and
stiff minus flexible residual orientation) separately from mechanisms. Fixed
spatial anchors, contour hopping, canonical transfers and bending provide
candidate explanations, but rates/processes are not independently varied in
this matrix. Supported near-one COM slopes do not alone establish terminal
diffusion; supported subunit monomer slopes are finite-window behavior, not
reptation or a measured entanglement length. No automatic diffusion/exponent
fit or numerical acceptance tolerance is introduced.

Performance uses observed per-run child/stage wall times, runtime range/mean,
peak recorded child RSS, evidence bytes and raw main/dynamics/E1 timer categories.
These timers overlap and must not be added as independent costs. Available
GPU headroom is not peak GPU memory. There was no isolated observer benchmark.
N32 measurements inform later planning but do not measure N64 cost. Current
tree bytes and the saved pre-final-summary byte count use different endpoints.

D1.6 remains **scientifically closed with qualifications — finite-timestep
equilibrium preservation not confirmed**. Origin averaging can mix startup
evolution with fluctuations; increasing T does not certify stationarity or
timestep accuracy. Stress/G(t) is outside this analysis; the
[six-component rheology requirements](E1_FUTURE_SIX_COMPONENT_RHEOLOGY.md) remain
unchanged and separate. No new physical conclusion is asserted in this
unexecuted preparation report.

## Regression commands and next milestone

Small [CPU-only checks](tests/d2a4_analysis_regression.py), unexecuted here,
cover R3 SE normalization, R2 compatibility, independent-replica slope domain
failures, integer boundaries, three-replica CSV reading and support-key matching.
They use analytical stencils/disposable records, never original evidence or
synthetic scientific figures. Optional local commands after review:

```sh
python3 -B examples/slip-springs/tests/d2a4_analysis_regression.py
python3 -B examples/slip-springs/tests/d2a3_analysis_regression.py
```

These do not replace full authentication or actual plot/scientific review.
Source changes are limited to this report, the shared analysis adaptation,
D2A.4 entry/report/comparison code, tests, README and project status. Original
evidence/products, accepted simulation/observer/correlator, manifests, source
identities, D1.6 and D2B are not changed.

After reviewing actual D2A.4 products, the next development milestone is
**D2A.5**, starting N64/M256 with Z4096 for constrained systems to preserve
Z/(M*N)=1/4, three independent replicas/system. T2000 is provisional and must
be reassessed from measured N32 relaxation and unresolved tails. No longer-chain
simulator/observer support, N64 campaign or D2A.5 code is implemented here.
Stop for independent review before local analysis execution.
