# Authenticated native build and CPU checks

New out-of-tree build: `examples/KG_Assoc/kg_assoc_100m/builds/ea_transfer_16m_20261017_v1`.
Native source SHA: `2d56f2ec26ba5780fcf38549264e7070ec46c71c`.
Forced compile: NVCC 12.8, GCC 11.2, production -O3, 73.661 seconds, all three targets.
Historical builds remain unchanged. The later handoff changes only Python
administration/tests and documentation, so this native build remains current.

| Executable | SHA256 |
|---|---|
| kg_assoc_stars | 1c3b6d9581fd02210187d356db268282235e2dc8b01a482492e6219e3e680397 |
| kg_assoc_stars_candidate_smoke | f108e201b2280af28df6ffc607f5b138900bca9f0a67954e59a90e05f51ab5f8 |
| kg_assoc_candidates_test | 38945cd2d684e705e3ad405051e4108fdd8712651c8239d95afd0e9fdba22da2 |

The full manifest, compile commands, source map and compiler logs are bound by
ARTIFACTS.sha256 and the archived BUILD_MANIFEST.log. Both native host self-tests,
the candidate suite, 398 strict-cutoff/periodic cases and twelve ULP negative cases
passed. Native host cap probes: one valid16M and eleven rejected scope/duration/
parent cases. Prepare ran nine host-only initial-state checks.

The full-parent optimized CPU probe verified 43,563 particles and 130,689 exact
float32 velocity components. No GPU context or MD was invoked by those CPU probes.
The initial literal preprocessor comparison failed only because two
`__cudaSafeCall` error-report line numbers changed:1103→1113 and1159→1169.
After normalizing exactly those two occurrences and build timestamps, every
ordinary simulation token matched. The refined check asserts both occurrences
and exact equality of all remaining tokens; it does not ignore arbitrary changes.

The final handoff CPU suites and actual nonexecuting --check are separately
archived. Every agent-run job after cancellation is a short test under ten minutes;
no further native MD or GPU diagnostic was launched.
