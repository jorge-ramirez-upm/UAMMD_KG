# KG_Assoc scientific decisions

These decisions are frozen unless new evidence requires revisiting them.

- The physical reaction cutoff is `r_assoc=1.25`, shared by association
  creation and breaking.
- Temporary associating FENE is topology-driven, remains mechanically active
  to `R0=1.5`, and is independent of the WCA neighbor-list range.
- Canonical C1 chemistry uses `Nevery=100` and `nu0=20`.
- Rheology determines the required production duration. Other observables
  should be extracted from the same long trajectories.

`examples/KG/kg_uammd.cu` is the canonical implementation reference for stress
correlation and buffering. Production must sample stress every MD timestep,
use all six independent stress/deviatoric channels, and follow its
`Correlator6` pattern. The target modulus estimator is:

```text
G(t) = V/(5 kBT) [Cxy + Cxz + Cyz]
     + V/(30 kBT) [CNxy + CNxz + CNyz]
```

where `Nxy = sigma_xx - sigma_yy`, `Nxz = sigma_xx - sigma_zz`, and
`Nyz = sigma_yy - sigma_zz`.

- Sample star COM MSD every 100 MD steps.
- Write unwrapped, LAMMPS-style star-COM trajectories approximately every
  10,000 MD steps.
- Compute isotropic COM `S(q,t)` offline from those trajectories with the
  `correlator.h` tools; do not compute it during production.
- Write topology snapshots at the same cadence as COM coordinates, synchronized
  in one time-series file rather than one file per frame.
- Seeds 12001 and 12002 are independent E1/E2 replicas. Multiple bank states
  from one seed are well-separated states, not independent replicas.
- Build a clean, readable, optimized production executable. Keep
  validation-only/test instrumentation out of its hot path.

## Development workflow and code style

Code development for `examples/KG_Assoc/` uses Codex with the Ponytail skill.
Use Ponytail to remove unnecessary duplication and boilerplate, factor repeated
logic appropriately, simplify control flow, and keep implementations compact
and maintainable. Compactness must not reduce readability.

The desired balance is **Ponytail compactness + Google-style readability**.
Use the Google C++ Style Guide: descriptive names, explicit control flow, and
short focused functions. Avoid deep nesting, clever one-liners, compressed
expressions that are hard to audit, and code golf. Factor repetition when it
improves clarity; keep hot paths efficient without obscuring intent. Comments
should explain non-obvious scientific or algorithmic intent, not obvious code.

For CUDA/C++, separate host orchestration from kernels where practical; keep
kernels small and purpose-specific; prefer explicit data flow and no hidden
side effects; make synchronization obvious; and avoid unnecessary host-device
transfers. Preserve validated performance-sensitive batching and buffering.

Priority order: scientific correctness, reproducibility/auditability,
performance, readability/maintainability, then compactness. Compactness is
desirable only when it does not harm a higher-priority goal.
