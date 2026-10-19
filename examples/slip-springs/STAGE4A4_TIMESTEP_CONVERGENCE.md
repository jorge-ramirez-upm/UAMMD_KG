# Stage 4A.4 — Adaptive timestep convergence protocol

Status: prospective CPU-only preparation. No timestep has changed and no GPU screen has been started.

## Exact equilibrium reference

The reference is deliberately not a small-timestep trajectory. The existing double-precision `semiflexible_reference.Chain` samples the exact factorised equilibrium bond-length and conditional-orientation distribution for the implemented finite-rest-length Kratky--Porod potential (`b0=1`, `kb=30`, interior `kappa`). The new `tests/stage4a4_equilibrium_reference.py` produces independent-chain JSON reference reports with chain-cluster standard errors for bond moments and histogram, local-angle cosine, orientation correlations, `R_e^2`, `R_g^2`, end-to-end distance, and stretching/bending energies. It uses no integrator, GPU code, or time origin.

CPU checks using 65,536 exact independent chains (seed 440401) gave these reference means. The JSON records uncertainty; rounded values below are not the comparison authority.

| N | kappa | mean r | `R_e^2` | `R_g^2` | stretch E | bend E | tangent(1) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0 | 1.06454 | 9.26876 | 1.72221 | 4.25827 | 0 | -0.00064 |
| 8 | 10 | 1.06447 | 56.33723 | 6.42838 | 4.24215 | 7.01233 | 0.89982 |
| 32 | 0 | 1.06461 | 37.25605 | 6.40189 | 17.03896 | 0 | -0.00079 |
| 32 | 10 | 1.06454 | 492.06954 | 58.82036 | 17.04703 | 31.01055 | 0.89997 |

The fixed histogram has 32 finite bins on `[0, 1+8/sqrt(30)]`, matching the simulator range; overflow is a separate tail.

## Pre-registered static criterion

For each simulator run, average scalar observations in the final half of equal physical time within each chain, then obtain uncertainty from between-chain variation. Frames, bonds, and overlapping origins are never treated as independent chains. For normalized difference `d` and quadrature reference/simulation chain-SE `s`, pass requires `d+3s <= tolerance`; reject requires `max(0,d-3s) > tolerance`; otherwise the result is unresolved. Overlapping confidence intervals therefore cannot by themselves accept a timestep.

| Observable | tolerance |
|---|---:|
| mean bond length and bond-square | 1% |
| `R_e^2`, `R_g^2`, tangent correlations 1--4 | 2% |
| bond histogram total variation | 0.02 |
| central histogram bin / tail probability | 0.01 / 0.005 absolute |
| stretching and bending energies | 1% |
| local angle mean / distribution | 2% / 0.02 total variation |

Nonfinite coordinates, diagnostic failure, or invalid sampled geometry rejects a candidate. Stability alone never passes it. The existing `full` scalar stream plus `bond_statistics.csv` supplies the geometry means, tangents, and bond histogram, but not dynamic angle and end-to-end distributions or energy components. Those must be supplied by an established coordinate/force diagnostic before final static acceptance; until then the candidate is explicitly unresolved rather than accepted on a reduced observable set. No simulator-output change is authorized here.

## Staged screening

Every trajectory retains exact equilibrium initialization, unchanged Euler--Maruyama dynamics, `kBT=zeta=1`, six stress channels every step including zero, 256-frame batches, eight CPU workers, full scalar output, and an independent scalar clock. Raw every-step stress is not dumped; existing online correlation is retained.

1. **A — reference validation.** Make four 65,536-chain exact reference reports and validate the analysis scripts on bounded fixtures; CPU only.
2. **B — N=8 static screen.** At both `kappa=0,10`, consider `dt=[2.5e-5,5e-5,1e-4,2.5e-4,5e-4,1e-3,2e-3]` at equal `T=20`. Scalar physical spacing is `0.01`, giving `--sample=[400,200,100,40,20,10,5]`. The first authorized bracket is baseline and `1e-3`; intermediate values bisect a pass/fail bracket. A first-half/final-half stationarity failure is unresolved and triggers a separately bounded extension decision.
3. **C — N=32.** Only static N=8 candidates enter, but each N/kappa is separately tested. Begin at `T=20`; extend only after documented stationarity failure and a new budget.
4. **D — dynamics.** Static passes are compared to `2.5e-5` at physical lags `0.01`, `0.05`, `0.10`, exactly representable by every candidate. Compare six-channel isotropic `H`, its first `H(0)/e` crossing when bracketed, and existing end-to-end vector relaxation when comparable. At fixed lags, the upper three-SE difference must not exceed 5% of baseline `H(0)`; crossing agreement is 10% plus three-SE uncertainty. An unbracketed crossing or unsupported tail is unresolved, never fitted. This is not a long relaxation campaign.

The selected value for each `(N,kappa)` is the largest candidate passing static and dynamic criteria. The speedup is `2.5e-5/dt`; success never transfers across N or kappa.

## Bounded first host screen

`tests/run_stage4a4_timestep_screen.sh` runs only from `/tmp/UAMMD_KG-slip-springs-dev`, verifies a clean `slip-springs` branch, CUDA 13.0, the double executable SHA-256, and both protected checkouts pinned clean at `4e46d6014aa812b1fc687335654c4b1f681ddd22`. It is preflight-only unless `--execute-first-screen` is supplied.

The explicit first screen executes sequential N=8 cases `(kappa,dt)=(0,2.5e-5),(0,1e-3),(10,2.5e-5),(10,1e-3)`. For `T=20`, baseline is 800,000 steps and each coarse case 20,000; there are 2,001 scalar frames and 800,001/20,001 stress frames including zero. Each run has a strict 900-second timeout. It preserves argv, host/GPU/compiler identities, executable SHA-256, `/usr/bin/time -v`, logs, GPU before/after snapshots, JSON reference, analysis receipt, exit status, and partial output in a unique `mktemp` root. Interrupted work is not resumable.

The only applicable measurement is the previous N=32/kappa=10 512-chain Stage A: 100,000 steps in 49.54 s, peak RSS 192 MiB, no producer blocking. Linear scaling of that different system estimates 396 s for one baseline; it is a planning bound, not an N=8 prediction. A baseline full scalar file has 1,024,512 rows, approximately 0.2--0.3 GiB at 200--300 bytes/row. Existing online correlation uses its declared 512 MiB budget; actual device, pinned, and RSS memory must be recorded.

Safe preflight:

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
bash examples/slip-springs/tests/run_stage4a4_timestep_screen.sh
```

Explicit user-authorized bounded screen:

```bash
cd /tmp/UAMMD_KG-slip-springs-dev
bash examples/slip-springs/tests/run_stage4a4_timestep_screen.sh --execute-first-screen
```

## Open decisions

No larger timestep is established. Final static acceptance remains blocked on an existing validated energy/angle/end-to-end-distribution diagnostic route, and N=32 mixing plus dynamic terminal support are not known. This protocol neither changes the production timestep nor authorizes a scientific campaign.
