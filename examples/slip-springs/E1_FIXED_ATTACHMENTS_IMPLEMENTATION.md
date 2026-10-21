# E1 Stage A — fixed-anchor, fixed-attachment implementation (development only)

Status: independently audited on 21 October 2026. CPU initialization checks and
bounded CUDA force/integration checks pass in both precisions on the development
RTX 3060 Ti with CUDA 13.0.88. See [the audit](E1_STAGE_A_AUDIT.md) for exact scope,
repairs, provenance and limitations. This is not scientific timestep acceptance.

## Opt-in interface and initialization

The existing `semiflexible` executable gains:

- `--slip-count Z`: fixed global population, default `0`; `0 <= Z <= chains*(N+1)`.
- `--slip-ms2 A2`: equilibrium mean-square connector extension; positive and
  representable in the selected precision when `Z>0`. The derived stiffness
  must also be finite, positive and representable.

The exact bare-backbone initializer runs first, followed by uniform sampling of
`Z` distinct bead sites without replacement and independent Gaussian anchor
components with variance `A2/3` about the stored bead positions. The CPU engine
is `mt19937_64`, seeded with both halves of the simulation seed and domain
`0x53117`; it consumes neither backbone initialization nor Philox dynamics
counters. Replay is supported for the same executable/standard library and
precision, not promised across platforms. Arithmetic rounding and finite RNG
tails remain. Prescribed `--initial`/`--force-input` coordinates receive the same
conditional anchor initialization, but are not certified backbone equilibrium.

`fixed_slip_springs.csv` records chain, bead and fixed anchor coordinates in
simulation precision. Each occupied bead owns one spring, including end beads.
The file is explicitly closed with write-error checking. Anchors and attachment
indices remain unchanged for the entire trajectory.

## GPU force, energy and disabled path

One thread owns each bead and adds

```text
U_ss,i = (3*kBT/(2*A2)) * |r_i-a_i|^2
F_ss,i = -(3*kBT/A2) * (r_i-a_i)
```

after the existing stretch/bend kernels, on the same stream. The spring energy
is counted once, entirely on its attached bead; summing the `energy` column of
`forces.csv` gives total backbone plus spring energy. The unchanged update uses
the total force. Nonfinite totals use the existing deterministic diagnostics
and snapshots. There is no spring stress estimator; active springs reject every
stress mode except `off`.

`Z=0` constructs no spring RNG, allocates no spring arrays and launches no spring
kernel. The validated backbone force/update/RNG paths are unchanged. Metadata
adds `slip_count`, requested `slip_ms2`, `slip_effective_stiffness`, `slip_mode`,
`slip_device_bytes`, `slip_launches`, and `slip_initialization_rng_domain`.
Inactive numerical parameters/domain are null. Spring host/device arrays and
the temporary site permutation enter the conservative workspace budget; actual
spring device capacity also enters `device_bytes`. Workspace is independent of
step count; the existing bound excludes runtime/allocator overhead.

## Bounded verification and examples

From the repository root, using the appropriate CUDA toolkit and architecture:

```sh
make -C examples/slip-springs check-fixed-slip-initialization
E1_BUILD="$PWD/examples/slip-springs/build/e1-audit"
make -C examples/slip-springs check-fixed-slip-springs PRECISION=single CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$E1_BUILD/single"
make -C examples/slip-springs check-fixed-slip-springs PRECISION=double CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 GPU_BUILD="$E1_BUILD/double"
```

The CPU target exercises the actual shared initializer in float and double,
including all occupied-site pairs on a tiny lattice, hypergeometric population,
Gaussian component moments, replay, full/zero occupancy and parameter guards.
The GPU target adds a frozen-anchor finite-difference test, scaled-energy and
nonfinite diagnostics, force/energy comparison with the backbone, one-step
added drift, RNG isolation, replay and zero allocation/launch/output recovery.

Tested short development example (N8,C64,dt0.0001,100 steps,stride10,seed4317):

```sh
E1_RUNS=$(mktemp -d /tmp/e1-fixed.XXXXXX)
"$E1_BUILD/double/semiflexible" --springs 8 --chains 64 --kappa 2 --dt 0.0001 --steps 100 --sample 10 --seed 4317 --slip-count 32 --slip-ms2 5 --stress-mode off --output "$E1_RUNS/short"
```

A moderately long **host-only, unexecuted** demonstration changes only duration
and output cadence (N8,C64,dt0.0001,10000 steps,stride100,seed4317):

```sh
"$E1_BUILD/double/semiflexible" --springs 8 --chains 64 --kappa 2 --dt 0.0001 --steps 10000 --sample 100 --seed 4317 --slip-count 32 --slip-ms2 5 --stress-mode off --output "$E1_RUNS/moderate"
```

These parameters are demonstrations, not calibrated physics or accepted
slip-spring timesteps. Outputs must be new directories.

## Scientific boundary

The Gaussian anchor integral is independent of bead position, so the annealed
initial ensemble retains the bare backbone conformational marginal. Fixed
attachments/anchors subsequently give conditional dynamics in each trajectory;
an individual trajectory is not a sampler over anchors/sites. Euler–Maruyama
has finite-step bias and added stiffness can require a smaller timestep. Neither
terminal entangled dynamics nor a physical relaxation modulus is established.

No hopping, escape, renewal, constraint release, stress correlations or
deformation is implemented. Stage A is retained exactly by `--hop-rate 0` (the default); the separately
authorized [Stage B](E1_STAGE_B_REPORT.md) adds interior hopping only. Stage C
has not started.
