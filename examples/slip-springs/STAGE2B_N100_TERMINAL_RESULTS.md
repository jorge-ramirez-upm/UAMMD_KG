# N=100 terminal stress relaxation and Stage 2B closure

**STAGE 2B COMPLETE — STREAMING STRESS RELAXATION VALIDATED**

Recorded 16 October 2026 (Europe/Madrid). Repository branch: `slip-springs`.
Closure task starting SHA: `a798e5db2643de5388b87370a15b311966c2707f`,
verified against the fetched remote before edits.

## Provenance and permanent artifact archive

This is a user-executed Linux-host experiment communicated through ChatGPT.
Codex inspected the accessible text artifacts and archived them byte-for-byte;
it did not independently execute or authenticate the simulation. Original output:
`/tmp/rouse-stage2b1-host.hl1lsY/terminal-N100/`. The `.log` and `.time` files
are in its parent directory. The artifacts do not embed an executable Git SHA;
the closure starting SHA above identifies this documentation task, rather than
independently proving the executable's source identity.

All five small text artifacts (about 310 KiB combined) are permanently copied to
[validation/stage2b-n100-terminal/](validation/stage2b-n100-terminal/):

| Original path relative to `/tmp/rouse-stage2b1-host.hl1lsY/` | Archived filename |
| --- | --- |
| `terminal-N100/metadata.json` | `metadata.json` |
| `terminal-N100/relaxation.csv` | `relaxation.csv` |
| `terminal-N100/stream_analysis.json` | `stream_analysis.json` |
| `terminal-N100.log` | `terminal-N100.log` |
| `terminal-N100.time` | `terminal-N100.time` |

[SHA256SUMS](validation/stage2b-n100-terminal/SHA256SUMS) preserves the SHA-256
hash of every archived file, which also matches its original host file. These
hashes identify the recorded bytes; they do not authenticate who ran the experiment.
The original log retains ANSI formatting and one trailing-space line to preserve
its exact hash; documentation whitespace checks exclude that raw log.
No binary simulation outputs or executables are committed. Verify the permanent
archive from the repository root:

```bash
(cd examples/slip-springs/validation/stage2b-n100-terminal && sha256sum -c SHA256SUMS)
```

## Experiment configuration

| Parameter | Value |
| --- | ---: |
| Rouse springs per chain N | 100 |
| Independent chains | 4,096 |
| Total beads | 413,696 (101 per chain) |
| Precision | Single (`real_bits=32`) |
| Requested timestep | 0.005 |
| Production steps | 700,000 |
| Production physical time | Approximately 3500 |
| Stress sampling | Every 20 integration steps |
| Stress observations per chain | 35,001, including step 0 |
| Random seed | 620100 |
| Equilibration steps | 0 |
| Backend | Asynchronous streaming |
| Effective CPU workers | 16 |
| Batch capacity | 128 frames |
| Multi-tau levels / slots / decimation | 20 / 16 / 2 |
| GPU | NVIDIA GeForce RTX 3060 Ti |

The stored single-precision timestep is `0.004999999888241291` and recorded
physical time is `3499.9999217689037`. No physics, precision arithmetic,
sampling interval, or analytical tolerance was changed in this archive task.

User-executed analysis command:

```bash
python3 examples/slip-springs/stream_analysis.py /tmp/rouse-stage2b1-host.hl1lsY/terminal-N100 --terminal
```

The archived analysis JSON preserves its result; the command was not rerun by
Codex. The timing report also preserves the exact simulator invocation.

## Scientific result and interpretation

**PASS 686/686 analytical 5-SE chain-cluster checks.** The stored analysis has
`passed=true`, `z_limit=5`, `min_pairs=8`, and all 686 checks marked passed.
Independent chains are the uncertainty clusters; overlapping time origins and
correlated stress channels are not treated as independent samples. The
multi-tau comparisons retain the existing finite-step, block-averaged reference.

The theoretical terminal stress-relaxation time is

\[
\tau_G=\frac{1}{24\sin^2[\pi/(2(N+1))]}.
\]

For N=100, `tau_G = 172.27678861671365`, approximately 172.3 simulation time
units. It is a theoretical stress-relaxation time, not an independently fitted
measurement. The archived terminal checks are:

| Target time | Available lag time | Modulus g | Chain-cluster SE | Stored check |
| ---: | ---: | ---: | ---: | --- |
| 2 tau_G = 344.5535772 | 332.7999926 | 0.1455084499 | 0.0050485052 | PASS |
| 4 tau_G = 689.1071545 | 665.5999851 | 0.0200928501 | 0.0041843229 | PASS |

The user reports that the terminal modulus remained statistically resolved
through approximately four terminal stress-relaxation times and approached the
noise floor by approximately six. The stored terminal checks support the stated
resolution near four; the approximate six-time noise-floor description is the
user's interpretation, not an additional independent fitted-time gate.

Agreement with the theoretical modulus and an independent numerical estimate of
the terminal relaxation time are distinct scientific claims. This experiment
validates consistency with the specified reference and terminal signal coverage.
No independent fitted relaxation time or fitted uncertainty is supplied or
inferred. Such an estimate would require a separately defined fit window,
block-averaging treatment, covariance/error procedure and goodness-of-fit check.

## Measured performance

| Metric | Value |
| --- | ---: |
| Production wall time | 25.472352884 s |
| GPU integration | 0.0776371686728598 ns/bead/step |
| Overall production | 0.08796090740198462 ns/bead/step |
| CPU correlation wall time | 15.257946317 s |
| CPU producer buffer wait | 0.000024964 s |
| Effective CPU workers | 16 |
| GPU stress sampling and transfer | 2.814416815 s |

Overall production cost is approximately **13.3% above** GPU integration-only
cost: `100*(overall/integration - 1) = 13.2974%`. The denominator is
413,696 beads times 700,000 production steps. Production excludes initialization,
equilibration and final curve evaluation/output, and includes the worker drain.
GPU stress sampling and transfer is a sum of CUDA event intervals, not a separate
critical-path wall interval. CPU correlation processing and GPU activity overlap;
their elapsed times must not be added as sequential costs. The 16-worker execution
sum is also not CPU correlation elapsed time. Results describe this GPU and host
configuration; production servers require their own benchmarks.

## Stage 2B closure evidence

| Evidence | Recorded outcome / provenance |
| --- | --- |
| Stage 1 and Stage 2A regressions | Validated reference suites; historical [Stage 1](STAGE1_REPORT.md) and [Stage 2A](STAGE2A_REPORT.md) reports |
| Full Stage 2B matrix | 54 simulations passed, user-reported |
| N32 terminal relaxation | 504/504 checks passed, user-reported |
| Stage 2B.1 parallel CPU correlator | Accepted on development host; [host results](STAGE2B1_HOST_RESULTS.md), deterministic output and performance evidence |
| Million-step memory stability | 728/728 checks; stable monitored memory, recorded in Stage 2B.1 host results |
| N100 terminal relaxation | 686/686 checks and terminal coverage; permanent five-file archive linked above |

**STAGE 2B COMPLETE — STREAMING STRESS RELAXATION VALIDATED** applies to the
independent Gaussian Rouse reference simulator and its stress-analysis pipeline.
It does not mean a slip-spring model has been implemented or scientifically
validated. Existing finite-coordinate-precision and Correlator6 export/sentinel
limitations remain documented. Stage 3 is not authorized or started by this
closure. The [next-stage assessment](NEXT_STAGE_ASSESSMENT.md) identifies the
existing roadmap and unresolved scientific decisions without selecting a model.
