# Validation evidence and fail-stop behavior

Only the `KG_ASSOC_VALIDATE_CANDIDATES` executable executes the new device
readback and mismatch instrumentation. Normal production candidate search,
mechanics and stochastic updates remain unchanged.

## Candidate mismatch

`checkSweep` computes the independent oracle, then compares ordered unique pair
sets and exact distances. On mismatch it writes `<prefix>.candidate_mismatch.tsv`
**before rethrowing**, before that sweep's `kinetics.update`. It never repairs a
set, skips an edge, changes a tolerance or continues MD after a mismatch.

The evidence contains:

* Full derived branch, system and replica, absolute MD step and branch-local
  chemistry sweep, box lengths, strict cutoff, real byte width and rounding mode.
* Executable path, compiler/date information, sibling build-manifest path and a
  complete embedded copy of that manifest, including Git/source/executable hashes.
  The established planner/launcher authenticates those hashes; the native writer
  records them and does not replace that cryptographic authorization gate.
* Every sticker's represented x/y/z and current partner, using stable IDs; full
  actual and oracle pair/distance lists, their set sizes and differing identities.
* Missing, extra and distance-only discrepancies, association and both-free flags,
  raw real-first/double-first displacements, image multiples, reduced displacements,
  both distances, and signed distances/squared distances from the strict cutoff.

Coordinates and box data allow additional image conventions, including the former
oracle's remainder reduction, to be reconstructed in CPU analysis. Full coordinate
capture avoids reliance on a later endpoint that may never be written.

Evidence uses O_EXCL creation, complete writes, fsync and read-only file mode.
Existing diagnostics are checked before GPU construction and cannot be overwritten,
including under --force. Failure to write evidence also aborts. Passing candidate
comparisons write no mismatch file. CPU tests inject missing free, extra associated
and distance-only errors and check fail-stop, contents and overwrite refusal.

## Initial device readback

For a derived transfer in the candidate-validation executable, after GPU/system,
partners and GJ are constructed but **before the first MD step**, explicit
cudaMemcpyDeviceToHost copies read coordinates, velocities, IDs and the complete
chemical partner array. This is not a read from a potentially valid host cache.
The copied device IDs define the index-to-stable-ID mapping, including sort order;
invalid or duplicate mappings fail. Expected positions use the unchanged loader's
center/fold and real precision; velocities use its unchanged real conversion.

`<prefix>.initial_device_validation.tsv` records expected and copied values for
all particles, types, stable IDs, host molecule identity and chemical partners,
plus the context/build manifest. Molecule IDs are explicitly host topology
metadata, not an invented GPU particle property. Coordinates must match modulo
PBC with zero residual; velocities, IDs, types and partners must match exactly.
The file records pass/fail, particle count and maximum coordinate/velocity errors.
Any failure writes the evidence and throws before stepping. No creation/break
counter is reset and no chemistry event is synthesized.

The E2 validator recognizes the new declaration/version and requires the receipt
for derived oracle builds containing the new evidence header. It checks build
identity, all rows, parent loader representation, original velocities, partners,
finite values and exact readback consistency. New state/event declarations must
agree. Older manifests/records keep their historical validation path; no prior
record or receipt is rewritten. Completion receipts already hash all new output
files, including readback evidence.

There are no RNG calls in these diagnostics. Accesses/copies/synchronization and
file I/O add validation overhead but do not write GPU particle/partner state,
resample velocities, change counter offsets or alter candidate sets. GJ remains
an independently reseeded, non-bitwise continuation. CPU fixtures exercise the
comparison and serialization; **the new device path has not been executed**.
It requires a separately authorized capped diagnostic retest.
