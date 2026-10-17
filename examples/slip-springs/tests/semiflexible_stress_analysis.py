"""Independent Stage 4A.3c gates. No simulator execution or altered criteria."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semiflexible_reference import Chain
from semiflexible_stress_reference import virials, components
from stream_analysis import geometric_mean

PROJECT = Path(__file__).resolve().parents[1]
PLAN_HASH = 'efd040ceba8cd903dee7a145296dce08435e3df3efa940c65170f4bcf98acb36'
ACCEPTED_SOURCE_HASHES = {'tests/semiflexible_stress_host.py': '0d343e9167bb9f21d147ce3fd437c30feb61af9bd851f952df3c4482d30befee', 'semiflexible_reference.py': 'a293806e16c4dcb58188ae680d852a487d5f3b95920222a2bb72b4aee8c17967', 'semiflexible_stress_reference.py': 'cc1ae1df5cf3cfb642b9576bfa41cffc76b31c3f60ecdb652f76a55dea50f84b', 'semiflexible.cu': 'cf20a1d68b17a72b06988c3278ab3062a44ccc5bf1216654e833bd860f8651b3', 'semiflexible.cuh': 'e9bf6917fa02f7eaf24efc002bc54eb62e4b1c9397f711ace473ef09240f6fd3', 'semiflexible_stress.cuh': '1aa17d9836ade9fa9c4f9d02c16ba8a4569e195151aa78a81093ea19ec029232', 'semiflexible_stress_stream.h': '2ef368cccb70c58fb2a414ae29e4061e2a431da217cc9ddd019b7872d8c041f2', 'stream_correlator.h': '3be57db604dc0b23a96fbe103b328baa3634815eb785c4a1eb050c2d29be0a68', 'cpu_workers.h': '8bf5e78123f84e1e37ff1b6d169abac0491f0ec6271d33e9bd5e56ed6df0c290'}
COLS = ('Cxy', 'Cxz', 'Cyz', 'Cxx_yy', 'Cxx_zz', 'Cyy_zz')
CHANNELS = ('xy', 'xz', 'yz', 'xx_yy', 'xx_zz', 'yy_zz')
WEIGHTS = np.array([1/5]*3+[1/30]*3)


class Invalid(ValueError):
    pass


def require(condition, explanation):
    if not condition:
        raise Invalid(explanation)


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def identity(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def load(path):
    def duplicate(pairs):
        d = {}
        for k, v in pairs:
            require(k not in d, 'duplicate JSON key: '+k)
            d[k] = v
        return d
    return json.loads(Path(path).read_text(), object_pairs_hook=duplicate,
                      parse_constant=lambda x: (_ for _ in ()).throw(Invalid('nonfinite JSON: '+x)))


def rows(path, columns=None):
    """One row at a time, including huge scalar observations; never infer IDs."""
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        require(reader.fieldnames and len(set(reader.fieldnames)) == len(reader.fieldnames), 'invalid CSV header: '+str(path))
        if columns is not None:
            require(reader.fieldnames == list(columns), 'wrong CSV columns: '+str(path))
        for line, row in enumerate(reader, 2):
            require(None not in row and None not in row.values() and '' not in row.values(), f'malformed CSV {path}:{line}')
            yield row


def number(row, key, integer=False):
    try:
        x = float(row[key])
        require(math.isfinite(x), 'nonfinite '+key)
        if integer:
            require(x == int(x), 'nonintegral '+key)
            return int(x)
        return x
    except (KeyError, ValueError, OverflowError) as e:
        raise Invalid('malformed numeric '+key) from e


def close(a, b, atol=0, rtol=0, why='numeric mismatch'):
    a, b = np.asarray(a), np.asarray(b)
    require(a.shape == b.shape and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
            and np.all(np.abs(a-b) <= atol+rtol*np.abs(b)), why)


def options(run):
    cmd = run['command']
    require(len(cmd) % 2 == 1 and all(cmd[i].startswith('--') for i in range(1, len(cmd), 2)), 'malformed command')
    d = dict(zip(cmd[1::2], cmd[2::2]))
    require(len(d)*2+1 == len(cmd), 'duplicate command option')
    defaults = dict(springs='8', chains='64', steps='1000', sample='100', seed='42001', dt='.0001',
                    kbt='1', zeta='1', **{'stress-mode':'off', 'stress-batch':'32', 'cpu-workers':'1',
                    'corr-levels':'16', 'corr-slots':'16', 'corr-m':'2', 'scalar-output':'full'})
    defaults.update({k[2:]: v for k, v in d.items()})
    return defaults


def model_file(path):
    v = Path(path).read_text().split()
    try:
        n = int(v[0]); require(len(v) == 3*n+2, 'wrong parameter count')
        bonds = np.array(v[1:1+2*n], float).reshape(n, 2)
        return Chain(bonds[:, 0], bonds[:, 1], np.array(v[1+2*n:], float))
    except (ValueError, IndexError) as e:
        raise Invalid('invalid model parameters: '+str(path)) from e


def model_key(model, temperature):
    return identity(dict(b0=model.b0.tolist(), kb=model.kb.tolist(), kappa=model.kappa.tolist(), kbt=temperature))


def authenticate(root):
    """Reconstruct unchanged generator output; paths vary, scientific commands cannot."""
    import contextlib
    import io
    from semiflexible_stress_host import generate
    root = Path(root).resolve()
    from semiflexible_scalar_schema import current_sources
    approved=current_sources(ACCEPTED_SOURCE_HASHES)
    for name,expected_hash in approved.items():
        allowed={expected_hash}
        if name=='semiflexible.cu':allowed.add(ACCEPTED_SOURCE_HASHES[name])
        require(digest(PROJECT/name) in allowed,'accepted source identity changed: '+name)
    if (root/'execution-profile.json').exists():
        from semiflexible_stress_profile import authenticate_profile
        return authenticate_profile(root)
    require(digest(PROJECT/'STAGE4A3C_VALIDATION_PLAN.md') == PLAN_HASH, 'local frozen plan hash changed')
    require(digest(root/'validation-plan.md') == PLAN_HASH, 'campaign frozen plan hash mismatch')
    require((root/'PLAN_SHA256').read_text() == PLAN_HASH+'  validation-plan.md\n', 'corrupted PLAN_SHA256')
    manifest = load(root/'manifest.json')
    require(isinstance(manifest, list) and len(manifest) == 282, 'manifest must contain exactly 282 runs')
    build = Path(manifest[0]['command'][0]).parents[1]
    with tempfile.TemporaryDirectory(prefix='stress-auth-') as temp, contextlib.redirect_stdout(io.StringIO()):
        expected_root = Path(temp)/'expected'
        expected = generate(expected_root, build)
        def relocate(obj):
            return json.loads(json.dumps(obj).replace(str(expected_root), str(root)))
        require(manifest == relocate(expected), 'manifest scientific identity/order/commands mismatch')
        for p in expected_root.iterdir():
            if p.name in ('manifest.json', 'validation-plan.md', 'PLAN_SHA256'):
                continue
            require((root/p.name).read_text() == p.read_text().replace(str(expected_root), str(root)), 'campaign input/command changed: '+p.name)
    ids = [identity(dict(phase=r['phase'], label=r['label'], precision=r['precision'],
                         command=[x.replace(str(root), '$CAMPAIGN').replace(str(build), '$BUILD') for x in r['command']])) for r in manifest]
    require(len(set(ids)) == 282, 'duplicate run identities')
    return manifest, ids, identity(manifest)


def source_provenance():
    from semiflexible_scalar_schema import current_sources
    if digest(PROJECT/'semiflexible.cu')==ACCEPTED_SOURCE_HASHES['semiflexible.cu']:return ACCEPTED_SOURCE_HASHES
    return current_sources(ACCEPTED_SOURCE_HASHES)


def approved_source_provenance(proof):
    from semiflexible_scalar_schema import current_sources
    return proof in (ACCEPTED_SOURCE_HASHES,current_sources(ACCEPTED_SOURCE_HASHES))


def summary(x):
    x = np.asarray(x, float)
    require(x.ndim >= 2 and len(x) >= 2 and np.all(np.isfinite(x)), 'need finite independent-chain clusters')
    return dict(count=len(x), mean=x.mean(axis=0).tolist(), se=(x.std(axis=0, ddof=1)/math.sqrt(len(x))).tolist())


def channel_statistics(x):
    x = np.asarray(x, float)
    raw = x[:, :, None]*x[:, None, :]
    centered = x-x.mean(axis=0)
    require(len(x)>2,'covariance jackknife requires at least three chains')
    centered_products=centered[:, :, None]*centered[:, None, :]
    # Exact leave-one-chain-out covariance jackknife, without retaining replicas.
    covariance=dict(count=len(x),mean=(centered_products.sum(0)/(len(x)-1)).tolist(),
                    se=(math.sqrt(len(x))/(len(x)-2)*centered_products.std(0,ddof=1)).tolist(),
                    estimator='unbiased sample covariance; leave-one-chain-out jackknife SE')
    return dict(mean=summary(x), products=summary(raw), covariance=covariance)


def gate(name, observed, target, se, target_se=0, floor=0, fraction=0, scale=None):
    o, t, s, ts = map(np.asarray, (observed, target, se, target_se))
    require(np.all(np.isfinite([o, t])) if o.shape == t.shape else False, 'nonfinite gate inputs: '+name)
    require(np.all(np.isfinite(s)) and np.all(s >= 0) and np.all(np.isfinite(ts)) and np.all(ts >= 0), 'invalid uncertainty: '+name)
    bound = 6*np.hypot(s, ts)+np.maximum(floor, fraction*np.abs(t if scale is None else np.asarray(scale)))
    excess = np.abs(o-t)-bound
    return dict(name=name, status='passed' if np.all(excess <= 0) else 'failed', max_excess=float(np.max(excess)),
                observed=o.tolist(),expected=t.tolist(),standard_error=s.tolist(),reference_standard_error=ts.tolist(),allowed_difference=bound.tolist())


def compare_statistics(name, actual, expected, scale):
    return gate(name, actual['mean'], expected['mean'], actual['se'], expected['se'], floor=1e-6, fraction=.01, scale=scale)


def lag_grid(frames, levels, slots, m):
    highest, width = 0, 1
    while highest+1 < levels and width*m <= frames:
        highest += 1; width *= m
    result = [(j, 1, frames-j) for j in range(min(slots, frames))]
    for level in range(1, highest):
        b = m**level
        result += [(j*b, b, frames//b-j) for j in range(slots//m, min(slots, frames//b))]
    return result


def gaussian_reference(meta, lag, block, frames):
    """Finite acquisition/origin and block average of squared two-time covariance.

    Geometric sums use the validated stable helper, not a continuous-time curve.
    v(n)=v_star+delta*a**(2n), with actual rounded drift AND noise.
    """
    n, stride = meta['springs'], meta['sample']
    lam = 12*np.sin(np.arange(1, n+1)*np.pi/(2*(n+1)))**2
    a = 1-meta['effective_mobility_step']*lam
    require(np.all((a > 0) & (a < 1)), 'unsupported/unstable Gaussian discrete multiplier')
    require(block >= 1 and lag % block == 0, 'invalid Gaussian bin')
    origins = frames//block-lag//block
    require(origins > 0 and (block == 1 or lag >= block), 'no Gaussian origins')
    star = meta['effective_noise']**2/(1-a*a)
    delta = meta['kbt']/lam-star
    logq = 2*stride*np.log(a)
    gm = geometric_mean
    ar, ar2 = gm(logq*block, origins), gm(logq*2*block, origins)
    if block == 1:
        terms = np.exp(logq*lag)*(star*star+2*star*delta*ar+delta*delta*ar2)
    else:
        ab = gm(logq, block); j = lag//block
        terms = (star*star*np.exp(logq*((j-1)*block+1))*ab*ab
                 + 2*star*delta*np.exp(logq*j*block)*ab*ar
                 + delta*delta*np.exp(logq*j*block)*ab*ab*ar2)
    value = float(np.sum(lam*lam*terms))
    require(math.isfinite(value) and value >= 0, 'invalid Gaussian prediction')
    return value


def terminal(rows_, spacing):
    """First downward crossing; pointwise bands and origin/block support only."""
    t = np.array([r['lag_time'] for r in rows_]); h = np.array([r['H'] for r in rows_]); se = np.array([r['H_se'] for r in rows_])
    result = dict(name='terminal_support', status='insufficient_support')
    if len(t) < 3 or h[0] <= 6*se[0]:
        return dict(result, reason='zero-lag amplitude unresolved')
    def crossing(y, target):
        for i in range(1, len(y)):
            if y[i] <= target < y[i-1]:
                return float(t[i-1]+(t[i]-t[i-1])*(y[i-1]-target)/(y[i-1]-y[i]))
        return None
    tau = crossing(h, h[0]/math.e)
    lo = crossing(h-6*se, (h[0]+6*se[0])/math.e)
    hi = crossing(h+6*se, (h[0]-6*se[0])/math.e)
    result.update(tau_e=tau, tau_bounds=[lo, hi])
    if tau is None or lo is None or hi is None or lo <= 0 or hi < lo:
        return dict(result, reason='first-crossing uncertainty not resolved within acquisition')
    supported = [i for i, r in enumerate(rows_) if r['pairs_per_chain'] >= 16 and r['block_samples']*spacing <= tau/4]
    # "near" is the nearest supported exported bin, bracketed by the acquisition.
    if not supported or 2*tau > max(t[supported]):
        return dict(result, reason='no supported bin near twice tau_e')
    i = min(supported, key=lambda i: abs(t[i]-2*tau))
    late = [j for j in supported if t[j] > 4*tau]
    result.update(positive_lag=float(t[i]), positive_offset=float(t[i]-2*tau), positive_signal=float(h[i]), positive_se=float(se[i]),positive_origins=rows_[i]['pairs_per_chain'],positive_block_time=rows_[i]['block_samples']*spacing)
    if not late:
        return dict(result, reason='no supported bin beyond four tau_e')
    j = next((j for j in late if abs(h[j])/h[0] <= .1+6*se[j]/h[0]), None)
    if h[i] <= 3*se[i]:
        return dict(result, reason='positive signal near twice tau_e unresolved')
    if j is None:
        return dict(result, status='failed', reason='supported late bins do not satisfy terminal threshold')
    return dict(result, status='passed', late_lag=float(t[j]), late_ratio=float(abs(h[j])/h[0]),late_origins=rows_[j]['pairs_per_chain'],late_block_time=rows_[j]['block_samples']*spacing)


def refinement(name, coarse, middle, fine, scale, reference=None):
    checks = [gate(name+': finest-middle', fine['mean'], middle['mean'], fine['se'], middle['se'], fraction=.01, scale=scale)]
    if reference is not None:
        target = np.asarray(reference['mean']); refse = np.asarray(reference['se'])
        ec, ef = abs(np.asarray(coarse['mean'])-target), abs(np.asarray(fine['mean'])-target)
        sc, sf = np.asarray(coarse['se']), np.asarray(fine['se'])
        resolved = ec > 6*np.hypot(sc, refse)
        ok = ef <= .75*ec+6*np.sqrt(sf*sf+.75**2*sc*sc+1.75**2*refse*refse)
        checks.append(dict(name=name+': coarse bias', status=('failed' if np.any(resolved & ~ok) else 'passed') if np.any(resolved) else 'statistically_unresolved_bias', resolved_components=int(np.sum(resolved)),max_coarse_error=float(np.max(ec)),max_fine_error=float(np.max(ef))))
    return checks


def positions(path, chains, n):
    result = np.empty((chains, n+1, 3)); count = 0
    for count, row in enumerate(rows(path, ('chain','bead','x','y','z')), 1):
        index = count-1
        require(index < chains*(n+1) and number(row,'chain',True) == index//(n+1)
                and number(row,'bead',True) == index%(n+1), 'missing/duplicated/out-of-order position IDs')
        result[index//(n+1), index%(n+1)] = [number(row,k) for k in ('x','y','z')]
    require(count == chains*(n+1), 'incomplete position snapshot')
    return result


def correlation_rows(path, raw_path, frames, chains, opts):
    grid = lag_grid(frames, int(opts['corr-levels']), int(opts['corr-slots']), int(opts['corr-m']))
    raw_columns=('lag_samples','lag_time','block_samples','g','g_se')+COLS+('pairs_per_chain','pairs_total')+tuple(k+'_se' for k in COLS)
    columns=raw_columns[:3]+('H','H_se')+raw_columns[5:]+('g','g_se')+(('G','G_se') if 'chain-density' in opts else ())
    actual, raw = list(rows(path,columns)), list(rows(raw_path,raw_columns))
    require(len(actual) == len(raw) == len(grid), 'missing/duplicate correlation bins or incomplete terminal levels')
    result = []
    for row, original, (lag, block, pairs) in zip(actual, raw, grid):
        for key, value in dict(lag_samples=lag, block_samples=block, pairs_per_chain=pairs, pairs_total=pairs*chains).items():
            require(number(row,key,True) == number(original,key,True) == value, 'incorrect correlation '+key)
        time = lag*float(opts['sample'])*float(opts['dt'])
        close(number(row,'lag_time'), time, atol=1e-12*max(1,time), why='wrong lag time')
        clean = {k: number(row,k) for k in row}
        require(all(clean[k] >= 0 for k in ('H_se','g_se')+tuple(k+'_se' for k in COLS)), 'negative correlation uncertainty')
        close(clean['H'], np.dot([clean[k] for k in COLS], WEIGHTS), atol=3e-11, rtol=3e-11, why='wrong isotropic weights or normal factor')
        for k in original:
            counterpart = {'g':'H','g_se':'H_se'}.get(k,k)
            close(number(original,k), clean[counterpart], atol=0, rtol=0, why='raw/normalized correlation disagreement: '+k)
        temperature = float(opts['kbt'])
        for suffix in ('','_se'):
            close(clean['g'+suffix], clean['H'+suffix]/temperature**2, rtol=2e-14, why='incorrect temperature normalization')
            if 'chain-density' in opts:
                close(clean['G'+suffix], float(opts['chain-density'])*clean['H'+suffix]/temperature, rtol=2e-14, why='incorrect density normalization')
            else:
                require('G'+suffix not in clean, 'physical density silently assigned')
        result.append(clean)
    return result


def performance(meta, stress, opts):
    main_keys = ('initialization_seconds','integration_seconds','production_wall_seconds','observation_seconds',
                 'recurrent_output_seconds','final_output_seconds','force_and_diagnostic_wall_seconds')
    stress_keys = ('gpu_stress_seconds','stress_transfer_seconds','stress_diagnostic_wait_seconds',
                   'cpu_correlation_seconds','cpu_barrier_seconds','cpu_worker_execution_sum_seconds',
                   'stress_output_and_moments_seconds','diagnostic_output_seconds','buffer_wait_seconds','finalization_output_seconds')
    for source, keys in ((meta,main_keys),(stress,stress_keys)):
        for k in keys:
            require(isinstance(source.get(k), (float,int)) and math.isfinite(source[k]) and source[k] >= 0, 'invalid performance metadata: '+k)
    require(stress['cpu_barrier_seconds'] <= stress['cpu_correlation_seconds']+1e-6, 'barrier is not a subset of CPU wall')
    denominator = meta['total_beads']*meta['steps']
    for key, timer in (('integration_ns_per_bead_step','integration_seconds'),('overall_ns_per_bead_step','production_wall_seconds')):
        if denominator:
            close(meta[key], meta[timer]*1e9/denominator, atol=5.1e-7, rtol=1e-12, why='inconsistent performance rate: '+key)
        else:
            require(meta[key] is None, 'non-null zero-step performance rate')
    require(meta['integration_seconds'] <= meta['production_wall_seconds']+1e-3, 'integration exceeds production wall')
    return {**{k:meta[k] for k in main_keys}, **{k:stress[k] for k in stress_keys},
            **{k:meta[k] for k in ('integration_ns_per_bead_step','overall_ns_per_bead_step','device_bytes')},
            **{k:stress[k] for k in ('gpu_stress_bytes','host_stress_batch_bytes','estimated_bytes')},
            'timer_note':'GPU/wait scopes overlap; barrier is a CPU wall subset; worker sums are not wall time'}


def validate_run(run):
    """Structural/numerical completion. CSV storage bounded independently of duration."""
    opts = options(run); out = Path(run['output'])
    require(not list(out.glob('*failure*')), 'numerical failure record present')
    m, sm = load(out/'metadata.json'), load(out/'stress_metadata.json')
    n, c, steps, stride = [int(opts[k]) for k in ('springs','chains','steps','sample')]
    frames, selected = steps//stride+1, (steps//stride+1)-(steps//2+stride-1)//stride
    diagnostic = opts['stress-mode'] == 'diagnostic'
    require(c >= 2 and n <= 32, 'unsupported frozen dimensions')
    for key, expected in dict(springs=n,chains=c,steps=steps,sample=stride,seed=int(opts['seed']),kbt=float(opts['kbt']),
                              zeta=float(opts['zeta']),dt=float(opts['dt']),precision_bits=32 if run['precision']=='single' else 64,
                              beads_per_chain=n+1,total_beads=c*(n+1),rng_domain=3,timer_version=2,
                              model='finite-rest-length-Kratky-Porod',initialization_method='CPU-direct-equilibrium').items():
        require(m.get(key) == expected, 'metadata inconsistent: '+key)
    close(m['production_time'], steps*m['dt'], why='wrong physical duration')
    cast = np.float32 if m['precision_bits']==32 else np.float64
    for key, expected in dict(effective_mobility_step=float(cast(m['dt']/m['zeta'])),
                              effective_noise=float(cast(math.sqrt(2*m['kbt']*m['dt']/m['zeta'])))).items():
        close(m[key], expected, rtol=1e-15, why='wrong precision-rounded update coefficient: '+key)
    model = model_file(out/'parameters.txt'); requested = model_file(opts['parameters'])
    for key in ('b0','kb','kappa'):
        close(getattr(model,key), getattr(requested,key).astype(cast).astype(float), why='wrong parameter/indexing: '+key)
    active = int(np.count_nonzero(model.kappa)); real_bytes = m['precision_bits']//8
    expected_bend = (n+1)*real_bytes if active else 0
    for key, expected in dict(active_angles=active,bending_device_bytes=expected_bend,update_launches=steps,
                              stretch_launches=steps+2,bending_launches=(steps+2 if active else 0)).items():
        require(m.get(key) == expected, 'force fast-path/count mismatch: '+key)
    require(m['device_bytes'] == 3*c*(n+1)*4*real_bytes+n*2*real_bytes+expected_bend+4, 'inconsistent force device capacity')
    for key, expected in dict(mode=opts['stress-mode'],frames=frames,spacing=stride*m['dt'],kbt=m['kbt'],
                              chain_density=float(opts['chain-density']) if 'chain-density' in opts else None,
                              moment_start_step=steps//2,moment_frames=0 if diagnostic else selected,
                              batch=int(opts['stress-batch']),cpu_workers=0 if diagnostic else int(opts['cpu-workers']),
                              levels=int(opts['corr-levels']),slots=int(opts['corr-slots']),coarsening=int(opts['corr-m']),
                              active_bending=bool(active),empirical_mean_subtraction=False,raw_connected=False,
                              stretch_stress_launches=frames,bending_stress_launches=frames if active else 0,
                              bending_stress_device_bytes=c*80 if diagnostic and active else 0,
                              host_stress_batch_bytes=0 if diagnostic else int(opts['stress-batch'])*c*48,
                              gpu_stress_bytes=c*128+8+(c*80 if diagnostic and active else 0)).items():
        require(sm.get(key) == expected, 'stress metadata inconsistent: '+key)
    # Frozen Linux 64-bit ABI: sizeof(OwnedCorrelator6)=296, ulong/pointers=8.
    bank_bytes=296+int(opts['corr-levels'])*(int(opts['corr-slots'])*(21*8+2*8)+13*8+6*8+2*4)
    expected_estimate=sm['gpu_stress_bytes']+sm['host_stress_batch_bytes']+(0 if diagnostic else c*(bank_bytes+8+42*8))
    require(sm['estimated_bytes']==expected_estimate,'stress bank/buffer memory estimate inconsistent with settings')
    require(m['cpu_workspace_budget_estimate_bytes']==c*(n+1)*(4*real_bytes*8+1024),'CPU workspace estimate inconsistent')
    initial = positions(out/'initial.csv',c,n); final = positions(out/'final.csv',c,n)
    if steps == 0:
        close(final,initial,why='zero-step positions changed')
    require(opts['scalar-output'] in ('full','compact'),'unknown scalar profile')
    require(run.get('scalar_profile',opts['scalar-output'])==opts['scalar-output'],'run scalar profile mismatch')
    scalar_result=None
    if opts['scalar-output']=='compact':
        from semiflexible_scalar_schema import validate as validate_scalar
        scalar_result=validate_scalar(out,opts,m)
    else:
        require(not any(out.glob('scalar_*.json')) and not any(out.glob('scalar_*.csv')),'full profile contains compact scalar files')
        # Validate large conformation CSV with constant memory and exact frame/chain order.
        count = 0;minimum_sampled=float('inf')
        for count, row in enumerate(rows(out/'samples.csv',('step','time','chain','mean_r','mean_r2','re2','rg2','cm_msd','monomer_msd','min_length')+tuple('tangent'+str(s) for s in range(1,min(4,n-1)+1))),1):
            frame, chain = divmod(count-1,c)
            require(frame < frames and number(row,'step',True)==frame*stride and number(row,'chain',True)==chain, 'missing frame or incorrect scalar chain ID')
            close(number(row,'time'),frame*stride*m['dt'],rtol=1e-14,why='incorrect sample time')
            for key in row:
                number(row,key)
            minimum_sampled=min(minimum_sampled,number(row,'min_length'))
            require(number(row,'min_length')>0,'collapsed observed bond in frozen campaign')
        close(m['minimum_sampled_bond'],minimum_sampled,rtol=1e-14,why='minimum observed bond metadata inconsistent')
        require(count == frames*c,'incomplete scalar observation frames')
    count = 0
    for count,row in enumerate(rows(out/'initial_bonds.csv',('chain','bond','length')),1):
        index=count-1
        require(index<c*n and number(row,'chain',True)==index//n and number(row,'bond',True)==index%n,'incorrect initial bond IDs')
        close(number(row,'length'),np.linalg.norm(initial[index//n,index%n+1]-initial[index//n,index%n]),rtol=1e-13,why='incorrect initial bond length')
    require(count==c*n,'missing initial bond records')
    count=0
    for count,row in enumerate(rows(out/'bond_statistics.csv',('chain','bond','frames','mean_r','mean_r2')+tuple('bin'+str(i) for i in range(33))),1):
        index=count-1
        require(index<c*n and number(row,'chain',True)==index//n and number(row,'bond',True)==index%n,'incorrect bond moment IDs')
        require(number(row,'frames',True)==selected,'incorrect final-half bond frames')
        require(all(number(row,'bin'+str(i),True)>=0 for i in range(33)),'negative histogram bin')
        require(sum(number(row,'bin'+str(i),True) for i in range(33))==selected,'incorrect bond histogram count')
        for key in row:
            number(row,key)
    require(count==c*n,'incomplete bond statistics')
    result=dict(metadata=m,stress_metadata=sm,performance=performance(m,sm,opts),checks=[])
    if scalar_result is not None:result['scalar_statistics']=scalar_result
    if diagnostic:
        result.update(validate_tensors(out,model,initial,run['precision'],m['kbt']))
    else:
        result['correlations']=correlation_rows(out/'stress_correlations.csv',out/'stress_correlations_raw.csv',frames,c,opts)
        means=np.empty((c,6)); products=np.empty((c,6,6)); count=0
        for count,row in enumerate(rows(out/'stress_moments.csv',('chain','frames')+tuple('mean'+str(i) for i in range(6))+tuple(f'raw{i}{j}' for i in range(6) for j in range(6))),1):
            require(count<=c and number(row,'chain',True)==count-1,'incorrect/duplicated stress moment chain ID')
            require(number(row,'frames',True)==selected and selected>=2,'missing final-half stress support')
            means[count-1]=[number(row,'mean'+str(i)) for i in range(6)]
            products[count-1]=[[number(row,f'raw{i}{j}') for j in range(6)] for i in range(6)]
        require(count==c,'incomplete final-half chain moments')
        close(products,products.transpose(0,2,1),rtol=1e-13,atol=1e-13,why='asymmetric raw stress products')
        require(np.all(np.diagonal(products,axis1=1,axis2=2) >= means*means-1e-10*np.maximum(1,means*means)),'invalid raw moment variance')
        result['time_statistics']=dict(mean=summary(means),products=summary(products))
        result['checks'].append(gate('final-half deviatoric mean',means.mean(0),np.zeros(6),means.std(0,ddof=1)/math.sqrt(c),floor=1e-6*max(1,n*m['kbt'])))
        if run['phase']=='reference':
            direct, initial_channels = direct_reference(out,opts,result['correlations'],frames,c)
            result['checks']+=direct
            result['initial_channels']=channel_statistics(initial_channels)
            expected_channels=np.array([np.r_[virials(model,r)['shears'],virials(model,r)['normal_differences']] for r in initial])
            close(initial_channels,expected_channels,atol=(2e-7 if run['precision']=='single' else 5e-13)*max(1,model.kb.max(),model.kappa.max()),rtol=3e-6 if run['precision']=='single' else 3e-12,why='initial raw channel convention disagrees with CPU virial')
        if run['label']=='gaussian-control':
            checks=[]
            for row in result['correlations']:
                prediction=gaussian_reference(m,int(row['lag_samples']),int(row['block_samples']),frames)
                for name in COLS+('H','g'):
                    factor=4 if name in COLS[3:] else (1/m['kbt']**2 if name=='g' else 1)
                    expected=prediction*factor
                    checks.append(gate(f'Gaussian {name} lag{row["lag_samples"]}',np.array(row[name]),np.array(expected),row[name+'_se'],floor=.002*n*m['kbt']**2*factor,fraction=.01))
            result['checks']+=checks
        elif run['phase']=='stream':
            result['checks'].append(terminal(result['correlations'],sm['spacing']))
    result['disk_bytes']=sum(p.stat().st_size for p in out.iterdir() if p.is_file())
    return result


def validate_tensors(out,model,initial,precision,temperature):
    c=len(initial); observed={k:np.empty((c,3,3)) for k in ('stretch','bend','total')}; count=0
    scale=max(1,float(model.kb.max()),float(model.kappa.max()))
    names=('stretch','bend','total')
    for count,row in enumerate(rows(out/'stress_tensors.csv',('step','chain','term')+tuple(f'w{i}{j}' for i in range(3) for j in range(3))),1):
        chain,term=divmod(count-1,3)
        require(chain<c and number(row,'step',True)==0 and number(row,'chain',True)==chain and row['term']==names[term], 'missing/duplicated tensor or incorrect term indexing')
        tensor=np.array([[number(row,f'w{i}{j}') for j in range(3)] for i in range(3)])
        close(tensor,tensor.T,atol=1e-11*scale,why='raw virial symmetry failure')
        if term==1:
            close(np.trace(tensor),0.,atol=3e-11*scale,why='incorrect bending trace')
        observed[names[term]][chain]=tensor
    require(count==c*3,'incomplete independent virial records')
    single=precision=='single'
    for chain in range(c):
        expected=virials(model,initial[chain])
        for term in names:
            close(observed[term][chain],expected[term],atol=(2e-7 if single else 5e-13)*scale,rtol=3e-6 if single else 3e-12,why='GPU/CPU '+term+' virial mismatch')
    close(observed['total'],observed['stretch']+observed['bend'],atol=3e-12*scale,rtol=3e-14,why='total virial missing contributions')
    checks=[]
    stats={name:summary(value) for name,value in observed.items()}
    for name,target in (('stretch',model.n*temperature*np.eye(3)),('bend',np.zeros((3,3)))):
        checks.append(gate('initial mean '+name,np.array(stats[name]['mean']),target,np.array(stats[name]['se']),floor=1e-6*max(1,model.n*temperature)))
    channels=np.array([np.r_[components(w)['shears'],components(w)['normal_differences']] for w in observed['total']])
    stat=channel_statistics(channels)
    checks.append(gate('initial deviatoric mean',np.array(stat['mean']['mean']),np.zeros(6),np.array(stat['mean']['se']),floor=1e-6*max(1,model.n*temperature)))
    return dict(virial_statistics=stats,initial_channels=stat,checks=checks)


def direct_reference(out,opts,correlations,frames,chains):
    require(frames*chains*6*8<=32*1024*1024,'direct fixture exceeds bounded 32MiB sample workspace')
    series=np.empty((frames,chains,6));count=0;stride=int(opts['sample'])
    for count,row in enumerate(rows(out/'stress_samples.csv',('step','chain')+CHANNELS),1):
        f,c=divmod(count-1,chains)
        require(f<frames and number(row,'step',True)==f*stride and number(row,'chain',True)==c,'missing stress frames or incorrect stress chain ID')
        series[f,c]=[number(row,k) for k in CHANNELS]
    require(count==frames*chains,'truncated direct stress sequence')
    checks=[]
    for row in correlations:
        block=int(row['block_samples']);lag=int(row['lag_samples'])//block;complete=frames//block
        blocks=series[:complete*block].reshape(complete,block,chains,6).mean(axis=1)
        products=(blocks[lag:]*blocks[:complete-lag]).mean(axis=0)
        expected=summary(products);paired=summary((products@WEIGHTS)[:,None])
        close(np.array([row[k] for k in COLS]),expected['mean'],atol=3e-11,rtol=3e-11,why='direct six-channel products / normal factors mismatch')
        close(np.array([row[k+'_se'] for k in COLS]),expected['se'],atol=3e-11,rtol=3e-11,why='incorrect direct chain-cluster channel SE')
        close(np.array([row['H'],row['H_se']]),np.array([paired['mean'][0],paired['se'][0]]),atol=3e-11,rtol=3e-11,why='incorrect direct H/paired uncertainty')
    checks.append(dict(name='all direct bins/channels/cluster errors',status='passed',bins=len(correlations)))
    return checks,series[0]


def equilibrium_reference(model,temperature,count=65536,seed=433301):
    """Independent CPU ensemble, bounded coordinate chunks; only six channels retained."""
    rng=np.random.default_rng(seed); channels=np.empty((count,6));index=0
    while index<count:
        batch=model.sample(min(128,count-index),rng,kbt=temperature)
        for r in batch:
            w=virials(model,r)
            channels[index]=np.r_[w['shears'],w['normal_differences']];index+=1
    return dict(key=model_key(model,temperature),count=count,seed=seed,kbt=temperature,
                parameters=dict(b0=model.b0.tolist(),kb=model.kb.tolist(),kappa=model.kappa.tolist()),
                statistics=channel_statistics(channels))


def equilibrium_checks(actual,reference):
    stats=reference['statistics']; diagonal=np.diag(stats['products']['mean'])
    scales=np.sqrt(diagonal[:,None]*diagonal[None,:]);checks=[]
    for kind in ('products','covariance'):
        checks.append(compare_statistics('initial CPU equilibrium '+kind,actual[kind],stats[kind],scales))
    return checks


def memory_observation(run,result):
    """Legacy peak/whole-device logs plus optional process RSS series; no invention."""
    out=Path(run['output']); checks=[];data={}
    timefile=Path(str(out)+'.time');gpufile=Path(str(out)+'.gpu.csv');monitor=Path(str(out)+'.monitor.csv')
    if timefile.exists():
        import re
        found=re.findall(r'Maximum resident set size \(kbytes\):\s*(\d+)',timefile.read_text())
        require(len(found)==1,'missing/duplicate time peak RSS')
        data['peak_rss_kib']=int(found[0])
    else:
        checks.append(dict(name='peak CPU RSS',status='missing_data',reason='external /usr/bin/time record absent'))
    if gpufile.exists():
        minimum,maximum,count=float('inf'),0.,0;production_min,production_max,production_count=float('inf'),0.,0
        gpu_previous=gpu_start=None;gpu_length=0;gpu_growth=0.
        for row in rows(gpufile):
            key=next((k for k in row if k.strip().startswith('memory.used')),None)
            require(key is not None,'malformed nvidia-smi header')
            value=float(row[key].strip().split()[0])
            require(math.isfinite(value) and value>=0,'invalid GPU memory measurement')
            minimum=min(minimum,value);maximum=max(maximum,value);count+=1
            if row.get('production_observed')=='1':
                production_min=min(production_min,value);production_max=max(production_max,value);production_count+=1
                if gpu_previous is None or value<gpu_previous:gpu_start=value;gpu_length=1
                else:gpu_length+=1
                if gpu_length>=3:gpu_growth=max(gpu_growth,value-gpu_start)
                gpu_previous=value
        if not count:checks.append(dict(name='GPU monitoring observations',status='missing_data',reason='monitor contains no GPU measurements'))
        if count:data['whole_device_gpu_mib']=[production_min,production_max] if production_count else [maximum,maximum]
        data['gpu_production_points']=production_count
        if production_count>=3:
            bound=max(16,.05*production_min)
            checks.append(dict(name='within-run whole-device GPU stability',status='passed' if production_max-production_min<=bound else 'failed' if gpu_growth>bound else 'insufficient_support',monotone_growth_mib=gpu_growth,range_mib=production_max-production_min,allowance_mib=bound))
        else:
            checks.append(dict(name='within-run whole-device GPU stability',status='insufficient_support',reason='no production-scoped GPU plateau series with at least three observations; peak alone is insufficient'))
    else:
        checks.append(dict(name='whole-device GPU memory',status='missing_data',reason='GPU monitoring record absent'))
    if monitor.exists():
        count=0;first=minimum=float('inf');maximum=0.;last_time=-1.;previous=start=None;length=0;growth=0.
        for row in rows(monitor,('elapsed_seconds','cpu_rss_kib','production_observed')):
            t=number(row,'elapsed_seconds');rss=number(row,'cpu_rss_kib');active=number(row,'production_observed',True)
            require(rss>=0 and t>=0 and active in (0,1) and t>last_time,'invalid RSS monitor/timestamps')
            last_time=t
            if active:
                if count==0:first=rss/1024
                minimum=min(minimum,rss/1024);maximum=max(maximum,rss/1024);count+=1
                if previous is None or rss<previous:start=rss;length=1
                else:length+=1
                if length>=3:growth=max(growth,(rss-start)/1024)
                previous=rss
        if count<3:
            checks.append(dict(name='within-run RSS stability',status='insufficient_support',reason='fewer than three production monitoring observations'))
        else:
            bound=max(16,.05*first)
            checks.append(dict(name='within-run RSS stability',status='passed' if maximum-minimum<=bound else 'failed' if growth>bound else 'insufficient_support',monotone_growth_mib=growth,range_mib=maximum-minimum,allowance_mib=bound))
        data['rss_series_points']=count
    else:
        checks.append(dict(name='within-run RSS stability',status='insufficient_support',reason='legacy evidence contains only peak RSS, not a resident-memory time series'))
    data['checks']=checks
    return data


def campaign_comparisons(manifest,ids,results,references):
    checks=[];groups={};replay={};memory={}
    for run,rid in zip(manifest,ids):
        result=results.get(rid)
        if not result or 'metadata' not in result:continue
        opts=options(run);temp=float(opts['kbt']);model=model_file(opts['parameters']);key=model_key(model,temp)
        reference=references.get(key)
        if 'initial_channels' in result:
            if reference is None:
                checks.append(dict(name=rid+': CPU equilibrium ensemble',status='missing_data',reason='authenticated 65536-chain CPU reference absent'))
            else:
                checks += [dict(g,run_id=rid) for g in equilibrium_checks(result['initial_channels'],reference)]
        if run['phase']=='stream':
            groups.setdefault((run['precision'],run['label']),[]).append((run,rid,result))
        if run['phase']=='reference':
            replay.setdefault((run['precision'],run['label']),[]).append((run,rid,result))
        if run['phase']=='memory':
            memory.setdefault(run['precision'],[]).append((run,rid,result))
    for key,entries in replay.items():
        if len(entries)!=3:
            checks.append(dict(name=str(key)+': worker/batch replay',status='missing_data'));continue
        hashes=[digest(Path(run['output'])/'stress_correlations.csv') for run,_,_ in entries]
        checks.append(dict(name=str(key)+': worker/batch byte replay',status='passed' if len(set(hashes))==1 else 'failed'))
    for key,entries in groups.items():
        by_seed={};by_dt={}
        for run,rid,result in entries:
            by_seed.setdefault(int(options(run)['seed']),[]).append((run,rid,result))
            by_dt.setdefault(float(options(run)['dt']),[]).append((run,rid,result))
        for seed,replicas in by_seed.items():
            name=f'{key}/seed{seed}'
            if len(replicas)!=3:
                checks.append(dict(name=name+': timestep matrix',status='missing_data'));continue
            replicas.sort(key=lambda item:float(options(item[0])['dt']),reverse=True)
            coarse,middle,fine=[item[2] for item in replicas]
            zero=np.array([fine['correlations'][0][col] for col in COLS]);product_scale=np.sqrt(abs(zero[:,None]*zero[None,:]))
            model=model_file(options(replicas[0][0])['parameters']);ref=references.get(model_key(model,coarse['metadata']['kbt']))
            for kind,scale in (('mean',abs(zero)),('products',product_scale)):
                independent=(dict(mean=[0.]*6,se=[0.]*6) if kind=='mean' else ref['statistics']['products'] if ref else None)
                checks+=refinement(name+': '+kind,coarse['time_statistics'][kind],middle['time_statistics'][kind],fine['time_statistics'][kind],scale,independent)
            require(len(middle['correlations'])==len(fine['correlations']),'timestep lag grids differ')
            resolved_count=0
            for rc,rm,rf in zip(coarse['correlations'],middle['correlations'],fine['correlations']):
                require(rc['lag_samples']==rm['lag_samples']==rf['lag_samples'],'timestep lag mismatch')
                for channel in COLS+('H',):
                    scale=abs(fine['correlations'][0][channel]);resolved=abs(rm[channel])>6*rm[channel+'_se'] or abs(rf[channel])>6*rf[channel+'_se']
                    if not resolved:continue
                    resolved_count+=1
                    values=[dict(mean=np.array(r[channel]),se=np.array(r[channel+'_se'])) for r in (rc,rm,rf)]
                    independent=None
                    if key[1]=='gaussian-control':
                        # Each dt has its own exact reference; compare errors for the bias gate.
                        preds=[gaussian_reference(v['metadata'],int(r['lag_samples']),int(r['block_samples']),v['stress_metadata']['frames'])*(4 if channel in COLS[3:] else 1) for v,r in zip((coarse,middle,fine),(rc,rm,rf))]
                        ec=values[0]['mean']-preds[0];ef=values[2]['mean']-preds[2]
                        bias=refinement(name+f': Gaussian residual {channel}/{rc["lag_samples"]}',dict(mean=ec,se=values[0]['se']),dict(mean=ec,se=values[0]['se']),dict(mean=ef,se=values[2]['se']),scale,dict(mean=np.array(0.),se=np.array(0.)))[1:]
                        checks+=bias
                    checks.append(gate(name+f': dt {channel}/{rc["lag_samples"]}',values[2]['mean'],values[1]['mean'],values[2]['se'],values[1]['se'],fraction=.01,scale=scale))
            if not resolved_count:checks.append(dict(name=name+': resolved timestep bins',status='insufficient_support'))
        for dt,replicas in by_dt.items():
            if len(replicas)!=3:
                checks.append(dict(name=str(key)+f': seed matrix dt{dt}',status='missing_data'));continue
            for i in range(3):
                for j in range(i):
                    left,right=replicas[i][2],replicas[j][2];name=f'{key}/dt{dt}/seeds{replicas[i][0]["seed"]}-{replicas[j][0]["seed"]}'
                    zero=np.array([left['correlations'][0][col] for col in COLS])
                    for kind,scale in (('mean',abs(zero)),('products',np.sqrt(abs(zero[:,None]*zero[None,:])))):
                        checks.append(compare_statistics(name+': '+kind,left['time_statistics'][kind],right['time_statistics'][kind],scale))
                    for a,b in zip(left['correlations'],right['correlations']):
                        for col in COLS+('H',):
                            if abs(a[col])>6*a[col+'_se'] or abs(b[col])>6*b[col+'_se']:
                                checks.append(gate(name+f': {col}/{a["lag_samples"]}',np.array(a[col]),np.array(b[col]),a[col+'_se'],b[col+'_se'],fraction=.01,scale=abs(left['correlations'][0][col])))
    for precision,entries in memory.items():
        if len(entries)!=6:
            checks.append(dict(name=precision+': memory matrix',status='missing_data'));continue
        for repeat in range(3):
            pair=[e for e in entries if f'-r{repeat}-' in e[0]['output']]
            pair.sort(key=lambda e:e[2]['metadata']['steps'])
            short,long=[e[2] for e in pair]
            for k in ('gpu_stress_bytes','host_stress_batch_bytes','estimated_bytes'):
                checks.append(dict(name=f'{precision}/r{repeat}: fixed {k}',status='passed' if short['stress_metadata'][k]==long['stress_metadata'][k] else 'failed'))
            for label in ('peak_rss_kib','whole_device_gpu_mib'):
                if label not in short.get('memory',{}) or label not in long.get('memory',{}):
                    checks.append(dict(name=f'{precision}/r{repeat}: {label} comparison',status='missing_data'));continue
                a,b=short['memory'][label],long['memory'][label]
                if isinstance(a,list):
                    allowance=max(16,.05*a[0]);growth=b[1]-a[0]
                else:
                    allowance=max(16*1024,.05*a);growth=b-a
                checks.append(dict(name=f'{precision}/r{repeat}: {label} stability',status='passed' if growth<=allowance else 'failed',observed_growth=growth,allowance=allowance))
    return checks
