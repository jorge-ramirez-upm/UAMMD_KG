# User-run handoff: GPU execution pending separate approval

The repaired six-history preparations already exist on titan. No GPU execution
is authorized by this CPU milestone. The old failed manual_ea_extensions_v1
campaign is preserved in full; do not delete, rename, resume or edit it.

Run these safe, read-only commands now:

```bash
cd /home/jramirez/UAMMD_KG
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --check
python3 examples/KG_Assoc/campaign/run_ea_extensions.py --status
```

The new durable state is:
`examples/KG_Assoc/kg_assoc_100m/aggregate/e2/manual_ea_extensions_readback_v2/state.json`.
HISTORIES.csv gives all six exact attempt paths, parents, requested/effective MD
streams, plans, approvals and output prefixes. Only original same-Ea qualified
24M endpoints are parents. Every output directory is empty at handoff.

Ea8 r001–r003 are prepared for +16M each, ending 40M. Ea10 r001–r003 are prepared
for +32M each, ending 56M. Prospective completed extensions total 144M steps.
All requested/effective MD streams differ from both consumed and unused streams
in the old campaign and earlier policies. Chemistry keeps the parent's seed,
absolute-step keys and counters. No bitwise GJ continuation is promised; do not
stitch segment-crossing IATs, SEMs or lifetime origins.

Each immutable preparation approval has GPU_execution_authorized=false.
The following is the eventual user-run command, **not permission to run it now**:

```bash
cd /home/jramirez/UAMMD_KG
python3 -u examples/KG_Assoc/campaign/run_ea_extensions.py --execute
```

Today it intentionally refuses with “GPU execution pending separate user approval;
preparation only” before the MD loop. That rejection was CPU-tested against the
real preparations with the MD loop mocked unreachable. The common E2 launcher
also rejects preparation-only approvals. Do not flip JSON fields manually.
A later explicit execution approval must be published as new immutable approval
evidence and bound to this exact cohort; preserve the original preparation
approvals. No activation/authorization command is provided in this milestone.

After separate execution approval, the same runner retains the tested lifecycle:
Ctrl+C once requests a graceful stop of the native child and preserves state.
Rerunning the same --execute command independently validates and skips completed
histories. Finished MD with an interrupted receipt can recover only after full
validation of actual evidence. A genuine partial without a bitwise checkpoint
restarts from its exact 24M parent in a fresh immutable attempt with fresh MD;
all abandoned attempts/reservations remain protected and overhead is separately
bounded. Numerical/provenance/oracle failures never trigger seed replacement.

Before the first integration step, the repaired native dispatcher calls the exact
initial device readback. A mismatch/write failure stops the native executable.
Full completion still requires its genuine file, chemistry/numerical replay,
160k/320k candidate comparisons, exact endpoint restart/sidecar and output hashes.
Stable IDs/types, partner reciprocity and exact float32-representation comparisons
remain mandatory. The host CPU probe is not a substitute for this GPU evidence.

Read-only status remains safe during future execution. Keep source/build/evidence
fixed and use one launcher; the existing workflow lock, PID-birth checks and
parent-death supervision protect interruption recovery. Raw managed dataset files
and native binaries already exist on titan; git pull alone does not install them
on a different host.

Ea8 and Ea10 remain on scientific hold. Future 40M/56M numerical completions need
scientific review and separate formal-acceptance approval. No additional cohort,
further extension, registry activation or production is part of this handoff.
