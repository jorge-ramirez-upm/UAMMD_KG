#ifndef EXAMPLES_KG_ASSOC_INTERACTORS_CUH
#define EXAMPLES_KG_ASSOC_INTERACTORS_CUH

#include <uammd.cuh>
#include <thrust/device_vector.h>
#include <stdexcept>

namespace kg_assoc {
__global__ void associatingFeneKernel(const uammd::real4* pos, const int* id2index,
                                      const int* partner, int n, uammd::Box box,
                                      uammd::real4* force, uammd::real* energy,
                                      uammd::real k, uammd::real r0, uammd::real shift) {
  int id=blockIdx.x*blockDim.x+threadIdx.x; if(id>=n || partner[id]<=id) return;
  int i=id2index[id], j=id2index[partner[id]];
  uammd::real3 rij=box.apply_pbc(uammd::make_real3(pos[j])-uammd::make_real3(pos[i]));
  uammd::real r2=dot(rij,rij), arg=uammd::real(1)-r2/(r0*r0);
  if(arg<=uammd::real(0)) return; // host diagnostic rejects this condition at kinetic/output boundaries.
  uammd::real3 fij=(k/arg)*rij; // force on i: identical to PairAssociating::compute.
  atomicAdd(&force[i].x,fij.x); atomicAdd(&force[i].y,fij.y); atomicAdd(&force[i].z,fij.z);
  atomicAdd(&force[j].x,-fij.x); atomicAdd(&force[j].y,-fij.y); atomicAdd(&force[j].z,-fij.z);
  if(energy) { uammd::real e=-uammd::real(.5)*k*r0*r0*log(uammd::real(1)-r2/(r0*r0))-shift; atomicAdd(&energy[i],e/uammd::real(2)); atomicAdd(&energy[j],e/uammd::real(2)); }
}
class AssociatingFENEInteractor : public uammd::Interactor {
 public:
  AssociatingFENEInteractor(std::shared_ptr<uammd::ParticleData> pd, uammd::Box box,
                            thrust::device_vector<int>& partner, double k, double r0, double ee, double rstar)
      : Interactor(pd,"KG_Assoc/FENE"),box_(box),partner_(&partner),k_(k),r0_(r0),shift_(-.5*k*r0*r0*std::log1p(-rstar*rstar/(r0*r0))-ee) {}
  void updateBox(uammd::Box box) override { box_=box; }
  void sum(Computables c,cudaStream_t st=0) override {
    if(!c.force && !c.energy) return;
    auto pos=pd->getPos(uammd::access::gpu,uammd::access::read); auto f=c.force?pd->getForce(uammd::access::gpu,uammd::access::readwrite).raw():nullptr; auto e=c.energy?pd->getEnergy(uammd::access::gpu,uammd::access::readwrite).raw():nullptr;
    int n=pd->getNumParticles(), threads=128;
    associatingFeneKernel<<<(n+threads-1)/threads,threads,0,st>>>(pos.raw(),pd->getIdOrderedIndices(uammd::access::gpu),thrust::raw_pointer_cast(partner_->data()),n,box_,f,e,k_,r0_,shift_); CudaCheckError();
  }
 private: uammd::Box box_; thrust::device_vector<int>* partner_; uammd::real k_,r0_,shift_;
};
} // namespace kg_assoc
#endif
