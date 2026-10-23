# CPU-only verification

Run from `/home/jramirez/UAMMD_KG` on the evidence host with a clean checkout:

```bash
timeout 600 python examples/KG_Assoc/reviews/production_compatibility_decision_20261023/VERIFY.txt
timeout 600 python examples/KG_Assoc/reviews/production_compatibility_decision_20261023/TEST_DECISION.txt -v
timeout 600 python examples/KG_Assoc/reviews/production_launch_validation_20261023/TEST_ADAPTER.txt -v
```

The verifier checks the committed publication and exact original evidence paths;
missing files fail closed. It authenticates the fifteen fresh strict replay results
from the closure against the unchanged receipts and output hashes, without repeating
MD, native probes or rewriting receipts. No additional stress estimator tests are
necessary because no native or analysis implementation changes.

`PUBLISH.txt` documents the one-time exclusive-create operation used at starting
HEAD `cb025ec6d734bc077dc485ae229cd7b77d6bc2e3`. It refuses an existing decision and
cannot be rerun at a different HEAD. Do not rerun it for verification. The Git-tracked
record copy is the byte-identical archival representation; the published index pins
both it and the original bank record.

This dossier provides no execution command. Production registry activation and exact
production execution approvals remain absent. Historical compatibility-driver output
will continue to show its original hold; use this separate verifier to read the new
approved administrative outcome. Do not edit historical flags or receipt hashes.
