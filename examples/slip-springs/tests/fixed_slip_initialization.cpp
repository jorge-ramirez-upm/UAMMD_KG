#include "../fixed_slip_springs.h"
#include <array>
#include <cassert>
#include <iostream>

template<class Real> struct Position { Real x,y,z,w; };
template<class F> void rejects(F f) {
  bool failed=false;
  try {f();} catch(const std::runtime_error&) {failed=true;}
  assert(failed);
}
template<class Real> void test() {
  using P=Position<Real>;
  std::vector<P> r{{1,2,3,0},{2,3,4,0},{3,4,5,0},{4,5,6,0}};
  const auto original=r;
  assert(fixed_slips::initialize(r,0,0,1).empty());
  assert(fixed_slips::stiffness<Real>(2,3)==Real(2));
  for(double ms2:{0.,-1.,std::numeric_limits<double>::infinity(),
                  std::numeric_limits<double>::denorm_min()})
    rejects([&]{fixed_slips::stiffness<Real>(1,ms2);});
  rejects([&]{fixed_slips::stiffness<Real>(std::numeric_limits<double>::max(),1);});
  rejects([&]{fixed_slips::stiffness<Real>(0,1);});
  rejects([&]{fixed_slips::stiffness<Real>(1e-300,1e30);});
  auto invalid=r; invalid[0].x=std::numeric_limits<Real>::infinity();
  rejects([&]{fixed_slips::initialize(invalid,4,3,1);});
  rejects([&]{fixed_slips::initialize(r,5,3,1);});
  // Finite ratio despite overflowing the old 3*kBT intermediate (double).
  if(sizeof(Real)==8) assert(fixed_slips::stiffness<Real>(1e308,1e308)==Real(3));
  const auto a=fixed_slips::initialize(r,2,3,123);
  const auto replay=fixed_slips::initialize(r,2,3,123);
  const auto changed=fixed_slips::initialize(r,2,3,(1ULL<<32)+123);
  bool different=false;
  for(size_t i=0;i<r.size();++i) {
    assert(a[i].x==replay[i].x && a[i].y==replay[i].y && a[i].z==replay[i].z && a[i].w==replay[i].w);
    different|=a[i].x!=changed[i].x || a[i].w!=changed[i].w;
    assert(r[i].x==original[i].x && r[i].y==original[i].y && r[i].z==original[i].z);
  }
  assert(different);
  for(auto p:fixed_slips::initialize(r,4,3,1)) assert(p.w==1);
  // All six unordered occupied pairs must be uniform. The count on the first
  // two sites has probabilities (1/6,4/6,1/6), the hypergeometric law.
  constexpr int trials=6000;
  std::array<int,16> subsets{}; std::array<int,3> populations{};
  double sum[3]{},square[3]{},cross=0;
  for(int seed=0;seed<trials;++seed) {
    auto anchors=fixed_slips::initialize(r,2,3,seed);
    int mask=0,n=0;
    for(int i=0;i<4;++i) if(anchors[i].w) {
      mask|=1<<i; ++n;
      double d[3]={double(anchors[i].x)-r[i].x,double(anchors[i].y)-r[i].y,double(anchors[i].z)-r[i].z};
      for(int k=0;k<3;++k){sum[k]+=d[k];square[k]+=d[k]*d[k];}
      cross+=d[0]*d[1];
    }
    assert(n==2); ++subsets[mask]; ++populations[bool(mask&1)+bool(mask&2)];
  }
  for(int mask:{3,5,6,9,10,12}) assert(std::abs(subsets[mask]-trials/6.)<6*std::sqrt(trials*5./36));
  assert(std::abs(populations[1]-trials*2./3)<6*std::sqrt(trials*2./9));
  for(int k=0;k<3;++k) {
    assert(std::abs(sum[k]/(2*trials))<6/std::sqrt(2.*trials));
    assert(std::abs(square[k]/(2*trials)-1)<6*std::sqrt(2./(2*trials)));
  }
  assert(std::abs(cross/(2*trials))<6/std::sqrt(2.*trials));
}
int main() {test<float>();test<double>();std::cout<<"fixed-slip CPU initialization: float/double passed\n";}
