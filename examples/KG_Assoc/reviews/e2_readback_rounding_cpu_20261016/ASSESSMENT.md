# CPU repair complete; separately authorized GPU retest required

The initial expected-velocity defect is corrected in the validation path only.
All CPU gates pass with an authenticated new optimized out-of-tree build. The
infrastructure is ready for a separately authorized capped GPU diagnostic retest.
A kinetic screen remains on hold until that GPU retest passes; this CPU milestone
neither exercises the repaired live readback nor resolves the original candidate
oracle concern on the GPU.

Starting SHA: `b8f518d49c9b00f7d957bc42fcaf0a34a9317c82`, clean local/remote
KremerGrest. The final SHA is the containing receipt commit. See BUILD_RESULTS.md
for the final source commit, manifest and executable hashes.

The old expression reproduces 43,559 incorrect x values and 43,556 incorrect y
values under the campaign NVCC/GCC -O3 toolchain. All 43,563 z values round correctly.
The repaired helper forces real storage before widening, giving exact agreement
for all 130,689 expected components with Python's independently computed parent
float32 values and the saved actual GPU values. The unchanged exact comparator
accepts the corrected host replay and rejects all 12 injected one/two float32-ULP
actual-velocity corruptions. No tolerance was introduced. No previous output was
edited or its native failed footer reclassified.

Final validation passes 168 Python tests, both native host self-tests, existing
candidate regressions, 398 cutoff/periodic cases, the twelve ULP rejection cases,
and twelve host initialization checks at absolute step 8,000,000. The first driver
attempt's forensic import error is retained alongside the corrected final run.
These are deterministic regression checks, not stochastic convergence results.

The production loader, device initialization, forces, reaction kernels, candidate
search, integrator and random streams remain unchanged. Ordinary preprocessed
source is identical with build timestamps held fixed. Ordinary trajectories were
not run; unchanged ordinary behavior is supported by source equivalence rather
than a fabricated trajectory comparison. The expected-value helper is used only
by diagnostic validation, has no physical state mutation and makes no random draw.
Protected examples/KG and src files remain unchanged.

Preservation authenticates 2,145 unchanged prior file bindings and three intended
source transitions against starting Git blobs. All twelve formal acceptances also
pass fresh exclusive validation. Both historical failed campaigns, their immutable
attempts/reservations and partial outputs, accepted parent states, previous dossiers
and prior executables remain byte-identical. The auxiliary v1 repair build and the
final v2 build are separately preserved and hash-bound. No reference selection or
new scientific acceptance was created.

GPU executions: zero. Additional MD steps: zero. New campaign seeds/attempts: zero.
The earlier retest remains failed-before-MD, and its twelve reservations remain
retired. A later GPU retest must use new immutable attempts/reservations and retain
cross-barrier parent pairing under its own explicit authorization. It must actually
exercise both the repaired initial device readback and the corrected candidate
oracle. A successful short diagnostic would establish execution under tested
conditions, not equilibrium invariance, slow-topology mixing or production readiness.

IMPLEMENTATION.md, REPRODUCTION.md, SOURCE_CHANGE.patch, PROBE.json, raw logs and
read-only verification scripts provide reproduction and provenance. Large raw CPU
fixtures/replay evidence and executables remain in ignored dataset locations,
authenticated by ARTIFACTS.sha256 under existing repository conventions.
