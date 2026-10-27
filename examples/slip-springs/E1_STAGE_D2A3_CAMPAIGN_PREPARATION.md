# D2A.3 — eight-run campaign preparation and operator handoff

27 October 2026. Starting local and queried remote `slip-springs` HEAD:
`64cc6aa6489054a7d1022aafab8c468aa4d5d0f3`.
**Preparation only: no run, test, build, benchmark, GPU query or scientific
analysis executed.** The user chose all eight sequential runs without a
mandatory intermediate review after the first. Independent review of this
preparation precedes the user's explicit launch; no per-run confirmation is
requested by the runner.

## Frozen inputs and identities

The [scientific design](E1_STAGE_D2A3_EXPLORATORY_DESIGN.md) remains unchanged.
[manifest.json](e1_d2a3_config/manifest.json) fixes all options, run order,
seeds/replica IDs, absolute source/binary/output paths, resource limits and
expected observations. Imported supervisor/helper file hashes are fixed as
well; copied schedules are rechecked before each run. Its SHA-256 is
`21fd5168be99823e0dccb9af0e83a03a0467b46c50ea79b9fa0bc1d3772fe1cb`,
pinned in the runner and [sidecar](e1_d2a3_config/manifest.sha256).

| Order / run | kappa | Z | Seed = unique whole-run replica ID |
|---|---:|---:|---:|
| 1 / A-r1 | 0 | 0 | 732303101 |
| 2 / A-r2 | 0 | 0 | 732303102 |
| 3 / B-r1 | 0 | 2048 | 732303201 |
| 4 / B-r2 | 0 | 2048 | 732303202 |
| 5 / C-r1 | 10 | 0 | 732303301 |
| 6 / C-r2 | 10 | 0 | 732303302 |
| 7 / D-r1 | 10 | 2048 | 732303401 |
| 8 / D-r2 | 10 | 2048 | 732303402 |

Before reserving these seeds, a literal search found no matches in available
repository/evidence JSON, Python, Markdown or text records under the roots listed
in the manifest. This establishes no recorded prior use in those records, not
an assertion about inaccessible external runs. Each run independently invokes
the accepted initializer and RNG with its own seed; chain results are averaged
within a whole-run replica. Replicas are unpaired across cells.

Common: N32/M256, kb30, b0=kBT=zeta=1, dt0.0001, T100, 1,000,000 steps,
double precision, slip-ms2=5, hop-rate=100, stress off. End renewal is enabled
for constrained cells and explicitly disabled for bare cells. No active jump
process exists at Z0. Correlation configuration is stride100/L11/P16/m2 with
256 MiB observer allowance; sample stride5000. The
[full-context schedule](e1_d2a3_config/equilibrium.steps) is
0,100000,...,1000000; [snapshot schedule](e1_d2a3_config/snapshots.steps)
is 0,1000000. Both are copied and hashed before execution. No frozen D1.6
schedule or acceptance rule is edited or reused as execution authority.

Use the existing, separately preserved executable:

    /home/jramirez/UAMMD_KG-d2a2-verification/build/current-double/semiflexible

SHA-256:
`da303c4c2b2de94172fe0114f4f5cc2d78fd9499ef188938a15114cc3100f342`.
Its source is the clean pinned worktree
`/home/jramirez/UAMMD_KG-d2a2-verification/sources/current`, commit
`d60982f4035b9b704a23397fb034ca1b58fe5771`. CUDA13.0.88/g++11.4.0,
sm_86, `-DDOUBLE_PRECISION`, `-O2 -std=c++17 --extended-lambda`, no fast math;
the external build-settings JSON is pinned by hash and copied to campaign
provenance. The runner rechecks binary/build hashes and source HEAD/clean status
before each run and after successful output validation. It does not rebuild,
copy over or modify either matched executable. The older baseline binary is
not a campaign input. Documentation/verifier changes since d60982f do not
change the prepared physical executable.

The fixed target is the previously recorded RTX3060Ti UUID
`GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274`; at launch, nvidia-smi must confirm
UUID/compute capability 8.6, driver/name and free memory. No CUDA runtime probe
or benchmark is added. The manifest records toolkit/host compiler versions as
build provenance, not a claim that driver compatibility was remeasured here.

## One launch command, for the user after review

Linux prerequisites: Python3 with the existing NumPy dependency of the reused
supervisor, GNU timeout, Git, nvidia-smi, the pinned executable/worktree and build-settings
file above, and the established CUDA13 installation. The development checkout
must be clean. No build, package installation or GPU test is performed by this
command before launching the specified simulations.

```sh
timeout --signal=TERM --kill-after=15s 7200s python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d2a3_run.py --execute-reviewed-eight
```

The runner requires this explicit execution flag; importing it launches nothing.
Output root is fixed and must be **absent**, including absent as a broken symlink:

    /home/jramirez/UAMMD_KG-evidence/d2a3/exploratory-eight-v1

The parent is created if needed. Each run occupies `runs/A-r1`, ..., `runs/D-r2`,
with the simulator's fresh directory at `output/`. There is no override to adopt
an existing campaign, resume, overwrite or retry a member. Do not delete failed
evidence to make the same command run again; return for review of a new attempt.
No input prompt occurs between successful runs. One child is launched and reaped,
its outputs validated and receipt recorded, before the next child starts.

## Resource safeguards and their practical limits

[e1_d2a3_run.py](e1_d2a3_run.py) reuses `run_process`, `resource_check`, and
the host/cgroup and directory-size helpers from the existing
[Linux supervisor](e1_d1_pilot_runner.py), unchanged. It does not invoke that
module's historical manifest/build/approval/campaign entry points. Sanitized
child environment selects the fixed GPU UUID and CUDA library directory; no
LD_PRELOAD or inherited compiler injection is passed. A persistent advisory
flock under `d2a3/.locks/` prevents two instances of this runner on that GPU.
Before each launch, an nvidia-smi compute-process query rejects another active
process on the target. Uncooperative external launchers can race that check;
the operator must reserve the GPU. Historical locks and evidence are untouched.

| Limit / requirement | Mechanism |
|---|---|
| 600 s per run | ITIMER_REAL covers run setup, child, validation and receipt; child supervisor also polls child wall time |
| 7200 s whole campaign | ITIMER_REAL deadline from entry covers preparation, queries, all children and completion validation; outer GNU timeout also covers Python import/startup; no clock reset between runs |
| 2 GiB child resident memory | /proc VmRSS polling and final wait4 ru_maxrss; breach kills child/fails stage; simulator allocation guard is additional, not an RSS cap |
| 256 MiB per run | Aggregate run-directory size polling, including logs; checked again after receipt; child RLIMIT_FSIZE additionally caps each individual file at 256 MiB |
| 2 GiB campaign output | Whole-tree size polling during each child and checks after receipts/final summary; includes configuration/provenance/logs |
| 8 GiB host headroom | Before every launch: minimum of /proc MemAvailable and visible unified-cgroup ancestor headroom |
| 4 GiB GPU headroom | nvidia-smi free-memory check before every launch, not a continuous peak-memory measurement |
| 10 GiB maintained free disk | Polled during children; checked before launch and after validation; prelaunch adds one run's output allowance as headroom |
| 18 GiB initial free disk | Checked once before the first member; separate preserved source/build storage already exists |

Wall deadlines raise exceptions, triggering the reused supervisor's process-group
SIGTERM then SIGKILL after up to one second; Linux parent-death SIGKILL protects
the direct simulator if the supervisor dies. SIGINT/SIGTERM abort and preserve
evidence. Polling is nominally 50 ms plus filesystem/OS latency. **RSS, total
directory bytes and free-disk thresholds are monitored with stop-on-violation,
not hard cgroup/filesystem quotas; transient overshoot is possible.** Linux
RLIMIT_RSS would not provide a reliable resident-memory cap, and RLIMIT_AS is
not substituted because CUDA virtual address reservations are different from
resident memory. No new privilege/cgroup requirement is introduced.

Deadline signaling/termination and durable error recording are not hard-real-time
guarantees; emergency partial-file hashing has a separate maximum 10-second
cleanup window after abort; the outer timeout escalates to SIGKILL after 15 s.
This can extend failure-recording wall time beyond
the scientific deadline, without launching another run. Abrupt SIGKILL, full
disk or I/O failure can prevent a final summary/receipt; absence of completion
remains failure, never an inferred pass. Restart/resume is not provided.

Budget is eight times 256 MiB =2 GiB total allowance, including small shared
records within that same aggregate limit. Actual sizes must fit; no automatic
cap expansion. The design's ~32.7 MiB correlator payload and ~2.52 GiB transfer
traffic per run are arithmetic planning quantities, not runtime/peak-memory
measurements. No mandatory first-run performance review is imposed. Resources
are summarized after the eight-run sequence or at failure; a breach stops it
immediately rather than waiting until the end. No parameter, cadence, duration
or replica count is automatically reduced.

## Output validation and evidence products

Successful simulator exit alone is insufficient. Each run must have final main
metadata, valid E1 completion/schema with 11 frames and the two snapshot steps,
the expected physical file set, and exact completion-inventory byte sizes for
the actual files. Main/dynamical model identities include N/M, kBT/zeta, seed,
precision, dt/steps, spring count, coefficients, effective spring stiffness,
initialization and acquisition settings. Stored parameters.txt is also checked.
Constrained hopping metadata must identify canonical renewal/rate100 and
1,000,000 batches. Sparse physical record row counts and finite values are
checked. At these schedules, full-frame backbone rows are in samples.csv;
equilibrium_backbone.csv is correctly header-only, not a missing data repair.

Dynamical completion must specify 10,001 frames, clock0/100/1000000,
shared_frames201/extra_readbacks9800, L11/P16/m2, 256 MiB guard, correct chain
and replica IDs, unwrapped coordinates, and unchanged displacement-decimation
and orientation-block semantics. Only the three expected dynamic products may
exist. Both CSV headers, row counts (256*88 chain rows and 88 replica rows),
ordered IDs, every integer lag/decimation/phase/origin count, lag time and
orientation block duration are checked. All recorded correlation quantities
must be finite. For level k, count is `floor(10001/2^k)-ell`; level10 is
omitted and the last exported lag is 76.8 with four origins per chain.
These are acquisition-completeness checks, not scientific value tolerances.

Each run preserves `preflight.json` (sampled headroom before the resource gate),
`launch.json` (complete argv, before-launch resources/GPU),
`stdout.log`, `stderr.log`, `process.json` (exit/status, measured child wall and
wait4 peak RSS), all simulator products, and `receipt.json` with hashes/byte
counts and validation scope. Hashes identify bytes, not scientific correctness.
On failure, raw evidence remains and `failure.json` attempts a bounded partial
inventory; a hashing failure is recorded in summary when possible. No scientific
curve shape, diffusion, relaxation or physical contrast is interpreted here.

At campaign level, `config/` preserves manifest/schedules and `provenance/`
preserves the runner plus imported local helper closure, build-settings and
launch environment/checkout identity. `summary.json` lists completed runs,
per-run exit/resource/receipt records, total elapsed time, maximum child RSS,
summed child wall and output sizes. GPU peak memory is explicitly unavailable;
launch headroom is not relabeled as a peak. Its success classification is
`completed_eight_runs_not_scientific_acceptance`. A stopped campaign reports
its failing member/error and completed subset; later members remain unrun.
Timing scopes overlap and are not added as independent wall costs.

## Verification preparation and limitations

[Unexecuted deterministic checks](tests/d2a3_runner_regression.py) use synthetic
CSV/JSON only to check finite curves, exact fine/coarse support, identity,
missing/extra rows and malformed values. Optional user command after review:

```sh
python3 -B examples/slip-springs/tests/d2a3_runner_regression.py
```

These do not test real GPU runtime, OS resource enforcement or all filesystem
failure paths. The supervisor has existing bounded verification history; this
new composition and its output validation have **not** been executed in Codex.
There is no new measurement framework, build target or numerical reference.
Source changes are only this runner, its fixed config/schedules, the small
unexecuted regression and documentation/status links. No accepted simulator,
correlator, D1.6 evidence or criteria, or matched executable changed.

D1.6 remains scientifically closed with qualifications — equilibrium preservation
not confirmed. The independent statistical unit remains one whole run; R=2
uncertainty is weak. The approved design's lag-support limitations, unknown
terminal behavior and timestep qualification remain. D2B force alternatives
are not implemented. Stop after preparation for review; only the user's later
explicit launch executes the full eight-run sequence.
