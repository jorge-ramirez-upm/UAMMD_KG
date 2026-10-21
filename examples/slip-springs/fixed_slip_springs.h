#pragma once
// CPU-only E1 initialization, shared with bounded tests (no CUDA runtime needed).
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <vector>

namespace fixed_slips {
template<class Real> Real stiffness(double kbt, double ms2) {
  // Wider intermediates avoid overflow/underflow before the final precision cast.
  const long double k=3.L*kbt/ms2;
  if(!(kbt>0 && std::isfinite(kbt) && ms2>0 &&
       Real(ms2)>0 && std::isfinite(Real(ms2)) &&
       Real(k)>0 && std::isfinite(Real(k))))
    throw std::runtime_error("active slips require representable positive slip-ms2 and stiffness");
  return Real(k);
}

template<class Position>
std::vector<Position> initialize(const std::vector<Position>& positions,
                                std::uint64_t count, double ms2, std::uint64_t seed) {
  using Real=decltype(Position{}.x);
  if(count>positions.size() || positions.size()>size_t(std::numeric_limits<int>::max()))
    throw std::runtime_error("slip-count exceeds number of bead sites");
  if(!count) return {}; // No allocation, RNG construction or parameter use when disabled.
  if(!(ms2>0 && Real(ms2)>0 && std::isfinite(Real(ms2))))
    throw std::runtime_error("active slips require representable positive slip-ms2");
  std::vector<Position> anchors(positions.size(),Position{});
  std::vector<int> sites(positions.size());
  std::iota(sites.begin(),sites.end(),0);
  std::seed_seq domain{unsigned(seed),unsigned(seed>>32),0x53117u};
  std::mt19937_64 rng(domain);
  std::shuffle(sites.begin(),sites.end(),rng);
  std::normal_distribution<double> standard(0.0,1.0);
  const double stddev=std::sqrt(ms2)/std::sqrt(3.0);
  for(std::uint64_t j=0;j<count;++j) {
    const int i=sites[j];
    const double x=double(positions[i].x)+stddev*standard(rng);
    const double y=double(positions[i].y)+stddev*standard(rng);
    const double z=double(positions[i].z)+stddev*standard(rng);
    if(!(std::isfinite(Real(x)) && std::isfinite(Real(y)) && std::isfinite(Real(z))))
      throw std::runtime_error("slip anchor coordinate not representable");
    anchors[i]=Position{Real(x),Real(y),Real(z),Real(1)};
  }
  return anchors;
}
} // namespace fixed_slips
