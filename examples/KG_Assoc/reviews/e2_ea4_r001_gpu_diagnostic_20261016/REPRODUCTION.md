# Read-only reproduction and integrity

From repository root, with original dataset artifacts present:

```bash
python3 examples/KG_Assoc/reviews/e2_ea4_r001_gpu_diagnostic_20261016/VERIFY_DRIVER.txt
python3 examples/KG_Assoc/reviews/e2_ea4_r001_gpu_diagnostic_20261016/ANALYSIS_DRIVER.txt \
  --output /tmp/UNUSED_ea4_r001_diagnostic_analysis
```

Neither command launches an executable, opens a CUDA context, allocates streams,
registers an acceptance or modifies an attempt. The analysis independently checks
the plan-bound scoped approval, complete receipt/output hashes, exact per-particle
device evidence, both empty unselected directories, numerical/chemical endpoint
validation, accepted events and strict runtime candidate-check cadence. It rebuilds
the network summaries with validated existing readers and integrates populations
in exact integer MD-step units. A same-step synthetic exposure self-check is
included. The prior event-exposure/network helpers are reused unchanged.

VERIFY_DRIVER.txt also audits 2,255 unchanged old bindings, authenticates the one
administrative launcher transition against the continuation-start Git blob, freshly
validates all twelve formal acceptances, checks the existing native build and
requires exact regenerated RESULTS.log identity. It checks both new hash maps.
ANALYSIS_DRIVER.txt writes only to a new output directory. Archived .txt drivers
and .log metadata follow the existing dossier convention; they are read-only
analysis/evidence rather than changes to native simulation source or build flags.

PLAN.log, APPROVAL.log, COMPLETION.log, SEED_RESERVATIONS.log, AUTHORIZATION.log and
EXECUTION_METADATA.log retain exact parsed identities; selected original JSON bytes
are copied verbatim under .log names. Raw particle readback, snapshots, sidecars,
plans, launch metadata and logs remain at their immutable dataset paths, all bound
by ARTIFACTS.sha256. INTEGRITY.sha256 binds the dossier except itself, which is bound
by the containing Git commit. BASELINE.sha256 pins the previous protected evidence;
PRESERVATION.log lists the one intended source transition and final audit counts.
The earlier held-preflight dossier remains unchanged and is superseded for execution
capability by the explicitly authorized selector, not rewritten.

CPU reproduction of the administrative selector (all subprocesses mocked):

```bash
PYTHONPATH=examples/KG_Assoc/campaign python3 -m unittest -v test_e2_single_history
```

REGRESSION_TESTS.log records 159 tests (149 previous shared/readback plus ten new
selector tests); TRANSFER_TESTS.log records fourteen; READBACK_CPU_TESTS.log records
nine (four overlap the shared suite, five forensic). This is 178 distinct passing
Python tests. Selector development runs with eight and then ten cases are retained
separately. Native host logs cover both self-tests, original candidate regressions,
398 boundary/periodic cases and twelve float32 ULP rejection cases. Source checks
verified that no native/header file changed; the existing build checker explicitly
ignores these administrative launcher/test changes for physical build equivalence.
No rebuild or replacement of any historical executable was needed.

PREPARE_DRIVER.txt is an archive of one immutable preparation, not a rerunnable
recipe or additional execution authority. It fails if output/reservation paths
exist. It checks fresh requested/effective stream collisions before reserving the
required twelve-row policy and uses the established derived planner. The planner's
three host probes do not launch r002/r003. The only real launch used the committed
CLI with --replica 1, --execute and the scoped plan-bound approval. Do not rerun
that launch, reuse its seeds or continue from its smoke endpoint under this task.
The per-history complete receipt is valid; the ordinary three-history verifier
remains unchanged and is not appropriate for claiming a complete triplet here.
