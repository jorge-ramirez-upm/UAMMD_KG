# E1 D1.6A — independent equilibrium reference implementation

**PREPARATION IMPLEMENTED — NO TEST OR NUMERICAL RESULT CLAIMED.**
Starting local and fetched `origin/slip-springs` SHA:
`cca7f0d5f235e4048648d4b159e10ad68311b956`.
Only static source/document inspection and Git preparation are permitted here.
No unit test, import check, quadrature, equilibrium draw, build, preflight,
benchmark, GPU operation or scientific data analysis was executed in Codex.
The implementation needs local readiness testing and independent review.

## Scope and unchanged authorities

Implements the unchanged [D1.6 reference contract](E1_STAGE_D16_REFERENCE_MOMENTS_V1.md),
with its [scientific](E1_STAGE_D16_SCIENTIFIC_DESIGN_V1.md) and
[resource](E1_STAGE_D16_RESOURCE_PLAN_V1.md) authorities. This is a separate
float64 CPU backbone reference. It neither reads simulation trajectories nor
modifies the accepted E1/CUDA model, sampler, RNG, observer, D0 tolerances,
frozen manifests or historical evidence. T100 and larger-system execution
remain unauthorized. A reference-quality result cannot establish dynamical
preservation of E1.

Files and responsibilities:

| File | Responsibility |
|---|---|
| `e1_d16a_reference.py` | Independent radial recurrence/quadrature, exact flexible moments, stiff size means, stable batch inference and precision rules |
| `e1_d16a_sampling.py` | Accepted-sampler worker, three independent phases, retained scalar evidence, read-only result recomputation |
| `e1_d16a_local.py` | Readiness, identity/preflight/approval checks, bounded supervision, authentication, compact packets |
| `tests/test_e1_d16a_reference.py` | Analytical identities and deterministic numerical/protocol tests |
| `tests/test_e1_d16a_local.py` | Synthetic authorization, resource-headroom, integrity and packaging tests |
| `E1_STAGE_D16A_LOCAL_EXECUTION_HANDOFF.md` | Copy-and-paste A/B/C operator workflow |
| This report | Scientific implementation, evidence scope and unresolved limitations |

README adds only a local-workflow pointer. Existing modules are read-only
dependencies. In particular the accepted `semiflexible_reference.py` SHA256 is
`a293806e16c4dcb58188ae680d852a487d5f3b95920222a2bb72b4aee8c17967`.
The existing D1.5 utility supplies strict JSON, SHA256, Git, clean-worktree,
bounded subprocess and sanitized-environment helpers unchanged.

Static repository checks: the read-only sampler hash matches the recorded
identity; the path audit against Stage0 source
`81fe5de9cd5ded849202eebab7c14e6bd35fb9ae` found all tracked differences,
new files and existing ignored artifacts within `examples/slip-springs/`.
`git diff --check` is the only automated change check performed here; it is
not a Python syntax check, test run or numerical validation.

## Analytical calculation and numerical error accounting

For a=15,b=1 use the half-line recurrence including the I1 boundary term:

    I0 = sqrt(pi)/(2 sqrt(a)) erfc(-sqrt(a)b)
    I1 = b I0 + exp(-ab^2)/(2a)
    Ij = b I(j-1) + (j-1)/(2a) I(j-2)
    mu_p = I(p+2)/I2, p=1,...,8.

Independent Gauss-Legendre orders 128/256/512 integrate in
y=(r-b)/sigma from the exact r=0 boundary to H=12, sigma=1/sqrt(2a).
For y>=H, r<=Cy with C=b/H+sigma. Thus the omitted unnormalized jth
integral is bounded above by sigma*C^j*Jj(H), where

    J0=sqrt(pi/2)erfc(H/sqrt(2)), J1=exp(-H^2/2)
    Jj=H^(j-1)exp(-H^2/2)+(j-1)J(j-2).

Propagate both numerator and denominator tails to normalized moments. Report
each quadrature value, analytic upper-tail bound, recurrence discrepancy and
floating-point allowance. Preserve **<1e-11 absolute** order128/256 checks for
mu1,mu2, including the unchanged accepted radial function. Require relative
radial/size-mean numerical error estimates <=1e-10. Variance/covariance errors
are propagated through interval corners in mu2,mu4 and reported separately.

The upper-tail bound is analytical. Refinement spread and the added float64
roundoff allowance are numerical diagnostics, **not certified interval
arithmetic bounds**. This limitation must remain visible in any precision claim.
An independently rigorous floating-point certificate would require a reviewed
interval/high-precision extension; none is silently substituted here.

For m=N+1 and Aij=min(i,j)(m-max(i,j))/m^2, define
t=tr(A), d=sum(Aii^2), h=tr(A^2), s=sum(Aij). Their closed finite sums are
implemented separately from the direct matrix construction used in tests.
With X=Re^2,Y=Rg^2:

    EX=N mu2; EY=t mu2
    VarX=N(mu4-mu2^2)+(2/3)N(N-1)mu2^2
    VarY=(2/3)mu2^2 h+(mu4-5mu2^2/3)d
    CovXY=t(mu4-mu2^2)+(2/3)mu2^2(s-t)
    EX^2=N mu4+(5/3)N(N-1)mu2^2
    EY^2=VarY+(t mu2)^2
    EXY=CovXY+N t mu2^2.

Here EX^2 means E[X^2], not (EX)^2. Unit tests cover direct finite sums,
the general bilinear quadratic-form covariance, symmetry/PSD, N1's Y=X/4,
fixed-length limit, and artificial Gaussian-vector algebra only as a check.
The physical target remains the nonlinear finite-rest-length radial law.
The b=0 gamma-integral limit supplies an additional independent radial check.

For kappa10, c=coth(10)-1/10 and
B(k)=k mu2+2 mu1^2 sum_(s=1)^(k-1)(k-s)c^s give exact EX and
EY=sum_k(m-k)B(k)/m^2. No flexible fourth-moment formula is used for stiff
chains. Fourth-order angular transfer/quadrature for stiff variances remains
an optional future independent cross-check, not an implemented claim.

## Independent sampling, stable estimates and family allocation

The worker calls unchanged `Chain.homogeneous(32,1,30,kappa).sample(512,rng,kbt=1)`.
It anchors translation as the accepted sampler does. NumPy PCG64 uses
`SeedSequence([721610000,kappa,phase,batch_index])` with zero-based batch
indices and phase IDs 1/2/3. Readiness tests audit generated identities over
both entire maximum seed namespaces; executed batch ledgers record entropy,
generated four-uint32 identities and full PCG64 before/after states. Distinct
namespaces and a collision check do not prove mathematical RNG independence.
Ordinary rejection inside the accepted exact radial sampler is intentional;
retry exhaustion, nonfinite/invalid chains and incomplete batches abort the
case. No chain is dropped or replaced to improve a result.

Phase1: 65536 calibration chains; nearest-rank ceil(S*p) thresholds at the nine
frozen probabilities per observable; store original and sorted scalar arrays,
cuts, binomial order-statistic rank intervals (diagnostic 18-cut family).
Phase2: 8192 independent sizing chains; no reuse for final inference.
Phase3: one fixed count selected from 16384/32768/65536/131072/262144/524288,
using new independent batches. No count can change after final draws begin.
Maximum is 598016 chains/stiffness over all three phases.

The final-quality family has **50 quantities**, 25/stiffness: two means,
two variances, covariance, two fourth-length moments, 18 CDF values; alpha=.05.
Pilot predicted half-width is

    t_(31,1-.05/(2*50)) * 2 * SE_pilot * sqrt(8192/S).

Select the first grid count satisfying all applicable targets or stop before
final sampling. At kappa0, known analytic values scale the precision targets;
at kappa10 the sizing/final moment estimates scale them as prescribed. Exact
means are primary references and do not consume Monte Carlo precision budgets.

Each batch retains count, X/Y mean and central cross-sum M2, all 23 W means,
first-five within-batch W covariance, integer CDF counts, extrema, X^4,Y^4,
X^2Y^2 diagnostics and radial/tangent diagnostics. Across independent batches,
retain the full covariance of mean W and the transformed 25-estimator covariance.
The first-five within-batch covariance is not misrepresented as a full 23x23
within-batch covariance; the stored scalar arrays retain the latter's inputs.

Central M2 merging gives unbiased VarX,VarY,CovXY using S/(S-1), avoiding
subtraction of large raw moments. For uncertainty, centered batch influence
values implement the specified delta gradients algebraically, including the
finite-S factor. Whole-batch delete-one jackknife SEs are independently
calculated using central-moment removal; their differences are diagnostics,
not a retrospectively chosen acceptance threshold. Full scalar X/Y evidence
is retained for further independent analysis without particle coordinates.

Final batch-t/delta intervals use B-1 degrees of freedom. At frozen cuts,
exact two-sided Clopper-Pearson beta intervals use alpha/50. Target probabilities
are F(q_hat), not automatically calibration p. Half-width is the larger distance
from the point estimate to either interval endpoint, including zero/full counts.
Calibration is excluded from these evaluation intervals.

Exactly one final assessment checks relative half-width <=.05 for variances
and E[X^2],E[Y^2]; covariance half-width <=.05 sqrt(VarX VarY); all CDF
half-widths <=.005; and analytical consistency of means plus all seven flexible
references. The deterministic error band must fit inside each corresponding
nominal consistency interval. An unmet condition is explicitly unresolved.
Radial/tangent and high-moment diagnostics are retained for review; they are
not extra uncounted tests added to the frozen 50-quantity pass family.

`PRECISION_RESOLVED_NOMINAL` is intentionally qualified: batch-t/delta intervals
are CLT approximations, particularly for high moments. Review tail/batch
stability and jackknife discrepancies before accepting reference quality.
The .05 reference-quality allocation is not automatically the future campaign's
reference-error allocation. A confirmatory .01 reference allocation requires
recomputing intervals and precision using retained evidence or a new approved
design; never claim .05 overall coverage by combining separate .05 families.

## Exact-E1 joint-score interpretation

Report v_f=VarX/(EX)^2, Var(A_joint)=v_f/256,
Var(B_joint)=2v_f/(3*2048), and zero cross covariance. For kappa0 these use
analytic radial/flexible results; for kappa10 they are plug-in values with
intervals propagated from final VarX and deterministic mean error. Zero
cross covariance does not imply independence. These instantaneous null laws
do not grant chain independence or temporal independence to evolved data.

## Execution, resources and evidence

Use the [operator handoff](E1_STAGE_D16A_LOCAL_EXECUTION_HANDOFF.md).
Readiness snapshots the clean fetched revision to durable external storage;
records Python, NumPy/SciPy code/native-library and mapped-library identities;
runs deterministic CPU/numerical checks under bounded subprocess timeouts;
and creates a false approval template. It performs no Chain.sample calls.
NumPy and SciPy must already be installed; no automatic downloads or new build.

A separate reviewed approval with trusted SHA256 is mandatory. It binds the
readiness/session/configuration/numerical/dependency identities and fixed limits.
The two stiffness cases are separately single-use. A root-level exclusive lock
prevents concurrent execution. No retry, continuation, resume, alternate seed,
partial-final-batch acceptance or automatic sample extension exists.
The Linux worker installs a parent-death SIGKILL guard before drawing, so loss
of its resource supervisor cannot leave an unsupervised sampler running.

Caps: 30s/batch, 1200s/stiffness (supervised execution plus post-run identity
authentication), 1GiB conservative worker+supervisor RSS high-water sum, and
16MiB/stiffness including phase data and stiffness-specific metadata/logs.
Shared readiness provenance and return packets are separate from case data.
CPU-only live headroom guards require 2GiB available RAM and 1GiB free disk;
these explicit conservative proposals must be reviewed with the approval.
They do not alter old GPU limits. Polling is 50ms; OS high-water checks catch
short-lived worker RSS peaks. Worker checks include batch write time. Polling
is not a hard real-time allocation interceptor. A kernel/process kill can leave
partial files, which are preserved and never accepted as a completed case.

Raw scalar payload at maximum is two arrays per chain across the three phases
plus a sorted calibration copy: 10.125MiB/stiffness before small NumPy headers.
Batch ledgers, inference, provenance and resource records add variable overhead;
the actual 16MiB cap is enforced, not promised from an unmeasured compression
ratio. Full coordinates are not stored. The packet contains JSON/JSONL/logs,
including every executed batch and seed; scalar arrays remain local with
absolute paths, sizes and hashes. Identical environment snapshots are
deduplicated against the retained primary bytes, with a receipt for each probe;
any changed environment snapshot is retained in full, including in error packets.
Packets stop at 8MiB uncompressed rather than silently drop results.

Stage C reauthenticates local inventories and recomputes cuts, sufficient
statistics, selection, inference and precision assessment from saved scalar
data. It creates no new equilibrium samples. SHA256 is integrity/provenance
binding with an externally reviewed approval anchor, not a digital signature
or defense against an adversary replacing every local record. Preserve trusted
archive/approval/completion digests outside mutable evidence as appropriate.

## Unresolved items requiring local execution/review

1. All new tests and numerical checks are **unexecuted**. No dependency version,
   measured runtime/RSS/output total or numerical moment value is asserted.
2. The conservative factor2 pilot rule with t31 can exhaust the grid at central
   CDF cuts even when a less conservative final interval might fit. It remains
   frozen; unresolved sizing needs a new reviewed amendment, not a fallback.
3. Pilot uncertainty from 16 batches is imprecise. No final-SE prediction is a
   guarantee; an unsuccessful final assessment stops without more draws.
4. Nominal high-moment CLT coverage and delta/jackknife robustness need actual
   evidence review. Neither a positive precision flag nor kappa0 agreement
   proves the kappa10 angular fourth moments independently.
5. Numerical roundoff estimates are not certified interval bounds. Tail bounds
   and empirical refinement are recorded separately to expose that distinction.
6. A hard interruption can leave the exclusive run lock and incomplete evidence;
   stop for operator review, never remove it to resume or adopt partial samples.
7. No approval record is granted here. A/B/C commands are prepared, not claimed
   to have run. Dynamical E1 preservation, T100, D2 and rheology remain separate.
