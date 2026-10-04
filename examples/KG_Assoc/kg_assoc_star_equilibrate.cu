#include <uammd.cuh>

#include "Integrator/VerletNVE.cuh"
#include "Integrator/VerletNVT.cuh"
#include "../KG/kg_interactors.cuh"
#include "../KG/kg_lammps_io.cuh"
#include "../KG/kg_runtime.cuh"
#include "kg_assoc_star_topology.cuh"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cmath>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr double kDPDTemperature = 1.0;
constexpr double kDPDGamma = 4.5;
constexpr double kDPDCutOff = 1.0;
constexpr double kDPDInitialAmplitude = 25.0;

struct Parameters {
  std::string input;
  std::string output;
  std::string diagnostics;
  int arms = 0;
  int beadsPerArm = 0;
  double dt = 0.01;
  double temperature = 1.0;
  double friction = 0.5;
  double sigma = 1.0;
  double epsilon = 1.0;
  double feneK = 30.0;
  double feneR0 = 1.5;
  double skin = 0.3;
  int stage1Loops = 4;
  int stage1Steps = 100;
  int stage2Steps = 50000;
  int stage3Loops = 10;
  int stage3Steps = 100;
  int stage3bSteps = 20000;
  int stage3bDiagnosticEvery = 500;
  int stage4Steps = 1000000;
  int promotionSteps = 1000;
  int wcaRampSteps = 500;
  int conformationEvery = 1000;
  double dtDpd = 0.01;
  double dtWca = 0.01;
  std::uint64_t seed = 0;
  bool hasSeed = false;
  bool stage4EntryDiagnosticOnly = false;
  bool stage4PromotionTest = false;
  bool wcaRamp = false;
  bool initializeVelocities = false;
  bool selfTest = false;
};

struct StarDefinition {
  int molecule = 0;
  int center = -1;
  std::vector<int> atoms;
  std::vector<int> terminals;
};

struct ConformationSample {
  double meanRg2 = 0.0;
  double meanCenterTerminalR2 = 0.0;
  double minPermanentBond = std::numeric_limits<double>::infinity();
  double maxPermanentBond = 0.0;
};

struct DpdBundle {
  std::shared_ptr<uammd::Integrator> integrator;
  std::shared_ptr<uammd::Interactor> nonBonded;
  std::shared_ptr<uammd::Interactor> bonded;
};

struct Vec3 {
  double x = 0.0;
  double y = 0.0;
  double z = 0.0;
};

struct PairDistanceInfo {
  int first = -1;
  int second = -1;
  double distance = std::numeric_limits<double>::infinity();
};

struct TransitionDiagnostics {
  double temperature = 0.0;
  double maxSpeed = 0.0;
  double minPermanentBond = std::numeric_limits<double>::infinity();
  double maxPermanentBond = 0.0;
  int minBondFirst = -1;
  int minBondSecond = -1;
  int maxBondFirst = -1;
  int maxBondSecond = -1;
  PairDistanceInfo closestPair;
  PairDistanceInfo closestNonBondedPair;
  long long pairsBelow05 = 0;
  long long pairsBelow06 = 0;
  long long pairsBelow07 = 0;
  long long pairsBelow08 = 0;
  bool positionsFinite = true;
  bool velocitiesFinite = true;
};

std::string nextArgument(int& index, int argc, char** argv) {
  if (++index >= argc) {
    throw std::runtime_error("missing option value");
  }
  return argv[index];
}

void printHelp() {
  std::cout
      << "kg_assoc_star_equilibrate -i FILE -o FILE --arms A --narm N [options]\n"
      << "  --diagnostics FILE --conformation-every N --dt DT --dt-dpd DT --dt-wca DT\n"
      << "  --friction XI --sigma S --epsilon E --fene-k K --fene-r0 R0 --skin S\n"
      << "  --stage1-loops N --stage1-steps N --stage2-steps N\n"
      << "  --stage3-loops N --stage3-steps N --stage3b-steps N\n"
      << "  --stage3b-diagnostic-every N --stage4-steps N\n"
      << "  --conformation-every N --seed INTEGER --stage4-entry-diagnostic-only\n"
      << "  --stage4-promotion-test --promotion-steps N --wca-ramp\n"
      << "  --wca-ramp-steps N --init-velocities --self-test\n";
}

Parameters parseArguments(int argc, char** argv) {
  Parameters parameters;
  for (int index = 1; index < argc; ++index) {
    const std::string option = argv[index];
    if (option == "-i" || option == "--input") {
      parameters.input = nextArgument(index, argc, argv);
    } else if (option == "-o" || option == "--output") {
      parameters.output = nextArgument(index, argc, argv);
    } else if (option == "--diagnostics") {
      parameters.diagnostics = nextArgument(index, argc, argv);
    } else if (option == "--arms") {
      parameters.arms = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--narm") {
      parameters.beadsPerArm = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--dt") {
      parameters.dt = std::stod(nextArgument(index, argc, argv));
      parameters.dtDpd = parameters.dt;
      parameters.dtWca = parameters.dt;
    } else if (option == "--dt-dpd") {
      parameters.dtDpd = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--dt-wca") {
      parameters.dtWca = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--temperature") {
      parameters.temperature = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--friction") {
      parameters.friction = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--sigma") {
      parameters.sigma = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--epsilon") {
      parameters.epsilon = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--fene-k") {
      parameters.feneK = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--fene-r0") {
      parameters.feneR0 = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--skin") {
      parameters.skin = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--stage1-loops") {
      parameters.stage1Loops = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--stage1-steps") {
      parameters.stage1Steps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--stage2-steps") {
      parameters.stage2Steps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--stage3-loops") {
      parameters.stage3Loops = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--stage3-steps") {
      parameters.stage3Steps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--stage3b-steps") {
      parameters.stage3bSteps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--stage3b-diagnostic-every") {
      parameters.stage3bDiagnosticEvery = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--stage4-steps") {
      parameters.stage4Steps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--conformation-every") {
      parameters.conformationEvery = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--seed") {
      parameters.seed = std::stoull(nextArgument(index, argc, argv));
      parameters.hasSeed = true;
    } else if (option == "--stage4-entry-diagnostic-only") {
      parameters.stage4EntryDiagnosticOnly = true;
    } else if (option == "--stage4-promotion-test") {
      parameters.stage4PromotionTest = true;
    } else if (option == "--promotion-steps") {
      parameters.promotionSteps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--wca-ramp") {
      parameters.wcaRamp = true;
    } else if (option == "--wca-ramp-steps") {
      parameters.wcaRampSteps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--init-velocities") {
      parameters.initializeVelocities = true;
    } else if (option == "--self-test") {
      parameters.selfTest = true;
    } else if (option == "--help" || option == "-h") {
      printHelp();
      std::exit(0);
    } else {
      throw std::runtime_error("unknown argument: " + option);
    }
  }
  if (parameters.selfTest) {
    return parameters;
  }
  if (parameters.input.empty() || parameters.output.empty() || parameters.arms <= 0 ||
      parameters.beadsPerArm <= 0 || parameters.dtDpd <= 0.0 ||
      parameters.dtWca <= 0.0 ||
      parameters.temperature <= 0.0 || parameters.friction <= 0.0 ||
      parameters.sigma <= 0.0 || parameters.epsilon <= 0.0 || parameters.feneK <= 0.0 ||
      parameters.feneR0 <= 0.0 || parameters.skin < 0.0 || parameters.stage1Loops < 1 ||
      parameters.stage1Steps < 1 || parameters.stage2Steps < 1 ||
      parameters.stage3Loops < 1 || parameters.stage3Steps < 1 ||
      parameters.stage3bSteps < 0 || parameters.stage3bDiagnosticEvery < 1 ||
      parameters.stage4Steps < 1 || parameters.promotionSteps < 1 ||
      parameters.wcaRampSteps < 1 ||
      parameters.conformationEvery < 1 ||
      (parameters.stage4EntryDiagnosticOnly && parameters.stage4PromotionTest)) {
    throw std::runtime_error("invalid E1 parameters");
  }
  return parameters;
}

double stage1DisplacementLimit(int loop) {
  return std::exp((static_cast<double>(loop) - 4.0) * std::log(10.0));
}

double stage3Amplitude(int loop) {
  return 25.0 + (1000.0 - 25.0) *
                    std::exp((static_cast<double>(loop) - 10.0) * 0.75);
}

bool shouldSampleStage3b(int localStep, int totalSteps, int every) {
  return localStep == totalSteps || localStep % every == 0;
}

std::vector<std::vector<int>> buildAdjacency(const kg::LammpsData& data) {
  std::vector<std::vector<int>> adjacency(data.natoms);
  for (const auto& bond : data.bonds) {
    const int first = bond.first - 1;
    const int second = bond.second - 1;
    if (first < 0 || second < 0 || first >= data.natoms || second >= data.natoms) {
      throw std::runtime_error("permanent bond has invalid LAMMPS atom ID");
    }
    adjacency[first].push_back(second);
    adjacency[second].push_back(first);
  }
  return adjacency;
}

std::vector<StarDefinition> buildStarDefinitions(
    const kg::LammpsData& data,
    const std::vector<std::vector<int>>& adjacency,
    int arms) {
  std::map<int, StarDefinition> stars;
  for (int atom = 0; atom < data.natoms; ++atom) {
    if (data.type[atom] == 1 || data.type[atom] == 2) {
      stars[data.mol[atom]].molecule = data.mol[atom];
      stars[data.mol[atom]].atoms.push_back(atom);
    }
  }
  std::vector<StarDefinition> definitions;
  definitions.reserve(stars.size());
  for (auto& item : stars) {
    StarDefinition& star = item.second;
    for (const int atom : star.atoms) {
      if (static_cast<int>(adjacency[atom].size()) == arms) {
        star.center = atom;
      }
      if (adjacency[atom].size() == 1 && data.type[atom] == 2) {
        star.terminals.push_back(atom);
      }
    }
    if (star.center < 0 || static_cast<int>(star.terminals.size()) != arms) {
      throw std::runtime_error("S0 audit/topology definition disagreement");
    }
    definitions.push_back(std::move(star));
  }
  return definitions;
}

Vec3 minimumImage(Vec3 displacement, const Vec3& lengths) {
  displacement.x -= lengths.x * std::nearbyint(displacement.x / lengths.x);
  displacement.y -= lengths.y * std::nearbyint(displacement.y / lengths.y);
  displacement.z -= lengths.z * std::nearbyint(displacement.z / lengths.z);
  return displacement;
}

double norm2(const Vec3& value) {
  return value.x * value.x + value.y * value.y + value.z * value.z;
}

bool isFinite(const Vec3& value) {
  return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

TransitionDiagnostics analyzeTransition(
    const kg::LammpsData& data,
    const std::vector<std::pair<int, int>>& permanentBonds,
    const std::vector<Vec3>& positions,
    const std::vector<Vec3>& velocities,
    const Vec3& lengths) {
  if (static_cast<int>(positions.size()) != data.natoms ||
      static_cast<int>(velocities.size()) != data.natoms) {
    throw std::runtime_error("transition diagnostic particle-state size mismatch");
  }

  TransitionDiagnostics diagnostics;
  double velocitySquaredSum = 0.0;
  for (int atom = 0; atom < data.natoms; ++atom) {
    if (!isFinite(positions[atom])) {
      diagnostics.positionsFinite = false;
      throw std::runtime_error("transition diagnostic found non-finite position at atom ID " +
                               std::to_string(atom + 1));
    }
    if (!isFinite(velocities[atom])) {
      diagnostics.velocitiesFinite = false;
      throw std::runtime_error("transition diagnostic found non-finite velocity at atom ID " +
                               std::to_string(atom + 1));
    }
    const double speed2 = norm2(velocities[atom]);
    velocitySquaredSum += speed2;
    diagnostics.maxSpeed = std::max(diagnostics.maxSpeed, std::sqrt(speed2));
  }
  if (data.natoms > 0) {
    diagnostics.temperature = velocitySquaredSum / (3.0 * data.natoms);
  }

  std::set<std::pair<int, int>> bondedPairs;
  for (const auto& bond : permanentBonds) {
    const std::pair<int, int> ordered = std::minmax(bond.first, bond.second);
    bondedPairs.insert(ordered);
    const Vec3 displacement = minimumImage(
        {positions[ordered.second].x - positions[ordered.first].x,
         positions[ordered.second].y - positions[ordered.first].y,
         positions[ordered.second].z - positions[ordered.first].z}, lengths);
    const double distance = std::sqrt(norm2(displacement));
    if (distance < diagnostics.minPermanentBond) {
      diagnostics.minPermanentBond = distance;
      diagnostics.minBondFirst = ordered.first;
      diagnostics.minBondSecond = ordered.second;
    }
    if (distance > diagnostics.maxPermanentBond) {
      diagnostics.maxPermanentBond = distance;
      diagnostics.maxBondFirst = ordered.first;
      diagnostics.maxBondSecond = ordered.second;
    }
  }

  const auto inspectPair = [&](int first, int second) {
    const Vec3 displacement = minimumImage(
        {positions[second].x - positions[first].x,
         positions[second].y - positions[first].y,
         positions[second].z - positions[first].z}, lengths);
    const double distance = std::sqrt(norm2(displacement));
    if (distance < diagnostics.closestPair.distance) {
      diagnostics.closestPair = {first, second, distance};
    }
    if (distance < 0.5) {
      ++diagnostics.pairsBelow05;
    }
    if (distance < 0.6) {
      ++diagnostics.pairsBelow06;
    }
    if (distance < 0.7) {
      ++diagnostics.pairsBelow07;
    }
    if (distance < 0.8) {
      ++diagnostics.pairsBelow08;
    }
    if (bondedPairs.count({first, second}) == 0 &&
        distance < diagnostics.closestNonBondedPair.distance) {
      diagnostics.closestNonBondedPair = {first, second, distance};
    }
  };

  constexpr double kPairDiagnosticCutoff = 0.8;
  const int cellsX = std::max(1, static_cast<int>(lengths.x / kPairDiagnosticCutoff));
  const int cellsY = std::max(1, static_cast<int>(lengths.y / kPairDiagnosticCutoff));
  const int cellsZ = std::max(1, static_cast<int>(lengths.z / kPairDiagnosticCutoff));
  const auto cellCoordinate = [](double coordinate, double length, int cells) {
    const double cellLength = length / cells;
    const int cell = static_cast<int>(std::floor((coordinate + 0.5 * length) /
                                                 cellLength));
    return std::max(0, std::min(cells - 1, cell));
  };
  const auto cellKey = [cellsX, cellsY](int x, int y, int z) {
    return x + cellsX * (y + cellsY * z);
  };
  std::vector<std::vector<int>> cells(cellsX * cellsY * cellsZ);
  std::vector<int> particleCellX(data.natoms);
  std::vector<int> particleCellY(data.natoms);
  std::vector<int> particleCellZ(data.natoms);
  for (int atom = 0; atom < data.natoms; ++atom) {
    particleCellX[atom] = cellCoordinate(positions[atom].x, lengths.x, cellsX);
    particleCellY[atom] = cellCoordinate(positions[atom].y, lengths.y, cellsY);
    particleCellZ[atom] = cellCoordinate(positions[atom].z, lengths.z, cellsZ);
    cells[cellKey(particleCellX[atom], particleCellY[atom], particleCellZ[atom])]
        .push_back(atom);
  }
  std::set<std::pair<int, int>> inspectedPairs;
  for (int first = 0; first < data.natoms; ++first) {
    for (int dx = -1; dx <= 1; ++dx) {
      for (int dy = -1; dy <= 1; ++dy) {
        for (int dz = -1; dz <= 1; ++dz) {
          const int x = (particleCellX[first] + dx + cellsX) % cellsX;
          const int y = (particleCellY[first] + dy + cellsY) % cellsY;
          const int z = (particleCellZ[first] + dz + cellsZ) % cellsZ;
          for (const int second : cells[cellKey(x, y, z)]) {
            if (first == second) {
              continue;
            }
            const std::pair<int, int> pair = std::minmax(first, second);
            if (!inspectedPairs.insert(pair).second) {
              continue;
            }
            inspectPair(pair.first, pair.second);
          }
        }
      }
    }
  }
  if (diagnostics.pairsBelow08 == 0) {
    // ponytail: exact rare fallback; use a hierarchical nearest-neighbor search
    // only if production conditions routinely have no pair below the cutoff.
    for (int first = 0; first < data.natoms; ++first) {
      for (int second = first + 1; second < data.natoms; ++second) {
        inspectPair(first, second);
      }
    }
  }
  return diagnostics;
}

void appendPairDescription(std::ostringstream& output,
                           const std::string& name,
                           const PairDistanceInfo& pair,
                           const kg::LammpsData& data) {
  output << ' ' << name << "_distance=" << pair.distance;
  if (pair.first < 0 || pair.second < 0) {
    output << ' ' << name << "_ids=none";
    return;
  }
  output << ' ' << name << "_ids=" << pair.first + 1 << ',' << pair.second + 1
         << ' ' << name << "_types=" << data.type[pair.first] << ','
         << data.type[pair.second] << ' ' << name << "_molecules="
         << data.mol[pair.first] << ',' << data.mol[pair.second];
}

std::string formatTransitionDiagnostics(const std::string& label,
                                        long long step,
                                        int stage3Loop,
                                        int stage3bLocalStep,
                                        double dpdAmplitude,
                                        const TransitionDiagnostics& diagnostics,
                                        const kg::LammpsData& data,
                                        double wcaEpsilon) {
  std::ostringstream output;
  output << std::setprecision(12) << "[E1 transition] label=" << label
         << " step=" << step << " stage3_loop=" << stage3Loop
         << " dpd_amplitude=" << dpdAmplitude
         << (wcaEpsilon >= 0.0 ? " epsilon=" + std::to_string(wcaEpsilon) : "")
         << " temperature=" << diagnostics.temperature
         << " max_speed=" << diagnostics.maxSpeed
         << " min_permanent_bond=" << diagnostics.minPermanentBond
         << " max_permanent_bond=" << diagnostics.maxPermanentBond;
  if (stage3bLocalStep >= 0) {
    output << " stage3b_local_step=" << stage3bLocalStep;
  }
  if (diagnostics.maxBondFirst >= 0) {
    output << " max_permanent_bond_ids=" << diagnostics.maxBondFirst + 1 << ','
           << diagnostics.maxBondSecond + 1;
  }
  if (diagnostics.minBondFirst >= 0) {
    output << " min_permanent_bond_ids=" << diagnostics.minBondFirst + 1 << ','
           << diagnostics.minBondSecond + 1;
  }
  appendPairDescription(output, "closest_pair", diagnostics.closestPair, data);
  appendPairDescription(output, "closest_nonbonded_pair",
                        diagnostics.closestNonBondedPair, data);
  output << " pairs_below_0.5=" << diagnostics.pairsBelow05
         << " pairs_below_0.6=" << diagnostics.pairsBelow06
         << " pairs_below_0.7=" << diagnostics.pairsBelow07
         << " pairs_below_0.8=" << diagnostics.pairsBelow08
         << " pair_counts_include_permanent_bonds=true"
         << " positions_finite=" << (diagnostics.positionsFinite ? "true" : "false")
         << " velocities_finite=" << (diagnostics.velocitiesFinite ? "true" : "false");
  return output.str();
}

void appendTransitionDiagnostics(
    const std::string& label,
    long long step,
    int stage3Loop,
    int stage3bLocalStep,
    double dpdAmplitude,
    std::ofstream& output,
    std::shared_ptr<uammd::ParticleData> particles,
    const kg::LammpsData& data,
    const std::vector<std::pair<int, int>>& permanentBonds,
    const Vec3& lengths,
    double feneR0,
    double wcaEpsilon = -1.0) {
  auto positionsByStorage = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto velocitiesByStorage = particles->getVel(uammd::access::cpu, uammd::access::read);
  auto idToIndex = particles->getIdOrderedIndices(uammd::access::cpu);
  std::vector<Vec3> positions(data.natoms);
  std::vector<Vec3> velocities(data.natoms);
  for (int id = 0; id < data.natoms; ++id) {
    const int storage = idToIndex[id];
    const uammd::real3 position = uammd::make_real3(positionsByStorage[storage]);
    positions[id] = {position.x, position.y, position.z};
    const uammd::real3 velocity = velocitiesByStorage[storage];
    velocities[id] = {velocity.x, velocity.y, velocity.z};
  }
  const TransitionDiagnostics diagnostics = analyzeTransition(
      data, permanentBonds, positions, velocities, lengths);
  const std::string message = formatTransitionDiagnostics(
      label, step, stage3Loop, stage3bLocalStep, dpdAmplitude, diagnostics, data,
      wcaEpsilon);
  uammd::System::log<uammd::System::MESSAGE>("%s", message.c_str());
  output << "# " << message << '\n';
  output.flush();
  if (diagnostics.maxPermanentBond >= feneR0) {
    throw std::runtime_error("transition diagnostic found permanent FENE bond at or above R0: " +
                             std::to_string(diagnostics.maxBondFirst + 1) + "--" +
                             std::to_string(diagnostics.maxBondSecond + 1) + " r=" +
                             std::to_string(diagnostics.maxPermanentBond));
  }
}

std::vector<Vec3> unwrapStar(const StarDefinition& star,
                             const std::vector<std::vector<int>>& adjacency,
                             const std::vector<Vec3>& positions,
                             const Vec3& lengths) {
  std::vector<Vec3> unwrapped(positions.size());
  std::vector<bool> visited(positions.size(), false);
  std::queue<int> pending;
  unwrapped[star.center] = positions[star.center];
  visited[star.center] = true;
  pending.push(star.center);
  while (!pending.empty()) {
    const int atom = pending.front();
    pending.pop();
    for (const int neighbour : adjacency[atom]) {
      if (visited[neighbour]) {
        continue;
      }
      const Vec3 displacement = minimumImage(
          {positions[neighbour].x - positions[atom].x,
           positions[neighbour].y - positions[atom].y,
           positions[neighbour].z - positions[atom].z}, lengths);
      unwrapped[neighbour] = {unwrapped[atom].x + displacement.x,
                               unwrapped[atom].y + displacement.y,
                               unwrapped[atom].z + displacement.z};
      visited[neighbour] = true;
      pending.push(neighbour);
    }
  }
  for (const int atom : star.atoms) {
    if (!visited[atom]) {
      throw std::runtime_error("star graph disconnected while unwrapping");
    }
  }
  return unwrapped;
}

ConformationSample computeConformationSample(
    const std::vector<StarDefinition>& stars,
    const std::vector<std::vector<int>>& adjacency,
    const std::vector<std::pair<int, int>>& bonds,
    const std::vector<Vec3>& positions,
    const Vec3& lengths) {
  ConformationSample sample;
  int terminalCount = 0;
  for (const StarDefinition& star : stars) {
    const std::vector<Vec3> unwrapped = unwrapStar(star, adjacency, positions, lengths);
    Vec3 centerOfMass;
    for (const int atom : star.atoms) {
      centerOfMass.x += unwrapped[atom].x;
      centerOfMass.y += unwrapped[atom].y;
      centerOfMass.z += unwrapped[atom].z;
    }
    const double inverseCount = 1.0 / static_cast<double>(star.atoms.size());
    centerOfMass.x *= inverseCount;
    centerOfMass.y *= inverseCount;
    centerOfMass.z *= inverseCount;
    double rg2 = 0.0;
    for (const int atom : star.atoms) {
      rg2 += norm2({unwrapped[atom].x - centerOfMass.x,
                    unwrapped[atom].y - centerOfMass.y,
                    unwrapped[atom].z - centerOfMass.z});
    }
    sample.meanRg2 += rg2 * inverseCount;
    for (const int terminal : star.terminals) {
      sample.meanCenterTerminalR2 += norm2(
          {unwrapped[terminal].x - unwrapped[star.center].x,
           unwrapped[terminal].y - unwrapped[star.center].y,
           unwrapped[terminal].z - unwrapped[star.center].z});
      ++terminalCount;
    }
  }
  sample.meanRg2 /= static_cast<double>(stars.size());
  sample.meanCenterTerminalR2 /= static_cast<double>(terminalCount);
  for (const auto& bond : bonds) {
    const Vec3 displacement = minimumImage(
        {positions[bond.second].x - positions[bond.first].x,
         positions[bond.second].y - positions[bond.first].y,
         positions[bond.second].z - positions[bond.first].z}, lengths);
    const double distance = std::sqrt(norm2(displacement));
    sample.minPermanentBond = std::min(sample.minPermanentBond, distance);
    sample.maxPermanentBond = std::max(sample.maxPermanentBond, distance);
  }
  return sample;
}

ConformationSample sampleConformation(
    std::shared_ptr<uammd::ParticleData> particles,
    const std::vector<StarDefinition>& stars,
    const std::vector<std::vector<int>>& adjacency,
    const std::vector<std::pair<int, int>>& bonds,
    const Vec3& lengths) {
  auto positionsByStorage = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto idToIndex = particles->getIdOrderedIndices(uammd::access::cpu);
  std::vector<Vec3> positions(particles->getNumParticles());
  for (int id = 0; id < particles->getNumParticles(); ++id) {
    const uammd::real3 position = uammd::make_real3(positionsByStorage[idToIndex[id]]);
    positions[id] = {static_cast<double>(position.x), static_cast<double>(position.y),
                     static_cast<double>(position.z)};
  }
  return computeConformationSample(stars, adjacency, bonds, positions, lengths);
}

std::string diagnosticsHeader() {
  return "# step time e_bonded e_nonbonded e_kinetic e_total temperature pressure "
         "mean_rg2 mean_center_terminal_r2 min_permanent_bond max_permanent_bond";
}

std::string formatDiagnosticsRow(long long step,
                                 double time,
                                 const kg::ThermoSnapshot& thermo,
                                 const ConformationSample& conformation) {
  std::ostringstream output;
  output << std::setprecision(12) << step << ' ' << time << ' '
         << thermo.bondedEnergy << ' ' << thermo.nonBondedEnergy << ' '
         << thermo.kineticEnergy << ' ' << thermo.totalEnergy << ' '
         << thermo.temperature << ' ' << thermo.pressure << ' '
         << conformation.meanRg2 << ' ' << conformation.meanCenterTerminalR2 << ' '
         << conformation.minPermanentBond << ' '
         << conformation.maxPermanentBond;
  return output.str();
}

DpdBundle makeDpdSegment(std::shared_ptr<uammd::ParticleData> particles,
                         const kg::SimulationBox& box,
                         const std::string& bondData,
                         double dt,
                         double amplitude) {
  auto dpd = kg::createDPDInteractor(particles, box.box, kDPDTemperature, kDPDGamma,
                                     amplitude, kDPDCutOff, dt);
  auto fene = kg::createFENEInteractor(particles, box.box, bondData);
  uammd::VerletNVE::Parameters integratorParameters;
  integratorParameters.dt = static_cast<uammd::real>(dt);
  integratorParameters.initVelocities = false;
  auto integrator = std::make_shared<uammd::VerletNVE>(particles, integratorParameters);
  integrator->addInteractor(dpd);
  integrator->addInteractor(fene);
  return {integrator, dpd, fene};
}

void checkStage4Cuda(const std::string& operation) {
  const cudaError_t synchronizeError = cudaDeviceSynchronize();
  if (synchronizeError != cudaSuccess) {
    throw std::runtime_error("E1_STAGE4_DIAG FAIL after " + operation +
                             ": cudaDeviceSynchronize: " +
                             cudaGetErrorString(synchronizeError));
  }
  const cudaError_t lastError = cudaGetLastError();
  if (lastError != cudaSuccess) {
    throw std::runtime_error("E1_STAGE4_DIAG FAIL after " + operation +
                             ": cudaGetLastError: " + cudaGetErrorString(lastError));
  }
}

template <class Function>
auto stage4Value(const std::string& operation, const Function& function)
    -> decltype(function()) {
  try {
    auto value = function();
    checkStage4Cuda(operation);
    return value;
  } catch (const std::exception& error) {
    const std::string prefix = "E1_STAGE4_DIAG FAIL after " + operation + ": ";
    if (std::string(error.what()).find(prefix) == 0) {
      throw;
    }
    throw std::runtime_error(prefix + error.what());
  }
}

template <class Function>
void stage4Void(const std::string& operation, const Function& function) {
  try {
    function();
    checkStage4Cuda(operation);
  } catch (const std::exception& error) {
    const std::string prefix = "E1_STAGE4_DIAG FAIL after " + operation + ": ";
    if (std::string(error.what()).find(prefix) == 0) {
      throw;
    }
    throw std::runtime_error(prefix + error.what());
  }
}

struct CpuWcaReference {
  double energy = 0.0;
  long long pairsInsideCutoff = 0;
  bool energyFinite = true;
};

CpuWcaReference computeCpuWcaReference(const std::vector<Vec3>& positions,
                                       const Vec3& lengths,
                                       double epsilon,
                                       double sigma) {
  const double cutoff = std::pow(2.0, 1.0 / 6.0) * sigma;
  const double cutoff2 = cutoff * cutoff;
  const int cellsX = std::max(1, static_cast<int>(lengths.x / cutoff));
  const int cellsY = std::max(1, static_cast<int>(lengths.y / cutoff));
  const int cellsZ = std::max(1, static_cast<int>(lengths.z / cutoff));
  const auto coordinateToCell = [](double coordinate, double length, int cells) {
    const int cell = static_cast<int>(std::floor(
        (coordinate + 0.5 * length) / (length / static_cast<double>(cells))));
    return std::max(0, std::min(cells - 1, cell));
  };
  const auto cellKey = [cellsX, cellsY](int x, int y, int z) {
    return x + cellsX * (y + cellsY * z);
  };
  std::vector<std::vector<int>> cells(cellsX * cellsY * cellsZ);
  std::vector<int> cellX(positions.size());
  std::vector<int> cellY(positions.size());
  std::vector<int> cellZ(positions.size());
  for (size_t atom = 0; atom < positions.size(); ++atom) {
    cellX[atom] = coordinateToCell(positions[atom].x, lengths.x, cellsX);
    cellY[atom] = coordinateToCell(positions[atom].y, lengths.y, cellsY);
    cellZ[atom] = coordinateToCell(positions[atom].z, lengths.z, cellsZ);
    cells[cellKey(cellX[atom], cellY[atom], cellZ[atom])].push_back(atom);
  }

  CpuWcaReference reference;
  std::set<std::pair<int, int>> visitedPairs;
  for (int first = 0; first < static_cast<int>(positions.size()); ++first) {
    for (int dx = -1; dx <= 1; ++dx) {
      for (int dy = -1; dy <= 1; ++dy) {
        for (int dz = -1; dz <= 1; ++dz) {
          const int x = (cellX[first] + dx + cellsX) % cellsX;
          const int y = (cellY[first] + dy + cellsY) % cellsY;
          const int z = (cellZ[first] + dz + cellsZ) % cellsZ;
          for (const int second : cells[cellKey(x, y, z)]) {
            if (first == second) {
              continue;
            }
            const std::pair<int, int> pair = std::minmax(first, second);
            if (!visitedPairs.insert(pair).second) {
              continue;
            }
            const Vec3 displacement = minimumImage(
                {positions[pair.second].x - positions[pair.first].x,
                 positions[pair.second].y - positions[pair.first].y,
                 positions[pair.second].z - positions[pair.first].z}, lengths);
            const double r2 = norm2(displacement);
            if (r2 <= 0.0 || r2 >= cutoff2) {
              continue;
            }
            const double inverseR2 = sigma * sigma / r2;
            const double inverseR6 = inverseR2 * inverseR2 * inverseR2;
            reference.energy += 4.0 * epsilon * inverseR6 * (inverseR6 - 1.0) +
                                epsilon;
            ++reference.pairsInsideCutoff;
          }
        }
      }
    }
  }
  reference.energyFinite = std::isfinite(reference.energy);
  return reference;
}

void appendCpuWcaReference(std::ofstream& output,
                           const CpuWcaReference& reference) {
  std::ostringstream message;
  message << std::setprecision(12) << "E1_STAGE4_DIAG cpu_wca_energy="
          << reference.energy << " cpu_wca_pairs_inside_cutoff="
          << reference.pairsInsideCutoff << " cpu_wca_energy_finite="
          << (reference.energyFinite ? "true" : "false");
  uammd::System::log<uammd::System::MESSAGE>("%s", message.str().c_str());
  output << "# " << message.str() << '\n';
  output.flush();
}

void limitDisplacements(std::shared_ptr<uammd::ParticleData> particles,
                        const kg::SimulationBox& box,
                        const std::vector<uammd::real4>& previous,
                        double maximum,
                        double dt) {
  auto positions = particles->getPos(uammd::access::cpu, uammd::access::write);
  auto velocities = particles->getVel(uammd::access::cpu, uammd::access::write);
  const uammd::real maxDisplacement = static_cast<uammd::real>(maximum);
  for (int index = 0; index < particles->getNumParticles(); ++index) {
    const uammd::real3 oldPosition = uammd::make_real3(previous[index]);
    const uammd::real3 displacement = box.box.apply_pbc(
        uammd::make_real3(positions[index]) - oldPosition);
    const uammd::real distance2 = displacement.x * displacement.x +
                                  displacement.y * displacement.y +
                                  displacement.z * displacement.z;
    if (distance2 <= maxDisplacement * maxDisplacement || distance2 <= 0.0) {
      continue;
    }
    const uammd::real scale = maxDisplacement / std::sqrt(distance2);
    const uammd::real3 limited = displacement * scale;
    positions[index] = uammd::make_real4(box.box.apply_pbc(oldPosition + limited),
                                         positions[index].w);
    velocities[index] = limited * static_cast<uammd::real>(1.0 / dt);
  }
}

std::vector<uammd::real4> copyPositions(std::shared_ptr<uammd::ParticleData> particles) {
  std::vector<uammd::real4> positions(particles->getNumParticles());
  auto source = particles->getPos(uammd::access::cpu, uammd::access::read);
  for (int index = 0; index < particles->getNumParticles(); ++index) {
    positions[index] = source[index];
  }
  return positions;
}

struct ParticleStateSnapshot {
  std::vector<Vec3> positions;
  std::vector<Vec3> velocities;
};

ParticleStateSnapshot copyParticleState(
    std::shared_ptr<uammd::ParticleData> particles,
    int numberParticles) {
  auto positionsByStorage = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto velocitiesByStorage = particles->getVel(uammd::access::cpu, uammd::access::read);
  auto idToIndex = particles->getIdOrderedIndices(uammd::access::cpu);
  ParticleStateSnapshot snapshot;
  snapshot.positions.resize(numberParticles);
  snapshot.velocities.resize(numberParticles);
  for (int id = 0; id < numberParticles; ++id) {
    const int storage = idToIndex[id];
    const uammd::real3 position = uammd::make_real3(positionsByStorage[storage]);
    snapshot.positions[id] = {position.x, position.y, position.z};
    const uammd::real3 velocity = velocitiesByStorage[storage];
    snapshot.velocities[id] = {velocity.x, velocity.y, velocity.z};
  }
  return snapshot;
}

kg::ThermoSnapshot computeStage4Thermo(
    const std::string& label,
    std::shared_ptr<uammd::Integrator> integrator,
    std::shared_ptr<uammd::ParticleData> particles,
    std::shared_ptr<uammd::Interactor> wca,
    std::shared_ptr<uammd::Interactor> fene,
    const kg::LammpsData& data,
    const kg::SimulationBox& box,
    const Parameters& parameters) {
  kg::ThermoSnapshot thermo;
  thermo.kineticEnergy = stage4Value(label + " kinetic energy", [&]() {
    return kg::detail::sumKineticEnergy(integrator, particles);
  });
  thermo.nonBondedEnergy = stage4Value(label + " WCA energy", [&]() {
    return kg::detail::sumInteractorEnergy(wca, particles);
  });
  thermo.bondedEnergy = stage4Value(label + " permanent FENE energy", [&]() {
    return kg::detail::sumInteractorEnergy(fene, particles);
  });
  const kg::BondedWCACorrection correction = stage4Value(
      label + " bonded WCA correction", [&]() {
        return kg::computeBondedWCACorrection(data, particles, box,
                                              parameters.epsilon, parameters.sigma);
      });
  thermo.bondedEnergy += correction.energy;
  thermo.nonBondedEnergy -= correction.energy;
  thermo.totalEnergy = thermo.kineticEnergy + thermo.nonBondedEnergy +
                       thermo.bondedEnergy;
  if (data.natoms > 0) {
    thermo.temperature = 2.0 * thermo.kineticEnergy / (3.0 * data.natoms);
  }
  const double volume = box.box.getVolume();
  if (volume > 0.0) {
    const double nonBondedVirial = stage4Value(label + " WCA virial", [&]() {
      return kg::detail::sumInteractorVirial(wca, particles);
    });
    const double bondedVirial = stage4Value(label + " permanent FENE virial", [&]() {
      return kg::detail::sumInteractorVirial(fene, particles);
    });
    thermo.pressure = 2.0 * thermo.kineticEnergy / (3.0 * volume) -
                      nonBondedVirial / (6.0 * volume) +
                      bondedVirial / (6.0 * volume);
  }
  return thermo;
}

std::string formatStage4Field(const std::string& label,
                              const std::string& name,
                              double value) {
  std::ostringstream message;
  message << std::setprecision(12) << "E1_STAGE4_DIAG label=" << label << ' '
          << name << '=' << value << " isfinite=" << (std::isfinite(value) ? "true" : "false");
  return message.str();
}

void appendStage4Field(std::ofstream& output,
                       const std::string& label,
                       const std::string& name,
                       double value) {
  const std::string message = formatStage4Field(label, name, value);
  uammd::System::log<uammd::System::MESSAGE>("%s", message.c_str());
  output << "# " << message << '\n';
}

std::string firstNonFiniteStage4Field(const kg::ThermoSnapshot& thermo,
                                      const ConformationSample& conformation) {
  if (!std::isfinite(thermo.bondedEnergy)) {
    return "bondedEnergy";
  }
  if (!std::isfinite(thermo.nonBondedEnergy)) {
    return "nonBondedEnergy";
  }
  if (!std::isfinite(thermo.kineticEnergy)) {
    return "kineticEnergy";
  }
  if (!std::isfinite(thermo.totalEnergy)) {
    return "totalEnergy";
  }
  if (!std::isfinite(thermo.temperature)) {
    return "temperature";
  }
  if (!std::isfinite(thermo.pressure)) {
    return "pressure";
  }
  if (!std::isfinite(conformation.meanRg2)) {
    return "meanRg2";
  }
  if (!std::isfinite(conformation.meanCenterTerminalR2)) {
    return "meanCenterTerminalR2";
  }
  if (!std::isfinite(conformation.minPermanentBond)) {
    return "minPermanentBond";
  }
  if (!std::isfinite(conformation.maxPermanentBond)) {
    return "maxPermanentBond";
  }
  return "";
}

std::string firstNonFiniteThermoField(const kg::ThermoSnapshot& thermo) {
  if (!std::isfinite(thermo.bondedEnergy)) {
    return "bondedEnergy";
  }
  if (!std::isfinite(thermo.nonBondedEnergy)) {
    return "nonBondedEnergy";
  }
  if (!std::isfinite(thermo.kineticEnergy)) {
    return "kineticEnergy";
  }
  if (!std::isfinite(thermo.totalEnergy)) {
    return "totalEnergy";
  }
  if (!std::isfinite(thermo.temperature)) {
    return "temperature";
  }
  if (!std::isfinite(thermo.pressure)) {
    return "pressure";
  }
  return "";
}

void validatePromotionState(const std::string& label,
                            const ParticleStateSnapshot& state,
                            const std::vector<std::pair<int, int>>& bonds,
                            const Vec3& lengths,
                            double feneR0,
                            const std::string& failurePrefix = "E1_PROMOTION") {
  for (size_t atom = 0; atom < state.positions.size(); ++atom) {
    if (!isFinite(state.positions[atom])) {
      throw std::runtime_error(failurePrefix + " FAIL after " + label +
                               ": non-finite position at atom ID " +
                               std::to_string(atom + 1));
    }
    if (!isFinite(state.velocities[atom])) {
      throw std::runtime_error(failurePrefix + " FAIL after " + label +
                               ": non-finite velocity at atom ID " +
                               std::to_string(atom + 1));
    }
  }
  double minBond = std::numeric_limits<double>::infinity();
  int minBondFirst = -1;
  int minBondSecond = -1;
  double maxBond = 0.0;
  int maxBondFirst = -1;
  int maxBondSecond = -1;
  for (const auto& bond : bonds) {
    const Vec3 displacement = minimumImage(
        {state.positions[bond.second].x - state.positions[bond.first].x,
         state.positions[bond.second].y - state.positions[bond.first].y,
         state.positions[bond.second].z - state.positions[bond.first].z}, lengths);
    const double distance = std::sqrt(norm2(displacement));
    if (distance < minBond) {
      minBond = distance;
      minBondFirst = bond.first;
      minBondSecond = bond.second;
    }
    if (distance > maxBond) {
      maxBond = distance;
      maxBondFirst = bond.first;
      maxBondSecond = bond.second;
    }
  }
  if (maxBond >= feneR0) {
    throw std::runtime_error(failurePrefix + " FAIL after " + label +
                             ": permanent bond at or above R0; min=" +
                             std::to_string(minBond) + " ids=" +
                             std::to_string(minBondFirst + 1) + "," +
                             std::to_string(minBondSecond + 1) + " max=" +
                             std::to_string(maxBond) + " ids=" +
                             std::to_string(maxBondFirst + 1) + "," +
                             std::to_string(maxBondSecond + 1));
  }
}

std::vector<double> promotionTimesteps() {
  return {0.002, 0.005, 0.01};
}

std::vector<double> wcaRampEpsilons() {
  return {0.01, 0.03, 0.10, 0.30, 1.00};
}

std::vector<double> promotionTimestepsAfterWcaRamp() {
  return {0.005, 0.01};
}

int wcaRampStepCount(int stepsPerEpsilon) {
  return static_cast<int>(wcaRampEpsilons().size()) * stepsPerEpsilon;
}

std::string formatTimestepLabel(double timestep) {
  std::ostringstream output;
  output << std::fixed << std::setprecision(3) << timestep;
  return output.str();
}

void appendStage4Sample(
    const std::string& label,
    long long step,
    double time,
    std::ofstream& output,
    std::shared_ptr<uammd::Integrator> integrator,
    std::shared_ptr<uammd::ParticleData> particles,
    std::shared_ptr<uammd::Interactor> wca,
    std::shared_ptr<uammd::Interactor> fene,
    const kg::LammpsData& data,
    const kg::SimulationBox& box,
    const Parameters& parameters,
    const std::vector<StarDefinition>& stars,
    const std::vector<std::vector<int>>& adjacency,
    const std::vector<std::pair<int, int>>& bonds,
    const Vec3& lengths) {
  const kg::ThermoSnapshot thermo = computeStage4Thermo(
      label, integrator, particles, wca, fene, data, box, parameters);
  const ConformationSample conformation = stage4Value(label + " conformation sample", [&]() {
    return sampleConformation(particles, stars, adjacency, bonds, lengths);
  });
  appendStage4Field(output, label, "bondedEnergy", thermo.bondedEnergy);
  appendStage4Field(output, label, "nonBondedEnergy", thermo.nonBondedEnergy);
  appendStage4Field(output, label, "kineticEnergy", thermo.kineticEnergy);
  appendStage4Field(output, label, "totalEnergy", thermo.totalEnergy);
  appendStage4Field(output, label, "temperature", thermo.temperature);
  appendStage4Field(output, label, "pressure", thermo.pressure);
  appendStage4Field(output, label, "meanRg2", conformation.meanRg2);
  appendStage4Field(output, label, "meanCenterTerminalR2",
                    conformation.meanCenterTerminalR2);
  appendStage4Field(output, label, "maxPermanentBond", conformation.maxPermanentBond);
  const std::string nonFiniteField = firstNonFiniteStage4Field(thermo, conformation);
  if (!nonFiniteField.empty()) {
    throw std::runtime_error("E1_STAGE4_DIAG FAIL after " + label +
                             " fields: non-finite " + nonFiniteField);
  }
  output << formatDiagnosticsRow(step, time, thermo, conformation) << '\n';
  output.flush();
}

void logThermo(long long step,
               std::shared_ptr<uammd::Integrator> integrator,
               std::shared_ptr<uammd::ParticleData> particles,
               std::shared_ptr<uammd::Interactor> nonBonded,
               std::shared_ptr<uammd::Interactor> bonded,
               const kg::LammpsData& data,
               const kg::SimulationBox& box,
               const Parameters& parameters,
               bool useWcaThermo) {
  kg::ThermoSnapshot thermo;
  if (useWcaThermo) {
    thermo = kg::computeThermoSnapshot(
        integrator, particles, nonBonded, bonded, data, box, parameters.epsilon,
        parameters.sigma, box.box.getVolume(), data.natoms);
  } else {
    thermo.kineticEnergy = kg::detail::sumKineticEnergy(integrator, particles);
    thermo.nonBondedEnergy = kg::detail::sumInteractorEnergy(nonBonded, particles);
    thermo.bondedEnergy = kg::detail::sumInteractorEnergy(bonded, particles);
    thermo.totalEnergy = thermo.kineticEnergy + thermo.nonBondedEnergy +
                         thermo.bondedEnergy;
    if (data.natoms > 0) {
      thermo.temperature = 2.0 * thermo.kineticEnergy / (3.0 * data.natoms);
    }
    const double volume = box.box.getVolume();
    if (volume > 0.0) {
      const double nonBondedVirial = kg::detail::sumInteractorVirial(nonBonded, particles);
      const double bondedVirial = kg::detail::sumInteractorVirial(bonded, particles);
      thermo.pressure = 2.0 * thermo.kineticEnergy / (3.0 * volume) -
                        nonBondedVirial / (6.0 * volume) +
                        bondedVirial / (6.0 * volume);
    }
  }
  if (!std::isfinite(thermo.bondedEnergy)) {
    throw std::runtime_error("non-finite permanent-FENE energy");
  }
  const std::string row = kg::formatThermoRow(static_cast<int>(step), thermo);
  uammd::System::log<uammd::System::MESSAGE>("[E1] %s", row.c_str());
}

void expectNear(const std::string& label, double observed, double expected) {
  if (std::abs(observed - expected) > 1.0e-10) {
    throw std::runtime_error(label + " self-test failed");
  }
}

template <class Function>
void expectReject(const std::string& label, const Function& function) {
  try {
    function();
  } catch (const std::runtime_error&) {
    return;
  }
  throw std::runtime_error(label + " self-test accepted invalid state");
}

void runSelfTest() {
  kg::LammpsData data;
  data.natoms = 3;
  data.nbonds = 2;
  data.xlo = -5.0;
  data.xhi = 5.0;
  data.ylo = -5.0;
  data.yhi = 5.0;
  data.zlo = -5.0;
  data.zhi = 5.0;
  data.type = {2, 1, 2};
  data.mol = {7, 7, 7};
  data.bonds = {{1, 2}, {2, 3}};
  (void)kg_assoc::auditStarTopology(data, {2, 1});
  const std::vector<std::vector<int>> adjacency = buildAdjacency(data);
  const std::vector<StarDefinition> stars = buildStarDefinitions(data, adjacency, 2);
  if (stars.size() != 1 || stars[0].center != 1 ||
      stars[0].terminals != std::vector<int>({0, 2})) {
    throw std::runtime_error("center or terminal identification self-test failed");
  }
  const std::vector<std::pair<int, int>> bonds = {{0, 1}, {1, 2}};
  const Vec3 lengths{10.0, 10.0, 10.0};
  ConformationSample sample = computeConformationSample(
      stars, adjacency, bonds, {{-1.0, 0.0, 0.0}, {0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}},
      lengths);
  expectNear("Rg2", sample.meanRg2, 2.0 / 3.0);
  expectNear("center-terminal r2", sample.meanCenterTerminalR2, 1.0);
  expectNear("minimum permanent bond", sample.minPermanentBond, 1.0);
  expectNear("maximum permanent bond", sample.maxPermanentBond, 1.0);
  sample = computeConformationSample(
      stars, adjacency, bonds, {{-4.2, 0.0, 0.0}, {4.8, 0.0, 0.0}, {3.8, 0.0, 0.0}},
      lengths);
  expectNear("PBC-safe Rg2", sample.meanRg2, 2.0 / 3.0);
  expectNear("PBC-safe center-terminal r2", sample.meanCenterTerminalR2, 1.0);
  expectNear("PBC-safe minimum permanent bond", sample.minPermanentBond, 1.0);

  kg::LammpsData transitionData;
  transitionData.natoms = 4;
  transitionData.type = {1, 2, 3, 1};
  transitionData.mol = {10, 10, 99, 11};
  const std::vector<std::pair<int, int>> transitionBonds = {{0, 1}};
  const std::vector<Vec3> transitionPositions = {
      {4.9, 0.0, 0.0}, {-4.9, 0.0, 0.0}, {0.0, 0.0, 0.0}, {0.55, 0.0, 0.0}};
  const std::vector<Vec3> transitionVelocities = {
      {0.0, 0.0, 0.0}, {0.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {3.0, 4.0, 0.0}};
  const TransitionDiagnostics transition = analyzeTransition(
      transitionData, transitionBonds, transitionPositions, transitionVelocities, lengths);
  if (transition.closestPair.first != 0 || transition.closestPair.second != 1 ||
      transition.closestNonBondedPair.first != 2 ||
      transition.closestNonBondedPair.second != 3 || transition.maxBondFirst != 0 ||
      transition.maxBondSecond != 1 || transition.minBondFirst != 0 ||
      transition.minBondSecond != 1 || transition.pairsBelow05 != 1 ||
      transition.pairsBelow06 != 2 || transition.pairsBelow07 != 2 ||
      transition.pairsBelow08 != 2 || !transition.positionsFinite ||
      !transition.velocitiesFinite) {
    throw std::runtime_error("transition pair diagnostic self-test failed");
  }
  expectNear("transition closest pair", transition.closestPair.distance, 0.2);
  expectNear("transition closest nonbonded pair",
             transition.closestNonBondedPair.distance, 0.55);
  expectNear("transition minimum permanent bond", transition.minPermanentBond, 0.2);
  expectNear("transition max speed", transition.maxSpeed, 5.0);
  expectNear("transition temperature", transition.temperature, 26.0 / 12.0);
  std::vector<Vec3> invalidPositions = transitionPositions;
  invalidPositions[0].x = std::numeric_limits<double>::quiet_NaN();
  expectReject("non-finite position", [&]() {
    (void)analyzeTransition(transitionData, transitionBonds, invalidPositions,
                            transitionVelocities, lengths);
  });
  std::vector<Vec3> invalidVelocities = transitionVelocities;
  invalidVelocities[0].x = std::numeric_limits<double>::infinity();
  expectReject("non-finite velocity", [&]() {
    (void)analyzeTransition(transitionData, transitionBonds, transitionPositions,
                            invalidVelocities, lengths);
  });

  const CpuWcaReference cpuWca = computeCpuWcaReference(
      {{4.9, 0.0, 0.0}, {-4.1, 0.0, 0.0}, {0.0, 0.0, 0.0}}, lengths, 1.0, 1.0);
  expectNear("CPU WCA energy", cpuWca.energy, 1.0);
  if (cpuWca.pairsInsideCutoff != 1 || !cpuWca.energyFinite) {
    throw std::runtime_error("CPU WCA pair-count self-test failed");
  }

  kg::ThermoSnapshot stage4Thermo;
  ConformationSample stage4Conformation;
  stage4Conformation.minPermanentBond = 1.0;
  if (!firstNonFiniteStage4Field(stage4Thermo, stage4Conformation).empty()) {
    throw std::runtime_error("finite Stage-4 field self-test failed");
  }
  stage4Thermo.bondedEnergy = std::numeric_limits<double>::quiet_NaN();
  if (firstNonFiniteStage4Field(stage4Thermo, stage4Conformation) != "bondedEnergy" ||
      formatStage4Field("self_test", "bondedEnergy", stage4Thermo.bondedEnergy)
              .find("isfinite=false") == std::string::npos) {
    throw std::runtime_error("non-finite Stage-4 field self-test failed");
  }

  std::vector<std::string> cliStorage = {
      "kg_assoc_star_equilibrate", "-i", "input.lammpsdat", "-o", "output.lammpsdat",
      "--arms", "2", "--narm", "1", "--seed", "17", "--dt", "0.002",
      "--stage3b-steps", "12", "--stage3b-diagnostic-every", "5",
      "--stage4-entry-diagnostic-only"};
  std::vector<char*> cliArguments;
  cliArguments.reserve(cliStorage.size());
  for (std::string& argument : cliStorage) {
    cliArguments.push_back(&argument[0]);
  }
  const Parameters parsed = parseArguments(
      static_cast<int>(cliArguments.size()), cliArguments.data());
  if (!parsed.stage4EntryDiagnosticOnly || !parsed.hasSeed || parsed.seed != 17 ||
      parsed.dtDpd != 0.002 || parsed.dtWca != 0.002 || parsed.stage3bSteps != 12 ||
      parsed.stage3bDiagnosticEvery != 5 || !shouldSampleStage3b(5, 12, 5) ||
      shouldSampleStage3b(6, 12, 5) || !shouldSampleStage3b(12, 12, 5)) {
    throw std::runtime_error("Stage-4 entry diagnostic CLI self-test failed");
  }
  cliStorage.push_back("--dt-wca");
  cliStorage.push_back("0.005");
  cliArguments.clear();
  for (std::string& argument : cliStorage) {
    cliArguments.push_back(&argument[0]);
  }
  const Parameters explicitTimesteps = parseArguments(
      static_cast<int>(cliArguments.size()), cliArguments.data());
  expectNear("explicit DPD timestep", explicitTimesteps.dtDpd, 0.002);
  expectNear("explicit WCA timestep", explicitTimesteps.dtWca, 0.005);
  if (explicitTimesteps.stage4PromotionTest) {
    throw std::runtime_error("explicit DPD/WCA timestep CLI self-test failed");
  }
  std::vector<std::string> normalCliStorage = {
      "kg_assoc_star_equilibrate", "-i", "input.lammpsdat", "-o", "output.lammpsdat",
      "--arms", "2", "--narm", "1"};
  std::vector<char*> normalCliArguments;
  for (std::string& argument : normalCliStorage) {
    normalCliArguments.push_back(&argument[0]);
  }
  const Parameters normalParsed = parseArguments(
      static_cast<int>(normalCliArguments.size()), normalCliArguments.data());
  if (normalParsed.stage4PromotionTest || normalParsed.wcaRamp) {
    throw std::runtime_error("normal-mode CLI self-test failed");
  }
  normalCliStorage.push_back("--wca-ramp");
  normalCliArguments.clear();
  for (std::string& argument : normalCliStorage) {
    normalCliArguments.push_back(&argument[0]);
  }
  const Parameters normalRampParsed = parseArguments(
      static_cast<int>(normalCliArguments.size()), normalCliArguments.data());
  if (normalRampParsed.stage4PromotionTest || !normalRampParsed.wcaRamp) {
    throw std::runtime_error("normal WCA-ramp CLI self-test failed");
  }
  std::vector<std::string> promotionCliStorage = {
      "kg_assoc_star_equilibrate", "-i", "input.lammpsdat", "-o", "output.lammpsdat",
      "--arms", "2", "--narm", "1", "--stage4-promotion-test",
      "--promotion-steps", "7", "--wca-ramp", "--wca-ramp-steps", "9"};
  std::vector<char*> promotionCliArguments;
  promotionCliArguments.reserve(promotionCliStorage.size());
  for (std::string& argument : promotionCliStorage) {
    promotionCliArguments.push_back(&argument[0]);
  }
  const Parameters promotionParsed = parseArguments(
      static_cast<int>(promotionCliArguments.size()), promotionCliArguments.data());
  if (!promotionParsed.stage4PromotionTest || promotionParsed.promotionSteps != 7 ||
      !promotionParsed.wcaRamp || promotionParsed.wcaRampSteps != 9) {
    throw std::runtime_error("promotion-test CLI self-test failed");
  }
  promotionCliStorage.push_back("--stage4-entry-diagnostic-only");
  promotionCliArguments.clear();
  for (std::string& argument : promotionCliStorage) {
    promotionCliArguments.push_back(&argument[0]);
  }
  expectReject("incompatible Stage-4 modes", [&]() {
    (void)parseArguments(
        static_cast<int>(promotionCliArguments.size()), promotionCliArguments.data());
  });
  const std::vector<double> promotion = promotionTimesteps();
  if (promotion != std::vector<double>({0.002, 0.005, 0.01})) {
    throw std::runtime_error("promotion timestep scheduling self-test failed");
  }
  if (wcaRampEpsilons() != std::vector<double>({0.01, 0.03, 0.10, 0.30, 1.00}) ||
      promotionTimestepsAfterWcaRamp() != std::vector<double>({0.005, 0.01}) ||
      wcaRampStepCount(9) != 45) {
    throw std::runtime_error("WCA ramp scheduling self-test failed");
  }
  ParticleStateSnapshot invalidPromotionState;
  invalidPromotionState.positions = {{0.0, 0.0, 0.0}, {1.5, 0.0, 0.0}};
  invalidPromotionState.velocities = {{0.0, 0.0, 0.0}, {0.0, 0.0, 0.0}};
  expectReject("promotion FENE validation", [&]() {
    validatePromotionState("self_test", invalidPromotionState, {{0, 1}}, lengths, 1.5);
  });
  kg::ThermoSnapshot thermo;
  const std::string row = formatDiagnosticsRow(10, 0.1, thermo, sample);
  if (diagnosticsHeader().find("mean_rg2") == std::string::npos ||
      row.find("10 0.1") != 0) {
    throw std::runtime_error("diagnostics formatting self-test failed");
  }
  const std::string transitionRow = formatTransitionDiagnostics(
      "wca_ramp_epsilon=0.01_before", 10, 10, -1, 1000.0, transition, transitionData,
      0.01);
  if (transitionRow.find("epsilon=0.010000") == std::string::npos ||
      transitionRow.find("min_permanent_bond=") == std::string::npos ||
      transitionRow.find("min_permanent_bond_ids=1,2") == std::string::npos ||
      transitionRow.find("max_permanent_bond_ids=1,2") == std::string::npos) {
    throw std::runtime_error("transition diagnostic formatting self-test failed");
  }
  std::cout << "E1_SELF_TEST PASS topology, PBC conformation, transition and Stage-4 diagnostics\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Parameters parameters = parseArguments(argc, argv);
    if (parameters.selfTest) {
      runSelfTest();
      return 0;
    }

    const kg::LammpsData data = kg::readLammpsDataFile(parameters.input);
    const kg_assoc::StarTopologyReport topology = kg_assoc::auditStarTopology(
        data, {parameters.arms, parameters.beadsPerArm});
    const std::vector<std::vector<int>> adjacency = buildAdjacency(data);
    const std::vector<StarDefinition> stars =
        buildStarDefinitions(data, adjacency, parameters.arms);
    std::vector<std::pair<int, int>> bonds;
    bonds.reserve(data.bonds.size());
    for (const auto& bond : data.bonds) {
      bonds.push_back({bond.first - 1, bond.second - 1});
    }

    const std::string diagnosticsPath = parameters.diagnostics.empty()
        ? parameters.output + ".e1_diagnostics"
        : parameters.diagnostics;
    std::ofstream diagnostics(diagnosticsPath);
    if (!diagnostics) {
      throw std::runtime_error("cannot open diagnostics file: " + diagnosticsPath);
    }
    diagnostics << "# executable=kg_assoc_star_equilibrate input=" << parameters.input
                << " arms=" << parameters.arms << " narm=" << parameters.beadsPerArm
                << " dt_dpd=" << parameters.dtDpd << " dt_wca=" << parameters.dtWca
                << " temperature=" << parameters.temperature
                << " friction=" << parameters.friction << " stage1="
                << parameters.stage1Loops * parameters.stage1Steps << " stage2="
                << parameters.stage2Steps << " stage3="
                << parameters.stage3Loops * parameters.stage3Steps << " stage3b="
                << parameters.stage3bSteps << " stage4="
                << parameters.stage4Steps << " seed="
                << (parameters.hasSeed ? std::to_string(parameters.seed) : "UAMMD_default")
                << " wca_ramp=" << (parameters.wcaRamp ? "true" : "false")
                << " wca_ramp_steps=" << parameters.wcaRampSteps
                << " chemistry=disabled\n";
    diagnostics << diagnosticsHeader() << '\n';

    auto system = std::make_shared<uammd::System>(argc, argv);
    if (parameters.hasSeed) {
      system->rng().setSeed(parameters.seed);
    }
    const kg::SimulationBox box = kg::makeSimulationBox(data);
    kg::SimParams validation;
    validation.feneR0 = parameters.feneR0;
    kg::validateAtomTypesAndBondTopology(data, validation, box);
    (void)kg::logClosestPairWCA(data, box);
    const auto particles = kg::createParticleDataFromLammps(data, system, box);
    const std::string bondData =
        kg::buildUammdBondDataFromLammps(data, parameters.feneK, parameters.feneR0);
    if (parameters.initializeVelocities) {
      kg::initializeVelocitiesAtTemperature(particles, kDPDTemperature, false);
    }
    const Vec3 lengths{data.xhi - data.xlo, data.yhi - data.ylo, data.zhi - data.zlo};

    std::cout << kg_assoc::formatStarTopologyReport(topology);
    std::cout << "E1 input " << parameters.input << " output " << parameters.output
              << " diagnostics " << diagnosticsPath << " seed="
              << (parameters.hasSeed ? std::to_string(parameters.seed) : "UAMMD_default")
              << " chemistry disabled\n";
    long long totalSteps = 0;
    double simulationTime = 0.0;
    const auto start = std::chrono::steady_clock::now();

    for (int loop = 1; loop <= parameters.stage1Loops; ++loop) {
      const DpdBundle bundle = makeDpdSegment(
          particles, box, bondData, parameters.dtDpd, kDPDInitialAmplitude);
      const double limit = stage1DisplacementLimit(loop);
      for (int local = 0; local < parameters.stage1Steps; ++local) {
        const std::vector<uammd::real4> previous = copyPositions(particles);
        bundle.integrator->forwardTime();
        limitDisplacements(particles, box, previous, limit, parameters.dtDpd);
        ++totalSteps;
        simulationTime += parameters.dtDpd;
        if (totalSteps % 100 == 0) {
          logThermo(totalSteps, bundle.integrator, particles, bundle.nonBonded, bundle.bonded,
                    data, box, parameters, false);
        }
      }
      CudaSafeCall(cudaDeviceSynchronize());
    }

    {
      const DpdBundle bundle = makeDpdSegment(
          particles, box, bondData, parameters.dtDpd, kDPDInitialAmplitude);
      for (int local = 0; local < parameters.stage2Steps; ++local) {
        bundle.integrator->forwardTime();
        ++totalSteps;
        simulationTime += parameters.dtDpd;
        if (totalSteps % 1000 == 0) {
          logThermo(totalSteps, bundle.integrator, particles, bundle.nonBonded, bundle.bonded,
                    data, box, parameters, false);
        }
      }
      CudaSafeCall(cudaDeviceSynchronize());
    }

    for (int loop = 1; loop <= parameters.stage3Loops; ++loop) {
      const double amplitude = stage3Amplitude(loop);
      const DpdBundle bundle = makeDpdSegment(
          particles, box, bondData, parameters.dtDpd, amplitude);
      for (int local = 0; local < parameters.stage3Steps; ++local) {
        bundle.integrator->forwardTime();
        ++totalSteps;
        simulationTime += parameters.dtDpd;
        if (totalSteps % 100 == 0) {
          logThermo(totalSteps, bundle.integrator, particles, bundle.nonBonded, bundle.bonded,
                    data, box, parameters, false);
        }
      }
      CudaSafeCall(cudaDeviceSynchronize());
      appendTransitionDiagnostics("after_stage3_loop", totalSteps, loop, -1, amplitude,
                                  diagnostics, particles, data, bonds, lengths,
                                  parameters.feneR0);
    }

    if (parameters.stage3bSteps > 0) {
      const double finalAmplitude = stage3Amplitude(parameters.stage3Loops);
      const DpdBundle bundle = makeDpdSegment(
          particles, box, bondData, parameters.dtDpd, finalAmplitude);
      for (int local = 1; local <= parameters.stage3bSteps; ++local) {
        bundle.integrator->forwardTime();
        ++totalSteps;
        simulationTime += parameters.dtDpd;
        if (shouldSampleStage3b(local, parameters.stage3bSteps,
                                parameters.stage3bDiagnosticEvery)) {
          CudaSafeCall(cudaDeviceSynchronize());
          appendTransitionDiagnostics("during_stage3b_relaxation_hold", totalSteps,
                                      parameters.stage3Loops, local, finalAmplitude,
                                      diagnostics, particles, data, bonds, lengths,
                                      parameters.feneR0);
        }
      }
      CudaSafeCall(cudaDeviceSynchronize());
    }

    appendTransitionDiagnostics("before_stage4", totalSteps, parameters.stage3Loops, -1,
                                stage3Amplitude(parameters.stage3Loops), diagnostics,
                                particles, data, bonds, lengths, parameters.feneR0);

    {
      const auto wca = stage4Value("construct WCA interactor", [&]() {
        return kg::createWCAInteractor_CellList(
            particles, box.box, data.atomTypes, parameters.epsilon, parameters.sigma,
            parameters.skin);
      });
      const auto fene = stage4Value("construct permanent FENE interactor", [&]() {
        return kg::createFENEInteractor(particles, box.box, bondData);
      });
      using NVT = uammd::VerletNVT::GronbechJensen;
      const auto makeNvtIntegrator = [&](std::shared_ptr<uammd::Interactor> segmentWca,
                                         double timestep,
                                         const std::string& label) {
        NVT::Parameters integratorParameters;
        integratorParameters.temperature = static_cast<uammd::real>(parameters.temperature);
        integratorParameters.friction = static_cast<uammd::real>(parameters.friction);
        integratorParameters.dt = static_cast<uammd::real>(timestep);
        integratorParameters.initVelocities = false;
        const auto integrator = stage4Value("construct NVT integrator " + label, [&]() {
          return std::make_shared<NVT>(particles, integratorParameters);
        });
        stage4Void("attach WCA interactor " + label, [&]() {
          integrator->addInteractor(segmentWca);
        });
        stage4Void("attach permanent FENE interactor " + label, [&]() {
          integrator->addInteractor(fene);
        });
        return integrator;
      };

      const ParticleStateSnapshot entryState = stage4Value(
          "copy Stage-4 entry particle state", [&]() {
            return copyParticleState(particles, data.natoms);
          });
      appendCpuWcaReference(
          diagnostics,
          computeCpuWcaReference(entryState.positions, lengths, parameters.epsilon,
                                 parameters.sigma));

      std::function<void()> runWcaRamp;
      {
        const auto runPromotionSegment = [&](double timestep,
                                             std::shared_ptr<uammd::Interactor> segmentWca,
                                             const Parameters& thermoParameters) {
          const std::string timestepLabel = "dt=" + formatTimestepLabel(timestep);
          const auto integrator = makeNvtIntegrator(segmentWca, timestep, timestepLabel);
          appendTransitionDiagnostics(
              "promotion_boundary_before_" + timestepLabel, totalSteps,
              parameters.stage3Loops, -1, stage3Amplitude(parameters.stage3Loops),
              diagnostics, particles, data, bonds, lengths, parameters.feneR0,
              thermoParameters.epsilon);
          appendStage4Sample("promotion_before_" + timestepLabel, totalSteps,
                             simulationTime, diagnostics, integrator, particles, segmentWca,
                             fene, data, box, thermoParameters, stars, adjacency, bonds,
                             lengths);

          for (int local = 1; local <= parameters.promotionSteps; ++local) {
            stage4Void("promotion " + timestepLabel + " forwardTime", [&]() {
              integrator->forwardTime();
            });
            ++totalSteps;
            simulationTime += timestep;
            const ParticleStateSnapshot state = stage4Value(
                "copy promotion " + timestepLabel + " particle state", [&]() {
                  return copyParticleState(particles, data.natoms);
                });
            validatePromotionState(
                timestepLabel + " step " + std::to_string(local), state, bonds, lengths,
                parameters.feneR0);
            const kg::ThermoSnapshot thermo = computeStage4Thermo(
                "promotion " + timestepLabel + " step " + std::to_string(local),
                integrator, particles, segmentWca, fene, data, box, thermoParameters);
            const std::string nonFiniteField = firstNonFiniteThermoField(thermo);
            if (!nonFiniteField.empty()) {
              throw std::runtime_error("E1_PROMOTION FAIL after " + timestepLabel +
                                       " step " + std::to_string(local) +
                                       ": non-finite " + nonFiniteField);
            }
          }

          appendTransitionDiagnostics(
              "promotion_boundary_after_" + timestepLabel, totalSteps,
              parameters.stage3Loops, -1, stage3Amplitude(parameters.stage3Loops),
              diagnostics, particles, data, bonds, lengths, parameters.feneR0,
              thermoParameters.epsilon);
          appendStage4Sample("promotion_after_" + timestepLabel, totalSteps,
                             simulationTime, diagnostics, integrator, particles, segmentWca,
                             fene, data, box, thermoParameters, stars, adjacency, bonds,
                             lengths);
        };

        runWcaRamp = [&]() {
          for (const double rampEpsilon : wcaRampEpsilons()) {
            const auto rampWca = stage4Value(
                "construct WCA ramp epsilon=" + std::to_string(rampEpsilon), [&]() {
                  return kg::createWCAInteractor_CellList(
                      particles, box.box, data.atomTypes, rampEpsilon, parameters.sigma,
                      parameters.skin);
                });
            Parameters rampThermoParameters = parameters;
            rampThermoParameters.epsilon = rampEpsilon;
            const auto integrator = makeNvtIntegrator(
                rampWca, 0.002, "WCA ramp epsilon=" + std::to_string(rampEpsilon));
            const std::string epsilonLabel = "wca_ramp_epsilon=" +
                std::to_string(rampEpsilon);
            appendTransitionDiagnostics(
                epsilonLabel + "_before", totalSteps, parameters.stage3Loops, -1,
                stage3Amplitude(parameters.stage3Loops), diagnostics, particles, data, bonds,
                lengths, parameters.feneR0, rampEpsilon);
            appendStage4Sample(
                epsilonLabel + "_before", totalSteps, simulationTime, diagnostics, integrator,
                particles, rampWca, fene, data, box, rampThermoParameters, stars, adjacency,
                bonds, lengths);

            for (int local = 1; local <= parameters.wcaRampSteps; ++local) {
              stage4Void(epsilonLabel + " step " + std::to_string(local), [&]() {
                integrator->forwardTime();
              });
              ++totalSteps;
              simulationTime += 0.002;
              const ParticleStateSnapshot state = stage4Value(
                  epsilonLabel + " copy step " + std::to_string(local), [&]() {
                    return copyParticleState(particles, data.natoms);
                  });
              validatePromotionState(
                  epsilonLabel + " step " + std::to_string(local), state, bonds, lengths,
                  parameters.feneR0, "E1_WCA_RAMP");
              const kg::ThermoSnapshot thermo = computeStage4Thermo(
                  epsilonLabel + " thermo step " + std::to_string(local), integrator,
                  particles, rampWca, fene, data, box, rampThermoParameters);
              const std::string nonFiniteField = firstNonFiniteThermoField(thermo);
              if (!nonFiniteField.empty()) {
                throw std::runtime_error(
                    "E1_WCA_RAMP FAIL epsilon=" + std::to_string(rampEpsilon) +
                    " local_step=" + std::to_string(local) +
                    ": non-finite " + nonFiniteField);
              }
            }

            appendTransitionDiagnostics(
                epsilonLabel + "_after", totalSteps, parameters.stage3Loops, -1,
                stage3Amplitude(parameters.stage3Loops), diagnostics, particles, data, bonds,
                lengths, parameters.feneR0, rampEpsilon);
            appendStage4Sample(
                epsilonLabel + "_after", totalSteps, simulationTime, diagnostics, integrator,
                particles, rampWca, fene, data, box, rampThermoParameters, stars, adjacency,
                bonds, lengths);
          }
        };

        if (parameters.stage4PromotionTest) {
          if (parameters.wcaRamp) {
            runWcaRamp();
            for (double timestep : promotionTimestepsAfterWcaRamp()) {
              runPromotionSegment(timestep, wca, parameters);
            }
          } else {
            for (double timestep : promotionTimesteps()) {
              runPromotionSegment(timestep, wca, parameters);
            }
          }
        }
        if (!parameters.stage4PromotionTest) {
          if (parameters.wcaRamp && !parameters.stage4EntryDiagnosticOnly) {
            runWcaRamp();
            for (double timestep : promotionTimestepsAfterWcaRamp()) {
              runPromotionSegment(timestep, wca, parameters);
            }
          }
          const auto integrator = makeNvtIntegrator(wca, parameters.dtWca, "normal Stage 4");
          appendStage4Sample("initial_stage4", totalSteps, simulationTime, diagnostics,
                             integrator, particles, wca, fene, data, box, parameters, stars,
                             adjacency, bonds, lengths);

          stage4Void("first NVT forwardTime", [&]() {
            integrator->forwardTime();
          });
          ++totalSteps;
          simulationTime += parameters.dtWca;
          appendStage4Sample("post_first_nvt_step", totalSteps, simulationTime, diagnostics,
                             integrator, particles, wca, fene, data, box, parameters, stars,
                             adjacency, bonds, lengths);

          if (!parameters.stage4EntryDiagnosticOnly) {
            for (int local = 1; local < parameters.stage4Steps; ++local) {
              integrator->forwardTime();
              ++totalSteps;
              simulationTime += parameters.dtWca;
              if (totalSteps % 10000 == 0) {
                logThermo(totalSteps, integrator, particles, wca, fene, data, box,
                          parameters, true);
              }
              if (totalSteps % parameters.conformationEvery == 0) {
                appendStage4Sample("stage4_periodic", totalSteps, simulationTime,
                                   diagnostics, integrator, particles, wca, fene, data, box,
                                   parameters, stars, adjacency, bonds, lengths);
              }
            }
            checkStage4Cuda("complete Stage 4");
          }
        }
      }
    }

    if (parameters.stage4EntryDiagnosticOnly || parameters.stage4PromotionTest) {
      if (parameters.stage4PromotionTest) {
        if (parameters.wcaRamp) {
          std::cout << "E1_PROMOTION PASS WCA ramp completed at dt=0.002, then "
                    << "promotion at dt=0.005 and 0.010; no E1 configuration written\n";
        } else {
          std::cout << "E1_PROMOTION PASS relaxed-state WCA segments completed at "
                    << "dt=0.002, 0.005, and 0.010; no E1 configuration written\n";
        }
        return 0;
      }
      std::cout << "E1_STAGE4_DIAG entry-only complete after one NVT step; "
                << "no E1 configuration written\n";
      return 0;
    }

    const std::string producer = "kg_assoc_star_equilibrate E1 chemistry disabled seed=" +
        (parameters.hasSeed ? std::to_string(parameters.seed) : "UAMMD_default");
    kg::writeLAMMPSDataSnapshot(parameters.output, static_cast<int>(totalSteps), data,
                                particles, producer);
    const double wallSeconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    std::cout << kg::formatPerformanceSummary(wallSeconds, static_cast<int>(totalSteps),
                                               data.natoms, parameters.dtWca)
              << "\nE1_INFRASTRUCTURE RUN COMPLETE chemistry disabled\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "E1_INFRASTRUCTURE FAIL: " << error.what() << '\n';
    return 1;
  }
}
