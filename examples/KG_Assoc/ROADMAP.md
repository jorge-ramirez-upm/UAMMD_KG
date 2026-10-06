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
- `Correlator6` now exports per-lag raw contribution support (`n_pairs`) with
  the stress correlator output. This is not an effective independent-sample
  count, but it replaces the arbitrary 25%-tail exclusion for new-format
  files. Existing eight-column pilot files remain explicitly legacy and
  provisional.
- Rerun the bounded two-seed pilot and inspect count-aware local-window tail
  classification before selecting a production duration or launching a longer
  trajectory.
- The planned overnight extension is 32,000,000 steps per seed for the same
  two independent C1 states (`s12001` and `s12002`), `dt=0.01`, or 320,000
  time units per seed. The runner will set `P42_PILOT_COM_EVERY=10000` for
  I/O control only; stress remains sampled every MD step and frame/topology
  cadence remains 10,000 steps. This is an extended P4.2 pilot, not final
  production, and is intended to improve long-lag support before adding more
  replicas.

- The completed 32M x 2 extension took 11,512.3 s and 11,253.8 s for seeds
  12001 and 12002. It exposed the length-dependent 320-count eligibility
  threshold as overly restrictive for late bins with roughly 50 contributions.
  The analyzer now sweeps `8,16,32,64,128`; it finds a resolved weak positive
  window near `t=39,321.6--57,671.68`, but all tested thresholds remain
  unresolved at their terminal eligible windows. The overall result is still
  analysis-pending and no further simulation is authorized before review.
- The next design is four genuinely independent 32M replicas: retain 12001
  and 12002, prepare E1/E2 restart-bank seeds 12003 and 12004 through the
  same validated P2.2/P3.3 path, validate each restart pair, then run all four
  at `P42_PILOT_COM_EVERY=10000`. Different restart times within one seed are
  not independent replicas. The expected one-GPU serial wall time is 12.65 h
  from the measured mean 32M runtime; do not start this run before reviewing
  the new-seed E1 diagnostics and restart-bank validation.

P4.3:

- Launch long multi-replica C1 production.

Later work: offline COM MSD, offline COM `S(q,t)`, bond dynamics,
topology/percolation, and C5/C6.

Do not start long production before P4.0/P4.1 validation.
