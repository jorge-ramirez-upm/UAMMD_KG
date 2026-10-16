# Validation-only expected-velocity rounding repair

Starting local/remote `KremerGrest` SHA:
`b8f518d49c9b00f7d957bc42fcaf0a34a9317c82`, clean tree, 2026-10-16.
Authority: the user-authorized CPU repair and the preceding
[failed retest assessment](../e2_ea_transfer_gpu_diagnostic_retest_20261016/ASSESSMENT.md).
No CUDA execution, MD, new seeds, attempts, acceptances or registry actions are part
of this milestone. The failed retest remains failed.

`kg_assoc_stars.cu` now calls validation-only `representedVelocity` when constructing
expected readback evidence. This helper stores all three serialized doubles in a
volatile `uammd::real` array before widening them into `std::array<double,3>`.
The volatile stores/reads require the represented precision to materialize under
the optimized campaign compiler. It uses the configured real precision, which is
float32 for this campaign. No global compiler flags or floating-point environment
are changed. Exact comparison in `writeInitialReadback` is unchanged.

The helper is included through the existing candidate-validation header, and the
caller remains inside `KG_ASSOC_VALIDATE_CANDIDATES`. There is no physical loading
path change. SOURCE_CHANGE.patch records the three existing-file edits: the caller,
validation helper and native validation tests. Makefile dependencies already include
the changed header for both validation targets; the forced out-of-tree build
rebuilds all three E2 executables, including ordinary stars.

The historical host probe reproduces the defect with NVCC 12.8/GCC 11.2 at `-O3`
and exact serialized parent values 0.270623, 0.266728, 0.876108. The new full-parent
probe uses the production candidate-smoke compile flags and the actual helper.
Python independently converts each authenticated parent value with struct.pack/
unpack('f'). The native probe checks all 43,563 particles/all 130,689 components
against those values and the saved actual device readback, then runs the unchanged
readback writer/comparator on the corrected host records. Python independently
checks every emitted expected and actual velocity again. There are zero corrected
or actual mismatches. The historical expression reproduces wrong counts
43,559 / 43,556 / 0 in x/y/z. This is host reanalysis of saved GPU evidence, not
execution of a new device readback and not a replacement successful smoke receipt.

Native evidence tests use the same helper and unchanged comparator, accepting
matching represented values and rejecting actual velocities shifted one and two
real ULPs in both directions on every axis (12 negative cases). Existing identity,
position, partner, nonfinite and mapping rejection tests remain.

ORDINARY_SOURCE.json records exact equality of normalized ordinary-star preprocessor
output at the starting commit and repaired source. Only preprocessing line markers
and whitespace are normalized; __DATE__/__TIME__ are fixed identically for this
comparison alone. The first comparison exposed the expected one-second compile
stamp difference, so timestamp macros were fixed for the comparison. Production
builds retain their true timestamps. This establishes no ordinary compiled-source
change beyond build metadata; no ordinary trajectory was run or claimed compared.
Forces, chemistry, candidate search, integrator and stream implementations remain
byte-identical in the preservation inventory. No physics/kinetics model was changed,
so no new LAMMPS semantic interpretation is needed.

The build workflow requires committed, clean source. The implementation and
reproducers are committed before the authenticated forced build. The subsequent
receipt commit adds Markdown/log/hash evidence only, preserving the build's exact
JSON/Python/native source map. BUILD_RESULTS.md and ASSESSMENT.md record the actual
build, tests, preservation and readiness outcome.

The first built test driver passed 149 shared and 14 transfer tests but selected
an older sibling module for the five forensic tests because multiple historical
reviews use the name reproduce.py. Its import error and stop are preserved. The
driver now places the forensic review first only for that command, retaining the
original shared-suite environment. A second source commit and new v2 build bind
this driver correction; the first v1 build remains preserved. No native repair
source changed between these two builds.
