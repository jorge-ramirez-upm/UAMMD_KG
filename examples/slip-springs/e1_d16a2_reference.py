"""D1.6A.2: independent moment/CDF gates. No calculation runs on import."""
import math
import numpy as np
from scipy.stats import beta, t

# Frozen routines are read-only dependencies; their interfaces/meaning stay intact.
from e1_d16a_reference import (BATCH, CALIBRATION, PILOT, GRID, PROBABILITIES,
    NAMES, SAMPLER_SHA, numerical_checks, batch_summary, merged,
    estimates, freeze_quantiles, joint_variances)

SCHEMA = 'e1-d16a2-reference-v1'
SEED_NAMESPACE = 721612000
ALPHA = .05
M_ALPHA, C_ALPHA = .025, .025
M_FAMILY, C_FAMILY = 14, 36  # Across BOTH stiffnesses: 7 moments/means and 18 CDFs.
M_INDICES = (2, 3, 4, 5, 6)


class NumericalConsistencyFailure(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise NumericalConsistencyFailure(message)


def seed_audit():
    """Audit maximum planned coverage, including all original D1.6A identities.

    No random draws: SeedSequence expansion and initial PCG64 states only.
    Distinct identities do not prove mathematical stream independence.
    """
    seen_entropy, seen_identity, seen_state = set(), set(), set()
    counts = {}
    for namespace in (721610000, SEED_NAMESPACE):
        count = 0
        for kappa in (0, 10):
            for phase, draws in ((1, CALIBRATION), (2, PILOT), (3, GRID[-1])):
                for index in range(draws//BATCH):
                    entropy = (namespace, kappa, phase, index)
                    seed = np.random.SeedSequence(entropy)
                    identity = tuple(map(int, seed.generate_state(4)))
                    state = np.random.PCG64(seed).state['state']
                    state = (state['state'], state['inc'])
                    require(entropy not in seen_entropy and identity not in seen_identity
                            and state not in seen_state, 'planned seed identity collision')
                    seen_entropy.add(entropy)
                    seen_identity.add(identity)
                    seen_state.add(state)
                    count += 1
        counts[str(namespace)] = count
    return {'schema': SCHEMA, 'status': 'NO_PLANNED_COLLISIONS',
            'namespaces': counts, 'total_identities': len(seen_identity),
            'scope': 'all maximum-grid batches, both kappas, all three phases; old namespace exclusion',
            'new_equilibrium_draws': 0}


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
    critical = float(t.ppf(1-M_ALPHA/(2*M_FAMILY), len(rows)-1))
    intervals = np.column_stack((point-critical*delta_se, point+critical*delta_se))
    for j, successes in enumerate(np.sum([r['cdf_counts'] for r in rows], axis=0).astype(int)):
        intervals[7+j] = binomial_interval(successes, count)
    half = np.maximum(point-intervals[:, 0], intervals[:, 1]-point)
    return {'schema': SCHEMA, 'names': list(NAMES), 'estimate': point.tolist(), 'delta_se': delta_se.tolist(),
            'jackknife_se': jackknife_se.tolist(), 'interval': intervals.tolist(),
            'half_width': half.tolist(), 'covariance_of_estimates_delta': covariance.tolist(),
            'covariance_of_mean_W': (np.cov([r['w_mean'] for r in rows], rowvar=False, ddof=1)/len(rows)).tolist(),
            'batches': len(rows), 'count': count, 'critical_t': critical,
            'confidence_allocation': confidence_allocation(),
            'interval_qualification': 'batch-t/delta nominal CLT; CDF exact binomial Bonferroni; jackknife diagnostic only'}


def binomial_interval(successes, count):
    require(0 <= successes <= count and count > 0, 'invalid binomial counts')
    tail = C_ALPHA/(2*C_FAMILY)
    return [0. if successes == 0 else float(beta.ppf(tail, successes, count-successes+1)),
            1. if successes == count else float(beta.ppf(1-tail, successes+1, count-successes))]


def limits(point):
    result = np.full(len(NAMES), np.inf)
    for index in (2, 3, 5, 6):
        result[index] = .05*point[index]
    result[4] = .05*math.sqrt(point[2]*point[3])
    result[7:] = .005
    return result


def confidence_allocation():
    return {'total_alpha': ALPHA, 'M': {'alpha': M_ALPHA, 'size_across_kappas': M_FAMILY},
            'C': {'alpha': C_ALPHA, 'size_across_kappas': C_FAMILY},
            'qualification': 'Bonferroni across two families and both kappas; M batch-t/delta nominal CLT; C exact conditional on frozen independent calibration cuts'}


def select_size(pilot, primary=None):
    point, se = np.asarray(pilot['estimate']), np.asarray(pilot['delta_se'])
    require(point.shape == (25,) and se.shape == (25,), 'invalid pilot dimensions')
    require(np.isfinite(point[:7]).all() and np.isfinite(se[:7]).all()
            and (se[list(M_INDICES)] > 0).all(), 'unresolved moment pilot uncertainty')
    critical = float(t.ppf(1-M_ALPHA/(2*M_FAMILY), GRID[0]//BATCH-1))
    scale = point.copy()
    if primary is not None:
        scale[:7] = [primary[name] for name in NAMES[:7]]
    require((scale[[2, 3, 5, 6]] > 0).all(), 'nonpositive moment pilot scale')
    thresholds = limits(scale)
    predictions, chosen = [], None
    for count in GRID:
        half = critical*2*se[:7]*math.sqrt(PILOT/count)
        passed = bool(np.all(half[list(M_INDICES)] <= thresholds[list(M_INDICES)]))
        predictions.append({'count': count, 'moment_half_width': half.tolist(), 'M_passes': passed})
        if passed and chosen is None:
            chosen = count
    return {'schema': SCHEMA, 'selected_count': chosen, 'predictions': predictions,
            'critical_t_31': critical, 'pilot_SE_multiplier': 2,
            'selection_family': 'M_ONLY', 'precision_limits': thresholds[2:7].tolist(),
            'final_draws_started': False}


def assess(final, numerical, kappa):
    point, half = np.asarray(final['estimate']), np.asarray(final['half_width'])
    require(point.shape == (25,) and half.shape == (25,) and np.isfinite(point).all()
            and np.isfinite(half).all() and (half >= 0).all(), 'invalid final inference')
    scale = point.copy()
    if kappa == 0:
        scale[:7] = [numerical['flexible'][name] for name in NAMES[:7]]
    targets = limits(scale)
    m_pass = bool(np.all(half[2:7] <= targets[2:7]))
    c_pass = bool(np.all(half[7:] <= targets[7:]))
    analytic = numerical['size_means'][str(kappa)].copy()
    errors = numerical['size_mean_absolute_error_estimates'][str(kappa)].copy()
    if kappa == 0:
        analytic.update({name: numerical['flexible'][name] for name in NAMES[:7]})
        errors.update({name: numerical['flexible_absolute_error_estimates'][name] for name in NAMES[:7]})
    checks = {}
    for name, target in analytic.items():
        lo, hi = final['interval'][NAMES.index(name)]
        checks[name] = lo <= target-errors[name] and target+errors[name] <= hi
    consistent = all(checks.values())
    m_status = 'MOMENTS_PRECISION_RESOLVED_NOMINAL' if m_pass else 'MOMENTS_PRECISION_UNRESOLVED'
    c_status = 'CDF_PRECISION_RESOLVED_NOMINAL' if c_pass else 'CDF_PRECISION_UNRESOLVED'
    observables = []
    for i, name in enumerate(NAMES):
        threshold = None if i < 2 else float(targets[i])
        observables.append({'name': name, 'family': 'M' if i < 7 else 'C',
            'estimate': float(point[i]), 'standard_error': final['delta_se'][i],
            'batch_jackknife_standard_error': final['jackknife_se'][i],
            'simultaneous_interval': final['interval'][i], 'half_width': float(half[i]),
            'required_precision_threshold': threshold,
            'precision_decision': 'ANALYTICAL_MEAN_DIAGNOSTIC' if i < 2 else
                ('PASS' if half[i] <= threshold else 'UNRESOLVED')})
    return {'schema': SCHEMA, 'final_assessment_performed': True, 'status': m_status if consistent else 'NUMERICAL_CONSISTENCY_FAILED',
            'moments_status': m_status, 'cdf_status': c_status,
            'moments_accepted': m_pass and consistent, 'cdf_precision_pass': c_pass,
            'consistency_status': 'CONSISTENT_NOMINAL' if consistent else 'NUMERICAL_CONSISTENCY_FAILED',
            'analytic_consistency': checks, 'observables': observables,
            'primary_moment_reference': 'ANALYTICAL_EXACT' if kappa == 0 else 'INDEPENDENT_FINAL_SAMPLE',
            'confidence_allocation': confidence_allocation(),
            'qualification': 'CI agreement is a consistency diagnostic, not proof of exact sampling correctness; nominal high-moment CLT review required; no dynamical preservation conclusion'}
