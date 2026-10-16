# Proposed preparation and validation protocol — not implemented or authorized

## Minimal implementation work, after separate authorization

Reuse the existing native Ea-switch helper and validated event/network readers.
Do not change the reaction kernel, energy, candidate search, integrator parameters
or frozen protocol. Keep the accepted parents read-only. Ordinary same-condition
extensions and their validation rules must retain their present behavior.

| Layer | Existing behavior | Necessary scoped change |
|---|---|---|
| `kg_assoc_stars.cu` restart front end | Explicit `--switch-ea-from 4 --Ea target` already supported; parent seed forced | Add an explicit, guarded chemical-reseed mode for derived histories, with expected old seed and distinct requested new seed; default unchanged |
| `kg_assoc_ea_switch.cuh` | Checks exact parent Ea, distinct target and explicit marker | Reuse unchanged |
| E2 planner/checker | Ordinary preparation Ea=4 only; cross-Ea C1 is smoke-only; same-condition predecessor required | Add explicit derived-preparation provenance mode, accepting only the exact qualified reference pairs and target SID/Ea whitelist; never reinterpret it as an ordinary extension |
| E2 parent/segment validation | `read_parent` requires parent seed equal to child seed | Authenticate parent seed separately from child seed and verify both against explicit reseed provenance; preserve all other strict checks |
| Storage/catalog | E2 bank ID omits Ea; existing seed map is keyed by bank | Include full target SID, Ea, branch ID and unique attempt in the derived identity; add explicit seed allocations; ensure same-bank records cannot be confused |
| Completion/acceptance readers | Understand ordinary E2 or corrected historical C1 | Carry derived parent acceptance path/hash, parent pair hashes, old/new seed identities and qualifications into a new reviewed provenance kind/mode; update schemas/readers/tests together where necessary |

Names of future flags/schema fields are design proposals, not executable commands
in this dossier. A suitable CLI convention would require both an expected parent
chemical seed and an explicit distinct new seed, analogous to the existing Ea
switch marker. Do not silently change the meaning of `--seed` on all restarts.
Parent sidecars must not be edited, even in a copied file pretending to be an
ordinary accepted restart. Decode the authenticated parent, validate it, then
initialize the child stream separately in memory.

At initialization preserve particle IDs/types, molecule IDs, permanent topology,
unit masses, box/density, positions modulo PBC, velocities and every reciprocal
chemical partner exactly to the loader's represented precision. The loader
centers/folds coordinates and converts to single precision; bytewise snapshot
identity or continuous unwrapped images is not promised. Validate minimum-image
coordinates/displacements and energies against the serialized parent, allowing
only established numeric representation tolerances. No velocity resampling,
partner resampling, force-law change or inferred chemical equilibrium is allowed.
Ea alone changes to 6/8/10; Ee=8, T=1, nu0=20, Nevery=100, dt=.01, r_assoc=1.25,
damping=2, K=30, R0=1.5 and the actual original box stay fixed.

Preserve the absolute parent step 8,000,000, physical time=step·dt and inherited
creation/break counters; record a new branch age starting at zero. Future events
use new chemical seed and absolute steps greater than 8M. Keep the identities
`creations−breaks=active bonds` and initial old-final/new-initial populations.
Do not reset both cumulative counters to zero with an already bonded network.
If segment-local activity counters are wanted, save their inherited offsets;
calculate activity by differences. Existing chemistry-sweep/candidate counters
are segment-local and must be labeled accordingly. No synthetic creation events
at initialization. New output sidecar records target Ea, new chemical seed,
absolute completion step and cumulative counters; metadata records both old and
new seeds and branch age. Do not overwrite any accepted file or reuse its output
prefix. A failed child remains a failed immutable attempt, not a replacement.

GJ construction resets internal step to zero and uses a fresh effective MD seed;
`initVelocities=false` preserves velocities. No integrator memory is restored.
Label this as a derived, independently reseeded preparation, **not bitwise MD
continuation**. Do not stitch IATs, SEMs, lifetimes, stress, transport or correlation
origins across the new-stream boundary. Initial bonds are left-censored for
child-only lifetime estimation; record survival separately without claiming full
lifetimes. Children inherit parent identity for paired statistical analysis.

Seed allocation must reserve nine new chemical streams and nine new effective MD
streams, plus separate controls, checking all existing plans/records and seed-map
reservations. Proposed illustrative chemical triplets are 620601–620603,
620801–620803, 621001–621003; illustrative requested MD triplets are
630601–630603, 630801–630803, 631001–631003. These are **not allocated, reserved
or approved** by this review. The implementation must allocate and authenticate
actual choices, including effective 32-bit MD collisions; distinct requested
64-bit seeds alone are insufficient. Avoid reusing parent 22001–22003 or
32001–32003. Each Ea/replica gets its own streams. A same-Ea control must also
use distinct streams. Seed uniqueness does not prove PRNG independence.

## Validation gates, in increasing cost

1. **CPU front end and restart fidelity.** Test explicit-switch/reseed positive
   paths and wrong parent seed/Ea, missing marker, same seed, wrong chemistry,
   partner nonreciprocity, changed geometry/Ee/cutoff, absent acceptance, corrupt
   parent hash and existing-output rejection. Demonstrate exact chemical pairs,
   counter offsets, absolute-step/cadence metadata and physical-state fidelity at
   branch age zero, before constructing a GPU system. Preserve default extension
   compatibility. Rebuild all affected header-based executables when a shared
   included header changes; record source/executable/build hashes and actual SHA.
   CPU fixture tests must reject system-ID/Ea/bank confusion. No acceptance record
   is created by this gate.
2. **Separately approved, capped numerical smoke.** After CPU checks pass, use
   accepted parents directly, never smoke endpoints as subsequent parents. Include
   target Ea6/8/10 and a reseeded Ea4 control, with independent streams; at most
   10k steps per smoke. Check first-state equality, finite coordinates/velocities,
   valid FENE, candidate oracle for both free/active candidates, event replay,
   partners, source/seed logs, numerical metadata and final output receipts. Few
   or no Ea10 reactions are expected in a short smoke: that validates loading and
   fail-closed execution, not kinetics or equilibration. No GPU smoke is run here.
3. **Targeted coupled-sampler/kinetic screen.** Retain three parent families and
   an Ea4 reseeded control. Begin with small capped chunks, review actual reaction
   exposure before extending. Use the event-count planning scenario in ASSESSMENT,
   around 200 distinct-neighbor losses per history, only as an initial kinetic
   screen. Track accepted creation/break rates, exact active-bond/free-sticker
   exposure, candidate opportunity, energy-dependent acceptance and gain/loss
   rates. Compare with q scaling as a conditional prediction; departures can be
   genuine moving-geometry kinetics. Inspect reference/control and all target
   population/shape paths for an immediate or coherent persistent change. Do not
   treat a rate mismatch alone as equilibrium failure or rate agreement as mixing.
   Where a discrepancy appears, use a targeted simpler coupled dimer/K1 or short
   star timestep comparison, chosen after inspecting the discrepancy. For a
   timestep check, halve dt and double Nevery to retain physical reaction interval
   Δ=1; that isolates MD discretization from q/cadence. A separate interval test
   changes Nevery at fixed dt. Both are validation studies, not changed campaign
   physics for a new accepted endpoint. Their GPU cost has not been benchmarked.
4. **Scientific relaxation review, not automatic acceptance.** Use each original
   history separately, retaining branch-age zero and the inherited source context.
   Choose physical-time windows long enough for observed activity, supplemented
   by equal-event windows labeled as nonuniform physical time. Compare unshifted,
   shifted and final-quarter paths; use nonoverlapping 500k/1M/2M windows when
   duration permits, rather than declaring stationary sparse constant bins.
   Measure intra/inter balance, 0/1/2 intra-loop populations, all inter-star
   multiplicities 0–4, L1, L2, distinct degree/moments, giant size, isolated-star
   identities/residence, satellite membership, Rg² and center–terminal R². Retain
   algebraic coupling between observables. Look for returns/plateaus or coherent
   redistribution, not solely smaller slopes. Estimate segment-local IAT/N_eff
   and 5/10/20-block sensitivity; sparse/constant bins are unresolved, not mixed.
   Treat three original parent families as independent units, with paired
   cross-barrier/control contrasts and df=2 exploratory uncertainty. Define
   observable-specific tolerances before interpreting a candidate equivalence
   test; a CI containing zero or equal total occupancy does not establish it.
   Full structural decorrelation is not an automatic requirement for qualified
   initialization, but a material new drift or unresolvable initialization
   discrepancy warrants a hold and diagnostic-specific extension proposal.

A common short physical-time settling interval can check mechanical restart
behavior. No common minimum duration establishes comparable chemical/topological
relaxation across barriers. Counts of accepted events, distinct neighbors and
actual identity coverage, plus return/mixing diagnostics, are more informative.
Repeated exchanges involving the same small subset of stars must not count as
whole-network mixing. Pilot 200 losses/system means only .2 losses/star and is
particularly inadequate for rare isolated and satellite states.

## Hybrid fallback and acceptance boundary

If transferred/control paths expose a bias that cannot be resolved from parent
variation and late returns, add a separately authorized E1-started comparison at
Ea6 first, using the same Ea6 Hamiltonian/kinetics and independent seeds. It is
cheaper than Ea10 and probes route dependence. Its initially unbound transient
must be retained and its own relaxation assessed; a short unbound control cannot
serve as an equilibrium truth. Escalate to other barriers or longer runs only
when evidence calls for it. An E1 route also needs planner support for these
same-bank target systems; bypassing the existing guard is not an authorized path.
If bias persists, improve sampling at Ea4 under its own review before creating
new derivatives, or retain a hold. Do not silently replace the accepted parents.

Only a later scientific assessment can recommend exact target endpoints; formal
registration requires separate user approval and system-specific records binding
actual target physics and child histories. Reference acceptance alone permits
none of those new target systems. Reused reference parents and child branches
must never multiply the independent-parent count. No registry selection or
production preparation belongs to this protocol implementation or review.
