#ifndef KG_ASSOC_READBACK_DISPATCH_CUH_
#define KG_ASSOC_READBACK_DISPATCH_CUH_

#include <initializer_list>
#include <stdexcept>

namespace kg_assoc_test {

// The callback is the real device readback in MD, and a CPU spy in the call-path probe.
template <class Readback>
void dispatchInitialReadback(bool reseeded, bool extension, Readback readback) {
  if (reseeded || extension) {
    readback();
  }
}

inline void probeInitialReadbackDispatch() {
  for (const bool reseeded : {false, true}) {
    for (const bool extension : {false, true}) {
      int calls = 0;
      dispatchInitialReadback(reseeded, extension, [&]() { ++calls; });
      if (calls != int(reseeded || extension)) {
        throw std::runtime_error("initial readback call-path regression");
      }
      bool reachedIntegration = false;
      bool rejected = false;
      try {
        dispatchInitialReadback(reseeded, extension, []() {
          throw std::runtime_error("CPU spy: missing required device evidence");
        });
        reachedIntegration = true;
      } catch (const std::runtime_error&) {
        rejected = true;
      }
      if (reachedIntegration != !(reseeded || extension) ||
          rejected != (reseeded || extension)) {
        throw std::runtime_error("initial readback fail-stop regression");
      }
    }
  }
}

}  // namespace kg_assoc_test
#endif
