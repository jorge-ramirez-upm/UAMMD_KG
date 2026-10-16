#include <uammd.cuh>

#include "Integrator/VerletNVT.cuh"
#include "../KG/kg_interactors.cuh"
#include "../KG/kg_runtime.cuh"
#include "kg_assoc_interactors.cuh"
#include "kg_assoc_star_runtime.cuh"
#include "kg_assoc_conformation.cuh"
#include "kg_assoc_ea_switch.cuh"
#include "kg_assoc_chemical_reseed.cuh"
#ifdef KG_ASSOC_VALIDATE_CANDIDATES
#include "kg_assoc_candidate_oracle.cuh"
#endif

#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <functional>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
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
  std::string output = "s1_smoke";
  int arms = 0;
  int beadsPerArm = 0;
  int steps = 100000;
  int every = 100;
  int diagnosticEvery = 1000;
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
  unsigned long long mdSeed = 0;
  bool force = false;
  bool selfTest = false;
  bool rAssocExplicit = false;
  bool seedExplicit = false;
  bool eaExplicit = false;
  bool eeExplicit = false;
  std::string derivedBranchId;
  bool reseedChemistry = false;
  bool referenceControl = false;
  bool validateInitialState = false;
  unsigned long long parentChemicalSeed = 0;
  long long branchOriginStep = 0;
  long long parentCreations = 0;
  long long parentBreaks = 0;
  std::set<std::string> explicitPhysics;
  bool switchEa = false;
  double switchEaFrom = 0.0;
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

unsigned long long parseSeed(const std::string& value) {
  if (value.empty() || value.find_first_not_of("0123456789") != std::string::npos) {
    throw std::runtime_error("seed must be an unsigned decimal integer");
  }
  return std::stoull(value);
}

void printHelp() {
  std::cout << "kg_assoc_stars (--input FILE | --restart-prefix PREFIX) [options]\n"
            << "  --steps N --dt DT --temperature T --Ea E --Ee E --nu0 X\n"
            << "  --Nevery N --r-assoc R --damp D --K K --R0 R --seed S\n"
            << "  --diagnostic-every N --md-seed S (fresh MD stream; chemistry seed unchanged)\n"
            << "  --switch-ea-from E --Ea E (explicit restart kinetics switch)\n"
            << "  --reseed-chemistry-from OLD --seed NEW (guarded Ea transfer)\n"
            << "  --reference-control (explicit Ea4 reseeded validation control)\n"
            << "  --validate-initial-state (host-only; creates no outputs)\n"
            << "  --md-seed-info S (host-only effective kernel seed)\n"
            << "  --restart-prefix PREFIX --output PREFIX --force --self-test\n";
}

Parameters parseArguments(int argc, char** argv) {
  Parameters parameters;
  for (int index = 1; index < argc; ++index) {
    const std::string option = argv[index];
    parameters.explicitPhysics.insert(option);
    if (option == "--derived-branch-id") {
      parameters.derivedBranchId = nextArgument(index, argc, argv);
    } else if (option == "--reseed-chemistry-from") {
      parameters.parentChemicalSeed = parseSeed(nextArgument(index, argc, argv));
      parameters.reseedChemistry = true;
    } else if (option == "--reference-control") {
      parameters.referenceControl = true;
    } else if (option == "--validate-initial-state") {
      parameters.validateInitialState = true;
    } else if (option == "--input") {
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
      parameters.eaExplicit = true;
    } else if (option == "--switch-ea-from") {
      parameters.switchEaFrom = std::stod(nextArgument(index, argc, argv));
      parameters.switchEa = true;
    } else if (option == "--Ee") {
      parameters.ee = std::stod(nextArgument(index, argc, argv));
      parameters.eeExplicit = true;
    } else if (option == "--nu0") {
      parameters.nu0 = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--Nevery") {
      parameters.every = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--diagnostic-every") {
      parameters.diagnosticEvery = std::stoi(nextArgument(index, argc, argv));
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
      parameters.seed = parseSeed(nextArgument(index, argc, argv));
      parameters.seedExplicit = true;
    } else if (option == "--md-seed") {
      parameters.mdSeed = parseSeed(nextArgument(index, argc, argv));
      if (parameters.mdSeed == 0) {
        throw std::runtime_error("--md-seed must be positive");
      }
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
  if (parameters.switchEa && (parameters.restartPrefix.empty() || !parameters.eaExplicit)) {
    throw std::runtime_error("Ea switching requires --restart-prefix and --Ea");
  }
  if ((parameters.reseedChemistry || parameters.referenceControl) &&
      (parameters.restartPrefix.empty() || !parameters.eaExplicit || parameters.force)) {
    throw std::runtime_error("derived reseeding requires restart, explicit Ea and no --force");
  }
  if ((!parameters.derivedBranchId.empty() && !parameters.reseedChemistry) ||
      (parameters.reseedChemistry && parameters.derivedBranchId.empty())) {
    throw std::runtime_error("derived branch identity requires explicit chemical reseeding");
  }
  if (parameters.validateInitialState && parameters.restartPrefix.empty()) {
    throw std::runtime_error("initial-state inspection requires a restart");
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
      parameters.diagnosticEvery <= 0 || parameters.dt <= 0.0 ||
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
  std::vector<std::string> arguments{
      "kg_assoc_stars", "--restart-prefix", "unused", "--seed", "22001", "--md-seed", "32001"};
  std::vector<char*> pointers;
  for (auto& argument : arguments) {
    pointers.push_back(&argument[0]);
  }
  const auto seeded = parseArguments(static_cast<int>(pointers.size()), pointers.data());
  if (seeded.seed != 22001 || seeded.mdSeed != 32001) {
    throw std::runtime_error("independent MD/chemistry seed parsing regression failed");
  }
  if (kg_assoc::restartEa(4.0, 8.0, true, true, 4.0) != 8.0 ||
      kg_assoc::restartEa(6.0, 4.0, false, false, 0.0) != 6.0) {
    throw std::runtime_error("explicit Ea switching regression failed");
  }
  expectReject("unmarked Ea switch", []() {
    kg_assoc::restartEa(4.0, 8.0, true, false, 0.0);
  });
  expectReject("wrong parent Ea", []() {
    kg_assoc::restartEa(4.0, 8.0, true, true, 6.0);
  });
  kg::LammpsData shape;
  shape.natoms = 4;
  shape.type = {1, 2, 2, 2};
  shape.mol = {1, 1, 1, 1};
  shape.bonds = {{1, 2}, {1, 3}, {1, 4}};
  const auto shapeTopology = kg_assoc::conformationTopology(shape, 3);
  const std::vector<std::array<double, 3>> shapePositions = {
      {{3.75, 0.0, 0.0}}, {{-3.45, 0.0, 0.0}},
      {{3.75, 0.8, 0.0}}, {{3.75, 0.0, 0.8}}};
  const auto means = kg_assoc::conformationMeans(shapeTopology, shapePositions, {8, 8, 8});
  if (!near(means.first, 0.36) || !near(means.second, 0.64)) {
    throw std::runtime_error("PBC conformation regression failed");
  }
  auto shiftedShape = shapePositions;
  shiftedShape[1][0] += 24.0;
  shiftedShape[2][1] -= 16.0;
  const auto shiftedMeans = kg_assoc::conformationMeans(shapeTopology, shiftedShape, {8, 8, 8});
  if (!near(shiftedMeans.first, means.first) || !near(shiftedMeans.second, means.second)) {
    throw std::runtime_error("image-invariant conformation regression failed");
  }
  for (const double ea : {4.0, 6.0, 8.0, 10.0}) {
    const double q = kg_assoc::attemptProbability(20.0 * std::exp(-ea));
    const double du = -2.0;
    const double ratio = q * kg_assoc::metropolisFactor(du, 1.0, true) /
        (q * kg_assoc::metropolisFactor(du, 1.0, false));
    if (!near(ratio, std::exp(-du))) {
      throw std::runtime_error("common attempt-factor ratio regression failed");
    }
  }
  std::set<unsigned int> effectiveSeeds;
  for (const auto streamSeed : {22001, 22002, 22003, 32001, 32002, 32003}) {
    uammd::Xorshift128plus rng(streamSeed);
    rng.next32();
    rng.next32();
    const auto effective = rng.next32();
    if (!effectiveSeeds.insert(effective).second) {
      throw std::runtime_error("MD kernel seed collision in recovery policy");
    }
    std::cout << "MD_SEED SELF_TEST requested=" << streamSeed << " effective=" << effective << '\n';
  }
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
            << " ea_switch=" << parameters.switchEa
            << " parent_Ea=" << (parameters.switchEa ? parameters.switchEaFrom : parameters.ea)
            << " md_seed=" << (parameters.mdSeed ? parameters.mdSeed : parameters.seed)
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
            << " ea_switch=" << parameters.switchEa
            << " parent_Ea=" << (parameters.switchEa ? parameters.switchEaFrom : parameters.ea)
            << " md_seed=" << (parameters.mdSeed ? parameters.mdSeed : parameters.seed)
            << " start_step=" << startStep
            << " total_requested_steps=" << startStep + parameters.steps
            << " original_lammps_atom_ids=1_based\n";
  eventFile.precision(previousPrecision);
  if (parameters.reseedChemistry) {
    for (std::ofstream* output : {&stateFile, &eventFile}) {
      *output << "# lineage_mode=Ea_reference_transfer_v1"
              << " branch_id=" << parameters.derivedBranchId
              << " parent_chemistry_seed=" << parameters.parentChemicalSeed
              << " reference_control=" << parameters.referenceControl
              << " branch_origin_step=" << parameters.branchOriginStep
              << " parent_creations=" << parameters.parentCreations
              << " parent_breaks=" << parameters.parentBreaks
              << " branch_age_start=0 bitwise_md_continuation=0\n";
    }
  }
}

void writeConformation(std::ofstream& output, long long step, const Parameters& parameters,
                       std::shared_ptr<uammd::ParticleData> particles,
                       const kg_assoc::ConformationTopology& topology,
                       const kg_assoc::BoxLengths& lengths) {
  auto positions = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto idToIndex = particles->getIdOrderedIndices(uammd::access::cpu);
  std::vector<std::array<double, 3>> ordered(topology.parent.size());
  for (size_t id = 0; id < ordered.size(); ++id) {
    const auto position = positions[idToIndex[id]];
    ordered[id] = {{position.x, position.y, position.z}};
  }
  const auto means = kg_assoc::conformationMeans(topology, ordered, lengths);
  output << std::setprecision(17) << step << ' ' << step * parameters.dt << ' '
         << means.first << ' ' << means.second << '\n';
}

void writeNumerics(std::ofstream& output,
                   long long step,
                   const Parameters& parameters,
                   const kg::LammpsData& data,
                   std::shared_ptr<uammd::ParticleData> particles,
                   std::shared_ptr<uammd::Integrator> integrator,
                   const kg_assoc::BoxLengths& lengths) {
  const double kinetic = kg::detail::sumKineticEnergy(integrator, particles);
  const double temperature = 2.0 * kinetic / (3.0 * data.natoms);
  double minimum = std::numeric_limits<double>::infinity();
  double maximum = 0.0;
  auto positions = particles->getPos(uammd::access::cpu, uammd::access::read);
  auto idToIndex = particles->getIdOrderedIndices(uammd::access::cpu);
  for (const auto& bond : data.bonds) {
    const auto first = positions[idToIndex[bond.first - 1]];
    const auto second = positions[idToIndex[bond.second - 1]];
    const double dx = kg_assoc::minimumImage(second.x - first.x, lengths.x);
    const double dy = kg_assoc::minimumImage(second.y - first.y, lengths.y);
    const double dz = kg_assoc::minimumImage(second.z - first.z, lengths.z);
    const double distance = std::sqrt(dx * dx + dy * dy + dz * dz);
    if (!std::isfinite(distance) || distance <= 0.0 || distance >= parameters.feneR0) {
      throw std::runtime_error("E2 diagnostic found invalid permanent FENE bond");
    }
    minimum = std::min(minimum, distance);
    maximum = std::max(maximum, distance);
  }
  if (!std::isfinite(kinetic) || !std::isfinite(temperature)) {
    throw std::runtime_error("E2 diagnostic found nonfinite kinetic energy");
  }
  output << std::setprecision(17) << step << ' ' << step * parameters.dt << ' '
         << kinetic << ' ' << temperature << ' ' << minimum << ' ' << maximum << '\n';
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 3 && std::string(argv[1]) == "--md-seed-info") {
      const auto seed = std::stoull(argv[2]);
      uammd::Xorshift128plus rng(seed);
      rng.next32();
      rng.next32();
      std::cout << rng.next32() << '\n';
      return 0;
    }
    Parameters parameters = parseArguments(argc, argv);
    if (parameters.selfTest) {
      if (!parameters.rAssocExplicit &&
          parameters.rAssoc != kg_assoc::kDefaultReactionCutoff) {
        throw std::runtime_error("default reaction cutoff regression failed");
      }
      runSelfTest();
      return 0;
    }
#ifdef KG_ASSOC_VALIDATE_CANDIDATES
    if (parameters.steps > 10000) {
      throw std::runtime_error("candidate-oracle smoke executable is limited to 10000 MD steps");
    }
#endif

    RestartMetadata restart;
    long long initialStep = 0;
    if (!parameters.restartPrefix.empty()) {
      restart = readRestartMetadata(parameters.restartPrefix + ".assoc_restart");
      if (parameters.rAssocExplicit && !near(parameters.rAssoc, restart.parameters.rAssoc)) {
        throw std::runtime_error("--r-assoc does not match restart metadata");
      }
      const double targetEa = parameters.referenceControl ? parameters.ea :
          kg_assoc::restartEa(restart.parameters.ea, parameters.ea,
                              parameters.eaExplicit, parameters.switchEa, parameters.switchEaFrom);
      const auto requestedSeed = kg_assoc::restartChemicalSeed(
          restart.parameters.seed, parameters.seed, parameters.seedExplicit,
          parameters.reseedChemistry, parameters.parentChemicalSeed, restart.parameters.ea,
          targetEa, parameters.switchEa, parameters.referenceControl, parameters.mdSeed);
      if (parameters.reseedChemistry) {
        const auto& parent = restart.parameters;
        auto unchanged = [&](const char* option, double requested, double actual) {
          if (parameters.explicitPhysics.count(option) && requested != actual) {
            throw std::runtime_error(std::string("derived physical mismatch: ") + option);
          }
        };
        unchanged("--arms", parameters.arms, parent.arms);
        unchanged("--narm", parameters.beadsPerArm, parent.beadsPerArm);
        unchanged("--dt", parameters.dt, parent.dt);
        unchanged("--temperature", parameters.temperature, parent.temperature);
        unchanged("--Ee", parameters.ee, parent.ee);
        unchanged("--nu0", parameters.nu0, parent.nu0);
        unchanged("--Nevery", parameters.every, parent.every);
        unchanged("--r-assoc", parameters.rAssoc, parent.rAssoc);
        unchanged("--damp", parameters.damping, parent.damping);
        unchanged("--K", parameters.feneK, parent.feneK);
        unchanged("--R0", parameters.feneR0, parent.feneR0);
        if (parent.arms != 4 || parent.beadsPerArm != 10 || parent.ee != 8.0 ||
            parent.dt != .01 || parent.temperature != 1.0 || parent.nu0 != 20.0 ||
            parent.every != 100 || parent.rAssoc != 1.25 || parent.damping != 2.0 ||
            parent.feneK != 30.0 || parent.feneR0 != 1.5 || restart.completedSteps != 8000000) {
          throw std::runtime_error("derived reference physics or absolute step mismatch");
        }
        const std::string systemId = "F04_N010_RP080_EE08_EA" +
            std::string(targetEa < 10 ? "0" : "") + std::to_string(int(targetEa));
        const auto parentSeed = restart.parameters.seed;
        const std::string suffix = ":r00" + std::to_string(parentSeed - 22000);
        if (parentSeed < 22001 || parentSeed > 22003 ||
            parameters.derivedBranchId.find(systemId + ":derived_" + systemId + "_") != 0 ||
            parameters.derivedBranchId.size() < suffix.size() ||
            parameters.derivedBranchId.compare(parameters.derivedBranchId.size() - suffix.size(),
                                               suffix.size(), suffix) != 0 ||
            parameters.derivedBranchId.find_first_not_of(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_:") != std::string::npos) {
          throw std::runtime_error("derived branch/system/parent identity differs");
        }
        parameters.branchOriginStep = restart.completedSteps;
        parameters.parentCreations = restart.creations;
        parameters.parentBreaks = restart.breaks;
      }
      const double requestedEa = targetEa;
      if (parameters.eeExplicit && parameters.ee != restart.parameters.ee) {
        throw std::runtime_error("--Ee does not match restart metadata");
      }
      const int requestedDiagnosticEvery = parameters.diagnosticEvery;
      parameters.arms = restart.parameters.arms;
      parameters.beadsPerArm = restart.parameters.beadsPerArm;
      parameters.dt = restart.parameters.dt;
      parameters.temperature = restart.parameters.temperature;
      parameters.ea = requestedEa;
      parameters.ee = restart.parameters.ee;
      parameters.nu0 = restart.parameters.nu0;
      parameters.every = restart.parameters.every;
      parameters.rAssoc = restart.parameters.rAssoc;
      parameters.damping = restart.parameters.damping;
      parameters.feneK = restart.parameters.feneK;
      parameters.feneR0 = restart.parameters.feneR0;
      parameters.seed = requestedSeed;
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

    // Validate the decoded initial chemical microstate before any GPU construction.
    if (!parameters.restartPrefix.empty()) {
      if (!data.hasVelocities) {
        throw std::runtime_error("restart requires stored velocities");
      }
      std::set<int> occupied;
      for (const auto& bond : restart.activeBonds) {
        const int first = bond.first - 1;
        const int second = bond.second - 1;
        if (first < 0 || second >= data.natoms || data.type[first] != 2 ||
            data.type[second] != 2 || !occupied.insert(first).second ||
            !occupied.insert(second).second) {
          throw std::runtime_error("invalid reciprocal valence-one initial partners");
        }
        double squared = 0.0;
        for (const auto& axis : {std::make_pair(&data.x, data.xhi - data.xlo),
                                std::make_pair(&data.y, data.yhi - data.ylo),
                                std::make_pair(&data.z, data.zhi - data.zlo)}) {
          const double distance = (*axis.first)[first] - (*axis.first)[second];
          const double image = distance - axis.second * std::round(distance / axis.second);
          squared += image * image;
        }
        if (!std::isfinite(squared) || squared >= parameters.feneR0 * parameters.feneR0) {
          throw std::runtime_error("invalid initial temporary FENE geometry");
        }
      }
    }

    if (parameters.reseedChemistry && (topology.stars != 1000 || data.natoms != 43563)) {
      throw std::runtime_error("derived reference geometry mismatch");
    }
    for (int id = 0; id < data.natoms; ++id) {
      if (!std::isfinite(data.x[id]) || !std::isfinite(data.y[id]) ||
          !std::isfinite(data.z[id]) || (data.hasVelocities &&
          (!std::isfinite(data.vx[id]) || !std::isfinite(data.vy[id]) ||
           !std::isfinite(data.vz[id])))) {
        throw std::runtime_error("nonfinite restart physical state");
      }
    }

    const std::string statePath = parameters.output + ".state";
    const std::string eventPath = parameters.output + ".events";
    const std::string numericsPath = parameters.output + ".numerics.tsv";
    const std::string conformationPath = parameters.output + ".conformation.tsv";
    const std::string finalSnapshotPath = parameters.output + ".final_permanent.lammpsdat";
    const std::string finalAssociationsPath = parameters.output + ".final_associations";
    const std::string restartSnapshotPath = parameters.output + ".restart.lammpsdat";
    const std::string restartMetadataPath = parameters.output + ".assoc_restart";
    if (!parameters.force && (std::ifstream(statePath) || std::ifstream(eventPath) ||
                              std::ifstream(numericsPath) ||
                              std::ifstream(conformationPath) ||
                              std::ifstream(finalSnapshotPath) ||
                              std::ifstream(finalAssociationsPath) ||
                              std::ifstream(restartSnapshotPath) ||
                              std::ifstream(restartMetadataPath))) {
      throw std::runtime_error("output exists; choose a new --output or use --force");
    }
#ifdef KG_ASSOC_VALIDATE_CANDIDATES
    const std::string candidatePath = parameters.output + ".candidate_validation.tsv";
    if (std::ifstream(candidatePath)) {
      throw std::runtime_error("candidate validation output already exists");
    }
#endif
    if (parameters.validateInitialState) {
      // A comparison fingerprint of the actual loader representation, not an auth hash.
      const auto box = kg::makeSimulationBox(data);
      std::uint64_t fingerprint = UINT64_C(14695981039346656037);
      auto mix = [&](const auto& value) {
        const auto* bytes = reinterpret_cast<const unsigned char*>(&value);
        for (std::size_t index = 0; index < sizeof(value); ++index) {
          fingerprint = (fingerprint ^ bytes[index]) * UINT64_C(1099511628211);
        }
      };
      for (int id = 0; id < data.natoms; ++id) {
        const auto position = box.box.apply_pbc(uammd::make_real3(
            uammd::real(data.x[id]) - box.center.x,
            uammd::real(data.y[id]) - box.center.y,
            uammd::real(data.z[id]) - box.center.z));
        mix(id);
        mix(data.type[id]);
        mix(data.mol[id]);
        mix(position.x);
        mix(position.y);
        mix(position.z);
        mix(uammd::real(data.vx[id]));
        mix(uammd::real(data.vy[id]));
        mix(uammd::real(data.vz[id]));
      }
      for (const auto& bond : data.bonds) {
        mix(bond.first);
        mix(bond.second);
      }
      mix(data.xlo);
      mix(data.xhi);
      mix(data.ylo);
      mix(data.yhi);
      mix(data.zlo);
      mix(data.zhi);
      const auto physicalFingerprint = fingerprint;
      fingerprint = UINT64_C(14695981039346656037);
      for (const auto& bond : restart.activeBonds) {
        mix(bond.first);
        mix(bond.second);
      }
      std::cout << "INITIAL_STATE_VALIDATED start_step=" << initialStep
                << " target_Ea=" << parameters.ea << " seed=" << parameters.seed
                << " parent_seed=" << restart.parameters.seed
                << " creations=" << restart.creations << " breaks=" << restart.breaks
                << " active_bonds=" << restart.activeBonds.size()
                << " particles=" << data.natoms << " physical_fingerprint=" << std::hex
                << physicalFingerprint << " chemical_fingerprint=" << fingerprint
                << std::dec << " branch_age=0 bitwise_md_continuation=0\n";
      return 0;
    }
    std::ofstream stateFile(statePath);
    std::ofstream eventFile(eventPath);
    std::ofstream numericsFile(numericsPath);
    std::ofstream conformationFile(conformationPath);
#ifdef KG_ASSOC_VALIDATE_CANDIDATES
    std::ofstream candidateFile(candidatePath);
    if (!candidateFile) {
      throw std::runtime_error("cannot write candidate validation");
    }
    candidateFile << "# step candidates oracle_verified_active_candidates\n";
#endif
    if (!stateFile || !eventFile || !numericsFile || !conformationFile) {
      throw std::runtime_error("cannot open S1 output files");
    }

    auto system = std::make_shared<uammd::System>(argc, argv);
    system->rng().setSeed(parameters.seed);
    const kg::SimulationBox simulationBox = kg::makeSimulationBox(data);
    const auto particles = kg::createParticleDataFromLammps(data, system, simulationBox);
    const auto conformationTopology = kg_assoc::conformationTopology(data, parameters.arms);
    const kg_assoc::BoxLengths lengths{
        data.xhi - data.xlo, data.yhi - data.ylo, data.zhi - data.zlo};
    const std::string permanentBondData =
        kg::buildUammdBondDataFromLammps(data, parameters.feneK, parameters.feneR0);

    const auto wca = kg::createWCAInteractor_CellList(
        particles, simulationBox.box, data.atomTypes, 1.0, 1.0, parameters.skin);
    const auto permanentFene = kg::createFENEInteractor(
        particles, simulationBox.box, permanentBondData);
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
    // Reseed only MD initialization; chemistry remains keyed to its restored seed.
    if (parameters.mdSeed != 0) {
      system->rng().setSeed(parameters.mdSeed);
    }
    auto mdRng = system->rng();
    mdRng.next32();
    mdRng.next32();
    const auto effectiveMdSeed = mdRng.next32();
    system->log<uammd::System::MESSAGE>(
        "[E2 MD stream] requested_seed=%llu effective_seed=%u internal_start_step=0",
        parameters.mdSeed ? parameters.mdSeed : parameters.seed, effectiveMdSeed);
    const auto integrator = std::make_shared<NVT>(particles, integratorParameters);
    integrator->addInteractor(wca);
    integrator->addInteractor(permanentFene);
    integrator->addInteractor(associating);

    kg_assoc::Kinetics kinetics(
        {parameters.nu0, parameters.ea, parameters.temperature, parameters.dt,
         parameters.every, parameters.seed},
        parameters.feneK, parameters.feneR0, parameters.ee);

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
    numericsFile << "# step time kinetic_energy temperature min_permanent_bond "
                    "max_permanent_bond\n";
    writeNumerics(numericsFile, initialStep, parameters, data, particles, integrator, lengths);
    conformationFile << "# step time mean_rg2 mean_center_terminal_r2\n";
    writeConformation(conformationFile, initialStep, parameters, particles,
                      conformationTopology, lengths);

    const auto start = std::chrono::steady_clock::now();
    for (int step = 1; step <= parameters.steps; ++step) {
      const long long absoluteStep = initialStep + step;
      integrator->forwardTime();
      const bool chemistryStep = absoluteStep % parameters.every == 0;
      const bool diagnosticStep = absoluteStep % parameters.diagnosticEvery == 0;
      if (!chemistryStep && !diagnosticStep) {
        continue;
      }
      CudaSafeCall(cudaStreamSynchronize(integrator->getStream()));
      if (associating->hasInvalidFene()) {
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
#ifdef KG_ASSOC_VALIDATE_CANDIDATES
        const auto eligibleActive = kg_assoc_test::checkSweep(
            particles, state, lengths, parameters.rAssoc, candidates);
        candidateFile << absoluteStep << ' ' << candidates.size() << ' ' << eligibleActive << '\n';
#endif
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
      counts = kg_assoc::checkAssociationInvariants(
          particles, data, state, permanentBonds, lengths, parameters.feneR0,
          creations, breaks);
      if (diagnosticStep) {
        kg_assoc::observeActiveBondDistances(
            particles, state, lengths, distanceDiagnostics);
        const kg_assoc::MolecularNetworkObservables network =
            kg_assoc::molecularNetworkObservables(data, state);
        writeState(stateFile, absoluteStep, parameters, counts, network, distanceDiagnostics,
                   static_cast<int>(stickerIds.size()), creations, breaks);
        writeNumerics(numericsFile, absoluteStep, parameters, data, particles, integrator, lengths);
        writeConformation(conformationFile, absoluteStep, parameters, particles,
                          conformationTopology, lengths);
      }
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
      writeNumerics(numericsFile, initialStep + parameters.steps, parameters, data,
                    particles, integrator, lengths);
      writeConformation(conformationFile, initialStep + parameters.steps, parameters, particles,
                        conformationTopology, lengths);
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
