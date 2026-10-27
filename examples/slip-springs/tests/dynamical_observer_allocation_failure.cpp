// Reuse the unchanged D2A.1 GNU new/new[] wrappers and bounded sweep helper.
#define main unused_d2a1_allocation_entry
#include "dynamical_allocation_failure.cpp"
#undef main
#include "../dynamical_observer.h"

namespace fs=std::filesystem;
struct Point {double x=0,y=0,z=0,w=0;};
int main(int argc,char** argv) {
  try {
    if(argc!=2)throw std::runtime_error("usage: observer_allocation_failure NEW_PERMANENT_DIRECTORY");
    const fs::path root=argv[1];if(!fs::create_directory(root))throw std::runtime_error("refusing existing test directory");
    dynamical_observer::Settings settings;settings.enabled=true;settings.correlation={3,4,2};
    dynamical_observer::Model model;model.chains=2;model.dt=.0001;model.kbt=1;model.zeta=1;
    model.precision_bits=64;model.mobility_step=.0001;model.noise=std::sqrt(.0002);
    model.b0.assign(32,1);model.kb.assign(32,30);model.kappa.assign(33,0);
    std::vector<Point> positions(66);
    for(unsigned i=0;i<66;++i)positions[i].x=i;
    unsigned attempt=0;
    sweep("observer construction/acquisition/export",[&] {
      const auto path=root/("attempt-"+std::to_string(++attempt));
      try {
        if(!fs::create_directory(path))throw std::runtime_error("reused allocation attempt");
        dynamical_observer::Observer observer(settings,model,path);
        observer.observe(0,positions,true,0,positions.size()*sizeof(Point));
        observer.finish();
      }catch(const std::bad_alloc&) {
        remaining=-1; // Completion inspection itself must not be fault-injected.
        if(fs::is_regular_file(path/"dynamics/metadata.json"))
          throw std::runtime_error("allocation failure published completion");
        throw;
      }
    });
    return 0;
  }catch(const std::exception& e){remaining=-1;std::cerr<<e.what()<<'\n';return 1;}
}
