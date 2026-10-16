#pragma once
#include "uammd.cuh"
#include <curand_kernel.h>
#include <climits>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace semiflexible {
using namespace uammd;
using Counter = unsigned long long;
constexpr Counter maxSteps = (~Counter(0))/8;
inline void check(cudaError_t e, const char* where) {
  if (e != cudaSuccess) throw std::runtime_error(std::string(where)+": "+cudaGetErrorString(e));
}
__device__ inline bool finite(real3 v) { return isfinite(v.x)&&isfinite(v.y)&&isfinite(v.z); }
__device__ inline real norm(real3 v) { return hypot(hypot(v.x,v.y),v.z); }
// Error key orders by bead then reason: 1 coordinates, 2 stretch, 3 bend,
// 4 nonfinite energy/force, 5 proposed update. Host aborts before another step.
__device__ inline void fail(int* error, int bead, int reason) { atomicMin(error,bead*8+reason); }

__global__ void stretch(const real4* r, real4* f, const real2* bonds,
                        int count, int m, int* error) {
  int i=blockIdx.x*blockDim.x+threadIdx.x;
  if(i>=count) return;
  int j=i%m;
  real3 fi=make_real3(0); real energy=0;
  if(!finite(make_real3(r[i]))) fail(error,i,1);
  for(int b=j-1;b<=j;++b) {
    if(b<0 || b>=m-1) continue;
    int left=i-j+b;
    real3 q=make_real3(r[left+1])-make_real3(r[left]);
    real l=norm(q); real2 p=bonds[b]; // x=b0,y=kb
    if(!isfinite(l) || (l==0 && p.x!=0)) { fail(error,i,2); continue; }
    real3 g=l==0 ? p.y*q : (p.y*(l-p.x))*(q/l);
    fi += (j==b ? real(1):real(-1))*g;
    energy += real(0.25)*p.y*(l-p.x)*(l-p.x);
  }
  if(!finite(fi)||!isfinite(energy)) fail(error,i,4);
  f[i]=make_real4(fi,energy);
}

// One writer per bead. Each active angle is recomputed by its three beads;
// no scatter/atomics are used for force accumulation.
__global__ void bend(const real4* r, real4* f, const real* kappa,
                     int count, int m, int* error) {
  int i=blockIdx.x*blockDim.x+threadIdx.x;
  if(i>=count) return;
  int j=i%m;
  real3 fi=make_real3(f[i]); real energy=f[i].w;
  for(int a=j-1;a<=j+1;++a) {
    if(a<1 || a>=m-1) continue;
    real k=kappa[a];
    if(k==0) continue; // No normalization or angular geometry for inactive angles.
    int center=i-j+a;
    real3 qa=make_real3(r[center])-make_real3(r[center-1]);
    real3 qb=make_real3(r[center+1])-make_real3(r[center]);
    real la=norm(qa), lb=norm(qb);
    if(!(la>0 && lb>0 && isfinite(la) && isfinite(lb))) { fail(error,i,3); continue; }
    real3 u=qa/la,v=qb/lb; real c=dot(u,v);
    real3 A=(-k/la)*(v-c*u),B=(-k/lb)*(u-c*v);
    fi += j==a-1 ? A : (j==a ? B-A : -B);
    real3 d=u-v;
    energy += (k/real(6))*dot(d,d); // One third of k*|u-v|^2/2.
  }
  if(!finite(fi)||!isfinite(energy)) fail(error,i,4);
  f[i]=make_real4(fi,energy);
}

__device__ inline real3 gaussian(Counter seed, Counter identity, Counter step) {
  curandStatePhilox4_32_10_t state;
  // Domain 3 is disjoint from all Rouse domains; identities are stable flat IDs.
  curand_init(seed,identity|(Counter(3)<<62),step*8,&state);
#ifdef DOUBLE_PRECISION
  auto a=curand_normal2_double(&state),b=curand_normal2_double(&state);
  return make_real3(a.x,a.y,b.x);
#else
  auto a=curand_normal4(&state); return make_real3(a.x,a.y,a.z);
#endif
}
__global__ void update(const real4* old, real4* next, const real4* f, int count,
                       real mobilityStep, real noise, Counter seed, Counter step, int* error) {
  int i=blockIdx.x*blockDim.x+threadIdx.x;
  if(i>=count) return;
  real3 p=make_real3(old[i])+mobilityStep*make_real3(f[i])+noise*gaussian(seed,i,step);
  if(!finite(p)) fail(error,i,5);
  next[i]=make_real4(p,0);
}
} // namespace semiflexible
