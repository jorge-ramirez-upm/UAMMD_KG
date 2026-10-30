# D2A.5 N64 analysis preparation for independent code review

This implements the task in `INSTRUCTIONS_CODEX.md`. Preparation only: Codex
has not executed tests, reductions, plots, builds, simulations or benchmarks.
Independent code review is required before either command below is executed.
No scientific result or authentication success is claimed by this document.

All three new source/documentation files are confined to
`examples/slip-springs/` on `analysis/d2a5-n64`. The explicit task overrides the
older AGENTS.md instruction to work on `slip-springs`. Neither the production
branch nor the active checkout is modified. Existing D2A.3/D2A.4 analyzers,
validators, manifests, simulator and KG correlators remain unchanged.

The Stage 0 comparison base is `81fe5de9cd5ded849202eebab7c14e6bd35fb9ae`.
The checkout already inherited a repository `.gitignore` addition for
`INSTRUCTIONS_CODEX.md` relative to that historical base. This task does not
change that file. The ignored task instructions are preserved.

## Authentication boundaries

The analyzer reads the active summary once, records the SHA256 of those
captured bytes and selects exactly n64-A/B/C/D-r1/r2/r3. It requires each ID
once in completed_runs and exactly one corresponding run record. It does not
require the entire campaign, or even its current active run, to be finished.
It never enumerates `runs/` or the active campaign root. Summary and progress
are excluded from subsequent immutable-input checks; progress is never read.

It pins the frozen manifest to
`297ad861edb98232ca91c9fbd11b7eef2443bc685d7c89ec592a7ab86777c365`,
checks the archived N64 schedules and frozen helper identities, and requires
recorded source/executable identity in the campaign launch record. It checks
the twelve summary-anchored receipts, full per-run file hash/size closure,
summary run byte totals, original CLI/seed/replica, successful exit and the
unchanged completion validator's result. That validator streams numerical
files and verifies physical metadata, frame counts, column labels, finite
values, exact integer clocks and filters, full E1 context and output closure.
The analyzer additionally matches the replica curves to the manifest's
explicit N64 integer grid and primary flags. No float tolerance selects support.

Only the twelve named N64 subtrees, the archived manifest/checksum, two N64
schedules, launch record and named frozen tools are inventoried. No N128 run
directory, production checkout, live executable or external production
prerequisite is opened, hashed or authenticated. N128 entries in the frozen
manifest/summary are merely parsed as part of those shared documents.
The preserved prerequisite archives are outside this analyzer's authentication
boundary. Recorded hashes are integrity evidence, not independent attestation
of historical execution or compiler invocation; the manifest's compiler
qualification is retained in authentication.json.

All selected immutable inputs are hashed again after authentication and after
analysis. File device/inode/size/mtime/ctime signatures are retained as well,
so a rewrite restoring identical bytes still invalidates completed N64 evidence.
Symlinks, including ancestor symlinks, and special files are rejected. Changed
inputs cause failure and FAILED.json; all products in that directory are then
invalid. As with any filesystem snapshot, modifications after the final check
are beyond the observation interval.

The N32 comparison is mandatory and uses the pinned D2A.4 raw campaign at
`/home/jramirez/UAMMD_KG-evidence/d2a4/long-t1000-twelve-v1`. The established
D2A.3 authentication function with the D2A.4 profile checks that completed
campaign, including its frozen summary/launch anchors and receipts; it is
rechecked after reduction. No D2A.3 campaign or old product directory is needed.
Existing reduced D2A.4 products are not regenerated or overwritten: this new
analysis independently reads the authenticated replica exports. Missing N32
evidence fails the job rather than silently omitting the requested comparison.

## Numerical products and interpretation

The four primary quantities are COM MSD, absolute bead32 MSD, C1 and C2.
`curves.csv` retains all three replicas, equal-weight means and descriptive
SE with two variance degrees of freedom. Independent whole runs are the only
uncertainty units. `slopes.csv` reuses the established nonuniform log-time
three-point derivative separately per replica, with explicit unavailable
statuses at record edges, multi-tau boundaries, nonpositive MSD or weak support.

`bare_com.csv` compares A/C to 6t/65; B/D receive no bare reference.
`orientation.csv` preserves sampled half-level crossings and primary endpoint
residuals with block duration. Crossings are neither fits nor proof of relaxation.
`terminal_windows.csv` retains every primary, same-level window with at least
three interior supported slope stencils, per run for both MSDs. It includes
slope ranges, effective D=g/(6t) ranges, interval duration ratio, origin counts
and C1/C2 endpoint values. These are supported diagnostic intervals, with no
automatic terminal verdict. Most same-level windows span less than a factor
two in lag; sustained behavior requires agreement across adjacent supported
windows and replicas. No fit or reptation exponent is calculated.

`comparison_n32_n64.csv` matches exact integer lag, decimation, phase and
orientation-block fields using the established D2A.4 alignment key. It maps
central bead16 to bead32 and preserves both sets of replica values, means, SE,
origin counts, primary masks, N/Z and observation duration. Shared physical
and cadence CLI options must match; N, Z, duration, scalar schedule, random
identities, output paths and correlator capacity may differ. The independent
completion validators verify both estimators' semantics. The binaries differ
because N64 uses the variable-N implementation; no identical-binary claim is
made. Comparisons describe emerging trends at N32/N64, not asymptotic scaling.

Four primary figures are written in PNG/PDF, segmented by multi-tau level and
primary/tail support. Thin curves preserve each replica; thick curves show
means; weak tails are dotted and shaded. `plot_support.json` records display
omissions; numerical tables retain zero-lag and zero-MSD values.
`SCIENTIFIC_REVIEW.md` reports supported interval diagnostics and orientational
residuals, with limitations and review criteria. `analysis_complete.json`
records source hashes, checkout SHA, software versions and product inventory.
A completion marker denotes descriptive products ready for review, not
scientific acceptance. There are no empirical numerical findings until execution.

## Exact local commands after independent review

Use the existing Python environment with NumPy and Matplotlib. Both commands
are CPU-only, run at low CPU/I/O priority, and cap common numerical thread pools
at two threads. No GPU visibility setting, GPU query, simulator or build occurs.
Hashing and validation are serial streaming operations, avoiding new workers
and full-trajectory allocations. An optional taskset affinity should only be
added after the operator identifies two suitable allowed idle CPUs; no affinity
is assumed here while production is active.

Regression (synthetic inputs only; full physical validation is mocked only in
the authentication fixture, while real streaming curve validation is exercised):

```bash
cd /home/jramirez/UAMMD_KG-d2a5-analysis-dev
nice -n 19 ionice -c 3 env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 MPLCONFIGDIR=/home/jramirez/UAMMD_KG-evidence/d2a5-analysis/n64-v1/matplotlib-cache python3 examples/slip-springs/tests/d2a5_n64_analysis_regression.py
```

Scientific analysis (twelve N64 runs plus authenticated completed N32 inputs):

```bash
cd /home/jramirez/UAMMD_KG-d2a5-analysis-dev
nice -n 19 ionice -c 3 env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 MPLCONFIGDIR=/home/jramirez/UAMMD_KG-evidence/d2a5-analysis/n64-v1/matplotlib-cache python3 examples/slip-springs/e1_d2a5_n64_analyze.py --run-reviewed-analysis
```

All generated products, fixtures and Matplotlib caches remain beneath
`/home/jramirez/UAMMD_KG-evidence/d2a5-analysis/n64-v1`:
`regression/` for CPU checks and `analysis/` for scientific products. Both leaf
directories must be absent before their respective commands run. Neither
command overwrites an existing attempt; preserve failed attempts for review.
These commands require local filesystem permissions to create that output root.
They are supplied for the user and have not been executed by Codex.

## Remaining review limits

No syntax compilation, regression, scientific authentication or reduction has
been run. Synthetic checks do not replace authentication of actual host evidence.
Runtime and peak analysis memory are unmeasured. N32 authentication requires
the recorded preparation Git objects to exist locally. Historical compiler
provenance remains limited, and D1.6 equilibrium preservation remains qualified.
No review or execution of the active N128 campaign is part of this preparation.
