# User-run bounded production compatibility tests

This authorizes **fifteen100k tests only** (maximum1,500,000 MD steps), never100M
production. The assistant has executed zero GPU/MD steps. All15 conditions are
covered with r001, except Ea10 uses r003 to include the documented scientific
exception. These are compatibility observations, not kinetic/convergence studies.

On `titan`, from the existing authenticated workspace:

```bash
cd /home/jramirez/UAMMD_KG
git switch KremerGrest
git pull --ff-only origin KremerGrest
timeout 600 python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/DRIVER.txt --check
timeout 600 python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/DRIVER.txt --status
```

Both commands are read-only CPU checks. They authenticate the frozen45-history
campaign, exact parent/hash/seed/build bindings, Git-published short-test authority
and identical authorized sources. A clean tree is required. Do not regenerate plans
or edit approvals/reservations if a check fails; retain the error for investigation.
The existing original workspace/parent bank/binaries are required; Git alone does
not recreate ignored simulation data.

The exact authorized **user-run GPU command**, tested with CPU process fixtures:

```bash
python3 -u examples/KG_Assoc/reviews/production_launch_validation_20261023/DRIVER.txt --execute
```

Do not run it from the assistant session. It executes the15 designated tests
sequentially, stops on the first failure and skips only reauthenticated independent
completions. It cannot select extra systems or redirect output/seed/length. The
`--replica` argument is for explicit recovery only, not a launch selector. Default
authority is `VALIDATION_BINDINGS_v3.log`; the unchanged15 approvals are listed in
VALIDATION_HISTORIES.csv. No `--production-authority` is supplied or authorized.

Expected native integration time from historical linear scaling is ~14min total,
~27–142s per history, **plus** initialization, stress flush, CPU hash/validation and
I/O overhead. These are estimates, not timing guarantees. Jobs execute one at a time;
retain the foreground terminal. Reserve provisionally2GB free for these short-test
outputs and logs; binary bead output alone is30.71MB. No raw stress is emitted.
No full MD checkpoint or automatic resume exists.

## Stop, monitor, recover

Ctrl-C or SIGTERM to the driver terminates/waits for its native child and preserves
the started/failure journals and partial files. A forced SIGKILL or power failure
may prevent journal finalization; investigate surviving native processes before any
further command. Status never launches or repeats MD:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/DRIVER.txt --status
```

Run status in another terminal for monitoring; the live launch holds the standard
OS workflow lock. A second launch is rejected. A partial/failed/native-finished
history is held on a repeated `--execute`; no seed replacement or output overwrite
occurs. Genuine incomplete replacements need separate approval, new identities and
fresh streams; none are prepared here.

If native completion is authenticated but its independent check encountered an
administrative exception, recover **only that history**, e.g. for the C1 condition:

```bash
python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/DRIVER.txt --recover F04_N010_RP080_EE08_EA04 --replica 1
```

Recovery is CPU-only. It requires the exact original source/approval identity,
started/native_finished receipts, native PASS/duration evidence and all independent
checks. It preserves original failure bytes and creates distinct recovery.json plus
a hash binding. Repeating it is idempotent. Numerical/provenance/native failures,
missing/corrupt scientific evidence and unauthenticated completions are rejected.
If native_finished.json is absent, retain the hold for explicit forensic recovery;
do not infer it from a partial file or rerun MD. After successful recovery, the same
`--execute` command skips that validated history and reaches the next prepared one.

## What a successful batch establishes

It establishes supported production output/counter/event/stress/endpoint checks
on these exact accepted parents. **It does not certify exact initial GPU state or
runtime independent candidate-oracle equality:** those mechanisms do not exist in
this production binary. The driver reports a compatibility hold after numerical
success. HOST_FIDELITY.log is a host-only float32 representation audit, not a device
readback substitute. Historical E2 oracle/readback results remain separate evidence.

Before production activation, review the actual bounded GPU results and resolve
those explicit unsupported checks under a separate decision. Full device/oracle
certification would require narrowly scoped validation-only instrumentation and a
new authenticated build/plan-compatibility decision, without changing physics. No
such native change or execution is performed here. The45 production preparations
remain dormant and no production execution approvals have been issued.
