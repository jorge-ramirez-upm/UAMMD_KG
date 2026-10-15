#include "../stream_correlator.h"
#include <cassert>
#include <iostream>
#include <type_traits>
int main() {
  using namespace streaming;
  static_assert(!std::is_copy_constructible<OwnedCorrelator6>::value);
  static_assert(!std::is_move_constructible<OwnedCorrelator6>::value);
  for (int repeat=0;repeat<200;++repeat) {
    OwnedCorrelator6 c({4,8,2});
    for (int i=0;i<35;++i) c.push({{double(i+1),2,3,4,5,6}});
    c.evaluate();
    assert(c.size()>=8 && c.getn(0)==35 && c.getn(7)==28);
    double expected=0;
    for (int i=1;i<=35;++i) expected+=i*i;
    assert(std::abs(c.getf(0,0)-expected/35)<1e-12);
    assert(c.getf(0,3)==16);
  }
  bool rejected=false;
  try { OwnedCorrelator6 invalid({2,7,2}); } catch(const std::exception&) { rejected=true; }
  assert(rejected);
  rejected=false;
  try { Bank invalid(100,{16,16,2},1); } catch(const std::exception&) { rejected=true; }
  assert(rejected);
  std::cout << "PASS: 200 allocation/add/evaluate/destruction cycles; ownership and budget guards\n";
}
