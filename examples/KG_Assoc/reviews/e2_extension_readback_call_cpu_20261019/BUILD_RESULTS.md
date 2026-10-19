# Fresh optimized native build

Source commit: `055a1a1de43a04edebaad76364726d53cfe654f5`.
Directory: `examples/KG_Assoc/kg_assoc_100m/builds/ea_24m_extensions_readback_20261019_v2`.
Forced out-of-tree compilation under timeout 600 took 75.097 seconds.
NVCC 12.8.93, GCC 11.2.0, C++14, -O3; candidate executable includes
KG_ASSOC_VALIDATE_CANDIDATES. Historical build files were not replaced.
The only compiler messages were three CUDA deprecated-target warnings.

| Executable | SHA256 |
|---|---|
| `kg_assoc_candidates_test` | `3ecdda955dcf1ab138d92c7576ca2f1810c391af484ae32888eb4657bf1a8144` |
| `kg_assoc_stars` | `66f6c8122728b87f5c2a04503fc24046723495a5165d157c102662f2440498ec` |
| `kg_assoc_stars_candidate_smoke` | `cab431ac0d110bd635390ffe37fae2527df02642666cc4f8105997b21f780306` |

PREPARATION_EVIDENCE.tar.gz archives 14 initial metadata files: new durable state,
two plans, six CPU-preparation approvals, two MD-only reservations and the complete
build manifest/stdout/stderr. PREPARED.log embeds the manifest and all six entries.
PREPARED_METADATA.sha256 binds the initial snapshot; live state may evolve only
after separately authorized user execution. No executable binary is stored in Git;
the managed dataset on titan contains the authenticated native build and parents.

The positive gate authenticates exact native and dispatch-header source hashes,
checks executable digests, and runs the selected diagnostic executable's
--readback-call-path-info CPU probe. The ordinary executable rejects that flag.
A malformed/missing/old source identity or failing compiled probe is rejected.
These gates supplement all existing plan/approval/source/build checks.

The probe reports CPU_ONLY. It exercises the same dispatcher as the pre-MD call,
with CPU callback spies, and creates no readback evidence. Actual device-to-host
readback and GPU-evolved-position oracle execution remain untested in this milestone.

Reproduce CPU-only native checks:

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 examples/KG_Assoc/kg_assoc_100m/builds/ea_24m_extensions_readback_20261019_v2/kg_assoc_stars --self-test
timeout 600 examples/KG_Assoc/kg_assoc_100m/builds/ea_24m_extensions_readback_20261019_v2/kg_assoc_stars_candidate_smoke --self-test
timeout 600 examples/KG_Assoc/kg_assoc_100m/builds/ea_24m_extensions_readback_20261019_v2/kg_assoc_candidates_test
timeout 600 examples/KG_Assoc/kg_assoc_100m/builds/ea_24m_extensions_readback_20261019_v2/kg_assoc_stars_candidate_smoke --readback-call-path-info
```

This existing build directory is immutable; rebuilding requires a different new
out-of-tree directory and authenticated plan/build updates, never replacement.
