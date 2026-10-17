#pragma once
#include "cpu_workers.h"
#include <filesystem>
#include <sstream>

// Host-only adapter: reuse the validated correlator and persistent worker bank.
// No empirical mean subtraction or changes to KG's block/lag definitions.
namespace stress3b {
struct Settings {
  std::string mode="off";
  unsigned workers=1, batch=32, correlatorMiB=512;
  streaming::Parameters correlation;
  double density=0; bool dump=false;
  bool enabled() const { return mode!="off"; }
  bool streaming() const { return mode=="stream"; }
  void validate(std::size_t chains) const {
    if(mode!="off"&&mode!="diagnostic"&&mode!="stream") throw std::runtime_error("stress-mode must be off, diagnostic or stream");
    correlation.validate();
    if(!batch||batch>4096||!correlatorMiB||correlatorMiB>65536)throw std::runtime_error("invalid stress batch/correlator budget");
    if(streaming()) {
      streaming::workerCount(workers,chains);
      if(std::size_t(batch)*chains*sizeof(streaming::Sample)>256ULL*1024*1024)throw std::runtime_error("stress batch exceeds 256 MiB");
      if(streaming::OwnedCorrelator6::bytes(correlation)+sizeof(void*)>std::size_t(correlatorMiB)*1024*1024/chains)throw std::runtime_error("stress bank exceeds correlator budget");
    }
    if(!std::isfinite(density)||density<0)throw std::runtime_error("chain-density must be finite and nonnegative (0=unspecified)");
  }
  std::size_t hostBytes(std::size_t chains) const {
    return streaming()?chains*(std::size_t(batch)*sizeof(streaming::Sample)+streaming::OwnedCorrelator6::bytes(correlation)+sizeof(void*)+42*sizeof(double)):0;
  }
};
inline std::ofstream file(const std::filesystem::path& p) {
  std::ofstream f(p);f.exceptions(std::ios::badbit|std::ios::failbit);f<<std::setprecision(17);return f;
}
class Correlations {
  Settings cfg;std::size_t chains;
  streaming::Bank bank;
  streaming::CpuWorkers cpu;
  std::ofstream dump;
  std::vector<double> sum,second;
  std::uint64_t momentStart=0;
public:
  double output_seconds=0;
  std::uint64_t frames=0,moment_frames=0;
  Correlations(Settings s,std::size_t c,const std::filesystem::path& out,std::uint64_t momentStartStep=0)
    :cfg(s),chains(c),bank(c,s.correlation,std::size_t(s.correlatorMiB)*1024*1024),
     cpu(bank,c,s.workers),sum(c*6,0),second(c*36,0),momentStart(momentStartStep) {
    if(cfg.dump){dump=file(out/"stress_samples.csv");dump<<"step,chain,xy,xz,yz,xx_yy,xx_zz,yy_zz\n";}
  }
  void received(const streaming::Sample* frame,std::uint64_t step) {
    auto begin=std::chrono::steady_clock::now();
    bool selected=step>=momentStart;if(selected)++moment_frames;
    for(std::size_t c=0;c<chains;++c) {
      if(cfg.dump)dump<<step<<','<<c;
      for(int a=0;a<6;++a) {
        double x=frame[c].v[a];if(!std::isfinite(x))throw std::runtime_error("nonfinite stress channel");
        if(selected){sum[c*6+a]+=x;for(int b=0;b<6;++b)second[c*36+a*6+b]+=x*frame[c].v[b];}
        if(cfg.dump)dump<<','<<x;
      }
      if(cfg.dump)dump<<'\n';
    }
    if(cfg.dump)dump.flush();
    output_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
    ++frames;
  }
  void consume(const streaming::Sample* batch,std::size_t count){cpu.consume(batch,count);}
  const streaming::CpuWorkers& workers() const {return cpu;}
  void write(const std::filesystem::path& out,double spacing,double kbt) {
    if(bank.frames!=frames)throw std::runtime_error("stress frames lost before finalization");
    bank.write((out/"stress_correlations_raw.csv").string(),spacing);
    std::ifstream input(out/"stress_correlations_raw.csv");input.exceptions(std::ios::badbit);if(!input)throw std::runtime_error("cannot read raw correlations");std::string line;
    auto normalized=file(out/"stress_correlations.csv");
    std::getline(input,line);
    // The reused Bank's legacy g/g_se columns are raw H/H_se for arbitrary T.
    auto pos=line.find(",g,g_se,");if(pos==std::string::npos)throw std::runtime_error("unexpected Bank header");
    line.replace(pos,8,",H,H_se,");normalized<<line<<",g,g_se";
    if(cfg.density>0)normalized<<",G,G_se";normalized<<'\n';
    while(std::getline(input,line)) {
      std::vector<std::string> fields;std::istringstream row(line);std::string v;
      while(std::getline(row,v,','))fields.push_back(v);
      double h=std::stod(fields.at(3)),se=std::stod(fields.at(4));
      double g=h/(kbt*kbt),gse=se/(kbt*kbt);
      if(!std::isfinite(g)||(chains>1&&!std::isfinite(gse)))throw std::runtime_error("stress normalization outside double range");
      normalized<<line<<','<<g<<','<<gse;
      if(cfg.density>0){double G=cfg.density*h/kbt,Gse=cfg.density*se/kbt;if(!std::isfinite(G)||(chains>1&&!std::isfinite(Gse)))throw std::runtime_error("intensive stress outside double range");normalized<<','<<G<<','<<Gse;}
      normalized<<'\n';
    }
    auto moments=file(out/"stress_moments.csv");moments<<"chain,frames";
    for(int a=0;a<6;++a)moments<<",mean"<<a;
    for(int a=0;a<6;++a)for(int b=0;b<6;++b)moments<<",raw"<<a<<b;
    moments<<'\n';
    for(std::size_t c=0;c<chains;++c){moments<<c<<','<<moment_frames;for(int a=0;a<6;++a)moments<<','<<(moment_frames?sum[c*6+a]/moment_frames:std::numeric_limits<double>::quiet_NaN());for(int a=0;a<36;++a)moments<<','<<(moment_frames?second[c*36+a]/moment_frames:std::numeric_limits<double>::quiet_NaN());moments<<'\n';}
    // Moments are raw products; these are not used to subtract trajectory means.
    if(dump.is_open())dump.close();
  }
};
}
