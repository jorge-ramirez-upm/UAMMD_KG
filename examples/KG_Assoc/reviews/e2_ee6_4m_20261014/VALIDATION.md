# CPU validation and reproduction

Starting local and remote KremerGrest HEAD: `1d1c0bfae9ce684d659c79876249db7c0fbe2e12`.
The final commit is the Git commit containing this immutable dossier (the final
SHA is reported in the task response; no self-referential commit hash is embedded).

## Checks performed

- 57 CPU regressions passed in 8.031 s across `test_e2_continuous4m_review`,
  `test_e2_continuous_review`, `test_e2_satellite_continuation`,
  `test_e2_peripheral_network`, `test_e2_window_sensitivity`, `test_joint_e2`,
  `test_e2_g1`, and `test_e2_acceptance`.
- Python byte compilation of the new driver and test passed.
- `kg_correlator6_counts_test.cpp` and `kg_assoc_correlator_checkpoint_test.cpp`
  compiled with g++ C++14, linked to the existing KG correlator, and passed on CPU.
  Binaries were written to `/tmp`, leaving the validated KG source untouched.
- `kg_assoc_stars.cu` compiled successfully to `/tmp/ee6_kg_assoc_stars_compile_check`
  using nvcc 12.8, GCC 11.2, C++14, extended lambdas, `MAXLOGLEVEL=5`, `-O3` and zlib.
  This was a compilation check only; the executable was not run and did not replace
  the plan-bound executable. No `.cu` or `.cuh` file changed, so no affected runtime
  executable needed rebuilding.
- Existing tests emit ResourceWarning messages from an existing unclosed sidecar
  reader. The C++ correlator emits existing unchecked `fscanf` warnings; nvcc warns
  about future removal of older architecture support. None caused a test failure.
- Full fresh validation covered 4001 frames per replica, absolute chemistry cadence,
  accepted event replay, stable particle identities, reciprocal valence-one partners,
  permanent topology and geometry, active FENE limits, final snapshot/sidecar/mirror
  consistency, conformation endpoint reconstruction and effective MD stream logs.
  The ordinary 4M histories do not have per-sweep candidate-oracle coverage.
- Remote LAMMPS scientific reference HEAD matches the local
  `feature/associating-stickers` checkout at
  `1c6faf70e94aef2389c208e8c80c60c084a96907`. The actual fix/pair implementation was
  inspected: both make/break candidates are distance gated; attempt probability is
  `-expm1(-nu0*exp(-Ea/T)*Nevery*dt)`; active mechanics add shifted FENE through R0.
  No new dimer, K1, GPU, E2 extension or production simulation was performed.

## Reproduce in a new, nonexistent output directory

```sh
PYTHONPATH=examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python -m unittest test_e2_continuous4m_review test_e2_continuous_review \
  test_e2_satellite_continuation test_e2_peripheral_network \
  test_e2_window_sensitivity test_joint_e2 test_e2_g1 test_e2_acceptance

MPLCONFIGDIR=/tmp/ee6_mpl \
python examples/KG_Assoc/analysis/analyze_e2_continuous4m_review.py \
  --dataset-root examples/KG_Assoc/kg_assoc_100m \
  --attempt examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE06/equilibrate_c6051f0ca57140819c10ae01e63036b5 \
  --plan-sha256 20eb13c5047cfce5a26646adb95839b4b575d232943b2b4bf7c37c49b0e623c6 \
  --output /tmp/ee6_review_reproduction
```

The driver reuses the existing authentication, validated compact graph capture,
interval estimates and paired-history helpers. It refuses an existing output,
wrong plan hash, wrong endpoint step, missing frame or wrong replica coverage.
Every interval is recalculated from its frames and events; no error or IAT is
stitched or averaged. Figure lines retain step zero and all initial transients;
the 500k means exclude each left boundary and include its right boundary.
Only histories r001, r002 and r003 are independent statistical units. Window
comparisons and blocks do not create new replicas. Three-history Student-t df=2
intervals are exploratory, unadjusted and not a stationarity/equivalence test.
Overlapping comparisons are correlated. IAT uses the existing first nonpositive
lag heuristic and assumes local stationarity; effective samples and block SEMs
are estimates, not guarantees of equilibration.

Supplemental final-quarter sensitivity and late zoom are reproduced in the new
output directory by copying the dossier's `terminal_halves.py` and `plot_late.py`
there and running them. Both refuse to replace their existing output. The terminal
script checked complete frame cadence, degree normalization/moments, and late
peripheral identities at every frame before calculating new interval estimates.
Python compilation of both supplemental scripts passed. Full-transient and late
shape/peripheral figures were visually inspected.

The pre-existing-evidence integrity snapshot covers 176 files, including all seven
formal acceptance records, original Ee6 attempt outputs, and existing review files.
All digests remained unchanged. Frozen Ee4 and corrected Ee8 accepted payloads and
evidence bindings also matched. Fresh 500k means were cross-checked against the
workflow checkpoint, and reconstructed exported graph means/moments against the
new interval estimates. Endpoint hashes match completion receipts and current bytes.
`git diff --check` with `cr-at-eol` (the standard CSV writer emits CRLF) passed; the staged paths are limited to the two new source/test
files and this new review directory. No original scientific or registry state,
`src/`, or `examples/KG/` was modified.
