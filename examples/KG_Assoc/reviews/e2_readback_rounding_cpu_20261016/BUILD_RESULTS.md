# Authenticated CPU build and final validation

Final implementation/test-driver source commit: `f086be92f42ca49e3a394b6e522e0c2da27c40a1`.
New preserved out-of-tree directory: `examples/KG_Assoc/kg_assoc_100m/builds/readback_rounding_cpu_20261016_v2`.
Manifest SHA256: `c9ea28fa53e713460e00ad021285d1bd2843dd537245d38bd9efd97e09ce6be9`.
Forced build duration: 73.428 s; source bindings: 651.
NVCC 12.8 and GCC 11.2 compile commands, versions, full source map, executable
hashes and build-log hashes are recorded in that immutable manifest. All three
targets were rebuilt with the production `-O3` flags. No historical binary was replaced.

| Executable | SHA256 |
|---|---|
| `kg_assoc_candidates_test` | `5209be4ec14f549c8ccd9f2dc8bbfac20905077b26940372f668fd7167357111` |
| `kg_assoc_stars` | `c4317aaed224f3c49d1ef65a40b336e71cc5800e7c3f5fd2ff5a50ad9a6ebfc8` |
| `kg_assoc_stars_candidate_smoke` | `a44da467cb470a16e768a0a1633e689fa41570ff3e6ba6dfdedcbf1be1421ef4` |

Final results against this v2 build:

| Check | Result |
|---|---|
| Shared/readback regression suite | 149 passed, 16.419 s |
| Transfer suite | 14 passed, 86.169 s |
| Historical forensic suite | 5 passed |
| Native ordinary/candidate-smoke host self-tests | Both passed |
| Native candidate contract suite | Original regressions, both counterexamples and 398 cases passed |
| Native exact velocity-corruption cases | 12 rejected: all axes, both directions, one/two float32 ULPs |
| Host initialization probes | 12 passed; start step 8,000,000; no simulation files |
| Optimized full-parent helper/comparator replay | 43,563 particles / 130,689 exact components; passed |
| Ordinary preprocessed source | Identical with build timestamps held fixed |
| Preservation/exclusive acceptance validation | 2,145 unchanged bindings; 3 authenticated source transitions; 12 acceptances passed |

Final driver: 18 command groups, all return zero. The full-parent probe is an
independently compiled optimized host executable using the same unchanged repaired
helper; its source and compile flags are bound by PROBE.json and the final manifest.
It is not a new GPU readback or successful trajectory receipt.

The earlier v1 build at source `4287ff1a4e55f63cd6fdcad9dc8f52f36ab55691` remains
preserved. Its native tests, 149 shared tests and 14 transfer tests passed; the
driver then stopped on a forensic module import collision. The v2 source fixes
only that test environment and its audit build path. Both builds and all initial
logs are authenticated in ARTIFACTS.sha256; initial_cpu/ retains the import error.
No native repair or simulation source changed between v1 and v2.

Final receipts add only Markdown, raw logs and .sha256 maps after the clean source
build, so its native/Python/JSON source map remains current. The final Git SHA is
the containing receipt commit, reported after push. No GPU execution, MD, chemistry
sweeps or scientific convergence test was performed.
