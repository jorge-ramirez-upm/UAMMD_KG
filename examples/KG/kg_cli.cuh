#ifndef EXAMPLES_KG_KG_CLI_CUH
#define EXAMPLES_KG_KG_CLI_CUH

// Command-line helpers for the Kremer-Grest example.
//
// This file centralizes:
//   - the simulation parameters exposed to users
//   - filename-derivation rules tied to `.lammpsdat` inputs
//   - help text and argument parsing

#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>

namespace kg {

// User-facing run configuration. The KG example always runs with both WCA and
// FENE enabled, so only physical parameters and output cadence remain exposed.
struct SimParams {
  std::string dataFile = "input.lammpsdat";

  int steps = 1000000;
  int dumpEvery = 10000;
  int thermoEvery = 1000;
  int restartEvery = 10000;

  double dt = 0.01;
  double temperature = 1.0;
  double friction = 0.5;

  double sigma = 1.0;
  double epsilon = 1.0;

  double feneK = 30.0;
  double feneR0 = 1.5;

  double skin = 0.3;

  bool initializeVelocities = false;
  bool removeCOMVelocity = false;
  bool gzipDump = false;
};

namespace detail {

// Consume the next token as the value for an option such as `--steps 1000`.
inline std::string getArg(int& i, int argc, char** argv) {
  if (i + 1 >= argc) {
    throw std::runtime_error(std::string("Missing value after ") + argv[i]);
  }
  return std::string(argv[++i]);
}

inline bool endsWith(const std::string& value, const std::string& suffix) {
  return value.size() >= suffix.size() &&
         value.compare(value.size() - suffix.size(), suffix.size(), suffix) == 0;
}

inline std::string stripLammpsDatExtension(const std::string& path) {
  static const std::string suffix = ".lammpsdat";
  // We derive every output filename by replacing the final input suffix, so we
  // reject inputs that do not follow the example's naming convention.
  if (!endsWith(path, suffix)) {
    throw std::runtime_error(
        "Input file must end with .lammpsdat to derive output filenames: " +
        path);
  }
  return path.substr(0, path.size() - suffix.size());
}

inline std::string basename(const std::string& path) {
  const size_t pos = path.find_last_of("/\\");
  if (pos == std::string::npos) {
    return path;
  }
  return path.substr(pos + 1);
}

} // namespace detail

inline std::string deriveDumpFilename(const std::string& dataFile) {
  return detail::stripLammpsDatExtension(dataFile) + ".lammpstrj";
}

inline std::string deriveRestartFilename(const std::string& dataFile, int which) {
  // `which` is typically 1 or 2 because the run alternates between two restart
  // files to avoid losing the last good snapshot on an interrupted write.
  return detail::stripLammpsDatExtension(dataFile) + ".restart" +
         std::to_string(which) + ".lammpsdat";
}

inline std::string deriveThermoFilename(const std::string& dataFile) {
  return detail::stripLammpsDatExtension(dataFile) + ".thermo";
}

inline void printHelpAndExit(const SimParams& dflt) {
  std::cout
      << "Usage:\n"
      << "  ./kg_uammd -i input.lammpsdat [options]\n\n"
      << "I/O:\n"
      << "  -i, --input FILE    LAMMPS data file input (default: "
      << dflt.dataFile << ")\n"
      << "                      Dump trajectory is derived as FILE with .lammpsdat replaced by .lammpstrj\n"
      << "  -z, --dump-gz       Write the dump as FILE.lammpstrj.gz instead of plain text\n"
      << "                      Restart files are derived as FILE with .lammpsdat replaced by .restart1.lammpsdat and .restart2.lammpsdat\n\n"
      << "Run control:\n"
      << "  -n, --steps N       Number of steps (default: " << dflt.steps
      << ")\n"
      << "  -d, --dump N        Dump interval (default: " << dflt.dumpEvery
      << ")\n"
      << "  -o, --thermo N      Thermo interval (default: "
      << dflt.thermoEvery << ")\n"
      << "  -r, --restart N     Restart interval (default: "
      << dflt.restartEvery << ")\n\n"
      << "Dynamics:\n"
      << "  -t, --dt DT         Time step (default: " << dflt.dt << ")\n"
      << "  -T, --temperature kT\n"
      << "                      Temperature (default: " << dflt.temperature
      << ")\n"
      << "  -x, --friction XI   Friction (default: " << dflt.friction
      << ")\n"
      << "      --init-velocities\n"
      << "                      Ignore input velocities and initialize a Maxwell distribution at the requested temperature\n"
      << "      --remove-com-velocity\n"
      << "                      Subtract the center-of-mass velocity from the system before step 0 and after each integration step\n\n"
      << "Nonbonded (WCA):\n"
      << "  -s, --sigma S       LJ sigma (default: " << dflt.sigma << ")\n"
      << "  -e, --epsilon E     LJ epsilon (default: " << dflt.epsilon
      << ")\n\n"
      << "Bonds (FENE):\n"
      << "  -k, --fene-k K      FENE K (default: " << dflt.feneK << ")\n"
      << "  -R, --fene-r0 R0    FENE R0 (default: " << dflt.feneR0
      << ")\n\n"
      << "Neighbor list:\n"
      << "  -w, --skin SKIN     Neighbor-list skin (default: " << dflt.skin
      << ")\n\n";
  std::exit(0);
}

inline SimParams parseArgs(int argc, char** argv) {
  // The parser stays intentionally small and explicit so the accepted flags are
  // easy to audit alongside the printed help text.
  SimParams p;
  for (int i = 1; i < argc; i++) {
    std::string a = argv[i];
    if (a == "-i" || a == "--input" || a == "--data")
      p.dataFile = detail::getArg(i, argc, argv);
    else if (a == "-n" || a == "--steps")
      p.steps = std::stoi(detail::getArg(i, argc, argv));
    else if (a == "-t" || a == "--dt")
      p.dt = std::stod(detail::getArg(i, argc, argv));
    else if (a == "-T" || a == "--temperature" || a == "--T")
      p.temperature = std::stod(detail::getArg(i, argc, argv));
    else if (a == "-x" || a == "--friction" || a == "--xi")
      p.friction = std::stod(detail::getArg(i, argc, argv));
    else if (a == "-d" || a == "--dump")
      p.dumpEvery = std::stoi(detail::getArg(i, argc, argv));
    else if (a == "-o" || a == "--thermo")
      p.thermoEvery = std::stoi(detail::getArg(i, argc, argv));
    else if (a == "-r" || a == "--restart")
      p.restartEvery = std::stoi(detail::getArg(i, argc, argv));
    else if (a == "-s" || a == "--sigma")
      p.sigma = std::stod(detail::getArg(i, argc, argv));
    else if (a == "-e" || a == "--epsilon" || a == "--eps")
      p.epsilon = std::stod(detail::getArg(i, argc, argv));
    else if (a == "-k" || a == "--fene-k" || a == "--feneK")
      p.feneK = std::stod(detail::getArg(i, argc, argv));
    else if (a == "-R" || a == "--fene-r0" || a == "--feneR0")
      p.feneR0 = std::stod(detail::getArg(i, argc, argv));
    else if (a == "-w" || a == "--skin")
      p.skin = std::stod(detail::getArg(i, argc, argv));
    else if (a == "-z" || a == "--dump-gz")
      p.gzipDump = true;
    else if (a == "--init-velocities")
      p.initializeVelocities = true;
    else if (a == "--remove-com-velocity")
      p.removeCOMVelocity = true;
    else if (a == "-h" || a == "--help")
      printHelpAndExit(SimParams{});
    else
      throw std::runtime_error("Unknown arg: " + a);
  }
  return p;
}

} // namespace kg

#endif
