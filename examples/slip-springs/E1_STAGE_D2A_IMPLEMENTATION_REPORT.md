# D2A.0 — planning implementation report

27 October 2026; permanent checkout
`/home/jramirez/UAMMD_KG-slip-springs-dev`, branch `slip-springs`.
Starting local and actual remote HEAD:
`7ffbc4735bb0fb832025656fc9eb98cf5333ec59`, verified before inspection.

| Documentation delivered | Purpose |
|---|---|
| [Observables](E1_STAGE_D2A_OBSERVABLES.md) | Exact selected indices, direct estimators, C1/C2 versus amplitude correlation, symmetry, replica uncertainty and unresolved-diffusion criteria |
| [Correlator reuse](E1_STAGE_D2A_CORRELATOR_REUSE.md) | Actual source/functions/lines, KG direct-displacement support, adapter boundaries and distinct coarse-level semantics |
| [Implementation plan](E1_STAGE_D2A_IMPLEMENTATION_PLAN.md) | Minimal CPU first milestone, existing data availability, later read-only acquisition and memory/storage accounting |
| [D2B ideas](E1_STAGE_D2B_FORCE_DISTRIBUTION_IDEAS.md) | Deferred kinetic versus conditional-equilibrium force averaging and model-change implications |
| [README](README.md) | Links and planning-only review gate |
| This report | Outcome, provenance and limitations |

The principal reuse finding is KG DiffusionCorrelator: it already accumulates
squared differences and promotes the last sample, avoiding unstable position-
moment subtraction. A small staged owner/clock adapter is needed; its numerical
algorithm can remain unchanged. Reuse the validated orientation adapter unchanged,
with replica-safe aggregation outside one-chain banks. Ordinary Vector correlations
average blocks and do not implement translational MSD. Coarse diffusion selects
decimated fine origins, while coarse orientation averages features over blocks;
their support must be labeled distinctly.

The proposed next step is **D2A.1, CPU-only estimator/ownership implementation
using prescribed inputs and direct references**, after independent review and
explicit authorization. No simulator integration, GPU acquisition or campaign
belongs to that first step. Later compact acquisition would retain CM plus five
bead vectors, with bounded batches. Existing CPU workers/transport are concretely
typed for stress, so they supply reusable scheduling/lifetime patterns rather
than an unchanged drop-in new-observable interface. No new generic framework is
recommended. Physical cadence, horizon, support/fit budgets, runtime overhead,
source lifetime checks and the sentinel/large-coordinate limits remain review
questions. Memory figures are source-derived formulas, not new measurements.

Existing D1.6 scalar/full schedules do not contain dense selected positions or
end-to-end directions; only four complete coordinate snapshots exist. No missing
trajectory is reconstructed and no physical result is calculated. The historical
orientation validation report is prior technical evidence, not a rerun or proof
of independence/mixing for E1. D1.6 remains **scientifically closed with
qualifications — equilibrium preservation not confirmed**. Timestep sensitivity
remains an interpretation limitation; T100 is not assumed terminal.

Only read-only source/document inspection, documentation edits and Git/filesystem
housekeeping were performed. No tests, builds, simulations, benchmarks, analyses,
sampling, symbolic/quadrature programs, hardware preflights or GPU operations ran.
No implementation or test code was added. Accepted simulator, forces, hopping,
renewal, RNG, integration, models, historical evidence, frozen protocols and
acceptance criteria are unchanged. All edits remain under `examples/slip-springs/`;
no persistent resource uses temporary storage. Commit/push hooks are disabled
for those invocations to avoid implicit prohibited execution. The final SHA and
remote push verification are supplied in the handoff. Stop for independent review;
neither D2A.1 execution nor D2B model development is authorized by this document.
