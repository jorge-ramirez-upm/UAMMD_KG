# Stage 4A.3c Gaussian-control scientific audit

18 October 2026 (Europe/Madrid). Read-only scientific audit at clean local and
fetched `origin/slip-springs` commit
`4e46d6014aa812b1fc687335654c4b1f681ddd22`. This report is the only repository
change. No simulation, integrator, analyzer, threshold, protocol, existing result
or executable was modified; no simulation or campaign was executed.

**Recommendation: conditional proceed to nonlinear N=8 validation, with separate
user-host execution authorization.** The completed Gaussian streams agree with
their exact finite-step reference under the frozen gates. Resolving an order of
timestep convergence is not a prerequisite established by those gates. This is
not full Stage4A.3c acceptance, authorization to execute, or validation of the
nonlinear model's relaxation spectrum.

## Evidence actually inspected

The supplied directory **was available**:
`/tmp/semiflexible-compact-host.CCBNa7/compact-v1`. Its saved report was generated
at `2026-10-18T09:32:55.902302+00:00`. The original/derived manifests, profile,
plan, source pins and analyzer version authenticate with the unchanged
`authenticate()` and profile-authentication functions. The canonical manifest
identity is `d81fee5eddc52a8b2f1bf9190bda26c19808168b21030116684cd68ee05ecf1f`;
this is distinct from the SHA256 of the serialized manifest file below.

| Evidence | SHA256 of existing file bytes |
|---|---|
| manifest.json | `7b16928c75e8ea00e0aa9ef2e5561107a2bf05f9ffc8a98c95d35ad40ecd142f` |
| execution-profile.json | `3dee19b2a93bc60f8c43a62ac48aac2c8c1e4c5f42a8c97cf0fe818463a39678` |
| scientific-analysis.json | `f788353628d6a27b1e9b00396e4f2dff9ec31a2fbaec88d4686824c5575e0996` |
| analysis-checkpoint.json | `58a0e66eedf0f7f5fd140a95e8d981aeb95405c38c97ac88711672bbb976e82a` |
| campaign-provenance.json | `81f6bf3e7e8949e099c324a17d516fd683335470c6d768f41b3cf58231442950` |
| validation-plan.md | `efd040ceba8cd903dee7a145296dce08435e3df3efa940c65170f4bcf98acb36` |

The saved analysis version matches the current implementation:
`09e01b70d42cbe2aaeb4ac536f4c5bbdfe6437e2f6cda129079d5ef68ff26565`.
Its status counts are58995 passed,5513 statistically_unresolved_bias,
265 missing_data,127 missing_provenance, and no failed checks. Overall and
scientific status are both **incomplete**. “282 analyzed” includes records for
missing runs; it does not mean282 simulations completed.

All18 Gaussian streams were freshly checked with the read-only `validate_run()`
function, without invoking the checkpoint-writing campaign analyzer. Correlation
rows and scientific checks matched the saved analysis exactly. Every file listed
in their completed execution receipts was SHA256-verified (179,000,646 bytes in
total), as were both current executables against the ledger. Their hashes are:

* Single: `fe962d1a3274669dffd2e50cd031069161c508f189b5256fc2987042dc71d08d`.
* Double: `a622ab8e391a166dfd0d143df855f477ff790ecfc4a7708dcd6f3bd4bcb1cf84`.

This independently checks stored observations/summaries and theory comparisons;
it does not replay trajectories. Compact streams do not retain complete stress
or coordinate histories. The54 diagnostic and54 direct-reference outcomes below
are inspected saved-analysis evidence, not a fresh rereading/recomputation of
all their raw CSVs. No existing evidence file was rewritten or copied into Git.

## Mathematical verification

Sources: [frozen plan](STAGE4A3C_VALIDATION_PLAN.md), gates3–6 and estimator
section; [analyzer](tests/semiflexible_stress_analysis.py), `gaussian_reference`,
`correlation_rows`, `validate_run`, `refinement`, `campaign_comparisons`;
[GPU dynamics](semiflexible.cuh), `stretch`, `gaussian`, `update`;
[driver](semiflexible.cu), `initialize`, `simulate`;
[virial reference](semiflexible_stress_reference.py).

Write theta=kBT, M=N+1, and D for the N-by-M incidence matrix with each row
(-1,+1). The Gaussian control is precisely b0=0,kb=3,kappa=0, so

\[
 U=\tfrac12\sum_\alpha r_\alpha^T K r_\alpha,
 \quad K=3D^TD,
 \quad \lambda_p=12\sin^2[p\pi/(2M)],\quad p=1,\ldots,N.
\]

K has free-end diagonal entries3, interior entries6, adjacent entries-3, and
one zero translation mode. There are N internal modes, not N+1 restoring modes.
The first bead starts at the origin but is not pinned during integration. The
anchored equilibrium bond ensemble projects onto independent internal Gaussian
modes of variance theta/lambda_p. Its initially correlated center of mass does
not enter the force or virial; subsequent center-of-mass Brownian motion has
diffusion theta/(M*zeta). No center-of-mass subtraction changes the stress.

For h=dt the code's stored-precision coefficients are

\[
 \mu=\operatorname{real}(h/\zeta),\qquad
 \eta=\operatorname{real}(\sqrt{2\theta h/\zeta}),\qquad
 a_p=1-\mu\lambda_p,
\]
\[
 X_{p,\alpha}(n+1)=a_pX_{p,\alpha}(n)+\eta\xi_{p,\alpha}(n).
\]

Orthogonal transformation preserves the independent unit Gaussian noise
covariance. The metadata records both rounded coefficients, which the analyzer
validates. The dynamics uses old/new buffers, eight reserved Philox draws per
bead/step and stable IDs/domain3. The analytical covariance is

\[
 v_p(0)=\theta/\lambda_p,\quad
 v_p(n+1)=a_p^2v_p(n)+\eta^2,\quad
 v_p(n)=v_{*,p}+\delta_pa_p^{2n},
\]
\[
 v_{*,p}=\eta^2/(1-a_p^2),\quad
 \delta_p=\theta/\lambda_p-v_{*,p},\quad
 C_p(m,n)=a_p^{|m-n|}v_p(\min(m,n)).
\]

Continuous-equilibrium initialization is not the stationary EM distribution.
The transient delta term is therefore required and is present. With unrounded
coefficients, v_star=theta/[lambda*(1-h*lambda/(2*zeta))]. Replacing it by
theta/lambda silently loses finite-step variance inflation. `gaussian_reference`
requires0<a_p<1; that is satisfied here. It does not implement every stable
oscillatory EM multiplier (-1<a_p<=0), and should not be generalized to them.

The positive affine virial is

\[
 W_{\alpha\beta}=3\sum_iq_{i\alpha}q_{i\beta}
                 =\sum_p\lambda_pX_{p,\alpha}X_{p,\beta}.
\]

Gaussian factorization gives the raw shear correlation
P(m,n)=sum_p lambda_p^2*C_p(m,n)^2. Each raw normal-difference autocorrelation
is4P: the two diagonal variances each supply2P and the Cartesian cross term
cancels its disconnected contribution. Raw channel order is
xy,xz,yz,xx-yy,xx-zz,yy-zz, without half factors. Thus

\[
 H=(C_{xy}+C_{xz}+C_{yz})/5
   +(C_{xx-yy}+C_{xx-zz}+C_{yy-zz})/30=P.
\]

The analyzer uses factor1 for shears/H,4 for normal differences, and1/theta²
for g. With explicitly supplied chain density, G=n_chain*H/theta. No physical
density or melt volume is assigned to the main streams. Ensemble deviatoric
means vanish, so raw and ensemble-connected deviatoric covariances agree here;
empirical trajectory means are never subtracted. The full configurational mean
is hydrostatic, not zero: initially N*theta*I, with EM internal variance inflation
at later times. This derivation is specific to the Gaussian control.

“Exact discrete” means the linear Gaussian EM model using the recorded rounded
drift/noise scales. It does not model every floating-point force normalization,
coordinate rounding, fused arithmetic operation or finite-PRNG effect exactly.
Agreement is tested at the frozen tolerances, not bitwise against real algebra.

## Acquisition and multi-tau estimator

For stride s, sample spacing Delta=s*h, F=floor(S/s)+1 includes step0. All18
main Gaussian streams have N8,C2048,T100,Delta0.002,F50001, three seeds
433201–433203, both precisions and h0.001,0.0005,0.00025 (strides2,4,8).
They have200 exported bins per run.

For block width B and exported lag ell in original sample units, the complete
blocks are z[k]=(1/B)sum_(u=0)^(B-1) y[kB+u]. The per-chain raw estimator is

\[
 Q_c(\ell,B)=\frac1O\sum_{k=0}^{O-1}z_c[k+\ell/B]z_c[k],
 \quad O=\lfloor F/B\rfloor-\ell/B.
\]

Its exact shear expectation is

\[
 \frac1{OB^2}\sum_{k,u,v,p}\lambda_p^2
 C_p\big(s(kB+u),s(kB+\ell+v)\big)^2.
\]

The implementation expands v(n)^2 and performs these sums geometrically using
`stream_analysis.geometric_mean`, with stable expm1 ratios. It squares each
two-time covariance before averaging; it does not square an averaged covariance.
Incomplete final blocks are truncated, never padded. The complete finite origin
window is included. Coarse products are block-averaged stresses, not stress at a
single nominal lag; offset delays span (ell-B+1)..(ell+B-1) sample spacings.
`lag_grid` and CSV validation enforce bin count/order, block widths, pair counts
and lag_time=ell*Delta, including the inherited deepest-level export omission.

Sources: [streaming adapter](semiflexible_stress_stream.h), `Correlations`;
[shared bank](stream_correlator.h), `Bank::write`, `Moments`;
[direct oracle](tests/semiflexible_stress_analysis.py), `direct_reference`.
The bank forms each chain's H before aggregation, preserving channel covariance.
SE is sd(Q_c)/sqrt(C), with sample variance denominator C-1. Time origins and
channels are not counted as independent chains. Final-half moments use their
own original window step>=floor(S/2); correlation estimators use all frames.

At the last Gaussian bin, lag94.208 has B2048 (width4.096) and one pair per
chain. Across2048 independent chains this is still an estimator with a chain SE;
it is not2048 independent time-origin histories per chain, or resolved terminal
signal. The absolute floor can dominate very small late-time predictions.

The continuum expression is theta²*sum exp(-2*lambda_p*t/zeta), with corresponding
block-offset averaging for coarse bins. It lacks EM inflation and transient
variance, and is not the reference used for these per-run gates.

## What the classifications actually mean

`gate()` passes when |observed-target| <=6*hypot(SE,reference_SE)+allowance.
For per-run Gaussian bins the allowance is
max(0.002*N*theta²*factor,0.01*abs(prediction*factor)). It checks all exported
bins/channels/H/g, not merely a selected positive-signal subset.

`refinement()` first checks finest versus middle using6 combined SE plus1%
of the supplied scale. For an independent target R it then sets

\[
 e_c=|M_c-R|,\quad e_f=|M_f-R|,\quad
 \text{resolved}: e_c>6\sqrt{s_c^2+s_R^2},
\]
\[
 e_f\le0.75e_c+6\sqrt{s_f^2+0.75^2s_c^2+1.75^2s_R^2}.
\]

If no component meets “resolved”, the second check is
`statistically_unresolved_bias`. Otherwise resolved components must meet the
25%-reduction inequality. The routine does not estimate an order or require
monotonicity over all three timesteps. The code explicitly permits unresolved
statuses in successful scientific aggregation; missing data/provenance determine
the present incomplete status.

The actual5513 unresolved entries split as follows:

* **5507 Gaussian residual checks:** for bins where middle or finest empirical
  signal exceeds6SE, `campaign_comparisons()` subtracts EACH timestep's exact
  EM prediction first. It passes residuals M_c-P_c and M_f-P_f to `refinement`
  with target0, retaining only its second check. All5507 have no coarse residual
  beyond6SE. This means unresolved discrepancy from the exact finite-step model,
  not unresolved discrepancy from the continuum model. Requiring these residuals
  to shrink would test reduction of model/numerical/sampling discrepancy after
  known EM effects are removed; it is not a direct measurement of EM convergence.
* **6 final-half mean checks:** one six-component check per precision/seed uses
  target0. No coarse deviatoric mean component exceeds6SE. Zero is also the exact
  symmetry prediction for finite-step EM, so these are not measurements of its
  hydrostatic or correlation discretization bias.

The missing CPU equilibrium-reference catalog means no reference-based
coarse-bias reduction check for the raw equal-time product matrices was emitted.
Their finest-middle consistency checks did run. Thus “all timestep biases are
unresolved” is too broad a conclusion from these labels.

For illustration, double-precision,seed433201, zero-lag H:

| h | Finite-acquisition EM prediction | Observed H | Chain SE |
|---|---:|---:|---:|
| 0.001 | 8.048271935472 | 8.049796070114 | 0.008630544189 |
| 0.0005 | 8.024057611259 | 8.020736766299 | 0.008636648606 |
| 0.00025 | 8.012009311206 | 8.004541273770 | 0.008758932478 |

The continuum point-lag target is8. The known theoretical coarse correction
is about0.04827 even though the EM residual is unresolved. Single seed433201
coarse H lies6.0467SE above8 (before allowances), while its residual to EM is
only0.5222SE. These are descriptive comparisons, not new acceptance gates or
proof of a measured convergence order. No such order is established here.

## Passed checks and their independence

Fresh read-only validation reproduced **28800/28800 Gaussian per-run theory
gates** (18 runs*200 bins*8 quantities), plus18 final-half zero-mean gates.
Maximum absolute theory residual was3.88145 chain SE; maximum fraction of the
frozen allowed difference was0.488614, for single/seed433202/h0.0005,
Cxz at lag672 samples. These200*8 values are strongly correlated, not1600
independent confirmations per run or a simultaneous confidence statement.

Saved Gaussian campaign checks additionally show:

| Check | Passed | Unresolved |
|---|---:|---:|
| Worker/batch byte replay | 2 | 0 |
| Finest-middle static means/products | 12 | 0 |
| Coarse zero-mean residual | 0 | 6 |
| Finest-middle resolved-bin correlations | 5507 | 0 |
| Coarse Gaussian-model residual | 0 | 5507 |
| Pairwise seed static comparisons | 36 | 0 |
| Pairwise seed resolved-bin comparisons | 16524 | 0 |

The54 saved direct-reference runs include six Gaussian runs: C64,F8193,
theta1.7,density0.25,h0.001, workers/batches1/1,2/7,4/32 in both precisions.
Each has160 bins, direct block/channel/H/SE checks and byte-identical replay
within its precision. These contribute another7680 passed Gaussian theory
gates, for36480 including main streams. The three worker configurations replay
the same seed433201; they are implementation comparisons, not three independent
statistical replicas. The54 diagnostic runs passed their stored tensor/initial
moment checks. Those per-run successes do not fill the missing independent CPU
equilibrium-ensemble comparisons required by gate3.

Authenticated prerequisite logs pass both7-test GPU suites and compact checks.
Their Gaussian smoke test is N2,theta1.7,40 steps, against the established Rouse
discrete reference; it is a small implementation check, not the N8 host result.
This audit reran only the pure CPU existing fixtures
`test_exact_gaussian_reference_against_explicit_mode_covariances` and
`test_statistical_pass_fail_unresolved_and_terminal_support`, without their GPU
setUpClass. Both passed. The former explicitly sums four point/block bins with
rounded drift/noise and perturbs noise to detect a wrong prediction.

An additional ephemeral, independent bead-matrix calculation used K=3D^TD,
P=I-11^T/M, A=P(I-mu*K)P, C0=P*(theta/3*L*L^T)*P (anchored-bond accumulation L),
and C(n+1)=A*C(n)*A^T+eta²*P. Direct block-offset sums of
Tr(K*Cab*K*Cab^T) matched `gaussian_reference` in24 cases (N1,3,8; float/double
rounded coefficients; theta1.7,stride3,F17; four point/block bins). Largest
absolute error was6.21725e-13, below the stated2e-11 check bound. This checks
the formula through bead-space recurrences, not another copy of its geometric
algebra. Neither this calculation nor any new test was added to production code.
Checks were timeout-bounded at30/120 seconds; no GPU or long experiment ran.

Independent-chain clustering correctly retains intra-chain time correlations
and H's cross-channel covariance. The three different seeds support replica
comparisons; they do not make different lags independent. Same-seed runs across
timesteps reuse initialization and indexed random streams, so they need not be
statistically independent. The frozen finest-middle and residual bounds use
hypot(SE1,SE2), not measured paired cross-timestep covariance. Positive pairing
would make that estimate conservative; unknown pairing does not guarantee this.
There is no paired-chain refinement error analysis or formal simultaneous-test
calibration here. No empirical-mean subtraction or independence of origins was
silently introduced. These limits do not negate the per-run Gaussian agreement.

## Remaining gaps and recommendation boundary

The265 missing-data checks comprise155 absent-run records,108 absent65536-chain
CPU equilibrium-reference comparisons, and two incomplete nonlinear pilot
timestep/seed matrices. Memory experiments and the rest of the nonlinear stream
matrix are not complete. All127 completed runs lack an original compilation
transcript: stored executable/source/command identities are verifiable, but
system CUDA11.5.119 and the driver's displayed CUDA capability do not establish
which toolkit compiled the binaries. A new build cannot retroactively prove it.

There is no Gaussian-theory failure requiring a changed integrator, thresholds,
longer Gaussian runs or resolved EM-residual trend before the next scientifically
reviewed N8 experiments. Conditional progression is justified by the per-run
agreement, mathematical/reference checks and estimator validation. Preserve the
missing-evidence classifications; complete the original independent equilibrium,
nonlinear timestep/replica/terminal and memory gates before acceptance. Do not
assign Gaussian terminal behavior to finite-rest-length chains, fit a tail,
extrapolate viscosity, or pool all bins/precisions as independent evidence.

This audit commit changes HEAD. The runner's existing `provenance()` guard
requires the clean execution checkout SHA to equal the frozen ledger SHA4e46d60.
Do not change that ledger or guard to resume from a new HEAD. Future authorized
execution needs a preserved clean4e46d60 checkout and the pinned existing binary/
input paths, or a separately reviewed provenance arrangement. Documentation does
not change already-running processes, but that launch guard is operationally
relevant. This audit neither resumes nor authorizes any experiment.

## Compact read-only user-host evidence commands

No missing Gaussian trajectory dataset is requested: the stored compact evidence
was accessible and the per-run checks were reproduced. The remaining compiler
proof needs an authentic historical build transcript if one exists. Do not
manufacture one. To return compact updated status and unresolved categories,
without regenerating analysis, writing checkpoints or exporting raw samples:

```sh
H=/tmp/semiflexible-compact-host.CCBNa7/compact-v1
sha256sum "$H/manifest.json" "$H/scientific-analysis.json" "$H/validation-plan.md"
python3 -B - "$H" <<'PY'
import collections,json,sys
from pathlib import Path
h=Path(sys.argv[1]);d=json.loads((h/'scientific-analysis.json').read_text())
print({k:d[k] for k in ('generated_utc','manifest_hash','analysis_version',
                       'overall_status','scientific_status','status_counts')})
c=collections.Counter(('Gaussian residual' if 'Gaussian residual' in g['name']
                       else 'other',g['status']) for g in d['campaign_checks'])
print('campaign categories:',dict(c))
for name in ('equilibrium-references.json','compiler-build-transcript.txt'):
    p=h/name;print(name,'present' if p.is_file() else 'absent')
PY
```

For a small per-Gaussian-run quantitative extract, from the repository root:

```sh
PYTHONPATH=examples/slip-springs/tests python3 -B - "$H" <<'PY'
import sys
from pathlib import Path
import semiflexible_stress_analysis as a
h=Path(sys.argv[1]);runs,ids,mhash=a.authenticate(h)
d=a.load(h/'scientific-analysis.json');assert d['manifest_hash']==mhash
for r,i in zip(runs,ids):
    if r['phase']!='stream' or r['label']!='gaussian-control':continue
    x=d['runs'][i];g=[v for v in x['checks'] if v['name'].startswith('Gaussian ')]
    z=x['correlations'][0]
    print(r['precision'],r['seed'],a.options(r)['dt'],len(g),
          all(v['status']=='passed' for v in g),
          'H0/SE',z['H'],z['H_se'],
          'max allowance fraction',max(abs(v['observed']-v['expected'])/
                                      v['allowed_difference'] for v in g))
PY
```

These commands inspect saved results; they do not run the checkpoint-writing
`campaign analyze` action. Missing independent CPU ensembles or nonlinear/memory
runs require separate host execution authorization, not a change to this audit's
conclusions or the frozen criteria.
