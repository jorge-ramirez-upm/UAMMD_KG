# Registration validation and reproduction

Starting local and remote `KremerGrest` HEAD were both
`cb78880925b60c0777d3cba43fbb6222a62175e2`; the working tree was clean.
The complete approved 20M dossier matches its integrity manifest and committed
bytes. The final SHA is the containing registration commit, reported after push.

Before creating any repository artifact, fresh CPU-only authentication replayed
all six histories across 0–16M and 16–20M. Both exact plans, E1 lineage and
available parent evidence, all three 16M parent pairs, all three 20M endpoint
pairs, build/source/log evidence, smoke/execution witnesses, outputs, receipts,
numerical checks, accepted events, stable identities, reciprocal partners,
multigraph accounting and final conformations authenticate. Full fresh plans and
validation results equal the approved provenance and all six completion receipts.
[AUTHENTICATION.log](AUTHENTICATION.log) and
[AUTHENTICATED_SOURCE.json](AUTHENTICATED_SOURCE.json) retain the results.

All 289 common native/build-recipe source hashes match both builds. Current
continuation executable bytes authenticate. Original 0–16M binaries were replaced
before this task by the continuation rebuild; source/build/log evidence and
recorded digests authenticate, but historical executable bytes are not independently
reauthenticated. Historical E1 executable bytes remain similarly limited. These
limitations are explicit in the acceptance. No simulation executable ran here.

[BOUNDARY.json](BOUNDARY.json) binds exact 16M parent hashes and partner-set
SHA256, unchanged chemical seeds 420801/420802/420803, absolute steps, cumulative
creations/breaks and old/new requested/effective MD seeds. Continuation initial
samples equal the original final chemical samples. Positions/velocities are
restored, `initVelocities=false`, `internal_start_step=0`; new requested seeds
520130/520131/520132 and effective seeds 3381585552/3373217424/3398338192 mean
this is **not bitwise MD continuation**. No stitched IAT, SEM or lifetime is
computed. The approved segment-local scientific estimates are preserved.

The unchanged `kg_assoc_e2_registry.accept` API performed another fresh
continuation replay, then exclusively created the record. `exclusive_validate`
authenticated all twelve records. The eleven earlier records and all **1,294
preserved file bindings** match their original hashes. This includes the exact
1,258 inherited bindings and the complete 36-file approved 20M dossier, protected
physics/KG/src evidence, simulation outputs, plans/receipts, build/executable
bindings and prior assessments. The earlier 16M hold is unchanged and those
endpoints are not accepted.

Deterministic CPU checks (no stochastic convergence claim):

| Check | Result |
|---|---|
| Baseline acceptance/campaign/analysis suite | 128 tests passed, 15.738 s |
| Approved joint-20M scientific suite, before registration | 15 tests passed, 12.360 s |
| Post-registration shared suite and seven new registration tests | 135 tests passed, 26.920 s |
| Python compilation of three new helpers/tests | Passed |
| Six-segment fresh authentication and completion equality | Passed |
| API continuation replay and twelve acceptance validators | Passed |
| Eleven previous acceptance hashes and 1,294 preserved bindings | Passed |

Logs: [baseline](BASELINE_CPU_TESTS.log), [scientific](SCIENTIFIC_CPU_TESTS.log),
[post-registration](CPU_TESTS.log), [registration](REGISTRATION.log).
New tests verify exact 20M pairs, seeds, qualifications and scope; reject wrong
parents, MD/chemical seeds, 16M substitutions, corrupt hashes and unauthorized
system/use; reject duplicate registration before replay; verify boundary partner
and counter continuity; and check the twelve-system inventory without selection
or production authorization. Shared fixture tests use temporary roots.
Historical live-inventory tests retain their original counts and are not edited.
The frozen 20M scientific tests ran before registration because their inventory
assertion intentionally describes the then-existing eleven-record state.
Existing reader ResourceWarnings are suppressed without changing their source.

From the repository root, rerun the post-registration suite:

```bash
PYTHONPATH=examples/KG_Assoc/reviews/e2_ee12_formal_acceptance_20261016:examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest -v \
  test_e2_acceptance test_catalog test_e2_g1 test_e2_recover test_joint_e2 \
  test_e2_continuous_review test_e2_continuous4m_review test_e2_continuous8m_review \
  test_e2_satellite_continuation test_e2_peripheral_network test_e2_window_sensitivity \
  test_reproduce test_joint_rp040_8m test_ee12_registration
```

Reauthenticate all six segments read-only into a new output path (several CPU
minutes; never overwrite the frozen authentication):

```bash
python3 examples/KG_Assoc/reviews/e2_ee12_formal_acceptance_20261016/authenticate.py \
  --output /tmp/ee12_fresh_source_unique.json
```

`register.py` requires the approved assessment HEAD and a nonexistent acceptance
filename. It is a historical registration receipt/helper, not a command to rerun
after acceptance. The public mechanism rejects an existing record before replay.

Verify new dossier/record integrity and preserved evidence:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
root = Path.cwd()
dossier = root / 'examples/KG_Assoc/reviews/e2_ee12_formal_acceptance_20261016'
for name, digest in json.loads((dossier / 'INTEGRITY.json').read_text())['sha256'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
for name, digest in json.loads((dossier / 'PRESERVED_EVIDENCE.json').read_text()).items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
print('PASS new integrity and 1294 preserved bindings')
PY
```

The manifest uses repository-relative SHA256 bindings for every new dossier file
and the new acceptance, excluding itself; the containing commit binds the manifest.
Preserved evidence follows the inherited absolute-path convention. Before commit,
staged scope and bytes must match this manifest, with only additions in the new
dossier and the exact new acceptance path; whitespace checks must pass.

The read-only catalog reports 23 systems: twelve formal acceptances (payload
loading deferred in the catalog, independently validated above), eight
`E1_acceptance_unknown`, three `review_required`. All 23 have production
authorization absent. No selected registry, registry view or selection exists.
No registry was published or activated. No production preparation, authorization,
100M campaign action, trajectory launch, GPU calculation or further equilibration
occurred. Only this new dossier and acceptance JSON are added.

No unresolved registration discrepancy remains. Scientific qualifications are
preserved in full: complete stationarity, structural decorrelation and absence
of initialization bias remain unproved. Initialization suitability does not
certify equilibrium of every structural observable. Protected directories,
frozen physics, simulation outputs, earlier reviews and eleven old acceptances
are unchanged.
