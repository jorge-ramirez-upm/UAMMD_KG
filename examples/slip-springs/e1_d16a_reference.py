"""Independent D1.6A radial, flexible-chain and batch-inference references.

No calculation runs on import. NumPy and SciPy are explicit local dependencies.
X=Re^2 and Y=Rg^2; X^2,Y^2 are fourth LENGTH moments, not X^4,Y^4.
"""
import math

import numpy as np
from scipy.stats import beta, binom, t

BATCH = 512
CALIBRATION = 65536
PILOT = 8192
GRID = (16384, 32768, 65536, 131072, 262144, 524288)
PROBABILITIES = (.01, .05, .10, .25, .50, .75, .90, .95, .99)
ALPHA = .05
FAMILY = 50
SAMPLER_SHA = 'a293806e16c4dcb58188ae680d852a487d5f3b95920222a2bb72b4aee8c17967'
NAMES = ('mean_X', 'mean_Y', 'var_X', 'var_Y', 'cov_XY', 'mean_X2', 'mean_Y2') + tuple(
    f'cdf_{name}_{p:g}' for name in ('X', 'Y') for p in PROBABILITIES)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def radial_recurrence(a=15., b=1., maximum=10):
    require(a > 0 and b >= 0 and maximum >= 2, 'invalid radial parameters')
    values = [math.sqrt(math.pi)/(2*math.sqrt(a))*math.erfc(-math.sqrt(a)*b)]
    values.append(b*values[0]+math.exp(-a*b*b)/(2*a))
    for j in range(2, maximum+1):
        values.append(b*values[-1]+(j-1)/(2*a)*values[-2])
    return {str(p): values[p+2]/values[2] for p in range(1, maximum-1)}


def radial_quadrature(order, a=15., b=1., maximum=10):
    """Independent finite-interval Gauss-Legendre integral + analytic upper tail.

    y=(r-b)/sigma, sigma=1/sqrt(2a); integrate from the EXACT r=0 boundary
    to y=12. For y>=12, b+sigma*y <= (b/12+sigma)*y bounds every tail.
    """
    sigma, high = 1/math.sqrt(2*a), 12.
    low = -b/sigma
    nodes, weights = np.polynomial.legendre.leggauss(order)
    y = (high+low)/2+(high-low)/2*nodes
    radius = b+sigma*y
    weights = weights*np.exp(-y*y/2)*sigma*(high-low)/2
    integrals = [float(weights @ radius**j) for j in range(maximum+1)]
    tails = [math.sqrt(math.pi/2)*math.erfc(high/math.sqrt(2)), math.exp(-high*high/2)]
    for j in range(2, maximum+1):
        tails.append(high**(j-1)*tails[1]+(j-1)*tails[j-2])
    tails = [sigma*(b/high+sigma)**j*tail for j, tail in enumerate(tails)]
    moments = {str(p): integrals[p+2]/integrals[2] for p in range(1, maximum-1)}
    bounds = {str(p): (tails[p+2]+moments[str(p)]*tails[2])/integrals[2]
              for p in range(1, maximum-1)}
    return {'moments': moments, 'tail_absolute_bound': bounds}


def matrix_a(n):
    i = np.arange(1, n+1)
    return np.minimum(i[:, None], i)*(n+1-np.maximum(i[:, None], i))/(n+1.)**2


def quadratic_covariance(b, c, mu2, mu4):
    return float(2*mu2**2/3*np.trace(b @ c)
                 +(mu4-5*mu2**2/3)*np.dot(np.diag(b), np.diag(c)))


def flexible(n, mu2, mu4):
    require(n >= 1 and mu2 > 0 and mu4 >= mu2**2, 'invalid isotropic bond moments')
    m = n+1
    trace = (m*m-1)/(6*m)
    diagonal = (m**4-1)/(30*m**3)
    square = (m*m-1)*(2*m*m+7)/(180*m*m)
    total = (m*m-1)/12
    vx = n*(mu4-mu2**2)+2/3*n*(n-1)*mu2**2
    vy = 2/3*mu2**2*square+(mu4-5*mu2**2/3)*diagonal
    cov = trace*(mu4-mu2**2)+2/3*mu2**2*(total-trace)
    return dict(mean_X=n*mu2, mean_Y=trace*mu2, var_X=vx, var_Y=vy, cov_XY=cov,
                mean_X2=n*mu4+5/3*n*(n-1)*mu2**2,
                mean_Y2=vy+(trace*mu2)**2, mean_XY=cov+n*trace*mu2**2)


def size_means(n, kappa, mu1, mu2):
    c = 0. if kappa == 0 else 1+2/math.expm1(2*kappa)-1/kappa
    spans = {k: k*mu2+2*mu1**2*math.fsum((k-s)*c**s for s in range(1, k))
             for k in range(1, n+1)}
    return {'mean_X': spans[n],
            'mean_Y': math.fsum((n+1-k)*spans[k] for k in spans)/(n+1)**2}


def numerical_checks():
    from semiflexible_reference import radial_moments
    recurrence = radial_recurrence()
    quads = {str(order): radial_quadrature(order) for order in (128, 256, 512)}
    accepted = {str(order): list(radial_moments(1, 30, order=order)) for order in (128, 256, 512)}
    errors = {}
    for p, value in recurrence.items():
        spread = max(abs(q['moments'][p]-value) for q in quads.values())
        # This roundoff allowance is an engineering estimate, not interval arithmetic.
        errors[p] = spread+max(q['tail_absolute_bound'][p] for q in quads.values())+128*np.finfo(float).eps*abs(value)
        require(errors[p] <= 1e-10*abs(value), 'radial numerical accuracy unresolved: '+p)
    for j, p in enumerate(('1', '2')):
        require(abs(accepted['128'][j]-accepted['256'][j]) < 1e-11,
                'accepted radial 128/256 check failed')
        require(abs(quads['128']['moments'][p]-quads['256']['moments'][p]) < 1e-11,
                'independent radial 128/256 check failed')
        require(max(abs(accepted[o][j]-recurrence[p]) for o in accepted) < 1e-11,
                'accepted radial/reference disagreement')
    exact = flexible(32, recurrence['2'], recurrence['4'])
    # Interval-corner propagation keeps cancellation error separate from radial error.
    corners = [flexible(32, recurrence['2']+s*errors['2'], recurrence['4']+u*errors['4'])
               for s in (-1, 1) for u in (-1, 1)]
    propagated = {name: max(abs(c[name]-v) for c in corners)+256*np.finfo(float).eps*abs(v)
                  for name, v in exact.items()}
    means, mean_errors = {}, {}
    for kappa in (0, 10):
        means[str(kappa)] = size_means(32, kappa, recurrence['1'], recurrence['2'])
        mean_corners = [size_means(32, kappa, recurrence['1']+s*errors['1'], recurrence['2']+u*errors['2'])
                        for s in (-1, 1) for u in (-1, 1)]
        mean_errors[str(kappa)] = {name: max(abs(c[name]-v) for c in mean_corners)
                                   +1024*np.finfo(float).eps*abs(v)
                                   for name, v in means[str(kappa)].items()}
        require(all(mean_errors[str(kappa)][name] <= 1e-10*abs(v)
                    for name, v in means[str(kappa)].items()), 'size-mean accuracy unresolved')
    return {'radial_recurrence': recurrence, 'quadrature': quads, 'accepted_radial_checks': accepted,
            'radial_absolute_error_estimates': errors, 'flexible': exact,
            'flexible_absolute_error_estimates': propagated, 'size_means': means,
            'size_mean_absolute_error_estimates': mean_errors,
            'error_qualification': 'analytic tail bounds; empirical refinement and estimated floating-point error, not certified interval arithmetic'}


def batch_summary(xy, cuts):
    require(xy.shape == (BATCH, 2) and np.isfinite(xy).all() and (xy >= 0).all(), 'invalid/incomplete batch')
    mean = xy.mean(axis=0)
    centered = xy-mean
    w = np.column_stack((xy, xy[:, 0]**2, xy[:, 1]**2, xy[:, 0]*xy[:, 1],
                         xy[:, 0, None] <= np.asarray(cuts[0]), xy[:, 1, None] <= np.asarray(cuts[1])))
    require(np.isfinite(w).all(), 'nonfinite fourth-length moments')
    # Retain first-five W covariance, and all W means/CDF counts. Batch-mean
    # covariance of ALL channels is reconstructed across independent batches.
    return {'count': BATCH, 'mean': mean.tolist(), 'M2': (centered.T @ centered).tolist(),
            'w_mean': w.mean(axis=0).tolist(), 'w_cov_first5': np.cov(w[:, :5], rowvar=False).tolist(),
            'cdf_counts': w[:, 5:].sum(axis=0).astype(int).tolist(),
            'X4_Y4_X2Y2': [float(np.mean(xy[:, 0]**4)), float(np.mean(xy[:, 1]**4)),
                           float(np.mean((xy[:, 0]*xy[:, 1])**2))],
            'min': xy.min(axis=0).tolist(), 'max': xy.max(axis=0).tolist()}


def merged(rows):
    count, mean, m2 = 0, np.zeros(2), np.zeros((2, 2))
    for row in rows:
        nb, mb = row['count'], np.asarray(row['mean'])
        delta = mb-mean
        m2 += np.asarray(row['M2'])+np.outer(delta, delta)*count*nb/(count+nb)
        mean += delta*nb/(count+nb)
        count += nb
    return count, mean, m2


def estimates(rows):
    count, mean, m2 = merged(rows)
    cov = m2/(count-1)
    raw = m2.diagonal()/count+mean**2
    cdf = np.sum([r['cdf_counts'] for r in rows], axis=0)/count
    return np.array([*mean, cov[0, 0], cov[1, 1], cov[0, 1], *raw, *cdf])


def inference(rows):
    require(len(rows) >= 2 and all(r['count'] == BATCH for r in rows), 'insufficient/equal batches required')
    count, mean, m2 = merged(rows)
    point = estimates(rows)
    transformed = []
    for row in rows:
        delta = np.asarray(row['mean'])-mean
        central = np.asarray(row['M2'])/BATCH+np.outer(delta, delta)
        w = row['w_mean']
        transformed.append([*row['mean'], central[0, 0]*count/(count-1),
                            central[1, 1]*count/(count-1), central[0, 1]*count/(count-1),
                            w[2], w[3], *w[5:]])
    covariance = np.cov(transformed, rowvar=False, ddof=1)/len(rows)
    delta_se = np.sqrt(np.maximum(0, covariance.diagonal()))
    leave_out = []
    for row in rows:
        nb, remain = row['count'], count-row['count']
        delta = np.asarray(row['mean'])-mean
        other_mean = mean-delta*nb/remain
        other_m2 = m2-np.asarray(row['M2'])-np.outer(delta, delta)*count*nb/remain
        require(np.all(other_m2.diagonal() > 0), 'degenerate/unstable leave-one-batch-out covariance')
        other_cov = other_m2/(remain-1)
        raw = other_m2.diagonal()/remain+other_mean**2
        cdf = (point[7:]*count-np.asarray(row['cdf_counts']))/remain
        leave_out.append([*other_mean, other_cov[0, 0], other_cov[1, 1], other_cov[0, 1], *raw, *cdf])
    jackknife_se = np.std(leave_out, axis=0, ddof=1)*(len(rows)-1)/math.sqrt(len(rows))
    require(np.isfinite(point).all() and np.isfinite(covariance).all() and np.isfinite(jackknife_se).all(),
            'nonfinite batch inference')
    require(point[2] > 0 and point[3] > 0 and point[4]**2 <= point[2]*point[3]*(1+1e-12),
            'non-positive-semidefinite conformational covariance')
    critical = float(t.ppf(1-ALPHA/(2*FAMILY), len(rows)-1))
    intervals = np.column_stack((point-critical*delta_se, point+critical*delta_se))
    for j, successes in enumerate(np.sum([r['cdf_counts'] for r in rows], axis=0).astype(int)):
        intervals[7+j] = binomial_interval(successes, count)
    half = np.maximum(point-intervals[:, 0], intervals[:, 1]-point)
    return {'names': list(NAMES), 'estimate': point.tolist(), 'delta_se': delta_se.tolist(),
            'jackknife_se': jackknife_se.tolist(), 'interval': intervals.tolist(),
            'half_width': half.tolist(), 'covariance_of_estimates_delta': covariance.tolist(),
            'covariance_of_mean_W': (np.cov([r['w_mean'] for r in rows], rowvar=False, ddof=1)/len(rows)).tolist(),
            'batches': len(rows), 'count': count, 'critical_t': critical,
            'interval_qualification': 'batch-t/delta nominal CLT; CDF exact binomial Bonferroni; jackknife diagnostic only'}


def binomial_interval(successes, count):
    require(0 <= successes <= count and count > 0, 'invalid binomial counts')
    tail = ALPHA/(2*FAMILY)
    return [0. if successes == 0 else float(beta.ppf(tail, successes, count-successes+1)),
            1. if successes == count else float(beta.ppf(1-tail, successes+1, count-successes))]


def limits(point):
    result = np.full(len(NAMES), np.inf)
    for index in (2, 3, 5, 6):
        result[index] = .05*point[index]
    result[4] = .05*math.sqrt(point[2]*point[3])
    result[7:] = .005
    return result


def select_size(pilot, primary=None):
    point, se = np.asarray(pilot['estimate']), np.asarray(pilot['delta_se'])
    require(np.isfinite(se).all() and (se[2:] > 0).all(), 'unresolved zero/nonfinite pilot uncertainty')
    critical = float(t.ppf(1-ALPHA/(2*FAMILY), GRID[0]//BATCH-1))
    scale = point.copy()
    if primary is not None:
        scale[:7] = [primary[name] for name in NAMES[:7]]
    thresholds = limits(scale)
    predictions = []
    chosen = None
    for count in GRID:
        half = critical*2*se*math.sqrt(PILOT/count)
        passed = bool(np.all(half[2:] <= thresholds[2:]))
        predictions.append({'count': count, 'half_width': half.tolist(), 'passes': passed})
        if passed and chosen is None:
            chosen = count
    return {'selected_count': chosen, 'predictions': predictions, 'critical_t_31': critical,
            'pilot_SE_multiplier': 2, 'precision_limits': thresholds[2:].tolist()}


def freeze_quantiles(calibration):
    require(calibration.shape == (CALIBRATION, 2) and np.isfinite(calibration).all(), 'incomplete calibration')
    sorted_xy = np.sort(calibration, axis=0)
    cuts, rank_intervals = [], []
    # Calibration uncertainty is diagnostic and separately Bonferroni-adjusted
    # over 18 cuts; it is NOT an additional final-reference acceptance family.
    for column in range(2):
        cuts.append([float(sorted_xy[math.ceil(CALIBRATION*p)-1, column]) for p in PROBABILITIES])
        entries = []
        for p in PROBABILITIES:
            lower = int(binom.ppf(.05/(2*18), CALIBRATION, p))
            upper = int(binom.ppf(1-.05/(2*18), CALIBRATION, p))+1
            entries.append({'population_p': p, 'order_statistic_ranks_1based': [lower, upper],
                            'interval': [float(sorted_xy[lower-1, column]) if lower >= 1 else None,
                                         float(sorted_xy[upper-1, column]) if upper <= CALIBRATION else None]})
        rank_intervals.append(entries)
    return sorted_xy, {'probabilities': list(PROBABILITIES), 'cuts': cuts,
                       'method': 'nearest rank ceil(S*p); <= for evaluation; binomial order-statistic calibration intervals',
                       'calibration_rank_intervals': rank_intervals}


def assess(final, numerical, kappa):
    point, half = np.asarray(final['estimate']), np.asarray(final['half_width'])
    scale = point.copy()
    if kappa == 0:
        scale[:7] = [numerical['flexible'][name] for name in NAMES[:7]]
    targets = limits(scale)
    quality = bool(np.all(half[2:] <= targets[2:]))
    analytic = numerical['size_means'][str(kappa)].copy()
    errors = numerical['size_mean_absolute_error_estimates'][str(kappa)].copy()
    if kappa == 0:
        analytic.update({name: numerical['flexible'][name] for name in NAMES[:7]})
        errors.update({name: numerical['flexible_absolute_error_estimates'][name] for name in NAMES[:7]})
    checks = {}
    for name, target in analytic.items():
        lo, hi = final['interval'][NAMES.index(name)]
        # Entire deterministic target error band must be inside the nominal interval.
        checks[name] = lo <= target-errors[name] and target+errors[name] <= hi
    return {'precision_pass': quality, 'analytic_consistency': checks,
            'precision_targets': targets[2:].tolist(),
            'status': 'PRECISION_RESOLVED_NOMINAL' if quality and all(checks.values()) else 'REFERENCE_PRECISION_OR_CONSISTENCY_UNRESOLVED',
            'qualification': 'nominal reference quality only; high-moment/CLT review still required; not dynamical preservation'}


def joint_variances(mean_x, var_x, chains=256, springs=2048):
    require(mean_x > 0 and var_x >= 0 and chains > 0 and springs > 0, 'invalid joint-law inputs')
    vf = var_x/mean_x**2
    return {'v_f': vf, 'var_A_joint': vf/chains, 'var_B_joint': 2*vf/(3*springs),
            'cov_A_B': 0., 'qualification': 'zero covariance is not independence; plug-in if Var(X) sampled'}
