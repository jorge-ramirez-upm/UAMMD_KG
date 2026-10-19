# Run the authorized extensions on titan

Before launch, update to the authorization commit and authenticate the fixed
cohort:

```bash
cd /home/jramirez/UAMMD_KG
git switch KremerGrest
git pull --ff-only origin KremerGrest
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --check
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --status
```

Launch all and only the six authorized histories on `titan`:

```bash
cd /home/jramirez/UAMMD_KG
python3 -u examples/KG_Assoc/campaign/run_ea_extensions.py --execute
```

Use `Ctrl-C` once for a graceful stop. Do not alter plans, approvals, state,
seeds or output directories. Reissue the same `--execute` command after a
clean interruption. Independently validated completed histories are skipped.
A native PASS is replayed and completed without rerunning MD only when every
required output, including genuine initial-device-readback evidence, validates.

A genuine partial attempt is preserved and retired. The runner will make a new
preparation attempt with fresh MD streams, then stop because that new immutable
attempt has no execution approval. Obtain a new scoped approval for that exact
replacement; do not copy or edit the current approval files. Restart overhead
is recorded separately and does not change the 144M completed-history cap.

Read status without writing state or launching MD:

```bash
cd /home/jramirez/UAMMD_KG
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --status
```

Any readback, candidate-oracle, numerical, provenance or replay failure holds
the campaign immediately. Do not retry a failed trajectory with a different
seed. These executions provide numerical endpoints only; Ea8/Ea10 still need
a later scientific review and separate formal-acceptance authorization.
