# Registration validation

**126 CPU Python tests passed in 53.197 seconds; zero failures.**
[Full output](CPU_TESTS.log) records every test result. Existing sidecar-reader
ResourceWarnings are retained in that output and caused no failures.

```bash
PYTHONPATH=examples/KG_Assoc/reviews/e2_rp040_ee8_formal_acceptance_20261014:examples/KG_Assoc/campaign:examples/KG_Assoc/analysis \
python3.11 -m unittest -v \
  test_e2_acceptance test_e2_n40_acceptance test_e2_ee6_acceptance \
  test_catalog test_e2_g1 test_e2_recover test_joint_e2 \
  test_e2_continuous_review test_e2_continuous4m_review \
  test_e2_continuous8m_review test_e2_satellite_continuation \
  test_e2_peripheral_network test_e2_window_sensitivity test_registration
```

The four new registration tests verify endpoint/seed/physics/review/permission
bindings and qualification retention; immutable exclusive creation and prior evidence;
rejection of endpoint/seed/hash/system/use substitutions; and the exact nine-record
inventory without any registry or production authorization.

Both historical current-catalog tests were first reproduced unchanged: each failed
only at `9 != 8` (two tests in 25.146 seconds). The repair preserves their immutable
seven/eight-record snapshots and all historical authentication assertions. Their
current views now require the previous eight exact records plus only the approved
RP040 acceptance, including its path, digest, identity and endpoint validation.
No unrestricted dynamic-count check replaces the assertions. Both pass in the final
126-test run.

Python compilation passed for the new registration script/test, both maintained
historical tests, and unchanged acceptance/provenance/catalog modules. Native
compilation was unnecessary: no C++/CUDA/header, build recipe or executable changed.
No GPU calculation, simulation, recovery or extension was executed.

Fresh CPU authentication of all six 0–6M/6–8M segments matched every entry and
numerical/event/conformation validation result in the immutable scientific review.
The API independently revalidated the accepted extension. All nine committed
acceptance payload sets passed the unchanged `exclusive_validate()` tool.
[Authentication output](AUTHENTICATION.log) and [REGISTRATION.json](REGISTRATION.json)
retain the checks and exact plan, lineage, build, seed and output bindings.

854 preexisting evidence bindings were checked. 852 remain byte-identical; only
the two explicitly maintained historical test files differ, with their exact before
and after hashes recorded in INTEGRITY.json. All eight previous acceptance records,
original attempts, scientific reviews, frozen campaign and protected code remain
unchanged. The only new dataset file is the authorized ninth acceptance record.

The existing offline catalog generator produced a new ignored immutable snapshot
with nine formal records, zero selections, zero registry views, no selected registry,
and absent production authorization for every campaign system. Its payload-deferred
metadata view is supplemented by the independent endpoint authentication here.
No `banks/e2_registry` directory exists. Whitespace, exact change scope and new
artifact digests were checked before commit; the final containing commit is reported
in the task response.
