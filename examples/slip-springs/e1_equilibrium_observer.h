#pragma once
// Host-only read-only serializer. No CUDA, dynamics or RNG dependency.
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace e1_observer {
using Step=std::uint64_t;
using Vec=std::array<double,3>;
inline void require(bool ok,const char* why) {if(!ok)throw std::runtime_error(why);}
inline Step readStep(const std::string& token) {
  require(!token.empty()&&token.find_first_not_of("0123456789")==std::string::npos,"equilibrium schedule requires integer steps, not times");
  size_t used=0;auto value=std::stoull(token,&used);require(used==token.size(),"invalid equilibrium step");return value;
}
// Validate once, then stream from the same open file; memory does not grow with frames.
class Schedule {
  std::ifstream file;
  Step next_=0,count_=0,consumed_=0,last_=0;
  Step expectedHash=14695981039346656037ULL,actualHash=14695981039346656037ULL;
  static Step hash(Step h,Step value){for(int i=0;i<8;++i){h^=(value>>(8*i))&255;h*=1099511628211ULL;}return h;}
public:
  Schedule(const std::filesystem::path& path,Step end,const std::vector<Step>& snapshots):file(path) {
    require(bool(file),"cannot open equilibrium schedule");
    std::string token;Step previous=0;size_t found=0;
    while(file>>token) {
      Step step=readStep(token);
      require(step<=end&&(count_?step>previous:step==0),"equilibrium steps must start at zero, be sorted, unique and in range");
      if(found<snapshots.size()&&step==snapshots[found])++found;
      expectedHash=hash(expectedHash,step);previous=step;++count_;
    }
    require(!file.bad()&&count_&&previous==end&&found==snapshots.size(),"equilibrium schedule must include final step and every snapshot");
    file.clear();file.seekg(0);require(bool(file),"cannot rewind equilibrium schedule");
    require(bool(file>>token),"empty equilibrium schedule");next_=readStep(token);
  }
  bool due(Step step) const {return consumed_<count_&&step==next_;}
  Step count()const{return count_;}
  void consume(Step step) {
    require(due(step)&&(consumed_==0||step>last_),"missing, repeated or inconsistent equilibrium frame");
    actualHash=hash(actualHash,step);last_=step;++consumed_;std::string token;
    if(consumed_<count_) {
      require(bool(file>>token),"truncated equilibrium schedule");next_=readStep(token);
      require(next_>step,"equilibrium schedule changed during execution");
    } else require(!(file>>token)&&!file.bad()&&actualHash==expectedHash,"equilibrium schedule changed during execution");
  }
  bool complete()const{return consumed_==count_;}
};
inline std::vector<Step> snapshotSteps(const std::filesystem::path& path,Step end) {
  std::vector<Step> result;
  if(path.empty())return end?std::vector<Step>{0,end}:std::vector<Step>{0};
  std::ifstream f(path);require(bool(f),"cannot open equilibrium snapshot schedule");std::string token;
  while(f>>token) {
    auto step=readStep(token);require(result.size()<8&&step<=end&&(result.empty()?step==0:step>result.back()),"snapshot steps must start at zero, be sorted, unique, in range, at most eight");result.push_back(step);
  }
  require(!f.bad()&&!result.empty()&&result.back()==end,"snapshot schedule must include initial and final steps");return result;
}
struct Slot {Vec anchor;int site,chain,previous,next;};
// Same order/meaning as the accepted counters, with canonical boundary proposals
// kept distinct from occupied-renewal rejections.
using Counts=std::array<Step,11>;
inline const char* counterNames="batches,attempts,accepted,boundary,occupied,metropolis,renewal_proposed,renewal_accepted,renewal_occupied,renewal_same_chain,renewal_cross_chain";
inline void checkCounts(const Counts& x,bool canonical) {
  // Subtraction avoids overflowing sums when checking corrupt input.
  Step rest=x[1];for(int i:{2,3,4,5}){require(x[i]<=rest,"inconsistent hopping counters");rest-=x[i];}require(rest==0,"inconsistent attempt total");
  require(x[7]<=x[6]&&x[8]==x[6]-x[7],"inconsistent renewal counters");
  require(x[9]<=x[7]&&x[10]==x[7]-x[9],"inconsistent transfer counters");
  require(canonical?x[6]==x[3]:x[6]==0,"inconsistent boundary/renewal counters");
}
inline std::ofstream open(const std::filesystem::path& path) {
  std::ofstream f;f.exceptions(std::ios::badbit|std::ios::failbit);f.open(path);f<<std::setprecision(17);return f;
}
struct ChainSums {Step z=0;Vec sum{};double e2=0;};
class Observer {
  std::filesystem::path root;
  std::vector<Step> snapshots;
  Schedule schedule;
  int chains,m;Step z,end,step_=0,previousStep=0,frames=0;
  double dt;Step sample;bool canonical,snapshot=false,inFrame=false,legacy=false;
  int chainRows=0;
  Counts previous{};
  std::vector<ChainSums> sums;
  std::vector<int> expected;
  std::ofstream backbone,tangents,sites,connectors,populations,events,positions,attachments;
public:
  double wallSeconds=0,transferSeconds=0,exclusiveSeconds=0;
  size_t transientBytes=0;
  Step transferredBytes=0;
  Observer(const std::filesystem::path& out,const std::filesystem::path& steps,const std::filesystem::path& snapshotPath,
           int chains_,int m_,Step z_,Step end_,double dt_,bool canonical_,Step sample_):root(out),snapshots(snapshotSteps(snapshotPath,end_)),
    schedule(steps,end_,snapshots),chains(chains_),m(m_),z(z_),end(end_),dt(dt_),sample(sample_),canonical(canonical_),sums(chains_),expected(size_t(chains_)*m_,-1),
    backbone(open(out/"equilibrium_backbone.csv")),tangents(open(out/"equilibrium_tangents.csv")),sites(open(out/"equilibrium_sites.csv")),connectors(open(out/"equilibrium_connectors.csv")),
    populations(open(out/"equilibrium_chains.csv")),events(open(out/"equilibrium_events.csv")),positions(open(out/"equilibrium_positions.csv")),attachments(open(out/"equilibrium_attachments.csv")) {
    require(chains>0&&m>1&&z<=expected.size()&&std::isfinite(dt)&&dt>0&&sample>0,"invalid observer dimensions");
    backbone<<"step,time,chain,mean_r,mean_r2,re2,rg2,min_length";
    for(int s:separations(m-1))if(s<=4)backbone<<",tangent"<<s;backbone<<'\n';
    tangents<<"step,time,chain";for(int s:separations(m-1))if(s>4)tangents<<",tangent"<<s;tangents<<'\n';
    sites<<"step,time,chain,bead,spring\n";
    connectors<<"step,time,spring,chain,bead,ex,ey,ez,e2\n";
    populations<<"step,time,chain,z,ex_sum,ey_sum,ez_sum,e2_sum\n";
    events<<"step,time,previous_step,interval_time,"<<counterNames<<'\n';
    positions<<"step,time,chain,bead,x,y,z\n";
    attachments<<"step,time,spring,chain,bead,ax,ay,az,previous,next\n";
    auto f=open(out/"equilibrium_schema.json");
    f<<"{\"version\":1,\"phase\":\"initial before dynamics; otherwise after BD and complete jump batch\",\"dt\":"<<dt
     <<",\"legacy_sample_stride\":"<<sample<<",\"steps\":"<<end<<",\"chains\":"<<chains<<",\"beads_per_chain\":"<<m<<",\"slip_count\":"<<z
     <<",\"canonical\":"<<(canonical?"true":"false")<<",\"expected_frames\":"<<schedule.count()<<",\"snapshot_steps\":[";
    for(size_t i=0;i<snapshots.size();++i)f<<(i?",":"")<<snapshots[i];f<<"]}\n";f.close();
  }
  static std::vector<int> separations(int n) {std::vector<int>s;for(int v:{1,2,3,4,8,16})if(v<n)s.push_back(v);return s;}
  static size_t estimatedBytes(int chains,int m) {return size_t(chains)*sizeof(ChainSums)+size_t(chains)*m*sizeof(int);}
  bool due(Step step)const{return schedule.due(step);}
  template<class Position>
  void begin(Step step,const std::vector<Position>& r,const std::vector<Position>& dense,const std::vector<Slot>& slots,
             const std::vector<int>& occupancy,const Counts& counts) {
    require(!inFrame&&due(step)&&r.size()==expected.size()&&slots.size()==z&&occupancy.size()==expected.size(),"inconsistent observer state sizes/step");
    require(z?dense.size()==r.size():dense.empty(),"inconsistent dense anchor size");
    checkCounts(counts,canonical);
    Counts delta{};for(size_t i=0;i<counts.size();++i){require(counts[i]>=previous[i],"decreasing event counter");delta[i]=counts[i]-previous[i];}
    checkCounts(delta,canonical);require(step||std::all_of(counts.begin(),counts.end(),[](Step n){return n==0;}),"nonzero initial counters");
    std::fill(expected.begin(),expected.end(),-1);std::fill(sums.begin(),sums.end(),ChainSums{});
    for(size_t j=0;j<slots.size();++j) {
      const auto& s=slots[j];require(s.site>=0&&size_t(s.site)<r.size()&&s.chain==s.site/m&&expected[s.site]==-1,"invalid/duplicate spring site");expected[s.site]=int(j);
      for(double a:s.anchor)require(std::isfinite(a),"nonfinite anchor");
    }
    for(size_t i=0;i<r.size();++i) {
      require(std::isfinite(double(r[i].x))&&std::isfinite(double(r[i].y))&&std::isfinite(double(r[i].z)),"nonfinite observed position");
      require(occupancy[i]==expected[i],"inconsistent occupancy map");
      if(z) {
        require(dense[i].w==(expected[i]<0?0:1),"inconsistent dense occupancy");
        if(expected[i]>=0){const auto& a=slots[expected[i]].anchor;require(double(dense[i].x)==a[0]&&double(dense[i].y)==a[1]&&double(dense[i].z)==a[2],"inconsistent dense anchor");}
      }
    }
    // Compare actual contour links with the site-ordered predecessor/successor.
    for(int c=0;c<chains;++c) {
      int prev=-1;
      for(int b=0;b<m;++b) {int j=expected[c*m+b];if(j<0)continue;require(slots[j].previous==prev&&(prev<0||slots[prev].next==j),"inconsistent spring ordering");prev=j;}
      require(prev<0||slots[prev].next==-1,"inconsistent last spring link");
    }
    step_=step;legacy=step%sample==0;snapshot=std::binary_search(snapshots.begin(),snapshots.end(),step);inFrame=true;chainRows=0;
    const double time=double(step)*dt;require(std::isfinite(time),"nonfinite observer time");
    for(size_t i=0;i<r.size();++i) {
      sites<<step<<','<<time<<','<<i/m<<','<<i%m<<','<<expected[i]<<'\n';
      if(snapshot)positions<<step<<','<<time<<','<<i/m<<','<<i%m<<','<<r[i].x<<','<<r[i].y<<','<<r[i].z<<'\n';
    }
    for(size_t j=0;j<slots.size();++j) {
      const auto& s=slots[j];Vec e{double(r[s.site].x)-s.anchor[0],double(r[s.site].y)-s.anchor[1],double(r[s.site].z)-s.anchor[2]};double e2=0;
      auto& a=sums[s.chain];++a.z;for(int d=0;d<3;++d){e2+=e[d]*e[d];a.sum[d]+=e[d];require(std::isfinite(a.sum[d]),"nonfinite connector sum");}
      require(std::isfinite(e2),"nonfinite connector square");a.e2+=e2;require(std::isfinite(a.e2),"nonfinite connector sum of squares");
      connectors<<step<<','<<time<<','<<j<<','<<s.chain<<','<<s.site%m<<','<<e[0]<<','<<e[1]<<','<<e[2]<<','<<e2<<'\n';
      if(snapshot)attachments<<step<<','<<time<<','<<j<<','<<s.chain<<','<<s.site%m<<','<<s.anchor[0]<<','<<s.anchor[1]<<','<<s.anchor[2]<<','<<s.previous<<','<<s.next<<'\n';
    }
    Step total=0;for(int c=0;c<chains;++c){const auto& a=sums[c];total+=a.z;populations<<step<<','<<time<<','<<c<<','<<a.z<<','<<a.sum[0]<<','<<a.sum[1]<<','<<a.sum[2]<<','<<a.e2<<'\n';}require(total==z,"population total mismatch");
    events<<step<<','<<time<<','<<previousStep<<','<<double(step-previousStep)*dt;for(auto n:delta)events<<','<<n;events<<'\n';previous=counts;previousStep=step;
  }
  // Existing scalar reductions supply these values. Only the two longer tangent
  // separations are new calculations, using the same already computed bonds.
  void chain(int c,const std::array<double,11>& scalar,const std::vector<Vec>& q,const std::vector<double>& length) {
    require(inFrame&&c==chainRows&&c<chains&&q.size()==size_t(m-1)&&length.size()==q.size(),"inconsistent backbone observer row");
    if(!legacy)backbone<<step_<<','<<double(step_)*dt<<','<<c;
    if(m-1>8)tangents<<step_<<','<<double(step_)*dt<<','<<c;
    for(int i:{0,1,2,3,6}){require(std::isfinite(scalar[i]),"nonfinite backbone diagnostic");if(!legacy)backbone<<','<<scalar[i];}
    require(scalar[6]>0,"undefined observed tangent");
    for(int s:separations(m-1)) {
      double corr=s<=4?scalar[s+6]:0;
      if(s>4)for(int b=0;b<m-1-s;++b)for(int d=0;d<3;++d)corr+=q[b][d]*q[b+s][d]/(length[b]*length[b+s])/(m-1-s);
      require(std::isfinite(corr),"nonfinite tangent diagnostic");
      if(s<=4){if(!legacy)backbone<<','<<corr;}else tangents<<','<<corr;
    }
    if(!legacy)backbone<<'\n';if(m-1>8)tangents<<'\n';++chainRows;
  }
  void endFrame() {
    require(inFrame&&chainRows==chains,"incomplete equilibrium frame");
    for(auto* f:{&backbone,&tangents,&sites,&connectors,&populations,&events,&positions,&attachments})f->flush();
    schedule.consume(step_);++frames;inFrame=false;
  }
  void finish() {
    require(!inFrame&&schedule.complete()&&frames==schedule.count(),"incomplete equilibrium output");
    for(auto* f:{&backbone,&tangents,&sites,&connectors,&populations,&events,&positions,&attachments})f->close();
    // Publish last, after legacy final output and metadata succeeded. Absence of
    // this marker makes all partial observer output unusable for science.
    auto f=open(root/"equilibrium_complete.tmp");f<<"{\"version\":1,\"complete\":true,\"frames\":"<<frames
      <<",\"extra_device_bytes\":0,\"reduction_workspace_bytes\":"<<(sums.capacity()*sizeof(ChainSums)+expected.capacity()*sizeof(int))
      <<",\"transient_workspace_bytes\":"<<transientBytes<<",\"exclusive_seconds\":"<<exclusiveSeconds
      <<",\"observer_wall_seconds\":"<<wallSeconds<<",\"transfer_seconds\":"<<transferSeconds<<",\"transferred_bytes\":"<<transferredBytes<<",\"files\":{";
    bool first=true;for(const char* name:{"equilibrium_schema.json","equilibrium_backbone.csv","equilibrium_tangents.csv","equilibrium_sites.csv","equilibrium_connectors.csv","equilibrium_chains.csv","equilibrium_events.csv","equilibrium_positions.csv","equilibrium_attachments.csv","initial.csv","final.csv","metadata.json","samples.csv","bond_statistics.csv","initial_bonds.csv"}) {
      f<<(first?"":",")<<'"'<<name<<"\":"<<std::filesystem::file_size(root/name);first=false;
    }
    for(const char* name:{"fixed_slip_springs.csv","slip_springs_initial.csv","slip_springs_final.csv","hopping_metadata.json"})if(std::filesystem::exists(root/name))f<<','<<'"'<<name<<"\":"<<std::filesystem::file_size(root/name);
    f<<"}}\n";f.close();std::filesystem::rename(root/"equilibrium_complete.tmp",root/"equilibrium_complete.json");
  }
};
} // namespace e1_observer
