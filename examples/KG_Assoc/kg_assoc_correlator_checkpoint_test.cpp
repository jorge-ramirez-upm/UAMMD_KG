#include "kg_assoc_correlator_checkpoint.cuh"

#include <cmath>
#include <sstream>
#include <stdexcept>

namespace {

void addSample(kg_assoc::CheckpointableCorrelator6& correlator, int index) {
  const double x = std::sin(0.013 * index);
  correlator.add(x, x + 1.0, 2.0 * x, x - 0.5, -x, 0.25 * x);
}

void expectSame(kg_assoc::CheckpointableCorrelator6& first,
                kg_assoc::CheckpointableCorrelator6& second) {
  first.evaluate();
  second.evaluate();
  if (first.npcorr != second.npcorr) {
    throw std::runtime_error("restored correlator lag count differs");
  }
  for (unsigned int lag = 0; lag < first.npcorr; ++lag) {
    if (first.gett(lag) != second.gett(lag) ||
        first.getn(lag) != second.getn(lag)) {
      throw std::runtime_error("restored correlator grid differs");
    }
    for (int channel = 0; channel < 6; ++channel) {
      if (first.getf(lag, channel) != second.getf(lag, channel)) {
        throw std::runtime_error("restored correlator value differs");
      }
    }
  }
}

}  // namespace

int main() {
  kg_assoc::CheckpointableCorrelator6 uninterrupted;
  for (int index = 0; index < 12345; ++index) {
    addSample(uninterrupted, index);
  }

  std::stringstream checkpoint(std::ios::in | std::ios::out | std::ios::binary);
  uninterrupted.save(checkpoint);
  checkpoint.seekg(0);

  kg_assoc::CheckpointableCorrelator6 restored;
  restored.load(checkpoint);
  expectSame(uninterrupted, restored);

  for (int index = 12345; index < 25000; ++index) {
    addSample(uninterrupted, index);
    addSample(restored, index);
  }
  expectSame(uninterrupted, restored);
  return 0;
}
