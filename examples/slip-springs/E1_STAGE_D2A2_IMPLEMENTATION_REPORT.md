# D2A.2 — optional read-only dynamical acquisition

Prepared 27 October 2026 in the permanent development checkout, branch
slip-springs. Starting local and actual remote HEAD both:
0b177a62cf33bcd1143aba98cb83931fecbda9d1, queried before work.
**No builds, tests, simulations, analyses, benchmarks or GPU operations ran.**
The user's reported successful D2A.1 correctness/sanitizer/allocation-failure
exit statuses are prior user reports; their logs were not inspected here.

## Integration and exact observation phase

[dynamical_observer.h](dynamical_observer.h) is synchronous host-only glue around
the unchanged [D2A.1 adapter](dynamical_observables.h): settings validation,
const-coordinate acquisition, allocation preflight and compact CSV/JSON export.
The host driver in semiflexible.cu adds parsing, guarded construction, two
acquisition call sites and final export. Makefile changes add header dependencies
only; existing build commands/flags and KG arithmetic stay unchanged.

The production order remains force evaluation at old state -> BD proposal ->
diagnostic -> swap current/following pointers -> entire hopping/end-renewal batch
at new coordinates -> invariant/diagnostic checks -> existing observations.
Acquisition reads the completed **current** buffer, never old/proposed coordinates.
It has no anchor, occupancy, force or RNG API and writes nothing to the device.

At step 0, existing observe(0) reads the initialized uploaded state after initial
force/state checks and before the first BD update. At shared acquisition steps,
the new call runs inside existing observe, **after** coordinate readback and
equilibrium begin, **before** legacy scalar reductions and equilibrium chain/
end-frame processing. All observers see the same frozen physical state.

When only the dynamics clock is due, an else-if after the existing observation
condition performs one synchronous full-coordinate readback into the existing
host vector and calls only the new observer. It does not invoke legacy scalar,
equilibrium or stress observation or change their schedules/formats. Only
0,stride,2*stride,...<=steps are acquired: floor(steps/stride)+1 frames. A
nonmultiple final step is not appended, and incomplete blocks are not padded.
Zero-step runs acquire the initialized frame.

The helper reads all 33 beads, using bead 0 as a numerical reference and double
offsets for CM summation, then selects beads 0,8,16,24,32 by immutable flat
chain-contiguous IDs. D2A.1 derives end-to-end direction from original end
positions and applies one fixed MSD offset per series. Coordinates are unwrapped.
No relative-to-CM monomer trajectories or internal MSDs are introduced.

## Configuration

Options take explicit values, following the existing parser. Dynamics is disabled
by default. Disabled observer settings are inactive: no bank, extra readback or
new directory. Default-off compatibility is intended, not claimed bitwise verified.

| Option | Default / enabled contract |
|---|---|
| --dynamics 0 or 1 | 0; N32 only; incompatible with force-input |
| --dynamics-stride STEPS | 100; positive integer integration-step spacing |
| --dynamics-levels L | 8; existing multi-tau limits |
| --dynamics-slots P | 16; existing divisibility/slot limits |
| --dynamics-m M | 2; existing coarsening limits |
| --dynamics-output SUBDIR | dynamics; one alphanumeric/underscore/hyphen child of --output NEW_DIR, not an external path |
| --dynamics-mib MiB | 256; 1..1024; conservative observer estimate must fit |
| --dynamics-replica ID | run seed; identity is not proof of statistical independence |

The existing E1 stress-off restriction and physical parameter/parameters-file
semantics are unchanged. The new feature does not use stress/rheology transport.
Invalid enabled settings fail during parsing before output preparation/GPU setup.
Physical workspace plus the observer estimate must also satisfy the existing
2-GiB aggregate guard.

## Output and failures

The selected new subdirectory contains:

- **chain_correlations.csv:** per-chain curves with replica and chain IDs.
- **replica_correlations.csv:** equally weighted chain means inside this replica;
  chain field is empty. Symmetry reductions occur inside each chain first.
- **metadata.json:** published last after both CSV streams close successfully.
  Until then, only metadata.pending.json exists; partial files remain on failure.

CSV fields include lag samples/steps/time, actual origins per chain, diffusion
decimation period/phase, orientation block size/duration, six MSDs, end/quarter
averages and differences, C1 and C2. No coordinate/anchor dumps or fits are added.
Diffusion has point width 1 and decimated fine origins. Orientation averages
instantaneous unit/rank-two features over blocks, giving a triangular lag mixture
with half-width (block_samples-1)*stride*dt; blocks are not renormalized.
KG's deepest-populated-level omission and incomplete-block truncation remain.

Metadata records phase/clock, frames/last step, seed and precision, actual stored
b0/kb/kappa arrays, kBT/zeta, rounded mobility/noise, spring count/variance/
stiffness, hopping rate, and requested versus active renewal. It also records
memory allowances, readback counts/bytes and scoped CPU/export timings.
One process is one independent replica: standard_error is null. D2A.1's
replica reduction remains available for compatible independent run results;
chains, monomers, origins and lag bins do not become replicas.

An existing new-observer directory is rejected. Streams throw on I/O errors and
are explicitly closed before completion publication. A new-observer failure
aborts with nonzero exit and no valid dynamical completion file. If final export
fails, legacy outputs/legacy completion may already exist; they do not certify
new products. Require successful process exit, a regular valid dynamical
metadata.json and both CSV files. Undefined end direction fails measurement;
it is never repaired by changing coordinates or dropping an acquisition.

## Resources and timing

Shared frames reuse the already-paid full-coordinate readback. Each dynamics-only
frame adds chains*33*sizeof(real4) synchronous D2H bytes, with at most
floor(steps/stride) additional transfers after the shared initial frame.
The same host vector is reused. CPU state comprises six MSD and three orientation
owners per chain, selected-frame scratch and final curves. No GPU gather, stream,
worker pool, checkpoint or campaign framework was added.

Preflight allows four times D2A.1's steady estimate plus selected-frame/ID scratch
and 64 KiB for fixed observer/model/I/O overhead. This is conservative allocation/
curve/transient accounting, not measured allocator/RSS enforcement. Large
configurations may be rejected conservatively; allocation failures propagate
through RAII. D2A.1's sentinel/coordinate/count limits remain.

Shared consumption contributes to existing observation wall accounting. Extra
readback/consumption is in production wall. Dynamical evaluation/CSV cost is
recorded separately and excludes metadata publication; legacy final-output
timing is not relabeled. Do not add overlapping scopes. No speedup or negligible
overhead is claimed.

## Verification prepared, not executed

[CPU checks](tests/dynamical_observer_cpu.cpp) reuse the orientation fixture's
direct grid/normalization helpers. Prescribed full-chain coordinates independently
check selected mapping, all-bead CM, const input, initial/uniform clocks and all
exported quantities on correct decimated/block supports for m=2 and 3. They cover
nonmultiple final steps, zero steps, configuration/budget/coordinate errors,
duplicate/missing frames, output collision, incomplete acquisition and deterministic
publication failure. JSON parsing is included in workstation commands below.
[Observer allocation-failure checks](tests/dynamical_observer_allocation_failure.cpp)
reuse D2A.1's GNU new/new[] wrappers and bounded sweep across construction,
acquisition and export, checking that bad_alloc never publishes completion.
This covers wrapped allocation sites, not arbitrary library/OS failures. D2A.1's
existing lifetime suite remains unchanged.

[Tiny-run checks](tests/dynamical_integration_tiny.py) require explicit separate
review and authorization. They take a baseline binary from the starting SHA and
a new binary with matching precision/compiler/toolkit/flags and hardware. The
caller must establish build provenance; recorded binary hashes identify bytes
only. Two fixed N32/M2/24-step fixtures use Z0/kappa0 and Z32/kappa10 with renewal
requested. Each compares baseline, current implicit-off, explicit-off, on and
repeated-on runs. Replays are not independent scientific replicas.

Legacy inventories must match. Every physical CSV, parameters, initial/final
anchors, sites/order, joint coordinate/attachment checkpoint, event record,
schema and hopping metadata requires **byte equality**. Only explicitly named
timer/rate keys in main metadata and three equilibrium timing keys may differ;
every other JSON field/schema must match. Repeated dynamic curves require byte
equality; dynamic metadata ignores only four named timing fields. No physical
numeric tolerance or ignore-all-metadata fallback is provided. Mismatches stop
verification and require investigation. Joint snapshots cover seven saved
checkpoints, not every integration step. No bitwise-invariance claim is made
before execution.

## Local workstation commands — none executed

CPU verification after independent review, from repository root. Use a fresh
permanent directory; choose a new name if it exists:

~~~sh
D2A2_BUILD="$PWD/examples/slip-springs/build/d2a2-review"
mkdir -p "$PWD/examples/slip-springs/build"
mkdir "$D2A2_BUILD"
g++ -std=c++17 -O1 -g -Wall -Wextra -pedantic -pthread -fsanitize=address,undefined -fno-omit-frame-pointer examples/slip-springs/tests/dynamical_observer_cpu.cpp examples/KG/correlator.cpp -o "$D2A2_BUILD/observer_cpu"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 180s "$D2A2_BUILD/observer_cpu" "$D2A2_BUILD/cpu-output"
python3 -m json.tool "$D2A2_BUILD/cpu-output/m2/metadata.json"
python3 -m json.tool "$D2A2_BUILD/cpu-output/m3/metadata.json"
g++ -std=c++17 -O1 -g -pthread -fsanitize=address,undefined -fno-omit-frame-pointer examples/slip-springs/tests/dynamical_observer_allocation_failure.cpp examples/KG/correlator.cpp -Wl,--wrap=_Znwm -Wl,--wrap=_Znam -o "$D2A2_BUILD/observer_allocation_failure"
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 180s "$D2A2_BUILD/observer_allocation_failure" "$D2A2_BUILD/allocation-output"
~~~

Previous D2A.1 commands remain in its [report](E1_STAGE_D2A1_IMPLEMENTATION_REPORT.md).
Successful user exit statuses do not constitute inspected logs here.

**CUDA compilation and tiny runs need separate review and explicit authorization;
these proposed commands grant neither.** Use a fresh build directory, appropriate
reviewed architecture/toolkit and a separately preserved baseline executable:

~~~sh
make -C examples/slip-springs semiflexible PRECISION=double CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$D2A2_BUILD/double"
# Independently authenticated baseline executable from the starting SHA:
D2A2_BASELINE=/absolute/permanent/path/to/baseline-semiflexible
python3 examples/slip-springs/tests/dynamical_integration_tiny.py --run-reviewed-tiny --binary "$D2A2_BUILD/double/semiflexible" --baseline-binary "$D2A2_BASELINE" --output "$D2A2_BUILD/tiny-double"
~~~

If separately approved, repeat with single precision and a matching single
baseline in distinct directories. Do not use a broad check target or a historical
campaign as a shortcut. Commands/timeouts are unexecuted proposals, not validated
runtime or compatibility claims.

## Preserved science and review gate

KG, D2A.1/orientation adapters, force kernels, initializer, hopping, renewal and
BD update arithmetic are unchanged. The host simulator source identity changes
for optional observation; no frozen source allowlist, evidence, manifest or
protocol is edited to authenticate this binary as an old one. D1.6 remains
scientifically closed with qualifications — equilibrium preservation not confirmed.
No D2B force change or scientific campaign is introduced. All edits stay under
examples/slip-springs/ and no persistent temporary storage is used. Only source/
document review and Git housekeeping ran. Stop after preparation for independent
review; the final SHA and normal push verification are supplied in the handoff.
