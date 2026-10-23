# Evidence required versus capabilities of the frozen production executable

The100k build includes the same native production implementation, fixed parameters,
corrected candidate search, stress path and output formats, differing from100M only
by the compile-time step cap. Its optimized bytes and258 repository-native dependencies
are authenticated in the preceding preparation dossier. No native file or build is
changed here. Exact preserved smoke hash:
`e1a00204f8753b4e513e6817169f40ec4aca0854decf52553550aaf25756d6d7`.
The frozen100M hash remains
`5c396533482e08a48bd20fc27e6bb63bec790efecf843ae73cf01a52bf6265e5`.

| Requested check | Evidence actually available / pending |
|---|---|
| Exact qualified parent | All15 acceptances and45 restart/sidecar pairs are authenticated through the existing preparation/registry validators;15 selected inputs have a fresh host-only representation audit. |
| Initial positions/velocities/IDs/types | Host parser plus existing E2 `represented_position` and float32 velocity materialization check all selected particles. Per-particle digest includes ID,molecule,type,partner,xyz andvelocity. **No actual production GPU readback is emitted.** |
| Initial partners/counters | Accepted sidecar/hash, valence-one/type checks and inherited counters; native invariant checks inspect live partners, bond geometry and conservation. This is not an exact per-particle initialization dump. |
| Corrected periodic candidates | Current native dependencies match the authenticated corrected search implementation; historical corrected cutoff-contract/E2 GPU evidence is reused. **Production does not execute the independent E2 all-pairs oracle.** Aggregate candidate counts cannot certify pair equality or reconstruct per-sweep positions. |
| Reaction scheduling/counters | Pending native100k logs report1000 chemistry sweeps; the adapter checks absolute step range/cadence/time for each event, molecule/type identity, segment counters against thermo and cumulative native totals against inherited offsets. Existing replay enforces reciprocal valence one and final partners. Zero new reactions at a high barrier is allowed; no arbitrary activity threshold is introduced. |
| Numerical geometry/identity | Existing runtime finite/FENE/association invariants and independent verify_run; added adapter checks final ID/type/molecule/permanent topology/box equality, finite coordinates and final association distances<R0. Final archive does not contain velocities or a reloadable MD/chemistry checkpoint. |
| Stress | Pending100k samples, six finite volume-weighted channels, exact existing normalization,116 populated lag/count bins; final raw lag901.12 has one pair. Existing P4 reader recomputes G; exact finite-grid arithmetic is checked. This short observation proves no terminal rheological tail or viscosity. |
| Native completion | Atomic native complete.json, zero process exit, exact absolute start/end and100k duration, PASS footer and stdout/stderr hashes. |
| Independent completion | Separate immutable validated.json or explicit recovery.json; all nine native outputs, native journals, source/approval/parent/build identities and exact hashes rechecked. Native PASS alone never causes a skip. |

No new online/offline correlator, GPU stress implementation, stress formula, raw
stress export or temporal correlator is introduced. Existing P4 stress tests,
Correlator6 count/block-average tests and serialization tests are reused, not rerun
as though they were missing. Normal differences are dependent and do not create
six independent replicas. The existing six-channel formula remains
G=(Gxy+Gxz+Gyz)/(5T)+(GNxy+GNxz+GNyz)/(30T), each channel already volume-weighted.

The strict production executable has no initial-state device-dump or independent
oracle option. The E2 dispatcher in kg_assoc_stars.cu belongs to a different
executable and cannot certify the production loader merely by being present in the
repository. A fresh E2 run on these parents would likewise not prove the production
call path. No absent evidence is fabricated, waived or relabeled. Plan capabilities
explicitly set initial_GPU_readback=false and runtime_independent_candidate_oracle=false.

**Decision after the user runs these tests:** review supported numerical/stress
compatibility, while retaining a hold on full device/oracle certification. If the
requirements continue to demand those checks on the production path, a validation-only
hook/new authenticated build and explicitly approved compatibility binding to the
frozen campaign are needed. This is a concrete remaining code issue, not a reason
to redesign physics, estimator or restart machinery. No production registry may be
activated or100M launched based solely on this bounded batch's numerical PASS.
