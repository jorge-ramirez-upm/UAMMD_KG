# D2A.5 N128 analysis preparation — execution and review pending

Starting checkout: `05bfdafe5504eb64b02dccd8dea392ae553ea71f`, clean,
`analysis/d2a5-n64`. Existing reviewed preparation commits are `3027f8e`
(dynamics), `a876aa8` (integer-support correction), and `05bfdaf` (statics).
New work belongs exclusively to `analysis/d2a5-n128`, pushed through
`github` = `git@github.com:jorge-ramirez-upm/UAMMD_KG.git`.
`origin` points to the protected local production checkout; never push there.
No merge into `slip-springs` is part of this task.

The operator reports 24/24 complete, no active run or error. Reading a summary
does not independently authenticate that claim. **No test, authentication job,
reference calculation or scientific reduction was executed during preparation.**
The entry point is prepared for independent code review and subsequent local
execution. No scientific result or acceptance follows from this commit.

## Changed source and reuse

- `e1_d2a5_n128_analyze.py`: full-campaign authentication and combined workflow.
- `e1_d2a5_n64_analyze.py`: optional chain length in the existing curve reader,
  numerical tables and figures. Authentication, slopes, support definitions,
  independent-run averaging and N64 defaults remain the existing definitions.
- `e1_d2a5_n64_statics.py`: optional N in backbone/context/reference helpers;
  run-specific scalar/full schedules and histogram frame counts; optional
  windows in static tables. N64 default windows/statistics remain unchanged.
- `tests/d2a5_n128_analysis_regression.py`: synthetic specifications, unexecuted.
- This preparation record.

No simulator, observer, correlator, build, campaign helper, frozen config or
historical evidence is modified. The source changes only adapt numerical
analysis and add its delivery workflow.
The boundary inspection found a pre-existing historical root `.gitignore` change
relative to STAGE0 and ignored `INSTRUCTIONS_CODEX.md` last modified October 31.
Both are preserved; current tracked/untracked changes are all local to this example.

## Authentication before reduction

Input production root:
`/home/jramirez/UAMMD_KG-evidence/d2a5/production-n64-n128-r3-v1`.
Required manifest SHA256:
`297ad861edb98232ca91c9fbd11b7eef2443bc685d7c89ec592a7ab86777c365`.

The new gate requires the completed status, finished phase, no active run/error
or resource violations, exactly 24 ordered completion records, exactly 24 run
directories, and unique seeds/replica identities. It validates all twelve N128
and all twelve preserved N64 receipts, output byte counts and complete SHA256
inventories, recorded successful process exits, launch CLI/seed/device identities,
and the frozen physical/acquisition matrix. No retry, repair, rebuild or rerun
path exists. Any failed check stops the workflow.

The existing variable-N completion validator streams numerical schemas, counts,
finite values, clocks, dynamic grids, metadata, E1 structural context, occupancy
and event identities. Archived tool bytes must equal frozen/local tool records.
All archived provenance files must close against launch `preserved_files`;
prerequisite copies must match manifest identities. The recorded source tree is
compared to the implementation commit's local Git tree. The executable identity
is checked in the recorded launch; the protected checkout and live executable
are never traversed. A historical compiler invocation was not independently
recorded: this preparation does not manufacture compiler or physical-execution
attestation.

One whole-campaign hash inventory precedes validation; inexpensive inode/size/
mtime/ctime stamps check stability during authentication. A second full hash
inventory and stamp comparison closes evidence after reduction. This includes
the now-completed summary and progress log. No repeated full hash pass is made
for each analysis stage. CSV validation and reductions still require multiple
streaming reads; do not describe those as a single physical I/O pass.

N32 uses the existing pinned D2A.4 authenticator at
`/home/jramirez/UAMMD_KG-evidence/d2a4/long-t1000-twelve-v1`, with its manifest,
summary and launch anchors and full completion validation. Old reduced products
are not silently trusted or overwritten. All scientific reductions begin only
after both campaign gates succeed. Final N32 and analysis-source hashes must
also remain unchanged.

## Exact schedules and available observables

| N bonds | beads | T | BD steps | dynamic frames | P,m,L | exported bins | scalar spacing/frames | full E1 spacing/frames |
|---|---|---|---|---|---|---|---|---|
| 32 | 33 | 1000 | 10000000 | 100001 | 16,2,15 | 116 | 0.5 / 2001 | 100 / 11 |
| 64 | 65 | 10000 | 100000000 | 1000001 | 16,2,19 | 143 | 10 / 1001 | 1000 / 11 |
| 128 | 129 | 40000 | 400000000 | 4000001 | 16,2,21 | 159 | 40 / 1001 | 4000 / 11 |

All three have dt=0.0001, dynamics stride 100, M=256 and R=3 independent
runs per cell. A/B have kappa=0; C/D have kappa=10. Bare Z=0;
constrained Z=2048/4096/8192. Schedules, seeds and identities are read from the
authenticated manifests; the table is explanatory, not a substitute input.

N128 COM MSD and absolute bead64 MSD are primary. Absolute bead0/32/96/128 MSDs
are secondary, retaining individual runs and equal-weight means/descriptive SE.
C1 is directional; C2 is the rank-two orientational correlation. Scalar backbone
records supply Re², Rg², mean bond length, mean squared bond length and tangent
separations 1–4. Full records add tangent separations 8/16, connector vectors and
moments, per-chain populations, site occupancy, hopping and renewal counters.
Bond histograms have 33 bins (last overflow) accumulated over [T/2,T], with
501 frames for N64/N128 and 1001 for N32. Only initial/final coordinates and
attachment snapshots are available; no full coordinate history is reconstructed.

Unavailable: stress/rheology, an independent physical-entanglement observable,
controlled timestep series, dense full-E1 temporal histories and an authenticated
N128 sampled numerical-reference uncertainty/CDF ensemble. Higher backbone
moments can be tabulated but have no transferred N32 Monte Carlo error model.

## Numerical methodology and limitations

N128 primary support is integer `5*lag_steps <= steps` and origins/chain >=32.
The last eligible lag is 786432 samples, 78643200 BD steps, t=7864.32,
block 65536 samples, 49 origins. Export retains the final 3670016-sample lag,
t=36700.16, one origin. Weak-tail curves remain visible and never establish
terminal motion/relaxation alone. N32/N64 primary endpoints are 184.32/1966.08.

MSD uses last-position decimation. Orientation uses block-averaged fine features
without renormalization, with triangular lag support. Existing centered local
logarithmic slopes require three positive points within one supported level.
All eligible same-level windows are retained: examine replica slope ranges,
g/(6t) ranges, adjacent supported windows and orientation residuals together.
The bare COM reference is `6t/(N+1)`, hence `6t/129` at N128.
No forced asymptotic exponent, automatic terminal acceptance, extrapolated
relaxation time or reptation fit is introduced. Sampled half-level crossings are
diagnostics only; they do not prove an adequately relaxed tail.

Every average uses whole runs as statistical units; chains, overlapping origins,
lag bins and bead positions do not increase R. Comparisons across independent
cells use unpaired differences. Constrained/bare ratios are ratios of cell means
with descriptive delta-method SE; replica labels never create paired samples.
Across lengths, exact integer lag, phase, block and physical clock/filter width
must match. Common-lag tables flag support in all three campaigns. Separate
ratio/slope plots use each campaign's primary range and explicitly label this
unequal support. Physical CLI options are checked for compatibility, allowing
only documented N/Z, duration, output and acquisition changes. The recorded N32
and D2A.5 binaries differ; no bitwise-equivalence claim follows.

N128 static windows are initial t=0; post-initial 40–40000; early 40–8000;
middle 16000–24000; late 32000–40000. Full-grid windows use only actual frames:
early 4000/8000, middle 16000/20000/24000, late 32000/36000/40000. No interpolation.
Other lengths use the same duration fractions and their actual acquisition clocks.
Static chain-length contrasts retain their different physical windows.

The five late B−A and D−C primary properties form ten prespecified contrasts
with Bonferroni nominal 95% family sensitivity (individual 99.5% Welch intervals).
R=3 and normal/CLT assumptions qualify coverage. Other contrasts are exploratory.
Leave-one-run-out summaries, drift and unresolved ACF tails remain explicit.
Zero observed run dispersion gives no zero-width unbounded interval. Bounded
occupancy/PMF/CDF intervals use conservative Hoeffding diagnostics. Nonsignificance
does not prove equality; no equivalence margin is silently assigned.

The nonlinear backbone reference uses radial moments at b0=1,kb=30 and Langevin
tangent correlations at kappa=0/10, evaluated for N128. Quadrature orders 128/256
provide engineering refinement sensitivity, not certified reference error bounds.
E1 connector targets are E²=5 and E⁴=125/3. The exact population law is
`C(129,k) C(33024−129,8192−k) / C(33024,8192)`; mean population 32 is conservation.
No binomial approximation or N32/N64 sampled numerical-reference uncertainty is
transferred. Event rates are descriptive; passing structural/event identities
does not establish detailed balance, mixing or ergodicity.

**EQUILIBRIUM PRESERVATION NOT CONFIRMED** remains the review position. A single
timestep cannot establish timestep convergence. Three chain lengths without
justified regimes cannot establish asymptotic scaling; slowing does not prove
reptation or physical topological entanglements.

## Resource limits and output contract

CPU only; no GPU query/call, simulation, build or benchmark. Launch at nice 19,
idle I/O class 3. The script verifies both on Linux x86_64/aarch64 and sets all
common numerical pools to two threads before numerical imports. Dependencies
are existing Python, NumPy, SciPy and Matplotlib; no installation is performed.
Raw CSV parsing is streaming, bounded by one frame. Only reduced frame averages,
small exported curves and derived tables remain in memory. No measured runtime
or peak-memory guarantee is claimed; hash/validation I/O will dominate some stages.

All new results, logs, fixtures and Matplotlib caches must be beneath
`/home/jramirez/UAMMD_KG-evidence/d2a5-analysis/n128-v1`. The entry point refuses
existing output directories, path escapes and symlinked ancestors. A failure
retains `FAILED.json` and invalidates every product; never automatically delete,
repair or resume it. Agree a new version/location explicitly if rerunning is
needed. Do not overwrite existing N64 analysis/statics products.

Expected products beneath `analysis/`: authentication report, raw input inventory,
comparison context, reproducibility record, dynamics/n32,n64,n128 replica/mean
curves and figures, local slopes, terminal-window and orientation diagnostics,
secondary monomers, statics/n128 references, contrasts, connector/population/site
tables, event rates, histograms, time-window drift, ACF summaries and figures;
comparison common-lag/ratio/slope/static tables and figures; `SCIENTIFIC_REVIEW.md`;
source/software/thread/Git provenance; final `result_inventory.json`.
The inventory hashes every preceding product and excludes itself. Interpret
products only if provenance and inventory exist and FAILED.json is absent.

## User-executed commands after independent review

Run from the isolated checkout. These commands are provided, **not executed**.
The synthetic suite exercises N64/N128 shared functions, 24-run closure rejection,
malformed dynamic grids/finite values, exact support and rounded endpoint behavior,
statistics, N128 windows/population/reference formulas, streaming frames, static
tables, plots and review generation. Authentication byte inventories/JSON and the
physical completion validator are mocked in that synthetic closure fixture;
real CSV validators and filesystem inventory/symlink checks run separately.
It cannot authenticate physical production or replace independent code review.

```bash
cd /home/jramirez/UAMMD_KG-d2a5-analysis-dev
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  nice -n 19 ionice -c 3 timeout 600s \
  python3 examples/slip-springs/tests/d2a5_n128_analysis_regression.py \
  --output /home/jramirez/UAMMD_KG-evidence/d2a5-analysis/n128-v1/regression
```

After the synthetic evidence and implementation receive independent review:

```bash
cd /home/jramirez/UAMMD_KG-d2a5-analysis-dev
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  nice -n 19 ionice -c 3 \
  python3 examples/slip-springs/e1_d2a5_n128_analyze.py --run-reviewed-analysis
```

Return regression/PASS.json, analysis/authentication.json,
analysis/n32_authentication.json, analysis/provenance.json,
analysis/result_inventory.json and analysis/SCIENTIFIC_REVIEW.md, retaining all
referenced products. Review the actual terminal windows, residuals, differences,
drift/ACF status and cross-length support before answering the scientific questions.
There is no automatic acceptance decision. Open execution questions are dependency
availability and unexecuted integration/regression behavior; scientific questions
remain dependent on user-executed authenticated evidence.
