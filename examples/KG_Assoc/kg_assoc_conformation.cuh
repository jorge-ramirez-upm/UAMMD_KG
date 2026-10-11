#ifndef EXAMPLES_KG_ASSOC_CONFORMATION_CUH
#define EXAMPLES_KG_ASSOC_CONFORMATION_CUH

#include "kg_assoc_star_runtime.cuh"

#include <array>
#include <queue>

namespace kg_assoc {

struct StarConformation {
  std::vector<int> traversal;
  std::vector<int> terminals;
  int center = -1;
};

struct ConformationTopology {
  std::vector<StarConformation> stars;
  std::vector<int> parent;
};

inline ConformationTopology conformationTopology(const kg::LammpsData& data, int arms) {
  ConformationTopology result;
  result.parent.assign(data.natoms, -1);
  std::vector<std::vector<int>> adjacency(data.natoms);
  for (const auto& bond : data.bonds) {
    const int first = bond.first - 1;
    const int second = bond.second - 1;
    adjacency.at(first).push_back(second);
    adjacency.at(second).push_back(first);
  }
  std::map<int, std::vector<int>> molecules;
  for (int atom = 0; atom < data.natoms; ++atom) {
    if (data.type.at(atom) == 1 || data.type.at(atom) == 2) {
      molecules[data.mol.at(atom)].push_back(atom);
    }
  }
  for (const auto& molecule : molecules) {
    StarConformation star;
    for (const int atom : molecule.second) {
      if (data.type.at(atom) == 1 && static_cast<int>(adjacency[atom].size()) == arms) {
        if (star.center != -1) {
          throw std::runtime_error("multiple conformation centers");
        }
        star.center = atom;
      }
      if (data.type.at(atom) == 2 && adjacency[atom].size() == 1) {
        star.terminals.push_back(atom);
      }
    }
    if (star.center < 0 || static_cast<int>(star.terminals.size()) != arms) {
      throw std::runtime_error("invalid conformation star topology");
    }
    std::queue<int> pending;
    pending.push(star.center);
    result.parent[star.center] = star.center;
    while (!pending.empty()) {
      const int atom = pending.front();
      pending.pop();
      star.traversal.push_back(atom);
      for (const int neighbor : adjacency[atom]) {
        if (result.parent[neighbor] != -1) {
          continue;
        }
        if (data.mol.at(neighbor) != molecule.first) {
          throw std::runtime_error("conformation bond crosses molecule");
        }
        result.parent[neighbor] = atom;
        pending.push(neighbor);
      }
    }
    if (star.traversal.size() != molecule.second.size()) {
      throw std::runtime_error("disconnected conformation star");
    }
    result.stars.push_back(std::move(star));
  }
  if (result.stars.empty()) {
    throw std::runtime_error("no conformation stars");
  }
  return result;
}

// Same permanent-bond BFS/minimum-image convention as validated E1; O(Nbeads) scratch.
inline std::pair<double, double> conformationMeans(
    const ConformationTopology& topology,
    const std::vector<std::array<double, 3>>& positions,
    const BoxLengths& box) {
  std::vector<std::array<double, 3>> unwrapped(positions.size());
  const std::array<double, 3> lengths{{box.x, box.y, box.z}};
  double rg2 = 0.0;
  double terminalR2 = 0.0;
  int terminals = 0;
  for (const auto& star : topology.stars) {
    std::array<double, 3> center{{0.0, 0.0, 0.0}};
    for (const int atom : star.traversal) {
      const int parent = topology.parent.at(atom);
      for (int axis = 0; axis < 3; ++axis) {
        unwrapped[atom][axis] = atom == parent ? positions.at(atom)[axis] :
            unwrapped[parent][axis] + minimumImage(
                positions.at(atom)[axis] - positions.at(parent)[axis], lengths[axis]);
        center[axis] += unwrapped[atom][axis] / star.traversal.size();
      }
    }
    for (const int atom : star.traversal) {
      for (int axis = 0; axis < 3; ++axis) {
        const double displacement = unwrapped[atom][axis] - center[axis];
        rg2 += displacement * displacement / star.traversal.size();
      }
    }
    for (const int terminal : star.terminals) {
      for (int axis = 0; axis < 3; ++axis) {
        const double displacement = unwrapped[terminal][axis] - unwrapped[star.center][axis];
        terminalR2 += displacement * displacement;
      }
      ++terminals;
    }
  }
  rg2 /= topology.stars.size();
  terminalR2 /= terminals;
  if (!std::isfinite(rg2) || !std::isfinite(terminalR2) || rg2 <= 0.0 || terminalR2 <= 0.0) {
    throw std::runtime_error("invalid E2 conformation observable");
  }
  return {rg2, terminalR2};
}

}  // namespace kg_assoc
#endif
