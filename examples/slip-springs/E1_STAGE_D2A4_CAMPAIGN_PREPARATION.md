# D2A.4 — long-duration dynamics campaign preparation

27 October 2026. Starting local and actual remote `slip-springs` HEAD:
`1d0870a92989fb9bebe41a0919ab8c7e2b6fe362`, verified before modifications.
**Preparation only. No test, build, reduction, simulation, benchmark or GPU
operation ran.** The user selected the complete twelve-run design with no
mandatory intermediate review between successful executions. Independent review
of this preparation precedes the user's explicit local launch.

## Frozen physical matrix and acquisition

[manifest.json](e1_d2a4_config/manifest.json) fixes source/binary/build identities,
all12 argv arrays, run order, seeds, replica IDs, schedules, clocks, expected
counts and resources. Manifest SHA-256:
`697f0f3be4841221d5b109e0376f4de9da63f239db6f088e5b128da0d4d438fc`.
It is pinned in the [sidecar](e1_d2a4_config/manifest.sha256) and tiny
[D2A.4 entry point](e1_d2a4_run.py).

| Cell | kappa | Z | Run IDs | Seeds = whole-run replica IDs |
|---|---:|---:|---|---|
| A | 0 | 0 | A-r1,A-r2,A-r3 | 732404101,732404102,732404103 |
| B | 0 | 2048 | B-r1,B-r2,B-r3 | 732404201,732404202,732404203 |
| C | 10 | 0 | C-r1,C-r2,C-r3 | 732404301,732404302,732404303 |
| D | 10 | 2048 | D-r1,D-r2,D-r3 | 732404401,732404402,732404403 |

Order is exactly the table order, three replicas per cell, twelve serial
processes. Before reserving seeds, literal searches found no matches in
available repository/evidence JSON/Python/Markdown/text records. Inaccessible
external uses cannot be excluded. Do not reuse D2A.3 replicas, rename seeds
after seeing results or replace failed runs automatically.

Every run: N32/33 beads, M256, kb30, b0=kBT=zeta=1, dt0.0001, T1000,
10000000 BD steps, double precision, slip-ms2=5 and hop-rate100. Canonical
end renewal is on for Z2048; bare Z0 has renewal explicitly off and no active
spring/jump process. **Stress mode stays off.** The existing E1 prohibition on
stress with active springs remains intact. No force, RNG, hopping, renewal,
integrator, initializer or observable arithmetic changed.

The same six absolute-position MSD owners (CM and beads0/8/16/24/32) and existing
orientation adapter produce C1/C2. No internal MSD or new observable is added.
Dynamic settings: stride100, delta0.01, L15/P16/m2, observer budget256 MiB,
100001 frames including the initialized step0. Subsequent frames are after
completed BD, coordinate-buffer swap, complete hopping/renewal and checks.
Shared frames reuse the existing readback; other frames use the same synchronous
buffer/CPU path. No new gather kernel, stream or worker pool is introduced.

Scalars remain every5000 steps (2001 frames). The
[full-context schedule](e1_d2a4_config/equilibrium.steps) is0,1000000,...,10000000
(11 frames), and [joint snapshots](e1_d2a4_config/snapshots.steps) are0 and10000000.
All context frames coincide with scalar/dynamical frames: shared2001, extra
readbacks98000. Existing scalar rows supply full-frame backbone values, so
equilibrium_backbone.csv remains correctly header-only. Endpoint snapshots
preserve coordinates and contemporaneous attachments without a dense trajectory.

The [resource/support plan](E1_STAGE_D2A4_RESOURCE_PLAN.md) derives116 exported
bins/chain, maximum lag901.12 with one origin, and conservative primary endpoint
184.32 with39 origins/chain. Counts are actual decimated/block-support counts,
not effective independent samples. Nominal coarse MSD and orientation lags have
different endpoint versus triangular block support. Three whole-run replicas
per cell remain the uncertainty units (only two variance degrees of freedom).
Cross-chain renewal/canonical occupancy can correlate chains within a run.

## Executable and reproducibility

Reuse the unchanged, previously prepared double executable:

    /home/jramirez/UAMMD_KG-d2a2-verification/build/current-double/semiflexible

SHA-256:
`da303c4c2b2de94172fe0114f4f5cc2d78fd9499ef188938a15114cc3100f342`.
Clean pinned source tree:
`/home/jramirez/UAMMD_KG-d2a2-verification/sources/current`, SHA
`d60982f4035b9b704a23397fb034ca1b58fe5771`.
Build provenance remains CUDA13.0.88/g++11.4.0, sm_86, double,
`-O2 -std=c++17 --extended-lambda`, no fast math. Original build-settings hash
is pinned in the manifest and copied to campaign provenance. Binary/source/
helper hashes are checked before every launch and after successful validation;
the script never builds or replaces the binary. The target GPU UUID remains
`GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274`; local nvidia-smi checks identity,
capability8.6, idle compute state and prelaunch free memory at user execution.
No device query ran during preparation.

## Minimal infrastructure changes and historical compatibility

The small [entry point](e1_d2a4_run.py) invokes the parameterized execution
function in [the existing runner](e1_d2a3_run.py); it does not duplicate the
process-supervision loop. That runner now takes a frozen config/hash and derives
frame/grid/clock/row expectations from its manifest. The shared validator models
partial last levels and deepest-level omission, rather than assuming every
configured coarse slot is populated. The low-level Linux supervisor is unchanged.

Direct D2A.3 execution retains its original flag, frozen manifest, eight-run
defaults, limits and completion classification. Its archived source/receipts/
evidence are unchanged. D2A.3 offline analysis had a strict local-validator
hash check: it now pins this reviewed parameterized validator, while archived
tool bytes still must match their original5f9aa4d Git blobs. Default validation
still uses the unchanged hash-pinned D2A.3 specification. No old data ignore
rule, numerical tolerance or acceptance criterion was relaxed. D2A.3 analysis
remains an eight-run/T100 tool and must not be pointed at D2A.4 evidence.

## Local launch after independent review

Linux prerequisites: Python3 with the existing supervisor's NumPy dependency,
Git, GNU timeout, nvidia-smi, the preserved executable/source/build-settings,
and the established CUDA installation. The preparation checkout must be clean.
The new permanent output root must not exist:

    /home/jramirez/UAMMD_KG-evidence/d2a4/long-t1000-twelve-v1

One command from any working directory:

```sh
timeout --signal=TERM --kill-after=15s 45000s python3 -B /home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d2a4_run.py --execute-reviewed-twelve
```

It creates the parent if needed, copies/hashes read-only configuration and
tool provenance, and runs every successful member without a prompt. One GPU
child at a time; every child must exit and validate before the next launch.
There is no resume, overwrite, failed-member substitution, retry or automatic
reduction of cadence/duration/replicas. Fresh-root and advisory-lock protections
remain. Any failure stops, preserves raw outputs/logs and records a partial
summary when possible. Do not remove evidence to reuse the same root.

Limits are3600 s/run,45000 s overall,2 GiB child RSS,512 MiB/run,8 GiB
aggregate output,8 GiB available host and4 GiB free GPU before launch,10 GiB
maintained free disk and26 GiB initially. The resource plan distinguishes
timer/per-file enforcement from polled thresholds and possible overshoot.
No new hard cgroup quota or privileged infrastructure is required.

## Completion products, checks and review gate

Require zero exit, valid physical/E1 and dynamic completion, exact fixed model/
seed/replica/coefficient/acquisition identity, all100001 frames, complete expected
physical CSV rows and finite values. Each chain has116 ordered curve rows:
29696 chain rows plus116 replica rows per run. Exact integer lags, actual counts,
decimation phases, block widths and physical lag times are checked. Invalid,
missing or unknown output files stop rather than being repaired/discarded.

Per-run products retain preflight/launch measurements, full argv, stdout/stderr,
exit status, wait4 child peak RSS, wall time, completion validation and file
hashes. Aggregate summary lists all completed IDs, resource/receipt records,
elapsed time and evidence sizes. GPU peak memory remains null. Success is
`completed_twelve_runs_not_scientific_acceptance`, never a physical acceptance
claim. Failed runs preserve partial inventory/error information when writable.
No curve fitting, terminal classification, stress or scientific reduction runs
inside execution. Resource usage is assessed after the cohort or on failure,
with safety monitoring throughout and no mandatory intermediate review.

[Small synthetic regression checks](tests/d2a4_campaign_regression.py), left
unexecuted, cover partial/deepest support, primary range, m=2/m=3, short records,
D2A.3 default support, frozen matrix/schedules/stress-off and malformed coarse
CSV counts/clocks/nonfinite/missing rows. Local optional verification commands:

```sh
python3 -B examples/slip-springs/tests/d2a4_campaign_regression.py
python3 -B examples/slip-springs/tests/d2a3_runner_regression.py
python3 -B examples/slip-springs/tests/d2a3_analysis_regression.py
```

None ran in Codex; this composition and long-duration runtime/peak usage remain
unverified. Long duration is the user's chosen horizon, not a deduction from
unexecuted D2A.3 curve analysis. T1000, R3 and184.32 supported lag do not prove
terminal diffusion, complete orientational relaxation, timestep accuracy or
ergodicity. D1.6 remains **scientifically closed with qualifications — equilibrium
preservation not confirmed**. No D1.6 reopening, D2B force change or rheology
implementation occurs. See the [future six-component rheology requirements](E1_FUTURE_SIX_COMPONENT_RHEOLOGY.md).
Stop after preparation for independent review before executing D2A.4.
