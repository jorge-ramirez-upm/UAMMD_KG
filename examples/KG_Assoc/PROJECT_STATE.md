# KG_Assoc project state

The P4.8b automated-driver lineage includes
`11e830cd79dae54f33228ea77ad385ea792afc57`. P4.1 remains closed at
`e843d6c60c38d5dd6c9aee74235de3fdc1bf79b3`; the preceding `c93ed2d...` and
`e843d6c...` commits contain the fail-closed host-validation repairs. The
earlier `ff5cd97a8ac7e80328a046e9796a7209c8ad0841` remains the last P3
scientific validation commit.

Development workflow: Codex + Ponytail; Google-style readable C++/CUDA.

Completed milestones:

- P2 / E1 validation
- P3.0 associating-cutoff audit
- P3.1 C1 E2 chemical/topological equilibration
- P3.2 chemically valid restart support
- P3.3 C1 chemically valid restart bank
- P4.0 associating-FENE stress tensor validation
- P4.1 production instrumentation and validation
- P4.8a C1 periodic-wrapping validation

P4.1 is CLOSED at validated HEAD
`e843d6c60c38d5dd6c9aee74235de3fdc1bf79b3`. Dedicated TITAN Xp validation and
the controlled baseline-vs-production benchmark both passed. No long
production campaign was started.

Validated C1 E2 duration: 6,000,000 MD steps at `dt=0.01`.

The validated C1 restart bank contains six chemically valid states at
`examples/KG_Assoc/systems/restart_bank/C1/`: seeds 12001 and 12002, each at
`t=40000`, `t=50000`, and `t=60000`.

Remaining major gaps:

- P4.2 profiling and overhead decomposition;
- rheology production;
- COM MSD;
- COM `S(q,t)` postprocessing;
- synchronized topology trajectory;
- finite-box P4.8b Ee crossover / `Ee_50` search (PAUSED, not complete);
- C5/C6 E2.

P4.8b status: the validated infrastructure has completed an Ee=7.5 C1
two-chain scout, which remains fully wrapping (replica mean wrapping fraction
0.99609375), and an incomplete Ee=7.0 chain-1 equilibration. Ee=7.0 exhausted
its 1M-step gate with all windows wrapping but failed the `intra_bonds`
stationarity tolerance; it is not an equilibrium scout plateau. No finite-box
`Ee_50` or thermodynamic critical point is claimed. Retain all artifacts and
the resumable state at `percolation_search/C1/automated_staircase_from_7p5.json`.
P4.8b is formally PAUSED and does not block main cross-condition production.

Production policy: after adequate equilibration, each selected scientific
condition has a common maximum production budget of 100,000,000 MD steps.
This is not a universal convergence claim. Analyze validated topology, bond/
network dynamics, walking/hopping where applicable, rheology, star-COM MSD,
self `F_s(q,t)`, and other available observables. Report terminal viscosity or
diffusion only when its predefined criteria are met; no terminal diffusion by
1e8 steps is acceptable and does not automatically extend a run. Percolation
search/equilibration runs are instead only as long as scientifically needed.

Immediate priority: design and generate the systematic cross-condition
associating-star dataset for comparative network topology, bond/network
dynamics, rheology, and translational dynamics. The parameter-space design is
not yet frozen.
