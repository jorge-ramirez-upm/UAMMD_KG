# Stage 4A.2 frozen Linux-host acceptance plan

Frozen before long experiments, 16 October 2026. Bounded Codex checks are software
verification only. Do not revise these gates after seeing campaign outcomes;
record deviations as a new plan/version. No stress or slip-spring observables.

Run both precisions on a Linux CUDA host. Record commit, GPU/driver/toolkit,
compiler, NumPy version, exact commands, all metadata and raw per-chain samples.
Use seeds 420201,420202,420203 as separate independent replicas. Independent
chains (not time origins) are uncertainty clusters. Average measurements per
chain over the final half of a run, then compute SE across chains; combine
replicas only after checking agreement. Initial ensembles are exact equilibrium,
so initial-vs-final shifts measure numerical bias rather than equilibration.

Systems: N=1,8,32; C=2048; b0=1,kb=30; homogeneous kappa=0,2,10, plus N=8
heterogeneous b0 alternating 0.8/1.2, kb alternating 20/40 and bead-indexed kappa
[0,0,2,0,10,0,2,0,0]. kBT=1,zeta=1. Physical duration T=20 for N=1,8 and
T=50 for N=32. Timesteps 0.0002,0.0001,0.00005; sample every physical 0.02.
Compare all radial first/second moments, fixed histograms, tangent separations
1..min(4,N-1), Re^2 and Rg^2 with independent Stage 4A.1 quadrature/transfer
predictions. Rg^2 is the sum of pair subchain mean-square distances divided by
(N+1)^2. Require finest timestep error <=6 cluster SE + 0.5% of prediction
(absolute floor 0.005 for near-zero tangent correlations). Initial ensembles
must pass 6 SE + 0.1% for nonzero moments, with the same 0.005 tangent floor.
Check histogram CDF distance <=0.065 initially (per-bond DKW false-rejection
bound <6.2e-8 at C=2048, allowing the full multiple-case campaign) and <=0.03 for pooled per-chain
CDFs at the finest step; estimate uncertainties from independent chain CDFs.

Timestep gate: for each nonzero observable, finest-vs-middle difference <=
6 combined SE + 0.5% of prediction. If coarsest error is resolved (>6 SE), its
error must decrease at least 25% between coarsest and finest, allowing six
combined chain SE in that trend comparison; unresolved errors
are reported as unresolved, not proof of first-order convergence. No failure,
NaN or collapsed active bond may occur. Report minimum observed bond length
and dt*max(kb/zeta,kappa/(zeta*l_min^2)); this is a stiffness indicator, not a
universal stability proof (stretch transverse curvature also depends on b0/l).

COM: MSD from the initial COM at physical times 0.02,0.1,1,5,20 (and 50 if
available) must match 6*kBT*t/((N+1)*zeta) within 6 chain SE + 0.5%.
Monomer MSD: use the controlled b0=0,kappa=0,kb=3 Gaussian case, N=8,C=4096,
seeds above, T=5, dt=0.001,0.0005,0.00025, sample0.01. Compare initial-origin
MSD with the exact discrete EM mode covariance (including its transient from
continuous equilibrium). Require 6 chain SE +0.5%; compare finest-step result
to continuous theory with 6 SE +1%. This controlled reference is not applied
to the finite-rest-length model. Check COM at all recorded times too.

Reproducibility: repeat a short run exactly in each precision; numerical files
must match byte for byte (timings excluded). Chain isolation: append independent
chains with the same seed; preceding chains must retain identical trajectories.
Noise check: one-step prescribed zero positions, b0=0,kappa=0,kb=3,C=8192,N=1,
dt=0.001,kBT=1,zeta=2. Standardized increments must have |mean|<6/sqrt(n),
|variance-1|<6*sqrt(2/(n-1)); cross-component covariance <6/sqrt(n).

Memory/performance: do not change sample frequency. Record initialization,
observation/D2H, recurrent/final output, GPU integration and production wall
costs separately, plus ns/bead/step, updates/s, device allocation and CPU
workspace estimates. Peak memory should be O(C*N), independent of step count;
compare T=1 and T=20 at equal C,N using /usr/bin/time -v and nvidia-smi.
The initial synchronous diagnostic implementation is not a production benchmark.
Run compute-sanitizer memcheck/racecheck on the bounded suite if available.

Exact campaign generation/execution and analysis commands are supplied by
`tests/semiflexible_host.py` and README. Its default only writes/prints the
campaign; `--run` explicitly executes the long user-host work. Store outputs
under a fresh external directory; never overwrite a campaign. Full scientific
acceptance requires an archived user-host report covering every gate above,
not merely a successful process exit or passing bounded suite.
