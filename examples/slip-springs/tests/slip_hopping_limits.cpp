#include "../slip_hopping.h"
#include <cassert>
#include <iostream>
#include <limits>
template<class F> void rejects(F f) {
  bool failed=false;try{f();}catch(const std::runtime_error&){failed=true;}assert(failed);
}
int main() {
  using slip_hopping::poissonMean;
  assert(poissonMean(4,2,.125)==1);
  assert(poissonMean(0,1e308,1)==0);
  assert(poissonMean(4,0,1)==0);
  assert(poissonMean(1,10000,1)==10000);
  rejects([]{poissonMean(0,-1,1);});
  rejects([]{poissonMean(1,std::numeric_limits<double>::infinity(),1);});
  rejects([]{poissonMean(1,std::numeric_limits<double>::quiet_NaN(),1);});
  rejects([]{poissonMean(1,1e-300,1e-300);});
  rejects([]{poissonMean(1000,1e308,1e308);});
  rejects([]{poissonMean(1,10001,1);});
  std::cout<<"hopping mean validation passed\n";
}
