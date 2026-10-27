# D2A.5 resource and uninterrupted-run planning

Preparation only; arithmetic estimates below are not benchmarks. The D2A.4
user-reported T1000/R3 four-cell aggregate was 13515.86144873 s, peak recorded
child RSS 163524608 bytes. Those reports are a reference, not new authentication
or scientific analysis. GPU peak memory was not measured. Actual D2A.4 scientific
interpretation remains separate; this implementation does not infer its results.

## Physical targets and workloads

| N bonds | Beads/chain | M | Total beads | Constrained Z | Proposed T | Steps at h=0.0001 |
|---|---|---|---|---|---|---|
| 32 | 33 | 256 | 8448 | 2048 | 1000 (previous campaign) | 10000000 |
| 64 | 65 | 256 | 16640 | 4096 | 10000 | 100000000 |
| 128 | 129 | 256 | 33024 | 8192 | 40000 | 400000000 |

Longer-chain targets are provisional: four cells (kappa0/10, bare/constrained),
three independent whole-run replicas per cell. No manifests, fixed seeds,
production launch commands or multi-day timeouts are selected in this milestone.
Desired terminal COM/monomer diffusion, intermediate constraint effects and C1/C2
relaxation are objectives, not predictions. Density Z/(MN)=1/4 is nominal.
Bare COM reference is `6t/(N+1)`; it does not apply to fixed spatial constraints.

Stretching work scales with MN, active bending with M(N-1); the existing force
implementation, GPU launch shape and old/new buffers are unchanged. Expected
hopping attempts per integration step are `Z*100*h` (20.48, 40.96, 81.92 for
these constrained systems). Actual scheduling, serial jump kernels, renewal
contour scans and accepted-event counts must be measured. Longer contiguously
indexed bead arrays change RNG logical IDs between lengths; matching seeds do
not create identical noise for each chain across different N.

Against N32/T1000, N64/T10000 has about 19.7 times bead-update work and 20 times
expected hopping work; N128/T40000 has about 156.4 and 160 times respectively.
Applying 20 or 160 to the reported 12-run total gives crude cohort proxies of
approximately 75 hours or 25 days on the same host. These are neither runtime
bounds nor portable predictions. Fixed launch costs, synchronous readback,
CPU correlation, filesystem, final serialization and load can change scaling.
No production wall-time budget is fixed before user-run bounded measurements.

## Memory and transfer accounting

For C=M(N+1), baseline device arrays contain three `real4` arrays (old, new,
force), plus N `real2` bonds and N+1 scalar angles only when active. Constrained
mobile systems additionally use C `real4` dense anchors, C integer occupancy,
Z `Spring` records and constant-size statistics/error state. In double precision
real4 is 32 bytes; use actual compiler `sizeof(Spring)` and vector capacities,
not an assumed packed ABI. All diagnostic/index and allocation guards are
retained. Physical `device_bytes` is array accounting, not driver peak usage.

Host initialization, force/reference and equilibrium-context workspaces scale
with C and Z. The simulator's existing host preflight estimate includes eight
coordinate-sized buffers plus C*1024 and optional occupancy/spring workspaces;
this conservative estimate is not RSS. Actual child RSS and allocation failures
must be checked at all three lengths. Do not infer GPU peak from preflight free
memory or sum overlapping host/GPU timers.

Correlator count stays nine owners per chain: six diffusion and three vector
feature owners for C1/C2. Length changes do not multiply this bank. For LP64,
P16, the principal per-owner per-level payload is
`P*(8*sizeof(double)+2*sizeof(unsigned long)) + 5*sizeof(void*)
+3*sizeof(double)+2*sizeof(unsigned int) = 1352 bytes`.
M256/L15 therefore uses about 44.6 MiB in these payloads. The unchanged observer
preflight applies a conservative multiplier and export/metadata scratch allowance;
its actual `conservative_observer_estimate_bytes`, budget and RSS are authoritative
for each build. Model coefficient vectors add O(N); CPU acquisition stays serial.

| N | Full double position readback/frame | Frames at stride100 and proposed T | Cumulative full-position transfer/run |
|---|---|---|---|
| 32 | 270336 bytes | 100001 at T1000 | about 27.0 GB |
| 64 | 532480 bytes | 1000001 | about 532.5 GB |
| 128 | 1056768 bytes | 4000001 | about 4.23 TB |

These are cumulative GPU-to-host bytes, not simultaneous memory or stored
trajectories. Shared scalar/equilibrium readbacks reduce redundant transfers;
existing byte counters distinguish shared versus extra reads. Across twelve
runs, longer targets imply about 6.39 TB / 50.7 TB of full-coordinate traffic.
No new gather kernel or asynchronous transport is proposed here.

## Provisional lag and storage choices for later review

Retain physical sample interval 0.01 if stride100 is retained. Candidate P16/m2
banks are L19 for N64/T10000 and L21 for N128/T40000, with a 512 MiB observer
budget for headroom. These are planning candidates, not frozen campaign settings.
For F frames, the existing KG export omits its deepest reached level. At level
k the completed coarse samples number `floor(F/2^k)`; exported lag ell*2^k has
origins `floor(F/2^k)-ell`, with ell=8,...,15 on promoted levels, when available.
The fine level has ell=0,...,15. Only completed blocks enter either estimator.

For the candidates above, longest exported lag is 9175.04 (N64) / 36700.16
(N128), each with only one origin per chain. A provisional conservative primary
ceiling uses both lag<=T/5 and >=32 origins per chain: last eligible lags are
1966.08 / 7864.32, each with 49 origins at the corresponding level. These
arithmetic supports must be checked against actual output after implementation
verification. They do not guarantee statistical independence, stationarity,
adequate relaxation or reliable uncertainty. Retain individual replicas and
whole-run SE. Do not interpret coarse orientation and displacement as the same
filter or fit across a level boundary without accounting for support.

Correlation CSV storage grows with chain count and exported grid depth, not F.
Dense scalar output, however, grows linearly with duration. Retaining sample5000
means 20001 / 80001 scalar frames and about 5.12 / 20.48 million chain rows per
longer run. Sparse full-E1 context and initial/final joint snapshots should stay
sparse, never full trajectories. A future campaign must review scalar cadence
separately from dynamics stride and estimate disk using measured row widths;
it must not silently thin accepted observations. No production schedule changes
are made now. Preserve evidence outside the repository, maintain free-disk
headroom and stop on failure without automatic retry.

The prepared optional 100/1000-step measurements in
[the implementation report](E1_STAGE_D2A5_IMPLEMENTATION_REPORT.md) collect actual
physical/observer metadata, wall time and RSS after correctness checks. They
expose startup/finalization costs and new-length failures; longer bounded timing
windows may later be needed to extrapolate steady throughput. No performance
result is claimed and no benchmark was executed. Checkpoint/restart is deferred;
production feasibility presently assumes uninterrupted execution.
