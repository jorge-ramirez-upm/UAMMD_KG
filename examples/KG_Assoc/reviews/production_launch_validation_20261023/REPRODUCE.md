# CPU reproduction and archive integrity

Read RUN_YOURSELF.md for user-only GPU instructions. Every command below is CPU-only
and bounded; no command executes the GPU driver action.

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/VERIFY.txt
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/TEST_ADAPTER.txt
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/TEST_SOURCE_BOUNDARIES.txt
timeout 600 env PYTHONPATH=examples/KG_Assoc/campaign:examples/KG_Assoc/analysis PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest -v test_campaign
out=$(mktemp -d /tmp/kg_production_launch_cpu.XXXXXXXX)
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_transfer_24m_joint_20261018/CPU_TEST_DRIVER.txt --output "$out/shared"
```

The17 adapter and4 boundary tests use synthetic temporary parents, journals,
authorities, outputs and mocked native processes. The stress parser test uses a
synthetic finite-grid file and the real P4 reader; it mocks the large endpoint
validator separately. Scheduling/counter trace tests use explicit synthetic records.
They establish deterministic administration/parsing, not GPU execution or physical
statistics. The100M fixture exercises the future authorization branch without
creating a real active registry or production approval.

HOST_FIDELITY.txt checks the real15 selected immutable parent files and host float32
representation with the established readback representation helper. Its output is
HOST_FIDELITY.log, explicitly marked initial_GPU_readback_executed=false. Reproduce
into a fresh output file, never overwrite a historical device-evidence file:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/HOST_FIDELITY.txt > "$out/host_representation.log"
```

The preserved native build was authenticated at the previous milestone by exact
optimized compile commands, historical manifest/logs, ancestry and258 native
repository dependencies. Current checks reuse that authentication. No rebuild is
required because no native dependency changed. Existing stress, correlator count,
online/offline and correlator serialization evidence remains under
`rheology_existing_method_20261023/`; those native tests were not needlessly repeated.

PREPARE.txt is the original one-time exclusive CPU publisher. It must not be rerun
against the existing identity. PUBLISH_SOURCE_V2.txt and PUBLISH_SOURCE_V3.txt record
exclusive administrative source evolution, preserving original immutable approvals,
plan, seeds and output directories. Earlier source records are preserved; only v3
is selected by the driver. These are reproducibility evidence, not reset/retry tools.
The full native source map remains unchanged from the frozen production preparation;
the runtime adapter/preparation/test Python text is separately hash-bound exactly.

ARCHIVE.txt copies the actual new record bytes without altering live metadata.
AUTHORIZATION_METADATA.tar.gz contains the full chain of plans, approvals, reservation,
authorities/source records, index publications and isolated run stubs. Extract only
into a fresh scratch tree; do not extract over live campaign paths. JSON bytes use
.log aliases for review archives; VALIDATION_HISTORIES.csv and IDENTITIES.log bind
all exact paths/SHA256s. Original large accepted simulation inputs remain at their
protected host locations; hashes do not reconstruct absent files in a data-free clone.

PRESERVED.sha256 checks5171 original bindings, including all15 acceptances and the
frozen94-file production-preparation binding set. INTEGRITY.sha256 seals the new
dossier excluding itself. VERIFY is intentionally a **pre-execution publication
audit**: it asserts15 output directories contain only run.json and all45 production
directories only their original planning metadata. After actual user execution,
use driver --status/--recover and retain this publication audit as historical
preflight evidence; do not rewrite it to make a later state look unexecuted.
