# CPU orientation correlator adapter: implementation and bounded validation

18 October 2026, Europe/Madrid. Starting local/fetched `origin/slip-springs`:
`9e466194c108f2c19a613739875eaf7a72e68959`. Work is isolated in
`/tmp/UAMMD_KG-slip-springs-dev`. The campaign execution checkout and existing
scientific executables were preserved at their original paths and identities.
No CUDA source, simulator dynamics/RNG, correlator mathematics, execution manager,
frozen plan/manifest/threshold, campaign input/output or old test changed.
No GPU work or scientific trajectory was executed.

**Outcome:** the isolated CPU adapter passes the specified direct-reference,
normalization, chain-uncertainty, ownership and sanitizer checks. It provides a
tested serial baseline for a later GPU acquisition benchmark, not an integrated
GPU observable or Stage4A.3c scientific acceptance.

## Implementation and API

[orientation_correlator.h](orientation_correlator.h) includes the existing
`stream_correlator.h` for shared parameter validation and the read-only KG
declarations. It does not instantiate the stress bank, CUDA or worker classes.
`OwnedVector` privately inherits `VectorCorrelator`, with staged unique ownership
of all allocations. The published KG level count stays0 until all arrays/tables
exist, making base destruction safe on allocation failure. The local destructor
frees the per-level rows missing from stock teardown; stock destructors free
tables, accumulators, cursors and outputs. Copy and move are deleted.

KG `VectorCorrelator::add`, `initialize`, `clear` and `Correlator::evaluate`
remain unchanged. This preserves complete nonoverlapping block means, incomplete
terminal block truncation, origin counts and deepest-populated-level omission.
No new numerical correlation algorithm or shared-KG modification was introduced.
The low-level owner's generic Vector inputs are checked for finiteness and the
stock sentinel; the high-level orientation bank supplies bounded unit/features.

`orientation::Bank` stores one C1 owner and optionally two C2 owners per chain.
For each complete frame, it validates the supplied integer step and chain count,
then normalizes **all** vectors before updating any chain. A bad vector reports
its step/chain, leaves frames/correlations unchanged, and is not silently skipped.
The next valid observation must still have the original expected step. Zero and
nonfinite vectors fail explicitly. Max-component scaling permits finite vectors
whose naive norm would overflow, and subnormal nonzero vectors, without a cutoff.

Given unit u, C1 receives u directly. The five features from the accepted proposal
are formed instantaneously; owners receive(f1,f2,f3) and(f4,f5,0). Their outputs
are summed **within each chain**, before Welford ensemble mean/variance. C2 is
never obtained by squaring C1. No empirical mean subtraction, coarse-vector/
feature renormalization, stress weights, temperature or density factors appear.

The API is an in-memory CPU numerical interface, with no file writer or GPU
coupling. Example (link unchanged `../KG/correlator.cpp`):

```cpp
#include "orientation_correlator.h"
int main() {
  orientation::Bank bank(2, {20,32,2}, {0,100,0.0001}, true);
  bank.observe(0,   {{{1,0,0}}, {{0,1,0}}});
  bank.observe(100, {{{0,1,0}}, {{0,0,1}}});
  auto result = bank.evaluate();
}
// result.metadata: parameters, explicit clock, chains, ranks, frames, last step.
// Each bin: lag_samples, lag_steps, block_samples, lag_time, block_duration,
// origins_per_chain, independent_chains, c1 and optional c2 estimates.
```

The clock is{first_step,stride,dt}; expected step is first_step+frame*stride.
Zero stride, nonpositive/nonfinite/unrepresentable spacing, incompatible lag
range, integer overflow, missing/duplicate/reordered steps and wrong chain counts
fail. Physical lag is lag_steps*dt; delivery/wall time is absent from acquisition.
`evaluate()` may be called repeatedly without changing accumulated samples.
An empty bank has metadata and no bins.

SE is sample sd across chain estimators divided by sqrt(C), with variance
denominator C-1. For C1-only mode C2 is absent; for C=1 each SE is `std::nullopt`,
not zero or a claim of independent time origins. Origin counts, block widths,
chain counts and rank grids are checked consistently across owners. Coarse
outputs retain their block-averaged interpretation. Lag bins and origins are
not advertised as independent statistical units.
Chain identities are the fixed input-vector indices. Stable chain ordering and
physical independence are caller obligations; the adapter cannot infer either
from numerical vectors alone. Prescribed fixtures validate the estimator, not
a claim that their deterministic sequences are physical independent replicas.

## Deterministic numerical checks

[tests/orientation_cpu.cpp](tests/orientation_cpu.cpp) independently normalizes
prescribed inputs with long-double norms. For each exported lag/block it directly
sums all within-block time-offset pairs of u dot v and scalar P2(u dot v), then
forms independent per-chain means and SE. The oracle does **not** call the
feature function for its C2 expectation. Comparison uses the prespecified
absolute3e-11 plus relative3e-11 tolerance, with no threshold changes.

Both ordinary and sanitized suites passed **1074 exported bins**, each checking
C1 and optional C2, available chain SE, lag, step, physical time, block width,
origins and chain counts. Maximum absolute numerical discrepancy, including
the supplementary contraction/metadata checks, was **1.33227e-15**.

Coverage includes constant directions with changing vector lengths, antiparallel,
orthogonal, periodic, icosahedral isotropic and anisotropic prescribed sequences,
plus generic nontrivial directions. The isotropic fixture separately verifies
zero first moment and identity/3 second moment. Tests span1/3/7 chains,
1–513 frames,32/64-slot20-level banks and smaller ladders, including m3;
incomplete blocks, first/last exported bins and repeated evaluation. Unblocked
C1(0)=C2(0)=1, antiparallel C1=-1/C2=1 and orthogonal C1=0/C2=-1/2 pass.

A discriminating covariance test uses three constant chain directions. The
two feature banks have opposing chain variations, while their C2 sum is1 with
zero SE within rounding. Adding the separate bank variances would give a
spurious SE≈0.4714; the adapter preserves their covariance and reports zero.
Independent scalar-Legendre comparisons separately verify the tensor identity.

Invalid final-chain vectors test frame atomicity. Zero, NaN, infinities, wrong
counts/steps, bad parameters, budget/clock/count-domain checks, maximum-double
and subnormal finite inputs pass their expected accept/reject behavior. The
low-level owner also passes100 construction/feed/evaluate/clear/destruction
cycles and rejects sentinel overlap/nonfinite pushes. Its clear behavior and
raw dot-product semantics remain those of the stock utility.

## Ownership and sanitizers

[tests/orientation_allocation_failure.cpp](tests/orientation_allocation_failure.cpp)
uses executable-local GNU linker wrappers for the real scalar/array `operator
new`. It preserves the real allocator/deallocator and sanitizer allocation tags;
there is no adapter test hook or replacement allocator in production/performance
code. Exhaustive failure at every construction allocation point passed:
**140 sites for C1-only,416 sites for combined C1+C2** (three-chain fixture).
This exercises failures in temporary pools, arrays, tables, container storage,
and later owners/chains after earlier allocations have succeeded.

ASan+UBSan with LeakSanitizer enabled passed both the complete numerical/lifetime
suite and both failure sweeps. Options were `detect_leaks=1:halt_on_error=1` and
`halt_on_error=1:print_stacktrace=1`; no suppression or threshold relaxation was
used. An initial sandbox run could not perform LSan thread inspection under
ptrace restrictions. The final bounded CPU suite ran outside that restriction
with all checks enabled and clean results. No sanitizer check remains unsupported
in the tested environment. Existing unrelated KG `read()` format/ignored-return
compiler warnings remain; this adapter neither calls nor changes those readers.

## Unchanged stress regressions

The harness compiled existing CPU sources to **new private test paths**, without
rebuilding any accepted Rouse/semiflexible executable:

* `correlator_smoke.cpp`:16 independent Correlator6 objects, direct fine/coarse
  oracle, all six signed channels, counts, repeated evaluation and clear/reuse.
* `tests/stream_lifetime.cpp`:200 ownership cycles under ASan/UBSan/LSan.
* `tests/cpu_workers.cpp`: reference/1/2/4/8 workers, unequal ranges, batches,
  error propagation and lifetime under ASan/UBSan/LSan.
* Existing `semiflexible_stress_correlator.cpp` plus the unchanged Python
  `test_semiflexible_stress_gpu.py::check_direct` helper: nine prescribed
  constant/zero-mean/nonzero-mean cases across workers1/2/4 and batches1/7/32.
  Every exported channel/H/paired-SE/count/normalization comparison passed;
  worker/batch correlation CSVs were byte-identical. Importing that helper did
  not invoke its GPU test setup or scientific simulations.

All passed. Existing test files, scientific gates and their tolerances are
unchanged. GPU regressions were not executed: this milestone is CPU-only.

## Bounded benchmark measurements

Environment: Linux5.15.0-198-generic,x86_64; Intel Core i7-12700;g++11.4.0,
`-O2 -std=c++17`, no fast-math. The process had20 CPUs in its affinity mask but
the adapter ran **serially on one calling thread**. Benchmarks are unsanitized.
No particular performance/efficiency core was pinned and other machine load
was not controlled; do not infer precise scaling from short small-chain runs.
Each configuration ran in three separate processes. Rows below are medians;
each used128 warm-up frames and512 timed frames, cycling eight precomputed
prescribed end-to-end frames. Throughput counts chain observations once, even
in the three-owner mode, and includes normalization, feature construction and
correlator updates. Allocation, evaluation and teardown are timed separately.
All20 levels allocate memory, but this short acquisition does not populate the
entire ladder. These are bounded CPU microbenchmarks, not trajectories or
production-server throughput predictions.

| Chains | Slots | Mode | Allocation ms | Teardown ms | Million chain-observations/s | Peak RSS MiB |
|---:|---:|---|---:|---:|---:|---:|
| 64 | 32 | C1 | 1.368 | 0.201 | 4.608 | 34.59* |
| 64 | 32 | C1+C2 | 5.164 | 0.258 | 2.130 | 34.59* |
| 64 | 64 | C1 | 2.042 | 0.111 | 3.652 | 34.59* |
| 64 | 64 | C1+C2 | 12.407 | 0.319 | 1.405 | 34.59* |
| 512 | 32 | C1 | 12.163 | 0.700 | 5.409 | 34.59* |
| 512 | 32 | C1+C2 | 25.009 | 2.864 | 1.574 | 83.70 |
| 512 | 64 | C1 | 13.817 | 0.985 | 3.894 | 55.34 |
| 512 | 64 | C1+C2 | 41.140 | 3.603 | 0.966 | 158.74 |
| 2048 | 32 | C1 | 30.049 | 3.835 | 3.617 | 110.82 |
| 2048 | 32 | C1+C2 | 78.637 | 12.791 | 0.789 | 324.27 |
| 2048 | 64 | C1 | 52.936 | 4.827 | 2.357 | 210.86 |
| 2048 | 64 | C1+C2 | 149.152 | 15.700 | 0.585 | 624.33 |

*`getrusage` reports lifetime peak RSS in KiB; baseline peak in these child
processes was34.59MiB, even when current preallocation RSS was much smaller.
Small-bank peaks therefore have that floor. The artifact also records current
RSS before/after allocation, baseline peak and post-teardown current RSS; peak
is not represented as incremental bank allocation.

The proposal's LP64 array payload formula80*L*P+72*L per Vector is exact for
these allocations. Three owners,C2048,L20 give **308.4375MiB at P32 and
608.4375MiB at P64**, matching the proposal. Steady estimates including owned
objects, chain pointers and normalization scratch are309.516/609.516MiB.
Measured allocated-RSS increases were320.723/620.781MiB: about12.3MiB above
array payload in either configuration, reflecting allocator/page overhead and
object/scratch storage. Peak process RSS was324.27/624.33MiB. No representation
or numerical work was changed to reduce this overhead. The1GiB API preflight
budget uses the documented steady estimate, not a guaranteed process RSS cap;
returned result storage and transient allocation pools are also excluded.

Freed memory remained resident in the tested allocator. A separate same-process
three-cycle construction/feed/evaluate/destruction check at C2048,P64,C1+C2
observed624.141,624.141,624.160MiB resident peaks/samples:20KiB variation.
Post-teardown RSS retention is not treated as a leak; ownership was independently
checked by LSan and failure injection. This is finite reuse evidence, not a
long-production memory-stability claim. Retained adapter state is structurally
O(C*L*P)+O(C), independent of total observations. Returned results are O(L*P);
a caller that retains every result would incur additional caller-owned growth.

## Reproduction and limits

From the **development** worktree, using no CUDA tools:

```sh
timeout 480s python3 -B examples/slip-springs/tests/run_orientation_cpu.py --benchmarks
```

The complete final run, including compilation, sanitizers, stress regressions,
36 benchmark processes and the large-memory reuse process, took about52 seconds
in subprocess scopes. Every command has a bounded timeout. Omit `--benchmarks`
for checks alone. Private artifacts are in `build/orientation-cpu/`: compiler
logs, sanitizer logs, per-process benchmark JSON logs and `results.json` containing
all repetitions, command durations, source/binary hashes and memory fields.
The default Makefile, its targets and compiled scientific executables are unused.
The recorded `results.json` SHA256 is
`7d2ab1b727ded3ad4266202375acc3e342bb1d931c30e85446287f9ad7bb64d6`;
the tested unsanitized binary SHA256 is
`75a04bd7ed7899edc712f64972dc7206e0fa6d1a9cf75ea7de1330d76b99a0be`.
Re-running benchmarks produces a new measurement artifact rather than those
same timing/checksum values.

The measured serial baseline is ready for independently authorized prescribed-
coordinate GPU acquisition/transfer benchmarking. It does not implement GPU
gathering, buffering, asynchronous transfers, CPU worker parallelism or simulator
sampling/output. The existing proposal's rough operation-count throughput estimate
is not validated by this serial result; its reference stress timing used four
workers, so direct speed comparisons or assumed linear scaling would be unsound.
Dense acquisition may be CPU-bound and requires actual end-to-end benchmarking.
Thread safety is caller-exclusive; do not call observe/evaluate concurrently.
Original Vector save/read restart behavior is not exposed or validated.

No CPU correctness/ownership blocker remains for this milestone. A future GPU
integration still requires separate authorization, acquisition/replay tests,
safe stream/buffer lifetimes and a versioned protocol; nothing here changes
the frozen Stage4A.3c campaign or establishes physical orientation relaxation.
