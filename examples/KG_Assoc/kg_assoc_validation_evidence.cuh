#ifndef EXAMPLES_KG_ASSOC_VALIDATION_EVIDENCE_CUH
#define EXAMPLES_KG_ASSOC_VALIDATION_EVIDENCE_CUH

// Validation-only host serialization and comparison; no random draws or candidate mutation.
#include "kg_assoc_star_runtime.cuh"
#include <array>
#include <cerrno>
#include <cfenv>
#include <fcntl.h>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <unistd.h>

namespace kg_assoc_test {

struct DiagnosticContext {
  std::string branch;
  std::string executable;
  std::string buildManifest;
  std::string buildJson;
  long long step = 0;
  long long sweep = 0;
};

inline void writeExclusive(const std::string& path, const std::string& text) {
  const int descriptor = ::open(path.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0444);
  if (descriptor < 0) {
    throw std::runtime_error("cannot create immutable validation evidence: " + path);
  }
  std::size_t offset = 0;
  while (offset < text.size()) {
    const auto count = ::write(descriptor, text.data() + offset, text.size() - offset);
    if (count < 0 && errno == EINTR) {
      continue;
    }
    if (count <= 0) {
      ::close(descriptor);
      throw std::runtime_error("cannot finish validation evidence: " + path);
    }
    offset += static_cast<std::size_t>(count);
  }
  const int synchronized = ::fsync(descriptor);
  const int closed = ::close(descriptor);
  if (synchronized != 0 || closed != 0) {
    throw std::runtime_error("cannot flush validation evidence: " + path);
  }
}

inline void evidenceHeader(std::ostream& out, const DiagnosticContext& context,
                           const kg_assoc::BoxLengths& box, double cutoff) {
  const auto separator = context.branch.find(':');
  const auto replica = context.branch.rfind(':');
  out << std::setprecision(17)
      << "# validation_evidence_version=1 system=" << context.branch.substr(0, separator)
      << " branch=" << context.branch
      << " replica=" << (replica == std::string::npos ? "unspecified" :
                         context.branch.substr(replica + 1))
      << " absolute_step=" << context.step << " chemistry_sweep=" << context.sweep
      << " real_bytes=" << sizeof(uammd::real) << " rounding_mode=" << std::fegetround()
      << " cutoff=" << cutoff << " strict_rsq_lt=" << cutoff * cutoff
      << " box=" << box.x << ',' << box.y << ',' << box.z << '\n'
      << "# executable=" << context.executable << " build_manifest=" << context.buildManifest
      << " compiler=" << __VERSION__ << " compiled=" << __DATE__ << ' ' << __TIME__ << '\n';
  std::istringstream manifest(context.buildJson);
  std::string line;
  while (std::getline(manifest, line)) {
    out << "# build " << line << '\n';
  }
}

struct PairArithmetic {
  std::array<double, 3> raw;
  std::array<double, 3> image;
  std::array<double, 3> displacement;
  double squared;
  double distance;
};

inline PairArithmetic pairArithmetic(uammd::real3 first, uammd::real3 second,
                                     const kg_assoc::BoxLengths& box, bool realFirst) {
  PairArithmetic result;
  const std::array<uammd::real, 3> a{{first.x, first.y, first.z}};
  const std::array<uammd::real, 3> b{{second.x, second.y, second.z}};
  const std::array<double, 3> lengths{{box.x, box.y, box.z}};
  for (int axis = 0; axis < 3; ++axis) {
    result.raw[axis] = realFirst ? double(uammd::real(b[axis] - a[axis])) :
                                  double(b[axis]) - double(a[axis]);
    result.image[axis] = std::nearbyint(result.raw[axis] / lengths[axis]);
    result.displacement[axis] = result.raw[axis] - lengths[axis] * result.image[axis];
  }
  const auto& d = result.displacement;
  result.squared = d[0] * d[0] + d[1] * d[1] + d[2] * d[2];
  result.distance = std::sqrt(result.squared);
  return result;
}

inline void writeCandidateMismatch(
    const std::string& path, const DiagnosticContext& context,
    const std::vector<kg_assoc::StickerCoordinate>& coordinates,
    const kg_assoc::StickerState& state, const kg_assoc::BoxLengths& box, double cutoff,
    const std::vector<kg_assoc::Candidate>& actual,
    const std::vector<kg_assoc::Candidate>& expected) {
  std::ostringstream out;
  evidenceHeader(out, context, box, cutoff);
  out << "# actual_size=" << actual.size() << " oracle_size=" << expected.size()
      << " ids=1_based partner_minus_one=free\n";
  std::map<std::pair<int, int>, double> found;
  std::map<std::pair<int, int>, double> reference;
  std::map<int, uammd::real3> positions;
  std::set<std::pair<int, int>> unionPairs;
  out << "# coordinates: id x y z partner\n";
  for (const auto& coordinate : coordinates) {
    positions[coordinate.id] = coordinate.position;
    const auto p = coordinate.position;
    const int partner = state.partner(coordinate.id);
    out << "coordinate " << coordinate.id + 1 << ' ' << p.x << ' ' << p.y << ' ' << p.z
        << ' ' << (partner < 0 ? -1 : partner + 1) << '\n';
  }
  for (const auto& edge : actual) {
    found[{edge.first, edge.second}] = edge.r;
    unionPairs.insert({edge.first, edge.second});
    out << "actual " << edge.first + 1 << ' ' << edge.second + 1 << ' ' << edge.r << '\n';
  }
  for (const auto& edge : expected) {
    reference[{edge.first, edge.second}] = edge.r;
    unionPairs.insert({edge.first, edge.second});
    out << "oracle " << edge.first + 1 << ' ' << edge.second + 1 << ' ' << edge.r << '\n';
  }
  out << "# difference: kind first second associated both_free actual_r oracle_r "
      << "real_r double_r real_r_minus_cutoff double_r_minus_cutoff "
      << "real_rsq_minus_cutoff_sq double_rsq_minus_cutoff_sq\n"
      << "# arithmetic: first second convention raw_xyz image_multiple_xyz mic_xyz\n";
  for (const auto& pair : unionPairs) {
    const auto a = found.find(pair);
    const auto b = reference.find(pair);
    if (a != found.end() && b != reference.end() && a->second == b->second) {
      continue;
    }
    if (!positions.count(pair.first) || !positions.count(pair.second)) {
      out << "# missing_coordinate_for_pair=" << pair.first + 1 << ',' << pair.second + 1 << '\n';
      continue;
    }
    const auto p = positions.at(pair.first);
    const auto q = positions.at(pair.second);
    const auto real = pairArithmetic(p, q, box, true);
    const auto precise = pairArithmetic(p, q, box, false);
    const auto absent = std::numeric_limits<double>::quiet_NaN();
    out << "difference " << (a == found.end() ? "missing" :
                              b == reference.end() ? "extra" : "distance")
        << ' ' << pair.first + 1 << ' ' << pair.second + 1
        << ' ' << state.bonded(pair.first, pair.second)
        << ' ' << (state.partner(pair.first) < 0 && state.partner(pair.second) < 0)
        << ' ' << (a == found.end() ? absent : a->second)
        << ' ' << (b == reference.end() ? absent : b->second)
        << ' ' << real.distance << ' ' << precise.distance
        << ' ' << real.distance - cutoff << ' ' << precise.distance - cutoff
        << ' ' << real.squared - cutoff * cutoff
        << ' ' << precise.squared - cutoff * cutoff << '\n';
    for (const bool realFirst : {true, false}) {
      const auto arithmetic = realFirst ? real : precise;
      out << "arithmetic " << pair.first + 1 << ' ' << pair.second + 1
          << ' ' << (realFirst ? "real_first" : "double_first");
      for (double value : arithmetic.raw) {
        out << ' ' << value;
      }
      for (double value : arithmetic.image) {
        out << ' ' << value;
      }
      for (double value : arithmetic.displacement) {
        out << ' ' << value;
      }
      out << '\n';
    }
  }
  out << "# mismatch_terminates_before_chemistry_update=1\n";
  writeExclusive(path, out.str());
}

struct InitialParticle {
  int expectedId = -1;
  int actualId = -1;
  int molecule = -1;  // Host topology identity, not a device property.
  int expectedType = -1;
  double actualType = -1;
  int expectedPartner = -1;
  int actualPartner = -1;
  std::array<double, 3> expectedPosition{};
  std::array<double, 3> actualPosition{};
  std::array<double, 3> expectedVelocity{};
  std::array<double, 3> actualVelocity{};
};

inline bool writeInitialReadback(const std::string& path, const DiagnosticContext& context,
                                const kg_assoc::BoxLengths& box,
                                const std::vector<InitialParticle>& particles,
                                bool validMapping) {
  std::ostringstream out;
  evidenceHeader(out, context, box, 1.25);
  out << "# initial_device_readback_version=1 branch_age=0 ids=0_based "
      << "mapping_valid=" << validMapping << " molecule_is_host_metadata=1\n"
      << "# particle: expected_id actual_id molecule expected_type actual_type "
      << "expected_partner actual_partner expected_xyz actual_xyz expected_vxyz actual_vxyz\n";
  bool valid = validMapping && !particles.empty();
  double maxPositionError = 0.0;
  double maxVelocityError = 0.0;
  const std::array<double, 3> lengths{{box.x, box.y, box.z}};
  for (std::size_t id = 0; id < particles.size(); ++id) {
    const auto& p = particles[id];
    valid = valid && p.expectedId == int(id) && p.actualId == int(id) &&
            p.expectedType == p.actualType && p.expectedPartner == p.actualPartner;
    out << "particle " << p.expectedId << ' ' << p.actualId << ' ' << p.molecule
        << ' ' << p.expectedType << ' ' << p.actualType
        << ' ' << p.expectedPartner << ' ' << p.actualPartner;
    for (const auto& values : {p.expectedPosition, p.actualPosition,
                               p.expectedVelocity, p.actualVelocity}) {
      for (double value : values) {
        out << ' ' << value;
        valid = valid && std::isfinite(value);
      }
    }
    for (int axis = 0; axis < 3; ++axis) {
      const double delta = p.actualPosition[axis] - p.expectedPosition[axis];
      const double error = delta - lengths[axis] * std::nearbyint(delta / lengths[axis]);
      const double velocityError = p.actualVelocity[axis] - p.expectedVelocity[axis];
      valid = valid && error == 0.0 && velocityError == 0.0;
      maxPositionError = std::max(maxPositionError, std::abs(error));
      maxVelocityError = std::max(maxVelocityError, std::abs(velocityError));
    }
    out << '\n';
  }
  out << "# readback_pass=" << valid << " particles=" << particles.size()
      << " max_position_mic_error=" << maxPositionError
      << " max_velocity_error=" << maxVelocityError << '\n';
  writeExclusive(path, out.str());
  return valid;
}

}  // namespace kg_assoc_test
#endif
