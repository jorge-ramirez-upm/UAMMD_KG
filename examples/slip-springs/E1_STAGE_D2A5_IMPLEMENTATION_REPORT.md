# D2A.5 variable-length implementation — preparation only

Starting local and independently queried remote `slip-springs` HEAD:
`a97a96cccb0b0ace531f0f4c0b9c46b3cb3c5dc1`.
Repository: `jorge-ramirez-upm/UAMMD_KG`. All changes are local to this example.
**Implemented, not compiled or verified.** No tests, simulations, GPU operations,
benchmarks or scientific reductions were executed in Codex. Independent review
and user execution precede any technical acceptance or campaign.

## Implementation and physical compatibility

Inspection found that physical dynamics already use runtime N. No new force,
initialization, topology, hopping, renewal or RNG implementation is needed.
`semiflexible.cu::parameters` allocates N bond entries and N+1 bending entries;
only beads 1 through N-1 have active bending. `initialize` builds chain-contiguous
N+1 coordinates with the existing radial/angular equilibrium initializer.
`simulate` sizes old/new coordinates, forces, optional anchors/occupancy and
spring identities from M(N+1), and passes N+1 into the existing kernels.
`semiflexible.cuh` stretching, bending and bead update use that same runtime
stride. `fixed_slip_springs.h` uses actual coordinate count for excluded uniform
site selection and conditional Gaussian anchors. `slip_hopping.cuh` and
`slip_renewal.cuh` use the runtime chain stride for free ends, neighbors and
same-/cross-chain transfers. Occupancy and ordered identity links remain unchanged.
The histogram's 32 finite bins plus overflow are unrelated to contour length.

The remaining N32 restriction was in the CPU dynamical observer. The changes:

- Support exactly N=32, 64 and 128 when dynamical acquisition is enabled.
- Carry actual N through model/result metadata and reject mixed-length replica
  reductions. Existing callers default to N32.
- Select `{0,N/4,N/2,3N/4,N}` and label CSV bead columns with actual indices.
  Six `DiffusionCorrelator` owners and the existing orientation adapter remain
  per chain. No internal MSDs or new observables were introduced.
- Dispatch acquisition to compile-time bead counts 33, 65 or 129. The N32 CM
  sum order and constant division by 33 retain their original expressions.
  Selection, immutable chain IDs, fixed per-series offsets and unwrapped
  coordinates retain the accepted semantics.
- Set `model.bonds=o.n` and update CLI help in `semiflexible.cu`; these are its
  only edits. Default-off acquisition, force evaluation, old/new swap, hopping,
  renewal, RNG domains/counters, launches and arithmetic are untouched.

Use semantic slot aliases `Center`, `QuarterLeft`, `QuarterRight`, `EndRight`
with `quantity_names_for(N)` for new clients. Historical `Bead16`, etc. remain
N32-compatible slot names, not assertions about longer-chain bead identities.
The simulator still permits other chain lengths with dynamics disabled; this
milestone restricts the observer, not the preexisting physical CLI.

The caller supplies Z: there is no automatic density or physical parameter
change. At M=256, constrained Z must be 2048/4096/8192 for N=32/64/128 to retain
Z/(MN)=1/4. This is nominal slip-spring density, not a measured entanglement density.
Keep kBT=zeta=b0=1, kb=30, kappa=0 or 10, a_ss²=5, hopping rate 100,
canonical renewal, double precision and initial dt=0.0001.

Historical campaign manifests, source hash pins and N32 analysis/validation
scripts are deliberately unchanged. They do not become variable-N campaign or
analysis tools through this patch. Future longer-chain campaigns need their own
reviewed parameterization and authentication against the new binary identity.

## Metadata contract and observation phase

Physical `metadata.json` continues to report `springs=N`, `beads_per_chain=N+1`,
`total_beads=M(N+1)`, stored precision, active angles, rounded coefficients,
RNG/seed, counts, timers and allocation estimates. No physical schema changes.
The CPU observer's existing version-1 metadata now reports actual `N`,
`beads_per_chain`, `selected_beads`, b0/kb vectors of length N and kappa of length
N+1 with zero endpoints. For N32 the field order, names and values are retained,
except the conservative allocation estimate may reflect the added contour tag.
This is recorded and budget-checked separately in baseline comparisons.
Unknown or physical metadata differences remain failures.

Acquisition phase is unchanged: step zero follows initialized force/state
validation before the first BD update. Subsequent acquisition follows the full
BD update, coordinate-buffer swap, hopping and end renewal, sharing completed
coordinates with existing equilibrium/scalar observations when scheduled.
Frames occur at integer steps 0,stride,...,floor(steps/stride)*stride, including
no shorter final interval. Each row carries replica/chain identity, lag samples,
lag steps/time, actual origins, block width and displacement phase. CSV columns
are CM, the five actual bead MSDs, end/quarter means and signed differences,
C1 and C2. Only the standalone replica reducer supplies across-run uncertainty;
a simulator run has one independent replica and null SE.

MSD uses direct displacement and last-position decimation. Orientation uses
block-averaged unit-vector and rank-two features, with triangular lag support.
Counts, omitted deepest level, incomplete blocks, sentinel handling and KG
arithmetic are unchanged. Coarse orientation and MSD have different filters.
Metadata records requested budget, conservative estimate, transfer bytes/frames,
clock and correlator support. This is not a measured GPU-peak-memory report.

## Prepared verification and limitations

`tests/dynamical_observer_cpu.cpp` retains N32 checks and adds independent
prescribed-coordinate references at N64/N128, m=2 and m=3, incomplete final
intervals/blocks, large offsets, read-only acquisition, CSV labels, metadata,
invalid dimensions and mixed-contour reduction rejection. It reuses the accepted
orientation reference helpers. Existing correctness/allocation tests still apply.

`tests/variable_contour_transitions.cu` exercises unchanged device helpers on
frozen coordinates for all three lengths: excluded interior hops, forward/reverse
moves, chain-end rejection, occupied source/destination ends, cross-chain renewal,
same-chain end transfer and occupancy/order invariants. No stochastic trajectory
is used by that fixture. It is a GPU test to run only after review.

`tests/d2a5_variable_n.py` reuses strict D2A.2 physical comparisons, the existing
Linux child supervisor, independent backbone force reference and actual export
grid. For each length, stiffness and occupancy cell it prepares M256, 24-step
on/off/replay runs and a prescribed-coordinate zero-step force case. It checks
stretch/bend/anchor forces and energies with existing double tolerances, parameter
indexing, canonical occupancy, identity/order, finite snapshots, completion
inventories, actual labels, clocks and lag counts. Full/joint context at
0,4,...,24 stays within the eight-snapshot limit. Expected dynamics: nine frames.
Bare COM `6t/(N+1)` ratios are descriptive only; these tiny records cannot test a
diffusion law or equilibrium moments.

N32 additionally compares all four cells to the unchanged accepted executable:
`/home/jramirez/UAMMD_KG-d2a2-verification/build/current-double/semiflexible`,
SHA256 `da303c4c2b2de94172fe0114f4f5cc2d78fd9499ef188938a15114cc3100f342`,
built from source `d60982f4035b9b704a23397fb034ca1b58fe5771`.
Physical coordinates, attachments, events and correlation CSVs must match bytes;
metadata comparisons permit only the existing named timing fields and the
separately checked observer allocation estimate. This compares saved states,
not every intermediate state. No statistical physical acceptance follows.
Annealed initialization source is unchanged; deterministic replay and valid
occupancy do not independently prove equilibrium sampling at new lengths.

The optional benchmark mode requires a successful same-binary correctness
summary. It measures only 100/1000-step cases, stride100, endpoint context,
without fits or scientific interpretation; launch/final-export overhead may
 dominate. It cannot establish multi-day throughput. Limits are 120 s per child,
600 s aggregate, 2 GiB RSS, 128 MiB/run output, 2 GiB total output and a maintained
10 GiB disk floor. The reused supervisor polls Linux resources and kills process
groups on violation; file-size rlimits and parent-death protection also apply.
Polling has overshoot and is not a hard address-space quota. An outer GNU timeout
also bounds CPU validation. No retry or automatic tolerance change.

Checkpoint/restart is explicitly deferred by the user's later instruction.
Runs are assumed uninterrupted; interrupted long runs cannot resume correlations.
No partial checkpoint implementation or design is included.

D1.6 remains **scientifically closed with qualifications — equilibrium preservation
not confirmed**. No reptation, terminal relaxation, quantitative entanglement
length or longer-chain stability claim is made. Stress/G(t), future six-component
rheology requirements and D2B force-distribution design remain unchanged.

## Local Linux commands — prepared, unexecuted

Run from the repository root after independent review. Use fresh paths and
preserve the accepted binary above. Toolchain settings below match its recorded
CUDA13.0.88/g++11.4/sm_86 double configuration; verify local versions before building.
Python >=3.9 and NumPy are required. No broad `make all` or historical analysis.

```bash
D5_BUILD="$PWD/examples/slip-springs/build/d2a5-review-v1"
mkdir "$D5_BUILD"
/usr/local/cuda-13.0/bin/nvcc --version > "$D5_BUILD/cuda-version.txt"
/usr/bin/g++ --version > "$D5_BUILD/host-compiler-version.txt"
git rev-parse HEAD > "$D5_BUILD/source-sha.txt"
git diff --exit-code > "$D5_BUILD/source-diff.txt"
make -C examples/slip-springs semiflexible PRECISION=double CUDA_HOME=/usr/local/cuda-13.0 NVCC=/usr/local/cuda-13.0/bin/nvcc CXX=/usr/bin/g++ CUDA_ARCH=sm_86 GPU_BUILD="$D5_BUILD/double" > "$D5_BUILD/build.log" 2>&1
sha256sum "$D5_BUILD/double/semiflexible" > "$D5_BUILD/binary.sha256"
g++ -std=c++17 -O1 -g -pthread -fsanitize=address,undefined -fno-omit-frame-pointer examples/slip-springs/tests/dynamical_observer_cpu.cpp examples/KG/correlator.cpp -o "$D5_BUILD/observer_cpu"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 180s "$D5_BUILD/observer_cpu" "$D5_BUILD/cpu-output"
g++ -std=c++17 -O1 -g -pthread -fsanitize=address,undefined -fno-omit-frame-pointer examples/slip-springs/tests/dynamical_cpu.cpp examples/KG/correlator.cpp -o "$D5_BUILD/dynamical_cpu"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 180s "$D5_BUILD/dynamical_cpu"
g++ -std=c++17 -O1 -g -pthread -fsanitize=address,undefined -fno-omit-frame-pointer examples/slip-springs/tests/dynamical_observer_allocation_failure.cpp examples/KG/correlator.cpp -Wl,--wrap=_Znwm -Wl,--wrap=_Znam -o "$D5_BUILD/observer_allocation_failure"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 180s "$D5_BUILD/observer_allocation_failure" "$D5_BUILD/allocation-output"
/usr/local/cuda-13.0/bin/nvcc -ccbin=/usr/bin/g++ -O2 -std=c++17 --extended-lambda -arch=sm_86 -DDOUBLE_PRECISION -Isrc -Isrc/third_party examples/slip-springs/tests/variable_contour_transitions.cu -o "$D5_BUILD/double/variable_contour_transitions"
timeout --signal=TERM --kill-after=15s 60s "$D5_BUILD/double/variable_contour_transitions"
timeout --signal=TERM --kill-after=15s 600s python3 -B examples/slip-springs/tests/d2a5_variable_n.py --run-reviewed-bounded --binary "$D5_BUILD/double/semiflexible" --baseline-binary /home/jramirez/UAMMD_KG-d2a2-verification/build/current-double/semiflexible --output /home/jramirez/UAMMD_KG-evidence/d2a5/bounded-v1
```

Stop at any failure; commands are individual review steps, not an unconditional
campaign. A fresh `D5_BUILD` leaf is required; create its parent if absent. For
single-precision build documentation only, the same targeted make command with
`PRECISION=single GPU_BUILD="$D5_BUILD/single"` prepares a separate executable;
scientific validation and the new GPU fixture require double precision.
After correctness passes and separate benchmark review:

```bash
timeout --signal=TERM --kill-after=15s 600s python3 -B examples/slip-springs/tests/d2a5_variable_n.py --run-reviewed-benchmark --correctness-summary /home/jramirez/UAMMD_KG-evidence/d2a5/bounded-v1/summary.json --binary "$D5_BUILD/double/semiflexible" --output /home/jramirez/UAMMD_KG-evidence/d2a5/benchmark-v1
```

The driver refuses existing output directories and preserves failures/logs.
Do not run the provisional N64/N128 production targets using this driver.
