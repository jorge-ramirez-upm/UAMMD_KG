#ifndef EXAMPLES_KG_KG_RUNTIME_CUH
#define EXAMPLES_KG_KG_RUNTIME_CUH

// Runtime helpers for the Kremer-Grest example.
//
// This module keeps setup and reporting details out of `main` by grouping:
//   - box/particle translation from LAMMPS to UAMMD conventions
//   - CPU-side input validation before the first GPU step
//   - velocity initialization and thermo bookkeeping
//   - run-summary and performance formatting utilities

#include "kg_cli.cuh"
#include "kg_lammps_io.cuh"

#include <cmath>
#include <iomanip>
#include <limits>
#include <memory>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>

#include <thrust/fill.h>
#include <thrust/reduce.h>

namespace kg {

struct SimulationBox {
  uammd::Box box;
  uammd::real3 center = uammd::make_real3(uammd::real(0.0));
};

inline SimulationBox makeSimulationBox(const LammpsData& ld) {
  using namespace uammd;

  const real3 lengths = make_real3((real)(ld.xhi - ld.xlo),
                                   (real)(ld.yhi - ld.ylo),
                                   (real)(ld.zhi - ld.zlo));

  // UAMMD's `Box` stores lengths and assumes the periodic domain is centered
  // around the origin, so we keep the original LAMMPS box center separately.
  SimulationBox simulationBox{Box(lengths)};
  simulationBox.box.setPeriodicity(true, true, true);
  simulationBox.center = make_real3((real)(0.5 * (ld.xlo + ld.xhi)),
                                    (real)(0.5 * (ld.ylo + ld.yhi)),
                                    (real)(0.5 * (ld.zlo + ld.zhi)));
  return simulationBox;
}

inline std::shared_ptr<uammd::ParticleData> createParticleDataFromLammps(
    const LammpsData& ld,
    std::shared_ptr<uammd::System> system,
    const SimulationBox& simulationBox) {
  using namespace uammd;

  auto particles = std::make_shared<ParticleData>(ld.natoms, system);

  {
    auto pos = particles->getPos(access::cpu, access::write);
    for (int i = 0; i < ld.natoms; ++i) {
      const real3 centered = make_real3((real)ld.x[i] - simulationBox.center.x,
                                        (real)ld.y[i] - simulationBox.center.y,
                                        (real)ld.z[i] - simulationBox.center.z);
      const real3 folded = simulationBox.box.apply_pbc(centered);
      pos[i] = make_real4(folded, (real)(ld.type[i] - 1));
    }
  }

  {
    auto mass = particles->getMass(access::cpu, access::write);
    auto vel = particles->getVel(access::cpu, access::write);
    auto force = particles->getForce(access::cpu, access::write);
    // The KG example uses unit mass throughout, and the force array is seeded
    // explicitly so the first thermo/force operations start from clean values.
    for (int i = 0; i < ld.natoms; ++i) {
      mass[i] = real(1.0);
      if (ld.hasVelocities) {
        vel[i] = make_real3((real)ld.vx[i], (real)ld.vy[i], (real)ld.vz[i]);
      } else {
        vel[i] = make_real3(real(0.0));
      }
      force[i] = make_real4(real(0.0));
    }
  }

  return particles;
}

inline uammd::real3 centeredPosition(const LammpsData& ld,
                                     int index,
                                     const SimulationBox& simulationBox) {
  using namespace uammd;

  return simulationBox.box.apply_pbc(make_real3((real)ld.x[index] -
                                                    simulationBox.center.x,
                                                (real)ld.y[index] -
                                                    simulationBox.center.y,
                                                (real)ld.z[index] -
                                                    simulationBox.center.z));
}

struct ClosestPairInfo {
  int i = -1;
  int j = -1;
  double distance = std::numeric_limits<double>::infinity();
  int overlapsBelow1e6 = 0;
  int overlapsBelow1e3 = 0;
};

inline ClosestPairInfo analyzeClosestPairWCA(const LammpsData& ld,
                                             const SimulationBox& simulationBox) {
  using namespace uammd;

  ClosestPairInfo info;
  double minR2 = std::numeric_limits<double>::infinity();

  for (int i = 0; i < ld.natoms; ++i) {
    const real3 ri = centeredPosition(ld, i, simulationBox);
    for (int j = i + 1; j < ld.natoms; ++j) {
      const real3 rj = centeredPosition(ld, j, simulationBox);
      const real3 rij = simulationBox.box.apply_pbc(rj - ri);
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

inline void validateAtomTypesAndBondTopology(const LammpsData& ld,
                                             const SimParams& par,
                                             const SimulationBox& simulationBox) {
  using namespace uammd;

  // These checks intentionally run on the CPU before the first GPU launch so
  // malformed topologies fail with an actionable message.
  for (int i = 0; i < ld.natoms; ++i) {
    if (ld.type[i] < 1 || ld.type[i] > ld.atomTypes) {
      throw std::runtime_error("Input validation error: atom " +
                               std::to_string(i + 1) + " has type " +
                               std::to_string(ld.type[i]) +
                               ", but atomTypes = " +
                               std::to_string(ld.atomTypes));
    }
  }

  const real maxBondLength = (real)par.feneR0;
  const real maxBondLength2 = maxBondLength * maxBondLength;
  for (size_t b = 0; b < ld.bonds.size(); ++b) {
    const int ai = ld.bonds[b].first - 1;
    const int aj = ld.bonds[b].second - 1;
    if (ai < 0 || aj < 0 || ai >= ld.natoms || aj >= ld.natoms) {
      throw std::runtime_error("Input validation error: bond " +
                               std::to_string(b + 1) + " references atoms " +
                               std::to_string(ld.bonds[b].first) + " and " +
                               std::to_string(ld.bonds[b].second) +
                               ", outside valid range 1.." +
                               std::to_string(ld.natoms));
    }

    const real3 ri = centeredPosition(ld, ai, simulationBox);
    const real3 rj = centeredPosition(ld, aj, simulationBox);
    const real3 rij = simulationBox.box.apply_pbc(rj - ri);
    const real r2 = dot(rij, rij);
    if (r2 >= maxBondLength2) {
      std::ostringstream out;
      out << "Input validation error: bond " << (b + 1)
          << " has length " << std::sqrt((double)r2)
          << " which is >= feneR0 = " << par.feneR0
          << " under minimum-image convention.";
      throw std::runtime_error(out.str());
    }
  }
}

inline ClosestPairInfo logClosestPairWCA(const LammpsData& ld,
                                         const SimulationBox& simulationBox) {
  const auto pairInfo = analyzeClosestPairWCA(ld, simulationBox);
  uammd::System::log<uammd::System::MESSAGE>(
      "[KG] Closest initial pair for WCA: atoms %d and %d, distance %.12g",
      pairInfo.i + 1, pairInfo.j + 1, pairInfo.distance);
  return pairInfo;
}

inline void validateInputConfiguration(const LammpsData& ld,
                                       const SimParams& par,
                                       const SimulationBox& simulationBox) {
  validateAtomTypesAndBondTopology(ld, par, simulationBox);
  const auto pairInfo = logClosestPairWCA(ld, simulationBox);
  if (pairInfo.overlapsBelow1e6 > 0) {
    std::ostringstream out;
    out << "Input validation error: found " << pairInfo.overlapsBelow1e6
        << " particle pairs with separation < 1e-6 under PBC.\n"
        << "Closest pair is atoms " << (pairInfo.i + 1) << " and "
        << (pairInfo.j + 1) << " with distance " << pairInfo.distance << ".";
    throw std::runtime_error(out.str());
  }
}

inline void removeCenterOfMassVelocity(
    std::shared_ptr<uammd::ParticleData> particles,
    bool is2D = false) {
  using namespace uammd;

  const int numberParticles = particles->getNumParticles();
  if (numberParticles <= 0) {
    return;
  }

  auto vel = particles->getVel(access::cpu, access::write);
  auto mass = particles->getMass(access::cpu, access::read);

  real3 vcm = make_real3(real(0.0));
  real totalMass = real(0.0);
  for (int i = 0; i < numberParticles; ++i) {
    vcm += mass[i] * vel[i];
    totalMass += mass[i];
  }

  if (totalMass > real(0.0)) {
    vcm /= totalMass;
  }

  for (int i = 0; i < numberParticles; ++i) {
    vel[i] -= vcm;
    if (is2D) {
      vel[i].z = real(0.0);
    }
  }
}

inline void initializeVelocitiesAtTemperature(
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

  for (int i = 0; i < numberParticles; ++i) {
    const real mi = mass[i];
    const real sigma = std::sqrt(real(temperature) / mi);
    vel[i] = make_real3(sigma * gaussian(gen),
                        sigma * gaussian(gen),
                        is2D ? real(0.0) : sigma * gaussian(gen));
  }

  removeCenterOfMassVelocity(particles, is2D);

  double kinetic = 0.0;
  const double dof = is2D ? 2.0 * numberParticles : 3.0 * numberParticles;
  for (int i = 0; i < numberParticles; ++i) {
    kinetic += 0.5 * static_cast<double>(mass[i]) *
               static_cast<double>(dot(vel[i], vel[i]));
  }

  if (kinetic > 0.0 && dof > 0.0 && temperature > 0.0) {
    // Rescale once after removing center-of-mass drift so the final kinetic
    // temperature matches the requested value.
    const double currentTemperature = (2.0 * kinetic) / dof;
    const real scale = real(std::sqrt(temperature / currentTemperature));
    for (int i = 0; i < numberParticles; ++i) {
      vel[i] *= scale;
    }
  }
}

namespace detail {

inline void resetParticleEnergy(std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  auto energy = particles->getEnergy(access::location::gpu, access::mode::write);
  thrust::fill(thrust::cuda::par, energy.begin(), energy.end(), real(0.0));
}

inline void resetParticleVirial(std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  auto virial = particles->getVirial(access::location::gpu, access::mode::write);
  thrust::fill(thrust::cuda::par, virial.begin(), virial.end(), real(0.0));
}

inline double reduceParticleEnergy(std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  auto energy = particles->getEnergy(access::location::gpu, access::mode::read);
  return thrust::reduce(thrust::cuda::par, energy.begin(), energy.end(), 0.0);
}

inline double reduceParticleVirial(std::shared_ptr<uammd::ParticleData> particles) {
  using namespace uammd;

  auto virial = particles->getVirial(access::location::gpu, access::mode::read);
  return thrust::reduce(thrust::cuda::par, virial.begin(), virial.end(), 0.0);
}

inline double sumKineticEnergy(std::shared_ptr<uammd::Integrator> integrator,
                               std::shared_ptr<uammd::ParticleData> particles) {
  resetParticleEnergy(particles);
  integrator->sumEnergy();
  return reduceParticleEnergy(particles);
}

inline double sumInteractorEnergy(std::shared_ptr<uammd::Interactor> interactor,
                                  std::shared_ptr<uammd::ParticleData> particles) {
  if (!interactor) {
    return 0.0;
  }

  resetParticleEnergy(particles);
  interactor->sum({.force = false, .energy = true, .virial = false}, 0);
  return reduceParticleEnergy(particles);
}

inline double sumInteractorVirial(std::shared_ptr<uammd::Interactor> interactor,
                                  std::shared_ptr<uammd::ParticleData> particles) {
  if (!interactor) {
    return 0.0;
  }

  resetParticleVirial(particles);
  interactor->sum({.force = false, .energy = false, .virial = true}, 0);
  return reduceParticleVirial(particles);
}

} // namespace detail

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

inline BondedWCACorrection computeBondedWCACorrection(
    const LammpsData& ld,
    std::shared_ptr<uammd::ParticleData> particles,
    const SimulationBox& simulationBox,
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
    const real3 rij = simulationBox.box.apply_pbc(rj - ri);
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

inline ThermoSnapshot computeThermoSnapshot(
    std::shared_ptr<uammd::Integrator> integrator,
    std::shared_ptr<uammd::ParticleData> particles,
    std::shared_ptr<uammd::Interactor> nonBondedInteractor,
    std::shared_ptr<uammd::Interactor> bondedInteractor,
    const LammpsData& ld,
    const SimulationBox& simulationBox,
    double epsilon,
    double sigma,
    double volume,
    int numberParticles) {
  ThermoSnapshot thermo;

  thermo.kineticEnergy = detail::sumKineticEnergy(integrator, particles);
  thermo.nonBondedEnergy = detail::sumInteractorEnergy(nonBondedInteractor, particles);
  thermo.bondedEnergy = detail::sumInteractorEnergy(bondedInteractor, particles);
  const auto correction =
      computeBondedWCACorrection(ld, particles, simulationBox, epsilon, sigma);
  thermo.bondedEnergy += correction.energy;
  thermo.nonBondedEnergy -= correction.energy;
  thermo.totalEnergy =
      thermo.kineticEnergy + thermo.nonBondedEnergy + thermo.bondedEnergy;

  if (numberParticles > 0) {
    thermo.temperature =
        (2.0 * thermo.kineticEnergy) / (3.0 * static_cast<double>(numberParticles));
  }

  if (volume > 0.0) {
    const double nonBondedVirial =
        detail::sumInteractorVirial(nonBondedInteractor, particles);
    const double bondedVirial =
        detail::sumInteractorVirial(bondedInteractor, particles);
    // The WCA PairForces and FENE BondedForces implementations store
    // per-particle virial with opposite position-vector conventions. The
    // reduced pair term therefore enters with a minus sign, while the bonded
    // term already matches the thermodynamic sign. Both sums are doubled over
    // the two particles participating in each interaction.
    thermo.pressure =
        (2.0 * thermo.kineticEnergy) / (3.0 * volume) -
        nonBondedVirial / (6.0 * volume) +
        bondedVirial / (6.0 * volume);
  }

  return thermo;
}

inline std::string formatThermoHeader() {
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

inline std::string formatThermoRow(int step, const ThermoSnapshot& thermo) {
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

inline std::string formatPerformanceSummary(double elapsedSeconds,
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

inline void logRunConfiguration(const SimParams& par,
                                const LammpsData& ld,
                                const std::string& thermoHeader) {
  using namespace uammd;

  System::log<System::MESSAGE>("[KG] Starting");
  System::log<System::MESSAGE>("[KG] atoms %d bonds %zu box %g %g %g",
                               ld.natoms, ld.bonds.size(),
                               (ld.xhi - ld.xlo), (ld.yhi - ld.ylo), (ld.zhi - ld.zlo));
  System::log<System::MESSAGE>("[KG] dt %g T %g xi %g skin %g",
                               par.dt, par.temperature, par.friction, par.skin);
  System::log<System::MESSAGE>("[KG] Model KG (WCA + FENE)");
  System::log<System::MESSAGE>("[KG] Dump output %s",
                               par.gzipDump ? "gzip-compressed" : "plain text");
  System::log<System::MESSAGE>("[KG] Velocities %s",
                               par.initializeVelocities
                                   ? "initialized from requested temperature"
                                   : (ld.hasVelocities ? "read from input file"
                                                       : "not present in input; using zeros"));
  System::log<System::MESSAGE>("[KG] COM velocity removal %s",
                               par.removeCOMVelocity ? "on" : "off");
  System::log<System::MESSAGE>("[KG] %s", thermoHeader.c_str());
}

} // namespace kg

#endif
