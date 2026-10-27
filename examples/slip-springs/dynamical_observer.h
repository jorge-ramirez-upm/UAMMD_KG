#pragma once
#include "dynamical_observables.h"
#include <chrono>
#include <filesystem>
#include <numeric>

// Host-only, synchronous acquisition/export glue. No writable device-state API.
namespace dynamical_observer {
using Counter=dynamics::Counter;
namespace fs=std::filesystem;
struct Settings {
  bool enabled=false;
  Counter stride=100;
  dynamics::Parameters correlation{8,16,2};
  unsigned memory_mib=256;
  std::string output="dynamics"; // One new child directory of --output.
  std::optional<Counter> replica_id; // Defaults to seed, not proof of independence.
  std::size_t estimated_bytes(std::size_t chains)const {
    const auto base=dynamics::Replica::estimated_bytes(chains,correlation);
    const auto limit=std::numeric_limits<std::size_t>::max();
    if(chains>(limit-65536)/(sizeof(dynamics::Observation)+2*sizeof(Counter)))
      throw std::overflow_error("dynamics observer memory overflow");
    const auto scratch=chains*(sizeof(dynamics::Observation)+2*sizeof(Counter))+65536;
    // Conservative allowance for evaluation curves, transient pools and scratch.
    if(base>(limit-scratch)/4)throw std::overflow_error("dynamics observer memory overflow");
    return 4*base+scratch;
  }
  void validate(int bonds,std::size_t chains,Counter steps,double dt,bool force_only=false)const {
    if(!enabled)return;
    if(bonds!=32||!chains||force_only)throw std::invalid_argument("dynamics requires N32 and dynamical chains");
    correlation.validate();
    if(!stride||!(dt>0&&std::isfinite(dt))||!std::isfinite(double(steps)*dt))
      throw std::invalid_argument("invalid dynamics clock");
    if(steps/stride>=std::numeric_limits<unsigned long>::max())
      throw std::overflow_error("dynamics observation count overflow");
    Counter lag=correlation.slots-1;
    for(unsigned k=1;k<correlation.levels;++k)lag*=correlation.coarsening; // cfg caps at 2^53.
    if(lag>std::numeric_limits<Counter>::max()/stride ||
       !std::isfinite(double(lag*stride)*dt) || !(double(stride)*dt>0))
      throw std::overflow_error("dynamics lag clock overflow");
    if(!memory_mib||memory_mib>1024)throw std::invalid_argument("dynamics-mib must be 1..1024");
    if(estimated_bytes(chains)>std::size_t(memory_mib)*1024*1024)
      throw std::length_error("dynamics observer exceeds requested memory budget");
    if(output.empty()||!std::all_of(output.begin(),output.end(),[](unsigned char c){
      return (c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-';}))
      throw std::invalid_argument("dynamics-output must be one alphanumeric/underscore/hyphen directory name");
  }
};

// Read only x/y/z; all 33 beads contribute to CM.
template<class Position> void acquire(const std::vector<Position>& positions,
                                     std::vector<dynamics::Observation>& frame) {
  if(frame.empty()||frame.size()>std::numeric_limits<std::size_t>::max()/33||positions.size()!=frame.size()*33)
    throw std::invalid_argument("dynamics coordinate dimensions mismatch");
  for(std::size_t c=0;c<frame.size();++c) {
    auto& sample=frame[c];sample.chain_id=c;
    const auto& first=positions[c*33];
    const dynamics::Vector origin{{double(first.x),double(first.y),double(first.z)}};
    dynamics::Vector offset{};
    for(unsigned i=0;i<33;++i) {
      const auto& r=positions[c*33+i];
      const dynamics::Vector v{{double(r.x),double(r.y),double(r.z)}};
      for(unsigned d=0;d<3;++d) {
        if(!std::isfinite(v[d]))throw std::invalid_argument("nonfinite acquired position");
        offset[d]+=(v[d]-origin[d])/33;
      }
    }
    for(unsigned d=0;d<3;++d) {
      sample.positions[0][d]=origin[d]+offset[d];
      if(!std::isfinite(sample.positions[0][d]))throw std::invalid_argument("unrepresentable acquired CM");
    }
    for(unsigned j=0;j<5;++j) {
      const auto& r=positions[c*33+dynamics::bead_indices[j]];
      sample.positions[j+1]={{double(r.x),double(r.y),double(r.z)}};
    }
  }
}

struct Model {
  std::size_t chains=0;
  Counter steps=0,seed=0,slip_count=0;
  double dt=0,kbt=0,zeta=0,slip_ms2=0,hop_rate=0,spring_k=0,mobility_step=0,noise=0;
  unsigned precision_bits=0;
  bool renewal_requested=false,renewal_active=false,supplied_initial=false;
  std::vector<double> b0,kb,kappa; // Actual stored coefficients, not just CLI defaults.
  void validate()const {
    if(b0.size()!=32||kb.size()!=32||kappa.size()!=33||!(kbt>0&&zeta>0)||
       (precision_bits!=32&&precision_bits!=64)||slip_count>chains*33)
      throw std::invalid_argument("invalid dynamics model metadata");
    for(double x:{dt,kbt,zeta,slip_ms2,hop_rate,spring_k,mobility_step,noise})
      if(!std::isfinite(x))throw std::invalid_argument("nonfinite dynamics model metadata");
    for(double x:b0)if(!(x>=0&&std::isfinite(x)))throw std::invalid_argument("invalid dynamics b0");
    for(double x:kb)if(!(x>0&&std::isfinite(x)))throw std::invalid_argument("invalid dynamics kb");
    for(double x:kappa)if(!(x>=0&&std::isfinite(x)))throw std::invalid_argument("invalid dynamics kappa");
  }
};

class Observer {
  using Clock=std::chrono::steady_clock;
  static double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
  Settings settings_;
  Model model_;
  fs::path directory_;
  std::unique_ptr<dynamics::Replica> bank_;
  std::vector<dynamics::Observation> frame_;
  std::ofstream chains_,replica_,metadata_;
  Counter shared_frames_=0,extra_frames_=0,shared_bytes_=0,extra_bytes_=0;
  double shared_readback_seconds_=0,extra_readback_seconds_=0,cpu_seconds_=0;
  bool finished_=false;
  static std::ofstream open(const fs::path& path) {
    std::ofstream f;f.exceptions(std::ios::badbit|std::ios::failbit);f.open(path);
    f<<std::setprecision(17);return f;
  }
  static void header(std::ostream& out) {
    out<<"replica,chain,lag_samples,lag_steps,lag_time,origins_per_chain,decimation_samples,diffusion_phase_samples,orientation_block_samples,orientation_block_duration";
    for(auto name:dynamics::quantity_names)out<<','<<name;
    out<<'\n';
  }
  void row(std::ostream& out,std::optional<Counter> chain,const dynamics::Bin& b)const {
    const auto& s=b.support;out<<settings_.replica_id.value_or(model_.seed)<<',';
    if(chain)out<<*chain;
    out<<','<<s.lag_samples<<','<<s.lag_steps<<','<<s.lag_time<<','<<s.origins_per_chain
       <<','<<s.decimation_samples<<','<<s.diffusion_phase_samples<<','<<s.decimation_samples<<','<<s.orientation_block_duration;
    for(double value:b.values)out<<','<<value;
    out<<'\n';
  }
  static void array(std::ostream& out,const char* key,const std::vector<double>& values) {
    out<<",\""<<key<<"\":[";
    for(std::size_t i=0;i<values.size();++i){if(i)out<<',';out<<values[i];}out<<']';
  }
public:
  Observer(Settings settings,Model model,const fs::path& run_output):settings_(std::move(settings)),model_(std::move(model)) {
    if(!settings_.enabled)throw std::invalid_argument("cannot construct disabled dynamics observer");
    settings_.validate(32,model_.chains,model_.steps,model_.dt);model_.validate();
    std::vector<Counter> ids(model_.chains);std::iota(ids.begin(),ids.end(),Counter(0));
    bank_=std::make_unique<dynamics::Replica>(settings_.replica_id.value_or(model_.seed),ids,
      settings_.correlation,dynamics::Clock{0,settings_.stride,model_.dt},std::size_t(settings_.memory_mib)*1024*1024);
    frame_.resize(model_.chains);
    directory_=run_output/settings_.output;
    if(!fs::create_directory(directory_))throw std::runtime_error("refusing to overwrite dynamics directory");
    chains_=open(directory_/"chain_correlations.csv");replica_=open(directory_/"replica_correlations.csv");
    metadata_=open(directory_/"metadata.pending.json");header(chains_);header(replica_);
    chains_.flush();replica_.flush();
  }
  Observer(const Observer&)=delete;
  Observer& operator=(const Observer&)=delete;
  bool due(Counter step)const{return step<=model_.steps&&step%settings_.stride==0;}
  template<class Position> void observe(Counter step,const std::vector<Position>& positions,
                                       bool shared,double readback_seconds,std::size_t readback_bytes) {
    if(finished_||!due(step)||!(readback_seconds>=0&&std::isfinite(readback_seconds)))
      throw std::invalid_argument("invalid dynamics acquisition");
    auto& bytes=shared?shared_bytes_:extra_bytes_;
    if(readback_bytes>std::numeric_limits<Counter>::max()-bytes)throw std::overflow_error("dynamics transfer count overflow");
    const auto start=Clock::now();acquire(positions,frame_);bank_->observe(step,frame_);
    cpu_seconds_+=elapsed(start);
    if(shared){++shared_frames_;shared_readback_seconds_+=readback_seconds;}
    else {++extra_frames_;extra_readback_seconds_+=readback_seconds;}
    bytes+=readback_bytes;
  }
  void finish() {
    if(finished_)throw std::logic_error("dynamics export already completed");
    if(bank_->frames()!=model_.steps/settings_.stride+1)throw std::runtime_error("incomplete dynamics acquisition");
    const auto start=Clock::now();const auto result=bank_->evaluate();
    for(const auto& chain:result.chains)for(const auto& bin:chain.bins)row(chains_,chain.chain_id,bin);
    for(const auto& bin:result.mean)row(replica_,std::nullopt,bin);
    chains_.close();replica_.close();const double evaluation_csv_seconds=elapsed(start);
    auto& f=metadata_;
    auto number=[&](const char* key,auto value){f<<",\""<<key<<"\":"<<value;};
    // Strings below are fixed literals/adapter constants, never unescaped CLI paths.
    auto text=[&](const char* key,const char* value){f<<",\""<<key<<"\":\""<<value<<'"';};
    f<<"{\"version\":1,\"complete\":true";
    number("replica",result.metadata.replica_id);number("chains",model_.chains);
    number("N",32);number("beads_per_chain",33);f<<",\"selected_beads\":[0,8,16,24,32]";
    number("first_step",0);number("stride",settings_.stride);number("dt",model_.dt);
    number("integration_steps",model_.steps);number("frames",result.metadata.frames);number("last_step",*result.metadata.last_step);
    text("initial_phase","initialized state before first BD update, after initial force/state validation");
    text("phase","after BD, coordinate-buffer swap and entire hopping/end-renewal batch");
    text("coordinates","unwrapped Cartesian; immutable flat chain-contiguous IDs");
    text("diffusion_semantics",dynamics::diffusion_semantics);text("orientation_semantics",dynamics::orientation_semantics);
    number("diffusion_point_width_samples",1);text("orientation_lag_half_width","(block_samples-1)*stride*dt");
    number("deepest_populated_level_omitted","true");number("incomplete_blocks_promoted","false");
    number("independent_replicas",1);number("standard_error","null");
    text("uncertainty_unit","independent replicas after chain averaging");
    number("correlator_levels",settings_.correlation.levels);number("correlator_slots",settings_.correlation.slots);
    number("correlator_m",settings_.correlation.coarsening);number("memory_budget_bytes",std::size_t(settings_.memory_mib)*1024*1024);
    number("conservative_observer_estimate_bytes",settings_.estimated_bytes(model_.chains));
    number("shared_frames",shared_frames_);number("extra_readbacks",extra_frames_);
    number("shared_readback_bytes",shared_bytes_);number("extra_readback_bytes",extra_bytes_);
    number("shared_readback_seconds",shared_readback_seconds_);number("extra_readback_seconds",extra_readback_seconds_);
    number("acquisition_cpu_seconds",cpu_seconds_);number("evaluation_csv_seconds",evaluation_csv_seconds);
    text("timer_scope","shared readback and consumption overlap existing observation accounting; extra readback/consumption are in production wall; CSV evaluation excludes metadata publication");
    number("seed",model_.seed);number("precision_bits",model_.precision_bits);number("kbt",model_.kbt);number("zeta",model_.zeta);
    number("effective_mobility_step",model_.mobility_step);number("effective_noise",model_.noise);
    number("slip_count",model_.slip_count);
    if(model_.slip_count)number("slip_ms2",model_.slip_ms2);else number("slip_ms2","null");
    number("slip_effective_stiffness",model_.spring_k);number("hop_rate",model_.hop_rate);
    number("end_renewal_requested",model_.renewal_requested?"true":"false");
    number("end_renewal_active",model_.renewal_active?"true":"false");
    text("initialization",model_.supplied_initial?"supplied-coordinates":"CPU-direct-equilibrium");
    array(f,"b0",model_.b0);array(f,"kb",model_.kb);array(f,"kappa",model_.kappa);
    f<<"}\n";f.close();fs::rename(directory_/"metadata.pending.json",directory_/"metadata.json");finished_=true;
  }
};
} // namespace dynamical_observer
