# Exact user execution authorization

The user explicitly authorizes execution approvals for the six existing preparations in
`manual_ea_extensions_48m_88m_v1`, based on starting commit
`4c5e6b5b4e9f14e7c379251d4e81331c15a2b3fb`.

- F04_N010_RP080_EE08_EA08 r001/r002/r003: absolute 40M to 48M, maximum 8M each.
- F04_N010_RP080_EE08_EA10 r001/r002/r003: absolute 56M to 88M, maximum 32M each.

Completed-trajectory budget: exactly 120M additional MD steps. Interruption overhead
is recorded separately. Replacement attempts require separate immutable execution
approval; these records grant no authority to new attempts or extensions.

The assistant publishes and CPU-tests the authorizations only. The user runs on
`titan`. No assistant GPU execution, scientific acceptance, registry activation,
production preparation, or changes to physics or RNG semantics are authorized.
Original preparation-only approvals and all historical evidence remain immutable.
