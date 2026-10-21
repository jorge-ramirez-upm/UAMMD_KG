# E1 Stage A independent audit — 21 October 2026

Starting branch: `slip-springs`, clean working tree, HEAD
`ddeb2f87d882f430a0927d767bb4499e16f04b73` (matches the requested SHA).
Remote `origin/slip-springs` independently returned that same SHA before push.
The E1 specifications, backbone model/status/rules, complete Stage A source,
build/test files and existing GPU backbone implementation were reviewed.

## Scientific findings

The model equations and original integration order are correct. With
`k_ss=3*kBT/A2`, the additional bead force is `-k_ss*(r-a)` and the energy is
`k_ss*|r-a|^2/2`. Each occupied bead receives the entire energy of its one spring;
backbone energy shares are retained, so no extra factor of two or three belongs
in the spring contribution. Stretch overwrites, bend adds, spring adds, and the
unchanged Euler–Maruyama update reads the total force on the same CUDA stream.
There are no anchor forces applied to other beads and no atomics for forces.

Shuffling all bead sites and taking the first Z gives uniform unordered distinct
site sets, including chain ends. Conditional anchor components have variance
`A2/3`, independently of kBT, because `kBT/k_ss=A2/3`. The Gaussian anchor integral
is `(2*pi*A2/3)^(3/2)` per spring, independent of bead position. Summing uniform
site sets and integrating anchors therefore restores the bare backbone
conformational marginal. This is an annealed ensemble statement; fixed-anchor
trajectories are conditional dynamics. Supplied coordinates are not certified
backbone-equilibrium samples. No sign, physical-unit or energy-counting error
was found in the original Stage A formulas.

## Problems repaired

| Finding | Correction |
|---|---|
| Infinite stiffness passed the `>0` input check; positive A2 could round to zero; `3*kBT` could overflow before division even for a finite ratio | Validate both finite positive precision-rounded A2 and stiffness; use a wider host intermediate, round once, reuse and record the actual GPU coefficient |
| Computing the squared extension before multiplying by stiffness could overflow when force and energy were representable | Compute spring energy as `-F_ss dot (displacement/2)`; regression includes a large extension with small stiffness |
| Original single test used only zero-step force probes and loose double tolerances | Add CPU tests of the actual shared initializer and GPU frozen-anchor finite differences, nonunit-temperature drift, noise isolation, runtime diagnostics, replay and zero allocation/launch recovery; tighten double tolerances |
| Conservative workspace estimate did not explicitly include both added host and device anchor arrays | Include both arrays and temporary site permutation; expose actual spring device capacity and launch count |
| Spring coefficient/initialization domain were absent from successful metadata and failed-force diagnostics lacked spring parameters | Record effective stiffness and CPU RNG domain; include spring parameters in `failure.json`; explicitly close/check the new anchor output |
| Existing CPU stress-reference build parsed a CUDA transport class from a shared header | Guard only that class with `__CUDACC__`; CPU correlation math and CUDA class contents remain unchanged |
| Consolidated status/README still claimed no slip-spring implementation | Update Stage A status, commands, outputs and scientific limitations |

The initializer was extracted into a CPU-only local header to test the exact
production implementation without CUDA. Its engine/domain, uniform permutation
and Gaussian algorithm remain isolated from backbone initialization and Philox.
The Gaussian scale uses `sqrt(A2)/sqrt(3)` to avoid underflow of `A2/3` before
its square root. Last-bit differences from the unaudited initializer are possible;
cross-version or cross-standard-library active-anchor byte identity is not promised.

## Execution evidence

Development host: NVIDIA GeForce RTX 3060 Ti, sm_86, driver 580.178.04;
`/usr/local/cuda/bin/nvcc` 13.0.88, g++ 11.4.0, C++17, `-O2`, no fast math.
Binaries were freshly compiled under `build/e1-audit/{single,double}`; original
campaign binaries and archived evidence were not replaced.

| Bounded check | Actual outcome |
|---|---|
| Requested default-toolchain `make check-fixed-slip-springs PRECISION=double` | Failed compiling the installed CUDA 11.5.119/GCC 11 `std_function.h` combination (parameter-pack errors); not a passing build |
| CUDA 13 simulator and new GPU test compilation | Passed in single and double |
| `check-fixed-slip-initialization` | Passed for float/double: all six site pairs on four sites, hypergeometric chain occupancy, Gaussian means/variances/cross-moment, seed replay/high seed bits, input immutability, zero/full occupancy and invalid parameters |
| `check-fixed-slip-springs`, final repaired source | Passed in both precisions: GPU unit executable plus four Python regression cases, including frozen-anchor finite differences and first failing active-force diagnostics |
| Existing `check-semiflexible` | Passed in both precisions: 7 GPU tests, 2 bounded host-tool tests, 12 CPU reference tests |
| Existing `check-semiflexible-stress` | Passed in both precisions after the header guard repair: 7 tests, independent CPU correlation oracle and diagnostic fixtures |
| Existing `make check` (Rouse/CUDA/pipeline/CLI/stream/theory) | Passed in both precisions |
| CPU stress reference, timestep preselector and Rouse theory/stress Python checks | Passed: 11, 7 and 10 tests respectively; backbone CPU reference also passed separately |
| New initializer ASan/UBSan/LSan; existing `check-workers`, `check-lifetime` | Passed with leak detection enabled outside sandbox tracing restrictions |
| CUDA 13 Compute Sanitizer, new force unit executable | memcheck: 0 errors; racecheck: 0 errors/warnings, both precisions |
| Compute Sanitizer, active simulator N3,C2,kappa2,Z3,A2=2.4,5 steps,stride1,seed4317 | memcheck: 0 errors, both precisions |
| Pre-E1 driver comparison (source from `f66db56`, both precisions) | Initial/final coordinates, parameters, scalar/bond outputs and streamed correlations/moments byte-identical for pre-E1/default/explicit Z0; N3,C4,kappa0/2,kBT1.7,dt0.0001,5 steps,stride1,seed4317, stress off/stream |
| Documented active short example, N8,C64,kappa2,dt0.0001,Z32,A2=5,100 steps,stride10,seed4317 | Executed successfully in both precisions; output and performance metadata saved |
| Historical `test_semiflexible_stress_campaign.py` with both new binaries | 12/13 passed; authentication case errors with `accepted source identity changed: semiflexible.cu` |
| Historical `test_semiflexible_scalar_output.py` with both new binaries | 6/7 passed; overlay authentication case errors for the same frozen source identity; runtime full/compact equivalence checks pass |

The last two suites **did not pass overall**. They authenticate a frozen
historical backbone campaign, not an arbitrary later simulator. The starting
Stage A driver already had SHA256
`c88f91a5f8f8c81d3b6012a3c668e593c84f9d08a6a4fcf70b06702cc72aebc5`,
which is outside their accepted identities. This audit leaves the frozen source
hashes, scientific plan, historical tests and thresholds intact. Use the pinned
historical checkout/binaries for that campaign; admitting a new source identity
requires a separately reviewed provenance update, not a test bypass.

Initial sandbox GPU attempts reported `cudaErrorNoDevice`; the device was visible
outside the sandbox and the actual GPU checks above then executed. Initial
sandbox worker assertions passed but LSan could not inspect traced threads;
the complete sanitizer rerun outside that restriction passed without suppressions.
Local build/test logs, comparisons and examples remain in ignored
`examples/slip-springs/build/e1-audit/`; sanitizer logs include `sanitizers.log`.
No generated scientific data is committed.

## Limits and reproducible commands

The unchanged backbone force/update/RNG header, Rouse implementation, KG/UAMMD
sources, original campaign binaries and frozen criteria are preserved. A
programmatic comparison to the Stage 0 source SHA
`81fe5de9cd5ded849202eebab7c14e6bd35fb9ae`, plus tracked/untracked/ignored-path
checks, found no changes or generated paths outside `examples/slip-springs/`.
No long campaign, Stage B, hopping, escape, renewal, constraint release,
slip-spring stress correlation or deformation was introduced.

These bounded tests establish implementation behavior on this host. They do
not establish equilibrium accuracy at finite dt, a stable timestep for arbitrary
A2/stiffness, terminal polymer dynamics, rheology, or portable performance.
Frozen springs confine trajectories; they remain development-only. Available
GPU checks were completed; no GPU-host check is pending because of absent CUDA
or device access. Other GPU hosts should reproduce the bounded commands below
with their own architecture/toolchain and fresh output directories. The moderate
example in the implementation document remains unexecuted host-only work.

From the repository root:

```sh
E1_BUILD="$PWD/examples/slip-springs/build/e1-audit"
make -C examples/slip-springs check-fixed-slip-initialization
make -C examples/slip-springs check-fixed-slip-springs check-semiflexible check-semiflexible-stress PRECISION=single CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$E1_BUILD/single"
make -C examples/slip-springs check-fixed-slip-springs check-semiflexible check-semiflexible-stress PRECISION=double CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$E1_BUILD/double"
/usr/local/cuda/bin/compute-sanitizer --tool memcheck --error-exitcode 99 "$E1_BUILD/double/fixed_slip_forces"
```
