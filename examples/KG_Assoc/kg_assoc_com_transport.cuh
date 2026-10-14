#ifndef KG_ASSOC_COM_TRANSPORT_CUH
#define KG_ASSOC_COM_TRANSPORT_CUH

#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <map>
#include <ostream>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <unistd.h>

namespace kg_assoc {

using ComPoint = std::array<double, 3>;
enum class NativeComConvention { unknown, continuous_gronbech_jensen_v1 };

// Observer only: offsets belong to immutable particle IDs, not storage indices.
class ComTransport {
 public:
  ComTransport(const std::vector<int>& molecules, const std::vector<int>& types,
               const std::vector<std::pair<int, int>>& permanentBonds,
               const std::vector<double>& masses, const std::vector<ComPoint>& initial,
               const ComPoint& lengths, double maximumBondLength,
               NativeComConvention convention)
      : lengths_(lengths), offsets_(initial.size(), {{0.0, 0.0, 0.0}}),
        permanentBonds_(permanentBonds), maximumBondLength_(maximumBondLength) {
    if (convention != NativeComConvention::continuous_gronbech_jensen_v1) {
      throw std::runtime_error("COM requires guaranteed continuous native segment coordinates");
    }
    const auto count = initial.size();
    if (molecules.size() != count || types.size() != count || masses.size() != count) {
      throw std::runtime_error("COM particle identity coverage differs");
    }
    for (double length : lengths_) {
      if (!std::isfinite(length) || length <= 0 || !std::isfinite(maximumBondLength) || maximumBondLength <= 0 ||
          maximumBondLength >= length / 2) {
        throw std::runtime_error("COM requires orthorhombic lengths and short permanent bonds");
      }
    }
    for (std::size_t id = 0; id < count; ++id) {
      if (masses[id] != 1.0) {
        throw std::runtime_error("COM supports the frozen unit-mass model only");
      }
      if (types[id] == 1 || types[id] == 2) {
        if (molecules[id] <= 0) {
          throw std::runtime_error("COM requires positive immutable molecule IDs");
        }
        stars_[molecules[id]].push_back(static_cast<int>(id));
      }
    }
    if (stars_.empty()) {
      throw std::runtime_error("COM has no permanent molecules");
    }
    std::vector<std::vector<int>> adjacency(count);
    for (const auto& bond : permanentBonds) {
      const int first = bond.first;
      const int second = bond.second;
      if (first < 0 || second < 0 || first >= static_cast<int>(count) ||
          second >= static_cast<int>(count) || first == second ||
          types[first] == 3 || types[second] == 3 || molecules[first] != molecules[second]) {
        throw std::runtime_error("COM permanent bond changes molecule membership");
      }
      adjacency[first].push_back(second);
      adjacency[second].push_back(first);
    }
    auto whole = initial;
    std::vector<bool> visited(count, false);
    for (const auto& star : stars_) {
      std::queue<int> pending;
      pending.push(star.second.front());
      visited[star.second.front()] = true;
      std::size_t reached = 0;
      std::size_t edges = 0;
      while (!pending.empty()) {
        const int parent = pending.front();
        pending.pop();
        ++reached;
        edges += adjacency[parent].size();
        for (int child : adjacency[parent]) {
          ComPoint displacement;
          double squared = 0;
          for (int axis = 0; axis < 3; ++axis) {
            const double raw = initial[child][axis] - initial[parent][axis];
            displacement[axis] = raw - lengths_[axis] * std::nearbyint(raw / lengths_[axis]);
            squared += displacement[axis] * displacement[axis];
          }
          if (!std::isfinite(squared) || squared >= maximumBondLength * maximumBondLength) {
            throw std::runtime_error("invalid permanent bond in COM origin reconstruction");
          }
          if (!visited[child]) {
            for (int axis = 0; axis < 3; ++axis) {
              whole[child][axis] = whole[parent][axis] + displacement[axis];
              offsets_[child][axis] = whole[child][axis] - initial[child][axis];
            }
            visited[child] = true;
            pending.push(child);
          }
        }
      }
      if (reached != star.second.size() || edges != 2 * (reached - 1)) {
        throw std::runtime_error("COM requires connected permanent star trees");
      }
    }
    positions(initial);  // Validate finite origin coordinates, including single-bead fixtures.
  }

  std::map<int, ComPoint> positions(const std::vector<ComPoint>& native) const {
    if (native.size() != offsets_.size()) {
      throw std::runtime_error("COM native coordinate coverage differs");
    }
    // Fixed image branches must remain compatible with short permanent bonds.
    // This detects internal coordinate folding; a shared whole-box fold still requires
    // the explicit continuous-integrator contract and cannot be inferred from samples.
    for (const auto& bond : permanentBonds_) {
      double squared = 0;
      for (int axis = 0; axis < 3; ++axis) {
        const double displacement = native[bond.first][axis] + offsets_[bond.first][axis] -
                                    native[bond.second][axis] - offsets_[bond.second][axis];
        squared += displacement * displacement;
      }
      if (!std::isfinite(squared) || squared >= maximumBondLength_ * maximumBondLength_) {
        throw std::runtime_error("native COM permanent-bond branch changed or became invalid");
      }
    }
    std::map<int, ComPoint> result;
    for (const auto& star : stars_) {
      ComPoint center{{0.0, 0.0, 0.0}};
      for (int id : star.second) {
        for (int axis = 0; axis < 3; ++axis) {
          const double value = native[id][axis] + offsets_[id][axis];
          if (!std::isfinite(value)) {
            throw std::runtime_error("nonfinite native COM coordinate");
          }
          center[axis] += value / star.second.size();
        }
      }
      result.emplace(star.first, center);
    }
    return result;
  }

  std::vector<int> moleculeIds() const {
    std::vector<int> ids;
    for (const auto& star : stars_) {
      ids.push_back(star.first);
    }
    return ids;
  }

 private:
  ComPoint lengths_;
  std::vector<ComPoint> offsets_;
  std::vector<std::pair<int, int>> permanentBonds_;
  double maximumBondLength_;
  std::map<int, std::vector<int>> stars_;
};

inline void requireIndependentComOrigin(const std::string& restartPrefix,
                                        bool requestedContinuation = false) {
  if (requestedContinuation) {
    throw std::runtime_error("COM continuation requires a verifiable origin checkpoint; unsupported");
  }
  for (const char* suffix : {".com_trajectory", ".com_samples", ".topology", ".complete.json"}) {
    if (!restartPrefix.empty() && std::ifstream(restartPrefix + suffix)) {
      throw std::runtime_error("production COM continuation is unsupported: origin checkpoint absent; "
                               "do not concatenate independent transport segments");
    }
  }
}

inline void requireOrthorhombicComInput(const std::string& path) {
  std::ifstream input(path);
  std::string line;
  while (std::getline(input, line)) {
    if (line.find("kg_assoc_campaign_production") != std::string::npos) {
      throw std::runtime_error("production archive has no resumable COM origin checkpoint");
    }
    if (line.find("Atoms") == 0) {
      break;
    }
    std::istringstream words(line);
    double xy, xz, yz;
    std::string first, second, third;
    if (words >> xy >> xz >> yz >> first >> second >> third) {
      if (first == "xy" && second == "xz" && third == "yz") {
        throw std::runtime_error("COM transport does not support triclinic input");
      }
    }
  }
}

inline void writeComTransportHeader(std::ostream& output, const std::array<double, 6>& bounds,
                                    const std::vector<int>& moleculeIds, long long originStep,
                                    long long cadence, double dt, const std::string& originId) {
  if (originId.empty() || cadence <= 0 || dt <= 0 || !std::isfinite(dt)) {
    throw std::runtime_error("invalid COM transport metadata");
  }
  for (unsigned char character : originId) {
    if (character < 32) {
      throw std::runtime_error("control character in COM origin identity");
    }
  }
  std::string scopedOriginId = originId;
  if (originId.front() != '/') {
    char directory[4096];
    if (!getcwd(directory, sizeof(directory))) {
      throw std::runtime_error("cannot bind COM origin to the producer working directory");
    }
    scopedOriginId = std::string(directory) + "/" + originId;
  }
  output << "# step time molecule_id com_x com_y com_z\n"
         << "# KG_COM_TRANSPORT 2\n"
         << "# convention native_continuous_plus_initial_backbone_offsets\n"
         << "# origin_kind independent_segment_no_concatenation\n"
         << "# origin_id " << std::quoted(scopedOriginId) << '\n'
         << "# origin_step " << originStep << '\n'
         << "# cadence_steps " << cadence << '\n'
         << "# dt " << std::setprecision(17) << dt << '\n'
         << "# unit_mass 1\n# box_bounds";
  for (double bound : bounds) {
    output << ' ' << bound;
  }
  output << "\n# molecule_ids";
  for (int id : moleculeIds) {
    output << ' ' << id;
  }
  output << "\n# END_KG_COM_TRANSPORT\n";
}

}  // namespace kg_assoc
#endif
