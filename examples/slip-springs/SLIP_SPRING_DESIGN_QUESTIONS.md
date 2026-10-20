# Slip-spring design questions

This agenda deliberately records decisions still needed before implementation. The repository contains no approved slip-spring Hamiltonian or kinetic specification, and its existing notes do not settle the questions below. The cited Wang et al. (2015), Likhtman (2005), and Tejedor et al. (2022) connections should be checked against the exact papers and chosen model before being used as requirements; no paper-specific conclusion is adopted here.

## State and energy

- What is a slip-spring: a bead-to-bead connector, a bead-to-fixed/host anchor, or an auxiliary link to a second chain? What is its reference length, spring potential, strength, and treatment at zero separation?
- Does it couple to the nonlinear semiflexible backbone through the same Cartesian coordinates and stress virial? Are bending and connector energies additive, and which terms contribute to reported H?
- Is the host flexible, imposed, or dynamically controlled? What sets the confinement scale or effective reference volume? If the host is controlled by the chain statistics, how is that control represented without changing the target ensemble?
- Are link counts fixed, chemically fluctuating, or driven? What equilibrium distribution, fugacity, or chemical potential defines the population?

## Topology and kinetics

- Which contour sites may attach, and may multiple links occupy one bead? Are intra-chain and inter-chain links both allowed? What happens at chain ends and crossings?
- How does a slip-link hop along the contour? What attempt frequency, friction, neighborhood, and rejection rule apply? Does the hopping rate depend on local stiffness, bond lengths, angle, connector extension, or available sites?
- How are links created, renewed, escaped, and deleted? What are end-renewal distributions, lifetimes, reverse moves, and population factors?
- Is the process equilibrium reversible with detailed balance, or is it a driven steady-state model? If equilibrium is intended, every attachment, hop, renewal, and deletion rate must include the correct proposal and state-weight ratios.

## Numerical and statistical consequences

- Do link forces introduce a shorter local timescale than the backbone Hessian? The existing `tau_min` and Q99 preselector must then be extended to the combined Hessian; neither current estimate includes slip-spring forces.
- Are topology events continuous-time, discrete attempts, or split from Euler–Maruyama? What splitting error and event/timestep coupling are acceptable?
- What is the independent statistical unit once chains are coupled by links: chain, replica, connected component, or full system? The current independent-chain stress SE cannot be transferred automatically.
- Which stress includes connector and host contributions, and what density normalization is intended? Preserve the raw six-channel convention only after deriving the new total virial.

## Baseline gates before production

1. Write the Hamiltonian/state space and target equilibrium or driven measure, including boundaries, multiplicity, density, and end rules.
2. Build a tiny CPU oracle or exhaustive enumeration for attachment, hopping, renewal, and population transitions. Check forces and stress by finite differences.
3. Verify equilibrium connector lengths, contour-site occupancy, link counts, end distributions, and zero-link recovery against independent predictions.
4. Test detailed balance or stationary fluxes, hopping waiting times, renewal/escape limits, and timestep/splitting dependence.
5. Recover the validated zero-new-interaction backbone, its dimensions, diffusion, stress conventions, and precision behavior when links are disabled.
6. Establish bounded GPU ownership, link capacity/overflow, identity, conflict resolution, and memory-lifetime tests before any large run.

Wang et al. (2015), Likhtman (2005), and Tejedor et al. (2022) are useful candidate literature anchors for different aspects of slip-spring or polymer constraint modeling, but this repository currently carries no bibliographic extracts or approved mapping from those papers to a model. The next conversation should pin exact citations and decide which observables and state variables are being adopted before code is written.
