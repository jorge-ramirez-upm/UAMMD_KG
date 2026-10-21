#pragma once
#include <cmath>
#include <cstdint>
#include <stdexcept>
namespace slip_hopping {
// Resource limits abort unsupported runs; neither the rate nor drawn K is clipped.
constexpr unsigned maxEvents=100000;
constexpr double maxMean=10000;
inline double poissonMean(std::uint64_t count,double rate,double dt) {
  if(!(std::isfinite(rate)&&rate>=0)) throw std::runtime_error("hop-rate must be finite and nonnegative");
  if(!count||rate==0) return 0;
  const long double mean=static_cast<long double>(count)*rate*dt;
  if(!(mean>0 && std::isfinite(mean) && double(mean)>0 && mean<=maxMean))
    throw std::runtime_error("hopping Poisson mean unrepresentable or exceeds event budget");
  return double(mean);
}
}
