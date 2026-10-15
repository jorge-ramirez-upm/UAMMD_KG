#include "../rouse.cuh"
#include <thrust/device_vector.h>
#include <thrust/sequence.h>
#include <array>
#include <cmath>
#include <iostream>
#include <vector>

using namespace rouse;
void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
__global__ void forces(const real4* p, real4* f, int n, int m) {
  const int i=blockIdx.x*blockDim.x+threadIdx.x;
  if(i<n) f[i]=make_real4(force(p,i,m),0);
}
__global__ void noises(real4* p, const Counter* ids, int n, Counter step) {
  const int i=blockIdx.x*blockDim.x+threadIdx.x;
  if(i<n) p[i]=make_real4(gaussian(918273645,ids[i],step),0);
}
std::vector<real4> copy(const thrust::device_vector<real4>& p) {
  std::vector<real4> result(p.size());
  check(cudaMemcpy(result.data(),thrust::raw_pointer_cast(p.data()),result.size()*sizeof(real4),cudaMemcpyDeviceToHost),"test readback");
  return result;
}
bool equal(real4 a,real4 b) { return a.x==b.x && a.y==b.y && a.z==b.z && a.w==b.w; }
void deterministic() {
  for(int m:{2,3,9}) for(int kind=0;kind<3;++kind) {
    constexpr int chains=3;
    const int n=m*chains;
    std::vector<real4> input(n);
    for(int c=0;c<chains;++c) for(int j=0;j<m;++j) {
      const int i=c*m+j;
      input[i]=kind==0 ? make_real4(real(c*16),real(-c*8),real(3),0)
              : kind==1 ? make_real4(real(j+c*16),real(2*j),real(-j),0)
              : make_real4(real((j*j+3*c)%7),real((3*j+c)%5),real(j%3),0);
    }
    // Independent CPU oracle accumulates equal/opposite bond forces.
    std::vector<std::array<double,3>> reference(n);
    for(int c=0;c<chains;++c) for(int j=0;j<m-1;++j) {
      const int i=c*m+j;
      const double q[3]={double(input[i+1].x)-input[i].x,double(input[i+1].y)-input[i].y,double(input[i+1].z)-input[i].z};
      for(int a=0;a<3;++a) { reference[i][a]+=3*q[a]; reference[i+1][a]-=3*q[a]; }
    }
    thrust::device_vector<real4> p(input),next(n),f(n);
    thrust::device_vector<Counter> ids(n);
    thrust::sequence(ids.begin(),ids.end(),Counter(0));
    forces<<<(n+63)/64,64>>>(thrust::raw_pointer_cast(p.data()),thrust::raw_pointer_cast(f.data()),n,m);
    update<<<(n+63)/64,64>>>(thrust::raw_pointer_cast(p.data()),thrust::raw_pointer_cast(next.data()),thrust::raw_pointer_cast(ids.data()),n,m,real(.01),7,0,false);
    check(cudaGetLastError(),"deterministic launch");
    auto actual=copy(f), moved=copy(next);
    for(int c=0;c<chains;++c) {
      double net[3]{};
      for(int j=0;j<m;++j) {
        const int i=c*m+j;
        const double forceValue[3]={double(actual[i].x),double(actual[i].y),double(actual[i].z)};
        const double old[3]={double(input[i].x),double(input[i].y),double(input[i].z)};
        const double value[3]={double(moved[i].x),double(moved[i].y),double(moved[i].z)};
        for(int a=0;a<3;++a) {
          require(forceValue[a]==reference[i][a],"GPU force != CPU bond oracle");
          net[a]+=forceValue[a];
          const double expected=old[a]+double(real(.01))*reference[i][a];
          const double tol=sizeof(real)==4 ? 3e-6 : 1e-13;
          require(std::abs(value[a]-expected)<tol*(1+std::abs(expected)),"GPU deterministic update != CPU reference");
        }
      }
      for(double x:net) require(x==0,"nonzero internal force sum");
    }
    // Translating just the middle chain must affect neither forces nor other updates.
    for(int j=m;j<2*m;++j) { input[j].x+=1024; input[j].y-=1024; }
    p=input;
    forces<<<(n+63)/64,64>>>(thrust::raw_pointer_cast(p.data()),thrust::raw_pointer_cast(f.data()),n,m);
    auto translated=copy(f);
    for(int i=0;i<n;++i) require(equal(actual[i],translated[i]),"translation/interchain-force error");
  }
}
void observationTests() {
  constexpr int m=5, chains=2;
  std::vector<real4> input(m*chains);
  std::vector<double> phi(m);
  for(int j=0;j<m;++j) phi[j]=std::sqrt(2./m)*std::cos(std::acos(-1.)*(j+.5)/m);
  for(int c=0;c<chains;++c) for(int j=0;j<m;++j)
    input[c*m+j]=make_real4(real(8192+c*16+j),real(-4096+j*j),real(j%2),0);
  thrust::device_vector<real4> p(input);
  thrust::device_vector<double> dphi(phi);
  thrust::device_vector<Observation> output(chains);
  observe<<<1,32>>>(thrust::raw_pointer_cast(p.data()),thrust::raw_pointer_cast(output.data()),
                    thrust::raw_pointer_cast(dphi.data()),chains,m);
  Observation actual[chains];
  check(cudaMemcpy(actual,thrust::raw_pointer_cast(output.data()),sizeof(actual),cudaMemcpyDeviceToHost),"observe oracle readback");
  for(int c=0;c<chains;++c) {
    double center[3]{},q2=0,rg2=0,ree2=0,mode[3]{};
    for(int j=0;j<m;++j) {
      const auto r=input[c*m+j];
      const double v[3]={double(r.x),double(r.y),double(r.z)};
      for(int a=0;a<3;++a) { center[a]+=v[a]/m; mode[a]+=phi[j]*v[a]; }
      if(j) {
        const auto prev=input[c*m+j-1];
        q2+=(std::pow(v[0]-prev.x,2)+std::pow(v[1]-prev.y,2)+std::pow(v[2]-prev.z,2))/(m-1);
      }
    }
    for(int j=0;j<m;++j) {
      const auto r=input[c*m+j];
      rg2+=(std::pow(double(r.x)-center[0],2)+std::pow(double(r.y)-center[1],2)+std::pow(double(r.z)-center[2],2))/m;
    }
    const auto first=input[c*m],last=input[c*m+m-1];
    const double end[3]={double(last.x)-first.x,double(last.y)-first.y,double(last.z)-first.z};
    for(int a=0;a<3;++a) {
      ree2+=end[a]*end[a];
      require(std::abs(actual[c].cm[a]-center[a])<1e-10,"CM observation mismatch");
      require(std::abs(actual[c].ee[a]-end[a])<1e-10,"end vector mismatch");
      require(std::abs(actual[c].mode[a]-mode[a])<1e-10,"cosine mode observation mismatch");
    }
    require(std::abs(actual[c].q2-q2)<1e-10,"bond observation mismatch");
    require(std::abs(actual[c].ree2-ree2)<1e-10,"end dimension mismatch");
    require(std::abs(actual[c].rg2-rg2)<1e-10,"gyration observation mismatch");
  }
}
void stressTests() {
  const int index[3][3]={{0,3,4},{3,1,5},{4,5,2}};
  for (int m:{2,5,9}) for (int kind=0;kind<5;++kind) {
    constexpr int chains=4;
    std::vector<real4> input(m*chains);
    std::vector<double> weights(m,0);
    thrust::device_vector<double> phi(weights);
    thrust::device_vector<Observation> observations(chains);
    std::vector<Observation> first;
    for (int translation:{0,1048576}) {
      for (int c=0;c<chains;++c) for (int j=0;j<m;++j) {
        const real base=translation+c*64;
        input[c*m+j]=kind<3 ? make_real4(base+(kind==0 ? j : 0),-base+(kind==1 ? j : 0),base+(kind==2 ? j : 0),0)
          : kind==3 ? make_real4(base+j*(c+1),-base+(j*j+2*c)%11,base+(3*j+c)%7,0)
                    : make_real4(base,-base,base,0);
      }
      thrust::device_vector<real4> positions(input);
      observe<<<1,32>>>(thrust::raw_pointer_cast(positions.data()),thrust::raw_pointer_cast(observations.data()),
                        thrust::raw_pointer_cast(phi.data()),chains,m);
      std::vector<Observation> actual(chains);
      check(cudaMemcpy(actual.data(),thrust::raw_pointer_cast(observations.data()),sizeof(Observation)*chains,cudaMemcpyDeviceToHost),"stress readback");
      for (int c=0;c<chains;++c) {
        double cpu[3][3]{};
        for (int j=0;j<m-1;++j) {
          const auto a=input[c*m+j],b=input[c*m+j+1];
          const double q[3]={double(b.x)-a.x,double(b.y)-a.y,double(b.z)-a.z};
          for (int row=0;row<3;++row) for (int col=0;col<3;++col) cpu[row][col]+=3*q[row]*q[col];
        }
        for (int row=0;row<3;++row) for (int col=0;col<3;++col) {
          const double gpu=actual[c].stress[index[row][col]];
          require(cpu[row][col]==cpu[col][row],"CPU tensor symmetry");
          require(std::abs(gpu-cpu[row][col])<1e-11*(1+std::abs(cpu[row][col])),"GPU stress != CPU outer product");
          if (translation) require(gpu==first[c].stress[index[row][col]],"stress changed under large translation");
        }
      }
      if (!translation) first=actual;
    }
  }
  std::cout << "PASS: six stress components, symmetric tensor, N=1,4,8, coordinate axes, arbitrary 3D, multiple chains, zero bonds, large translations\n";
}
void randomTests() {
  constexpr int n=131072;
  thrust::device_vector<Counter> ids(n);
  thrust::sequence(ids.begin(),ids.end(),Counter(0));
  thrust::device_vector<real4> noise(n);
  auto generate=[&](Counter step) {
    noises<<<(n+255)/256,256>>>(thrust::raw_pointer_cast(noise.data()),thrust::raw_pointer_cast(ids.data()),n,step);
    check(cudaGetLastError(),"noise launch");
    return copy(noise);
  };
  const auto a=generate(0), b=generate(1), repeat=generate(0);
  double sum[3]{},squares[3]{},fourths[3]{},cross[3]{},temporal[3]{},adjacent[3]{};
  for(int i=0;i<n;++i) {
    require(equal(a[i],repeat[i]),"seed replay failed");
    const double x[3]={double(a[i].x),double(a[i].y),double(a[i].z)};
    const double y[3]={double(b[i].x),double(b[i].y),double(b[i].z)};
    const double z[3]={double(a[(i+1)%n].x),double(a[(i+1)%n].y),double(a[(i+1)%n].z)};
    for(int k=0;k<3;++k) {
      sum[k]+=x[k]; squares[k]+=x[k]*x[k]; fourths[k]+=std::pow(x[k],4);
      cross[k]+=x[k]*x[(k+1)%3]; temporal[k]+=x[k]*y[k]; adjacent[k]+=x[k]*z[k];
    }
  }
  for(int k=0;k<3;++k) {
    require(std::abs(sum[k]/n)<6/std::sqrt(double(n)),"Gaussian mean outside 6 SE");
    require(std::abs(squares[k]/n-1)<6*std::sqrt(2./n),"Gaussian variance outside 6 SE");
    require(std::abs(fourths[k]/n-3)<6*std::sqrt(96./n),"Gaussian fourth moment outside 6 SE");
    for(double v:{cross[k],temporal[k],adjacent[k]})
      require(std::abs(v/n)<6/std::sqrt(double(n)),"Gaussian component/step/bead covariance outside 6 SE");
    std::cout << "Gaussian component " << k << ": mean=" << sum[k]/n << " variance=" << squares[k]/n << '\n';
  }
  const auto high=generate(Counter(1)<<40), end=generate(maxSteps-1);
  require(!equal(a[0],high[0]) && !equal(high[0],end[0]),"high counter aliases low counter");
  std::vector<Counter> reverse(n);
  for(int i=0;i<n;++i) reverse[i]=n-1-i;
  ids=reverse;
  const auto reversed=generate(0);
  for(int i=0;i<n;++i) require(equal(reversed[i],a[n-1-i]),"RNG depends on storage index");
}
int main() {
  try {
    deterministic(); observationTests(); stressTests(); randomTests();
    check(cudaDeviceSynchronize(),"test sync");
    std::cout << "PASS: free-end forces N=1,2,8; CPU update; per-chain force conservation; translation/chain isolation; RNG replay, moments, covariances, IDs and 64-bit counters\n";
  } catch(const std::exception& e) { std::cerr << "FAIL: " << e.what() << '\n'; return 1; }
}
