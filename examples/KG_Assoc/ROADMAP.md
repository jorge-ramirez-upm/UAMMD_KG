# KG_Assoc roadmap

## P4 — production/rheology instrumentation

P4 implementation follows the development workflow and code style in
`SCIENTIFIC_DECISIONS.md`.

P4.0 (CLOSED):

- Inspect and port the `kg_uammd.cu` stress machinery.
- Add the associating-FENE virial/stress contribution.
- Validate the total stress tensor.

The active temporary FENE contribution now uses the same endpoint-doubled
cache and `+1/2` reducer convention as permanent FENE. It is independent of
the WCA list and remains active to `R0`; `Ee` does not enter its stress.

P4.1 (CLOSED):

- Create a clean production executable.
- Sample stress every step and COM every 100 steps.
- Write unwrapped COM trajectory and synchronized topology stream every
  10,000 steps.

Dedicated-host validation passed at `e843d6c60c38d5dd6c9aee74235de3fdc1bf79b3`.
Measured production overhead was approximately 61.3% wall time and 38.0%
throughput loss relative to the controlled baseline.

P4.2 (rheology pilot pending):

- The cache-reuse optimization passed dedicated-host validation and reduced
  controlled overhead to 28.7%; redundant interaction passes are removed.
- The bounded two-seed pilot has been run, but its first `G(0)`-scaled tail
  criterion was rejected as physically inappropriate for weak slow modes.
- Repair and inspect local-window tail classification before selecting a
  production duration; the current pilot is unresolved and needs longer
  support plus more independent replicas.

P4.3:

- Launch long multi-replica C1 production.

Later work: offline COM MSD, offline COM `S(q,t)`, bond dynamics,
topology/percolation, and C5/C6.

Do not start long production before P4.0/P4.1 validation.
