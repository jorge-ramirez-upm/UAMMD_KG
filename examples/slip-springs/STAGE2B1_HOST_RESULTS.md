# Stage 2B.1 Linux-host results and milestone closure

**STAGE 2B.1 ACCEPTED — DEVELOPMENT-HOST SCIENCE, PERFORMANCE AND MEMORY VALIDATION PASSED**

Recorded 16 October 2026 (Europe/Madrid). Validated implementation commit:
`1029567096531a2654f362bf7b958359ec77f44c` on `slip-springs`.

## Provenance and evidence

These are user-executed Linux-host results communicated through ChatGPT. Codex
recorded the supplied measurements and inspected accessible output files; it did
not independently execute or authenticate the host measurements. Acceptance is
for the development host and tested workloads, based on that evidence.

Host output directory: `/tmp/rouse-stage2b1-host.hl1lsY`.
[STAGE2B1_HOST_SHA256SUMS](STAGE2B1_HOST_SHA256SUMS) records SHA-256 hashes of all
71 accessible files, with exact paths relative to that directory: metadata,
relaxation curves, analyses, logs, timing reports and memory-monitor traces.
Hashes identify the bytes inspected at recording time; they do not authenticate
execution provenance. Raw artifacts remain in the host directory, outside Git;
its temporary location is not a permanent archive. This document and the
manifest preserve the numerical summary and file identities in repository history.

Relevant paths relative to the host output directory:

- `single-w{1,2,4,8,12,16}-b128/`: worker scaling, with `metadata.json`,
  `relaxation.csv` and `stream_analysis.json` in each directory.
- `single-w{8,16}-b{32,512}/`: additional batch sensitivity runs, same three files.
- `double-w{1,8,16}-b128/`: double-precision runs, same three files.
- Matching `<run>.log` and `<run>.time`: simulator logs and process timing reports.
- `memory/metadata.json`, `memory/relaxation.csv`, `memory/stream_analysis.json`,
  `memory.log`, `rss.txt`, `gpu-memory.txt`: million-step run and memory monitoring.

The brace notation above groups paths; the manifest lists each exact filename.
To check the accessible artifact snapshot again from the repository root:

```bash
MANIFEST=$(realpath examples/slip-springs/STAGE2B1_HOST_SHA256SUMS)
(cd /tmp/rouse-stage2b1-host.hl1lsY && sha256sum -c "$MANIFEST")
```

## Environment and scientific validation

Development host: NVIDIA GeForce RTX 3060 Ti; Intel Core i7-12700 with 12 physical
cores and 20 logical CPUs; Linux and CUDA 13. Single- and double-precision
builds used asynchronous streaming and independent per-chain Correlator6
instances. CPU and platform details are supplied by the user; simulator metadata
also identifies the GPU and numerical precision.

Stage 2B previously passed the full 54-simulation matrix and N32 terminal
relaxation validation (504/504 checks), as reported by the user. Stage 2B.1
preserved byte-identical correlation outputs across tested worker counts.
Inspection of this artifact directory found all 10 short single-precision
relaxation files byte-identical, including batch variants; all three short
double-precision relaxation files were byte-identical within that precision.
No pathwise equality between precisions is implied.

The million-step memory-stability run passed **728/728 analytical 5-SE checks**.
The accessible `memory/stream_analysis.json` contains 728 checks marked passed,
`z_limit=5`, `min_pairs=8`, and overall `passed=true`. Scientific tolerances,
raw stress channels, modulus weighting and chain-cluster uncertainties remain
unchanged. No new simulation or analysis campaign was executed by Codex to close
this milestone.

Million-step workload:

| Parameter | Value |
| --- | ---: |
| Springs per chain N | 32 |
| Independent chains | 4,096 |
| Requested dt | 0.005 |
| Integration steps | 1,000,000 |
| Stress sampling interval | 20 steps |
| CPU workers | 16 |
| Batch capacity | 128 frames |
| Correlator levels / slots / decimation | 20 / 16 / 2 |
| Precision | Single (metadata `real_bits=32`) |
| Seed | 620032 (metadata) |

The stored single-precision dt is `0.004999999888241291`; the requested dt is
0.005. No sampling-frequency adjustment was used for performance.

## Memory stability

| Monitored quantity | Result |
| --- | ---: |
| CPU RSS after initialization | Constant 419,556 KiB |
| GPU memory | Constant 192 MiB |
| Observed increase during monitored execution | None |

`rss.txt` includes an initial 8,668 KiB startup observation followed by ten
419,556 KiB observations; `gpu-memory.txt` contains ten 192 MiB observations.
These observations support stability over this monitored run; they are not a
claim about unobserved intervals or every possible workload.

## Single-precision worker scaling

Every run: 4,096 chains, N32, 80,000 integration steps, requested dt=0.005,
stress every 20 steps, batch128, L20/p16/m2. Overall production ns/bead/step is
the primary metric. Speedup is relative to the one-worker run.

| Workers | Overall ns/bead/step | CPU correlation wall (s) | Buffer waiting (s) | Speedup |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1.02956 | 11.1010 | 9.7289 | 1.00 |
| 2 | 0.75180 | 8.0975 | 6.8424 | 1.37 |
| 4 | 0.42426 | 4.5554 | 3.4435 | 2.43 |
| 8 | 0.26014 | 2.7807 | 1.7679 | 3.96 |
| 12 | 0.20633 | 2.1997 | 1.2023 | 4.99 |
| 16 | 0.16399 | 1.7421 | 0.7585 | 6.28 |

## Batch and precision sensitivity

Same 80,000-step physical workload and correlator configuration as above.

| Precision | Workers | Batch | Overall ns/bead/step |
| --- | ---: | ---: | ---: |
| Single | 8 | 32 | 0.26221 |
| Single | 8 | 128 | 0.26014 |
| Single | 8 | 512 | 0.26522 |
| Single | 16 | 32 | 0.17830 |
| Single | 16 | 128 | 0.16399 |
| Single | 16 | 512 | 0.16281 |
| Double | 1 | 128 | 1.40377 |
| Double | 8 | 128 | 1.37617 |
| Double | 16 | 128 | 1.37705 |

At 16 workers, single-precision batch512 improves overall performance by only
approximately 0.7% relative to batch128. Prefer **16 workers, batch128** as the
practical development-host configuration for this workload. This is an explicit
run configuration; the simulator default remains one worker. These observations
do not establish a universally optimal worker count or batch size.

## Bottleneck diagnosis and timing scopes

| Precision | Workers | GPU ns/bead/step | Overall ns/bead/step | CPU corr wall (s) | Consumer idle (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Single | 1 | 0.07748 | 1.02956 | 11.1010 | 0.0305 |
| Single | 8 | 0.07534 | 0.26014 | 2.7807 | 0.0306 |
| Single | 16 | 0.07496 | 0.16399 | 1.7421 | 0.0293 |
| Double | 1 | 1.36388 | 1.40377 | 10.9038 | 4.2456 |
| Double | 8 | 1.36326 | 1.37617 | 2.7237 | 12.1270 |
| Double | 16 | 1.36329 | 1.37705 | 1.7296 | 13.1310 |

The measurements support CPU correlation as a substantial single-precision
bottleneck, while double precision is GPU-limited on this particular GPU.
Increasing workers substantially reduces double-precision correlation time but
barely changes overall production cost; consumer idle time increases.

CPU correlation wall is elapsed batch processing (`cpu_correlation_wall_seconds`),
not aggregate worker execution time. Buffer waiting is producer free-slot wait;
consumer idle is queue wait. CPU, GPU and transfer scopes overlap and must not
be added to obtain production elapsed time. Overall production includes final
worker drain and excludes initialization, equilibration and final curve output.
See [STAGE2B1_REPORT.md](STAGE2B1_REPORT.md) for complete timing definitions.

## Acceptance and remaining scope

**STAGE 2B.1 ACCEPTED — DEVELOPMENT-HOST SCIENCE, PERFORMANCE AND MEMORY VALIDATION PASSED**

Further optimization is not required before N100 terminal-relaxation experiments.
Those experiments have not been executed as part of this documentation task.
Production-server-specific performance must be benchmarked separately; portable
implementation does not imply equal scaling or optimal settings on other CPUs
or GPUs. No universal performance claim is made.

This milestone closure changes documentation only. Simulator code, physics,
tests, numerical tolerances, sampling frequency and repository-wide
infrastructure remain unchanged. Stage 3 and new physics have not begun.
The original [validation plan](STAGE2B1_VALIDATION_PLAN.md) remains a record of
planned commands; the actual supplied results and accessible run coverage are
recorded here (double workers1/8/16 and a 16-worker memory run).

## Subsequent Stage 2B closure

**STAGE 2B COMPLETE — STREAMING STRESS RELAXATION VALIDATED**

The later user-executed N100 terminal experiment passed 686/686 checks; its
configuration, performance, interpretation and permanent five-file text archive
are in [STAGE2B_N100_TERMINAL_RESULTS.md](STAGE2B_N100_TERMINAL_RESULTS.md).
This supersedes the earlier prospective N100 statement above without changing
the original Stage 2B.1 measurements or its 71-file snapshot manifest. The
validated system is the independent Rouse reference; slip-spring physics remains
unimplemented and unvalidated. No Stage 3 implementation has begun.
