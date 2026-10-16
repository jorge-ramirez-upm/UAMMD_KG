#pragma once
#include "stream_correlator.h"
#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <exception>
#include <filesystem>
#include <sstream>
#include <mutex>
#include <thread>
#ifdef __linux__
#include <sched.h>
#endif

namespace streaming {
// Affinity includes scheduler affinity and cpuset restrictions.
inline unsigned affinityCpus() {
#ifdef __linux__
  // Grow beyond CPU_SETSIZE for large Linux hosts; no homogeneous-core assumption.
  for (std::size_t n=128;n<=1048576;n*=2) {
    cpu_set_t* set=CPU_ALLOC(n);
    if (!set) break;
    const auto bytes=CPU_ALLOC_SIZE(n);
    CPU_ZERO_S(bytes,set);
    const int rc=sched_getaffinity(0,bytes,set);
    const int count=rc==0 ? CPU_COUNT_S(bytes,set):0;
    CPU_FREE(set);
    if (count>0) return unsigned(count);
  }
#endif
  return std::max(1u,std::thread::hardware_concurrency());
}
// Best-effort standard Linux cgroup mounts, including ancestor quotas. Unknown
// layouts fall back to affinity; explicit --cpu-workers remains authoritative.
inline unsigned availableCpus() {
  unsigned cpus=affinityCpus();
#ifdef __linux__
  std::ifstream groups("/proc/self/cgroup");
  std::string line;
  while (std::getline(groups,line)) {
    const auto a=line.find(':'), b=line.find(':',a+1);
    if (a==std::string::npos || b==std::string::npos) continue;
    const auto controllers=line.substr(a+1,b-a-1);
    const bool v2=controllers.empty();
    if (!v2 && (","+controllers+",").find(",cpu,")==std::string::npos) continue;
    std::filesystem::path root=v2 ? "/sys/fs/cgroup":"/sys/fs/cgroup/cpu";
    std::error_code ec;
    if (!v2 && !std::filesystem::exists(root,ec)) root="/sys/fs/cgroup/cpu,cpuacct";
    auto path=(root/line.substr(b+1).substr(1)).lexically_normal();
    // Namespace-relative paths may not exist at the mount; still check its root.
    if (path.string().compare(0,root.string().size(),root.string())!=0 ||
        !std::filesystem::exists(path,ec)) path=root;
    for (;;) {
      long long quota=-1,period=0;
      if (v2) {
        std::ifstream file(path/"cpu.max"); std::string q;
        if (file>>q>>period && q!="max") { std::istringstream value(q); value>>quota; }
      } else {
        std::ifstream(path/"cpu.cfs_quota_us")>>quota;
        std::ifstream(path/"cpu.cfs_period_us")>>period;
      }
      if (quota>0 && period>0) cpus=std::min(cpus,unsigned(std::min<long long>(cpus,std::max(1LL,quota/period))));
      if (path==root || path==path.parent_path()) break;
      path=path.parent_path();
    }
  }
#endif
  return cpus;
}
inline unsigned workerCount(unsigned requested,std::size_t chains) {
  if (!chains) throw std::runtime_error("CPU workers require chains");
  if (requested>1024 || requested>chains)
    throw std::runtime_error("--cpu-workers must be <= chains and <= 1024 (0 selects auto)");
  return requested ? requested : unsigned(std::min({chains,std::size_t(availableCpus()),std::size_t(1024)}));
}
// The caller is worker 0 (the existing async consumer); helpers never use CUDA.
// Only one caller may run a batch. No batch data is copied or queued here.
class CpuWorkers {
  using Clock=std::chrono::steady_clock;
  static double seconds(Clock::time_point t) {
    return std::chrono::duration<double>(Clock::now()-t).count();
  }
  Bank& bank;
  std::size_t chains;
  unsigned count;
  std::vector<std::thread> helpers;
  std::vector<double> times;
  std::mutex mutex;
  std::condition_variable start,done;
  bool stopping=false;
  std::size_t generation=0,remaining=0,frames=0;
  const Sample* data=nullptr;
  std::exception_ptr failure;
  void range(unsigned id) {
    const auto begin=Clock::now();
    bank.consumeRange(data,frames,chains*id/count,chains*(id+1)/count);
    times[id]+=seconds(begin);
  }
  void helper(unsigned id) noexcept {
    std::size_t seen=0;
    std::unique_lock<std::mutex> lock(mutex);
    for (;;) {
      start.wait(lock,[&]{return stopping || seen!=generation;});
      if (stopping) return;
      seen=generation;
      lock.unlock();
      std::exception_ptr error;
      try { range(id); } catch (...) { error=std::current_exception(); }
      lock.lock();
      if (error && !failure) failure=error;
      if (!--remaining) done.notify_one();
    }
  }
  void stop() noexcept {
    { std::lock_guard<std::mutex> lock(mutex); stopping=true; }
    start.notify_all();
    for (auto& t:helpers) if (t.joinable()) t.join();
  }
public:
  double wall_seconds=0,barrier_seconds=0;
  CpuWorkers(Bank& b,std::size_t c,unsigned n):bank(b),chains(c),count(workerCount(n,c)),times(count,0) {
    try { for (unsigned i=1;i<count;++i) helpers.emplace_back([this,i]{helper(i);}); }
    catch (...) { stop(); throw; }
  }
  ~CpuWorkers() { stop(); }
  CpuWorkers(const CpuWorkers&)=delete;
  CpuWorkers& operator=(const CpuWorkers&)=delete;
  void consume(const Sample* samples,std::size_t n) {
    const auto begin=Clock::now();
    if (count==1) {
      bank.consume(samples,n); // preserved Stage 2B reference
      const double t=seconds(begin); times[0]+=t; wall_seconds+=t; return;
    }
    {
      std::lock_guard<std::mutex> lock(mutex);
      if (failure) std::rethrow_exception(failure);
      data=samples; frames=n; remaining=count-1; ++generation;
    }
    start.notify_all();
    std::exception_ptr error;
    try { range(0); } catch (...) { error=std::current_exception(); }
    const auto wait=Clock::now();
    {
      std::unique_lock<std::mutex> lock(mutex);
      done.wait(lock,[&]{return remaining==0;});
      if (error && !failure) failure=error;
      barrier_seconds+=seconds(wait);
      wall_seconds+=seconds(begin);
      if (failure) std::rethrow_exception(failure);
    }
    bank.frames+=n;
  }
  unsigned size() const { return count; }
  // Read only after consume completes / the async consumer joins.
  double aggregateSeconds() const { double s=0; for (double t:times) s+=t; return s; }
};
}
