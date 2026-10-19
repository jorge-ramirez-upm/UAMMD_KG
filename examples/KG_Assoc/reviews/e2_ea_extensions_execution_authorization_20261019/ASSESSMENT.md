# Ea8/Ea10 extension execution authorization

This dossier publishes execution authorization for the six previously prepared
`manual_ea_extensions_readback_v2` histories. It authorizes user-run GPU work
only; no GPU program was launched while creating this dossier.

Each history has two immutable approvals. Its existing preparation approval
remains `GPU_execution_authorized=false`. A separate `*_execution.json` approval
has `GPU_execution_authorized=true`, binds the exact plan SHA, one replica, the
preparation-approval SHA, start/end steps, 500k diagnostic partition and cap.
The durable state pins both approval hashes.

| System | Replicas | Start → endpoint | Added/history | Completed cap |
|---|---|---:|---:|---:|
| F04_N010_RP080_EE08_EA08 | r001–r003 | 24M → 40M | 16M | 48M |
| F04_N010_RP080_EE08_EA10 | r001–r003 | 24M → 56M | 32M | 96M |

The aggregate completed-history cap is 144M steps. The existing runner retains
its explicit replica selector, endpoint and cap checks, fresh-MD reservations,
parent checks, no-output-reuse rule, candidate-oracle/numerical validation and
completion replay. It validates the GPU-enabled execution approval before it
creates `started.json` or invokes the native process.

The execution approval also pins the only post-preparation source changes:
`kg_assoc_e2.py`, `run_ea_extensions.py`, and this milestone's test file. The
launcher reconstructs the full current source map from the prepared plan plus
those exact hashes. Any other changed source, a modified approval, a changed
preparation approval, an unauthorized replica, a changed cap, an old executable
or a missing device-readback output fails closed.

The selected candidate executable remains the repaired optimized build:
`kg_assoc_stars_candidate_smoke` SHA256
`cab431ac0d110bd635390ffe37fae2527df02642666cc4f8105997b21f780306`.
The CPU-only call-path probe is still required before launch. This probe is not
a GPU readback. Each completed history must contain and independently validate
its genuine `state.initial_device_validation.tsv` evidence before it is marked
complete.

The held `manual_ea_extensions_v1` Ea8 r001 trajectory remains unvalidated and
unchanged. It is not an authorized parent, cannot be resumed by this state, and
its seeds are not reusable. All thirteen formal acceptance records and prior
campaign evidence remain protected. Ea8 and Ea10 remain on scientific hold.
