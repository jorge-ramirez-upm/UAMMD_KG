# Validated GPU Rouse chains and Stage 4A.2 semiflexible dynamics

The validated Rouse executable in this standalone UAMMD/CUDA example simulates
independent Gaussian chains with local Euler–Maruyama Brownian dynamics. It is a distinct coarse-grained model
from Kremer–Grest molecular dynamics. Stage 1 implements equilibrium Gaussian
initialization, free-end harmonic forces, unwrapped updates, conformation
observables and direct-lag dynamic validation. Stage 2A adds double-accumulated
GPU per-chain configurational stress, direct-lag stress correlations and permanent
performance reporting. Stage 2B adds bounded synchronous/asynchronous Correlator6
streaming and the chain-density-normalized relaxation modulus.
**STAGE 2B COMPLETE — STREAMING STRESS RELAXATION VALIDATED**.
The validated Rouse reference has Stage 1/2A regressions, the full 54-simulation
Stage 2B matrix, N32 terminal 504/504 checks, accepted parallel CPU processing,
million-step memory 728/728 checks, and N100 terminal 686/686 checks. The
[N100 results](STAGE2B_N100_TERMINAL_RESULTS.md) include a permanent text-artifact
archive and hashes. Slip-spring physics has not been implemented or validated.
User-executed Linux-host results show byte-identical correlations across tested
worker counts, 728/728 analytical 5-SE checks in the million-step memory run,
and 6.28x single-precision overall speedup at 16 workers. On the RTX 3060 Ti /
i7-12700 development host, prefer async streaming with `--cpu-workers 16 --batch 128`
for the tested N32/4096-chain workload. Defaults remain unchanged. Production
servers require separate benchmarking; this is not a universal optimum.
See [STAGE2B1_HOST_RESULTS.md](STAGE2B1_HOST_RESULTS.md) for measurements,
provenance and artifact hashes. Stage 3 remains unauthorized. Stage 4A.2 adds a
separate semiflexible executable. **STAGE 4A.2 ACCEPTED — GPU SEMIFLEXIBLE
BACKBONE SCIENTIFIC VALIDATION PASSED** on the independent 204-experiment host
campaign. Acceptance is limited to tested configurations/tolerances; coarse-step
bias was unresolved, so no convergence order is claimed. Stage 4A.3b implementation
is accepted; Stage 4A.3c scientific host execution requires separate authorization.

A Rouse chain has **N springs and N+1 beads**, numbered 0 through N. Units are
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

## CPU stress theory and reference (Stage 4A.3a)

Stage 4A.3a adds a separate float64 CPU reference and bounded independent tests;
it does not add GPU stress sampling or correlations to either simulator.
[STAGE4A3A_REPORT.md](STAGE4A3A_REPORT.md) derives the full positive affine virial
`W=V*sigma=sum(g outer q)=-sum(F outer (r-r_ref))`, including bending.
Each angular contribution is symmetric and traceless. At isotropic equilibrium,
`<W_stretch>=N*kBT*I`, `<W_bend>=0`; the full configurational mean is hydrostatic,
not zero. Volume and chain density are external normalization inputs.

From the repository root (Python 3 + NumPy; the new suite takes a few seconds):

```sh
timeout 120s python3 examples/slip-springs/tests/test_semiflexible_stress.py
python3 examples/slip-springs/tests/test_semiflexible_reference.py
PYTHONPATH=examples/slip-springs python3 - <<'PY'
from semiflexible_reference import Chain
from semiflexible_stress_reference import virials
model = Chain.homogeneous(2, b0=1, kb=3, kappa=4)
result = virials(model, [[0,0,0], [1,0,0], [1,1,0]])
print("Unnormalized virial W:", result['total'])
print("Shears xy,xz,yz:", result['shears'])
print("Raw normal differences xx-yy,xx-zz,yy-zz:", result['normal_differences'])
PY
```

`virials` returns `stretch`, `bend`, `total` (3x3), plus total-tensor `symmetric`
(xx,yy,zz,xy,xz,yz), `shears` and `normal_differences`. No volume division,
symmetrization or trace projection is performed. All-zero bending skips angular
operations; inactive angles are skipped individually. That CPU milestone left the existing reference,
accepted dynamics, RNGs, tests, builds and frozen plans unchanged.

For future isotropic Green–Kubo calculations, the existing raw six-channel
weights 1/5 for shears and 1/30 for normal-difference products remain valid.
If their weighted raw-W covariance is H, `G=(C/V)*H/kBT` and
`g=G/[(C/V)*kBT]=H/(kBT)^2`. The existing Rouse convention has kBT=1.
Stretch/bend cross-correlations must be retained in the total stress; no
arbitrary physical melt modulus is assigned here. The Stage 4A.3b extension
below uses this accepted derivation; Stage 4A.3b is accepted; Stage 4A.3c scientific host execution
still requires separate authorization.

Do not run work expected to exceed 10 minutes in Codex; provide instructions
for the dedicated Linux host instead, as recorded in AGENTS.md. No production
campaign is needed for these static CPU checks.

## GPU stress and streaming (Stage 4A.3b accepted; host validation pending)

[STAGE4A3B_REPORT.md](STAGE4A3B_REPORT.md) documents the complete read-only GPU
virial and the unchanged Stage 2B `Bank`/persistent `CpuWorkers` reuse. This
initial adapter is **synchronous**: no background consumer or transfer overlap.
Forces/update/RNG kernels and Rouse code remain unchanged. The nonlinear model
is not assigned Gaussian Rouse relaxation times. No stress-relaxation scientific
acceptance is claimed from bounded verification.

```sh
make -C examples/slip-springs check-semiflexible-stress CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check-semiflexible-stress CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
```

Both short examples below are bounded and tested (N8,C64,dt0.0001,20 steps,
stride5,seed433101,kBT1.7,kb30,b0=1,kappa2). Output child directories must be new:

```sh
STRESS_RUNS=$(mktemp -d /tmp/semiflexible-stress.XXXXXX)
examples/slip-springs/build/single/semiflexible --springs 8 --chains 64 --dt 0.0001 --steps 20 --sample 5 --seed 433101 --kbt 1.7 --kappa 2 --stress-mode stream --stress-batch 7 --cpu-workers 2 --corr-levels 5 --corr-slots 8 --output "$STRESS_RUNS/single"
examples/slip-springs/build/double/semiflexible --springs 8 --chains 64 --dt 0.0001 --steps 20 --sample 5 --seed 433101 --kbt 1.7 --kappa 2 --stress-mode stream --stress-batch 7 --cpu-workers 2 --corr-levels 5 --corr-slots 8 --output "$STRESS_RUNS/double"
```

A moderately long **user-host** example (not run in Codex), N8,C512,
20,000 steps,dt0.0001,stride100,seed433108; review before execution:

```sh
examples/slip-springs/build/double/semiflexible --springs 8 --chains 512 --dt 0.0001 --steps 20000 --sample 100 --seed 433108 --kappa 2 --stress-mode stream --cpu-workers 4 --stress-batch 32 --output "$STRESS_RUNS/moderate"
```

`--stress-mode off` is the default and allocates no stress resources.
`--stress-input FILE` evaluates prescribed configurations without integration,
using the existing whitespace x y z format and parameter-file pathway; it
selects diagnostic mode. `--stress-mode diagnostic` can also record tensors
at observation frames of a short trajectory. `stress_tensors.csv` contains
separate stretch/bend/total **raw nine-entry** W tensors, so symmetry and bending
trace are checked before channel extraction. Input force/position buffers are
compared byte-for-byte after a prescribed-configuration stress probe. Both
precisions use double stress arithmetic/reductions on stored coordinates and
precision-rounded parameters. No stock angular virial is substituted.

Streaming produces:

* `stress_correlations_raw.csv`: exact reused Bank output; its legacy `g,g_se`
  column names represent raw **H,H_se** for this model at arbitrary kBT.
* `stress_correlations.csv`: unambiguous H,H_se, six raw channel product correlations/SE,
  lag/count/block fields, and dimensionless g,g_se=H,H_se/(kBT)^2. Supply a
  positive `--chain-density NC` to add G,G_se=NC*H,H_se/kBT. Without density,
  G columns are absent and metadata density is null; no volume is assigned.
* `stress_moments.csv`: per-chain final-half frame count, six means, and all
  36 raw channel products. These do not subtract empirical trajectory means.
  With no selected final-half frame the count is zero and moments are nan.
* `stress_metadata.json`: frame/worker/batch counts, actual GPU capacities,
  force-independent angular launch counters, timing scopes and estimates.
* Optional `--stress-dump 1`: `stress_samples.csv` with step,chain and the six
  raw channels. It grows with frames and is for bounded/direct reference runs;
  it is disabled in ordinary streaming. Existing scalar conformation output
  and its fixed cadence remain unchanged, and grow as already documented.

Channels remain xy,xz,yz,xx-yy,xx-zz,yy-zz without factors1/2 or1/4. The total
virial is assembled before correlation, automatically retaining cross terms.
The estimator is a raw product of complete nonoverlapping block means with
chain-cluster SE, not a finite-trajectory mean-subtracted connected estimator.
All measured frames enter the bank; a partial last batch is drained. Incomplete
coarse blocks are not padded, and the legacy highest-populated-level export
omission is preserved. Sample timing is step0 and exact stride multiples;
a partial final integration interval is not an extra observation. The inherited
KG admission limit `xy > -1e10` is checked explicitly and is not regularized.

At all-zero kappa there is no angular stress allocation, geometry or kernel
launch. Active streaming angles add directly to the total tensor; their
separate diagnostic buffer is also absent in stream mode. Skipped inactive
angles and finite-result/symmetry/trace diagnostics are regression conditions.
Stress failures abort with `stress_failure.json` and a coordinate snapshot;
force/input errors retain the accepted existing diagnostics.

The adapter has O(chains*levels*slots + batch*chains) CPU memory and O(chains)
additional GPU memory, independent of steps. Buffer/bank budgets are checked
alongside the existing 2 GiB workspace estimate (excluding CUDA context,
allocator overhead and worker stacks). GPU integration ns/bead/step remains
separate from overall production cost. Stress GPU, D2H, synchronization, CPU
pool, barrier/worker-time sum, moment/dump output and finalization are reported
separately. Subset/overlapping timers must not be summed. Stress-on main metadata
uses timer_version2 because final output includes stress exports/metadata;
stress-off retains version1. No sampling-frequency optimization is applied.

The **frozen, unexecuted** Stage 4A.3c plan is
[STAGE4A3C_VALIDATION_PLAN.md](STAGE4A3C_VALIDATION_PLAN.md). Generate/review only:

```sh
STRESS_HOST=$(mktemp -d /tmp/semiflexible-stress-host.XXXXXX)
python3 examples/slip-springs/tests/semiflexible_stress_host.py --output "$STRESS_HOST/campaign"
```

This generates 282 commands in diagnostic, main stream, direct-reference and
memory scripts plus a plan hash; it never runs them. There is no --run option.
Stage 4A.3b is accepted. Separate authorization is required before host execution;
scripts require `STAGE4A3B_REVIEWED`. Some proposed runs can take hours and
must never run in Codex. The plan includes explicit failure/terminal-support
gates; its diagnostic/direct tools are not a complete scientific acceptance
analyzer. Stage 4A.3c experiments and Stage 4B remain unauthorized here.

## Host-validation readiness (Stage 4A.3b.1)

The [scalar-output audit](STAGE4A3B2_OUTPUT_AUDIT.md) identified the 9.876GB pilot
scalar CSV. Stage 4A.3b.2b implements its opt-in compact profile, with every
scalar still evaluated and every stress frame retained. See the
[implementation report](STAGE4A3B2_IMPLEMENTATION_REPORT.md) and
[output schema V1](STAGE4A3C_OUTPUT_SCHEMA_V1.md). The frozen scientific plan
and original campaign remain unchanged. No pilot restart or scientific host
execution is authorized by this implementation task.


[STAGE4A3B1_REPORT.md](STAGE4A3B1_REPORT.md) describes the complete host analyzer,
resumable serial runner and scientific limitations. Simulator, build, accepted
references, correlators, original generator and frozen plan are unchanged.
No Stage 4A.3c experiment or Stage 4B work is authorized by this readiness task.
[Clarification proposal V1](STAGE4A3C_CLARIFICATION_PROPOSAL_V1.md) records
operational ambiguities separately; it does not amend the frozen criteria.

Bounded tests (existing single/double binaries, no rebuild needed):

```sh
timeout 180s python3 examples/slip-springs/tests/test_semiflexible_stress_campaign.py examples/slip-springs/build/single/semiflexible examples/slip-springs/build/double/semiflexible
```

Preparation only, without executing experiments:

```sh
HOST_ROOT=$(mktemp -d /tmp/semiflexible-readiness.XXXXXX)
python3 examples/slip-springs/tests/semiflexible_stress_host.py --output "$HOST_ROOT/campaign"
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" list --pilot
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" analyze --pilot
```

An unexecuted pilot returns **INCOMPLETE/exit2**, as intended. Analysis authenticates
all282 commands, copied plan/hash and parameter inputs before looking at results.
JSON/CSV validation rejects missing or duplicate frames/IDs, malformed parameters,
wrong counts/normalization, singular/nonfinite failures and incomplete outputs.
It checks separate tensors, independent static ensembles, exact finite-acquisition
Gaussian EM theory, direct multi-tau references, timestep/replica gates, operational
terminal support, and memory/performance evidence. Independent chains are clusters;
no empirical trajectory-mean subtraction or nonlinear Rouse spectrum is introduced.

Outputs are `scientific-analysis.json`, `scientific-summary.txt` and authenticated
`analysis-checkpoint.json`. Repeated analysis reuses unchanged completed results;
`--verify-hashes` performs a deep file-content audit. Live outputs are not scanned.
Scientific status and provenance readiness are separate; missing data/support,
unknown compiler evidence and unresolved bias are not silently labeled passing.
Raw long CSVs are streamed; only frozen short direct-reference sequences use a
bounded32MiB workspace. Fixed65536-chain CPU reference preparation is host-only.

For a **separately authorized** Linux-host pilot, run the following there. The
pilot is the unchanged frozen N8,kappa10,single,seed433201,dt0.000025 member:
8,000,000 steps,C2048,stride400, plus its matching zero-step tensor diagnostic.
Runtime/disk planning comes from the completed full pilot, never the tiny tests.

```sh
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" prerequisites --authorize-host-execution STAGE4A3C
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" run --pilot --phase diagnostic --authorize-host-execution STAGE4A3C
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" run --pilot --authorize-host-execution STAGE4A3C
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$HOST_ROOT/campaign" pilot-report
```

The runner preserves original argv, serializes GPU processes, saves executable/
repository/environment identities, exit/timestamp receipts, process-tree RSS,
whole-device GPU monitoring and disk growth. Partial/failed/orphan outputs are
preserved and refused; verified completions skip, optionally with deep hashes.
No automatic failed-trajectory restart or overwrite. Use `--phase` or `--run-id`
for eventual authorized phases; the same commands resume between complete runs.
An original `--build-log FILE` can be supplied on the first execution-management
command; an archived no-op build still does not prove original compiler identity.
System nvcc is reported separately.

After separate campaign authorization, `references --authorize-host-execution
STAGE4A3C` prepares the fixed independent CPU ensembles resumably, and `analyze`
without selection incrementally processes the entire manifest. Missing references
or sparse monitoring remain incomplete. Scientific acceptance requires the full
frozen gates and provenance review, not a successful pilot or exit status alone.
No simulation expected to exceed10 minutes may run in Codex.

## Running the current simulator

`--scalar-output full|compact` defaults to `full`, preserving existing files and
Stage 4A.2 behavior. `compact` requires `--stress-mode stream`. It replaces
`samples.csv` with `scalar_statistics.csv` (per-chain original final-half means,
all-frame minima/counts), `scalar_metadata.json` (coverage/checksums/version) and
`scalar_selected.csv` (scheduled exact quarter-time frames). It retains all
stress and bond outputs. These summaries cannot reconstruct the omitted scalar
trajectory. Stress stride, physics, RNG and correlator are unchanged.

Use separate binaries to protect existing campaigns. From the repository root:

```sh
SCALAR_BUILD="$PWD/examples/slip-springs/build/scalar-v1"
make -C examples/slip-springs semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single GPU_BUILD="$SCALAR_BUILD/single"
make -C examples/slip-springs semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double GPU_BUILD="$SCALAR_BUILD/double"
timeout 240s python3 examples/slip-springs/tests/test_semiflexible_scalar_output.py "$SCALAR_BUILD/single/semiflexible" "$SCALAR_BUILD/double/semiflexible"
SCALAR_DEMO=$(mktemp -d /tmp/semiflexible-compact-demo.XXXXXX)
"$SCALAR_BUILD/single/semiflexible" --output "$SCALAR_DEMO/run" --springs 8 --chains 128 --kappa 10 --kbt 1.7 --dt .0001 --steps 400 --sample 1 --seed 433501 --stress-mode stream --scalar-output compact --stress-batch 7 --cpu-workers 2 --corr-levels 5 --corr-slots 8
```

The new suite ran both precisions, including this bounded configuration. Prepare
a new compact-profile host pilot **without executing it**:

```sh
SCALAR_HOST=$(mktemp -d /tmp/semiflexible-compact-host.XXXXXX)
python3 examples/slip-springs/tests/semiflexible_stress_host.py --output "$SCALAR_HOST/full-parent" --build "$SCALAR_BUILD"
python3 examples/slip-springs/tests/semiflexible_stress_profile.py --base "$SCALAR_HOST/full-parent" --output "$SCALAR_HOST/compact-v1"
python3 examples/slip-springs/tests/semiflexible_stress_campaign.py "$SCALAR_HOST/compact-v1" list --pilot
```

Keep the parent root: overlay authentication verifies its unchanged 282 commands
and inputs. All derived IDs/outputs/receipts/checkpoints are separate. There are
174 compact stream/memory runs and 108 unchanged full diagnostic/reference runs.
The selected host pilot remains N8,C2048,kappa10,dt0.000025,8,000,000 steps,
stride400,seed433201,single precision. It was not executed here. After separate
host authorization, existing manager actions operate on the **new** root; first
run its `prerequisites` action with the explicit host-execution flag. Never adopt
the interrupted legacy pilot or overwrite its files. Long host durations cannot
be inferred from the tiny output-size fixture. A moderately long example is the
unchanged pilot command prepared above; it is host-only and not a Codex test.

Stage 4A.2 provides a separate **`semiflexible`** executable: exact finite-rest-
length harmonic stretching plus Kratky–Porod bending, free ends, unwrapped
coordinates and Euler–Maruyama overdamped Brownian dynamics. Default mode retains
the accepted backbone behavior. Stage 4A.3b optionally adds stress streaming
with accepted Stage 4A.3b implementation; scientific host acceptance is pending. There
is no excluded volume, hydrodynamics or slip-spring interaction. This model's bounded
checks pass; **STAGE 4A.2 ACCEPTED — GPU SEMIFLEXIBLE BACKBONE SCIENTIFIC
VALIDATION PASSED** (17 October 2026). The original 204-run analysis has zero
statistical failures. The [permanent evidence archive](validation/stage4a2-acceptance/README.md)
preserves original analysis, metadata and separate memory evidence. All 456
timestep bias comparisons were unresolved; no convergence order is inferred.
Acceptance covers the frozen tested cases/tolerances, not arbitrary parameters.
See [STAGE4A2_REPORT.md](STAGE4A2_REPORT.md) and the frozen
[host plan](STAGE4A2_VALIDATION_PLAN.md).

Build and bounded verification (from the repository root):

```sh
make -C examples/slip-springs semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
make -C examples/slip-springs check-semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single
make -C examples/slip-springs check-semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double
```

`all` and `check` retain their Rouse targets. Use the explicit targets above for
this model. `clean-semiflexible` removes only its named binaries/dependency files.
Both short examples below were executed (N=8,C=64,dt=0.0001,20 steps,sample5,
seed42021,kBT=zeta=1,b0=1,kb=30,kappa=2):

```sh
SEMI_RUNS=$(mktemp -d /tmp/semiflexible-stage4a2.XXXXXX)
examples/slip-springs/build/single/semiflexible --springs 8 --chains 64 --dt 0.0001 --steps 20 --sample 5 --seed 42021 --b0 1 --kb 30 --kappa 2 --kbt 1 --zeta 1 --output "$SEMI_RUNS/single"
examples/slip-springs/build/double/semiflexible --springs 8 --chains 64 --dt 0.0001 --steps 20 --sample 5 --seed 42021 --b0 1 --kb 30 --kappa 2 --kbt 1 --zeta 1 --output "$SEMI_RUNS/double"
```

A moderately long **user-host** example, not run in Codex (N=32,C=512,
dt=0.0001,20000 steps,sample100,seed42032; other parameters as above):

```sh
examples/slip-springs/build/double/semiflexible --springs 32 --chains 512 --dt 0.0001 --steps 20000 --sample 100 --seed 42032 --b0 1 --kb 30 --kappa 2 --output "$SEMI_RUNS/moderate"
```

The initial ensemble is drawn directly from the radial Jacobian and conditional
orientation laws on CPU, then uploaded. There is no equilibration flag or need
for artificial burn-in. The uniform per-bead friction is configurable with
`--zeta`; thermal energy is `--kbt`. Seed is unsigned 64-bit; dynamics Philox
domain3 leaves Rouse domains/trajectories unchanged. Reproducibility is within
the same build/standard library and hardware environment, not across precisions.

Heterogeneous coefficients share the same GPU architecture. `--parameters FILE`
overrides scalar b0/kb/kappa and contains: N; N lines `b0[i] kb[i]` for bonds
0..N-1; N+1 kappa entries indexed by **bead**, with exactly zero endpoints.
`--springs` must match N. For example:

```text
3
0.8 20
1.2 40
1.0 30
0 0 3 0
```

Save that text under the fresh output parent, then pass
`--springs 3 --parameters "$SEMI_RUNS/parameters.txt"` with a new child output
directory. Bounded tests exercise this path. Only kb>0,b0>=0,kappa>=0 and
positive kBT,zeta,dt are allowed; derived scales must fit the selected precision.
All-zero kappa allocates no bending GPU storage and launches no bending kernel;
zero entries in mixed arrays are skipped before angular geometry. Requested
tangent *measurements* are computed separately at observation times.

The force-only interface is `--force-input FILE --springs N --chains C` plus
parameters and `--output NEW_DIR`. FILE has C*(N+1) unwrapped x y z triples in
chain/bead order, no header. This disables integration. `forces.csv` holds each
bead's force and energy share; summing energy over beads gives the Hamiltonian.
`initial.csv` records the actual precision-rounded input. `--initial FILE` uses
that format as a supplied starting state while retaining dynamics.

Outputs are bounded in memory, streamed to a fresh directory:

* `metadata.json`: physical parameters, precision, timing scopes, memory estimate,
  actual bending allocation capacity and launch counters. `parameters.txt` saves
  precision-rounded heterogeneous arrays. Zero-step rates are JSON null.
* `samples.csv`: per-chain length moments, Re^2,Rg^2, COM/monomer MSD from the
  initial configuration, minimum bond length and tangent separations 1..min(4,N-1).
  Samples are at step0 and exact stride multiples; a final partial interval is
  integrated and validated but not sampled.
* `initial_bonds.csv`: individual initial lengths. `bond_statistics.csv`:
  per-chain/per-bond mean, second moment and 32 fixed histogram bins plus overflow,
  accumulated over observation frames in the final half of production. Bin edges
  are uniform from zero to metadata's histogram_max; bin32 is overflow. These
  per-chain statistics support clustered uncertainties without retaining trajectories.
* `initial.csv` and `final.csv`: coordinate snapshots. On a numerical failure,
  `failure.json`, `failure_positions.csv` and (for failed proposals)
  `failure_proposal.csv` preserve the first failing step, selected bead and geometry.
  Error codes 1/2/3/4/5 mean coordinates/stretch/bend/nonfinite force-energy/update.
  Invalid input/configuration errors also return nonzero with a diagnostic.

Undefined active angles and undefined stretching forces are rejected. Smooth
zero-rest-length collapsed bonds are permitted when no active angle touches
them; their tangent measurements are explicitly `nan`, because a tangent is
undefined. No force or step is clamped, regularized or silently skipped.

Per-step diagnostics synchronize with the GPU. Integration event timing includes
force/update kernels, diagnostic D2H and host launch/sync gaps; observation/D2H,
CPU reduction/formatting and output are separate. Full-coordinate observation
readback is an initial correctness choice, not a production throughput claim.
Initialization (including first CUDA setup and saved initial state) is separate.
Workspace has a conservative 2 GiB cap excluding the CUDA context; storage is
O(C*N) and independent of trajectory length. Scalar sample files grow with
C*frames. No observation-frequency optimization is applied.

Independent **user-host** replication commands (204 runs; long work, never
executed in Codex). The original campaign is now accepted and archived; no
rerun is needed for this documentation closure. For a separately authorized
replication, first generate/review commands without running simulations:

```sh
SEMI_HOST=$(mktemp -d /tmp/semiflexible-host.XXXXXX)
python3 examples/slip-springs/tests/semiflexible_host.py --output "$SEMI_HOST/campaign"
cp examples/slip-springs/STAGE4A2_VALIDATION_PLAN.md "$SEMI_HOST/campaign/validation-plan.md"
git rev-parse HEAD > "$SEMI_HOST/campaign/commit.txt"
nvidia-smi > "$SEMI_HOST/campaign/gpu.txt"
# User-host execution only:
bash "$SEMI_HOST/campaign/commands.sh"
python3 examples/slip-springs/tests/semiflexible_host.py --analyze "$SEMI_HOST/campaign"
```

The analyzer writes `analysis.json` and returns nonzero on a statistical gate
failure. It streams input rows and clusters by chain. Passing it is necessary;
the frozen plan also requires manual host evidence. The completed campaign's
user-supplied acceptance and archived memory records are documented in the report.
For future replications, preserve the same evidence requirements. It refuses to
overwrite `analysis.json`; retain each analysis as evidence. Do not apply Gaussian
Rouse predictions to finite-rest-length dynamics. The Gaussian controlled case
in the plan has b0=0,kappa=0 specifically to provide an independent exact test.

The separate memory comparison (N=8,C=2048,kappa10,dt0.00005,sample400,
seed420201) measured peak RSS 108556/108392 KiB and GPU run plateaus of 145/145
MiB at 20000/400000 steps. GPU monitoring is whole-device, not process-specific;
the small RSS difference is not interpreted as growth/shrinkage. Integration
costs were 1.934/1.944 and overall costs 2.926/2.939 ns/bead/step on this host.
No production-server claim follows. Host system nvcc was reported as CUDA
11.5.119; development used CUDA 13.0.88, but the host build was a no-op, so the
original campaign compilation toolkit remains unverified. See the report for
full provenance. Synchronous diagnostics/CPU observations and singular-geometry
timestep limitations remain. `rouse` is unchanged; no stress extensions or
slip-springs are introduced. [ROADMAP.md](ROADMAP.md) retains the UAMMD reuse
review as future work; scientific acceptance does not establish faster or
simpler infrastructure.

The Stage 4A.1 CPU reference remains available independently:


Stage 4A.1 adds a separate **CPU equilibrium reference**, always in float64;
`rouse` and its validated model are unchanged. The scientific contract, force derivation,
sampling proof and UAMMD assessment are in [STAGE4A1_REPORT.md](STAGE4A1_REPORT.md).
Run the bounded new tests from the repository root (Python 3 + NumPy):

```sh
python3 examples/slip-springs/tests/test_semiflexible_reference.py
```

A short independent-equilibrium example (N=4, 1024 chains, seed 41001,
b0=1, kb=30, kappa=2, kBT=1; no dt, steps or sample stride because there is no
time integration; results go to stdout):

```sh
PYTHONPATH=examples/slip-springs python3 - <<'PY'
import numpy as np
from semiflexible_reference import Chain
model = Chain.homogeneous(4, b0=1, kb=30, kappa=2)
r = model.sample(1024, np.random.default_rng(41001), kbt=1)
print("Predictions:", model.equilibrium_predictions(kbt=1))
print("Sample mean Re^2:", np.mean(np.sum(r[:, -1]**2, axis=1)))
print("First chain energy:", model.energy_forces(r[0])[0])
PY
```

Heterogeneous construction uses N-entry `b0`, `kb` and N+1-entry bead-indexed
`kappa` with zero endpoints, e.g. `Chain([0.4,1,2], [3,10,5], [0,0.3,4,0])`.
The historical Rouse build/run commands below retain their existing interface.
Their bounded checks were rerun in both precisions for Stage 4A.2.

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

Stage 2B is complete for the independent Rouse reference; the
[N100 closure record](STAGE2B_N100_TERMINAL_RESULTS.md) collects the scientific
evidence, and [Stage 2B.1 host results](STAGE2B1_HOST_RESULTS.md) document parallel
performance and memory acceptance. The existing roadmap assigns benchmarking
and optimization to Stage 3, then semiflexibility and slip-spring dynamics to
Stage 4. No next stage is authorized. See
[NEXT_STAGE_ASSESSMENT.md](NEXT_STAGE_ASSESSMENT.md) for the unresolved model,
kinetic, statistical and GPU design decisions; no slip-spring model is validated.
