// Frozen anchors: differentiation must not regenerate anchors with moved beads.
#include "../semiflexible_slipspring.cuh"
#include <thrust/device_vector.h>
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
using namespace semiflexible;
int main() {
  thrust::device_vector<real4> r(2),f(2),a(2);
  thrust::device_vector<int> error(1,INT_MAX);
  auto ptr=[](auto& v){return thrust::raw_pointer_cast(v.data());};
  a[0]=make_real4(.2,-.4,.7,1); a[1]=make_real4(0,0,0,0);
  const real k=real(2.5);
  auto evaluate=[&](real3 position) {
    r[0]=make_real4(position,0);r[1]=make_real4(3,2,1,0);
    f[0]=make_real4(1,2,3,4);f[1]=make_real4(5,6,7,8);
    error[0]=INT_MAX;
    fixed_slip_force<<<1,32>>>(ptr(r),ptr(f),ptr(a),2,k,ptr(error));
    check(cudaGetLastError(),"fixed slip launch");
    check(cudaDeviceSynchronize(),"fixed slip sync");
    assert(int(error[0])==INT_MAX);
    real4 inactive=f[1]; assert(inactive.x==5 && inactive.y==6 && inactive.z==7 && inactive.w==8);
    return real4(f[0]);
  };
  real3 position=make_real3(1.1,.3,-.5);
  auto value=evaluate(position);
  const double h=sizeof(real)==4 ? .002 : 1e-5;
  const double tolerance=sizeof(real)==4 ? .002 : 2e-9;
  const double anchor[3]={.2,-.4,.7},xyz[3]={position.x,position.y,position.z};
  const double force[3]={value.x-1,value.y-2,value.z-3};
  double expectedEnergy=4;
  for(int d=0;d<3;++d) {
    expectedEnergy+=.5*k*(xyz[d]-anchor[d])*(xyz[d]-anchor[d]);
    auto plus=position,minus=position;
    if(d==0){plus.x+=h;minus.x-=h;}
    if(d==1){plus.y+=h;minus.y-=h;}
    if(d==2){plus.z+=h;minus.z-=h;}
    double gradient=(evaluate(plus).w-evaluate(minus).w)/(2*h);
    assert(std::abs(force[d]+gradient)<tolerance);
    assert(std::abs(force[d]+k*(xyz[d]-anchor[d]))<tolerance);
  }
  assert(std::abs(value.w-expectedEnergy)<tolerance);
  // Large extension and small stiffness: |d|^2 overflows float, U and F do not.
  r[0]=make_real4(real(1e20),0,0,0);a[0]=make_real4(0,0,0,1);f[0]=make_real4(0,0,0,0);
  error[0]=INT_MAX;
  fixed_slip_force<<<1,32>>>(ptr(r),ptr(f),ptr(a),1,real(1e-20),ptr(error));
  check(cudaDeviceSynchronize(),"scaled energy");
  assert(int(error[0])==INT_MAX);value=f[0];
  assert(std::abs(double(value.w)/5e19-1)<1e-6);
  assert(std::abs(double(value.x)+1)<1e-6);
  // Nonfinite force/energy must set the existing deterministic error key.
  fixed_slip_force<<<1,32>>>(ptr(r),ptr(f),ptr(a),1,std::numeric_limits<real>::max(),ptr(error));
  check(cudaDeviceSynchronize(),"nonfinite diagnostic");
  assert(int(error[0])==4);
  std::cout<<"fixed-slip GPU force/energy/finite differences passed\n";
}
