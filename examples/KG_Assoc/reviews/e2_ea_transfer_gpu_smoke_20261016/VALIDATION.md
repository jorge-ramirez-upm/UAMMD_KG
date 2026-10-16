# Validation, reproducibility and preservation

**Overall GPU smoke failed at Ea8 r001.** Passing CPU tests and six numerical
completions do not override the candidate-oracle failure or certify this milestone.

## Checks run

* 145 existing shared CPU regressions passed, 15.878 s; REGRESSION_TESTS.log.
* Five new deterministic CPU analysis tests passed; ANALYSIS_TESTS.log. They test
  exact event-integrated exposures, zero-event records, same-step/end events,
  invalid chronology/population, complete multiplicity/loop/degree accounting and
  nonzero sparse-count uncertainty. These are not stochastic convergence tests.
* The unchanged host-only candidate regression passed; CANDIDATE_CPU_TESTS.log.
  Its existing random/dyadic and cutoff cases miss the new precision counterexample.
* The new actual-C++ host-only counterexample reproduces the unchanged count mismatch.
  COUNTEREXAMPLE.log, source, compiler command, build log, source/header/executable
  SHA256 and compiler provenance are preserved. Exit status zero means **the
  discrepancy was reproduced**, not that the candidate contract passed.
* Six histories passed the established numerical validator, accepted-event/network
  replay and 100 candidate-oracle sweeps each. The failed history has 70 successful
  sweeps and one count mismatch; the five unstarted histories have no observations.
* Partial replay checks all eight Ea8 accepted events through the last diagnostic,
  reciprocal partner/counter/graph accounting, finite conformation and numeric
  samples, absolute cadence, physics and actual effective MD stream. No missing
  endpoint is synthesized. Exposure through the next sweep uses the documented
  stop-step inference, not a nonexistent completion receipt.

The previous 13 transfer tests passed before allocation, as documented in the
CPU milestone. Their positive-path fixtures assume unused default reservations;
those reservations are now legitimately claimed. They are not rerun against an
occupied campaign or weakened to allow reuse. The relevant shared regressions and
new analysis tests above were run for this milestone.

## CPU reproduction only

From repository root:

```bash
PYTHONWARNINGS=ignore::ResourceWarning \
python3 examples/KG_Assoc/reviews/e2_ea_transfer_gpu_smoke_20261016/reproduce.py \
  --output /tmp/ea_smoke_review_reproduction

PYTHONPATH=examples/KG_Assoc/reviews/e2_ea_transfer_gpu_smoke_20261016 \
python3 -m unittest -v test_smoke_analysis
```

The first command authenticates plans, approvals and output hashes read-only,
reruns the six complete validations plus failed-history partial replay, and writes
new analysis artifacts only. It does not invoke a GPU executable, launch MD or
attempt formal acceptance. REPRODUCTION_CHECK.log records independent regeneration
from the review helper; RESULTS.json is compared exactly after canonical JSON
serialization, and both summary CSVs are compared byte-for-byte. Figure byte hashes
can depend on plotting-library metadata/version; the plotted numeric records are bound.

The counterexample uses the original out-of-tree build’s candidate-test compiler
recipe with only source/output paths replaced. Exact argv and cwd are in
COUNTEREXAMPLE_COMMAND.json. Its `main` calls only host vector overloads: no System,
ParticleData, GPU allocation, kernel or trajectory. It includes the unchanged
candidate and oracle headers. No physics or search changes are implemented.

The 145-test shared command is the one preserved in the CPU milestone’s
VALIDATION.md; the full executed test names/results are in REGRESSION_TESTS.log.

## Integrity

All **1,602 preserved starting file bindings** match BASELINE_SHA256.json.
All twelve prior acceptance records match their prior hashes and pass fresh
exclusive validation, including their referenced payload hashes. Historical source
bindings also pass the prior CPU preservation helper, which authenticates seven
source changes made in that *earlier* milestone against its starting Git commit.
This GPU milestone changes **zero existing simulation or campaign source files**.
No earlier scientific review, reference pair, executable, frozen kernel, force law,
candidate search, integrator or acceptance record is modified.

INTEGRITY_VERIFICATION.json records the checks. NEW_OUTPUTS_SHA256.json binds 106
new immutable campaign files. EXECUTION_METADATA.json preserves parsed plan/approval/
receipt/environment copies, while the raw-file hashes preserve their exact identities.
INTEGRITY.json binds every new dossier file except itself (bound by its Git commit).
Run `python3 examples/KG_Assoc/reviews/e2_ea_transfer_gpu_smoke_20261016/verify_integrity.py`
for a read-only byte audit, including all 591 historical build source bindings.
This historical audit is not a new live-build or GPU-execution authorization.

The campaign remains 23 systems and twelve formal qualified acceptances. There is
no new registry selection/activation, production authorization or preparation.
The only scope deviation is fail-stop execution: six completed, one failed, five
not executed, rather than proceeding after a failed oracle. No additional GPU
work, rerun, ordinary equilibration or kinetic screen was attempted.
