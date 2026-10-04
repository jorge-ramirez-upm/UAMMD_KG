#include <uammd.cuh>

#include "Integrator/VerletNVE.cuh"
#include "Integrator/VerletNVT.cuh"
#include "../KG/kg_interactors.cuh"
#include "../KG/kg_lammps_io.cuh"
#include "../KG/kg_runtime.cuh"
#include "kg_assoc_star_topology.cuh"

#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <queue>
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
  int stage4Steps = 1000000;
  int conformationEvery = 10000;
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

std::string nextArgument(int& index, int argc, char** argv) {
  if (++index >= argc) {
    throw std::runtime_error("missing option value");
  }
  return argv[index];
}

void printHelp() {
  std::cout
      << "kg_assoc_star_equilibrate -i FILE -o FILE --arms A --narm N [options]\n"
      << "  --diagnostics FILE --conformation-every N --dt DT --temperature T\n"
      << "  --friction XI --sigma S --epsilon E --fene-k K --fene-r0 R0 --skin S\n"
      << "  --stage1-loops N --stage1-steps N --stage2-steps N\n"
      << "  --stage3-loops N --stage3-steps N --stage4-steps N\n"
      << "  --init-velocities --self-test\n";
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
    } else if (option == "--stage4-steps") {
      parameters.stage4Steps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--conformation-every") {
      parameters.conformationEvery = std::stoi(nextArgument(index, argc, argv));
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
      parameters.beadsPerArm <= 0 || parameters.dt <= 0.0 ||
      parameters.temperature <= 0.0 || parameters.friction <= 0.0 ||
      parameters.sigma <= 0.0 || parameters.epsilon <= 0.0 || parameters.feneK <= 0.0 ||
      parameters.feneR0 <= 0.0 || parameters.skin < 0.0 || parameters.stage1Loops < 1 ||
      parameters.stage1Steps < 1 || parameters.stage2Steps < 1 ||
      parameters.stage3Loops < 1 || parameters.stage3Steps < 1 ||
      parameters.stage4Steps < 1 || parameters.conformationEvery < 1) {
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
    sample.maxPermanentBond = std::max(sample.maxPermanentBond,
                                       std::sqrt(norm2(displacement)));
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
         "mean_rg2 mean_center_terminal_r2 max_permanent_bond";
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

DpdBundle makeWcaSegment(std::shared_ptr<uammd::ParticleData> particles,
                         const kg::SimulationBox& box,
                         const kg::LammpsData& data,
                         const Parameters& parameters,
                         const std::string& bondData) {
  auto wca = kg::createWCAInteractor_CellList(
      particles, box.box, data.atomTypes, parameters.epsilon, parameters.sigma,
      parameters.skin);
  auto fene = kg::createFENEInteractor(particles, box.box, bondData);
  using NVT = uammd::VerletNVT::GronbechJensen;
  NVT::Parameters integratorParameters;
  integratorParameters.temperature = static_cast<uammd::real>(parameters.temperature);
  integratorParameters.friction = static_cast<uammd::real>(parameters.friction);
  integratorParameters.dt = static_cast<uammd::real>(parameters.dt);
  integratorParameters.initVelocities = false;
  auto integrator = std::make_shared<NVT>(particles, integratorParameters);
  integrator->addInteractor(wca);
  integrator->addInteractor(fene);
  return {integrator, wca, fene};
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

void appendStage4Diagnostics(long long step,
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
  const kg::ThermoSnapshot thermo = kg::computeThermoSnapshot(
      integrator, particles, wca, fene, data, box, parameters.epsilon,
      parameters.sigma, box.box.getVolume(), data.natoms);
  const ConformationSample conformation =
      sampleConformation(particles, stars, adjacency, bonds, lengths);
  if (!std::isfinite(thermo.totalEnergy) || !std::isfinite(conformation.meanRg2) ||
      !std::isfinite(conformation.meanCenterTerminalR2) ||
      !std::isfinite(conformation.maxPermanentBond)) {
    throw std::runtime_error("non-finite Stage 4 diagnostic");
  }
  output << formatDiagnosticsRow(step, step * parameters.dt, thermo, conformation) << '\n';
  output.flush();
}

void expectNear(const std::string& label, double observed, double expected) {
  if (std::abs(observed - expected) > 1.0e-10) {
    throw std::runtime_error(label + " self-test failed");
  }
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
  expectNear("maximum permanent bond", sample.maxPermanentBond, 1.0);
  sample = computeConformationSample(
      stars, adjacency, bonds, {{-4.2, 0.0, 0.0}, {4.8, 0.0, 0.0}, {3.8, 0.0, 0.0}},
      lengths);
  expectNear("PBC-safe Rg2", sample.meanRg2, 2.0 / 3.0);
  expectNear("PBC-safe center-terminal r2", sample.meanCenterTerminalR2, 1.0);
  kg::ThermoSnapshot thermo;
  const std::string row = formatDiagnosticsRow(10, 0.1, thermo, sample);
  if (diagnosticsHeader().find("mean_rg2") == std::string::npos ||
      row.find("10 0.1") != 0) {
    throw std::runtime_error("diagnostics formatting self-test failed");
  }
  std::cout << "E1_SELF_TEST PASS topology, PBC conformation, diagnostics\n";
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
                << " dt=" << parameters.dt << " temperature=" << parameters.temperature
                << " friction=" << parameters.friction << " stage1="
                << parameters.stage1Loops * parameters.stage1Steps << " stage2="
                << parameters.stage2Steps << " stage3="
                << parameters.stage3Loops * parameters.stage3Steps << " stage4="
                << parameters.stage4Steps << " chemistry=disabled\n";
    diagnostics << diagnosticsHeader() << '\n';

    auto system = std::make_shared<uammd::System>(argc, argv);
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
              << " diagnostics " << diagnosticsPath << " chemistry disabled\n";
    long long totalSteps = 0;
    const auto start = std::chrono::steady_clock::now();

    for (int loop = 1; loop <= parameters.stage1Loops; ++loop) {
      const DpdBundle bundle = makeDpdSegment(
          particles, box, bondData, parameters.dt, kDPDInitialAmplitude);
      const double limit = stage1DisplacementLimit(loop);
      for (int local = 0; local < parameters.stage1Steps; ++local) {
        const std::vector<uammd::real4> previous = copyPositions(particles);
        bundle.integrator->forwardTime();
        limitDisplacements(particles, box, previous, limit, parameters.dt);
        ++totalSteps;
        if (totalSteps % 100 == 0) {
          logThermo(totalSteps, bundle.integrator, particles, bundle.nonBonded, bundle.bonded,
                    data, box, parameters, false);
        }
      }
      CudaSafeCall(cudaDeviceSynchronize());
    }

    {
      const DpdBundle bundle = makeDpdSegment(
          particles, box, bondData, parameters.dt, kDPDInitialAmplitude);
      for (int local = 0; local < parameters.stage2Steps; ++local) {
        bundle.integrator->forwardTime();
        ++totalSteps;
        if (totalSteps % 1000 == 0) {
          logThermo(totalSteps, bundle.integrator, particles, bundle.nonBonded, bundle.bonded,
                    data, box, parameters, false);
        }
      }
      CudaSafeCall(cudaDeviceSynchronize());
    }

    for (int loop = 1; loop <= parameters.stage3Loops; ++loop) {
      const DpdBundle bundle = makeDpdSegment(
          particles, box, bondData, parameters.dt, stage3Amplitude(loop));
      for (int local = 0; local < parameters.stage3Steps; ++local) {
        bundle.integrator->forwardTime();
        ++totalSteps;
        if (totalSteps % 100 == 0) {
          logThermo(totalSteps, bundle.integrator, particles, bundle.nonBonded, bundle.bonded,
                    data, box, parameters, false);
        }
      }
      CudaSafeCall(cudaDeviceSynchronize());
    }

    {
      const DpdBundle bundle = makeWcaSegment(particles, box, data, parameters, bondData);
      appendStage4Diagnostics(totalSteps, diagnostics, bundle.integrator, particles,
                              bundle.nonBonded, bundle.bonded, data, box, parameters,
                              stars, adjacency, bonds, lengths);
      for (int local = 0; local < parameters.stage4Steps; ++local) {
        bundle.integrator->forwardTime();
        ++totalSteps;
        if (totalSteps % 10000 == 0) {
          logThermo(totalSteps, bundle.integrator, particles, bundle.nonBonded, bundle.bonded,
                    data, box, parameters, true);
        }
        if (totalSteps % parameters.conformationEvery == 0) {
          appendStage4Diagnostics(totalSteps, diagnostics, bundle.integrator, particles,
                                  bundle.nonBonded, bundle.bonded, data, box, parameters,
                                  stars, adjacency, bonds, lengths);
        }
      }
      CudaSafeCall(cudaDeviceSynchronize());
    }

    kg::writeLAMMPSDataSnapshot(parameters.output, static_cast<int>(totalSteps), data,
                                particles, "kg_assoc_star_equilibrate E1 chemistry disabled");
    const double wallSeconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    std::cout << kg::formatPerformanceSummary(wallSeconds, static_cast<int>(totalSteps),
                                               data.natoms, parameters.dt)
              << "\nE1_INFRASTRUCTURE RUN COMPLETE chemistry disabled\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "E1_INFRASTRUCTURE FAIL: " << error.what() << '\n';
    return 1;
  }
}
