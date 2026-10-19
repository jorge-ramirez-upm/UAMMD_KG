# CPU-only repaired extension preparation

User authorization: 2026-10-19. Starting SHA
32adf91b3dda2ef94b535597744234685d422e87.

Prepare exactly Ea8 r001–r003, 24M→40M (+16M each), and Ea10 r001–r003,
24M→56M (+32M each), from the exact authenticated corresponding 24M parents.
Prospective completed extension budget: 144M steps. Scientific windows remain
500k; finer chemistry/oracle/numerical records remain unchanged.

This authorizes CPU implementation, native compilation and immutable preparations
only. Each preparation approval carries GPU_execution_authorized=false. Neither
this document nor these approvals authorize a GPU launch. Future GPU execution
requires separate explicit approval and newly authenticated execution approvals;
no activation command is part of this milestone.

Preserve the old manual_ea_extensions_v1 state and every old attempt/reservation,
including the unvalidated native-PASS Ea8 r001 24M→40M trajectory. The new state
is manual_ea_extensions_readback_v2; all six attempts and requested/effective MD
streams are fresh. Chemistry retains its original same-Ea seed and absolute-step
keys and all inherited counters. Fresh GJ noise is not bitwise MD continuation.

Previously authorized interrupted-restart overhead remains separately recorded;
completed extension lengths are fixed. No scientific failure triggers an automatic
retry. No extension is run now. No Ea8/Ea10 acceptance, registry action or production
is authorized. The held old trajectory is not retrospectively validated.
