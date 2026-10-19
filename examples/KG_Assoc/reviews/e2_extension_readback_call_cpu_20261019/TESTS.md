# CPU evidence and reproduction

All jobs were bounded by timeout 600. No GPU simulation was launched.

| Check | Result | File |
|---|---|---|
| Shared established regression modules | 189 passed | SHARED_REGRESSION_TESTS.log |
| Transfer/native host initialization | 14 passed | TRANSFER_TESTS.log |
| Call-path, hold, extension/lifecycle and all six real preparations | 41 passed, no skips | FINAL_FOCUSED_TESTS.log |
| Formal Ea6 registration and prior acceptances | 6 passed | FORMAL_ACCEPTANCE_TESTS.log |
| Actual held native-PASS missing evidence | Correct rejection even with oracle=False | ACTUAL_MISSING_READBACK_REJECTION.log |
| Native host invariants and candidate/cutoff/readback-corruption cases | Passed; 398 cutoff cases, 12 velocity ULP rejections | NATIVE_HOST_TESTS.log |
| Ordinary executable rejects diagnostic host probe | Passed before CUDA construction | ORDINARY_PROBE_REJECTION.log |
| Read-only check/status and approval boundary | Passed; MD loop mocked unreachable | READ_ONLY_AND_GPU_GATE.log |
| Historical and new preparation integrity | Passed | PRESERVATION.log |

Total unittest cases: 250 passed. The missing-evidence integration driver is an
additional CPU check, not a simulated device result. The positive receipt-recovery
fixture creates synthetic evidence only inside temporary CPU fixture directories;
no real readback file, output or acceptance was fabricated.

The exact production C++ call block is extracted into a minimal CPU harness with
a spy named initialDeviceReadback. NVCC 12.8/GCC 11.2 compile it with -O3. All four
reseed/extension combinations run with successful and throwing spies. Extension
and reseeded modes must call exactly once; a thrown/missing-evidence callback must
prevent the following integration sentinel. Ordinary mode calls zero times.
A mutation disabling extension dispatch compiles and must fail the same harness.
The actual diagnostic binary's --readback-call-path-info probe separately runs
its shared dispatcher. Its marker explicitly says CPU_ONLY.

Static checks tie this dispatcher to the real GPU function before forwardTime,
and verify the unchanged readback body and physical tail except this dispatch.
These tests establish CPU control flow, not actual GPU transfers. Only later
user-run native execution can supply actual device-readback evidence.

Prebuild logs retain the initial source-map refusal while the new dispatcher was
untracked, followed by passing tests after registration in Git's tracked source
inventory. Prebuild missing-build/preparation skips were expected. The final
optimized-build/prepared-parent suite exercised every case without skips.

Reproduce from a clean repository on titan's authenticated dataset:

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 env PYTHONPATH=examples/KG_Assoc/campaign \
  PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest -v \
  test_e2_readback_call_path test_e2_extension_readback_hold test_e2_extensions
timeout 600 env PYTHONPATH=examples/KG_Assoc/campaign \
  KG_ASSOC_TRANSFER_HOST_EXE="$PWD/examples/KG_Assoc/kg_assoc_100m/builds/ea_24m_extensions_readback_20261019_v2/kg_assoc_stars" \
  python3 -m unittest -v test_e2_transfer
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea6_formal_acceptance_20261018/TEST_REGISTRATION.txt
timeout 600 python3 examples/KG_Assoc/reviews/e2_extension_readback_call_cpu_20261019/REJECT_MISSING.txt
timeout 600 python3 examples/KG_Assoc/reviews/e2_extension_readback_call_cpu_20261019/VERIFY.txt
```

Shared module names are recorded in SHARED_REGRESSION_TESTS.log; the previous
handoff's TEST_COMMANDS.txt gives the same unchanged shared CPU invocation.
Native self-test/probe commands appear in BUILD_RESULTS.md and NATIVE_HOST_TESTS.log.
GPU execution commands in older handoffs do not authorize this new cohort.

VERIFY.txt checks the initial prepared handoff, including empty outputs and false
GPU approvals. It is intentionally a pre-execution snapshot audit. Once future
execution is separately authorized, use the runner's read-only status/check for
live monitoring; do not expect the durable live state to retain its initial hash.
The immutable initial metadata is archived in PREPARATION_EVIDENCE.tar.gz.
