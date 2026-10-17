# Stopped by user; long execution handed off

**No long simulation is running. No 24M endpoint completed.**
The user explicitly cancelled agent-run long computations and required a user-run
handoff. AGENTS.md now records a mandatory ten-minute maximum for assistant-run
short tests and prohibits long jobs, including background/detached workarounds.
The correct self-run commands and restart behavior are in [RUN_YOURSELF.md](RUN_YOURSELF.md).

Starting local/remote SHA: `798cf932510a9345a0103f2706e1744e4d3b17a9`.
Initial committed validation support: `2d56f2ec26ba5780fcf38549264e7070ec46c71c`.
Agent launch source: `e1f31a830cb50cc03196c821c784f1a0179d4b41`.
The containing handoff commits record the later administrative selector/runner,
tests and durable execution policy. No native source changed after the initial
cap-only diagnostic build. No further GPU trajectory was launched after cancellation.

## Execution outcome

Only Ea6 r001 started. It originated from the exact qualified corrected-C1 Ea4/Ee8
r001 absolute-8M reference, with chemistry seed 1020601, requested MD seed 1030601
and effective MD seed 909083124. All other eight histories remained unstarted.

The controlled launcher received SIGINT at the user's request and terminated its
native child. Its interruption receipt is dated 2026-10-17T10:30:18.918563Z.
A subsequent actual `nvidia-smi --query-compute-apps` returned no processes.
The generic launcher stop record calls this a failure; USER_STOP.log records the
specific classification **user cancellation**, without relabeling it a completion.

Initial actual device readback passed for every one of 43,563 particles, with
exact represented positions/velocities, IDs/types and chemical partners.
The last fully written passing oracle record is absolute 10,304,200: 23,042
comparisons. The last fully written accepted event is absolute 10,332,900.
Therefore at least **2,332,900 additional MD steps** executed. SIGTERM did not
serialize the exact integration step or flush every buffered output; this is a
lower bound, not an exact completion count. No final restart/sidecar was produced.
The partial is not a validated 24M endpoint or an equilibrated preparation.

An independent replay of the fully flushed first 500k steps passed: 1,416 creations,
1,422 breaks, 1,278 neighbor gains, 1,273 losses, 5,000 oracle comparisons and 501
finite numerical/conformation/state samples. The earlier observer check merely
waited for an unflushed conformation buffer; its diagnostic is preserved. No MD
retry or numerical-oracle relaxation occurred. No candidate mismatch was reported.

| System | r001 | r002 | r003 |
|---|---|---|---|
| Ea6 | user-interrupted partial | not started | not started |
| Ea8 | not started | not started | not started |
| Ea10 | not started | not started | not started |

All three systems remain on scientific hold: there are no completed new endpoints
on which to make an E2 acceptance recommendation. The requested joint 16M scientific
assessment and plots cannot be produced from unexecuted trajectories. Draft
analysis tools were CPU-tested, but no future observations or stationarity results
are represented as measured. No formal acceptance, registry or production action occurred.

## Validated handoff

`run_ea_preparation.py --execute` is for the user to run on titan. It prepares fresh
immutable plans/reservations, binds each selected replica and exact 16M cap, and
executes the nine original-parent branches. It never overwrites this cancelled
campaign. The same command skips checked completions, recovers finished MD whose
receipt was interrupted, and automatically replaces a user-interrupted partial
with a fresh original-parent attempt and streams. Genuine numerical/provenance
failures remain fail-closed and are never silently retried with another seed.
This is workflow continuation; a partial history restarts from 8M because no
intermediate GJ checkpoint exists. Extra partial work is separately visible.

Per-replica approvals permit launching a pending history while other replica
directories already contain completed outputs. Unselected histories cannot launch
implicitly. Selected output reuse is still rejected by the low-level launcher;
the user-facing runner handles it by preparing unique attempts. Existing smoke
selectors and ordinary E2 gates retain their tests. The administrative runner is
explicitly excluded from the native scientific-source comparison, like run_e2.py;
no physical or validation implementation is excluded wholesale.

CPU validation: 189 shared/selector/manual-run tests, fourteen transfer tests and
five forensic tests passed (208 distinct Python tests). The forty focused selector
and lifecycle cases overlap that total. Mocked lifecycle checks cover interruption,
completed-history skipping, orphan completion receipt recovery, fresh reservation
collisions, existing unused approvals, unselected-directory preservation and
stop-on-genuine-failure. No test invokes real MD. A final actual `--check` authenticates
the committed source/build/parents without GPU execution or seed allocation.

The initial build also passed both native host self-tests, original candidate
regressions, 398 cutoff/periodic cases, twelve exact ULP corruption rejections,
twelve cap boundary probes and all nine host parent checks. The optimized parent
velocity probe checked all 130,689 components exactly. Ordinary preprocessing
differs only in two CUDA error-report line numbers. See BUILD_RESULTS.md.

Preservation checks authenticate the twelve formal acceptances and payloads,
failed campaigns, successful smoke, old reservations, reviews and executable builds.
The original 2,629-binding baseline permits only the three documented validation/
administrative source transitions; protected payload bytes remain unchanged.
STOPPED_OUTPUTS.sha256 additionally authenticates this cancelled campaign's raw
plans, approvals, partial outputs and logs. No protected examples/KG or src file
was modified. The final repository SHA and local/remote clean-tree check are
reported with the handoff; long execution belongs to the user from this point.
