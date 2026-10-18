# Run the six extensions yourself on titan

**Codex must not execute these long GPU jobs.** This handoff implements and
CPU-tests them only. Run on the existing authenticated dataset and build on
`titan`; neither raw simulation data nor native executables are downloaded by
`git pull`. They are already prepared in this host's managed dataset.

## Check, inspect, execute

From your terminal:

```bash
cd /home/jramirez/UAMMD_KG
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --check
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --status
python3 -u examples/KG_Assoc/campaign/run_ea_extensions.py --execute
```

Only `--execute` launches GPU work. The six preparations already exist; no manual
folder, seed, approval or JSON editing is needed. If preparation itself was
interrupted, `--execute` finishes the CPU preparation first. The separate
`--prepare` command creates/authenticates preparations without running MD.
`--check` and `--status` are read-only and allocate no streams.

The runner selects exactly Ea8 r001–r003, +16M each from 24M to 40M, and Ea10
r001–r003, +32M each from 24M to 56M. It never returns to an 8M parent, uses a smoke
as a parent, launches Ea6, or creates another cohort after all six completions.
Completed histories are independently replayed and skipped on repeated execution.
The completion budget is 144M steps. You authorized separately recorded restart
overhead; interrupted attempts are not merged into completed trajectories.

## Interrupt and restart safely

For foreground execution, press **Ctrl+C once** and allow the runner to stop its
native child and save status. Then rerun the **same `--execute` command**.
Finished validated histories are skipped. A trajectory whose MD finished but
whose receipt was interrupted is validated and its receipt recovered without
repeating MD. A genuine partial restarts from its exact authenticated 24M parent
with fresh requested/effective MD streams in a new immutable attempt. The old
attempt and all reservations stay untouched. Do not delete or rename directories.

The executable has no suitable intermediate integrator/noise checkpoint. A new
attempt is not a bitwise checkpoint continuation. Chemistry retains its seed and
absolute-step keys; partial retry streams must be kept separate. Partial overhead
is recorded with conservative bounds because a hard interruption can lose the
last buffered diagnostics. A still-active old native process blocks a duplicate
launch until that process exits. Numerical, oracle, chemistry and provenance
failures stop the campaign and are never silently retried with another seed.

Keep the committed source, build and evidence fixed during execution. Do not run
multiple foreground/background launchers. The OS workflow lock prevents duplicate
launches and releases automatically when a runner exits. SIGINT/SIGTERM are the
supported graceful stops; Linux parent-death supervision also stops an orphaned
native child. Prefer graceful termination so all diagnostic buffers are flushed.

## Optional detached terminal run

The following are commands for **you**, not Codex. Use these instead of the
foreground `--execute` command:

```bash
cd /home/jramirez/UAMMD_KG
EA_DATASET="$PWD/examples/KG_Assoc/kg_assoc_100m"
nohup python3 -u examples/KG_Assoc/campaign/run_ea_extensions.py --execute \
    >> "$EA_DATASET/ea_extensions_console.log" 2>&1 &
EA_EXTENSION_PID=$!
printf 'Extension runner PID: %s\n' "$EA_EXTENSION_PID"
```

To stop that background runner from the same shell:

```bash
kill -TERM "$EA_EXTENSION_PID"
wait "$EA_EXTENSION_PID"
```

Exit status 130 indicates the requested interruption; it does not erase any output.
To restart, repeat the nohup block or use the foreground command, after the old
runner/child has exited. Use the same workflow state; never create a second cohort.

From another terminal, status and console monitoring are read-only:

```bash
cd /home/jramirez/UAMMD_KG
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --status
tail -f examples/KG_Assoc/kg_assoc_100m/ea_extensions_console.log
```

The console prints each exact per-history log directory. The durable state is
`examples/KG_Assoc/kg_assoc_100m/aggregate/e2/manual_ea_extensions_v1/state.json`.
Each selected history retains its immutable plan, replica-bound approval,
MD reservation, CPU initialization evidence, actual GPU initial readback,
candidate comparisons, events, network/conformation/numerical records, final
restart/sidecar, completion receipt and full process logs. The runner reports
partial-work bounds separately and never asserts an exact lost-buffer step count.

No package installation is needed. Read-only status reports authenticated plan/
approval metadata and live process identity; `--execute` performs independent full
numerical replay before skipping a completion. It also replays the corresponding
24M parent's full 16M segment before each new GPU start. No tolerance or oracle
comparison is weakened. The initial device check runs before any MD integration.

All six final endpoints remain on scientific hold pending the separate review
described in IMPLEMENTATION.md. Numerical completion is not formal acceptance.
No further extension, registry activation or 100M production is part of this runner.
