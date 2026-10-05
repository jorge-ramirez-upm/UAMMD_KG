#include <uammd.cuh>
#include "Integrator/VerletNVE.cuh"
#include "Integrator/VerletNVT.cuh"
#include "../KG/kg_interactors.cuh"
#include "kg_assoc_interactors.cuh"
#include "kg_assoc_cutoff_audit.cuh"
#include "kg_assoc_kinetics.cuh"
#include "kg_assoc_state.cuh"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
#include <set>
#include <stdexcept>
#include <unordered_map>

using namespace uammd;
namespace {
constexpr double kInitialDpdAmplitude = 25.0;
constexpr double kFinalDpdAmplitude = 1000.0;
constexpr int kDpdRampLevels = 10;
constexpr int kDpdRampStepsPerLevel = 100;

struct P { int n=256,push=5000,warmup=20000,steps=100000,every=100,sample=100; double rho=.05,dt=.005,t=1,nu0=20,ea=4,ee=4,damp=2,k=30,r0=1.5,rassoc=std::pow(2.,1./6.); unsigned long long seed=410510; std::string out="k1"; bool force=false,selfTest=false; };
std::string next(int&i,int n,char**v){if(++i>=n)throw std::runtime_error("missing option value");return v[i];}
P parse(int n,char**v){P p;for(int i=1;i<n;++i){std::string a=v[i];if(a=="--n")p.n=std::stoi(next(i,n,v));else if(a=="--rho")p.rho=std::stod(next(i,n,v));else if(a=="--push-steps")p.push=std::stoi(next(i,n,v));else if(a=="--warmup")p.warmup=std::stoi(next(i,n,v));else if(a=="--steps")p.steps=std::stoi(next(i,n,v));else if(a=="--dt")p.dt=std::stod(next(i,n,v));else if(a=="--temperature")p.t=std::stod(next(i,n,v));else if(a=="--nu0")p.nu0=std::stod(next(i,n,v));else if(a=="--Ea")p.ea=std::stod(next(i,n,v));else if(a=="--Ee")p.ee=std::stod(next(i,n,v));else if(a=="--r-assoc")p.rassoc=std::stod(next(i,n,v));else if(a=="--Nevery")p.every=std::stoi(next(i,n,v));else if(a=="--sample")p.sample=std::stoi(next(i,n,v));else if(a=="--damp")p.damp=std::stod(next(i,n,v));else if(a=="--seed")p.seed=std::stoull(next(i,n,v));else if(a=="--output")p.out=next(i,n,v);else if(a=="--force")p.force=true;else if(a=="--self-test")p.selfTest=true;else if(a=="--help"){std::cout<<"kg_assoc_k1 [--n 256 --rho .05 --push-steps 5000 --warmup 20000 --steps 100000 --Ea 4 --Ee 4 --r-assoc R --Nevery 100 --sample 100 --seed S --output PREFIX --self-test]\n";std::exit(0);}else throw std::runtime_error("unknown argument: "+a);}if(p.n<2||p.push<0||p.rho<=0||p.rassoc<=0||p.rassoc>=p.r0||p.every<=0||p.sample<=0||p.damp<=0)throw std::runtime_error("invalid K1 parameters");return p;}
double minImage(double x,double side){return x-side*std::nearbyint(x/side);}
double dpdRampAmplitude(int level) {
  return kInitialDpdAmplitude +
         (kFinalDpdAmplitude - kInitialDpdAmplitude) *
             std::exp((static_cast<double>(level) - kDpdRampLevels) * 0.75);
}

void runDpdPushOffSegment(
    const std::shared_ptr<ParticleData>& particles,
    Box box,
    const P& parameters,
    double amplitude,
    int steps) {
  auto dpd = kg::createDPDInteractor(
      particles, box, parameters.t, 4.5, amplitude, 1.0, parameters.dt);

  VerletNVE::Parameters integratorParameters;
  integratorParameters.dt = parameters.dt;
  integratorParameters.initVelocities = false;

  auto integrator = std::make_shared<VerletNVE>(particles, integratorParameters);
  integrator->addInteractor(dpd);
  for (int step = 0; step < steps; ++step) {
    integrator->forwardTime();
  }
  CudaSafeCall(cudaStreamSynchronize(0));
}

std::vector<kg_assoc::Candidate> candidates(std::shared_ptr<ParticleData> pd,double side,double cut){
  auto x=pd->getPos(access::cpu,access::read);auto id=pd->getId(access::cpu,access::read);int n=pd->getNumParticles(),nc=std::max(1,int(side/cut));double cell=side/nc;std::unordered_map<int,std::vector<int>> bins;
  auto cellId=[&](double z){int q=int(std::floor((z+side*.5)/cell));return (q%nc+nc)%nc;};
  for(int i=0;i<n;++i){auto r=make_real3(x[i]);int a=cellId(r.x),b=cellId(r.y),c=cellId(r.z);bins[a+nc*(b+nc*c)].push_back(i);}std::set<std::pair<int,int>> seen;std::vector<kg_assoc::Candidate> out;
  for(const auto& bin:bins) for(int i:bin.second){auto ri=make_real3(x[i]);int a=cellId(ri.x),b=cellId(ri.y),c=cellId(ri.z);for(int da=-1;da<=1;++da)for(int db=-1;db<=1;++db)for(int dc=-1;dc<=1;++dc){int aa=(a+da+nc)%nc,bb=(b+db+nc)%nc,cc=(c+dc+nc)%nc;auto it=bins.find(aa+nc*(bb+nc*cc));if(it==bins.end())continue;for(int j:it->second){if(i==j)continue;int lo=std::min(id[i],id[j]),hi=std::max(id[i],id[j]);if(!seen.emplace(lo,hi).second)continue;auto rj=make_real3(x[j]);double dx=minImage(double(rj.x-ri.x),side),dy=minImage(double(rj.y-ri.y),side),dz=minImage(double(rj.z-ri.z),side),r=std::sqrt(dx*dx+dy*dy+dz*dz);if(r<cut)out.push_back({lo,hi,r});}}}
  return out;
}
void preparationCheck(std::shared_ptr<ParticleData> pd, double side,
                      const char* stage, bool requireWcaSafe) {
  auto positions = pd->getPos(access::cpu, access::read);
  auto velocities = pd->getVel(access::cpu, access::read);
  auto ids = pd->getId(access::cpu, access::read);
  double minimumSeparation = std::numeric_limits<double>::infinity();
  int firstId = -1;
  int secondId = -1;

  for (int i = 0; i < pd->getNumParticles(); ++i) {
    const auto firstPosition = make_real3(positions[i]);
    if (!std::isfinite(firstPosition.x) || !std::isfinite(firstPosition.y) ||
        !std::isfinite(firstPosition.z) || !std::isfinite(velocities[i].x) ||
        !std::isfinite(velocities[i].y) || !std::isfinite(velocities[i].z)) {
      throw std::runtime_error(std::string("nonfinite state after ") + stage);
    }

    for (int j = i + 1; j < pd->getNumParticles(); ++j) {
      const auto secondPosition = make_real3(positions[j]);
      const double dx = minImage(double(secondPosition.x - firstPosition.x), side);
      const double dy = minImage(double(secondPosition.y - firstPosition.y), side);
      const double dz = minImage(double(secondPosition.z - firstPosition.z), side);
      const double separation = std::sqrt(dx * dx + dy * dy + dz * dz);
      if (separation < minimumSeparation) {
        minimumSeparation = separation;
        firstId = std::min(ids[i], ids[j]);
        secondId = std::max(ids[i], ids[j]);
      }
    }
  }

  std::cout << "K1 preparation " << stage << " min_separation "
            << minimumSeparation << " ids " << firstId << ' ' << secondId
            << " finite_positions_velocities yes\n";
  if (requireWcaSafe && minimumSeparation < 0.8) {
    throw std::runtime_error(
        std::string("unsafe WCA configuration after ") + stage +
        ": min separation " + std::to_string(minimumSeparation));
  }
}
bool warmupIdSelfTest(){return minImage(6.,10.)==-4.&&minImage(-6.,10.)==4.;}
double bondDistance(std::shared_ptr<ParticleData> pd,int i,int j,double side){auto x=pd->getPos(access::cpu,access::read);auto map=pd->getIdOrderedIndices(access::cpu);auto a=make_real3(x[map[i]]),b=make_real3(x[map[j]]);double dx=minImage(double(b.x-a.x),side),dy=minImage(double(b.y-a.y),side),dz=minImage(double(b.z-a.z),side);return std::sqrt(dx*dx+dy*dy+dz*dz);}
void checkActiveBonds(std::shared_ptr<ParticleData> pd,const kg_assoc::StickerState&s,double side,double r0){for(int i:s.stickers())if(s.partner(i)>i){int j=s.partner(i);double r=bondDistance(pd,i,j,side);if(!std::isfinite(r)||r>=r0)throw std::runtime_error("associating FENE bond invalid: ids "+std::to_string(i)+","+std::to_string(j)+" r="+std::to_string(r));}}
void observeActiveBonds(std::shared_ptr<ParticleData> pd,const kg_assoc::StickerState&s,double side,const P&p,kg_assoc::CutoffAudit& audit){for(int i:s.stickers())if(s.partner(i)>i)audit.observe(bondDistance(pd,i,s.partner(i),side),p.k,p.r0,p.ee,p.t);}
void writeState(std::ofstream& f,long long step,const P&p,const kg_assoc::StickerState&s,long long made,long long broke){long long b=0;for(int i:s.stickers())if(s.partner(i)>i)++b;long long a=p.n-2*b;if(a+2*b!=p.n||b!=made-broke)throw std::runtime_error("K1 state invariant failed");f<<step<<' '<<step*p.dt<<' '<<a<<' '<<b<<' '<<made<<' '<<broke<<'\n';}
}
int main(int argc, char** argv) {
  try {
    const P parameters = parse(argc, argv);
    if (parameters.selfTest) {
      if (!warmupIdSelfTest()) {
        throw std::runtime_error("minimum-image self-test failed");
      }
      std::cout << "K1 SELF_TEST PASS preparation minimum-image logic\n";
      return 0;
    }

    const std::string statePath = parameters.out + ".state";
    const std::string eventPath = parameters.out + ".events";
    const std::string cutoffAuditPath = parameters.out + ".cutoff_audit";
    if (!parameters.force &&
        (std::ifstream(statePath) || std::ifstream(eventPath) ||
         std::ifstream(cutoffAuditPath))) {
      throw std::runtime_error("output exists; choose --output or use --force");
    }

    const double side = std::cbrt(parameters.n / parameters.rho);
    auto system = std::make_shared<System>(argc, argv);
    Box box(make_real3(real(side)));
    box.setPeriodicity(true, true, true);
    auto particles = std::make_shared<ParticleData>(parameters.n, system);

    std::mt19937_64 randomNumberGenerator(parameters.seed + 11);
    std::uniform_real_distribution<double> uniformPosition(
        -side * 0.5, side * 0.5);
    {
      auto positions = particles->getPos(access::cpu, access::write);
      auto ids = particles->getId(access::cpu, access::write);
      auto masses = particles->getMass(access::cpu, access::write);
      auto velocities = particles->getVel(access::cpu, access::write);
      auto forces = particles->getForce(access::cpu, access::write);
      for (int particle = 0; particle < parameters.n; ++particle) {
        positions[particle] = make_real4(
            real(uniformPosition(randomNumberGenerator)),
            real(uniformPosition(randomNumberGenerator)),
            real(uniformPosition(randomNumberGenerator)), 0);
        ids[particle] = particle;
        masses[particle] = 1;
        velocities[particle] = make_real3(0);
        forces[particle] = make_real4(0);
      }
    }

    runDpdPushOffSegment(
        particles, box, parameters, kInitialDpdAmplitude, parameters.push);
    preparationCheck(particles, side, "initial_soft_push_off", false);

    for (int level = 1; level <= kDpdRampLevels; ++level) {
      const double amplitude = dpdRampAmplitude(level);
      std::cout << "K1 DPD ramp level " << level << "/" << kDpdRampLevels
                << " amplitude " << amplitude << "\n";
      runDpdPushOffSegment(
          particles, box, parameters, amplitude, kDpdRampStepsPerLevel);
    }
    CudaSafeCall(cudaStreamSynchronize(0));
    preparationCheck(particles, side, "DPD_ramp", true);

    auto wca = kg::createWCAInteractor_CellList(
        particles, box, 1, 1.0, 1.0, 0.4);
    using NVT = VerletNVT::GronbechJensen;
    NVT::Parameters integratorParameters;
    integratorParameters.temperature = parameters.t;
    integratorParameters.friction = 1.0 / parameters.damp;
    integratorParameters.dt = parameters.dt;
    integratorParameters.initVelocities = true;
    auto integrator = std::make_shared<NVT>(particles, integratorParameters);
    integrator->addInteractor(wca);
    for (int step = 0; step < parameters.warmup; ++step) {
      integrator->forwardTime();
    }
    CudaSafeCall(cudaStreamSynchronize(integrator->getStream()));
    preparationCheck(particles, side, "WCA_equilibration", true);

    std::vector<int> stickerIds(parameters.n);
    for (int particle = 0; particle < parameters.n; ++particle) {
      stickerIds[particle] = particle;
    }
    kg_assoc::StickerState state(parameters.n, stickerIds);
    auto associating =
        std::make_shared<kg_assoc::AssociatingFENEInteractor>(
            particles, box, state.devicePartner(), parameters.k,
            parameters.r0, parameters.ee,
            kg_assoc::rstar(parameters.k, parameters.r0));
    integrator->addInteractor(associating);

    kg_assoc::Kinetics kinetics(
        {parameters.nu0, parameters.ea, parameters.t, parameters.dt,
         parameters.every, parameters.seed},
        parameters.k, parameters.r0, parameters.ee);

    std::ofstream stateFile(statePath);
    std::ofstream eventFile(eventPath);
    if (!stateFile || !eventFile) {
      throw std::runtime_error("cannot open K1 output");
    }
    stateFile << "# timestep time N_A N_B creations breaks\n"
              << "# N=" << parameters.n
              << " rho=" << parameters.rho
              << " T=" << parameters.t
              << " dt=" << parameters.dt
              << " nu0=" << parameters.nu0
              << " damp=" << parameters.damp
              << " Ea=" << parameters.ea
              << " Ee=" << parameters.ee
              << " r_assoc=" << parameters.rassoc
              << " Nevery=" << parameters.every
              << " seed=" << parameters.seed
              << " push=" << parameters.push
              << " warmup=" << parameters.warmup
              << " production=" << parameters.steps << "\n";
    eventFile << "# timestep event_type sticker_i sticker_j\n";

    long long creations = 0;
    long long breaks = 0;
    long long chemistrySweeps = 0;
    long long candidateEdgeSum = 0;
    kg_assoc::CutoffAudit cutoffAudit;
    writeState(stateFile, 0, parameters, state, creations, breaks);

    const auto productionStart = std::chrono::steady_clock::now();
    for (int step = 1; step <= parameters.steps; ++step) {
      integrator->forwardTime();
      if (step % parameters.every == 0) {
        CudaSafeCall(cudaStreamSynchronize(integrator->getStream()));
        if (associating->hasInvalidFene()) {
          const auto badPair = associating->invalidFenePair();
          throw std::runtime_error(
              "associating FENE kernel invalid: ids " +
              std::to_string(badPair.first) + "," +
              std::to_string(badPair.second) + " r=" +
              std::to_string(
                  bondDistance(particles, badPair.first, badPair.second, side)));
        }
        checkActiveBonds(particles, state, side, parameters.r0);
        observeActiveBonds(particles, state, side, parameters, cutoffAudit);

        auto candidateEdges = candidates(particles, side, parameters.rassoc);
        candidateEdgeSum += candidateEdges.size();
        ++chemistrySweeps;

        std::vector<kg_assoc::Event> acceptedEvents;
        kinetics.update(
            step, state, std::move(candidateEdges), acceptedEvents);
        for (const auto& event : acceptedEvents) {
          eventFile << event.step << ' ' << event.type << ' ' << event.first
                    << ' ' << event.second << '\n';
          if (event.type == 'C') {
            ++creations;
          } else {
            ++breaks;
          }
        }
      }

      if (step % parameters.sample == 0) {
        writeState(stateFile, step, parameters, state, creations, breaks);
      }
    }

    CudaSafeCall(cudaStreamSynchronize(integrator->getStream()));
    if (associating->hasInvalidFene()) {
      const auto badPair = associating->invalidFenePair();
      throw std::runtime_error(
          "associating FENE kernel invalid: ids " +
          std::to_string(badPair.first) + "," +
          std::to_string(badPair.second) + " r=" +
          std::to_string(
              bondDistance(particles, badPair.first, badPair.second, side)));
    }

    const double productionWallSeconds =
        std::chrono::duration<double>(
            std::chrono::steady_clock::now() - productionStart)
            .count();
    std::cout << "K1 done wall_seconds " << productionWallSeconds
              << " timesteps_per_second "
              << parameters.steps / productionWallSeconds
              << " ns_per_particle_timestep "
              << 1e9 * productionWallSeconds /
                     (static_cast<double>(parameters.n) *
                      static_cast<double>(parameters.steps))
              << " chemistry_sweeps " << chemistrySweeps
              << " mean_candidate_edges "
              << (chemistrySweeps
                      ? static_cast<double>(candidateEdgeSum) / chemistrySweeps
                      : 0.0)
              << " creations " << creations
              << " breaks " << breaks << "\n";
    cutoffAudit.write(std::cout, "K1 ");
    std::ofstream cutoffAuditFile(cutoffAuditPath);
    if (!cutoffAuditFile) {
      throw std::runtime_error("cannot open K1 cutoff audit output");
    }
    cutoffAuditFile << "mode k1_active_bond_audit\n";
    cutoffAuditFile << "r_assoc " << parameters.rassoc << "\n";
    cutoffAudit.write(cutoffAuditFile);
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "K1 error: " << error.what() << '\n';
    return 1;
  }
}
