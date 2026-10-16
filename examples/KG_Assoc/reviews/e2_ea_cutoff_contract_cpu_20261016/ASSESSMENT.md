# Ea transfer cutoff contract and CPU diagnostic repair

**Decision: the validation arithmetic is repaired without changing production
candidate sets or frozen physics. CPU gates pass; ready for a separately authorized
capped GPU diagnostic retest after the authenticated build recorded in
BUILD_RESULTS.md. No GPU operation or retest is performed in this milestone.**

Starting clean local and remote `KremerGrest` HEAD:
`2f5c991bd354eb3c599f8cb2fed36ed2b5c9f6d2`. Date: 2026-10-16.
The authoritative failed smoke remains
[immutable historical evidence](../e2_ea_transfer_gpu_smoke_20261016/ASSESSMENT.md).
Its six completions, one oracle failure and five unexecuted histories retain
exactly their original statuses. No failed attempt is resumed or reinterpreted.

Two numerical discrepancies were established: float-first versus double-first
coordinate subtraction, and explicit nearest-image reduction versus remainder.
The strict cutoff can classify their rounded boundary results differently. The
chosen [contract](CONTRACT.md) is the already implemented UAMMD real-first,
double-image, strict-rsq predicate. The all-pairs oracle now independently uses
that arithmetic. The cell search, its image helper and `stickerDistance` are
byte-identical; reaction probabilities, candidate range, force laws, Ee/Ea,
Nevery, T, dt, integrator and random-stream semantics are unchanged.

This is a **numerical validation correction**, not a change to the production
geometric predicate. Switching production to double-first subtraction would be
a different numerical model choice requiring separate scientific authorization;
it is not needed to make an oracle of the frozen implementation correct.
LAMMPS's double-coordinate strict-cutoff semantics were inspected on the current
remote reference branch and their exact source bytes authenticated.

[Diagnostics](DIAGNOSTICS.md) now preserve full candidate/oracle sets, differing
pairs, sticker coordinates/partners, both arithmetic conventions, periodic images,
cutoff residuals, exact branch/step/sweep and build identity before termination.
A separate validation-only device readback compares initial positions, velocities,
IDs, types and partners to the authenticated loader representation before any MD.
It writes evidence and aborts on disagreement. Its device-to-host calls are
compiled but **not executed here**; pure CPU fixtures test comparison and evidence.
The established E2 validator audits new receipts while retaining old provenance.

The historical GPU failure's actual pair/frame was never saved. These proven
arithmetic defects are plausible causes, not a forensic identification of that
failure. Another search discrepancy remains possible; the independent oracle and
new failure capture must still pass a real diagnostic retest.

CPU evidence includes the original candidate regressions, 398 additional boundary/
periodic/differential cases in each of single and double precision, both explicit
counterexamples, failure/readback corruption tests, fourteen transfer tests and
149 shared/readback tests. Single/double host testing does not change the campaign
precision: campaign executions remain single precision. The temporary seed fixtures
in tests are not campaign reservations; real consumed smoke streams remain ineligible.

All twelve acceptance records/payloads and the failed-smoke outputs are unchanged.
Historical executable/source identities remain bound to their original commits;
prior manifests and dossiers are not rewritten for today's source. The six
explicit source transitions are authenticated against this milestone's starting
commit. New build directories preserve every historical executable.

No scientific equilibrium, structural mixing, initialization-bias or production
suitability claim follows from this repair. All reference qualifications persist.
The next stage requires separate capped GPU authorization, fresh immutable seed
reservations and new attempts, using the established planner and plan-bound gates.
No further equilibration, kinetic screen, formal acceptance, registry selection
or production preparation occurs here.

[VALIDATION.md](VALIDATION.md) records reproduction and limitations;
PRESERVATION.json and INTEGRITY.json bind the audit and scoped implementation.
