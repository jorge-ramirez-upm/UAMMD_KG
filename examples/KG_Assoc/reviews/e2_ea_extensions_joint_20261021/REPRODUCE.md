# Reproduce the CPU-only review

Start from the repository root on the host retaining the immutable campaign dataset. Python 3,
NumPy and Matplotlib are required. No command below launches GPU integration. Original dataset
paths under `/home/jramirez/UAMMD_KG` must remain available for full numerical authentication;
the committed replay archives support scientific inspection without replacing the original
device-readback evidence, endpoint files or validators.

The review reuses the authenticated prior 24M dossier and the existing ordinary endpoint validator.
Review source files have `.txt` names following the established dossier convention; no simulation
source map is modified. Use a **new output identity** for a fresh replay; never point the analysis
driver at an existing original attempt or overwrite a completed analysis file.

Each command below is an independent CPU job with a ten-minute timeout. Run histories separately;
do not replace them with a single unbounded nine-hour batch or any simulation command.

```bash
cd /home/jramirez/UAMMD_KG
git status --short --branch
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/VERIFY_DRIVER.txt
timeout 600 env OPENBLAS_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/ANALYSIS_TESTS.txt
```

For a new complete replay, choose an unused directory under `kg_assoc_100m/aggregate/e2`, for
example `ea_extensions_joint_cpu_replay_v2`. Execute each history command individually:

```bash
timeout 600 env OPENBLAS_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/ANALYSIS_DRIVER.txt --history 0 --output examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/analysis
timeout 600 env OPENBLAS_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/ANALYSIS_DRIVER.txt --history 1 --output examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/analysis
timeout 600 env OPENBLAS_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/ANALYSIS_DRIVER.txt --history 2 --output examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/analysis
timeout 600 env OPENBLAS_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/ANALYSIS_DRIVER.txt --history 3 --output examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/analysis
timeout 600 env OPENBLAS_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/ANALYSIS_DRIVER.txt --history 4 --output examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/analysis
timeout 600 env OPENBLAS_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/ANALYSIS_DRIVER.txt --history 5 --output examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/analysis
mkdir -p examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/summary
timeout 600 env OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/ea_review_matplotlib python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/SUMMARIZE_DRIVER.txt --analysis examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/analysis --output examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/summary
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_extensions_joint_20261021/REPORT_DRIVER.txt examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/analysis examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/REPLICA_DIAGNOSTICS.md examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/summary
```

The analysis tests default to the original review analysis directory. They verify the committed
review archive computations and actual-series snippets; VERIFY_DRIVER checks the archived files
and original raw hashes. The original preparation archives remain under the prior dossier.
An 8M-origin edge ledger crosses the state handoff only to measure structural identity continuity;
all ACFs, IATs, SEMs and residence episodes remain in their respective MD segments.

The established CPU regression command used was:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_transfer_24m_joint_20261018/CPU_TEST_DRIVER.txt --output examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_extensions_joint_cpu_replay_v2/cpu_regression
```

The focused campaign tests were run from `examples/KG_Assoc/campaign`:

```bash
timeout 600 python3 -m unittest test_e2_extensions test_e2_transfer test_e2_acceptance test_e2_single_history
```

Result: 63 tests in 93.199 seconds, OK with one existing opt-in skip. `RUN` lines printed by
extension administration tests are mocked launcher fixtures, not GPU execution. The established
suite completed 189 tests in 22.335 seconds. Review-local direct/FFT, event/exposure, boundary
and actual-series tests completed 10 tests in 1.752 seconds. Legacy ResourceWarnings in the
focused suite are retained as a maintenance limitation. Exact test output for the established
and review-local suites is included in this dossier.

INTEGRITY.sha256 binds the new dossier; PRESERVED.sha256 binds 3,588 pre-review files.
ANALYSIS.sha256 binds each uncompressed member of the six new replay archives.
PROVENANCE.tar.gz contains byte copies of 73 original plans/approvals/reservations/build manifests,
receipts, logs and durable state; PROVENANCE.sha256 binds their original absolute paths.
No native executable is embedded in the dossier, and no missing GPU evidence is synthesized.
