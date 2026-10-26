"""Read-only imports of reviewed reference/performance evidence; never samples."""
from pathlib import Path
import math
import numpy as np

import e1_d16b_spec as spec
from e1_d1_pilot import require, load, file_record, identity

MOMENT_NAMES = ('mean_X','mean_Y','var_X','var_Y','cov_XY','mean_X2','mean_Y2')
METRIC_NAMES = ('re2','rg2','spatial_var_re2','spatial_var_rg2','spatial_cov_re2_rg2','raw_re4','raw_rg4')


def verify_files(root, records):
    root = spec.durable(root)
    require(root.is_dir() and not root.is_symlink(), 'missing/symlink evidence root')
    for name, proof in records.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'unsafe evidence member')
        require((root/name).resolve().is_relative_to(root), 'evidence path escaped root')
        require(file_record(root/name) == proof, 'reviewed evidence changed: '+name)


def import_moments():
    """Hashes/authentication only; consume recorded intervals, never refit them."""
    import e1_d16a2_local as reference_auth
    lock = load(spec.CONFIG/'reference-lock.json')
    require(lock['schema'] == 'e1-d16b-reviewed-reference-lock-v1', 'reference lock schema')
    root = Path(lock['root'])
    verify_files(root, lock['files'])
    session, project = reference_auth.checked(root)
    require(session['commit'] == lock['source_commit'], 'archived reference source commit mismatch')
    numerical = load(root/'numerical.json')
    cases = {}
    for kappa in (0,10):
        result = reference_auth.authenticate_case(root,kappa)
        case = root/f'kappa-{kappa}'
        assessment = load(case/'assessment.json')
        inference = load(case/'final-inference.json')
        require(result['status'] == 'MOMENTS_PRECISION_RESOLVED_NOMINAL'
                and assessment['moments_accepted'] is True
                and assessment['consistency_status'] == 'CONSISTENT_NOMINAL', 'moment reference unaccepted')
        require(inference['names'][:7] == list(MOMENT_NAMES) and len(inference['names']) == 25,
                'reference observable identity mismatch')
        covariance = np.asarray(inference['covariance_of_estimates_delta'],dtype=float)
        require(covariance.shape == (25,25) and np.isfinite(covariance).all()
                and np.allclose(covariance,covariance.T,atol=1e-10,rtol=1e-12)
                and np.min(np.linalg.eigvalsh(covariance)) >= -1e-10*max(1.,np.max(np.diag(covariance))),
                'reference covariance missing/nonfinite/non-PSD')
        require(len(inference['interval']) == 25 and len(inference['delta_se']) == 25,
                'reference uncertainty incomplete')
        values = {}
        for index,(name,metric) in enumerate(zip(MOMENT_NAMES,METRIC_NAMES)):
            # Both size means stay analytical, including in the stiff chain.
            exact = kappa == 0 or index < 2
            if exact:
                source = numerical['flexible'] if kappa == 0 else numerical['size_means']['10']
                error_source = (numerical['flexible_absolute_error_estimates'] if kappa == 0
                                else numerical['size_mean_absolute_error_estimates']['10'])
                point, error = source[name], error_source[name]
                interval, se = [point-error,point+error], 0.
            else:
                point, interval, se = inference['estimate'][index], inference['interval'][index], inference['delta_se'][index]
                error = 0.
            require(math.isfinite(point) and math.isfinite(se) and se>=0
                    and len(interval)==2 and interval[0]<=point<=interval[1], 'invalid reference interval')
            values[metric] = {'estimate':point,'interval':interval,'standard_error':se,
                             'numerical_error':error,'source':'ANALYTICAL' if exact else 'INDEPENDENT_MONTE_CARLO'}
        for metric,source in (('reference_squared_re2','spatial_var_re2'),
                              ('reference_squared_rg2','spatial_var_rg2'),
                              ('reference_cross_re2_rg2','spatial_cov_re2_rg2')):
            values[metric] = dict(values[source])
        require(all(o['precision_decision']=='PASS' for o in assessment['observables'][2:7]),
                'missing moment precision gate')
        require(kappa!=10 or assessment['cdf_status']=='CDF_PRECISION_UNRESOLVED',
                'stiff CDF status differs from independently reviewed evidence; review new lock')
        cuts = load(case/'quantiles.json')['cuts']
        require(np.asarray(cuts).shape==(2,9), 'frozen CDF cut coverage')
        for i,name in enumerate(inference['names'][7:],7):
            values[name]={'estimate':inference['estimate'][i], 'interval':inference['interval'][i],
                         'standard_error':inference['delta_se'][i], 'numerical_error':0.,
                         'source':'INDEPENDENT_MONTE_CARLO_CDF', 'precision_status':assessment['cdf_status']}
        cases[str(kappa)]={'values':values,'cuts':cuts,'cdf_status':assessment['cdf_status'],
            'moments_status':assessment['moments_status'],'sampling_inference':inference,
            'assessment':assessment,'completion':file_record(case/'completion.json'),
            'joint_null_law':load(case/'joint-null-law.json'),
            'radial':{'moments':numerical['radial_recurrence'],'errors':numerical['radial_absolute_error_estimates']}}
    # Cross-file validation is read-only: no writes to reference roots.
    verify_files(root,lock['files'])
    return {'schema':'e1-d16b-imported-references-v1','lock':file_record(spec.CONFIG/'reference-lock.json'),
            'source_session':file_record(root/'session.json'),'archived_source':session,
            'cases':cases,'numerical_reference':numerical,'reference_family_alpha':.025,
            'qualification':'M nominal batch CLT; C precision independently reported; no dynamics proof'}


def import_performance():
    import e1_d15_auth as auth
    lock = load(spec.CONFIG/'performance-lock.json')
    reports=[]
    for record in lock['records']:
        root=Path(record['session_root'])
        verify_files(root,record['files'])
        manifest,items=auth.authenticate_campaign(record['campaign_root'],record['manifest'],
            record['manifest_sha256'],record['approval_sha256'],record['completion_sha256'])
        report=load(root/record['report'])
        require(report['kind']==record['kind'] and len(report['runs'])==4, 'M256 performance cohort incomplete')
        for observed,item in zip(report['runs'],items):
            require(observed['run']==item['run'] and observed['metadata']==item['data']['metadata']
                    and observed['child_wall_seconds']==item['receipt']['wall_seconds'], 'performance report binding mismatch')
            require(item['run']['M']==256, 'M64 proxy cannot replace M256 measurements')
        reports.append({'kind':record['kind'],'report':report,'trusted_identities':record})
        verify_files(root,record['files'])
    pilot=next(r['report'] for r in reports if r['kind']=='pilot')
    return {'schema':'e1-d16b-imported-performance-v1','cohorts':reports,
            'gross_production_T100_proxy_seconds':4*100*sum(r['metadata']['production_wall_seconds'] for r in pilot['runs']),
            'qualification':'authenticated M256 measurements; linear-in-time planning proxy, no runtime guarantee or new benchmark'}
