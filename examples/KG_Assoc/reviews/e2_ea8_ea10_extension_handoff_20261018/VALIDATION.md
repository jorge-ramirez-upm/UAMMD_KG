# CPU validation and preservation

Milestone began 2026-10-18 and completed checks on 2026-10-19 local time.
Starting clean local/remote KremerGrest HEAD was
`ceb4048a00897b8c335d718d885f9e14ac2c37e7`.
Administrative/native-front-end source was committed as
`79fbba03348b575faa2da988f9eaedf51772579c` before building or preparing attempts.
No GPU calculation was launched. Every assistant CPU job was bounded by timeout 600.

| Check | Result | Evidence |
|---|---:|---|
| Established shared regression modules | 189 passed | SHARED_REGRESSION_TESTS.log |
| Transfer regression against new optimized native front-end | 14 passed | TRANSFER_TESTS.log |
| Extension scope, lifecycle, actual six parents and native rejection | 27 passed, no skips | EXTENSION_TESTS.log |
| Exact Ea6 registration, qualifications and old records | 6 passed | sibling REGISTRATION_TESTS_FINAL.log |
| Native host invariant/stream tests | both passed | NATIVE_HOST_TESTS.log |
| Host candidate, cutoff and corruption tests | passed; 398 cutoff cases, 12 velocity ULP rejections | NATIVE_HOST_TESTS.log |
| Actual six parent host initializations | passed, empty output directories | PREPARE.log; EXTENSION_TESTS.log |
| Read-only status/check | passed; state/metadata bytes unchanged | READ_ONLY_CHECKS.log |
| Protected historical data and bindings | passed | PRESERVATION.log |

Total: **236 Python tests passed**, plus the native host test groups. Earlier
pre-build logs are retained separately; their preparation-class skip preceded
creation of the real plans. The final 27-test extension run exercised that class.
These are deterministic validation tests, not statistical convergence evidence.
No existing historical review's tests or scientific conclusions were edited.

The source-preservation test checks byte identity of the complete physical tail
of `kg_assoc_stars.cu` (restart restoration through force/MD execution) and the
complete repaired initial-device-readback implementation against the starting
commit. The fixed reversible transition manifest authenticates exact native
front-end, lineage-validator and reservation-owner changes; all remaining
scientific source hashes must match. The full committed source map separately
binds administrative code. No changes occurred in `examples/KG/` or `src/`.

The immutable pre-change baseline has 3,022 bindings. Exactly 3,018 are unchanged;
the other four are the intentionally scoped source files, checked against exact
before/after committed bytes. This includes all twelve previous formal records,
their protected endpoints/payloads, both failed smoke campaigns, successful smoke,
manual 24M campaign evidence, scientific reviews, historical reservations/builds
and production-registry bindings. There are now exactly thirteen formal records,
with only the authorized Ea6 addition. No Ea8/Ea10 acceptance or registry mutation
was made. The Ea6 record's SHA256 is
`042b8a8dffa15ceba46cd4989bae4fb91cf9331dffeedf67d04c675adbe7ebd6`.

The exact Ea6 histories underwent separate full CPU numerical/event replays and
the registration mechanism's independent triplet replay before publication.
Each retains 160,000 historical GPU candidate comparisons and an authenticated
43,563-particle initial device readback. The six continuation parents are the
exact authenticated same-Ea 24M endpoints from that completed manual campaign;
the workflow replays the corresponding full parent segment again before any
user-launched trajectory. No smoke output is an extension parent.

## Reproduce without simulations

From the clean repository on the authenticated dataset host:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea8_ea10_extension_handoff_20261018/VERIFY.txt
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea6_formal_acceptance_20261018/TEST_REGISTRATION.txt
timeout 600 env PYTHONPATH=examples/KG_Assoc/campaign python3 -m unittest -v test_e2_extensions
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --check
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --status
```

VERIFY.txt checks the **pre-execution prepared handoff snapshot**, including empty
outputs. It is intentionally inapplicable after the user starts MD; the durable
state then evolves. PREPARATION_EVIDENCE.tar.gz retains the original 14 metadata
files: initial state, two triplet plans, six selected approvals, two immutable
MD-only reservations and build manifest/logs. PREPARED_METADATA.sha256 records
that snapshot, not a requirement that the live state stay unchanged forever.
INTEGRITY.sha256 seals this review and the formal-registration review's seal.
Use the runner's read-only status/check for live campaign monitoring.

Status does lightweight metadata/process authentication to avoid parsing live
output midway through a write. Complete output hashes and independent numerical
replay are required by --execute before any completion is skipped. Only
--execute starts GPU work, and that command is exclusively for the user.

The new administrative front-end has no assistant-run GPU result. Its device
readback, candidate oracle, chemistry and numerical endpoint checks remain
mandatory at actual user execution. No guarantee of future hardware or trajectory
success is inferred from CPU tests. Failures preserve evidence and stop rather
than generating another scientifically selected seed.
