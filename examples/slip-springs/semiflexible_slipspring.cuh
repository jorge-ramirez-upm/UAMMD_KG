#pragma once
// Development-only E1 fixed bead/anchor springs. No hopping or renewal.
// Exactly one spring per occupied bead; inactive entries have w=0.
#include "semiflexible.cuh"

namespace semiflexible {
__global__ void fixed_slip_force(const real4* positions, real4* forces,
                                 const real4* anchors, int count,
                                 real springK, int* error) {
  const int i=blockIdx.x*blockDim.x+threadIdx.x;
  if(i>=count) return;
  const real4 anchor=anchors[i];
  if(anchor.w==real(0)) return;
  const real3 displacement=make_real3(positions[i])-make_real3(anchor);
  const real3 contribution=-springK*displacement;
  const real additionalEnergy=real(0.5)*springK*dot(displacement,displacement);
  real4 f=forces[i];
  const real3 total=make_real3(f)+contribution;
  const real energy=f.w+additionalEnergy;
  if(!finite(displacement)||!finite(total)||!isfinite(energy)) {
    fail(error,i,4);return;
  }
  forces[i]=make_real4(total,energy);
}
} // namespace semiflexible
