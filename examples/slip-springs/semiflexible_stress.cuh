#pragma once
#include "semiflexible.cuh"
#include "semiflexible_stress_stream.h"
#include <thrust/device_vector.h>

namespace stress3b {
using namespace uammd;
using semiflexible::check;
using Counter=semiflexible::Counter;
struct Tensor { double w[9]; double scale; };
__device__ inline void error(Counter* key,int bead,int code){atomicMin(key,Counter(bead)*16+code);}
__device__ inline double3 bond(const real4* p,int i){return make_double3(double(p[i+1].x)-double(p[i].x),double(p[i+1].y)-double(p[i].y),double(p[i+1].z)-double(p[i].z));}
__device__ inline double bondLength(double3 q){return hypot(hypot(q.x,q.y),q.z);}
__device__ inline bool valid(Tensor w){for(int a=0;a<9;++a)if(!isfinite(w.w[a]))return false;return isfinite(w.scale);}
__global__ void stretchTensor(const real4* p,Tensor* out,const real2* params,int chains,int m,Counter* key){
  int c=blockIdx.x*blockDim.x+threadIdx.x;if(c>=chains)return;Tensor w{};
  for(int i=0;i<m-1;++i){
    double3 q=bond(p,c*m+i);double l=bondLength(q),b0=params[i].x,k=params[i].y;
    if(!isfinite(l)||(l==0&&b0!=0)){error(key,c*m+i,1);continue;}
    double v[3]={q.x,q.y,q.z};double factor=l==0?k:k*(1-b0/l);
    for(int a=0;a<3;++a)for(int b=0;b<3;++b)w.w[a*3+b]+=(factor*v[a])*v[b];
    w.scale+=fabs(factor)*l*l;
  }
  if(!valid(w))error(key,c*m,2);out[c]=w;
}
__global__ void bendTensor(const real4* p,Tensor* total,Tensor* diagnostic,const real* kappa,int chains,int m,Counter* key){
  int c=blockIdx.x*blockDim.x+threadIdx.x;if(c>=chains)return;Tensor w{};
  for(int i=1;i<m-1;++i){
    double k=kappa[i];if(k==0)continue;
    double3 a=bond(p,c*m+i-1),b=bond(p,c*m+i);double la=bondLength(a),lb=bondLength(b);
    if(!(la>0&&lb>0&&isfinite(la)&&isfinite(lb))){error(key,c*m+i,3);continue;}
    double u[3]={a.x/la,a.y/la,a.z/la},v[3]={b.x/lb,b.y/lb,b.z/lb};double cosine=0;
    for(int d=0;d<3;++d)cosine+=u[d]*v[d];Tensor angle{};
    for(int x=0;x<3;++x)for(int y=0;y<3;++y)angle.w[x*3+y]=k*(cosine*(u[x]*u[y]+v[x]*v[y])-u[x]*v[y]-v[x]*u[y]);
    double tol=128*2.2204460492503131e-16*fmax(1.,k);
    if(!valid(angle))error(key,c*m+i,4);
    for(int x=0;x<3;++x)for(int y=0;y<3;++y)if(fabs(angle.w[x*3+y]-angle.w[y*3+x])>tol)error(key,c*m+i,5);
    if(fabs(angle.w[0]+angle.w[4]+angle.w[8])>3*tol)error(key,c*m+i,6);
    for(int d=0;d<9;++d)w.w[d]+=angle.w[d];w.scale+=4*fabs(k);
  }
  if(!valid(w))error(key,c*m,4);
  if(diagnostic)diagnostic[c]=w;
  for(int d=0;d<9;++d)total[c].w[d]+=w.w[d];total[c].scale+=w.scale;
}
__global__ void channels(const Tensor* total,streaming::Sample* out,int chains,int m,Counter* key){
  int c=blockIdx.x*blockDim.x+threadIdx.x;if(c>=chains)return;Tensor w=total[c];double scale=fmax(1.,w.scale);
  for(int d=0;d<9;++d)scale=fmax(scale,fabs(w.w[d]));
  for(int a=0;a<3;++a)for(int b=0;b<3;++b)if(fabs(w.w[a*3+b]-w.w[b*3+a])>128*2.2204460492503131e-16*scale)error(key,c*m,5);
  if(!valid(w))error(key,c*m,4);
  out[c]={{w.w[1],w.w[2],w.w[5],w.w[0]-w.w[4],w.w[0]-w.w[8],w.w[4]-w.w[8]}};
  for(int a=0;a<6;++a)if(!isfinite(out[c].v[a]))error(key,c*m,4);
}

class Observer {
  Settings cfg;int chains,m;double spacing,kbt;Counter seed,momentStart;std::filesystem::path output;
  const real2* parameters;const real* kappa;bool active;
  thrust::device_vector<Tensor> tensors,diagnosticBend;
  thrust::device_vector<streaming::Sample> samples;
  thrust::device_vector<Counter> key;
  streaming::Sample* batch=nullptr;
  std::unique_ptr<Correlations> correlations;
  std::unique_ptr<EveryStepTransport> every;
  std::size_t fill=0;cudaEvent_t start=nullptr,stop=nullptr;
  std::ofstream diagnostics;
  double gpu_seconds=0,transfer_seconds=0,diagnostic_seconds=0,diagnostic_output_seconds=0,final_seconds=0;
  Counter frames=0,stretch_launches=0,bend_launches=0;
  template<class T> static T* ptr(thrust::device_vector<T>& v){return thrust::raw_pointer_cast(v.data());}
  static double elapsed(std::chrono::steady_clock::time_point t){return std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();}
  void failure(const real4* positions,Counter step){
    Counter value;check(cudaMemcpy(&value,ptr(key),sizeof(value),cudaMemcpyDeviceToHost),"stress diagnostic");
    if(value==~Counter(0))return;
    auto f=file(output/"stress_failure.json");f<<"{\"step\":"<<step<<",\"seed\":"<<seed<<",\"flat_bead\":"<<value/16<<",\"reason\":"<<value%16<<"}\n";
    std::vector<real4> snapshot(std::size_t(chains)*m);check(cudaMemcpy(snapshot.data(),positions,snapshot.size()*sizeof(real4),cudaMemcpyDeviceToHost),"stress failed geometry");
    auto geometry=file(output/"stress_failure_positions.csv");geometry<<"chain,bead,x,y,z\n";
    for(std::size_t i=0;i<snapshot.size();++i)geometry<<i/m<<','<<i%m<<','<<snapshot[i].x<<','<<snapshot[i].y<<','<<snapshot[i].z<<'\n';
    throw std::runtime_error("stress failure at step "+std::to_string(step)+", bead "+std::to_string(value/16)+", reason "+std::to_string(value%16));
  }
public:
  static std::size_t estimatedBytes(Settings s,std::size_t c,bool active){return s.hostBytes(c)+c*(sizeof(Tensor)+sizeof(streaming::Sample)+(active&&s.mode=="diagnostic"?sizeof(Tensor):0)+(s.everyStep()?2*std::size_t(s.batch)*sizeof(streaming::Sample):0))+sizeof(Counter);}
  Observer(Settings s,int c,int beads,const real2* parameters,const real* kappa,bool active,double spacing,double kbt,Counter seed,Counter momentStart,const std::filesystem::path& out)
   :cfg(s),chains(c),m(beads),spacing(spacing),kbt(kbt),seed(seed),momentStart(momentStart),output(out),parameters(parameters),kappa(kappa),active(active),tensors(c),diagnosticBend(active&&s.mode=="diagnostic"?c:0),samples(c),key(1,~Counter(0)){
    if(cfg.streaming()){
      correlations=std::make_unique<Correlations>(cfg,c,out,momentStart);
      check(cudaMallocHost(&batch,std::size_t(cfg.batch)*c*sizeof(streaming::Sample)),"pinned stress batch");
    }else if(cfg.everyStep()){
      every=std::make_unique<EveryStepTransport>(c,cfg.batch,cfg.correlation,std::size_t(cfg.correlatorMiB)*1024*1024,cfg.workers,momentStart);
    }else{
      diagnostics=file(out/"stress_tensors.csv");diagnostics<<"step,chain,term";
      for(int a=0;a<3;++a)for(int b=0;b<3;++b)diagnostics<<",w"<<a<<b;diagnostics<<'\n';
    }
    check(cudaEventCreate(&start),"stress event");check(cudaEventCreate(&stop),"stress event");
  }
  ~Observer(){cudaDeviceSynchronize();if(batch)cudaFreeHost(batch);if(start)cudaEventDestroy(start);if(stop)cudaEventDestroy(stop);}
  void sample(const real4* positions,Counter step){
    check(cudaEventRecord(start),"stress start");
    stretchTensor<<<(chains+127)/128,128>>>(positions,ptr(tensors),parameters,chains,m,ptr(key));++stretch_launches;
    auto stamp=[&](){check(cudaEventRecord(stop),"stress stop");auto waitStart=std::chrono::steady_clock::now();check(cudaEventSynchronize(stop),"stress wait");diagnostic_seconds+=elapsed(waitStart);float ms;check(cudaEventElapsedTime(&ms,start,stop),"stress elapsed");gpu_seconds+=ms/1000.;};
    std::vector<Tensor> stretch;
    if(!cfg.correlating()){
      stamp();auto transferStart=std::chrono::steady_clock::now();
      stretch.resize(chains);check(cudaMemcpy(stretch.data(),ptr(tensors),chains*sizeof(Tensor),cudaMemcpyDeviceToHost),"stretch diagnostic readback");
      transfer_seconds+=elapsed(transferStart);check(cudaEventRecord(start),"stress diagnostic restart");
    }
    if(active){bendTensor<<<(chains+127)/128,128>>>(positions,ptr(tensors),ptr(diagnosticBend),kappa,chains,m,ptr(key));++bend_launches;}
    streaming::Sample* output=every?every->destination():ptr(samples);
    channels<<<(chains+127)/128,128>>>(ptr(tensors),output,chains,m,ptr(key));
    check(cudaGetLastError(),"stress launch");stamp();
    auto t=std::chrono::steady_clock::now();failure(positions,step);diagnostic_seconds+=elapsed(t);
    t=std::chrono::steady_clock::now();
    if(cfg.streaming()){
      auto* destination=batch+fill*std::size_t(chains);
      check(cudaMemcpy(destination,ptr(samples),chains*sizeof(streaming::Sample),cudaMemcpyDeviceToHost),"stress channel D2H");transfer_seconds+=elapsed(t);
      correlations->received(destination,step);++fill;
      if(fill==cfg.batch){correlations->consume(batch,fill);fill=0;}
    }else if(every){
      every->published();
    }else{
      std::vector<Tensor> total(chains),bend(chains);
      check(cudaMemcpy(total.data(),ptr(tensors),chains*sizeof(Tensor),cudaMemcpyDeviceToHost),"total diagnostic readback");
      if(active)check(cudaMemcpy(bend.data(),ptr(diagnosticBend),chains*sizeof(Tensor),cudaMemcpyDeviceToHost),"bend diagnostic readback");
      transfer_seconds+=elapsed(t);
      t=std::chrono::steady_clock::now();
      for(int c=0;c<chains;++c){const Tensor values[]={stretch[c],bend[c],total[c]};const char* names[]={"stretch","bend","total"};for(int term=0;term<3;++term){diagnostics<<step<<','<<c<<','<<names[term];for(double x:values[term].w)diagnostics<<','<<x;diagnostics<<'\n';}}
      diagnostics.flush();diagnostic_output_seconds+=elapsed(t);
    }
    ++frames;
  }
  void finish(){if(correlations&&fill){correlations->consume(batch,fill);fill=0;}if(correlations&&correlations->frames!=frames)throw std::runtime_error("stress sample accounting mismatch");if(every)every->finish();}
  void write(){
    auto t=std::chrono::steady_clock::now();
    if(correlations)correlations->write(output,spacing,kbt);
    if(every){
      every->write((output/"stress_correlations_raw.csv").string(),spacing);every->writeMoments(output/"stress_moments.csv");
      std::ifstream input(output/"stress_correlations_raw.csv");if(!input)throw std::runtime_error("cannot read every-step raw correlations");std::string line;std::getline(input,line);auto normalized=file(output/"stress_correlations.csv");auto pos=line.find(",g,g_se,");if(pos==std::string::npos)throw std::runtime_error("unexpected every-step correlation header");line.replace(pos,8,",H,H_se,");normalized<<line<<",g,g_se";if(cfg.density>0)normalized<<",G,G_se";normalized<<'\n';while(std::getline(input,line)){std::vector<std::string> fields;std::istringstream row(line);std::string v;while(std::getline(row,v,','))fields.push_back(v);double h=std::stod(fields.at(3)),se=std::stod(fields.at(4));normalized<<line<<','<<h/(kbt*kbt)<<','<<se/(kbt*kbt);if(cfg.density>0)normalized<<','<<cfg.density*h/kbt<<','<<cfg.density*se/kbt;normalized<<'\n';}
    }if(diagnostics.is_open())diagnostics.close();final_seconds=elapsed(t);
    auto f=file(output/"stress_metadata.json");
    f<<"{\"mode\":\""<<cfg.mode<<"\",\"frames\":"<<frames<<",\"spacing\":"<<spacing<<",\"kbt\":"<<kbt<<",\"chain_density\":";
    if(cfg.density>0)f<<cfg.density;else f<<"null";
    f<<",\"moment_start_step\":"<<momentStart<<",\"moment_frames\":"<<(correlations?correlations->moment_frames:(every?every->momentFrames():0))<<",\"raw_connected\":false,\"empirical_mean_subtraction\":false,\"batch\":"<<cfg.batch<<",\"cpu_workers\":"<<(correlations?correlations->workers().size():(every?every->cpu().size():0))
     <<",\"levels\":"<<cfg.correlation.levels<<",\"slots\":"<<cfg.correlation.slots<<",\"coarsening\":"<<cfg.correlation.coarsening
     <<",\"active_bending\":"<<(active?"true":"false")<<",\"gpu_stress_bytes\":"<<(tensors.capacity()*sizeof(Tensor)+diagnosticBend.capacity()*sizeof(Tensor)+samples.capacity()*sizeof(streaming::Sample)+sizeof(Counter)+(every?every->deviceBytes():0))<<",\"host_stress_batch_bytes\":"<<(cfg.streaming()?std::size_t(cfg.batch)*chains*sizeof(streaming::Sample):(every?every->hostBytes():0))<<",\"bending_stress_device_bytes\":"<<diagnosticBend.capacity()*sizeof(Tensor)<<",\"bending_stress_launches\":"<<bend_launches<<",\"stretch_stress_launches\":"<<stretch_launches
     <<",\"gpu_stress_seconds\":"<<gpu_seconds<<",\"stress_transfer_seconds\":"<<(every?every->transfer_seconds:transfer_seconds)<<",\"stress_transfer_completion_wait_seconds\":"<<(every?every->transfer_completion_wait_seconds:0)<<",\"stress_transfer_bytes\":"<<(every?every->transfer_bytes:0)<<",\"stress_consumer_idle_seconds\":"<<(every?every->consumer_idle_seconds:0)<<",\"stress_diagnostic_wait_seconds\":"<<diagnostic_seconds
     <<",\"cpu_correlation_seconds\":"<<(correlations?correlations->workers().wall_seconds:(every?every->cpu().wall_seconds:0))<<",\"cpu_barrier_seconds\":"<<(correlations?correlations->workers().barrier_seconds:(every?every->cpu().barrier_seconds:0))
     <<",\"cpu_worker_execution_sum_seconds\":"<<(correlations?correlations->workers().aggregateSeconds():(every?every->cpu().aggregateSeconds():0))<<",\"stress_output_and_moments_seconds\":"<<(correlations?correlations->output_seconds:0)
     <<",\"diagnostic_output_seconds\":"<<diagnostic_output_seconds<<",\"buffer_wait_seconds\":"<<(every?every->buffer_wait_seconds:0)<<",\"producer_blocked_seconds\":"<<(every?every->producer_blocked_seconds:0)<<",\"queue_slot_capacity\":"<<(every?every->slotCapacity():0)<<",\"max_inflight_slots\":"<<(every?every->max_inflight_slots:0)<<",\"finalization_output_seconds\":"<<final_seconds<<",\"estimated_bytes\":"<<estimatedBytes(cfg,chains,active)
     <<",\"estimator\":\"raw products of nonoverlapping block means; no empirical mean subtraction; terminal incomplete blocks not padded; deepest level not exported\",\"buffer_mode\":\""<<(every?"two-slot asynchronous D2H with chain-major CPU workers":"synchronous D2H and persistent CPU workers; no asynchronous buffer queue")<<"\"}\n";
    std::cout<<"stress frames="<<frames<<" gpu_s="<<gpu_seconds<<" D2H_s="<<transfer_seconds<<" cpu_s="<<(correlations?correlations->workers().wall_seconds:0)<<" final_s="<<final_seconds<<'\n';
  }
};
}
