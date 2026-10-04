#include <uammd.cuh>

#include "Integrator/VerletNVT.cuh"
#include "../KG/kg_interactors.cuh"
#include "../KG/kg_runtime.cuh"
#include "kg_assoc_interactors.cuh"
#include "kg_assoc_star_runtime.cuh"

#include <chrono>
#include <cmath>
#include <functional>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Parameters {
  std::string input;
  std::string output = "s1_smoke";
  int arms = 0;
  int beadsPerArm = 0;
  int steps = 100000;
  int every = 100;
  double dt = 0.01;
  double temperature = 1.0;
  double ea = 4.0;
  double ee = 8.0;
  double nu0 = 20.0;
  double rAssoc = std::pow(2.0, 1.0 / 6.0);
  double damping = 2.0;
  double feneK = 30.0;
  double feneR0 = 1.5;
  double skin = 0.4;
  unsigned long long seed = 12345;
  bool force = false;
  bool selfTest = false;
};

std::string nextArgument(int& index, int argc, char** argv) {
  if (++index >= argc) {
    throw std::runtime_error("missing option value");
  }
  return argv[index];
}

void printHelp() {
  std::cout << "kg_assoc_stars --input FILE --arms NA --narm NARM [options]\n"
            << "  --steps N --dt DT --temperature T --Ea E --Ee E --nu0 X\n"
            << "  --Nevery N --r-assoc R --damp D --K K --R0 R --seed S\n"
            << "  --output PREFIX --force --self-test\n";
}

Parameters parseArguments(int argc, char** argv) {
  Parameters parameters;
  for (int index = 1; index < argc; ++index) {
    const std::string option = argv[index];
    if (option == "--input") {
      parameters.input = nextArgument(index, argc, argv);
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
    } else if (option == "--r-assoc") {
      parameters.rAssoc = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--damp") {
      parameters.damping = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--K") {
      parameters.feneK = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--R0") {
      parameters.feneR0 = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--seed") {
      parameters.seed = std::stoull(nextArgument(index, argc, argv));
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
  if (parameters.input.empty() || parameters.arms <= 0 || parameters.beadsPerArm <= 0 ||
      parameters.steps <= 0 || parameters.every <= 0 || parameters.dt <= 0.0 ||
      parameters.temperature <= 0.0 || parameters.ea < 0.0 || parameters.nu0 < 0.0 ||
      parameters.rAssoc <= 0.0 || parameters.feneK <= 0.0 || parameters.feneR0 <= 0.0 ||
      parameters.rAssoc >= parameters.feneR0 || parameters.damping <= 0.0) {
    throw std::runtime_error("invalid S1 parameters");
  }
  return parameters;
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
  std::cout << "STAR_ASSOCIATION_SMOKE SELF_TEST PASS sticker subset and invariants\n";
}

void writeState(std::ofstream& output,
                long long step,
                const Parameters& parameters,
                const kg_assoc::AssociationCounts& counts,
                long long creations,
                long long breaks) {
  output << step << ' ' << std::setprecision(12) << step * parameters.dt << ' '
         << counts.freeStickers << ' ' << counts.bonds << ' ' << creations << ' '
         << breaks << ' ' << counts.intraStarBonds << ' ' << counts.interStarBonds << '\n';
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
    const std::vector<int> stickerIds = kg_assoc::extractStickerIds(data);
    if (static_cast<int>(stickerIds.size()) != topology.stickers) {
      throw std::runtime_error("type-2 sticker extraction disagrees with S0 audit");
    }
    const std::set<std::pair<int, int>> permanentBonds =
        kg_assoc::permanentBondPairs(data);

    const std::string statePath = parameters.output + ".state";
    const std::string eventPath = parameters.output + ".events";
    if (!parameters.force && (std::ifstream(statePath) || std::ifstream(eventPath))) {
      throw std::runtime_error("output exists; choose a new --output or use --force");
    }
    std::ofstream stateFile(statePath);
    std::ofstream eventFile(eventPath);
    if (!stateFile || !eventFile) {
      throw std::runtime_error("cannot open S1 output files");
    }

    auto system = std::make_shared<uammd::System>(argc, argv);
    const kg::SimulationBox simulationBox = kg::makeSimulationBox(data);
    const auto particles = kg::createParticleDataFromLammps(data, system, simulationBox);
    const kg_assoc::BoxLengths lengths{
        data.xhi - data.xlo, data.yhi - data.ylo, data.zhi - data.zlo};
    const std::string permanentBondData =
        kg::buildUammdBondDataFromLammps(data, parameters.feneK, parameters.feneR0);

    const auto wca = kg::createWCAInteractor_CellList(
        particles, simulationBox.box, data.atomTypes, 1.0, 1.0, parameters.skin);
    const auto permanentFene = kg::createFENEInteractor(
        particles, simulationBox.box, permanentBondData);
    kg_assoc::StickerState state(data.natoms, stickerIds);
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

    stateFile << "# timestep time N_free_stickers N_assoc_bonds creations breaks N_intra N_inter\n"
              << "# atom IDs in events are original 1-based LAMMPS IDs\n";
    eventFile << "# timestep event_type sticker_i sticker_j molecule_i molecule_j\n"
              << "# sticker IDs are original 1-based LAMMPS IDs\n";

    long long creations = 0;
    long long breaks = 0;
    long long chemistrySweeps = 0;
    long long candidatePairs = 0;
    kg_assoc::AssociationCounts counts = kg_assoc::checkAssociationInvariants(
        particles, data, state, permanentBonds, lengths, parameters.feneR0, creations, breaks);
    writeState(stateFile, 0, parameters, counts, creations, breaks);

    const auto start = std::chrono::steady_clock::now();
    for (int step = 1; step <= parameters.steps; ++step) {
      integrator->forwardTime();
      if (step % parameters.every != 0) {
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

      std::vector<kg_assoc::Candidate> candidates = kg_assoc::findStickerCandidates(
          particles, state, lengths, parameters.rAssoc);
      candidatePairs += static_cast<long long>(candidates.size());
      ++chemistrySweeps;
      std::vector<kg_assoc::Event> acceptedEvents;
      kinetics.update(step, state, std::move(candidates), acceptedEvents);
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
      counts = kg_assoc::checkAssociationInvariants(
          particles, data, state, permanentBonds, lengths, parameters.feneR0,
          creations, breaks);
      writeState(stateFile, step, parameters, counts, creations, breaks);
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
