#ifndef EXAMPLES_KG_KG_LAMMPS_IO_CUH
#define EXAMPLES_KG_KG_LAMMPS_IO_CUH

// LAMMPS-oriented I/O helpers for the Kremer-Grest example.
//
// This file owns:
//   - parsing the subset of LAMMPS data files used by the example
//   - building bond payloads for UAMMD bonded interactors
//   - writing dumps and alternating restart snapshots

#include <algorithm>
#include <cctype>
#include <fstream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#include <zlib.h>

#include <uammd.cuh>

namespace kg {

// Minimal in-memory representation of the LAMMPS input used by this example.
// Atom and bond identifiers remain in their original 1-based LAMMPS form here;
// conversion to UAMMD indexing happens later in the runtime helpers.
struct LammpsData {
  int natoms = 0;
  int nbonds = 0;
  int atomTypes = 1;

  double xlo = 0;
  double xhi = 0;
  double ylo = 0;
  double yhi = 0;
  double zlo = 0;
  double zhi = 0;

  std::vector<double> x;
  std::vector<double> y;
  std::vector<double> z;
  std::vector<double> vx;
  std::vector<double> vy;
  std::vector<double> vz;
  std::vector<int> type;
  std::vector<int> mol;
  std::vector<std::pair<int, int>> bonds;
  bool hasVelocities = false;
};

namespace detail {

// LAMMPS section headers may appear with trailing comments, so we treat
// whitespace and `# ...` as acceptable after the section name.
inline bool isSectionHeader(const std::string& line, const std::string& name) {
  std::string s = line;
  s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](unsigned char c) {
            return !std::isspace(c);
          }));
  s.erase(std::find_if(s.rbegin(), s.rend(), [](unsigned char c) {
            return !std::isspace(c);
          }).base(),
          s.end());
  if (s.size() < name.size())
    return false;
  if (s.substr(0, name.size()) != name)
    return false;
  if (s.size() == name.size())
    return true;
  const char c = s[name.size()];
  return std::isspace(static_cast<unsigned char>(c)) || c == '#';
}

inline void readHeaderLineCounts(const std::string& line, LammpsData& d) {
  std::istringstream iss(line);
  int n;
  std::string what;
  if (!(iss >> n >> what))
    return;
  if (what == "atoms")
    d.natoms = n;
  else if (what == "bonds")
    d.nbonds = n;
  else if (what == "atom") {
    std::string maybeTypes;
    if (iss >> maybeTypes) {
      if (maybeTypes == "types")
        d.atomTypes = n;
    }
  }
}

inline bool readBoxBounds(const std::string& line,
                          double& lo,
                          double& hi,
                          const std::string& key) {
  std::istringstream iss(line);
  std::string a, b, c, d;
  if (!(iss >> a >> b >> c >> d))
    return false;
  if (c == key + "lo" && d == key + "hi") {
    lo = std::stod(a);
    hi = std::stod(b);
    return true;
  }
  return false;
}

inline void readAtomsSection(std::ifstream& in, LammpsData& d) {
  d.x.assign(d.natoms, 0.0);
  d.y.assign(d.natoms, 0.0);
  d.z.assign(d.natoms, 0.0);
  d.type.assign(d.natoms, 1);
  d.mol.assign(d.natoms, 1);

  std::string line;
  while (std::getline(in, line)) {
    const bool allspace = std::all_of(line.begin(), line.end(),
                                      [](unsigned char c) {
                                        return std::isspace(c);
                                      });
    if (allspace || line.empty())
      break;
    if (line[0] == '#')
      continue;

    std::istringstream iss(line);
    int id = 0;
    int mol = 1;
    int typ = 1;
    double x = 0;
    double y = 0;
    double z = 0;
    // The example expects `Atoms # bond` style records: id, molecule, type,
    // and Cartesian coordinates.
    if (!(iss >> id >> mol >> typ >> x >> y >> z))
      continue;
    if (id < 1 || id > d.natoms)
      continue;

    const int idx = id - 1;
    d.mol[idx] = mol;
    d.type[idx] = typ;
    d.x[idx] = x;
    d.y[idx] = y;
    d.z[idx] = z;
  }
}

inline void readVelocitiesSection(std::ifstream& in, LammpsData& d) {
  d.vx.assign(d.natoms, 0.0);
  d.vy.assign(d.natoms, 0.0);
  d.vz.assign(d.natoms, 0.0);
  d.hasVelocities = false;

  std::string line;
  while (std::getline(in, line)) {
    const bool allspace = std::all_of(line.begin(), line.end(),
                                      [](unsigned char c) {
                                        return std::isspace(c);
                                      });
    if (allspace || line.empty())
      break;
    if (line[0] == '#')
      continue;

    std::istringstream iss(line);
    int id = 0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    // Velocities are optional in the input file, so we keep zero-filled arrays
    // unless at least one valid line is found.
    if (!(iss >> id >> vx >> vy >> vz))
      continue;
    if (id < 1 || id > d.natoms)
      continue;

    const int idx = id - 1;
    d.vx[idx] = vx;
    d.vy[idx] = vy;
    d.vz[idx] = vz;
    d.hasVelocities = true;
  }
}

inline void readBondsSection(std::ifstream& in, LammpsData& d) {
  d.bonds.clear();
  d.bonds.reserve(d.nbonds);

  std::string line;
  while (std::getline(in, line)) {
    const bool allspace = std::all_of(line.begin(), line.end(),
                                      [](unsigned char c) {
                                        return std::isspace(c);
                                      });
    if (allspace || line.empty())
      break;
    if (line[0] == '#')
      continue;

    std::istringstream iss(line);
    int id = 0;
    int btype = 1;
    int ai = 0;
    int aj = 0;
    // Bond type is currently ignored because the KG example uses one FENE
    // parameter set for every bond.
    if (!(iss >> id >> btype >> ai >> aj))
      continue;
    d.bonds.push_back({ai, aj});
  }
}

} // namespace detail

inline LammpsData readLammpsDataFile(const std::string& path) {
  std::ifstream in(path);
  if (!in)
    throw std::runtime_error("Cannot open LAMMPS data file: " + path);

  LammpsData d;
  std::string line;

  // The parser is single-pass and only extracts the sections required by this
  // example, leaving unsupported sections untouched.
  while (std::getline(in, line)) {
    detail::readHeaderLineCounts(line, d);
    (void)detail::readBoxBounds(line, d.xlo, d.xhi, "x");
    (void)detail::readBoxBounds(line, d.ylo, d.yhi, "y");
    (void)detail::readBoxBounds(line, d.zlo, d.zhi, "z");

    if (detail::isSectionHeader(line, "Atoms")) {
      std::getline(in, line);
      if (d.natoms <= 0)
        throw std::runtime_error("Header did not set 'atoms' count.");
      detail::readAtomsSection(in, d);
    }
    if (detail::isSectionHeader(line, "Bonds")) {
      std::getline(in, line);
      if (d.nbonds > 0)
        detail::readBondsSection(in, d);
    }
    if (detail::isSectionHeader(line, "Velocities")) {
      std::getline(in, line);
      if (d.natoms <= 0)
        throw std::runtime_error("Header did not set 'atoms' count.");
      detail::readVelocitiesSection(in, d);
    }
  }

  if (d.natoms <= 0)
    throw std::runtime_error("Failed to read natoms from header.");
  if (d.xhi == d.xlo || d.yhi == d.ylo || d.zhi == d.zlo) {
    throw std::runtime_error("Failed to read box bounds (xlo/xhi etc.)");
  }
  if (static_cast<int>(d.x.size()) != d.natoms) {
    throw std::runtime_error("Atoms section missing or failed to parse.");
  }
  return d;
}

inline std::string writeUammdBondFileFromLammps(const std::string& outPath,
                                                const LammpsData& d,
                                                double feneK,
                                                double feneR0) {
  std::ofstream out(outPath);
  if (!out)
    throw std::runtime_error("Cannot write bond file: " + outPath);

  out << d.bonds.size() << "\n";
  for (const auto& bond : d.bonds) {
    const int ai = bond.first - 1;
    const int aj = bond.second - 1;
    if (ai < 0 || aj < 0 || ai >= d.natoms || aj >= d.natoms)
      continue;
    out << ai << " " << aj << " " << feneK << " " << feneR0 << "\n";
  }
  return outPath;
}

inline std::string buildUammdBondDataFromLammps(const LammpsData& d,
                                                double feneK,
                                                double feneR0) {
  // UAMMD bonded interactors expect a compact text block: count on the first
  // line, then one zero-based bond record per line.
  std::ostringstream out;
  out << d.bonds.size() << "\n";
  for (const auto& bond : d.bonds) {
    const int ai = bond.first - 1;
    const int aj = bond.second - 1;
    if (ai < 0 || aj < 0 || ai >= d.natoms || aj >= d.natoms)
      continue;
    out << ai << " " << aj << " " << feneK << " " << feneR0 << "\n";
  }
  return out.str();
}

class DumpWriter {
public:
  DumpWriter(const std::string& path, bool gzip) : gzip(gzip), path(path) {
    if (gzip) {
      gz = gzopen(path.c_str(), "wb");
    } else {
      out.open(path);
    }
  }

  ~DumpWriter() {
    close();
  }

  DumpWriter(const DumpWriter&) = delete;
  DumpWriter& operator=(const DumpWriter&) = delete;

  bool good() const {
    return gzip ? gz != nullptr : static_cast<bool>(out);
  }

  void write(const std::string& text) {
    if (gzip) {
      if (!gz || gzwrite(gz, text.data(), static_cast<unsigned int>(text.size())) == 0) {
        throw std::runtime_error("Cannot write gzip dump file: " + path);
      }
    } else {
      out << text;
      if (!out) {
        throw std::runtime_error("Cannot write dump file: " + path);
      }
    }
  }

  void close() {
    if (gzip) {
      if (gz) {
        gzclose(gz);
        gz = nullptr;
      }
    } else if (out.is_open()) {
      out.close();
    }
  }

private:
  bool gzip = false;
  std::string path;
  std::ofstream out;
  gzFile gz = nullptr;
};

inline std::string buildLAMMPSDumpFrame(
    int step,
    const LammpsData& ld,
    std::shared_ptr<uammd::ParticleData> pd,
    double xlo,
    double xhi,
    double ylo,
    double yhi,
    double zlo,
    double zhi) {
  using namespace uammd;

  // Particle positions are stored in UAMMD's centered box convention, so we
  // shift them back to the original LAMMPS `[lo, hi]` frame when writing.
  const real xshift = real(0.5) * real(xlo + xhi);
  const real yshift = real(0.5) * real(ylo + yhi);
  const real zshift = real(0.5) * real(zlo + zhi);

  auto pos = pd->getPos(access::cpu, access::read);
  auto vel = pd->getVel(access::cpu, access::read);

  std::ostringstream out;
  out << "ITEM: TIMESTEP\n" << step << "\n";
  out << "ITEM: NUMBER OF ATOMS\n" << ld.natoms << "\n";
  out << "ITEM: BOX BOUNDS pp pp pp\n";
  out << xlo << " " << xhi << "\n";
  out << ylo << " " << yhi << "\n";
  out << zlo << " " << zhi << "\n";
  out << "ITEM: ATOMS id type x y z vx vy vz\n";

  for (int i = 0; i < ld.natoms; i++) {
    const int id = i + 1;
    const int typ = (i < static_cast<int>(ld.type.size())) ? ld.type[i] : 1;
    const auto r = pos[i];
    const auto v = vel[i];
    out << id << " " << typ << " " << (r.x + xshift) << " " << (r.y + yshift)
        << " " << (r.z + zshift) << " "
        << v.x << " " << v.y << " " << v.z << "\n";
  }
  return out.str();
}

inline void appendLAMMPSDumpFrame(
    DumpWriter& out,
    int step,
    const LammpsData& ld,
    std::shared_ptr<uammd::ParticleData> pd,
    double xlo,
    double xhi,
    double ylo,
    double yhi,
    double zlo,
    double zhi) {
  out.write(buildLAMMPSDumpFrame(step, ld, pd, xlo, xhi, ylo, yhi, zlo, zhi));
}

inline void writeLAMMPSDataSnapshot(
    const std::string& filename,
    int step,
    const LammpsData& ld,
    std::shared_ptr<uammd::ParticleData> pd,
    const std::string& producerTag) {
  using namespace uammd;

  // Restart files preserve the original LAMMPS-style box bounds and 1-based
  // identifiers so they can be fed back into the same workflow directly.
  const real xshift = real(0.5) * real(ld.xlo + ld.xhi);
  const real yshift = real(0.5) * real(ld.ylo + ld.yhi);
  const real zshift = real(0.5) * real(ld.zlo + ld.zhi);

  auto pos = pd->getPos(access::cpu, access::read);
  auto vel = pd->getVel(access::cpu, access::read);

  std::ofstream out(filename);
  if (!out)
    throw std::runtime_error("Cannot write restart file: " + filename);

  out << "LAMMPS data file written by " << producerTag << ", step " << step
      << "\n\n";
  out << ld.natoms << " atoms\n";
  out << ld.bonds.size() << " bonds\n\n";
  out << ld.atomTypes << " atom types\n";
  out << 1 << " bond types\n\n";

  out << ld.xlo << " " << ld.xhi << " xlo xhi\n";
  out << ld.ylo << " " << ld.yhi << " ylo yhi\n";
  out << ld.zlo << " " << ld.zhi << " zlo zhi\n\n";

  out << "Masses\n\n";
  for (int t = 1; t <= ld.atomTypes; ++t) {
    out << t << " 1.0\n";
  }
  out << "\n";

  out << "Atoms # bond\n\n";
  for (int i = 0; i < ld.natoms; i++) {
    const int id = i + 1;
    const int mol = (i < static_cast<int>(ld.mol.size())) ? ld.mol[i] : 1;
    const int typ = (i < static_cast<int>(ld.type.size())) ? ld.type[i] : 1;
    const auto r = pos[i];
    out << id << " " << mol << " " << typ << " " << (r.x + xshift) << " "
        << (r.y + yshift) << " " << (r.z + zshift) << "\n";
  }
  out << "\n";

  out << "Velocities\n\n";
  for (int i = 0; i < ld.natoms; i++) {
    const int id = i + 1;
    const auto v = vel[i];
    out << id << " " << v.x << " " << v.y << " " << v.z << "\n";
  }
  out << "\n";

  out << "Bonds\n\n";
  for (size_t b = 0; b < ld.bonds.size(); ++b) {
    const int id = static_cast<int>(b) + 1;
    const int ai = ld.bonds[b].first;
    const int aj = ld.bonds[b].second;
    out << id << " 1 " << ai << " " << aj << "\n";
  }
  out << "\n";
}

inline void writeLAMMPSDataRestart(
    const std::string& filename,
    int step,
    const LammpsData& ld,
    std::shared_ptr<uammd::ParticleData> pd) {
  writeLAMMPSDataSnapshot(filename, step, ld, pd, "kg_uammd");
}

} // namespace kg

#endif
