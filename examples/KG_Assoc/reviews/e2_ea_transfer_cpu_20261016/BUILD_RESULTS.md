# Authenticated post-commit CPU build receipt

The clean implementation commit is `523f49be292d32c48ad216103b126341ba337159`.
Its official out-of-tree build passed authentication; all three E2 targets were
forcibly compiled with no GPU execution. Existing binaries were not replaced.

* Build directory: `examples/KG_Assoc/kg_assoc_100m/builds/ea_reference_transfer_cpu_20261016_v1`.
* Manifest SHA256: `6d04459efe40df2698e5f40a6ad67d922fe31b5fc49ba16e9450f2290ced5446`.
* Source bindings: 591; exact compiler commands: 3.
* Build time: 71.82 s; compiler/toolchain versions are in the manifest.
* Both native host-only self-tests passed.
* Transfer regressions against this authenticated executable: **13 passed, 79.873 s**.
* Read-only CLI inspection with `--build-evidence` passed and selected the new
  candidate executable; its prospective attempt does not exist.

| Executable | SHA256 |
|---|---|
| `kg_assoc_candidates_test` | `275d03f2706842082fa5419fcf063621ad647c31216cbfbe84d850b6abf41182` |
| `kg_assoc_stars` | `fcf7fc296e4cfa16f8178b174287a2c4ec7dac2bf8d9c8cad975bf72412b5a1a` |
| `kg_assoc_stars_candidate_smoke` | `bc67902ecbf9ee61ba5d3955f63648c284a648d5406c474a0d18209ab09eb578` |

| Build evidence | SHA256 |
|---|---|
| `stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `stderr.log` | `d881965a177eff60c4c28d0a540521ab014679bf9ff4528fdd871bfda973cf08` |
| `host_self_tests.log` | `d57c4ad5b29e21b8a78c593aa61a309b05ca938970115ef335b78bf564a1ea3d` |
| `transfer_tests.log` | `75003d9a017ffd33aa34534d6a9215b9b337e9814cf79027eaf66f502971efc0` |
| `inspection_ea06.json` | `311492dc08b518ea6d3447e092e430eb3344e66d1901ef0df9624fe41f18e1a2` |

The build manifest and logs remain in the ignored, immutable build directory.
Reproduce the CPU build from a clean committed tree using a **new** output directory:

```bash
python3 examples/KG_Assoc/campaign/kg_assoc_e2.py build \
  --dataset-root examples/KG_Assoc/kg_assoc_100m \
  --output examples/KG_Assoc/kg_assoc_100m/builds/NEW_UNIQUE_CPU_BUILD \
  --out-of-tree
```

Repeat the transfer command in VALIDATION.md with `KG_ASSOC_TRANSFER_HOST_EXE`
set to the resulting `kg_assoc_stars` path. This repeated run emitted inherited
`ResourceWarning` messages from historical file readers; all assertions passed.
Those historical readers were left unchanged.

Final preservation and dossier SHA256 checks passed: twelve acceptance records
unchanged; 1,327 protected live bindings unchanged; seven authorized source
transitions authenticated against the starting Git commit. Historical source
manifests and prior scientific dossiers are unchanged.

This Markdown receipt is intentionally added after the build. It is bound by
its containing Git commit; it does not change the source files captured by the
build or the earlier INTEGRITY.json bindings.

**Ready for a separately authorized capped GPU smoke.** Device restoration and
dynamical behavior remain untested. No real derived attempt, GPU calculation,
new acceptance, registry action or production preparation occurred.
