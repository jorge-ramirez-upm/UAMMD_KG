#pragma once
#include "slip_hopping.cuh"

namespace slip_renewal {
using namespace semiflexible;
using slip_hopping::Spring;
constexpr Counter rngBase=Counter(3)<<61;
struct Statistics { Counter proposed=0,accepted=0,occupied=0,sameChain=0,crossChain=0; };
enum Result { transferred, occupied, invalid };

// Transactional end transfer: inspect occupancy and validate the candidate before
// unlinking the source. No energy/Metropolis factor belongs in this operation.
__device__ inline Result transfer(Spring* springs,int* occupancy,real4* dense,
                                  int m,int count,int z,int j,int destination,
                                  real4 candidate,int* error) {
  if(j<0||j>=z||destination<0||destination>=count ||
     (destination%m!=0&&destination%m!=m-1)) {fail(error,0,6);return invalid;}
  const Spring old=springs[j];
  if(old.site<0||old.site>=count||old.site/m!=old.chain||occupancy[old.site]!=j ||
     (old.site%m!=0&&old.site%m!=m-1)) {fail(error,0,6);return invalid;}
  // The source end is still occupied here, even for a same-chain proposal.
  if(occupancy[destination]!=-1)return occupied;
  if(!finite(make_real3(candidate))) {fail(error,old.site,7);return invalid;}
  for(int direction=-1;direction<=1;direction+=2) {
    int neighbor=direction<0?old.previous:old.next;
    if(neighbor==-1)continue;
    if(neighbor<0||neighbor>=z) {fail(error,old.site,6);return invalid;}
    const Spring other=springs[neighbor];
    if(other.chain!=old.chain||(direction<0?other.site>=old.site:other.site<=old.site)||
       (direction<0?other.next:other.previous)!=j) {fail(error,old.site,6);return invalid;}
  }
  if((old.site%m==0&&old.previous!=-1)||(old.site%m==m-1&&old.next!=-1)) {
    fail(error,old.site,6);return invalid;
  }
  const int chain=destination/m;
  const bool left=destination%m==0;
  int neighbor=-1;
  // Find the current destination extreme, excluding the source identity. This
  // also handles transferring a singleton to its own opposite vacant end.
  for(int b=left?0:m-1;b>=0&&b<m;b+=left?1:-1) {
    const int site=chain*m+b,id=occupancy[site];
    if(id==-1||id==j)continue;
    if(id<0||id>=z||springs[id].site!=site||springs[id].chain!=chain ||
       (left?springs[id].previous:springs[id].next)!=-1) {fail(error,site,6);return invalid;}
    neighbor=id;break;
  }
  if(old.previous!=-1)springs[old.previous].next=old.next;
  if(old.next!=-1)springs[old.next].previous=old.previous;
  occupancy[old.site]=-1;dense[old.site]=make_real4(0,0,0,0);
  candidate.w=real(1);
  springs[j]={candidate,destination,chain,left?-1:neighbor,left?neighbor:-1};
  if(neighbor!=-1) {
    if(left)springs[neighbor].previous=j;
    else springs[neighbor].next=j;
  }
  occupancy[destination]=j;dense[destination]=candidate;
  return transferred;
}

__device__ inline real4 anchor(const real4& position,double sigma,
                               curandStatePhilox4_32_10_t& rng,int* error,int site) {
#ifdef DOUBLE_PRECISION
  const auto a=curand_normal2_double(&rng),b=curand_normal2_double(&rng);
  const double x=a.x,y=a.y,z=b.x;
#else
  const auto a=curand_normal4(&rng);
  const double x=a.x,y=a.y,z=a.z;
#endif
  const real4 candidate=make_real4(double(position.x)+sigma*x,double(position.y)+sigma*y,double(position.z)+sigma*z,1);
  if(!finite(make_real3(candidate)))fail(error,site,7);
  return candidate;
}
__device__ inline Result propose(const real4* r,Spring* springs,int* occupancy,real4* dense,
                                 int m,int count,int z,int j,double sigma,
                                 curandStatePhilox4_32_10_t& rng,int* error) {
  const int chain=slip_hopping::index(rng,count/m,error);
  const int destination=chain*m+((curand(&rng)&1)?m-1:0);
  if(*error!=INT_MAX)return invalid;
  if(occupancy[destination]!=-1)return occupied;
  const real4 candidate=anchor(r[destination],sigma,rng,error,destination);
  if(*error!=INT_MAX)return invalid;
  return transfer(springs,occupancy,dense,m,count,z,j,destination,candidate,error);
}
__device__ inline void batch(const real4* r,Spring* springs,int* occupancy,real4* dense,
                             int m,int count,int z,real stiffness,double kbt,double mean,
                             double sigma,Counter seed,Counter step,
                             slip_hopping::Statistics* stats,Statistics* renewal,int* error) {
  if(!z||mean==0)return;
  if(step>maxSteps) {fail(error,0,7);return;}
  curandStatePhilox4_32_10_t hopRng,renewRng;
  curand_init(seed,(Counter(1)<<61)|step,0,&hopRng);
  curand_init(seed,rngBase|step,0,&renewRng);
  const unsigned k=slip_hopping::poisson(hopRng,mean,error);
  if(*error!=INT_MAX||!slip_hopping::recordCount(k,stats,error))return;
  for(unsigned event=0;event<k;++event) {
    const int j=slip_hopping::index(hopRng,z,error),delta=(curand(&hopRng)&1)?1:-1;
    const double logu=log(slip_hopping::uniform(hopRng,error));
    if(*error!=INT_MAX)return;
    const Spring s=springs[j];
    if(s.site<0||s.site>=count||s.site/m!=s.chain||occupancy[s.site]!=j) {fail(error,0,6);return;}
    if((s.site%m==0&&delta==-1)||(s.site%m==m-1&&delta==1)) {
      ++stats->boundary;++renewal->proposed;
      const Result result=propose(r,springs,occupancy,dense,m,count,z,j,sigma,renewRng,error);
      if(result==invalid)return;
      if(result==occupied)++renewal->occupied;
      else {
        ++renewal->accepted;
        if(s.chain==springs[j].chain)++renewal->sameChain;
        else ++renewal->crossChain;
      }
    } else {
      const auto result=slip_hopping::attempt(r,springs,occupancy,dense,m,count,z,j,delta,logu,stiffness,kbt,error);
      if(result==slip_hopping::invalid)return;
      if(result==slip_hopping::accepted)++stats->accepted;
      else if(result==slip_hopping::occupied)++stats->occupied;
      else if(result==slip_hopping::metropolis)++stats->metropolis;
      else {fail(error,s.site,6);return;}
    }
  }
}
__global__ void hopping(const real4* r,Spring* springs,int* occupancy,real4* dense,
                        int m,int count,int z,real stiffness,double kbt,double mean,
                        double sigma,Counter seed,Counter step,
                        slip_hopping::Statistics* stats,Statistics* renewal,int* error) {
  if(!blockIdx.x&&!threadIdx.x)batch(r,springs,occupancy,dense,m,count,z,stiffness,kbt,mean,sigma,seed,step,stats,renewal,error);
}
} // namespace slip_renewal
