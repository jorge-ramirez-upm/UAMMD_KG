# Stage 2B — streaming stress relaxation modulus

**STAGE 2B COMPLETE — STREAMING STRESS RELAXATION VALIDATED**

Closure recorded 16 October 2026. Evidence includes the existing Stage 1/2A
regressions, user-reported full 54-simulation matrix and N32 terminal 504/504
checks, accepted Stage 2B.1 parallel processing, million-step memory stability
(728/728 checks), and N100 terminal relaxation (686/686 checks). See
[STAGE2B1_HOST_RESULTS.md](STAGE2B1_HOST_RESULTS.md) and the permanent
[N100 results and artifact archive](STAGE2B_N100_TERMINAL_RESULTS.md).
The host experiments were user-executed; Codex recorded the supplied evidence
and inspected accessible artifacts without independently running/authenticating
the measurements. Closure validates the independent Rouse reference and stress
pipeline; slip-spring physics is unimplemented and unvalidated. Stage 3 remains
unauthorized. See [NEXT_STAGE_ASSESSMENT.md](NEXT_STAGE_ASSESSMENT.md).

The implementation, architecture, short-test and timing record below is
historical (15 October 2026); subsequent acceptance supersedes its original gate.

## Provenance and isolation

Fetched origin/slip-springs and independently verified its remote HEAD before
changes: **46795f34b6637dfeb77b9c8a1c9ffe46b3b6d008**. This matches the supplied
last-known commit. Work continued on slip-springs in /tmp/UAMMD_KG-slip-springs.
The final SHA and push result are supplied in the handoff; a commit cannot
contain its own SHA. No PR, merge, history overwrite or force push is requested.

Modified: AGENTS.md, Makefile, README.md, rouse.cu.
Created: stream_correlator.h, stream_pipeline.cuh, stream_analysis.py,
STAGE2B_REPORT.md, STAGE2B_VALIDATION_PLAN.md, tests/stream_lifetime.cpp,
tests/pipeline_tests.cu, tests/test_stream.py, tests/test_stream_theory.py,
tests/stage2b_compare.py. All fourteen paths are under examples/slip-springs/.
Existing physics kernels, historical reports and tests are unchanged. The
Makefile adds the new checks while retaining every earlier regression; the KG
header/implementation are consistently selected from the local read-only sibling
even when UAMMD_ROOT overrides core header paths.

The original checkout remains on KremerGrest with its pre-existing modified
examples/KG/Makefile and untracked examples/KG/Stars_TEST/ preserved. KG/UAMMD
are read-only dependencies; no other existing example is rebuilt. The final
programmatic audit checks tracked differences against this starting SHA and
Stage 0's source 81fe5de9cd5ded849202eebab7c14e6bd35fb9ae, untracked files and
ignored generated files. Build products stay in the project's ignored build/;
short run data/logs stay outside the repository under /tmp.

## Implemented pipeline and normalization

The historical CLI defaults to detailed CSV, retaining conformation, COM,
end-to-end, mode and tensor observations, including the shorter final sampling
interval. Explicit --output-mode stream selects compact correlation output;
--backend sync|async, --batch frames and --corr-levels/slots/m configure it.
Defaults: sync,64 frames,L16,p16,m2. The adapter is built with the original KG
correlator.cpp, without copying or changing its computational implementation.

A GPU kernel reduces the six stresses per chain in double from stored unwrapped
coordinates. It sends xy,xz,yz,xx-yy,xx-zz,yy-zz, with RAW normal differences, to
one independent correlator per chain. It transfers no bead history. Equilibration
uses the unchanged RNG sequence; observation index0 follows equilibration.
Streaming feeds only evenly spaced samples at production steps0,sample,2*sample,
etc. Remaining final integration steps are advanced but not correlated. Metadata
records the number of frames and unsampled trailing steps. Final partial batches
and zero-step runs are supported. Empty bins are omitted.

    g = G/(n_ch*kBT) = sum(3 shear correlations)/5
                      + sum(3 RAW normal-difference correlations)/30.

There is no volume or extra chain-count factor. Correlations are formed within
each chain before ensemble averaging. For each lag, g is combined within each
chain before Welford accumulation across chains, preserving channel covariance.
The output includes six raw means and SEs, g/g_se, physical/sample lag, stress
block width, pairs_per_chain and pairs_total. These counts are not independent
sample sizes. SEs use independent chains, not overlapping origins; a single
chain yields undefined/NaN SE. Compact sufficient statistics use O(L*p) storage.

Sync uses one device/page-locked buffer; the main thread waits for the transfer
and processes its batch. Async uses two slots, a nonblocking transfer stream and
one CPU consumer. A producer-ready event orders each batch after its GPU stress
writes; a copy-complete event orders CPU access. Mutex/CV slot states and cyclic
producer/consumer indices preserve chronological order and bounded backpressure.
A slot stays unavailable until CPU processing completes. The consumer alone
modifies correlators; evaluation runs on main only after drain/join. Exceptions
propagate to main, which joins and waits for pending CUDA work before cleanup.
No unbounded queue or trajectory-sized stress allocation is used.

The existing integration stop-event synchronization per observation chunk is
retained. Transfer/CPU work can overlap later integration; no new production
cudaDeviceSynchronize is added. End-of-run/destructor waits protect pending work.
No kernel optimization or speculative concurrency beyond this pipeline is added.

## Ownership repair and memory

The local final adapter privately inherits Correlator6, forbids copying/moving
and exposes only needed computational/readout methods. It stages all allocations
with unique_ptr before publishing numcorrelators, so bad_alloc cannot expose
partially initialized base ownership. Its destructor frees twelve double-array
rows and unsigned-long count rows. Original destructors subsequently free the
pointer tables, accumulators, cursors and flattened output arrays exactly once.
Inherited resizing, checkpointing, shallow copying and base deletion are hidden.
The KG add/initialize/evaluate routines are reused verbatim through linkage.
The raw KG classes retain their original leak; every new runtime correlator uses
the local ownership adapter.

On LP64 per-chain storage is approximately 184*L*p+160*L+sizeof(adapter), plus
a bank pointer and allocator overhead. Default storage here is49,968 bytes/chain
including its bank pointer (about48.8 KiB), or about48.8 MiB for1024 chains.
--correlator-mib defaults512 and bounds the estimated bank allocation. Allocation
failures propagate; estimates exclude allocator overhead and CUDA events.
Each slot has 48*chains*batch device bytes AND the same pinned-host bytes;
sync has1 slot and async2. Combined device+pinned buffer allocations are capped
at512 MiB. Events use O(slots*batch), coordinates/IDs O(total beads), and neither
correlators nor buffers grow with simulated duration.

The unchanged sentinel requires xy>-1e10 and finite channels. The adapter
validates each sample. Count overflow and lag representation constraints are
checked before a run. KG exports finest lags and coarse levels k<kmax, omitting
the deepest reached level. This remains unchanged and is documented; an extra
allocated level may be needed. Coarse bins correlate stress block means.

## Exact references

The continuous point reference is sum_p exp(-2*lambda_p*t), with the exact
finite-N rates lambda_p=12 sin^2(p*pi/(2*(N+1))). At lag0 it is N.
For EM, a_p=1-lambda_p*dt, v*=1/[lambda_p*(1-lambda_p*dt/2)], and
v(n)=v*+(1/lambda_p-v*)a_p^(2n). At a fine lag ell the reference averages
sum_p [lambda_p*v_p(n)*a_p^ell]^2 over actual origins.

For block width B, let the earlier block start at observation rB, its offset
u, the later block start at rB+lag_samples, its offset v. With production stride
s, n=equil+s(rB+u), gap=s(lag_samples+v-u). The reference averages
sum_p lambda_p^2*v_p(n)^2*a_p^(2*gap) over r,u,v, using only completed blocks.
The implementation expands v(n)^2 into three terms and performs the finite
geometric sums analytically in O(N) time/storage per bin. It never squares an
origin-averaged covariance. Continuous theory is averaged over the same block
windows. The closed form was compared with independently enumerated Wick sums
for N8,32,100 and N1, three requested dt values, equil0/17, several lags and
block widths1,2,3,4. Very large block arithmetic is checked without long histories.

## Passed short tests

Environment: NVIDIA GeForce RTX3060 Ti, sm86,8192 MiB; driver580.178.04;
CUDA13.0 nvcc13.0.88; GNU g++11.4.0; C++17, -O2, no fast-math. Both precisions
build successfully. Rouse/RNG math is unchanged: float uses curand_normal4;
double uses curand_normal2_double. Stress/correlation arithmetic uses double
in both builds. Double coordinates do not imply matching float/double paths.

Commands run, with no full scientific suite:

```sh
make -C examples/slip-springs check-lifetime
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
/usr/local/cuda/compute-sanitizer/compute-sanitizer --tool memcheck --error-exitcode 99 examples/slip-springs/build/single/pipeline_tests
/usr/local/cuda/compute-sanitizer/compute-sanitizer --tool memcheck --error-exitcode 99 examples/slip-springs/build/double/pipeline_tests
```

| Short check | Result |
|---|---|
| CPU adapter200 create/add/evaluate/destroy cycles, ASan/UBSan/LSan | PASS; no leak or invalid access |
| Stage0 CUDA and functional Correlator6 smoke | PASS |
| Existing Stage1 forces/update/RNG and Stage2A GPU stress unit tests | PASS, both precisions |
| Existing CPU theory4, stress4 and CLI3 tests | PASS, both builds |
| New exact block-reference tests2 | PASS (explicit Wick sums, large bins) |
| New sync/async CPU-consumer failure cleanup | PASS, both precisions |
| CUDA memcheck consumer-error cases | PASS;0 errors, both precisions |
| Six bounded pipeline scenarios per precision | PASS |
| Independent CSV reconstruction of six channels, g, paired SE, lags/counts/block widths | PASS; rtol=atol=2e-11 |
| Sync/async and batch1/39/40 identical-workload files | Byte-identical |
| Eight invalid-input/memory/lag guards | PASS, before output creation |
| Host plan shell-block syntax | PASS; campaigns not executed |

Pipeline scenarios include N1, initial-only/zero/equilibrated runs, one chain
(undefined SE), partial final batches, irregular final integration intervals,
full batches, multiple levels and m3 coarsening. No repeated validation campaign
of KG's correlation algorithm was undertaken.

The sandbox's ptrace restriction initially prevented LSan inspection; running
the same small test outside that restriction passed without suppressions.
The PATH compute-sanitizer could not locate its injection library; using the
complete /usr/local/cuda/compute-sanitizer installation passed. An initial
negative fixture mistakenly expected a representable lag configuration to fail;
the fixture was corrected to exceed the pre-existing exact-lag limit. No
scientific tolerance was changed; final short checks all pass.

The final prefix audit passed for tracked changes against both recorded bases,
all ten new files, and all ignored generated paths. No outside path changed.
Final logs: /tmp/stage2b-check-{single,double}-final.log,
/tmp/stage2b-lifetime-final.log,
/tmp/stage2b-memcheck-{single,double}.log. Short example artifacts:
/tmp/rouse-stage2b-examples.mpc7ktyl; its path is also saved in
/tmp/stage2b-example-root.txt. These are generated artifacts, not bulk committed
data. The README commands reproduce the examples in fresh directories.

## Short example results and timing

All probes below: N8,C64,576 beads,dt.005,200 production steps,physical time1,
sample10,equil0; streaming L16,p16,m2,batch7,21 processed frames. Single CSV,
sync and async seed620008; double async seed620009. Runs were sequential.
Each denominator is115,200 bead updates. These submillisecond/millisecond
production intervals are illustrations, not performance benchmarks.

| Precision/mode | Integration s | Integration ns/bead/step | Production s | Overall ns/bead/step | Total measured s | Final data s |
|---|---:|---:|---:|---:|---:|---:|
| single CSV | .000455520 | 3.9542 | .007185733 | 62.3762 | .139611422 | .000016542 |
| single sync | .000455680 | 3.9556 | .000855670 | 7.4277 | .124182343 | .000126065 |
| single async | .000489472 | 4.2489 | .000869786 | 7.5502 | .211313550 | .000139617 |
| double async | .003188672 | 27.6794 | .003572197 | 31.0087 | .148870406 | .000145432 |

Single sync: sampling-GPU .000120128s,D2H .000016736s,CPU correlations .000140039s,
free-buffer wait .000000143s,transfer wait .000038733s; throughput252.81M updates/s.
Single async: sampling-GPU .000143232s,D2H .000017280s,CPU correlations .000148576s,
free-buffer wait .000000115s,transfer wait .000008629s; throughput235.36M updates/s.
Double async: sampling-GPU .000137280s,D2H .000009440s,CPU correlations .000166014s,
free-buffer wait .000000134s,transfer wait .000007997s; throughput36.13M updates/s.
All are measured timers. GPU intervals include submission gaps; CPU worker,
transfer and integration intervals overlap and must not be summed as wall time.

Bank estimate3,197,952 bytes for64 chains. Async device/pinned buffers43,008 bytes
each; sync21,504 each. cudaMemGetInfo delta was4,194,304 bytes per run, reflecting
allocation granularity/cache/context effects in addition to explicit arrays.
Tiny workload async cost did not improve on sync; sync remains default.
Representative-host measurements are required before selecting async for long runs.

As a limited end-to-end science smoke, the existing Stage2A analyzer passed71
available gates on this tiny CSV, and streaming exact-reference analysis passed98
available5-SE checks in each precision. This does not cover terminal decay,
long-run memory, N32/100 scientific dynamics, timestep convergence or production
performance. Zero-lag g (averaged over21 origins):

| Build | g(0) | Chain-cluster SE | Exact transient EM | Continuous |
|---|---:|---:|---:|---:|
| float | 8.5067271691 | .4277497072 | 8.2232733860 | 8 |
| double | 8.0832231324 | .3751747830 | 8.2232733915 | 8 |

## Closed scientific acceptance and remaining limitations

Stage 2B is complete on the recorded evidence above. Original host commands and
fixed criteria remain in STAGE2B_VALIDATION_PLAN.md; their historical pending
status is superseded by this closure and linked results. No scientific thresholds
were changed. Production-server-specific performance requires separate benchmarks.
Large unwrapped float coordinates can still lose bond/increment resolution;
double reductions cannot recover lost coordinate bits. Streaming does not collect
coordinate diagnostics; use the preserved CSV mode for targeted checks.

The validated system is the Gaussian Rouse reference, with no slip-spring model.
No Stage 3 implementation or new physics is authorized by this closure.

Short copy-and-paste runs, from the repository root (after building as above):

```sh
RUNS=$(mktemp -d /tmp/rouse-stage2b-examples.XXXXXX)
examples/slip-springs/build/single/rouse --springs 8 --chains 64 --dt .005 --steps 200 --sample 10 --equil 0 --seed 620008 --output-mode stream --backend async --batch 7 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$RUNS/single"
examples/slip-springs/build/double/rouse --springs 8 --chains 64 --dt .005 --steps 200 --sample 10 --equil 0 --seed 620009 --output-mode stream --backend async --batch 7 --corr-levels 16 --corr-slots 16 --corr-m 2 --output "$RUNS/double"
```
