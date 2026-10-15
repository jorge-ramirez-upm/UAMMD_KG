// Read-only linkage to KG. Oracle uses offline block averages and direct sums.
#include "correlator.h"
#include <array>
#include <cmath>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

using Sample = std::array<double, 6>;
using Series = std::vector<Sample>;

void verify(Correlator6& correlator, const Series& raw) {
  correlator.evaluate();
  // With (levels,p,m)=(3,4,2), evaluate() excludes deepest reached level 2.
  if (correlator.npcorr != 6) throw std::runtime_error("wrong lag bin count");
  unsigned int bin = 0;
  for (int level = 0; level < 2; ++level) {
    const int block = 1 << level;
    Series averaged(raw.size()/block, Sample{});
    for (std::size_t i = 0; i < averaged.size(); ++i)
      for (int j = 0; j < block; ++j)
        for (int channel = 0; channel < 6; ++channel)
          averaged[i][channel] += raw[i*block+j][channel]/block;
    for (int lag = level == 0 ? 0 : 2; lag < 4; ++lag, ++bin) {
      const auto pairs = averaged.size()-lag;
      if (correlator.gett(bin) != lag*block || correlator.getn(bin) != pairs)
        throw std::runtime_error("lag/count mismatch");
      for (int channel = 0; channel < 6; ++channel) {
        double reference = 0;
        for (std::size_t i = lag; i < averaged.size(); ++i)
          reference += averaged[i][channel]*averaged[i-lag][channel];
        reference /= pairs;
        const double actual = correlator.getf(bin, channel);
        if (!std::isfinite(actual) || std::abs(actual-reference) > 1e-12*(1+std::abs(reference)))
          throw std::runtime_error("direct correlation mismatch");
      }
    }
  }
}

int main() {
  try {
    // Never copy owning Correlator6 objects or delete through the base class.
    std::vector<std::unique_ptr<Correlator6>> correlators;
    std::vector<Series> input(16);
    for (int chain = 0; chain < 16; ++chain) {
      correlators.emplace_back(new Correlator6);
      correlators.back()->setsize(3, 4, 2);
      correlators.back()->initialize();
    }
    for (int pass = 0; pass < 2; ++pass) {
      for (int chain = 0; chain < 16; ++chain) {
        auto& c = *correlators[chain];
        if (pass) c.clear();
        input[chain].clear();
        for (int i = 0; i < 32; ++i) {
          Sample s{};
          for (int channel = 0; channel < 6; ++channel)
            s[channel] = pass ? chain-channel-0.5
                : ((i*(channel+3)+chain)%17)-8+0.25*channel;
          input[chain].push_back(s);
          c.add(s[0], s[1], s[2], s[3], s[4], s[5]);
        }
      }
      for (int chain = 0; chain < 16; ++chain) {
        verify(*correlators[chain], input[chain]);
        verify(*correlators[chain], input[chain]); // evaluate must not consume state
      }
    }
    std::cout << "PASS: 16 independent Correlator6 objects, six signed channels, "
                 "fine/coarse direct oracle, counts, repeated evaluation, clear/reuse\n";
  } catch (const std::exception& error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
