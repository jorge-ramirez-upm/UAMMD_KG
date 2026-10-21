#pragma once
#include "semiflexible.cuh"
#include "slip_hopping.h"

namespace slip_hopping {
using namespace semiflexible;
struct Spring {
  real4 anchor;
  int site,chain,previous=-1,next=-1;
};
struct Statistics {
  Counter batches=0,attempts=0,accepted=0,boundary=0,occupied=0,metropolis=0;
};
enum Result { accepted, boundary, occupied, metropolis, invalid };

// All intermediate energy/acceptance arithmetic is double, on stored real
// coordinates and the exact same precision-rounded stiffness as the force.
__device__ inline Result attempt(const real4* r,Spring* springs,int* occupancy,
                                 real4* dense,int m,int count,int z,int j,int delta,
                                 double logUniform,real stiffness,double kbt,int* error) {
  if(j<0||j>=z||(delta!=-1&&delta!=1)||!isfinite(logUniform)||logUniform>0) {
    fail(error,0,6);return invalid;
  }
  Spring& s=springs[j];
  if(s.site<0||s.site>=count||s.site/m!=s.chain||occupancy[s.site]!=j) {fail(error,0,6);return invalid;}
  const int bead=s.site%m;
  if(bead+delta<0||bead+delta>=m) return boundary;
  const int dest=s.site+delta;
  if(occupancy[dest]!=-1) return occupied;
  if((s.previous!=-1 && (s.previous<0||s.previous>=z||springs[s.previous].site>=dest)) ||
     (s.next!=-1 && (s.next<0||s.next>=z||springs[s.next].site<=dest))) {
    fail(error,s.site,6);return invalid;
  }
  const real4 a=s.anchor,old=r[s.site],next=r[dest];
  // Difference of squares, avoiding subtraction of two large total energies.
  const double coefficient=0.5*double(stiffness)/kbt;
  const double dx=double(next.x)-old.x,dy=double(next.y)-old.y,dz=double(next.z)-old.z;
  const double sumx=(double(next.x)-a.x)+(double(old.x)-a.x);
  const double sumy=(double(next.y)-a.y)+(double(old.y)-a.y);
  const double sumz=(double(next.z)-a.z)+(double(old.z)-a.z);
  const double change=(coefficient*dx)*sumx+(coefficient*dy)*sumy+(coefficient*dz)*sumz;
  if(!isfinite(change)) {fail(error,s.site,7);return invalid;}
  if(change>0 && logUniform>=-change) return metropolis;
  occupancy[s.site]=-1; dense[s.site]=make_real4(0,0,0,0);
  s.site=dest;occupancy[dest]=j;dense[dest]=s.anchor;
  return accepted;
}

__device__ inline double uniform(curandStatePhilox4_32_10_t& rng,int* error) {
  for(int retry=0;retry<128;++retry) {
    double u=curand_uniform_double(&rng);
    if(u>0&&u<1) return u;
  }
  fail(error,0,7);return 0.5;
}
__device__ inline unsigned index(curandStatePhilox4_32_10_t& rng,unsigned z,int* error) {
  const unsigned threshold=(-z)%z;
  for(int retry=0;retry<128;++retry) {
    unsigned value=curand(&rng);
    if(value>=threshold)return value%z;
  }
  fail(error,0,7);return 0;
}
// Exponential interarrival construction of Poisson K. Avoid curand_poisson's
// large-mean normal approximation and float conversion of the requested mean.
__device__ inline unsigned poisson(curandStatePhilox4_32_10_t& rng,double mean,int* error) {
  if(!(isfinite(mean)&&mean>=0&&mean<=maxMean)) {fail(error,0,7);return 0;}
  if(mean==0)return 0;
  double arrival=0;
  for(unsigned k=0;k<=maxEvents;++k) {
    arrival-=log(uniform(rng,error));
    if(*error!=INT_MAX)return 0;
    if(arrival>mean)return k;
  }
  fail(error,0,7);return 0;
}
__device__ inline bool recordCount(unsigned k,Statistics* stats,int* error) {
  if(k>maxEvents||stats->batches==~Counter(0)||stats->attempts>~Counter(0)-k) {
    fail(error,0,7);return false;
  }
  ++stats->batches;stats->attempts+=k;return true;
}
__device__ inline void batch(const real4* r,Spring* springs,int* occupancy,real4* dense,
                             int m,int count,int z,real stiffness,double kbt,double mean,
                             Counter seed,Counter step,Statistics* stats,int* error) {
  if(!z||mean==0)return;
  // One disjoint subsequence per BD step, not a fixed draw offset: K is variable.
  // [2^61,2^62) is disjoint from stable bead IDs and Rouse/BD domains 1/2/3.
  if(step>maxSteps) {fail(error,0,7);return;}
  curandStatePhilox4_32_10_t rng;
  curand_init(seed,(Counter(1)<<61)|step,0,&rng);
  const unsigned k=poisson(rng,mean,error);
  if(*error!=INT_MAX)return;
  if(!recordCount(k,stats,error))return;
  for(unsigned event=0;event<k;++event) {
    const int j=index(rng,z,error),delta=(curand(&rng)&1)?1:-1;
    const double logu=log(uniform(rng,error));
    if(*error!=INT_MAX)return;
    const Result result=attempt(r,springs,occupancy,dense,m,count,z,j,delta,logu,stiffness,kbt,error);
    if(result==invalid)return;
    if(result==accepted)++stats->accepted;
    else if(result==boundary)++stats->boundary;
    else if(result==occupied)++stats->occupied;
    else ++stats->metropolis;
  }
}
__device__ inline void invariant(const Spring* springs,const int* occupancy,const real4* dense,
                                 int m,int count,int z,int j,int* error) {
  const Spring s=springs[j];
  if(s.site<0||s.site>=count||s.chain!=s.site/m||occupancy[s.site]!=j) {fail(error,0,6);return;}
  const real4 a=dense[s.site];
  if(a.x!=s.anchor.x||a.y!=s.anchor.y||a.z!=s.anchor.z||a.w!=1) {fail(error,s.site,6);return;}
  for(int direction=-1;direction<=1;direction+=2) {
    int neighbor=direction<0?s.previous:s.next;
    if(neighbor==-1)continue;
    if(neighbor<0||neighbor>=z) {fail(error,s.site,6);return;}
    const Spring other=springs[neighbor];
    if(other.chain!=s.chain||(direction<0?other.site>=s.site:other.site<=s.site)||
       (direction<0?other.next:other.previous)!=j)fail(error,s.site,6);
  }
}
__device__ inline void siteInvariant(const Spring* springs,const int* occupancy,const real4* dense,
                                     int z,int i,int* error) {
  int j=occupancy[i];
  if(j==-1) {if(dense[i].w!=0)fail(error,i,6);return;}
  if(j<0||j>=z||springs[j].site!=i)fail(error,i,6);
}
__global__ void hopping(const real4* r,Spring* springs,int* occupancy,real4* dense,
                        int m,int count,int z,real stiffness,double kbt,double mean,
                        Counter seed,Counter step,Statistics* stats,int* error) {
  if(blockIdx.x||threadIdx.x)return;
  batch(r,springs,occupancy,dense,m,count,z,stiffness,kbt,mean,seed,step,stats,error);
}
__global__ void checkState(const Spring* springs,const int* occupancy,const real4* dense,
                           int m,int count,int z,int* error) {
  int j=blockIdx.x*blockDim.x+threadIdx.x;
  if(j<count)siteInvariant(springs,occupancy,dense,z,j,error);
  if(j<z)invariant(springs,occupancy,dense,m,count,z,j,error);
}
} // namespace slip_hopping
