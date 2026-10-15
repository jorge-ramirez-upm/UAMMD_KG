// Stage 0 only: allocation, deterministic CUDA work, readback, and shutdown.
#include "uammd.cuh"
// Compile the inspected APIs in both precisions; do not construct an integrator.
#include "Integrator/BrownianDynamics.cuh"
#include "Interactor/BondedForces.cuh"
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>

namespace {
void checkCuda(cudaError_t error, const char* operation) {
  if (error != cudaSuccess)
    throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(error));
}

__global__ void fillPositions(uammd::real4* positions, int count) {
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < count) {
    const uammd::real x = i;
    positions[i] = uammd::make_real4(x, 2*x, -x, 0);
  }
}
} // namespace

int main(int argc, char** argv) {
#ifdef DOUBLE_PRECISION
  static_assert(std::is_same<uammd::real, double>::value, "Expected double precision");
#else
  static_assert(std::is_same<uammd::real, float>::value, "Expected ordinary precision");
#endif
  try {
    int deviceCount = 0;
    checkCuda(cudaGetDeviceCount(&deviceCount), "cudaGetDeviceCount");
    if (deviceCount == 0) {
      std::cerr << "UNAVAILABLE: no CUDA device; runtime smoke test did not pass\n";
      return 2;
    }
    auto system = std::make_shared<uammd::System>(argc, argv);
    int device = 0;
    cudaDeviceProp properties{};
    checkCuda(cudaGetDevice(&device), "cudaGetDevice");
    checkCuda(cudaGetDeviceProperties(&properties, device), "cudaGetDeviceProperties");
    {
      constexpr int count = 8;
      auto particles = std::make_shared<uammd::ParticleData>(count, system);
      {
        auto positions = particles->getPos(uammd::access::gpu, uammd::access::write);
        fillPositions<<<1, 32>>>(positions.raw(), count);
        checkCuda(cudaGetLastError(), "fillPositions launch");
        checkCuda(cudaDeviceSynchronize(), "fillPositions synchronization");
      }
      {
        auto positions = particles->getPos(uammd::access::cpu, uammd::access::read);
        for (int i = 0; i < count; ++i) {
          const auto p = positions[i];
          if (p.x != i || p.y != 2*i || p.z != -i || p.w != 0)
            throw std::runtime_error("GPU position readback mismatch");
        }
      }
    } // Release particle data and access handles before System::finish().
    system->finish();
    std::cout << "PASS: UAMMD/CUDA initialization, 8 particles, kernel, synchronization, "
              << "readback, shutdown; real=" << 8*sizeof(uammd::real)
              << " bits; device=" << properties.name << " (sm_"
              << properties.major << properties.minor << ")\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
