#include <uammd.cuh>
#include "Integrator/VerletNVT.cuh"
#include "../KG/kg_interactors.cuh"
#include "kg_assoc_cli.cuh"
#include "kg_assoc_interactors.cuh"
#include "kg_assoc_kinetics.cuh"
#include "kg_assoc_state.cuh"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <vector>

using namespace uammd;
namespace {
double distance(std::shared_ptr<ParticleData> pd, Box box) { auto p=pd->getPos(access::cpu,access::read); auto d=box.apply_pbc(make_real3(p[1])-make_real3(p[0])); return std::sqrt(double(dot(d,d))); }
bool near(double a,double b,double tol=2e-10){return std::abs(a-b)<=tol*std::max(1.0,std::max(std::abs(a),std::abs(b)));}
bool diagnostics(const kg_assoc::Params& p) {
  const double rs=kg_assoc::rstar(p.k,p.r0), h=1e-6;
  // Independently tabulated from the current LAMMPS PairAssociating equations.
  if (p.k==30. && p.r0==1.5 && p.ee==4. &&
      (!near(rs,.9608971989592554) || !near(kg_assoc::deltaU(.8,p.k,p.r0,p.ee),-10.532554868411678) ||
       !near(kg_assoc::deltaU(1.2,p.k,p.r0,p.ee),12.652183479619136))) { std::cerr<<"FAIL LAMMPS potential reference values\n"; return false; }
  for(double r: {0.8,rs,1.2,1.49}) { if(r>=p.r0) continue; double numeric=-(kg_assoc::deltaU(r+h,p.k,p.r0,p.ee)-kg_assoc::deltaU(r-h,p.k,p.r0,p.ee))/(2*h); double analytic=-p.k*r/(1-r*r/(p.r0*p.r0)); if(!near(numeric,analytic,3e-5)){std::cerr<<"FAIL force derivative at "<<r<<"\n";return false;} }
  if(!near(kg_assoc::deltaU(rs,p.k,p.r0,p.ee),-p.ee)||!near(kg_assoc::deltaU(1.1,p.k,p.r0,p.ee)-kg_assoc::deltaU(1.1,p.k,p.r0,0),-p.ee)||!near(-p.k*1.1/(1-1.1*1.1/(p.r0*p.r0)),-71.39423076923079)){std::cerr<<"FAIL FENE shift/force convention\n";return false;}
  bool guarded=false; try { (void)kg_assoc::deltaU(p.r0,p.k,p.r0,p.ee); } catch(const std::runtime_error&) {guarded=true;} if(!guarded){std::cerr<<"FAIL R0 guard\n";return false;}
  // Exercise the exact host/device expression used by AssociatingFENEInteractor.
  const double shift=kg_assoc::associatingFeneShift(p.k,p.r0,p.ee,rs);
  for(double r: {0.8,rs,1.1,1.2}) {
    const double e=kg_assoc::checkedAssociatingFeneEnergy(r,p.k,p.r0,shift);
    const double expected=kg_assoc::fene(r,p.k,p.r0)-kg_assoc::fene(rs,p.k,p.r0)-p.ee;
    if(!near(e,expected,3e-5)) {std::cerr<<"FAIL interactor energy at "<<r<<"\n";return false;}
    const double dh=1e-4;
    const double numeric=-(kg_assoc::checkedAssociatingFeneEnergy(r+dh,p.k,p.r0,shift)-kg_assoc::checkedAssociatingFeneEnergy(r-dh,p.k,p.r0,shift))/(2*dh);
    const double force=-r*kg_assoc::associatingFeneForceDivR(real(r*r),real(p.k),real(p.r0));
    if(!near(numeric,force,3e-3)) {std::cerr<<"FAIL interactor force derivative at "<<r<<"\n";return false;}
  }
  if(!near(kg_assoc::checkedAssociatingFeneEnergy(rs,p.k,p.r0,shift),-p.ee,3e-5) ||
     !near(kg_assoc::checkedAssociatingFeneEnergy(1.1,p.k,p.r0,shift+p.ee)-kg_assoc::checkedAssociatingFeneEnergy(1.1,p.k,p.r0,shift),-p.ee,3e-5) ||
     !near(-1.1*kg_assoc::associatingFeneForceDivR(real(1.1*1.1),real(p.k),real(p.r0)),-71.39423076923079,3e-5)) {std::cerr<<"FAIL interactor Ee shift/force independence\n";return false;}
  if(!std::isfinite(kg_assoc::checkedAssociatingFeneEnergy(1.49,p.k,p.r0,shift))) {std::cerr<<"FAIL interactor near-R0 behavior\n";return false;}
  guarded=false; try {(void)kg_assoc::checkedAssociatingFeneEnergy(p.r0,p.k,p.r0,shift);} catch(const std::runtime_error&) {guarded=true;} if(!guarded) {std::cerr<<"FAIL interactor R0 guard\n";return false;}
  // Independent expected values: q=-expm1(-rate*dt), then min(1, Boltzmann).
  for(double rateDt: {1e-12,.7}) for(double du: {-2.,0.,2.}) { double q=-std::expm1(-rateDt), pf=q*(du<=0?1:std::exp(-du/p.temperature)), pb=q*(du>=0?1:std::exp(du/p.temperature)); if(!near(kg_assoc::attemptProbability(rateDt),q)||!near(pf/pb,std::exp(-du/p.temperature),2e-12)){std::cerr<<"FAIL detailed balance\n";return false;} }
  std::cout<<"SELF_TEST PASS rstar="<<std::setprecision(12)<<rs<<" interactor-energy/force/R0/detailed-balance (small and moderate q)\n"; return true;
}
}
int main(int argc,char**argv) {
  kg_assoc::Params p; try {p=kg_assoc::parseArgs(argc,argv);} catch(const std::exception&e){std::cerr<<"Argument error: "<<e.what()<<"\n";return 1;} if(!diagnostics(p)) return 2; if(p.selfTest)return 0;
  auto sys=std::make_shared<System>(argc,argv); Box box(make_real3(real(p.box))); box.setPeriodicity(true,true,true); auto pd=std::make_shared<ParticleData>(2,sys);
  {auto x=pd->getPos(access::cpu,access::write); x[0]=make_real4(real(-.5),real(0),real(0),real(0)); x[1]=make_real4(real(.5),real(0),real(0),real(0)); auto id=pd->getId(access::cpu,access::write);auto m=pd->getMass(access::cpu,access::write);auto v=pd->getVel(access::cpu,access::write);auto f=pd->getForce(access::cpu,access::write);for(int i=0;i<2;++i){id[i]=i;m[i]=real(1);v[i]=make_real3(real(0));f[i]=make_real4(real(0));}}
  kg_assoc::StickerState state(2,{0,1}); auto wca=kg::createWCAInteractor_CellList(pd,box,1,1.,1.,.3); auto assoc=std::make_shared<kg_assoc::AssociatingFENEInteractor>(pd,box,state.devicePartner(),p.k,p.r0,p.ee,kg_assoc::rstar(p.k,p.r0));
  using NVT=VerletNVT::GronbechJensen; NVT::Parameters ip;ip.temperature=real(p.temperature);ip.friction=real(p.friction);ip.dt=real(p.dt);ip.initVelocities=true;auto integrator=std::make_shared<NVT>(pd,ip);integrator->addInteractor(wca);integrator->addInteractor(assoc);
  kg_assoc::Kinetics kinetics({p.nu0,p.ea,p.temperature,p.dt,p.every,p.seed},p.k,p.r0,p.ee); std::ofstream events(p.prefix+".events"); if(!events){std::cerr<<"cannot open event log\n";return 1;} events<<"# timestep event_type sticker_i sticker_j\n";
  long long updates=0, creations=0, breaks=0, bondedSamples=0, unboundSamples=0, bondN=0; double bondSum=0; long long boundStart=-1, freeStart=0; double boundDur=0,freeDur=0; long long nBound=0,nFree=0;
  for(int step=1;step<=p.steps;++step){integrator->forwardTime(); if(step%p.every) continue; ++updates; CudaSafeCall(cudaStreamSynchronize(integrator->getStream())); double r=distance(pd,box); if(assoc->hasInvalidFene() || (state.bonded(0,1)&&r>=p.r0)){std::cerr<<"Associating FENE bond exceeded R0\n";return 3;} std::vector<kg_assoc::Event> ev; if(r<p.rAssoc) kinetics.update(step,state,{{0,1,r}},ev); for(auto&e:ev){events<<e.step<<' '<<e.type<<' '<<e.first<<' '<<e.second<<'\n';if(e.type=='C'){++creations;freeDur+=step-freeStart;++nFree;boundStart=step;}else{++breaks;boundDur+=step-boundStart;++nBound;freeStart=step;}} if(state.bonded(0,1)){++bondedSamples;bondSum+=r;++bondN;}else ++unboundSamples; }
  if(state.bonded(0,1)){boundDur+=(p.steps+1-boundStart);++nBound;}else{freeDur+=(p.steps+1-freeStart);++nFree;} std::ofstream summary(p.prefix+".summary"); summary<<std::setprecision(12)<<"kinetic_updates "<<updates<<"\naccepted_creations "<<creations<<"\naccepted_breaks "<<breaks<<"\nfraction_bonded "<<(updates?double(bondedSamples)/updates:0)<<"\nfraction_unbonded "<<(updates?double(unboundSamples)/updates:0)<<"\nmean_bond_distance "<<(bondN?bondSum/bondN:std::numeric_limits<double>::quiet_NaN())<<"\nmean_bonded_episode_steps "<<(nBound?boundDur/nBound:0)<<"\nmean_unbound_episode_steps "<<(nFree?freeDur/nFree:0)<<"\n"; std::cout<<summary.rdbuf(); return 0;
}
