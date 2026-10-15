#pragma once
#include "../KG/correlator.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>

namespace streaming {
struct Sample { double v[6]; }; // xy,xz,yz,xx-yy,xx-zz,yy-zz; RAW differences
struct Parameters {
  unsigned levels=16, slots=16, coarsening=2;
  void validate() const {
    if (!levels || levels>48 || slots<2 || slots>65536 || coarsening<2 ||
        coarsening>slots || slots%coarsening)
      throw std::runtime_error("multi-tau requires 1<=levels<=48, 2<=slots<=65536, 2<=m<=slots, slots divisible by m");
    long double lag=slots-1;
    for (unsigned k=1;k<levels;++k) lag*=coarsening;
    if (lag>9007199254740992.L) throw std::runtime_error("multi-tau lags exceed exact double integer range");
  }
};
// Staged allocation also repairs KG setsize's partial-allocation exception hazard.
// Only allocation/ownership changes here; add/initialize/evaluate remain KG code.
class OwnedCorrelator6 final : private Correlator6 {
  template<class T> struct Pool {
    std::vector<std::unique_ptr<T[]>> allocations;
    T* make(std::size_t n) {
      allocations.push_back(std::make_unique<T[]>(n));
      return allocations.back().get();
    }
    void release() { for (auto& x:allocations) x.release(); }
  };
public:
  explicit OwnedCorrelator6(Parameters cfg) {
    cfg.validate();
    Pool<double> values; Pool<double*> tables;
    Pool<unsigned long> counts; Pool<unsigned long*> countTables;
    Pool<unsigned int> cursors;
    p=cfg.slots; m=cfg.coarsening; dmin=p/m; length=cfg.levels*p;
    double*** rows[]={&shift,&shift2,&shift3,&shift4,&shift5,&shift6,
                     &correlation,&correlation2,&correlation3,&correlation4,&correlation5,&correlation6};
    for (auto table:rows) {
      *table=tables.make(cfg.levels);
      for (unsigned k=0;k<cfg.levels;++k) (*table)[k]=values.make(p);
    }
    ncorrelation=countTables.make(cfg.levels);
    for (unsigned k=0;k<cfg.levels;++k) ncorrelation[k]=counts.make(p);
    double** acc[]={&accumulator,&accumulator2,&accumulator3,&accumulator4,&accumulator5,&accumulator6};
    for (auto a:acc) *a=values.make(cfg.levels);
    double** outputs[]={&t,&f,&tav,&fav,&f2,&f3,&f4,&f5,&f6};
    for (auto a:outputs) *a=values.make(length);
    n=counts.make(length);
    naccumulator=cursors.make(cfg.levels); insertindex=cursors.make(cfg.levels);
    values.release(); tables.release(); counts.release(); countTables.release(); cursors.release();
    numcorrelators=cfg.levels; // Publish only after every allocation succeeded.
    Correlator6::initialize();
  }
  ~OwnedCorrelator6() {
    double** rows[]={shift,shift2,shift3,shift4,shift5,shift6,
                    correlation,correlation2,correlation3,correlation4,correlation5,correlation6};
    for (auto table:rows) for (unsigned k=0;k<numcorrelators;++k) delete[] table[k];
    for (unsigned k=0;k<numcorrelators;++k) delete[] ncorrelation[k];
    // Base destructors own tables, accumulators, cursors and flattened outputs.
  }
  OwnedCorrelator6(const OwnedCorrelator6&)=delete;
  OwnedCorrelator6& operator=(const OwnedCorrelator6&)=delete;
  OwnedCorrelator6(OwnedCorrelator6&&)=delete;
  OwnedCorrelator6& operator=(OwnedCorrelator6&&)=delete;
  using Correlator6::evaluate;
  using Correlator6::getf;
  using Correlator::gett;
  using Correlator::getn;
  unsigned size() const { return npcorr; }
  void push(const Sample& s) {
    for (double x:s.v) if (!std::isfinite(x)) throw std::runtime_error("nonfinite streaming stress");
    if (s.v[0]<=-1e10) throw std::runtime_error("stress overlaps KG unused-sample sentinel");
    Correlator6::add(s.v[0],s.v[1],s.v[2],s.v[3],s.v[4],s.v[5]);
  }
  static std::size_t bytes(Parameters c) {
    // 12 double rows, 9 output arrays, 2 unsigned-long arrays, 13 tables,
    // six accumulators, two cursor arrays; excludes malloc metadata.
    return sizeof(OwnedCorrelator6)+std::size_t(c.levels)*
      (c.slots*(21*sizeof(double)+2*sizeof(unsigned long))+
       12*sizeof(double*)+sizeof(unsigned long*)+6*sizeof(double)+2*sizeof(unsigned));
  }
};
struct Moments {
  double mean=0,m2=0;
  void add(double x,std::size_t n) {
    const double d=x-mean; mean+=d/n; m2+=d*(x-mean);
  }
  double se(std::size_t n) const {
    return n>1 ? std::sqrt(std::max(0.,m2)/(n-1)/n) : std::numeric_limits<double>::quiet_NaN();
  }
};
class Bank {
  Parameters cfg;
  std::vector<std::unique_ptr<OwnedCorrelator6>> chains;
public:
  std::uint64_t frames=0;
  Bank(std::size_t count,Parameters c,std::size_t budget):cfg(c) {
    c.validate();
    if (!count || count>budget/(OwnedCorrelator6::bytes(c)+sizeof(void*)))
      throw std::runtime_error("per-chain correlators exceed --correlator-mib memory budget");
    chains.reserve(count);
    for (std::size_t i=0;i<count;++i) chains.push_back(std::make_unique<OwnedCorrelator6>(c));
  }
  void consume(const Sample* data,std::size_t count) {
    for (std::size_t f=0;f<count;++f) {
      for (std::size_t c=0;c<chains.size();++c) chains[c]->push(data[f*chains.size()+c]);
      ++frames;
    }
  }
  void write(const std::string& path,double spacing) {
    struct Bin { double lag; unsigned long pairs; std::array<Moments,7> moments; };
    std::vector<Bin> bins;
    for (std::size_t c=0;c<chains.size();++c) {
      auto& corr=*chains[c]; corr.evaluate();
      if (!c) { bins.resize(corr.size()); for (unsigned i=0;i<corr.size();++i) {
        bins[i].lag=corr.gett(i); bins[i].pairs=corr.getn(i);
      }}
      if (bins.size()!=corr.size()) throw std::runtime_error("chain lag grids differ");
      for (unsigned i=0;i<corr.size();++i) {
        if (bins[i].pairs!=corr.getn(i) || bins[i].lag!=corr.gett(i))
          throw std::runtime_error("chain counts or lag grids differ");
        double g=0;
        for (int j=0;j<6;++j) {
          const double x=corr.getf(i,j);
          if (!std::isfinite(x)) throw std::runtime_error("nonfinite correlation");
          bins[i].moments[j].add(x,c+1); g+=x*(j<3 ? 1./5 : 1./30);
        }
        bins[i].moments[6].add(g,c+1); // preserves all six-channel covariance
      }
    }
    std::ofstream out; out.exceptions(std::ios::badbit|std::ios::failbit); out.open(path);
    out << "lag_samples,lag_time,block_samples,g,g_se,Cxy,Cxz,Cyz,Cxx_yy,Cxx_zz,Cyy_zz,pairs_per_chain,pairs_total,Cxy_se,Cxz_se,Cyz_se,Cxx_yy_se,Cxx_zz_se,Cyy_zz_se\n" << std::setprecision(17);
    for (auto& b:bins) {
      std::uint64_t block=1;
      while (b.lag>=double(cfg.slots)*block) block*=cfg.coarsening;
      out << b.lag << ',' << b.lag*spacing << ',' << block << ',' << b.moments[6].mean
          << ',' << b.moments[6].se(chains.size());
      for (int j=0;j<6;++j) out << ',' << b.moments[j].mean;
      out << ',' << b.pairs << ',' << b.pairs*chains.size();
      for (int j=0;j<6;++j) out << ',' << b.moments[j].se(chains.size());
      out << '\n';
    }
    out.close();
  }
};
}
