#include "../orientation_correlator.h"
#include <iostream>
#include <new>

// GNU linker wrappers keep the real allocator/deallocator and sanitizer tags.
// Never linked into the adapter or performance benchmark.
static long remaining=-1;
void allocation_point() {
  if(remaining==0) throw std::bad_alloc();
  if(remaining>0) --remaining;
}
extern "C" void* __real__Znwm(std::size_t);
extern "C" void* __real__Znam(std::size_t);
extern "C" void* __wrap__Znwm(std::size_t n) {allocation_point();return __real__Znwm(n);}
extern "C" void* __wrap__Znam(std::size_t n) {allocation_point();return __real__Znam(n);}

int main() {
  try {
    for(bool second:{false,true}) {
      long failure_sites=0;
      for(long site=0;site<2000;++site) {
        remaining=site;bool completed=false;
        try {orientation::Bank bank(3,{3,8,2},{0,1,.1},second);completed=true;}
        catch(const std::bad_alloc&) {}
        remaining=-1;
        if(completed) {failure_sites=site;break;}
      }
      if(!failure_sites) throw std::runtime_error("allocation failure sweep did not complete");
      std::cout<<"PASS allocation failure sites="<<failure_sites<<" second_rank="<<second<<'\n';
    }
    return 0;
  } catch(const std::exception& e) {remaining=-1;std::cerr<<e.what()<<'\n';return 1;}
}
