# D1.6E — numerical verification prepared, not executed

**No numerical results were calculated in D1.6E.** The following is an
independently reviewable verification procedure and code, not a completed
verification report. No tests, quadrature, symbolic programs, builds,
preflights, sampling or scientific analyses were run. The explicit execution
restriction takes precedence over the numerical-verification objective.

The [derivation](E1_STAGE_D16E_FORCE_SQUARE_DERIVATION.md) establishes the
analytic expression without relying on the supplied decimals. The standalone
[verification program](tests/d16e_force_square.py) is **UNEXECUTED**, is not
named `test_*.py`, and has no build-target integration. It imports no production
or reference implementation and accesses no historical evidence.

## 1. Quantities to calculate independently

Fixed cohort: N=32, kb=30, b0=T=zeta=1, kappa=0 or 10, a_ss²=5. Use
a=kb/(2*T), x=kappa/T, mu=1/zeta, k_ss=3*T/a_ss². Calculate

    In=int_0^infinity l^n exp[-a*(l-b0)²] dl, n=0,1,2,
    A=I1/I2, B=I0/I2,
    C=int_-1^1 c*exp[x*(c-1)] dc / int_-1^1 exp[x*(c-1)] dc,
    D=int_-1^1 c²*exp[x*(c-1)] dc / int_-1^1 exp[x*(c-1)] dc.

Then evaluate K_bb from the independent derivation, and report separately
K_EM=mu²*(K_bb+k_ss²*a_ss²). “Total coefficient” below means **K_EM**, not K_bb,
and does not include h². Neither number estimates the higher-order remainder.

| Quantity | Supplied external comparison only | D1.6E computed value/status |
|---|---:|---|
| A | 0.967741936179418 | Not computed; unverified |
| B | 0.967741914617288 | Not computed; unverified |
| K_EM, kappa=0 | 63.73548379003136 | Not computed; unverified |
| K_EM, kappa=10 | 161.21348857512433 | Not computed; unverified |

These supplied values appear only in the program's final comparison block,
after its independent integrals, analytic identities and refinement checks.
They are not used as quadrature input, normalization constants, stopping rules,
or substituted force-square expectations. They remain unconfirmed here.

## 2. Deterministic quadrature and independent identity path

The standard-library program uses composite Simpson integration, with
`math.fsum` accumulation, over panel counts 256,512,1024,2048,4096,8192.
It retains each grid's raw radial integrals, normalized moments, angular
normalizers and moments, K_bb, and K_EM. It checks the last two grids but
prints all six so nonmonotone or accidentally small refinement differences
remain visible. No convergence order is inferred from small differences.

The radial range is [0,L], L=b0+12*sqrt(T/kb); a separate 14-thermal-length
cutoff uses the final panel count. The inverse moments are integrated as I1/I2
and I0/I2 after analytic cancellation of l² in the measure, so the code never
evaluates 1/0, clips lengths, drops near-zero intervals, or replaces the half-line
density by a whole-line Gaussian.

A separate half-line evaluation uses

    I0=sqrt(pi)/(2*sqrt(a))*erfc(-sqrt(a)*b0),
    I1=b0*I0+exp(-a*b0²)/(2*a),
    I2=b0*I1+I0/(2*a).

This keeps the finite-boundary term and has positive terms for this cohort,
avoiding subtraction of nearly equal numbers. Comparing quadrature I2 to this
independent normalizer checks total radial probability mass. All three raw
integrals, not just ratios that might hide common normalization errors, are
compared. For kappa=0, a direct integral of
kb²*(l-b0)²*p(l), multiplied by 2*N/(N+1), independently checks K_bb using the
stretch-force square rather than the Laplacian formula.

Angular quadrature uses exp[x*(c-1)]<=1 instead of exp(x*c). Independent
normalization is Z_scaled=-expm1(-2*x)/x for x>0 and 2 at x=0. The identity
path uses C=coth(x)-1/x in an equivalent negative-exponential form, and
D=1-2*C/x. The small-x branch uses the displayed series in the derivation;
x=0 is explicit. This avoids 0/0 and catastrophic cancellation near zero.
Mathematical tests compare x=0, a small positive x and x=10 to quadrature;
none of those tests has been run.

## 3. Tail control and numerical qualifications

For t0=sqrt(a)*(L-b0)>0 define Jn=int_t0^infinity t^n exp(-t²) dt. Then

    J0<=exp(-t0²)/(2*t0),
    J1=exp(-t0²)/2,
    J2=t0*exp(-t0²)/2+J0/2.

The respective I0,I1,I2 tail upper bounds are

    J0/sqrt(a),
    b0*J0/sqrt(a)+J1/a,
    b0²*J0/sqrt(a)+2*b0*J1/a+J2/a^(3/2).

These positive bounds apply at the stated nonnegative b0 and control the
omitted half-line integrals independently of refinement. For exact truncated
integrals in, write In=in+tn; for j=0,1,

    |Ij/I2-ij/i2| <= tj/I2 + ij*t2/(i2*I2).

The program reports the raw tail bounds and requires each below 1e-20.
That is a proposed check, not an evaluated bound in this document. Angular
quadrature covers the full support and has no truncation tail.

Proposed engineering checks: absolute moment/refinement/normalization discrepancy
<=1e-10; absolute K_bb/K_EM identity or refinement discrepancy <=2e-8. The
supplied-value comparison uses the same respective budgets, after independent
checks. These are new deterministic verification budgets, not changes to D0
acceptance criteria or historical reference tolerances. They are intentionally
looser than the decimal strings' last digits: agreement would not certify every
printed digit. The output retains differences through the raw values.

Refinement, recurrence agreement and a tail bound do not certify the total
floating-point/quadrature error: no interval-arithmetic rounding bound or
global Simpson derivative bound is implemented. Inverse raw moments are smooth
integrals here after Jacobian cancellation, but this does not regularize the
simulator's actual small-length force. Library exp/erfc accuracy and binary64
rounding remain numerical assumptions. The script is tailored to this small
cohort and limiting cases, not a general-purpose extreme-parameter integrator.

## 4. Independent mathematical and symbolic checks prepared

`--tests` prepares checks for the Gaussian-bond limit b0=0,kappa=0, correct
N+1 endpoint normalization, no angle at N=1, regular x->0 angular moments,
algebraic removal of the virtual force, its normalized one-sided k_ss->0+
limit, the incidence metric, and the exact quadratic EM coefficient without an
extra factor 1/2. The last uses an explicitly identified harmonic toy and is
not evidence about nonlinear stationary bias.

`--symbolic` optionally requires SymPy (no dependency was installed). It starts
from Cartesian stretch and cosine energies with six independent bond
components, differentiates first, and only then substitutes a frame
q=(l,0,0), p=(m*c,m*sqrt(1-c²),0), with l,m>0 and physical -1<c<1. It checks
the stretch Laplacian, both angle bond Laplacians, mixed Hessian trace and total
three-bead Laplacian. Substituting a frame before differentiation would omit
transverse terms; the program deliberately avoids that error. No symbolic
program was executed and no symbolic test pass is asserted.

Future explicit user commands, **not run during preparation**, from repository
root after independent review:

```sh
python3 examples/slip-springs/tests/d16e_force_square.py --quadrature
python3 examples/slip-springs/tests/d16e_force_square.py --tests
# Optional, only in a user environment already providing SymPy:
python3 examples/slip-springs/tests/d16e_force_square.py --symbolic
```

The commands write to stdout only. Preserve any future outputs in a fresh
permanent location without overwriting historical evidence. A failed assertion
or unresolved symbolic simplification is a failed/unresolved verification,
never permission to weaken a threshold or relabel a supplied number as verified.
