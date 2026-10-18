#pragma once
#include "stream_correlator.h"
#include <algorithm>
#include <optional>
#include <string>

// CPU only. KG supplies all add/evaluate/coarsening arithmetic unchanged.
namespace orientation {
using Vector = std::array<double,3>;
using Counter = std::uint64_t;
using Parameters = streaming::Parameters;

class OwnedVector final : private VectorCorrelator {
  template<class T> struct Pool {
    std::vector<std::unique_ptr<T[]>> allocations;
    T* make(std::size_t n) {
      allocations.push_back(std::make_unique<T[]>(n));
      return allocations.back().get();
    }
    void release() noexcept { for(auto& a:allocations) a.release(); }
  };
public:
  explicit OwnedVector(Parameters cfg) {
    cfg.validate();
    Pool<double> values; Pool<double*> tables;
    Pool<unsigned long> counts; Pool<unsigned long*> countTables;
    Pool<unsigned int> cursors;
    p=cfg.slots; m=cfg.coarsening; dmin=p/m; length=cfg.levels*p;
    double*** rows[]={&shift,&shift2,&shift3,&correlation};
    for(auto table:rows) {
      *table=tables.make(cfg.levels);
      for(unsigned k=0;k<cfg.levels;++k) (*table)[k]=values.make(p);
    }
    ncorrelation=countTables.make(cfg.levels);
    for(unsigned k=0;k<cfg.levels;++k) ncorrelation[k]=counts.make(p);
    for(auto a:{&accumulator,&accumulator2,&accumulator3}) *a=values.make(cfg.levels);
    for(auto a:{&t,&f,&tav,&fav}) *a=values.make(length);
    n=counts.make(length);
    naccumulator=cursors.make(cfg.levels); insertindex=cursors.make(cfg.levels);
    values.release(); tables.release(); counts.release(); countTables.release(); cursors.release();
    // Base destructors see zero levels until all allocations have succeeded.
    numcorrelators=cfg.levels;
    VectorCorrelator::initialize();
  }
  ~OwnedVector() {
    for(auto table:{shift,shift2,shift3,correlation})
      for(unsigned k=0;k<numcorrelators;++k) delete[] table[k];
    for(unsigned k=0;k<numcorrelators;++k) delete[] ncorrelation[k];
    // Stock destructors own tables, accumulators, cursors and output arrays.
  }
  OwnedVector(const OwnedVector&)=delete;
  OwnedVector& operator=(const OwnedVector&)=delete;
  OwnedVector(OwnedVector&&)=delete;
  OwnedVector& operator=(OwnedVector&&)=delete;
  void push(const Vector& v) {
    for(double x:v) if(!std::isfinite(x)) throw std::invalid_argument("nonfinite Vector input");
    if(v[0]<=-1e10) throw std::invalid_argument("Vector input overlaps KG sentinel");
    VectorCorrelator::add(v[0],v[1],v[2]);
  }
  using VectorCorrelator::clear;
  using Correlator::evaluate;
  unsigned size() const { return npcorr; }
  double lag(unsigned i) const { return t[i]; }
  double value(unsigned i) const { return f[i]; }
  unsigned long origins(unsigned i) const { return n[i]; }
  static std::size_t payload_bytes(Parameters cfg) {
    cfg.validate();
    return std::size_t(cfg.levels)*(cfg.slots*(8*sizeof(double)+2*sizeof(unsigned long))+
                                  5*sizeof(void*)+3*sizeof(double)+2*sizeof(unsigned int));
  }
};

inline Vector unit(const Vector& r) {
  for(double x:r) if(!std::isfinite(x)) throw std::invalid_argument("nonfinite end-to-end vector");
  double scale=std::max({std::abs(r[0]),std::abs(r[1]),std::abs(r[2])});
  if(scale==0) throw std::invalid_argument("zero end-to-end vector");
  Vector u{{r[0]/scale,r[1]/scale,r[2]/scale}};
  double length=std::sqrt(u[0]*u[0]+u[1]*u[1]+u[2]*u[2]);
  for(double& x:u) x/=length;
  return u;
}
inline std::array<double,5> rank2(const Vector& u) {
  const double root=std::sqrt(3.);
  return {{root*u[0]*u[1],root*u[0]*u[2],root*u[1]*u[2],
           root/2*(u[0]*u[0]-u[1]*u[1]),(3*u[2]*u[2]-1)/2}};
}

struct Clock {
  Counter first_step, stride;
  double dt;
};
struct Estimate {
  double mean=0;
  std::optional<double> standard_error; // Unavailable for one independent chain.
};
struct Bin {
  Counter lag_samples,lag_steps,block_samples,origins_per_chain;
  double lag_time,block_duration;
  std::size_t independent_chains;
  Estimate c1;
  std::optional<Estimate> c2;
};
struct Metadata {
  Parameters parameters;
  Clock clock;
  std::size_t independent_chains;
  bool second_rank;
  Counter frames;
  std::optional<Counter> last_step;
};
struct Result { Metadata metadata; std::vector<Bin> bins; };

class Bank {
  struct Chain {
    OwnedVector c1;
    std::unique_ptr<OwnedVector> a,b;
    Chain(Parameters cfg,bool second):c1(cfg) {
      if(second) { a=std::make_unique<OwnedVector>(cfg); b=std::make_unique<OwnedVector>(cfg); }
    }
  };
  Parameters cfg_;
  Clock clock_;
  bool second_;
  Counter frames_=0;
  std::vector<std::unique_ptr<Chain>> chains_;
  std::vector<Vector> normalized_;
  static Counter multiply(Counter a,Counter b) {
    if(b && a>std::numeric_limits<Counter>::max()/b) throw std::overflow_error("orientation clock overflow");
    return a*b;
  }
  Counter step(Counter frame) const {
    Counter offset=multiply(frame,clock_.stride);
    if(offset>std::numeric_limits<Counter>::max()-clock_.first_step) throw std::overflow_error("orientation clock overflow");
    return clock_.first_step+offset;
  }
public:
  static std::size_t estimated_bytes(std::size_t chains,Parameters cfg,bool second=true) {
    const std::size_t payload=OwnedVector::payload_bytes(cfg);
    const std::size_t per=sizeof(std::unique_ptr<Chain>)+sizeof(Chain)+sizeof(Vector)+payload+
                          (second?2*(sizeof(OwnedVector)+payload):0);
    if(chains>(std::numeric_limits<std::size_t>::max()-sizeof(Bank))/per)
      throw std::overflow_error("orientation allocation estimate overflow");
    return sizeof(Bank)+chains*per; // Excludes malloc overhead, temporary pools and returned results.
  }
  Bank(std::size_t chains,Parameters cfg,Clock clock,bool second=true,
       std::size_t budget=std::size_t(1)<<30):cfg_(cfg),clock_(clock),second_(second) {
    cfg.validate();
    if(!chains) throw std::invalid_argument("orientation needs at least one chain");
    if(!clock.stride || !(clock.dt>0 && std::isfinite(clock.dt))) throw std::invalid_argument("invalid orientation clock");
    Counter maximum=cfg.slots-1;
    for(unsigned k=1;k<cfg.levels;++k) maximum=multiply(maximum,cfg.coarsening);
    if(!std::isfinite(double(multiply(maximum,clock.stride))*clock.dt) ||
       !std::isfinite(double(clock.first_step)*clock.dt) ||
       !(double(clock.stride)*clock.dt>0)) throw std::invalid_argument("orientation time outside double range");
    if(estimated_bytes(chains,cfg,second)>budget) throw std::length_error("orientation bank exceeds allocation budget");
    normalized_.resize(chains); chains_.reserve(chains);
    for(std::size_t c=0;c<chains;++c) chains_.push_back(std::make_unique<Chain>(cfg,second));
  }
  Bank(const Bank&)=delete;
  Bank& operator=(const Bank&)=delete;
  Bank(Bank&&)=delete;
  Bank& operator=(Bank&&)=delete;
  Counter frames() const { return frames_; }
  void observe(Counter actual_step,const std::vector<Vector>& vectors) {
    if(actual_step!=step(frames_)) throw std::invalid_argument("missing/duplicate/out-of-order orientation step");
    if(vectors.size()!=chains_.size()) throw std::invalid_argument("orientation chain count mismatch");
    if(frames_==std::numeric_limits<Counter>::max() || frames_==std::numeric_limits<unsigned long>::max())
      throw std::overflow_error("orientation origin count overflow");
    // Validate the complete frame before mutating any correlator.
    for(std::size_t c=0;c<vectors.size();++c) {
      try { normalized_[c]=unit(vectors[c]); }
      catch(const std::invalid_argument& e) {
        throw std::invalid_argument("orientation step "+std::to_string(actual_step)+", chain "+std::to_string(c)+": "+e.what());
      }
    }
    for(std::size_t c=0;c<chains_.size();++c) {
      auto& chain=*chains_[c];const auto& u=normalized_[c];chain.c1.push(u);
      if(second_) {
        const auto f=rank2(u);
        chain.a->push({{f[0],f[1],f[2]}}); chain.b->push({{f[3],f[4],0}});
      }
    }
    ++frames_;
  }
  Result evaluate() {
    Result result{{cfg_,clock_,chains_.size(),second_,frames_,frames_?std::optional<Counter>(step(frames_-1)):std::nullopt},{}};
    for(std::size_t c=0;c<chains_.size();++c) {
      auto& chain=*chains_[c];chain.c1.evaluate();
      if(second_) { chain.a->evaluate();chain.b->evaluate(); }
      if(c==0) {
        result.bins.reserve(chain.c1.size());
        for(unsigned i=0;i<chain.c1.size();++i) {
          Counter lag=Counter(chain.c1.lag(i)),block=1;
          while(lag>=Counter(cfg_.slots)*block) block*=cfg_.coarsening;
          Counter lag_steps=multiply(lag,clock_.stride),block_steps=multiply(block,clock_.stride);
          Bin bin{lag,lag_steps,block,chain.c1.origins(i),double(lag_steps)*clock_.dt,
                  double(block_steps)*clock_.dt,chains_.size(),{},std::nullopt};
          if(second_) bin.c2=Estimate{};
          if(bin.origins_per_chain!=frames_/block-lag/block) throw std::logic_error("unexpected KG orientation origins");
          result.bins.push_back(bin);
        }
      }
      if(chain.c1.size()!=result.bins.size()) throw std::logic_error("orientation chain grids differ");
      if(second_ && (chain.a->size()!=chain.c1.size() || chain.b->size()!=chain.c1.size()))
        throw std::logic_error("orientation feature bank grids differ");
      for(unsigned i=0;i<chain.c1.size();++i) {
        auto& bin=result.bins[i];
        for(const auto* corr:{&chain.c1,chain.a.get(),chain.b.get()}) if(corr) {
          if(corr->lag(i)!=double(bin.lag_samples) || corr->origins(i)!=bin.origins_per_chain)
            throw std::logic_error("orientation lag/origin mismatch");
        }
        auto add=[&](Estimate& estimate,double value) {
          if(!std::isfinite(value)) throw std::runtime_error("nonfinite orientation correlation");
          double delta=value-estimate.mean;estimate.mean+=delta/double(c+1);
          estimate.standard_error=estimate.standard_error.value_or(0)+delta*(value-estimate.mean);
        };
        add(bin.c1,chain.c1.value(i));
        if(second_) add(*bin.c2,chain.a->value(i)+chain.b->value(i));
      }
    }
    for(auto& bin:result.bins) {
      for(auto* estimate:{&bin.c1,bin.c2?&*bin.c2:nullptr}) if(estimate) {
        if(chains_.size()==1) estimate->standard_error.reset();
        else estimate->standard_error=std::sqrt(std::max(0.,*estimate->standard_error)/double(chains_.size()-1)/double(chains_.size()));
      }
    }
    return result;
  }
};
} // namespace orientation
