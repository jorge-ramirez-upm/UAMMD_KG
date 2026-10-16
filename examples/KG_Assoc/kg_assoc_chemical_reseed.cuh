#ifndef EXAMPLES_KG_ASSOC_CHEMICAL_RESEED_CUH
#define EXAMPLES_KG_ASSOC_CHEMICAL_RESEED_CUH

#include <stdexcept>

namespace kg_assoc {

// Only future random draws change; partners, absolute time and counters are retained.
inline unsigned long long restartChemicalSeed(
    unsigned long long parentSeed, unsigned long long requestedSeed, bool explicitSeed,
    bool reseeding, unsigned long long expectedParentSeed, double parentEa,
    double targetEa, bool switchingEa, bool referenceControl,
    unsigned long long mdSeed) {
  if (!reseeding) {
    if (referenceControl || (explicitSeed && requestedSeed != parentSeed)) {
      throw std::runtime_error("chemical seed mismatch: explicit derived reseed required");
    }
    return parentSeed;
  }
  const bool target = targetEa == 6.0 || targetEa == 8.0 || targetEa == 10.0;
  if (!explicitSeed || parentSeed == 0 || expectedParentSeed != parentSeed ||
      requestedSeed == 0 || requestedSeed == parentSeed || mdSeed == 0 ||
      mdSeed == requestedSeed || mdSeed == parentSeed || parentEa != 4.0 ||
      (referenceControl ? (switchingEa || targetEa != 4.0) : (!switchingEa || !target))) {
    throw std::runtime_error("invalid explicit Ea reference-transfer chemical reseed");
  }
  return requestedSeed;
}

}  // namespace kg_assoc
#endif
