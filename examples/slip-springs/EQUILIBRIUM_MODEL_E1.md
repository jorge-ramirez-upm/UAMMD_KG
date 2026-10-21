# Equilibrium Model E1 — canonical anchored slip-springs
Status: **scientific design frozen (2026-10-20); Stage A fixed attachments implemented and audited (2026-10-21)**.
See [the Stage A audit](E1_STAGE_A_AUDIT.md); hopping and renewal remain unimplemented.
Scope: `examples/slip-springs/` only. This document specifies the equilibrium measure and ideal continuous-time transition kernels. It does **not** authorize production simulation, timestep acceptance, or a rheological estimator.

## 1. Scientific objective and boundary

Model dilute, identical semiflexible *probe* chains embedded in an implicit flexible entangled host. Entanglements are harmonic springs to spatial anchors; the host determines provisional slip-spring parameters. Varying probe stiffness must not artificially change the **bare equilibrium conformational distribution**. This is a dynamical model of entanglement constraints, not an explicit melt.

The already validated nonlinear backbone remains the reference: `N` bonds, `N+1` beads, free ends, finite-rest-length harmonic stretching, discrete Kratky–Porod bending, overdamped Langevin dynamics, no excluded volume or hydrodynamic interactions. The existing exact backbone equilibrium initializer remains authoritative. The provisional BD timestep `5e-4` is not finally accepted for all conditions and has not been tested with slip-spring forces.

We first model `M` identical chains (same `N` and homogeneous `kappa`) and a globally fixed total number `Z` of slip-springs. Inhomogeneous contour stiffness is deferred.

## 2. State space and harmonic Hamiltonian

Chain `c=1,...,M` has bead positions `r[c,i]`, `i=0,...,N`, with bond vectors `q[c,i]=r[c,i+1]-r[c,i]` and unit tangents `u[c,i]=q[c,i]/|q[c,i]|`.

The backbone energy of a chain is
```text
U_bb(R_c) = sum_{i=0}^{N-1} (k_b/2)(|q[c,i]|-b_0)^2
          + sum_{i=1}^{N-1} kappa (1-u[c,i-1]·u[c,i]).
```
The production code's documented coefficient conventions prevail.

A live slip-spring has a host chain `c_j`, occupied bead `s_j`, and an anchor vector `a_j` fixed in laboratory coordinates for that spring's lifetime. Its energy is
```text
E_j = (k_ss/2) |r[c_j,s_j]-a_j|^2,
k_ss = 3 k_B T / a_ss^2,   a_ss^2 := N_s b_h^2.
U = sum_c U_bb(R_c) + sum_j E_j.
```
This is a *zero-rest-length* Hookean connector, unlike the backbone bonds. `a_ss^2` is the equilibrium **mean-square connector extension**, not automatically the tube diameter or the spatial distance between neighboring constraints. `b_h` describes the flexible host. Initially take `N_e=N_e^(h)` from the flexible-host reference, independent of probe stiffness; `a_ss` is likewise held fixed provisionally. Both may be revisited in later scientific work.

Let `L=M(N+1)` be the total number of bead sites, with `0<=Z<=L`. Single occupancy is mandatory: each bead site carries at most one spring. Springs on one chain cannot overtake each other during interior hopping; a spring escaping and renewing at an end acquires a new contour placement/identity for ordering purposes. No permanent label-order restriction is imposed across successive lifetimes. This preserves the uniform target over occupied-site sets.

## 3. Joint canonical *annealed* equilibrium ensemble

Use `S`, an **unordered** set of `Z` distinct chain–bead sites; one anchor coordinate is associated to each occupied site. Equivalently one can use spring identities with a consistent constant combinatorial factor, not an extra position-dependent weight. Define the normalized conditional Gaussian
```text
g(a|r) = (beta*k_ss/(2*pi))^(3/2) exp[-beta*k_ss*|a-r|^2/2],
beta = 1/(k_B T).
```
Then the normalized equilibrium density (modulo the usual translational zero-mode treatment of unconfined chains) is
```text
pi(R,S,A) = pi_bb(R) / choose(L,Z) * product_{x in S} g(a_x | r_x),
pi_bb(R) ∝ exp[-beta sum_c U_bb(R_c)].
```
This is the Boltzmann distribution for the additive Hamiltonian under the corresponding flat site and anchor measures. **Annealed** means anchors are integrated over in the ensemble, not that an anchor diffuses during a lifetime.

Consequences, exact for the specified ensemble:
- Integrating all anchors and summing over sites yields `pi(R)=pi_bb(R)`. This holds for the nonlinear semiflexible backbone, even at heterogeneous stiffness, because each Gaussian anchor integral is independent of its bead position.
- Each site has occupancy probability `Z/L`, including ends. Uniform marginal occupancy **does not** imply uniformly likely attachment sites conditional on a fixed configuration `R,A`.
- The occupancy count `Z_c` on one chain is hypergeometric:
  `Pr(Z_c=z) = choose(N+1,z)*choose((M-1)*(N+1),Z-z)/choose(L,Z)`;
  `E[Z_c]=Z/M`. For many chains and dilute sites, a binomial, possibly approximately Poisson, marginal arises.
- Conditional anchor displacement components are independent zero-mean Gaussians of variance `a_ss^2/3`, giving `E|a-r|^2=a_ss^2`.
- Choose the nearest admissible integer total `Z ~ M*N/N_e^(h)`; record the rounding convention and actual density. A choice exceeding `L` is invalid.

Correct exact annealed initialization: generate independent bare equilibrium probe conformations using the existing initializer; choose `Z` distinct sites uniformly from the `L` sites; draw each anchor independently from `g(a|r_site)`. Preserve anchors and attachments afterward until hopping/renewal changes them. Fixed-attachment/no-hopping dynamics is a **development-only** conditional-equilibrium test, not intended entangled terminal dynamics.

## 4. Ideal hopping kernel (scientific target)

Interior hopping uses discrete attachments as in Wang et al. (2015), rather than the continuous contour Langevin coordinate used by Likhtman (2005).

Each live spring has a Poisson **attempt** clock of rate `nu_hop`, and proposes left/right with probability 1/2. For a permitted adjacent site `x'` on the same chain, leaving the anchor unchanged,
```text
w(X→X') = (nu_hop/2) min[1,exp(-beta*(E_new-E_old))].
```
Reject occupied targets and any move violating noncrossing. For any allowed move its reverse exists with the same unweighted proposal frequency, and
```text
w(X→X')/w(X'→X) = exp[-beta*(E_new-E_old)] = pi(X')/pi(X).
```
Thus this jump kernel satisfies detailed balance at fixed bead positions and other spring variables.

**Attempt ordering:** independent rate-`nu_hop` Poisson clocks correspond to random sequential spring selection *with replacement*. For the conserved total `Z`, in a frozen-coordinate interval `dt_h`, draw `K ~ Poisson(Z*nu_hop*dt_h)` and perform `K` sequential, uniformly selected spring attempts, updating the state after each event. When the batch follows `m` BD steps, `dt_h=m*dt_BD`; freeze `m=1` initially. Hopping event statistics are exact for *fixed* coordinates in a batch, but operator splitting with moving beads has time-discretization error. No numeric value of `nu_hop` is frozen. Wang's neighboring-monomer trial interval `0.002 tau` (where `tau=zeta*b^2/(kBT)`) is a literature reference scale, not a calibrated value for our backbone.

`nu_hop` is intended as an artificial fast variable; independence of slow observables at sufficiently high rate is an **unproven hypothesis**, especially because end escape uses the same rate. Do not assert that the limit `nu_hop→infinity` yields finite, rate-independent terminal behavior.

## 5. End escape and canonical renewal kernel

At either occupied terminal bead, an *outward* attempt is made at rate `nu_hop/2`. Propose a destination chain uniformly among all `M` chains, including the source, and select its left/right end equally. If the chosen destination end **was occupied in the pre-event state** (including the source bead), reject the entire move. Otherwise:
1. Remove the source spring/old anchor.
2. Create the new spring at the proposed vacant destination end.
3. Independently sample its new anchor from `g(a_new|r_dest)`.
4. Accept the permitted transfer with probability one. The total `Z` is conserved.

For distinct ends `x` (source) and `y` (destination), the forward transition-rate density is
```text
w(X→Y) = [nu_hop/(4M)] g(a_new|r_y),
w(Y→X) = [nu_hop/(4M)] g(a_old|r_x).
```
Because `pi(Y)/pi(X)=g(a_new|r_y)/g(a_old|r_x)` for the fixed bead geometry and other springs, we have
```text
pi(X)w(X→Y) = pi(Y)w(Y→X).
```
This is detailed balance of the **complete** renewal event, including the new anchor proposal density. No extra exp(-beta*(E_new-E_old)) acceptance factor is needed; adding one would in general *break* the target equilibrium. Occupied-end rejections are null events and preserve stationarity. Transfer to the *same chain at the other vacant end* is allowed; transfer to the same occupied source end is rejected. Renewal is only by end escape; there is **no internal host constraint release**.

A highly stretched connector does not automatically have a higher outward-escape acceptance: connector energies affect its preceding contour hopping probabilities; allowed outward transfer is accepted once a free destination is selected. This is a chosen kinetic model, not a universal microscopic escape law.

## 6. Stationarity, dynamical limits and unresolved physics

With the anchors and site indices held fixed, overdamped bead dynamics with total force `-grad_R U` preserves the conditional Boltzmann measure in continuous time. The hopping and renewal jump kernels separately satisfy detailed balance for the **same** joint measure. Thus their combined *ideal continuous-time process* preserves `pi`. This establishes stationarity, not a general ergodicity theorem. Euler–Maruyama plus batched hopping introduces finite-`dt` splitting and integration errors; E1 does not claim numerical exact equilibrium at finite `dt`.

The equilibrated attachment distribution at fixed polymer/anchor configuration is **not** a simple independent per-spring Boltzmann distribution when exclusion and ordering are imposed. Furthermore, finite-time kinetic accessibility differs from conditional equilibrium probability: intervening high-energy sites and moving neighboring slip-springs can make otherwise favorable positions extremely difficult to reach. We retain explicit hopping. Any adiabatic/finite-time force averaging is deferred.

Deferred scientific questions:
- How effective `N_e` depends on probe stiffness in a flexible host; it is known that holding it fixed is not generally physically appropriate for widely differing stiffness.
- Whether stiffness changes effective spring-extension statistics or other confinement parameters; holding `a_ss^2` fixed is provisional.
- Whether realistic terminal observables become weakly dependent on `nu_hop`; shared hopping/escape rate may make them dependent.
- Quantitative relation between connector extension, contour spacing, spatial entanglement scale, and tube diameter.
- Finite-time coarse-graining/unobserved escape events, and any future host constraint release.

## 7. Stress and mechanics boundary

Do **not** assume that the autocorrelation of total (backbone plus virtual-spring) stress is the physical relaxation modulus. The intended later study of the probe's partial stress relaxation involves the backbone autocorrelation and a backbone–virtual-spring cross-correlation; see Ramirez, Sukumaran and Likhtman (2007), DOI: 10.1063/1.2746867. The precise partial-response observable for this nonlinear semiflexible implementation needs a dedicated derivation later. Deformation/anchor transformation is **not in scope** now. At the first development stage the slip-spring **force** is sufficient:
```text
F_ss(on attached bead) = -k_ss*(r_site-a).
```
Do not modify the existing six-channel stress estimator or claim a final rheology formula in E1.

## 8. Narrow implementation sequence (only Stage A implemented)

1. Development-only, no-hopping, fixed-attachment harmonic connectors: exact annealed initialization and basic force checks. Disabled connectors must recover the validated backbone. Keep all changes in `examples/slip-springs/`.
2. Explicit adjacent-bead stochastic Metropolis hopping with Poisson batches at `m=1`, respecting exclusion/order.
3. End transfer/reanchoring with the kernel above; check stationary occupancy, anchor extension, population fluctuations and elementary detailed balance.
4. Only then investigate scientifically justified hopping-rate and timestep/splitting sensitivity. Do not reopen broad backbone validation without a specific requirement.

## 9. Literature and provenance

- A. E. Likhtman, *Single-Chain Slip-Link Model of Entangled Polymers*, Macromolecules **38**, 6128–6139 (2005), DOI: 10.1021/ma050399h. Continuous contour Langevin attachments, harmonic fixed anchors, and the annealed-chain-statistics argument.
- M. Wang, A. E. Likhtman and B. D. Olsen, *Tube Curvature Slows the Motion of Rod–Coil Block Copolymers through Activated Reptation*, ACS Macro Lett. **4**, 242–246 (2015), DOI: 10.1021/mz5007377. Discrete adjacent-monomer Metropolis attempts, fixed anchors, end renewal; parameters calibrated in that model.
- M. Wang, A. E. Likhtman and B. D. Olsen, *Crossover between Activated Reptation and Arm Retraction Mechanisms in Entangled Rod-Coil Block Copolymers*, J. Chem. Phys. **143**, 184904 (2015), DOI: 10.1063/1.4933427. Discrete slip-spring motion, noncrossing and renewal of a conserved multi-chain population.
- A. R. Tejedor, J. R. Tejedor and J. Ramírez, *Detailed dynamics of discrete Gaussian semiflexible chains with arbitrary stiffness along the contour*, J. Chem. Phys. **157**, 164904 (2022), DOI: 10.1063/5.0112951. Background on Gaussian semiflexible chains, **not** the current finite-rest-length nonlinear backbone or the E1 kinetics.
- J. Ramírez, S. K. Sukumaran and A. E. Likhtman (2007), J. Chem. Phys., DOI: 10.1063/1.2746867. Stress cross-correlation motivation; stress work deferred.

Authoritative repository context: `PROJECT_STATUS.md`, `BACKBONE_MODEL_AND_VALIDATION.md`, `TIMESTEP_SELECTION.md`, `DEVELOPMENT_HISTORY.md`, and `SLIP_SPRING_DESIGN_QUESTIONS.md` in this directory. E1 supersedes the *unresolved design questions* only for decisions explicitly fixed above; it does not supersede backbone acceptance limits.
