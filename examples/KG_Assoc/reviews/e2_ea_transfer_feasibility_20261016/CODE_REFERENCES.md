# Exact code references

UAMMD references are pinned to starting commit `bd77a09daa28791972810fc81ffc82b8a9024460`;
local file SHA256 bindings and inspected evidence are in SOURCE_SHA256.json.

| Source and line | Role |
|---|---|
| [examples/KG_Assoc/kg_assoc_kinetics.cuh:16](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_kinetics.cuh#L16) | FENE, r*, energy shift, q, Metropolis |
| [examples/KG_Assoc/kg_assoc_kinetics.cuh:43](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_kinetics.cuh#L43) | Hash ordering, eligibility re-read, sequential acceptance |
| [examples/KG_Assoc/kg_assoc_star_runtime.cuh:234](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_star_runtime.cuh#L234) | Geometry-only periodic candidate enumeration and strict cutoff |
| [examples/KG_Assoc/kg_assoc_interactors.cuh:22](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_interactors.cuh#L22) | Energy shift and force implementation |
| [examples/KG_Assoc/kg_assoc_ea_switch.cuh:10](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_ea_switch.cuh#L10) | Explicit Ea-change guards |
| [examples/KG_Assoc/kg_assoc_stars.cu:634](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_stars.cu#L634) | Parent seed immutability |
| [examples/KG_Assoc/kg_assoc_stars.cu:637](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_stars.cu#L637) | Restart Ea switch, metadata and absolute step |
| [examples/KG_Assoc/kg_assoc_stars.cu:723](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_stars.cu#L723) | Exact partner restoration |
| [examples/KG_Assoc/kg_assoc_stars.cu:743](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_stars.cu#L743) | GJ initVelocities=false, fresh effective MD seed, local step reset |
| [examples/KG_Assoc/kg_assoc_stars.cu:775](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_stars.cu#L775) | Inherited counters, initial samples and reaction cadence |
| [examples/KG/kg_runtime.cuh:55](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG/kg_runtime.cuh#L55) | Single-precision positions/PBC folding and loaded velocities |
| [examples/KG_Assoc/campaign/kg_assoc_e2.py:287](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/campaign/kg_assoc_e2.py#L287) | Ea4 ordinary preparation gate and C1-smoke restriction |
| [examples/KG_Assoc/campaign/kg_assoc_e2.py:207](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/campaign/kg_assoc_e2.py#L207) | Frozen system/parent/seed/Ea transition checks |
| [examples/KG_Assoc/campaign/kg_assoc_e2_validate.py:49](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/campaign/kg_assoc_e2_validate.py#L49) | Strict parent seed, physics, state and counter checks |
| [examples/KG_Assoc/campaign/kg_assoc_campaign.py:106](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/campaign/kg_assoc_campaign.py#L106) | Shared-Ea bank identity omits Ea |
| [examples/KG_Assoc/campaign/kg_assoc_e2_registry.py:13](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/campaign/kg_assoc_e2_registry.py#L13) | Acceptance use and exact system restrictions |
| [examples/KG_Assoc/campaign/kg_assoc_e2_registry.py:69](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/campaign/kg_assoc_e2_registry.py#L69) | Immutable acceptance payload authentication |
| [examples/KG_Assoc/campaign/kg_assoc_e2.py:267](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/campaign/kg_assoc_e2.py#L267) | Requested/effective MD seed allocation |
| [examples/KG_Assoc/kg_assoc_dimer.cu:258](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/kg_assoc_dimer.cu#L258) | Existing fixed-geometry/cutoff regression |
| [examples/KG_Assoc/VALIDATION.md:742](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/bd77a09daa28791972810fc81ffc82b8a9024460/examples/KG_Assoc/VALIDATION.md#L742) | Executed validation and Gate C limits |

LAMMPS local branch `feature/associating-stickers`, commit
`1c6faf70e94aef2389c208e8c80c60c084a96907`. No external repository files changed.

| Source and line | Role |
|---|---|
| [src/ASSOCIATING/fix_associating_kinetics.cpp:101](https://github.com/jorge-ramirez-upm/lammps/blob/1c6faf70e94aef2389c208e8c80c60c084a96907/src/ASSOCIATING/fix_associating_kinetics.cpp#L101) | Exact finite-step factor and Metropolis |
| [src/ASSOCIATING/fix_associating_kinetics.cpp:106](https://github.com/jorge-ramirez-upm/lammps/blob/1c6faf70e94aef2389c208e8c80c60c084a96907/src/ASSOCIATING/fix_associating_kinetics.cpp#L106) | Ordering and sequential chemical updates |
| [src/ASSOCIATING/fix_associating_kinetics.cpp:198](https://github.com/jorge-ramirez-upm/lammps/blob/1c6faf70e94aef2389c208e8c80c60c084a96907/src/ASSOCIATING/fix_associating_kinetics.cpp#L198) | Neighbor proposals, strict cutoff and permanent-neighbor exclusion |
| [src/ASSOCIATING/pair_associating.cpp:61](https://github.com/jorge-ramirez-upm/lammps/blob/1c6faf70e94aef2389c208e8c80c60c084a96907/src/ASSOCIATING/pair_associating.cpp#L61) | Shifted FENE, r* and Ee energetics |
| [src/ASSOCIATING/pair_associating.cpp:71](https://github.com/jorge-ramirez-upm/lammps/blob/1c6faf70e94aef2389c208e8c80c60c084a96907/src/ASSOCIATING/pair_associating.cpp#L71) | Active forces below R0 and invalid-FENE rejection |
