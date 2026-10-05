#include <uammd.cuh>

#include "Integrator/VerletNVT.cuh"
#include "../KG/correlator.h"
#include "../KG/kg_interactors.cuh"
#include "../KG/kg_runtime.cuh"
#include "kg_assoc_interactors.cuh"
#include "kg_assoc_star_runtime.cuh"

#include <chrono>
#include <cmath>
#include <cstdio>
#include <functional>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

bool near(double left, double right, double tolerance = 1e-12) {
  return std::abs(left - right) <= tolerance * std::max(1.0, std::abs(right));
}

struct Parameters {
  std::string input;
  std::string restartPrefix;
  std::string output = "assoc_production";
  int arms = 0;
  int beadsPerArm = 0;
  int steps = 100000;
  int every = 100;
  int diagnosticEvery = 1000;
  int comEvery = 100;
  int frameEvery = 10000;
  double dt = 0.01;
  double temperature = 1.0;
  double ea = 4.0;
  double ee = 8.0;
  double nu0 = 20.0;
  double rAssoc = 1.25;
  double damping = 2.0;
  double feneK = 30.0;
  double feneR0 = 1.5;
  double skin = 0.4;
  unsigned long long seed = 12345;
  bool force = false;
  bool selfTest = false;
  bool rAssocExplicit = false;
  bool seedExplicit = false;
};

struct RestartMetadata {
  long long completedSteps = 0;
  long long creations = 0;
  long long breaks = 0;
  Parameters parameters;
  std::vector<std::pair<int, int>> activeBonds;
};

std::string nextArgument(int& index, int argc, char** argv) {
  if (++index >= argc) {
    throw std::runtime_error("missing option value");
  }
  return argv[index];
}

void printHelp() {
  std::cout << "kg_assoc_production (--input FILE | --restart-prefix PREFIX) [options]\n"
            << "  --steps N --dt DT --temperature T --Ea E --Ee E --nu0 X\n"
            << "  --Nevery N --r-assoc R --damp D --K K --R0 R --seed S\n"
            << "  --diagnostic-every N --com-every N --frame-every N\n"
            << "  --restart-prefix PREFIX --output PREFIX --force --self-test\n";
}

Parameters parseArguments(int argc, char** argv) {
  Parameters parameters;
  for (int index = 1; index < argc; ++index) {
    const std::string option = argv[index];
    if (option == "--input") {
      parameters.input = nextArgument(index, argc, argv);
    } else if (option == "--restart-prefix") {
      parameters.restartPrefix = nextArgument(index, argc, argv);
    } else if (option == "--arms") {
      parameters.arms = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--narm") {
      parameters.beadsPerArm = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--steps") {
      parameters.steps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--dt") {
      parameters.dt = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--temperature") {
      parameters.temperature = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--Ea") {
      parameters.ea = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--Ee") {
      parameters.ee = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--nu0") {
      parameters.nu0 = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--Nevery") {
      parameters.every = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--diagnostic-every") {
      parameters.diagnosticEvery = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--com-every") {
      parameters.comEvery = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--frame-every") {
      parameters.frameEvery = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--r-assoc") {
      parameters.rAssoc = std::stod(nextArgument(index, argc, argv));
      parameters.rAssocExplicit = true;
    } else if (option == "--damp") {
      parameters.damping = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--K") {
      parameters.feneK = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--R0") {
      parameters.feneR0 = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--seed") {
      parameters.seed = std::stoull(nextArgument(index, argc, argv));
      parameters.seedExplicit = true;
    } else if (option == "--output") {
      parameters.output = nextArgument(index, argc, argv);
    } else if (option == "--force") {
      parameters.force = true;
    } else if (option == "--self-test") {
      parameters.selfTest = true;
    } else if (option == "--help") {
      printHelp();
      std::exit(0);
    } else {
      throw std::runtime_error("unknown argument: " + option);
    }
  }
  if (parameters.selfTest) {
    return parameters;
  }
  if ((!parameters.input.empty() && !parameters.restartPrefix.empty()) ||
      (parameters.input.empty() && parameters.restartPrefix.empty())) {
    throw std::runtime_error("provide exactly one of --input or --restart-prefix");
  }
  if ((!parameters.restartPrefix.empty() &&
       (parameters.arms < 0 || parameters.beadsPerArm < 0)) ||
      (!parameters.input.empty() && (parameters.arms <= 0 || parameters.beadsPerArm <= 0)) ||
      parameters.steps <= 0 || parameters.every <= 0 ||
      parameters.diagnosticEvery <= 0 || parameters.comEvery <= 0 ||
      parameters.frameEvery <= 0 || parameters.dt <= 0.0 ||
      parameters.temperature <= 0.0 || parameters.ea < 0.0 || parameters.nu0 < 0.0 ||
      parameters.rAssoc <= 0.0 || parameters.feneK <= 0.0 || parameters.feneR0 <= 0.0 ||
      parameters.rAssoc >= parameters.feneR0 || parameters.damping <= 0.0) {
    throw std::runtime_error("invalid S1 parameters");
  }
  return parameters;
}

void writeRestartMetadata(const std::string& path,
                          const Parameters& parameters,
                          long long completedSteps,
                          long long creations,
                          long long breaks,
                          const kg_assoc::StickerState& state) {
  std::ofstream output(path);
  if (!output) {
    throw std::runtime_error("cannot write associating restart metadata");
  }
  output << std::setprecision(17);
  output << "KG_ASSOC_RESTART 1\n"
         << "completed_steps " << completedSteps << "\n"
         << "arms " << parameters.arms << "\n"
         << "narm " << parameters.beadsPerArm << "\n"
         << "dt " << parameters.dt << "\n"
         << "temperature " << parameters.temperature << "\n"
         << "Ea " << parameters.ea << "\n"
         << "Ee " << parameters.ee << "\n"
         << "nu0 " << parameters.nu0 << "\n"
         << "Nevery " << parameters.every << "\n"
         << "r_assoc " << parameters.rAssoc << "\n"
         << "damping " << parameters.damping << "\n"
         << "K " << parameters.feneK << "\n"
         << "R0 " << parameters.feneR0 << "\n"
         << "seed " << parameters.seed << "\n"
         << "creations " << creations << "\n"
         << "breaks " << breaks << "\n";
  std::vector<std::pair<int, int>> bonds;
  for (const int first : state.stickers()) {
    const int second = state.partner(first);
    if (second > first) {
      bonds.push_back({first + 1, second + 1});
    }
  }
  output << "active_bonds " << bonds.size() << "\n";
  for (const auto& bond : bonds) {
    output << bond.first << ' ' << bond.second << '\n';
  }
  output << "end\n";
}

RestartMetadata readRestartMetadata(const std::string& path) {
  std::ifstream input(path);
  if (!input) {
    throw std::runtime_error("cannot open associating restart metadata");
  }
  RestartMetadata metadata;
  std::string key;
  int version = 0;
  if (!(input >> key >> version) || key != "KG_ASSOC_RESTART" || version != 1) {
    throw std::runtime_error("unsupported or malformed associating restart metadata");
  }
  auto readKey = [&](const char* expected, auto& value) {
    if (!(input >> key >> value) || key != expected) {
      throw std::runtime_error(std::string("malformed associating restart field: ") + expected);
    }
  };
  readKey("completed_steps", metadata.completedSteps);
  readKey("arms", metadata.parameters.arms);
  readKey("narm", metadata.parameters.beadsPerArm);
  readKey("dt", metadata.parameters.dt);
  readKey("temperature", metadata.parameters.temperature);
  readKey("Ea", metadata.parameters.ea);
  readKey("Ee", metadata.parameters.ee);
  readKey("nu0", metadata.parameters.nu0);
  readKey("Nevery", metadata.parameters.every);
  readKey("r_assoc", metadata.parameters.rAssoc);
  readKey("damping", metadata.parameters.damping);
  readKey("K", metadata.parameters.feneK);
  readKey("R0", metadata.parameters.feneR0);
  readKey("seed", metadata.parameters.seed);
  readKey("creations", metadata.creations);
  readKey("breaks", metadata.breaks);
  std::size_t bondCount = 0;
  readKey("active_bonds", bondCount);
  std::set<std::pair<int, int>> uniqueBonds;
  for (std::size_t index = 0; index < bondCount; ++index) {
    int first = 0;
    int second = 0;
    if (!(input >> first >> second) || first >= second || first <= 0) {
      throw std::runtime_error("malformed active temporary bond in restart");
    }
    if (!uniqueBonds.insert({first, second}).second) {
      throw std::runtime_error("duplicate active temporary bond in restart");
    }
    metadata.activeBonds.push_back({first, second});
  }
  if (!(input >> key) || key != "end" || (input >> key)) {
    throw std::runtime_error("trailing or missing end marker in associating restart");
  }
  if (metadata.completedSteps < 0 || metadata.creations < 0 || metadata.breaks < 0 ||
      metadata.creations - metadata.breaks != static_cast<long long>(bondCount)) {
    throw std::runtime_error("inconsistent associating restart event counters");
  }
  const Parameters& parameters = metadata.parameters;
  if (parameters.arms <= 0 || parameters.beadsPerArm <= 0 ||
      !std::isfinite(parameters.dt) || !std::isfinite(parameters.temperature) ||
      !std::isfinite(parameters.ea) || !std::isfinite(parameters.ee) ||
      !std::isfinite(parameters.nu0) || !std::isfinite(parameters.rAssoc) ||
      !std::isfinite(parameters.damping) || !std::isfinite(parameters.feneK) ||
      !std::isfinite(parameters.feneR0) || parameters.dt <= 0.0 ||
      parameters.temperature <= 0.0 || parameters.ea < 0.0 || parameters.nu0 < 0.0 ||
      parameters.every <= 0 || parameters.rAssoc <= 0.0 || parameters.damping <= 0.0 ||
      parameters.feneK <= 0.0 || parameters.feneR0 <= 0.0 ||
      parameters.rAssoc >= parameters.feneR0) {
    throw std::runtime_error("invalid physical parameters in associating restart");
  }
  return metadata;
}

void expectReject(const std::string& name, const std::function<void()>& operation) {
  try {
    operation();
  } catch (const std::runtime_error&) {
    return;
  }
  throw std::runtime_error("self-test accepted invalid case: " + name);
}

void runSelfTest() {
  kg::LammpsData data;
  data.natoms = 5;
  data.nbonds = 0;
  data.type = {1, 2, 3, 2, 1};
  data.mol = {10, 10, 99, 11, 11};
  const std::vector<int> stickers = kg_assoc::extractStickerIds(data);
  if (stickers != std::vector<int>({1, 3})) {
    throw std::runtime_error("type-2 sticker extraction failed");
  }

  const kg_assoc::BoxLengths lengths{10.0, 10.0, 10.0};
  const std::vector<kg_assoc::StickerCoordinate> coordinates = {
      {1, uammd::make_real3(0.0, 0.0, 0.0)},
      {3, uammd::make_real3(0.5, 0.0, 0.0)}};
  const std::vector<kg_assoc::Candidate> candidates =
      kg_assoc::findStickerCandidates(coordinates, lengths, 1.0);
  if (candidates.size() != 1 || candidates[0].first != 1 || candidates[0].second != 3) {
    throw std::runtime_error("sticker-only candidate search failed");
  }

  kg_assoc::StickerState state(5, stickers, false);
  state.make(1, 3);
  const kg_assoc::AssociationCounts counts = kg_assoc::summarizeAssociationState(
      data, state, {}, 1, 0);
  if (counts.freeStickers != 0 || counts.bonds != 1 || counts.intraStarBonds != 0 ||
      counts.interStarBonds != 1) {
    throw std::runtime_error("association count or intra/inter classification failed");
  }

  expectReject("non-sticker transient endpoint", [&]() {
    kg_assoc::StickerState invalidState(5, stickers, false);
    invalidState.make(0, 1);
  });
  expectReject("permanent/transient duplicate", [&]() {
    const std::set<std::pair<int, int>> permanent = {{1, 3}};
    (void)kg_assoc::summarizeAssociationState(data, state, permanent, 1, 0);
  });
  expectReject("state-count mismatch", [&]() {
    (void)kg_assoc::summarizeAssociationState(data, state, {}, 0, 0);
  });

  const auto emptyGraph = kg_assoc::analyzeMolecularGraph({10, 11, 12}, {});
  if (emptyGraph.connectedComponents != 3 || emptyGraph.largestClusterSize != 1 ||
      emptyGraph.meanDegree != 0.0 || emptyGraph.primaryLoops != 0 ||
      emptyGraph.secondaryLoops != 0) {
    throw std::runtime_error("empty molecular graph regression failed");
  }
  const auto oneEdge = kg_assoc::analyzeMolecularGraph({10, 11, 12}, {{10, 11}});
  if (oneEdge.connectedComponents != 2 || oneEdge.largestClusterSize != 2 ||
      !near(oneEdge.meanDegree, 2.0 / 3.0)) {
    throw std::runtime_error("single molecular edge regression failed");
  }
  const auto doubleEdge = kg_assoc::analyzeMolecularGraph({10, 11}, {{10, 11}, {10, 11}});
  const auto tripleEdge = kg_assoc::analyzeMolecularGraph(
      {10, 11}, {{10, 11}, {10, 11}, {10, 11}});
  if (doubleEdge.primaryLoops != 1 || tripleEdge.primaryLoops != 3 ||
      !near(tripleEdge.meanDegree, 1.0)) {
    throw std::runtime_error("molecular edge multiplicity regression failed");
  }
  const auto triangle = kg_assoc::analyzeMolecularGraph(
      {10, 11, 12}, {{10, 11}, {10, 12}, {11, 12}});
  const auto duplicatedTriangle = kg_assoc::analyzeMolecularGraph(
      {10, 11, 12}, {{10, 11}, {10, 11}, {10, 12}, {11, 12}});
  if (triangle.secondaryLoops != 1 || duplicatedTriangle.primaryLoops != 1 ||
      duplicatedTriangle.secondaryLoops != 1 || !near(triangle.secondDegreeMoment, 4.0)) {
    throw std::runtime_error("molecular triangle regression failed");
  }
  kg::LammpsData intraData = data;
  intraData.mol[3] = 10;
  kg_assoc::StickerState intraState(5, stickers, false);
  intraState.make(1, 3);
  const auto intraOnly = kg_assoc::molecularNetworkObservables(intraData, intraState);
  if (intraOnly.connectedComponents != 2 || intraOnly.largestClusterSize != 1 ||
      intraOnly.meanDegree != 0.0) {
    throw std::runtime_error("intra-star graph exclusion regression failed");
  }
  expectReject("malformed molecular graph", [&]() {
    (void)kg_assoc::analyzeMolecularGraph({10, 10}, {});
  });

  const std::string restartTestPath = "/tmp/kg_assoc_restart_self_test.assoc_restart";
  Parameters restartParameters;
  restartParameters.arms = 4;
  restartParameters.beadsPerArm = 10;
  restartParameters.seed = 12001;
  kg_assoc::StickerState restartState(5, stickers, false);
  restartState.make(1, 3);
  writeRestartMetadata(restartTestPath, restartParameters, 200, 4, 3, restartState);
  const RestartMetadata restart = readRestartMetadata(restartTestPath);
  if (restart.completedSteps != 200 || restart.creations != 4 || restart.breaks != 3 ||
      restart.parameters.seed != 12001 || restart.activeBonds !=
          std::vector<std::pair<int, int>>({{2, 4}})) {
    throw std::runtime_error("restart metadata round-trip regression failed");
  }
  {
    std::ofstream malformed(restartTestPath);
    malformed << "KG_ASSOC_RESTART 1\n"
              << "completed_steps 0\narms 4\nnarm 10\ndt 0.01\ntemperature 1\n"
              << "Ea 4\nEe 8\nnu0 20\nNevery 100\nr_assoc 1.25\ndamping 2\n"
              << "K 30\nR0 1.5\nseed 1\ncreations 1\nbreaks 0\nactive_bonds 1\n"
              << "2 2\nend\n";
  }
  expectReject("malformed associating restart", [&]() {
    (void)readRestartMetadata(restartTestPath);
  });
  std::remove(restartTestPath.c_str());
  std::cout << "STAR_ASSOCIATION_SMOKE SELF_TEST PASS sticker subset and invariants\n";
}

void writeState(std::ofstream& output,
                long long step,
                const Parameters& parameters,
                const kg_assoc::AssociationCounts& counts,
                const kg_assoc::MolecularNetworkObservables& network,
                const kg_assoc::ActiveBondDistanceDiagnostics& distances,
                int stickerCount,
                long long creations,
                long long breaks) {
  output << step << ' ' << std::setprecision(12) << step * parameters.dt << ' '
         << counts.freeStickers << ' ' << counts.bonds << ' ' << creations << ' '
         << breaks << ' ' << counts.intraStarBonds << ' ' << counts.interStarBonds << ' '
         << 2.0 * counts.bonds / stickerCount << ' '
         << network.connectedComponents << ' ' << network.largestClusterSize << ' '
         << network.largestClusterFraction << ' ' << network.meanDegree << ' '
         << network.secondDegreeMoment << ' ' << network.primaryLoops << ' '
         << network.secondaryLoops << ' ' << distances.observations << ' '
         << distances.maximumDistance << ' '
         << (distances.observations ?
             static_cast<double>(distances.above125) / distances.observations : 0.0) << ' '
         << (distances.observations ?
             static_cast<double>(distances.above130) / distances.observations : 0.0) << ' '
         << (distances.observations ?
             static_cast<double>(distances.above140) / distances.observations : 0.0) << '\n';
}

void writeProvenance(std::ofstream& stateFile,
                     std::ofstream& eventFile,
                     const Parameters& parameters,
                     const kg::LammpsData& data,
                     int stickers,
                     long long startStep) {
  const std::streamsize previousPrecision = stateFile.precision();
  stateFile << std::setprecision(17)
            << "# input_file=" << parameters.input
            << " arms=" << parameters.arms
            << " narm=" << parameters.beadsPerArm
            << " total_particles=" << data.natoms
            << " stickers=" << stickers
            << " permanent_bonds=" << data.nbonds
            << " T=" << parameters.temperature
            << " dt=" << parameters.dt
            << " Ea=" << parameters.ea
            << " Ee=" << parameters.ee
            << " nu0=" << parameters.nu0
            << " Nevery=" << parameters.every
            << " diagnostic_every=" << parameters.diagnosticEvery
            << " r_assoc=" << parameters.rAssoc
            << " damping=" << parameters.damping
            << " K=" << parameters.feneK
            << " R0=" << parameters.feneR0
            << " seed=" << parameters.seed
            << " start_step=" << startStep
            << " total_requested_steps=" << startStep + parameters.steps << '\n';
  stateFile.precision(previousPrecision);
  eventFile << std::setprecision(17)
            << "# input_file=" << parameters.input
            << " arms=" << parameters.arms
            << " narm=" << parameters.beadsPerArm
            << " total_particles=" << data.natoms
            << " stickers=" << stickers
            << " permanent_bonds=" << data.nbonds
            << " T=" << parameters.temperature
            << " dt=" << parameters.dt
            << " Ea=" << parameters.ea
            << " Ee=" << parameters.ee
            << " nu0=" << parameters.nu0
            << " Nevery=" << parameters.every
            << " r_assoc=" << parameters.rAssoc
            << " damping=" << parameters.damping
            << " K=" << parameters.feneK
            << " R0=" << parameters.feneR0
            << " seed=" << parameters.seed
            << " start_step=" << startStep
            << " total_requested_steps=" << startStep + parameters.steps
            << " original_lammps_atom_ids=1_based\n";
  eventFile.precision(previousPrecision);
}

class StarComWriter {
 public:
  StarComWriter(const kg::LammpsData& data, const kg_assoc::BoxLengths& lengths)
      : lengths_(lengths) {
    for (int id = 0; id < data.natoms; ++id) {
      if (data.type[id] == 1 || data.type[id] == 2) {
        starParticles_[data.mol[id]].push_back(id);
      }
    }
  }

  void write(long long step, double time,
             std::shared_ptr<uammd::ParticleData> particles,
             std::ostream& output) {
    auto positions = particles->getPos(uammd::access::cpu, uammd::access::read);
    auto idToIndex = particles->getIdOrderedIndices(uammd::access::cpu);
    for (const auto& star : starParticles_) {
      const uammd::real3 anchor = uammd::make_real3(positions[idToIndex[star.second.front()]]);
      uammd::real3 wrappedCom = uammd::make_real3(uammd::real(0.0));
      for (const int id : star.second) {
        const uammd::real3 position = uammd::make_real3(positions[idToIndex[id]]);
        wrappedCom += anchor + uammd::make_real3(
            kg_assoc::minimumImage(position.x - anchor.x, lengths_.x),
            kg_assoc::minimumImage(position.y - anchor.y, lengths_.y),
            kg_assoc::minimumImage(position.z - anchor.z, lengths_.z));
      }
      wrappedCom /= static_cast<uammd::real>(star.second.size());
      uammd::real3 unwrappedCom = wrappedCom;
      const auto previous = previousWrapped_.find(star.first);
      if (previous != previousWrapped_.end()) {
        unwrappedCom = unwrappedCom_[star.first] + uammd::make_real3(
            kg_assoc::minimumImage(wrappedCom.x - previous->second.x, lengths_.x),
            kg_assoc::minimumImage(wrappedCom.y - previous->second.y, lengths_.y),
            kg_assoc::minimumImage(wrappedCom.z - previous->second.z, lengths_.z));
      }
      previousWrapped_[star.first] = wrappedCom;
      unwrappedCom_[star.first] = unwrappedCom;
      output << step << ' ' << std::setprecision(17) << time << ' ' << star.first
             << ' ' << unwrappedCom.x << ' ' << unwrappedCom.y << ' ' << unwrappedCom.z
             << '\n';
    }
  }

 private:
  kg_assoc::BoxLengths lengths_;
  std::map<int, std::vector<int>> starParticles_;
  std::map<int, uammd::real3> previousWrapped_;
  std::map<int, uammd::real3> unwrappedCom_;
};

void writeTopologyFrame(std::ostream& output, long long step, double time,
                        const kg::LammpsData& data,
                        const kg_assoc::StickerState& state) {
  int bonds = 0;
  for (const int first : state.stickers()) {
    bonds += state.partner(first) > first;
  }
  output << "FRAME " << step << ' ' << std::setprecision(17) << time << ' ' << bonds << '\n';
  for (const int first : state.stickers()) {
    const int second = state.partner(first);
    if (second > first) {
      output << first + 1 << ' ' << second + 1 << ' ' << data.mol[first] << ' '
             << data.mol[second] << '\n';
    }
  }
}

}  // namespace

int main(int argc, char** argv) {
  try {
    Parameters parameters = parseArguments(argc, argv);
    if (parameters.selfTest) {
      if (!parameters.rAssocExplicit &&
          parameters.rAssoc != kg_assoc::kDefaultReactionCutoff) {
        throw std::runtime_error("default reaction cutoff regression failed");
      }
      runSelfTest();
      return 0;
    }

    RestartMetadata restart;
    long long initialStep = 0;
    if (!parameters.restartPrefix.empty()) {
      restart = readRestartMetadata(parameters.restartPrefix + ".assoc_restart");
      if (parameters.rAssocExplicit && !near(parameters.rAssoc, restart.parameters.rAssoc)) {
        throw std::runtime_error("--r-assoc does not match restart metadata");
      }
      if (parameters.seedExplicit && parameters.seed != restart.parameters.seed) {
        throw std::runtime_error("--seed does not match restart metadata");
      }
      const int requestedDiagnosticEvery = parameters.diagnosticEvery;
      parameters.arms = restart.parameters.arms;
      parameters.beadsPerArm = restart.parameters.beadsPerArm;
      parameters.dt = restart.parameters.dt;
      parameters.temperature = restart.parameters.temperature;
      parameters.ea = restart.parameters.ea;
      parameters.ee = restart.parameters.ee;
      parameters.nu0 = restart.parameters.nu0;
      parameters.every = restart.parameters.every;
      parameters.rAssoc = restart.parameters.rAssoc;
      parameters.damping = restart.parameters.damping;
      parameters.feneK = restart.parameters.feneK;
      parameters.feneR0 = restart.parameters.feneR0;
      parameters.seed = restart.parameters.seed;
      parameters.diagnosticEvery = requestedDiagnosticEvery;
      parameters.input = parameters.restartPrefix + ".restart.lammpsdat";
      initialStep = restart.completedSteps;
    }
    const kg::LammpsData data = kg::readLammpsDataFile(parameters.input);
    const kg_assoc::StarTopologyReport topology = kg_assoc::auditStarTopology(
        data, {parameters.arms, parameters.beadsPerArm});
    const std::vector<int> stickerIds = kg_assoc::extractStickerIds(data);
    if (static_cast<int>(stickerIds.size()) != topology.stickers) {
      throw std::runtime_error("type-2 sticker extraction disagrees with S0 audit");
    }
    const std::set<std::pair<int, int>> permanentBonds =
        kg_assoc::permanentBondPairs(data);

    const std::string statePath = parameters.output + ".state";
    const std::string eventPath = parameters.output + ".events";
    const std::string modulusPath = parameters.output + ".stress_correlator";
    const std::string comSamplesPath = parameters.output + ".com_samples";
    const std::string comTrajectoryPath = parameters.output + ".com_trajectory";
    const std::string topologyPath = parameters.output + ".topology";
    const std::string finalSnapshotPath = parameters.output + ".final_permanent.lammpsdat";
    const std::string finalAssociationsPath = parameters.output + ".final_associations";
    const std::string restartSnapshotPath = parameters.output + ".restart.lammpsdat";
    const std::string restartMetadataPath = parameters.output + ".assoc_restart";
    if (!parameters.force && (std::ifstream(statePath) || std::ifstream(eventPath) ||
                              std::ifstream(finalSnapshotPath) ||
                              std::ifstream(finalAssociationsPath) ||
                              std::ifstream(restartSnapshotPath) ||
                              std::ifstream(restartMetadataPath))) {
      throw std::runtime_error("output exists; choose a new --output or use --force");
    }
    std::ofstream stateFile(statePath);
    std::ofstream eventFile(eventPath);
    std::ofstream modulusFile(modulusPath);
    std::ofstream comSamplesFile(comSamplesPath);
    std::ofstream comTrajectoryFile(comTrajectoryPath);
    std::ofstream topologyFile(topologyPath);
    if (!stateFile || !eventFile || !modulusFile || !comSamplesFile ||
        !comTrajectoryFile || !topologyFile) {
      throw std::runtime_error("cannot open S1 output files");
    }

    auto system = std::make_shared<uammd::System>(argc, argv);
    system->rng().setSeed(parameters.seed);
    const kg::SimulationBox simulationBox = kg::makeSimulationBox(data);
    const auto particles = kg::createParticleDataFromLammps(data, system, simulationBox);
    const kg_assoc::BoxLengths lengths{
        data.xhi - data.xlo, data.yhi - data.ylo, data.zhi - data.zlo};
    StarComWriter comWriter(data, lengths);
    comSamplesFile << "# step time molecule_id com_x com_y com_z\n";
    comTrajectoryFile << "# step time molecule_id com_x com_y com_z\n";
    topologyFile << "# FRAME step time active_pairs; pairs: atom_i atom_j molecule_i molecule_j\n";
    const std::string permanentBondData =
        kg::buildUammdBondDataFromLammps(data, parameters.feneK, parameters.feneR0);

    const auto wca = kg::createWCAStressInteractor_CellList(
        particles, simulationBox.box, data.atomTypes, 1.0, 1.0, parameters.skin);
    const auto permanentFene = kg::createFENEStressInteractor(
        particles, simulationBox.box, data.bonds, parameters.feneK, parameters.feneR0);
    kg_assoc::StickerState state(data.natoms, stickerIds);
    if (!parameters.restartPrefix.empty()) {
      std::vector<int> partners(data.natoms, -1);
      for (const auto& bond : restart.activeBonds) {
        const int first = bond.first - 1;
        const int second = bond.second - 1;
        if (first < 0 || second < 0 || first >= data.natoms || second >= data.natoms ||
            partners[first] != -1 || partners[second] != -1) {
          throw std::runtime_error("invalid temporary partner IDs in restart");
        }
        partners[first] = second;
        partners[second] = first;
      }
      state.loadPartners(partners);
    }
    const auto associating = std::make_shared<kg_assoc::AssociatingFENEInteractor>(
        particles, simulationBox.box, state.devicePartner(), parameters.feneK,
        parameters.feneR0, parameters.ee,
        kg_assoc::rstar(parameters.feneK, parameters.feneR0));

    using NVT = uammd::VerletNVT::GronbechJensen;
    NVT::Parameters integratorParameters;
    integratorParameters.temperature = static_cast<uammd::real>(parameters.temperature);
    integratorParameters.friction = static_cast<uammd::real>(1.0 / parameters.damping);
    integratorParameters.dt = static_cast<uammd::real>(parameters.dt);
    integratorParameters.initVelocities = false;
    const auto integrator = std::make_shared<NVT>(particles, integratorParameters);
    integrator->addInteractor(wca);
    integrator->addInteractor(permanentFene);
    integrator->addInteractor(associating);

    kg_assoc::Kinetics kinetics(
        {parameters.nu0, parameters.ea, parameters.temperature, parameters.dt,
         parameters.every, parameters.seed},
        parameters.feneK, parameters.feneR0, parameters.ee);

    Correlator6 stressCorrelator;
    stressCorrelator.setsize(40, 16, 2);
    stressCorrelator.initialize();
    constexpr int stressBufferSize = 4096;
    constexpr int stressReductionThreads = 256;
    const int stressReductionBlocks =
        (data.natoms + stressReductionThreads - 1) / stressReductionThreads;
    thrust::device_vector<kg::detail::StressTensorSample> stressSamplesDevice(
        stressBufferSize);
    thrust::device_vector<kg::detail::StressTensorSample> stressPartialSumsDevice(
        stressReductionBlocks);
    std::vector<kg::detail::StressTensorSample> stressSamplesHost(stressBufferSize);
    int bufferedStressSamples = 0;
    long long stressSamplesQueued = 0;
    const cudaStream_t samplingStream = integrator->getStream();
    auto flushStressSamples = [&]() {
      if (bufferedStressSamples == 0) {
        return;
      }
      CudaSafeCall(cudaStreamSynchronize(samplingStream));
      CudaSafeCall(cudaMemcpy(stressSamplesHost.data(),
                              thrust::raw_pointer_cast(stressSamplesDevice.data()),
                              sizeof(kg::detail::StressTensorSample) * bufferedStressSamples,
                              cudaMemcpyDeviceToHost));
      for (int index = 0; index < bufferedStressSamples; ++index) {
        const auto& stress = stressSamplesHost[index];
        stressCorrelator.add(stress.xy, stress.xz, stress.yz,
                             stress.xx - stress.yy, stress.xx - stress.zz,
                             stress.yy - stress.zz);
      }
      bufferedStressSamples = 0;
    };
    auto queueStressSample = [&]() {
      if (bufferedStressSamples == stressBufferSize) {
        flushStressSamples();
      }
      wca->sum({.force = false, .energy = false, .virial = false, .stress = true},
               samplingStream);
      permanentFene->sum(
          {.force = false, .energy = false, .virial = false, .stress = true},
          samplingStream);
      associating->sum(
          {.force = false, .energy = false, .virial = false, .stress = true},
          samplingStream);
      kg::appendStressTensorSampleAsync(
          particles, simulationBox, wca, permanentFene, associating,
          thrust::raw_pointer_cast(stressPartialSumsDevice.data()),
          thrust::raw_pointer_cast(stressSamplesDevice.data()) + bufferedStressSamples,
          samplingStream);
      ++bufferedStressSamples;
      ++stressSamplesQueued;
    };

    stateFile << "# timestep time N_free_stickers N_assoc_bonds creations breaks N_intra N_inter bound_fraction connected_components largest_cluster_size largest_cluster_fraction mean_degree second_degree_moment L1 L2 active_bond_observations max_active_bond_distance fraction_active_gt_1p25 fraction_active_gt_1p30 fraction_active_gt_1p40\n";
    eventFile << "# timestep event_type sticker_i sticker_j molecule_i molecule_j\n";
    writeProvenance(stateFile, eventFile, parameters, data,
                    static_cast<int>(stickerIds.size()), initialStep);

    long long creations = restart.creations;
    long long breaks = restart.breaks;
    long long chemistrySweeps = 0;
    long long candidatePairs = 0;
    kg_assoc::ActiveBondDistanceDiagnostics distanceDiagnostics;
    kg_assoc::AssociationCounts counts = kg_assoc::checkAssociationInvariants(
        particles, data, state, permanentBonds, lengths, parameters.feneR0, creations, breaks);
    const kg_assoc::MolecularNetworkObservables initialNetwork =
        kg_assoc::molecularNetworkObservables(data, state);
    writeState(stateFile, initialStep, parameters, counts, initialNetwork, distanceDiagnostics,
               static_cast<int>(stickerIds.size()), creations, breaks);

    const auto start = std::chrono::steady_clock::now();
    for (int step = 1; step <= parameters.steps; ++step) {
      const long long absoluteStep = initialStep + step;
      integrator->forwardTime();
      const bool chemistryStep = absoluteStep % parameters.every == 0;
      const bool diagnosticStep = absoluteStep % parameters.diagnosticEvery == 0;
      if (chemistryStep || diagnosticStep) {
        CudaSafeCall(cudaStreamSynchronize(integrator->getStream()));
      }
      if ((chemistryStep || diagnosticStep) && associating->hasInvalidFene()) {
        const auto pair = associating->invalidFenePair();
        throw std::runtime_error("associating FENE kernel invalid: atom IDs " +
                                 std::to_string(pair.first + 1) + " and " +
                                 std::to_string(pair.second + 1) + " r=" +
                                 std::to_string(kg_assoc::stickerDistance(
                                     particles, pair.first, pair.second, lengths)));
      }

      if (chemistryStep) {
        std::vector<kg_assoc::Candidate> candidates = kg_assoc::findStickerCandidates(
            particles, state, lengths, parameters.rAssoc);
        candidatePairs += static_cast<long long>(candidates.size());
        ++chemistrySweeps;
        std::vector<kg_assoc::Event> acceptedEvents;
        kinetics.update(absoluteStep, state, std::move(candidates), acceptedEvents);
        for (const kg_assoc::Event& event : acceptedEvents) {
          const int firstLammpsId = event.first + 1;
          const int secondLammpsId = event.second + 1;
          eventFile << event.step << ' ' << event.type << ' ' << firstLammpsId << ' '
                    << secondLammpsId << ' ' << data.mol.at(event.first) << ' '
                    << data.mol.at(event.second) << '\n';
          if (event.type == 'C') {
            ++creations;
          } else if (event.type == 'B') {
            ++breaks;
          } else {
            throw std::runtime_error("unknown kinetic event type");
          }
        }
      }
      // Stress is sampled after chemistry at this MD step, so its temporary
      // FENE cache and topology output use the same partner state.
      queueStressSample();
      if (chemistryStep || diagnosticStep) {
        counts = kg_assoc::checkAssociationInvariants(
            particles, data, state, permanentBonds, lengths, parameters.feneR0,
            creations, breaks);
      }
      if (diagnosticStep) {
        kg_assoc::observeActiveBondDistances(
            particles, state, lengths, distanceDiagnostics);
        const kg_assoc::MolecularNetworkObservables network =
            kg_assoc::molecularNetworkObservables(data, state);
        writeState(stateFile, absoluteStep, parameters, counts, network, distanceDiagnostics,
                   static_cast<int>(stickerIds.size()), creations, breaks);
      }
      if (absoluteStep % parameters.comEvery == 0 ||
          absoluteStep % parameters.frameEvery == 0) {
        CudaSafeCall(cudaStreamSynchronize(samplingStream));
        if (absoluteStep % parameters.comEvery == 0) {
          comWriter.write(absoluteStep, absoluteStep * parameters.dt, particles,
                          comSamplesFile);
        }
        if (absoluteStep % parameters.frameEvery == 0) {
          comWriter.write(absoluteStep, absoluteStep * parameters.dt, particles,
                          comTrajectoryFile);
          writeTopologyFrame(topologyFile, absoluteStep, absoluteStep * parameters.dt,
                             data, state);
        }
      }
    }

    flushStressSamples();
    stressCorrelator.evaluate();
    const double volume = static_cast<double>(simulationBox.box.getVolume());
    modulusFile << "# stress_samples=" << stressSamplesQueued
                << " step0_sampled=no stress_interval_steps=1 dt="
                << std::setprecision(17) << parameters.dt << '\n';
    modulusFile << "# time Gxy Gxz Gyz GNxy GNxz GNyz G\n";
    for (unsigned int index = 0; index < stressCorrelator.npcorr; ++index) {
      const double gxy = volume * stressCorrelator.getf(index, 0);
      const double gxz = volume * stressCorrelator.getf(index, 1);
      const double gyz = volume * stressCorrelator.getf(index, 2);
      const double gnxy = volume * stressCorrelator.getf(index, 3);
      const double gnxz = volume * stressCorrelator.getf(index, 4);
      const double gnyz = volume * stressCorrelator.getf(index, 5);
      const double modulus =
          (gxy + gxz + gyz) / (5.0 * parameters.temperature) +
          (gnxy + gnxz + gnyz) / (30.0 * parameters.temperature);
      modulusFile << stressCorrelator.gett(index) * parameters.dt << ' '
                  << gxy << ' ' << gxz << ' ' << gyz << ' ' << gnxy << ' '
                  << gnxz << ' ' << gnyz << ' ' << modulus << '\n';
    }
    CudaSafeCall(cudaStreamSynchronize(integrator->getStream()));
    if (associating->hasInvalidFene()) {
      const auto pair = associating->invalidFenePair();
      throw std::runtime_error("associating FENE kernel invalid at final step: atom IDs " +
                               std::to_string(pair.first + 1) + " and " +
                               std::to_string(pair.second + 1));
    }
    counts = kg_assoc::checkAssociationInvariants(
        particles, data, state, permanentBonds, lengths, parameters.feneR0,
        creations, breaks);
    if ((initialStep + parameters.steps) % parameters.diagnosticEvery != 0) {
      kg_assoc::observeActiveBondDistances(particles, state, lengths, distanceDiagnostics);
      const kg_assoc::MolecularNetworkObservables network =
          kg_assoc::molecularNetworkObservables(data, state);
      writeState(stateFile, initialStep + parameters.steps, parameters, counts, network,
                 distanceDiagnostics, static_cast<int>(stickerIds.size()), creations, breaks);
    }
    stateFile << "# chemistry_sweeps=" << chemistrySweeps
              << " candidate_sticker_pairs=" << candidatePairs
              << " mean_candidate_sticker_pairs="
              << (chemistrySweeps == 0 ? 0.0 :
                  static_cast<double>(candidatePairs) / chemistrySweeps) << '\n';
    kg::writeLAMMPSDataSnapshot(
        finalSnapshotPath, initialStep + parameters.steps, data,
        particles, "kg_assoc_e2_permanent_only");
    kg::writeLAMMPSDataSnapshot(
        restartSnapshotPath, initialStep + parameters.steps, data,
        particles, "kg_assoc_e2_restart_snapshot");
    writeRestartMetadata(restartMetadataPath, parameters, initialStep + parameters.steps,
                         creations, breaks, state);
    std::ofstream activeBondsFile(finalAssociationsPath);
    if (!activeBondsFile) {
      throw std::runtime_error("cannot open final active-association record");
    }
    activeBondsFile << "# Mirror of " << restartMetadataPath << "; use --restart-prefix "
                    << parameters.output << " to reload.\n";
    activeBondsFile << "# atom_i atom_j molecule_i molecule_j\n";
    for (const int first : state.stickers()) {
      const int second = state.partner(first);
      if (second > first) {
        activeBondsFile << first + 1 << ' ' << second + 1 << ' '
                        << data.mol.at(first) << ' ' << data.mol.at(second) << '\n';
      }
    }
    const double wallSeconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    std::cout << kg_assoc::formatStarTopologyReport(topology);
    std::cout << "S1 total_timesteps " << parameters.steps
              << " wall_seconds " << wallSeconds
              << " particle_timesteps_per_second "
              << static_cast<double>(data.natoms) * parameters.steps / wallSeconds
              << " chemistry_sweeps " << chemistrySweeps
              << " mean_candidate_sticker_pairs "
              << (chemistrySweeps == 0 ? 0.0 :
                  static_cast<double>(candidatePairs) / chemistrySweeps)
              << " creations " << creations
              << " breaks " << breaks
              << " final_associating_bonds " << counts.bonds
              << " final_intra_star_bonds " << counts.intraStarBonds
              << " final_inter_star_bonds " << counts.interStarBonds << '\n';
    if (creations == 0 || breaks == 0) {
      throw std::runtime_error("S1 smoke requires at least one creation and one break");
    }
    std::cout << "STAR_ASSOCIATION_SMOKE PASS\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "STAR_ASSOCIATION_SMOKE FAIL: " << error.what() << '\n';
    return 1;
  }
}
