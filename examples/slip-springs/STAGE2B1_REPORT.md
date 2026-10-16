# Stage 2B.1 implementation report

**STAGE 2B.1 ACCEPTED — DEVELOPMENT-HOST SCIENCE, PERFORMANCE AND MEMORY VALIDATION PASSED**

Implementation commit: `1029567096531a2654f362bf7b958359ec77f44c`.
The implementation and bounded-check record below is retained. Subsequent
user-executed Linux-host validation is recorded permanently in
[STAGE2B1_HOST_RESULTS.md](STAGE2B1_HOST_RESULTS.md), with an artifact SHA-256
manifest. Codex inspected accessible output files but did not independently
execute or authenticate the host measurements. The reported 6.28x single-precision
overall speedup, byte-identical correlations and 728/728 analytical memory-run
checks support development-host acceptance. Prefer 16 workers and batch128 for
the tested N32/4096-chain workload on the i7-12700 / RTX 3060 Ti. Production
servers must be benchmarked separately.

**STAGE 2B COMPLETE — STREAMING STRESS RELAXATION VALIDATED**
The subsequent user-executed N100 terminal experiment passed 686/686 checks.
See [STAGE2B_N100_TERMINAL_RESULTS.md](STAGE2B_N100_TERMINAL_RESULTS.md) for all
Stage 2B closure evidence, permanent archived artifacts and SHA-256 hashes.
The accepted model remains the independent Rouse reference; no slip-spring
physics is implemented or validated, and Stage 3 remains unauthorized.

Starting SHA: `6aadcc7edd6f2cfbb4051654b1a0dd881fd44718`, verified against
fetched `origin/slip-springs` before edits. Worktree:
`/tmp/UAMMD_KG-slip-springs`. Final SHA is supplied with the commit handoff.
All source, tests, documentation and build changes are confined to this project.
KG, KG_Assoc, UAMMD and global build files remain unchanged. No PR or Stage 3.
The user's Stage 2B 54-run matrix and N32 terminal 504/504 result are the starting
scientific evidence; no long validation or performance campaign was run by
Codex during implementation.

## Implementation

`cpu_workers.h` adds a portable C++17 persistent pool. Async's existing consumer
is worker 0, with N−1 helpers, for exactly N correlation threads plus the GPU
producer/main thread. There is no dispatcher. Worker i exclusively updates
chains `[C*i/N,C*(i+1)/N)` in the existing stable bank. Frames remain the outer
loop inside each range, preserving chronological arithmetic per chain, including
unequal ranges. Synchronization is outside the inner correlation loops.

The consumer waits for the CUDA copy-completion event, then publishes the same
pinned pointer and frame count with a mutex-protected generation. Helpers wake
once per batch. Worker 0 handles its own range, then waits for a completion
counter. Only afterward does the existing slot transition to free. There is no
full-batch copy, per-batch thread creation, extra queue or new global GPU sync.
The existing two-slot bounded backpressure and CUDA event dependencies protect
device transfers and pinned-buffer lifetimes. Final partial batches use the same
path. Existing shutdown default-stream/transfer waits remain unchanged.

Exceptions from any range are captured; every helper completes before rethrow.
The consumer publishes failures to the producer via the existing pipeline path.
A failed bank is never evaluated. Construction joins partially created helpers
if thread creation fails. Destruction joins the consumer before slot release;
helpers are idle after the completion barrier and stop/join before bank release.
CPU tests cover failures in both worker 0 and helpers; GPU tests cover consumer
failure while batches are submitted. OS thread-creation failure is handled but
not deliberately injected. Concurrent callers of CpuWorkers are unsupported.

`Bank::consume` remains the one-worker reference. `consumeRange` only restricts
its chain loop; Correlator6 add/evaluate, floating-point order per chain, raw
stress inputs, multi-tau mathematics and the final ascending-chain reduction are
unchanged. The six-channel modulus and chain-cluster SE retain channel covariance.
Rouse/RNG, GPU stress kernel and sampling cadence are unchanged. Both precisions
still feed double stress values into the unchanged KG correlator.

## Configuration, portability and memory

Default `--cpu-workers 1` preserves old command behavior. Async `N>1` means exact
N threads, rejected for N>chains or N>1024. Explicit N may exceed available CPUs
when requested. Zero chooses min(chains, available CPUs,1024); synchronous zero
selects one. Sync rejects explicit N>1; CSV accepts 0/1 and records effective 0.
Both requested and effective counts appear in metadata.

Linux dynamic `sched_getaffinity` masks account for cpusets and scheduler
restrictions, including hosts beyond CPU_SETSIZE. Standard cgroup v2 and v1 CPU
mounts are inspected for own/ancestor quotas, rounding fractional budgets down
(minimum one). Missing/unreadable/custom mounts may evade quota detection.
Other platforms fall back to hardware_concurrency, then one. Affinity changes
after initialization are not tracked. This selects a resource bound, not an
optimal hybrid-core configuration; explicit counts and host measurement remain
useful. Only standard C++ concurrency is required, with optional Linux resource
queries. No OpenMP, Intel-specific API, pinning or physical-core assumptions.

Correlator memory stays O(chains*levels*slots), buffers O(chains*batch) per slot.
N adds O(N) handles/timers and OS thread stacks; no per-worker bank/history copy.
Memory is bounded in simulation duration. Existing bank and combined buffer
budgets remain intact; thread stacks and allocator overhead are outside them.

## Timing

All historical performance fields remain. Metadata/terminal output add effective
workers, worker execution sum, worker-0 barrier wait and consumer queue idle.
`cpu_correlation_wall_seconds` measures summed dispatch-to-completion batch wall
intervals; the historical `cpu_correlation_seconds` wraps that call. Neither
includes transfer waits. `cpu_worker_execution_sum_seconds` adds the per-range
execution intervals and can exceed elapsed time. `cpu_worker_barrier_wait_seconds`
is worker 0 waiting after its range (a subset of correlation wall time).
`cpu_consumer_idle_seconds` measures queue waits, separately from existing
transfer-completion waits and producer free-buffer waits. Helper idle waits are
not measured. CUDA, CPU and producer timers overlap and cannot be added to derive
wall time. Production wall time includes final drain, excludes initialization,
equilibration and final curve evaluation/write; overall ns/bead/step is primary.

## Executed bounded checks

CUDA13.0, GNU g++11.4, RTX3060 Ti sm86; C++17, -O2, no fast-math.

| Check | Result |
|---|---|
| Both `make check` precision builds and bounded suites | PASS |
| Historical Stage 2B executable versus new default, both precisions | Byte-identical relaxation.csv |
| CPU serial Bank versus pool1/2/4/8, chains1/9/17, batches1/3/16/43 | Byte-identical |
| GPU streaming workers1/2/4/8/auto, 9 chains, batch1/7/39/40 | Byte-identical within precision |
| Initial-only, partial-final, small reused buffers, sync/async and CSV reconstruction | PASS |
| 14 invalid CLI/memory/configuration guards | PASS, before output creation |
| CPU repeated lifetime and worker/helper failures | PASS, ASan/UBSan/LSan |
| CPU worker synchronization, ThreadSanitizer | PASS, no race report |
| Linux restricted-one-CPU auto-selection assertion | PASS |
| Existing ownership lifetime test, ASan/UBSan/LSan | PASS |
| Both CUDA pipeline failure tests, compute-sanitizer memcheck | PASS, 0 errors |
| README four-worker 200-step examples, both precisions | PASS |
| Host plan Bash syntax and embedded Python syntax | PASS; campaign not executed |

Commands used:

```bash
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
make -C examples/slip-springs check-lifetime
# check includes check-workers; it can also be run CPU-only:
make -C examples/slip-springs check-workers
g++ -std=c++17 -O1 -g -pthread -fsanitize=thread examples/slip-springs/tests/cpu_workers.cpp examples/KG/correlator.cpp -o examples/slip-springs/build/cpu_workers_tsan
examples/slip-springs/build/cpu_workers_tsan
for precision in single double; do
  /usr/local/cuda/compute-sanitizer/compute-sanitizer --tool memcheck --error-exitcode 99 "examples/slip-springs/build/$precision/pipeline_tests"
done
```

Initial sandbox attempts could not access the GPU; LSan could not inspect a
ptraced process. The same bounded checks succeeded outside those sandbox
restrictions, without suppressing leak detection. Read-only KG persistence
functions retain existing ignored-fscanf-return-value warnings.
Logs: `/tmp/stage2b1-{single,double}-final.log`,
`/tmp/stage2b1-{workers,lifetime,tsan}.log`,
`/tmp/stage2b1-memcheck-{single,double}.log`.
Short example outputs: `/tmp/rouse-stage2b1-examples.JNZBfW`.
Historical executable build/comparison instructions are reproducible in the
host plan; independent CSV reconstruction retains rtol=atol=2e-11. Worker-count,
backend, batch and historical executable comparisons require exact file equality.
No tolerance was weakened.

## Handoff and limits

Changed files: `cpu_workers.h`, `stream_correlator.h`, `stream_pipeline.cuh`,
`rouse.cu`, local `Makefile`, `tests/cpu_workers.cpp`, `tests/pipeline_tests.cu`,
`tests/test_stream.py`, `tests/stage2b1_regression.py`, `README.md`, `AGENTS.md`,
this report and `STAGE2B1_VALIDATION_PLAN.md`.

Development-host performance and memory validation are accepted as recorded in
STAGE2B1_HOST_RESULTS.md; no universally optimal worker count is claimed.
Heterogeneous cores, memory bandwidth, thread-stack RSS and coordination can
limit scaling; static ranges do not balance heterogeneous-core speeds. Existing
KG sentinel, coarse-level export and finite precision limitations remain.
Production-server performance requires separate benchmarking. Do not begin Stage 3.

Exact 1/2/4/8/12/16-worker, both-precision 4096-chain benchmark, historical
regression, result-table Python and memory/replay commands are in
[STAGE2B1_VALIDATION_PLAN.md](STAGE2B1_VALIDATION_PLAN.md). Run those on the host.
Current short commands (new directories; executed here):

```bash
RUNS=$(mktemp -d /tmp/rouse-stage2b1-examples.XXXXXX)
examples/slip-springs/build/single/rouse --springs 8 --chains 64 --dt .005 --steps 200 --sample 10 --equil 0 --seed 620008 --output-mode stream --backend async --cpu-workers 4 --batch 7 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$RUNS/single"
examples/slip-springs/build/double/rouse --springs 8 --chains 64 --dt .005 --steps 200 --sample 10 --equil 0 --seed 620009 --output-mode stream --backend async --cpu-workers 4 --batch 7 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$RUNS/double"
```
