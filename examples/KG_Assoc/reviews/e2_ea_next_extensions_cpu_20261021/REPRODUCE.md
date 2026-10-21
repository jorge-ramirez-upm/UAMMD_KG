# CPU-only reproduction and immutable evidence

Run from `/home/jramirez/UAMMD_KG` on a host retaining the immutable dataset and historical Git
objects. Read-only `--check` and `--status` require the clean committed source tree and preserve
all existing state. No command here launches GPU integration. Each uncertain CPU computation has
a 600-second timeout, and jobs are independent rather than segments of a long simulation.

```bash
timeout 600 python3 examples/KG_Assoc/campaign/run_ea_next_extensions.py --check
timeout 600 python3 examples/KG_Assoc/campaign/run_ea_next_extensions.py --status
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_next_extensions_cpu_20261021/VERIFY_DRIVER.txt
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/e2_ea_next_extensions_cpu_20261021/PREPARED_TESTS.txt
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_next_extensions_cpu_20261021/LIFECYCLE_TESTS.txt
```

The focused tests, from `examples/KG_Assoc/campaign`, are:

```bash
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest -v test_e2_next_extensions test_e2_extensions test_e2_readback test_e2_derived_preparation
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning KG_ASSOC_TRANSFER_HOST_EXE=/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/builds/ea_extensions_48m_88m_20261021_v1/kg_assoc_stars python3 -m unittest -v test_e2_transfer
```

Representative full parent replays, each as its own bounded CPU job from the repository root:

```bash
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/e2_ea_next_extensions_cpu_20261021/REPLAY_PARENT.txt --Ea 8
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/e2_ea_next_extensions_cpu_20261021/REPLAY_PARENT.txt --Ea 10
```

They use the ordinary independent validator and original parent files. They do not generate a
substitute initial-device result or change a receipt. All six reviewed parents are authenticated
by exact prior review, state, plan, approval, reservation, receipt and output bindings; these two
replays additionally exercise recovered and ordinary history through the new historical reader.

The established 189-test E2 suite was reproduced with the existing bounded CPU_TEST_DRIVER.txt
from `e2_ea_transfer_24m_joint_20261018`, writing to the new ignored
`aggregate/e2/ea_next_extensions_cpu_20261021_v1/regression` directory. Its exact output is included.

The forced optimized build was performed once with:

```text
timeout 600 python3 examples/KG_Assoc/campaign/kg_assoc_e2.py build --dataset-root examples/KG_Assoc/kg_assoc_100m --output examples/KG_Assoc/kg_assoc_100m/builds/ea_extensions_48m_88m_20261021_v1 --out-of-tree
```

That build and preparation already exist. Do not run the build command into that directory again;
read-only checks authenticate its manifest, all three binaries and build logs. A deliberate rebuild
requires a new uniquely named build and corresponding new plan bindings; no historical executable
may be replaced. `--prepare` on the existing campaign performs idempotent authentication rather
than reallocating streams or overwriting plans. All six real output directories remain empty.

PLAN and metadata copies are packaged in PREPARATION.tar.gz. STATE.log is a byte copy of the
immutable state, BUILD.log of the exact manifest, and PLANS.log contains the two new complete plans.
PREPARATION_BINDINGS.sha256 binds 689 live source/build/preparation files; PRESERVED.sha256 binds
3,626 historical files from the before/after snapshot. INTEGRITY.sha256 binds the new dossier.
PACK_DRIVER.txt records packaging into an unused dossier output; it is not a launch mechanism.

The CPU readback dispatcher probe and host initialization are explicitly CPU evidence. Actual
device readback and candidate comparisons for the newly prepared segments remain pending separate
GPU authorization. Synthetic native-process fixtures in tests are temporary-only; `RUN`/completion
messages from mocked tests are not simulation outcomes. No synthetic evidence exists in real attempts.
