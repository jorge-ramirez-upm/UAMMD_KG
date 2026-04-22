// kg_uammd_equilibrate.cu
//
// Equilibration driver for overlapping Kremer-Grest initial configurations.

#include <uammd.cuh>

#include "Integrator/VerletNVE.cuh"
#include "Integrator/VerletNVT.cuh"
#include "kg_cli.cuh"
#include "kg_interactors.cuh"
#include "kg_lammps_io.cuh"
#include "kg_runtime.cuh"

#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr double kDPDCutOff = 1.0;
constexpr double kDPDTemperature = 1.0;
constexpr double kDPDGamma = 4.5;
constexpr double kDPDInitialAmplitude = 25.0;
constexpr int kStage1Loops = 4;
constexpr int kStage1StepsPerLoop = 100;
constexpr int kStage2Steps = 50000;
constexpr int kStage3Loops = 10;
constexpr int kStage3StepsPerLoop = 100;
constexpr int kStage4Steps = 1000000;

struct EquilibrationThermoSnapshot {
  double bondedEnergy = 0.0;
  double nonBondedEnergy = std::numeric_limits<double>::quiet_NaN();
  double kineticEnergy = 0.0;
  double totalEnergy = std::numeric_limits<double>::quiet_NaN();
  double temperature = 0.0;
  double pressure = 0.0;
};

struct EquilibrationParams {
  std::string dataFile = "input.lammpsdat";
  double dt = 0.01;
  double temperature = 1.0;
  double friction = 0.5;
  double sigma = 1.0;
  double epsilon = 1.0;
  double feneK = 30.0;
  double feneR0 = 1.5;
  double skin = 0.3;
  int stage1Loops = kStage1Loops;
  int stage1StepsPerLoop = kStage1StepsPerLoop;
  int stage2Steps = kStage2Steps;
  int stage3Loops = kStage3Loops;
  int stage3StepsPerLoop = kStage3StepsPerLoop;
  int stage4Steps = kStage4Steps;
  bool initializeVelocities = false;
};

struct StageOutputs {
  std::ofstream& thermo;
  const kg::LammpsData& ld;
  std::shared_ptr<uammd::ParticleData> pd;
  const kg::SimulationBox& simulationBox;
  const EquilibrationParams& par;
  const std::string& thermoHeader;
};

struct InteractorBundle {
  std::shared_ptr<uammd::Integrator> integrator;
  std::shared_ptr<uammd::Interactor> nonBonded;
  std::shared_ptr<uammd::Interactor> bonded;
};

struct EquilibrationArgs {
  EquilibrationParams sim;
  int maxStage = 4;
};

inline double stage1DisplacementLimit(int loopIndex) {
  return std::exp((static_cast<double>(loopIndex) - 4.0) * std::log(10.0));
}

inline double stage3Amplitude(int loopIndex) {
  return 25.0 + (1000.0 - 25.0) *
                    std::exp((static_cast<double>(loopIndex) - 10.0) * 0.75);
}

inline std::vector<uammd::real4> copyCurrentPositions(
    std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  std::vector<real4> positions(particles->getNumParticles());
  auto pos = particles->getPos(access::cpu, access::read);
  for (int i = 0; i < particles->getNumParticles(); ++i) {
    positions[i] = pos[i];
  }
  return positions;
}

inline void limitParticleDisplacements(
    std::shared_ptr<uammd::ParticleData> particles,
    const kg::SimulationBox& simulationBox,
    const std::vector<uammd::real4>& previousPositions,
    double maxDisplacement,
    double dt) {
  using namespace uammd;

  if (maxDisplacement <= 0.0 || previousPositions.empty()) {
    return;
  }

  auto pos = particles->getPos(access::cpu, access::write);
  auto vel = particles->getVel(access::cpu, access::write);
  const real maxDisp = static_cast<real>(maxDisplacement);
  const real invDt = dt > 0.0 ? real(1.0 / dt) : real(0.0);

  for (int i = 0; i < particles->getNumParticles(); ++i) {
    const real3 oldPos = make_real3(previousPositions[i]);
    const real3 rawDisp = simulationBox.box.apply_pbc(make_real3(pos[i]) - oldPos);
    const real disp2 = dot(rawDisp, rawDisp);
    if (disp2 <= maxDisp * maxDisp || disp2 <= real(0.0)) {
      continue;
    }

    const real scale = maxDisp / std::sqrt(static_cast<double>(disp2));
    const real3 limitedDisp = rawDisp * scale;
    pos[i] = make_real4(simulationBox.box.apply_pbc(oldPos + limitedDisp), pos[i].w);
    if (dt > 0.0) {
      vel[i] = limitedDisp * invDt;
    }
  }
}

inline EquilibrationThermoSnapshot computeDPDThermoSnapshot(
    std::shared_ptr<uammd::Integrator> integrator,
    std::shared_ptr<uammd::ParticleData> particles,
    std::shared_ptr<uammd::Interactor> dpdInteractor,
    std::shared_ptr<uammd::Interactor> bondedInteractor,
    double volume,
    int numberParticles) {
  EquilibrationThermoSnapshot thermo;

  thermo.kineticEnergy = kg::detail::sumKineticEnergy(integrator, particles);
  thermo.nonBondedEnergy = kg::detail::sumInteractorEnergy(dpdInteractor, particles);
  thermo.bondedEnergy = kg::detail::sumInteractorEnergy(bondedInteractor, particles);
  thermo.totalEnergy =
      thermo.kineticEnergy + thermo.nonBondedEnergy + thermo.bondedEnergy;

  if (numberParticles > 0) {
    thermo.temperature =
        (2.0 * thermo.kineticEnergy) / (3.0 * static_cast<double>(numberParticles));
  }

  if (volume > 0.0) {
    const double nonBondedVirial =
        kg::detail::sumInteractorVirial(dpdInteractor, particles);
    const double bondedVirial =
        kg::detail::sumInteractorVirial(bondedInteractor, particles);
    thermo.pressure =
        (2.0 * thermo.kineticEnergy) / (3.0 * volume) -
        nonBondedVirial / (6.0 * volume) +
        bondedVirial / (6.0 * volume);
  }

  return thermo;
}

inline std::string formatEquilibrationThermoHeader() {
  std::ostringstream out;
  out << std::right
      << std::setw(9) << "step"
      << std::setw(14) << "e_bonded"
      << std::setw(14) << "e_nonbonded"
      << std::setw(14) << "e_kinetic"
      << std::setw(14) << "e_total"
      << std::setw(14) << "temperature"
      << std::setw(14) << "pressure";
  return out.str();
}

inline std::string formatEquilibrationThermoRow(
    int step,
    const EquilibrationThermoSnapshot& thermo) {
  std::ostringstream out;
  out << std::defaultfloat << std::setprecision(8) << std::right
      << std::setw(9) << step
      << std::setw(14) << thermo.bondedEnergy
      << std::setw(14) << thermo.nonBondedEnergy
      << std::setw(14) << thermo.kineticEnergy
      << std::setw(14) << thermo.totalEnergy
      << std::setw(14) << thermo.temperature
      << std::setw(14) << thermo.pressure;
  return out.str();
}

inline std::string commentThermoHeaderForFile(const std::string& header) {
  if (header.empty()) {
    return "#";
  }

  std::string commented = header;
  commented[0] = '#';
  return commented;
}

struct BondStretchInfo {
  int bondIndex = -1;
  int atomI = -1;
  int atomJ = -1;
  double maxDistance = 0.0;
};

inline BondStretchInfo analyzeMaxBondStretch(
    const kg::LammpsData& ld,
    std::shared_ptr<uammd::ParticleData> particles,
    const kg::SimulationBox& simulationBox) {
  using namespace uammd;

  BondStretchInfo info;
  auto pos = particles->getPos(access::cpu, access::read);
  for (size_t b = 0; b < ld.bonds.size(); ++b) {
    const int ai = ld.bonds[b].first - 1;
    const int aj = ld.bonds[b].second - 1;
    if (ai < 0 || aj < 0 || ai >= ld.natoms || aj >= ld.natoms) {
      continue;
    }

    const real3 ri = make_real3(pos[ai]);
    const real3 rj = make_real3(pos[aj]);
    const real3 rij = simulationBox.box.apply_pbc(rj - ri);
    const double distance = std::sqrt(static_cast<double>(dot(rij, rij)));
    if (distance > info.maxDistance) {
      info.maxDistance = distance;
      info.bondIndex = static_cast<int>(b) + 1;
      info.atomI = ai + 1;
      info.atomJ = aj + 1;
    }
  }

  return info;
}

inline void printEquilibrationHelpAndExit(const EquilibrationParams& dflt) {
  std::cout
      << "Usage:\n"
      << "  ./kg_uammd_equilibrate -i input.lammpsdat [options]\n\n"
      << "I/O:\n"
      << "  -i, --input FILE    LAMMPS data file input (default: "
      << dflt.dataFile << ")\n"
      << "                      Thermo is written as FILE with _equilibration.thermo appended\n"
      << "                      Final configuration is written as FILE with _equilibrated.lammpsdat appended\n\n"
      << "Dynamics:\n"
      << "  -t, --dt DT         Time step (default: " << dflt.dt << ")\n"
      << "  -T, --temperature kT\n"
      << "                      Temperature used in Stage 4 Langevin NVT (default: "
      << dflt.temperature << ")\n"
      << "  -x, --friction XI   Friction used in Stage 4 Langevin NVT (default: "
      << dflt.friction << ")\n"
      << "      --init-velocities\n"
      << "                      Ignore input velocities and initialize a Maxwell distribution for equilibration\n\n"
      << "Nonbonded (WCA Stage 4):\n"
      << "  -s, --sigma S       LJ sigma (default: " << dflt.sigma << ")\n"
      << "  -e, --epsilon E     LJ epsilon (default: " << dflt.epsilon << ")\n\n"
      << "Bonds (FENE):\n"
      << "  -k, --fene-k K      FENE K (default: " << dflt.feneK << ")\n"
      << "  -R, --fene-r0 R0    FENE R0 (default: " << dflt.feneR0 << ")\n\n"
      << "Neighbor list:\n"
      << "  -w, --skin SKIN     Neighbor-list skin for Stage 4 WCA (default: "
      << dflt.skin << ")\n\n"
      << "Stage lengths:\n"
      << "      --stage1-loops N         Stage 1 loops (default: "
      << dflt.stage1Loops << ")\n"
      << "      --stage1-steps N         Stage 1 steps per loop (default: "
      << dflt.stage1StepsPerLoop << ")\n"
      << "      --stage2-steps N         Stage 2 steps (default: "
      << dflt.stage2Steps << ")\n"
      << "      --stage3-loops N         Stage 3 loops (default: "
      << dflt.stage3Loops << ")\n"
      << "      --stage3-steps N         Stage 3 steps per loop (default: "
      << dflt.stage3StepsPerLoop << ")\n"
      << "      --stage4-steps N         Stage 4 steps (default: "
      << dflt.stage4Steps << ")\n\n"
      << "Thermo cadence:\n"
      << "  Stage 1: every 100 steps\n"
      << "  Stage 2: every 1000 steps\n"
      << "  Stage 3: every 100 steps\n"
      << "  Stage 4: every 10000 steps\n\n";
  std::exit(0);
}

inline std::string requireValue(int& i, int argc, char** argv) {
  if (i + 1 >= argc) {
    throw std::runtime_error(std::string("Missing value after ") + argv[i]);
  }
  return std::string(argv[++i]);
}

inline EquilibrationArgs parseEquilibrationArgs(int argc, char** argv) {
  EquilibrationArgs args;

  for (int i = 1; i < argc; ++i) {
    const std::string token(argv[i]);
    if (token == "--max-stage") {
      if (i + 1 >= argc) {
        throw std::runtime_error("Missing value after --max-stage");
      }
      args.maxStage = std::stoi(argv[++i]);
      continue;
    }
    if (token == "-i" || token == "--input" || token == "--data") {
      args.sim.dataFile = requireValue(i, argc, argv);
    } else if (token == "-t" || token == "--dt") {
      args.sim.dt = std::stod(requireValue(i, argc, argv));
    } else if (token == "-T" || token == "--temperature" || token == "--T") {
      args.sim.temperature = std::stod(requireValue(i, argc, argv));
    } else if (token == "-x" || token == "--friction" || token == "--xi") {
      args.sim.friction = std::stod(requireValue(i, argc, argv));
    } else if (token == "-s" || token == "--sigma") {
      args.sim.sigma = std::stod(requireValue(i, argc, argv));
    } else if (token == "-e" || token == "--epsilon" || token == "--eps") {
      args.sim.epsilon = std::stod(requireValue(i, argc, argv));
    } else if (token == "-k" || token == "--fene-k" || token == "--feneK") {
      args.sim.feneK = std::stod(requireValue(i, argc, argv));
    } else if (token == "-R" || token == "--fene-r0" || token == "--feneR0") {
      args.sim.feneR0 = std::stod(requireValue(i, argc, argv));
    } else if (token == "-w" || token == "--skin") {
      args.sim.skin = std::stod(requireValue(i, argc, argv));
    } else if (token == "--stage1-loops") {
      args.sim.stage1Loops = std::stoi(requireValue(i, argc, argv));
    } else if (token == "--stage1-steps") {
      args.sim.stage1StepsPerLoop = std::stoi(requireValue(i, argc, argv));
    } else if (token == "--stage2-steps") {
      args.sim.stage2Steps = std::stoi(requireValue(i, argc, argv));
    } else if (token == "--stage3-loops") {
      args.sim.stage3Loops = std::stoi(requireValue(i, argc, argv));
    } else if (token == "--stage3-steps") {
      args.sim.stage3StepsPerLoop = std::stoi(requireValue(i, argc, argv));
    } else if (token == "--stage4-steps") {
      args.sim.stage4Steps = std::stoi(requireValue(i, argc, argv));
    } else if (token == "--init-velocities") {
      args.sim.initializeVelocities = true;
    } else if (token == "-h" || token == "--help") {
      printEquilibrationHelpAndExit(EquilibrationParams{});
    } else {
      throw std::runtime_error("Unknown arg: " + token);
    }
  }

  if (args.maxStage < 1 || args.maxStage > 4) {
    throw std::runtime_error("--max-stage must be between 1 and 4");
  }
  if (args.sim.stage1Loops < 1 || args.sim.stage1StepsPerLoop < 1 ||
      args.sim.stage2Steps < 1 || args.sim.stage3Loops < 1 ||
      args.sim.stage3StepsPerLoop < 1 || args.sim.stage4Steps < 1) {
    throw std::runtime_error("All stage loop/step counts must be >= 1");
  }
  return args;
}

inline int thermoEveryForStage(int stageIndex) {
  switch (stageIndex) {
  case 1:
    return 100;
  case 2:
    return 1000;
  case 3:
    return 100;
  case 4:
    return 10000;
  default:
    return 0;
  }
}

inline kg::SimParams makeValidationParams(const EquilibrationParams& par) {
  kg::SimParams validation;
  validation.feneR0 = par.feneR0;
  return validation;
}

inline InteractorBundle makeDPDSegment(
    std::shared_ptr<uammd::ParticleData> pd,
    const kg::SimulationBox& simulationBox,
    const std::string& bondData,
    double dt,
    double amplitude) {
  using namespace uammd;

  auto dpd = kg::createDPDInteractor(pd, simulationBox.box, kDPDTemperature,
                                     kDPDGamma, amplitude, kDPDCutOff, dt);
  auto fene = kg::createFENEInteractor(pd, simulationBox.box, bondData);

  VerletNVE::Parameters ip;
  ip.dt = static_cast<real>(dt);
  ip.initVelocities = false;
  auto integrator = std::make_shared<VerletNVE>(pd, ip);
  integrator->addInteractor(dpd);
  integrator->addInteractor(fene);

  return {integrator, dpd, fene};
}

inline InteractorBundle makeWCASegment(
    std::shared_ptr<uammd::ParticleData> pd,
    const kg::SimulationBox& simulationBox,
    const kg::LammpsData& ld,
    const EquilibrationParams& par,
    const std::string& bondData) {
  using namespace uammd;

  auto wca = kg::createWCAInteractor_CellList(
      pd, simulationBox.box, ld.atomTypes, par.epsilon, par.sigma, par.skin);
  auto fene = kg::createFENEInteractor(pd, simulationBox.box, bondData);

  using NVT = VerletNVT::GronbechJensen;
  NVT::Parameters ip;
  ip.temperature = static_cast<real>(par.temperature);
  ip.friction = static_cast<real>(par.friction);
  ip.dt = static_cast<real>(par.dt);
  ip.initVelocities = false;
  auto integrator = std::make_shared<NVT>(pd, ip);
  integrator->addInteractor(wca);
  integrator->addInteractor(fene);

  return {integrator, wca, fene};
}

inline void appendOutputsIfNeeded(
    int step,
    int thermoEvery,
    int stageIndex,
    StageOutputs& outputs,
    std::shared_ptr<uammd::Integrator> integrator,
    std::shared_ptr<uammd::Interactor> nonBondedInteractor,
    std::shared_ptr<uammd::Interactor> bondedInteractor,
    bool nonBondedHasEnergy) {
  if (thermoEvery > 0 && step % thermoEvery == 0) {
    if (nonBondedHasEnergy) {
      const auto thermo = kg::computeThermoSnapshot(
          integrator, outputs.pd, nonBondedInteractor, bondedInteractor,
          outputs.ld, outputs.simulationBox, outputs.par.epsilon,
          outputs.par.sigma, outputs.simulationBox.box.getVolume(),
          outputs.ld.natoms);
      if (!std::isfinite(thermo.bondedEnergy)) {
        const auto bondInfo =
            analyzeMaxBondStretch(outputs.ld, outputs.pd, outputs.simulationBox);
        std::ostringstream message;
        message << "[KG equilibration] Non-finite bonded energy at stage "
                << stageIndex << ", step " << step << ". ";
        if (bondInfo.bondIndex > 0) {
          message << "Max bond is " << bondInfo.bondIndex << " between atoms "
                  << bondInfo.atomI << " and " << bondInfo.atomJ
                  << " with length " << bondInfo.maxDistance
                  << " (feneR0 = " << outputs.par.feneR0 << ").";
        }
        throw std::runtime_error(message.str());
      }
      const std::string row = kg::formatThermoRow(step, thermo);
      uammd::System::log<uammd::System::MESSAGE>("[KG equilibration] %s",
                                                 row.c_str());
      outputs.thermo << row << "\n";
      outputs.thermo.flush();
    } else {
      const auto thermo = computeDPDThermoSnapshot(
          integrator, outputs.pd, nonBondedInteractor, bondedInteractor,
          outputs.simulationBox.box.getVolume(), outputs.ld.natoms);
      const std::string row = formatEquilibrationThermoRow(step, thermo);
      uammd::System::log<uammd::System::MESSAGE>("[KG equilibration] %s",
                                                 row.c_str());
      outputs.thermo << row << "\n";
      outputs.thermo.flush();
    }
  }
}

inline void writeRunHeaderAndStep0(
    const std::string& runLabel,
    int stageIndex,
    bool nonBondedHasEnergy,
    StageOutputs& outputs,
    std::shared_ptr<uammd::Integrator> integrator,
    std::shared_ptr<uammd::Interactor> nonBondedInteractor,
    std::shared_ptr<uammd::Interactor> bondedInteractor) {
  uammd::System::log<uammd::System::MESSAGE>("[KG equilibration] %s",
                                             runLabel.c_str());
  uammd::System::log<uammd::System::MESSAGE>("[KG equilibration] %s",
                                             outputs.thermoHeader.c_str());
  outputs.thermo << "# " << runLabel << "\n";
  outputs.thermo << commentThermoHeaderForFile(outputs.thermoHeader) << "\n";
  outputs.thermo.flush();

  if (nonBondedHasEnergy) {
    const auto thermo = kg::computeThermoSnapshot(
        integrator, outputs.pd, nonBondedInteractor, bondedInteractor,
        outputs.ld, outputs.simulationBox, outputs.par.epsilon,
        outputs.par.sigma, outputs.simulationBox.box.getVolume(),
        outputs.ld.natoms);
    if (!std::isfinite(thermo.bondedEnergy)) {
      const auto bondInfo =
          analyzeMaxBondStretch(outputs.ld, outputs.pd, outputs.simulationBox);
      std::ostringstream message;
      message << "[KG equilibration] Non-finite bonded energy at stage "
              << stageIndex << ", step 0. ";
      if (bondInfo.bondIndex > 0) {
        message << "Max bond is " << bondInfo.bondIndex << " between atoms "
                << bondInfo.atomI << " and " << bondInfo.atomJ
                << " with length " << bondInfo.maxDistance
                << " (feneR0 = " << outputs.par.feneR0 << ").";
      }
      throw std::runtime_error(message.str());
    }
    const std::string row = kg::formatThermoRow(0, thermo);
    uammd::System::log<uammd::System::MESSAGE>("[KG equilibration] %s",
                                               row.c_str());
    outputs.thermo << row << "\n";
    outputs.thermo.flush();
  } else {
    const auto thermo = computeDPDThermoSnapshot(
        integrator, outputs.pd, nonBondedInteractor, bondedInteractor,
        outputs.simulationBox.box.getVolume(), outputs.ld.natoms);
    const std::string row = formatEquilibrationThermoRow(0, thermo);
    uammd::System::log<uammd::System::MESSAGE>("[KG equilibration] %s",
                                               row.c_str());
    outputs.thermo << row << "\n";
    outputs.thermo.flush();
  }
}

template <class BundleFactory>
inline void runSegment(int steps,
                       int stageIndex,
                       const std::string& runLabel,
                       StageOutputs& outputs,
                       double maxDisplacement,
                       bool nonBondedHasEnergy,
                       const BundleFactory& bundleFactory) {
  const auto bundle = bundleFactory();
  const int thermoEvery = thermoEveryForStage(stageIndex);
  writeRunHeaderAndStep0(runLabel, stageIndex, nonBondedHasEnergy, outputs,
                         bundle.integrator, bundle.nonBonded, bundle.bonded);

  for (int localStep = 1; localStep <= steps; ++localStep) {
    std::vector<uammd::real4> previousPositions;
    if (maxDisplacement > 0.0) {
      previousPositions = copyCurrentPositions(outputs.pd);
    }

    bundle.integrator->forwardTime();

    if (maxDisplacement > 0.0) {
      limitParticleDisplacements(outputs.pd, outputs.simulationBox,
                                 previousPositions, maxDisplacement,
                                 outputs.par.dt);
    }

    appendOutputsIfNeeded(localStep, thermoEvery, stageIndex, outputs,
                          bundle.integrator,
                          bundle.nonBonded, bundle.bonded, nonBondedHasEnergy);
  }

  cudaDeviceSynchronize();
}

inline void logStageBanner(int stageIndex, const std::string& label) {
  uammd::System::log<uammd::System::MESSAGE>(
      "[KG equilibration] #############################");
  uammd::System::log<uammd::System::MESSAGE>(
      "[KG equilibration] STAGE %d: %s", stageIndex, label.c_str());
  uammd::System::log<uammd::System::MESSAGE>(
      "[KG equilibration] #############################");
}

} // namespace

int main(int argc, char** argv) {
  using namespace uammd;

  auto sys = std::make_shared<System>(argc, argv);

  EquilibrationArgs eqArgs;
  try {
    eqArgs = parseEquilibrationArgs(argc, argv);
  } catch (const std::exception& e) {
    std::cerr << "Argument error: " << e.what() << "\nUse --help\n";
    return 1;
  }
  const EquilibrationParams& par = eqArgs.sim;

  kg::LammpsData ld;
  try {
    ld = kg::readLammpsDataFile(par.dataFile);
  } catch (const std::exception& e) {
    std::cerr << "LAMMPS data read error: " << e.what() << "\n";
    return 1;
  }

  std::string thermoFile;
  std::string finalConfigFile;
  try {
    thermoFile = kg::deriveTaggedThermoFilename(par.dataFile, "_equilibration");
    finalConfigFile = kg::deriveTaggedDataFilename(par.dataFile, "_equilibrated");
  } catch (const std::exception& e) {
    std::cerr << "Output filename error: " << e.what() << "\n";
    return 1;
  }

  const auto simulationBox = kg::makeSimulationBox(ld);
  const auto pd = kg::createParticleDataFromLammps(ld, sys, simulationBox);

  try {
    kg::validateAtomTypesAndBondTopology(ld, makeValidationParams(par),
                                         simulationBox);
    const auto pairInfo = kg::logClosestPairWCA(ld, simulationBox);
    if (pairInfo.overlapsBelow1e6 > 0) {
      System::log<System::WARNING>(
          "[KG equilibration] Starting from %d pairs with separation < 1e-6",
          pairInfo.overlapsBelow1e6);
    }
  } catch (const std::exception& e) {
    std::cerr << e.what() << "\n";
    return 1;
  }

  const std::string bondData =
      kg::buildUammdBondDataFromLammps(ld, par.feneK, par.feneR0);

  if (par.initializeVelocities) {
    kg::initializeVelocitiesAtTemperature(pd, kDPDTemperature, false);
  }

  std::ofstream thermo(thermoFile);
  if (!thermo) {
    std::cerr << "Cannot open thermo file: " << thermoFile << "\n";
    return 1;
  }
  const std::string thermoHeader = formatEquilibrationThermoHeader();

  System::log<System::MESSAGE>("[KG equilibration] Input: %s", par.dataFile.c_str());
  System::log<System::MESSAGE>("[KG equilibration] Thermo output: %s",
                               thermoFile.c_str());
  System::log<System::MESSAGE>("[KG equilibration] Final configuration: %s",
                               finalConfigFile.c_str());
  System::log<System::MESSAGE>("[KG equilibration] Executing through stage %d",
                               eqArgs.maxStage);
  System::log<System::MESSAGE>(
      "[KG equilibration] Stage lengths: s1=%d x %d, s2=%d, s3=%d x %d, s4=%d",
      par.stage1Loops, par.stage1StepsPerLoop, par.stage2Steps,
      par.stage3Loops, par.stage3StepsPerLoop, par.stage4Steps);
  int totalSteps = 0;

  StageOutputs outputs{thermo, ld, pd, simulationBox, par, thermoHeader};
  const auto loopStart = std::chrono::steady_clock::now();

  logStageBanner(1, "DPD + FENE with limited displacement");
  for (int loop = 1; loop <= par.stage1Loops; ++loop) {
    const double maxDisplacement = stage1DisplacementLimit(loop);
    const std::string runLabel =
        "Stage 1 run " + std::to_string(loop) + "/" +
        std::to_string(par.stage1Loops) + ", max displacement " +
        std::to_string(maxDisplacement);
    System::log<System::MESSAGE>(
        "[KG equilibration]   loop %d/%d, max displacement %.12g",
        loop, par.stage1Loops, maxDisplacement);
    runSegment(par.stage1StepsPerLoop, 1, runLabel, outputs, maxDisplacement, false, [&]() {
      return makeDPDSegment(pd, simulationBox, bondData, par.dt,
                            kDPDInitialAmplitude);
    });
    totalSteps += par.stage1StepsPerLoop;
  }

  if (eqArgs.maxStage == 1) {
    goto finalize;
  }

  logStageBanner(2, "DPD + FENE without displacement cap");
  runSegment(par.stage2Steps, 2, "Stage 2 run 1/1", outputs, -1.0, false, [&]() {
    return makeDPDSegment(pd, simulationBox, bondData, par.dt,
                          kDPDInitialAmplitude);
  });
  totalSteps += par.stage2Steps;

  if (eqArgs.maxStage == 2) {
    goto finalize;
  }

  logStageBanner(3, "DPD + FENE fast push-off");
  for (int loop = 1; loop <= par.stage3Loops; ++loop) {
    const double amplitude = stage3Amplitude(loop);
    const std::string runLabel =
        "Stage 3 run " + std::to_string(loop) + "/" +
        std::to_string(par.stage3Loops) + ", DPD amplitude " +
        std::to_string(amplitude);
    System::log<System::MESSAGE>(
        "[KG equilibration]   loop %d/%d, DPD amplitude %.12g",
        loop, par.stage3Loops, amplitude);
    runSegment(par.stage3StepsPerLoop, 3, runLabel, outputs, -1.0, false, [&]() {
      return makeDPDSegment(pd, simulationBox, bondData, par.dt, amplitude);
    });
    totalSteps += par.stage3StepsPerLoop;
  }

  if (eqArgs.maxStage == 3) {
    goto finalize;
  }

  logStageBanner(4, "full WCA + FENE with Langevin NVT");
  runSegment(par.stage4Steps, 4, "Stage 4 run 1/1", outputs, -1.0, true, [&]() {
    return makeWCASegment(pd, simulationBox, ld, par, bondData);
  });
  totalSteps += par.stage4Steps;

finalize:
  const auto loopEnd = std::chrono::steady_clock::now();
  const double loopSeconds =
      std::chrono::duration<double>(loopEnd - loopStart).count();

  try {
    kg::writeLAMMPSDataSnapshot(finalConfigFile, totalSteps, ld, pd,
                                "kg_uammd_equilibrate");
  } catch (const std::exception& e) {
    std::cerr << "Final configuration write error: " << e.what() << "\n";
    return 1;
  }

  System::log<System::MESSAGE>(
      "%s",
      kg::formatPerformanceSummary(loopSeconds, totalSteps, ld.natoms, par.dt).c_str());
  System::log<System::MESSAGE>("[KG equilibration] Done");
  return 0;
}
