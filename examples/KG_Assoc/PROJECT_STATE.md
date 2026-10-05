# KG_Assoc project state

Current validated branch/HEAD: `KremerGrest` at `ff5cd97a8ac7e80328a046e9796a7209c8ad0841`.

Completed milestones:

- P2 / E1 validation
- P3.0 associating-cutoff audit
- P3.1 C1 E2 chemical/topological equilibration
- P3.2 chemically valid restart support
- P3.3 C1 chemically valid restart bank

Validated C1 E2 duration: 6,000,000 MD steps at `dt=0.01`.

The validated C1 restart bank contains six chemically valid states at
`examples/KG_Assoc/systems/restart_bank/C1/`: seeds 12001 and 12002, each at
`t=40000`, `t=50000`, and `t=60000`.

Remaining major gaps:

- production instrumentation;
- associating-bond stress-contribution audit;
- rheology production;
- COM MSD;
- COM `S(q,t)` postprocessing;
- synchronized topology trajectory;
- rigorous PBC wrapping/percolation;
- C5/C6 E2.
