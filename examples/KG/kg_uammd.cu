// kg_uammd.cu
//
// Main orchestration file for the Kremer-Grest UAMMD example.
//
// Utility tasks are split into small modules:
//   - kg_cli.*        command-line parsing and defaults
//   - kg_lammps_io.*  LAMMPS readers/writers and restart helpers
//   - kg_interactors.* force/interactor construction
//
// Important conventions to keep in mind while reading:
//   - LAMMPS atom IDs in the input file are 1-based.
//   - UAMMD particle indexing is 0-based.

#include <uammd.cuh>

#include "Integrator/VerletNVT.cuh"
#include "kg_cli.cuh"
#include "kg_interactors.cuh"
#include "kg_lammps_io.cuh"

#include <cmath>
#include <chrono>
#include <limits>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <thrust/fill.h>
#include <thrust/reduce.h>

static void resetParticleEnergy(std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  auto energy = particles->getEnergy(access::location::gpu, access::mode::write);
  thrust::fill(thrust::cuda::par, energy.begin(), energy.end(), real(0.0));
}

static void resetParticleVirial(std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  auto virial = particles->getVirial(access::location::gpu, access::mode::write);
  thrust::fill(thrust::cuda::par, virial.begin(), virial.end(), real(0.0));
}

static double reduceParticleEnergy(std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  auto energy = particles->getEnergy(access::location::gpu, access::mode::read);
  return thrust::reduce(thrust::cuda::par, energy.begin(), energy.end(), 0.0);
}

static double reduceParticleVirial(std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  auto virial = particles->getVirial(access::location::gpu, access::mode::read);
  return thrust::reduce(thrust::cuda::par, virial.begin(), virial.end(), 0.0);
}

static double sumKineticEnergy(std::shared_ptr<uammd::Integrator> integrator,
                               std::shared_ptr<uammd::ParticleData> particles) {
  resetParticleEnergy(particles);
  integrator->sumEnergy();
  return reduceParticleEnergy(particles);
}

static double sumInteractorEnergy(std::shared_ptr<uammd::Interactor> interactor,
                                  std::shared_ptr<uammd::ParticleData> particles) {
  if (!interactor) {
    return 0.0;
  }

  resetParticleEnergy(particles);
  interactor->sum({.force = false, .energy = true, .virial = false}, 0);
  return reduceParticleEnergy(particles);
}

static double sumInteractorVirial(std::shared_ptr<uammd::Interactor> interactor,
                                  std::shared_ptr<uammd::ParticleData> particles) {
  if (!interactor) {
    return 0.0;
  }

  resetParticleVirial(particles);
  interactor->sum({.force = false, .energy = false, .virial = true}, 0);
  return reduceParticleVirial(particles);
}

struct ThermoSnapshot {
  double bondedEnergy = 0.0;
  double nonBondedEnergy = 0.0;
  double kineticEnergy = 0.0;
  double totalEnergy = 0.0;
  double temperature = 0.0;
  double pressure = 0.0;
};

struct BondedWCACorrection {
  double energy = 0.0;
};

static BondedWCACorrection computeBondedWCACorrection(
    const kg::LammpsData& ld,
    std::shared_ptr<uammd::ParticleData> particles,
    const uammd::Box& box,
    double epsilon,
    double sigma) {
  using namespace uammd;

  BondedWCACorrection correction;
  if (ld.bonds.empty()) {
    return correction;
  }

  const double cutOff = std::pow(2.0, 1.0 / 6.0) * sigma;
  const double cutOff2 = cutOff * cutOff;
  const double sigma2 = sigma * sigma;

  auto pos = particles->getPos(access::cpu, access::read);
  for (const auto& bond : ld.bonds) {
    const int ai = bond.first - 1;
    const int aj = bond.second - 1;
    if (ai < 0 || aj < 0 || ai >= ld.natoms || aj >= ld.natoms) {
      continue;
    }

    const real3 ri = make_real3(pos[ai]);
    const real3 rj = make_real3(pos[aj]);
    const real3 rij = box.apply_pbc(rj - ri);
    const double r2 = static_cast<double>(dot(rij, rij));
    if (r2 <= 0.0 || r2 >= cutOff2) {
      continue;
    }

    const double invr2 = sigma2 / r2;
    const double invr6 = invr2 * invr2 * invr2;
    correction.energy += 4.0 * epsilon * invr6 * (invr6 - 1.0) + epsilon;
  }

  return correction;
}

static ThermoSnapshot computeThermoSnapshot(
    std::shared_ptr<uammd::Integrator> integrator,
    std::shared_ptr<uammd::ParticleData> particles,
    std::shared_ptr<uammd::Interactor> nonBondedInteractor,
    std::shared_ptr<uammd::Interactor> bondedInteractor,
    const kg::LammpsData& ld,
    const uammd::Box& box,
    double epsilon,
    double sigma,
    bool repartitionBondedWCA,
    double volume,
    int numberParticles) {
  ThermoSnapshot thermo;

  thermo.kineticEnergy = sumKineticEnergy(integrator, particles);
  thermo.nonBondedEnergy = sumInteractorEnergy(nonBondedInteractor, particles);
  thermo.bondedEnergy = sumInteractorEnergy(bondedInteractor, particles);
  if (repartitionBondedWCA) {
    const auto correction =
        computeBondedWCACorrection(ld, particles, box, epsilon, sigma);
    thermo.bondedEnergy += correction.energy;
    thermo.nonBondedEnergy -= correction.energy;
  }
  thermo.totalEnergy =
      thermo.kineticEnergy + thermo.nonBondedEnergy + thermo.bondedEnergy;

  if (numberParticles > 0) {
    thermo.temperature =
        (2.0 * thermo.kineticEnergy) / (3.0 * static_cast<double>(numberParticles));
  }

  if (volume > 0.0) {
    const double nonBondedVirial =
        sumInteractorVirial(nonBondedInteractor, particles);
    const double bondedVirial = sumInteractorVirial(bondedInteractor, particles);
    // The WCA PairForces and FENE BondedForces implementations use opposite
    // position-vector conventions when storing per-particle virial:
    //   - Radial pair forces use rj-ri, so the reduced virial has opposite sign.
    //   - Bonded forces orient the vector from the current particle to its
    //     partner, so the reduced virial already matches the standard sign.
    // Both are double-counted over the two particles in the interaction.
    thermo.pressure =
        (2.0 * thermo.kineticEnergy) / (3.0 * volume) -
        nonBondedVirial / (6.0 * volume) +
        bondedVirial / (6.0 * volume);
  }

  return thermo;
}

static std::string formatThermoHeader() {
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

static std::string formatThermoRow(int step, const ThermoSnapshot& thermo) {
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

static std::string formatPerformanceSummary(double elapsedSeconds,
                                            int steps,
                                            int numberParticles,
                                            double dt) {
  std::ostringstream out;
  const double tauPerDay =
      elapsedSeconds > 0.0 ? (static_cast<double>(steps) * dt * 86400.0) / elapsedSeconds
                           : 0.0;
  const double stepsPerSecond =
      elapsedSeconds > 0.0 ? static_cast<double>(steps) / elapsedSeconds : 0.0;
  const double megaAtomStepsPerSecond =
      elapsedSeconds > 0.0
          ? (static_cast<double>(steps) * static_cast<double>(numberParticles)) /
                (1.0e6 * elapsedSeconds)
          : 0.0;
  const double nanosecondsPerParticleStep =
      (steps > 0 && numberParticles > 0)
          ? (elapsedSeconds * 1.0e9) /
                (static_cast<double>(steps) * static_cast<double>(numberParticles))
          : 0.0;

  out << std::fixed << std::setprecision(2)
      << "Loop time of " << elapsedSeconds
      << " for " << steps << " steps with " << numberParticles << " particles";
  out << "\n";
  out << std::setprecision(3)
      << "Performance: " << tauPerDay << " tau/day, "
      << stepsPerSecond << " timesteps/s, "
      << megaAtomStepsPerSecond << " Matom-step/s, "
      << nanosecondsPerParticleStep << " ns/particle/timestep";
  return out.str();
}

static void initializeVelocitiesAtTemperature(
    std::shared_ptr<uammd::ParticleData> particles,
    double temperature,
    bool is2D = false) {
  using namespace uammd;

  const int numberParticles = particles->getNumParticles();
  if (numberParticles <= 0) {
    return;
  }

  auto vel = particles->getVel(access::cpu, access::write);
  auto mass = particles->getMass(access::cpu, access::read);

  std::mt19937 gen(particles->getSystem()->rng().next32());
  std::normal_distribution<real> gaussian(real(0.0), real(1.0));

  real3 vcm = make_real3(real(0.0));
  real totalMass = real(0.0);
  for (int i = 0; i < numberParticles; ++i) {
    const real mi = mass[i];
    const real sigma = std::sqrt(real(temperature) / mi);
    vel[i] = make_real3(sigma * gaussian(gen),
                        sigma * gaussian(gen),
                        is2D ? real(0.0) : sigma * gaussian(gen));
    vcm += mi * vel[i];
    totalMass += mi;
  }

  if (totalMass > real(0.0)) {
    vcm /= totalMass;
  }

  double kinetic = 0.0;
  const double dof = is2D ? 2.0 * numberParticles : 3.0 * numberParticles;
  for (int i = 0; i < numberParticles; ++i) {
    vel[i] -= vcm;
    kinetic += 0.5 * static_cast<double>(mass[i]) *
               static_cast<double>(dot(vel[i], vel[i]));
  }

  if (kinetic > 0.0 && dof > 0.0 && temperature > 0.0) {
    const double currentTemperature = (2.0 * kinetic) / dof;
    const real scale = real(std::sqrt(temperature / currentTemperature));
    for (int i = 0; i < numberParticles; ++i) {
      vel[i] *= scale;
    }
  }
}

struct ClosestPairInfo {
  int i = -1;
  int j = -1;
  double distance = std::numeric_limits<double>::infinity();
  int overlapsBelow1e6 = 0;
  int overlapsBelow1e3 = 0;
};

static ClosestPairInfo analyzeClosestPairWCA(const kg::LammpsData& ld,
                                             uammd::Box box,
                                             uammd::real3 boxCenter) {
  using namespace uammd;

  ClosestPairInfo info;
  double minR2 = std::numeric_limits<double>::infinity();

  for (int i = 0; i < ld.natoms; ++i) {
    const real3 ri = box.apply_pbc(make_real3((real)ld.x[i] - boxCenter.x,
                                              (real)ld.y[i] - boxCenter.y,
                                              (real)ld.z[i] - boxCenter.z));
    for (int j = i + 1; j < ld.natoms; ++j) {
      const real3 rj = box.apply_pbc(make_real3((real)ld.x[j] - boxCenter.x,
                                                (real)ld.y[j] - boxCenter.y,
                                                (real)ld.z[j] - boxCenter.z));
      const real3 rij = box.apply_pbc(rj - ri);
      const double r2 = static_cast<double>(dot(rij, rij));
      if (r2 < minR2) {
        minR2 = r2;
        info.i = i;
        info.j = j;
      }
      if (r2 < 1e-12) {
        info.overlapsBelow1e6++;
      }
      if (r2 < 1e-6) {
        info.overlapsBelow1e3++;
      }
    }
  }

  info.distance = std::sqrt(minR2);
  return info;
}

// --------------------------
// main
// --------------------------
int main(int argc, char** argv){
  using namespace uammd;
  using kg::LammpsData;
  using kg::SimParams;
  using kg::deriveDumpFilename;
  using kg::deriveRestartFilename;
  using kg::deriveThermoFilename;

  auto sys = std::make_shared<System>(argc, argv);

  // 1. Read user options or fall back to defaults.
  SimParams par;
  try{
    par = kg::parseArgs(argc, argv);
  } catch(const std::exception& e){
    std::cerr << "Argument error: " << e.what() << "\nUse --help\n";
    return 1;
  }

  // 2. Load the initial configuration from a LAMMPS data file.
  // This provides:
  //   - the atom coordinates
  //   - atom types and molecule IDs
  //   - bond connectivity
  //   - simulation box dimensions
  LammpsData ld;
  try{
    ld = kg::readLammpsDataFile(par.dataFile);
  } catch(const std::exception& e){
    std::cerr << "LAMMPS data read error: " << e.what() << "\n";
    return 1;
  }

  // 2b. Derive output filenames directly from the input data filename.
  // Example:
  //   input.lammpsdat -> input.lammpstrj
  //   input.lammpsdat -> input.restart1.lammpsdat / input.restart2.lammpsdat
  //   path/input.lammpsdat -> input.thermo
  std::string dumpFile;
  std::string thermoFile;
  try{
    dumpFile = deriveDumpFilename(par.dataFile);
    thermoFile = deriveThermoFilename(par.dataFile);
  } catch(const std::exception& e){
    std::cerr << "Output filename error: " << e.what() << "\n";
    return 1;
  }

  // 3. Create the UAMMD particle container with one entry per atom.
  auto pd = std::make_shared<ParticleData>(ld.natoms, sys);

  // 4. Build a periodic UAMMD box from the LAMMPS bounds.
  // The LAMMPS file stores low/high limits, while UAMMD's `Box` stores lengths.
  real3 L = make_real3((real)(ld.xhi-ld.xlo), (real)(ld.yhi-ld.ylo), (real)(ld.zhi-ld.zlo));
  Box box(L);
  box.setPeriodicity(true,true,true);
  const real3 boxCenter = make_real3((real)(0.5 * (ld.xlo + ld.xhi)),
                                     (real)(0.5 * (ld.ylo + ld.yhi)),
                                     (real)(0.5 * (ld.zlo + ld.zhi)));

  // 5. Copy the initial coordinates into UAMMD.
  // The fourth component of `real4` stores the particle type in UAMMD.
  // LAMMPS types are 1-based, while UAMMD expects 0-based type ids.
  // UAMMD's periodic box utilities expect positions centered around the origin,
  // so we shift LAMMPS coordinates from [xlo,xhi] to [-L/2,L/2).
  {
    auto pos = pd->getPos(access::cpu, access::write);
    for(int i=0;i<ld.natoms;i++){
      const real3 centered = make_real3((real)ld.x[i] - boxCenter.x,
                                        (real)ld.y[i] - boxCenter.y,
                                        (real)ld.z[i] - boxCenter.z);
      const real3 folded = box.apply_pbc(centered);
      pos[i] = make_real4(folded, (real)(ld.type[i] - 1));
    }
  }

  // Explicitly initialize basic per-particle properties used on the first step.
  {
    auto mass = pd->getMass(access::cpu, access::write);
    auto vel = pd->getVel(access::cpu, access::write);
    auto force = pd->getForce(access::cpu, access::write);
    for(int i=0;i<ld.natoms;i++){
      mass[i] = real(1.0);
      if(ld.hasVelocities){
        vel[i] = make_real3((real)ld.vx[i], (real)ld.vy[i], (real)ld.vz[i]);
      } else {
        vel[i] = make_real3(real(0.0));
      }
      force[i] = make_real4(real(0.0));
    }
  }

  // Preflight validation on the CPU to catch malformed input before the first
  // GPU force/integration kernel runs.
  {
    for(int i=0;i<ld.natoms;i++){
      if(ld.type[i] < 1 || ld.type[i] > ld.atomTypes){
        std::cerr << "Input validation error: atom " << (i + 1)
                  << " has type " << ld.type[i]
                  << ", but atomTypes = " << ld.atomTypes << "\n";
        return 1;
      }
    }

    const real maxBondLength = (real)par.feneR0;
    const real maxBondLength2 = maxBondLength * maxBondLength;
    for(size_t b=0; b<ld.bonds.size(); ++b){
      const int ai = ld.bonds[b].first - 1;
      const int aj = ld.bonds[b].second - 1;
      if(ai < 0 || aj < 0 || ai >= ld.natoms || aj >= ld.natoms){
        std::cerr << "Input validation error: bond " << (b + 1)
                  << " references atoms " << ld.bonds[b].first
                  << " and " << ld.bonds[b].second
                  << ", outside valid range 1.." << ld.natoms << "\n";
        return 1;
      }

      const real3 ri = box.apply_pbc(make_real3((real)ld.x[ai] - boxCenter.x,
                                                (real)ld.y[ai] - boxCenter.y,
                                                (real)ld.z[ai] - boxCenter.z));
      const real3 rj = box.apply_pbc(make_real3((real)ld.x[aj] - boxCenter.x,
                                                (real)ld.y[aj] - boxCenter.y,
                                                (real)ld.z[aj] - boxCenter.z));
      const real3 rij = box.apply_pbc(rj - ri);
      const real r2 = dot(rij, rij);
      if(r2 >= maxBondLength2){
        std::cerr << "Input validation error: bond " << (b + 1)
                  << " has length " << std::sqrt((double)r2)
                  << " which is >= feneR0 = " << par.feneR0
                  << " under minimum-image convention.\n";
        return 1;
      }
    }
  }

  if (par.enableWCA) {
    const auto pairInfo = analyzeClosestPairWCA(ld, box, boxCenter);
    System::log<System::MESSAGE>(
        "[KG] Closest initial pair for WCA: atoms %d and %d, distance %.12g",
        pairInfo.i + 1, pairInfo.j + 1, pairInfo.distance);
    if (pairInfo.overlapsBelow1e6 > 0) {
      std::cerr << "Input validation error: found "
                << pairInfo.overlapsBelow1e6
                << " particle pairs with separation < 1e-6 under PBC.\n"
                << "Closest pair is atoms " << (pairInfo.i + 1) << " and "
                << (pairInfo.j + 1) << " with distance "
                << pairInfo.distance << ".\n";
      return 1;
    }
  }

  // 6. Translate the LAMMPS bond topology into the auxiliary format expected
  // by UAMMD's bonded-force module, if FENE is enabled.
  std::string bondData;
  if(par.enableFENE){
    bondData = kg::buildUammdBondDataFromLammps(ld, par.feneK, par.feneR0);
  }

  // 7. Create the two interaction terms that define the KG model:
  //   - WCA repulsion between all particles
  //   - FENE springs along each chain bond
  std::shared_ptr<Interactor> wca;
  std::shared_ptr<Interactor> fene;
  if(par.enableWCA){
    wca = kg::createWCAInteractor_CellList(pd, box, ld.atomTypes, par.epsilon,
                                           par.sigma, par.skin,
                                           par.forceWCANBody);
  }
  if(par.enableFENE){
    fene = kg::createFENEInteractor(pd, box, bondData);
  }

  // 8. Configure the time integrator.
  // `GronbechJensen` is UAMMD's Langevin-style NVT integrator.
  using NVT = VerletNVT::GronbechJensen;
  NVT::Parameters ip;
  ip.temperature = (real)par.temperature;
  ip.friction    = (real)par.friction;
  ip.dt          = (real)par.dt;
  ip.initVelocities = false; // we handle optional startup initialization explicitly
  if(par.initializeVelocities){
    initializeVelocitiesAtTemperature(pd, par.temperature, false);
  }
  auto integrator = std::make_shared<NVT>(pd, ip);

  // Register both force contributions with the integrator so each time step
  // includes nonbonded and bonded forces.
  if(wca){
    integrator->addInteractor(wca);
  }
  if(fene){
    integrator->addInteractor(fene);
  }

  // 9. Open the trajectory output file now so we can append frames as we go.
  std::ofstream dump(dumpFile);
  if(!dump){
    std::cerr << "Cannot open dump file: " << dumpFile << "\n";
    return 1;
  }

  std::ofstream thermo(thermoFile);
  if(!thermo){
    std::cerr << "Cannot open thermo file: " << thermoFile << "\n";
    return 1;
  }
  const std::string thermoHeader = formatThermoHeader();
  thermo << thermoHeader << "\n";

  // Print a short run summary through UAMMD's message system.
  System::log<System::MESSAGE>("[KG] Starting");
  System::log<System::MESSAGE>("[KG] atoms %d bonds %zu box %g %g %g",
                               ld.natoms, ld.bonds.size(),
                               (ld.xhi - ld.xlo), (ld.yhi - ld.ylo), (ld.zhi - ld.zlo));
  System::log<System::MESSAGE>("[KG] dt %g T %g xi %g skin %g",
                               par.dt, par.temperature, par.friction, par.skin);
  System::log<System::MESSAGE>("[KG] WCA %s FENE %s",
                               par.enableWCA ? "on" : "off",
                               par.enableFENE ? "on" : "off");
  System::log<System::MESSAGE>("[KG] Velocities %s",
                               par.initializeVelocities
                                   ? "initialized from requested temperature"
                                   : (ld.hasVelocities ? "read from input file"
                                                       : "not present in input; using zeros"));
  if(par.forceWCANBody){
    System::log<System::MESSAGE>("[KG] WCA debugging mode: forcing PairForces NBody path");
  }
  System::log<System::MESSAGE>("[KG] %s", thermoHeader.c_str());

  // 10. Write the initial state before any integration step has happened.
  kg::appendLAMMPSDumpFrame(dump, 0, ld, pd, ld.xlo, ld.xhi, ld.ylo, ld.yhi, ld.zlo, ld.zhi);

  const auto thermo0 =
      computeThermoSnapshot(integrator, pd, wca, fene, ld, box, par.epsilon,
                            par.sigma, par.enableWCA && par.enableFENE,
                            box.getVolume(), ld.natoms);
  const std::string thermoRow0 = formatThermoRow(0, thermo0);
  System::log<System::MESSAGE>("[KG] %s", thermoRow0.c_str());
  thermo << thermoRow0 << "\n";

  // Optionally write an initial restart as well. This gives us a clean snapshot
  // of the starting configuration using the same machinery as later restarts.
  if(par.restartEvery > 0){
    try{
      kg::writeLAMMPSDataRestart(deriveRestartFilename(par.dataFile, 1), 0, ld, pd);
    } catch(const std::exception& e){
      std::cerr << "Restart write error: " << e.what() << "\n";
      return 1;
    }
  }

  // 11. Main simulation loop.
  // Each iteration advances the system by one time step and then performs any
  // scheduled outputs for energy, trajectory, and restart data.
  const auto loopStart = std::chrono::steady_clock::now();
  for(int step=1; step<=par.steps; ++step){
    // Advance positions/velocities by one integrator step, including all forces.
    integrator->forwardTime();

    if(par.thermoEvery>0 && step % par.thermoEvery == 0){
      const auto thermoNow =
          computeThermoSnapshot(integrator, pd, wca, fene, ld, box,
                                par.epsilon, par.sigma,
                                par.enableWCA && par.enableFENE,
                                box.getVolume(), ld.natoms);
      const std::string thermoRow = formatThermoRow(step, thermoNow);
      System::log<System::MESSAGE>("[KG] %s", thermoRow.c_str());
      thermo << thermoRow << "\n";
    }

    if(par.dumpEvery>0 && step % par.dumpEvery == 0){
      // Append one trajectory frame for visualization or post-processing.
      kg::appendLAMMPSDumpFrame(dump, step, ld, pd, ld.xlo, ld.xhi, ld.ylo, ld.yhi, ld.zlo, ld.zhi);
    }

    if(par.restartEvery>0 && step % par.restartEvery == 0){
      // Alternate between two filenames.
      // This is a common restart strategy because there is always at least one
      // previously completed restart file if a write is interrupted.
      int which = ((step / par.restartEvery) % 2) ? 2 : 1;
      std::string fn;
      try{
        fn = deriveRestartFilename(par.dataFile, which);
        kg::writeLAMMPSDataRestart(fn, step, ld, pd);
      } catch(const std::exception& e){
        std::cerr << "Restart write error: " << e.what() << "\n";
        return 1;
      }
    }
  }
  const auto loopEnd = std::chrono::steady_clock::now();
  const double loopSeconds =
      std::chrono::duration<double>(loopEnd - loopStart).count();

  System::log<System::MESSAGE>("%s",
      formatPerformanceSummary(loopSeconds, par.steps, ld.natoms, par.dt).c_str());
  System::log<System::MESSAGE>("[KG] Done");
  return 0;
}
