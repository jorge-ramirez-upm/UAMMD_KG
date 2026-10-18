# Authenticated native build

Build source commit: `79fbba03348b575faa2da988f9eaedf51772579c`.
Build started after that commit with a clean tree; completed in 73.378 seconds under timeout 600.
The new directory is `examples/KG_Assoc/kg_assoc_100m/builds/ea_24m_extensions_20261018_v1`.
No historical executable or build manifest was replaced. Compilation and subsequent tests were CPU-only.

NVCC 12.8.93, GCC 11.2.0, C++14, `-O3`; candidate diagnostic build retains `-DKG_ASSOC_VALIDATE_CANDIDATES`.
The only compiler messages were the existing CUDA deprecated-target warning, once per target.

| Executable | SHA256 |
|---|---|
| `kg_assoc_candidates_test` | `05b5c35e19acc679d8a9c6fa96d4522c8efeee100dfb8670c39d7958f51e675f` |
| `kg_assoc_stars` | `d1bce000740cbb77cc1eb7b24c6fa61371cf15dbb840f67bf6cb2a15cbd0c00a` |
| `kg_assoc_stars_candidate_smoke` | `88e8225f9dd4f221ff861f135e68cec927b4a3228d166429ae804a39129b636b` |

The complete manifest, compiler commands, source hashes and logs are archived in
`PREPARATION_EVIDENCE.tar.gz`; `PREPARED.log` also embeds the manifest. Both plans bind
the manifest, all executables, build logs, authorization evidence and exact source map.
Documentation-only descendant commits may reuse this build only with identical complete
source maps and verified ancestral Git history.

`NATIVE_HOST_TESTS.log` records two invariant/MD-stream self-tests and the host-only
candidate test executable: 398 cutoff cases and 12 deliberate float32 velocity ULP
rejections, alongside position/identity/type/partner and corruption checks.
Six real parent initializations and six native rejection cases also passed in the
27-test extension suite. These host-only operations return before device initialization.

No new GPU readback, MD integration or oracle execution was performed. Historical
GPU evidence is authenticated through the same-Ea exact 24M parents. The new front-end
is tested on the device only when the user executes the extensions; failures stop execution.
