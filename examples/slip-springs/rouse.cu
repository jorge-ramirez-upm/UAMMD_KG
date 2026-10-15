#include "rouse.cuh"
#include "stream_pipeline.cuh"
#include <thrust/device_vector.h>
#include <thrust/sequence.h>
#include <algorithm>
#include <chrono>
#include <climits>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <vector>

namespace fs = std::filesystem;
using rouse::Counter;
using uammd::real;
using uammd::real4;

struct Options {
  int springs=8, chains=512;
  bool stream=false, asynchronous=false, backendSpecified=false;
  std::size_t batch=64, correlatorMiB=512;
  streaming::Parameters corr;
  double dt=0.005;
  Counter steps=1000, seed=12345, sample=100, equil=0;
  fs::path output=fs::path(SLIP_SPRINGS_DIR)/"build/run";
};
Counter integer(const std::string& s) {
  if (s.empty() || s.find_first_not_of("0123456789") != std::string::npos)
    throw std::runtime_error("expected unsigned integer: "+s);
  std::size_t end;
  const auto n=std::stoull(s,&end);
  if (end!=s.size()) throw std::runtime_error("invalid integer");
  return n;
}
Options parse(int argc, char** argv) {
  Options o;
  for (int i=1;i<argc;++i) {
    const std::string key=argv[i];
    if (key=="--help") {
      std::cout << "rouse [--springs N] [--chains C] [--dt H] [--steps S] "
                   "[--seed K] [--sample STRIDE] [--equil S] [--output NEW_DIRECTORY]\n"
                   "[--output-mode csv|stream] [--backend sync|async] [--batch FRAMES]\n"
                   "[--corr-levels L] [--corr-slots P] [--corr-m M] [--correlator-mib MiB]\n";
      std::exit(0);
    }
    if (++i==argc) throw std::runtime_error("missing value for "+key);
    const std::string value=argv[i];
    if (key=="--output-mode") {
      if (value!="csv" && value!="stream") throw std::runtime_error("output-mode must be csv or stream");
      o.stream=value=="stream";
    } else if (key=="--backend") {
      if (value!="sync" && value!="async") throw std::runtime_error("backend must be sync or async");
      o.asynchronous=value=="async"; o.backendSpecified=true;
    } else if (key=="--output") o.output=value;
    else if (key=="--dt") {
      std::size_t end;
      o.dt=std::stod(value,&end);
      if (end!=value.size()) throw std::runtime_error("invalid dt");
    } else {
      const Counter n=integer(value);
      if (key=="--springs" || key=="--chains") {
        if (n==0 || n>=INT_MAX) throw std::runtime_error("N and chains must be positive and < INT_MAX");
        if (key=="--springs") o.springs=int(n); else o.chains=int(n);
      } else if (key=="--steps") o.steps=n;
      else if (key=="--seed") o.seed=n;
      else if (key=="--sample") o.sample=n;
      else if (key=="--equil") o.equil=n;
      else if (key=="--batch" && n>0 && n<=4096) o.batch=n;
      else if (key=="--correlator-mib" && n>0 && n<=65536) o.correlatorMiB=n;
      else if (key=="--corr-levels" && n<=48) o.corr.levels=n;
      else if (key=="--corr-slots" && n<=65536) o.corr.slots=n;
      else if (key=="--corr-m" && n<=65536) o.corr.coarsening=n;
      else throw std::runtime_error("unknown option: "+key);
    }
  }
  if (Counter(o.springs+1)*o.chains>INT_MAX-256) throw std::runtime_error("too many beads for ParticleData");
  if (!std::isfinite(o.dt) || o.dt<=0 || !std::isfinite(real(o.dt)) || real(o.dt)<=0)
    throw std::runtime_error("dt must be finite and positive in the selected precision");
  const double lambda=12*std::pow(std::cos(std::acos(-1.)/(2*(o.springs+1))),2);
  if (double(real(o.dt))*lambda>=2) throw std::runtime_error("dt violates Euler-Maruyama stability bound");
  if (!o.sample || o.equil>rouse::maxSteps || o.steps>rouse::maxSteps-o.equil)
    throw std::runtime_error("sample must be positive; equil+steps must not exceed floor(UINT64_MAX/8)");
  o.corr.validate();
  if (!o.stream && o.backendSpecified) throw std::runtime_error("backend requires --output-mode stream");
  if (o.stream) {
    if ((o.steps/o.sample+1)>std::numeric_limits<unsigned long>::max()/o.chains)
      throw std::runtime_error("stream pair counts would overflow");
    if (o.batch*std::size_t(o.chains)*sizeof(streaming::Sample)*(o.asynchronous?4:2)>512ULL*1024*1024)
      throw std::runtime_error("stress buffers exceed fixed 512 MiB combined device/pinned limit");
    if (streaming::OwnedCorrelator6::bytes(o.corr)+sizeof(void*)>o.correlatorMiB*1024*1024/std::size_t(o.chains))
      throw std::runtime_error("correlators exceed --correlator-mib budget");
  }
  return o;
}

bool within(const fs::path& path, const fs::path& root) {
  const auto relative=path.lexically_relative(root);
  return !relative.empty() && *relative.begin()!="..";
}
fs::path prepareOutput(const fs::path& requested) {
  const auto project=fs::canonical(SLIP_SPRINGS_DIR);
  const auto root=project.parent_path().parent_path();
  const auto path=fs::weakly_canonical(fs::absolute(requested));
  if (within(path,root) && !within(path,project))
    throw std::runtime_error("output inside this repository must be under examples/slip-springs");
  if (fs::exists(path)) throw std::runtime_error("output directory already exists; refusing to overwrite: "+path.string());
  fs::create_directories(path);
  return path;
}
struct Events {
  cudaEvent_t start,stop;
  Events() { rouse::check(cudaEventCreate(&start),"event create"); rouse::check(cudaEventCreate(&stop),"event create"); }
  ~Events() { cudaEventDestroy(start); cudaEventDestroy(stop); }
  void begin() { rouse::check(cudaEventRecord(start),"event record"); }
  double end() {
    rouse::check(cudaEventRecord(stop),"event record");
    rouse::check(cudaEventSynchronize(stop),"event sync");
    float ms;
    rouse::check(cudaEventElapsedTime(&ms,start,stop),"event elapsed");
    return ms/1000.;
  }
};
std::string rate(double value, bool applicable) {
  if (!applicable) return "null";
  std::ostringstream out;
  out << std::setprecision(17) << value;
  return out.str();
}
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point start) { return std::chrono::duration<double>(Clock::now()-start).count(); }

void simulate(const Options& o, const fs::path& output, std::shared_ptr<uammd::System> sys, double contextTime) {
  const auto initializationStart=Clock::now();
  const int m=o.springs+1, count=m*o.chains;
  const real h=real(o.dt);
  int device;
  cudaDeviceProp prop{};
  rouse::check(cudaGetDevice(&device),"get device");
  rouse::check(cudaGetDeviceProperties(&prop,device),"device properties");
  std::cerr << "Rouse: N=" << o.springs << " chains=" << o.chains << " beads=" << count
            << " dt=" << std::setprecision(17) << double(h) << " steps=" << o.steps
            << " equil=" << o.equil << " sample=" << o.sample << " seed=" << o.seed
            << " real_bits=" << 8*sizeof(real) << " GPU=" << prop.name << '\n';
  std::size_t freeBefore,totalMemory,freeAfter;
  rouse::check(cudaMemGetInfo(&freeBefore,&totalMemory),"memory query");
  auto particles=std::make_shared<uammd::ParticleData>(count,sys);
  auto positions=particles->getPos(uammd::access::gpu,uammd::access::write);
  thrust::device_vector<real4> scratch(count);
  // Logical IDs are immutable RNG keys; fixed chain-contiguous topology is never sorted.
  thrust::device_vector<Counter> ids(count);
  thrust::sequence(ids.begin(),ids.end(),Counter(0));
  std::vector<double> weights(m);
  for (int j=0;j<m;++j) weights[j]=std::sqrt(2./m)*std::cos(std::acos(-1.)*(j+0.5)/m);
  thrust::device_vector<double> phi(weights);
  thrust::device_vector<rouse::Observation> deviceObs(o.stream?0:o.chains);
  std::vector<rouse::Observation> hostObs(o.stream?0:o.chains);
  rouse::check(cudaMemGetInfo(&freeAfter,&totalMemory),"memory query");
  real4* current=positions.raw();
  real4* next=thrust::raw_pointer_cast(scratch.data());
  const auto id=thrust::raw_pointer_cast(ids.data());
  rouse::initialize<<<(o.chains+127)/128,128>>>(current,o.chains,m,o.seed);
  rouse::check(cudaGetLastError(),"initialize launch");
  rouse::check(cudaDeviceSynchronize(),"initialize sync");
  std::unique_ptr<streaming::Pipeline> pipeline;
  if (o.stream) pipeline=std::make_unique<streaming::Pipeline>(o.chains,m,o.batch,o.asynchronous,o.corr,o.correlatorMiB*1024*1024);
  std::ofstream samples,ensemble;
  if (!o.stream) {
  samples.open(output/"samples.csv"); ensemble.open(output/"ensemble.csv");
  samples.exceptions(std::ios::badbit|std::ios::failbit);
  ensemble.exceptions(std::ios::badbit|std::ios::failbit);
  samples << "step,time,chain,q2,ree2,rg2,cm_x,cm_y,cm_z,ee_x,ee_y,ee_z,mode1_x,mode1_y,mode1_z,max_abs,zero_bonds,Sxx,Syy,Szz,Sxy,Sxz,Syz\n" << std::setprecision(17);
  ensemble << "step,time,q2,q2_se,ree2,ree2_se,rg2,rg2_se\n" << std::setprecision(17);
  }
  Counter globalStep=0;
  Events events;
  double updateTime=0,samplingTime=0,outputTime=0,maxabs=0,zeros=0;
  auto advance=[&](Counter n) {
    if (!n) return 0.;
    events.begin();
    for (Counter i=0;i<n;++i,++globalStep) {
      rouse::update<<<(count+255)/256,256>>>(current,next,id,count,m,h,o.seed,globalStep);
      std::swap(current,next);
    }
    rouse::check(cudaGetLastError(),"update launch");
    return events.end();
  };
  auto sample=[&](Counter productionStep) {
    auto start=Clock::now();
    rouse::observe<<<(o.chains+127)/128,128>>>(current,thrust::raw_pointer_cast(deviceObs.data()),
                                           thrust::raw_pointer_cast(phi.data()),o.chains,m);
    rouse::check(cudaGetLastError(),"observe launch");
    rouse::check(cudaMemcpy(hostObs.data(),thrust::raw_pointer_cast(deviceObs.data()),
                           sizeof(rouse::Observation)*o.chains,cudaMemcpyDeviceToHost),"observation readback");
    samplingTime+=seconds(start);
    start=Clock::now();
    double sums[3]{},squares[3]{};
    for (int c=0;c<o.chains;++c) {
      const auto& v=hostObs[c];
      const double values[3]={v.q2,v.ree2,v.rg2};
      for (int k=0;k<3;++k) {
        if (!std::isfinite(values[k])) throw std::runtime_error("nonfinite conformation");
        sums[k]+=values[k]; squares[k]+=values[k]*values[k];
      }
      maxabs=std::max(maxabs,v.maxabs); zeros+=v.zeroBonds;
      samples << productionStep << ',' << double(productionStep)*double(h) << ',' << c
              << ',' << v.q2 << ',' << v.ree2 << ',' << v.rg2;
      for (double x:v.cm) samples << ',' << x;
      for (double x:v.ee) samples << ',' << x;
      for (double x:v.mode) samples << ',' << x;
      samples << ',' << v.maxabs << ',' << v.zeroBonds;
      for (double x:v.stress) {
        if (!std::isfinite(x)) throw std::runtime_error("nonfinite stress");
        samples << ',' << x;
      }
      samples << '\n';
    }
    ensemble << productionStep << ',' << double(productionStep)*double(h);
    for (int k=0;k<3;++k) {
      const double mean=sums[k]/o.chains;
      const double se=o.chains>1 ? std::sqrt(std::max(0.,(squares[k]-sums[k]*mean)/(o.chains-1)/o.chains))
                               : std::numeric_limits<double>::quiet_NaN();
      ensemble << ',' << mean << ',' << se;
    }
    ensemble << '\n';
    outputTime+=seconds(start);
  };
  const double initializationTime=contextTime+seconds(initializationStart);
  const auto equilStart=Clock::now();
  const double equilGpu=advance(o.equil);
  const double equilTime=seconds(equilStart);
  const auto start=Clock::now();
  if (pipeline) pipeline->sample(current); else sample(0);
  Counter done=0;
  while (done<o.steps) {
    const Counter n=std::min(o.sample,o.steps-done);
    updateTime+=advance(n); done+=n;
    if (pipeline) { if (done%o.sample==0) pipeline->sample(current); }
    else sample(done);
  }
  if (pipeline) {
    pipeline->finish();
    samplingTime=pipeline->sampling_gpu_seconds+pipeline->transfer_seconds;
  }
  const double elapsed=seconds(start);
  const auto flushStart=Clock::now();
  if (pipeline) pipeline->write((output/"relaxation.csv").string(),double(h)*double(o.sample));
  else { samples.close(); ensemble.close(); }
  const double finalOutputTime=seconds(flushStart);
  const double measuredSimulationTime=contextTime+seconds(initializationStart);
  rouse::check(cudaMemGetInfo(&freeAfter,&totalMemory),"memory query");
  const double updates=double(count)*double(o.steps);
  const double spacing=double(std::nextafter(real(maxabs),std::numeric_limits<real>::infinity())-real(maxabs));
  std::ofstream meta(output/"metadata.json");
  meta.exceptions(std::ios::badbit|std::ios::failbit);
  meta << std::setprecision(17)
       << "{\n\"springs\":" << o.springs << ",\"chains\":" << o.chains << ",\"beads\":" << count
       << ",\"dt_requested\":" << o.dt << ",\"dt\":" << double(h)
       << ",\"steps\":" << o.steps << ",\"equil\":" << o.equil << ",\"sample\":" << o.sample
       << ",\"seed\":" << o.seed << ",\"real_bits\":" << 8*sizeof(real)
       << ",\"gpu\":\"" << prop.name << "\",\"compute_capability\":\"" << prop.major << '.' << prop.minor
       << "\",\"update_seconds\":" << updateTime << ",\"sampling_seconds\":" << samplingTime
       << ",\"output_seconds\":" << outputTime+finalOutputTime << ",\"wall_seconds\":" << elapsed
       << ",\"timing_schema_version\":2,\"beads_per_chain\":" << m
       << ",\"physical_time\":" << double(o.steps)*double(h)
       << ",\"initialization_seconds\":" << initializationTime
       << ",\"context_initialization_seconds\":" << contextTime
       << ",\"equilibration_seconds\":" << equilTime << ",\"equilibration_gpu_seconds\":" << equilGpu
       << ",\"production_seconds\":" << elapsed
       << ",\"recurrent_output_seconds\":" << outputTime
       << ",\"final_output_seconds\":" << finalOutputTime
       << ",\"integration_ns_per_bead_step\":" << rate(o.steps ? 1e9*updateTime/updates : 0, o.steps!=0)
       << ",\"overall_ns_per_bead_step\":" << rate(o.steps ? 1e9*elapsed/updates : 0, o.steps!=0)
       << ",\"gpu_timing_includes_launch_gaps\":true,\"gpu_timing_includes_sampling\":false"
       << ",\"gpu_timing_includes_host_sync_wait\":false,\"sampling_includes_recurrent_transfer\":true"
       << ",\"bead_updates_per_second\":" << rate(o.steps ? updates/updateTime : 0, o.steps!=0)
       << ",\"explicit_device_bytes\":" << 2*sizeof(real4)*std::size_t(count)+sizeof(Counter)*std::size_t(count)+sizeof(double)*m+sizeof(rouse::Observation)*(o.stream?0:o.chains)+(pipeline?o.batch*o.chains*sizeof(streaming::Sample)*(o.asynchronous?2:1):0)
       << ",\"cuda_memory_delta_bytes\":" << freeBefore-freeAfter
       << ",\"max_abs_coordinate\":" << rate(maxabs,!pipeline) << ",\"max_spacing_over_noise\":" << rate(spacing/std::sqrt(2*double(h)),!pipeline)
       << ",\"sampled_zero_bonds\":" << rate(zeros,!pipeline)
       << ",\"coordinate_diagnostics_available\":" << (pipeline?"false":"true")
       << ",\"output_mode\":\"" << (o.stream?"stream":"csv") << "\""
       << ",\"backend\":\"" << (o.asynchronous?"async":"sync") << "\""
       << ",\"stress_frames\":" << (pipeline?pipeline->frames():1+o.steps/o.sample+(o.steps%o.sample!=0))
       << ",\"unsampled_final_steps\":" << (pipeline?o.steps%o.sample:0)
       << ",\"batch_frames\":" << o.batch
       << ",\"corr_levels\":" << o.corr.levels << ",\"corr_slots\":" << o.corr.slots
       << ",\"corr_m\":" << o.corr.coarsening
       << ",\"correlator_estimated_bytes\":" << (pipeline?std::size_t(o.chains)*(streaming::OwnedCorrelator6::bytes(o.corr)+sizeof(void*)):0)
       << ",\"buffer_device_bytes\":" << (pipeline?o.batch*o.chains*sizeof(streaming::Sample)*(o.asynchronous?2:1):0)
       << ",\"buffer_pinned_bytes\":" << (pipeline?o.batch*o.chains*sizeof(streaming::Sample)*(o.asynchronous?2:1):0)
       << ",\"sampling_gpu_seconds\":" << (pipeline?pipeline->sampling_gpu_seconds:0)
       << ",\"sampling_enqueue_seconds\":" << (pipeline?pipeline->enqueue_seconds:0)
       << ",\"transfer_seconds\":" << (pipeline?pipeline->transfer_seconds:0)
       << ",\"transfer_wait_seconds\":" << (pipeline?pipeline->transfer_wait_seconds:0)
       << ",\"buffer_wait_seconds\":" << (pipeline?pipeline->buffer_wait_seconds:0)
       << ",\"cpu_correlation_seconds\":" << (pipeline?pipeline->correlation_seconds:0)
       << ",\"measured_simulation_seconds\":" << measuredSimulationTime
       << ",\"sampling_timer_scope\":\"" << (pipeline?"GPU stress event sum plus D2H event sum; may overlap integration":"blocking observation kernel plus D2H wall time") << "\""
       << ",\"stream_times_overlap\":" << (o.asynchronous?"true":"false")
       << ",\"modulus_normalization\":\"G/(n_ch*kBT)\"\n}\n";
  meta.close();
  if (pipeline) std::cerr << "Streaming: frames=" << pipeline->frames() << " backend=" << (o.asynchronous?"async":"sync")
    << " batch_frames=" << o.batch << " sampling_GPU=" << pipeline->sampling_gpu_seconds
    << " s; D2H=" << pipeline->transfer_seconds << " s; CPU_correlations=" << pipeline->correlation_seconds
    << " s; free_buffer_wait=" << pipeline->buffer_wait_seconds << " s; transfer_wait=" << pipeline->transfer_wait_seconds
    << " s. Overlapping timers must not be summed.\n";
  std::cerr << "Performance: chains=" << o.chains << " springs/chain=" << o.springs
            << " beads/chain=" << m << " total_beads=" << count << " production_steps=" << o.steps
            << " physical_time=" << double(o.steps)*double(h) << " tau_0\n"
            << "  GPU integration=" << updateTime << " s; ns/bead/step="
            << (o.steps ? std::to_string(1e9*updateTime/updates) : "N/A") << "; bead updates/s="
            << (o.steps ? std::to_string(updates/updateTime) : "N/A") << '\n'
            << "  Production loop=" << elapsed << " s; overall ns/bead/step="
            << (o.steps ? std::to_string(1e9*elapsed/updates) : "N/A") << '\n'
            << "  Sampling + recurrent D2H (GPU event sums in stream mode)=" << samplingTime << " s; recurrent CSV=" << outputTime
            << " s; final data evaluation/write=" << finalOutputTime << " s\n"
            << "  Total measured simulation=" << measuredSimulationTime << " s (context through final data output)\n"
            << "  Initialization=" << initializationTime << " s (includes System/CUDA context); equilibration="
            << equilTime << " s (" << o.equil << " steps; GPU " << equilGpu << " s)\n"
            << "  GPU event intervals include launch gaps; exclude sampling and host sync wait.\n"
            << "  Production includes synchronization, sampling/D2H, recurrent CSV or streaming worker drain; excludes initialization,\n"
            << "  equilibration, final data evaluation/write, metadata serialization and terminal logging.\n"
            << "  Results=" << output << '\n';
}
int main(int argc, char** argv) {
  try {
    const auto o=parse(argc,argv);
    const auto output=prepareOutput(o.output);
    const auto contextStart=Clock::now();
    auto sys=std::make_shared<uammd::System>();
    const double contextTime=seconds(contextStart);
    simulate(o,output,sys,contextTime);
    sys->finish();
  } catch (const std::exception& error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
