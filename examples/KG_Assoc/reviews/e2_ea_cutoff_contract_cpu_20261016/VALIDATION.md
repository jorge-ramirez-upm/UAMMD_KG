# CPU validation and reproducibility

Starting SHA: `2f5c991bd354eb3c599f8cb2fed36ed2b5c9f6d2`, verified against remote
KremerGrest with a clean tree before work. No GPU calculation is performed.

## Tests and compilation

* Original candidate regressions pass, plus 398 boundary/periodic/differential
  cases in each single- and double-precision **host-only** build. Both explicit
  arithmetic counterexamples pass under the corrected oracle contract. Injected
  missing/free, extra/associated and distance-only mismatch tests verify evidence
  is written before rejection; successful comparisons neither write a mismatch
  file nor change partners. Readback fixtures reject changed positions, velocities,
  IDs, types, partners, nonfinite data and invalid mappings. Existing evidence
  cannot be overwritten. Exact commands and executable hashes are in
  FINAL_CANDIDATE_CPU_BUILDS.json and final_candidate_*.build/tests.log.
* Fourteen Ea-transfer tests pass, 83.024 s: TRANSFER_TESTS.log. The original
  default reservations are already claimed by immutable smoke plans. Positive
  tests now use a temporary, explicitly test-only reservation fixture with fresh
  values; no real policy/plan/output is modified. A new test requires the real
  consumed reservation set to remain ineligible. Native host preflight still
  authenticates the exact accepted parents, physics, seeds and loader state.
* 149 shared/readback CPU regressions pass, 16.220 s: REGRESSION_TESTS.log. These
  include the previous 145 ordinary E2/acceptance/catalog/recovery/analysis tests
  and four readback tests. READBACK_TESTS.log also records the final four tests
  separately after the rounding-mode check was added. Fixtures are synthetic
  evidence, not trajectories, equilibrium samples or formal registrations.
* Preliminary affected-target compilation succeeded in a new ignored directory.
  The subsequent official forced build from a clean committed tree, actual source/
  executable hashes, native host self-tests and repeated regressions are recorded
  in **BUILD_RESULTS.md**. No historical executable is replaced. The changed
  frontend, candidate-validation executable and candidate test are all rebuilt.

Single/double comparison builds test arithmetic portability; no double-precision
campaign or change to the frozen campaign precision is prepared. The newly added
GPU copies and initialization path are compiled only: their execution remains
reserved for a separately authorized diagnostic retest.

## Reproduction commands

From repository root, point KG_ASSOC_TRANSFER_HOST_EXE at the new out-of-tree
kg_assoc_stars executable; it is used only for --validate-initial-state and
--md-seed-info in these tests:

```bash
PYTHONWARNINGS=ignore::ResourceWarning \
KG_ASSOC_TRANSFER_HOST_EXE=/absolute/path/to/new/build/kg_assoc_stars \
PYTHONPATH=examples/KG_Assoc/campaign \
python3 -m unittest -v test_e2_transfer test_e2_readback
```

The full shared regression command is the one used in the prior GPU-smoke
VALIDATION.md, with test_e2_readback appended. Exact executed test names/results
are retained in REGRESSION_TESTS.log. For the C++ host boundary/oracle suite, run
only the new build's kg_assoc_candidates_test with no arguments. Its default
path uses host coordinate-vector overloads and StickerState(..., false), without
System/ParticleData construction, device allocation or MD. Double comparison uses
its same compiler recipe plus -DDOUBLE_PRECISION, as recorded in the CPU build map.

All included .cu/.cuh changes require forced rebuild. Use the established
kg_assoc_e2.py build --out-of-tree action with a **new** dataset build directory,
from a clean committed tree. It compiles the three E2 targets only. The post-build
receipt is Markdown, added after compilation so it does not change captured source
JSON/Python/native bindings. INTEGRITY.json intentionally excludes that later
receipt; its containing Git commit binds it.

## Historical provenance and integrity

BASELINE_SHA256.json contains 1,739 starting bindings: 1,733 protected live files
remain byte-identical and six authorized source changes are authenticated against
this milestone's starting Git commit. Run:

```bash
python3 examples/KG_Assoc/reviews/e2_ea_cutoff_contract_cpu_20261016/verify_preservation.py
```

PRESERVATION.json records both classes. Earlier manifests are historical source
maps, not current build maps, and remain unchanged. The old counterexample's
original source/binary still documents its original oracle; reproducing that
historical result requires its original source version. Its assertion is not
rewritten to pretend the old oracle and new oracle are the same.

ACCEPTANCE_AUDIT.json records fresh exclusive validation of all twelve prior
acceptance records and their referenced payloads; their hashes match the prior
inventory. All 106 failed-smoke campaign artifact bindings remain unchanged,
including complete/incomplete receipts, plans, approvals and physical output.
All earlier scientific dossiers remain unchanged. FROZEN_SOURCE_AUDIT.json checks
exact unchanged production search, kinetics, partner state, forces, loader and
integrator source bytes. No examples/KG or src file is modified.

The campaign inventory remains 23 systems and twelve qualified acceptances, with
no new registration, registry selection or production authorization. No actual
preparation attempt, fresh campaign stream reservation, GPU retest, kinetic screen
or production preparation is performed. Only new ignored CPU build/evidence
artifacts and scoped implementation/review files are written.

## Limits and readiness

These tests resolve two oracle arithmetic inconsistencies without changing the
production candidate set. They cannot recover the missing failing GPU frame or
prove that either inconsistency caused that failure. They do not prove cell-search
correctness on every extreme finite input. They do not execute the new device
readback, verify actual GPU restart fidelity or establish numerical equilibrium.

The code is ready for a separately authorized capped diagnostic GPU retest using
new immutable attempts and fresh reservation files. The failed smoke remains failed.
No ordinary equilibration or kinetic screen follows automatically.
