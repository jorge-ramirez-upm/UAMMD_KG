# Project roadmap: reuse UAMMD before replacing it

Recorded 16 October 2026 after Stage 4A.2, implementation commit
`cde9d092a29ac3f6fc4f9729992948dd8f09d547`.

This records future priorities and the user's architectural requirements. It
is not authorization to implement refactors, run benchmarks or begin another
scientific stage. All work stays under `examples/slip-springs/`; UAMMD, KG,
KG_Assoc and repository-wide infrastructure remain read-only.

## 1. Protect the current campaign and validated references

The Stage 4A.2 campaign is now complete and accepted on 17 October 2026;
original evidence is archived in `validation/stage4a2-acceptance/`. Each campaign
must finish against its original executable,
parameters, command manifest, frozen validation plan and analysis version.
Documentation changes do not affect its calculations. Do not rebuild or replace
campaign executables, change its scripts, thresholds or inputs, or overwrite its
outputs while it is running. Queued experiments launch binaries by path, so
replacing a binary could mix implementations within one campaign even though
an already-running process continues using its original executable.

Archive the campaign commit, executable hashes, environment, raw data and
analysis. Preserve existing results regardless of subsequent architectural
changes. Stage 4A.2 acceptance is limited to the frozen tested cases/tolerances;
all 456 coarse-bias comparisons were unresolved, so no convergence order is
claimed. Bounded checks alone establish software verification, not scientific
acceptance.
The existing scientifically validated Rouse implementation remains the reference.

## 2. Apply the reuse requirement explicitly

Inspect the actual checked-out UAMMD source before introducing replacements.
Use its existing functionality whenever it meets the scientific contract.
Ponytail's reuse-first rule applies to infrastructure as well as potentials.

The user's acceptance condition for duplicated functionality is that the new
implementation is **simpler, clearer AND faster** than the existing one. All
three need evidence. A passing correctness suite does not establish any speed
advantage, and a shorter kernel alone does not establish lower total complexity.
The present local kernels have no equivalent-UAMMD performance comparison;
claims of superiority are therefore unproven.

Separate missing model-specific behavior from reusable infrastructure. A small
custom potential or diagnostic adapter does not justify replacing an entire
force traversal or integration framework. Preserve the independent CPU
reference for scientific verification; it serves a different purpose from the
GPU simulation infrastructure.

## 3. Semiflexible: prefer UAMMD force infrastructure

The source audit found:

* `BondedForces<BondType,2/3>` already handles heterogeneous pair/three-bead
  records, adjacency traversal, particle-ID mapping and per-particle force
  accumulation without force scatter races. Our gather kernels duplicate these
  capabilities. Their replacement of that infrastructure was insufficiently
  justified.
* `BondedType::Harmonic` supplies the required nondegenerate rest-length spring
  forces and energy. Its collapsed-bond behavior differs from our required
  diagnostics; assess a small local adapter/potential for that difference.
* The checked-out `BondedType::Angular` lacks energy and uses a different force
  coefficient convention. Implementing the exact Kratky–Porod potential locally
  is justified; it can use the existing three-bead bonded framework.
* Zero bending can be implemented by constructing no angular interactor or
  topology. Mixed zero coefficients should be omitted from active records.
  The zero-bending requirement does not itself require custom traversal kernels.

After the campaign and explicit implementation authorization, prepare a local
UAMMD-backed alternative with minimal custom potentials/diagnostics. Preserve
Hamiltonian, heterogeneous indexing, initialization, error behavior, observables,
precision and zero-bending guarantees. Do not modify core or silently switch the
existing executable's implementation before comparison and validation.

## 4. Integration: reuse what fits, retain only required differences

`BD::EulerMaruyama` already implements overdamped Brownian dynamics and computes
all forces before updating positions. Its subsequent position update is safe
with respect to using the same old configuration; an in-place position write
alone is not grounds for rejecting that integrator.

The checked-out stock integrator uses Saru and narrower seed/step counters,
whereas this project's contract specifies stable IDs, explicit Philox domains,
64-bit seed/counters and precision-specific Gaussian generation. Determine how
much existing force/integration orchestration can be reused while preserving
those requirements and failure snapshots. Retain the smallest necessary local
update/adapter; do not silently change RNG semantics to claim code reuse.

## 5. Rouse: preserve first, compare separately

UAMMD harmonic bonds with k=3,r0=0 and Euler–Maruyama represent the Rouse model.
Our specialization fuses neighbor-force calculation and integration into one
launch without a separate force buffer or explicit bond topology. These are
concrete structural advantages, but no measured advantage over an equivalent
UAMMD implementation has been established.

Keep `rouse`, its CLI, RNG domains/trajectories, correlator, tests and accepted
results unchanged. After explicit authorization, build any UAMMD comparison as
a separate local executable. Existing scientific validation remains valid; it
does not prove that the custom implementation is the best architecture. Do not
replace the reference solely for architectural consistency.

## 6. Evidence required before choosing an implementation

For each candidate, document reused components, unavoidable custom code,
maintenance burden and clarity of indexing, ownership, synchronization and errors.
Validate CPU/GPU forces and energies, invariance/conservation, degeneracies,
heterogeneous parameters, zero-bending execution, noise/RNG semantics and
both precisions without weakening existing thresholds.

A later explicitly authorized host comparison must use identical physical
models, chain sizes/counts, timestep, precision, observation cadence and output
policy. Match RNG requirements and diagnostic guarantees; disclose differences
rather than treating reduced checks or sampling as an optimization. Compare
initialization, memory, GPU integration ns/bead/step, observation/output costs
and overall production ns/bead/step, with repeated timings and uncertainty.
Compare total implementation complexity, not just kernel length. Preserve
correctness and scientific acceptance gates independently of performance.

Prefer the UAMMD-backed implementation unless duplicated infrastructure is
shown to meet all three user conditions. Retain local code only for genuine
missing requirements or demonstrated advantages. Any selected replacement needs
its own regression and host scientific validation before inheriting acceptance.

## 7. Stage 4A.3a: static CPU stress theory, pending independent review

The user authorized analytical derivation, a separate CPU stress reference and
bounded CPU tests on 17 October 2026. See [STAGE4A3A_REPORT.md](STAGE4A3A_REPORT.md).
The implementation reuses the accepted Chain parameter validation and direct
sampler, leaving all dynamics/RNG/build/test sources and frozen plans unchanged.

The complete virial is the positive affine derivative W=sum(g outer q), with
explicit stretch and bend terms. Every bending-angle tensor is symmetric and
traceless. Equilibrium has <W>=N*kBT*I, zero mean bending and zero deviatoric
means. Future normalization must preserve explicit chain density and kBT
factors, raw deviatoric channel ordering and stretch/bend cross-correlations.
CPU affine/force-virial and independent metric-tensor checks are implemented;
there is no GPU stress sampling, relaxation calculation or assigned melt modulus.

Before Stage 4A.3b, obtain independent review of the derivation, signs, tensor
indexing, normalization and tests, then explicit implementation authorization.
Future GPU work must follow the reuse-first assessment and reproduce the CPU
angular virial without changing accepted dynamics or weakening existing gates.
No GPU or multi-tau implementation is authorized by this roadmap or Stage 4A.3a.

The user prefers all work expected to exceed **10 minutes** on the dedicated
Linux host. Supply reproducible commands and return-evidence instructions for
that work instead of running it in Codex. Keep local verification bounded and
preserve the existing prohibition on production campaigns. This milestone's
CPU tests take seconds, with no time integration or long run required.

## Stage boundaries

Current authorization is limited to Stage 4A.3a static stress theory/CPU checks
and documentation, while preserving accepted campaign evidence and any running
campaigns. The infrastructure reuse review and comparisons above are future
proposals, not blanket permission for refactoring or optimization. Stage 3 benchmarking/optimization still requires
explicit authorization. Stage 4A.3b GPU stress sampling/correlations, slip-springs,
excluded volume and hydrodynamics remain unauthorized.

Relevant evidence: [Stage 4A.1 assessment](STAGE4A1_REPORT.md),
[Stage 4A.2 report](STAGE4A2_REPORT.md), and the unchanged
[frozen host validation plan](STAGE4A2_VALIDATION_PLAN.md).
