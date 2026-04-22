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
#include <vector>

#include <thrust/device_vector.h>
#include <thrust/fill.h>

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

namespace stress_detail {

inline __device__ uammd::real4 makeDiagStress(const uammd::real3& rij,
                                              const uammd::real3& force) {
  return uammd::make_real4(rij.x * force.x, rij.y * force.y, rij.z * force.z,
                           uammd::real(0.0));
}

inline __device__ uammd::real4 makeOffStress(const uammd::real3& rij,
                                             const uammd::real3& force) {
  return uammd::make_real4(rij.x * force.y, rij.x * force.z, rij.y * force.z,
                           uammd::real(0.0));
}

inline __device__ uammd::real ljForceDivR(uammd::real r2,
                                          uammd::real sigma,
                                          uammd::real epsilon) {
  const uammd::real invr2 = (sigma * sigma) / r2;
  const uammd::real invr6 = invr2 * invr2 * invr2;
  return epsilon * (uammd::real(-48.0) * invr6 + uammd::real(24.0)) * invr6 *
         invr2;
}

inline __device__ uammd::real ljShiftedEnergyHalf(uammd::real r2,
                                                  uammd::real sigma,
                                                  uammd::real epsilon) {
  const uammd::real invr2 = (sigma * sigma) / r2;
  const uammd::real invr6 = invr2 * invr2 * invr2;
  return uammd::real(0.5) *
         (uammd::real(4.0) * epsilon * invr6 * (invr6 - uammd::real(1.0)) +
          epsilon);
}

inline __device__ uammd::real feneForceDivR(uammd::real r2,
                                            uammd::real k,
                                            uammd::real r0) {
  const uammd::real r02 = r0 * r0;
  return -r02 * k / (r02 - r2);
}

inline __device__ uammd::real feneEnergyHalf(uammd::real r2,
                                             uammd::real k,
                                             uammd::real r0) {
  const uammd::real r02 = r0 * r0;
  return -uammd::real(0.25) * k * r02 * log(uammd::real(1.0) - r2 / r02);
}

template <class NeighbourContainer>
__global__ void computeWCAWithStress(NeighbourContainer neighbours,
                                     int numberParticles,
                                     uammd::Box box,
                                     uammd::real4* force,
                                     uammd::real* energy,
                                     uammd::real* virial,
                                     uammd::real4* stressDiag,
                                     uammd::real4* stressOff,
                                     uammd::real sigma,
                                     uammd::real epsilon,
                                     uammd::real cutOff2) {
  using namespace uammd;

  const int sortedIndex = blockIdx.x * blockDim.x + threadIdx.x;
  if (sortedIndex >= numberParticles) {
    return;
  }

  const real3 pi = make_real3(neighbours.getSortedPositions()[sortedIndex]);
  const int globalIndex = neighbours.getGroupIndexes()[sortedIndex];
  real3 totalForce = make_real3(real(0.0));
  real totalEnergy = real(0.0);
  real totalVirial = real(0.0);
  real4 totalStressDiag = make_real4(real(0.0));
  real4 totalStressOff = make_real4(real(0.0));

  neighbours.set(sortedIndex);
  auto it = neighbours.begin();
  while (it) {
    auto neighbour = *it++;
    const real3 pj = make_real3(neighbour.getPos());
    const real3 rij = box.apply_pbc(pj - pi);
    const real r2 = dot(rij, rij);
    if (r2 <= real(0.0) || r2 >= cutOff2) {
      continue;
    }

    const real3 fij = ljForceDivR(r2, sigma, epsilon) * rij;
    if (force) {
      totalForce += fij;
    }
    if (energy) {
      totalEnergy += ljShiftedEnergyHalf(r2, sigma, epsilon);
    }
    if (virial) {
      totalVirial += dot(fij, rij);
    }
    if (stressDiag) {
      totalStressDiag += makeDiagStress(rij, fij);
    }
    if (stressOff) {
      totalStressOff += makeOffStress(rij, fij);
    }
  }

  if (force) {
    force[globalIndex] += make_real4(totalForce, real(0.0));
  }
  if (energy) {
    energy[globalIndex] += totalEnergy;
  }
  if (virial) {
    virial[globalIndex] += totalVirial;
  }
  if (stressDiag) {
    stressDiag[globalIndex] = totalStressDiag;
  }
  if (stressOff) {
    stressOff[globalIndex] = totalStressOff;
  }
}

__global__ void computeFENEWithStress(const uammd::real4* pos,
                                      const int2* bonds,
                                      int numberBonds,
                                      const int* id2index,
                                      uammd::Box box,
                                      uammd::real4* force,
                                      uammd::real* energy,
                                      uammd::real* virial,
                                      uammd::real4* stressDiag,
                                      uammd::real4* stressOff,
                                      uammd::real feneK,
                                      uammd::real feneR0) {
  using namespace uammd;

  const int bondIndex = blockIdx.x * blockDim.x + threadIdx.x;
  if (bondIndex >= numberBonds) {
    return;
  }

  const int2 bond = bonds[bondIndex];
  const int indexI = id2index[bond.x];
  const int indexJ = id2index[bond.y];
  const real3 ri = make_real3(pos[indexI]);
  const real3 rj = make_real3(pos[indexJ]);
  const real3 rij = box.apply_pbc(rj - ri);
  const real r2 = dot(rij, rij);
  if (r2 <= real(0.0)) {
    return;
  }

  // UAMMD's bonded convention computes the force on the first endpoint using
  // the opposite bond vector, so with rij = rj - ri we need an extra minus sign
  // to recover the same endpoint force as BondedType::FENE.
  const real3 fij = -feneForceDivR(r2, feneK, feneR0) * rij;
  const real eHalf = energy ? feneEnergyHalf(r2, feneK, feneR0) : real(0.0);
  // BondedType::FENE stores the virial with the opposite bond-vector convention,
  // which makes the per-particle bonded virial negative for a stretched bond.
  const real vPair = virial ? -dot(fij, rij) : real(0.0);
  const real4 diagPair =
      stressDiag ? -makeDiagStress(rij, fij) : make_real4(real(0.0));
  const real4 offPair =
      stressOff ? -makeOffStress(rij, fij) : make_real4(real(0.0));

  if (force) {
    atomicAdd(&force[indexI].x, fij.x);
    atomicAdd(&force[indexI].y, fij.y);
    atomicAdd(&force[indexI].z, fij.z);
    atomicAdd(&force[indexJ].x, -fij.x);
    atomicAdd(&force[indexJ].y, -fij.y);
    atomicAdd(&force[indexJ].z, -fij.z);
  }
  if (energy) {
    atomicAdd(&energy[indexI], eHalf);
    atomicAdd(&energy[indexJ], eHalf);
  }
  if (virial) {
    atomicAdd(&virial[indexI], vPair);
    atomicAdd(&virial[indexJ], vPair);
  }
  if (stressDiag) {
    atomicAdd(&stressDiag[indexI].x, diagPair.x);
    atomicAdd(&stressDiag[indexI].y, diagPair.y);
    atomicAdd(&stressDiag[indexI].z, diagPair.z);
    atomicAdd(&stressDiag[indexJ].x, diagPair.x);
    atomicAdd(&stressDiag[indexJ].y, diagPair.y);
    atomicAdd(&stressDiag[indexJ].z, diagPair.z);
  }
  if (stressOff) {
    atomicAdd(&stressOff[indexI].x, offPair.x);
    atomicAdd(&stressOff[indexI].y, offPair.y);
    atomicAdd(&stressOff[indexI].z, offPair.z);
    atomicAdd(&stressOff[indexJ].x, offPair.x);
    atomicAdd(&stressOff[indexJ].y, offPair.y);
    atomicAdd(&stressOff[indexJ].z, offPair.z);
  }
}

} // namespace stress_detail

class StressAwareWCAInteractor : public uammd::Interactor {
 public:
  StressAwareWCAInteractor(std::shared_ptr<uammd::ParticleData> particleData,
                           const uammd::Box& box,
                           double epsilon,
                           double sigma,
                           double skin)
      : uammd::Interactor(particleData, "KG/WCAStress"),
        box_(box),
        epsilon_(static_cast<uammd::real>(epsilon)),
        sigma_(static_cast<uammd::real>(sigma)),
        cutOff_(static_cast<uammd::real>(std::pow(2.0, 1.0 / 6.0) * sigma)),
        neighbourList_(std::make_shared<uammd::VerletList>(particleData)),
        stressDiag_(particleData->getNumParticles(), uammd::make_real4(0.0)),
        stressOff_(particleData->getNumParticles(), uammd::make_real4(0.0)) {
    if (neighbourList_ && skin > 0.0) {
      const uammd::real multiplier =
          static_cast<uammd::real>((cutOff_ + skin) / cutOff_);
      neighbourList_->setCutOffMultiplier(multiplier);
    }
  }

  void updateBox(uammd::Box box) override { box_ = box; }

  void sum(Computables comp, cudaStream_t st = 0) override {
    using namespace uammd;

    auto force = comp.force
                     ? pd->getForce(access::location::gpu, access::mode::readwrite)
                           .raw()
                     : nullptr;
    auto energy = comp.energy
                      ? pd->getEnergy(access::location::gpu,
                                      access::mode::readwrite)
                            .raw()
                      : nullptr;
    auto virial = comp.virial
                      ? pd->getVirial(access::location::gpu,
                                      access::mode::readwrite)
                            .raw()
                      : nullptr;

    real4* stressDiag = nullptr;
    real4* stressOff = nullptr;
    if (comp.force || comp.stress) {
      thrust::fill(thrust::cuda::par.on(st), stressDiag_.begin(), stressDiag_.end(),
                   make_real4(real(0.0)));
      thrust::fill(thrust::cuda::par.on(st), stressOff_.begin(), stressOff_.end(),
                   make_real4(real(0.0)));
      stressDiag = thrust::raw_pointer_cast(stressDiag_.data());
      stressOff = thrust::raw_pointer_cast(stressOff_.data());
    }

    neighbourList_->update(box_, cutOff_, st);
    auto neighbours = neighbourList_->getNeighbourContainer();
    const int numberParticles = pd->getNumParticles();
    const int threads = 128;
    const int blocks = (numberParticles + threads - 1) / threads;
    stress_detail::computeWCAWithStress<<<blocks, threads, 0, st>>>(
        neighbours, numberParticles, box_, force, energy, virial, stressDiag,
        stressOff, sigma_, epsilon_, cutOff_ * cutOff_);
    CudaCheckError();
  }

  const thrust::device_vector<uammd::real4>& getStressDiag() const {
    return stressDiag_;
  }

  const thrust::device_vector<uammd::real4>& getStressOff() const {
    return stressOff_;
  }

 private:
  uammd::Box box_;
  uammd::real epsilon_ = uammd::real(0.0);
  uammd::real sigma_ = uammd::real(0.0);
  uammd::real cutOff_ = uammd::real(0.0);
  std::shared_ptr<uammd::VerletList> neighbourList_;
  thrust::device_vector<uammd::real4> stressDiag_;
  thrust::device_vector<uammd::real4> stressOff_;
};

class StressAwareFENEInteractor : public uammd::Interactor {
 public:
  StressAwareFENEInteractor(std::shared_ptr<uammd::ParticleData> particleData,
                            const uammd::Box& box,
                            const std::vector<std::pair<int, int>>& bonds,
                            double feneK,
                            double feneR0)
      : uammd::Interactor(particleData, "KG/FENEStress"),
        box_(box),
        feneK_(static_cast<uammd::real>(feneK)),
        feneR0_(static_cast<uammd::real>(feneR0)),
        stressDiag_(particleData->getNumParticles(), uammd::make_real4(0.0)),
        stressOff_(particleData->getNumParticles(), uammd::make_real4(0.0)) {
    std::vector<int2> bondPairs;
    bondPairs.reserve(bonds.size());
    for (const auto& bond : bonds) {
      bondPairs.push_back(make_int2(bond.first - 1, bond.second - 1));
    }
    bonds_ = std::move(bondPairs);
  }

  void updateBox(uammd::Box box) override { box_ = box; }

  void sum(Computables comp, cudaStream_t st = 0) override {
    using namespace uammd;

    auto force = comp.force
                     ? pd->getForce(access::location::gpu, access::mode::readwrite)
                           .raw()
                     : nullptr;
    auto energy = comp.energy
                      ? pd->getEnergy(access::location::gpu,
                                      access::mode::readwrite)
                            .raw()
                      : nullptr;
    auto virial = comp.virial
                      ? pd->getVirial(access::location::gpu,
                                      access::mode::readwrite)
                            .raw()
                      : nullptr;

    real4* stressDiag = nullptr;
    real4* stressOff = nullptr;
    if (comp.force || comp.stress) {
      thrust::fill(thrust::cuda::par.on(st), stressDiag_.begin(), stressDiag_.end(),
                   make_real4(real(0.0)));
      thrust::fill(thrust::cuda::par.on(st), stressOff_.begin(), stressOff_.end(),
                   make_real4(real(0.0)));
      stressDiag = thrust::raw_pointer_cast(stressDiag_.data());
      stressOff = thrust::raw_pointer_cast(stressOff_.data());
    }

    const int numberBonds = static_cast<int>(bonds_.size());
    if (numberBonds == 0) {
      return;
    }

    auto pos = pd->getPos(access::location::gpu, access::mode::read);
    const int* id2index = pd->getIdOrderedIndices(access::location::gpu);
    const int threads = 128;
    const int blocks = (numberBonds + threads - 1) / threads;
    stress_detail::computeFENEWithStress<<<blocks, threads, 0, st>>>(
        pos.raw(), thrust::raw_pointer_cast(bonds_.data()), numberBonds, id2index,
        box_, force, energy, virial, stressDiag, stressOff, feneK_, feneR0_);
    CudaCheckError();
  }

  const thrust::device_vector<uammd::real4>& getStressDiag() const {
    return stressDiag_;
  }

  const thrust::device_vector<uammd::real4>& getStressOff() const {
    return stressOff_;
  }

 private:
  uammd::Box box_;
  uammd::real feneK_ = uammd::real(0.0);
  uammd::real feneR0_ = uammd::real(0.0);
  thrust::device_vector<int2> bonds_;
  thrust::device_vector<uammd::real4> stressDiag_;
  thrust::device_vector<uammd::real4> stressOff_;
};

inline std::shared_ptr<StressAwareWCAInteractor> createWCAStressInteractor_CellList(
    std::shared_ptr<uammd::ParticleData> particleData,
    const uammd::Box& box,
    int atomTypes,
    double epsilon,
    double sigma,
    double skin) {
  (void)atomTypes;
  return std::make_shared<StressAwareWCAInteractor>(particleData, box, epsilon,
                                                    sigma, skin);
}

inline std::shared_ptr<StressAwareFENEInteractor> createFENEStressInteractor(
    std::shared_ptr<uammd::ParticleData> particleData,
    const uammd::Box& box,
    const std::vector<std::pair<int, int>>& bonds,
    double feneK,
    double feneR0) {
  return std::make_shared<StressAwareFENEInteractor>(particleData, box, bonds,
                                                     feneK, feneR0);
}

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
