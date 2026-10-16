# Authenticated CPU build and final regression receipt

Implementation commit: `74933f7c4e12f8812e44707c89662af1aec273f7`.
New out-of-tree build: `examples/KG_Assoc/kg_assoc_100m/builds/ea_cutoff_contract_cpu_20261016_v1`.
Manifest SHA256: `3739b7611ecd5b4e78d0739f882677a8c163eb107526515fcce7cff74fbc890a`.
Forced compile time: 73.336 s; source bindings: 620.
The compiler versions, exact three compiler commands, sources, logs and executable
hashes are retained in this immutable build manifest. No historical binary was overwritten.

| Executable | SHA256 |
|---|---|
| `kg_assoc_candidates_test` | `c58bdb3573d97e6b34b219dc2503e192995e6b9662facd2115d3541d36768d85` |
| `kg_assoc_stars` | `f0b1494fc25859485c94466866dde5bf6683d1c6dc63efa290b888f8799108ac` |
| `kg_assoc_stars_candidate_smoke` | `45a8f85e8a421a6730e8ba96f543635bbad0a7c56bf23bfd8d7e865604e7089c` |

Final authenticated-build results:

* Both native `--self-test` calls passed (host-only).
* The rebuilt candidate test passed its original regressions, both precision
  counterexamples, 398 single-precision boundary/differential cases and injected
  mismatch/readback tests. The separate double host build also passed.
* Twelve read-only `--validate-initial-state` probes passed using the new candidate
  executable and old authenticated plan inputs, with new temporary output prefixes.
  No files were generated and the GPU context/readback path was never entered.
* Ran 14 tests in 83.746s; OK (Ea-transfer suite).
* Ran 149 tests in 16.018s; OK (shared/readback suite).

| Final CPU evidence | SHA256 |
|---|---|
| `stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `stderr.log` | `d881965a177eff60c4c28d0a540521ab014679bf9ff4528fdd871bfda973cf08` |
| `native_host_tests.log` | `7a64705268cfde5a1036dd1fbf0291f975ce36de5a48138845347c34fbbfa424` |
| `host_preflight_checks.log` | `d7260f9fdbdca264cbc6bd77a88651620d9f279e44df1f0b85f865b90cd66845` |
| `transfer_tests.log` | `f8a15ca341457c8446ef44de2a163c6522276f6c1ac7c7974580f5dfb9804c79` |
| `regression_tests.log` | `585ad3d8501675de989bdc6abf3204988d29fe802d7836d34977ea2608003472` |

Final preservation and scoped dossier hash checks passed: 1,733 unchanged
protected live bindings and six source transitions authenticated at the starting
Git commit. All twelve acceptance records/payloads and all failed-smoke output
bindings remain unchanged. Frozen production search/physics/source bytes remain
unchanged. No GPU calculation, real preparation, retest, kinetic screen, acceptance,
registry action or production preparation occurred.

This Markdown receipt is added after the build, preserving its captured JSON/
Python/native source map. It is bound by its containing Git commit and deliberately
excluded from the preceding INTEGRITY.json. The build remains an ancestor-source
authenticated build after this documentation-only commit.

**Ready for a separately authorized capped GPU diagnostic retest.** The original
failed GPU pair is unknown; the new actual device readback and failure-capture
path have not been exercised on a GPU. CPU success does not relabel the earlier
smoke as passed or establish initialization/equilibrium suitability.
