# D2A.5 resource limits and local execution

Preparation only. None of these commands ran in Codex. Independent review and
the user's later local execution choice are required before any command runs.
The [frozen design](E1_STAGE_D2A5_PRODUCTION_PREPARATION.md) supplies the matrix,
SHA256 identities, lag derivation, schedules and provenance limitations.

## Runtime and storage plan

The supplied sustained preflight reports about3569 and1777 production steps/s
for constrained stiff N64/N128 on the recorded RTX3060 Ti. Constant-throughput
proxies are7.8 and62.5 hours/run; these are not bounds, new benchmarks or
predictions for bare/flexible cells. Applying each stiff proxy to all12 runs at
that length gives about35 days total. Larger correlator banks, deeper population
of levels, scalar/context output, GPU load and host/filesystem changes can alter
that proxy. No automatic physical, cadence or resource adjustment is permitted.

| Limit | Frozen value |
|---|---|
| N64 child and complete run stage | 129600 s =36 hours |
| N128 child and complete run stage | 864000 s =10 days |
| Aggregate | 12096000 s =140 days |
| Outer GNU timeout | 12182400 s =141 days, plus15 s kill grace |
| Child peak recorded RSS | 2 GiB |
| Host/cgroup headroom before launch | 8 GiB minimum |
| Host/cgroup headroom during minute monitoring | 1 GiB minimum |
| Free selected GPU memory before launch | 4 GiB minimum; no compute processes |
| Per-run output including logs/receipts | 512 MiB |
| Aggregate output | 16 GiB |
| Disk free initially / maintained | 26 GiB /10 GiB |

The run budgets are about4.6/3.8 times the supplied constrained-stiff time
proxies. Their sum across24 runs is138 days, leaving two days aggregate
allowance for setup/validation. All time arithmetic uses Python integers and
monotonic seconds; Linux alarm/timeout intervals support these durations. There
is no arbitrary24-hour ceiling. The simulator's existing2 GiB estimated-workspace
guard remains in force independently of the supervisor's2 GiB RSS limit.

Serialization allowances in the manifest use32 bytes/numeric field including
delimiter, scheduled row counts, and32 MiB/run for headers, JSON and logs.
The worst constrained-cell allowances are256794080 bytes at N64 and340429280
bytes at N128 (about245/325 MiB), below512 MiB. They include scalar256256 rows,
11 full context frames, two snapshots, initial/final coordinates and spring
files, bond statistics, and all143/159 dynamics bins for256 chains plus the
replica mean. This is an arithmetic planning allowance, not measured output.
For example, scalar rows alone budget14*32*256256=114802688 bytes/run; retaining
D2A.4's sample5000 would multiply that part by roughly20/80. Actual numeric row
widths vary. All24 per-run caps sum to12 GiB; the16 GiB aggregate allows parent
provenance/progress overhead. Initial26 GiB covers that aggregate plus the10 GiB
maintained floor. The supervisor still stops if actual output exceeds a cap.

The existing Linux supervisor remains unchanged: one child, process group,
50 ms time/RSS/disk/output polling, per-file RLIMIT_FSIZE, Linux parent-death
signal, wait4 peak RSS and termination/reaping. Polled limits can overshoot;
RSS is not a hard address-space or cgroup quota. The parent adds minute progress
and host-memory checks and a deadline covering authentication/validation as well
as integration. Termination signals propagate into the supervisor's stop path.
Storage exhaustion, SIGKILL or power loss can prevent a final receipt. There is
no checkpoint, restart, resume or adoption of an interrupted root.

`gpu_before` records device-wide total/free bytes. `device_array_accounting_bytes`
is simulator array accounting; `gpu_peak_memory_bytes` remains null. Neither
field is a process-specific peak measurement. Host RSS is recorded for the child;
parent validator/NumPy memory is outside that peak and covered by headroom checks.

## Commands proposed after independent review

Prerequisites: existing Python3.9+/NumPy environment, Git, GNU timeout,
nvidia-smi, established CUDA13 runtime,64-bit Linux/LP64, recorded sm86 GPU UUID,
the unchanged verified executable and all pinned prerequisite evidence. The
preparation checkout must be committed and clean. Keep source, verified binary,
scripts and evidence stable throughout the campaign. Do not rebuild or replace
a binary needed by queued runs.

From the repository root, first the small CPU-only synthetic checks:

```bash
timeout --signal=TERM --kill-after=15s 120s python3 -B examples/slip-springs/tests/d2a5_campaign_regression.py
```

This creates a fresh persistent fixture leaf
`examples/slip-springs/build/d2a5-campaign-regression-v1` and refuses to overwrite
it. It does not launch subprocesses, query a GPU or run scientific trajectories.
Preserve fixtures on failure. A later verification attempt can select a fresh
leaf using `--output examples/slip-springs/build/d2a5-campaign-regression-v2`;
do not erase old evidence.

Then authenticate the frozen inputs and prerequisite records without querying
or executing the GPU:

```bash
timeout --signal=TERM --kill-after=15s 300s python3 -B examples/slip-springs/e1_d2a5_production.py --verify-preparation
```

This hashes the manifest/tools/schedules/binary, prior correctness/preflight
records and preflight outputs/provenance; it makes no source/build change and
does not create the production root. Failure requires investigation, with no
automatic rebuilding, tolerance relaxation or substitution. Stop before launch
if either local verification fails. Review these results locally before making
the explicit execution choice; this preparation itself supplies no execution
authorization.

The proposed single foreground launch from the repository root is:

```bash
timeout --signal=TERM --kill-after=15s 12182400s python3 -u -B examples/slip-springs/e1_d2a5_production.py --execute-reviewed-24
```

Use a persistent terminal/session on the dedicated host; a reboot, power loss,
SIGKILL or disconnected terminal sending HUP ends the uninterrupted experiment.
No service installation, background launch or system-policy change is performed
by this preparation. No intermediate manual review is required between validated
successes; the runner authenticates, checks headroom, executes, validates and
records each member before continuing.

The frozen new root is
`/home/jramirez/UAMMD_KG-evidence/d2a5/production-n64-n128-r3-v1`.
It must not already exist. There is no root override, force flag, retry or
resume. After an interruption, retain the entire root and review the failure;
a separately reviewed campaign/root is required for any replacement work.

The runner holds a nonblocking advisory lock at
`/home/jramirez/UAMMD_KG-evidence/.locks/GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274.lock`
and verifies the selected GPU is idle before every child. It launches exactly
one GPU child at a time. The lock serializes this runner's invocations; external
programs and historical runners may not honor it. Reserve the GPU and do not
start another GPU simulation during this uninterrupted campaign. The runtime
environment selects the frozen physical GPU UUID explicitly.

## Monitoring and returned evidence

From any terminal, read progress and summary without altering the campaign:

```bash
tail -n 1 /home/jramirez/UAMMD_KG-evidence/d2a5/production-n64-n128-r3-v1/progress.jsonl
cat /home/jramirez/UAMMD_KG-evidence/d2a5/production-n64-n128-r3-v1/summary.json
```

The append-only progress JSONL is fsynced about every60 seconds during work;
it reports UTC, active run, phase, elapsed campaign time, host/cgroup headroom,
free disk and accumulated evidence bytes. It does not invent actual integration
progress: this simulator reports completed step counts only in final metadata.
Polling/validation can briefly delay a heartbeat. A crash can leave a truncated
last line; all earlier complete lines remain evidence. Summary updates occur at
run boundaries; launch/process/receipt records live under `runs/<run-id>/`.

Each successful receipt includes complete file hashes, selected GPU and command
via the hashed launch record, actual step/grid validation, child wall time/RSS,
physical/dynamics timers, production steps/s, output volume and scopes. Stage
elapsed time also includes authentication, context checks and hashing. GPU event
integration, production wall time, CPU acquisition, readback and serialization
are separate, overlapping scopes; never sum subset timers as wall time.

On failure, summary retains all completed run IDs and receipts, identifies the
active run/phase/error and records resource-limit reasons when detected. A child
failure preserves process.json, raw outputs and logs plus failure.json; no failed
run is counted as completed. Failure evidence is not deleted or regenerated.
Return the root summary, manifest/sidecar/config schedules, progress, provenance,
all launch/process/receipt/failure records and raw output inventories for review.
Completion status is `completed_24_runs_not_scientific_acceptance` only after all
members validate. The next step is the separate
[scientific handoff](E1_STAGE_D2A5_PRODUCTION_ANALYSIS_HANDOFF.md), not an
automatic scientific reduction.
