#include "../cpu_workers.h"
#include <cassert>
#include <filesystem>
#include <iostream>
#include <iterator>
#include <limits>
std::string output(streaming::Bank& bank,const std::filesystem::path& path) {
  bank.write(path.string(),.1);
  std::ifstream in(path);
  return {std::istreambuf_iterator<char>(in),{}};
}
int main() {
  using namespace streaming;
  const auto path=std::filesystem::temp_directory_path()/
    ("slip-workers-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
  const Parameters cfg{5,8,2};
  for (std::size_t chains:{1,9,17}) {
    std::vector<Sample> data(43*chains);
    for (std::size_t i=0;i<data.size();++i)
      for (int j=0;j<6;++j) data[i].v[j]=std::sin(double(i+j))+.2;
    Bank reference(chains,cfg,1<<24); reference.consume(data.data(),43);
    const auto expected=output(reference,path);
    for (unsigned workers:{1,2,4,8}) {
      if (workers>chains) continue;
      for (std::size_t batch:{1,3,16,43}) {
        Bank bank(chains,cfg,1<<24);
        CpuWorkers pool(bank,chains,workers);
        for (std::size_t f=0;f<43;f+=batch)
          pool.consume(data.data()+f*chains,std::min(batch,43-f));
        assert(bank.frames==43);
        assert(output(bank,path)==expected);
      }
    }
  }
  for (int repeat=0;repeat<40;++repeat) {
    Bank bank(9,cfg,1<<24); CpuWorkers pool(bank,9,4);
    Sample data[9]{};
    // Fail in worker 0 and a helper, then ensure poisoned-pool rethrow and join.
    data[repeat%9].v[0]=std::numeric_limits<double>::quiet_NaN();
    for (int attempt=0;attempt<2;++attempt) {
      bool failed=false;
      try { pool.consume(data,1); } catch (const std::runtime_error&) { failed=true; }
      assert(failed);
    }
  }
  assert(workerCount(0,1)==1);
#ifdef __linux__
  cpu_set_t original;
  if (sched_getaffinity(0,sizeof original,&original)==0) {
    cpu_set_t one; CPU_ZERO(&one);
    for (int cpu=0;cpu<CPU_SETSIZE;++cpu) if (CPU_ISSET(cpu,&original)) {
      CPU_SET(cpu,&one); break;
    }
    if (sched_setaffinity(0,sizeof one,&one)==0) {
      assert(affinityCpus()==1 && workerCount(0,9)==1);
      assert(sched_setaffinity(0,sizeof original,&original)==0);
    }
  }
#endif
  for (unsigned n:{10,1025}) {
    bool failed=false;
    try { workerCount(n,9); } catch (const std::runtime_error&) { failed=true; }
    assert(failed);
  }
  std::filesystem::remove(path);
  std::cout << "PASS: exact reference/1/2/4/8, unequal ranges, batches, failure, lifetime\n";
}
