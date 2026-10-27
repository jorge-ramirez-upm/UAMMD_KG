# D1.6F — implementation and limitations

Prepared 27 October 2026 in the permanent checkout
`/home/jramirez/UAMMD_KG-slip-springs-dev`, branch `slip-springs`.
Starting local and actual remote HEAD both
`4973cf4c2178eef6fcd401e99cea9f23527ae64f`, queried before work. No newer
committed remote work was present at that check. Normal push preserves history.

| Deliverable | Contents |
|---|---|
| [Invariant response](E1_STAGE_D16F_INVARIANT_RESPONSE.md) | Source order, adjoints, perturbation signs, modified generator distinction, assumptions, local corrector and Gaussian static pairing. |
| [Sign analysis](E1_STAGE_D16F_SIGN_ANALYSIS.md) | Spectral argument, exact reversible finite-state counterexample, restricted positivity hypotheses and conditional bounds. |
| [Reduced models](E1_STAGE_D16F_REDUCED_MODELS.md) | Gaussian projection/reflection identities and nonclosure; three solvable toys, finite-step covariances and limitations. |
| [Scientific decision](E1_STAGE_D16F_SCIENTIFIC_DECISION.md) | What is established, full-E1 unknowns, D1.6C implications and review gate. |
| [Mathematical specifications](tests/d16f_math_regression.py) | Unexecuted exact rational checks of operator algebra, counterexample, covariances, reflection and static pairing. |
| [README](README.md) | Links and preparation-only status. |
| This report | Scope, provenance and execution limitations. |

No mathematical tests, Python imports/discovery, quadrature, symbolic programs,
builds, preflights, GPU queries/work, simulations, sampling, reference
recalculations or scientific analyses ran. Only source/document inspection,
file preparation and Git/filesystem housekeeping were performed. No code was
executed to evaluate or verify mathematical claims. The written analytical
derivations and rational examples are not fabricated executed test results.
The standalone regression file is outside `test_*.py` discovery and requires
an explicit action. No execution infrastructure or dependency was introduced.

The accepted simulator/model, forces, initialization, RNG, integration,
hopping, renewal and observer are unchanged. Four source files inspected were
compared to scientific SHA `0dea651b58171a72206774bcebb2f4c74960069b` without
differences. Frozen results, evidence, D0 criteria, manifests and approved
source identities were not modified. D1.6D/E records remain historical records.
This stage does not authenticate subsequent D1.6E numerical results asserted
in the current brief. All changes stay in `examples/slip-springs/`; no
persistent work uses `/tmp`, `/var/tmp` or another temporary location.

The main conclusion is conditional mathematical structure, not a definite
full-E1 sign: the inverse generator weights mixed modes; general reversibility
cannot settle the sign, and extra Gaussian identities do not close the E1
Poisson equation. Toy positivity results, the non-E1 negative counterexample
and bounds are explicitly scoped. Singular-source/domain and invariant-law
assumptions prevent treating formal response identities as a completed E1
stationary-bias theorem. No magnitude or relaxation time was calculated.

Repository-only ancestry, whitespace and path-isolation checks precede the
commit. Git hooks are disabled for commit/push invocations to prevent implicit
tests or other prohibited execution. Final SHA and push verification are
reported in the handoff, avoiding a self-referential identity here.

Future explicit user command after independent review, **not run here**:

```sh
python3 examples/slip-springs/tests/d16f_math_regression.py --tests
```

It performs exact finite algebra, with no scientific trajectory or production
source import. No test pass is claimed. Stop after preparation; independent
review precedes authorization of verification or further experiments.
