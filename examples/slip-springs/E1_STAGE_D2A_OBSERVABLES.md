# D2A.0 — dynamical observables and estimators

Planning only, 27 October 2026. No implementation or scientific computation.
D1.6 remains **scientifically closed with qualifications — equilibrium
preservation not confirmed**; see [closure](E1_STAGE_D16_SCIENTIFIC_CLOSURE.md).
The accepted dynamics and historical evidence are unchanged.

## Coordinates and direct reference estimators

For N=32 bonds, m=33 equal-friction beads, use immutable chain/bead IDs and
selected beads I={0,8,16,24,32}. For replica r, chain c and acquired frame n,

    R_c(n)=(1/33)*sum_(i=0)^32 r_ci(n),
    rho_ci(n)=r_ci(n)-R_c(n), E_c(n)=r_c32(n)-r_c0(n),
    u_c(n)=E_c(n)/|E_c(n)|.

All r and R are unwrapped laboratory Cartesian coordinates. Do not subtract
the instantaneous center of mass from an absolute/translational observable.
One fixed coordinate offset per time series is harmless for displacements;
a different offset at each frame changes the observable. Zero/nonfinite E has
undefined direction: fail/report the complete invalid frame, following the
orientation adapter, rather than skipping it or choosing an arbitrary direction.

Acquire a uniform integer clock step_n=step_first+n*stride, physical spacing
delta=stride*dt. For F frames and integer lag ell, let O_ell={0,...,F-ell-1}
and n_ell=F-ell. For any vector series x define the direct reference

    MSD_x,c(ell)=(1/n_ell)*sum_(n in O_ell)|x_c(n+ell)-x_c(n)|².

Do not produce an estimate with zero pairs. For an explicitly restricted origin
window, use its actual valid pair set and count; no interpolation across missing
frames or shortened final intervals. This finite-record definition needs no
stationary position distribution. Interpreting it as a function of lag alone
requires time-homogeneous increments over the chosen observation segment.

| Observable | Vector x / estimator | Units and normalization |
|---|---|---|
| Center-of-mass MSD | x=R_c | Length squared; sum all three Cartesian components, no division by 3 |
| Absolute selected-bead MSD | x=r_ci, separately for i in I | Length squared, laboratory displacement |
| Internal selected-bead MSD | x=rho_ci, separately for i in I | Length squared, displacement relative to each endpoint's instantaneous chain CM |
| Directional C1 | mean_(O_ell) u_c(n) dot u_c(n+ell) | Dimensionless; C1(0)=1 on valid fine frames |
| Orientational C2 | mean_(O_ell) [3*(u_c(n) dot u_c(n+ell))²-1]/2 | Dimensionless P2 correlation; C2(0)=1; do not square an averaged C1 |

Internal MSD is not absolute MSD minus CM MSD for an individual selected bead:

    |Delta r_i|²=|Delta R|²+|Delta rho_i|²
                 +2*Delta R dot Delta rho_i.

The cross term can be nonzero, particularly in E1. Only an average over **all
33 beads**, with identical pairs, cancels it identically because sum_i rho_i=0.
Averaging five selected beads does not have that identity. An internal plateau
would approach 2*<|rho_i|²> if internal mixing and zero mean have been justified;
this is not an assumption that such a plateau is reached in T100.

## Three different end-to-end correlations

Also distinguish the optional amplitude-sensitive dot correlation

    G_E(ell)=mean_(O_ell) E(n) dot E(n+ell),
    C_E(ell)=G_E(ell)/G_E(0).

Here G_E(0) is the full specified segment's mean E², with its own count and
normalization recorded. This is a stationary-amplitude convention, not an
identity for arbitrary nonstationary end-to-end lengths. Report G_E and the
denominator separately if included; it is not a primary D2A.0 requirement.
Neither G_E nor C_E equals the directional C1 in general, because vector length
fluctuates. C2 is the second Legendre polynomial of each **pair's directional
dot product**, not P2(C1), C1², or a normalized E² time correlation.

The existing adapter forms the five instantaneous features

    t(u)=(sqrt(3)*ux*uy, sqrt(3)*ux*uz, sqrt(3)*uy*uz,
          sqrt(3)/2*(ux²-uy²), (3*uz²-1)/2),
    t(u) dot t(v)=P2(u dot v).

Reuse that validated contraction unchanged. No density, stress weighting,
temperature prefactor, empirical mean subtraction or fitted plateau belongs
in C1/C2. Any connected correlation would be a separately named observable.

## Symmetry and statistical unit

Retain the five separate selected-bead curves. Form end=(MSD_0+MSD_32)/2 and
quarter=(MSD_8+MSD_24)/2 **within each chain and replica**, using matched pairs.
Retain differences MSD_0-MSD_32 and MSD_8-MSD_24 as symmetry diagnostics for
both absolute and internal MSD. Center bead 16 is its own category. Do not turn
the two ends into two independent uncertainty samples.

For each replica first average chain curves with equal chain weights on a
common valid grid, then estimate uncertainty across independent replicas:

    Y_r=(1/M)*sum_c Y_rc,
    mean Y=(1/R)*sum_r Y_r,
    SE=sqrt(sum_r(Y_r-mean Y)²/[R*(R-1)]), R>1.

The SE is nominal replica uncertainty, not a simultaneous confidence band;
R=1 gives unavailable uncertainty, never zero. Preserve replica curves and
actual counts. E1's canonical population/renewal exchange couples chain histories,
even though the annealed equal-time backbone marginal factors. Chain-based SE
is not justified by that marginal. Bare chains with Z=0 and independent
initialization/noise have a physical chain-independence argument, but independent
trajectories remain the primary comparison units. Lag bins and overlapping
origins are correlated; pair count is support metadata, not effective sample size.

## Diffusion and comparisons: proposed interpretation criteria

Compare bare Z=0 versus unchanged current E1, kappa=0 versus 10, at matched N,
backbone parameters, precision, physical acquisition grid and observation phase.
Keep dt=.0001 and .00025 as D1.6-context comparison levels, not newly accepted
production timesteps. Independent cells are unpaired unless pairing was genuinely
designed; do not retrofit paired uncertainty. No run matrix is authorized here.

The bare control requires Z=0: turning hopping or renewal off with Z>0 retains
anchor forces. For Z=0 the translationally invariant backbone forces sum to zero,
giving D_CM=T/(33*zeta) in ideal arithmetic, independent of kappa. The ideal
bead EM CM update also has the corresponding free Brownian increments. This is
a useful analytical reference, not a new measured coefficient or proof of
internal/terminal relaxation. E1's anchor forces remove that CM cancellation.

A long-time diffusion coefficient would satisfy MSD_CM(tau)~6*D_CM*tau in 3D.
Require a supported range of several lags with approximately unit log slope,
stable MSD/(6*tau) and stable slope estimates under reasonable adjacent-window
and early/late-origin sensitivity. Do not force a finite-window intercept to zero
without justification. Short-time overdamped Brownian motion can also have unit
slope: check that internal MSDs have resolved saturation and orientation has
resolved decorrelation, and that selected absolute MSD slopes become compatible
with CM slopes. These are supporting diagnostics, not a guarantee of terminality.

No fixed terminal time, fitting interval or relaxation time is supplied. Before
inference, review/fix minimum lag/pair and replica support and stability budgets
using a separate exploratory/design stage; freeze confirmatory choices before
future confirmatory data. Never select a favorable fit and call it prespecified.
For an exploratory display a lag cap such as duration/4 is conservative support
bookkeeping, not an independence or terminal-relaxation theorem. If there is no
stable, adequately supported long-time regime, report D_CM as **unresolved** and
show the finite-lag curves/effective slopes. T100 and D1.6's unresolved tails do
not establish terminal relaxation. Carry the equilibrium/timestep qualification
into subsequent physical interpretation; do not reopen D1.6 here.
