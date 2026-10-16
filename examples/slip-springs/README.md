# GPU Rouse chains and parallel streaming stress modulus: Stage 2B.1

This standalone UAMMD/CUDA example simulates independent Gaussian chains with
local Euler–Maruyama Brownian dynamics. It is a distinct coarse-grained model
from Kremer–Grest molecular dynamics. Stage 1 implements equilibrium Gaussian
initialization, free-end harmonic forces, unwrapped updates, conformation
observables and direct-lag dynamic validation. Stage 2A adds double-accumulated
GPU per-chain configurational stress, direct-lag stress correlations and permanent
performance reporting. Stage 2B adds bounded synchronous/asynchronous Correlator6
streaming and the chain-density-normalized relaxation modulus.
**STAGE 2B.1 ACCEPTED — DEVELOPMENT-HOST SCIENCE, PERFORMANCE AND MEMORY VALIDATION PASSED**.
User-executed Linux-host results show byte-identical correlations across tested
worker counts, 728/728 analytical 5-SE checks in the million-step memory run,
and 6.28x single-precision overall speedup at 16 workers. On the RTX 3060 Ti /
i7-12700 development host, prefer async streaming with `--cpu-workers 16 --batch 128`
for the tested N32/4096-chain workload. Defaults remain unchanged. Production
servers require separate benchmarking; this is not a universal optimum.
See [STAGE2B1_HOST_RESULTS.md](STAGE2B1_HOST_RESULTS.md) for measurements,
provenance and artifact hashes. Further optimization is not required before
N100 terminal-relaxation experiments. Stage 3 and new physics remain unauthorized.

A chain has **N springs and N+1 beads**, numbered 0 through N. Units are
b=kBT=zeta=1 per bead, tau_0=1, tau_s=1/3. Its energy is
`U=(3/2) sum |r_(i+1)-r_i|^2`; there are no excluded-volume, hydrodynamic,
interchain or periodic interactions. Every update reads an old buffer and writes
a different buffer. All chains share one UAMMD particle ensemble.

All source changes and generated files must stay in `examples/slip-springs/`
or, for generated artifacts, outside the repository. Existing UAMMD, KG and
KG_Assoc files remain read-only. `STAGE0_REPORT.md` is historical; see
[STAGE1_REPORT.md](STAGE1_REPORT.md) and [STAGE2A_REPORT.md](STAGE2A_REPORT.md)
for numerical results and limitations, and
[AGENTS.md](AGENTS.md) for permanent scientific/development rules.

## Build and quick tests

Requirements: GNU Make, a C++17 host compiler, a CUDA toolkit including cuRAND
headers and Thrust/CUB, a compatible NVIDIA GPU, and Python 3.10+ with NumPy for
analysis/tests. Nothing is downloaded automatically. CUDA 13 requires C++17.
The device RNG is header-only; no cuRAND library linkage is needed.

From this worktree's repository root:

```sh
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
```

`check` builds/runs the Stage 0 smokes, GPU force/observation/RNG unit tests,
independent CPU matrix/Wick-theory tests, and CLI/reproducibility/timer tests. It does
**not** run the full stochastic suite below. Use `make rouse` for the simulator
alone or `make all` to build the main executables without running them. `make
check-correlator` remains CPU-only. `make check-lifetime` runs the local ownership
adapter under AddressSanitizer/LeakSanitizer; it must pass before large ensembles.

`CUDA_HOME` selects the toolkit, or set `NVCC=/path/to/nvcc`. `CXX=/path/to/g++`
also selects nvcc's host compiler. `CUDA_ARCH=sm_86` matches the validation GPU;
choose yours or omit it for nvcc's default. `UAMMD_ROOT` overrides the default
relative repository root for UAMMD headers. The KG dependency always comes from
this project's read-only sibling directory. CPPFLAGS, CXXFLAGS, NVCCFLAGS and LDLIBS are configurable;
retain C++17 and `--extended-lambda`, and do not enable fast-math for validated
precision behavior. Clean and rebuild after changing compiler/flags/header root.

`PRECISION=single` (default) uses UAMMD `real=float`; `PRECISION=double` defines
`DOUBLE_PRECISION`. Separate binaries live in `build/single/` and `build/double/`.
`make clean` removes only named executables/dependency files, preserving run data.
The previous Stage 0 smoke and correlator sources remain available unchanged.

## Running the current simulator

From the slip-springs repository root, target RTX 3060 Ti / CUDA13. Output
child directories must not exist; the executable refuses overwrites. Both short
streaming commands below were executed. The moderate command is **host-only**,
provided for external validation rather than claimed as tested in Codex.

```sh
make -C examples/slip-springs rouse CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs rouse CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
RUNS=$(mktemp -d /tmp/rouse-stage2b1-examples.XXXXXX)
examples/slip-springs/build/single/rouse --springs 8 --chains 64 --dt .005 --steps 200 --sample 10 --equil 0 --seed 620008 --output-mode stream --backend async --cpu-workers 4 --batch 7 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$RUNS/single"
examples/slip-springs/build/double/rouse --springs 8 --chains 64 --dt .005 --steps 200 --sample 10 --equil 0 --seed 620009 --output-mode stream --backend async --cpu-workers 4 --batch 7 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$RUNS/double"
ls "$RUNS/single/" "$RUNS/double/"
```

Synchronous streaming uses the same flags with `--backend sync` (the streaming
default). Historical detailed diagnostic output remains the default
`--output-mode csv`: per-chain tensor/COM/dimension samples.csv, ensemble.csv,
and metadata.json. It is useful for Stage 1/2A analysis and pipeline comparison.
For example, with the same initial state/dynamics as the single short command:

```sh
examples/slip-springs/build/single/rouse --springs 8 --chains 64 --dt .005 --steps 200 --sample 10 --equil 0 --seed 620008 --output-mode csv --output "$RUNS/csv"
python3 examples/slip-springs/tests/test_stream.py --compare "$RUNS/csv" "$RUNS/single"
```

A moderately long streaming example for the dedicated host (N32, 512 chains,
dt.005, 20000 steps, sample20, seed620032; not run in Codex):

```sh
examples/slip-springs/build/single/rouse --springs 32 --chains 512 --dt .005 --steps 20000 --sample 20 --equil 0 --seed 620032 --output-mode stream --backend sync --batch 100 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$RUNS/moderate"
python3 examples/slip-springs/stream_analysis.py "$RUNS/moderate"
```

Quick tests (bounded, no scientific campaign):

```sh
make -C examples/slip-springs check-lifetime
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
```

Full scientific regressions, terminal relaxation, sampling/buffer sensitivity,
performance and memory stability are **user-run host work**. Completed Stage 2B.1
results are recorded in [STAGE2B1_HOST_RESULTS.md](STAGE2B1_HOST_RESULTS.md).
Exact historical commands,
fixed seeds and acceptance criteria are in
[STAGE2B_VALIDATION_PLAN.md](STAGE2B_VALIDATION_PLAN.md). Do not execute these
long campaigns in Codex. Short tests cannot establish scientific acceptance.

CLI: `--springs`, `--chains`, `--dt`, `--steps`, `--equil`, `--sample`, `--seed`,
`--output` preserve their earlier meaning. Production step0 follows optional
equilibration; the RNG counter remains continuous. `--steps` counts production
steps only. `--output` defaults to build/run, must be new, and must be under this
project or outside the repository. No full bead trajectories, periodic box,
volume, checkpoint/resume or new physics are introduced. New options:

| Option | Default | Meaning |
|---|---:|---|
| `--output-mode` | csv | csv diagnostic history or compact stream |
| `--backend` | sync | sync or async; requires explicit stream mode |
| `--cpu-workers` | 1 | Async workers: 0 auto, or exact N <= chains and <= 1024 |
| `--batch` | 64 | Observation frames per bounded buffer, 1–4096 |
| `--corr-levels` | 16 | KG multi-tau level count L |
| `--corr-slots` | 16 | Slots p per level; divisible by m |
| `--corr-m` | 2 | Consecutive samples averaged per next-level sample |
| `--correlator-mib` | 512 | Estimated CPU correlator allocation budget |

Streaming observes step0 and exact multiples of `--sample`. It advances any
remaining MD steps without adding an irregular observation; metadata records
`unsampled_final_steps`. CSV retains its historical shorter final sample.
Partial batches are drained, including a zero-step run's one initial frame.
Empty bins are omitted. One chain is supported, but its SE is NaN/undefined.

## Streaming estimator and outputs

Each chain has its own unmodified KG Correlator6, fed in order with RAW
xy,xz,yz,xx-yy,xx-zz,yy-zz stresses. GPU double reductions read unwrapped stored
coordinates and transfer only six doubles per chain/frame. No bead history or
full stress trajectory is retained. No cross-chain stress products are formed.

`relaxation.csv` columns:

- `lag_samples`, `lag_time`: observation lag and physical lag in tau_0;
- `block_samples`: width of stress block means, 1 at the exact finest level;
- `g`, `g_se`: G/(n_ch*kBT), and standard error across independent chains;
- `Cxy,Cxz,Cyz,Cxx_yy,Cxx_zz,Cyy_zz`: six raw per-chain correlations averaged
  over chains; normal differences have **not** been divided by four;
- `pairs_per_chain,pairs_total`: raw products contributing to this bin (the
  latter includes all chains, but is not an independent statistical sample size);
- the six matching `C..._se` columns: independent-chain SE for each channel.

The combined estimator is `g=(Cxy+Cxz+Cyz)/5+(Cxx_yy+Cxx_zz+Cyy_zz)/30`.
It is computed within each chain before estimating its SE, preserving channel
covariance. Initial continuous-equilibrium g(0)=N. No fictitious volume or density
is supplied. Multiply by an explicitly chosen n_ch*kBT only when appropriate.
Stage 2A normal-difference products divided by four must not receive the raw
1/30 weight. Overlapping origins are averaged within each independent chain.

`metadata.json` records effective precision-rounded dt, seed/hardware, physical
parameters, sample count/stride, backend/batch, multi-tau parameters, estimated
correlator and buffer memory, and measured timing. Coordinate-resolution
indicators remain available in CSV mode; streaming records them as null with
`coordinate_diagnostics_available=false`, avoiding extra full observations.
`stream_analysis.py DIRECTORY` adds stream_analysis.json with chain-cluster
95% intervals, 5-SE gates and exact origin-dependent EM and continuous **block**
references. `--terminal` adds coverage/resolved-signal checks. This script
analyzes compact data and does not launch simulations.

The unchanged KG class averages m samples recursively. Coarse bins correlate
stress **block means**, not exact point samples. Its evaluate() exports finest
bins then levels k<kmax, omitting the deepest level reached. Configure extra
levels for the intended lag range; trust emitted lags/counts, not nominal span.
The adapter rejects nonfinite stress and xy<=-1e10 because KG uses a sentinel.
Counts/lag configuration are checked against integer/double representation limits.

## Streaming ownership, memory and thread model

`stream_correlator.h` privately derives an owning, noncopyable/nonmovable adapter.
It stages allocations safely before publishing ownership, frees only leaked row
arrays in its destructor, and lets KG destructors release tables/scalars.
Original add/initialize/evaluate calculations remain linked read-only.

Sync uses one device/pinned buffer and correlates on the main thread. Async uses
two buffers and N dedicated CPU workers. The existing consumer is worker 0;
N−1 persistent helpers process fixed contiguous ranges `[C*i/N,C*(i+1)/N)`.
No dispatcher is added. All workers read the same pinned batch without copying.
A condition-variable generation and completion counter release the slot only
after every range completes, including on failure. Each range sees frames in
chronological order; final evaluation still reduces chains in ascending order. CUDA producer events precede copies
on a nonblocking transfer stream; completion events precede CPU access. Slot
states free/filling/queued/processing and a condition variable impose bounded
backpressure and chronological consumption. No correlator has simultaneous
writers; finish drains and joins before evaluation. Consumer exceptions reach
the producer, and error cleanup waits for pending work before releasing buffers.
The existing per-observation integration stop-event synchronization is retained;
CPU processing and D2H can overlap later integration, but launch-ahead is bounded
by these waits. There is no new global device synchronization in production.

On LP64 each correlator uses approximately `184*L*p+160*L+sizeof(adapter)` bytes,
plus its bank pointer and allocator overhead: O(chains*L*p), independent of run
length. Default L16,p16 is about 50 KiB/chain. Each slot uses
`48*chains*batch` bytes on device AND pinned host memory. Sync has one slot,
async two; their combined device/pinned bytes are limited to 512 MiB. Timing
events scale as O(slots*batch), compact curve statistics as O(L*p). Default CPU
correlator budget is 512 MiB; it excludes allocator overhead/events/buffers.
GPU coordinates/RNG identities remain O(total beads). Event intervals can include
host submission gaps. These are estimates,
not guarantees of available memory; allocation failures propagate safely.

`--cpu-workers 1` preserves the serial reference; both backend and worker defaults
remain unchanged. Explicit N>1 requires async streaming and is rejected before
output creation if N exceeds chain count or 1024. Explicit N may oversubscribe
available CPUs by user choice. Zero selects min(chains, available CPUs, 1024),
or one for synchronous streaming; CSV has zero effective correlation workers
and accepts 0/1. Requested/effective counts are stored in metadata.

On Linux, automatic selection reads the calling thread's dynamic affinity mask
(including cpusets), then applies integer CPU budgets from cgroup v2 `cpu.max`
or v1 CPU quotas at standard mounts and ancestors. Fractional quotas round down
with a minimum of one. Custom cgroup mounts/unreadable restrictions may be missed;
elsewhere or when affinity fails, `std::thread::hardware_concurrency()` falls
back to one if unknown. This is a resource bound, not a physical-core or hybrid-CPU
performance model. No pinning, Intel APIs or OpenMP dependency is introduced.

Worker memory adds O(N) thread handles, counters and OS thread stacks; correlator
and device/pinned allocations do not multiply with N. The queue remains two
slots. Pool construction failure joins all started helpers; worker exceptions
wait for all ranges before rethrowing to the consumer and producer. Failed banks
are not evaluated. Helpers stop before the bank is destroyed. Repeated pool
creation/destruction and failures are covered by CPU leak tests.

`cpu_correlation_seconds` retains its outer batch-processing wall scope;
`cpu_correlation_wall_seconds` times pool calls (dispatch through completion).
Both are sums of nonoverlapping batch wall intervals and exclude transfer waits.
`cpu_worker_execution_sum_seconds` sums per-range execution intervals across all
workers and can exceed elapsed time; it excludes dispatch and barrier waits.
`cpu_worker_barrier_wait_seconds` measures only worker 0's wait for helper
completion, inside the correlation wall timer. `cpu_consumer_idle_seconds` is
worker 0 waiting for queued batches, excluding D2H completion waits (reported
separately). Helpers' idle waits are not instrumented. Buffer waits measure the
producer waiting for a free slot. These timers overlap GPU/D2H and each other;
never add them to obtain production wall time. Existing GPU throughput, final
output and production scopes are unchanged. Overall ns/bead/step remains primary.

See [STAGE2B1_REPORT.md](STAGE2B1_REPORT.md) for implementation evidence and
[STAGE2B1_VALIDATION_PLAN.md](STAGE2B1_VALIDATION_PLAN.md) for exact host commands,
including the 4096-chain sweep at 1/2/4/8/12/16 workers and memory checks.

Sync remains default. Async streaming with 16 workers and batch128 is accepted
for the tested development-host workload; benchmark other hosts separately.

## RNG and precision

The local kernel uses CUDA cuRAND **Philox4x32-10** with the explicit 64-bit seed.
Each logical bead owns a subsequence; eight 32-bit draws are reserved per unsigned
64-bit timestep. Initialization bonds and independent Gaussian chain translations
use disjoint subsequence domains. Immutable IDs, not launch/storage indices,
key the RNG. Topology is fixed chain-contiguous; sorting/reordering requires
remapping neighbors while retaining IDs and is not supported by this executable.

Float builds call `curand_normal4` (float Gaussian math). Double builds call
`curand_normal2_double` twice: 53-bit uniform construction and double
Box–Muller/transcendentals, rather than casting float Gaussians. Only xyz are
used. Both are finite-precision pseudorandom approximations, with finite tails;
reproducibility is for the same executable/toolkit/device, not across platforms
or precisions. No claim of cryptographic randomness or exhaustive RNG testing.

Reject equilibration+production >floor(UINT64_MAX/8); never reset/wrap that
counter to extend a run. Restarting this executable with the same seed starts
again from the same initial ensemble. A future checkpoint feature must preserve
absolute steps/IDs. There are no persistent per-bead RNG states.

Bonds are sampled independently with each component variance1/3 and accumulated
in the selected precision. No dynamic equilibration is required to obtain the
initial continuous-time equilibrium distribution. Euler–Maruyama subsequently
introduces stationary variance bias. Analysis uses exact transient finite-step
mode covariance as well as continuous theory; this bias is not a precision bug.
Unwrapped COM coordinates grow without bound, eventually losing small increments
and bond differences. Metadata records max coordinate spacing/sqrt(2dt) and
collapsed sampled bonds; these diagnostics certify only the sampled range.
No recentering or mixed-precision coordinates are implemented.

## Full scientific validation

Acceptance thresholds, seeds and uncertainty definitions are in
[tests/VALIDATION_PLAN.md](tests/VALIDATION_PLAN.md), set before execution.
Run this historical Stage 1 campaign **only on the user GPU host**, after both
precision builds; never in Codex:

```sh
python3 examples/slip-springs/validate.py suite /tmp/rouse-validation-new
```

The new output directory contains per-run CSVs/metadata, logs and `summary.json`.
The suite executes N=8,32,100 initialization checks (8192 chains), then three
timesteps 0.01/0.005/0.0025 and both precisions (512 chains). Each trajectory
covers at least 1.25 exact slowest relaxation times. It also compares the two
precisions statistically and records one separate small timing probe per build.
Exit zero requires every predeclared scientific gate; runtime failure never
counts as a pass. It is a scientific campaign and is excluded from Codex runs.

## Configurational stress and exact references

At each requested observation the existing GPU pass accumulates
`S_ab=3 sum_i q_ia*q_ib` from unwrapped stored bonds in double precision, even
when coordinates use float. Only chain observables are copied to the CPU.
There is no simulation volume, kinetic stress or density prefactor.

`stress.py` preserves xy,xz,yz,xx-yy,xx-zz,yy-zz separately. Shear products are
unchanged; normal-difference products carry1/4. It computes uncentered direct
products at matching chain IDs and multiple time origins, then chain-level SE.
Raw diagonal autocorrelations include the mean-stress product; they are not
compared to a zero-mean shear formula. There is no mean subtraction or channel
averaging. The three normal differences are linearly dependent.

Continuous equilibrium shear correlation is sum_p exp(-2 lambda_p*t).
For EM, with a_p=1-lambda_p*dt and per-coordinate mode variance v_p(n), use
`mean_origins(sum_p (lambda_p*v_p(n)*a_p^lag)^2)`. The square is taken BEFORE
the origin average. Evolved zero-lag moments reflect EM bias, whereas initial
moments are N for shears and4N for raw normal differences. Default direct lags
are0,1,4,16,32 sample intervals; unavailable lags are skipped. Short examples
are demonstrations, not replacements for the full predeclared validation suite.

## Permanent performance reporting

Every successful simulation prints counts, physical time and measured rates,
including zero-step initialization runs. Metadata timing_schema_version2 uses:

- update_seconds: summed CUDA-event intervals for production integration only.
  Includes host launch gaps between recorded events; excludes sampling and host
  synchronization wait. GPU event timing is not the sum of isolated kernel times.
- production_seconds (wall_seconds alias): wall interval containing the initial
  sample, all production updates/synchronization, sampling/D2H and recurrent
  CSV formatting/writing or streaming worker drain. Excludes initialization,
  optional equilibration and final evaluation/output.
- sampling_seconds: CSV mode uses blocking observation/D2H wall time. Streaming
  uses sampling_gpu_seconds+transfer_seconds (CUDA-event sums), which can overlap
  integration. Never add these to production_seconds.
- recurrent_output_seconds: in-loop CSV formatting/writing (also part of production).
- final_output_seconds: final CSV flush/close or streaming evaluation/reduction
  and compact-file writing, measured after production ends.
  output_seconds is recurrent_output_seconds+final_output_seconds.
- initialization_seconds: System/CUDA context creation, allocation, weights,
  Gaussian conformation initialization and output setup. Context time is also
  separately available. Equilibration wall/GPU times have separate fields.
- integration_ns_per_bead_step=1e9*update_seconds/(total_beads*production_steps).
  overall_ns_per_bead_step uses production_seconds with the same denominator.
  bead_updates_per_second uses the inverse measured update time. All three are
  JSON null and terminal N/A for zero production steps, including runs with
  nonzero optional equilibration.

All duration fields are seconds; rates are labeled explicitly. Metadata
serialization/closing, terminal logging and final System shutdown are telemetry
or teardown outside these intervals. File timers measure buffered OS I/O, not
fsync-to-device durability. Timer scope intentionally differs from historical
Stage 1 schema1, which included equilibration and final flushing in broader sums.

Additional streaming fields separate sampling_gpu_seconds, sampling_enqueue_seconds,
transfer_seconds, transfer_wait_seconds, buffer_wait_seconds and
cpu_correlation_seconds. Worker processing and GPU times overlap in async mode;
production_seconds is the actual critical-path wall time, including final drain.
measured_simulation_seconds is a wall timer from context setup through final
output; it excludes metadata serialization, terminal logging and teardown.

## Roadmap

Stages 0, 1 and 2A have recorded scientific validation. Stage 2B passed the
user-reported 54-simulation matrix and N32 terminal 504/504 checks. Stage 2B.1
is accepted on the development host; see
[STAGE2B1_HOST_RESULTS.md](STAGE2B1_HOST_RESULTS.md). Further optimization is not
required before N100 terminal-relaxation experiments. Stage 3 optimization,
semiflexibility and slip-spring physics remain future unauthorized work.
