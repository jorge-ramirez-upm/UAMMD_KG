# CPU tests and immutable-evidence audit

All assistant jobs were CPU-only and bounded by timeout 600. No native MD,
new trajectory, new plan/approval/reservation, recovery receipt or campaign-state
update was executed. Source starting SHA is
`dbd79b1ba3fba4c9701e54d09de9a9a5cf6e700f`.

| Suite | Result | Evidence |
|---|---|---|
| Established shared regression modules | 189 passed | SHARED_REGRESSION_TESTS.log |
| Transfer regressions against preserved optimized executable | 14 passed | TRANSFER_TESTS.log |
| New forensic/hold tests plus extension regressions | 31 passed; one pre-execution fixture class skipped | FOCUSED_TESTS.log |
| Existing formal Ea6 registration and twelve earlier records | 6 passed | FORMAL_ACCEPTANCE_TESTS.log |
| Native host invariants/MD-stream self-tests | both passed | NATIVE_HOST_TESTS.log |
| Host candidate/cutoff/corruption tests | passed: 398 cutoff cases and 12 velocity ULP rejections | NATIVE_HOST_TESTS.log |
| Actual-history CPU forensic replay | expected missing-readback hold; remaining recorded checks passed | INVESTIGATION.log |
| Read-only status/check | explicit hold; no original bindings changed | CLI_CHECKS.log |
| Preservation | 3,097 unchanged bindings; three scoped existing source/test changes | PRESERVATION.log |

Total: **240 Python tests passed**. The skipped class contains the four original
checks that required all six histories to remain prepared with empty output
directories. That pre-execution condition no longer applies after user-run MD.
Its earlier successful execution remains in the immutable previous handoff.
The new real-plan tests cover all six affected build identities; the forensic
replay authenticates all six original plans/approvals and exact parents and
checks that the other five output directories are empty. The skip does not mark
the failed history valid or exempt it from any required check.

Eight new tests reproduce the exact native-PASS/missing-file failure, sticky
failed-state preservation, rejection without an incomplete receipt, strict
missing-readback rejection, authenticated-evidence-only receipt recovery using
synthetic CPU fixtures, pre-mutation runner holds, common-launcher holds and the
shared defective build across all six actual plans. Simulations are mocked in
unit tests; positive synthetic readback evidence exists only in temporary fixture
directories. No device evidence was fabricated in any real attempt.

The strict validator and native source are unchanged. No build was performed:
the preserved optimized binary was used only with host self-test flags, and the
candidate-test target performs CPU tests. Existing source/build provenance and
all historical executable hashes remain intact. Source changes are limited to
the shared administrative launcher, extension runner, extension test fixtures and
one new regression test module. SOURCE_CHANGES.sha256 binds their exact bytes.

STARTING_BINDINGS.sha256 authenticates 3,100 bindings at the start of this task.
Three existing administrative/test files changed intentionally; the other 3,097
remain byte-identical. ORIGINAL_FILES.sha256 separately binds all 33 relevant
original campaign/output/build/evidence files, including the failed durable
state, both plans, six approvals, two reservations and actual native outputs.
All are unchanged. All thirteen formal acceptance records, their payloads,
protected outputs, previous failed campaigns, successful smoke, scientific
reviews, earlier handoff archive, historical builds and registry bindings remain
preserved. The original twelve records and the newly approved Ea6 record retain
their original bytes and qualifications. No acceptance or registry changes occur.

Reproduce focused CPU tests:

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 env PYTHONPATH=examples/KG_Assoc/campaign \
  PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest -v \
  test_e2_extension_readback_hold test_e2_extensions
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea6_formal_acceptance_20261018/TEST_REGISTRATION.txt
```

The shared/transfer/native test commands are the unchanged CPU commands in the
previous handoff's TEST_COMMANDS.txt, also identified by their full module list in
SHARED_REGRESSION_TESTS.log. GPU commands from the older handoff must not be used
while this hold remains. The scoped repair intentionally stops affected launches;
it does not make the defective build safe or retrospectively validate missing
initial state evidence. Scientific and numerical acceptance remain held.
