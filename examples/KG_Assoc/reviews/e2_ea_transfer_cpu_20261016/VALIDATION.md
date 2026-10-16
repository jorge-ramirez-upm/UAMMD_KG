# CPU validation and integrity

Starting SHA: `283ac81058fe49a75ea0c75e44e443c1ff9928e1` on `KremerGrest`.
The implementation uses the existing frozen restart loader and E2 validation;
no reaction kernel, interaction, integrator, temperature, density or cadence changes.

## Deterministic results

* **13 transfer tests passed, 79.487 s**: [TRANSFER_TESTS.log](TRANSFER_TESTS.log).
  Real accepted parents are authenticated read-only. Tests cover all nine targets
  and three independent controls; native effective seeds; physical/chemical
  fingerprints against ordinary restart; reciprocal chemistry; corrupt parents,
  counters and metadata; wrong Ea/physical parameters/seed/branch identity;
  requested/effective seed collisions; versioned reservation identity; output
  reuse; temporary-root preparation; unsigned approval rejection; derived
  validation/acceptance-reader round trips and ordinary restart compatibility.
* **145 shared regressions passed, 15.687 s**:
  [REGRESSION_TESTS.log](REGRESSION_TESTS.log). This covers acceptance, catalog,
  E2-G1, recovery, joint/continuous assessments, peripheral/satellite diagnostics,
  reproducibility and the E2 workflow.
* Both changed native targets were forcibly compiled in `/tmp/ea_transfer_cpu_build/`
  without replacing existing executables. Both host-only `--self-test` calls passed:
  [CPU_BUILD.json](CPU_BUILD.json), exact commands/build logs, and
  [HOST_SELF_TESTS.log](HOST_SELF_TESTS.log).
* All twelve native initialization preflights return before device/System creation,
  output I/O or MD. Fingerprints match the original restart state in the existing
  loader representation. The three original parent families remain the statistical
  independence units; twelve branches are not twelve independent preparations.

Synthetic static segment files are bookkeeping fixtures in temporary directories,
not physical trajectories or scientific equilibration evidence. Acceptance-reader
fixtures are in memory; no campaign acceptance record was created.
These tests are deterministic regression checks, not stochastic convergence tests.
No dynamic or GPU validation has been performed for this new path.

## Reproduction

From repository root, after compiling the changed native front end, run:

```bash
KG_ASSOC_TRANSFER_HOST_EXE=/tmp/ea_transfer_cpu_build/kg_assoc_stars \
PYTHONPATH=examples/KG_Assoc/campaign \
python3 -m unittest -v test_e2_transfer
```

The shared regression command is:

```bash
PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_e2_acceptance test_catalog test_e2_g1 test_e2_recover \
  test_joint_e2 test_e2_continuous_review test_e2_continuous4m_review \
  test_e2_continuous8m_review test_e2_satellite_continuation \
  test_e2_peripheral_network test_e2_window_sensitivity test_reproduce \
  test_joint_rp040_8m test_run_e2
```

The official clean-commit out-of-tree build and repeated transfer tests using
its executable are recorded in the subsequent [BUILD_RESULTS.md](BUILD_RESULTS.md).
That Markdown receipt is committed after the build, without changing any source
JSON/Python/native file captured by its source manifest. It is bound by its Git
commit rather than the earlier INTEGRITY.json, avoiding a self-referential build.

## Preservation and historical source provenance

Run `python3 examples/KG_Assoc/reviews/e2_ea_transfer_cpu_20261016/verify_preservation.py`.
[BASELINE_SHA256.json](BASELINE_SHA256.json) preserves 1,334 prior bindings:
1,327 protected live file bindings remain byte-identical, and seven authorized
implementation source files have authenticated source transitions. Their exact
historical bytes still match the starting Git commit; prior source manifests
were neither rewritten nor reinterpreted as current build evidence.
[PRESERVATION.json](PRESERVATION.json) records both classes explicitly.
The prior feasibility review's 47 source bindings are also checked with this rule.

[ACCEPTANCE_INTEGRITY.json](ACCEPTANCE_INTEGRITY.json) records fresh exclusive
validation of all twelve immutable acceptances, including their referenced
payload hashes. All twelve record hashes match the earlier inventory. Protected
simulation outputs, accepted endpoints, prior reviews, frozen source and preserved
executables remain unchanged. No files in `examples/KG/` or `src/` were modified.
Campaign inventory remains 23 systems, twelve formal qualified acceptances,
no selected registry and no production authorization.

[INTEGRITY.json](INTEGRITY.json) binds the scoped implementation/configuration,
tests and this dossier, excluding itself and the later BUILD_RESULTS.md receipt.
The containing Git commits bind those exclusions.

## Scientific limits and next gate

The code is ready for a separately authorized capped GPU smoke. Device state
restoration, candidate-oracle comparisons, numerical behavior and coupled-sampler
invariance remain to be tested before any ordinary derived equilibration segment.
No claim of equilibrium invariance, full stationarity, complete structural
mixing or absence of initialization bias follows from these CPU tests.
The reference qualifications and historical executable authentication limits
remain explicit in each derived lineage.

No GPU calculation, actual derived attempt, formal acceptance, registry selection,
production preparation or production launch was performed.
