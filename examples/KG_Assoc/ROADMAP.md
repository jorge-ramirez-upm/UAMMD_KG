# KG_Assoc roadmap

## P4 — production/rheology instrumentation

P4 implementation follows the development workflow and code style in
`SCIENTIFIC_DECISIONS.md`.

P4.0:

- Inspect and port the `kg_uammd.cu` stress machinery.
- Add the associating-FENE virial/stress contribution.
- Validate the total stress tensor.

P4.1:

- Create a clean production executable.
- Sample stress every step and COM every 100 steps.
- Write unwrapped COM trajectory and synchronized topology stream every
  10,000 steps.

P4.2:

- Benchmark overhead and I/O.
- Run a short rheology pilot.
- Estimate the required production duration.

P4.3:

- Launch long multi-replica C1 production.

Later work: offline COM MSD, offline COM `S(q,t)`, bond dynamics,
topology/percolation, and C5/C6.

Do not start long production before P4.0/P4.1 validation.
