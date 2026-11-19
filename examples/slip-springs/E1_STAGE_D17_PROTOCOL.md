# D1.7 controlled timestep experiment — candidate, execution withheld

Worktree: /home/jramirez/UAMMD_KG-d2a5-analysis-dev.
Branch: validation/d17-equilibrium-dt. All evidence belongs beneath
/home/jramirez/UAMMD_KG-evidence/d17/. No existing production resource may be
modified. No build, test, numerical calculation or simulation was executed here.

## Scientific basis and evidence qualifications

EQUILIBRIUM_MODEL_E1.md and D1.6 closure distinguish exact annealed marginal
invariance from preservation by a discrete integrator. D1.6D source tracing and
D1.6E/F show a positive local bead-only EM connector defect of order h², but its
stationary response is a signed Poisson-equation quantity whose sign is unknown.
The implemented sequence is old-coordinate force evaluation, EM bead update,
then complete sequential Poisson hopping/renewal batch. At fixed coordinates,
ideal hopping and Gaussian end renewal preserve the conditional joint measure.
Their physical attempt rate remains100, with mean attempts Z*100*dt per step.
Changing dt changes the splitting frequency as well as EM error; this experiment
measures the complete accepted discrete algorithm, not an isolated EM coefficient.
Exact invariant substeps would compose invariantly; EM is not such a substep.
Finite RNG, count/retry bounds and arithmetic remain qualifications. No kernel,
initializer, RNG, rate, force or transition changes are proposed.

D1.6B was N32/M256/T100 with four replicas, only constrained systems, dt=.0001
and .00025; D1.6C's stiff/coarse -0.04462 e² window change was post-selected,
with unresolved temporal support. D1.6 closes without preservation acceptance.
The saved D2A.5 N64 static review reports broad conformational compatibility,
including a D-C Re² interval roughly [-520,595], and unresolved stiff connector
drift; those are quoted unauthenticated saved report values, not new reductions.
Only n64-v1 was present in the inspected d2a5-statics root. N128 static results
were not located or authenticated; their review remains an explicit readiness
prerequisite. Neither chain-length comparison supplies a timestep convergence test.

## Candidate Stage A and Stage B gate

24 independent runs: N32, 33 beads, M256, kappa10; Z=0 or2048;
dt=.00025,.0001,.00005; four new independent seeds/cell. All use kb30,
b0=kBT=zeta=1, A2=5 (effective stiffness .6), nu100, m1, renewal on for Z>0,
stress off, full scalar output, double precision, accepted exact initialization.
Seed allocation is a proposal requiring collision audit against historical ledgers.
No matching seed numbers or paired timestep estimates are used.

T100 is deliberately a precision pilot, not a claim of sufficient equilibration.
Steps/run:400000,1000000,2000000; total27.2 million steps across 24 runs.
Scalar cadence .5 (201 frames); complete E1 cadence2 (51 frames); snapshots only
0 and100. This matches regular D1.6B acquisition, but omits its five supplemental
early full frames and intermediate audit snapshots at .01 and50. New seeds,
bare controls, third dt and executable provenance are further differences.
No dynamics correlator or dense coordinate trajectory is needed.

Stage B is a design shell only: same six cells, new seeds, R and T selected
only after independent pilot review and a new frozen manifest. No Stage B
execution commands or automatic extension are authorized. Reject the pilot as
inadequate for planning a stationary comparison if tails or window behavior
remain unresolved. More independent replicas cannot cure an unsupported horizon.

## Frozen inference plan

Primary family: connector e² (constrained only, target5), Re², Rg², mean bond
length squared, tangent1 (both systems). Initial frame is separate. Windows:
early [.5,10], middle[40,60], late[80,100]. Scalar counts20/41/41; full counts
5/11/11 (times2..10,40..60,80..100). Retain actual endpoints and durations.
Compute chain/spring averages within frames, then window means within runs.
Independent whole runs are the uncertainty units, R4. Retain all individual
estimates, nominal t3 intervals and all leave-one-run-out means. Paired window
changes use each run's own difference; timestep and bare/constrained contrasts
are independent Welch comparisons. Zero observed dispersion cannot certify
precision. Primary late-family multiplicity comprises27 target comparisons
(3 connector +24 backbone); use nominal Bonferroni .05/27 sensitivity alongside
pointwise intervals. Trends/secondary diagnostics remain exploratory.

Use analytical nonlinear backbone targets: radial density r² exp[-15(r-1)²],
mu2=I4/I2, mu1=I3/I2; c=coth(10)-.1; B(k)=k*mu2+
2*mu1²*sum_(s=1..k-1)(k-s)c^s. Re²=B(32),
Rg²=sum_(k=1..32)(33-k)B(k)/33², tangent1=c. Reuse accepted radial quadrature
with its 128/256 refinement check, report engineering numerical sensitivity;
never substitute a Gaussian-chain dimension. D1.6A.2 N32 references may be
imported only through their existing full authenticator with covariance and
uncertainty; they are unnecessary for the five primary means.

Secondary: e⁴=125/3, Cartesian connector means/covariance (variance5/3),
histograms, tangents, hypergeometric chain population and contour occupancy.
Population mean8 and fixed Z are conservation, not sampling validation.
Reuse D1.6B ACF diagnostics on regular scalar/full grids, excluding initialization,
including late-half sensitivity and exact-target/sample centering. Unresolved
tails yield null IAT/ESS. No interpolated connector measurements. Stationarity
requires supported tails and consistent windows; stability alone cannot prove
the correct invariant law. No automatic stationary label is permitted.

No new equivalence margin is adopted. Earlier D0 2% size,1% bond,.02 tangent,
.1 e² contextual margins are not automatically tolerances for discretization.
Proposed *planning sensitivities*, not acceptance margins: e² change .01,
relative dimension change .5%, relative bond² change .1%, tangent change .001.
Review these scientific resolutions before pilot execution. Report achieved CI
widths against them; estimate required R using conservative between-run variance
and sensitivity, without treating pilot power estimates as precise at R4.

Compare each dt to target, independent dt contrasts, and constrained-minus-bare
changes at each dt. Constant, linear h and quadratic h models are candidates,
not imposed orders. Three dt levels cannot robustly discriminate arbitrary
remainders; with unsupported stationarity or insufficient precision, do not fit
an extrapolated intercept. Target departures, dt trend, shrinking target error,
insufficient precision and practical equivalence are distinct conclusions.

## Resource budget and readiness boundary

At aggregate throughput v steps/s, GPU time estimate is27.2e6/v seconds:
7.56 hours at1000 steps/s,45.3 minutes at10000 steps/s. These are illustrative
scenarios, not measured predictions. Separate initialization, CPU observation,
GPU integration and total wall telemetry, retaining original timer definitions.
Reserve24 hours as a proposed pilot wall cap pending authenticated host timings.
Per constrained run:51456 scalar rows,104448 connector rows,430848 site rows,
13056 chain and tangent rows each,16896 position rows for two snapshots plus
attachments/endpoints/bonds/events. Bare runs omit connector/attachment rows.
Text-width-dependent disk planning allowance:128 MiB/run,3 GiB total, plus
provenance/logs and headroom; stop at limits rather than thinning output.
Do not request execution until executable/source proof, seed audit, readiness,
resource feasibility and the completed N128 review have been independently checked.

## Implementation status and proposed commands

This commit freezes the candidate physical matrix and scientific design. The
existing D1.6B runner cannot safely launch it unchanged: its authentication,
row counts, schedule and inference hard-code the older cohort. The existing N64
analyzer also hard-codes N64. Neither may be repurposed by changing its frozen
manifest. A new lightweight wrapper still needs implementation and review for
this matrix, binding an explicitly selected independent executable copy and its
build/source proof, immutable schedules/parameters, child exit status, complete
output receipt closure and full cohort analysis. Production executable identity
must not be inferred from a no-op build or system nvcc.

No executable is selected or copied in this preparation. Consequently no safe
pilot execution command or executable regression suite is supplied yet. Proposed
future CLI contract (NOT IMPLEMENTED; do not execute):

    python3 e1_d17_host.py prepare --executable <independent-copy> --build-proof <proof> --root /home/jramirez/UAMMD_KG-evidence/d17/pilot-v1
    python3 tests/d17_regression.py --output /home/jramirez/UAMMD_KG-evidence/d17/regression-v1
    python3 e1_d17_host.py run --root /home/jramirez/UAMMD_KG-evidence/d17/pilot-v1 --approval <reviewed-approval> --approval-sha256 <trusted-sha>
    nice -n 19 ionice -c 3 env OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python3 e1_d17_analyze.py --root /home/jramirez/UAMMD_KG-evidence/d17/pilot-v1

Required regression cases: rational schedules across all dt; distinct seeds and
historical collision checks; fixed physical rate; truncated/missing/nonfinite
frames; receipt/source/executable mutations; output symlinks/path escapes;
R4/LOO and unpaired uncertainty; unresolved ACF; reference error propagation;
rejection of partial cohorts, unauthorized execution and Stage B requests.

DELIVERY LIMITATION: protocol preparation is complete; runner, executable
manifest, analysis implementation and regression specifications are outstanding.
This is not an execution-ready pilot packet. Stop for independent design review;
no scientific acceptance or Stage B authorization follows.
