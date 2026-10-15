# Scientific and repository rules

## Isolation and stage gate

ALL project modifications must remain under `examples/slip-springs/`. Never
modify, delete, reformat, or move UAMMD core files, KG, KG_Assoc, other examples,
or repository-wide build/configuration/documentation files. Existing code may
be inspected, included, and linked only as a read-only dependency. Document any
obstacle that would require an outside change and propose a local alternative.
Do not copy entire KG modules. Preserve unrelated work and branch history.

Work on `slip-springs`, never on `KremerGrest`. Keep generated outputs and
compiler products here or outside the repository. Before committing, compare
against the recorded source SHA in STAGE0_REPORT.md and programmatically check
tracked, untracked, and ignored generated paths. Stop and report any outside
change; never silently remove it. Use an isolated worktree when needed.

Only Stage 0 is authorized initially. Do not implement Rouse dynamics until
Stage 0 has been reviewed and approved. Later stages require their own scope:
1. Independent Rouse chains on the GPU.
2. Configurational stress correlations and modulus using Correlator6.
3. Benchmarking and optimization.
4. Semiflexibility and slip-spring dynamics.

## Permanent initial physical model

This is a coarse-grained Gaussian-chain model, distinct from Kremer–Grest MD.
A chain has **N springs and N+1 beads**, with bead indices 0 through N, free
ends, statistical bond length b=1, thermal energy kBT=1, and friction zeta=1
**per bead**. There is no excluded volume, no hydrodynamic interaction, and no
interaction between chains. Coordinates remain unwrapped throughout.

With q_i = r_(i+1) - r_i,

    U = (3/2) sum_(i=0)^(N-1) |q_i|^2.
    dr_i = F_i dt + sqrt(2) dW_i.
    tau_0 = zeta b^2/(kBT) = 1.
    tau_s = zeta b^2/(3 kBT) = 1/3.

Use truly overdamped dynamics, independent Gaussian noise for each bead,
Cartesian component, and time increment, and correct fluctuation-dissipation
normalization. NVT Langevin dynamics with mass and velocity is a different
model. Do not introduce new physics by changing core or existing KG code.

Draw initial conformations directly from equilibrium Gaussian statistics:
independent bond components with mean zero and variance 1/3, accumulated along
the chain. Dynamic equilibration alone is insufficient initialization. Choose
chain translations separately without adding forces or interchain interactions.

## Future stress and validation

Use chain configurational stress

    S_ab^(c) = 3 sum_(i=0)^(N-1) q_ia^(c) q_ib^(c).

The six Correlator6 inputs per independent chain will be, in order:
S_xy, S_xz, S_yz, S_xx-S_yy, S_xx-S_zz, S_yy-S_zz.
Initially feed CPU correlators from GPU stress samples. Reuse
`../KG/correlator.h` and `../KG/correlator.cpp` unchanged; do not copy them.
Read the limitations in STAGE0_REPORT.md before allocating many objects.

Normalize the relaxation modulus consistently with the chain or bead density.
If C chains occupy volume V, chain density is C/V and bead density is
C(N+1)/V. Averaging per-chain correlations must not introduce an extra factor
of C or 1/C. Distinguish chain stress from volume-normalized total stress;
never import KG's volume prefactors without deriving the normalization.

Validate future GPU results against exact **discrete** Rouse predictions for
equilibrium dimensions, center-of-mass diffusion, relaxation times, and stress
relaxation. With M=N+1: <Re^2>=N, <Rg^2>=(M^2-1)/(6M), D_CM=1/M,
and mode decay rates lambda_p=12 sin^2(p*pi/(2M)), p=1,...,M-1.
Stress mode contributions decay at twice these rates. Separate finite-step
Euler–Maruyama bias from statistical uncertainty and floating-point effects.
Check free ends, multiple chains, and the absence of interchain forces.

Start with UAMMD ordinary precision (`real=float`); maintain a documented
`DOUBLE_PRECISION` build for statistical validation. Do not claim double noise
or full double arithmetic solely because coordinates are double. Do not add a
mixed-precision coordinate representation without an approved later scope.
Report actual compilation and execution separately; unexecuted tests never pass.
