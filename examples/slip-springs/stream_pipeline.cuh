#pragma once
#include "rouse.cuh"
#include "stream_correlator.h"
#include <chrono>
#include <condition_variable>
#include <exception>
#include <mutex>
#include <thread>

namespace streaming {
using Clock=std::chrono::steady_clock;
inline double elapsed(Clock::time_point t) { return std::chrono::duration<double>(Clock::now()-t).count(); }
struct Event {
  cudaEvent_t value=nullptr;
  Event() { rouse::check(cudaEventCreate(&value),"stream event create"); }
  ~Event() { if (value) cudaEventDestroy(value); }
  Event(const Event&)=delete;
  Event& operator=(const Event&)=delete;
};
inline double duration(const Event& a,const Event& b) {
  float ms; rouse::check(cudaEventElapsedTime(&ms,a.value,b.value),"stream event elapsed"); return ms/1000.;
}
__global__ void stress(const uammd::real4* pos,Sample* out,int chains,int m) {
  const int c=blockIdx.x*blockDim.x+threadIdx.x;
  if (c>=chains) return;
  double s[6]{};
  for (int i=0;i<m-1;++i) {
    const auto a=pos[c*m+i],b=pos[c*m+i+1];
    const double x=double(b.x)-double(a.x),y=double(b.y)-double(a.y),z=double(b.z)-double(a.z);
    s[0]+=3*x*x; s[1]+=3*y*y; s[2]+=3*z*z;
    s[3]+=3*x*y; s[4]+=3*x*z; s[5]+=3*y*z;
  }
  out[c]={{s[3],s[4],s[5],s[0]-s[1],s[0]-s[2],s[1]-s[2]}};
}
class Pipeline {
  struct Slot {
    Sample* device=nullptr;
    Sample* host=nullptr;
    Event ready,copyStart,copyDone;
    std::vector<std::unique_ptr<Event>> starts,stops;
    std::size_t frames=0;
    enum State { free,filling,queued,processing } state=free;
    ~Slot() { if (host) cudaFreeHost(host); if (device) cudaFree(device); }
  };
  int chains,m,deviceId;
  std::size_t capacity;
  bool asynchronous;
  Bank bank;
  cudaStream_t transfer=nullptr;
  std::vector<std::unique_ptr<Slot>> slots;
  std::size_t producer=0,consumer=0,fill=0;
  std::thread worker;
  std::mutex mutex;
  std::condition_variable changed;
  bool closing=false,joined=false;
  std::exception_ptr failure;
  void rethrow() { if (failure) std::rethrow_exception(failure); }
  void process(Slot& s) {
    const auto wait=Clock::now();
    rouse::check(cudaEventSynchronize(s.copyDone.value),"stream transfer completion");
    transfer_wait_seconds+=elapsed(wait);
    transfer_seconds+=duration(s.copyStart,s.copyDone);
    for (std::size_t f=0;f<s.frames;++f) sampling_gpu_seconds+=duration(*s.starts[f],*s.stops[f]);
    const auto begin=Clock::now();
    bank.consume(s.host,s.frames);
    correlation_seconds+=elapsed(begin);
  }
  void consume() noexcept {
    try {
      rouse::check(cudaSetDevice(deviceId),"consumer device");
      for (;;) {
        Slot* s;
        {
          std::unique_lock<std::mutex> lock(mutex);
          changed.wait(lock,[&]{ return closing || slots[consumer]->state==Slot::queued; });
          s=slots[consumer].get();
          if (s->state!=Slot::queued) return;
          s->state=Slot::processing;
        }
        process(*s);
        {
          std::lock_guard<std::mutex> lock(mutex);
          s->state=Slot::free; consumer=(consumer+1)%slots.size();
        }
        changed.notify_all();
      }
    } catch (...) {
      { std::lock_guard<std::mutex> lock(mutex); failure=std::current_exception(); }
      changed.notify_all();
    }
  }
  void submit() {
    if (!fill) return;
    auto& s=*slots[producer];
    s.frames=fill;
    rouse::check(cudaEventRecord(s.ready.value),"producer ready");
    rouse::check(cudaStreamWaitEvent(transfer,s.ready.value,0),"transfer waits producer");
    rouse::check(cudaEventRecord(s.copyStart.value,transfer),"transfer start");
    rouse::check(cudaMemcpyAsync(s.host,s.device,fill*std::size_t(chains)*sizeof(Sample),
                                cudaMemcpyDeviceToHost,transfer),"stress batch D2H");
    rouse::check(cudaEventRecord(s.copyDone.value,transfer),"transfer done");
    if (asynchronous) {
      { std::lock_guard<std::mutex> lock(mutex); rethrow(); s.state=Slot::queued; }
      changed.notify_all();
    } else { process(s); s.state=Slot::free; }
    fill=0; producer=(producer+1)%slots.size();
  }
public:
  double sampling_gpu_seconds=0,enqueue_seconds=0,transfer_seconds=0,
         transfer_wait_seconds=0,buffer_wait_seconds=0,correlation_seconds=0;
  Pipeline(int c,int beads,std::size_t batch,bool async,Parameters cfg,std::size_t budget)
      :chains(c),m(beads),capacity(batch),asynchronous(async),bank(c,cfg,budget) {
    rouse::check(cudaGetDevice(&deviceId),"producer device");
    try {
      rouse::check(cudaStreamCreateWithFlags(&transfer,cudaStreamNonBlocking),"transfer stream");
      for (int i=0;i<(async ? 2:1);++i) {
        slots.push_back(std::make_unique<Slot>());
        auto& s=*slots.back();
        const auto bytes=capacity*std::size_t(chains)*sizeof(Sample);
        rouse::check(cudaMalloc(&s.device,bytes),"device stress batch");
        rouse::check(cudaMallocHost(&s.host,bytes),"pinned stress batch");
        for (std::size_t f=0;f<capacity;++f) {
          s.starts.push_back(std::make_unique<Event>()); s.stops.push_back(std::make_unique<Event>());
        }
      }
      if (async) worker=std::thread([this]{consume();});
    } catch (...) { if (transfer) cudaStreamDestroy(transfer); throw; }
  }
  ~Pipeline() {
    // Error exit: drain queued work, join before any pinned/device allocation dies.
    if (worker.joinable()) {
      { std::lock_guard<std::mutex> lock(mutex); closing=true; }
      changed.notify_all(); worker.join();
    }
    // Protect even an unfinished frame if a launch/submit threw before publication.
    cudaStreamSynchronize(nullptr);
    if (transfer) { cudaStreamSynchronize(transfer); cudaStreamDestroy(transfer); }
  }
  Pipeline(const Pipeline&)=delete;
  Pipeline& operator=(const Pipeline&)=delete;
  void sample(const uammd::real4* positions) {
    auto& s=*slots[producer];
    if (!fill) {
      const auto wait=Clock::now();
      std::unique_lock<std::mutex> lock(mutex);
      changed.wait(lock,[&]{return failure || s.state==Slot::free;});
      rethrow(); s.state=Slot::filling;
      buffer_wait_seconds+=elapsed(wait);
    }
    const auto begin=Clock::now();
    rouse::check(cudaEventRecord(s.starts[fill]->value),"stress start");
    stress<<<(chains+127)/128,128>>>(positions,s.device+fill*std::size_t(chains),chains,m);
    rouse::check(cudaGetLastError(),"stream stress launch");
    rouse::check(cudaEventRecord(s.stops[fill]->value),"stress stop");
    enqueue_seconds+=elapsed(begin);
    if (++fill==capacity) submit();
  }
  void finish() {
    submit();
    if (worker.joinable()) {
      { std::lock_guard<std::mutex> lock(mutex); closing=true; }
      changed.notify_all(); worker.join();
    }
    rethrow(); joined=true;
  }
  std::uint64_t frames() const { return bank.frames; }
  void write(const std::string& path,double spacing) {
    if (!joined) throw std::runtime_error("finish streaming before evaluation");
    bank.write(path,spacing);
  }
};
}
