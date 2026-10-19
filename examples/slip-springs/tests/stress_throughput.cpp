// Isolated CPU benchmark: production Bank/CpuWorkers/KG mathematics are unchanged.
#include "../cpu_workers.h"
#include "chain_major_correlator.h"
#include <sys/resource.h>
#include <unistd.h>
#include <iostream>

using Clock=std::chrono::steady_clock;
static double elapsed(Clock::time_point t) {return std::chrono::duration<double>(Clock::now()-t).count();}
static double cpuSeconds() {
  rusage u{}; if(getrusage(RUSAGE_SELF,&u))throw std::runtime_error("getrusage failed");
  return u.ru_utime.tv_sec+u.ru_utime.tv_usec*1e-6+u.ru_stime.tv_sec+u.ru_stime.tv_usec*1e-6;
}
static std::size_t rss() {
  std::ifstream f("/proc/self/statm");std::size_t total=0,resident=0;
  if(!(f>>total>>resident))throw std::runtime_error("cannot read resident memory");
  return resident*std::size_t(sysconf(_SC_PAGESIZE));
}
static streaming::Sample prescribed(std::size_t f,std::size_t c,unsigned pattern) {
  // Exact dyadic inputs: identifiable chains, shared stretch/bend variation and cross terms.
  double a=(int((f*17+c*13)%101)-50)/64.;
  double b=(int((f*7+c*19)%67)-33)/64.;
  if(pattern==1){a=(int(c%11)-5)/16.;b=.25;}
  if(pattern==2){a=(f%2?-.5:.5);b=(f%4<2?-.25:.25);}
  const double offset=(int(c%11)-5)/32.;
  const double xx=1+a+.5*b+offset, yy=.5-.25*a+b, zz=.25+.125*a-.5*b;
  return {{.125+a+.25*b+offset,-.25+.5*a-b,.375-.25*a+.75*b,xx-yy,xx-zz,yy-zz}};
}
int main(int argc,char** argv) {
 try {
  if(argc!=11&&argc!=12)throw std::runtime_error("chains slots levels workers batch warm frames output-prefix pattern budget [frame|chain]");
  auto number=[](const char* x){std::string s(x);std::size_t end=0;auto v=std::stoull(s,&end);if(s.empty()||s[0]=='-'||end!=s.size())throw std::runtime_error("invalid integer");return v;};
  const auto c=number(argv[1]),p=number(argv[2]),l=number(argv[3]),w=number(argv[4]),batch=number(argv[5]),warm=number(argv[6]),frames=number(argv[7]),pattern=number(argv[9]);
  // Last argument is an explicit byte budget, capped at 1 GiB, never a silent resize.
  const auto budget=number(argv[10]);
  const std::string traversal=argc==12?argv[11]:"frame";
  if(traversal!="frame"&&traversal!="chain")throw std::runtime_error("traversal must be frame or chain");
  if(!c||c>2048||p>64||l>24||!w||w>8||!batch||batch>1024||warm>1024||!frames||frames>65537||pattern>2||budget>(1ULL<<30))throw std::runtime_error("benchmark bounds exceeded");
  streaming::Parameters cfg{unsigned(l),unsigned(p),2};cfg.validate();
  const std::size_t bankBytes=c*(streaming::OwnedCorrelator6::bytes(cfg)+sizeof(void*));
  if(bankBytes>budget)throw std::runtime_error("preflight: correlator allocation exceeds budget");
  const std::size_t baseline=rss();auto t=Clock::now();
  std::unique_ptr<streaming::Bank> frameBank;
  std::unique_ptr<chain_major::Bank> chainBank;
  if(traversal=="frame")frameBank=std::make_unique<streaming::Bank>(c,cfg,budget);
  else chainBank=std::make_unique<chain_major::Bank>(c,cfg,budget);
  const double init=elapsed(t);const auto bankRss=rss();t=Clock::now();
  std::unique_ptr<streaming::CpuWorkers> framePool;
  std::unique_ptr<chain_major::Workers> chainPool;
  if(traversal=="frame")framePool=std::make_unique<streaming::CpuWorkers>(*frameBank,c,unsigned(w));
  else chainPool=std::make_unique<chain_major::Workers>(*chainBank,c,unsigned(w));
  const double workerInit=elapsed(t);
  const std::size_t cycle=1024;
  t=Clock::now();std::vector<streaming::Sample> input(cycle*c);
  for(std::size_t f=0;f<cycle;++f)for(std::size_t chain=0;chain<c;++chain)input[f*c+chain]=prescribed(f,chain,unsigned(pattern));
  const double inputSeconds=elapsed(t);const auto allocatedRss=rss();
  std::size_t submissions=0;
  auto feed=[&](std::size_t first,std::size_t count){
    for(std::size_t n=0;n<count;){const auto start=(first+n)%cycle;const auto size=std::min({std::size_t(batch),count-n,cycle-start});
      if(framePool)framePool->consume(input.data()+start*c,size);else chainPool->consume(input.data()+start*c,size);n+=size;++submissions;}
  };
  t=Clock::now();feed(0,warm);const double warmSeconds=elapsed(t);
  const double previousWall=framePool?framePool->wall_seconds:chainPool->wall_seconds,previousBarrier=framePool?framePool->barrier_seconds:chainPool->barrier_seconds,previousWorker=framePool?framePool->aggregateSeconds():chainPool->aggregateSeconds();submissions=0;
  const auto cpuStart=cpuSeconds();t=Clock::now();feed(warm,frames);const double updates=elapsed(t),cpu=cpuSeconds()-cpuStart;
  const double poolWall=(framePool?framePool->wall_seconds:chainPool->wall_seconds)-previousWall,barrier=(framePool?framePool->barrier_seconds:chainPool->barrier_seconds)-previousBarrier,worker=(framePool?framePool->aggregateSeconds():chainPool->aggregateSeconds())-previousWorker;
  if((frameBank?frameBank->frames:chainBank->frames)!=warm+frames)throw std::runtime_error("omitted/duplicated frame count");
  t=Clock::now();if(frameBank)frameBank->write(std::string(argv[8])+".csv",1.);else chainBank->write(std::string(argv[8])+".csv",1.);const double evaluation=elapsed(t);
  t=Clock::now();framePool.reset();chainPool.reset();const double join=elapsed(t);t=Clock::now();frameBank.reset();chainBank.reset();const double teardown=elapsed(t);
  rusage usage{};getrusage(RUSAGE_SELF,&usage);
  std::ofstream out(std::string(argv[8])+".json");out.exceptions(std::ios::badbit|std::ios::failbit);out<<std::setprecision(17);
  out<<"{\"chains\":"<<c<<",\"slots\":"<<p<<",\"levels\":"<<l<<",\"workers\":"<<w<<",\"batch\":"<<batch<<",\"traversal\":\""<<traversal<<"\",\"warm_frames\":"<<warm<<",\"timed_frames\":"<<frames<<",\"total_frames\":"<<warm+frames<<",\"pattern\":"<<pattern
     <<",\"bank_bytes\":"<<bankBytes<<",\"input_bytes\":"<<input.size()*sizeof(streaming::Sample)<<",\"rss_baseline\":"<<baseline<<",\"rss_bank\":"<<bankRss<<",\"rss_allocated\":"<<allocatedRss<<",\"peak_rss_kib\":"<<usage.ru_maxrss
     <<",\"init_seconds\":"<<init<<",\"worker_init_seconds\":"<<workerInit<<",\"input_seconds\":"<<inputSeconds<<",\"warm_seconds\":"<<warmSeconds<<",\"update_seconds\":"<<updates<<",\"pool_wall_seconds\":"<<poolWall<<",\"barrier_seconds\":"<<barrier<<",\"aggregate_worker_seconds\":"<<worker<<",\"process_cpu_seconds\":"<<cpu
     <<",\"submissions\":"<<submissions<<",\"caller_outside_pool_seconds\":"<<updates-poolWall<<",\"evaluation_output_seconds\":"<<evaluation<<",\"worker_join_seconds\":"<<join<<",\"bank_teardown_seconds\":"<<teardown<<",\"chain_observations_per_second\":"<<double(c)*frames/updates<<",\"frames_per_second\":"<<frames/updates<<",\"cpu_core_equivalents\":"<<cpu/updates<<"}\n";
  std::cout<<"PASS chain observations/s="<<double(c)*frames/updates<<'\n';
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
