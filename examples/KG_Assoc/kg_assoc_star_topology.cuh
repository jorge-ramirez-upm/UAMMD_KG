#ifndef EXAMPLES_KG_ASSOC_STAR_TOPOLOGY_CUH
#define EXAMPLES_KG_ASSOC_STAR_TOPOLOGY_CUH

#include "../KG/kg_lammps_io.cuh"

#include <algorithm>
#include <iomanip>
#include <map>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace kg_assoc {

struct StarTopologyExpectations {
  int arms = 0;
  int beadsPerArm = 0;
};

struct StarTopologyReport {
  int totalAtoms = 0;
  int polymerBeads = 0;
  int stickers = 0;
  int solventBeads = 0;
  int stars = 0;
  int permanentBonds = 0;
  double lx = 0.0;
  double ly = 0.0;
  double lz = 0.0;
  double volume = 0.0;
  double totalDensity = 0.0;
  double polymerDensity = 0.0;
};

inline std::string atomLabel(int index) {
  return "atom id " + std::to_string(index + 1);
}

inline std::string moleculeLabel(int molecule) {
  return "star molecule " + std::to_string(molecule);
}

inline void fail(const std::string& message) {
  throw std::runtime_error("STAR_TOPOLOGY_AUDIT FAIL: " + message);
}

inline StarTopologyReport auditStarTopology(
    const kg::LammpsData& data,
    const StarTopologyExpectations& expectations) {
  if (expectations.arms <= 0 || expectations.beadsPerArm <= 0) {
    fail("--arms and --narm must both be positive");
  }
  if (data.natoms <= 0 || static_cast<int>(data.type.size()) != data.natoms ||
      static_cast<int>(data.mol.size()) != data.natoms) {
    fail("parser did not provide one type and molecule ID for every atom");
  }
  if (static_cast<int>(data.bonds.size()) != data.nbonds) {
    fail("parsed " + std::to_string(data.bonds.size()) + " bond records, header declares " +
         std::to_string(data.nbonds));
  }

  StarTopologyReport report;
  report.totalAtoms = data.natoms;
  report.permanentBonds = data.nbonds;
  report.lx = data.xhi - data.xlo;
  report.ly = data.yhi - data.ylo;
  report.lz = data.zhi - data.zlo;
  report.volume = report.lx * report.ly * report.lz;
  if (report.lx <= 0.0 || report.ly <= 0.0 || report.lz <= 0.0) {
    fail("box lengths must be positive");
  }

  std::map<int, std::vector<int>> starAtoms;
  for (int index = 0; index < data.natoms; ++index) {
    const int type = data.type[index];
    if (type == 1 || type == 2) {
      ++report.polymerBeads;
      if (type == 2) {
        ++report.stickers;
      }
      starAtoms[data.mol[index]].push_back(index);
    } else if (type == 3) {
      ++report.solventBeads;
    } else {
      fail(atomLabel(index) + " has unsupported type " + std::to_string(type));
    }
  }

  std::vector<std::vector<int>> adjacency(data.natoms);
  for (const auto& bond : data.bonds) {
    // LammpsData retains 1-based LAMMPS atom IDs.  Convert only after bounds
    // checks so an invalid ID cannot alias a zero-based internal index.
    const int first = bond.first - 1;
    const int second = bond.second - 1;
    if (first < 0 || second < 0 || first >= data.natoms || second >= data.natoms) {
      fail("bond references out-of-range LAMMPS atom IDs " +
           std::to_string(bond.first) + " and " + std::to_string(bond.second));
    }
    if (first == second) {
      fail("self bond at " + atomLabel(first));
    }
    if (data.type[first] == 3 || data.type[second] == 3) {
      fail("permanent bond involving solvent: " + atomLabel(first) + " -- " +
           atomLabel(second));
    }
    if (data.mol[first] != data.mol[second]) {
      fail("permanent inter-star bond: " + atomLabel(first) + " (molecule " +
           std::to_string(data.mol[first]) + ") -- " + atomLabel(second) +
           " (molecule " + std::to_string(data.mol[second]) + ")");
    }
    adjacency[first].push_back(second);
    adjacency[second].push_back(first);
  }

  const int expectedBeads = 1 + expectations.arms * expectations.beadsPerArm;
  const int expectedBonds = expectations.arms * expectations.beadsPerArm;
  for (const auto& star : starAtoms) {
    const int molecule = star.first;
    const std::vector<int>& atoms = star.second;
    if (static_cast<int>(atoms.size()) != expectedBeads) {
      fail(moleculeLabel(molecule) + " has " + std::to_string(atoms.size()) +
           " polymer beads; expected " + std::to_string(expectedBeads));
    }

    int localBonds = 0;
    int center = -1;
    int centerCount = 0;
    int terminalCount = 0;
    for (const int atom : atoms) {
      localBonds += static_cast<int>(adjacency[atom].size());
      if (static_cast<int>(adjacency[atom].size()) == expectations.arms) {
        center = atom;
        ++centerCount;
      }
      if (adjacency[atom].size() == 1) {
        ++terminalCount;
        if (data.type[atom] != 2) {
          fail(moleculeLabel(molecule) + " terminal " + atomLabel(atom) +
               " is type " + std::to_string(data.type[atom]) + ", not sticker type 2");
        }
      } else if (data.type[atom] != 1) {
        fail(moleculeLabel(molecule) + " non-terminal " + atomLabel(atom) +
             " is type " + std::to_string(data.type[atom]) + ", not type 1");
      }
    }
    localBonds /= 2;
    if (centerCount != 1) {
      fail(moleculeLabel(molecule) + " has " + std::to_string(centerCount) +
           " degree-" + std::to_string(expectations.arms) + " centers; expected one");
    }
    if (terminalCount != expectations.arms) {
      fail(moleculeLabel(molecule) + " has " + std::to_string(terminalCount) +
           " terminal beads; expected " + std::to_string(expectations.arms));
    }

    std::vector<int> distance(data.natoms, -1);
    std::queue<int> pending;
    distance[center] = 0;
    pending.push(center);
    int visited = 0;
    bool hasCycle = false;
    while (!pending.empty()) {
      const int atom = pending.front();
      pending.pop();
      ++visited;
      for (const int neighbour : adjacency[atom]) {
        if (distance[neighbour] == -1) {
          distance[neighbour] = distance[atom] + 1;
          pending.push(neighbour);
        } else if (distance[neighbour] != distance[atom] - 1) {
          hasCycle = true;
        }
      }
    }
    if (visited != static_cast<int>(atoms.size())) {
      fail(moleculeLabel(molecule) + " permanent-bond graph is disconnected");
    }
    if (hasCycle) {
      fail(moleculeLabel(molecule) + " permanent-bond graph contains a cycle");
    }
    if (localBonds != expectedBonds) {
      fail(moleculeLabel(molecule) + " has " + std::to_string(localBonds) +
           " permanent bonds; expected " + std::to_string(expectedBonds));
    }
    for (const int atom : atoms) {
      if (adjacency[atom].size() == 1 &&
          distance[atom] != expectations.beadsPerArm) {
        fail(moleculeLabel(molecule) + " terminal " + atomLabel(atom) +
             " has graph distance " + std::to_string(distance[atom]) +
             " from center; expected " + std::to_string(expectations.beadsPerArm));
      }
    }
  }

  report.stars = static_cast<int>(starAtoms.size());
  if (report.stars == 0) {
    fail("no polymer star molecules found");
  }
  if (report.stickers != report.stars * expectations.arms) {
    fail("total sticker count " + std::to_string(report.stickers) + " does not equal " +
         std::to_string(report.stars) + " * " + std::to_string(expectations.arms));
  }
  report.totalDensity = static_cast<double>(report.totalAtoms) / report.volume;
  report.polymerDensity = static_cast<double>(report.polymerBeads) / report.volume;
  return report;
}

inline std::string formatStarTopologyReport(const StarTopologyReport& report) {
  std::ostringstream out;
  out << std::setprecision(12);
  out << "total atoms " << report.totalAtoms << "\n";
  out << "polymer beads " << report.polymerBeads << "\n";
  out << "stickers " << report.stickers << "\n";
  out << "solvent beads " << report.solventBeads << "\n";
  out << "number of stars " << report.stars << "\n";
  out << "permanent bonds " << report.permanentBonds << "\n";
  out << "box lengths " << report.lx << " " << report.ly << " " << report.lz << "\n";
  out << "volume " << report.volume << "\n";
  out << "total bead density " << report.totalDensity << "\n";
  out << "polymer bead density " << report.polymerDensity << "\n";
  return out.str();
}

}  // namespace kg_assoc

#endif
