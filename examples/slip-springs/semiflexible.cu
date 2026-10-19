#include "semiflexible.cuh"
#include "semiflexible_stress.cuh"
#include "semiflexible_scalar_output.h"
#include <thrust/device_vector.h>
#include <array>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <sstream>
#include <vector>
#include <algorithm>
#include <cstring>

using namespace semiflexible;
namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
using Vec=std::array<double,3>;
double seconds(Clock::time_point t) { return std::chrono::duration<double>(Clock::now()-t).count(); }
std::string jsonNumber(double x) { if(!std::isfinite(x)) return "null"; std::ostringstream s;s<<std::setprecision(17)<<x;return s.str(); }
struct Options {
  int n=8,chains=64; Counter steps=1000,sample=100,seed=42001;
  double dt=0.0001,b0=1,kb=30,kappa=2,kbt=1,zeta=1;
  fs::path output,parameters,initial; bool forceOnly=false;
  stress3b::Settings stress;
  std::string scalarOutput="full";
};
Counter integer(std::string s) {
  if(s.empty()||s.find_first_not_of("0123456789")!=std::string::npos) throw std::runtime_error("expected unsigned integer");
  return std::stoull(s);
}
double number(std::string s) {
  size_t end; double x=std::stod(s,&end);
  if(end!=s.size()||!std::isfinite(x)) throw std::runtime_error("expected finite number");
  return x;
}
Options parse(int argc,char** argv) {
  Options o;
  for(int i=1;i<argc;++i) {
    std::string key=argv[i];
    if(key=="--help") {
      std::cout<<"semiflexible --output NEW_DIR [--springs N --chains C --dt H --steps S --sample STRIDE --seed K]\n"
        "[--b0 B --kb K --kappa A --kbt T --zeta Z --parameters FILE --initial FILE --force-input FILE]\n"
        "[--stress-mode off|diagnostic|stream|every-step --stress-input FILE --stress-dump 0|1 --scalar-output full|compact]\n"
        "[--stress-batch FRAMES --cpu-workers N --corr-levels L --corr-slots P --corr-m M --correlator-mib MiB --chain-density NC]\n"
        "parameters: N, then N (b0 kb) pairs, then N+1 bead-indexed kappa values; --springs must match.\n"
        "initial/force-input: chains*(N+1) Cartesian triples; force-input disables integration.\n";
      std::exit(0);
    }
    if(++i==argc) throw std::runtime_error("missing value for "+key);
    std::string v=argv[i];
    if(key=="--output") o.output=v;
    else if(key=="--parameters") o.parameters=v;
    else if(key=="--initial"||key=="--force-input") { o.initial=v;o.forceOnly=key=="--force-input"; }
    else if(key=="--stress-input") {o.initial=v;o.forceOnly=true;o.stress.mode="diagnostic";}
    else if(key=="--stress-mode")o.stress.mode=v;
    else if(key=="--scalar-output")o.scalarOutput=v;
    else if(key=="--chain-density")o.stress.density=number(v);
    else if(key=="--stress-batch"||key=="--cpu-workers"||key=="--corr-levels"||key=="--corr-slots"||key=="--corr-m"||key=="--correlator-mib"||key=="--stress-dump") {
      auto value=integer(v);if(value>65536)throw std::runtime_error("stress option out of range");
      if(key=="--stress-batch")o.stress.batch=value;
      else if(key=="--cpu-workers")o.stress.workers=value;
      else if(key=="--corr-levels")o.stress.correlation.levels=value;
      else if(key=="--corr-slots")o.stress.correlation.slots=value;
      else if(key=="--corr-m")o.stress.correlation.coarsening=value;
      else if(key=="--correlator-mib")o.stress.correlatorMiB=value;
      else {if(value>1)throw std::runtime_error("stress-dump must be 0 or 1");o.stress.dump=value;}
    }
    else if(key=="--steps") o.steps=integer(v);
    else if(key=="--sample") o.sample=integer(v);
    else if(key=="--seed") o.seed=integer(v);
    else if(key=="--springs"||key=="--chains") {
      auto n=integer(v); if(n<1||n>=INT_MAX) throw std::runtime_error("invalid N/chains");
      if(key=="--springs") o.n=n; else o.chains=n;
    } else if(key=="--dt") o.dt=number(v);
    else if(key=="--b0") o.b0=number(v);
    else if(key=="--kb") o.kb=number(v);
    else if(key=="--kappa") o.kappa=number(v);
    else if(key=="--kbt") o.kbt=number(v);
    else if(key=="--zeta") o.zeta=number(v);
    else throw std::runtime_error("unknown option: "+key);
  }
  if(Counter(o.n+1)*o.chains>(INT_MAX-8)/8) throw std::runtime_error("too many beads for diagnostic keys");
  if(o.output.empty()||!o.sample||o.steps>maxSteps) throw std::runtime_error("output, positive sample, steps<=UINT64_MAX/8 required");
  if(!(o.dt>0&&o.kbt>0&&o.zeta>0&&o.b0>=0&&o.kb>0&&o.kappa>=0)) throw std::runtime_error("invalid physical parameters");
  for(double v:{o.dt,o.kbt,o.zeta,o.kb}) if(!(real(v)>0&&std::isfinite(real(v)))) throw std::runtime_error("parameter not representable in precision");
  if(!(real(o.dt/o.zeta)>0&&std::isfinite(real(o.dt/o.zeta))&&real(std::sqrt(2*o.kbt*o.dt/o.zeta))>0&&std::isfinite(real(std::sqrt(2*o.kbt*o.dt/o.zeta)))))
    throw std::runtime_error("update scales not representable");
  if(!std::isfinite(double(o.steps)*o.dt)) throw std::runtime_error("time overflow");
  if(o.stress.everyStep()&&o.stress.batch==32)o.stress.batch=256; // New mode default; legacy stream remains batch32.
  if(o.stress.everyStep()&&o.stress.correlation.slots==16)o.stress.correlation.slots=64;
  o.stress.validate(o.chains);
  if(o.scalarOutput!="full"&&o.scalarOutput!="compact")throw std::runtime_error("scalar-output must be full or compact");
  if(o.scalarOutput=="compact"&&(!o.stress.streaming()||o.forceOnly))throw std::runtime_error("compact scalars require stress streaming");
  if(o.stress.enabled()&&!(std::isfinite(double(o.sample)*o.dt)&&double(o.sample)*o.dt>0))throw std::runtime_error("stress sample spacing outside double range");
  if(o.stress.streaming()&&!(std::isfinite(o.kbt*o.kbt)&&o.kbt*o.kbt>0))throw std::runtime_error("stress thermal normalization outside double range");
  if(o.stress.correlating()&&o.forceOnly)throw std::runtime_error("correlating stress modes require dynamics (zero steps allowed)");
  if(o.stress.correlating()&&((o.stress.everyStep()?o.steps+1:o.steps/o.sample+1)>std::numeric_limits<unsigned long>::max()/o.chains))throw std::runtime_error("correlation pair count overflow");
  if(o.stress.enabled()&&stress3b::Observer::estimatedBytes(o.stress,o.chains,true)>2ULL*1024*1024*1024)throw std::runtime_error("stress workspace exceeds budget");
  return o;
}
std::ofstream outputFile(fs::path p) {
  std::ofstream f(p); f.exceptions(std::ios::badbit|std::ios::failbit); f<<std::setprecision(17); return f;
}
fs::path prepare(fs::path requested) {
  auto root=fs::canonical(SLIP_SPRINGS_DIR).parent_path().parent_path();
  auto p=fs::weakly_canonical(fs::absolute(requested));
  auto rel=p.lexically_relative(root);
  if(!rel.empty()&&*rel.begin()!="..") {
    auto local=p.lexically_relative(fs::canonical(SLIP_SPRINGS_DIR));
    if(local.empty()||*local.begin()=="..") throw std::runtime_error("repository output must stay inside examples/slip-springs");
  }
  if(fs::exists(p)) throw std::runtime_error("refusing to overwrite output directory");
  fs::create_directories(p); return p;
}
struct Parameters {
  std::vector<real2> bonds; std::vector<real> kappa; bool active=false;
};
Parameters parameters(const Options& o) {
  Parameters p; p.bonds.resize(o.n); p.kappa.resize(o.n+1);
  std::vector<double> b(o.n,o.b0),k(o.n,o.kb),a(o.n+1,o.kappa); a[0]=a[o.n]=0;
  if(!o.parameters.empty()) {
    std::ifstream f(o.parameters); int n;
    if(!(f>>n)||n!=o.n) throw std::runtime_error("parameter file N mismatch");
    for(int i=0;i<o.n;++i) if(!(f>>b[i]>>k[i])) throw std::runtime_error("truncated bond parameters");
    for(auto& v:a) if(!(f>>v)) throw std::runtime_error("truncated bead-indexed kappa");
    std::string extra; if(f>>extra) throw std::runtime_error("extra parameter data");
  }
  for(int i=0;i<o.n;++i) {
    if(!(std::isfinite(b[i])&&b[i]>=0&&std::isfinite(k[i])&&k[i]>0&&std::isfinite(real(b[i]))&&std::isfinite(real(k[i]))&&real(k[i])>0)
       ||(b[i]>0&&real(b[i])==0)) throw std::runtime_error("invalid/unrepresentable bond parameter");
    p.bonds[i]=make_real2(b[i],k[i]);
  }
  for(int i=0;i<=o.n;++i) {
    if(!(std::isfinite(a[i])&&a[i]>=0&&std::isfinite(real(a[i])))||(a[i]>0&&real(a[i])==0)) throw std::runtime_error("invalid/unrepresentable kappa");
    p.kappa[i]=a[i]; p.active|=a[i]!=0;
  }
  if(a[0]!=0||a[o.n]!=0) throw std::runtime_error("kappa endpoints must be zero");
  return p;
}
Vec direction(std::mt19937_64& rng,std::normal_distribution<double>& normal) {
  Vec u={normal(rng),normal(rng),normal(rng)}; double l=std::hypot(std::hypot(u[0],u[1]),u[2]);
  if(!(l>0&&std::isfinite(l))) throw std::runtime_error("unrepresentable random direction");
  for(auto& x:u) x/=l; return u;
}
std::vector<real4> initialize(const Options& o,const Parameters& p) {
  std::vector<real4> r(size_t(o.chains)*(o.n+1));
  if(!o.initial.empty()) {
    std::ifstream f(o.initial);
    for(auto& v:r) {
      double x,y,z; if(!(f>>x>>y>>z)) throw std::runtime_error("invalid/truncated initial coordinates");
      v=make_real4(x,y,z,0);
    }
    std::string extra; if(f>>extra) throw std::runtime_error("extra initial coordinates");
    return r;
  }
  // CPU initialization domain; consumes no Philox dynamics counters.
  // Per-chain engines preserve earlier chains when chain count is increased.
  for(int c=0;c<o.chains;++c) {
    std::seed_seq seq{unsigned(o.seed),unsigned(o.seed>>32),unsigned(c),0x4a2u};
    std::mt19937_64 rng(seq); std::normal_distribution<double> normal;
    auto uniform=[&](){return std::generate_canonical<double,53>(rng);};
    Vec position{},u=direction(rng,normal);
    r[size_t(c)*(o.n+1)]=make_real4(0,0,0,0);
    for(int i=0;i<o.n;++i) {
      double sigma=std::sqrt(o.kbt/double(p.bonds[i].y)),a=double(p.bonds[i].x)/sigma;
      double mode=a/2+std::hypot(a,std::sqrt(8.))/2,t=0;
      if(!(sigma>0&&std::isfinite(a)&&std::isfinite(mode))) throw std::runtime_error("initial radial scale overflow");
      bool accepted=false;
      for(int trial=0;trial<10000;++trial) {
        double delta=normal(rng); t=mode+delta;
        if(t>0&&std::log(uniform())<2*(std::log1p(delta/mode)-delta/mode)) { accepted=true;break; }
      }
      if(!accepted) throw std::runtime_error("radial sampler retry limit exceeded");
      if(i) {
        double x=double(p.kappa[i])/o.kbt;
        if(!std::isfinite(x)) throw std::runtime_error("initial angular scale overflow");
        if(x==0) u=direction(rng,normal);
        else {
          double h=uniform();
          double cosine=x<0.05 ? 1+std::log1p((1-h)*std::expm1(-2*x))/x :
            (h==0 ? -1 : 1+std::log(h+(1-h)*std::exp(-2*std::min(x,350.)))/x);
          cosine=std::max(-1.,std::min(1.,cosine));
          int axis=int(std::min_element(u.begin(),u.end(),[](double v,double w){return std::abs(v)<std::abs(w);})-u.begin());
          Vec e{},v{},w{};e[axis]=1;
          for(int d=0;d<3;++d) v[d]=u[(d+1)%3]*e[(d+2)%3]-u[(d+2)%3]*e[(d+1)%3];
          double l=std::hypot(std::hypot(v[0],v[1]),v[2]); for(auto& z:v) z/=l;
          for(int d=0;d<3;++d) w[d]=u[(d+1)%3]*v[(d+2)%3]-u[(d+2)%3]*v[(d+1)%3];
          double phi=2*std::acos(-1.)*uniform(),sine=std::sqrt((1-cosine)*(1+cosine));
          for(int d=0;d<3;++d) u[d]=cosine*u[d]+sine*(std::cos(phi)*v[d]+std::sin(phi)*w[d]);
        }
      }
      for(int d=0;d<3;++d) position[d]+=sigma*t*u[d];
      r[size_t(c)*(o.n+1)+i+1]=make_real4(position[0],position[1],position[2],0);
    }
  }
  return r;
}
struct Event {
  cudaEvent_t start,stop;
  Event(){check(cudaEventCreate(&start),"event");check(cudaEventCreate(&stop),"event");}
  ~Event(){cudaEventDestroy(start);cudaEventDestroy(stop);}
  void begin(){check(cudaEventRecord(start),"event start");}
  double end(){check(cudaEventRecord(stop),"event stop");check(cudaEventSynchronize(stop),"event wait");float ms;check(cudaEventElapsedTime(&ms,start,stop),"elapsed");return ms/1000.;}
};
void positionsFile(fs::path file,const std::vector<real4>& r,int m) {
  auto f=outputFile(file); f<<"chain,bead,x,y,z\n";
  for(size_t i=0;i<r.size();++i) f<<i/m<<','<<i%m<<','<<r[i].x<<','<<r[i].y<<','<<r[i].z<<'\n';
}
void simulate(const Options& o,const fs::path& out,const Parameters& p) {
  auto initStart=Clock::now();
  int m=o.n+1,count=m*o.chains; size_t bytes=count*sizeof(real4);
  // Explicit bounded allocations, independent of number of steps/frames.
  size_t estimate=bytes*8+size_t(count)*1024;
  if(estimate+(o.scalarOutput=="compact"?scalar_output::Compact::estimatedBytes(o.chains):0)+(o.stress.enabled()?stress3b::Observer::estimatedBytes(o.stress,o.chains,p.active):0)>size_t(2)*1024*1024*1024) throw std::runtime_error("reference workspace exceeds 2 GiB budget");
  auto host=initialize(o,p),initial=host;
  thrust::device_vector<real4> r(host),next(count),forces(count);
  thrust::device_vector<real2> bonds(p.bonds);
  thrust::device_vector<real> angles; // Empty and unallocated for all-zero bending.
  if(p.active) angles=p.kappa;
  thrust::device_vector<int> error(1,INT_MAX);
  auto ptr=[](auto& v){return thrust::raw_pointer_cast(v.data());};
  real4* current=ptr(r);real4* following=ptr(next);
  Counter stretchLaunches=0,bendLaunches=0,updateLaunches=0;
  auto diagnose=[&](Counter step,bool proposed=false) {
    int key;check(cudaMemcpy(&key,ptr(error),sizeof(int),cudaMemcpyDeviceToHost),"diagnostic readback");
    if(key!=INT_MAX) {
      std::vector<real4> snapshot(count);
      check(cudaMemcpy(snapshot.data(),current,bytes,cudaMemcpyDeviceToHost),"failure snapshot");
      positionsFile(out/"failure_positions.csv",snapshot,m);
      if(proposed) {
        check(cudaMemcpy(snapshot.data(),following,bytes,cudaMemcpyDeviceToHost),"failed proposal snapshot");
        positionsFile(out/"failure_proposal.csv",snapshot,m);
      }
      auto f=outputFile(out/"failure.json");
      f<<"{\"step\":"<<step<<",\"time\":"<<double(step)*o.dt<<",\"flat_bead\":"<<key/8
       <<",\"chain\":"<<(key/8)/m<<",\"bead\":"<<(key/8)%m<<",\"reason\":"<<key%8<<",\"stage\":\""<<(proposed?"proposal":"force")<<"\",\"precision_bits\":"<<8*sizeof(real)<<",\"kbt\":"<<o.kbt<<",\"zeta\":"<<o.zeta<<",\"seed\":"<<o.seed<<",\"dt\":"<<o.dt<<"}\n";
      throw std::runtime_error("GPU diagnostic failure at step "+std::to_string(step)+", bead "+std::to_string(key/8)+", reason "+std::to_string(key%8));
    }
  };
  auto evaluate=[&](Counter step) {
    stretch<<<(count+255)/256,256>>>(current,ptr(forces),ptr(bonds),count,m,ptr(error));++stretchLaunches;
    if(p.active) {bend<<<(count+255)/256,256>>>(current,ptr(forces),ptr(angles),count,m,ptr(error));++bendLaunches;}
    check(cudaGetLastError(),"force launch");diagnose(step);
  };
  auto pf=outputFile(out/"parameters.txt"); pf<<o.n<<'\n';
  for(auto v:p.bonds) pf<<v.x<<' '<<v.y<<'\n';for(auto k:p.kappa)pf<<k<<'\n';pf.close();
  evaluate(0); // Validate the uploaded precision, including inactive-angle policy.
  positionsFile(out/"initial.csv",host,m);
  std::vector<real4> hf(count);
  if(o.forceOnly) {
    check(cudaMemcpy(hf.data(),ptr(forces),bytes,cudaMemcpyDeviceToHost),"force readback");
    auto f=outputFile(out/"forces.csv");f<<"chain,bead,fx,fy,fz,energy\n";
    for(int i=0;i<count;++i) f<<i/m<<','<<i%m<<','<<hf[i].x<<','<<hf[i].y<<','<<hf[i].z<<','<<hf[i].w<<'\n';
  }
  std::unique_ptr<stress3b::Observer> stressObserver;
  if(o.stress.enabled())stressObserver=std::make_unique<stress3b::Observer>(o.stress,o.chains,m,ptr(bonds),ptr(angles),p.active,(o.stress.everyStep()?o.dt:o.sample*o.dt),o.kbt,o.seed,o.forceOnly?0:o.steps/2,out);
  if(o.forceOnly&&stressObserver){
    stressObserver->sample(current,0);
    std::vector<real4> afterForce(count),afterPosition(count);
    check(cudaMemcpy(afterForce.data(),ptr(forces),bytes,cudaMemcpyDeviceToHost),"stress immutable forces");
    check(cudaMemcpy(afterPosition.data(),current,bytes,cudaMemcpyDeviceToHost),"stress immutable positions");
    if(std::memcmp(afterForce.data(),hf.data(),bytes)||std::memcmp(afterPosition.data(),host.data(),bytes))throw std::runtime_error("stress modified positions or forces");
  }
  std::unique_ptr<scalar_output::Compact> compactScalar;
  if(o.scalarOutput=="compact")compactScalar=std::make_unique<scalar_output::Compact>(o.chains,o.n,o.steps,o.sample,o.dt,out);
  auto samples=outputFile(out/(compactScalar?"scalar_selected.csv":"samples.csv"));
  samples<<"step,time,chain,mean_r,mean_r2,re2,rg2,cm_msd,monomer_msd,min_length";
  int sep=std::min(4,o.n-1);for(int s=1;s<=sep;++s)samples<<",tangent"<<s;samples<<'\n';
  auto ib=outputFile(out/"initial_bonds.csv");ib<<"chain,bond,length\n";
  size_t bn=size_t(o.chains)*o.n;
  std::vector<double> sums(bn),squares(bn);
  std::vector<Counter> hist(bn*33,0);Counter observations=0;
  double histogramMax=0,minLength=std::numeric_limits<double>::infinity();
  for(auto v:p.bonds) histogramMax=std::max(histogramMax,double(v.x)+8*std::sqrt(o.kbt/double(v.y)));
  if(!(histogramMax>0&&std::isfinite(histogramMax))) throw std::runtime_error("histogram range not representable");
  double observationTime=0,outputTime=0,updateTime=0,diagnosticTime=0;
  std::vector<Vec> initialCm(o.chains);
  for(int c=0;c<o.chains;++c)for(int j=0;j<m;++j){auto v=initial[c*m+j];initialCm[c][0]+=double(v.x)/m;initialCm[c][1]+=double(v.y)/m;initialCm[c][2]+=double(v.z)/m;}
  auto observe=[&](Counter step) {
    if(stressObserver&&!o.stress.everyStep())stressObserver->sample(current,step);
    auto t=Clock::now();check(cudaMemcpy(host.data(),current,bytes,cudaMemcpyDeviceToHost),"observation readback");
    // CPU observation reductions use double, from the stored precision.
    std::ostringstream rows,initialRows;rows<<std::setprecision(17);initialRows<<std::setprecision(17);
    bool serialize=!compactScalar||compactScalar->selectedStep(step);
    bool accumulate=step>=o.steps/2; if(accumulate)++observations;
    for(int c=0;c<o.chains;++c) {
      Vec cm{},ee{};double mono=0,re2=0,rg2=0,cmmsd=0,mean=0,second=0,lmin=std::numeric_limits<double>::infinity();
      std::vector<Vec> q(o.n);std::vector<double> length(o.n);
      auto origin=host[c*m];
      for(int j=0;j<m;++j) {
        auto v=host[c*m+j],start=initial[c*m+j];
        double x[3]={double(v.x),double(v.y),double(v.z)},z[3]={double(start.x),double(start.y),double(start.z)};
        double anchor[3]={double(origin.x),double(origin.y),double(origin.z)};
        for(int d=0;d<3;++d){cm[d]+=(x[d]-anchor[d])/m;mono+=(x[d]-z[d])*(x[d]-z[d])/m;}
        if(j){auto prev=host[c*m+j-1];q[j-1]={x[0]-double(prev.x),x[1]-double(prev.y),x[2]-double(prev.z)};}
      }
      for(int b=0;b<o.n;++b) {
        length[b]=std::hypot(std::hypot(q[b][0],q[b][1]),q[b][2]);double l=length[b];
        if(!std::isfinite(l)) throw std::runtime_error("nonfinite observed length");
        mean+=l/o.n;second+=l*l/o.n;lmin=std::min(lmin,l);minLength=std::min(minLength,l);
        size_t index=size_t(c)*o.n+b;
        if(accumulate){sums[index]+=l;squares[index]+=l*l;++hist[index*33+std::min(32,int(std::min(32.,32*l/histogramMax)))];}
        if(step==0)initialRows<<c<<','<<b<<','<<l<<'\n';
      }
      auto end=host[c*m+o.n];ee={double(end.x)-origin.x,double(end.y)-origin.y,double(end.z)-origin.z};
      for(int d=0;d<3;++d){re2+=ee[d]*ee[d];double anchor=d==0?origin.x:(d==1?origin.y:origin.z);double delta=anchor+cm[d]-initialCm[c][d];cmmsd+=delta*delta;}
      for(int j=0;j<m;++j){auto v=host[c*m+j];double x[3]={double(v.x)-origin.x,double(v.y)-origin.y,double(v.z)-origin.z};for(int d=0;d<3;++d)rg2+=(x[d]-cm[d])*(x[d]-cm[d])/m;}
      std::array<double,11> scalarValues{mean,second,re2,rg2,cmmsd,mono,lmin};
      if(serialize)rows<<step<<','<<step*o.dt<<','<<c<<','<<mean<<','<<second<<','<<re2<<','<<rg2<<','<<cmmsd<<','<<mono<<','<<lmin;
      for(int s=1;s<=sep;++s){double corr=0;for(int b=0;b<o.n-s;++b){if(length[b]==0||length[b+s]==0){corr=std::numeric_limits<double>::quiet_NaN();break;}for(int d=0;d<3;++d)corr+=q[b][d]*q[b+s][d]/(length[b]*length[b+s])/(o.n-s);}scalarValues[s+6]=corr;if(serialize)rows<<','<<corr;}
      if(serialize)rows<<'\n';
      if(compactScalar&&compactScalar->record(step,c,scalarValues))positionsFile(out/"scalar_failure_positions.csv",host,m);
    }
    observationTime+=seconds(t);t=Clock::now();samples<<rows.str();if(step==0)ib<<initialRows.str();samples.flush();ib.flush();outputTime+=seconds(t);
  };
  double initializationTime=seconds(initStart);
  Event event;auto productionStart=Clock::now();
  if(!o.forceOnly) {
    if(stressObserver&&o.stress.everyStep())stressObserver->sample(current,0);
    observe(0);
    for(Counter step=0;step<o.steps;++step) {
      event.begin();auto d=Clock::now();
      evaluate(step);diagnosticTime+=seconds(d);
      update<<<(count+255)/256,256>>>(current,following,ptr(forces),count,real(o.dt/o.zeta),real(std::sqrt(2*o.kbt*o.dt/o.zeta)),o.seed,step,ptr(error));++updateLaunches;
      check(cudaGetLastError(),"update launch");d=Clock::now();diagnose(step,true);diagnosticTime+=seconds(d);
      std::swap(current,following);updateTime+=event.end();
      if(stressObserver&&o.stress.everyStep())stressObserver->sample(current,step+1);
      if((step+1)%o.sample==0)observe(step+1);
    }
    // Validate final state even if it is not an observation frame.
    evaluate(o.steps);
  }
  if(stressObserver)stressObserver->finish();
  double productionTime=seconds(productionStart);auto finalStart=Clock::now();
  if(stressObserver)stressObserver->write();
  check(cudaMemcpy(host.data(),current,bytes,cudaMemcpyDeviceToHost),"final positions");positionsFile(out/"final.csv",host,m);
  auto stats=outputFile(out/"bond_statistics.csv");stats<<"chain,bond,frames,mean_r,mean_r2";for(int b=0;b<33;++b)stats<<",bin"<<b;stats<<'\n';
  if(observations)for(size_t i=0;i<bn;++i){stats<<i/o.n<<','<<i%o.n<<','<<observations<<','<<sums[i]/observations<<','<<squares[i]/observations;for(int b=0;b<33;++b)stats<<','<<hist[i*33+b];stats<<'\n';}
  stats.close();samples.close();ib.close();if(compactScalar)compactScalar->write(o.n);double finalTime=seconds(finalStart);
  int device;cudaDeviceProp prop{};check(cudaGetDevice(&device),"device");check(cudaGetDeviceProperties(&prop,device),"properties");
  size_t deviceBytes=3*bytes+p.bonds.size()*sizeof(real2)+(angles.capacity()*sizeof(real))+sizeof(int);
  double denominator=double(count)*(o.forceOnly?0:o.steps);auto rate=[&](double x){if(denominator>0)return std::to_string(x/denominator*1e9);return std::string("null");};
  auto meta=outputFile(out/"metadata.json");
  meta<<"{\n\"model\":\"finite-rest-length-Kratky-Porod\",\"timer_version\":"<<(stressObserver?2:1)<<",\"precision_bits\":"<<8*sizeof(real)
      <<",\"gpu\":\""<<prop.name<<"\",\"chains\":"<<o.chains<<",\"springs\":"<<o.n<<",\"beads_per_chain\":"<<m<<",\"total_beads\":"<<count
      <<",\"dt\":"<<o.dt<<",\"effective_mobility_step\":"<<double(real(o.dt/o.zeta))<<",\"effective_noise\":"<<double(real(std::sqrt(2*o.kbt*o.dt/o.zeta)))
      <<",\"steps\":"<<(o.forceOnly?0:o.steps)<<",\"production_time\":"<<(o.forceOnly?0:o.steps*o.dt)<<",\"sample\":"<<o.sample<<",\"seed\":"<<o.seed<<",\"rng_domain\":3,\"kbt\":"<<o.kbt<<",\"zeta\":"<<o.zeta
      <<",\"bending_device_bytes\":"<<(angles.capacity()*sizeof(real))<<",\"active_angles\":"<<std::count_if(p.kappa.begin(),p.kappa.end(),[](real v){return v!=0;})
      <<",\"stretch_launches\":"<<stretchLaunches<<",\"bending_launches\":"<<bendLaunches<<",\"update_launches\":"<<updateLaunches
      <<",\"device_bytes\":"<<deviceBytes<<",\"cpu_workspace_budget_estimate_bytes\":"<<estimate
      <<",\"initialization_method\":\""<<(o.initial.empty()?"CPU-direct-equilibrium":"supplied-coordinates")<<"\",\"initialization_seconds\":"<<initializationTime<<",\"integration_seconds\":"<<updateTime<<",\"production_wall_seconds\":"<<productionTime
      <<",\"observation_seconds\":"<<observationTime<<",\"recurrent_output_seconds\":"<<outputTime<<",\"final_output_seconds\":"<<finalTime
      <<",\"force_and_diagnostic_wall_seconds\":"<<diagnosticTime<<",\"integration_ns_per_bead_step\":"<<rate(updateTime)<<",\"overall_ns_per_bead_step\":"<<rate(productionTime)
      <<",\"bead_updates_per_second\":"<<(updateTime>0?std::to_string(denominator/updateTime):"null")
      <<",\"histogram_max\":"<<histogramMax<<",\"histogram_finite_bins\":32,\"histogram_overflow_bin\":32,\"minimum_sampled_bond\":"<<jsonNumber(minLength)
      <<",\"integration_timer_scope\":\"CUDA events: forces, update, diagnostic D2H and host launch/synchronization gaps; excludes observations and output\",\"observation_scope\":\"D2H full positions, CPU reductions and formatting; output writes separate\"}\n";
  meta.close(); // Main metadata/terminal telemetry excluded; v2 final time includes stress exports/metadata.
  std::cout<<"semiflexible N="<<o.n<<" chains="<<o.chains<<" beads="<<count<<" steps="<<(o.forceOnly?0:o.steps)
    <<" physical_time="<<(o.forceOnly?0:o.steps*o.dt)<<" updates/s="<<(updateTime>0?denominator/updateTime:0)<<" init_s="<<initializationTime<<" integration_s="<<updateTime<<" production_s="<<productionTime
    <<" integration_ns/bead/step="<<rate(updateTime)<<" overall_ns/bead/step="<<rate(productionTime)
    <<" observation_s="<<observationTime<<" recurrent_output_s="<<outputTime<<" final_output_s="<<finalTime
    <<" bending_bytes="<<(angles.capacity()*sizeof(real))<<" bending_launches="<<bendLaunches<<'\n';
}
int main(int argc,char** argv) {
  try {auto o=parse(argc,argv);auto p=parameters(o);auto out=prepare(o.output);simulate(o,out,p);return 0;}
  catch(const std::exception& e){std::cerr<<"semiflexible: "<<e.what()<<'\n';return 1;}
}
