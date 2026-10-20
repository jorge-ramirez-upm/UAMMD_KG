# Backbone model and validation

## Model

For bonds `q_i = r_(i+1)-r_i`, `i=0,...,N-1`, the implemented energy is

`U = Σ_i (kb_i/2)(|q_i|-b0_i)^2 + Σ_i κ_i(1-u_(i-1)·u_i)`,

where `u_i=q_i/|q_i|`, angular entries are bead-indexed `i=1,...,N-1`, and endpoint `κ_0=κ_N=0`. The code evaluates the angular term equivalently as `κ_i|u_(i-1)-u_i|²/2`. There are N bonds and N+1 beads, free ends, and no interchain force. Positive `kb`, nonnegative `b0` and `κ`, and positive uniform `kBT` and `zeta` are required. The validated standard choice is `b0=1`, `kb=30`, `kBT=zeta=1`; the unit of time is `zeta b0²/kBT`.

The stretching gradient is `g_i=kb_i(|q_i|-b0_i)q_i/|q_i|`. For an active angle, with `c=u·v`, the force gradients are `A=-κ(v-cu)/|q_(i-1)|` and `B=-κ(u-cv)/|q_i|`, distributed over beads `i-1,i,i+1` as `A`, `B-A`, `-B`. Undefined active collapsed bonds fail explicitly; a collapsed zero-rest-length inactive-angle bond has the documented smooth stretching behavior. No clamp, cutoff, or angular regularization is applied.

## Initialization and dynamics

The initializer samples the exact factorized equilibrium measure: radial bond lengths from the three-dimensional finite-rest-length distribution and successive orientations from the conditional Kratky–Porod law. It does not equilibrate a guessed configuration through dynamics. Coordinates are accumulated from bead zero and remain unwrapped. Each chain is independently initialized; translation is handled separately from internal forces.

The overdamped update is Euler–Maruyama,

`r_i(t+dt)=r_i(t)+(dt/zeta)F_i + sqrt(2 kBT dt/zeta) ξ_i`,

with independent standard Gaussian Cartesian noise. The GPU uses old/new buffers, stable flat IDs, Philox domain 3 for this model, and precision-specific float or double arithmetic. Force, proposal, and final-state checks fail deterministically on nonfinite or undefined geometry. The accepted Stage 4A.2 campaign validates only its tested parameter and timestep matrix.

## Stress observable

The per-chain configurational virial is the positive affine derivative `W=Σ(g outer q)`, with stretch and bend contributions assembled before channel extraction. The six raw channels are `Cxy, Cxz, Cyz, Cxx-yy, Cxx-zz, Cyy-zz`. The isotropic scalar used by the streaming analysis is

`H(t) = [Cxy + Cxz + Cyz]/5 + [Cxx-yy + Cxx-zz + Cyy-zz]/30`.

No volume or melt density is silently assigned. The streaming estimator retains raw products, stretch/bend cross terms, nonoverlapping block means, and chain-level uncertainty. Channels and overlapping origins are correlated and are not counted as independent samples. `G` is exported only when an explicit density is provided.

The first `H(0)/e` crossing is a short-time characteristic of the sampled stress curve. Multiscale relaxation is represented by the multi-tau hierarchy and its block widths; a crossing is not a single-exponential fit. Terminal relaxation requires support at later physical times and a justified tail criterion. Neither Stage 4A.4 T=20 nor a first crossing establishes terminal relaxation.

## Validation and computation

Stage 4A.1/4A.2 CPU and GPU tests cover force/energy agreement, rotations, translations, torque and net-force checks, free ends, N=1, mixed coefficients, collapsed-geometry diagnostics, replay, noise, observables, and both precisions. Stage 4A.2 records 204 independent user-host experiments with zero automated statistical failures. This acceptance is bounded to the tested matrix; it is not a universal timestep or stiffness theorem.

Stage 4A.3A derives and tests the CPU virial reference. Stage 4A.3B reuses the existing KG Correlator6 through a local streaming adapter, with bounded ownership and explicit stress metadata. The frozen Stage 4A.3C campaign distinguishes GPU, transfer, CPU, output, and wall timers; overlapping scopes must not be summed. Stage 2B remains the validated Gaussian/Rouse stress reference and is not evidence for nonlinear terminal behavior.

Stage 4A.4 compares N=8 and N=32 at `kappa=0,10`, using 512 chains, seed 433201, exact initialization, every-step stress, and physical scalar spacing 0.01. Static comparisons use chain clusters and 1%/2% tolerances with three-SE uncertainty. Dynamic comparisons retain six channels, fixed-lag 5% and crossing 10% rules, while reporting H(0) separately. N32 external trajectories and recovery receipts are not part of the Git tree; the committed protocol records their provenance and limitations.

Numerical precision is explicit: scientific GPU runs use the double build, while both float and double implementations are tested. The unchanged correlator has finite hierarchy support, block averaging, sentinel and deepest-level limitations documented in its audit. These are analysis constraints, not reasons to reinterpret unsupported tails as resolved.
