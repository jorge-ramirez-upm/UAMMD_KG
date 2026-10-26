# D1.6B resource amendment v1 — proposed, not approved

This independent contract applies only to the new M256/R4/T100 candidate.
`e1_d16b_config/resources.json` is its machine-readable identity. No old D1.5
validator, 120 s/3600 s ceiling, manifest or approval is changed or reinterpreted.
The new spec validates exactly this budget; changing it requires a new version
and independent review. It grants no scientific or operational execution approval.

| Control | Proposed D1.6B value |
|---|---:|
| Per-run stage, child plus output authentication | 600 seconds |
| Entire local cohort command, including authentication/supervision | 14,400 seconds |
| Maximum scientific/output-authentication child host RSS | 2 GiB |
| Minimum available host/cgroup headroom before each run | 8 GiB |
| Minimum free GPU memory before each run | 4 GiB |
| Maximum run plus its output-authentication evidence | 256 MiB |
| Maximum aggregate campaign output/provenance | 4 GiB |
| Minimum free disk maintained while executing | 10 GiB |
| Minimum initial disk: floor plus two campaign quotas | 18 GiB |

The extra quota provisions room for an evidence copy; it is headroom, not an
automatically made backup. The operator must also provision source/build/reference
storage and actual filesystem quotas. Stage A queries headroom before the tiny
fixtures and before declaring readiness. The execution runner checks again before
T100 and every member. Host memory respects available cgroup headroom as in the
accepted supervisor. GPU free memory is a floor before launch, not measured peak
usage. The existing model workspace, event guards and double precision remain.

Planning basis is the authenticated M256 T.1/T1 D1.5 evidence, pinned by
`performance-lock.json`. The D1.6 recorded T100 gross production proxy was
~2056 s (34.3 min) over 16 runs, before some new overhead; worst cell proxy was
~167.7 s/run. Neither proxy is a performance confidence bound. Readiness imports
and reauthenticates the original reports/receipts and raw cohorts rather than
running another benchmark or substituting older M64 scaling estimates.

The unchanged CSV schemas and new audit placement give exactly115,192,412 bytes
of conservative width-envelope CSV/run and1,843,078,592 bytes/cohort (~1.72 GiB).
Add2 MiB/run metadata and64 MiB shared provenance as planning allowances. The
256 MiB/run and4 GiB/cohort quotas leave room beyond these envelopes; limits
are enforced even if real serialization or logs differ. No compression ratio
is assumed for raw output. The empirical M256 output widths remain planning
observations, not hard row-width limits. An unusual binary/build log or evidence
closure can consume that room and must fail visibly, never enlarge a quota.

The existing schema-generic bounded process supervisor is reused through a
private new specification binding. It supplies POSIX group termination, Linux
parent-death kill, wait4 peak RSS, per-process OS file-size limit and periodic
wall/RSS/output/disk checks. D1.6B adds a bounded output-authentication subprocess
whose time is the remaining part of the same600 s run stage, not an additional
600 s allowance. Its receipts count toward that run's output quota. The local
outer cohort subprocess has an explicit14,400 s deadline covering prelaunch
reference/environment/source checks and final cohort authentication as well as
child work. An outer-supervisor death kills the nested GPU supervisor/child.
There is a separate durable D1.6B GPU lock; historical lock files are unchanged.
Checks poll at50 ms; OS scheduling/termination latency is recorded and no
hard-real-time guarantee is claimed. A cap overshoot prevents successful completion.

Each invocation consumes an immutable launch and execution-attempt record before
GPU work. Roots and cases cannot be overwritten or adopted. No retry, restart,
resume, failed-member replacement or automatic continuation is implemented.
Interruption preserves raw files, receipts/status and failure logs; a missing or
changed completion marker cannot become a complete scientific cohort.

Readiness is separate: deterministic tests120 s, build480 s (inherited compiler
itself240 s), reference import600 s, performance import900 s, environment/
read-only preflight commands180 s each. With the operator's existing authorization
for tiny readiness scope, reuse only the unchanged nine-step N3/M4 and N17/M2
fixtures. Their inherited test guards (30 s/member,60 s technical scope,64 MiB
technical root,4 GiB fixture child ceiling) are distinct from the T100 budget;
the top-level tiny-fixture command is limited to120 s. This does not authorize
an M256/T100 member or a new benchmark. Build, test and scientific source paths
stay in the new durable readiness root; TMPDIR for retained fixtures/compiler
scratch is explicitly durable. No prior approval is promoted to T100 authority.

Stage C has a separate proposed7200 s /4 GiB RSS /256 MiB analysis-output cap.
It authenticates raw inputs before/after streaming reduction and does no GPU
work or new sampling. The compressed analysis preserves reduced results,
replica vectors, full uncertainty/reference covariance and support diagnostics.
The return packet has a32 MiB uncompressed-member total cap and16 MiB/member cap;
it contains the compressed analysis, small records and raw-file inventory,
without raw CSVs or executables. Oversize packets stop without dropping evidence.
Readiness and results packet creation, durable checkout/build storage and an
operator's raw backup lie outside the T100 cohort quota and must be provisioned
separately. Full raw output remains local; packaging never deletes it.
