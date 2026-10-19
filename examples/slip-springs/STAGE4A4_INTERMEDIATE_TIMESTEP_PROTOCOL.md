# Stage 4A.4 — Intermediate timestep validation protocol

Status: prepared only. The two `dt=5e-4` GPU trajectories have not been launched, and this document does not infer their results.

## Authorized bounded experiments

| setting | kappa=0 | kappa=10 |
|---|---:|---:|
| springs / chains | 8 / 512 | 8 / 512 |
| precision | double | double |
| timestep / physical duration | .0005 / 20 | .0005 / 20 |
| integration steps / scalar stride | 40,000 / 20 | 40,000 / 20 |
| stress | six channels every step, including zero | six channels every step, including zero |
| transport / workers | 256 frames / 8 | 256 frames / 8 |
| hierarchy | 32 slots x 20 levels | 32 slots x 20 levels |
| initializer / seed | existing exact initializer / 433201 | existing exact initializer / 433201 |
| scalar profile / timeout | full / 300 s | full / 300 s |

The runner preserves `b0=1`, `kb=30`, all existing dynamics and stress definitions. Each run is sequential and receives its own strict five-minute `timeout`; a timeout preserves output and receipts but is never resumable.

The closest measured cost is the existing `dt=1e-3` screen: 4.82 s wall / 1.01 s integration for kappa=0 and 6.65 s / 1.66 s for kappa=10. Doubling only the integration-step count gives planning estimates of about 5.8 s and 8.3 s respectively (constant observation/output cost plus doubled integration). These are extrapolations, not performance claims; the 300 s bound remains authoritative. The intermediate run has 40,001 online stress frames and 2,001 scalar frames, so scalar output volume is comparable to the old screen while stress accumulation remains bounded rather than raw-dumped. `/usr/bin/time -v`, simulator metadata, and stress metadata provide measured RSS, device/pinned estimates, and timing after execution.

## Host commands

Preflight is safe by default and makes a unique evidence root:

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
bash examples/slip-springs/tests/run_stage4a4_intermediate_timestep.sh
```

Explicit user-authorized execution only:

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
bash examples/slip-springs/tests/run_stage4a4_intermediate_timestep.sh --execute-intermediate
```

The runner refuses a non-development checkout, dirty branch, missing CUDA 13.0/double executable, or either protected checkout not clean and pinned at `4e46d6014aa812b1fc687335654c4b1f681ddd22`. It records Git identity, executable SHA-256, exact argv, compiler/GPU/host information, GPU snapshots, `/usr/bin/time -v`, exit status, and partial-evidence receipt. Existing baseline evidence in `/tmp/stage4a4-timestep-preflight.GkS8wI` is read only.

## Post-run analysis

`tests/stage4a4_intermediate_timestep_analysis.py` runs automatically only after both intermediate cases complete, writing fresh JSON receipts in the new evidence root. It compares baseline `.000025`, intermediate `.0005`, and existing `.001` using:

- chain-cluster first/second-half static estimates and the established exact equilibrium references;
- bond moments, `R_e²`, `R_g²`, tangents, and the available per-chain bond histogram;
- explicit reporting of unavailable energy, local-angle-distribution, and end-to-end-distribution diagnostics;
- `H(0)`, normalized `H/H(0)`, three fixed-lag comparisons, crossing intervals, six weighted channel contributions, block widths, and origin counts.

It uses the existing conservative unpaired timestep propagation. It reports the intermediate and large `H(0)` changes with their uncertainty as a **prospective amplitude-bias diagnostic only**. No quantitative `H(0)` threshold is added here, so it cannot determine final acceptance by itself.

The frozen decisions remain unchanged: static bond moments use 1%, size/tangent observables 2%; at fixed dynamic lags, `|ΔH|+3SE` must not exceed 5% of baseline `H(0)`; and the crossing comparison must meet its 10% criterion accounting for uncertainty. Different multi-tau bin centers and widths are reported rather than interpolated away.

## Expected decision use

The new data can establish whether `.0005` reduces the resolved `.001` kappa=10 bond/tangent and stress-amplitude shifts, but cannot assume linearity in timestep. It may pass available static, normalized-shape, and absolute-stress gates independently. Final production-timestep authorization remains incomplete until the missing static diagnostics are available; kappa=10 additionally needs a resolved crossing comparison if its uncertainty remains as in the `.001` screen.
