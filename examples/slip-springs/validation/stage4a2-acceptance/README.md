# Stage 4A.2 original host evidence archive

Archived 17 October 2026 (Europe/Madrid). This is evidence from user-executed
Linux-host experiments, inspected and copied by Codex without rerunning them.
Checksums identify bytes; they do not authenticate the execution or independently
prove the compiler/executable Git identity.

## Original files

`ORIGINAL_FILES.json` lists the exact source path, archived relative path, byte
count and SHA-256 of all **230 original files**, copied byte-for-byte:

* From `/tmp/semiflexible-host.CR6bWs/campaign/`: original manifest, analysis,
  command script, 12 small parameter files and all 204 per-run metadata files.
* From `/tmp/semiflexible-memory.wLFbVS/`: original build-command output,
  two time reports, two GPU-monitor logs, two execution logs, and metadata/
  parameter files for both memory runs.

`BENDING_METADATA_INDEX.json` is a **derived** compact index of the original
204 metadata files, not an additional independent measurement. It records
114 zero-active-angle cases with zero bending allocation/launches and 90 active
cases with nonzero allocation/launches. `ORIGINAL_FILES.json` is also derived.

The original supplied `stage4a2-review.tar.gz` and `evidence.tar.gz` members were
compared with the loose originals and matched. Their redundant tar containers
are not committed. Large samples, per-chain observations, bond histograms,
coordinate snapshots, executables and the redundant all-zero input file are
not committed. Original data directories are untouched.

## Inspected results

Original analysis status:

    statistical gates passed; manual host evidence still required

`failures` is empty. The manifest has 204 experiments; the analysis has 198
non-noise summaries plus the six noise experiments handled by the analyzer.
All 456 timestep records have `coarse_bias_resolved=false`. This supports no
measured Euler–Maruyama convergence order. The analysis status is preserved
verbatim, including its manual-evidence reminder; it is not rewritten to say
accepted. The user's final acceptance instruction and separate memory evidence
are recorded in [the report](../../STAGE4A2_REPORT.md).

The original frozen plan is retained unchanged in the repository. Its SHA-256
is `fd57af47349304a9f71bae89ff6c23a4fae844894e2b12658d25b1f009cb60c2`.
No original campaign-root copy of the plan, commit file, compiler transcript or
hardware-provenance transcript was present. Source identity and the reported
8192 MiB, driver 580.178.04, NumPy 2.2.4 and system nvcc CUDA 11.5.119 are
user-supplied provenance. GPU model is additionally present in original metadata.
The archived build output says `Nothing to be done`; it does not establish
which toolkit originally compiled the binaries. Development CUDA 13.0.88 is
historical implementation evidence, not independently verified campaign-build
provenance. No original executable hash or campaign-wide stdout transcript was
available in these evidence directories; none is fabricated.

The original memory files support peak CPU RSS 108556/108392 KiB and GPU
run plateaus of 145 MiB for 20000/400000 steps. GPU-monitor files contain startup
readings of 1/2 MiB before the plateau. These are whole-device nvidia-smi readings,
not process-specific allocations. The small RSS difference is not interpreted
as memory growth or shrinkage. Full original execution commands and performance
measurements remain in the time/log files.

## Verification

`SHA256SUMS` covers every payload file, including the derived indexes and this
README, but excludes the checksum file itself. Original-file hashes in
`ORIGINAL_FILES.json` also matched the source files at archival time.

From the repository root:

```sh
(cd examples/slip-springs/validation/stage4a2-acceptance && sha256sum -c SHA256SUMS)
```

Acceptance is limited to the frozen plan's tested configurations/tolerances.
It does not establish arbitrary-parameter stability, a production-server speed
claim, architectural superiority over UAMMD, stress extensions or slip-springs.
