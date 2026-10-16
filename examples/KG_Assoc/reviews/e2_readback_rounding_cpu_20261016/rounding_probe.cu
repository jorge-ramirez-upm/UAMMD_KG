// Host-only replay of saved device evidence; no CUDA calls, allocations or kernels.
#include "kg_assoc_validation_evidence.cuh"

#include <iostream>

__attribute__((noinline)) std::array<double, 3> historical(const double* values) {
  return {{uammd::real(values[0]), uammd::real(values[1]), uammd::real(values[2])}};
}

void require(bool condition, const char* message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

int main(int argc, char** argv) {
  try {
    require(argc == 4, "expected parent fixture, saved readback and new evidence path");
    require(sizeof(uammd::real) == 4, "campaign probe requires float32");
    std::ifstream fixture(argv[1]);
    std::ifstream saved(argv[2]);
    require(bool(fixture) && bool(saved), "missing authenticated input");
    kg_assoc::BoxLengths box;
    fixture >> box.x >> box.y >> box.z;
    require(bool(fixture), "missing authenticated box");
    std::vector<kg_assoc_test::InitialParticle> records;
    std::array<int, 3> oldMismatch{};
    std::string line;
    while (std::getline(saved, line)) {
      if (line.compare(0, 9, "particle ") != 0) {
        continue;
      }
      std::istringstream row(line);
      std::string marker;
      kg_assoc_test::InitialParticle record;
      row >> marker >> record.expectedId >> record.actualId >> record.molecule
          >> record.expectedType >> record.actualType
          >> record.expectedPartner >> record.actualPartner;
      for (auto* values : {&record.expectedPosition, &record.actualPosition,
                           &record.expectedVelocity, &record.actualVelocity}) {
        for (double& value : *values) {
          row >> value;
        }
      }
      require(bool(row), "invalid saved particle row");
      int id;
      double serialized[3];
      double independent[3];
      fixture >> id >> serialized[0] >> serialized[1] >> serialized[2]
              >> independent[0] >> independent[1] >> independent[2];
      require(bool(fixture) && id == record.expectedId, "parent fixture ID differs");
      const auto old = historical(serialized);
      record.expectedVelocity = kg_assoc_test::representedVelocity(
          serialized[0], serialized[1], serialized[2]);
      for (int axis = 0; axis < 3; ++axis) {
        oldMismatch[axis] += old[axis] != independent[axis];
        require(record.expectedVelocity[axis] == independent[axis],
                "corrected expected velocity differs from independent Python float32");
        require(record.actualVelocity[axis] == independent[axis],
                "saved actual device velocity differs from parent float32");
      }
      records.push_back(record);
    }
    require(records.size() == 43563, "wrong particle count");
    std::string extra;
    require(!(fixture >> extra), "extra parent rows");
    require(oldMismatch[0] > 0 && oldMismatch[1] > 0 && oldMismatch[2] == 0,
            "optimized historical defect not reproduced");
    kg_assoc_test::DiagnosticContext context;
    context.branch = "CPU_replay_of_failed_Ea4_r001_not_a_GPU_retest";
    context.executable = argv[0];
    context.step = 8000000;
    require(kg_assoc_test::writeInitialReadback(argv[3], context, box, records, true),
            "exact validator rejected corrected host replay");
    std::cout << "HOST_REPLAY PASS particles=" << records.size()
              << " components=" << records.size() * 3
              << " historical_wrong_by_axis=" << oldMismatch[0] << ','
              << oldMismatch[1] << ',' << oldMismatch[2]
              << " corrected_wrong=0 saved_actual_wrong=0 GPU_calls=0\n";
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
