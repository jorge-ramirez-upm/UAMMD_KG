# Stage 4A.3c — every-step performance and scientific capacity audit

This is a prospective audit using the user-provided `cholosimeone` bounded
result. It does not change scientific thresholds, launch a campaign, or claim
that Milestone B is scientifically accepted.

## Timer meanings and the reported N8 result

| Field | Meaning | Critical-path interpretation |
| --- | --- | --- |
| `gpu_stress_seconds` | CUDA-event elapsed from stress-kernel sequence start through channel production | GPU work scope; not additive with wall time |
| `stress_transfer_seconds` | Sum of D2H copy-stream event intervals | DMA interval; may overlap GPU/CPU work |
| `stress_transfer_completion_wait_seconds` | Consumer wall wait for a copy-done event | May include copy-stream queuing plus DMA; not an extra cost to add |
| `stress_diagnostic_wait_seconds` | Event/key synchronization and mandatory diagnostic readbacks | Producer-visible synchronization; overlaps kernel scopes |
| `cpu_correlation_seconds` | Persistent chain-major worker-pool elapsed time | Per-batch consumer work; may overlap producer work |
| `cpu_barrier_seconds` | Worker-0 wait at the worker-pool barrier | Strict subset of CPU correlation time |
| `cpu_worker_execution_sum_seconds` | Sum across workers | CPU work, not elapsed time |
| `buffer_wait_seconds` | All producer slot-acquisition elapsed time | Includes uncontended lock/check cost |
| `producer_blocked_seconds` | Subset of slot acquisition that began with its slot non-free | Actual producer backpressure delay |
| `production_wall_seconds` | Simulator production wall time | The only end-to-end elapsed time; never sum the other scopes |

The prior `0.493 s` “producer waiting” was the old broad acquisition scope. It
can contain uncontended ownership checks and must not be interpreted directly as
critical delay. `producer_blocked_seconds` is the corrected backpressure measure.
Likewise `1.068 s` diagnostic waiting is synchronized work already represented
in GPU/event timing, not a second wall-time contribution. The reported GPU
stress1.515s and CPU correlation2.193s overlap by design; their sum is not
comparable with the2.381s wall time.

Two slots reached maximum occupancy2, proving the fixture exercised the bounded
handoff. It does not prove a sustained steady state: only10,001 frames and one
N8,κ10 case were observed. The two-slot/256-frame design is therefore adequate
for bounded lossless operation, but not yet justified as a production throughput
choice. Do not add slots merely to hide a positive `producer_blocked_seconds`.

## Same-host protocol

Run the following only on `cholosimeone`; it builds both precisions, repeats
each bounded case three times, and writes all evidence to a fresh `/tmp` root:

```sh
cd /tmp/UAMMD_KG-slip-springs-dev
CUDA_HOME=/usr/local/cuda-13.0 CXX=g++ CUDA_ARCH=sm_86 \
  bash examples/slip-springs/tests/run_stage4a3c_performance_audit.sh
```

It compares N8/N32,κ0/κ10,single/double with C=2048, workers8, batch256 and
two same-memory-budget hierarchy candidates:64 slots×20 levels and32×24. The
isolated CPU chain-major runs use exactly C, slots, levels, workers and batch
settings. `gpu-summary.csv`, per-run metadata and CPU JSON records provide
producer/consumer rates, queue occupancy, blocked time and wall time. The
2000-step fixture is performance evidence only, never relaxation science.

## Multi-tau coverage

Every-step spacing is `dt=0.000025`. With `p` slots, `L` levels and coarsening2,
the nominal deepest lag is `(p−1)2^(L−1)dt`; usable lag also requires at least
16 complete block origins. Run the reproducible arithmetic with:

```sh
python3 examples/slip-springs/tests/stage4a3c_capacity_audit.py --frames 8000001 --slots 64 --levels 21
python3 examples/slip-springs/tests/stage4a3c_capacity_audit.py --frames 160000001 --slots 32 --levels 24
```

The documented Gaussian N8 control time is about1.382. The frozen plan supplies
no nonlinear spectrum for finite-rest-length κ0/κ10. Its only N32 planning scale
is the rigid-rod rotational estimate≈565; it is not a claimed chain relaxation
time. Consequently no finite-rest-length configuration can be declared to meet
terminal support solely from this audit.

| Candidate | Bank at C=2048 | Nominal lag | Prospective finding |
| --- | ---: | ---: | --- |
|64×12|280.34 MiB|3.2256|Validation fixture only; cannot cover N8 duration200 or terminal tails.|
|64×20|466.84 MiB|825.75|Fits512 MiB; N8 duration200 may be covered, but N32 4×565=2260 cannot.|
|64×21|490.16 MiB|1651.51|Largest 64-slot candidate within512 MiB; still incapable of 4×565 N32 planning coverage.|
|64×22|513.47 MiB|3303.01|Mathematically longer, but bank alone exceeds the declared512 MiB cap.|
|32×24|284.09 MiB|6501.17|Fits cap and can prospectively cover N32 duration4000; inspect level bin width and origins before use.|

### Minimum levels by planning target

Using the helper's exact hierarchy arithmetic (coarsening2, `dt=0.000025`),
the first level count whose *supported* maximum reaches the planning target is:

| Planning case | Target | P=16 | P=32 | P=64 |
| --- | ---: | --- | --- | --- |
| N=8 Gaussian control, 4×1.382 | 5.528 | L=15, 91.53 MiB, supported6.144,140 bins | L=14,165.97 MiB, supported6.3488,248 bins | L=13,303.66 MiB, supported6.4512,450 bins |
| N=32 rod-scale planning bound, 4×565 | 2260 | **none within the 160,000,001-frame trajectory** (16 origins fail before target) | L=23,272.28 MiB, supported2306.8672,396 bins | L=22,513.47 MiB, supported3145.728,737 bins |

The bin counts are exported lag bins through the target, not independent
statistical samples. All overlapping time-origin products remain correlated;
the effective independent cluster count is the number of chains (2048), not the
pair count. At the N=8 target, the largest bin widths are0.2048 (P16),0.1024
(P32) and0.0512 (P64), versus the Gaussian resolution criterion
`tau/4=0.3455`; all three have several admissible fine/coarse levels. P16's
coarsest0.4096 bin is1.19× that criterion, so its last one or two tail bins are
too broad even though lower levels resolve the region.

At the N=32 planning target, P16 cannot satisfy the 16-origin condition at the
level needed to reach2260: its last usable supported lag is1572.864 even with
16×40. P32×23 reaches2306.8672 with16 origins and a104.8576 bin (0.742×
`tau/4=141.25`). P64×22 reaches3145.728 with16 origins and a52.4288 bin,
but its bank alone exceeds512 MiB. P16×40 is a useful historical reference,
not a solution: at C=2048 its bank is≈243.09 MiB, but its supported N32 lag is
still1572.864 and its additional levels have zero/insufficient origins.

The exact hierarchy also shows the scientific distinction between “more levels”
and “more usable information”: levels beyond the observation window add no
supported bins, and a nominal lag with fewer than16 origins cannot satisfy the
frozen terminal gate. Multiple bins around a fitted regime must come from the
lower-level rows; a single deepest bin is not a relaxation measurement.

### Recommendation by chain length

For N=8, P=16×15 is mathematically sufficient for the documented Gaussian
4τ horizon and is the minimum-memory choice. P=32×14 is a meaningful scientific
improvement because it supplies roughly twice as many lag bins and keeps every
bin width through the target below τ/4, at only166 MiB. P=64×13 adds more bins
but costs304 MiB; throughput alone does not justify it. For nonlinear finite-
rest-length N=8, the relevant τ remains unresolved, so these are capacity
recommendations, not terminal-support acceptance.

For N=32, P=16—including historical16×40—is mathematically incapable of the
16-origin 4×565 planning target in the frozen 4,000-time trajectory. P=32×23
is the minimum cap-compatible hierarchy that reaches it and provides a usable
104.8576-time-unit coarse bin. P=64×22 improves resolution and supported tail,
but exceeds the512 MiB bank cap before integration/slab memory. Therefore P=32
is the minimum prospective N=32 choice; adequacy still requires the frozen
terminal checks after an actual nonlinear τ is established.

For the N8 frozen duration200 (8,000,001 frames), 64×21 has nominal lag196.608
and supported lag147.456, satisfying the Gaussian N8 four-time horizon but not
establishing nonlinear terminal support. For N32 (160,000,001 frames),64×21
cannot reach four rod-scale times;32×24 has nominal lag3774.8736 and supported
lag2306.8672, barely beyond4×565=2260. It can reach them only at levels whose
block width must be checked against the `tau/4` requirement. At tau=565,
`tau/4≈141.25`; the level22 width is104.8576 and is usable only if it retains
at least16 origins. The audit helper performs that exact count; nominal deepest
lag alone is insufficient.

## Memory and recommendation

At C=2048 a six-double frame is98,304 bytes. Two256-frame device slabs are48
MiB and two pinned slabs are48 MiB. These are in addition to integration state,
tensor/channel buffers, the CPU bank, worker stacks and output/moment vectors.
The reported377 MiB estimate is configuration-specific and should not be used as
a cap. Orientation banks are not included; reserve their memory separately in a
future authorized milestone.

No production configuration is justified yet. Use64×20 for bounded throughput
comparison only, and evaluate32×24 as the only currently cap-compatible N32
long-lag candidate. Select actual levels only after host measurements and the
frozen terminal-support analysis establish a relevant nonlinear time and its
bin/origin support.
