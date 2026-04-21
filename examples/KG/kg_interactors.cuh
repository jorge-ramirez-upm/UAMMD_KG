#ifndef EXAMPLES_KG_KG_INTERACTORS_CUH
#define EXAMPLES_KG_KG_INTERACTORS_CUH

// Interactor builders for the Kremer-Grest example.
//
// These wrappers hide the UAMMD template plumbing needed to instantiate the
// WCA nonbonded term and the FENE bonded term used by the model.

#include "Interactor/BondedForces.cuh"
#include "Interactor/NeighbourList/VerletList.cuh"
#include "Interactor/PairForces.cuh"
#include "Interactor/Potential/Potential.cuh"

#include <cmath>
#include <memory>
#include <string>

#include <uammd.cuh>

namespace kg {

inline std::shared_ptr<uammd::Interactor> createWCAInteractor_CellList(
    std::shared_ptr<uammd::ParticleData> particleData,
    const uammd::Box& box,
    int atomTypes,
    double epsilon,
    double sigma,
    double skin) {
  using namespace uammd;

  using PairForce = PairForces<Potential::LJ, VerletList>;
  auto potential = std::make_shared<Potential::LJ>();

  // WCA is implemented as a shifted Lennard-Jones potential truncated at the
  // minimum, which removes the attractive tail.
  const double cutoff = std::pow(2.0, 1.0 / 6.0) * sigma;
  for (int ti = 0; ti < atomTypes; ++ti) {
    for (int tj = 0; tj < atomTypes; ++tj) {
      Potential::LJ::InputPairParameters par;
      par.epsilon = static_cast<real>(epsilon);
      par.sigma = static_cast<real>(sigma);
      par.cutOff = static_cast<real>(cutoff);
      par.shift = true;
      potential->setPotParameters(ti, tj, par);
    }
  }

  PairForce::Parameters params;
  params.box = box;
  // The standard KG setup uses an explicit Verlet neighbour list.
  params.nl = std::make_shared<VerletList>(particleData);
  if (params.nl && skin > 0.0) {
    // UAMMD stores the neighbour-list radius as a multiple of the force cutoff.
    const real multiplier = static_cast<real>((cutoff + skin) / cutoff);
    params.nl->setCutOffMultiplier(multiplier);
  }

  return std::make_shared<PairForce>(particleData, params, potential);
}

inline std::shared_ptr<uammd::Interactor> createFENEInteractor(
    std::shared_ptr<uammd::ParticleData> particleData,
    const uammd::Box& box,
    const std::string& bondData) {
  using namespace uammd;

  using Bond = BondedType::FENE;
  using BondedForce = BondedForces<Bond, 2>;

  BondedForce::Parameters params;
  // `bondData` is the text payload built from the original LAMMPS topology.
  params.data = bondData;
  return std::make_shared<BondedForce>(particleData, params,
                                       std::make_shared<Bond>(box));
}

} // namespace kg

#endif
