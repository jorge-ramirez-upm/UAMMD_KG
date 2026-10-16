# Validation and reproduction

## Results

* **GPU milestone: failed.** One actual device readback, failed native comparison,
  zero MD steps, zero chemical/oracle sweeps, zero completions, eleven unstarted.
  The launcher stopped at the first failure. No retry, correction, alternative
  executable or gate relaxation was attempted. Numerical/event replay cannot
  validate a nonexistent trajectory; there are no final endpoint hashes/receipts.
* **149 shared/readback CPU tests pass**, 16.044 s: REGRESSION_TESTS.log.
* **14 transfer tests pass**, 86.459 s: TRANSFER_TESTS.log. Consumed default
  reservations remain ineligible; positive fixtures use temporary test-only seeds.
* **5 new deterministic forensic tests pass**, ANALYSIS_TESTS.log: raw-double
  versus represented float32, observed expected-column defect, exact mismatch
  detection including one float step, correct rounding and nonfinite rejection.
  These test analysis, not stochastic convergence or native GPU success.
* Host-only candidate suite passes its original cases, both arithmetic
  counterexamples, 398 cutoff/periodic cases and injected mismatch/readback tests:
  CANDIDATE_CPU_TESTS.log. Native host self-test passes NATIVE_HOST_SELF_TESTS.log.
  This milestone does not rerun the separate historical double-precision build.
* The first shared-suite invocation omitted two review directories from PYTHONPATH:
  135 tests passed, two modules failed import (137 reported). The original logs and
  command JSON are retained. The existing documented PYTHONPATH then passed all
  149 before execution. No test assertion or execution gate was weakened.
* All twelve exact accepted corrected-C1 host states pass initialization and native
  effective-seed queries during immutable planning; initial receipts are embedded
  in EXECUTION_METADATA.json. All four plans/approvals are revalidated before launch.
* The native host-only narrowing probe reproduces the expected-value problem with
  NVCC 12.8/GCC 11.2 `-O3`, while `-O0` and explicit volatile-float storage round all
  axes. COMPILER_PROBE.json records exact commands and source/executable hashes.
  Probe exit zero means the host experiment executed, not that the smoke passed.
  No CUDA calls, allocation, kernel or trajectory exists in narrowing_probe.cu.

## CPU-only reproduction

Run from repository root with the original authenticated dataset/build artifacts
present. Large raw particle evidence remains in the dataset, as in earlier reviews;
this is not a self-contained replacement for the protected campaign payloads.

```bash
python3 examples/KG_Assoc/reviews/e2_ea_transfer_gpu_diagnostic_retest_20261016/reproduce.py \
  --output /tmp/ea_transfer_diagnostic_retest_reproduction

PYTHONPATH=examples/KG_Assoc/reviews/e2_ea_transfer_gpu_diagnostic_retest_20261016 \
python3 -m unittest -v test_diagnostic_analysis

python3 examples/KG_Assoc/reviews/e2_ea_transfer_gpu_diagnostic_retest_20261016/verify_integrity.py
```

Reproduction authenticates the new artifact map, all four immutable plans and
approvals, original parents, no-completion statuses and empty unstarted directories.
It audits all 43,563 device rows against authenticated parent data, expected physical
representation, partner reciprocity, metadata and the embedded build identity.
It reconstructs the three reference graphs using the existing validated topology
reader, with all multiplicities/loops/degrees/components/isolated IDs and snapshot
conformations. It does not call an executable, initialize CUDA or perform MD.

The independent actual-velocity audit does **not** change the native footer,
output file, official validator or failure status. Exact float32 representation
is checked with struct.pack/unpack; no epsilon is introduced. OFFICIAL_READBACK_REJECTION.json records that the unchanged official reader also
rejects `readback_pass=0`, as required. The raw readback
has `readback_pass=0`. There is no successful full E2 verification receipt.

REPRODUCTION_CHECK.json records exact regenerated RESULTS.json and HISTORIES.csv
identity from a separate output directory. Figure metadata is library-dependent;
the numeric error values and complete readback bytes remain hash-bound. The
figure displays actual minus recorded-expected velocities, not physical drift.

To rerun the shared/transfer CPU suites, use the documented environment from the
preceding CPU review, including both RP040 review modules and analysis/campaign
paths, appending test_e2_readback. CPU_CHECKS.json records exact module lists;
CPU_COMMAND_DRIVER.txt archives the executed environment and commands, not a launch recipe.
Its exclusive log creation intentionally refuses to overwrite existing evidence.
The native executables are used only in host test/seed/initialization modes.

To repeat the compiler probe, compile narrowing_probe.cu in a fresh temporary
output directory with the compiler/flags in COMPILER_PROBE.json; substitute only
source/output paths and run arguments `0.270623 0.266728 0.876108`. Output columns
are axis, serialized double, direct float-cast-then-widen result, and forced stored
float-then-widen result. No runtime source is patched by this experiment. These
are small separate CPU-probe builds, not replacements for campaign executables.

## Integrity and limits

The preflight verified clean local/remote SHA agreement, the prior CPU dossier's
scoped hashes, its historical-source preservation helper and all 106 previous
failed-smoke bindings. All twelve existing formal acceptances/payloads passed
fresh exclusive validation; PREFLIGHT.log records each success. BASELINE_SHA256.json
then captured 1,773 current bindings including protected output, reviews, accepted
states, records and historical build/source bytes. All remain unchanged.
NEW_OUTPUTS_SHA256.json binds 28 new campaign files. INTEGRITY.json binds the new
review files except itself, which is bound by its containing Git commit.
verify_integrity.py checks all three maps and the unchanged acceptance inventory.
No existing simulation, campaign, examples/KG or src source is changed. The new
reservation's exact tracked snapshot is SEED_RESERVATIONS.json; raw campaign
plans/outputs stay in their original ignored locations under established conventions.

This is a failed execution milestone with a localized validation defect and a
proposed next CPU repair. It is not an implemented repair, passed restart smoke,
kinetic test, equilibrium-invariance test, acceptance or production authorization.
No rates/uncertainty intervals are estimated from zero exposure. The three parent
families cannot become twelve independent preparation samples by branching.

Raw test logs are preserved verbatim, including test-runner trailing spaces.
The source/document whitespace check excludes those evidence logs.
