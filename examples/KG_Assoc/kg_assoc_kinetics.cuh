#ifndef EXAMPLES_KG_ASSOC_KINETICS_CUH
#define EXAMPLES_KG_ASSOC_KINETICS_CUH

#include "kg_assoc_state.cuh"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace kg_assoc {
struct Candidate { int first, second; double r; };
struct Event { long long step; char type; int first, second; };
struct KineticParameters { double nu0, ea, temperature, dt; int every; unsigned long long seed; };
inline double fene(double r, double k, double r0) {
  if (!(r >= 0.0 && r < r0)) throw std::runtime_error("associating FENE requires 0 <= r < R0");
  return -0.5 * k * r0 * r0 * std::log1p(-r * r / (r0 * r0));
}
inline double kgDerivative(double r, double k, double r0) {
  return -48.0/std::pow(r,13) + 24.0/std::pow(r,7) + k*r/(1.0-r*r/(r0*r0));
}
inline double rstar(double k, double r0) {
  double lo=0.5, hi=std::pow(2.0, 1.0/6.0);
  for(int n=0;n<100;++n) { double m=.5*(lo+hi); if(kgDerivative(m,k,r0)<0) lo=m; else hi=m; }
  return .5*(lo+hi);
}
inline double deltaU(double r, double k, double r0, double ee) { return fene(r,k,r0)-fene(rstar(k,r0),k,r0)-ee; }
inline double attemptProbability(double rateDt) { return -std::expm1(-rateDt); }
inline double metropolisFactor(double du, double t, bool creation) {
  return creation ? (du <= 0.0 ? 1.0 : std::exp(-du/t)) : (du >= 0.0 ? 1.0 : std::exp(du/t));
}
inline std::uint64_t ahash(std::uint64_t x) { x+=UINT64_C(0x9e3779b97f4a7c15); x=(x^(x>>30))*UINT64_C(0xbf58476d1ce4e5b9); x=(x^(x>>27))*UINT64_C(0x94d049bb133111eb); return x^(x>>31); }
inline std::uint64_t randomValue(std::uint64_t seed, long long step, int first, int second, std::uint64_t stream) {
  // Exact stateless LAMMPS hash/stream convention, with UAMMD particle ids.
  std::uint64_t key=seed^std::uint64_t(step)^(std::uint64_t(first)<<1)^(std::uint64_t(second)<<17);
  return ahash(key^stream);
}
inline double uniform53(std::uint64_t bits) { return double(bits >> 11) * 0x1.0p-53; }
class Kinetics {
 public:
  Kinetics(KineticParameters p, double k, double r0, double ee) : p_(p), k_(k), r0_(r0), ee_(ee) {}
  bool update(long long step, StickerState& state, std::vector<Candidate> edges, std::vector<Event>& events) {
    constexpr std::uint64_t order=UINT64_C(0x4f52444552), accept=UINT64_C(0x414343455054);
    std::sort(edges.begin(),edges.end(),[&](const Candidate&a,const Candidate&b){ auto pa=randomValue(p_.seed,step,a.first,a.second,order),pb=randomValue(p_.seed,step,b.first,b.second,order); return pa!=pb ? pa<pb : (a.first!=b.first ? a.first<b.first : a.second<b.second); });
    const double q=attemptProbability(p_.nu0*std::exp(-p_.ea/p_.temperature)*p_.every*p_.dt);
    bool changed=false;
    for(const auto& e:edges) {
      if (e.first >= e.second || !state.isSticker(e.first) || !state.isSticker(e.second) || !(e.r >= 0.0 && e.r < r0_))
        throw std::runtime_error("invalid associating candidate edge");
      // Re-read current state after each earlier ordered transition, as LAMMPS does.
      const bool make=state.partner(e.first)==-1 && state.partner(e.second)==-1;
      const bool cut=state.bonded(e.first,e.second);
      if(!make && !cut) continue;
      const double p=q*metropolisFactor(deltaU(e.r,k_,r0_,ee_),p_.temperature,make);
      if(uniform53(randomValue(p_.seed,step,e.first,e.second,accept)) >= p) continue;
      if(make) state.make(e.first,e.second); else state.breakPair(e.first,e.second);
      events.push_back({step,make?'C':'B',e.first,e.second}); changed=true;
    }
    if(changed) state.syncDevice();
    state.validate();
    return changed;
  }
  double q() const { return attemptProbability(p_.nu0*std::exp(-p_.ea/p_.temperature)*p_.every*p_.dt); }
 private: KineticParameters p_; double k_,r0_,ee_;
};
}  // namespace kg_assoc
#endif
