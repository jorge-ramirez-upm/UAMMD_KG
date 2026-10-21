#include "../e1_equilibrium_observer.h"
#include <cassert>
#include <cstring>
#include <iostream>
#include <malloc.h>
namespace fs=std::filesystem;
using namespace e1_observer;
struct P {double x,y,z,w;};
template<class F>void fails(F f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}assert(failed);}
void text(const fs::path& p,const std::string& s){auto f=open(p);f<<s;f.close();}
int main(int argc,char**argv) {
  assert(argc==2);fs::path root=argv[1];assert(!fs::exists(root));fs::create_directories(root);
  auto path=root/"steps";
  for(auto s:{"","1 3","0 0 3","0 2 1 3","0 4","0 1","0 0.5 3","0 -1 3","0 18446744073709551616 3","0 1e-4 3"}) {
    text(path,s);fails([&]{Schedule x(path,3,{0,3});});
  }
  text(path,"0 1 3");fails([&]{Schedule x(path,3,{0,2,3});});
  text(root/"too-many","0 1 2 3 4 5 6 7 8");fails([&]{snapshotSteps(root/"too-many",8);});
  text(root/"snapshots","0 1 3");
  std::vector<P> r,dense(9);for(int c=0;c<3;++c)for(int b=0;b<3;++b)r.push_back({double(b),double(c),0,0});
  std::vector<Slot> slots{{{-.1,-.2,-.3},0,0,-1,1},{{.9,-.2,-.3},1,0,0,-1},{{1.9,1.8,-.3},8,2,-1,-1}};
  std::vector<int> occupancy(9,-1);
  auto refresh=[&]{std::fill(dense.begin(),dense.end(),P{});std::fill(occupancy.begin(),occupancy.end(),-1);for(int j=0;j<3;++j){auto s=slots[j];dense[s.site]={s.anchor[0],s.anchor[1],s.anchor[2],1};occupancy[s.site]=j;}};refresh();
  auto heapBefore=mallinfo2().uordblks;
  Observer obs(root,path,root/"snapshots",3,3,3,3,.00025,true,4);
  auto heapAfter=mallinfo2().uordblks;
  std::cout<<"observer constructor malloc delta bytes="<<(heapAfter-heapBefore)<<'\n';
  auto write=[&](Step step,Counts counters) {
    const auto oldr=r,oldd=dense;const auto olds=slots;const auto oldo=occupancy;
    obs.begin(step,r,dense,slots,occupancy,counters);
    for(int c=0;c<3;++c)obs.chain(c,{1,1,4,2./3,0,0,1,1,0,0,0},{{1,0,0},{1,0,0}},{1,1});
    obs.endFrame();assert(std::memcmp(r.data(),oldr.data(),r.size()*sizeof(P))==0);
    assert(std::memcmp(dense.data(),oldd.data(),dense.size()*sizeof(P))==0);
    assert(std::memcmp(slots.data(),olds.data(),slots.size()*sizeof(Slot))==0);assert(occupancy==oldo);
  };
  write(0,{});slots[1].site=2;refresh();write(1,{1,1,1,0,0,0,0,0,0,0,0});
  slots[0].site=3;slots[0].chain=1;slots[0].next=-1;slots[1].previous=-1;refresh();
  write(3,{3,4,1,2,1,0,2,1,1,0,1});
  for(const char* name:{"initial.csv","final.csv","metadata.json","samples.csv","bond_statistics.csv","initial_bonds.csv"})text(root/name,"fixture\n");
  text(root/"samples.csv","step,time,chain,mean_r,mean_r2,re2,rg2,min_length,tangent1\n0,0,0,1,1,4,0.66666666666666663,1,1\n0,0,1,1,1,4,0.66666666666666663,1,1\n0,0,2,1,1,4,0.66666666666666663,1,1\n");
  obs.finish();assert(fs::exists(root/"equilibrium_complete.json"));
  // Each failure directory must remain without a completion marker.
  int serial=0;auto bad=[&](auto operation){auto out=root/("failure"+std::to_string(serial++));fs::create_directory(out);{
    Observer x(out,path,{},3,3,3,3,.0001,true,4);fails([&]{operation(x);});
  }assert(!fs::exists(out/"equilibrium_complete.json"));};
  bad([&](Observer& x){x.finish();});
  bad([&](Observer& x){auto wrong=occupancy;wrong[3]=-1;x.begin(0,r,dense,slots,wrong,{});});
  bad([&](Observer& x){auto wrong=slots;wrong[0].site=wrong[1].site;x.begin(0,r,dense,wrong,occupancy,{});});
  bad([&](Observer& x){auto wrong=slots;wrong[0].anchor[0]=NAN;x.begin(0,r,dense,wrong,occupancy,{});});
  bad([&](Observer& x){auto wrong=slots;wrong[1].previous=2;x.begin(0,r,dense,wrong,occupancy,{});});
  bad([&](Observer& x){auto wrong=r;wrong[0].x=INFINITY;x.begin(0,wrong,dense,slots,occupancy,{});});
  bad([&](Observer& x){x.begin(0,r,dense,slots,occupancy,{0,1,0,0,0,0,0,0,0,0,0});});
  bad([&](Observer& x){x.begin(0,r,dense,slots,occupancy,{});x.endFrame();});
  bad([&](Observer& x){x.begin(0,r,dense,slots,occupancy,{});x.chain(0,{1,1,NAN,1,0,0,1},{{1,0,0},{1,0,0}},{1,1});});
  bad([&](Observer& x){x.begin(0,r,dense,slots,occupancy,{});x.chain(0,{1,1,1,1,0,0,0},{{0,0,0},{1,0,0}},{0,1});});
  auto full=root/"full";fs::create_directory(full);fs::create_symlink("/dev/full",full/"equilibrium_sites.csv");
  fails([&]{Observer x(full,path,{},3,3,3,3,.0001,true,4);x.begin(0,r,dense,slots,occupancy,{});x.endFrame();});
  assert(!fs::exists(full/"equilibrium_complete.json"));
  std::cout<<"E1 observer host schedules, state, finite checks, incomplete output, write failures and read-only checks passed\n";
}
