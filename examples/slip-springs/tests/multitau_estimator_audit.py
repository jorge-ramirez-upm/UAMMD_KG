"""Independent CPU audit of the frozen KG multi-tau recurrence.

The recurrence below is intentionally small and scalar. It is compared to direct
time-origin products and to the exact correlation of non-overlapping block means;
it is not used by production code.
"""
import argparse
import math
import numpy as np

def multi_tau(values, slots, levels, m=2):
    shifts=[[-2e10]*slots for _ in range(levels)]
    sums=[0.]*levels; counts=[0]*levels; cursors=[0]*levels; kmax=0
    corr=[[0.]*slots for _ in range(levels)]; n=[[0]*slots for _ in range(levels)]
    def add(w,k=0):
        nonlocal kmax
        if k==levels:return
        kmax=max(kmax,k); i=cursors[k]; shifts[k][i]=w
        sums[k]+=w; counts[k]+=1
        if counts[k]==m:
            sums[k]=sums[k]/m; counts[k]=0; forwarded=sums[k]; sums[k]=0.; add(forwarded,k+1)
        if k==0: offsets=range(slots)
        else: offsets=range(slots//m,slots)
        for j in offsets:
            other=(i-j if k==0 else i-slots//m-(j-slots//m))%slots
            if shifts[k][other]>-1e10:
                corr[k][j]+=shifts[k][i]*shifts[k][other]; n[k][j]+=1
        cursors[k]=(i+1)%slots
    for x in values:add(float(x))
    out=[]
    # KG evaluate intentionally omits the deepest populated level (kmax).
    for k in range(min(kmax,levels)):
        js=range(slots) if k==0 else range(slots//m,slots)
        for j in js:
            if n[k][j]:out.append((j*m**k,corr[k][j]/n[k][j],n[k][j],m**k,k))
    return out

def direct(values, lag):
    return float(np.mean(values[:len(values)-lag]*values[lag:])), len(values)-lag

def block_expected(values, width, lag):
    blocks=values[:len(values)//width*width].reshape(-1,width).mean(axis=1)
    offset=lag//width
    return direct(blocks,offset)

def ar1(rng,n,phi):
    x=np.zeros(n); noise=rng.normal(size=n); scale=math.sqrt(1-phi*phi)
    x[0]=rng.normal()
    for i in range(1,n):x[i]=phi*x[i-1]+scale*noise[i]
    return x

def sequence(kind,seed,n):
    rng=np.random.default_rng(seed)
    if kind=='white':return rng.normal(size=n)
    if kind=='exp':return ar1(rng,n,.97)
    if kind=='fast-slow':return .7*ar1(rng,n,.7)+.3*ar1(rng,n,.995)
    if kind=='tail':return .2*ar1(rng,n,.8)+.8*ar1(rng,n,.9995)
    if kind=='deterministic':
        t=np.arange(n);return np.cos(.013*t)+.4*np.cos(.071*t+.3)+.2*np.sin(.003*t)
    raise ValueError(kind)

def compare(kind,slots,levels,n=131072,repeats=8):
    errors=[]; block_errors=[]; pair_rows=[]
    for rep in range(repeats):
        x=sequence(kind,433700+rep,n); multi=multi_tau(x,slots,levels)
        for lag,value,pairs,width,level in multi:
            expected,raw=direct(x,lag); bmean,bpairs=block_expected(x,width,lag)
            errors.append(abs(value-expected));block_errors.append(abs(value-bmean));pair_rows.append((lag,pairs,raw,width,level))
    return {'kind':kind,'slots':slots,'levels':levels,'observations':n,'repeats':repeats,
            'bins':len(multi),'max_abs_vs_instant':max(errors or [0]),
            'max_abs_vs_block_expected':max(block_errors or [0]),
            'first_lag':pair_rows[0][0] if pair_rows else None,
            'last_lag':pair_rows[-1][0] if pair_rows else None,
            'last_pairs':pair_rows[-1][1] if pair_rows else None,
            'last_raw_pairs':pair_rows[-1][2] if pair_rows else None,
            'last_width':pair_rows[-1][3] if pair_rows else None}

def main():
    p=argparse.ArgumentParser();p.add_argument('--observations',type=int,default=131072);p.add_argument('--repeats',type=int,default=8);a=p.parse_args()
    for kind in ('white','exp','fast-slow','tail','deterministic'):
        for slots,levels in ((16,16),(32,15),(64,14)):
            print(compare(kind,slots,levels,a.observations,a.repeats))

if __name__=='__main__':main()
