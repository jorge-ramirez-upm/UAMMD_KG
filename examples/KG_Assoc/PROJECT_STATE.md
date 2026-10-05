# KG_Assoc project state

Current validated branch/HEAD: `KremerGrest` at
`e843d6c60c38d5dd6c9aee74235de3fdc1bf79b3`.
P4.1 is closed there; the preceding `c93ed2d...` and `e843d6c...` commits
contain the fail-closed host-validation repairs. The earlier
`ff5cd97a8ac7e80328a046e9796a7209c8ad0841` remains the last P3 scientific
validation commit.

Development workflow: Codex + Ponytail; Google-style readable C++/CUDA.

Completed milestones:

- P2 / E1 validation
- P3.0 associating-cutoff audit
- P3.1 C1 E2 chemical/topological equilibration
- P3.2 chemically valid restart support
- P3.3 C1 chemically valid restart bank
- P4.0 associating-FENE stress tensor validation
- P4.1 production instrumentation and validation

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
- rigorous PBC wrapping/percolation;
- C5/C6 E2.
