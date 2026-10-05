#ifndef EXAMPLES_KG_ASSOC_CLI_CUH
#define EXAMPLES_KG_ASSOC_CLI_CUH

#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>

namespace kg_assoc {

struct Params {
  int steps = 10000;
  int every = 100;
  double dt = .005;
  double temperature = 1.;
  double ee = 4.;
  double ea = 1.;
  double nu0 = 10.;
  double rAssoc = 1.25;
  double k = 30.;
  double r0 = 1.5;
  double friction = .5;
  double box = 8.;
  double distance = 1.0;
  unsigned long long seed = 12345;
  std::string prefix = "kg_assoc_dimer";
  bool selfTest = false;
  bool staticMode = false;
  bool initialBound = false;
  bool rAssocExplicit = false;
  bool bondedRadialAudit = false;
  int auditBurnin = 10000;
  int auditSample = 100;
};

inline std::string nextArgument(int& index, int argc, char** argv) {
  if (++index >= argc) {
    throw std::runtime_error("missing option value");
  }
  return argv[index];
}

inline void printHelp() {
  std::cout
      << "kg_assoc_dimer [--static --distance R --initial-bound] "
      << "--steps N --dt DT --temperature T --Ee E --Ea E --nu0 X "
      << "--Nevery N --r-assoc R --K K --R0 R --box L --seed S "
      << "--output PREFIX [--bonded-radial-audit --audit-burnin N --audit-sample N] [--self-test]\n";
}

inline Params parseArgs(int argc, char** argv) {
  Params params;

  for (int index = 1; index < argc; ++index) {
    const std::string option = argv[index];
    if (option == "--steps" || option == "-n") {
      params.steps = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--dt") {
      params.dt = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--temperature" || option == "-T") {
      params.temperature = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--Ee") {
      params.ee = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--Ea") {
      params.ea = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--nu0") {
      params.nu0 = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--Nevery") {
      params.every = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--r-assoc") {
      params.rAssoc = std::stod(nextArgument(index, argc, argv));
      params.rAssocExplicit = true;
    } else if (option == "--K") {
      params.k = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--R0") {
      params.r0 = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--box") {
      params.box = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--distance") {
      params.distance = std::stod(nextArgument(index, argc, argv));
    } else if (option == "--seed") {
      params.seed = std::stoull(nextArgument(index, argc, argv));
    } else if (option == "--output" || option == "--prefix") {
      params.prefix = nextArgument(index, argc, argv);
    } else if (option == "--static") {
      params.staticMode = true;
    } else if (option == "--initial-bound") {
      params.initialBound = true;
    } else if (option == "--bonded-radial-audit") {
      params.bondedRadialAudit = true;
    } else if (option == "--audit-burnin") {
      params.auditBurnin = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--audit-sample") {
      params.auditSample = std::stoi(nextArgument(index, argc, argv));
    } else if (option == "--self-test") {
      params.selfTest = true;
    } else if (option == "--help") {
      printHelp();
      std::exit(0);
    } else {
      throw std::runtime_error("unknown argument: " + option);
    }
  }

  if (params.steps < 0 || params.every <= 0 || params.dt <= 0.0 ||
      params.temperature <= 0.0 || params.k <= 0.0 || params.r0 <= 0.0 ||
      params.rAssoc <= 0.0 || params.rAssoc >= params.r0 ||
      params.box <= 2.0 * params.r0 || params.distance < 0.0 ||
      params.auditBurnin < 0 || params.auditSample <= 0) {
    throw std::runtime_error("invalid physical parameters");
  }
  return params;
}

}  // namespace kg_assoc

#endif
