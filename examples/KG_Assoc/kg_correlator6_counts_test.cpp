#include "../KG/correlator.h"

#include <cassert>
#include <cmath>

namespace {

bool nearlyEqual(double first, double second) {
  return std::abs(first - second) < 1.0e-12;
}

}  // namespace

int main() {
  Correlator6 correlator;
  correlator.setsize(3, 4, 2);
  correlator.initialize();

  for (int sample = 1; sample <= 8; ++sample) {
    correlator.add(sample, 2.0 * sample, 3.0 * sample,
                   4.0 * sample, 5.0 * sample, 6.0 * sample);
  }
  correlator.evaluate();

  const double expectedTimes[] = {0.0, 1.0, 2.0, 3.0, 4.0, 6.0};
  const unsigned long int expectedCounts[] = {8, 7, 6, 5, 2, 1};
  const double expectedBase[] = {25.5, 24.0, 22.166666666666668,
                                 20.0, 17.25, 11.25};
  const double scales[] = {1.0, 4.0, 9.0, 16.0, 25.0, 36.0};

  assert(correlator.npcorr == 6);
  for (unsigned int index = 0; index < correlator.npcorr; ++index) {
    assert(nearlyEqual(correlator.gett(index), expectedTimes[index]));
    assert(correlator.getn(index) == expectedCounts[index]);
    for (int channel = 0; channel < 6; ++channel) {
      assert(nearlyEqual(correlator.getf(index, channel),
                         expectedBase[index] * scales[channel]));
    }
  }
  return 0;
}
