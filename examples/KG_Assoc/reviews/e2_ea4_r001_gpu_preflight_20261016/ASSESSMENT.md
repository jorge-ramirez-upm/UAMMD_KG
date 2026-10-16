# Single-history Ea4 GPU diagnostic preflight — execution held

Starting clean local and remote KremerGrest SHA:
`e63944aedfa7432c69a0b40fff2437a58a24bd21`, verified 2026-10-16.
The user authorizes only Ea4 r001 from the qualified corrected-C1 8M parent,
with a 10,000-step maximum. No GPU execution occurred in this preflight.

The latest repaired build passes its existing read-only dossier verification and
current build authentication. Its exact source, compiler, executable and manifest
identities are copied in PREFLIGHT.log. The reference acceptance and exact r001
restart/chemistry pair authenticate; parent prefix is
`banks/e2_extensions/C1_periodic_recovery_v1/r001/state`, absolute step 8,000,000.
Restart SHA256: `09e1a9f5329a2be06e28112c5bc53e399f54c7aba74369684f12968f68d6b21b`.
Sidecar SHA256: `9eb4e566d96f0080d9a03677e5d23d231ce389193c71a57f68c58f22035e9ecc`.
The qualification remains unchanged; this is not a new scientific acceptance.

The established workflow has two incompatible limitations:

* Native argument validation rejects steps <= 0. The derived planner requires
  3,000–10,000 steps for smoke execution. No authenticated zero-step GPU readback
  path exists; --validate-initial-state is host-only and cannot substitute for it.
* The derived planner produces three-replica plans; the launcher always iterates
  all three histories. Neither provides a single-history execution selector.
  Invoking the existing launcher would risk unauthorized r002/r003 execution.
  Direct invocation or editing a prepared plan would bypass established gates.

Relevant existing code: kg_assoc_stars.cu argument validation;
campaign/kg_assoc_e2_transfer.py inspect/prepare/check_plan;
campaign/kg_assoc_e2.py launch. No such code was modified. The user's instruction
limits this milestone's commits to evidence and nonphysics validation documentation.
A narrowly scoped administrative launcher-selector change was therefore requested
explicitly through the pending clarification, rather than inferred or implemented.

The proposed next step is a tested launcher selector restricted to derived Ea4
reference-control r001 smoke execution, with an additional plan-bound approval
scope and step cap. Keep planner/build/parent checks and existing defaults intact;
leave other planned histories unexecuted. The existing reservation format also
requires twelve rows, even for one selected execution; do not prepare or claim
anything until the supported scope is resolved. No reservation identity or random
stream was allocated here, and no immutable attempt or approval was created.

Native host candidate tests pass, including original regressions, both precision
counterexamples, 398 cutoff/periodic cases and twelve ULP corruption rejections.
Both native host self-tests pass. Nine focused readback/forensic Python tests pass.
These deterministic checks do not execute a device readback, MD, candidate checks
on live GPU states, chemical event replay or endpoint validation.

The source also confirms that the existing independent all-pairs oracle is a host
routine over positions read from ParticleData after GPU synchronization. A later
live GPU trajectory can exercise these runtime comparisons; it must not be
reported as an oracle CUDA kernel. No port or numerical-contract change is made.

Previous repair dossier verification passes, including all twelve formal acceptance
validations, historical failed attempts, reservations and protected outputs. A new
baseline records 2,248 current file bindings, all unchanged. Frozen simulation
sources, examples/KG and src are untouched. No conformation/network/kinetic results
exist for a new history, no final endpoint exists, and no scientific conclusion
from earlier dossiers is revised.

Actual GPU history launches: 0. Device readbacks: 0. Candidate runtime comparisons:
0. Chemical events/exposures: unobserved. Additional MD steps: exactly 0. No seeds,
plans, execution receipts, equilibration, acceptance, registry or production action
was performed. The authorized single-history diagnostic remains unexecuted and on
hold pending a supported, explicitly approved selector. Final Git SHA is the
containing documentation commit, reported after push.

BASELINE.sha256 binds preserved inputs; INTEGRITY.sha256 binds this dossier except
itself. PREFLIGHT.log binds the exact authenticated parent/build and limitations;
raw host-test logs are retained verbatim. These JSON-formatted .log/.sha256 evidence
files and Markdown do not alter the repaired build's native/Python/JSON source map.
