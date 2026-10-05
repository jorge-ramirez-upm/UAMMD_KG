#include <uammd.cuh>

#include "../KG/kg_interactors.cuh"
#include "../KG/kg_runtime.cuh"
#include "kg_assoc_interactors.cuh"
#include "kg_assoc_kinetics.cuh"
#include "kg_assoc_state.cuh"

#include <cmath>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

namespace {

using Stress = kg::detail::StressTensorSample;

bool near(double left, double right, double tolerance = 2e-5) {
  return std::abs(left - right) <=
         tolerance * std::max(1.0, std::max(std::abs(left), std::abs(right)));
}

void requireNear(const Stress& actual, const Stress& expected, const char* label) {
  const double actualValues[] = {actual.xx, actual.yy, actual.zz,
                                 actual.xy, actual.xz, actual.yz};
  const double expectedValues[] = {expected.xx, expected.yy, expected.zz,
                                   expected.xy, expected.xz, expected.yz};
  for (int component = 0; component < 6; ++component) {
    if (!near(actualValues[component], expectedValues[component])) {
      throw std::runtime_error(std::string(label) + " component " +
                               std::to_string(component) + " mismatch");
    }
  }
}

Stress scaled(double factor, const Stress& value) {
  return factor * value;
}

Stress associatingStress(const kg_assoc::AssociatingFENEInteractor& interactor,
                         double volume) {
  return scaled(0.5 / volume, kg::detail::reduceInteractorStress(interactor));
}

Stress analyticAssociatingStress(const uammd::real3& rij,
                                 double k,
                                 double r0,
                                 double volume) {
  const double r2 = rij.x * rij.x + rij.y * rij.y + rij.z * rij.z;
  const double forceDivR = k / (1.0 - r2 / (r0 * r0));
  const double fx = forceDivR * rij.x;
  const double fy = forceDivR * rij.y;
  const double fz = forceDivR * rij.z;
  return {-rij.x * fx / volume, -rij.y * fy / volume, -rij.z * fz / volume,
          -rij.x * fy / volume, -rij.x * fz / volume, -rij.y * fz / volume};
}

struct Fixture {
  std::shared_ptr<uammd::System> system;
  std::shared_ptr<uammd::ParticleData> particles;
  kg::SimulationBox box;

  Fixture() : system(std::make_shared<uammd::System>()),
              particles(std::make_shared<uammd::ParticleData>(3, system)),
              box{uammd::Box(uammd::make_real3(uammd::real(8.0)))} {
    box.box.setPeriodicity(true, true, true);
    auto positions = particles->getPos(uammd::access::cpu, uammd::access::write);
    auto velocities = particles->getVel(uammd::access::cpu, uammd::access::write);
    auto masses = particles->getMass(uammd::access::cpu, uammd::access::write);
    auto ids = particles->getId(uammd::access::cpu, uammd::access::write);
    auto forces = particles->getForce(uammd::access::cpu, uammd::access::write);
    positions[0] = uammd::make_real4(-0.8, -0.4, -0.3, 0.0);
    positions[1] = uammd::make_real4(0.0, 0.0, 0.0, 0.0);
    positions[2] = uammd::make_real4(0.6, 0.5, 0.4, 0.0);
    velocities[0] = uammd::make_real3(0.1, -0.2, 0.3);
    velocities[1] = uammd::make_real3(-0.3, 0.2, -0.1);
    velocities[2] = uammd::make_real3(0.2, 0.1, -0.2);
    for (int i = 0; i < 3; ++i) {
      ids[i] = i;
      masses[i] = uammd::real(1.0);
      forces[i] = uammd::make_real4(0.0);
    }
  }
};

void updateStress(const std::shared_ptr<uammd::Interactor>& interactor) {
  interactor->sum({.force = false, .energy = false, .virial = false, .stress = true});
  CudaSafeCall(cudaDeviceSynchronize());
}

void runStressRegression() {
  constexpr double k = 30.0;
  constexpr double r0 = 1.5;
  Fixture fixture;
  const double volume = fixture.box.box.getVolume();
  kg_assoc::StickerState state(3, {1, 2});
  auto associating = std::make_shared<kg_assoc::AssociatingFENEInteractor>(
      fixture.particles, fixture.box.box, state.devicePartner(), k, r0, 8.0,
      kg_assoc::rstar(k, r0));
  auto wca = kg::createWCAStressInteractor_CellList(
      fixture.particles, fixture.box.box, 1, 1.0, 1.0, 0.4);
  auto permanent = kg::createFENEStressInteractor(
      fixture.particles, fixture.box.box, {{1, 2}}, k, r0);

  updateStress(wca);
  updateStress(permanent);
  updateStress(associating);
  const Stress ordinary = kg::sampleStressTensor(
      fixture.particles, fixture.box, wca, permanent);
  const Stress withoutAssociations = kg::sampleStressTensor(
      fixture.particles, fixture.box, wca, permanent, associating);
  requireNear(withoutAssociations, ordinary, "zero temporary bonds");
  requireNear(associatingStress(*associating, volume), kg::detail::zeroStressTensorSample(),
              "zero temporary bond cache");

  state.make(1, 2);
  state.syncDevice();
  updateStress(associating);
  const uammd::real3 rij = uammd::make_real3(0.6, 0.5, 0.4);
  const Stress expected = analyticAssociatingStress(rij, k, r0, volume);
  const Stress actual = associatingStress(*associating, volume);
  requireNear(actual, expected, "one non-axis-aligned temporary bond");

  const double r2 = rij.x * rij.x + rij.y * rij.y + rij.z * rij.z;
  const double forceDivR = k / (1.0 - r2 / (r0 * r0));
  const double expectedTrace = -forceDivR * r2 / volume;
  if (!near(actual.xx + actual.yy + actual.zz, expectedTrace)) {
    throw std::runtime_error("associating trace/virial convention mismatch");
  }

  {
    auto positions = fixture.particles->getPos(uammd::access::cpu, uammd::access::readwrite);
    const uammd::real4 temporary = positions[1];
    positions[1] = positions[2];
    positions[2] = temporary;
  }
  updateStress(associating);
  requireNear(associatingStress(*associating, volume), actual, "endpoint reversal");

  updateStress(wca);
  updateStress(permanent);
  const Stress total = kg::sampleStressTensor(
      fixture.particles, fixture.box, wca, permanent, associating);
  const Stress decomposed = kg::sampleStressTensor(
      fixture.particles, fixture.box, wca, permanent) + associatingStress(*associating, volume);
  requireNear(total, decomposed, "total decomposed stress");

  thrust::device_vector<Stress> partialSums(1);
  thrust::device_vector<Stress> bufferedSample(1);
  kg::appendStressTensorSampleAsync(
      fixture.particles, fixture.box, wca, permanent, associating,
      thrust::raw_pointer_cast(partialSums.data()),
      thrust::raw_pointer_cast(bufferedSample.data()), 0);
  CudaSafeCall(cudaDeviceSynchronize());
  requireNear(bufferedSample[0], total, "asynchronous stress reducer");

  if (!std::isfinite((total.xx + total.yy + total.zz) / 3.0)) {
    throw std::runtime_error("nonfinite total pressure from stress trace");
  }

  state.breakPair(1, 2);
  state.syncDevice();
  updateStress(associating);
  requireNear(associatingStress(*associating, volume), kg::detail::zeroStressTensorSample(),
              "stale temporary stress after bond break");

  kg_assoc::Kinetics kinetics({1000.0, 0.0, 1.0, 0.01, 1, 9876}, k, r0, 0.0);
  bool sawCreation = false;
  bool sawBreak = false;
  for (int step = 1; step <= 1000 && (!sawCreation || !sawBreak); ++step) {
    std::vector<kg_assoc::Event> events;
    kinetics.update(step, state, {{1, 2, std::sqrt(r2)}}, events);
    updateStress(associating);
    const Stress liveStress = associatingStress(*associating, volume);
    if (state.bonded(1, 2)) {
      sawCreation = sawCreation || !events.empty();
      requireNear(liveStress, actual, "live kinetic association stress");
    } else {
      sawBreak = sawBreak || !events.empty();
      requireNear(liveStress, kg::detail::zeroStressTensorSample(),
                  "live kinetic dissociation stress");
    }
  }
  if (!sawCreation || !sawBreak) {
    throw std::runtime_error("short kinetic smoke did not form and break a bond");
  }

  std::cout << "KG_ASSOC_STRESS_TEST PASS tensor, reversal, trace, decomposition, kinetic topology\n";
}

}  // namespace

int main() {
  try {
    runStressRegression();
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "KG_ASSOC_STRESS_TEST FAIL " << error.what() << '\n';
    return 1;
  }
}
