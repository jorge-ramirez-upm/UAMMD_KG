// Test-only bounded fixtures exercising production transfers and complete batches.
#include "../slip_renewal.cuh"
#include "../semiflexible_slipspring.cuh"
#include <thrust/device_vector.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <math_constants.h>
#include <vector>
#include <algorithm>
using namespace semiflexible;
namespace hop=slip_hopping;
namespace renewal=slip_renewal;
struct Operation {int kind,j,delta,destination;double u;real4 candidate;};
struct Trial {
  hop::Spring springs[8];int occupancy[16];Operation ops[16];int results[16];
  hop::Statistics stats;renewal::Statistics renew;
  Counter seed;int error=INT_MAX;
};
__device__ void validate(Trial& t,real4* dense,int m,int count,int z) {
  for(int i=0;i<count;++i)hop::siteInvariant(t.springs,t.occupancy,dense,z,i,&t.error);
  for(int j=0;j<z;++j)hop::invariant(t.springs,t.occupancy,dense,m,count,z,j,&t.error);
}
__global__ void run(Trial* cases,real4* positions,real4* allDense,int n,int m,int count,int z,
                    int operations,int batches,double mean,double ms2,double kbt) {
  int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=n)return;
  Trial& t=cases[i];real4* dense=allDense+i*count;real4* r=positions+i*count;
  for(int b=0;b<count;++b){t.occupancy[b]=-1;dense[b]=make_real4(0,0,0,0);}
  for(int j=0;j<z;++j){t.occupancy[t.springs[j].site]=j;dense[t.springs[j].site]=t.springs[j].anchor;}
  validate(t,dense,m,count,z);if(t.error!=INT_MAX)return;
  curandStatePhilox4_32_10_t rng;curand_init(t.seed,renewal::rngBase,0,&rng);
  const double sigma=sqrt(ms2)/sqrt(3.);const real k=real(3*kbt/ms2);
  for(int e=0;e<operations;++e) {
    auto op=t.ops[e];
    if(op.kind==0) {
      auto result=hop::attempt(r,t.springs,t.occupancy,dense,m,count,z,op.j,op.delta,log(op.u),k,kbt,&t.error);
      t.results[e]=result==hop::invalid?6:int(result);
    } else {
      renewal::Result result;
      if(op.kind==2)result=renewal::propose(r,t.springs,t.occupancy,dense,m,count,z,op.j,sigma,rng,&t.error);
      else {
        if(op.kind==3)op.candidate.x=real(CUDART_INF);
        result=renewal::transfer(t.springs,t.occupancy,dense,m,count,z,op.j,op.destination,op.candidate,&t.error);
      }
      t.results[e]=result==renewal::transferred?4:(result==renewal::occupied?5:6);
    }
    validate(t,dense,m,count,z);if(t.error!=INT_MAX)return;
  }
  for(int b=0;b<batches;++b) {
    renewal::batch(r,t.springs,t.occupancy,dense,m,count,z,k,kbt,mean,sigma,t.seed,b,&t.stats,&t.renew,&t.error);
    validate(t,dense,m,count,z);if(t.error!=INT_MAX)return;
  }
}
int main(int argc,char** argv) {
  try {
    if(argc!=3)throw std::runtime_error("input output required");
    std::ifstream input(argv[1]);std::ofstream output(argv[2]);
    input.exceptions(std::ios::failbit|std::ios::badbit);output.exceptions(std::ios::failbit|std::ios::badbit);
    int n,m,count,z,ops,batches;double mean,ms2,kbt;
    input>>n>>m>>count>>z>>ops>>batches>>mean>>ms2>>kbt;
    if(n<1||n>32768||m<2||count<m||count>16||count%m||z<1||z>8||z>count||ops<0||ops>16||batches<0||batches>1024)
      throw std::runtime_error("fixture bounds");
    std::vector<Trial> host(n);std::vector<real4> positions(n*count);
    for(int i=0;i<n;++i) {
      auto& t=host[i];input>>t.seed;
      for(int b=0;b<count;++b){double x,y,z;input>>x>>y>>z;positions[i*count+b]=make_real4(x,y,z,0);}
      for(int j=0;j<z;++j) {
        int site;double x,y,z;input>>site>>x>>y>>z;
        if(site<0||site>=count)throw std::runtime_error("fixture site");
        t.springs[j]={make_real4(x,y,z,1),site,site/m,-1,-1};
      }
      std::vector<int> order(z);for(int j=0;j<z;++j)order[j]=j;
      std::sort(order.begin(),order.end(),[&](int a,int b){return t.springs[a].site<t.springs[b].site;});
      for(int j=1;j<z;++j)if(t.springs[order[j-1]].chain==t.springs[order[j]].chain) {
        t.springs[order[j-1]].next=order[j];t.springs[order[j]].previous=order[j-1];
      }
      for(int e=0;e<ops;++e) {
        auto& op=t.ops[e];double x,y,z;
        input>>op.kind>>op.j>>op.delta>>op.u>>op.destination>>x>>y>>z;
        op.candidate=make_real4(x,y,z,1);
      }
    }
    thrust::device_vector<Trial> cases(host);thrust::device_vector<real4> r(positions),dense(n*count),forces(n*count,make_real4(0,0,0,0));
    thrust::device_vector<int> error(1,INT_MAX);
    auto ptr=[](auto& v){return thrust::raw_pointer_cast(v.data());};
    run<<<(n+63)/64,64>>>(ptr(cases),ptr(r),ptr(dense),n,m,count,z,ops,batches,mean,ms2,kbt);
    check(cudaGetLastError(),"renewal fixtures");check(cudaDeviceSynchronize(),"renewal completion");
    fixed_slip_force<<<(n*count+255)/256,256>>>(ptr(r),ptr(forces),ptr(dense),n*count,real(3*kbt/ms2),ptr(error));
    check(cudaDeviceSynchronize(),"renewed force");
    check(cudaMemcpy(host.data(),ptr(cases),n*sizeof(Trial),cudaMemcpyDeviceToHost),"states");
    std::vector<real4> f(n*count);check(cudaMemcpy(f.data(),ptr(forces),f.size()*sizeof(real4),cudaMemcpyDeviceToHost),"forces");
    output<<std::setprecision(17)<<8*sizeof(real)<<'\n'<<int(error[0])<<'\n';
    for(int i=0;i<n;++i) {
      const auto& t=host[i];const auto s=t.stats;const auto c=t.renew;
      output<<t.error<<' '<<s.batches<<' '<<s.attempts<<' '<<s.accepted<<' '<<s.boundary<<' '<<s.occupied<<' '<<s.metropolis
            <<' '<<c.proposed<<' '<<c.accepted<<' '<<c.occupied<<' '<<c.sameChain<<' '<<c.crossChain;
      for(int j=0;j<z;++j){const auto& p=t.springs[j];output<<' '<<p.site<<' '<<p.chain<<' '<<p.previous<<' '<<p.next<<' '<<p.anchor.x<<' '<<p.anchor.y<<' '<<p.anchor.z;}
      for(int e=0;e<ops;++e)output<<' '<<t.results[e];
      for(int b=0;b<count;++b){auto v=f[i*count+b];output<<' '<<v.x<<' '<<v.y<<' '<<v.z<<' '<<v.w;}
      output<<'\n';
    }
    output.close();return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
