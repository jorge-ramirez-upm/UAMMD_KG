# Stage 4A.3b.2b compact scalar-output implementation

18 October 2026. Starting local/fetched origin/slip-springs SHA:
`1243e104b2b0a229cd55dedbf68f12d4f36cfda6`; clean worktree before edits.
Implementation and bounded verification only. No Stage4A.3c campaign member or
Stage4B/slip-spring work was executed. The interrupted legacy pilot was untouched.

## Architecture and scientific invariants

`--scalar-output full|compact` defaults to full. Compact requires stress streaming.
Full preserves its file set, headers, cadence and arithmetic; no new metadata
fields are imposed on historical runs. The only simulator changes select scalar
serialization and accumulate host-side evidence after the original scalar
calculations. Initializer, integration loop, force/update/RNG kernels, GPU stress
kernels, streaming adapter, shared correlators and normalization are unchanged.
All original observations, including step0 and nonselected frames, still run.
Stretch/bend cross terms remain in the complete stress before correlation.

The new host-only `semiflexible_scalar_output.h` retains 88 bytes per chain plus
at most64 bytes of selected-step capacity, independent of integration duration.
There is no new GPU allocation or kernel. Original workspace guards include the
extra allocation. One explicit Makefile header dependency ensures incremental
rebuilds of this writer; compile/link commands and existing targets are unchanged.
Separate `build/scalar-v1/{single,double}` binaries preserved existing binaries.

Exact schemas, field units and checksum recurrence are frozen in
[STAGE4A3C_OUTPUT_SCHEMA_V1.md](STAGE4A3C_OUTPUT_SCHEMA_V1.md), SHA256
`78d112f65ed47083976fd692edf959a051bd5b3a85f80dae87fdfc1c7c10deaa`.
Compact replaces only `samples.csv`:

| File | Retained information |
|---|---|
| scalar_statistics.csv | Ascending chain IDs; all-frame counts, finite counts, first/last steps and schedule checksum; all-frame minimum bond length; original final-half means of Re²,Rg²,tangent1..min(4,N−1); record checksum |
| scalar_metadata.json | Explicit profile/schema/hash, dimensions, sampling schedule, windows/counts, selected steps, global minimum, aggregate checksums and actual extra host/GPU allocation |
| scalar_selected.csv | Original scalar columns at exact scheduled times0,T/4,T/2,3T/4,T only |

For S steps and stride s, observations are0,s,...,floor(S/s)*s. The original
final-half condition is step>=floor(S/2), including an on-grid boundary. Selected
quarters must be integral steps divisible by s; no rounding or invented final
observation. S=0 selects step0 only. Streaming incomplete final batches and
multi-tau incomplete blocks retain their accepted behavior.

Initial/final coordinates, parameters, initial bonds, original final-half bond
moments/histograms, stress moments/correlations, optional reference stress dumps,
diagnostic files and numerical-failure snapshots are retained. Every scalar is
checked for finiteness. A first nonfinite scalar or summary overflow records
step/chain/reason and the complete observed configuration in scalar_failure.json
and scalar_failure_positions.csv. These invalidate acceptance; no update is
skipped or potential regularized. Existing force failure behavior is unchanged.
Smooth b0=0 collapsed flexible bonds remain force-defined; undefined tangents
remain NaN and fail unchanged frozen analyzer rules. Compact summaries do not
reconstruct omitted trajectories or supply unmeasured all-time MSDs.

## Analysis, operational overlay and execution management

The host analyzer accepts both schemas. Compact validation checks exact schema
keys/version/hash, schedule/window bounds, ordered chain and selected-frame IDs,
counts, finite status, minima and checksums. Original required stress/bond outputs,
chain clusters, scientific formulae and thresholds remain unchanged. It rejects
legacy samples.csv in compact output and compact artifacts in full output.
Coverage/value checksums detect accidental corruption; SHA256 receipts bind files
to their completed run. They are not signatures against adversarial rewriting.

`tests/semiflexible_stress_profile.py` generates an authenticated operational
overlay against an unchanged original full parent. The parent generator, frozen
plan and all282 original scientific commands are unchanged. The overlay contains
174 compact stream/memory runs and108 full diagnostic/reference runs. Derived
entries explicitly map parent IDs to new run/profile IDs, new output directories
and separately selected binary paths; only compact entries add the profile flag.
Parameters remain in the preserved parent root. Authentication reconstructs the
entire mapping and refuses modified scientific arguments or plan/schema hashes.
This is an output-schema/operational addendum, not a scientific-protocol amendment.

Provenance records distinguish approved legacy/current driver source identities
and pin executables. Separate profile identities protect receipts, checkpoints,
prerequisites and cache reuse; old full receipts remain readable. Changed analysis
versions recompute rather than reusing stale calculations. The compact profile
also requires the new bounded scalar suite in its prerequisite proof.

Production monitoring uses flushed initial_bonds.csv records in either profile.
Disk monitoring records selected/full CSV bytes plus total bytes. Receipts
durably distinguish child_execution, postprocessing, file_validation, hashing and
completed stages, preserving child exit/time and explicit failed/interrupted
states. A child exit0 is not completion. Pilot projections distinguish serialized
scalar frames from actual stress frames: all stress-frame costs remain. Scalar
disk projections exclude compact summaries and are explicitly approximate.

## Bounded verification

All commands were timeout-bounded, each well below10 minutes. No long campaign
or large CPU reference ensemble was run. New7-test suite:12.971 seconds.

* Both precisions, N1,2,8, homogeneous/heterogeneous coefficients, zero/mixed/
  active bending, odd/even S, nonunit kBT1.7, exact/off-grid quarters, initial and
  final observations, and incomplete batches passed full/compact comparisons.
* Initial/final coordinates, every six-channel stress sample, complete moments,
  correlations/raw correlations and uncertainties, bond statistics/histograms,
  initial bonds and parameters were byte-identical. Nontiming metadata and
  allocation/launch/frame counts matched. Prefix replay at S0..5 in both
  precisions checked every update in that fixture.
* Preserved old binaries and new default-full binaries produced byte-identical
  nontiming files. No former full output was changed for compact compatibility.
* Independent NumPy reductions of original scalar CSVs matched compact per-chain
  means with absolute+relative tolerance2e-14: different summation order in float64
  justifies this rounding allowance. Minima and selected rows matched exactly.
  GPU force/stress precision tolerances remain those of the existing suites.
* Smooth collapsed Gaussian bonds preserved trajectories/stress and zero-angular
  launches; undefined flexible tangents produced explicit compact failure evidence.
  Collapsed active angles were rejected identically in both profiles/precisions.
* Deliberate missing/duplicate/reordered chains/frames, wrong counts/final-half
  counts, profile/version/schema hash, schedule checksum, minima, NaN summaries,
  missing metadata and scientific overlay mutation were rejected. Cross-profile
  checkpoint reuse failed. Mocked interrupted validation/hashing preserved stage,
  child success and interruption state; monitoring recognized compact production.
  Completed compact receipts and pilot disk/runtime estimates were checked with
  real bounded outputs and a mocked independent diagnostic result.
* Existing Rouse `make check`: passed in both precisions, including worker
  ASan/UBSan/LSan and GPU pipeline/RNG checks. Lifetime sanitizer passed200 cycles.
* Existing `check-semiflexible`: both precisions passed7 GPU+2 host+12 CPU tests.
  Existing stress GPU/stream suite:7 tests per precision, including cross-precision
  arguments. Independent CPU stress11/reference12 and host readiness13 passed.
  Intentional failed/incomplete analyzer fixtures are expected test output.
* Python compilation, whitespace checks, profile generation/authentication and
  CLI pilot listing passed. No pilot was launched. Archive SHA256 verification
  passed233 Stage4A.2 files and5 Stage2B N100 files. Frozen plan SHA remains
  `efd040ceba8cd903dee7a145296dce08435e3df3efa940c65170f4bcf98acb36`.

## Measured bounded output size, memory and timing

Fixture: N8,C128,kappa10,kBT1.7,dt0.0001,S400,stride1,seed433501,workers2,
batch7, no raw stress dump.401 original frames;51,328 original scalar rows.
These are actual file sizes from the final bounded suite, including simulator
metadata but excluding test logs/host-runner monitoring. Timing serialization
can change total bytes slightly between repetitions.

| Measurement | Single full | Single compact | Double full | Double compact |
|---|---:|---:|---:|---:|
| Scalar CSV/replacement bundle bytes | 12,396,136 | 170,582 | 12,393,727 | 170,600 |
| All simulator output bytes | 12,806,343 | 580,803 | 12,803,892 | 580,777 |
| Serialized original scalar rows | 51,328 | 640 | 51,328 | 640 |
| Additional compact host capacity bytes | 0 | 11,328 | 0 | 11,328 |
| Model+stress GPU allocation bytes | 71,792 | 71,792 | 127,188 | 127,188 |
| GPU integration ns/bead/step | 25.934167 | 27.370069 | 69.644236 | 69.856736 |
| Overall production ns/bead/step | 447.522914 | 180.529082 | 497.741274 | 231.633379 |

Scalar storage decreased about72.7-fold; total output about22-fold. Compact
also writes128 summary rows and one small metadata record. Allocation numbers
are measured model/vector capacities, not total process RSS or whole-device
usage. Original observation/readback costs remain. Overlapping timers are not
summed. These tiny, sequential functional runs do not establish long-run speedup,
production memory stability or server performance. Optional raw stress dumps
still scale with frames/chains and are intentionally retained for direct tests.

## Remaining limits and host preparation

Scientific Stage4A.3c acceptance remains pending independent host execution.
No thresholds, physics or protocol were amended. Long-run resource behavior,
runtime and disk growth require the separately authorized new-profile pilot.
The original interrupted pilot was neither inspected nor adopted. Existing frozen
plan ambiguities remain documented separately; no terminal spectrum, convergence
order, viscosity or slip-spring claim follows from these tests.

Copy-and-paste both-precision builds, bounded demo/tests and preparation-only
host commands are in README's **Running the current simulator** section. Generate
the original full parent, generate its new compact-v1 overlay, then use the
manager's `list --pilot`. Keep both roots and existing campaign binaries. Do not
execute the generated pilot until separately authorized on the Linux host.
