# D2B — deferred force-distribution ideas

Scientific note only, 27 October 2026. No implementation, model selection,
execution or campaign is authorized. D2A observes the unchanged accepted
single-bead force F_i=-k_ss*(r_i-a) at the spring's actual occupied site.

## Finite-time kinetic weighting

One possible future alternative distributes a spring's force using attachment
transition probabilities over a declared physical horizon theta. At frozen bead
geometry and fixed anchors, p(theta)=p(0)*exp(theta*J_hop) is a kinetic endpoint
law; a time-residence weighting would instead use
theta^(-1)*int_0^theta p(t)dt. They answer different questions. With moving beads,
the transition law is geometry-history dependent. Renewal further changes
anchors, membership and ordering, so it needs the complete joint state rather
than an unqualified single-spring site matrix.

“Accessible within theta” is not automatically a useful hard subset: Poisson
hopping allows arbitrarily many attempts with nonzero probability, so every
connected admissible site can have nonzero finite-time support. A probability
threshold, residence criterion or other operational definition would need a
scientific decision, not an arbitrary implementation cutoff. Exclusion and
noncrossing depend on other springs and cannot generally be factorized.

A schematic expected contribution -k_ss*p_i*(r_i-a) is therefore not an approved
force law. Its horizon, endpoint/residence interpretation, joint constraints,
memory, noise and feedback would have to be specified and derived.

## Conditional-equilibrium / fast-hopping weighting

Another alternative could average the force over a conditional attachment law
at fixed R and fixed anchors. Its equilibrium weights are Boltzmann weights on
the **admissible joint assignments**, with canonical Z, exclusion and any fixed-
order sector. Independent per-spring exp(-beta*E_i) weights generally omit those
constraints. Conditional equilibrium probabilities are not finite-time
transition probabilities and require a justified separation of timescales to
replace hopping dynamics.

For a properly eliminated equilibrium attachment state, an effective potential
-T*log(sum_admissible exp(-U/T)) gives a conditional mean force. This is different
from differentiating an arbitrarily weighted mean energy while ignoring the
R-dependence of its weights. Eliminating fast dynamics may also require memory,
friction or stochastic corrections to preserve the intended response and
fluctuation-dissipation structure. Shared hopping/renewal rates complicate a
fast-hopping limit; making them large also accelerates anchor renewal. Averaging
the complete annealed (sites,anchors) law at frozen R would even average the
Gaussian connector force to zero, illustrating why the conditional variables
must be specified before invoking such a limit.

Both alternatives **change the dynamical model** and may require a different
equilibrium or coarse-graining treatment. Neither inherits the accepted E1
transition balance, dynamics or physical interpretation automatically. They
remain D2B questions for separate derivation, review and authorization; no
accepted force, hopping or renewal rule is changed in D2A.0.
