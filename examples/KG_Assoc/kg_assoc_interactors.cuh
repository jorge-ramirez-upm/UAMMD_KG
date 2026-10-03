#ifndef EXAMPLES_KG_ASSOC_INTERACTORS_CUH
#define EXAMPLES_KG_ASSOC_INTERACTORS_CUH

#include <uammd.cuh>
#include <thrust/device_vector.h>
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
__global__ void associatingFeneKernel(const uammd::real4* pos, const int* id2index,
                                      const int* partner, int n, uammd::Box box,
                                      uammd::real4* force, uammd::real* energy,
                                      uammd::real k, uammd::real r0, uammd::real shift,
                                      int* invalidFene) {
  int id=blockIdx.x*blockDim.x+threadIdx.x; if(id>=n || partner[id]<=id) return;
  int i=id2index[id], j=id2index[partner[id]];
  uammd::real3 rij=box.apply_pbc(uammd::make_real3(pos[j])-uammd::make_real3(pos[i]));
  uammd::real r2=dot(rij,rij), arg=uammd::real(1)-r2/(r0*r0);
  if(arg<=uammd::real(0)) { if(atomicCAS(&invalidFene[0],0,1)==0) { invalidFene[1]=id; invalidFene[2]=partner[id]; } return; }
  uammd::real3 fij=associatingFeneForceDivR(r2,k,r0)*rij; // force on i: identical to PairAssociating::compute.
  atomicAdd(&force[i].x,fij.x); atomicAdd(&force[i].y,fij.y); atomicAdd(&force[i].z,fij.z);
  atomicAdd(&force[j].x,-fij.x); atomicAdd(&force[j].y,-fij.y); atomicAdd(&force[j].z,-fij.z);
  if(energy) { uammd::real e=associatingFeneEnergyFromR2(r2,k,r0,shift); atomicAdd(&energy[i],e/uammd::real(2)); atomicAdd(&energy[j],e/uammd::real(2)); }
}
class AssociatingFENEInteractor : public uammd::Interactor {
 public:
  AssociatingFENEInteractor(std::shared_ptr<uammd::ParticleData> pd, uammd::Box box,
                            thrust::device_vector<int>& partner, double k, double r0, double ee, double rstar)
      : Interactor(pd,"KG_Assoc/FENE"),box_(box),partner_(&partner),k_(k),r0_(r0),shift_(associatingFeneShift(k,r0,ee,rstar)),invalidFene_(3,0) {}
  void updateBox(uammd::Box box) override { box_=box; }
  void sum(Computables c,cudaStream_t st=0) override {
    if(!c.force && !c.energy) return;
    auto pos=pd->getPos(uammd::access::gpu,uammd::access::read); auto f=c.force?pd->getForce(uammd::access::gpu,uammd::access::readwrite).raw():nullptr; auto e=c.energy?pd->getEnergy(uammd::access::gpu,uammd::access::readwrite).raw():nullptr;
    int n=pd->getNumParticles(), threads=128;
    associatingFeneKernel<<<(n+threads-1)/threads,threads,0,st>>>(pos.raw(),pd->getIdOrderedIndices(uammd::access::gpu),thrust::raw_pointer_cast(partner_->data()),n,box_,f,e,k_,r0_,shift_,thrust::raw_pointer_cast(invalidFene_.data())); CudaCheckError();
  }
  bool hasInvalidFene() const { return invalidFene_[0] != 0; }
  std::pair<int,int> invalidFenePair() const { return {invalidFene_[1],invalidFene_[2]}; }
 private: uammd::Box box_; thrust::device_vector<int>* partner_; uammd::real k_,r0_,shift_;
  thrust::device_vector<int> invalidFene_;
};
} // namespace kg_assoc
#endif
