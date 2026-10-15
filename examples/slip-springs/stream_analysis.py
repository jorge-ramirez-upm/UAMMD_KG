#!/usr/bin/env python3
"""Stage 2B chain-cluster gates and exact point/block-averaged Rouse references."""
import argparse
import json
from pathlib import Path
import numpy as np
import validate as rouse

CHANNELS=('Cxy','Cxz','Cyz','Cxx_yy','Cxx_zz','Cyy_zz')

def geometric_mean(logq, count):
    """Mean exp(j*logq), j=0..count-1; stable also when logq ~ 0."""
    logq=np.asarray(logq)
    with np.errstate(divide='ignore',invalid='ignore'):
        result=np.expm1(count*logq)/(count*np.expm1(logq))
    return np.where(logq==0,1.,result)

def reference(meta, lag, block, continuous=False):
    """Actual exported bin convention, including startup and completed blocks.

    For later block j and earlier block i, Wick gives
    sum_p lambda_p^2 v_p(n_i)^2 a_p^(2(n_j-n_i)).
    Expand v(n)^2 into three terms, then sum geometrically over origins and
    the two block offsets. This averages covariance SQUARED, never its square
    after averaging, and uses O(N) work/memory even for very coarse bins.
    """
    n,dt,stride=meta['springs'],meta['dt'],meta['sample']
    frames=meta['stress_frames']
    lam,_=rouse.modes(n)
    if block<1 or lag%block or lag<0: raise ValueError('invalid lag/block')
    i=lag//block
    origins=frames//block-i
    if origins<1 or (block>1 and i<1): raise ValueError('unpopulated/unsupported bin')
    if continuous:
        logq=-2*lam*dt*stride
        if block==1: return float(np.exp(logq*lag).sum())
        ab=geometric_mean(logq,block)
        return float((np.exp(logq*((i-1)*block+1))*ab**2).sum())
    a=1-lam*dt
    if np.any(np.abs(a)>=1): raise ValueError('unstable EM timestep')
    with np.errstate(divide='ignore'):
        loga=np.log(np.abs(a))
    logq=2*stride*loga
    star=1/(lam*(1-lam*dt/2))
    delta=1/lam-star
    initial=np.ones_like(lam) if meta['equil']==0 else np.exp(2*meta['equil']*loga)
    ab=geometric_mean(logq,block)
    ar=geometric_mean(logq*block,origins)
    ar2=geometric_mean(logq*2*block,origins)
    if block==1:
        base=np.ones_like(lam) if lag==0 else np.exp(logq*lag)
        terms=base*(star**2+2*star*delta*initial*ar+delta**2*initial**2*ar2)
    else:
        terms=(star**2*np.exp(logq*((i-1)*block+1))*ab**2+
               2*star*delta*initial*np.exp(logq*i*block)*ab*ar+
               delta**2*initial**2*np.exp(logq*i*block)*ab**2*ar2)
    return float((lam**2*terms).sum())

def analyze(directory,terminal=False,min_pairs=8):
    meta=json.loads((directory/'metadata.json').read_text())
    if meta['output_mode']!='stream' or meta['chains']<2: raise ValueError('need streaming and >=2 independent chains')
    rows=np.atleast_1d(np.genfromtxt(directory/'relaxation.csv',names=True,delimiter=','))
    checks=[]
    for row in rows:
        if row['pairs_per_chain']<min_pairs: continue
        lag,block=int(row['lag_samples']),int(row['block_samples'])
        em=reference(meta,lag,block)
        continuous=reference(meta,lag,block,True)
        for name in ('g',)+CHANNELS:
            scale=4 if name in CHANNELS[3:] else 1
            se=row['g_se'] if name=='g' else row[name+'_se']
            item=rouse.record(name,row[name]/scale,se/scale,em,continuous)
            item.update(lag_samples=lag,block_samples=block,pairs_per_chain=int(row['pairs_per_chain']))
            checks.append(item)
    if not checks: raise ValueError('no bins satisfy the declared minimum pair count')
    tail=[]
    if terminal:
        lam,_=rouse.modes(meta['springs']); tau=1/(2*lam[0])
        for multiple in (2,4):
            target=multiple*tau
            index=int(np.argmin(np.abs(rows['lag_time']-target)))
            row=rows[index]
            # Coverage and resolved positive signal are mandatory, beyond mere
            # consistency with a broad confidence interval containing zero.
            tail.append(dict(target=target,lag_time=float(row['lag_time']),g=float(row['g']),
                             se=float(row['g_se']),passed=bool(abs(row['lag_time']-target)<=.25*target
                             and row['pairs_per_chain']>=min_pairs and row['g']>2*row['g_se'])))
    result=dict(metadata=meta,z_limit=rouse.Z_LIMIT,min_pairs=min_pairs,checks=checks,terminal=tail,
                passed=all(x['passed'] for x in checks+tail))
    rouse.save(directory/'stream_analysis.json',result)
    print('PASS' if result['passed'] else 'FAIL',len(checks),'5-SE chain-cluster gates;',directory/'stream_analysis.json')
    return result['passed']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory',type=Path)
    p.add_argument('--terminal',action='store_true')
    p.add_argument('--min-pairs',type=int,default=8)
    a=p.parse_args()
    if a.min_pairs<1: p.error('--min-pairs must be positive')
    return 0 if analyze(a.directory,a.terminal,a.min_pairs) else 1
if __name__=='__main__': raise SystemExit(main())
