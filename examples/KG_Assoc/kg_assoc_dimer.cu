#include <uammd.cuh>

#include "Integrator/VerletNVT.cuh"
#include "../KG/kg_interactors.cuh"
#include "kg_assoc_cli.cuh"
#include "kg_assoc_cutoff_audit.cuh"
#include "kg_assoc_interactors.cuh"
#include "kg_assoc_kinetics.cuh"
#include "kg_assoc_state.cuh"

#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

using namespace uammd;

namespace {

bool near(double left, double right, double tolerance = 2e-10) {
  return std::abs(left - right) <=
         tolerance * std::max(1.0, std::max(std::abs(left), std::abs(right)));
}

double dimerDistance(const std::shared_ptr<ParticleData>& particles, Box box) {
  auto positions = particles->getPos(access::cpu, access::read);
  const real3 displacement =
      box.apply_pbc(make_real3(positions[1]) - make_real3(positions[0]));
  return std::sqrt(static_cast<double>(dot(displacement, displacement)));
}

struct Theory {
  double deltaU = 0.0;
  double q = 0.0;
  double pf = 0.0;
  double pb = 0.0;
  double fractionBound = 0.0;
};

Theory staticTheory(const kg_assoc::Params& params) {
  const double deltaU =
      kg_assoc::deltaU(params.distance, params.k, params.r0, params.ee);
  const double q = kg_assoc::attemptProbability(
      params.nu0 * std::exp(-params.ea / params.temperature) * params.every *
      params.dt);
  const double pf = q * kg_assoc::metropolisFactor(
                            deltaU, params.temperature, true);
  const double pb = q * kg_assoc::metropolisFactor(
                            deltaU, params.temperature, false);
  return {deltaU, q, pf, pb, pf / (pf + pb)};
}

struct EpisodeStatistics {
  bool bound = false;
  long long startSweep = 0;
  long long completeFree = 0;
  long long completeBound = 0;
  double completeFreeSweeps = 0.0;
  double completeBoundSweeps = 0.0;

  explicit EpisodeStatistics(bool initiallyBound) : bound(initiallyBound) {}

  void transition(long long sweep, bool nowBound) {
    const long long length = sweep - startSweep;
    if (bound) {
      ++completeBound;
      completeBoundSweeps += length;
    } else {
      ++completeFree;
      completeFreeSweeps += length;
    }
    bound = nowBound;
    startSweep = sweep;
  }
};

struct StaticResult {
  long long sweeps = 0;
  long long creations = 0;
  long long breaks = 0;
  long long freeEligibleSweeps = 0;
  long long boundEligibleSweeps = 0;
  long long freeSamples = 0;
  long long boundSamples = 0;
  EpisodeStatistics episodes{false};
};

StaticResult runStatic(const kg_assoc::Params& params, bool writeFiles) {
  if (params.initialBound && params.distance >= params.r0) {
    throw std::runtime_error("initially bound static dimer requires distance < R0");
  }

  kg_assoc::StickerState state(2, {0, 1}, false);
  if (params.initialBound) {
    state.make(0, 1);
  }

  kg_assoc::Kinetics kinetics(
      {params.nu0, params.ea, params.temperature, params.dt, params.every,
       params.seed},
      params.k, params.r0, params.ee);

  std::ofstream eventFile;
  if (writeFiles) {
    eventFile.open(params.prefix + ".events");
    if (!eventFile) {
      throw std::runtime_error("cannot open static event log");
    }
    eventFile << "# timestep event_type sticker_i sticker_j\n";
  }

  StaticResult result;
  result.episodes = EpisodeStatistics(params.initialBound);
  char previousEvent = '\0';

  const long long sweeps = params.steps / params.every;
  for (long long sweep = 1; sweep <= sweeps; ++sweep) {
    const long long timestep = sweep * params.every;
    const bool candidateExists = params.distance < params.rAssoc;
    const bool wasBound = state.bonded(0, 1);

    if (candidateExists) {
      if (wasBound) {
        ++result.boundEligibleSweeps;
      } else {
        ++result.freeEligibleSweeps;
      }
    }

    std::vector<kg_assoc::Candidate> candidates;
    if (candidateExists) {
      candidates.push_back({0, 1, params.distance});
    }

    std::vector<kg_assoc::Event> events;
    kinetics.update(timestep, state, std::move(candidates), events);
    state.validate();

    for (const auto& event : events) {
      if ((previousEvent != '\0' && previousEvent == event.type) ||
          event.first != 0 || event.second != 1) {
        throw std::runtime_error("invalid static two-state event sequence");
      }
      previousEvent = event.type;
      if (event.type == 'C') {
        ++result.creations;
      } else {
        ++result.breaks;
      }
      result.episodes.transition(sweep, event.type == 'C');
      if (writeFiles) {
        eventFile << event.step << ' ' << event.type << ' ' << event.first
                  << ' ' << event.second << '\n';
      }
    }

    if (state.bonded(0, 1)) {
      ++result.boundSamples;
    } else {
      ++result.freeSamples;
    }
    ++result.sweeps;
  }

  if (result.creations - result.breaks != (state.bonded(0, 1) ? 1 : 0) -
                                              (params.initialBound ? 1 : 0)) {
    throw std::runtime_error("static creation/break state invariant failed");
  }
  return result;
}

void writeStaticSummary(const kg_assoc::Params& params, const StaticResult& result) {
  std::ofstream summary(params.prefix + ".summary");
  if (!summary) {
    throw std::runtime_error("cannot open static summary");
  }

  const bool kineticCandidate = params.distance < params.rAssoc;
  const Theory theory = kineticCandidate
                            ? staticTheory(params)
                            : Theory{std::numeric_limits<double>::quiet_NaN(),
                                     0.0, 0.0, 0.0,
                                     params.initialBound ? 1.0 : 0.0};
  const double fractionBound = result.sweeps
                                   ? static_cast<double>(result.boundSamples) /
                                         result.sweeps
                                   : 0.0;
  const double observedPf = result.freeEligibleSweeps
                                ? static_cast<double>(result.creations) /
                                      result.freeEligibleSweeps
                                : 0.0;
  const double observedPb = result.boundEligibleSweeps
                                ? static_cast<double>(result.breaks) /
                                      result.boundEligibleSweeps
                                : 0.0;
  const double meanFree = result.episodes.completeFree
                              ? result.episodes.completeFreeSweeps /
                                    result.episodes.completeFree
                              : std::numeric_limits<double>::quiet_NaN();
  const double meanBound = result.episodes.completeBound
                               ? result.episodes.completeBoundSweeps /
                                     result.episodes.completeBound
                               : std::numeric_limits<double>::quiet_NaN();
  const auto reportComparison = [&](const char* name, double observed,
                                    double expected) {
    summary << name << "_observed " << observed << "\n"
            << name << "_expected " << expected << "\n"
            << name << "_absolute_difference " << std::abs(observed - expected)
            << "\n"
            << name << "_relative_difference "
            << (expected ? observed / expected - 1.0
                         : std::numeric_limits<double>::quiet_NaN())
            << "\n";
  };

  summary << std::setprecision(12)
          << "mode static\n"
          << "distance " << params.distance << "\n"
          << "kinetic_sweeps " << result.sweeps << "\n"
          << "accepted_creations " << result.creations << "\n"
          << "accepted_breaks " << result.breaks << "\n"
          << "fraction_free " << (1.0 - fractionBound) << "\n"
          << "fraction_bound " << fractionBound << "\n"
          << "complete_free_episodes " << result.episodes.completeFree << "\n"
          << "complete_bound_episodes " << result.episodes.completeBound << "\n"
          << "mean_free_episode_sweeps " << meanFree << "\n"
          << "mean_bound_episode_sweeps " << meanBound << "\n"
          << "eligible_free_sweeps " << result.freeEligibleSweeps << "\n"
          << "eligible_bound_sweeps " << result.boundEligibleSweeps << "\n"
          << "observed_Pf " << observedPf << "\n"
          << "observed_Pb " << observedPb << "\n"
          << "theoretical_deltaU " << theory.deltaU << "\n"
          << "theoretical_q " << theory.q << "\n"
          << "theoretical_Pf " << theory.pf << "\n"
          << "theoretical_Pb " << theory.pb << "\n"
          << "theoretical_fraction_bound " << theory.fractionBound << "\n"
          << "theoretical_mean_free_episode_sweeps "
          << (theory.pf ? 1.0 / theory.pf : std::numeric_limits<double>::infinity())
          << "\n"
          << "theoretical_mean_bound_episode_sweeps "
          << (theory.pb ? 1.0 / theory.pb : std::numeric_limits<double>::infinity())
          << "\n";
  reportComparison("Pf", observedPf, theory.pf);
  reportComparison("Pb", observedPb, theory.pb);
  reportComparison("fraction_bound", fractionBound, theory.fractionBound);
  reportComparison("mean_free_episode", meanFree,
                   theory.pf ? 1.0 / theory.pf
                             : std::numeric_limits<double>::infinity());
  reportComparison("mean_bound_episode", meanBound,
                   theory.pb ? 1.0 / theory.pb
                             : std::numeric_limits<double>::infinity());
  std::cout << summary.rdbuf();
}

bool staticRegression() {
  kg_assoc::Params params;
  params.steps = 1000;
  params.every = 10;
  params.distance = kg_assoc::rstar(params.k, params.r0);
  params.ea = 2.0;
  params.ee = 2.0;

  const Theory theory = staticTheory(params);
  if (!near(theory.pf / theory.pb,
            std::exp(-theory.deltaU / params.temperature)) ||
      !near(theory.fractionBound, theory.pf / (theory.pf + theory.pb)) ||
      !near(1.0 / theory.pf, 1.0 / theory.pf)) {
    return false;
  }

  params.distance = 1.20;
  params.rAssoc = std::pow(2.0, 1.0 / 6.0);
  params.initialBound = false;
  const StaticResult freeOutsideCutoff = runStatic(params, false);
  if (freeOutsideCutoff.creations != 0 || freeOutsideCutoff.breaks != 0 ||
      freeOutsideCutoff.boundSamples != 0) {
    return false;
  }

  params.initialBound = true;
  const StaticResult boundOutsideCutoff = runStatic(params, false);
  if (boundOutsideCutoff.creations != 0 || boundOutsideCutoff.breaks != 0 ||
      boundOutsideCutoff.freeSamples != 0) {
    return false;
  }

  params.distance = params.r0;
  try {
    (void)runStatic(params, false);
    return false;
  } catch (const std::runtime_error&) {
    return true;
  }
}

bool interactorRegression() {
  const double k = 30.0;
  const double r0 = 1.5;
  const double ee = 4.0;
  const double deltaEe = 1.75;
  const double rStar = kg_assoc::rstar(k, r0);
  const double shift = kg_assoc::associatingFeneShift(k, r0, ee, rStar);
  const double shiftedEe =
      kg_assoc::associatingFeneShift(k, r0, ee + deltaEe, rStar);

  for (const double distance : {0.8, rStar, 1.1, 1.2}) {
    const double energy =
        kg_assoc::checkedAssociatingFeneEnergy(distance, k, r0, shift);
    const double expected = kg_assoc::fene(distance, k, r0) -
                            kg_assoc::fene(rStar, k, r0) - ee;
    if (!near(energy, expected, 3e-5)) {
      return false;
    }

    const double finiteDifference = 1e-4;
    const double numericalForce =
        -(kg_assoc::checkedAssociatingFeneEnergy(
              distance + finiteDifference, k, r0, shift) -
          kg_assoc::checkedAssociatingFeneEnergy(
              distance - finiteDifference, k, r0, shift)) /
        (2.0 * finiteDifference);
    const double interactorForce =
        -distance * kg_assoc::associatingFeneForceDivR(
                        real(distance * distance), real(k), real(r0));
    const double shiftedNumericalForce =
        -(kg_assoc::checkedAssociatingFeneEnergy(
              distance + finiteDifference, k, r0, shiftedEe) -
          kg_assoc::checkedAssociatingFeneEnergy(
              distance - finiteDifference, k, r0, shiftedEe)) /
        (2.0 * finiteDifference);
    if (!near(numericalForce, interactorForce, 3e-3) ||
        !near(shiftedNumericalForce, interactorForce, 3e-3)) {
      return false;
    }

    const double shiftedEnergy =
        kg_assoc::checkedAssociatingFeneEnergy(distance, k, r0, shiftedEe);
    if (!near(shiftedEnergy - energy, -deltaEe, 3e-5)) {
      return false;
    }
  }

  if (!near(kg_assoc::checkedAssociatingFeneEnergy(rStar, k, r0, shift),
            -ee, 3e-5) ||
      !std::isfinite(
          kg_assoc::checkedAssociatingFeneEnergy(1.49, k, r0, shift))) {
    return false;
  }

  try {
    (void)kg_assoc::checkedAssociatingFeneEnergy(r0, k, r0, shift);
    return false;
  } catch (const std::runtime_error&) {
    return true;
  }
}

bool diagnostics(const kg_assoc::Params& params) {
  if (!params.rAssocExplicit &&
      !near(params.rAssoc, kg_assoc::kDefaultReactionCutoff)) {
    return false;
  }
  const double rStar = kg_assoc::rstar(params.k, params.r0);
  const double step = 1e-6;

  for (const double distance : {0.8, rStar, 1.2, 1.49}) {
    const double numericalForce =
        -(kg_assoc::deltaU(distance + step, params.k, params.r0, params.ee) -
          kg_assoc::deltaU(distance - step, params.k, params.r0, params.ee)) /
        (2.0 * step);
    const double analyticForce =
        -params.k * distance /
        (1.0 - distance * distance / (params.r0 * params.r0));
    if (!near(numericalForce, analyticForce, 3e-5)) {
      return false;
    }
  }

  kg_assoc::CutoffAudit cutoffAudit;
  for (const double distance : {0.9, 1.13, 1.17, 1.22}) {
    cutoffAudit.observe(distance, params.k, params.r0, params.ee,
                        params.temperature);
  }
  for (std::size_t index = 1;
       index < kg_assoc::kCutoffAuditThresholds.size(); ++index) {
    if (cutoffAudit.outside[index - 1] < cutoffAudit.outside[index] ||
        cutoffAudit.missingBreakWeight[index - 1] <
            cutoffAudit.missingBreakWeight[index]) {
      return false;
    }
  }

  if (!interactorRegression() || !staticRegression()) {
    return false;
  }
  std::cout << "SELF_TEST PASS actual-interactor and static-kinetics regressions\n";
  return true;
}

int runBondedRadialAudit(const kg_assoc::Params& params, int argc, char** argv) {
  auto system = std::make_shared<System>(argc, argv);
  Box box(make_real3(real(params.box)));
  box.setPeriodicity(true, true, true);
  auto particles = std::make_shared<ParticleData>(2, system);

  {
    auto positions = particles->getPos(access::cpu, access::write);
    auto ids = particles->getId(access::cpu, access::write);
    auto masses = particles->getMass(access::cpu, access::write);
    auto velocities = particles->getVel(access::cpu, access::write);
    auto forces = particles->getForce(access::cpu, access::write);
    positions[0] = make_real4(real(-.5), real(0), real(0), real(0));
    positions[1] = make_real4(real(.5), real(0), real(0), real(0));
    for (int index = 0; index < 2; ++index) {
      ids[index] = index;
      masses[index] = real(1);
      velocities[index] = make_real3(real(0));
      forces[index] = make_real4(real(0));
    }
  }

  kg_assoc::StickerState state(2, {0, 1});
  state.make(0, 1);
  state.syncDevice();
  auto wca = kg::createWCAInteractor_CellList(particles, box, 1, 1., 1., .3);
  auto associating = std::make_shared<kg_assoc::AssociatingFENEInteractor>(
      particles, box, state.devicePartner(), params.k, params.r0, params.ee,
      kg_assoc::rstar(params.k, params.r0));
  using NVT = VerletNVT::GronbechJensen;
  NVT::Parameters integratorParameters;
  integratorParameters.temperature = real(params.temperature);
  integratorParameters.friction = real(params.friction);
  integratorParameters.dt = real(params.dt);
  integratorParameters.initVelocities = true;
  auto integrator = std::make_shared<NVT>(particles, integratorParameters);
  integrator->addInteractor(wca);
  integrator->addInteractor(associating);

  kg_assoc::CutoffAudit audit;
  for (int step = 1; step <= params.steps; ++step) {
    integrator->forwardTime();
    if (step <= params.auditBurnin || step % params.auditSample != 0) {
      continue;
    }
    CudaSafeCall(cudaStreamSynchronize(integrator->getStream()));
    const double distance = dimerDistance(particles, box);
    if (associating->hasInvalidFene() || distance >= params.r0) {
      throw std::runtime_error("bonded radial audit reached invalid FENE distance");
    }
    audit.observe(distance, params.k, params.r0, params.ee, params.temperature);
  }

  std::ofstream output(params.prefix + ".cutoff_audit");
  if (!output) {
    throw std::runtime_error("cannot open bonded radial audit output");
  }
  output << std::setprecision(12)
         << "mode bonded_radial_audit\n"
         << "Ee " << params.ee << "\n"
         << "K " << params.k << "\n"
         << "R0 " << params.r0 << "\n"
         << "temperature " << params.temperature << "\n"
         << "steps " << params.steps << "\n"
         << "burnin_steps " << params.auditBurnin << "\n"
         << "sample_interval_steps " << params.auditSample << "\n";
  audit.write(output);
  audit.write(std::cout);
  return 0;
}

int runDynamic(const kg_assoc::Params& params, int argc, char** argv) {
  auto system = std::make_shared<System>(argc, argv);
  Box box(make_real3(real(params.box)));
  box.setPeriodicity(true, true, true);
  auto particles = std::make_shared<ParticleData>(2, system);

  {
    auto positions = particles->getPos(access::cpu, access::write);
    auto ids = particles->getId(access::cpu, access::write);
    auto masses = particles->getMass(access::cpu, access::write);
    auto velocities = particles->getVel(access::cpu, access::write);
    auto forces = particles->getForce(access::cpu, access::write);
    positions[0] = make_real4(real(-.5), real(0), real(0), real(0));
    positions[1] = make_real4(real(.5), real(0), real(0), real(0));
    for (int index = 0; index < 2; ++index) {
      ids[index] = index;
      masses[index] = real(1);
      velocities[index] = make_real3(real(0));
      forces[index] = make_real4(real(0));
    }
  }

  kg_assoc::StickerState state(2, {0, 1});
  auto wca = kg::createWCAInteractor_CellList(particles, box, 1, 1., 1., .3);
  auto associating = std::make_shared<kg_assoc::AssociatingFENEInteractor>(
      particles, box, state.devicePartner(), params.k, params.r0, params.ee,
      kg_assoc::rstar(params.k, params.r0));

  using NVT = VerletNVT::GronbechJensen;
  NVT::Parameters integratorParameters;
  integratorParameters.temperature = real(params.temperature);
  integratorParameters.friction = real(params.friction);
  integratorParameters.dt = real(params.dt);
  integratorParameters.initVelocities = true;
  auto integrator = std::make_shared<NVT>(particles, integratorParameters);
  integrator->addInteractor(wca);
  integrator->addInteractor(associating);

  kg_assoc::Kinetics kinetics(
      {params.nu0, params.ea, params.temperature, params.dt, params.every,
       params.seed},
      params.k, params.r0, params.ee);
  std::ofstream events(params.prefix + ".events");
  if (!events) {
    throw std::runtime_error("cannot open dynamic event log");
  }
  events << "# timestep event_type sticker_i sticker_j\n";

  long long kineticUpdates = 0;
  long long creations = 0;
  long long breaks = 0;
  long long bondedSamples = 0;
  long long unboundSamples = 0;
  long long bondDistanceSamples = 0;
  long long boundStart = -1;
  long long freeStart = 0;
  long long completeBoundEpisodes = 0;
  long long completeFreeEpisodes = 0;
  double bondDistanceSum = 0.0;
  double boundDuration = 0.0;
  double freeDuration = 0.0;

  for (int step = 1; step <= params.steps; ++step) {
    integrator->forwardTime();
    if (step % params.every != 0) {
      continue;
    }

    ++kineticUpdates;
    CudaSafeCall(cudaStreamSynchronize(integrator->getStream()));
    const double distance = dimerDistance(particles, box);
    if (associating->hasInvalidFene() ||
        (state.bonded(0, 1) && distance >= params.r0)) {
      throw std::runtime_error("associating FENE bond exceeded R0");
    }

    std::vector<kg_assoc::Candidate> candidates;
    if (distance < params.rAssoc) {
      candidates.push_back({0, 1, distance});
    }
    std::vector<kg_assoc::Event> accepted;
    kinetics.update(step, state, std::move(candidates), accepted);
    for (const auto& event : accepted) {
      events << event.step << ' ' << event.type << ' ' << event.first << ' '
             << event.second << '\n';
      if (event.type == 'C') {
        ++creations;
        freeDuration += step - freeStart;
        ++completeFreeEpisodes;
        boundStart = step;
      } else {
        ++breaks;
        boundDuration += step - boundStart;
        ++completeBoundEpisodes;
        freeStart = step;
      }
    }

    if (state.bonded(0, 1)) {
      ++bondedSamples;
      bondDistanceSum += distance;
      ++bondDistanceSamples;
    } else {
      ++unboundSamples;
    }
  }

  if (state.bonded(0, 1)) {
    boundDuration += params.steps + 1 - boundStart;
    ++completeBoundEpisodes;
  } else {
    freeDuration += params.steps + 1 - freeStart;
    ++completeFreeEpisodes;
  }

  std::ofstream summary(params.prefix + ".summary");
  if (!summary) {
    throw std::runtime_error("cannot open dynamic summary");
  }
  summary << std::setprecision(12)
          << "kinetic_updates " << kineticUpdates << "\n"
          << "accepted_creations " << creations << "\n"
          << "accepted_breaks " << breaks << "\n"
          << "fraction_bonded "
          << (kineticUpdates
                  ? static_cast<double>(bondedSamples) / kineticUpdates
                  : 0.0)
          << "\n"
          << "fraction_unbonded "
          << (kineticUpdates
                  ? static_cast<double>(unboundSamples) / kineticUpdates
                  : 0.0)
          << "\n"
          << "mean_bond_distance "
          << (bondDistanceSamples
                  ? bondDistanceSum / bondDistanceSamples
                  : std::numeric_limits<double>::quiet_NaN())
          << "\n"
          << "mean_bonded_episode_steps "
          << (completeBoundEpisodes
                  ? boundDuration / completeBoundEpisodes
                  : 0.0)
          << "\n"
          << "mean_unbound_episode_steps "
          << (completeFreeEpisodes
                  ? freeDuration / completeFreeEpisodes
                  : 0.0)
          << "\n";
  summary.close();
  std::cout << "kinetic_updates " << kineticUpdates << "\n"
            << "accepted_creations " << creations << "\n"
            << "accepted_breaks " << breaks << "\n";
  return 0;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const kg_assoc::Params params = kg_assoc::parseArgs(argc, argv);
    if (!diagnostics(params)) {
      std::cerr << "SELF_TEST FAIL\n";
      return 2;
    }
    if (params.selfTest) {
      return 0;
    }
    if (params.staticMode) {
      const StaticResult result = runStatic(params, true);
      writeStaticSummary(params, result);
      return 0;
    }
    if (params.bondedRadialAudit) {
      return runBondedRadialAudit(params, argc, argv);
    }
    return runDynamic(params, argc, argv);
  } catch (const std::exception& error) {
    std::cerr << "Dimer error: " << error.what() << '\n';
    return 1;
  }
}
