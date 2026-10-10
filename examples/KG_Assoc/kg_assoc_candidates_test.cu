#include "kg_assoc_candidate_oracle.cuh"

#include <iostream>
#include <random>

namespace {

void require(bool condition, const char* message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

void check(const std::vector<kg_assoc::StickerCoordinate>& coordinates,
           const kg_assoc::BoxLengths& box) {
  kg_assoc_test::compare(kg_assoc::findStickerCandidates(coordinates, box, 1.25),
                        kg_assoc_test::oracle(coordinates, box, 1.25));
}

void synthetic() {
  std::mt19937 random(7301);
  for (const auto& box : std::vector<kg_assoc::BoxLengths>{
           {8, 8, 8}, {1, 2, 4}, {2, 2, 2}, {4, 2, 1}, {16, 8, 4}}) {
    std::vector<kg_assoc::StickerCoordinate> coordinates;
    for (int i = 0; i < 40; ++i) {
      coordinates.push_back({i, uammd::make_real3(
          (int(random() % 65) - 32) / 16.0,
          (int(random() % 65) - 32) / 16.0,
          (int(random() % 65) - 32) / 16.0)});
    }
    const auto reference = kg_assoc::findStickerCandidates(coordinates, box, 1.25);
    check(coordinates, box);
    for (int trial = 0; trial < 30; ++trial) {
      auto translated = coordinates;
      for (auto& sticker : translated) {
        sticker.position.x += (int(random() % 33) - 16) * box.x;
        sticker.position.y += (int(random() % 33) - 16) * box.y;
        sticker.position.z += (int(random() % 33) - 16) * box.z;
      }
      check(translated, box);
      kg_assoc_test::compare(kg_assoc::findStickerCandidates(translated, box, 1.25), reference);
      std::reverse(translated.begin(), translated.end());
      check(translated, box);
    }
  }
  const kg_assoc::BoxLengths box{8, 8, 8};
  const std::vector<kg_assoc::StickerCoordinate> boundaries{
      {0, uammd::make_real3(3.75, 3.75, 3.75)},
      {1, uammd::make_real3(-3.75, 3.75, 3.75)},
      {2, uammd::make_real3(-3.75, -3.75, 3.75)},
      {3, uammd::make_real3(-3.75, -3.75, -3.75)},
      {4, uammd::make_real3(4.25, 4.25, 4.25)},
      {5, uammd::make_real3(-4.25, -4.25, -4.25)}};
  check(boundaries, box);
  require(kg_assoc::findStickerCandidates(boundaries, box, 1.25).size() == 15,
          "face/edge/corner regression");
  const std::vector<kg_assoc::StickerCoordinate> cutoff{
      {0, uammd::make_real3(0, 0, 0)},
      {1, uammd::make_real3(1.25, 0, 0)},
      {2, uammd::make_real3(1.249, 0, 0)},
      {3, uammd::make_real3(1.251, 0, 0)}};
  check(cutoff, box);
  const auto cutoffPairs = kg_assoc_test::pairs(kg_assoc::findStickerCandidates(cutoff, box, 1.25));
  require(!cutoffPairs.count({0, 1}) && cutoffPairs.count({0, 2}) && !cutoffPairs.count({0, 3}),
          "strict cutoff regression");

  // The actual kinetics sorts by pair-keyed hash and ID tie-breaks, not cell traversal.
  kg_assoc::StickerState first(6, {0, 1, 2, 3, 4, 5}, false);
  kg_assoc::StickerState second(6, {0, 1, 2, 3, 4, 5}, false);
  first.make(0, 1);
  second.make(0, 1);
  kg_assoc::Kinetics kinetics({20, 4, 1, .01, 100, 7301}, 30, 1.5, 8);
  const auto edges = kg_assoc::findStickerCandidates(boundaries, box, 1.25);
  auto shuffled = kg_assoc_test::oracle(boundaries, box, 1.25);
  std::reverse(shuffled.begin(), shuffled.end());
  for (int step = 100; step <= 20000; step += 100) {
    std::vector<kg_assoc::Event> a, b;
    kinetics.update(step, first, edges, a);
    kinetics.update(step, second, shuffled, b);
    require(a.size() == b.size(), "kinetic ordering event count");
    for (std::size_t i = 0; i < a.size(); ++i) {
      require(a[i].type == b[i].type && a[i].first == b[i].first && a[i].second == b[i].second,
              "kinetic ordering event identity");
    }
    for (int i = 0; i < 6; ++i) {
      require(first.partner(i) == second.partner(i), "kinetic ordering partner state");
    }
  }
  // For primary-cell inputs, fmod leaves the old bin indices unchanged.
  for (int i = -63; i < 64; ++i) {
    const double x = i / 16.0;
    require(kg_assoc::cellIndex(x, 8, 6) == int(std::floor((x + 4) / (8.0 / 6))),
            "primary-cell bin equivalence");
  }
  std::cout << "CANDIDATE SELF_TEST PASS translations, degenerate grids, cutoff, active partners, kinetics\n";
}

void snapshot(const std::string& path, int expected) {
  const auto data = kg::readLammpsDataFile(path);
  const kg_assoc::BoxLengths box{data.xhi - data.xlo, data.yhi - data.ylo, data.zhi - data.zlo};
  std::vector<kg_assoc::StickerCoordinate> coordinates;
  for (int i = 0; i < data.natoms; ++i) {
    if (data.type[i] == 2) {
      coordinates.push_back({i, uammd::make_real3(
          data.x[i] - .5 * (data.xlo + data.xhi),
          data.y[i] - .5 * (data.ylo + data.yhi),
          data.z[i] - .5 * (data.zlo + data.zhi))});
    }
  }
  const auto found = kg_assoc::findStickerCandidates(coordinates, box, 1.25);
  kg_assoc_test::compare(found, kg_assoc_test::oracle(coordinates, box, 1.25));
  require(int(found.size()) == expected, "real snapshot reference count");
  std::cout << "SNAPSHOT PASS " << path << " candidates=" << found.size() << '\n';
  const std::string suffix = ".restart.lammpsdat";
  require(path.size() >= suffix.size() &&
              path.substr(path.size() - suffix.size()) == suffix,
          "snapshot must have .restart.lammpsdat suffix");
  std::ifstream sidecar(path.substr(0, path.size() - suffix.size()) + ".assoc_restart");
  require(bool(sidecar), "missing chemical snapshot sidecar");
  const auto eligible = kg_assoc_test::pairs(found);
  const auto reference = kg_assoc_test::pairs(kg_assoc_test::oracle(coordinates, box, 1.25));
  std::string line;
  int bonds = -1;
  while (std::getline(sidecar, line)) {
    if (line.find("active_bonds ") == 0) {
      bonds = std::stoi(line.substr(13));
      break;
    }
  }
  require(bonds >= 0, "missing active bond count");
  int activeCandidates = 0;
  for (int i = 0; i < bonds; ++i) {
    int first, second;
    require(bool(sidecar >> first >> second), "truncated active bond list");
    const std::pair<int, int> pair{first - 1, second - 1};
    require(eligible.count(pair) == reference.count(pair), "missing eligible active bond");
    activeCandidates += eligible.count(pair);
  }
  std::cout << "ACTIVE SNAPSHOT PASS eligible=" << activeCandidates << " total=" << bonds << '\n';
}

}  // namespace

int main(int argc, char** argv) {
  try {
    synthetic();
    if (argc == 3) {
      snapshot(argv[1], std::stoi(argv[2]));
    } else if (argc != 1) {
      throw std::runtime_error("usage: kg_assoc_candidates_test [SNAPSHOT EXPECTED_COUNT]");
    }
  } catch (const std::exception& error) {
    std::cerr << "CANDIDATE FAIL: " << error.what() << '\n';
    return 1;
  }
}
