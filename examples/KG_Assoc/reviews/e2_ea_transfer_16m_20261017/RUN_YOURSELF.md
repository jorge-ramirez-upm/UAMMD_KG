# Run on your Linux host

The assistant must not execute these long runs. AGENTS.md limits assistant-run
jobs to short tests of at most ten minutes. The user runs the commands below.

From the existing repository and authenticated dataset on **titan**:

```bash
cd /home/jramirez/UAMMD_KG
python3 examples/KG_Assoc/campaign/run_ea_preparation.py --check
python3 examples/KG_Assoc/campaign/run_ea_preparation.py --execute
```

`--check` authenticates the committed source, preserved native build and exact
qualified parents. It allocates no seeds and runs no MD. `--execute` explicitly
records the user's terminal authorization and runs only Ea6/Ea8/Ea10 r001–r003,
16,000,000 additional steps per successful history, from absolute 8M to 24M.
The scientific diagnostic partition remains 500k (32 windows per history), with
the existing finer numerical/chemistry/conformation records retained.

**After Ctrl+C, run the same `--execute` command again.** Completed validated
histories are checked and skipped. A finished trajectory whose completion receipt
was interrupted is validated without repeating MD. An interrupted partial history
restarts automatically from its authenticated 8M parent using fresh streams and a
new unique attempt directory. Its old directory and consumed reservation are
preserved. Other pending histories run normally. No folder deletion, overwrite,
manual seed editing or manual approval editing is needed.

These are full 16M segments, not bitwise checkpoint continuations. The executable
has no intermediate GJ checkpoint containing the needed integrator/noise state.
Restarting a partial therefore repeats that history from its original parent;
partial execution remains separately recorded rather than counted as completed
preparation. Reissuing `--execute` explicitly requests that restart. Numerical,
chemistry, candidate, build or provenance failures stop the campaign and are never
silently reseeded to obtain a pass.

To keep the run alive after closing the terminal, use the standard Linux tools
already on the host, for example:

```bash
cd /home/jramirez/UAMMD_KG
nohup python3 -u examples/KG_Assoc/campaign/run_ea_preparation.py --execute \
  >> examples/KG_Assoc/kg_assoc_100m/ea16m_console.log 2>&1 &
EA_RUN_PID=$!
```

To stop that background runner from the same shell, use `kill -TERM "$EA_RUN_PID"`.
The runner catches SIGINT/SIGTERM, stops its native child and saves its interrupted
status. Use either foreground execution or `nohup`, not both at once. The shared OS lock
prevents concurrent workflow launches and releases automatically after a process
ends. Keep the source checkout fixed during execution; the native executable and
plan are authenticated. No packages need to be installed for this runner.

Status and logs:

```bash
python3 examples/KG_Assoc/campaign/run_ea_preparation.py --status
tail -f examples/KG_Assoc/kg_assoc_100m/ea16m_console.log
```

The console prints the exact log directory before each history. Durable manual
state is `examples/KG_Assoc/kg_assoc_100m/aggregate/e2/manual_ea16m_v1/state.json`.
Each attempt retains its plan, per-replica approval, host initialization receipts,
actual initial device readback, candidate checks, events, network/conformation and
numerical records, final restart/sidecar, logs and authenticated completion receipt.
Each approved launch selects one replica explicitly; occupied unselected replica
directories do not cause output-reuse errors and are untouched. The underlying
planner retains complete triplet entries, while approvals bind only the selected
history and its exact 16M cap. Unused reservation rows remain reserved.

The previously cancelled agent-run campaign is separate and is never resumed or
overwritten. The first manual run starts fresh from the accepted reference pairs.
All previously used/reserved streams are excluded, including the cancelled
campaign's unexecuted entries. Repeating the command after all nine completions
only validates/skips them; it does not launch another cohort.

The existing latest diagnostic native build is reused after authentication.
Administrative runner/selector changes require no native rebuild. No physical
source, reaction, search, loader, force or integrator changed in this handoff.
Successful endpoint validation is followed by scientific review; the runner does
not register acceptance, activate a registry, extend trajectories or run production.
