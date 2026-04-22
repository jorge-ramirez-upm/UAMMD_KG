#ifndef EXAMPLES_KG_KG_INTERACTORS_CUH
#define EXAMPLES_KG_KG_INTERACTORS_CUH

// Interactor builders for the Kremer-Grest example.
//
// These wrappers hide the UAMMD template plumbing needed to instantiate the
// WCA nonbonded term and the FENE bonded term used by the model.

#include "Interactor/BondedForces.cuh"
#include "Interactor/NeighbourList/VerletList.cuh"
#include "Interactor/PairForces.cuh"
#include "Interactor/Potential/DPD.cuh"
#include "Interactor/Potential/Potential.cuh"

#include <cmath>
#include <memory>
#include <string>

#include <uammd.cuh>

namespace kg {

class DPDWithConservativeEnergy : public uammd::Potential::DPD {
 public:
  using Base = uammd::Potential::DPD;
  using Parameters = Base::Parameters;

  explicit DPDWithConservativeEnergy(Parameters par) : Base(par) {}

  struct Transverser {
   private:
    uammd::real4* pos;
    uammd::real3* vel;
    uammd::real4* force;
    uammd::real* energy;
    uammd::real* virial;
    uammd::Box box;
    ullint seed;
    ullint step;
    int N;
    uammd::real rcut;
    uammd::real invrcut;
    uammd::Potential::DefaultDissipation gamma;
    uammd::real sigma;
    uammd::real A;

   public:
    using returnInfo = uammd::ForceEnergyVirial;

    struct Info {
      uammd::real3 vel;
      int id;
    };

    Transverser(uammd::real4* pos,
                uammd::real3* vel,
                uammd::real4* force,
                uammd::real* energy,
                uammd::real* virial,
                ullint seed,
                ullint step,
                uammd::Box box,
                int N,
                uammd::real rcut,
                uammd::Potential::DefaultDissipation gamma,
                uammd::real sigma,
                uammd::real A)
        : pos(pos),
          vel(vel),
          force(force),
          energy(energy),
          virial(virial),
          box(box),
          seed(seed),
          step(step),
          N(N),
          rcut(rcut),
          invrcut(uammd::real(1.0) / rcut),
          gamma(gamma),
          sigma(sigma),
          A(A) {}

    inline __device__ returnInfo compute(const uammd::real4& pi,
                                         const uammd::real4& pj,
                                         const Info& infoi,
                                         const Info& infoj) {
      using namespace uammd;

      const real3 rij = box.apply_pbc(make_real3(pi) - make_real3(pj));
      const real3 vij = make_real3(infoi.vel) - make_real3(infoj.vel);
      const real r2 = dot(rij, rij);
      if (r2 <= real(0.0)) {
        return {};
      }

      const real rmod = sqrt(r2);
      if (rmod >= rcut) {
        return {};
      }

      int i = infoi.id;
      int j = infoj.id;
      if (i > j) {
        thrust::swap(i, j);
      }

      const int ij = i + N * j;
      Saru rng(ij, seed, step);
      const real invrmod = real(1.0) / rmod;
      const real wr = real(1.0) - rmod * invrcut;

      const real Fc = A * wr * invrmod;
      const real g =
          gamma.dissipativeStrength(i, j, pi, pj, infoi.vel, infoj.vel);
      const real wd = wr * wr;
      const real Fd = -g * wd * invrmod * invrmod * dot(rij, vij);
      const real Fr = rng.gf(real(0.0), sigma * sqrt(g) * wr * invrmod).x;
      const real3 F = (force || virial) ? (Fc + Fd + Fr) * rij : real3();
      const real E = energy ? real(0.5) * A * rcut * wr * wr : real(0.0);
      const real V = virial ? dot(F, rij) : real(0.0);
      return {F, E, V};
    }

    inline __device__ Info getInfo(int pi) { return {vel[pi], pi}; }

    inline __device__ void set(uint pi, const returnInfo& total) {
      if (force) {
        force[pi] += uammd::make_real4(total.force, 0);
      }
      if (energy) {
        energy[pi] += total.energy;
      }
      if (virial) {
        virial[pi] += total.virial;
      }
    }
  };

  auto getTransverser(uammd::Interactor::Computables comp,
                      uammd::Box box,
                      std::shared_ptr<uammd::ParticleData> pd) {
    using namespace uammd;

    auto pos = pd->getPos(access::location::gpu, access::mode::read);
    auto vel = pd->getVel(access::location::gpu, access::mode::read);
    auto force = comp.force ? pd->getForce(access::location::gpu,
                                           access::mode::readwrite)
                                  .raw()
                            : nullptr;
    auto energy = comp.energy ? pd->getEnergy(access::location::gpu,
                                              access::mode::readwrite)
                                    .raw()
                              : nullptr;
    auto virial = comp.virial ? pd->getVirial(access::location::gpu,
                                              access::mode::readwrite)
                                    .raw()
                              : nullptr;
    static auto seed = pd->getSystem()->rng().next();
    this->step++;
    const int N = pd->getNumParticles();
    return Transverser(pos.raw(), vel.raw(), force, energy, virial, seed,
                       this->step, box, N, this->rcut, this->gamma,
                       this->sigma, this->A);
  }
};

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

inline std::shared_ptr<uammd::Interactor> createDPDInteractor(
    std::shared_ptr<uammd::ParticleData> particleData,
    const uammd::Box& box,
    double temperature,
    double gamma,
    double amplitude,
    double cutOff,
    double dt) {
  using namespace uammd;

  using PairForce = PairForces<DPDWithConservativeEnergy>;

  DPDWithConservativeEnergy::Parameters dpd;
  dpd.temperature = static_cast<real>(temperature);
  dpd.gamma = static_cast<real>(gamma);
  dpd.A = static_cast<real>(amplitude);
  dpd.cutOff = static_cast<real>(cutOff);
  dpd.dt = static_cast<real>(dt);

  PairForce::Parameters params;
  params.box = box;

  return std::make_shared<PairForce>(particleData, params,
                                     std::make_shared<DPDWithConservativeEnergy>(dpd));
}

} // namespace kg

#endif
