# Semiflexible-chain project status

This repository is a validated backbone for a future slip-spring model. Its long-term objective is to study semiflexible chains with dynamically introduced, moved, and removed slip-springs while retaining an independently testable polymer reference. Development-only E1 Stage A fixed-attachment harmonic slip-springs are implemented and independently audited; hopping, renewal and slip-spring rheology remain unimplemented. See [the audit](E1_STAGE_A_AUDIT.md).

The present backbone uses an open chain with **N bonds and N+1 beads**, free ends, unwrapped coordinates, no excluded volume, no hydrodynamics, no periodic wrapping, and independent chains. The finite-rest-length Hamiltonian, exact equilibrium initializer, overdamped Euler–Maruyama update, GPU observations, configurational stress, and CPU reference tools are implemented under this directory. The original Gaussian Rouse path remains available and unchanged.

| Area | Status | Evidence and boundary |
|---|---|---|
| Rouse reference, dimensions, diffusion, stress relaxation | Completed/validated for tested matrix | Stage 1/2A/2B/2B.1 reports and archived N100 results; hardware-specific performance only |
| Nonlinear finite-rest-length semiflexible backbone | Validated for the frozen Stage 4A.2 campaign | 204 user-executed experiments, zero automated statistical failures; no universal stiffness, timestep, or N guarantee |
| GPU six-channel stress and streaming implementation | Implementation and bounded verification complete; scientific host campaign remains separate | Stage 4A.3A/B reports and frozen 4A.3C plan; no slip-spring interaction |
| GPU computational measurements | Validated only for recorded hosts/configurations | Stage 4A.3C benchmark and execution reports; overlapping timers are not additive |
| Timestep convergence, N=8 and N=32 | Provisional/unresolved | Stage 4A.4 reports and external N32 recovery receipts; missing diagnostics and exact-lag limitations remain |
| Hessian/local-mode timestep preselector | Heuristic tool, software-tested | Stage 4A.5 report; no stability or accuracy guarantee |
| Energy/distribution static diagnostics for Stage 4A.4 | Unresolved | Existing scalar outputs do not provide all required energy, angle, end-to-end, or full-contour distributions |
| Terminal nonlinear relaxation | Unresolved | T=20 timestep studies are short-time comparisons, not terminal campaigns |
| E1 canonical slip-spring equilibrium and fixed attachments | Design frozen; Stage A implemented and bounded checks passed | [EQUILIBRIUM_MODEL_E1.md](EQUILIBRIUM_MODEL_E1.md), [Stage A audit](E1_STAGE_A_AUDIT.md); no hopping, renewal, timestep acceptance or rheology validation |

The current numerical reference choices are `kBT=1`, `zeta=1`, `b0=1`, `kb=30`, double precision for scientific validation, and typically `seed=433201` for timestep studies. Interior `kappa` is nonnegative and endpoint entries are zero. The baseline timestep in Stage 4A.4 was `2.5e-5`; `5e-4` and `1e-3` were comparison candidates, not silently promoted production values.

The recorded CPU stress benchmark reached 1.938 million chain observations per second (946.2 complete frames/s) in its selected largest-bank median. A separate archived GPU measurement reported 1.943 ns/bead/step integration-only and 2.384 ns/bead/step overall for its tested N=8 configuration. These are measurements of named hosts and configurations, not portable performance guarantees; GPU stress, transfer, CPU-worker, output, and wall scopes overlap and must not be added.

The authoritative sources are the committed reports, source, tests, and frozen plans in `examples/slip-springs/`. Large GPU trajectories and some analysis receipts were generated on an external host and are not committed here; their paths, hashes, and limitations are stated in the corresponding reports. E1 fixes the canonical state space and proposed kinetics. Stage A covers only fixed attachments, annealed initialization and harmonic forces; later kinetic stages require separate authorization.
