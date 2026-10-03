#!/usr/bin/env python3
"""K1 event/exposure analysis; input is kg_assoc_k1's compact .state file."""
import argparse,csv,glob,math,os,re,statistics,sys
def read(path):
 r=[];meta={}
 for line in open(path):
  if line.startswith('#'):
   for x in line[1:].split():
    if '=' in x:
     k,v=x.split('=',1);meta[k]=v
   continue
  x=line.split()
  if len(x)==6:r.append(tuple(map(float,x)))
 if len(r)<2:raise ValueError(path+' has too few samples')
 n=r[0][2]+2*r[0][3]
 for z in r:
  if z[2]+2*z[3]!=n or z[3]!=z[4]-z[5]:raise ValueError(path+' invariant failure')
 return r,n,meta
def integ(r,fn,kind='trap'):
 return sum((r[i+1][1]-r[i][1])*((fn(r[i])+fn(r[i+1]))/2 if kind=='trap' else fn(r[i+(kind=='right')])) for i in range(len(r)-1))
def meanse(x):return statistics.mean(x),statistics.stdev(x)/math.sqrt(len(x)) if len(x)>1 else float('nan')
def slope(points):
 x,y=zip(*points);xm=statistics.mean(x);ym=statistics.mean(y);return sum((a-xm)*(b-ym)for a,b in points)/sum((a-xm)**2 for a in x)
def main():
 p=argparse.ArgumentParser();p.add_argument('files',nargs='+');p.add_argument('--summary',default='k1.csv');a=p.parse_args();out=[]
 pat=re.compile(r'Ea([0-9.]+)_Ee([0-9.]+)_N([0-9]+)_r([0-9]+)')
 for path in sorted(set(sum((glob.glob(q)for q in a.files),[]))):
  m=pat.search(os.path.basename(path));
  if not m:continue
  ea,ee,every,rep=float(m[1]),float(m[2]),int(m[3]),int(m[4]);r,n,meta=read(path);rho=float(meta['rho']);dt=float(meta['dt']);nu0=float(meta.get('nu0',20));temp=float(meta.get('T',1))
  v=n/rho;made=r[-1][4]-r[0][4];broke=r[-1][5]-r[0][5];hf=integ(r,lambda z:z[2]*(z[2]-1)/v);hb=integ(r,lambda z:z[3]);
  ex=max(abs(integ(r,lambda z:z[2]*(z[2]-1)/v,'left')/hf-1),abs(integ(r,lambda z:z[2]*(z[2]-1)/v,'right')/hf-1),abs(integ(r,lambda z:z[3],'left')/hb-1)if hb else 0,abs(integ(r,lambda z:z[3],'right')/hb-1)if hb else 0)
  eq=r[len(r)//2:];ks=[(z[3]/v)/(z[2]/v)**2 for z in eq if z[2]>0];q=-math.expm1(-nu0*math.exp(-ea/temp)*every*dt);out.append(dict(file=path,rho=rho,Ea=ea,Ee=ee,Nevery=every,replica=rep,creations=made,breaks=broke,kf_event=made/hf if hf else float('nan'),kb_event=broke/hb if hb else float('nan'),kf_over_q=(made/hf/q)if hf else float('nan'),kb_over_q=(broke/hb/q)if hb else float('nan'),Keq_event=(made/hf)/(broke/hb)if hb and broke else float('nan'),Keq_direct=statistics.mean(ks),exposure_relative_difference=ex))
 if not out:sys.exit('no K1 files matched')
 with open(a.summary,'w',newline='')as f:w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
 groups={}
 for z in out:groups.setdefault((z['Ea'],z['Ee'],z['Nevery']),[]).append(z)
 fields=['Ea','Ee','Nevery','replicas']+[q+s for q in ('creations','breaks','kf_event','kb_event','kf_over_q','kb_over_q','Keq_event','Keq_direct','exposure_relative_difference')for s in ('','_se')]
 with open(os.path.splitext(a.summary)[0]+'_conditions.csv','w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for k,g in sorted(groups.items()):
   z=dict(zip(('Ea','Ee','Nevery'),k));z['replicas']=len(g)
   for q in ('creations','breaks','kf_event','kb_event','kf_over_q','kb_over_q','Keq_event','Keq_direct','exposure_relative_difference'):z[q],z[q+'_se']=meanse([x[q]for x in g])
   w.writerow(z)
 print('wrote',a.summary,'and condition table; all sampled invariants passed')
 if len({z['Ee']for z in out if z['Ea']==4 and z['Nevery']==100})>=2:
  for q in ('Keq_event','Keq_direct'):print('ln %s vs Ee slope'%q,slope([(z['Ee'],math.log(z[q]))for z in out if z['Ea']==4 and z['Nevery']==100 and z[q]>0]))
if __name__=='__main__':main()
