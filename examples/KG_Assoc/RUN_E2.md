# E2 campaign: terminal workflow

Run from the repository checkout on the Linux GPU host:

```bash
git pull --ff-only origin KremerGrest
python3 examples/KG_Assoc/campaign/run_e2.py smoke-all
```

The second command authorizes only the seven E2-G1 numerical smoke conditions,
10,000 steps per replica, three replicas each. It verifies and skips compatible
completed tests, including the already passed weak-binding and dilute tests.
It runs the remaining f=3, f=6, N=20, N=40 and corrected C1 Ea=8 switch tests.
A failed/tampered/incompatible prior test is retained and gets a new attempt.
No equilibration extension, equilibrium acceptance or production is launched.
Rerunning the same command verifies existing results and runs only missing tests.

The wrapper discovers the repository/dataset from its own location, requires
`KremerGrest`, authenticates the frozen inventory/parents, reuses a build bound to
the current committed sources or forces a rebuild, allocates unique attempt IDs,
and generates plan-hash-bound approval records from the explicit CLI request.
It records user, host, argv, PID, code SHA and request hash. These records attest
to terminal-command authorization; they are not scientific acceptance records.
The checkout must be clean. GPU driver/build/validation failures retain logs and
return a nonzero exit code. Ctrl-C stops the active runner; its evidence remains.

Other commands require no paths, approval editing or version numbers:

```bash
python3 examples/KG_Assoc/campaign/run_e2.py status
python3 examples/KG_Assoc/campaign/run_e2.py smoke --system F03_N010_RP080_EE08_EA04
```

`status` performs verification, runs no MD, and reports completed, pending,
failed and running attempts. Legacy/external-host processes without local
liveness evidence are explicitly unresolved. The named smoke command authorizes
only that condition, including automatic corrected-C1 selection for the Ea=8 ID.

## Wave A: first 2M scientific checkpoint

From an updated `KremerGrest` checkout on the GPU host, run this one command:

```bash
python3 examples/KG_Assoc/campaign/run_e2.py equilibrate --system F04_N010_RP080_EE04_EA04 --steps 2000000 --window-steps 500000
```

It selects the frozen three independent E1 histories, starts each unbound at
absolute E2 step zero, reuses verified compatible smoke evidence and an
authenticated build (or rebuilds automatically), allocates unique plans and
fresh MD seeds, and runs the histories **sequentially**. Chemistry seeds remain
those in the fixed bank seed map. Physics is T=1, dt=0.01, Ea=4, Ee=4 and all
other frozen protocol parameters. Approval JSON and paths require no manual work.
The same command without `--window-steps` also defaults to 500k for 2M segments;
the explicit option makes the review checkpoint visible in the requested argv.

After every history the existing fail-fast numerical/event/network/conformation
validator runs. After all three pass, the command automatically revalidates and
analyzes four windows: (0,500k], (500k,1M], (1M,1.5M], (1.5M,2M]. No initial
transient is discarded. It prints a short 3/3 completion summary and the path of
`SCIENTIFIC_REVIEW.md`, with window populations, intra/inter bonds, reaction and
distinct-neighbor exchange rates, connectivity, L1/L2, Rg² and arm end-to-center
R². The report includes autocorrelation SEM/effective samples, drift slopes,
replica Student-t intervals, paired late-window changes and mixing/resolution
flags. Detailed 5/10/20-block sensitivity and exact event-integrated exposures
remain in the linked immutable JSON/CSV evidence.

**2M is a first review checkpoint, not equilibrium acceptance.** No extension,
other condition or production is launched. If a completed ordinary segment
already exists, this command refuses to silently extend it. Execution or analysis
failure returns a nonzero exit, retains all evidence and does not mark scientific
review complete. Valid MD data survive an analysis failure and can be reviewed
later with the read-only `review` command.

Estimated MD time on the recorded TITAN Xp: about 9.9 minutes/history, **30 minutes
for three sequential histories**, based on the corrected C1 2M ordinary-run
measurements (same molecular geometry, different Ee). Allow additional rebuild
and CPU replay/analysis time; Ee-dependent reaction/topology work can change the
runtime. This is an estimate, not a measured result for the new condition.

## Later E2 equilibration — separate explicit authorization

These are usage examples, **not authorized by the wrapper implementation task**:

```bash
python3 examples/KG_Assoc/campaign/run_e2.py equilibrate --system F03_N010_RP080_EE08_EA04 --steps 2000000
python3 examples/KG_Assoc/campaign/run_e2.py review --system F03_N010_RP080_EE08_EA04
```

`equilibrate` launches exactly one named three-history segment of the requested
length and automatically generates its scientific review. It first verifies or executes the necessary 10k oracle smoke for the
same condition and exact parents; that capped prerequisite is recorded under
this explicit command. Fresh preparation requires Ea=4. Accepted C1 is excluded
from further equilibration. Lengths must be multiples of 1000 and at least 4000,
to support synchronized review. No automatic extension occurs. If an ordinary
completed segment exists, extension needs the same explicit command with
`--extend`; the latest unique validated segment becomes its authenticated parent.
A failed/incomplete attempt is retained; a retry receives a fresh identity and
fresh MD seeds. Extensions retain chemical RNG identity and absolute steps.

`review` revalidates and analyzes all completed ordinary segments for the named
system, writes new immutable reports, and prints their locations. It defaults
to 500k windows for segment lengths divisible by 500k; otherwise it uses two
equal windows (when each is at least 4000 steps), or one full window.
`--window-steps N` can request a different valid partition. Correlation,
replica agreement, chemistry activity, network topology and conformation still
require scientific review. One-window reports cannot establish late-window
stationarity. It neither accepts equilibrium nor launches extra MD.

## Compatibility and provenance

Reuse always calls the existing full completion/event/topology/conformation
validator. It compares parents, chemistry seeds, Ea/Ee and all other physical
parameters, exact executable hashes and scientific/validation source hashes.
Administrative changes to `run_e2.py`, the E2 orchestration helper, and regression
tests alone do not invalidate a verified numerical smoke; changes to CUDA,
kinetics, numerical code, validators, analysis or frozen parameter manifests do.
Authenticated builds from an ancestor commit can likewise be reused when all
scientific sources, all six executable hashes and build-log hashes still match.
The original build SHA/source record is preserved; the new plan pins current
sources and references the original immutable build manifest. Administrative
report/wrapper changes require no CUDA rebuild or repeated GPU smoke.
Old plans/approvals/completions are never edited or relabeled. A new segment is
bound to current committed sources/builds and its own authorization; any reused
smoke's original plan/completion hashes are recorded by the underlying runner.

Commands are serialized by an OS advisory lock, automatically released when the
process exits. Underlying attempt/replica exclusivity, fail-fast checks, distinct
chemical seed maps, fresh recorded MD seeds, corrected-C1 8M authentication and
mandatory production acceptance registries remain in force. Reports and request
records are stored under `aggregate/e2/workflow/`; all output names are generated.
There is no production subcommand. Physics, integrators and production parameters
are unchanged. Details of scientific validation remain in [E2_G1.md](E2_G1.md).

## Recover the interrupted dilute 2M checkpoint

After updating the clean `KremerGrest` checkout to the recovery implementation,
run exactly:

```bash
python3 examples/KG_Assoc/campaign/run_e2.py recover --system F04_N010_RP020_EE08_EA04
```

The command discovers the unique ordinary attempt for this condition. It requires
its original plan-bound approval, pinned E1 parents, geometry, chemistry and MD
seeds, full physical parameters, scientific source hashes, executable/build-log
hashes and matching completed smoke evidence. Unrelated documentation, catalog,
or administrative runner/test changes can have a different Git SHA; changes to
physics, integrators, validators, scientific analysis or frozen manifests fail
closed. The original plan commit must be an ancestor of the recovery checkout.
Recovery never rebuilds executables or launches replacement smokes.

It fully revalidates r001 and the preserved r002 outputs before any missing MD.
An orphaned endpoint needs the original authenticated start, all required outputs,
the executable PASS marker and full numerical/event/network/conformation validation;
PASS alone is insufficient. Only the unstarted r003 runs, sequentially, using its
exact original command, parents and seeds. Incomplete MD payloads are refused;
they are never overwritten or restarted from E1. An interruption before MD may
leave empty logs/administrative receipts: these are preserved, with new recovery
logs allocated separately. Completed recovery MD gets its own hash-bound endpoint
receipt before post-MD validation so subsequent recovery never repeats it.

Each invocation creates exclusive authorization and validation receipts under
`banks/e2_recoveries/` and a wrapper journal under `aggregate/e2/workflow/`. The
records bind the original plan/approval, preserved file hashes, original and
recovery code commits, user request and per-history operation. The original
plan, approval, r001 completion, old failure receipts and all existing outputs
remain byte-identical. Missing completion records are added exclusively after
validation; they point to the recovery authorization. Original wall time is
unknown for an orphaned endpoint and is not fabricated.

After all three histories validate, the original scientific analyzer produces
four 500k-step windows and prints `SCIENTIFIC_REVIEW.md`. Repeated invocation
revalidates completions, runs no completed MD, and reuses a hash-bound compatible
review. Failed invocations retain their journals/output evidence; they return a
nonzero exit code. Multiple ordinary attempts are ambiguous and cause a safe
stop rather than timestamp-based selection. No extensions, other conditions,
equilibrium acceptance or production are authorized.

This operation was implemented in an isolated worktree starting at
`5084f44a1ab3c0e98052761a91bcfd42d706ccf7`. Regression tests use deterministic
GPU-process mocks. No recovery GPU calculation was run in the coding environment;
the command above is the required GPU-host execution check.
