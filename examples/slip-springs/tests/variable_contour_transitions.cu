// Prepared, UNEXECUTED frozen-coordinate indexing/reciprocity fixtures.
// Production hopping/renewal helpers unchanged; no BD trajectory or sampling.
#include "../slip_renewal.cuh"
#include <thrust/device_vector.h>
#include <iostream>
using namespace semiflexible;
namespace hop=slip_hopping;
namespace renewal=slip_renewal;
__device__ void verify(hop::Spring* s,int* occ,real4* dense,int m,int count,int* error) {
  for(int i=0;i<count;++i)hop::siteInvariant(s,occ,dense,4,i,error);
  for(int j=0;j<4;++j)hop::invariant(s,occ,dense,m,count,4,j,error);
}
__global__ void fixture(const real4* r,hop::Spring* s,int* occ,real4* dense,int m,int* error) {
  const int count=2*m;
  verify(s,occ,dense,m,count,error);
  if(hop::attempt(r,s,occ,dense,m,count,4,0,1,-1000.,real(.6),1.,error)!=hop::occupied)semiflexible::fail(error,0,6);
  if(hop::attempt(r,s,occ,dense,m,count,4,1,1,-1000.,real(.6),1.,error)!=hop::accepted)semiflexible::fail(error,0,6);
  verify(s,occ,dense,m,count,error);
  if(hop::attempt(r,s,occ,dense,m,count,4,1,-1,-1000.,real(.6),1.,error)!=hop::accepted||s[1].site!=1)semiflexible::fail(error,0,6);
  if(hop::attempt(r,s,occ,dense,m,count,4,0,-1,-1000.,real(.6),1.,error)!=hop::boundary)semiflexible::fail(error,0,6);
  for(int edge=0;edge<2;++edge) {
    const int dest=edge?m-1:0;
    if(renewal::transfer(s,occ,dense,m,count,4,0,dest,r[dest],error)!=renewal::occupied)semiflexible::fail(error,0,6);
  }
  if(renewal::transfer(s,occ,dense,m,count,4,0,count-1,r[count-1],error)!=renewal::transferred)semiflexible::fail(error,0,6);
  verify(s,occ,dense,m,count,error);
  if(s[0].chain!=1||s[0].site!=count-1||s[0].previous!=3||s[3].next!=0)semiflexible::fail(error,0,6);
  if(renewal::transfer(s,occ,dense,m,count,4,2,0,r[0],error)!=renewal::transferred)semiflexible::fail(error,0,6);
  verify(s,occ,dense,m,count,error);
  if(s[2].chain!=0||s[2].next!=1||s[1].previous!=2)semiflexible::fail(error,0,6);
  if(renewal::transfer(s,occ,dense,m,count,4,2,m-1,r[m-1],error)!=renewal::transferred)semiflexible::fail(error,0,6);
  verify(s,occ,dense,m,count,error);
}
int main() {
  try {
    static_assert(sizeof(real)==8,"double precision required for new-length verification");
    for(int n:{32,64,128}) {
      const int m=n+1,count=2*m;
      std::vector<real4> r(count),dense(count,make_real4(0,0,0,0));std::vector<int> occ(count,-1);
      for(int i=0;i<count;++i)r[i]=make_real4(i%m,3*(i/m),0,0);
      std::vector<hop::Spring> s(4);
      s[0]={r[0],0,0,-1,1};s[1]={r[1],1,0,0,2};s[2]={r[n],n,0,1,-1};s[3]={r[m],m,1,-1,-1};
      for(int j=0;j<4;++j){s[j].anchor.w=1;occ[s[j].site]=j;dense[s[j].site]=s[j].anchor;}
      thrust::device_vector<real4> dr(r),dd(dense);thrust::device_vector<int> dOcc(occ),error(1,INT_MAX);
      thrust::device_vector<hop::Spring> ds(s);
      auto ptr=[](auto& v){return thrust::raw_pointer_cast(v.data());};
      fixture<<<1,1>>>(ptr(dr),ptr(ds),ptr(dOcc),ptr(dd),m,ptr(error));
      check(cudaGetLastError(),"variable contour fixture launch");check(cudaDeviceSynchronize(),"variable contour fixture");
      if(int(error[0])!=INT_MAX)throw std::runtime_error("variable contour transition/indexing mismatch N="+std::to_string(n));
    }
    std::cout<<"PASS frozen-coordinate contour fixtures N32/N64/N128; not scientific acceptance\n";
    return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
