# User-run execution on titan

Execution is now authorized **only** for the six original preparations in
`manual_ea_extensions_48m_88m_v1`: Ea8 r001--r003 40M--48M (8M each) and Ea10
r001--r003 56M--88M (32M each). Completed-history budget: 120M additional steps.
The assistant has not launched any GPU or integrated any MD step.

From the existing clean checkout on `titan`, update if necessary:

```bash
cd /home/jramirez/UAMMD_KG
git switch KremerGrest
git pull --ff-only origin KremerGrest
git status --short --branch
```

Run the authoritative read-only execution preflight and status:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_next_extensions_execution_authorization_20261021/PREFLIGHT_DRIVER.txt --check
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_next_extensions_execution_authorization_20261021/PREFLIGHT_DRIVER.txt --status
```

Both must pass. These commands authenticate the six separate execution approvals,
source records, exact parents, build, immutable preparation and protection inventories;
they never launch MD or allocate attempts. Initially all six statuses are `prepared`.
The old runner's `--check`/`--status` still prints “preparation only” because it checks
the immutable original GPU-disabled preparation records. Use the new read-only
driver above to verify the separately published GPU execution authority. Likewise,
the historical CPU-preparation verifier asserts that execution approvals do not yet
exist; preserve that historical result and use the new audit after authorization.

Then the user may launch the controlled campaign in the foreground:

```bash
python3 examples/KG_Assoc/campaign/run_ea_next_extensions.py --execute
```

This is the eventual user-run command. It was tested through temporary mocked
native processes and real read-only authentication, never invoked against the
actual campaign by the assistant. Keep the checkout and source/build files unchanged
throughout execution. Native selection is the authenticated candidate-validation
executable; do not substitute a raw executable command or disable validation.
No recompilation or recreation of prepared attempts is required.

## Interruption and failures

Use Ctrl-C once in the foreground, allow the runner/native process to stop, and then
run the read-only status command above. Do not start another runner while a history
is running. Keep all output directories, reservations and receipts.

Reissuing the controlled `--execute` command skips independently replayed validated
completions. A genuine interrupted partial cannot continue bitwise: the runner
preserves it, records lower/upper bounds on interruption overhead separately,
prepares a fresh immutable replacement from the exact parent with fresh MD streams,
and **stops for a separate plan-bound execution approval**. These six approvals
never transfer to that replacement. The new preflight rejects a runtime replacement
until a subsequent authorization milestone supplies its updated audited bindings.

Native PASS followed by an administrative exception is a validation hold, not a
partial/retry. The runner preserves `incomplete.json` and native outputs and does
not rerun it. Request CPU-only independent recovery. Candidate, device-readback,
numerical, provenance or chemistry failures likewise stop execution; do not delete
or bypass evidence. Missing genuine device readback can never be replaced by a
host-only preflight or synthetic file.

Every completed history still requires exact initial GPU readback, candidate-oracle
agreement, accepted-event/counter replay, finite numerical/geometry observations,
exact endpoint restart/sidecar validation and authenticated completion hashes.
Fresh GJ streams mean each segment is not bitwise MD continuation. Scientific
acceptance remains held for both systems; successful completion authorizes neither
another extension nor production.
