// Test-only fixed-coordinate fixtures. Calls the production device kernel;
// Python supplies independent energies, enumeration and statistical oracles.
#include "../slip_hopping.cuh"
#include "../semiflexible_slipspring.cuh"
#include <thrust/device_vector.h>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <vector>
using namespace semiflexible;
namespace hop=slip_hopping;
struct Operation {int spring,delta;double uniform;};
struct Trial {
  hop::Spring springs[4]; int occupancy[8];
  Operation ops[8];int outcomes[8];hop::Statistics stats;
  int error=INT_MAX;Counter seed=0;int corrupt=0;
};
__global__ void trials(Trial* cases,real4* r,real4* dense,int n,int m,int count,int z,
                       int operations,int batches,double mean,real stiffness,double kbt) {
  int id=blockIdx.x*blockDim.x+threadIdx.x;if(id>=n)return;
  Trial& t=cases[id];real4* anchors=dense+id*count;const real4* positions=r+id*count;
  for(int i=0;i<count;++i){t.occupancy[i]=-1;anchors[i]=make_real4(0,0,0,0);}
  for(int j=0;j<z;++j){t.occupancy[t.springs[j].site]=j;anchors[t.springs[j].site]=t.springs[j].anchor;}
  if(t.corrupt)t.occupancy[t.springs[0].site]=-1;
  for(int i=0;i<count;++i)hop::siteInvariant(t.springs,t.occupancy,anchors,z,i,&t.error);
  for(int j=0;j<z;++j)hop::invariant(t.springs,t.occupancy,anchors,m,count,z,j,&t.error);
  if(t.error!=INT_MAX)return;
  for(int i=0;i<operations;++i) {
    auto op=t.ops[i];
    t.outcomes[i]=hop::attempt(positions,t.springs,t.occupancy,anchors,m,count,z,op.spring,op.delta,log(op.uniform),stiffness,kbt,&t.error);
    for(int j=0;j<z;++j)hop::invariant(t.springs,t.occupancy,anchors,m,count,z,j,&t.error);
    if(t.error!=INT_MAX)return;
  }
  for(int b=0;b<batches;++b) {
    hop::batch(positions,t.springs,t.occupancy,anchors,m,count,z,stiffness,kbt,mean,t.seed,b,&t.stats,&t.error);
    for(int j=0;j<z;++j)hop::invariant(t.springs,t.occupancy,anchors,m,count,z,j,&t.error);
    if(t.error!=INT_MAX)return;
  }
}
__global__ void randomCounts(unsigned* counts,int* errors,int n,double mean) {
  int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=n)return;
  curandStatePhilox4_32_10_t rng;curand_init(119431,i,0,&rng);
  counts[i]=hop::poisson(rng,mean,errors+i);
}
__global__ void guard(unsigned k,hop::Statistics* stat,int* error) {
  hop::recordCount(k,stat,error);
}
int main(int argc,char** argv) {
  try {
    if(argc!=3)throw std::runtime_error("fixture input output required");
    std::ifstream input(argv[1]);std::ofstream output(argv[2]);
    input.exceptions(std::ios::badbit|std::ios::failbit);output.exceptions(std::ios::badbit|std::ios::failbit);
    output<<std::setprecision(17)<<sizeof(real)*8<<'\n';
    int mode;input>>mode;
    auto ptr=[](auto& v){return thrust::raw_pointer_cast(v.data());};
    if(mode==1) {
      int n;double mean;input>>n>>mean;
      if(n<1||n>65536)throw std::runtime_error("sample budget");
      thrust::device_vector<unsigned> counts(n);thrust::device_vector<int> errors(n,INT_MAX);
      randomCounts<<<(n+127)/128,128>>>(ptr(counts),ptr(errors),n,mean);check(cudaDeviceSynchronize(),"Poisson samples");
      std::vector<unsigned> host(n);std::vector<int> error(n);
      check(cudaMemcpy(host.data(),ptr(counts),n*sizeof(unsigned),cudaMemcpyDeviceToHost),"counts");
      check(cudaMemcpy(error.data(),ptr(errors),n*sizeof(int),cudaMemcpyDeviceToHost),"errors");
      for(int i=0;i<n;++i)output<<host[i]<<' '<<error[i]<<'\n';
    } else if(mode==2) {
      unsigned k;Counter attempts,batches;input>>k>>attempts>>batches;
      hop::Statistics stat;stat.attempts=attempts;stat.batches=batches;
      thrust::device_vector<hop::Statistics> stats(1,stat);thrust::device_vector<int> errors(1,INT_MAX);
      guard<<<1,1>>>(k,ptr(stats),ptr(errors));check(cudaDeviceSynchronize(),"count guard");stat=stats[0];
      output<<int(errors[0])<<' '<<stat.attempts<<' '<<stat.batches<<'\n';
    } else {
      int n,m,count,z,operations,batches;double mean,k,kbt;
      input>>n>>m>>count>>z>>operations>>batches>>mean>>k>>kbt;
      if(n<1||n>65536||m<2||count>8||count<m||count%m||z<1||z>4||operations<0||operations>8||batches<0||batches>1000)
        throw std::runtime_error("fixture budget/dimensions");
      std::vector<Trial> host(n);std::vector<real4> positions(n*count);
      for(int i=0;i<n;++i) {
        auto& t=host[i];input>>t.seed>>t.corrupt;
        for(int bead=0;bead<count;++bead){double x,y,z;input>>x>>y>>z;positions[i*count+bead]=make_real4(x,y,z,0);}
        for(int j=0;j<z;++j) {
          double x,y,z;int site;input>>site>>x>>y>>z;
          if(site<0||site>=count)throw std::runtime_error("fixture site");
          t.springs[j]={make_real4(x,y,z,1),site,site/m,-1,-1};
          for(int p=j-1;p>=0;--p)if(t.springs[p].chain==site/m){t.springs[j].previous=p;t.springs[p].next=j;break;}
        }
        for(int j=0;j<operations;++j)input>>t.ops[j].spring>>t.ops[j].delta>>t.ops[j].uniform;
      }
      thrust::device_vector<Trial> cases(host);thrust::device_vector<real4> r(positions),dense(n*count),forces(n*count,make_real4(0,0,0,0));
      thrust::device_vector<int> forceError(1,INT_MAX);
      trials<<<(n+127)/128,128>>>(ptr(cases),ptr(r),ptr(dense),n,m,count,z,operations,batches,mean,real(k),kbt);
      check(cudaGetLastError(),"fixture launch");check(cudaDeviceSynchronize(),"fixture completion");
      fixed_slip_force<<<(n*count+255)/256,256>>>(ptr(r),ptr(forces),ptr(dense),n*count,real(k),ptr(forceError));
      check(cudaDeviceSynchronize(),"relocated force");
      check(cudaMemcpy(host.data(),ptr(cases),n*sizeof(Trial),cudaMemcpyDeviceToHost),"fixture state");
      std::vector<real4> f(n*count);check(cudaMemcpy(f.data(),ptr(forces),f.size()*sizeof(real4),cudaMemcpyDeviceToHost),"fixture forces");
      output<<int(forceError[0])<<'\n';
      for(int i=0;i<n;++i) {
        auto& t=host[i];auto stat=t.stats;
        output<<t.error<<' '<<stat.batches<<' '<<stat.attempts<<' '<<stat.accepted<<' '<<stat.boundary<<' '<<stat.occupied<<' '<<stat.metropolis;
        for(int j=0;j<z;++j)output<<' '<<t.springs[j].site;
        for(int j=0;j<operations;++j)output<<' '<<t.outcomes[j];
        for(int j=0;j<count;++j){auto v=f[i*count+j];output<<' '<<v.x<<' '<<v.y<<' '<<v.z<<' '<<v.w;}
        output<<'\n';
      }
    }
    output.close();return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
