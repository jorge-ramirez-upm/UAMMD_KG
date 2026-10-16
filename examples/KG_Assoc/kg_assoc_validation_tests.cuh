#ifndef EXAMPLES_KG_ASSOC_VALIDATION_TESTS_CUH
#define EXAMPLES_KG_ASSOC_VALIDATION_TESTS_CUH

#include "kg_assoc_candidate_oracle.cuh"
#include <cstdio>
#include <random>

namespace kg_assoc_test {

inline void cpuRequire(bool passed, const char* reason) {
  if (!passed) {
    throw std::runtime_error(reason);
  }
}

inline void cutoffContractTests() {
  using uammd::make_real3;
  using uammd::real;
  const kg_assoc::BoxLengths box{40, 40, 40};
  const std::vector<kg_assoc::StickerCoordinate> counterexample{
      {0, make_real3(-.1, 0, 0)}, {1, make_real3(1.15, 0, 0)}};
  compare(kg_assoc::findStickerCandidates(counterexample, box, 1.25),
          oracle(counterexample, box, 1.25));
  const auto first = counterexample[0].position;
  const auto second = counterexample[1].position;
  const auto realFirst = pairArithmetic(first, second, box, true);
  const auto doubleFirst = pairArithmetic(first, second, box, false);
  if (sizeof(real) == 4) {
    cpuRequire(realFirst.distance == 1.25 && doubleFirst.distance < 1.25,
               "historical subtraction counterexample not reproduced");
  }
  std::cout << "CUTOFF_COUNTEREXAMPLE real_bytes=" << sizeof(real)
            << " real_first=" << std::setprecision(17) << realFirst.distance
            << " double_first=" << doubleFirst.distance << '\n';

  const kg_assoc::BoxLengths imageBox{20.916666666666668, 40, 40};
  const std::vector<kg_assoc::StickerCoordinate> imagePair{
      {0, make_real3(0, 0, 0)}, {1, make_real3(64, 0, 0)}};
  const double manual = 64.0 - imageBox.x * std::nearbyint(64.0 / imageBox.x);
  const double remainder = std::remainder(64.0, imageBox.x);
  cpuRequire(manual == 1.25 && remainder < 1.25,
             "minimum-image arithmetic counterexample not reproduced");
  compare(kg_assoc::findStickerCandidates(imagePair, imageBox, 1.25),
          oracle(imagePair, imageBox, 1.25));
  cpuRequire(oracle(imagePair, imageBox, 1.25).empty(), "MIC strict cutoff enlarged");
  std::cout << "MIC_COUNTEREXAMPLE subtraction=" << manual
            << " remainder=" << remainder << '\n';

  // Below/at/above along each axis, signs, periodic faces and non-primary images.
  long long cases = 0;
  for (const real distance : {std::nextafter(real(1.25), real(0)), real(1.25),
                              std::nextafter(real(1.25), real(2))}) {
    for (int axis = 0; axis < 3; ++axis) {
      for (const int sign : {-1, 1}) {
        const auto a = make_real3(0, 0, 0);
        auto b = a;
        if (axis == 0) {
          b.x = sign * distance;
        } else if (axis == 1) {
          b.y = sign * distance;
        } else {
          b.z = sign * distance;
        }
        const std::vector<kg_assoc::StickerCoordinate> coordinates{{0, a}, {1, b}};
        const auto found = kg_assoc::findStickerCandidates(coordinates, box, 1.25);
        compare(found, oracle(coordinates, box, 1.25));
        cpuRequire(found.size() == std::size_t(distance < real(1.25)),
                   "strict cutoff boundary contract failed");
        ++cases;
      }
    }
  }
  for (const double shift : {-1000., -1., 0., 1., 1000.}) {
    for (const double sign : {-1., 1.}) {
      for (const auto& box : std::vector<kg_assoc::BoxLengths>{
               {40, 40, 40}, {37.1450195, 39.7, 34.3}, {2, 2, 2}, {1, 2, 4}}) {
        std::vector<kg_assoc::StickerCoordinate> coordinates{
            {0, make_real3(sign * (shift * box.x + .1), shift * box.y, 0)},
            {1, make_real3(sign * ((shift + 1) * box.x - 1.15), shift * box.y, 0)},
            {2, make_real3(-box.x / 2, box.y / 2, -box.z / 2)},
            {3, make_real3(box.x / 2, -box.y / 2, box.z / 2)}};
        compare(kg_assoc::findStickerCandidates(coordinates, box, 1.25),
                oracle(coordinates, box, 1.25));
        std::reverse(coordinates.begin(), coordinates.end());
        compare(kg_assoc::findStickerCandidates(coordinates, box, 1.25),
                oracle(coordinates, box, 1.25));
        cases += 2;
      }
    }
  }
  std::mt19937 random(20261016);
  std::uniform_real_distribution<double> sample(-2000., 2000.);
  for (int trial = 0; trial < 300; ++trial) {
    const kg_assoc::BoxLengths box{37.1450195, 39.7, 34.3};
    std::vector<kg_assoc::StickerCoordinate> coordinates;
    for (int id = 0; id < 48; ++id) {
      coordinates.push_back({id, make_real3(sample(random), sample(random), sample(random))});
    }
    compare(kg_assoc::findStickerCandidates(coordinates, box, 1.25),
            oracle(coordinates, box, 1.25));
    ++cases;
  }
  std::cout << "CUTOFF_CONTRACT PASS cases=" << cases
            << " strict_boundaries periodic_faces images nondyadic_coordinates\n";
}

inline void evidenceTests() {
  char pattern[] = "/tmp/kg_assoc_validation_XXXXXX";
  char* created = ::mkdtemp(pattern);
  cpuRequire(created != nullptr, "cannot create CPU evidence test directory");
  const std::string root(created);
  DiagnosticContext context;
  context.branch = "F04_N010_RP080_EE08_EA08:derived_cpu_fixture:r001";
  context.step = 8007100;
  context.sweep = 71;
  context.executable = "CPU_fixture";
  context.buildManifest = "CPU_fixture_manifest";
  context.buildJson = "{\"git_sha\":\"CPU_fixture_only\",\"executable_sha256\":\"fixture\"}";
  const kg_assoc::BoxLengths box{40, 40, 40};
  const std::vector<kg_assoc::StickerCoordinate> coordinates{
      {0, uammd::make_real3(-.1, 0, 0)}, {1, uammd::make_real3(1.15, 0, 0)},
      {2, uammd::make_real3(0, 10, 0)}, {3, uammd::make_real3(1, 10, 0)}};
  kg_assoc::StickerState state(4, {0, 1, 2, 3}, false);
  state.make(0, 1);
  const auto correct = oracle(coordinates, box, 1.25);
  auto corrupt = correct;
  corrupt.push_back({0, 1, 1.25});  // Injected extra active pair at the strict cutoff.
  corrupt.erase(corrupt.begin());  // Injected missing free pair.
  bool rejected = false;
  const std::string mismatch = root + "/mismatch.tsv";
  try {
    compareWithEvidence(corrupt, correct, coordinates, state, box, 1.25, &context, mismatch);
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  cpuRequire(rejected, "injected mismatch was allowed to continue");
  std::ifstream input(mismatch);
  const std::string text((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
  cpuRequire(text.find("difference missing 3 4 0 1") != std::string::npos &&
             text.find("difference extra 1 2 1 0") != std::string::npos &&
             text.find("absolute_step=8007100 chemistry_sweep=71") != std::string::npos &&
             text.find("CPU_fixture_only") != std::string::npos &&
             text.find("coordinate 1 ") != std::string::npos &&
             text.find("arithmetic 1 2 double_first") != std::string::npos,
             "mismatch evidence lacks required identities/arithmetic");
  const std::string unchanged = root + "/unchanged.tsv";
  compareWithEvidence(correct, correct, coordinates, state, box, 1.25, &context, unchanged);
  cpuRequire(!std::ifstream(unchanged), "passing comparison wrote mismatch evidence");
  cpuRequire(state.bonded(0, 1) && state.partner(2) == -1 && state.partner(3) == -1,
             "validation changed chemical partners");
  auto distanceMismatch = correct;
  distanceMismatch[0].r = std::nextafter(distanceMismatch[0].r, 2.0);
  const std::string distancePath = root + "/distance.tsv";
  rejected = false;
  try {
    compareWithEvidence(distanceMismatch, correct, coordinates, state, box, 1.25,
                        &context, distancePath);
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  cpuRequire(rejected && bool(std::ifstream(distancePath)),
             "distance-only mismatch was not preserved and rejected");
  ::unlink(distancePath.c_str());
  rejected = false;
  try {
    writeExclusive(mismatch, "overwrite");
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  cpuRequire(rejected, "evidence overwrite was permitted");

  std::vector<InitialParticle> particles(2);
  for (int id = 0; id < 2; ++id) {
    particles[id].expectedId = id;
    particles[id].actualId = id;
    particles[id].molecule = 1;
    particles[id].expectedType = 2;
    particles[id].actualType = 2;
    particles[id].expectedPartner = 1 - id;
    particles[id].actualPartner = 1 - id;
  }
  particles[1].actualPosition[0] = 40;  // Exact periodic image is equivalent.
  const auto valid = particles;
  const std::string initial = root + "/initial.tsv";
  cpuRequire(writeInitialReadback(initial, context, box, particles, true),
             "unchanged initial readback was rejected");
  for (int mutation = 0; mutation < 7; ++mutation) {
    particles = valid;
    if (mutation == 0) {
      particles[0].actualPosition[0] = 1e-7;
    } else if (mutation == 1) {
      particles[0].actualVelocity[0] = 1e-7;
    } else if (mutation == 2) {
      particles[0].actualId = 1;
    } else if (mutation == 3) {
      particles[0].actualType = 1;
    } else if (mutation == 4) {
      particles[0].actualPartner = -1;
    } else if (mutation == 5) {
      particles[0].actualPosition[0] = std::numeric_limits<double>::quiet_NaN();
    }
    const std::string path = root + "/bad" + std::to_string(mutation);
    cpuRequire(!writeInitialReadback(path, context, box, particles, mutation != 6),
               "corrupt initial readback was accepted");
    ::unlink(path.c_str());
  }
  ::unlink(mismatch.c_str());
  ::unlink(initial.c_str());
  ::rmdir(root.c_str());
  std::cout << "VALIDATION_EVIDENCE PASS missing extra active free provenance immutable "
               "readback_position_velocity_ids_types_partners_nonfinite_mapping\n";
}

}  // namespace kg_assoc_test
#endif
