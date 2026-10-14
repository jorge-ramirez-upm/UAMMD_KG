# CPU validation, reproduction and integrity

Local entry HEAD: `bb7d72acbcadfaef5a09333b27439de763597b93` (clean).
Remote HEAD: `979929480cb443aff23da332852fa2ed9c997e09`; fast-forwarded before
assessment. The difference was documentation only. No runtime source changed in
this task, so an affected UAMMD executable rebuild was not required.

## Results

- **72 existing CPU unit tests passed**, in 8.263 s: continuous 6M/4M review,
  satellite/degree replay, peripheral network, window sensitivity, joint E2,
  E2-G1 provenance/numerical validation, acceptance and COM/PBC regressions.
- **8 dossier CPU tests passed**, in 0.327 s: exact scope, immutable-output and
  plan guards, transient/context policy, unchanged IAT arithmetic, restoration
  of the scoped helper, full frame/degree/peripheral/window-mean identities, and
  double/triple/quadruple bonds plus intra loops without changing permanent star IDs.
- **2 C++ CPU correlator tests compiled and passed** with g++ C++14/O2:
  `kg_correlator6_counts_test.cpp` and `kg_assoc_correlator_checkpoint_test.cpp`,
  linked against the unchanged protected KG correlator. Binaries were placed
  in `/tmp/rp040_correlator_counts` and `/tmp/rp040_correlator_checkpoint`.
- Python byte compilation of the five dossier scripts and seven reused analysis
  modules passed. Whitespace/integrity checks passed with `cr-at-eol` enabled
  for the established CSV writer's CRLF line endings.
- Fresh full validation passed for all three 0–6M histories: numerical limits,
  accepted events, permanent topology, endpoint geometry, chemistry, MD seeds,
  graph replay, conformation output and all restart/sidecar/mirror payloads.
- **5040 shared scalar/vector statistic entries matched the authenticated 500k
  checkpoint exactly**: means, IAT, effective samples, slopes, SEMs, blocks and
  all three blocking uncertainties. New estimates include 34 intervals per
  history, with 500k/1M/2M windows, shifted comparisons and four final 250k windows.
  There are 350 shifted/early–late and 350 consecutive observable contrasts;
  these are exploratory correlated comparisons, never 700 new statistical units.
- Neighboring RP020 and corrected RP080 formal records and endpoint evidence
  passed the existing read-only `exclusive_validate` API. No `accept`, `publish`
  or `resolve` call, registry selection or production authorization occurred.
- All **814 pre-existing protected/evidence file bindings** in
  [PRESERVED_SHA256.json](PRESERVED_SHA256.json) remained unchanged. This includes
  eight existing formal acceptances, current attempt/checkpoint, E1 and accepted
  neighbor payloads, historical reviews, `src/`, `examples/KG/` and tracked frozen
  campaign files. The installed plan-bound binaries still match their manifests.
- Full-transient and late figures were generated from validated frames; the late
  shape/network paths were visually inspected. Matplotlib warned that optional
  Axes3D is unavailable; all requested 2D figures were produced. Existing tests
  emit sidecar-reader ResourceWarnings; the unchanged KG correlator emits
  unchecked-fscanf compiler warnings. None caused a test failure.

The final integrated suite ran all **80 Python CPU tests together in 8.387 s**,
with zero failures. Together with the two C++ tests, all 82 CPU checks passed.

## Statistical computation

The established window, graph, event, blocking and paired-history helpers are reused.
The original IAT implementation computes exactly the same `statistics.mean(values)`
for every centered sample, which makes long repeated reviews needlessly expensive.
The local reproduction script executes its **unchanged function bytecode** with a
scoped, exact per-call cache for that mean; it checks the input object identity,
does not change arithmetic order and restores the original helper after each window,
including exceptions. No source helper was edited. Deterministic regressions compare
results exactly with the original implementation, and all authenticated 500k
checkpoint statistics agree bit for bit. No original review or simulation file was
replaced.

## Reproduce into a new, nonexistent directory

```sh
PYTHONPATH=examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3.11 -m unittest test_e2_continuous_review test_e2_continuous4m_review \
  test_e2_satellite_continuation test_e2_peripheral_network \
  test_e2_window_sensitivity test_joint_e2 test_e2_g1 test_e2_acceptance \
  test_com_pbc_audit

PYTHONPATH=examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3.11 -m unittest test_reproduce

MPLCONFIGDIR=/tmp/rp040_mpl python3.11 \
  examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014/reproduce.py \
  --output /tmp/rp040_review_reproduction
python3.11 examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014/consecutive.py \
  /tmp/rp040_review_reproduction
MPLCONFIGDIR=/tmp/rp040_mpl python3.11 \
  examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014/plot_late.py \
  /tmp/rp040_review_reproduction
```

The optional full multigraph supplement is reproduced with:

```sh
python3.11 examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014/multiplicity.py \
  /tmp/rp040_review_reproduction
```

It reuses validated event parsing and graph replay, verifies L1 and loop accounting
at every frame and writes fresh distribution uncertainties and full-transient CSVs.
Zero rare-state counts are labeled as absence of mixing evidence.

The driver reauthenticates the fixed attempt and exact plan hash before calculating
statistics. Existing output paths are refused. Actual task execution authenticated
once, retaining the fresh in-memory replay temporarily in `/tmp`, then generated
statistics/figures from that same authenticated replay. No cached historic estimate
was substituted for a newly computed interval. Only immutable completed files were
read, and no simulation, recovery or GPU program was invoked.

Final source/evidence digests are in [INTEGRITY.json](INTEGRITY.json). The final Git
SHA is the commit containing this dossier and is reported in the task response,
avoiding a self-referential commit hash inside the immutable evidence.
