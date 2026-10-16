// Compile the frozen host reaction loop with a host-only state adapter; no CUDA.
// Device synchronization and MD are intentionally outside this test's scope.
#define EXAMPLES_KG_ASSOC_STATE_CUH
#include <array>
#include <iomanip>
#include <iostream>
#include <stdexcept>

namespace kg_assoc {
class StickerState {
 public:
  std::array<int, 4> partners{{-1, -1, -1, -1}};
  bool isSticker(int id) const { return id >= 0 && id < 4; }
  int partner(int id) const { return partners.at(id); }
  bool bonded(int first, int second) const {
    return partner(first) == second && partner(second) == first;
  }
  void make(int first, int second) {
    if (partner(first) != -1 || partner(second) != -1) {
      throw std::runtime_error("occupied host fixture");
    }
    partners[first] = second;
    partners[second] = first;
  }
  void breakPair(int first, int second) {
    if (!bonded(first, second)) {
      throw std::runtime_error("missing host fixture bond");
    }
    partners[first] = -1;
    partners[second] = -1;
  }
  void syncDevice() {}
  void validate() const {
    for (int id = 0; id < 4; ++id) {
      if (partner(id) != -1 && !bonded(id, partner(id))) {
        throw std::runtime_error("nonreciprocal host fixture");
      }
    }
  }
};
}  // namespace kg_assoc

#include "examples/KG_Assoc/kg_assoc_kinetics.cuh"
#include "examples/KG_Assoc/kg_assoc_ea_switch.cuh"

int main() {
  std::cout << std::setprecision(17);
  const std::vector<kg_assoc::Candidate> edges{{0, 1, .93}, {1, 2, 1.02}, {2, 3, 1.20}};
  for (double ea : {4., 6., 8., 10.}) {
    for (double temperature : {.8, 1., 1.2}) {
      kg_assoc::Kinetics kinetics({20., ea, temperature, .01, 100, 17}, 30., 1.5, 8.);
      for (const auto& edge : edges) {
        const double du = kg_assoc::deltaU(edge.r, 30., 1.5, 8.);
        std::cout << "P " << ea << ' ' << temperature << ' ' << edge.r << ' '
                  << du << ' ' << kinetics.q() << ' '
                  << kinetics.q() * kg_assoc::metropolisFactor(du, temperature, true) << ' '
                  << kinetics.q() * kg_assoc::metropolisFactor(du, temperature, false) << '\n';
      }
    }
    for (unsigned long long seed = 1; seed <= 17; ++seed) {
      for (int initial : {0, 1, 2, 4, 5}) {
        kg_assoc::StickerState state;
        for (int edge = 0; edge < 3; ++edge) {
          if (initial & (1 << edge)) {
            state.make(edges[edge].first, edges[edge].second);
          }
        }
        kg_assoc::Kinetics kinetics({20., ea, 1., .01, 100, seed}, 30., 1.5, 8.);
        std::vector<kg_assoc::Event> events;
        kinetics.update(100, state, edges, events);
        int final = 0;
        for (int edge = 0; edge < 3; ++edge) {
          if (state.bonded(edges[edge].first, edges[edge].second)) {
            final |= 1 << edge;
          }
        }
        std::cout << "S " << ea << ' ' << seed << ' ' << initial << ' ' << final << '\n';
      }
    }
  }
  if (kg_assoc::restartEa(4., 8., true, true, 4.) != 8.) {
    return 1;
  }
  for (int fixture = 0; fixture < 2; ++fixture) {
    try {
      kg_assoc::restartEa(4., 8., true, fixture != 0, 6.);
      return 2;
    } catch (const std::runtime_error&) {
    }
  }
  std::cout << "RESTART_GUARDS_PASS\n";
}
