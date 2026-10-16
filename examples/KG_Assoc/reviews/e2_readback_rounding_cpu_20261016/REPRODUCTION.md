# CPU-only reproduction

Run from repository root. Pick fresh output directories; evidence is not overwritten.

```bash
python3 examples/KG_Assoc/reviews/e2_readback_rounding_cpu_20261016/reproduce.py \
  --output /tmp/readback_rounding_fresh_probe
python3 examples/KG_Assoc/reviews/e2_readback_rounding_cpu_20261016/check_ordinary_source.py
python3 examples/KG_Assoc/reviews/e2_readback_rounding_cpu_20261016/verify_preservation.py
```

The first command authenticates original parent/output hashes, emits an independent
Python float32 fixture, compiles a native host-only probe with the campaign NVCC/GCC
`-O3` flags, reproduces the old defect and verifies the repaired helper plus the
unchanged exact readback comparator. It never invokes the historical GPU executable.
PROBE.json retains commands, source/input/executable/output identities; large raw
replay evidence stays under the ignored dataset aggregate directory, following
existing review conventions. An earlier development probe used a placeholder box
with identical expected/actual positions; the final authenticated_box_probe uses
the exact saved box. Only the latter binds the final full-parent result.

After committing source, build with the existing forced-build workflow, choosing
an unused directory directly below dataset builds:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_e2.py build \
  --dataset-root examples/KG_Assoc/kg_assoc_100m \
  --output examples/KG_Assoc/kg_assoc_100m/builds/UNUSED_BUILD_NAME --out-of-tree
python3 examples/KG_Assoc/reviews/e2_readback_rounding_cpu_20261016/run_cpu_tests.py \
  --build examples/KG_Assoc/kg_assoc_100m/builds/UNUSED_BUILD_NAME \
  --output /tmp/readback_rounding_fresh_tests
```

The driver runs host candidate tests, both host self-tests, the historical shared
regression suite, transfer suite, five forensic tests, and twelve host-only
initialization probes using immutable old plan arguments with fresh temporary
output prefixes. These probes allocate no streams, write no simulation outputs
and do not initialize CUDA. The old plan/seed identities are test inputs only;
retired reservations remain retired.

Final read-only authentication with the actual milestone build/artifacts present:

```bash
python3 examples/KG_Assoc/reviews/e2_readback_rounding_cpu_20261016/verify_dossier.py
```

The baseline captures 2,148 authenticated existing files. Three intended source
transitions are authenticated against the starting Git blobs; every other binding
must remain identical. This includes both failed campaigns, their plans/seeds,
previous dossiers, all historical build bytes, twelve formal acceptance records
and protected output payloads. All twelve acceptances are also freshly validated
by the existing exclusive validator. Historical manifests continue to describe
their original source versions; their live source differences are not retroactively
rewritten. INTEGRITY.sha256 binds this dossier except itself; ARTIFACTS.sha256
binds the new build and raw CPU evidence. The containing Git commit binds the
integrity map. No stochastic convergence test or GPU result is inferred here.
