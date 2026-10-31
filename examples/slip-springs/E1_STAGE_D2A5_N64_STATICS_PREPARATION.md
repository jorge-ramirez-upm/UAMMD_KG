# D2A.5-S N64 static equilibrium audit — preparation for review

Prepared 31 October 2026 on `analysis/d2a5-n64`, starting at reviewed
`a876aa8663d0f6e93cba96bc22c9c91b64962588`. The user's explicit instruction to
work on the current branch overrides the instruction file's new-branch name.
No tests, analysis, numerical targets, builds, simulations or GPU operations were
executed. No scientific acceptance decision is made. Stop for independent code
review before any execution. **EQUILIBRIUM PRESERVATION NOT CONFIRMED.**

Only the new analyzer, its regression specification and this handoff are changed.
The dynamical N64 analyzer/results, original validators, physical code, original
campaign inputs, accepted references and frozen criteria remain unchanged.

## Evidence boundary and authentication

The analyzer imports the unchanged `e1_d2a5_n64_analyze.authenticate`: same frozen
manifest, twelve explicit N64 IDs, independent seeds, recorded launch/source/
executable identities, success receipts, complete file hash/size closure, schema
and acquisition revalidation, and before/after immutable inventories. It reads
the mutable summary once and records the bytes' SHA256 without demanding that
summary/progress remain fixed. It never enumerates or hashes an N128 directory,
executes archived code, opens production binaries or accesses the production
checkout. Authentication hashes all files in the twelve completed N64 subtrees,
including dynamical CSVs, to retain output-to-receipt closure. This can involve
substantial I/O even though reductions stream the static CSVs.

No new sidecars or output are written in the campaign root. New execution
artifacts go exclusively beneath
`/home/jramirez/UAMMD_KG-evidence/d2a5-statics/n64-v1`:
`analysis/` for analysis and `regression/` for synthetic fixtures. Paths reject
symlink ancestors, escapes and preexisting destinations. An incomplete analysis
retains `FAILED.json`; no retry, overwrite or automatic cleanup is supported.
`result_inventory.json` is written last and hashes all preceding products,
including provenance; it does not recursively hash itself. Checksums detect
changes, not independent attestation of scientific execution. Local Python
modules, scientific review documents and regression source are hashed before
and after reduction. Python and library versions and thread settings are saved.

## Observational inventory (inspected headers and observer/validator sources)

| Record | Actual support | Supported static quantities and limits |
|---|---|---|
| `samples.csv` | 1001 times, 0:10:10000, 256 rows/time | Chain Re², Rg², mean length, mean squared length, minimum length, tangent separations 1–4. Chain averages precede time averages. Spatial variance/covariance and raw Re⁴/Rg⁴ are descriptive additional reductions. |
| `equilibrium_tangents.csv` | 11 times, 0:1000:10000, 256 rows/time | Tangent separations 8 and 16 only, averaged along contour within chain. No complete contour function. |
| `initial.csv`, `final.csv` and `equilibrium_positions.csv` | Two endpoint conformations | Arbitrary endpoint quantities could be reconstructed; no intermediate conformations. Existing authentication verifies endpoint agreement. The new audit uses recorded scalar dimensions rather than generating extra endpoint-only discovery families. |
| `initial_bonds.csv` | One length/bond at initialization | Initial empirical distribution can be reconstructed, but is not a time series. Not used as a higher-precision equilibrium reference. |
| `bond_statistics.csv` | 501 observations at 5000:10:10000 for each of 16384 bonds | Per-bond accumulated first/second moments and 33 histogram counts. Analyzer sums counts within runs, verifies each bond's 501 counts, and cross-checks the accumulated moments against scalar final-half means. |
| Histogram metadata | 32 finite bins, bin 32 overflow | Edges `j*histogram_max/32`; last bin is `[histogram_max,infinity)`. Same edges required for B−A/D−C. No exact arbitrary-cut CDF or complete distribution outside those bins. |
| `equilibrium_connectors.csv` (B,D) | 11 times, all 4096 live springs/time | ex, ey, ez, e²; compute all-live e²/e⁴, Cartesian means, second and cross moments. No spring/frame becomes an independent replica. |
| `equilibrium_chains.csv` | 11 times, all chains | z and connector component/squared sums; canonical population mean, centered population variance around 16, full PMF/CDF and probability z≥2. |
| `equilibrium_sites.csv` | 11 times, all 65 contour sites on all chains | Occupancy probability versus contour index; cross-check each chain's count against z. |
| `equilibrium_events.csv`, hopping metadata | Initial zeros and ten interval records | Counts, rates on actual intervals, proposal/rejection/renewal consistency from existing validator. Rates at t=0 undefined. No IID Poisson/binomial uncertainty for accepted events. |
| `equilibrium_backbone.csv` | Header only | No additional intermediate backbone rows: full times already coincide with scalar times. |

The accumulated histogram is a final-half sampled distribution, not a continuous
time integral. No time-resolved bond histogram, per-bond trajectory, arbitrary
intermediate conformation, full contour function or recorded total-energy time
series is available. Stretch energy **is** recoverable from chain bond moments:
`15*64*(mean_r2 - 2*mean_r + 1)`. Bend energy could likewise be derived from
nearest-neighbor tangents, but is omitted to avoid an algebraically redundant
family. Minimum length is recorded but not treated as a marginal-distribution
reference. No unrecorded trajectories or interpolated full contexts are created.

## Predefined estimands and uncertainty

Primary family: late-window means of Re², Rg², mean length, mean squared length
and tangent1, separately B−A at kappa0 and D−C at kappa10. Ten contrasts total.
No absolute size comparison across stiffness is evidence of preservation.
`backbone_comparisons.csv` uses unpaired Welch intervals with alpha=.005 for
these ten (nominal Bonferroni family sensitivity), alpha=.05 elsewhere. Each
mean is first computed within an independent whole run. R=3 per cell; matching
replica numbers across cells do not imply pairing. Every individual run value,
SE and leave-one-run-out mean is retained; contrasts retain all nine independent
leave-one-out combinations. Normal/CLT and tiny R qualifications limit nominal
coverage. No run is omitted, and frames/chains/springs never increase R.

Cell/window summaries and paired within-run window changes use nominal 95% t2
intervals. Zero observed run dispersion yields an unavailable unbounded
interval, never a claimed exact result. PMF/CDF, occupancy and other bounded
probability summaries additionally use independent-run Hoeffding intervals;
rare zero counts cannot create false zero-width precision. Histogram contrasts
retain nominal Welch plus two-cell Hoeffding intervals. Probability drift
intervals are only descriptive t2, with zero dispersion explicitly flagged.
All probability vectors and histograms have correlated bins; no collection of
secondary bin findings is independently confirmatory.

Tables distinguish a descriptive difference from compatibility within available
uncertainty, unavailable references and insufficient precision/zero dispersion.
Neither compatibility nor a nonsignificant test establishes equality. No new
practical equivalence margin or acceptance threshold is invented. Broad
intervals require an insufficient-precision interpretation; without an
applicable tolerance, practical equivalence remains unavailable.

## Windows, grids and stationarity

Windows are fixed before inspecting any differences:

| Window | Requested physical limits | Scalar support | Full context support |
|---|---|---|---|
| Initial | [0,0] | 1 frame, duration 0 | 1 frame, duration 0 |
| Post-initial | [10,10000] | 1000 frames, duration 9990 | 10 frames at 1000..10000, duration 9000 |
| Early | [10,2000] | 200 frames, duration 1990 | 2 frames at 1000,2000, duration 1000 |
| Middle | [4000,6000] | 201 frames, duration 2000 | 3 frames, duration 2000 |
| Late | [8000,10000] | 201 frames, duration 2000 | 3 frames, duration 2000 |

Initial exact-target construction is displayed separately. Equal frame means
on each actual uniform grid are used; full-grid values are never carried forward
onto the scalar grid. Early full support is especially weak. Store exact actual
first/last observation times and counts per quantity. Paired within-run contrasts:
late−initial, middle−early, late−middle, late−early; aggregate only the three run
contrasts. Compare signs and leave-one-out sensitivity, not just pooled drift.

Event bins must lie wholly within a requested window. Thus early uses only
(1000,2000], middle (4000,5000] and (5000,6000], late (8000,9000] and
(9000,10000]. Post-initial excludes (0,1000]. Rate tables record actual interval
support; this differs from instantaneous full-frame means. Event totals and
identities are mechanically revalidated; no arbitrary ideal acceptance/renewal
rate is manufactured. Fixed Z and population mean16 are conservation only.

The unchanged D1.6B ACF diagnostic is reused on prespecified scalar and full-grid
observables, post-initial and late-half segments. It retains quarter-record lag
support, overlap counts, sample/target centering sensitivity, positive-sequence,
self-consistent-window and half-record checks. Outputs include full curves and
partial sums. Conditional effective frame count is `min(n,n*spacing/(2*tau))`
only when those conservative diagnostics support tau. This is not a rigorous
bound or a source of additional independent replicas. All full-context records
are too short for that helper's half-record criterion, so their tau/ESS remain
unresolved. Scalar aliasing below 10 time units also remains unresolved. Apparent
drift challenges the stationarity assumption even if an ACF criterion passes.

## References and D1.6 continuity

E1 exact annealed backbone identity remains a theoretical target, not established
finite-step preservation. Accepted direct initialization samples independent
radial lengths with density proportional to `r² exp[-15(r-1)²]`, and the exact
orientation Markov law. `semiflexible_reference.radial_moments` and `langevin`
are reused unchanged, with the preserved 128/256 radial refinement <1e-11 check.
The D1.6 finite-chain formulas are evaluated for **N64**, including Rg², with
float64 quadrature sensitivity recorded separately. Refinement differences are
engineering numerical diagnostics, not certified error intervals; target
comparison tables have that qualification and no silently exact quadrature claim.
No quadrature or reference computation was executed during preparation.

Connector targets: e²=5, e⁴=125/3, Cartesian means/cross moments zero and second
moments5/3. `canonical_population(256,64,4096)` supplies the exact finite-population
hypergeometric law over 65 sites per chain (16640 sites globally), including its
finite-population variance and negative cross-chain covariance. Occupancy target
is4096/16640; population mean16 alone cannot demonstrate canonical sampling.

The D1.6A.2 accepted numerical reference ensemble is **N32**. Its sampled stiff
variances/covariances/fourth moments and frozen CDF cuts cannot be transferred to
N64. The new audit does not import it or report zero reference uncertainty;
those N64 comparisons are explicitly unavailable. It does not generate new
reference ensembles. Spatial moments remain secondary descriptive B−A/D−C
comparisons. No bare-model Gaussian-chain approximation is substituted.

D1.6 closure and B/C protocols, D/E/F scientific decisions and reference
methodology were read. Earlier stiff/coarse connector drift (-0.04462) was a
post-selected N32/T100 window change at dt=.00025, not stationary bias. Here
N64/T10000/dt=.0001 changes multiple factors. The new late−early e²/e⁴ and
population traces can strengthen, weaken or leave that descriptive concern
unresolved, but no like-for-like timestep test, convergence order, invariant
response sign or mechanism is established. D0 contextual margins quoted by
D1.6B concern deviations from references in the earlier exploratory protocol:
2% size means, 1% bond moments, .02 tangent correlations, .1 connector e².
They are **not** equivalence margins for these N64 constrained-minus-bare
contrasts. No new distributional/variance margin is assigned. Stiff D1.6 CDF
reference precision was unresolved even at N32.

## Products and exact commands (unexecuted; review and authorization first)

The implementation writes authentication and source provenance, reference
qualification, availability report, replica windows/drifts, backbone contrasts,
equilibrium summaries (including connectors/occupancy/populations), histogram
counts/intervals, event counts/rates, ACF/ESS diagnostics, two PNG/PDF trace
figures, `SCIENTIFIC_REVIEW.md`, and a final hash inventory. The generated review
lists all ten primary numerical contrasts and retains unresolved scientific
questions; independent interpretation of the secondary tables is still needed.

No dependencies are installed by these commands. Use an existing Python
environment with NumPy, SciPy and Matplotlib; versions are recorded on execution.
No build command is needed or authorized. Set `PYTHONDONTWRITEBYTECODE=1` to
avoid cache writes outside the permitted output root.

```bash
cd /home/jramirez/UAMMD_KG-d2a5-analysis-dev/examples/slip-springs
nice -n 19 ionice -c 3 env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OMP_THREAD_LIMIT=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 BLIS_NUM_THREADS=2 timeout 600s python3 tests/d2a5_n64_statics_regression.py
nice -n 19 ionice -c 3 env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OMP_THREAD_LIMIT=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 BLIS_NUM_THREADS=2 python3 e1_d2a5_n64_statics.py --run-reviewed-analysis
```

Both commands are CPU-only and must be run by the user after review and separate
execution authorization. The analysis command has no ten-minute timeout because
full receipt authentication may take longer on the host. The analyzer sets all
common numerical pools to two before importing libraries and checks niceness19.
Shell `ionice -c 3` provides idle I/O priority. No GPU call, executable launch,
simulation, recompilation or numerical sampling is involved. If interrupted,
the existing directory is incomplete and preserved; choose a separately reviewed
version/output location before retrying. Do not delete or relocate evidence.

Regression specifications cover exact synthetic reductions, R3 uncertainty,
unpaired contrasts/LOO, zero dispersion, bounded rare bins, sparse-window support,
drift values, unresolved ACF tails, canonical population moments, connector norms,
missing/truncated/nonfinite/extra CSV frames, schema/label failures, output escapes,
symlink ancestors, immutable N64 changes and ignoring an inaccessible N128 sibling.
They do not authenticate real evidence or establish scientific acceptance.
