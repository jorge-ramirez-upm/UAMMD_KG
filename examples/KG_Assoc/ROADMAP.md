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
- Five genuinely independent 32M replicas (12001--12005) are now available.
  Replica-level 95% Student-t window CIs replace sign/agreement checks for
  detecting a mean compatible with zero: mixed signs near zero are expected.
  Thresholds 8--64 find sustained decay to the available noise floor; 128 is
  support-limited before it can form the required three-window confirmation.
  The late positive excursion is not replica-robust. P4.2 remains pending
  review before viscosity/production precision design; no new simulation is
  authorized.

P4.3 (limited C1 viscosity estimate complete):

- Five 32M C1 replicas establish terminal relaxation for C1 only. Trapezoidal
  integration on the actual multi-tau lag grid gives the deliberately
  approximate estimate `eta0 = 184.28 +/- 89.36` (95% replica CI) at
  `t_c=28835.84`, with cutoff sensitivity `16.32` over the terminal
  20k--50k target range. This is adequate for C1 comparison, not maximal
  viscosity precision.
- Another/slower system must independently establish terminal relaxation
  before reporting viscosity; 32M is not a universal duration.
- Priority now moves to diffusion, sticker lifetime distributions, and
  network/topology including hopping/walking mechanisms. Do not launch a new
  viscosity simulation automatically.

P4.4 (C1 star-COM diffusion analysis pending):

- `analysis/analyze_p44_com_diffusion.py` reads each self-contained unwrapped
  COM segment and uses the installed `correlator.DiffusionCorrelator` at its
  selected multi-tau lags, averaging the per-star MSDs. The five 32M C1
  segments have 3,200 frames of 1,000 ordered star IDs at 100 time-unit
  spacing; segments are never stitched across restart boundaries.
- The multi-tau estimator passes deterministic ballistic and constant tests,
  fine-lag brute-force all-origin checks, and a C1 short-slice check. Its raw
  origin count is reported only as support, never as the replica uncertainty.
- The five-replica mean remains subdiffusive over the sampled range: the
  five-point local logarithmic slope is about 0.63--0.86 and never supplies
  five adjacent points within 0.1 of one. Thus the diagnostic linear-fit
  values around `2.6e-4--2.8e-4` are not yet a defensible terminal `D`; more
  long-time support is needed before reporting C1 diffusion. The 100-time-unit
  COM spacing is adequate for that long-time diagnosis; denser old data would
  instead help short/intermediate-time physics.
- For later self-`S(q,t)`, the same package offers
  `SqtCorrelatorIsotropic` and `SqtCorrelatorIsotropicManyQ`, which evaluate
  isotropic `sinc(q|Delta R|)` at selected multi-tau lags. Candidate COM
  wave numbers are `2pi/L=0.1691`, `1/Rg=0.3776`, and their low multiples;
  this reconnaissance does not launch a q-grid analysis.

Later work: offline COM MSD, offline COM `S(q,t)`, bond dynamics,
topology/percolation, and C5/C6.

Do not start long production before P4.0/P4.1 validation.
