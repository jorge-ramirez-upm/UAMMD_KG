# D2A.1 — CPU dynamical observable adapter

Prepared 27 October 2026. **Not built or tested in Codex.** Starting local and
actual remote `slip-springs` HEAD both
`1b26d3849df38bc2266903180127eb26a64ee40b`, verified before work in the permanent
development checkout. Independent review precedes user verification.

## Implementation and scope

[dynamical_observables.h](dynamical_observables.h) is a standalone C++17 CPU
header linking unchanged `../KG/correlator.cpp`. It adds no simulator dependency,
CUDA include, acquisition kernel, numerical integration, fitted diffusion
coefficient or physical inference. The user's D2A.1 simplification supersedes
the older D2A.0 plan's internal-MSD proposal: **six Diffusion owners per chain,
no internal monomer MSDs or relative-to-CM monomer trajectories**.

`dynamics::OwnedDiffusion` stages the Vector-layout allocation with the same
RAII pool and per-level row cleanup pattern as `orientation::OwnedVector`.
The published base level count remains zero until allocation succeeds. Copy
and move are disabled. It explicitly invokes **DiffusionCorrelator::add**,
retaining KG direct squared differences and last-position decimation. It reuses
unchanged initialization, clear and evaluate; no KG arithmetic was copied or
modified. Its finite/sentinel checks and conservative coordinate bound prevent
overflow of squared-displacement sums over the supported unsigned-long count
lifetime. Coordinates that cannot meet that bound are rejected, not clipped.

`dynamics::Replica` owns six such correlators and one unchanged one-chain
`orientation::Bank` per immutable physical chain. It derives the end-to-end
vector only from the original bead 32 and 0 positions, before independent MSD
offsets are subtracted, and keeps C1/C2 normalization unchanged. Supplied
CM coordinates must be the actual 33-bead CM; the adapter cannot verify that
from only five monomers. Inputs are unwrapped; no PBC conversion is attempted.
The constructor fixes ordered unique chain IDs, replica ID, correlator parameters
and `{first_step,stride,dt}`. Every complete frame is validated before any
correlator advances. Wrong/missing/reordered IDs, size/clock errors, zero or
nonfinite end-to-end vectors, nonfinite positions, shifted sentinel overlap and
unrepresentable accumulations fail explicitly. Input validation failure leaves
frame counts, offsets and accumulated estimates unchanged, so the correct frame
can be resubmitted. Scratch storage may change during validation but is not data.

One initial offset per absolute CM/monomer series is saved only on acceptance
of the first complete frame. It is never changed afterwards. This preserves
absolute displacements, including chain translation. Repeated evaluation does
not add samples. The initial offset is only a numerical gauge: fine-lag bins
average all valid time origins rather than just the first frame. Evaluation
allocation failure may be retried; caller-exclusive
ownership is required (observe/evaluate are not thread-safe). The acquisition
path allocates no storage after construction for valid input frames.

## Input and result API

`Observation.positions` order is **CM, bead 0,8,16,24,32**, six Cartesian triples.
N=32/33 beads is the fixed caller contract. A minimal usage sketch follows;
it was not compiled or executed:

```cpp
#include "dynamical_observables.h"
int main() {
dynamics::Replica replica(101, {700}, {6,16,2}, {0,10,0.0001});
std::vector<dynamics::Observation> frame(1);
frame[0].chain_id=700;
frame[0].positions={dynamics::Vector{0,0,0}, dynamics::Vector{-2,0,0},
  dynamics::Vector{-1,0,0}, dynamics::Vector{0,0,0},
  dynamics::Vector{1,0,0}, dynamics::Vector{2,0,0}};
replica.observe(0, frame);
auto result=replica.evaluate();
auto single=dynamics::summarize({result}); // SE absent for one replica.
}
```

`Result` contains acquisition `Metadata`, ordered per-chain `ChainResult` curves
and equally weighted within-replica chain means. Each `Bin.values` is indexed
by the `Quantity` enum and named by `quantity_names`: six MSDs (CM and the five
monomers), end average, quarter average, end difference (0 minus 32), quarter
difference (8 minus 24), C1 and C2. Symmetry reductions occur inside each chain
before averaging chains. No chain/monomer/origin SE is reported.

`summarize(vector<Result>)` combines equal-weight replica means, checks unique
replica IDs and matching acquisition/grid/count support, and computes Welford
replica SE=sqrt(sum squared replica deviations/[R*(R-1)]). For R=1 the optional
SE is absent. Preserve the individual replica results; independence is the
caller's scientific obligation and is not proved by different integer IDs.
The minimal aggregator requires the same chain count and frame support across
replicas; unsupported differing-record combination is rejected. It accepts
results from this adapter, not an unauthenticated external scientific file format.
No serializer or new provenance framework is needed for this in-memory API.

Support includes lag in samples/steps/time, actual origins per chain, decimation
period b and phase b-1, and orientation block duration. Metadata retains replica
ID, chain count, actual frames/last step, integer clock and correlator parameters;
chain IDs are retained on chain results. The ensemble's acquisition template
comes from its first replica, with its full replica-ID list recorded separately.

Diffusion samples x((j+1)*b-1): it is a direct fine-coordinate displacement at
nominal lag with **decimated origins**, not all fine origins. Point width is 1.
Orientation correlates complete block means of instantaneous unit-vector/rank-two
features without block renormalization: its pair support is a triangular mixture
over nominal lag +/- (b-1) fine samples. `diffusion_semantics` and
`orientation_semantics` describe this distinction. Both preserve incomplete
terminal-block truncation, actual counts and KG's omitted deepest populated
level. A shared nominal lag/count does not mean identical temporal smoothing.

## Prepared deterministic verification

[tests/dynamical_cpu.cpp](tests/dynamical_cpu.cpp) includes the unchanged existing
`orientation_cpu.cpp` under a renamed entry point to reuse its direct grid,
long-double normalization, scalar P2 oracle and correctness tests. It calls its
correctness suite, **never its benchmark or memory-measurement entry points**.
New prescribed-coordinate checks compare six MSDs against independent endpoint-
decimated sums, including coarsening 2 and 3, incomplete blocks and deepest-level
export. A discriminating nonuniform-increment fixture separately computes full-
origin and block-mean MSD to ensure neither is mistaken for decimated MSD.

Other fixtures cover constant positions, translation, large fixed offsets,
time-varying monomer deformation plus chain translation, all symmetry curves,
direct C1/C2, replica reduction and absent R1 uncertainty, mismatched replica
support/IDs, invalid observations/clock/sentinel, atomic validation, repeated
evaluation, clear/reuse and lifetime. The toy input generator may construct
33 prescribed positions to supply a consistent CM, but no internal observable
is computed or stored by the adapter.

[tests/dynamical_allocation_failure.cpp](tests/dynamical_allocation_failure.cpp)
uses the same GNU-linker allocation wrappers as the existing orientation fault
fixture. It injects failures at each allocation point through successful owner
and multi-chain Replica construction, and through repeatable result evaluation.
Wrappers are test-only; normal allocation is unchanged. All checks are
**prepared and unexecuted**. Their thresholds are verification choices, not new
physical acceptance criteria or changes to historical tests.

## User workstation verification commands — unexecuted

From the repository root on Linux with g++, C++17 and GNU ld. Create a fresh
permanent directory; `mkdir` refuses to reuse the named directory. Choose a new
name if it exists. No Makefile/scientific executable is invoked.

```sh
D2A_BUILD="$PWD/examples/slip-springs/build/d2a1-cpu-review"
mkdir -p "$PWD/examples/slip-springs/build"
mkdir "$D2A_BUILD"
g++ -std=c++17 -O2 -Wall -Wextra -pedantic -pthread examples/slip-springs/tests/dynamical_cpu.cpp examples/KG/correlator.cpp -o "$D2A_BUILD/dynamical_cpu"
timeout 180s "$D2A_BUILD/dynamical_cpu" > "$D2A_BUILD/correctness.log" 2>&1
g++ -std=c++17 -O1 -g -Wall -Wextra -pedantic -pthread -fsanitize=address,undefined -fno-omit-frame-pointer examples/slip-springs/tests/dynamical_cpu.cpp examples/KG/correlator.cpp -o "$D2A_BUILD/dynamical_sanitized"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 timeout 180s "$D2A_BUILD/dynamical_sanitized" > "$D2A_BUILD/sanitizers.log" 2>&1
g++ -std=c++17 -O1 -g -Wall -Wextra -pedantic -pthread -fsanitize=address,undefined -fno-omit-frame-pointer examples/slip-springs/tests/dynamical_allocation_failure.cpp examples/KG/correlator.cpp -Wl,--wrap=_Znwm -Wl,--wrap=_Znam -o "$D2A_BUILD/dynamical_allocation_failure"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 timeout 180s "$D2A_BUILD/dynamical_allocation_failure" > "$D2A_BUILD/allocation-failure.log" 2>&1
```

Review each exit status/log before continuing; a compiler/sanitizer/test failure
is unresolved verification, not a pass or reason to weaken existing checks.
These commands have not been validated by execution in this milestone.

## Limits and preserved science

No builds, tests, benchmarks, simulations, analyses, GPU operations or scientific
computations ran in Codex. Verification consists only of source review and Git
housekeeping, not a compiled correctness claim. KG and the accepted orientation
header/tests are unchanged. The simulator, forces, hopping, renewal, integration,
RNG, D1.6 evidence and acceptance criteria remain unchanged. All changes stay
under `examples/slip-springs/`; all persistent work stays in the permanent checkout.

The six MSD plus three orientation owners give nine Vector-layout payloads per
chain, plus objects, offsets and scratch. `Replica::estimated_bytes` preflights
a conservative steady allocation estimate; it excludes allocator metadata,
temporary allocation pools/ID validation copies, returned curves and caller-held
results. No measured runtime/RSS or long-record accuracy is claimed. Binary64
cannot recover coordinate information already quantized by the producer; fixed
offsets do not remove KG's negative-x sentinel limit, and extreme replica moment
overflow is reported rather than silently accepted. Different physical cohorts
must not be pooled merely because their acquisition metadata match.

D1.6 remains scientifically closed with qualifications — equilibrium preservation
not confirmed. This adapter makes no terminal-diffusion fit, stationary-bias
claim or D2B model change. Stop for independent review before verification or
any separately authorized CUDA acquisition integration. Final commit SHA and
push verification are supplied in the handoff.
