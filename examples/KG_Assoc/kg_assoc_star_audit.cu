#include "kg_assoc_star_topology.cuh"

#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

struct Arguments {
  std::string input;
  int arms = 0;
  int beadsPerArm = 0;
  bool selfTest = false;
};

std::string nextArgument(int& index, int argc, char** argv) {
  if (++index >= argc) {
    throw std::runtime_error("missing option value");
  }
  return argv[index];
}

void printHelp() {
  std::cout << "kg_assoc_star_audit --input FILE --arms NA --narm NARM [--self-test]\n";
}

Arguments parseArguments(int argc, char** argv) {
  Arguments arguments;
  for (int index = 1; index < argc; ++index) {
    const std::string option = argv[index];
    if (option == "--input") {
      arguments.input = nextArgument(index, argc, argv);
    } else if (option == "--arms") {
      arguments.arms = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--narm") {
      arguments.beadsPerArm = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--self-test") {
      arguments.selfTest = true;
    } else if (option == "--help") {
      printHelp();
      std::exit(0);
    } else {
      throw std::runtime_error("unknown argument: " + option);
    }
  }
  if (!arguments.selfTest && arguments.input.empty()) {
    throw std::runtime_error("--input is required");
  }
  if (!arguments.selfTest && (arguments.arms <= 0 || arguments.beadsPerArm <= 0)) {
    throw std::runtime_error("--arms and --narm must both be positive");
  }
  return arguments;
}

kg::LammpsData makeSelfTestData() {
  kg::LammpsData data;
  data.natoms = 11;
  data.nbonds = 9;
  data.xlo = 0.0;
  data.xhi = 10.0;
  data.ylo = 0.0;
  data.yhi = 10.0;
  data.zlo = 0.0;
  data.zhi = 10.0;
  data.type = {1, 1, 1, 2, 1, 1, 2, 1, 1, 2, 3};
  data.mol = {10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 99};
  data.bonds = {{1, 2}, {2, 3}, {3, 4}, {1, 5}, {5, 6},
                {6, 7}, {1, 8}, {8, 9}, {9, 10}};
  return data;
}

void expectReject(const std::string& name,
                  kg::LammpsData data,
                  const kg_assoc::StarTopologyExpectations& expectations) {
  try {
    (void)kg_assoc::auditStarTopology(data, expectations);
  } catch (const std::runtime_error&) {
    return;
  }
  throw std::runtime_error("self-test accepted malformed topology: " + name);
}

void runSelfTest() {
  const kg_assoc::StarTopologyExpectations expectations{3, 3};
  const kg::LammpsData valid = makeSelfTestData();
  (void)kg_assoc::auditStarTopology(valid, expectations);

  kg::LammpsData wrongTerminalCount = valid;
  wrongTerminalCount.type[3] = 1;
  expectReject("wrong terminal sticker count", wrongTerminalCount, expectations);

  kg::LammpsData wrongArmLength = valid;
  wrongArmLength.bonds = {{1, 2}, {2, 3}, {1, 4}, {4, 5}, {5, 6},
                          {1, 7}, {7, 8}, {8, 9}, {9, 10}};
  wrongArmLength.type = {1, 1, 2, 1, 1, 2, 1, 1, 1, 2, 3};
  expectReject("branch of wrong length", wrongArmLength, expectations);

  kg::LammpsData interStar = valid;
  interStar.mol[9] = 11;
  expectReject("permanent inter-star bond", interStar, expectations);

  kg::LammpsData solventBond = valid;
  solventBond.bonds[0] = {1, 11};
  expectReject("bond involving solvent", solventBond, expectations);

  kg::LammpsData invalidLammpsId = valid;
  invalidLammpsId.bonds[0] = {0, 2};
  expectReject("invalid 1-based LAMMPS bond ID", invalidLammpsId, expectations);

  kg::LammpsData nonTerminalSticker = valid;
  nonTerminalSticker.type[1] = 2;
  expectReject("non-terminal type-2 bead", nonTerminalSticker, expectations);

  kg::LammpsData cycle = valid;
  cycle.bonds.push_back({2, 5});
  ++cycle.nbonds;
  expectReject("cycle or extra permanent bond", cycle, expectations);

  std::cout << "STAR_TOPOLOGY_AUDIT SELF_TEST PASS malformed graph rejections\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Arguments arguments = parseArguments(argc, argv);
    if (arguments.selfTest) {
      runSelfTest();
      return 0;
    }
    const kg::LammpsData data = kg::readLammpsDataFile(arguments.input);
    const kg_assoc::StarTopologyExpectations expectations{
        arguments.arms, arguments.beadsPerArm};
    const kg_assoc::StarTopologyReport report =
        kg_assoc::auditStarTopology(data, expectations);
    std::cout << kg_assoc::formatStarTopologyReport(report);
    std::cout << "STAR_TOPOLOGY_AUDIT PASS\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
}
