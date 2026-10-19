#pragma once
#include "cpu_workers.h"
#include "tests/chain_major_correlator.h" // Local validated traversal; KG remains unchanged.
#include <filesystem>
#include <sstream>

// Host-only adapter: reuse the validated correlator and persistent worker bank.
// No empirical mean subtraction or changes to KG's block/lag definitions.
namespace stress3b {
struct Settings {
  std::string mode="off";
  unsigned workers=1, batch=32, correlatorMiB=512;
  streaming::Parameters correlation;
  double density=0; bool dump=false;
  bool enabled() const { return mode!="off"; }
  bool streaming() const { return mode=="stream"; }
  bool everyStep() const { return mode=="every-step"; }
  bool correlating() const { return streaming()||everyStep(); }
  void validate(std::size_t chains) const {
    if(mode!="off"&&mode!="diagnostic"&&mode!="stream"&&mode!="every-step") throw std::runtime_error("stress-mode must be off, diagnostic, stream or every-step");
    correlation.validate();
    if(!batch||batch>4096||!correlatorMiB||correlatorMiB>65536)throw std::runtime_error("invalid stress batch/correlator budget");
    if(correlating()) {
      streaming::workerCount(workers,chains);
      if(std::size_t(batch)*chains*sizeof(streaming::Sample)>256ULL*1024*1024)throw std::runtime_error("stress batch exceeds 256 MiB");
      if(streaming::OwnedCorrelator6::bytes(correlation)+sizeof(void*)>std::size_t(correlatorMiB)*1024*1024/chains)throw std::runtime_error("stress bank exceeds correlator budget");
    }
    if(!std::isfinite(density)||density<0)throw std::runtime_error("chain-density must be finite and nonnegative (0=unspecified)");
  }
  std::size_t hostBytes(std::size_t chains) const {
    return correlating()?chains*((everyStep()?2:1)*std::size_t(batch)*sizeof(streaming::Sample)+streaming::OwnedCorrelator6::bytes(correlation)+sizeof(void*)+42*sizeof(double)):0;
  }
};

// Benchmark-derived adapter for every-step semiflexible stress. A single CUDA
// producer owns a slot until its copy event; one consumer owns the chain-major
// bank and deterministic persistent worker ranges. Slots are never overwritten.
class EveryStepTransport {
  struct Slot {
    streaming::Sample* device=nullptr; streaming::Sample* host=nullptr;
    cudaEvent_t ready=nullptr, copyStart=nullptr, copyDone=nullptr; std::size_t frames=0,firstFrame=0;
    enum State { free, filling, queued, processing } state=free;
    ~Slot(){ if(ready)cudaEventDestroy(ready);if(copyStart)cudaEventDestroy(copyStart);if(copyDone)cudaEventDestroy(copyDone);if(host)cudaFreeHost(host);if(device)cudaFree(device); }
  };
  int chains,deviceId; std::size_t batch,producer=0,consumer=0,fill=0,momentStart;
  chain_major::Bank bank; chain_major::Workers workers; cudaStream_t transfer=nullptr;
  std::vector<std::unique_ptr<Slot>> slots; std::thread thread; std::mutex mutex; std::condition_variable changed;
  bool closing=false,joined=false; std::exception_ptr failure; std::vector<double> sum,second; std::uint64_t moment_frames=0;
  void checkFailure(){if(failure)std::rethrow_exception(failure);}
  void consume(){try { semiflexible::check(cudaSetDevice(deviceId),"every-step consumer device"); for(;;){Slot* slot;{std::unique_lock<std::mutex> lock(mutex);auto idle=std::chrono::steady_clock::now();changed.wait(lock,[&]{return closing||slots[consumer]->state==Slot::queued;});consumer_idle_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-idle).count();if(slots[consumer]->state!=Slot::queued)return;slot=slots[consumer].get();slot->state=Slot::processing;} auto completion=std::chrono::steady_clock::now();semiflexible::check(cudaEventSynchronize(slot->copyDone),"every-step D2H completion");transfer_completion_wait_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-completion).count();float ms=0;semiflexible::check(cudaEventElapsedTime(&ms,slot->copyStart,slot->copyDone),"every-step D2H elapsed");transfer_seconds+=ms/1000.;transfer_bytes+=slot->frames*std::size_t(chains)*sizeof(streaming::Sample);for(std::size_t f=0;f<slot->frames;++f)if(slot->firstFrame+f>=momentStart){++moment_frames;for(int c=0;c<chains;++c)for(int a=0;a<6;++a){double x=slot->host[f*std::size_t(chains)+c].v[a];sum[c*6+a]+=x;for(int b=0;b<6;++b)second[c*36+a*6+b]+=x*slot->host[f*std::size_t(chains)+c].v[b];}}workers.consume(slot->host,slot->frames);{std::lock_guard<std::mutex> lock(mutex);slot->state=Slot::free;consumer=(consumer+1)%slots.size();}changed.notify_all();}}catch(...){std::lock_guard<std::mutex> lock(mutex);failure=std::current_exception();changed.notify_all();}}
  void submit(){if(!fill)return;auto& slot=*slots[producer];slot.frames=fill;semiflexible::check(cudaEventRecord(slot.ready),"every-step ready");semiflexible::check(cudaStreamWaitEvent(transfer,slot.ready,0),"every-step copy wait");semiflexible::check(cudaEventRecord(slot.copyStart,transfer),"every-step copy start");semiflexible::check(cudaMemcpyAsync(slot.host,slot.device,fill*std::size_t(chains)*sizeof(streaming::Sample),cudaMemcpyDeviceToHost,transfer),"every-step D2H");semiflexible::check(cudaEventRecord(slot.copyDone,transfer),"every-step copy done");{std::lock_guard<std::mutex> lock(mutex);checkFailure();slot.state=Slot::queued;unsigned used=0;for(const auto& v:slots)used+=v->state!=Slot::free;max_inflight_slots=std::max(max_inflight_slots,used);}changed.notify_all();fill=0;producer=(producer+1)%slots.size();}
 public:
  std::uint64_t frames=0,transfer_bytes=0; unsigned max_inflight_slots=0; double buffer_wait_seconds=0,producer_blocked_seconds=0,transfer_seconds=0,transfer_completion_wait_seconds=0,consumer_idle_seconds=0;
  EveryStepTransport(int c,unsigned framesPerSlot,streaming::Parameters cfg,std::size_t budget,unsigned cpuWorkers,std::size_t start):chains(c),batch(framesPerSlot),momentStart(start),bank(c,cfg,budget),workers(bank,c,cpuWorkers),sum(c*6,0),second(c*36,0){
    semiflexible::check(cudaGetDevice(&deviceId),"every-step producer device");semiflexible::check(cudaStreamCreateWithFlags(&transfer,cudaStreamNonBlocking),"every-step transfer stream");
    try {for(int i=0;i<2;++i){slots.push_back(std::make_unique<Slot>());auto& s=*slots.back();auto bytes=batch*std::size_t(chains)*sizeof(streaming::Sample);semiflexible::check(cudaMalloc(&s.device,bytes),"every-step device slab");semiflexible::check(cudaMallocHost(&s.host,bytes),"every-step pinned slab");semiflexible::check(cudaEventCreate(&s.ready),"every-step ready event");semiflexible::check(cudaEventCreate(&s.copyStart),"every-step copy-start event");semiflexible::check(cudaEventCreate(&s.copyDone),"every-step copy-done event");}thread=std::thread([this]{consume();});}catch(...){if(transfer)cudaStreamDestroy(transfer);throw;}
  }
  ~EveryStepTransport(){try{finish();}catch(...){ } if(transfer){cudaStreamSynchronize(transfer);cudaStreamDestroy(transfer);}}
  EveryStepTransport(const EveryStepTransport&)=delete;
  streaming::Sample* destination(){auto& slot=*slots[producer];if(!fill){auto begin=std::chrono::steady_clock::now();std::unique_lock<std::mutex> lock(mutex);const bool blocked=slot.state!=Slot::free;changed.wait(lock,[&]{return failure||slot.state==Slot::free;});const double waited=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();buffer_wait_seconds+=waited;if(blocked)producer_blocked_seconds+=waited;checkFailure();slot.state=Slot::filling;slot.firstFrame=frames;}return slot.device+fill*std::size_t(chains);}
  void published(){++fill;++frames;if(fill==batch)submit();}
  void finish(){if(joined)return;submit();{std::lock_guard<std::mutex> lock(mutex);closing=true;}changed.notify_all();if(thread.joinable())thread.join();checkFailure();if(bank.frames!=frames)throw std::runtime_error("every-step stress frame accounting mismatch");joined=true;}
  void write(const std::string& path,double spacing){if(!joined)throw std::runtime_error("finish every-step transport before write");bank.write(path,spacing);}
  void writeMoments(const std::filesystem::path& path){std::ofstream out(path);out.exceptions(std::ios::badbit|std::ios::failbit);out<<std::setprecision(17)<<"chain,frames";for(int a=0;a<6;++a)out<<",mean"<<a;for(int a=0;a<6;++a)for(int b=0;b<6;++b)out<<",raw"<<a<<b;out<<'\n';for(int c=0;c<chains;++c){out<<c<<','<<moment_frames;for(int a=0;a<6;++a)out<<','<<(moment_frames?sum[c*6+a]/moment_frames:std::numeric_limits<double>::quiet_NaN());for(int a=0;a<36;++a)out<<','<<(moment_frames?second[c*36+a]/moment_frames:std::numeric_limits<double>::quiet_NaN());out<<'\n';}}
  const chain_major::Workers& cpu() const{return workers;}
  std::uint64_t momentFrames() const{return moment_frames;}
  unsigned slotCapacity() const{return unsigned(slots.size());}
  std::size_t deviceBytes() const{return 2*batch*std::size_t(chains)*sizeof(streaming::Sample);}
  std::size_t hostBytes() const{return deviceBytes();}
};
inline std::ofstream file(const std::filesystem::path& p) {
  std::ofstream f(p);f.exceptions(std::ios::badbit|std::ios::failbit);f<<std::setprecision(17);return f;
}
class Correlations {
  Settings cfg;std::size_t chains;
  streaming::Bank bank;
  streaming::CpuWorkers cpu;
  std::ofstream dump;
  std::vector<double> sum,second;
  std::uint64_t momentStart=0;
public:
  double output_seconds=0;
  std::uint64_t frames=0,moment_frames=0;
  Correlations(Settings s,std::size_t c,const std::filesystem::path& out,std::uint64_t momentStartStep=0)
    :cfg(s),chains(c),bank(c,s.correlation,std::size_t(s.correlatorMiB)*1024*1024),
     cpu(bank,c,s.workers),sum(c*6,0),second(c*36,0),momentStart(momentStartStep) {
    if(cfg.dump){dump=file(out/"stress_samples.csv");dump<<"step,chain,xy,xz,yz,xx_yy,xx_zz,yy_zz\n";}
  }
  void received(const streaming::Sample* frame,std::uint64_t step) {
    auto begin=std::chrono::steady_clock::now();
    bool selected=step>=momentStart;if(selected)++moment_frames;
    for(std::size_t c=0;c<chains;++c) {
      if(cfg.dump)dump<<step<<','<<c;
      for(int a=0;a<6;++a) {
        double x=frame[c].v[a];if(!std::isfinite(x))throw std::runtime_error("nonfinite stress channel");
        if(selected){sum[c*6+a]+=x;for(int b=0;b<6;++b)second[c*36+a*6+b]+=x*frame[c].v[b];}
        if(cfg.dump)dump<<','<<x;
      }
      if(cfg.dump)dump<<'\n';
    }
    if(cfg.dump)dump.flush();
    output_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
    ++frames;
  }
  void consume(const streaming::Sample* batch,std::size_t count){cpu.consume(batch,count);}
  const streaming::CpuWorkers& workers() const {return cpu;}
  void write(const std::filesystem::path& out,double spacing,double kbt) {
    if(bank.frames!=frames)throw std::runtime_error("stress frames lost before finalization");
    bank.write((out/"stress_correlations_raw.csv").string(),spacing);
    std::ifstream input(out/"stress_correlations_raw.csv");input.exceptions(std::ios::badbit);if(!input)throw std::runtime_error("cannot read raw correlations");std::string line;
    auto normalized=file(out/"stress_correlations.csv");
    std::getline(input,line);
    // The reused Bank's legacy g/g_se columns are raw H/H_se for arbitrary T.
    auto pos=line.find(",g,g_se,");if(pos==std::string::npos)throw std::runtime_error("unexpected Bank header");
    line.replace(pos,8,",H,H_se,");normalized<<line<<",g,g_se";
    if(cfg.density>0)normalized<<",G,G_se";normalized<<'\n';
    while(std::getline(input,line)) {
      std::vector<std::string> fields;std::istringstream row(line);std::string v;
      while(std::getline(row,v,','))fields.push_back(v);
      double h=std::stod(fields.at(3)),se=std::stod(fields.at(4));
      double g=h/(kbt*kbt),gse=se/(kbt*kbt);
      if(!std::isfinite(g)||(chains>1&&!std::isfinite(gse)))throw std::runtime_error("stress normalization outside double range");
      normalized<<line<<','<<g<<','<<gse;
      if(cfg.density>0){double G=cfg.density*h/kbt,Gse=cfg.density*se/kbt;if(!std::isfinite(G)||(chains>1&&!std::isfinite(Gse)))throw std::runtime_error("intensive stress outside double range");normalized<<','<<G<<','<<Gse;}
      normalized<<'\n';
    }
    auto moments=file(out/"stress_moments.csv");moments<<"chain,frames";
    for(int a=0;a<6;++a)moments<<",mean"<<a;
    for(int a=0;a<6;++a)for(int b=0;b<6;++b)moments<<",raw"<<a<<b;
    moments<<'\n';
    for(std::size_t c=0;c<chains;++c){moments<<c<<','<<moment_frames;for(int a=0;a<6;++a)moments<<','<<(moment_frames?sum[c*6+a]/moment_frames:std::numeric_limits<double>::quiet_NaN());for(int a=0;a<36;++a)moments<<','<<(moment_frames?second[c*36+a]/moment_frames:std::numeric_limits<double>::quiet_NaN());moments<<'\n';}
    // Moments are raw products; these are not used to subtract trajectory means.
    if(dump.is_open())dump.close();
  }
};
}
