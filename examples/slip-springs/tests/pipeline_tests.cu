#include "../stream_pipeline.cuh"
#include <cassert>
#include <iostream>
#include <limits>
int main() {
  try {
    using namespace uammd;
    real4* device=nullptr;
    rouse::check(cudaMalloc(&device,18*sizeof(real4)),"test positions");
    const real nan=std::numeric_limits<real>::quiet_NaN();
    real4 positions[18]={make_real4(0,0,0,0),make_real4(nan,1,0,0)};
    rouse::check(cudaMemcpy(device,positions,sizeof positions,cudaMemcpyHostToDevice),"test copy");
    for (unsigned workers:{1,2,4,8}) {
    for (bool async:{false,true}) {
      if (!async && workers!=1) continue;
      bool rejected=false;
      try {
        streaming::Pipeline p(9,2,1,async,{3,4,2},1024*1024,workers);
        // Multiple submissions exercise both backpressure and finish error paths.
        for (int i=0;i<5;++i) p.sample(device);
        p.finish();
      } catch (const std::exception& e) {
        rejected=std::string(e.what()).find("nonfinite streaming stress")!=std::string::npos;
      }
      assert(rejected);
    }
    }
    rouse::check(cudaFree(device),"test free");
    std::cout << "PASS: sync/async consumer errors propagate; queued resources drain and join\n";
  } catch(const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
