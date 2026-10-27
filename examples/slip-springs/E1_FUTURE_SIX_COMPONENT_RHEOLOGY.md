# Future rheology requirements — six components and ordered partial correlations

Recorded during D2A.4 preparation, 27 October 2026. **Scientific requirements
only. No stress acquisition, cross-correlator, stress reduction or G(t)
calculation is implemented or authorized by D2A.4.** Its accepted E1 dynamics
and active-slip-spring stress prohibition remain unchanged.

## Selected isotropic estimator

For a physically specified stress sigma and volume V, the selected convention is

\[
G(t)=\frac{V}{5k_BT}\big[
\langle\sigma_{xy}(t)\sigma_{xy}(0)\rangle+
\langle\sigma_{xz}(t)\sigma_{xz}(0)\rangle+
\langle\sigma_{yz}(t)\sigma_{yz}(0)\rangle\big]
+\frac{V}{30k_BT}\big[
\langle N_{xy}(t)N_{xy}(0)\rangle+
\langle N_{xz}(t)N_{xz}(0)\rangle+
\langle N_{yz}(t)N_{yz}(0)\rangle\big],
\]

where N_xy=sigma_xx-sigma_yy, N_xz=sigma_xx-sigma_zz and
N_yz=sigma_yy-sigma_zz. Channel order is exactly

1. sigma_xy
2. sigma_xz
3. sigma_yz
4. N_xy
5. N_xz
6. N_yz

Keep the raw normal differences, all three of them, and exact coefficients
**1/5 and1/30**. N_xz=N_xy+N_yz makes them linearly dependent; it does not
permit dropping one from this prescribed rotational average. No arbitrary
tensor average, single-shear replacement, division by six, or hidden factor1/4
in the normal-difference products is allowed. Apply the same channel map to
backbone and virtual-spring tensors. Dependent components are not independent
statistical samples.

This fixes the component contraction, **not** the physical stress/response of
the implicit-host probe model. V, stress density versus virial, ensemble,
normalization and response conjugacy remain to be established before this
expression can be identified with a physical probe relaxation modulus.

## Four correlation classes with an immutable physical chain index

For chain c, define future instantaneous tensors sigma_bb,c (all intramolecular
stretching plus bending) and sigma_ss,c (all virtual springs attached to c at
that observation time). Combine stretching/bending at the instantaneous tensor
level for bb; their internal cross terms must not disappear by summing only
separate autocorrelations.

Let x_X,c,j be the six channels of X in {bb,ss}. Retain component-resolved
ordered products

\[
H^{(j)}_{XY,c}(\tau)=\langle x_{X,c,j}(t_0+\tau)x_{Y,c,j}(t_0)\rangle,
\qquad
\mathcal I_{XY,c}=\frac15\sum_{j=1}^3H^{(j)}_{XY,c}
+\frac1{30}\sum_{j=4}^6H^{(j)}_{XY,c}.
\]

| Class | Late tensor / early tensor | Quantity retained |
|---|---|---|
| A | bb / bb | Backbone autocorrelation, six channels |
| B | bb / ss | Backbone–virtual cross-correlation, six ordered channels |
| C | ss / bb | Reverse cross-correlation, six ordered channels |
| D | ss / ss | Virtual autocorrelation, six channels |

The c at both endpoints denotes the **same backbone chain**, never a permanent
spring-to-chain association. Hopping/renewal changes membership. Allocate each
spring's stress to its actual attached chain at each endpoint; after a renewal
transfer it contributes to the destination chain at that time. A chain may have
no live spring, giving the empty sum, rather than a carried-forward tensor.
Use one consistent completed physical-state phase for every channel/class.

Accumulate by chain before within-replica averaging; whole-run replicas remain
the uncertainty units. Canonical population and interchain transfers can couple
chains statistically. Do not automatically add c!=c' correlations. A hypothetical
macroscopic sum over chains would require examining those terms, whereas a
same-probe correlation deliberately fixes c; the physical response question
must decide their role separately.

Keep B and C time ordering explicitly. Equality of population cross-correlations
requires justified stationarity, time-reversal/parity and equilibrium symmetry
conditions; it does not make independently accumulated finite-sample estimates
identical. D1.6 did not confirm finite-step equilibrium preservation. Do not
replace the two measured orders by a symmetrized estimate without establishing
and recording the relevant assumptions.

Algebraically, autocorrelating bb+ss includes four classes. **Their sum is not
automatically the physical partial probe modulus**, nor the G(t) of an explicit
melt. Keep raw products, component contraction, volume/temperature prefactors
and the scientifically justified response combination as distinct operations.

## Inspected KG capabilities and limits

KG files were read, never changed:
[header](../KG/correlator.h), [implementation](../KG/correlator.cpp).

| Existing source | Actual capability and future reuse |
|---|---|
| correlator.h:190–234; correlator.cpp:483–726, especially add585–655/evaluate656–696 | Correlator6 accepts six scalar values, accumulates six separate autocorrelation numerators on one lag/count grid and returns getf(i,j), j=0..5. Reuse one safe owned bank per chain for bb and one for ss. It does not compute cross products between the supplied channels/tensors. |
| correlator.h:8–92; correlator.cpp:162–186 | gett(i) is lag in acquisition samples, getn(i) is actual origin count. Coarse levels are block means; deepest populated level omitted, incomplete blocks truncated. Convert to physical time with an explicit integer clock; counts/bins are not independent samples. |
| correlator.h:96–124; correlator.cpp:264–312 | CrossCorrelator inserts scalar A/B pairs. The implemented product is **current A times earlier B**, not the reversed endpoint ordering suggested by the header's prose. Block averaging occurs separately on both inputs; output is one ordered cross curve. |
| correlator.h:152–186; correlator.cpp:782–846 | CrossVectorCorrelator inserts two three-vectors (six arguments) and returns one three-component dot-product cross sum, not six scalar cross outputs. Actual order is again current A dot earlier B, with no division by three in this function. |
| stream_correlator.h:28 onward | OwnedCorrelator6 already stages allocations and owns row lifetimes around unchanged KG arithmetic. Reuse its ownership/limits pattern; the existing stress bank's physical normalization is not automatically E1's response. |

Thus for class B, a future ordered scalar API must map A=bb and B=ss to the
actual implementation's late/early convention; reverse those inputs for C.
Test this with explicitly asymmetric prescribed time series rather than trusting
class/header naming. No such cross test or adapter is implemented here.

No inspected single KG class provides all six component-resolved ordered cross
outputs on a shared grid. If these six outputs are retained as required, a
**minimal local six-component cross owner/adapter** is needed in the later
milestone, with one bank per ordered class/chain and shared clock/counts.
Two CrossVector instances could retain two triplet sums, but lose individual
component information; six independent CrossCorrelator owners duplicate grids
and allocation overhead. Prefer a small shared-grid design derived from the
existing scalar cross arithmetic/ownership patterns after separate review.
Do not implement it or modify KG now. Polarization using autocorrelations of
sums/differences does not preserve the two ordered mixed classes separately.

Correlator6 performs raw products and block averaging; it applies no physical
V/kBT, isotropic weights or mean subtraction. All six outputs share the first
channel's population/count support. Future callers must validate atomic finite
six-value samples, signed sentinel limits (stored values must exceed -1e10),
clock/count overflow, allocation failure and lifetime. Do not clip stress or
copy the MSD coordinate-offset trick: a stress offset changes raw correlations.
Coarse stress/cross curves correlate block means, with triangular fine-time
support; never relabel them exact fine-trajectory correlations at one lag.

## Required dedicated scientific derivation before implementation

- Re-establish the actual nonlinear finite-rest-length stretching and discrete
  cosine-bending intramolecular stress/virial, including sign and tensor order.
  Reuse [the backbone stress derivation](STAGE4A3A_REPORT.md) and actual accepted
  force source as starting authorities, with their scope/precision qualifications.
- Derive the virtual-spring virial and its deformation conjugacy for spatial
  anchors. Specify which bead/anchor coordinates deform, whether host stress/work
  enters, the origin/translation convention, and any external-force boundary
  terms. A bead-only force virial with nonzero net anchor force is not
  automatically a translation-invariant molecular stress.
- Account for instantaneous stress changes during hopping and renewal, anchor
  replacement/chain transfer and any kinetic/jump contributions required by
  the response derivation. Do not alter the accepted dynamics to fit a formula.
- State raw versus connected correlations and mean-subtraction procedure,
  stationarity and equilibrium assumptions. Isotropy may imply zero ideal shear/
  normal-difference means, but finite-step and estimated finite-run means require
  explicit treatment; do not silently substitute centered data into the raw formula.
- Define ensemble, effective V, probe concentration/density, tensor units and
  normalization. If W=V*sigma is actually stored, elementary substitution gives
  prefactor1/(V*kBT) on W products, not V/kBT; this conditional unit conversion
  does not determine V or the physical response. Do not silently assign unit
  volume from simulation chain count or identify phantom probes with a melt.
- Derive whether/how A–D, same-chain versus distinct-chain terms and any host
  response enter the desired partial probe modulus. Preserve the selected
  three-shear/three-normal rotational contraction and exact coefficients, while
  separating that contraction from the unresolved physical response combination.

D2A.4 has no dense bond/anchor tensor time series; its compact MSD/C1/C2 curves,
sparse scalar context and endpoint snapshots cannot reconstruct the missing
six-channel stress histories. Future rheology needs its own reviewed derivation,
read-only acquisition/verification and explicit authorization. It is not a
postprocessing promise for this dynamics-only campaign. No D2B force distribution
change, stress calculation, or macroscopic-modulus claim is made here.
