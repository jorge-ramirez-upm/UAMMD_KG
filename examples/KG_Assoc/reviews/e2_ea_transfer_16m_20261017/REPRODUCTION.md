# Reproduction and integrity

The user-run commands are in RUN_YOURSELF.md. The assistant must not run long jobs.

CPU-only authentication, with the original protected dataset/builds present:

```bash
timeout 600 python3 examples/KG_Assoc/campaign/run_ea_preparation.py --check
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_transfer_16m_20261017/VERIFY_HANDOFF.txt
```

Focused mocked launcher and self-run lifecycle tests (no GPU):

```bash
PYTHONPATH=examples/KG_Assoc/campaign timeout 600 python3 -m unittest -v \
  test_e2_derived_preparation test_e2_single_history test_e2_remaining_smoke \
  test_run_ea_preparation
```

These forty cases overlap the 189-test shared suite. Its module list is visible
in REGRESSION_TESTS.log; transfer and forensic suites add fourteen and five tests.
The native host logs record the separate cutoff/readback/cap and parent probes.
Every test group is short and capped at ten minutes when its runtime is uncertain.

PREPARE_DRIVER.txt and EXECUTION_DRIVER.txt archive the **cancelled** campaign's
original invocation. They are not self-run instructions and must not be rerun.
Their used paths and streams remain immutable; the new user-facing runner handles
fresh attempts automatically and never invokes those archived drivers.

ARTIFACTS.sha256 authenticates the raw cancelled campaign, native build, reservation,
CPU evidence and analysis-development files. STOPPED_OUTPUTS.sha256 separately
freezes the three old plans, approvals and the single partial output directory.
BASELINE.sha256/PRESERVATION_FINAL.log bind 2,626 untouched earlier files and the
three intended source transitions authenticated against starting Git. All twelve
formal acceptances and payloads remain unchanged. USER_CODE.sha256 pins the final
policy, planner/validator/native sources and user-run tests/entry point.
INTEGRITY.sha256 binds every dossier file except itself, which is bound by Git.
Older source maps still describe their original commits; administrative code is
not falsely claimed byte-identical to historical source versions.

The final --check is actual host authentication, not a new GPU trajectory. The
new manual runner's lifecycle is CPU-tested with launches mocked. Actual prior
GPU evidence covers the preserved numerical smoke and the cancelled Ea6 partial;
it does not prove that a future long run cannot encounter hardware or numerical
failures. Those gates remain strict, and real failures remain explicit.
