# Implemented kinetics and equilibrium-invariance derivation

All equations use kB=1, the configured thermostat temperature T, and positive
nu0 and reaction interval Δ = Nevery·dt. The kinetic kernel uses configured T,
not a rescaled measured kinetic temperature. Campaign values: T=1, nu0=20,
Nevery=100, dt=.01, Δ=1, Ee=8, K=30, R0=1.5, r_assoc=1.25, damping=2.
Observed reference temperature near .98 does not justify changing this formula.

## Energy and conditional transition probabilities

Let F(r) = −K R0² log(1−r²/R0²)/2. The reference r* solves the derivative of
WCA + permanent KG FENE equal to zero, below 2^(1/6)σ. The additional temporary
bond energy is u(r)=F(r)−F(r*)−Ee, finite only for 0≤r<R0.
WCA acts in both chemical states, so it cancels from the bond-toggle energy
change; it must not be counted again in u. Permanent bonds are unchanged.
Changing Ee shifts chemical energy; Ea changes only attempts and is absent
from both energy and forces.

For each geometry-selected candidate pair:

```
λ(Ea,T) = nu0 exp(−Ea/T)
q(Ea,T,Δ) = 1 − exp(−λΔ) = −expm1(−λΔ)
a+ = min(1, exp(−u/T))
a− = min(1, exp(+u/T))
p(free pair → bound) = q a+
p(bound pair → free) = q a−
```

Both stickers must be free for formation; only reciprocal existing partners can
break. In other valence-one states this edge update is the identity. Both
reaction directions require `r < r_assoc`, a strict geometric cutoff implemented
by the caller. `Kinetics.update` itself validates r<R0 and assumes its supplied
edge list has already passed that cutoff. Active bonds outside r_assoc remain
mechanically active below R0; both toggle probabilities there are zero. There
is no automatic overstretch rupture, and invalid FENE geometry is an error.

For eligible inverse states at the same geometry,

```
p+ / p− = a+ / a− = exp(−u/T)
p±(Ea') / p±(Ea) = q(Ea') / q(Ea)
q(Ea')/q(Ea) = [1−exp(−nu0 exp(−Ea'/T) Δ)] /
               [1−exp(−nu0 exp(−Ea /T) Δ)]
```

This is an exact symbolic identity for the Bernoulli thresholds, not a result
about measured trajectory rates. If λΔ≪1 at both barriers, the last expression
approaches exp[−(Ea'−Ea)/T]. At Ea4 it is not accurate enough to silently use
that approximation. A per-visit discrete frequency p/Δ scales with q. The
constant-environment geometric survival hazard −log(1−qa)/Δ does not scale
exactly with q when qa is appreciable; its forward/reverse ratio is generally
not exp(−u/T). The equilibrium ratio is a ratio of transition probabilities,
not of those two inferred continuous hazards. At a fixed isolated two-state
geometry the nontrivial eigenvalue is 1−q(a++a−); its correlation times also
require the finite-step logarithm. Moving polymer geometry adds other modes.

## Why competing edges need a proof

At fixed geometry x, define the conditional target over allowed valence-one
matchings M as

```
π(M | x) ∝ exp[−Σ_(ij∈M) u(rij)/T].
```

Every eligible inverse pair M ↔ M∪{e} has weight ratio exp(−u_e/T).
Therefore π(M) q a+ = π(M∪{e}) q a−. Forbidden availability states stay put.
An edge with r≥r_assoc is also an identity kernel even if bonded, so it leaves
π invariant, although fixed-geometry chemistry can then be reducible.
There is no selection-normalization factor for the number of free candidates:
the actual code builds *all* geometric sticker pairs once per sweep, without
filtering them by chemical state, then re-reads availability after each update.
Thus each single-edge kernel K_e preserves π. Every fixed ordered product
K_e1 K_e2 ... K_en preserves π too. A geometry-dependent mixture of these orders
also preserves π if the ordering law is independent of M and acceptance draws
have the assumed conditional distribution. Uniform permutation sampling is not
necessary for invariance. Reversibility of the entire product is not necessary
and does not follow from reversibility of its factors.

The CPU enumeration retains a five-state four-sticker path with competing edges,
including a two-bond state. All six orderings preserve π at Ea4/6/8/10 to
floating-point precision. One fixed-order sweep has nonzero detailed-balance
flux (about .00434 at Ea4), while preserving π. An empty-to-two-bond path contains
q²; its probability ratio at two barriers is (q'/q)², not q'/q. These examples
show explicitly why a complete sweep is neither automatically reversible nor
an exact uniformly slowed clock. The actual hash-ordered update has been checked
against 340 deterministic host sweeps, including both occupied/free decisions.

LAMMPS constructs the same geometry-only edge list with minimum images, stable
atom tags, both cutoff directions and explicit exclusion of directly permanently
bonded neighbors. For the present stars the stickers are terminal beads on
N=10 arms, so no two stickers share a permanent bond. UAMMD's all-sticker search
therefore gives the corresponding allowed set. No omitted proposal-ratio factor
arises from that topology here. This argument must not be transplanted unchanged
to a chemically filtered or randomly selected-one-candidate algorithm.

## Numerical and full-process limits

`uniform53(hash)` is a deterministic 53-bit grid value u∈{0,...,2^53−1}/2^53.
For an ideal uniform integer, the literal test `u < p` has probability
ceil(2^53 p)/2^53, clamped at endpoints, rather than an arbitrary real p. Each
threshold differs by at most 2^−53. Floating-point energy/exponential evaluation
adds rounding. Very small probabilities require relative-error care. In this
Ea range those quantization errors are negligible for the intended probabilities,
but an exact real-arithmetic detailed-balance proof should not be claimed as
bitwise equality of floating-point transition probabilities.

The SplitMix-style stateless hash uses seed, absolute step, ordered stable IDs
and separate order/accept streams. With a fixed seed the path is deterministic;
standard Markov calculations model it as suitable uniform pseudorandom noise.
Separate stream tags and distinct seeds are not a theorem of independent draws.
This review does not certify PRNG independence. The host test checks literal
hash/sort/accept behavior without replacing the frozen loop.

If, in an idealized coupled process, the MD kernel for every fixed M preserved
π(x,v|M), and the chemical kernel preserved π(M|x), their alternating composition
would preserve the joint π(x,v,M) for every Ea. This conditional-invariance
argument does not require full-sweep detailed balance. Ea-invariant Hamiltonian
and chemical conditional balance alone do not prove that MD premise. Here GJ
Langevin uses finite dt, nonlinear forces, single precision and newly initialized
integrator memory at restarts, with no accept/reject correction. Exact coupled
invariance is unproved, just as the formal reference record states. Reaction
statistics sampled along trajectories can change with Ea through changed geometry,
recrossings, candidate opportunities and topology. None of the CPU matching
matrices tests that moving-coordinate effect.

The intended equilibrium distribution is therefore Ea-invariant; the ideal
chemical conditional sampler has that invariance; the actual complete numerical
process has supporting historical tests and an explicit remaining qualification.
That distinction is the reason for targeted validation, not a claim of a
known model inconsistency or a demand for complete structural decorrelation.
