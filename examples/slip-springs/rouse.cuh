#pragma once
#include "uammd.cuh"
#include <curand_kernel.h>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace rouse {
using namespace uammd;
using Counter = unsigned long long;
constexpr Counter maxSteps = (~Counter(0))/8;
constexpr Counter domainShift = 62;

inline void check(cudaError_t e, const char* where) {
  if (e != cudaSuccess) throw std::runtime_error(std::string(where)+": "+cudaGetErrorString(e));
}

// Eight reserved 32-bit draws per bead/step; domains 1/2 isolate bonds/translations.
__device__ inline real3 gaussian(Counter seed, Counter identity, Counter step, Counter domain=0) {
  curandStatePhilox4_32_10_t state;
  curand_init(seed, identity | (domain << domainShift), step*8, &state);
#ifdef DOUBLE_PRECISION
  const auto xy = curand_normal2_double(&state);
  const auto zw = curand_normal2_double(&state);
  return make_real3(xy.x, xy.y, zw.x);
#else
  const auto v = curand_normal4(&state);
  return make_real3(v.x, v.y, v.z);
#endif
}

__device__ inline real3 force(const real4* old, int i, int beadsPerChain) {
  const int bead = i % beadsPerChain;
  const real3 center = make_real3(old[i]);
  real3 f = make_real3(0);
  if (bead > 0) f += real(3)*(make_real3(old[i-1])-center);
  if (bead+1 < beadsPerChain) f += real(3)*(make_real3(old[i+1])-center);
  return f;
}

__global__ void update(const real4* old, real4* next, const Counter* identities,
                       int count, int beadsPerChain, real dt, Counter seed,
                       Counter step, bool thermal=true) {
  const int i = blockIdx.x*blockDim.x+threadIdx.x;
  if (i >= count) return;
  real3 p = make_real3(old[i])+dt*force(old,i,beadsPerChain);
  if (thermal) p += sqrt(real(2)*dt)*gaussian(seed,identities[i],step);
  next[i] = make_real4(p,old[i].w);
}

__global__ void initialize(real4* pos, int chains, int m, Counter seed) {
  const int c = blockIdx.x*blockDim.x+threadIdx.x;
  if (c >= chains) return;
  real3 p = gaussian(seed,c,0,2);
  pos[c*m] = make_real4(p,0);
  for (int j=1; j<m; ++j) {
    p += sqrt(real(1)/real(3))*gaussian(seed,Counter(c)*m+j,0,1);
    pos[c*m+j] = make_real4(p,0);
  }
}

struct Observation {
  double q2, ree2, rg2;
  double cm[3], ee[3], mode[3];
  double maxabs, zeroBonds;
};

// Double reductions of stored coordinates; anchoring avoids subtracting large squares.
__global__ void observe(const real4* pos, Observation* result, const double* phi,
                        int chains, int m) {
  const int c = blockIdx.x*blockDim.x+threadIdx.x;
  if (c >= chains) return;
  Observation out{};
  const real4 anchor = pos[c*m];
  const double origin[3] = {double(anchor.x),double(anchor.y),double(anchor.z)};
  double offset[3]{};
  for (int j=0; j<m; ++j) {
    const auto r = pos[c*m+j];
    const double v[3] = {double(r.x),double(r.y),double(r.z)};
    for (int a=0; a<3; ++a) {
      offset[a] += (v[a]-origin[a])/m;
      out.mode[a] += phi[j]*(v[a]-origin[a]);
      out.maxabs = fmax(out.maxabs,fabs(v[a]));
    }
    if (j) {
      const auto previous = pos[c*m+j-1];
      const double q[3] = {v[0]-double(previous.x),v[1]-double(previous.y),v[2]-double(previous.z)};
      double qsq=0;
      for (int a=0; a<3; ++a) qsq += q[a]*q[a];
      out.q2 += qsq/(m-1);
      if (qsq == 0) out.zeroBonds += 1;
    }
  }
  for (int a=0; a<3; ++a) out.cm[a] = origin[a]+offset[a];
  for (int j=0; j<m; ++j) {
    const auto r = pos[c*m+j];
    const double v[3] = {double(r.x),double(r.y),double(r.z)};
    for (int a=0; a<3; ++a) {
      const double d = (v[a]-origin[a])-offset[a];
      out.rg2 += d*d/m;
      if (j == m-1) {
        out.ee[a] = v[a]-origin[a];
        out.ree2 += out.ee[a]*out.ee[a];
      }
    }
  }
  result[c] = out;
}
} // namespace rouse
