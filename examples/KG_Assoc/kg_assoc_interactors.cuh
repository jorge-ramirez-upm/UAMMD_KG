#ifndef EXAMPLES_KG_ASSOC_INTERACTORS_CUH
#define EXAMPLES_KG_ASSOC_INTERACTORS_CUH

#include <uammd.cuh>
#include "../KG/kg_interactors.cuh"

#include <thrust/device_vector.h>
#include <thrust/fill.h>
#include <stdexcept>

namespace kg_assoc {
// These are shared by the CUDA kernel and the CPU self-test, preventing the
// interactor's constant-shift convention from drifting from its regression.
__host__ __device__ inline uammd::real associatingFeneEnergyFromR2(
    uammd::real r2, uammd::real k, uammd::real r0, uammd::real shift) {
  return -uammd::real(.5)*k*r0*r0*log(uammd::real(1)-r2/(r0*r0))-shift;
}
__host__ __device__ inline uammd::real associatingFeneForceDivR(
    uammd::real r2, uammd::real k, uammd::real r0) {
  return k/(uammd::real(1)-r2/(r0*r0));
}
inline double associatingFeneShift(double k, double r0, double ee, double rstar) {
  return -.5*k*r0*r0*std::log1p(-rstar*rstar/(r0*r0))+ee;
}
inline double checkedAssociatingFeneEnergy(double r, double k, double r0,
                                           double shift) {
  if (!(r >= 0.0 && r < r0))
    throw std::runtime_error("associating FENE requires 0 <= r < R0");
  return static_cast<double>(associatingFeneEnergyFromR2(
      static_cast<uammd::real>(r*r), static_cast<uammd::real>(k),
      static_cast<uammd::real>(r0), static_cast<uammd::real>(shift)));
}
__global__ void associatingFeneKernel(const uammd::real4* pos,
                                      const int* id2index,
                                      const int* partner,
                                      int n,
                                      uammd::Box box,
                                      uammd::real4* force,
                                      uammd::real* energy,
                                      uammd::real4* stressDiag,
                                      uammd::real4* stressOff,
                                      uammd::real k,
                                      uammd::real r0,
                                      uammd::real shift,
                                      int* invalidFene) {
  const int id = blockIdx.x * blockDim.x + threadIdx.x;
  if (id >= n || partner[id] <= id) {
    return;
  }

  const int i = id2index[id];
  const int j = id2index[partner[id]];
  const uammd::real3 rij =
      box.apply_pbc(uammd::make_real3(pos[j]) - uammd::make_real3(pos[i]));
  const uammd::real r2 = dot(rij, rij);
  const uammd::real arg = uammd::real(1) - r2 / (r0 * r0);
  if (arg <= uammd::real(0)) {
    if (atomicCAS(&invalidFene[0], 0, 1) == 0) {
      invalidFene[1] = id;
      invalidFene[2] = partner[id];
    }
    return;
  }

  // This is the force on i, identical to PairAssociating::compute.
  const uammd::real3 fij = associatingFeneForceDivR(r2, k, r0) * rij;
  if (force) {
    atomicAdd(&force[i].x, fij.x);
    atomicAdd(&force[i].y, fij.y);
    atomicAdd(&force[i].z, fij.z);
    atomicAdd(&force[j].x, -fij.x);
    atomicAdd(&force[j].y, -fij.y);
    atomicAdd(&force[j].z, -fij.z);
  }
  if (energy) {
    const uammd::real pairEnergy = associatingFeneEnergyFromR2(r2, k, r0, shift);
    atomicAdd(&energy[i], pairEnergy / uammd::real(2));
    atomicAdd(&energy[j], pairEnergy / uammd::real(2));
  }
  // Match StressAwareFENEInteractor exactly: cache -rij tensor fij on both
  // endpoints. The KG reducer applies +1/2 because this pair cache is doubled.
  const uammd::real4 diagPair = -kg::stress_detail::makeDiagStress(rij, fij);
  const uammd::real4 offPair = -kg::stress_detail::makeOffStress(rij, fij);
  if (stressDiag) {
    atomicAdd(&stressDiag[i].x, diagPair.x);
    atomicAdd(&stressDiag[i].y, diagPair.y);
    atomicAdd(&stressDiag[i].z, diagPair.z);
    atomicAdd(&stressDiag[j].x, diagPair.x);
    atomicAdd(&stressDiag[j].y, diagPair.y);
    atomicAdd(&stressDiag[j].z, diagPair.z);
  }
  if (stressOff) {
    atomicAdd(&stressOff[i].x, offPair.x);
    atomicAdd(&stressOff[i].y, offPair.y);
    atomicAdd(&stressOff[i].z, offPair.z);
    atomicAdd(&stressOff[j].x, offPair.x);
    atomicAdd(&stressOff[j].y, offPair.y);
    atomicAdd(&stressOff[j].z, offPair.z);
  }
}
class AssociatingFENEInteractor : public uammd::Interactor {
 public:
  AssociatingFENEInteractor(std::shared_ptr<uammd::ParticleData> pd, uammd::Box box,
                            thrust::device_vector<int>& partner, double k, double r0, double ee, double rstar)
      : Interactor(pd, "KG_Assoc/FENE"),
        box_(box),
        partner_(&partner),
        k_(k),
        r0_(r0),
        shift_(associatingFeneShift(k, r0, ee, rstar)),
        invalidFene_(3, 0),
        stressDiag_(pd->getNumParticles(), uammd::make_real4(0.0)),
        stressOff_(pd->getNumParticles(), uammd::make_real4(0.0)) {}
  void updateBox(uammd::Box box) override { box_=box; }
  void sum(Computables c,cudaStream_t st=0) override {
    if (!c.force && !c.energy && !c.stress) {
      return;
    }

    auto pos = pd->getPos(uammd::access::gpu, uammd::access::read);
    auto force = c.force
                     ? pd->getForce(uammd::access::gpu,
                                    uammd::access::readwrite).raw()
                     : nullptr;
    auto energy = c.energy
                      ? pd->getEnergy(uammd::access::gpu,
                                      uammd::access::readwrite).raw()
                      : nullptr;
    uammd::real4* stressDiag = nullptr;
    uammd::real4* stressOff = nullptr;
    if (c.force || c.stress) {
      thrust::fill(thrust::cuda::par.on(st), stressDiag_.begin(), stressDiag_.end(),
                   uammd::make_real4(0.0));
      thrust::fill(thrust::cuda::par.on(st), stressOff_.begin(), stressOff_.end(),
                   uammd::make_real4(0.0));
      stressDiag = thrust::raw_pointer_cast(stressDiag_.data());
      stressOff = thrust::raw_pointer_cast(stressOff_.data());
    }
    const int numberParticles = pd->getNumParticles();
    const int threads = 128;
    const int blocks = (numberParticles + threads - 1) / threads;
    associatingFeneKernel<<<blocks, threads, 0, st>>>(
        pos.raw(), pd->getIdOrderedIndices(uammd::access::gpu),
        thrust::raw_pointer_cast(partner_->data()), numberParticles, box_, force,
        energy, stressDiag, stressOff, k_, r0_, shift_,
        thrust::raw_pointer_cast(invalidFene_.data()));
    CudaCheckError();
  }
  bool hasInvalidFene() const { return invalidFene_[0] != 0; }
  std::pair<int, int> invalidFenePair() const {
    return {invalidFene_[1], invalidFene_[2]};
  }
  const thrust::device_vector<uammd::real4>& getStressDiag() const {
    return stressDiag_;
  }
  const thrust::device_vector<uammd::real4>& getStressOff() const {
    return stressOff_;
  }

 private:
  uammd::Box box_;
  thrust::device_vector<int>* partner_;
  uammd::real k_;
  uammd::real r0_;
  uammd::real shift_;
  thrust::device_vector<int> invalidFene_;
  thrust::device_vector<uammd::real4> stressDiag_;
  thrust::device_vector<uammd::real4> stressOff_;
};
} // namespace kg_assoc
#endif
