# Read-only inspection now; GPU execution is not yet authorized

On `titan`, from the clean committed checkout:

```bash
cd /home/jramirez/UAMMD_KG
git status --short --branch
timeout 600 python3 examples/KG_Assoc/campaign/run_ea_next_extensions.py --check
timeout 600 python3 examples/KG_Assoc/campaign/run_ea_next_extensions.py --status
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_next_extensions_cpu_20261021/VERIFY_DRIVER.txt
```

These commands inspect `manual_ea_extensions_48m_88m_v1`; they never use or edit the completed
`manual_ea_extensions_readback_v2` state. Preparation already exists; do not delete or overwrite
its folders. `--prepare` is CPU-only and idempotently verifies an existing immutable preparation.

**Do not execute the following command now. It requires separate user approval and publication of
new immutable execution approvals and execution-source authorizations for these exact plans:**

```bash
# UNAUTHORIZED until the separate GPU execution-authorization milestone is complete:
python3 examples/KG_Assoc/campaign/run_ea_next_extensions.py --execute
```

The runner currently rejects this command with `GPU execution is NOT authorized; preparation only`.
Do not edit preparation approval hashes, set a false field to true, reuse historical approvals,
or bypass the planner by invoking a raw native command. A subsequent authorization milestone
must publish new plan-bound execution and source records, preserving all preparation records.

Once separately authorized, the same runner can execute only Ea8 r001--r003 40M--48M and Ea10
r001--r003 56M--88M. It requires exact actual device readback before MD, every candidate-oracle
comparison, strict chemistry/event/numerical replay and authenticated endpoint completion.

For interruption, send Ctrl-C to the foreground runner and inspect `--status` after the native
process stops. Keep every directory and reservation. Completed validated histories are replayed
and skipped. A genuine partial history receives a fresh immutable CPU-prepared attempt and a
separate overhead entry; it does not resume bitwise and needs its own new execution approval.
A native-PASS history with an administrative validation exception remains held for CPU recovery
and must never be rerun automatically. All numerical/candidate/provenance failures stop the campaign.

No new computation beyond the six completed-trajectory caps or automatic scientific acceptance
is authorized by these instructions.
