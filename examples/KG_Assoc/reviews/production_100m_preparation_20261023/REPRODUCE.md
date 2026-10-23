# Reproducibility and evidence layout

From repository root, run read-only `VERIFY.txt`, `PREPARE.txt check` and
`PREPARE.txt status` as in RUN_YOURSELF.md. VERIFY checks the sealed plan, all94
preparation bindings, current sources/build,5039 protected bindings, fifteen formal
acceptances and absence of any native output/execution authority. Its preparation-
only assertion is intentionally specific to this publication, rather than a future
post-execution audit. Each command is bounded by `timeout600` in the handoff.

Focused CPU tests (fixtures only in temporary directories):

```bash
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/production_100m_preparation_20261023/TEST_PREPARATION.txt
timeout 600 env PYTHONPATH=examples/KG_Assoc/campaign:examples/KG_Assoc/analysis PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest -v test_campaign
```

The shared suite was run with the established driver, preserving189 results in
E2_REGRESSION.log. To reproduce without overwriting evidence:

```bash
out=$(mktemp -d /tmp/kg_production_cpu.XXXXXXXX)
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_transfer_24m_joint_20261018/CPU_TEST_DRIVER.txt --output "$out/shared"
```

Existing correlator and P4 tests/results were reused; see the preceding
`rheology_existing_method_20261023/REPRODUCE.md` and its authenticated manifests.
Do not claim new online/offline correlation or GPU tests from these administrative
unit tests. No100M samples were generated to test lag arithmetic.

`AUTHENTICATE_BUILD.txt` records the original one-time NVCC dependency-only
preprocessing, historical blob comparison and exclusive binary preservation. Do
not rerun it against its existing immutable copy directory. `PREPARE.txt prepare`
also deliberately rejects reuse. The first preparation was done with clean committed
sources; HOST_PREFLIGHT.log records its45 native metadata-only checks. Current
`build_check` rechecks all258 dependency hashes, binaries, logs and Git ancestry
without compiling or initializing CUDA.

`ARCHIVE.txt` is the one-time capture program; it refuses existing archive/table
names. It changes no live campaign metadata. To inspect PREPARED_METADATA.tar.gz,
extract only into a new scratch directory and compare its members against the
embedded prepared.json SHA map; absolute paths refer to the authenticated host
workspace, not a portable substitute parent bank. Exact accepted restart/sidecar
files remain in their original protected locations. No simulation data can be
reconstructed from a hash if those original inputs are absent.

PRESERVED.sha256 is a JSON path→SHA256 map, matching earlier review conventions.
It combines the prior protected inventory, starting tracked files, all fifteen
formal records and historical executables. The one intentional administrative
source edit is audited separately by E2_BEFORE.txt, ADMINISTRATIVE.patch and
SOURCE_AUTHORIZATION.log. INTEGRITY.sha256 seals this dossier, excluding itself.
PLAN.log and its live plan copy bind the workflow/test source files explicitly;
changing either requires a new authenticated administrative authorization, not an
in-place plan edit. Later activation support must publish immutable source evolution
bindings if tracked administrative sources change, using one map both pre-/post-run.
