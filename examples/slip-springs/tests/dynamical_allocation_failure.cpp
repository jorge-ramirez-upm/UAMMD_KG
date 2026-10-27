#include "../dynamical_observables.h"
#include <iostream>
#include <new>

// Same GNU-linker allocation-failure technique as orientation_allocation_failure.cpp.
// Only this test executable links the wrappers; production uses real allocation.
static long remaining=-1;
void allocation_point(){if(remaining==0)throw std::bad_alloc();if(remaining>0)--remaining;}
extern "C" void* __real__Znwm(std::size_t);
extern "C" void* __real__Znam(std::size_t);
extern "C" void* __wrap__Znwm(std::size_t n){allocation_point();return __real__Znwm(n);}
extern "C" void* __wrap__Znam(std::size_t n){allocation_point();return __real__Znam(n);}

template<class F> void sweep(const char* name,F construct) {
  for(long site=0;site<10000;++site) {
    remaining=site;bool complete=false;
    try {construct();complete=true;}catch(const std::bad_alloc&){}
    remaining=-1;
    if(complete){std::cout<<"PASS allocation failure sweep "<<name<<" sites="<<site<<'\n';return;}
  }
  throw std::runtime_error("allocation failure sweep did not complete");
}
int main() {
  try {
    sweep("diffusion",[]{dynamics::OwnedDiffusion owner({3,8,2});owner.push({{1,2,3}});owner.evaluate();});
    sweep("replica",[]{dynamics::Replica bank(7,{10,11},{3,8,2},{0,1,.1});});
    dynamics::Replica stable(7,{10,11},{3,8,2},{0,1,.1});
    std::vector<dynamics::Observation> input(2);
    for(unsigned c=0;c<2;++c){input[c].chain_id=10+c;input[c].positions[5]={{1,0,0}};}
    stable.observe(0,input);
    sweep("evaluation retry",[&]{auto result=stable.evaluate();if(result.mean.empty())throw std::logic_error("lost samples");});
    stable.observe(1,input);
    if(stable.evaluate().metadata.frames!=2)throw std::logic_error("evaluation failure damaged acquisition");
    return 0;
  }catch(const std::exception& e){remaining=-1;std::cerr<<e.what()<<'\n';return 1;}
}
