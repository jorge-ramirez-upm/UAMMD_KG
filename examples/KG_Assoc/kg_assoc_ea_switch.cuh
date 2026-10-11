#ifndef EXAMPLES_KG_ASSOC_EA_SWITCH_CUH
#define EXAMPLES_KG_ASSOC_EA_SWITCH_CUH

#include <cmath>
#include <stdexcept>

namespace kg_assoc {

// A switch changes future kinetics only; the caller retains the loaded microstate.
inline double restartEa(double parentEa, double requestedEa, bool explicitEa,
                        bool switching, double expectedParentEa) {
  if (!std::isfinite(parentEa) || parentEa < 0.0 ||
      !std::isfinite(requestedEa) || requestedEa < 0.0) {
    throw std::runtime_error("invalid restart Ea");
  }
  if (switching) {
    if (!explicitEa || !std::isfinite(expectedParentEa) ||
        expectedParentEa != parentEa || requestedEa == parentEa) {
      throw std::runtime_error("Ea switch requires matching --switch-ea-from and distinct --Ea");
    }
    return requestedEa;
  }
  if (explicitEa && requestedEa != parentEa) {
    throw std::runtime_error("Ea mismatch: use explicit --switch-ea-from with --Ea");
  }
  return parentEa;
}

}  // namespace kg_assoc
#endif
