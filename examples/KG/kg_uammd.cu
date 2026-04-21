// kg_uammd.cu
//
// Minimal Kremer–Grest (KG) polymer melt using UAMMD (core, header-only).
//
// Adds requested features:
//   - LAMMPS-style dump file (lammpstrj) with x,y,z,vx,vy,vz
//   - Alternating restart files in LAMMPS data format:
//       restart1.lammpsdat, restart2.lammpsdat
//   - Explicit neighbor list: CellList (good for dense/high-density GPU systems)
//   - --help shows default values
//
// Physics:
//   - Nonbonded: WCA (repulsive LJ) via Potential::LJ with cutOff=2^(1/6)*sigma and shift=true
//   - Bonds:     FENE via BondedForces<BondedType::FENE,2> reading a generated bond file
//   - Dynamics:  Langevin using VerletNVT::GronbechJensen
//
// Notes:
//   - LAMMPS atom IDs are 1-based; UAMMD is 0-based internally. We convert when building bond file.
//   - This reader targets a common LAMMPS "data" format with:
//       Atoms: id mol type x y z
//       Bonds: id bond_type ai aj
//     (It ignores extra trailing columns in Atoms/Bonds lines.)
//   - We store mol IDs so we can write restarts back in the same atom_style bond layout.

#include <uammd.cuh>

#include "Integrator/VerletNVT.cuh"
#include "Interactor/PairForces.cuh"
#include "Interactor/Potential/Potential.cuh"
#include "Interactor/BondedForces.cuh"

#include "Interactor/NeighbourList/CellList.cuh"


// Neighbor list (linked-cell). UAMMD provides several NL options; CellList is typically best for dense systems.
#include "Interactor/NeighbourList/CellList.cuh"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <stdexcept>

// --------------------------
// CLI parsing (minimal)
// --------------------------
static std::string getArg(int& i, int argc, char** argv){
  if(i+1 >= argc){
    throw std::runtime_error(std::string("Missing value after ") + argv[i]);
  }
  return std::string(argv[++i]);
}

struct SimParams{
  // I/O
  std::string dataFile      = "system.data";
  std::string dumpFile      = "traj.lammpstrj";
  std::string restartBase   = "restart"; // will produce restart1.lammpsdat/restart2.lammpsdat

  // Run control
  int steps                 = 10000;
  int dumpEvery             = 1000;
  int thermoEvery           = 1000;
  int restartEvery          = 5000; // write alternating restarts

  // Dynamics
  double dt                 = 0.01;
  double temperature        = 1.0;
  double friction           = 0.5;  // xi

  // KG parameters
  double sigma              = 1.0;
  double epsilon            = 1.0;

  // FENE
  double feneK              = 30.0;
  double feneR0             = 1.5;

  // Neighbor list tuning (WCA cutoff fixed by sigma; skin is adjustable)
  double skin               = 0.3;   // typical NL skin in reduced units; tune for performance
};

static void printHelpAndExit(const SimParams& dflt){
  std::cout <<
    "Usage:\n"
    "  ./kg_uammd --data system.data [options]\n\n"
    "I/O:\n"
    "  --data FILE           LAMMPS data file input (default: " << dflt.dataFile << ")\n"
    "  --dumpfile FILE       LAMMPS dump trajectory (default: " << dflt.dumpFile << ")\n"
    "  --restartbase STR     Restart base name -> STR1.lammpsdat/STR2.lammpsdat (default: " << dflt.restartBase << ")\n\n"
    "Run control:\n"
    "  --steps N             Number of steps (default: " << dflt.steps << ")\n"
    "  --dump N              Dump interval (default: " << dflt.dumpEvery << ")\n"
    "  --thermo N            Thermo interval (default: " << dflt.thermoEvery << ")\n"
    "  --restart N           Restart interval (default: " << dflt.restartEvery << ")\n\n"
    "Dynamics:\n"
    "  --dt DT               Time step (default: " << dflt.dt << ")\n"
    "  --T  kT               Temperature (default: " << dflt.temperature << ")\n"
    "  --xi XI               Friction (default: " << dflt.friction << ")\n\n"
    "Nonbonded (WCA):\n"
    "  --sigma S             LJ sigma (default: " << dflt.sigma << ")\n"
    "  --eps E               LJ epsilon (default: " << dflt.epsilon << ")\n\n"
    "Bonds (FENE):\n"
    "  --feneK K             FENE K (default: " << dflt.feneK << ")\n"
    "  --feneR0 R0           FENE R0 (default: " << dflt.feneR0 << ")\n\n"
    "Neighbor list:\n"
    "  --skin SKIN           Neighbor-list skin (default: " << dflt.skin << ")\n\n";
  std::exit(0);
}

static SimParams parseArgs(int argc, char** argv){
  SimParams p; // defaults
  for(int i=1;i<argc;i++){
    std::string a = argv[i];
    if(a=="--data")         p.dataFile     = getArg(i,argc,argv);
    else if(a=="--dumpfile")p.dumpFile     = getArg(i,argc,argv);
    else if(a=="--restartbase") p.restartBase = getArg(i,argc,argv);

    else if(a=="--steps")   p.steps        = std::stoi(getArg(i,argc,argv));
    else if(a=="--dt")      p.dt           = std::stod(getArg(i,argc,argv));
    else if(a=="--T")       p.temperature  = std::stod(getArg(i,argc,argv));
    else if(a=="--xi")      p.friction     = std::stod(getArg(i,argc,argv));
    else if(a=="--dump")    p.dumpEvery    = std::stoi(getArg(i,argc,argv));
    else if(a=="--thermo")  p.thermoEvery  = std::stoi(getArg(i,argc,argv));
    else if(a=="--restart") p.restartEvery = std::stoi(getArg(i,argc,argv));

    else if(a=="--sigma")   p.sigma        = std::stod(getArg(i,argc,argv));
    else if(a=="--eps")     p.epsilon      = std::stod(getArg(i,argc,argv));

    else if(a=="--feneK")   p.feneK        = std::stod(getArg(i,argc,argv));
    else if(a=="--feneR0")  p.feneR0       = std::stod(getArg(i,argc,argv));

    else if(a=="--skin")    p.skin         = std::stod(getArg(i,argc,argv));

    else if(a=="--help"){
      printHelpAndExit(SimParams{});
    } else {
      throw std::runtime_error("Unknown arg: " + a);
    }
  }
  return p;
}

// ---------------------------------------
// LAMMPS data reader (minimal, pragmatic)
// ---------------------------------------
struct LammpsData{
  int natoms = 0;
  int nbonds = 0;
  int atomTypes = 1;

  // Box bounds
  double xlo=0, xhi=0, ylo=0, yhi=0, zlo=0, zhi=0;

  // Atom data (stored by ID order, 0..natoms-1)
  std::vector<double> x, y, z;
  std::vector<int> type; // 1..atomTypes
  std::vector<int> mol;  // molecule ID (from data file)

  // Bonds stored as 1-based IDs from file
  std::vector<std::pair<int,int>> bonds;
};

static bool isSectionHeader(const std::string& line, const std::string& name){
  std::string s = line;
  s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](unsigned char c){return !std::isspace(c);} ));
  s.erase(std::find_if(s.rbegin(), s.rend(), [](unsigned char c){return !std::isspace(c);} ).base(), s.end());
  if(s.size() < name.size()) return false;
  if(s.substr(0, name.size()) != name) return false;
  if(s.size()==name.size()) return true;
  char c = s[name.size()];
  return std::isspace((unsigned char)c) || c=='#';
}

static void readHeaderLineCounts(const std::string& line, LammpsData& d){
  std::istringstream iss(line);
  int n; std::string what;
  if(!(iss >> n >> what)) return;
  if(what=="atoms") d.natoms = n;
  else if(what=="bonds") d.nbonds = n;
  else if(what=="atom"){
    std::string maybeTypes;
    if(iss >> maybeTypes){
      if(maybeTypes=="types") d.atomTypes = n;
    }
  }
}

static bool readBoxBounds(const std::string& line, double& lo, double& hi, const std::string& key){
  std::istringstream iss(line);
  std::string a,b,c,d;
  if(!(iss >> a >> b >> c >> d)) return false;
  if(c==key+"lo" && d==key+"hi"){
    lo = std::stod(a);
    hi = std::stod(b);
    return true;
  }
  return false;
}

static void readAtomsSection(std::ifstream& in, LammpsData& d){
  d.x.assign(d.natoms, 0.0);
  d.y.assign(d.natoms, 0.0);
  d.z.assign(d.natoms, 0.0);
  d.type.assign(d.natoms, 1);
  d.mol.assign(d.natoms, 1);

  std::string line;
  while(std::getline(in, line)){
    bool allspace = std::all_of(line.begin(), line.end(), [](unsigned char c){return std::isspace(c);});
    if(allspace || line.empty()) break;
    if(line[0]=='#') continue;

    // Expect: id mol type x y z ...
    std::istringstream iss(line);
    int id=0, mol=1, typ=1;
    double x=0,y=0,z=0;
    if(!(iss >> id >> mol >> typ >> x >> y >> z)) continue;
    if(id < 1 || id > d.natoms) continue;
    int idx = id - 1;
    d.mol[idx]  = mol;
    d.type[idx] = typ;
    d.x[idx]    = x;
    d.y[idx]    = y;
    d.z[idx]    = z;
  }
}

static void readBondsSection(std::ifstream& in, LammpsData& d){
  d.bonds.clear();
  d.bonds.reserve(d.nbonds);

  std::string line;
  while(std::getline(in, line)){
    bool allspace = std::all_of(line.begin(), line.end(), [](unsigned char c){return std::isspace(c);});
    if(allspace || line.empty()) break;
    if(line[0]=='#') continue;

    // Expect: id bond_type ai aj ...
    std::istringstream iss(line);
    int id=0, btype=1, ai=0, aj=0;
    if(!(iss >> id >> btype >> ai >> aj)) continue;
    d.bonds.push_back({ai, aj});
  }
}

static LammpsData readLammpsDataFile(const std::string& path){
  std::ifstream in(path);
  if(!in) throw std::runtime_error("Cannot open LAMMPS data file: " + path);

  LammpsData d;
  std::string line;

  // single pass: parse header and sections when encountered
  while(std::getline(in, line)){
    readHeaderLineCounts(line, d);
    (void)readBoxBounds(line, d.xlo, d.xhi, "x");
    (void)readBoxBounds(line, d.ylo, d.yhi, "y");
    (void)readBoxBounds(line, d.zlo, d.zhi, "z");

    if(isSectionHeader(line, "Atoms")){
      std::getline(in, line); // skip blank/comment
      if(d.natoms<=0) throw std::runtime_error("Header did not set 'atoms' count.");
      readAtomsSection(in, d);
    }
    if(isSectionHeader(line, "Bonds")){
      std::getline(in, line);
      if(d.nbonds>0) readBondsSection(in, d);
    }
  }

  if(d.natoms<=0) throw std::runtime_error("Failed to read natoms from header.");
  if(d.xhi==d.xlo || d.yhi==d.ylo || d.zhi==d.zlo){
    throw std::runtime_error("Failed to read box bounds (xlo/xhi etc.)");
  }
  if((int)d.x.size()!=d.natoms) throw std::runtime_error("Atoms section missing or failed to parse.");
  return d;
}

// ---------------------------------------
// Write UAMMD bond file (for BondedForces)
// ---------------------------------------
static std::string writeUammdBondFileFromLammps(
  const std::string& outPath,
  const LammpsData& d,
  double feneK,
  double feneR0
){
  std::ofstream out(outPath);
  if(!out) throw std::runtime_error("Cannot write bond file: " + outPath);

  out << d.bonds.size() << "\n";
  for(const auto& b : d.bonds){
    int ai = b.first  - 1;
    int aj = b.second - 1;
    if(ai<0 || aj<0 || ai>=d.natoms || aj>=d.natoms) continue;
    out << ai << " " << aj << " " << feneK << " " << feneR0 << "\n";
  }
  return outPath;
}

// ---------------------------------------
// LAMMPS dump writer (lammpstrj style)
// ---------------------------------------
static void appendLAMMPSDumpFrame(
  std::ofstream& out,
  int step,
  const LammpsData& ld,
  std::shared_ptr<uammd::ParticleData> pd,
  double xlo, double xhi, double ylo, double yhi, double zlo, double zhi
){
  using namespace uammd;
  auto pos = pd->getPos(access::cpu, access::read);
  auto vel = pd->getVel(access::cpu, access::read);

  out << "ITEM: TIMESTEP\n" << step << "\n";
  out << "ITEM: NUMBER OF ATOMS\n" << ld.natoms << "\n";
  out << "ITEM: BOX BOUNDS pp pp pp\n";
  out << xlo << " " << xhi << "\n";
  out << ylo << " " << yhi << "\n";
  out << zlo << " " << zhi << "\n";
  out << "ITEM: ATOMS id type x y z vx vy vz\n";

  // Write atoms in ID order (1..N)
  for(int i=0;i<ld.natoms;i++){
    int id  = i+1;
    int typ = (i<(int)ld.type.size()) ? ld.type[i] : 1;
    auto r  = pos[i];
    auto v  = vel[i];
    out << id << " " << typ << " "
        << r.x << " " << r.y << " " << r.z << " "
        << v.x << " " << v.y << " " << v.z << "\n";
  }
}

// ---------------------------------------
// LAMMPS data restart writer
// ---------------------------------------
static void writeLAMMPSDataRestart(
  const std::string& filename,
  int step,
  const LammpsData& ld,
  std::shared_ptr<uammd::ParticleData> pd
){
  using namespace uammd;
  auto pos = pd->getPos(access::cpu, access::read);
  auto vel = pd->getVel(access::cpu, access::read);

  std::ofstream out(filename);
  if(!out) throw std::runtime_error("Cannot write restart file: " + filename);

  // Header
  out << "LAMMPS data file written by kg_uammd, step " << step << "\n\n";
  out << ld.natoms << " atoms\n";
  out << ld.bonds.size() << " bonds\n\n";
  out << ld.atomTypes << " atom types\n";
  out << 1 << " bond types\n\n";

  out << ld.xlo << " " << ld.xhi << " xlo xhi\n";
  out << ld.ylo << " " << ld.yhi << " ylo yhi\n";
  out << ld.zlo << " " << ld.zhi << " zlo zhi\n\n";

  // Masses (reduced units: m=1)
  out << "Masses\n\n";
  for(int t=1; t<=ld.atomTypes; ++t){
    out << t << " 1.0\n";
  }
  out << "\n";

  // Atoms: id mol type x y z
  out << "Atoms # bond\n\n";
  for(int i=0;i<ld.natoms;i++){
    int id  = i+1;
    int mol = (i<(int)ld.mol.size())  ? ld.mol[i]  : 1;
    int typ = (i<(int)ld.type.size()) ? ld.type[i] : 1;
    auto r  = pos[i];
    out << id << " " << mol << " " << typ << " "
        << r.x << " " << r.y << " " << r.z << "\n";
  }
  out << "\n";

  // Velocities: id vx vy vz
  out << "Velocities\n\n";
  for(int i=0;i<ld.natoms;i++){
    int id = i+1;
    auto v = vel[i];
    out << id << " " << v.x << " " << v.y << " " << v.z << "\n";
  }
  out << "\n";

  // Bonds: id bond_type ai aj  (we write bond_type=1 for all; KG uses one bond type)
  out << "Bonds\n\n";
  for(size_t b=0;b<ld.bonds.size();++b){
    int id = (int)b + 1;
    int ai = ld.bonds[b].first;
    int aj = ld.bonds[b].second;
    out << id << " 1 " << ai << " " << aj << "\n";
  }
  out << "\n";
}

// ---------------------------------------
// Create UAMMD interactors (WCA + FENE)
// ---------------------------------------
static std::shared_ptr<uammd::Interactor> createWCAInteractor_CellList(
  std::shared_ptr<uammd::ParticleData> pd,
  const uammd::Box& box,
  int atomTypes,
  double epsilon,
  double sigma,
  double skin
){
  using namespace uammd;

  using PF = PairForces<Potential::LJ>;
  auto pot = std::make_shared<Potential::LJ>();

  const double rc = std::pow(2.0, 1.0/6.0) * sigma; // WCA cutoff

  // Set same LJ for all type pairs (0-based types in UAMMD parameters)
  for(int ti=0; ti<atomTypes; ++ti){
    for(int tj=0; tj<atomTypes; ++tj){
      Potential::LJ::InputPairParameters par;
      par.epsilon = (real)epsilon;
      par.sigma   = (real)sigma;
      par.cutOff  = (real)rc;
      par.shift   = true;
      pot->setPotParameters(ti, tj, par);
    }
  }

  typename PF::Parameters params;
  params.box = box;

  // Explicit GPU-friendly neighbor list for dense systems:
  // CellList builds a linked-cell structure and is typically very efficient at high density.
  {
    using NL = CellList;
    typename NL::Parameters nlp;
    // Many UAMMD NLs accept a cutoff+skin or a "rcut" here; to keep this robust, we set the rcut
    // to rc+skin in the parameters (common pattern).
    nlp.cutOff = (real)(rc + skin);
    nlp.box = box;
    auto nl = std::make_shared<NL>(pd, nlp);
    params.nl = nl;
  }

  return std::make_shared<PF>(pd, params, pot);
}

static std::shared_ptr<uammd::Interactor> createFENEInteractor(
  std::shared_ptr<uammd::ParticleData> pd,
  const uammd::Box& box,
  const std::string& bondFile
){
  using namespace uammd;
  using Bond = BondedType::FENE;
  using BF   = BondedForces<Bond,2>;

  typename BF::Parameters params;
  params.file = bondFile;
  return std::make_shared<BF>(pd, params);
}

// --------------------------
// main
// --------------------------
int main(int argc, char** argv){
  using namespace uammd;

  SimParams par;
  try{
    par = parseArgs(argc, argv);
  } catch(const std::exception& e){
    std::cerr << "Argument error: " << e.what() << "\nUse --help\n";
    return 1;
  }

  // Read initial configuration from LAMMPS
  LammpsData ld;
  try{
    ld = readLammpsDataFile(par.dataFile);
  } catch(const std::exception& e){
    std::cerr << "LAMMPS data read error: " << e.what() << "\n";
    return 1;
  }

  // Build UAMMD particle data
  auto pd = std::make_shared<ParticleData>(ld.natoms);

  // Periodic box
  real3 L = make_real3((real)(ld.xhi-ld.xlo), (real)(ld.yhi-ld.ylo), (real)(ld.zhi-ld.zlo));
  Box box(L);
  box.setPeriodicity(true,true,true);

  // Initialize positions
  {
    auto pos = pd->getPos(access::cpu, access::write);
    for(int i=0;i<ld.natoms;i++){
      pos[i] = make_real4((real)ld.x[i], (real)ld.y[i], (real)ld.z[i], 0.0);
    }
  }

  // Convert bonds to UAMMD file for BondedForces
  std::string bondFile = "bonds_fene.dat";
  try{
    writeUammdBondFileFromLammps(bondFile, ld, par.feneK, par.feneR0);
  } catch(const std::exception& e){
    std::cerr << "Bond file write error: " << e.what() << "\n";
    return 1;
  }

  // Interactors: WCA + FENE
  auto wca  = createWCAInteractor_CellList(pd, box, ld.atomTypes, par.epsilon, par.sigma, par.skin);
  auto fene = createFENEInteractor(pd, bondFile);

  // Langevin integrator
  using NVT = VerletNVT::GronbechJensen;
  NVT::Parameters ip;
  ip.temperature = (real)par.temperature;
  ip.friction    = (real)par.friction;
  ip.dt          = (real)par.dt;
  ip.initVelocities = true; // Maxwell at t=0
  auto integrator = std::make_shared<NVT>(pd, ip);

  integrator->addInteractor(wca);
  integrator->addInteractor(fene);

  // Open dump file
  std::ofstream dump(par.dumpFile);
  if(!dump){
    std::cerr << "Cannot open dump file: " << par.dumpFile << "\n";
    return 1;
  }

  std::cout << "# KG-UAMMD starting\n";
  std::cout << "# atoms " << ld.natoms << " bonds " << ld.bonds.size() << " box "
            << (ld.xhi-ld.xlo) << " " << (ld.yhi-ld.ylo) << " " << (ld.zhi-ld.zlo) << "\n";
  std::cout << "# dt " << par.dt << " T " << par.temperature << " xi " << par.friction
            << " skin " << par.skin << "\n";

  // Dump step 0
  appendLAMMPSDumpFrame(dump, 0, ld, pd, ld.xlo, ld.xhi, ld.ylo, ld.yhi, ld.zlo, ld.zhi);

  // Restart at step 0 if requested interval divides 0? (Usually you want an initial restart anyway.)
  if(par.restartEvery > 0){
    try{
      writeLAMMPSDataRestart(par.restartBase + "1.lammpsdat", 0, ld, pd);
    } catch(const std::exception& e){
      std::cerr << "Restart write error: " << e.what() << "\n";
      return 1;
    }
  }

  // Time loop
  for(int step=1; step<=par.steps; ++step){
    integrator->forwardTime();

    if(par.thermoEvery>0 && step % par.thermoEvery == 0){
      auto E = integrator->sumEnergy();
      std::cout << "Step " << step << " E " << E << "\n";
    }

    if(par.dumpEvery>0 && step % par.dumpEvery == 0){
      appendLAMMPSDumpFrame(dump, step, ld, pd, ld.xlo, ld.xhi, ld.ylo, ld.yhi, ld.zlo, ld.zhi);
    }

    if(par.restartEvery>0 && step % par.restartEvery == 0){
      // Alternate between restart1 and restart2
      int which = ((step / par.restartEvery) % 2) ? 2 : 1;
      std::string fn = par.restartBase + std::to_string(which) + ".lammpsdat";
      try{
        writeLAMMPSDataRestart(fn, step, ld, pd);
      } catch(const std::exception& e){
        std::cerr << "Restart write error: " << e.what() << "\n";
        return 1;
      }
    }
  }

  std::cout << "# Done\n";
  return 0;
}
