// Host-only compiler probe: no CUDA calls, device allocations or kernels.
#include <array>
#include <cstdlib>
#include <iomanip>
#include <iostream>

__attribute__((noinline)) std::array<double, 3> direct(const double* values) {
  return {{float(values[0]), float(values[1]), float(values[2])}};
}

__attribute__((noinline)) std::array<double, 3> stored(const double* values) {
  volatile float rounded[3] = {float(values[0]), float(values[1]), float(values[2])};
  return {{rounded[0], rounded[1], rounded[2]}};
}

int main(int argc, char** argv) {
  if (argc != 4) {
    return 2;
  }
  double values[3];
  for (int axis = 0; axis < 3; ++axis) {
    values[axis] = std::strtod(argv[axis + 1], nullptr);
  }
  const auto first = direct(values);
  const auto second = stored(values);
  std::cout << std::setprecision(17);
  for (int axis = 0; axis < 3; ++axis) {
    std::cout << axis << ' ' << values[axis] << ' ' << first[axis] << ' '
              << second[axis] << '\n';
  }
}
