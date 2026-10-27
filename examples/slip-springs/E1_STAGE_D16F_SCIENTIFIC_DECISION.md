# D1.6F — scientific decision

Theoretical preparation only, 27 October 2026. No tests, code for mathematical
verification, quadrature, symbolic software, simulations, sampling, builds,
preflights, GPU work or scientific analyses were executed.

## Supported analytical findings

The [operator derivation](E1_STAGE_D16F_INVARIANT_RESPONSE.md) independently
recovers P_h=E_h exp(hJ) and the forward order exp(hJ*) E_h*. The leading
invariant source is C*pi, while the modified generator contains
C-B²/2+[B,J]/2. These operators differ but have the same equilibrium source.
With a justified invariant expansion and reversible H=-L, the response is

    pi_h(f)-pi(f)=h*a_f+o(h),
    a_f=<s,H^(-1)(f-pi(f))>, s=(C*pi)/pi.

Reversibility does not fix the sign of this mixed pairing. The
[sign analysis](E1_STAGE_D16F_SIGN_ANALYSIS.md) gives a rigorous three-state
Markov counterexample with reversible ideal L, a nonnegative squared observable,
positive one-step defect (2/3)*h² and exact negative stationary bias -h/6.
It disproves a general sign inference; it has neither EM nor E1's Gaussian
renewal structure, and does not prove negative bias in E1.

Gaussian E1 fibers supply additional identities: the centered connector mean
has zero conditional first-generator average; the local-corrector pairing is
3*mu*T/2; and the formal response separates into that static term plus
<g,J H^(-1)F>. The sign and size of the dynamical term remain unresolved. The
nonlinear backbone, energy-dependent hopping, evolving occupancy and terminal
renewal obstruct finite Poisson closure. The exact Gaussian conditional law is
not a license to average anchors freshly at every dynamical step.

[Solvable models](E1_STAGE_D16F_REDUCED_MODELS.md) yield positive stationary
variance bias for a fixed harmonic anchor, a coupled harmonic backbone/connector,
and a constant-rate Gaussian-refresh toy. Their exact finite-step covariances
agree analytically with the response formula. The coupled toy has a one-step
coefficient growing with backbone stiffness but a first-order stationary
connector coefficient independent of that stiffness. Gaussian refresh changes
the stationary response without changing the leading local coefficient.
These are restricted sign/dependence results, not approximations substituted
for the accepted nonlinear E1 model.

## What is not established for full E1

Neither positive nor negative leading stationary connector bias has been proved
for the actual model. The theory permits a signed response at the level of its
formal mixed representation, but no negative E1 counterexample or positive E1
sign theorem has been obtained. Its magnitude is also uncomputed. Existence
and uniqueness of the relevant invariant internal family, adequate mixing,
Poisson solvability, the weak remainder and source regularity near collapsed
bonds remain assumptions. A spectral gap is not established. Conditional bounds
require a source norm/dual norm and a proved relaxation or coercivity estimate;
the known local coefficient alone supplies neither. Unresolved D1.6C IATs are
not used as relaxation inputs.

The current brief's quoted D1.6E coefficients are prior local-defect inputs.
This milestone neither repeats nor authenticates numerical verification; the
committed D1.6E preparation record remains unchanged. No new decimal values of
scientific expectations are asserted.

## Interpretation of D1.6C and next review

The observed approximately -0.04462 stiff/coarse late-minus-early change is
a post-selected finite-window contrast, not a measured invariant-distribution
shift. It establishes neither the sign of a_f nor the mechanism of a stationary
bias. Four replicas and unresolved temporal support retain their original
qualifications. A positive local defect does not explain that negative change.

Only if both timesteps lie in a controlled common expansion can their stationary
levels differ by (hc-hf)*a_f to leading order. No such regime or convergence order
is demonstrated here. Larger stiff-chain K_EM need not mean larger stationary
bias; jumping/renewal rates affect the inverse generator even when absent from
the leading source. Rate monotonicity and stiffness monotonicity for E1 are open.

Independent review should check operator signs/order, the counterexample's
stochasticity and exact invariant law, local-corrector domains, Gaussian
reflection/projection identities, and the separation of toy and E1 hypotheses.
To settle E1's sign analytically would require an additional alignment/positivity
theorem, controlled solution or bounds for the full Poisson equation, or a
counterexample retaining the relevant E1 structure. No such information is
replaced by a fitted unresolved relaxation time.

The [rational regression specifications](tests/d16f_math_regression.py) are
prepared and **UNEXECUTED**. They check exact toy algebra, not the accepted
simulator. No verification or experiment is authorized by this decision; no
GPU campaign is designed. Stop for independent review before any execution.
