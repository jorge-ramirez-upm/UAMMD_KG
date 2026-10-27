# D1.6D — accepted-source trace

Preparation only, 27 October 2026. Source inspection is not execution verification.
All line ranges below refer to **scientific source commit**
`0dea651b58171a72206774bcebb2f4c74960069b`, under `examples/slip-springs/`.
The eight files in the tables are unchanged at starting local/remote HEAD
`d6924acbed63d9facc667cd8e72a73e61d597676`, as inspected with `git diff`.
Use `git show <scientific-SHA>:examples/slip-springs/<file>` to resolve historical
lines; GitHub links below pin that commit. No source was copied or modified.

## Initialization and state

| Mathematical/source rule | Accepted implementation and lines | Consequence |
|---|---|---|
| k=3T/A2, stored coefficient | [fixed_slip_springs.h](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/0dea651b58171a72206774bcebb2f4c74960069b/examples/slip-springs/fixed_slip_springs.h#L13-L20), `stiffness`, 13–20 | Long-double intermediate; final `Real` cast. |
| Canonical Z, uniform distinct sites | Same file, `initialize`, 24–37 | Count bound, all-site shuffle, first Z sites; no independent Bernoulli occupancy. |
| Conditional independent anchors | Same file, 35–47 | Separate host RNG domain; sigma=sqrt(input A2)/sqrt(3); centered on actual stored bead positions; cast to `Real`. |
| Backbone coefficient convention | [semiflexible.cu](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/0dea651b58171a72206774bcebb2f4c74960069b/examples/slip-springs/semiflexible.cu#L147-L225), `parameters`, 147–167 | `real2` stores (b0,kb), bead-indexed kappa, zero endpoints; positive kb and nonnegative b0/kappa. |
| Bare-backbone direct draw | Same file, `direction`/`initialize`, 169–225 | Separate engine per chain; bead 0 initially zero; radial l² Jacobian rejection at 194–202; conditional angular draw at 203–219. Supplied coordinates bypass sampler at 176–183. |
| Coupled initialization order | Same file, `simulate`, 250–269 | Backbone first, sites/anchors conditional on it; IDs subsequently assigned in increasing occupied site order, reciprocal contour links constructed. |
| State variables and exclusion map | [slip_hopping.cuh](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/0dea651b58171a72206774bcebb2f4c74960069b/examples/slip-springs/slip_hopping.cuh#L7-L46), `Spring`, 7–10; `attempt`, 24–32 | Stable storage ID, current anchor/site/chain/previous/next; one ID per occupied site. |

## Jump rules

| Mathematical/source rule | Accepted implementation and lines | Consequence |
|---|---|---|
| Attempt mean Z*nu*h | [slip_hopping.h](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/0dea651b58171a72206774bcebb2f4c74960069b/examples/slip-springs/slip_hopping.h#L6-L15), `poissonMean`, 6–15 | Wider intermediate, max mean 10000, max events 100000; invalid requests abort, never clip. |
| Poisson exponential arrivals | `slip_hopping.cuh`, `uniform`/`poisson`, 49–55, 64–75 | Ideal Poisson uniformization; finite RNG/retry/event bounds qualify exactness. |
| Uniform ID with replacement, equal directions | Same file, `index`, 56–63; `batch`, 83–105 | Integer rejection avoids modulo bias; each event sees the mutated preceding state; not a synchronous sweep. |
| Boundary/exclusion/order | Same file, `attempt`, 24–33 | Outward is `boundary`; occupied is null; inconsistent neighbor restriction is fatal. Adjacent vacant target cannot overtake on a valid state. |
| Metropolis energy | Same file, `attempt`, 34–46 | Double difference-of-squares on stored `real` values; log acceptance; same effective k as force; old site cleared, new site filled. |
| Reciprocal bookkeeping invariants | Same file, `invariant`, `siteInvariant`, `checkState`, 107–138 | Chain/site/ID, anchor buffer, reciprocal previous/next and exclusion checked. |
| Outward attempts become renewal | [slip_renewal.cuh](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/0dea651b58171a72206774bcebb2f4c74960069b/examples/slip-springs/slip_renewal.cuh#L73-L125), `batch`, 84–119 | Same Poisson/ID/direction process; outward rate nu/2 per occupied end; separate renewal RNG domain. |
| Destination chosen among all 2M ends | Same file, `propose`, 73–82 | Uniform chain and end; pre-event occupied end rejected, including the source itself; no redraw until vacancy. |
| New Gaussian anchor | Same file, `anchor`, 60–71; `semiflexible.cu`, 241–244 | Float normal4 / double normal2; center at updated destination bead; sigma from input A2, then `real` storage. |
| Acceptance one, same-chain inverse | `slip_renewal.cuh`, `transfer`, 13–57 | Validate terminal source/destination; occupied check before unlink; source terminal-order check 24–34; find destination extreme excluding source ID 35–46; unlink/reinsert 47–56. No energy acceptance factor. |
| Sequential single writer | `slip_hopping.cuh`, `hopping`, 128–133; `slip_renewal.cuh`, `hopping`, 121–125 | One CUDA thread mutates each complete batch. |

## Forces, integration and observation

| Mathematical/source rule | Accepted implementation and lines | Consequence |
|---|---|---|
| Finite-rest-length stretching | [semiflexible.cuh](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/0dea651b58171a72206774bcebb2f4c74960069b/examples/slip-springs/semiflexible.cuh#L22-L87), `stretch`, 22–41 | g=kb*(l-b0)*q/l; endpoint signs; half bond energy per bead; undefined l=0,b0>0 fails. |
| Kratky–Porod bending | Same file, `bend`, 45–68 | A,B at 61; bead forces A,B-A,-B at 62; thirds of kappa*(1-u·v) at 64; zero kappa skipped before normalization. |
| Connector force/energy | [semiflexible_slipspring.cuh](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/0dea651b58171a72206774bcebb2f4c74960069b/examples/slip-springs/semiflexible_slipspring.cuh#L7-L24), `fixed_slip_force`, 7–24 | -k*(r-a), k*e²/2, added to exactly one occupied bead; no new dynamics implied by stale “fixed” header comment. |
| Force accumulation order | `semiflexible.cu`, `evaluate` lambda, 317–321 | Stretch overwrites, bend adds if active, dense spring force adds. |
| BD noise and buffers | `semiflexible.cuh`, `gaussian`/`update`, 70–87 | Stable bead identity/step, disjoint domain 3, eight draws reserved; precision-specific Gaussian; old/next coordinates. |
| Mobility and noise scale | `semiflexible.cu`, 451–456 | `real(h/zeta)` and `real(sqrt(2*T*h/zeta))`; rounded separately; swaps complete updated buffer. |
| BD then jumps at updated R | Same file, 451–465 | Evaluate old-state forces; EM; swap; complete batch; invariants; observation. Backward operator P_h=E_h Q_h. |
| Observer reads current joint state | Same file, 363–404 | Device state copied to host; actual current anchors/sites/links, no mutation of device state. |
| Observation phase, live connectors | [e1_equilibrium_observer.h](https://github.com/jorge-ramirez-upm/UAMMD_KG/blob/0dea651b58171a72206774bcebb2f4c74960069b/examples/slip-springs/e1_equilibrium_observer.h#L95-L160), constructor 95–114; `begin`, 119–160 | Initial before dynamics, otherwise after full step; e computed at **current** site/anchor 152–157; all chains' sums 159; no permanent initial pair. |
| Observer ordering/exclusion | Same file, 128–145 | Independent host reconstruction of occupied sites and contour links; canonical total checked at 159. |

## What inspection establishes

The formulas and ideal reversibility proofs in the [audit](E1_STAGE_D16D_THEORETICAL_AUDIT.md)
describe the inspected production rules. The standalone proposed mathematical
tests do not invoke these kernels and cannot demonstrate compiled equivalence.
No force sign/coefficient discrepancy or asymmetric allowed jump edge was found.
The input-variance versus rounded-k mismatch is an actual precision convention,
not a demonstrated cause of the empirical signal. Compiler arithmetic, finite-bit
RNG distributions, abort probabilities and full-process ergodicity remain outside
what source inspection proves. Historical reports are supporting context only;
none of their tests was repeated here.
