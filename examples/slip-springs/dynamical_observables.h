#pragma once
#include "orientation_correlator.h"
#include <utility>

// CPU only. KG owns all displacement/coarsening arithmetic; no simulator hooks.
namespace dynamics {
using Vector=orientation::Vector;
using Counter=orientation::Counter;
using Parameters=orientation::Parameters;
using Clock=orientation::Clock;
inline constexpr std::array<int,5> bead_indices{{0,8,16,24,32}};
enum Quantity { CM, Bead0, Bead8, Bead16, Bead24, Bead32,
                Ends, Quarters, EndDifference, QuarterDifference, C1, C2, Quantities };
inline constexpr std::array<const char*,Quantities> quantity_names{{
  "cm_msd","bead0_msd","bead8_msd","bead16_msd","bead24_msd","bead32_msd",
  "end_msd","quarter_msd","end_msd_difference","quarter_msd_difference","c1","c2"}};

class OwnedDiffusion final : private DiffusionCorrelator {
  template<class T> struct Pool {
    std::vector<std::unique_ptr<T[]>> allocations;
    T* make(std::size_t n) {
      allocations.push_back(std::make_unique<T[]>(n));
      return allocations.back().get();
    }
    void release() noexcept {for(auto& a:allocations)a.release();}
  };
  Counter frames_=0;
public:
  explicit OwnedDiffusion(Parameters cfg) {
    cfg.validate();
    Pool<double> values; Pool<double*> tables;
    Pool<unsigned long> counts; Pool<unsigned long*> countTables;
    Pool<unsigned int> cursors;
    p=cfg.slots;m=cfg.coarsening;dmin=p/m;length=cfg.levels*p;
    for(auto table:{&shift,&shift2,&shift3,&correlation}) {
      *table=tables.make(cfg.levels);
      for(unsigned k=0;k<cfg.levels;++k)(*table)[k]=values.make(p);
    }
    ncorrelation=countTables.make(cfg.levels);
    for(unsigned k=0;k<cfg.levels;++k)ncorrelation[k]=counts.make(p);
    for(auto a:{&accumulator,&accumulator2,&accumulator3})*a=values.make(cfg.levels);
    for(auto a:{&t,&f,&tav,&fav})*a=values.make(length);
    n=counts.make(length);
    naccumulator=cursors.make(cfg.levels);insertindex=cursors.make(cfg.levels);
    values.release();tables.release();counts.release();countTables.release();cursors.release();
    // Until publication, all stock base destructors see zero levels.
    numcorrelators=cfg.levels;
    VectorCorrelator::initialize();
  }
  ~OwnedDiffusion() {
    for(auto table:{shift,shift2,shift3,correlation})
      for(unsigned k=0;k<numcorrelators;++k)delete[] table[k];
    for(unsigned k=0;k<numcorrelators;++k)delete[] ncorrelation[k];
  }
  OwnedDiffusion(const OwnedDiffusion&)=delete;
  OwnedDiffusion& operator=(const OwnedDiffusion&)=delete;
  OwnedDiffusion(OwnedDiffusion&&)=delete;
  OwnedDiffusion& operator=(OwnedDiffusion&&)=delete;
  static void validate(const Vector& v) {
    // Bound the entire unsigned-long lifetime sum, not just one squared pair.
    const double limit=std::sqrt(std::numeric_limits<double>::max()/64/
                                double(std::numeric_limits<unsigned long>::max()));
    for(double x:v)if(!std::isfinite(x)||std::abs(x)>limit)
      throw std::invalid_argument("unrepresentable displacement accumulation");
    if(v[0]<=-1e10)throw std::invalid_argument("displacement input overlaps KG sentinel");
  }
  void push(const Vector& v) {
    validate(v);
    if(frames_==std::numeric_limits<Counter>::max() ||
       frames_==std::numeric_limits<unsigned long>::max())
      throw std::overflow_error("displacement count overflow");
    DiffusionCorrelator::add(v[0],v[1],v[2]);
    ++frames_;
  }
  void clear(){VectorCorrelator::clear();frames_=0;}
  using Correlator::evaluate;
  unsigned size()const{return npcorr;}
  double lag(unsigned i)const{return t[i];}
  double value(unsigned i)const{return f[i];}
  unsigned long origins(unsigned i)const{return n[i];}
};

struct Observation {
  Counter chain_id=0;
  std::array<Vector,6> positions{}; // CM, bead 0,8,16,24,32; unwrapped.
};
struct Support {
  Counter lag_samples,lag_steps,origins_per_chain,decimation_samples,diffusion_phase_samples;
  double lag_time,orientation_block_duration;
};
inline bool same_support(const Support& a,const Support& b) {
  return a.lag_samples==b.lag_samples && a.lag_steps==b.lag_steps &&
    a.origins_per_chain==b.origins_per_chain && a.decimation_samples==b.decimation_samples &&
    a.diffusion_phase_samples==b.diffusion_phase_samples && a.lag_time==b.lag_time &&
    a.orientation_block_duration==b.orientation_block_duration;
}
inline constexpr const char* diffusion_semantics=
  "direct displacement; last-position decimation; point width=1; origin stride=b; phase=b-1";
inline constexpr const char* orientation_semantics=
  "unit/features formed at fine frames then averaged in blocks b; no block renormalization; triangular lag support";
struct Bin {Support support;std::array<double,Quantities> values{};};
struct ChainResult {Counter chain_id;std::vector<Bin> bins;};
struct Metadata {
  Counter replica_id;
  Parameters parameters;
  Clock clock;
  std::size_t chains;
  Counter frames;
  std::optional<Counter> last_step;
};
struct Result {Metadata metadata;std::vector<ChainResult> chains;std::vector<Bin> mean;};

class Replica {
  struct Chain {
    std::array<std::unique_ptr<OwnedDiffusion>,6> msd;
    orientation::Bank orientation;
    std::array<Vector,6> offset{};
    std::vector<Vector> end_to_end=std::vector<Vector>(1);
    Chain(Parameters cfg,Clock clock):orientation(1,cfg,clock,true) {
      for(auto& owner:msd)owner=std::make_unique<OwnedDiffusion>(cfg);
    }
  };
  Counter id_,frames_=0;
  Parameters cfg_;
  Clock clock_;
  std::vector<Counter> ids_;
  std::vector<std::unique_ptr<Chain>> chains_;
  std::vector<std::array<Vector,6>> shifted_;
  static Counter multiply(Counter a,Counter b) {
    if(b && a>std::numeric_limits<Counter>::max()/b)throw std::overflow_error("dynamics clock overflow");
    return a*b;
  }
  Counter step(Counter frame)const {
    const Counter offset=multiply(frame,clock_.stride);
    if(offset>std::numeric_limits<Counter>::max()-clock_.first_step)
      throw std::overflow_error("dynamics clock overflow");
    return clock_.first_step+offset;
  }
public:
  static std::size_t estimated_bytes(std::size_t chains,Parameters cfg) {
    cfg.validate();
    const auto per=sizeof(Chain)+sizeof(std::unique_ptr<Chain>)+sizeof(std::array<Vector,6>)+
      sizeof(Counter)+sizeof(Vector)+6*(sizeof(OwnedDiffusion)+orientation::OwnedVector::payload_bytes(cfg))+
      orientation::Bank::estimated_bytes(1,cfg,true);
    if(chains>(std::numeric_limits<std::size_t>::max()-sizeof(Replica))/per)
      throw std::overflow_error("dynamics allocation estimate overflow");
    return sizeof(Replica)+chains*per;
  }
  Replica(Counter replica_id,std::vector<Counter> chain_ids,Parameters cfg,Clock clock,
          std::size_t budget=std::size_t(1)<<30):id_(replica_id),cfg_(cfg),clock_(clock),ids_(std::move(chain_ids)) {
    cfg.validate();
    if(ids_.empty())throw std::invalid_argument("dynamics needs chains");
    auto sorted=ids_;std::sort(sorted.begin(),sorted.end());
    if(std::adjacent_find(sorted.begin(),sorted.end())!=sorted.end())
      throw std::invalid_argument("duplicate chain identity");
    if(!clock.stride || !(clock.dt>0 && std::isfinite(clock.dt)))
      throw std::invalid_argument("invalid dynamics clock");
    Counter maximum=cfg.slots-1;
    for(unsigned k=1;k<cfg.levels;++k)maximum=multiply(maximum,cfg.coarsening);
    if(!std::isfinite(double(multiply(maximum,clock.stride))*clock.dt) ||
       !std::isfinite(double(clock.first_step)*clock.dt) || !(double(clock.stride)*clock.dt>0))
      throw std::invalid_argument("dynamics time outside double range");
    if(estimated_bytes(ids_.size(),cfg)>budget)throw std::length_error("dynamics exceeds allocation budget");
    shifted_.resize(ids_.size());chains_.reserve(ids_.size());
    for(std::size_t c=0;c<ids_.size();++c)chains_.push_back(std::make_unique<Chain>(cfg,clock));
  }
  Replica(const Replica&)=delete;
  Replica& operator=(const Replica&)=delete;
  Replica(Replica&&)=delete;
  Replica& operator=(Replica&&)=delete;
  Counter frames()const{return frames_;}
  void observe(Counter actual_step,const std::vector<Observation>& observations) {
    if(actual_step!=step(frames_) || !std::isfinite(double(actual_step)*clock_.dt))
      throw std::invalid_argument("missing/duplicate/out-of-order dynamics step");
    if(observations.size()!=chains_.size())throw std::invalid_argument("dynamics chain count mismatch");
    if(frames_==std::numeric_limits<Counter>::max() || frames_==std::numeric_limits<unsigned long>::max())
      throw std::overflow_error("dynamics frame overflow");
    // No allocation or correlator mutation until every chain has passed validation.
    for(std::size_t c=0;c<chains_.size();++c) {
      const auto& input=observations[c];auto& chain=*chains_[c];
      if(input.chain_id!=ids_[c])throw std::invalid_argument("changed/reordered chain identity");
      for(unsigned q=0;q<6;++q) {
        for(unsigned d=0;d<3;++d) {
          const double x=input.positions[q][d];
          if(!std::isfinite(x))throw std::invalid_argument("nonfinite dynamics position");
          shifted_[c][q][d]=x-(frames_?chain.offset[q][d]:x);
        }
        OwnedDiffusion::validate(shifted_[c][q]);
      }
      for(unsigned d=0;d<3;++d)
        chain.end_to_end[0][d]=input.positions[5][d]-input.positions[1][d];
      orientation::unit(chain.end_to_end[0]);
    }
    for(std::size_t c=0;c<chains_.size();++c) {
      auto& chain=*chains_[c];chain.orientation.observe(actual_step,chain.end_to_end);
      for(unsigned q=0;q<6;++q)chain.msd[q]->push(shifted_[c][q]);
      if(!frames_)chain.offset=observations[c].positions;
    }
    ++frames_;
  }
  Result evaluate() {
    Result out{{id_,cfg_,clock_,chains_.size(),frames_,frames_?std::optional<Counter>(step(frames_-1)):std::nullopt},{},{}};
    for(std::size_t c=0;c<chains_.size();++c) {
      auto& chain=*chains_[c];auto angles=chain.orientation.evaluate();
      for(auto& owner:chain.msd) {
        owner->evaluate();
        if(owner->size()!=angles.bins.size())throw std::logic_error("dynamics lag grids differ");
      }
      ChainResult result{ids_[c],{}};result.bins.reserve(angles.bins.size());
      for(unsigned i=0;i<angles.bins.size();++i) {
        const auto& a=angles.bins[i];
        Bin bin{{a.lag_samples,a.lag_steps,a.origins_per_chain,a.block_samples,a.block_samples-1,
                 a.lag_time,a.block_duration},{}};
        for(unsigned q=0;q<6;++q) {
          const auto& owner=*chain.msd[q];
          if(owner.lag(i)!=double(a.lag_samples)||owner.origins(i)!=a.origins_per_chain)
            throw std::logic_error("dynamics lag/count mismatch");
          bin.values[q]=owner.value(i);
        }
        bin.values[Ends]=(bin.values[Bead0]+bin.values[Bead32])/2;
        bin.values[Quarters]=(bin.values[Bead8]+bin.values[Bead24])/2;
        bin.values[EndDifference]=bin.values[Bead0]-bin.values[Bead32];
        bin.values[QuarterDifference]=bin.values[Bead8]-bin.values[Bead24];
        bin.values[C1]=a.c1.mean;bin.values[C2]=a.c2->mean;
        for(double value:bin.values)if(!std::isfinite(value))throw std::runtime_error("nonfinite dynamics result");
        if(c==0)out.mean.push_back(bin);
        else {
          if(!same_support(out.mean[i].support,bin.support))throw std::logic_error("chain supports differ");
          for(unsigned q=0;q<Quantities;++q)out.mean[i].values[q]+=(bin.values[q]-out.mean[i].values[q])/double(c+1);
        }
        result.bins.push_back(bin);
      }
      out.chains.push_back(std::move(result));
    }
    return out;
  }
};

struct Estimate {double mean=0;std::optional<double> standard_error;};
struct EnsembleBin {Support support;std::array<Estimate,Quantities> values{};};
struct Ensemble {
  Metadata acquisition; // Same acquisition settings; replica IDs below supersede its single ID.
  std::vector<Counter> replica_ids;
  std::vector<EnsembleBin> bins;
};
inline Ensemble summarize(const std::vector<Result>& replicas) {
  if(replicas.empty())throw std::invalid_argument("no independent replicas");
  Ensemble out{replicas.front().metadata,{},{}};
  const auto& ref=replicas.front();
  for(std::size_t r=0;r<replicas.size();++r) {
    const auto& sample=replicas[r];const auto& meta=sample.metadata;const auto& m=ref.metadata;
    if(std::find(out.replica_ids.begin(),out.replica_ids.end(),meta.replica_id)!=out.replica_ids.end())
      throw std::invalid_argument("duplicate replica identity");
    if(meta.parameters.levels!=m.parameters.levels || meta.parameters.slots!=m.parameters.slots ||
       meta.parameters.coarsening!=m.parameters.coarsening || meta.clock.first_step!=m.clock.first_step ||
       meta.clock.stride!=m.clock.stride || meta.clock.dt!=m.clock.dt || meta.chains!=m.chains ||
       meta.frames!=m.frames || meta.last_step!=m.last_step || sample.mean.size()!=ref.mean.size())
      throw std::invalid_argument("incompatible replica acquisition");
    out.replica_ids.push_back(meta.replica_id);
    for(std::size_t i=0;i<sample.mean.size();++i) {
      const auto& bin=sample.mean[i];
      if(!same_support(bin.support,ref.mean[i].support))throw std::invalid_argument("replica supports differ");
      if(r==0)out.bins.push_back({bin.support,{}});
      for(unsigned q=0;q<Quantities;++q) {
        auto& e=out.bins[i].values[q];const double x=bin.values[q];
        if(!std::isfinite(x))throw std::invalid_argument("nonfinite replica estimate");
        const double delta=x-e.mean;e.mean+=delta/double(r+1);
        e.standard_error=e.standard_error.value_or(0)+delta*(x-e.mean);
      }
    }
  }
  for(auto& bin:out.bins)for(auto& e:bin.values) {
    if(replicas.size()==1)e.standard_error.reset();
    else {
      if(!std::isfinite(*e.standard_error))throw std::overflow_error("replica moment overflow");
      e.standard_error=std::sqrt(std::max(0.,*e.standard_error)/double(replicas.size()-1)/double(replicas.size()));
      if(!std::isfinite(e.mean)||!std::isfinite(*e.standard_error))throw std::overflow_error("replica moment overflow");
    }
  }
  return out;
}
} // namespace dynamics
