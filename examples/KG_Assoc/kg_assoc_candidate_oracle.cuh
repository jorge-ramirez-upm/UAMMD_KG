#ifndef EXAMPLES_KG_ASSOC_CANDIDATE_ORACLE_CUH
#define EXAMPLES_KG_ASSOC_CANDIDATE_ORACLE_CUH

// Test-only all-pairs oracle. Never included in ordinary production builds.
#include "kg_assoc_star_runtime.cuh"
#include <algorithm>
#include <map>

namespace kg_assoc_test {

inline std::vector<kg_assoc::Candidate> oracle(
    const std::vector<kg_assoc::StickerCoordinate>& coordinates,
    const kg_assoc::BoxLengths& box,
    double cutoff) {
  std::vector<kg_assoc::Candidate> result;
  for (std::size_t i = 0; i < coordinates.size(); ++i) {
    for (std::size_t j = i + 1; j < coordinates.size(); ++j) {
      const auto a = coordinates[i].position;
      const auto b = coordinates[j].position;
      const double dx = std::remainder(double(b.x) - double(a.x), box.x);
      const double dy = std::remainder(double(b.y) - double(a.y), box.y);
      const double dz = std::remainder(double(b.z) - double(a.z), box.z);
      const double squared = dx * dx + dy * dy + dz * dz;
      if (squared < cutoff * cutoff) {
        const auto pair = std::minmax(coordinates[i].id, coordinates[j].id);
        result.push_back({pair.first, pair.second, std::sqrt(squared)});
      }
    }
  }
  return result;
}

inline std::map<std::pair<int, int>, double> pairs(
    const std::vector<kg_assoc::Candidate>& candidates) {
  std::map<std::pair<int, int>, double> result;
  for (const auto& edge : candidates) {
    if (edge.first >= edge.second ||
        !result.emplace(std::make_pair(edge.first, edge.second), edge.r).second) {
      throw std::runtime_error("candidate regression: unordered or duplicate pair");
    }
  }
  return result;
}

inline void compare(const std::vector<kg_assoc::Candidate>& actual,
                    const std::vector<kg_assoc::Candidate>& expected) {
  const auto found = pairs(actual);
  const auto reference = pairs(expected);
  if (found.size() != reference.size()) {
    throw std::runtime_error("candidate regression: oracle count mismatch");
  }
  for (const auto& item : reference) {
    const auto match = found.find(item.first);
    if (match == found.end() || std::abs(match->second - item.second) > 1e-4) {
      throw std::runtime_error("candidate regression: oracle pair/distance mismatch");
    }
  }
}

inline std::size_t checkSweep(std::shared_ptr<uammd::ParticleData> particles,
                              const kg_assoc::StickerState& state,
                              const kg_assoc::BoxLengths& box,
                              double cutoff,
                              const std::vector<kg_assoc::Candidate>& found) {
  auto positions = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto mapping = particles->getIdOrderedIndices(uammd::access::cpu);
  std::vector<kg_assoc::StickerCoordinate> coordinates;
  for (int id : state.stickers()) {
    coordinates.push_back({id, uammd::make_real3(positions[mapping[id]])});
  }
  const auto expected = oracle(coordinates, box, cutoff);
  compare(found, expected);
  std::size_t active = 0;
  for (const auto& edge : expected) {
    active += state.bonded(edge.first, edge.second);
  }
  return active;
}

}  // namespace kg_assoc_test
#endif
