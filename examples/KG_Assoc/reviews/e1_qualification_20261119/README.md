# Formal E1 qualification for non-associating initialization

All 24 original E1 states are **accepted with qualification** for direct
initialization at the established finite-step KG protocol (WCA, permanent FENE,
GJF bath T=1, friction 0.5, dt=0.01). The decision applies to the eight exact
triplets under `acceptances/`. Each identity is
`e1_direct_nonassoc_initialization_20261119_v1/<geometry>`:

| Geometry | Judgment for r001–r003 |
|---|---|
| F03_N010_RP080 | Accept. Weak positive Rg² slopes and about 0.59% r001–r002 late separation qualify the plateau evidence. |
| F04_N010_RP020 | Accept. Close late agreement in both shape observables, temperature and pressure. |
| F04_N010_RP040 | Accept. Close late agreement in both shape observables, temperature and pressure. |
| F04_N010_RP060 | Accept. Weak Rg² trends retained. r002 uses the registered attempt001 after the original failure. |
| F04_N010_RP080 | Accept. Small late shape variations across families. |
| F04_N020_RP080 | Accept. The first-block swelling subsides. Late Rg² trends have opposite signs in r002 and r003. |
| F04_N040_RP080 | Accept with lower confidence. Late shape means agree within the audit's heuristic uncertainty after a shared early transient. |
| F06_N010_RP080 | Accept. Close late agreement in both shape observables, temperature and pressure. |

The records contain each replica's exact resolved path, hashes, numerical checks,
original command and retained input provenance, paired associating systems, and
late-window temperature, pressure, Rg², and center-to-terminal distance statistics.
The snapshot checks cover finite coordinates/velocities, permanent FENE lengths,
input and final geometry, and stable atom/molecule IDs and permanent topology.
The registered RP060/r002 failure files retain their original hashes. Ten old
records lack launch-time input and executable hashes. The other fourteen record
both. The current E1 executable has different bytes from the recorded preparation
build, so the manifest reports the historical digest without claiming a fresh
authentication of those binary bytes.

The E1 windows show stable temperature and pressure (maximum half-window changes
0.0251% and 0.0760%). Late on-site kinetic temperatures of 0.979–0.989 are consistent
with the GJF integer-time velocity estimator. The original force-based half-step
reconstruction averaged 0.999659. The endpoint configurational-temperature proxy
averages 1.01280 and lacks a time series and a smaller-timestep comparison. That
question remains open for continuum accuracy. For the stated initialization
criterion, the control uses the same thermostat and timestep as final E1, and
the finite-step evidence supports proceeding without retuning or rescaling.

The N=40 full-window Rg² and center-to-terminal half differences reach 2.31%
and 2.40%. The late Rg² split differences are 0.15–0.74%, with roughly 5–18
effective temporal samples. r001 retains a 1.02% final-quarter split and r002
a −1.43% late fit. Late Rg² means are 29.381, 29.329 and 29.432, and the late
center-to-terminal squared-distance means are 68.007, 67.914 and 68.406.
Agreement of those late windows and the absence of a common continuing trend are
sufficient for qualified starts. The evidence leaves slower collective
relaxation and loss of common initial-condition memory unresolved. When
production is eventually analyzed, compare replica-resolved early and late
shape windows, including time series and paired family comparisons. The decision
is scoped to initial configurations and grants no trajectory execution.

Reproduce from repository root with
`timeout 600 python3 examples/KG_Assoc/reviews/e1_qualification_20261119/QUALIFY.txt`.
This reuses the original audit and old closure hashes and rechecks the actual
24 snapshots. The prior readiness dossier records the state before this
qualification decision.
