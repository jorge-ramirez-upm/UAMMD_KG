#include "../orientation_correlator.h"
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sys/resource.h>
#include <type_traits>

using orientation::Vector;
using orientation::Counter;
using Series=std::vector<std::vector<Vector>>;
using LVector=std::array<long double,3>;
void require(bool ok,const char* why) { if(!ok) throw std::runtime_error(why); }
double max_error=0;std::size_t compared_bins=0;
void close(double got,long double expected) {
  const double error=std::abs(got-double(expected));max_error=std::max(max_error,error);
  if(error>3e-11+3e-11*std::abs(expected)) throw std::runtime_error("direct orientation comparison failed");
}
template<class F> void rejects(F f) {
  bool bad=false;try {f();} catch(const std::exception&) {bad=true;}
  require(bad,"invalid orientation input accepted");
}
LVector independent_unit(Vector r) {
  long double length=0;for(double x:r) length+=static_cast<long double>(x)*x;
  length=std::sqrt(length);
  return {{r[0]/length,r[1]/length,r[2]/length}};
}
long double dot(const LVector& a,const LVector& b) {
  long double r=0;for(int d=0;d<3;++d) r+=a[d]*b[d];return r;
}
std::pair<long double,long double> mean_se(const std::vector<long double>& data) {
  long double mean=0,variance=0;for(auto x:data) mean+=x/data.size();
  for(auto x:data) variance+=(x-mean)*(x-mean);
  return {mean,data.size()>1?std::sqrt(variance/(data.size()-1)/data.size()):0};
}
struct Grid {Counter lag,block,origins;};
std::vector<Grid> grid(Counter frames,orientation::Parameters cfg) {
  std::vector<Grid> out;Counter deepest=0,capacity=1;
  while(deepest+1<cfg.levels && capacity*cfg.coarsening<=frames) {++deepest;capacity*=cfg.coarsening;}
  for(Counter j=0;j<cfg.slots && j<frames;++j) out.push_back({j,1,frames-j});
  Counter block=1;
  for(Counter k=1;k<deepest;++k) {
    block*=cfg.coarsening;
    for(Counter j=cfg.slots/cfg.coarsening;j<cfg.slots && j<frames/block;++j)
      out.push_back({j*block,block,frames/block-j});
  }
  return out;
}
void verify(const Series& data,orientation::Parameters cfg,bool second=true) {
  const orientation::Clock clock{17,20,.000025};
  orientation::Bank bank(data[0].size(),cfg,clock,second);
  require(bank.evaluate().bins.empty(),"empty bank exports data");
  for(std::size_t f=0;f<data.size();++f) bank.observe(clock.first_step+f*clock.stride,data[f]);
  auto result=bank.evaluate();auto again=bank.evaluate();const auto expected=grid(data.size(),cfg);
  require(result.bins.size()==expected.size() && again.bins.size()==expected.size(),"wrong exported bin count");
  require(result.metadata.frames==data.size() && result.metadata.last_step==17+(data.size()-1)*20,"wrong acquisition metadata");
  require(result.metadata.clock.first_step==17 && result.metadata.clock.stride==20 && result.metadata.second_rank==second,"wrong clock/rank metadata");
  std::vector<std::vector<LVector>> units(data.size());
  for(std::size_t t=0;t<data.size();++t) for(auto r:data[t]) units[t].push_back(independent_unit(r));
  for(std::size_t i=0;i<expected.size();++i) {
    auto e=expected[i];const auto& b=result.bins[i];
    require(b.lag_samples==e.lag && b.block_samples==e.block && b.origins_per_chain==e.origins,"wrong lag/block/origin");
    require(b.lag_steps==e.lag*20 && b.independent_chains==data[0].size(),"wrong step/chain metadata");
    close(b.lag_time,e.lag*20*.000025L);close(b.block_duration,e.block*20*.000025L);
    std::vector<long double> c1,c2;
    for(std::size_t c=0;c<data[0].size();++c) {
      long double a=0,z=0;
      for(Counter origin=0;origin<e.origins;++origin)
        for(Counter s=0;s<e.block;++s) for(Counter t=0;t<e.block;++t) {
          const auto value=dot(units[origin*e.block+s][c],units[origin*e.block+e.lag+t][c]);
          a+=value;z+=(3*value*value-1)/2;
        }
      const long double denominator=static_cast<long double>(e.origins)*e.block*e.block;
      c1.push_back(a/denominator);c2.push_back(z/denominator);
    }
    const auto a=mean_se(c1),z=mean_se(c2);close(b.c1.mean,a.first);close(again.bins[i].c1.mean,b.c1.mean);
    if(c1.size()==1) require(!b.c1.standard_error,"one chain reports independent-chain SE");
    else close(*b.c1.standard_error,a.second);
    require(bool(b.c2)==second,"wrong optional second rank");
    if(second) {
      close(b.c2->mean,z.first);close(again.bins[i].c2->mean,b.c2->mean);
      if(c2.size()==1) require(!b.c2->standard_error,"one chain reports C2 SE");
      else close(*b.c2->standard_error,z.second);
    }
    ++compared_bins;
  }
  close(result.bins[0].c1.mean,1);if(second) close(result.bins[0].c2->mean,1);
}
Series prescribed(std::size_t frames,std::size_t chains,int kind) {
  Series data(frames,std::vector<Vector>(chains));const double phi=(1+std::sqrt(5.))/2;
  std::vector<Vector> isotropic;
  for(double a:{-1.,1.}) for(double b:{-1.,1.}) {
    isotropic.push_back({{0,a,b*phi}});isotropic.push_back({{a,b*phi,0}});isotropic.push_back({{b*phi,0,a}});
  }
  for(std::size_t f=0;f<frames;++f) for(std::size_t c=0;c<chains;++c) {
    Vector v{};
    if(kind==0) v={{2,-3,4}};
    else if(kind==1) v={{f%2?-1.:1.,0,0}};
    else if(kind==2) {const Vector axes[]={{{1,0,0}},{{0,1,0}},{{-1,0,0}},{{0,-1,0}}};v=axes[(f+c)%4];}
    else if(kind==3) v=isotropic[(f+c)%isotropic.size()];
    else if(kind==4) v={{.2*std::cos(.2*f+c),.2*std::sin(.2*f+c),1}};
    else v={{std::sin(.17*f+.43*c)+.2,std::cos(.13*f+.31*c)-.3,std::sin(.07*f+.51*c)+.1}};
    const double scale=1+double((f+3*c)%5);for(auto& x:v) x*=scale;
    data[f][c]=v;
  }
  return data;
}
void tests() {
  static_assert(!std::is_copy_constructible<orientation::OwnedVector>::value);
  static_assert(!std::is_move_constructible<orientation::OwnedVector>::value);
  static_assert(!std::is_copy_constructible<orientation::Bank>::value);
  static_assert(!std::is_move_constructible<orientation::Bank>::value);
  for(int kind=0;kind<6;++kind) for(std::size_t chains:{1,3,7}) {
    verify(prescribed(65,chains,kind),{6,8,2});
    verify(prescribed(31,chains,kind),{5,12,3},false);
  }
  for(std::size_t frames:{1,2,7,8,17,64,129,513}) verify(prescribed(frames,4,5),{8,16,2});
  auto isotropic=prescribed(72,1,3);LVector mean{};long double moment[3][3]{};
  for(const auto& frame:isotropic) {
    auto u=independent_unit(frame[0]);
    for(int i=0;i<3;++i) {mean[i]+=u[i]/isotropic.size();for(int j=0;j<3;++j) moment[i][j]+=u[i]*u[j]/isotropic.size();}
  }
  for(int i=0;i<3;++i) {close(double(mean[i]),0);for(int j=0;j<3;++j) close(double(moment[i][j]),i==j?1.L/3:0);}
  verify(isotropic,{6,8,2});
  for(auto cfg:{orientation::Parameters{20,32,2},orientation::Parameters{20,64,2}})
    verify(prescribed(257,3,5),cfg);
  // Scalar Legendre evaluation is independent of the tensor feature representation.
  auto data=prescribed(257,1,5);
  for(std::size_t i=1;i<data.size();++i) {
    auto u=independent_unit(data[i][0]),v=independent_unit(data[i-1][0]);
    Vector a{{double(u[0]),double(u[1]),double(u[2])}},b{{double(v[0]),double(v[1]),double(v[2])}};
    auto fa=orientation::rank2(a),fb=orientation::rank2(b);double value=0;
    for(int k=0;k<5;++k) value+=fa[k]*fb[k];
    close(value,(3*dot(u,v)*dot(u,v)-1)/2);
  }
  orientation::Bank covariance(3,{4,8,2},{0,1,1});
  covariance.observe(0,{{{1,0,0}},{{0,0,1}},{{1,1,1}}});
  const auto paired=covariance.evaluate().bins[0];
  close(paired.c2->mean,1);close(*paired.c2->standard_error,0);
  const auto separate=mean_se({0,0,1});
  require(std::sqrt(2.)*double(separate.second)>.4,"covariance fixture is not discriminating");
  orientation::Bank antiparallel(1,{3,8,2},{0,1,1});
  for(Counter f=0;f<17;++f) antiparallel.observe(f,{{{f%2?-1.:1.,0,0}}});
  auto curves=antiparallel.evaluate();close(curves.bins[1].c1.mean,-1);close(curves.bins[1].c2->mean,1);
  orientation::Bank orthogonal(1,{3,8,2},{0,1,1});
  orthogonal.observe(0,{{{1,0,0}}});orthogonal.observe(1,{{{0,1,0}}});
  curves=orthogonal.evaluate();close(curves.bins[1].c1.mean,0);close(curves.bins[1].c2->mean,-.5);
  orientation::Bank atomic(3,{4,8,2},{5,2,.1});
  auto valid=prescribed(1,3,0)[0];
  for(auto invalid:{Vector{{0,0,0}},Vector{{INFINITY,0,0}},Vector{{0,NAN,0}},Vector{{0,0,-INFINITY}}}) {
    auto bad=valid;bad[2]=invalid;rejects([&]{atomic.observe(5,bad);});
    require(atomic.frames()==0 && atomic.evaluate().bins.empty(),"partially accepted invalid frame");
  }
  rejects([&]{atomic.observe(4,valid);});rejects([&]{atomic.observe(5,{{{1,0,0}}});});
  atomic.observe(5,valid);rejects([&]{atomic.observe(5,valid);});rejects([&]{atomic.observe(9,valid);});
  require(atomic.frames()==1,"invalid step changed clock");atomic.observe(7,valid);
  for(auto cfg:{orientation::Parameters{0,8,2},orientation::Parameters{4,7,2},orientation::Parameters{49,8,2}})
    rejects([&]{orientation::Bank b(2,cfg,{0,1,1});});
  for(auto clock:{orientation::Clock{0,0,1},orientation::Clock{0,1,0},orientation::Clock{0,1,NAN},orientation::Clock{0,1,INFINITY},orientation::Clock{0,Counter(-1),1}})
    rejects([&]{orientation::Bank b(2,{4,8,2},clock);});
  rejects([]{orientation::Bank b(0,{4,8,2},{0,1,1});});
  rejects([]{orientation::Bank b(2048,{20,64,2},{0,1,.1},true,1);});
  rejects([]{orientation::Bank::estimated_bytes(std::size_t(-1),{20,64,2});});
  orientation::Bank overflow(1,{3,8,2},{Counter(-1),1,1});overflow.observe(Counter(-1),{{{1,0,0}}});
  rejects([&]{overflow.observe(0,{{{1,0,0}}});});require(overflow.frames()==1,"overflow mutated clock");
  for(Vector extreme: {Vector{{std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),0}},
                       Vector{{std::numeric_limits<double>::denorm_min(),0,0}}}) {
    orientation::Bank b(1,{4,8,2},{0,1,1});b.observe(0,{extreme});close(b.evaluate().bins[0].c1.mean,1);close(b.evaluate().bins[0].c2->mean,1);
  }
  for(int repeat=0;repeat<100;++repeat) {
    orientation::OwnedVector v({4,8,2});
    for(int f=0;f<35;++f) v.push({{1,2,3}});
    v.evaluate();require(v.origins(0)==35,"owner origin count");close(v.value(0),14);
    v.clear();for(int f=0;f<17;++f) v.push({{2,3,4}});
    v.evaluate();require(v.origins(0)==17,"clear retained origins");close(v.value(0),29);
    rejects([&]{v.push({{-1e10,0,0}});});rejects([&]{v.push({{1,0,NAN}});});
    orientation::Bank b(3,{4,8,2},{0,1,1});b.observe(0,valid);b.evaluate();
  }
  std::cout<<"PASS direct bins="<<compared_bins<<" max_absolute_error="<<std::setprecision(17)<<max_error
           <<"; C1/C2, paired SE, clocks, invalid-frame atomicity, clear, overflow, lifetime\n";
}
using Steady=std::chrono::steady_clock;
double elapsed(Steady::time_point start) {return std::chrono::duration<double>(Steady::now()-start).count();}
long peak() {rusage r{};if(getrusage(RUSAGE_SELF,&r)) throw std::runtime_error("getrusage failed");return r.ru_maxrss;}
long rss() {
  std::ifstream f("/proc/self/status");std::string line;
  while(std::getline(f,line)) if(line.rfind("VmRSS:",0)==0) return std::stol(line.substr(6));
  throw std::runtime_error("Linux VmRSS unavailable");
}
void benchmark(std::size_t chains,unsigned slots,bool second) {
  const orientation::Parameters cfg{20,slots,2};const orientation::Clock clock{0,20,.000025};
  auto input=prescribed(8,chains,5);const auto baseline=rss(),baseline_peak=peak();
  auto t=Steady::now();auto bank=std::make_unique<orientation::Bank>(chains,cfg,clock,second);double allocation=elapsed(t);
  const auto allocated=rss();
  for(Counter f=0;f<128;++f) bank->observe(f*20,input[f%input.size()]);
  constexpr Counter frames=512;t=Steady::now();
  for(Counter f=128;f<128+frames;++f) bank->observe(f*20,input[f%input.size()]);
  double processing=elapsed(t);t=Steady::now();const auto result=bank->evaluate();double evaluation=elapsed(t);
  require(!result.bins.empty() && std::isfinite(result.bins.back().c1.mean),"benchmark evaluation failed");
  const long maximum=peak();t=Steady::now();bank.reset();double teardown=elapsed(t);
  std::cout<<std::setprecision(17)<<"{\"chains\":"<<chains<<",\"slots\":"<<slots<<",\"levels\":20,\"second_rank\":"<<(second?"true":"false")
           <<",\"frames_timed\":"<<frames<<",\"warmup_frames\":128,\"observations_timed\":"<<chains*frames
           <<",\"allocation_seconds\":"<<allocation<<",\"processing_seconds\":"<<processing<<",\"evaluation_seconds\":"<<evaluation
           <<",\"teardown_seconds\":"<<teardown<<",\"observations_per_second\":"<<chains*frames/processing
           <<",\"estimated_bytes\":"<<orientation::Bank::estimated_bytes(chains,cfg,second)
           <<",\"array_payload_bytes\":"<<chains*(second?3:1)*orientation::OwnedVector::payload_bytes(cfg)
           <<",\"baseline_rss_kib\":"<<baseline<<",\"baseline_peak_rss_kib\":"<<baseline_peak
           <<",\"allocated_rss_kib\":"<<allocated<<",\"peak_rss_kib\":"<<maximum<<",\"post_teardown_rss_kib\":"<<rss()<<"}\n";
}
void memory_cycles() {
  auto input=prescribed(1,2048,5)[0];
  std::cout<<"[";
  for(int cycle=0;cycle<3;++cycle) {
    auto bank=std::make_unique<orientation::Bank>(2048,orientation::Parameters{20,64,2},orientation::Clock{0,1,1});
    for(Counter f=0;f<128;++f) bank->observe(f,input);
    bank->evaluate();auto resident=rss();bank.reset();
    std::cout<<(cycle?",":"")<<"{\"cycle\":"<<cycle<<",\"allocated_rss_kib\":"<<resident
             <<",\"post_teardown_rss_kib\":"<<rss()<<",\"peak_rss_kib\":"<<peak()<<"}";
  }
  std::cout<<"]\n";
}
int main(int argc,char** argv) {
  try {
    if(argc==1) tests();
    else if(argc==2 && std::string(argv[1])=="--memory-cycles") memory_cycles();
    else if(argc==5 && std::string(argv[1])=="--benchmark") {
      auto chains=std::stoull(argv[2]);auto slots=std::stoul(argv[3]);auto second=std::stoul(argv[4]);
      require(chains>0 && chains<=2048 && (slots==32 || slots==64) && second<=1,"invalid bounded benchmark dimensions");
      benchmark(chains,unsigned(slots),bool(second));
    } else throw std::runtime_error("usage: orientation_cpu [--benchmark chains slots second_rank | --memory-cycles]");
    return 0;
  } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
