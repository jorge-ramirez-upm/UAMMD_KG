# Strict candidate-cutoff numerical contract

The physical gate remains **r < r_assoc**, with r_assoc=1.25 and a strict squared
comparison against 1.5625. There is no epsilon, enlarged range, cutoff clamp or
probability change. The numerical contract is the frozen UAMMD implementation,
not exact arithmetic on the original serialized decimal coordinates.

For each stored coordinate component a,b of type `uammd::real`, define:

```
d = double(real(b - a))
n = nearbyint(d / L)
s = d - L*n
rsq = sx*sx + sy*sy + sz*sz
include iff rsq < r_assoc*r_assoc
reported distance = sqrt(rsq)
```

The ordinary campaign uses real=float32, double box lengths and default
round-to-nearest/ties-to-even. The subtraction is evaluated at the stored real
precision, before promotion. `nearbyint` follows the floating-point environment;
the diagnostic records its mode and the validation driver rejects non-nearest
environments without changing them. The production cell search and `stickerDistance`
already implement this contract and remain byte-identical. The corrected oracle
spells out the same arithmetic independently and retains its own all-pairs loops.
It does not call the search, its image helper or its distance helper.

Mathematically equivalent formulas need not agree at a strict floating-point
boundary. Two CPU counterexamples establish distinct discrepancies in the former
oracle:

| Case | Production arithmetic | Former oracle arithmetic | Classification |
|---|---|---|---|
| a=-0.1f, b=1.15f, L=40 | float subtraction gives 1.25 | double-first gives 1.2499999776482582 | production excludes; former oracle includes |
| a=0, b=64, L=20.916666666666668 | d-L*nearbyint(d/L)=1.25 | remainder(d,L)=1.2499999999999964 | production excludes; former oracle includes |

The second case isolates minimum-image reduction rounding, even when coordinate
subtraction is exactly representable. Both are exactly at/near the represented
cutoff; neither justifies changing it. The corrected oracle excludes both pairs,
matching the unchanged production predicate. Distance comparison is now exact
under the common arithmetic contract; the former 1e-4 diagnostic distance
comparison is removed. That old comparison never defined the physical cutoff.

## Reference semantics

LAMMPS `feature/associating-stickers` at
`1c6faf70e94aef2389c208e8c80c60c084a96907` uses double atom coordinates, subtracts
them in double, applies `domain->minimum_image`, and includes a pair only when
`rsq < r_assoc*r_assoc` (fix_associating_kinetics.cpp:214). The active pair force
uses the same domain geometry and remains mechanically active to R0. Its kinetics
candidate gate does not become R0 for already associated pairs.

The orthogonal LAMMPS image routine repeatedly adds/subtracts L while |d|>L/2.
Its half-box tie preserves the displacement sign; UAMMD's nearest-integer rule
can choose another sign at ties. Squared distance is unchanged at the exact tie,
and campaign r_assoc is far below half the box size. LAMMPS and UAMMD need not
have bit-identical cutoff classification on a boundary: their stored coordinate
precision and reduction operations differ. Imposing the former oracle's double
predicate on UAMMD production would change its numerical candidate set. **That
alternative was not implemented.** It would require a separate scientific decision.

LAMMPS source identity and exact relevant file hashes are in LAMMPS_REFERENCE.json.
Those files equal that commit. Unrelated local LAMMPS working-tree changes exist;
they were neither used as a clean-build claim nor modified here.

## Scope, availability and limits

Both algorithms enumerate geometric sticker pairs, including free pairs, active
pairs and pairs currently unavailable because of other partners. Availability,
competing reactions, energy factors and valence-one reciprocity remain in the
unchanged kinetics implementation. An active pair outside r_assoc stays excluded
from chemistry while remaining mechanically active below R0. Ea, Ee, T, dt,
Nevery, probabilities, force law and random-stream semantics are unchanged.

Tests cover strict below/at/above boundaries, signs, axes, periodic faces/corners,
small/degenerate grids, reversed input, many image positions and nondyadic random
coordinates, in float and double host builds. Lossy float coordinate translations
are not required to preserve exact mathematical positions; the two algorithms
must agree for the *same represented inputs*. This is not a proof of the cell
search for every finite coordinate, grid size or rounding environment. Triclinic
boxes are outside this implementation.

The actual GPU failure at inferred 8,007,100 had no saved frame/pair difference.
These two inconsistencies are proven, but neither is proven to be its cause.
A cell-list omission or another discrepancy remains possible. The independent
all-pairs algorithm and new failure capture preserve the ability to detect it.
No previous failed history is relabeled as passed by this CPU repair.
