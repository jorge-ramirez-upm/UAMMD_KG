# Roadmap assessment after Stage 2B closure

16 October 2026. Assessment only: no next-stage implementation is authorized.

## What the repository actually plans

Reviewed the project README, AGENTS.md, Stage 0/1/2A/2B/2B.1 reports and the
scientific validation plans under this directory. No separate slip-spring model
design specification was found in the project documents. Historical reports
record stage gates at their original dates; current closure is in
[STAGE2B_N100_TERMINAL_RESULTS.md](STAGE2B_N100_TERMINAL_RESULTS.md).

AGENTS.md's actual sequence is Stage 3 **benchmarking and optimization**, followed
by Stage 4 **semiflexibility and slip-spring dynamics**. Stage 2B.1 supplied a
bounded CPU parallelization step within the authorized stress pipeline. That
does not silently renumber the roadmap or authorize the later physics stage.
Before coding, decide whether to retain Stage 3 as a separate host-performance
milestone, explicitly waive it, or formally revise the stage sequence. Further
optimization is not a prerequisite imposed by the completed Rouse validation.
Production-server benchmarking remains hardware-specific work.

The next planned *model* features are semiflexibility and slip-spring dynamics;
their mathematical definitions, ensemble and kinetic rules are not specified
by the existing roadmap. The items below are requirements to decide and validate,
not claims that a particular slip-spring formulation has been approved.

## Preserve the validated reference

Keep an independently runnable zero-new-interaction Rouse path: N springs/N+1
beads, free ends, Gaussian equilibrium initialization, unwrapped coordinates,
overdamped Euler–Maruyama update and its existing bead RNG/seed semantics.
New stochastic processes should have distinct RNG domains without changing the
reference draws. Preserve float/double builds, the fixed sampling cadence,
read-only KG Correlator6 calculations, bounded transfer buffers, deterministic
chain reduction, timing scopes and historical tests/tolerances.

Retain the raw six-channel stress convention and covariance-aware modulus
estimator for the reference. Any new interaction requires a derived additional
stress contribution and normalization; the old bond-only stress kernel can
remain the reference kernel. Gaussian initialization and independent-chain
uncertainty are justified for the present reference; they cannot automatically
be transferred to a model that changes equilibrium statistics or couples chains.

## Scientific decisions required before a model implementation

| Area | Parameters or rules that must be specified | Consistency/validation requirement |
| --- | --- | --- |
| Semiflexibility | Bending energy, stiffness or persistence-length parameter, angle convention, free-end treatment; whether introduced separately from slip-springs | Forces and stress must follow the selected energy; verify zero-stiffness recovery and an independent equilibrium reference for the chosen discrete chain |
| Slip-spring topology | Fixed external anchors, anchors moving with a medium, or bead-to-bead links; intra/interchain eligibility, multiplicity and crossing rules | Define the state space and whether chains remain independent; specify spatial boundary conditions and any volume/density |
| Connector elasticity | Spring energy, strength/length scale, any maximum extension or regularization | Derive forces and stress; use independent finite-difference force/energy checks and equilibrium connector statistics |
| Population/ensemble | Fixed number versus fluctuating number; target density/count or chemical potential/fugacity | Specify the joint bead/link equilibrium distribution and whether compensation is needed to preserve intended chain statistics |
| Attachment | Allowed attachment sites, anchor positions or partner selection, proposal probabilities and insertion rates | Include all proposal/selection factors in the chosen equilibrium-consistent rule; enumerate a tiny system as an independent check |
| Hopping | Which endpoint moves, adjacent-site moves or larger jumps, hop attempt rate/friction, rejection rules and time discretization | Derive transition rates or acceptance from the chosen stationary measure; test detailed balance if equilibrium reversible dynamics is intended |
| Renewal | End detachment versus bulk deletion, paired versus independent creation/deletion, anchor renewal distribution, lifetime parameters | Reverse processes and population factors must be consistent with the selected ensemble; verify stationary counts, endpoint distributions and kinetic limits |
| Time integration | Continuous-time events versus discrete attempts; bead/move splitting and relative update frequency | Control timestep and splitting bias; equilibrium correctness alone does not establish correct dynamics |
| Observables/uncertainty | Total stress, possible anchor/medium contributions, density normalization and independent replica definition | Derive stress for the selected model; if links couple chains, use independent replicas or justified clusters rather than independent-chain SE |

A choice is also needed on model targets: retain ideal Gaussian chain statistics
with a compensating interaction, or deliberately change equilibrium structure;
use equilibrium reversible slip-springs, or specify a driven/nonreversible model
and its target steady state. Neither choice follows from Stage 2B acceptance.
Do not assign default physical values or select a reference paper implicitly.

## Architecture and GPU implications

Keep the validated integrator and stress pipeline as the reference path. A future
link representation needs stable bead/link identities, bounded capacity and
explicit overflow handling, plus ownership rules for mutable topology. Define
who owns each endpoint and when topology updates become visible to force/stress
kernels. Concurrent hops, shared endpoints and creation/deletion need a specified
conflict-resolution algorithm; race freedom alone is not proof of an unbiased
transition process. Compare the selected parallel schedule with a serial oracle.

Interchain links would invalidate the present assumption that each chain's force
is independent. Plan force accumulation and synchronization explicitly, and
reconsider sample layout/statistical clusters if the observable becomes a total
coupled-system stress. Reuse the bounded CUDA event/host-buffer lifetime contract
where applicable. Extra kernels, memory and topology transfers must be measured
without changing stress sampling or presenting overlapping timers as sequential
costs. Bitwise reference recovery and scientifically justified comparisons for
new stochastic paths should be declared before implementation.

## Validation gates to agree before coding

1. Specify the Hamiltonian/state space and target equilibrium or steady-state
   distribution, then derive force, stress and each topology transition rule.
2. Build an independent small CPU oracle or exhaustive state enumeration for
   attachment/hopping/renewal, including boundaries and population changes.
3. Check equilibrium structure, connector distributions and population statistics
   against independent predictions for the chosen model; verify reversible
   transition fluxes where required and investigate timestep/splitting dependence.
4. Check hopping and renewal kinetics, waiting-time distributions and relevant
   dynamical limits independently. Require the zero-new-interaction Rouse
   dynamics, dimensions, diffusion and stress-relaxation regressions to recover
   their existing predictions and tolerances.
5. Establish relaxation/rheological predictions or a trusted independent numerical
   implementation for the selected slip-spring model. Rouse agreement alone
   cannot validate the new physics. Use uncertainties based on truly independent
   realizations and preserve channel covariance.
6. Agree GPU correctness, precision, memory-lifetime and host-performance gates
   after the scientific rules are fixed; only then authorize implementation.

Open discussion therefore concerns stage sequencing, the specific model and
reference, stiffness and connector energies, topology/ensemble, boundary and
density conventions, compensation, kinetic rates and renewal rules, update
scheduling, total stress and the independent statistical unit. No choices in
this list have been silently resolved, and Stage 3 has not begun.
