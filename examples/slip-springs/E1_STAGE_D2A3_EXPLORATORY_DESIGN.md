# D2A.3 — first exploratory dynamical study, proposed

27 October 2026. **Documentation only; no execution authorization.** Starting
local and freshly queried remote `slip-springs` HEAD:
`41daadb7f3fce70eef08cb4a9eaf37ea54ced2d9`. No tests, builds, simulations,
benchmarks, GPU operations or scientific reducers ran in this milestone.

## D2A.2 bounded technical closure

The user reports successful CPU correctness, sanitizer and allocation-failure
verification of D2A.1/D2A.2, the corrected metadata regression, and the
double-precision tiny GPU integration verifier. Record **bounded technical
acceptance within the tested scope**, not long-time scientific or performance
acceptance. Detailed user logs were not independently inspected here.

The [D2A.1 report](E1_STAGE_D2A1_IMPLEMENTATION_REPORT.md) and
[D2A.2 report](E1_STAGE_D2A2_IMPLEMENTATION_REPORT.md) specify the checks and
their original preparation-time status. The latter's
[tiny verifier](tests/dynamical_integration_tiny.py) exercises N32/M2/24-step
Z0/kappa0 and Z32/kappa10 fixtures: baseline versus implicit-off, explicit-off
and enabled acquisition, plus deterministic enabled replay and invalid settings.
Physical coordinates, attachments and event records agreed within the verified
**saved-output scope**, including seven joint checkpoints; all intermediate
physical states were not compared. Dynamical correlation curves replayed
identically; metadata used explicit timing allowlists.

Verifier correction commit `41daadb7f3fce70eef08cb4a9eaf37ea54ced2d9` and the
[metadata regression](tests/dynamical_integration_metadata_regression.py) retain
inventory filenames and every physical file size, exempting only the byte count
of timing-containing main metadata, whose actual contents are checked
structurally. Unknown/physical metadata differences remain failures.
Prepared matched double executables came from baseline
`0b177a62cf33bcd1143aba98cb83931fecbda9d1` and integration source
`d60982f4035b9b704a23397fb034ca1b58fe5771`; the correction changes the verifier,
not those binaries. External preparation provenance is at
`/home/jramirez/UAMMD_KG-d2a2-verification/PROVENANCE.md`.
Existing binaries and evidence remain untouched.

D1.6 remains **scientifically closed with qualifications — equilibrium
preservation not confirmed**; see [closure](E1_STAGE_D16_SCIENTIFIC_CLOSURE.md).
Technical acquisition acceptance does not establish a stationary distribution,
general trajectory invariance, terminal relaxation or host throughput.

## Scientific question and compact proposed matrix

Ask how stiffness and the accepted E1 coupling alter finite-time translational,
selected-monomer and orientational curves, and whether T=100 supplies useful
long-lag support. This is curve reconnaissance, not a terminal-dynamics claim.

All cells: N=32 bonds/33 beads, M=256 chains, kBT=zeta=b0=1, kb=30, double
precision, unwrapped coordinates, accepted equilibrium initialization and
unchanged BD-then-hop/renewal dynamics. No stress/rheology acquisition. The
constrained cells retain Z=2048, slip-ms2=5 (effective k_ss=3/5 in these units),
hop-rate=100 and end-renewal=1 as in the
[D1.6B protocol](E1_STAGE_D16B_PROTOCOL_V1.md). There is no new force coupling.
For bare cells Z=0, retain the same supplied spring/hopping/renewal settings;
they have no active springs/events. Record requested versus active settings.

| Cell | Interior kappa | Z | Proposed independent replicas | Proposed dt | Proposed T | Steps per run |
|---|---:|---:|---:|---:|---:|---:|
| A, flexible bare | 0 | 0 | 2 | 0.0001 | 100 | 1,000,000 |
| B, flexible E1 | 0 | 2048 | 2 | 0.0001 | 100 | 1,000,000 |
| C, stiff bare | 10 | 0 | 2 | 0.0001 | 100 | 1,000,000 |
| D, stiff E1 | 10 | 2048 | 2 | 0.0001 | 100 | 1,000,000 |

**Recommendation for review: eight serial runs, two independent replicas per
cell, T=100, dt=0.0001.** These are explicit provisional choices, not a selected
production timestep or authorization. D1.6 completed T100/M256 at both 0.0001
and 0.00025 with four replicas per cell; autocorrelation tails remained
unresolved and the stiff/coarse late-minus-early connector contrast was about
-0.04462 relative to intended equilibrium 5. That experience motivates beginning
with the finer previously explored step and a small cohort. It proves neither
that 0.0001 is accurate nor that T100 reaches terminal relaxation.

Two replicas allow a first check of between-run variation, with only one
variance degree of freedom. They cannot support precise uncertainty or a
confirmatory contrast. Before authorization, assign eight distinct unused seeds
and unique replica IDs, record source/binary identity, all options, and a fixed
cell/replica order. Do not reuse D1.6 runs as dynamical replicas or infer missing
positions/directions from scalar summaries. Comparisons here are unpaired;
different seed labels alone are not proof of independent initialization/RNG.

M=256 means independent backbone interactions in the bare model. E1 has a
global canonical population and cross-chain renewal, so its chain observables
can be correlated. Average chains inside each run and estimate uncertainty
across independent whole-run replicas for **all** cells. Do not multiply the
independent sample count by 256, five monomers, origins or lag bins.

## Observables and interpretation

Prioritize CM MSD, bead-16 absolute MSD, directional C1 and orientational C2.
Retain the existing absolute MSDs for beads 0,8,24,32 and the existing within-chain
end/quarter means and differences. No internal MSD or new observable is proposed.

For each series x, g(tau) is the average of
`|x(t+tau)-x(t)|^2` over the actual retained origin pairs. CM uses all 33 beads.
For u=(r32-r0)/|r32-r0|, fine C1 is `<u(t+tau).u(t)>` and fine C2 is
`<(3*(u(t+tau).u(t))^2-1)/2>`. C1 is not the amplitude-sensitive
`<Re(t+tau).Re(t)>/<Re^2>`; C2 is not a square of C1. End/quarter symmetry
reductions remain within chain, then within replica, before replica uncertainty.

For the bare chain, cancellation of all internal forces gives the translational
reference `D_CM=kBT/[(N+1)*zeta]=1/33`, hence `g_CM(tau)=6*tau/33` in 3D
for the ideal implementation, including the independent-noise EM CM increments.
Recorded noise rounding and floating-point force cancellation qualify actual
finite-precision comparisons. Use this as a reference line, not a newly imposed acceptance threshold or a
nonlinear conformational-relaxation prediction. Spatial anchors exert external
forces on a chain; do not assume 1/33, nonzero terminal diffusion, or even that
T100 reveals a terminal regime for E1. A sublinear/plateau-like curve over this
window is evidence only about that window.

Origin averaging can mix startup evolution with subsequent fluctuations: exact
initial equilibrium does not ensure finite-step stationarity. Treat these as
finite-record curves, retaining sparse scalar/E1 context for interpretation;
do not silently label a pooled curve a stationary correlation or remove an
equilibration window after viewing the data without reporting that choice.

## Acquisition proposal and actual lag support

Use the existing options without changing defaults or adapters:

| Setting | Proposed value / purpose |
|---|---|
| dynamics | 1 |
| dynamics-stride | 100 steps; delta=0.01 physical time |
| dynamics-levels / slots / m | 11 / 16 / 2 |
| dynamics-mib | 256, conservative observer allocation guard |
| dynamics-output | dynamics, compact child directory of each fresh run |
| dynamics-replica | explicit unique whole-run replica ID |
| sample | 5000 steps; existing scalar output every 0.5 time units |
| equilibrium-steps | proposed new schedule 0,100000,...,1000000 (11 frames) |
| equilibrium-snapshots | proposed new schedule 0,1000000 only |

Schedules are a proposal, not files added to a frozen protocol. Endpoint joint
snapshots suffice for a small state record; do not dump coordinates at every
dynamical acquisition. Full-E1 frames provide sparse connector/population/event
context, not an equilibrium reanalysis or a new D1.6 acceptance test. Scalars
have 201 frames. These existing schedules are compatible: all their frames are
on the dynamics clock, allowing shared host readback. No diagnostic event/state
schedule or RNG clock in the integrator changes.

The initialized step-0 state is acquired before the first update. Later frames
read the current coordinate buffer after BD, swap, complete hopping/renewal and
checks, at exactly 0,100,...,1000000: F=10001 frames. No arbitrary final frame is
appended. Shared frames reuse the existing full-coordinate readback; the other
9800 frames add a synchronous readback into the same host vector, followed by
serial CPU consumption. Acquisition can stall the producer; no asynchronous
transport, new GPU gather or worker pool is proposed.

The unchanged [KG/adaptor semantics](E1_STAGE_D2A_CORRELATOR_REUSE.md) imply, for
level k, b=2^k, slot ell, lag=ell*b*delta and actual origin count
`floor(F/b)-ell`. Level 0 exports ell=0..15; coarser exported levels ell=8..15.
The deepest populated level is omitted. Here level 10 receives 9 samples and
is omitted; levels 0..9 export 88 bins, ending at 15*512*0.01=76.8.
The configured lag ceiling 153.6 is **not** an exported lag.

| Example bin | Nominal lag | Origins per chain | Meaning for exploration |
|---|---:|---:|---|
| k0, ell1 | 0.01 | 10000 | Shortest nonzero lag; faster motion is unresolved |
| k0, ell15 | 0.15 | 9986 | End of fine, all-origin support |
| k7, ell15 | 19.2 | 63 | Longest bin meeting both provisional display-support screens below |
| k8, ell8 | 20.48 | 31 | Already below the proposed origin-count screen |
| k9, ell15 | 76.8 | 4 | Sparse tail, descriptive only |

Keep all exported bins with counts. For primary interpretation provisionally
flag lag>T/5 or count<32 as weak support; these screens do not establish
independent origins, effective sample size or a valid fit window. Under this
proposal the primary range ends at 19.2. Long sparse tails cannot justify T100
terminal claims. More levels cannot repair a short record.

Diffusion retains positions `x((j+1)*b-1)` with last-position decimation: direct
squared displacements at the nominal lag, origins spaced b*delta, phase b-1.
Coarse MSD is not a block-averaged-position MSD and not the all-fine-origin
estimate. Orientation instead correlates complete block means of instantaneous
unit and rank-two features, without renormalizing those means. Its lag support
is triangular over `[ell*b-(b-1),ell*b+(b-1)]*delta`. For the 19.2 bin its
half-width is 1.27; for 76.8 it is 5.11. Diffusion has point endpoints, so equal
nominal lags/counts do not imply equal smoothing. Preserve metadata, widths,
integer clocks, actual counts and incomplete-block truncation in any plots.

## Resource planning, not a new benchmark

Review basis: [D1.6 resource plan](E1_STAGE_D16_RESOURCE_PLAN_V1.md),
[D1.6B resource amendment](E1_STAGE_D16B_RESOURCE_AMENDMENT_V1.md), and the
[D2A.2 synchronous cost model](E1_STAGE_D2A2_IMPLEMENTATION_REPORT.md#resources-and-timing).
The recorded development host is RTX 3060 Ti/sm_86 with i7-12700-class CPU;
the matched binaries used CUDA 13.0.88/g++11.4.0. Prior M256 measurements recorded
about 103–104 MiB child RSS, ~1.22 MB explicit device arrays, ~8.07 GB free GPU
and ~31.5 GB available host memory at one pilot observation. These are historical
observations, not current availability or GPU peak measurements. No hardware,
headroom or toolchain probe ran now; availability must be confirmed by the user
before any separately authorized launch. Use one process/GPU run at a time,
with synchronous CPU work on the calling thread; older stress-worker speedups
do not apply to this adapter.

Explicit planning arithmetic, assuming 64-bit Linux sizes (double, pointer,
unsigned long =8 bytes; unsigned int=4):

- Nine Vector-layout payloads per chain (six displacement plus three orientation)
  use `L*[P*(8*8+2*8)+5*8+3*8+2*4]` bytes each: 14872 bytes for L11/P16.
  Across 256 chains their payload is 34265088 bytes (~32.7 MiB), plus objects,
  IDs, offsets and scratch. The observer guards four times its steady estimate
  plus frame scratch and 64 KiB; four times the payload alone is ~130.7 MiB.
  The 256 MiB observer guard leaves room for the additional accounting; the
  actual source preflight remains authoritative. This is not a measured RSS cap.
  Existing aggregate physical-plus-observer guard is 2 GiB.
- One double real4 readback is `256*33*32=270336` bytes (264 KiB).
  Dynamics requires 10001 such frames, ~2.52 GiB cumulative transfer/run;
  201 reuse scalar readbacks and 9800 are additional (~2.47 GiB). The buffer is
  reused, so this is traffic, not resident memory or on-disk trajectory storage.
  Six-plus-three owner input calls total `10001*256*9=23042304` per run before
  recursive coarse promotions; each call also loops over slots. CPU cost is
  unmeasured and may dominate despite small GPU memory.
- At most 88*(256+1)=22616 dynamic CSV data rows/run. A provisional 1200-byte
  row envelope is ~25.9 MiB; reserve 64 MiB for curves/metadata and 256 MiB for
  all run outputs/logs including scalars, sparse E1 frames and endpoints. This
  row width is a planning assumption, not a guaranteed serialization bound.
  Eight run allowances total 2 GiB; no compression gain is assumed.

Existing T1/M256/Z2048/dt0.0001 production measurements were 1.395845 s at kappa0
and 1.676938 s at kappa10. Multiplying by 100 gives old acquisition-cost proxies
of 139.6/167.7 s per constrained T100 run, ~615 s for the four constrained runs.
This over-repeats some fixed costs and omits the new 10001-frame CPU consumption
and readbacks. It is not a bound, prediction of the new runtime, or a bare-chain
benchmark. Bare-chain cost and new acquisition/export overhead are unmeasured.
The older ~34.3-minute D1.6B sixteen-run proxy is likewise a historical planning
quantity, not D2A.3 performance evidence. Timers have nested scopes; do not add
integration, production, observation and acquisition timers as independent costs.

For review, propose ceilings of 600 s/run, 2 GiB child RSS, 256 MiB/run output,
2 GiB total cohort output and 7200 s total session, running serially. Require
at least 8 GiB available host headroom, 4 GiB free GPU and 10 GiB maintained
free disk; retain the prior conservative 18 GiB initial-disk allowance plus
separate source/build storage. These borrow planning scales from D1.6B without
changing its contract. **No new enforcement software or approval is created.**
Existing adapter guards cover allocation estimates, not OS RSS, runtime or disk.
The operator must agree how to enforce the proposed execution ceilings before
authorization. A limit breach preserves partial output and returns for review;
it does not justify automatic retries, reduced acquisition or extended budgets.

## Minimal postprocessing plan, not implemented or run

Use existing per-chain and per-replica CSVs and dynamical metadata; successful
exit and valid completion metadata are prerequisites, not scientific acceptance.
Check common model/grid/clock support, expected frames/counts, unique replica IDs
and complete files before combining compatible runs. Retain raw outputs and
individual replica curves. No new analysis framework is needed.

1. Plot log-log CM and bead-16 MSD against nominal lag, excluding lag zero from
   logarithms. Show replicas faintly, equal-weight replica means prominently,
   and replica SE where defined. Add the bare `6*tau/33` reference line only to
   bare-control interpretation. Identify fine versus decimated bins and weak
   support, rather than connecting all bins as uniformly precise observations.
2. Plot directional C1 and P2 C2 against lag, allowing negative values (linear
   ordinate). Show fine and block-averaged portions distinctly with block-width
   metadata. Do not force a single exponential, positive tail or terminal zero.
3. Optionally compare center, within-chain averaged ends/quarters and symmetry
   differences, using the already exported quantities. No independent monomer
   error bars. Preserve separate bead curves for diagnostic inspection.
4. Where MSD is positive and support adequate, show provisional finite-difference
   `alpha=d(log g)/d(log tau)` within a level or an explicitly comparable support
   segment. Do not differentiate across coarse-level joins without labeling the
   estimator change. Compute slopes per replica before summarizing variation;
   nearby slopes are correlated. Likewise `g_CM/(6*tau)` is only a provisional
   effective diffusion ratio until terminal behavior is supported.

For R replicas, SE of the mean curve is
`sqrt(sum_r (g_r-g_mean)^2/[R*(R-1)])`; R=1 means unavailable, never zero.
At R=2 this uncertainty is fragile and does not certify Gaussian intervals.
No bootstrap of origins/chains, simultaneous confidence bands or post-selected
discovery claims. These are exploratory comparisons with no prespecified
confirmatory test family. No relaxation time is borrowed from the unresolved
D1.6 autocorrelation tails.

A candidate terminal translational regime would need a sustained near-one MSD
slope over a substantial lag range, stable effective diffusion across neighboring
adequately supported windows and independent replicas, and no material shift
when the time horizon and timestep are separately checked. Orientational decay
must also have adequate temporal support; it is not by itself proof of CM
diffusion. Fit windows are not selected from future confirmatory data here.
If these conditions are absent, report terminal D or relaxation time as
**unresolved**, describe the observed intermediate-time regime, and recommend
review of a longer record. Do not fit a terminal coefficient merely because a
straight segment or a few long-lag points exist.

## Review decisions and preparation report

The recommendation is the matrix above with delta=0.01 and L11/P16/m2, not a
launch instruction. Independent review must settle the provisional dt/T/R,
eight new seeds/IDs and run order, host resource availability and ceiling
enforcement, sparse schedules, output roots and accepted binary provenance.
Use fresh permanent directories, preserve failed/partial runs and prior evidence,
and do not reuse frozen D1.6 runners/manifests as authority for D2A.3.

Timestep sensitivity remains an explicit interpretation limitation. A possible
later separately reviewed comparison would halve dt to 0.00005 at equal physical
duration/cadence (stride 200), especially for constrained/stiff dynamics; it is
not part of this first eight-run proposal or authorized now. Neither the two
D1.6 timesteps nor the first D2A.3 curves establish a zero-step extrapolation.
Longer duration, more replicas, finer acquisition or timestep comparisons require
review of what the initial curves actually resolve, not automatic extensions.

This preparation changes only this design, README links/current acceptance
wording, and PROJECT_STATUS. It adds no code, seed manifest, launch command,
measurement infrastructure, test or build target. Existing implementation and
historical verification records remain intact. Documentation/source inspection
and Git housekeeping are the only actions performed; arithmetic above is
planning, not an executed numerical analysis. Forces, RNG, initialization,
hopping, renewal, integration, KG arithmetic, adapters, frozen evidence and D0
criteria are unchanged. No internal MSD or D2B alternative coupling is proposed.
Stop for independent scientific review and separate authorization of any first
exploratory simulations.
