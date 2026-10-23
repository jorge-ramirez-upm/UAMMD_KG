# E2 and production: shared implementation, distinct evidence

`source/SHARED_IMPLEMENTATION.log` records thirteen exact native-file SHA256s
matching the historical E2 optimized-build source map, production's authenticated
native dependency map and current bytes. Source version equality is established
for those files; **the two executables and their whole programs are not identical**.
The production100k and100M binaries use the same included production implementation,
with different compile-time step caps. Source/build/executable identities remain
those in the frozen preparation and short-test authorization dossiers.

| Path / operation | Shared evidence and actual distinction |
|---|---|
| `kg_assoc_campaign_production.cu` | Strict production CLI fixes dt=.01,T=1,nu0=20,Nevery=100,r_assoc=1.25 and cadence.100k tests use the smoke macro;100M remains separately gated. Its validate-initial-state branch checks metadata on CPU, before System creation. It is not the E2 fingerprint/readback path. |
| `readRestartMetadata` in `kg_assoc_stars.cu:282` and `kg_assoc_production.cu:270` | Entire function text is identical, SHA256 e4ffb2f968bc47901d5e8a057c84b1443edaf45cfcb8cf90c8f4d36b3195acb5. It checks exact field order, physical parameter validity, active pairs, unique IDs, end marker and inherited event-counter balance. Request-validation/CLI policy around it differs. |
| Production request/parameter restoration (`kg_assoc_production.cu:339,882–916`) | Frozen physical parameters are checked against accepted metadata. Requested Ea/Ee and the fresh production seed are retained intentionally. This differs from seed-preserving E2 extensions; it is the documented production RNG policy, not silent bitwise continuation. |
| `kg::readLammpsDataFile`, `makeSimulationBox`, `createParticleDataFromLammps` (`../KG/kg_lammps_io.cuh`, `kg_runtime.cuh:38–95`) | Both call the same reader/constructor. Centered/folded float32 positions, type−1 in pos.w, stable IDs, unit masses, restored float32 velocities and zero forces use the same code. Both set initVelocities=false. Common ParticleData and GJ source hashes match. Production's exact pre-MD GPU arrays were not dumped; final archival labels alone do not measure initial GPU pos.w. |
| Partner restoration, shared `StickerState::loadPartners` | The complete call-site block creating state, converting one-based pairs, checking IDs, loading reciprocal partners and constructing AssociatingFENE is text-identical; SHA25622dccb7af1750a2c0c5232216c2cc6535f48bab5b989099e21bab10726d3ff80. Shared state header validates sticker-only valence one/reciprocity and syncs host partners to its device vector. |
| GJ integrator / streams | Same GronbechJensen/Basic code and dt,T,friction,initVelocities=false. E2 can reset a distinct MD seed immediately before construction; production seeds System earlier and uses its requested seed for chemistry too. The supported constructors before GJ contain no applicable extra System RNG draws; the third-next32 effective-seed derivation remains the established policy. Production does not directly read out the internal GJ seed; requested seed bindings/logged chemistry plus source derivation are the available evidence. |
| Reaction candidate call (`kg_assoc_stars.cu:1203`, `kg_assoc_production.cu:1166`) | Identical overload/arguments: particles,state,double box lengths,r_assoc. Both synchronize GPU-evolved positions before chemistry. The **search itself is common host C++**, reading CPU positions via stable-ID-ordered indices, then the same periodic cell enumeration; it is not a separate untested production GPU search implementation. |
| `kg_assoc_star_runtime.cuh:210–319` | Same corrected periodic binning for unwrapped coordinates, ID-pair deduplication, represented float subtraction before double minimum-image reduction, strict squared cutoff and reported distance. It includes geometric sticker pairs regardless of chemical availability; shared Kinetics handles eligibility/acceptance. Earlier E2 and CPU oracle tests support this common routine; production does not record exact candidate sets or fenv mode per sweep. |
| `kg_assoc_kinetics.cuh`, `kg_assoc_interactors.cuh` | Same Kinetics update and associating shifted-FENE interaction. Absolute step keys, finite-step attempts and temporary-bond mechanical range remain the implemented semantics. Production's accepted events/counters were independently replayed; this does not prove completeness of unrecorded candidate sets. |
| Permanent/nonbonded force and observation paths | E2 calls standard WCA/FENE wrappers. Production uses existing StressAwareWCA/StressAwareFENE, the same associating interactor, buffered six-channel stress after integration/chemistry, COM and bead observers. These are real whole-program differences; source-sharing of initialization/search does not prove bitwise force trajectories. Existing P4 stress/force/cache tests and the current15 actual production GPU tests support this distinct path. |
| E2 diagnostics (`kg_assoc_stars.cu:1147–1153,1205–1211`) | Only the candidate-enabled E2 build dispatches exact initial readback and all-pairs comparisons before Kinetics update. Production neither includes that oracle dispatcher nor produces those payloads. There is no hidden production option that was accidentally omitted from the short-test commands. |

## Earlier actual GPU evidence authenticated in this review

`SOURCE_REVIEW.txt` checked the original six late Ea8/Ea10 E2 completion receipts,
plans and output hashes, then reran the existing exact CPU readback validator on
**six real device-to-host payloads**,43563 particles each. It checked complete
100-step cadence/count records for **1,200,000 existing oracle comparisons**,
matching authenticated completion counts and native PASS logs. These were runtime
independent comparisons on synchronized GPU-evolved coordinates; no new oracle
comparison or MD integration occurred here. Their source/executable provenance is
`ea_extensions_48m_88m_20261021_v1`, candidate executable SHA256
6331c034d8ddb494be616770f2bcc56f5a5fb644f5cb30838e593d259eaf451d.
The oracle is an independent host all-pairs routine, not a second GPU kernel.

This strongest directly rechecked cohort covers the F04/N010/RP080/Ee8 geometry
at Ea8/Ea10. The earlier complete transfer smoke also records all four barriers
and three families; frozen-cutoff CPU tests cover boundaries, periodic images,
small/degenerate grids and float/double cases. It would be inaccurate to claim
an independently compared production candidate set for each of today's15 conditions,
or exhaustive search coverage for every possible future coordinate/state.
All earlier failed smoke/readback/dispatch attempts retain their original failed
or held conclusions and bytes. The cutoff-oracle/expected-velocity repairs did not
change the physical loader/search. The earlier extension dispatch omission shows
why a source hook cannot be presumed executed; today's production absence is
explicitly recorded rather than relabeled as a PASS.

## Evidence classes and residual uncertainty

A. **Direct current production GPU evidence:** exact native/source/approval/input
bindings, successful100k native completions, actual single-precision TITAN Xp/GJ
logs, finite thermo and all six stress channels, exact lag/count/normalization,
event scheduling/replay/counters, final coordinates/velocities and archival permanent
identity/topology/association geometry. These15 cases exercise every condition's
geometry/chemistry with one selected family, not every one of the45 production starts.

B. **Support for shared implementation:** thirteen matching native files, identical
restart-reader/partner blocks, common loader/search/update call paths, prior exact
E2 GPU readbacks/oracle runs and existing CPU/P4 tests. This is substantial tested
reuse, not a new production readback/oracle result or proof of whole-program identity.

C. **Not demonstrated for production:** byte-exact per-particle GPU state immediately
before the first integration, and independent per-sweep candidate-set/distance equality
on the actual production positions/rounding environment. Finite stress/event replay
cannot rule out every initialization discrepancy or rare candidate omission. Thirty
remaining family starts have host/qualified-state evidence but no new production100k
run. Neither100M stability nor equilibrium/terminal rheology follows from this smoke.

No concrete current initialization/search defect is identified. The absence of
additional certification is residual validation uncertainty. Mandatory new
instrumentation would increase direct assurance, particularly about compiler/call-site
or rare-boundary effects, but is not a repair justified by a reproduced production
failure in these data. The proposed decision in this dossier addresses whether
that extra assurance is required; it does not change any observed status or gate.
