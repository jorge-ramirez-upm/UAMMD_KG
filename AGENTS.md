# Local Codex instructions

## Repository boundaries

- `examples/KG/` is the validated non-associating Kremer-Grest baseline.
- Do not modify `examples/KG/*` unless explicitly requested.
- Do not modify `src/*` unless an API limitation makes it unavoidable and this has been discussed first.
- New associating-KG work belongs under `examples/KG_Assoc/`.

## Scientific source of truth

For associating-polymer physics and kinetics, use the current LAMMPS reference implementation:

- repository: `jorge-ramirez-upm/lammps`
- branch: `feature/associating-stickers`
- `src/ASSOCIATING/fix_associating_kinetics.*`
- `src/ASSOCIATING/pair_associating.*`

When reproducing K1 validation, also inspect:

- `bench/associating/dimer_kinetics/`

Do not replace implemented semantics with generic assumptions.

## Development workflow

### User-run long computations — mandatory

- Do not launch long simulations or other computations from the assistant session.
- The assistant may run short tests only, with a maximum runtime of 10 minutes per job.
- Use a timeout of at most 600 seconds when a short test's runtime is uncertain.
- For any simulation or job expected to exceed 10 minutes, prepare and test the workflow,
  then give the user the exact commands to run it themselves on their Linux host.
- Requests to prepare or run substantial trajectories mean prepare a user-run handoff;
  they do not authorize the assistant to launch long jobs here.
- Do not evade this limit using background processes, detached sessions, schedulers,
  polling loops, or many short segments of a long simulation.
- Make handoff commands handle existing output directories and interruptions safely:
  preserve earlier evidence, skip completed validated histories, and automatically
  allocate fresh attempts when a partially executed history must restart.
- Never promise bitwise continuation when the executable has no suitable checkpoint.
- Only a later explicit user instruction overriding this policy permits an exception.

- Inspect existing code before implementing.
- Prefer reusing validated helpers over duplication.
- Make small, scientifically testable changes.
- Run focused tests before larger simulations.
- Never fabricate GPU or scientific results when hardware is unavailable.
- For stochastic validation, distinguish deterministic regression tests from statistical convergence tests.
- Preserve provenance: git SHA, parameters, seed, executable, and relevant build information.

## UAMMD build rule

UAMMD is header-based. If any included `.cu` or `.cuh` file changes, rebuild the affected executable.

Do not assume `git pull` is sufficient.

## Code style

Use readable C++/CUDA style broadly consistent with Google C++ Style.

- One statement per line.
- Do not compress several declarations or operations onto one line.
- Use braces for control flow.
- Prefer descriptive names over very short names, except conventional loop indices.
- Break long function calls across lines.
- Keep lines roughly <= 100 characters where practical.
- Separate logical stages with blank lines.
- Prefer small helpers when they improve clarity.
- Avoid code-golf style.
- Compactness should come from reuse and abstraction, not from minimizing lines.

Do not reformat untouched validated files solely for style.

## Scientific coding principles

- Preserve stable particle IDs; do not assume ParticleData storage order is permanent.
- Valence-one partner state must remain reciprocal.
- `r_assoc` is the kinetic candidate cutoff.
- Active associating bonds remain mechanically active up to `R0`.
- Current LAMMPS semantics gate both creation and breaking by `r_assoc`.
- Transient association adds shifted FENE only; do not duplicate WCA.
- Use the exact finite-step probability:
  `q = -expm1(-nu0 * exp(-Ea/T) * Nevery * dt)`.
- `Ee` affects equilibrium energetics; `Ea` controls the kinetic attempt scale.
- Do not silently clamp or ignore invalid FENE states.

## Validation hierarchy

Prefer validating in this order:

1. analytic/self-tests;
2. static fixed-distance dimer kinetics;
3. dynamic dimer;
4. K1 many-sticker validation against LAMMPS;
5. full associating-star production system.

Do not advance to a more complex stage when a simpler validation stage is unresolved.
Before proposing or implementing a more complex validation, verify that the immediately simpler validation level has actually been executed and its results inspected.

## Reporting

At the end of a task report:

- starting SHA;
- final SHA;
- files changed;
- tests run and results;
- scientific checks performed;
- any unresolved discrepancy;
- confirmation that protected directories were not modified.

