# Registration validation

Starting local and remote `KremerGrest` HEAD were both
`68d80f5b38e328e4522e012acc74d54022f510ab`; the working tree was clean.
The approved 12M dossier is complete and matches its integrity manifest and
committed bytes. The final SHA is the containing registration commit.

Before creating any repository artifact, fresh CPU-only validation authenticated
all six simulation segments, the two exact plan hashes, E1 identities, all three
8M parent restart/sidecar pairs, all three 12M endpoint pairs, output hashes,
completion receipts, source/build records, smoke and execution witnesses.
All six validation results and complete plans match the approved provenance
exactly. Numerical checks, accepted-event replay, stable permanent identities,
reciprocal chemical partners, graph accounting and endpoint conformation pass.
[AUTHENTICATION.log](AUTHENTICATION.log) records replay results;
[AUTHENTICATED_SOURCE.json](AUTHENTICATED_SOURCE.json) contains full bindings.

All 289 common native/build-recipe hashes authenticate against the two builds.
Current extension executable bytes authenticate. Original 0–8M binaries were
replaced before this task; their recorded digests, source/build logs and frozen
review authenticate, but their historical bytes cannot be reauthenticated.
Historical E1 executable bytes remain similarly limited. No binary was launched.
These qualifications are carried into the acceptance without weakening them.

[BOUNDARY.json](BOUNDARY.json) binds the 8M parent pairs, partner-set digests,
chemical seeds, preserved counters and fresh requested/effective MD seeds.
The initial continuation samples equal the final original samples for absolute
step and chemical populations/counters. Parent-sidecar replay starts from the
same exact partners; cumulative counters are not reset. Source and execution
logs establish restored positions/velocities, `initVelocities=false` and a fresh
GJ stream at `internal_start_step=0`: this is not bitwise MD continuation.
No stitched IAT, SEM or bond lifetime is computed.

The unchanged `kg_assoc_e2_registry.accept` API performed an additional fresh
continuation replay before exclusively creating the new record. All eleven
acceptances then passed `exclusive_validate`. The ten old records retain their
exact hashes. All **1,098 preserved file bindings** pass, covering previous
assessments and their integrity manifests, both attempts and checkpoint evidence,
protected physics/KG/src files, existing acceptance records, reference payloads
and relevant build/executable evidence. The earlier 8M hold remains unchanged;
its endpoints are not accepted. The new record accepts only the exact 12M pairs,
only the approved system, and only `production_initial_state`.

Deterministic CPU results, with zero failures/errors:

| Check | Result |
|---|---|
| Pre-registration acceptance/campaign/analysis suite with the historical ten-record registration tests | 120 tests passed in 20.123 s |
| Approved joint-12M scientific regression suite | 9 tests passed in 1.136 s |
| Post-registration acceptance/campaign/analysis suite with the new eleven-record registration tests | 121 tests passed in 24.389 s |
| Compilation of all three new Python scripts | Passed |
| Preserved evidence and all prior acceptance hashes | Passed |
| New dossier/acceptance integrity and staged scope checks | Passed |

Logs: [baseline](BASELINE_CPU_TESTS.log), [scientific](SCIENTIFIC_CPU_TESTS.log),
[post-registration](CPU_TESTS.log), [registration](REGISTRATION.log).
These are integrity/deterministic regression tests, not new stochastic convergence
evidence. Historical registration tests retain their original inventory counts;
the ten-record live test ran before registration, and the new eleven-record test
ran after it. No frozen test was edited to change its expected inventory.

The new tests exercise exact endpoint/seeds/scope and qualification bindings,
parent and MD/chemical seed substitutions, explicit rejection of 8M substitution,
endpoint hash corruption, duplicate registration rejection before replay,
chemical boundary continuity and recorded partner/counter proof, prior evidence
preservation, the exact eleven-system inventory, and absence of registry selection
or production authorization. Fixture-based legacy tests run inside temporary
roots. Existing reader ResourceWarnings are suppressed; their source is unchanged.

From the repository root, rerun the current suite with:

```bash
PYTHONPATH=examples/KG_Assoc/reviews/e2_ee10_formal_acceptance_20261015:examples/KG_Assoc/campaign:examples/KG_Assoc/analysis \
PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest -v \
  test_e2_acceptance test_catalog test_e2_g1 test_e2_recover test_joint_e2 \
  test_e2_continuous_review test_e2_continuous4m_review test_e2_continuous8m_review \
  test_e2_satellite_continuation test_e2_peripheral_network \
  test_e2_window_sensitivity test_ee10_registration

PYTHONPATH=examples/KG_Assoc/reviews/e2_ee10_12m_20261015:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest -v test_ee10_12m
```

For the pre-registration suite, the same eleven shared modules ran with
`test_rp060_registration` instead of `test_ee10_registration`, using the historical
RP060 registration directory in PYTHONPATH. That live inventory test intentionally
expects the ten-record state that existed before this registration.

`INTEGRITY.json` uses repository-relative SHA256 bindings for the new acceptance
and every new dossier artifact except itself. The containing commit binds that
manifest. `PRESERVED_EVIDENCE.json` uses the inherited absolute-path convention
for preexisting evidence. Verification from the repository root:

```bash
python3 - <<'PYTHON'
import hashlib, json
from pathlib import Path
root = Path.cwd()
dossier = root / 'examples/KG_Assoc/reviews/e2_ee10_formal_acceptance_20261015'
for name, digest in json.loads((dossier / 'INTEGRITY.json').read_text())['sha256'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
for name, digest in json.loads((dossier / 'PRESERVED_EVIDENCE.json').read_text()).items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
print('PASS new integrity and 1098 preserved bindings')
PYTHON
```

The catalog contains 23 campaign systems: eleven formal acceptances, eight
`E1_acceptance_unknown`, three `review_required`, and one `absent` scientific
status. Catalog payload loading is deferred; the independent exclusive validators
above authenticate accepted payloads. Production authorization is absent for all
23. No registry view, registry selection, activation or publication exists.

No unresolved registration discrepancy remains. Scientific qualifications remain
unchanged: incomplete slow sampling/decorrelation, r002 L1, r003 redistribution,
replica offsets, common conformational contraction and possible initialization
bias, plus historical executable limits. Complete stationarity, structural
decorrelation and absence of initialization bias have not been demonstrated.

Only this new dossier and its new acceptance JSON are added. Protected directories,
frozen physics, simulation outputs, previous assessments and the ten old acceptance
records are unchanged. No GPU calculation, further equilibration, production
registry action, 100M preparation, authorization or production launch occurred.
