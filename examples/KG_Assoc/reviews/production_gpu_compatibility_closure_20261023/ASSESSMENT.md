# Scientific and numerical closure review of production GPU compatibility

Starting clean local/remote `KremerGrest`:
`6a5e5c9732621639a15140087ccf0d25fa5164c7`.
Review date:23 October2026. This milestone executed **zero GPU calculations and
zero additional MD steps**. It changes only this new review dossier. The containing
publication commit is the final review identity, reported after local/remote verification.

## Recommendation

**Accept the existing supported compatibility evidence with explicit, narrowly scoped
software/scientific validation limitations, subject to subsequent explicit user
approval of a separate immutable CPU decision.** No observed defect presently
justifies making new native instrumentation mandatory. Direct instrumentation remains
an option for stronger assurance, not a repair demanded by a reproduced failure.

This is a recommendation, **not a waiver or production activation**. The existing
compatibility hold remains in force. No capability flag, validator, original receipt,
plan, seed, executable, journal or acceptance record was changed. In particular,
production-specific exact initial GPU readback and independent runtime candidate-
oracle comparisons remain **not demonstrated**, not PASS. PROPOSED_DECISION.md
specifies the separate approval record needed to resolve those additional certification
requirements without relaxing any numerical/provenance/completion/output gate.

The recommendation is defensible because all15 actual production-path GPU tests
pass fresh independent replay, the disputed loader/partner/search paths are shared
with substantially GPU-validated E2 code, and no source/observed numerical discrepancy
is found. It is not based merely on a console PASS or the existence of source hooks.
Whole-program identity and exhaustive correctness are not asserted.

## Authentication and independent numerical findings

All fifteen real tests have ordinary immutable `validated.json` receipts, zero-exit
native_finished records, actual stdout/stderr, atomic native completions and output
hashes. Every receipt's exact history/plan/parent/seed/approval/executable/source
identity reauthenticates through the original published authority. The started source
map equals the same currently authorized map used by post-run validation. Source
ancestry and all native dependencies/build manifests remain valid. No recovery,
replacement, failure journal or consumed-seed substitution was found in this cohort.

The review called the **unchanged strict independent numerical validator again on
all15 native output sets**, including chemistry_trace, event replay, endpoint geometry
and the P4 stress reader/grid checks. Every resulting numerical object is exactly
equal to its original completion receipt. Replays are written only into the review;
no original completion/status file is updated. REVALIDATE.txt blocks every non-Git
subprocess, making native/GPU execution unreachable during the numerical replay.

| Existing evidence independently checked | Result |
|---|---|
| Exactly100k additional steps/history |15/15 PASS;1,500,000 existing steps total; absolute intervals follow their exact accepted parents, not a common initial step. |
| Exact source/build/executable/approvals/streams |15/15 PASS; smoke SHA e1a00204f8753b4e513e6817169f40ec4aca0854decf52553550aaf25756d6d7, source authority SHA279cf4c2bc007865cd492597f322f80bfff80ec556b2e8acae21d7aaea223cf3. |
| Native device/integrator evidence |15 actual TITAN Xp, single-precision GJ logs, T=1,dt=.01,friction=.5; no native failure/error message. |
| Finite thermo |100 rows/history,1500 total; complete1000-step cadence and finite recorded energies, pressure and kinetic temperature. |
| Stress |100,000 samples/history,1.5M total;116 lag/count rows/history,1740 total; all six channels finite. |
| Six-channel G reconstruction |All1740 saved G values reproduce from their six saved volume-weighted channels; maximum observed absolute residual0.0. |
| Exact finite multi-tau support |All grids/counts match the existing implementation. Last raw lag901.12 has one pair and is not an independent-information estimate. |
| Reaction schedule and event replay |15,000 chemistry sweeps;46,901 accepted creations and46,926 breaks,93,827 events total; absolute100-step scheduling, times, IDs, molecule/type labels, reciprocity and counters pass. |
| Inherited counter accounting |Native cumulative totals equal authenticated parent offsets plus new events; thermo segment counters reproduce the timestamped event trace. |
| Final chemistry/geometry/topology |Replay equals final association pairs; valence one, permanent identity/type/topology/box, finite positions, permanent/association geometry and completion step checks pass. |
| Final archival velocities |All1,022,839 particle velocities across15 endpoints are present and finite. This is end-state evidence, not an initial-state device comparison. |
| Output integrity |All240 completed-directory files and journals are hash-bound/preserved; no numerical/provenance mismatch was found. |

PER_SYSTEM.md gives every condition's exact absolute interval, new C/B counts,
bond populations and G(0); replay/PER_SYSTEM.csv additionally records each parent,
seed, executable, final snapshot/association and receipt identity plus numerical ranges.
The15 per-history replay logs preserve fresh validator results and exact output hashes.
The raw completed evidence is authoritative; console status alone was not used.

The actual native integration time totals669.8404s, ranging28.0216–85.1671s/test.
These are observations of the user's completed jobs, not new runs or promises of
100M performance. No new resource allocation, trajectory or seed was prepared.

## Rheology and chemistry interpretation

The estimator is unchanged:

    G(t) = (Gxy + Gxz + Gyz)/(5T) + (GNxy + GNxz + GNyz)/(30T).

Each channel already includes volume; target T=1 is the frozen normalization.
Stress was sampled after integration/scheduled chemistry every MD step, with no
step-zero sample, using the existing Correlator6(40,16,2). The three normal
differences are dependent and do not supply extra statistical replicas. The
existing P4 reader and its arithmetic/support conventions were reused; no stress
formula, raw stress export, temporal correlator or new correlation estimator was added.

Observed G(0) ranges37.20279–66.99719 across geometry/chemistry conditions. The
plots show signed whole-test curves and accepted counts. Fast stress-waveform
similarity is useful compatibility evidence, not proof that slow rheology is
Ea/Ee-independent. The100k tests span1000 reduced time units; their sparse late
pairs and single family per condition cannot establish a terminal tail or zero-shear
viscosity. No viscosity, tail-resolution or equilibrium claim is made from them.
No additional equilibration criterion or mandatory temporal/conditioned G(t) output
is introduced.

Recorded kinetic temperatures range0.964492–0.993626, below the thermostat setpoint
rather than identically1. Similar finite-step kinetic-estimator ranges were already
reported in the E2 evidence. This review confirms the configured T=1 and finite
measurements; it does not newly calibrate the thermostat, prove its target distribution
or substitute instantaneous kinetic T into G. The existing finite-step/discrete-time
qualifications remain. No instability or new parameter/source mismatch is found.

The Ea10 r003 test has only2 creations and6 breaks. It checks the recorded chemistry
path and event consistency, not accurate high-barrier rates or slow-network mixing.
Its accepted initial state's unresolved triangle/conformation qualification remains
unchanged. The15 conditions have one selected family each (Ea10 r003, otherwise
r001); the original families remain paired where appropriate, and curves/channels/
time bins are not promoted to independent preparations. The other30 production starts
retain their existing formal/host evidence and were not newly GPU-tested here.

## Shared implementation versus missing production certification

SOURCE_EQUIVALENCE.md documents actual call sites and distinctions. Thirteen
shared native files match hashes recorded by both optimized builds. The entire
duplicated restart-reader and partner-construction blocks are text-identical.
Both programs call the same LAMMPS-data/float32 ParticleData loader, restore the
same partner vector, disable velocity initialization and use the same GJ source.
Both chemistry paths synchronize before calling the **same host cell-search overload**
on stable-ID-ordered GPU-evolved coordinates and the same Kinetics implementation.
There is no separate production-only reaction search algorithm to validate from scratch.

The source audit independently rechecked six genuine earlier E2 GPU readback payloads,
43563 particles each, with exact comparisons, and authenticated complete records of
1,200,000 earlier runtime independent-oracle comparisons. These strengthen confidence
in the shared loader/search. They remain E2 evidence for that geometry and executable;
they are not relabeled as checks performed by production. Existing boundary/image/float
CPU tests and P4 stress/force/cache tests remain supporting evidence, not new GPU runs.

Production also has genuinely distinct stress-aware WCA/permanent-FENE wrappers,
observation/synchronization and stream-policy code. Both binaries are optimized
separate translation units; the review does not infer byte-identical trajectories
or exact initial GPU arrays merely from shared source. Production final type labels
are written from immutable input metadata, not a fresh dump of initial GPU pos.w.
The absent per-particle pre-MD payload and per-sweep independent pair-set/rounding-
environment comparison are **residual validation uncertainties**. Valid replay can
coexist with an unobserved candidate omission; finite stress alone cannot exclude
every initialization error. No such concrete defect is demonstrated by this cohort.

Earlier failed smoke/readback/dispatch histories remain failed or held under their
original conclusions. Their subsequent validation-only repairs do not establish an
undocumented production diagnostic. The present production absence is intentional
in its source and was explicitly reported by the driver, rather than a claimed
readback/oracle hook whose evidence silently disappeared.

### Documentation correction

Earlier production-preparation capability prose said the final archive did not
contain velocities. Actual `writeCampaignFinalSnapshot` and all15 files include a
Velocities section. This review corrects that description without editing the
historical dossier. The archive is still not a full restart bundle: it lacks a
serialized chemical-counter/RNG/GJ/correlator continuation state. Final velocities
cannot reconstruct initial velocities or unrecorded stress microtrajectories.
The uninterrupted100M/no-stitching production strategy remains unchanged.

## Why recommend conditional acceptance of existing evidence

The remaining requested mechanisms are useful additional **certifications**, with
real residual risk when absent. They are not themselves evidence of a physical
failure. Current independent outputs, broad per-condition GPU coverage, matching
shared source and substantial earlier exact diagnostic evidence give a reasonable
basis for qualified software compatibility under the existing frozen configuration.
No present mismatch supplies a concrete corrective target or requires changing
native physics/loader/search. Mandatory instrumentation would improve assurance
but is not necessary to repair an observed defect in these results.

The proposed subsequent CPU record would waive only the requirement to obtain those
two additional production-specific certificates, while recording that they remain
not performed. It would bind this evidence, exact sources/builds, tested hardware,
frozen45 initial states/plans and all scientific qualifications. It must **not** waive
numerical integrity, event replay, source authentication, output hashes, approval
limits, endpoint validation, or fail-stop/recovery rules. It would grant no execution
and activate no registry. No such record is published by this review.

If the user wants stronger direct assurance instead, reuse existing helpers in a
new validation-only production diagnostic build with demonstrated pre-MD dispatch
and runtime comparisons, under separately approved provenance and bounded user-run
GPU validation. That is a prospective alternative, not code/plan/seed preparation
or a GPU command in this milestone.

## Preservation, tests and remaining prerequisites

Five new read-only-review tests,17 existing adapter tests and4 source-boundary tests
pass: **26 targeted deterministic CPU tests**. Fifteen real independent numerical
replays pass, reproducing every completion receipt. Six historical exact readback
payloads and1.2M recorded oracle comparisons reauthenticate on CPU; no new GPU
certification is claimed. Earlier correlator/P4 tests are reused rather than
unnecessarily repeated. Every test/audit job is bounded at600s.

PRESERVED.sha256 protects **5476 bindings**, including all15 acceptances, all45
production preparations, all completed short-test outputs/journals and prior scientific
reviews, failures, recoveries, sources, executables and reservations. The final audit
also checks all240 completed files and the frozen preparation receipt. No existing
file, native code, numerical validator, RNG or integrator was modified. Only this
new review dossier changed; `src/` and `examples/KG/` are untouched.

Remaining production prerequisites are explicit: the user must decide whether to
approve the proposed additional-certification policy record or request direct
instrumentation; then separately authorize active-registry publication and exact45
production execution approvals with CPU preflight. The old hold and false capability
flags remain immutable meanwhile. No100M run, registry activation, production approval,
new extension, formal scientific acceptance or waiver was issued here.
