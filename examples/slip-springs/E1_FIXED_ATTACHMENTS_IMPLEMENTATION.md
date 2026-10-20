# E1 Stage A — fixed-anchor, fixed-attachment implementation (development only)

Status: **code committed; CUDA build and GPU regression not executed in the assistant environment**. This stage implements only the already approved E1 annealed initializer and harmonic force term. It does NOT implement contour hopping, end escape, renewal, host constraint release or virtual-spring stress.

## Opt-in interface

The existing `semiflexible` executable gains:

- `--slip-count Z`: globally conserved number of active fixed springs, default `0`.
- `--slip-ms2 A2`: desired equilibrium mean-square connector extension, required positive and representable when `Z>0`.

Existing default settings and validated backbone stretch/bend and Brownian noise paths are unchanged when `Z=0`. Stress modes other than `off` are explicitly refused when active springs are requested: the currently implemented stress correlator excludes the physical partial-response cross term, and its results must not be presented as slip-spring rheology. Do not use these fixed springs for terminal polymer dynamics.

For `Z>0`, the existing exact bare-backbone initializer runs first (or prescribed input coordinates are read). A separate seeded CPU RNG chooses `Z` distinct bead sites uniformly without replacement, then samples Cartesian anchor displacements from `Normal(0, A2/3)`. Anchors and assignments remain frozen for the whole trajectory. The file `fixed_slip_springs.csv` records chain, bead and fixed anchor coordinates.

The new opt-in GPU kernel adds for each occupied bead `i`
```text
U_ss,i = (3*kBT/(2*A2)) * |r_i-a_i|^2
F_ss,i = -(3*kBT/A2) * (r_i-a_i)
```
to the existing per-bead energy/force buffer following the unchanged stretch/bend kernels. One thread owns one bead; no atomics, overlaps or springs-to-springs forces are required. The old update kernel then uses the *total* force. The initial spring distribution is exactly conditional Gaussian (subject to arithmetic precision), making the joint ensemble annealed even though springs subsequently remain quenched per trajectory.

There is **no new numerical timestep acceptance** for active springs: stiffness `3*kBT/A2` adds a local fast relaxation mode and could require a shorter BD timestep.

## Short GPU-host verification (not performed here)

From the repository root on a machine with nvcc and a compatible CUDA GPU, execute:

```sh
make -C examples/slip-springs check-fixed-slip-springs PRECISION=double CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86
```

Select an appropriate `CUDA_HOME` and `CUDA_ARCH` for the host. The bounded regression uses 2 chains × 4 beads, fixed prescribed coordinates, and no integration steps; it checks spring force/energy differences relative to the zero-spring reference, unique occupied sites, deterministic replay and explicit zero-spring force recovery. Run a single-precision build separately if desired. **Compilation and tests are pending user-host verification.**

Example opt-in *development-only* short run after that check:

```sh
OUT=$(mktemp -d /tmp/e1-fixed.XXXXXX)
examples/slip-springs/build/double/semiflexible \
  --springs 8 --chains 64 --kappa 2 --dt 0.0001 \
  --steps 100 --sample 10 --seed 4317 \
  --slip-count 32 --slip-ms2 5 --stress-mode off \
  --output "$OUT/test"
```

The chosen numerical values in this command are demonstration inputs, not host calibration or accepted physical parameters.

## Scientific boundary

See `EQUILIBRIUM_MODEL_E1.md` for the equilibrium measure, canonical population, hopping and renewal detailed balance. With frozen spring identities, trajectories sample conditional ensembles; correct initial *annealed* statistics are recovered only across properly initialized chains/replicas. No claim of physical long-time reptation or of a slip-spring relaxation modulus can be inferred from Stage A.

The next stage, only after code review and host checks, is local discrete Metropolis hopping with exclusion. Renewal remains separate.
