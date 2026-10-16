// Host-only diagnostic of the unchanged candidate/oracle arithmetic; no GPU initialization.
#include "kg_assoc_candidate_oracle.cuh"
#include <iomanip>
#include <iostream>

int main() {
  const kg_assoc::BoxLengths box{40.0, 40.0, 40.0};
  const std::vector<kg_assoc::StickerCoordinate> coordinates{
      {0, uammd::make_real3(-0.1, 0.0, 0.0)},
      {1, uammd::make_real3(1.15, 0.0, 0.0)}};
  const auto found = kg_assoc::findStickerCandidates(coordinates, box, 1.25);
  const auto expected = kg_assoc_test::oracle(coordinates, box, 1.25);
  const auto first = coordinates[0].position.x;
  const auto second = coordinates[1].position.x;
  std::cout << std::setprecision(17)
            << "sizeof(real)=" << sizeof(uammd::real)
            << " first=" << double(first) << " second=" << double(second)
            << " candidate_displacement=" << double(second - first)
            << " oracle_displacement=" << double(second) - double(first)
            << " found=" << found.size() << " expected=" << expected.size() << '\n';
  if (sizeof(uammd::real) != 4 || !found.empty() || expected.size() != 1) {
    return 1;
  }
  try {
    kg_assoc_test::compare(found, expected);
  } catch (const std::runtime_error& error) {
    std::cout << "UNCHANGED_CODE_COUNTEREXAMPLE_REPRODUCED: " << error.what() << '\n';
    return 0;
  }
  return 1;
}
