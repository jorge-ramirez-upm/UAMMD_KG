# CPU validation and reproduction

Starting clean local/remote `KremerGrest` HEAD:
`bd77a09daa28791972810fc81ffc82b8a9024460`.
All changes belong exclusively to this new feasibility-review directory.
The final SHA is the containing review commit, reported after push.

| Check | Result |
|---|---|
| Existing acceptance/campaign/catalog/analysis/runner CPU suite | 152 tests passed, 27.298 s |
| New deterministic feasibility suite | 11 tests passed, 40.333 s |
| Existing S2 CPU analyzer self-test | PASS |
| Frozen native host probabilities and sequential reaction loop | 36 probability cases, 340 ordered sweeps passed within new suite |
| Enumerated competing-edge conditional Gibbs invariance | All six orders, four barriers passed |
| Fresh existing reference continuation replay | All three corrected 6–8M histories passed numerical/event/network/endpoint checks |
| Repeated analysis into a separate new directory | Three JSON artifacts byte-identical |
| Existing immutable acceptance validation | All twelve records passed, hashes unchanged |
| Preserved evidence / inspected source checks | 1,312 inherited bindings and 47 source/evidence bindings passed |
| Python helper compilation | Passed |

Logs: [CPU_TESTS.log](CPU_TESTS.log), [REGRESSION_TESTS.log](REGRESSION_TESTS.log),
[CPU_REPLAY.log](CPU_REPLAY.log), [CPU_REPRODUCTION.log](CPU_REPRODUCTION.log).
The reproducibility hashes are in [REPRODUCIBILITY.json](REPRODUCIBILITY.json).
Stored regression logs strip trailing spaces only. Existing ResourceWarnings are
suppressed without editing their source. Legacy
live-inventory tests expecting fewer acceptances are left untouched; the current
twelve-record registration suite is used. Existing tests use temporary fixtures;
no real attempt, approval, selection or registry is created. Host-only initial-state
validation inside existing tests returns before GPU initialization. No smoke or
simulation execution is performed.

The native CPU harness compiles `kinetics_host_check.cpp` with g++ C++17 into a
temporary directory and includes the unchanged frozen kinetics/Ea-switch headers.
C++17 supports the header's hexadecimal floating-point literal. A small host-only
state adapter bypasses the CUDA state header and implements reciprocal partners;
it does not replace or modify the reaction code. GPU state synchronization,
forces, candidate search and MD are outside this native harness's tested scope.
The deterministic expected sweeps use literal 64-bit hash/ordering and actual
native energy values. The separate matching-matrix enumeration models ideal
uniform accept draws and proves the stated finite-state example, not PRNG or
full coupled-MD invariance. Tests also exercise restart/Ea/seed refusal, exact
system/use scope and current-plan collision checks on illustrative seed triplets.
Those seeds are not reserved; future allocation must recheck then-current state.

The reference replay calls CPU readers/validators only, with executable oracle
invocation disabled. It authenticates original historical parents as provenance,
never as accepted new starts. The replay does not rerun original E1/E2 or
reauthenticate unavailable historical executable bytes. Available exact payloads,
status/receipt bindings and current source evidence are authenticated; historical
limitations remain explicit. No new stochastic convergence conclusion is derived
from these tests.

From repository root, reproduce into a NEW output directory:

```bash
python3 examples/KG_Assoc/reviews/e2_ea_transfer_feasibility_20261016/reproduce.py \
  --output /tmp/ea_transfer_unique_output

PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_ea_transfer_feasibility_20261016:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_feasibility

python3 examples/KG_Assoc/analysis/analyze_s2.py --self-test
```

The feasibility module is run separately from historical modules also named
`reproduce` to avoid Python import-name collisions. The shared suite command is:

```bash
PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_ee12_formal_acceptance_20261016:examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_e2_acceptance test_catalog test_e2_g1 test_e2_recover \
  test_joint_e2 test_e2_continuous_review test_e2_continuous4m_review \
  test_e2_continuous8m_review test_e2_satellite_continuation test_e2_peripheral_network \
  test_e2_window_sensitivity test_reproduce test_joint_rp040_8m \
  test_ee12_registration test_run_e2
```

New artifacts and all inherited bindings are verified as follows:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
root = Path.cwd()
d = root / 'examples/KG_Assoc/reviews/e2_ea_transfer_feasibility_20261016'
for name, h in json.loads((d / 'INTEGRITY.json').read_text())['sha256'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == h, name
for manifest in ('PRESERVED_SHA256.json', 'SOURCE_SHA256.json'):
    for name, h in json.loads((d / manifest).read_text()).items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == h, name
print('PASS review integrity and inherited/source bindings')
PY
```

`INTEGRITY.json` binds every new artifact except itself using repository-relative
paths; the containing commit binds the manifest. Inherited/source maps retain
the established absolute-path convention. Staging is restricted to additions in
this directory and bytes matching the manifest; no generated `__pycache__` or
compiled executable is included. No physics, protected output, older assessment,
acceptance record or existing test is edited. No GPU computation, transfer
implementation, acceptance expansion, registry action, production preparation,
authorization or launch occurred.

Unresolved scientific issue: conditional chemical invariance does not certify
the full finite-step MD sampler or eliminate reference initialization bias.
Unresolved implementation limitation: fresh chemical reseeding and ordinary
cross-Ea derived E2 preparation need explicit supported modes. These are the
review's findings, not failed authentication or numerical regression checks.
