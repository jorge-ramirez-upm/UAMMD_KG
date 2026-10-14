# Qualified RP060 acceptance validation

Starting local and remote `KremerGrest` HEAD and user-approved scientific assessment:
`bc8bda0c2e9616d2fc0c28b4b45b06fe9cebe0fc`. The working tree was clean before
authentication. The final containing commit is reported with the push result.

Before repository edits or registration, the assessment's immutable integrity,
739 preserved source/evidence files, execution receipts and smoke bindings were
verified. Fresh CPU authentication replayed all three continuous 0–6M histories;
plans, source/build/current executable bytes, parent identities, output hashes,
numerical/event/graph/conformation checks and all completion receipts matched the
approved scientific dossier exactly. Each history has 6,001 frames; accepted-event
counts are 211200/209838/211013, and final bond counts are 1770/1772/1765.

r002's parent is the accepted active E1 retry
`banks/e1_retries/F04_N010_RP060/r002/attempt001/state.e1.lammpsdat`, hash
`a0f0c654f729e81fb84d7ded27e3d57348d2596452e1a89390f002c7a11188cb`.
It matches the frozen inventory and active map. The original failed E1 preparation
is preserved and is not used. The exact three restart/chemistry-sidecar pairs
match every hash in the approved ENDPOINTS.md, not just their path names.
`AUTHENTICATED_SOURCE.json` retains the fresh matching validation and build scope.

**The unchanged pre-registration suite passed 126 CPU Python tests in 65.062
seconds, zero failures.** `BASELINE_CPU_TESTS.log` records the run. Historical
N40, Ee6 and RP040 registration tests include assertions that the live inventory
contains exactly nine records. They were run on that exact nine-record baseline,
before adding RP060; their source and immutable historical snapshots remain
unchanged. The post-registration suite below uses the new exact ten-record live
inventory test and all existing fixture-based acceptance/catalog/regression tests.
It does not weaken or monkeypatch the historical count assertions.

**The post-registration suite passed 120 CPU Python tests in 18.590 seconds,
zero failures.** `CPU_TESTS.log` records every result, including the six new exact
registration tests. Thus 246 test executions passed across the unchanged
nine-record baseline and the ten-record post-registration state. Both new Python
files compiled successfully. All ten acceptance payload sets passed the existing
acceptance validator, all 772 preexisting bindings remained unchanged, and the
read-only live catalog required the exact ten eligible records with all registry
and production exclusions intact. Whitespace and final dossier digests were
checked before commit.

Baseline command:

```bash
PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_rp040_ee8_formal_acceptance_20261014:examples/KG_Assoc/campaign:examples/KG_Assoc/analysis \
python3 -m unittest -v test_e2_acceptance test_e2_n40_acceptance \
  test_e2_ee6_acceptance test_catalog test_e2_g1 test_e2_recover test_joint_e2 \
  test_e2_continuous_review test_e2_continuous4m_review test_e2_continuous8m_review \
  test_e2_satellite_continuation test_e2_peripheral_network \
  test_e2_window_sensitivity test_registration
```

Post-registration command:

```bash
PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_rp060_ee8_formal_acceptance_20261015:examples/KG_Assoc/campaign:examples/KG_Assoc/analysis \
python3 -m unittest -v test_e2_acceptance test_catalog test_e2_g1 test_e2_recover \
  test_joint_e2 test_e2_continuous_review test_e2_continuous4m_review \
  test_e2_continuous8m_review test_e2_satellite_continuation \
  test_e2_peripheral_network test_e2_window_sensitivity test_rp060_registration
```

The new tests enforce exact endpoint/seed/step/physics/evidence/use bindings and
qualification retention; reject altered steps, prefixes, chemistry hashes, MD
seed pins, failed E1 parents and broadened use/system scope; check exclusive
creation rejects duplicate registration before replay; authenticate all nine
previous record hashes and 772 preexisting evidence bindings; and require exactly
ten formal records with no selection or production authorization. Existing tests
exercise immutable acceptance schema, lineage, numerical/event validation,
satellite/peripheral graph definitions and three-history statistical units.

The established `kg_assoc_e2_registry.accept()` API independently revalidates the
source histories before writing the new record exclusively. Its unchanged
`exclusive_validate()` checks the new record and all nine previous accepted
payload sets. `REGISTRATION.json` binds the new record hash, approved scientific
commit, exact endpoints and nine previous record digests. `RECORDS.json` is the
new ten-record snapshot; `CATALOG_CHECK.json` records the read-only catalog view.
`INTEGRITY.json` binds all new dossier files and the new acceptance record; the
containing commit binds that manifest itself.

Historical E1 executable bytes were not independently reauthenticated, as
explicitly stated in the qualification. Numerical validity and active exchange
do not demonstrate complete stationarity, structural decorrelation, absence of
initialization bias or complete slow-topology sampling. The approved scientific
assessment remains unchanged; registration preserves every requested limitation.

No native source/header/build recipe changed, so no executable rebuild is needed.
No GPU, further equilibration, physics change, old acceptance rewrite, registry
publication/selection/activation, production preparation, authorization or launch
occurred. Protected KG/src files, raw simulation outputs and prior scientific
evidence remain byte-identical. Python compilation is the only compilation check.
