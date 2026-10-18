# Stage 4A.3c stress temporal-resolution audit

18 October 2026, Europe/Madrid. Documentation development starts at
`87bc14063c432b5b7a78b2da8c9661f14c5996e3`, on `slip-springs` in the separate
`/tmp/UAMMD_KG-slip-springs-dev` worktree. The absolute execution checkout
`/tmp/UAMMD_KG-slip-springs` remains clean and detached at the pinned
`4e46d6014aa812b1fc687335654c4b1f681ddd22`. No binaries, source, analyzer,
protocol, manifests, provenance, thresholds or existing outputs were changed.
No simulations, builds, campaign generation or checkpoint-writing analysis ran.

**Finding:** the original cadence0.01 structurally excludes every terminal-
eligible bin for the measured N8,kappa0 curves. Longer trajectories cannot fix
that condition. **Additional finding:** cadence alone is not sufficient: with
32 slots, cadence0.001 restricts eligible lags to0.124, while the measured curve
only approaches10% near0.15. The prospective design must address both early
acquisition and the range of narrow-block correlations.

**Recommendation:** investigate a common nonlinear cadence0.001 with64 slots,
using0.0005 dense reference acquisitions to establish adequacy. This is a
candidate, not a frozen amendment or execution authorization. N32 tails and
kappa2 dynamics are unmeasured here;64 slots is not a universal guarantee.

## Available evidence and authentication

The supplied `/tmp/semiflexible-compact-host.CCBNa7/compact-v1` is accessible.
Read-only authentication used the **original execution checkout's** Python
modules with bytecode writing disabled. Authentication from the development
path rejects the generated `commands_reference_analysis.sh` absolute paths;
no script or guard was changed to bypass that protection.

The saved analysis snapshot is `2026-10-18T13:06:56.548499+00:00`. Its canonical
manifest identity remains
`d81fee5eddc52a8b2f1bf9190bda26c19808168b21030116684cd68ee05ecf1f` and its
analyzer version matches the pinned implementation. Snapshot file SHA256s:

| File | SHA256 |
|---|---|
| manifest.json | `7b16928c75e8ea00e0aa9ef2e5561107a2bf05f9ffc8a98c95d35ad40ecd142f` |
| scientific-analysis.json | `5bf1651e72f97768c2a5415725f7254a894fbe0f68e732ff48a4bfdc2a9d745a` |
| analysis-checkpoint.json | `6a3a394ac0ee0c73892da795dbfb84c4530cfb942052b6227f683c9cbb3b68f4` |
| validation-plan.md | `efd040ceba8cd903dee7a145296dce08435e3df3efa940c65170f4bcf98acb36` |
| campaign-provenance.json | `81f6bf3e7e8949e099c324a17d516fd683335470c6d768f41b3cf58231442950` |

For the four completed nonlinear streams inspected below, all receipted files
were SHA256-verified:38,946,320 bytes including external logs/monitoring.
`correlation_rows()` independently reread their normalized/raw tables, checked
lag/block/pair counts and normalizations, and reproduced saved rows exactly.
Calling `terminal()` reproduced all four saved outcomes. No trajectories were
replayed and no raw scalar history was reconstructed.

All four are single precision, seed433201,C2048,N8,b0=1,kb30,kBT=zeta=1,
T200,cadence0.01,levels20,slots32,coarsening2,workers4,batch32:

| kappa | dt | H(0) | tau_e | Pointwise6SE crossing bracket | Terminal result |
|---|---:|---:|---:|---|---|
| 0 | 0.0001 | 25.1085674 | 0.0224142811 | [0.0221575644,0.0226706896] | insufficient_support |
| 0 | 0.00005 | 25.0709072 | 0.0224486068 | [0.0221905788,0.0227063777] | insufficient_support |
| 0 | 0.000025 | 25.0446642 | 0.0224778885 | [0.0222180695,0.0227374727] | insufficient_support |
| 10 | 0.000025 | 27.1075558 | 0.1005591501 | [0.0977711791,0.1035735941] | passed |

The kappa10 row is the completed pilot, not a completed timestep/seed/precision
matrix. No completed kappa2,N8 stream or N32,kappa0/2/10 stream was found.
Existing diagnostic/direct-reference evidence is not substituted for those
missing production-duration measurements. Original compilation-transcript
provenance remains missing, as described in the Gaussian audit.

## Exact terminal-support diagnosis

Sources: [frozen plan](STAGE4A3C_VALIDATION_PLAN.md), gate7;
[analyzer](tests/semiflexible_stress_analysis.py), `terminal`, `lag_grid`;
[correlator adapter](stream_correlator.h), `Bank::write`.

`terminal()` uses the first linearly interpolated crossing of H(0)/e, with
pointwise mean+/-6SE crossing brackets. Eligible bins require origins>=16 and
block_samples*Delta<=tau_e/4. It then requires:

1. An eligible maximum lag at least2*tau_e; choose the nearest eligible bin
   to2*tau_e and require H>3SE there.
2. At least one eligible lag **strictly greater** than4*tau_e satisfying
   |H|/H(0)<=0.1+6*SE/H(0).

Every block has at least one original frame. Hence Delta<=tau_e/4 is necessary.
For kappa0, tau_e/4 is0.005604–0.005619; even the upper crossing brackets divided
by4 are below0.005685. Delta0.01 makes the eligible set empty. This explains
the exact reason `no supported bin near twice tau_e`, independently of chain
count or duration. It is not evidence of an incorrect stress calculation.

The dyadic lag grid adds a stronger range constraint. With P slots, fine bins
have lag j*Delta,j=0..P-1. Higher levels use block B=2^l and j=P/2..P-1,
lag j*B*Delta. For F observations each bin has
O=floor(F/B)-j origins. Subject also to exported-level availability, let

    Bmax = largest power of two with Bmax*Delta <= tau_e/4.

Without finite-duration restrictions, the largest eligible lag is
(P-1)*Bmax*Delta. It must exceed4*tau_e; width eligibility alone is insufficient.
The origin condition further restricts j<=floor(F/B)-16. Approximately,
reaching4*tau_e at width w requires T>=4*tau_e+16*w, plus grid/floor margins.
All checks must use the actual exported grid, including its deepest-level
omission and any configured level cap, not just these approximate inequalities.

For P32, w is in (tau_e/8,tau_e/4], so maximum eligible lag ranges from just
above3.875*tau_e to7.75*tau_e. A narrow dyadic range can even miss4*tau_e.
More generally a multi-component stress curve may not reach10% within that
eligible range at all. P64 approximately doubles the accessible range at a
fixed permissible block width; it does not change the width/pair criteria.

Using the finest measured kappa0 tau_e, existing `lag_grid()` gives:

| Delta | Largest eligible lag, P32 | Largest eligible lag, P64 |
|---:|---:|---:|
| 0.01 | none | none |
| 0.005 | 0.155 | 0.315 |
| 0.002 | 0.124 | 0.252 |
| 0.001 | 0.124 | 0.252 |
| 0.0005 | 0.124 | 0.252 |

These are mathematical eligibility ranges at T200, not predictions of new
measured tau_e or a promised pass. More sampling with P32 can move the dyadic
width below0.005 and shorten its eligible physical lag range. Longer runs do
not extend (P-1)*w when width is already the binding restriction.

## What the measured curves resolve

Selected stored ratios, finest dt; parentheses give marginal chain SE/H(0),
not a propagated ratio error including the random denominator:

| Lag | kappa0 H/H(0) | kappa10 H/H(0) |
|---:|---:|---:|
| 0.01 | 0.58300 (0.000315) | 0.75506 (0.000698) |
| 0.02 | 0.39202 (0.000306) | 0.65176 (0.000693) |
| 0.03 | 0.29460 (0.000299) | 0.58616 (0.000687) |
| 0.10 | 0.13110 (0.000255) | 0.36889 (0.000651) |
| 0.12 | 0.11635 (0.000250) | — |
| 0.13 | 0.11018 (0.000247) | — |
| 0.14 | 0.10470 (0.000243) | — |
| 0.15 | 0.09983 (0.000241) | 0.29245 (0.000622) |
| 0.20 | 0.08125 (0.000233) | 0.23982 (0.000594) |
| 0.50 | 0.04102 (0.000200) | 0.10049 (0.000482) |
| 1.00 | 0.02318 (0.000166) | 0.04617 (0.000410) |
| 2.00 | 0.01074 (0.000137) | 0.02331 (0.000373) |

Lags through0.31 are unblocked B1;0.50 uses B2,1.00 B4,2.00 B8. Coarse rows
are correlations of block means, not instantaneous point-lag correlations.
At lag0.14 the kappa0 ratio exceeds its frozen allowance0.1+6SE/H0≈0.10146;
at0.15 it meets it. Thus existing observations place a qualifying late row near
6.7*tau_e, although4*tau_e is only0.08991. No single exponential is assigned.
The table makes it **likely**, not independently proved for unobserved times,
that Delta0.002/0.001/0.0005 with P32 would still lack a qualifying late bin:
their maximum0.124 falls between stored0.12/0.13, both above the threshold.

For kappa10, the pilot has a clear crossing near0.10–0.11. The analyzer selects
positive lag0.20 (H6.50098,SE0.01611,O19981,w0.01) and late lag0.50
(ratio0.1004903,O9975,w0.02), below its allowed ratio≈0.10289. Width0.02 is
less than tau_e/4≈0.02514. Its terminal pass is meaningful for that pilot only.

Kappa0 loses about42% of H before the first nonzero lag; kappa10 loses24.5%.
The existing data give sampled operational e-fold estimates, not a resolved
sub-0.01 spectrum. Small crossing SE brackets exclude interpolation error,
cross-lag covariance and model-form uncertainty; close dt estimates do not
establish convergence order or temporal-acquisition convergence. Independent
chains remain statistical clusters; neither time origins nor lag bins become
independent samples. No tail fit, viscosity extrapolation or tau_max estimate
was performed.

## Physical scales: estimates, not a substituted model

The actual Hamiltonian is harmonic in bond **length deviations**, plus
kappa*(1-u dot v); it is not a Gaussian Rouse chain. The following estimates
derive from local linearizations and equilibrium reference functions, not new
dynamic simulations. The [CPU reference](semiflexible_reference.py),
`radial_moments` and `langevin`, supplies the exact equilibrium conventions.
For kb30,b0=1,theta=zeta=1, mean length≈1.06452, mean square≈1.16452.

* **Stretching:** for an isolated bond, relative mobility is2/zeta. Linear
  radial displacement relaxes at rate2*kb/zeta=60, time0.0167. The radial
  Jacobian gives effective potential kb(r-b0)^2/2-2*theta*log(r), increasing
  local curvature to kb+2*theta/r²; this is an additional local approximation.
  Stress contains a linear kb*b0*delta-r term and quadratic fluctuations, so
  it is incorrect to universally halve the bond-amplitude time. As a different
  limiting calculation, a straight unstrained longitudinal chain has eigenrates
  4*kb*sin²[p*pi/(2M)]/zeta: fastest amplitude times0.00859 (N8),0.00835 (N32),
  slowest0.276/3.681. A purely quadratic modal stress can decay twice as fast,
  giving short contributions around0.0042. Random orientations, prestress and
  coupling alter this spectrum; these are not bounds on the nonlinear system.
* **Bending:** near a straight chain with spacing l, transverse displacements
  have energy kappa/(2*l²)*sum|x_(j+1)-2*x_j+x_(j-1)|². With the second-
  difference matrix E the Hessian is(kappa/l²)*E^T E. Its largest eigenvalue is
  at most16*kappa/l² in this linearized model. At l≈1 the corresponding fast
  amplitude scales are0.0313 (kappa2) and0.00625 (kappa10); quadratic stress
  components may have scales0.0156 and0.00313. A single isolated angle has
  curvature factor6*kappa/l², giving different local scales0.0833/0.0167.
  Neither estimate is the e-fold time of total chain stress. Small-angle theory
  is especially crude at kappa2. Equilibrium tangent factors L(2)=0.5373 and
  L(10)=0.9000 imply persistence lengths1.61/9.49 bonds, respectively.
* **Collective motion:** near-straight bending amplitudes scale roughly as
  zeta*l²*N^4/kappa; whole-chain rank-two rotational relaxation for a rigid rod
  is zeta*l²*M*(M²-1)/(72*theta), about11.3 (N8) and565 (N32). A flexible,
  long-wavelength entropic coarse-graining at kappa0 gives a heuristic slow
  stress scale zeta*mean(r²)/(24*theta*sin²[pi/(2M)]), about1.61/21.4.
  These are contrasting limiting estimates, not assigned terminal spectra or
  upper/lower bounds. None is identified with the observed tau_e≈0.0225.
* **Total stress:** H includes stretch/stretch, bend/bend and both cross terms.
  They can have different amplitudes and signs. Stronger bending can accelerate
  local transverse restoring motion while making chains more extended and
  slowing collective orientation. Here kappa10's measured e-fold time is about
  4.47 times kappa0's, not shorter. Compact total-stress streams do not separate
  dynamic cross correlations; static diagnostic tensor decomposition cannot
  recover their time dependence.

Inverse bond lengths preclude a universal fastest-timescale bound: the radial
distribution extends to arbitrarily small positive r. Minimum sampled lengths
were0.0762 (finest kappa0) and0.0973 (kappa10), not all-step minima. Near-small
active bonds can have far larger local curvature than estimates using l≈1.
No finite cadence resolves all Brownian fluctuations; the practical target must
be resolution of stress contributions of appreciable weight, verified by dense
data, while retaining the existing finite/collapse diagnostics. This audit does
not propose changing dt, force regularization or Euler–Maruyama.

## Candidate cadence and resource decision table

All intervals below are integer multiples of every frozen nonlinear dt; e.g.
Delta0.001 has strides10/20/40. Physical durations stay T200 (N8) and T4000
(N32). Frequency multiplier R=0.01/Delta. D2H figures are decimal GB of **six
stress doubles only**, computed as48*C*(floor(T/Delta)+1), not disk output.

| Delta | Frames per measured kappa0 tau_e | R | Stress D2H GB: N8 / N32 | Assessment with prospective P64 |
|---:|---:|---:|---|---|
| 0.01 | 2.25 | 1 | 1.97 / 39.32 | Fails width criterion regardless of slots |
| 0.005 | 4.50 | 2 | 3.93 / 78.64 | Width feasible; early fast stress remains coarse; P32 late range marginal |
| 0.002 | 11.24 | 5 | 9.83 / 196.61 | Useful intermediate; only≈1.6 samples per0.0031 local estimate |
| 0.001 | 22.48 | 10 | 19.66 / 393.22 | Leading common candidate;≈3.2 samples per0.0031 local estimate |
| 0.0005 | 44.96 | 20 | 39.32 / 786.43 | Dense reference/candidate if0.001 inadequate;≈6.3 samples per0.0031 |

These sample/time ratios are heuristics, not Nyquist guarantees for stochastic
non-bandlimited signals. Delta0.001 is not yet demonstrated sufficient for
kappa10 fast stress. If0.0005 is itself questionable, a very short0.0001
reference at the finest dt can test the earliest decay without changing EM.
This is not a proposed0.0001 production cadence: retaining the N32 long-lag
range at that spacing would require a separate level-cap and memory-budget
assessment, not merely changing the stride in the20-level setup.

Existing `observe()` also transfers full positions and computes **all** scalar
observations at each stress frame. Single-precision coordinate traffic is3 times
the stress traffic for N8 and11 times for N32; add the stress traffic to obtain
4x/12x totals. Double precision gives7x/23x totals. Stress failure-key transfers
and unchanged per-step integration diagnostics are additional. CPU conformation
work scales roughly as C*N*frames; correlator work approximately as C*P*frames,
with amortized dyadic levels. Reducing scalar serialization does not remove
these costs; reducing stress frequency to improve benchmarks is not proposed.

Measured kappa10 pilot timers: integration286.497s, production351.511s,
stress GPU2.023s,D2H0.153s,stress wait/diagnostic2.069s,CPU bank wall15.139s,
scalar observation17.051s. GPU/wait scopes overlap; do not add all timers.
An explicitly crude budget I+R*(production-I), attributing all nonintegration
production work to observations, gives P32 totals417/612/937/1587 seconds for
the four finer cadences. Doubling P and adding R*15.139s gives P64 budgets
447/687/1088/1890 seconds. These are **unmeasured forecasts**, not wall-time
bounds or speed claims: cache, scheduling, barrier, fixed overhead and hardware
contention can change them. N32 cannot be timed reliably by these N8 numbers.
Future runs must still report integration and production ns/bead/step separately.

At fixed topology, workers, batch, P and levels, GPU/host allocations do not grow
with frame count. Current stress GPU capacity is262,152 bytes and pinned batch
3,145,728 bytes. Estimated host+GPU observer capacity is240.75MiB at P32,
470.75MiB at P64,930.75MiB at P128 (C2048,levels20). The P64 correlator bank
itself remains within512MiB; P128 would require an explicit larger budget.
These are source-formula allocation estimates, not process RSS measurements.

Compact N8 main output measured about9.64–9.74MB. Its five selected scalar
frames, per-chain summaries, stress moments and bond histograms remain bounded
at fixed C,N; only the number of exported correlation bins grows slowly with
duration/frame count and P. At T200, P32 bin counts for the four candidates are
195/216/232/248; P64 counts359/400/432/464. Output is not multiplied by R as a
full raw history would be. No precise new total MB is claimed. N32 bond records
scale with N. Monitoring/log bytes grow with wall time. Optional raw stress
dumps scale with frames: an existing N8 reference averaged126.67 bytes/chain/
frame, so even short dense diagnostics need explicit disk limits.

## Multi-resolution and long-time acquisition

The existing estimator already is multi-resolution: uniformly acquire every
fine instantaneous stress frame, then form nonoverlapping dyadic block means.
The configured20 levels cover the proposed N8/N32 durations, but retained bin
widths, counts and the finite level cap must be enumerated for each proposed
system. A smaller Delta does not require retaining trajectories or changing EM.
An unchanged32-slot bank can still fail the narrow-block late-support condition;
64 slots is available through existing CLI parameters but changes the lag grid
and compute/memory footprint and must be versioned explicitly.

Long-time support is not automatic even at T4000. As a **hypothetical** check,
if N32 had tau_e565 (the rod estimate, not a measurement), the largest eligible
lag with P32 is2539.52 at Delta0.005, but2031.616 at0.002/0.001/0.0005;
the latter cannot reach4*tau_e2260 with16 origins. The fine grids put their
next coarser block beyond the origin allowance. P64 can supply longer lags at
smaller block width. If actual supported signal lies beyond the available
duration, a separately reviewed duration extension is required; this audit
does not shorten T, assume a rod spectrum or guarantee any terminal pass.

Alternatives to uniform fine acquisition include a dense short diagnostic
ensemble plus the unchanged coarse long ensemble. That combination can study
early dynamics, but it cannot retroactively give coarse runs narrow-block late
origins or merge their correlations into the same frozen estimator. A single
run with changing sample cadence is unsupported by the current uniform-spacing
correlator and analyzer. Sparse sampling of instantaneous stress is also not
the same as averaging every fine stress sample into a coarse block. A custom
multiple-clock acquisition or stitching scheme would require a separate theory,
implementation and validation; it is not the minimum change here.

## Minimum evidence before a prospective acquisition V2

Prefer a **common nonlinear cadence and lag layout** across N8/N32,kappa0/2/10,
all dt and both precisions. This simplifies physical-time comparisons and avoids
choosing model-specific settings from noisy tau estimates. Keep Gaussian-control
cadence and its exact-discrete checks explicit and separate. If a common design
is prohibitively expensive, model-specific schedules need the same resolution
and terminal-support evidence, not an assumption that high kappa relaxes faster.

Before freezing any revised protocol, separately authorize these limited user-
host measurements; none was performed here:

1. Dense total-stress diagnostics at Delta0.0005, finest dt, for all six
   N8/N32,kappa0/2/10 combinations, one fixed seed initially. A starting
   C256,T2 acquisition with raw six-channel output is a bounded **proposal**,
   about1,024,256 rows/model (roughly130MB using the measured CSV row size).
   It tests early decay, not long-time acceptance; extend only if crossings or
   early comparisons remain unresolved. Include a second independent seed and
   the other precision on the fast/extreme cases before generalizing a design.
2. From each dense history, compare instantaneous decimations to0.001,0.002,
   0.005 using exact schedules, direct correlations and per-chain paired errors.
   Do not replace decimation by block averaging. Match physical lag/block
   windows where possible and separately examine acquisition-dependent origins.
   Measure initial losses, crossing/interpolation shifts, H0, early curvature,
   and low-amplitude late shoulders. Predefine the proposed comparison gates
   before running these diagnostics; this audit adds no acceptance thresholds.
3. Enumerate actual proposed lag grids and recompute eligible widths/origins for
   measured tau brackets. Confirm a positive bin near2*tau and a qualifying
   late bin within the permitted width, using the same frozen conditions. P64
   is a justified first candidate for the observed kappa0 shoulder; assess
   larger P or reviewed extra duration only when measurements require them.
   T2 diagnostics cannot establish N32 terminal coverage. Independent long
   nonlinear support evidence remains necessary at the original T200/T4000.
4. Measure representative N32 and active-bending observation/worker cost, RSS,
   transfer volume and output growth. Verify replay invariance across cadence
   choices: force/update/RNG/initialization and integration step count stay fixed.
   Do not extrapolate a long-run speedup from a tiny diagnostic.

The present total streams cannot identify separate dynamic stretch/bend cross
terms. If their separate spectra are needed to justify adequacy, seek a narrowly
authorized diagnostic extension or independent CPU experiment before using them;
no such extension is implemented or required to reinterpret stored total H.

Any eventual **acquisition V2** must be a separately reviewed scientific-protocol
amendment with a new plan/version identity, commands, outputs, receipts and
analysis provenance. It must state cadence, slot count, frame/origin grids,
direct-reference durations, unchanged normalizations and preserved numerical
gates. Fixed8193-frame reference runs would have shorter physical coverage at a
finer cadence; explicitly retain their physical coverage or justify a new direct
test design. Memory comparisons also need matched new cadences. All old results
and their insufficient-support classifications remain authentic and unchanged;
none may be adopted into V2 as if acquired on the new schedule.

No revised protocol should be frozen yet. The empirical kappa2/N32 early and
late structure,0.001-versus0.0005 resolution, any required larger P, and actual
resource cost remain open. No new integrator, Heun step, exact Gaussian
propagator, stress model, slip-spring interaction or production execution is
proposed by this documentation change.
