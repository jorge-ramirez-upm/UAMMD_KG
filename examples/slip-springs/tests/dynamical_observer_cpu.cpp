// Reuse the existing orientation grid and independent unit/P2 reference helpers.
#define main unused_orientation_entry
#include "orientation_cpu.cpp"
#undef main
#include "../dynamical_observer.h"
#include <iterator>
#include <sstream>

namespace fs=std::filesystem;
struct Position {double x=0,y=0,z=0,w=0;};
using Coordinates=std::vector<Position>;
using Frame=std::vector<dynamics::Observation>;
using Values=std::array<long double,dynamics::Quantities>;

Coordinates coordinates(unsigned frame,double offset=0,unsigned bonds=32) {
  const unsigned beads=bonds+1;Coordinates out(2*beads);
  for(unsigned c=0;c<2;++c)for(unsigned i=0;i<beads;++i) {
    const double f=double(i)/bonds,t=frame;
    out[c*beads+i]={offset+100*c+.125*t+f*(2+std::cos(t*.13)),
                 offset-c+.25*t+f*std::sin(t*.13)+std::sin(i*.12)*std::sin(t*.19),
                 offset+2*c-.125*t+f*(1+std::sin(t*.07)),double(i)};
  }
  return out;
}
Frame reference_frame(const Coordinates& positions,unsigned bonds=32) {
  const unsigned beads=bonds+1;const std::array<unsigned,5> selected{{0,bonds/4,bonds/2,3*bonds/4,bonds}};
  Frame out(2);
  for(unsigned c=0;c<2;++c) {
    out[c].chain_id=c;
    for(unsigned d=0;d<3;++d) {
      long double sum=0;
      for(unsigned i=0;i<beads;++i){const auto& p=positions[c*beads+i];sum+=d==0?p.x:(d==1?p.y:p.z);}
      out[c].positions[0][d]=double(sum/beads);
    }
    for(unsigned j=0;j<5;++j){const auto& p=positions[c*beads+selected[j]];out[c].positions[j+1]={{p.x,p.y,p.z}};}
  }
  return out;
}
Values direct(const std::vector<Frame>& frames,unsigned chain,Grid g) {
  Values out{};
  for(Counter n=0;n<g.origins;++n) {
    const Counter a=(n+1)*g.block-1,b=a+g.lag;
    for(unsigned q=0;q<6;++q)for(unsigned d=0;d<3;++d) {
      const long double delta=static_cast<long double>(frames[b][chain].positions[q][d])-frames[a][chain].positions[q][d];
      out[q]+=delta*delta/g.origins;
    }
    for(Counter j=0;j<g.block;++j)for(Counter k=0;k<g.block;++k) {
      auto unit_at=[&](Counter frame) {
        Vector e{};for(unsigned d=0;d<3;++d)e[d]=frames[frame][chain].positions[5][d]-frames[frame][chain].positions[1][d];
        return independent_unit(e);
      };
      const auto cosine=dot(unit_at(n*g.block+j),unit_at(n*g.block+g.lag+k));
      const long double count=static_cast<long double>(g.origins)*g.block*g.block;
      out[dynamics::C1]+=cosine/count;out[dynamics::C2]+=(3*cosine*cosine-1)/2/count;
    }
  }
  out[dynamics::Ends]=(out[dynamics::Bead0]+out[dynamics::Bead32])/2;
  out[dynamics::Quarters]=(out[dynamics::Bead8]+out[dynamics::Bead24])/2;
  out[dynamics::EndDifference]=out[dynamics::Bead0]-out[dynamics::Bead32];
  out[dynamics::QuarterDifference]=out[dynamics::Bead8]-out[dynamics::Bead24];
  return out;
}
std::string read(const fs::path& path) {
  std::ifstream f(path);require(bool(f),"missing metadata file");
  f.exceptions(std::ios::badbit);
  return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};
}
std::vector<std::string> split(const std::string& text) {
  std::vector<std::string> out;std::istringstream in(text);std::string field;
  while(std::getline(in,field,','))out.push_back(field);return out;
}
dynamical_observer::Model model(Counter steps=194,unsigned bonds=32) {
  dynamical_observer::Model m;m.bonds=int(bonds);m.chains=2;m.steps=steps;m.seed=4317;m.dt=.0001;
  m.kbt=1;m.zeta=1;m.mobility_step=.0001;m.noise=std::sqrt(.0002);m.precision_bits=64;
  m.b0.assign(bonds,1);m.kb.assign(bonds,30);m.kappa.assign(bonds+1,0);return m;
}
void check_csv(const fs::path& path,const std::vector<Frame>& frames,orientation::Parameters cfg,bool mean) {
  std::ifstream in(path);require(bool(in),"missing dynamics CSV");std::string line;std::getline(in,line);
  require(split(line).size()==10+dynamics::Quantities,"CSV header width");
  const auto expected=grid(frames.size(),cfg);std::size_t row=0;
  while(std::getline(in,line)) {
    const auto fields=split(line);require(fields.size()==10+dynamics::Quantities,"CSV row width");
    const auto bin=row%expected.size();const auto chain=unsigned(row/expected.size());
    require(mean?chain==0:chain<2,"unexpected output rows");
    const auto g=expected[bin];require(std::stoull(fields[0])==77,"replica identity");
    require(mean?fields[1].empty():std::stoull(fields[1])==chain,"chain identity");
    require(std::stoull(fields[2])==g.lag && std::stoull(fields[3])==g.lag*3 &&
            std::stoull(fields[5])==g.origins && std::stoull(fields[6])==g.block &&
            std::stoull(fields[7])==g.block-1 && std::stoull(fields[8])==g.block,"exported support/counts");
    close(std::stod(fields[4]),g.lag*3*.0001L);close(std::stod(fields[9]),g.block*3*.0001L);
    auto values=direct(frames,chain,g);
    if(mean){const auto other=direct(frames,1,g);for(unsigned q=0;q<dynamics::Quantities;++q)values[q]=(values[q]+other[q])/2;}
    for(unsigned q=0;q<dynamics::Quantities;++q)close(std::stod(fields[10+q]),values[q]);
    ++row;
  }
  require(row==expected.size()*(mean?1:2),"wrong curve row count");
}
void checks(const fs::path& root) {
  dynamical_observer::Settings cfg;cfg.enabled=true;cfg.stride=3;cfg.replica_id=77;
  cfg.correlation={5,8,2};cfg.output="m2";
  for(unsigned coarsening:{2,3}) {
    auto s=cfg;s.correlation={5,coarsening==2?8u:12u,coarsening};s.output=coarsening==2?"m2":"m3";
    dynamical_observer::Observer observer(s,model(),root);std::vector<Frame> frames;
    for(unsigned step=0;step<=194;++step) {
      require(observer.due(step)==(step%3==0),"acquisition phase/stride");
      if(!observer.due(step))continue;
      auto input=coordinates(step/3);const auto saved=input;
      Frame acquired(2);dynamical_observer::acquire(input,acquired);const auto expected=reference_frame(input);
      for(unsigned c=0;c<2;++c) {
        require(acquired[c].chain_id==c,"immutable acquired IDs");
        for(unsigned q=0;q<6;++q)for(unsigned d=0;d<3;++d)close(acquired[c].positions[q][d],expected[c].positions[q][d]);
      }
      if(step==0)rejects([&]{observer.observe(3,input,true,0,input.size()*sizeof(Position));});
      observer.observe(step,input,step%6==0,0,input.size()*sizeof(Position));frames.push_back(expected);
      if(step==0)rejects([&]{observer.observe(0,input,true,0,input.size()*sizeof(Position));});
      for(unsigned i=0;i<input.size();++i)require(input[i].x==saved[i].x&&input[i].y==saved[i].y&&
        input[i].z==saved[i].z&&input[i].w==saved[i].w,"read-only acquisition modified coordinates");
    }
    require(!observer.due(195),"acquisition beyond production horizon");observer.finish();
    rejects([&]{observer.finish();});
    const auto directory=root/s.output;
    check_csv(directory/"chain_correlations.csv",frames,s.correlation,false);
    check_csv(directory/"replica_correlations.csv",frames,s.correlation,true);
    const auto metadata=read(directory/"metadata.json");
    for(const auto* expected:{"\"complete\":true","\"frames\":65","\"last_step\":192",
      "\"selected_beads\":[0,8,16,24,32]","\"shared_frames\":33","\"extra_readbacks\":32",
      "\"standard_error\":null","last-position decimation","triangular lag support","entire hopping/end-renewal batch"})
      require(metadata.find(expected)!=std::string::npos,"missing metadata/semantics");
    require(!fs::exists(directory/"metadata.pending.json"),"completion left pending metadata");
    rejects([&]{dynamical_observer::Observer duplicate(s,model(),root);});
  }
  auto disabled=cfg;disabled.enabled=false;disabled.validate(8,2,194,.0001,true);
  rejects([&]{cfg.validate(8,2,194,.0001);});rejects([&]{cfg.validate(32,2,194,.0001,true);});
  auto bad=cfg;bad.stride=0;rejects([&]{bad.validate(32,2,194,.0001);});
  for(const auto* name:{"","../bad","/absolute","a/b","metadata.json"}){bad=cfg;bad.output=name;rejects([&]{bad.validate(32,2,194,.0001);});}
  bad=cfg;bad.correlation={0,8,2};rejects([&]{bad.validate(32,2,194,.0001);});
  bad=cfg;bad.memory_mib=0;rejects([&]{bad.validate(32,2,194,.0001);});
  bad=cfg;bad.memory_mib=1;bad.correlation={20,64,2};rejects([&]{bad.validate(32,256,194,.0001);});
  rejects([&]{cfg.validate(32,2,194,INFINITY);});
  bad=cfg;bad.stride=Counter(-1);rejects([&]{bad.validate(32,2,194,.0001);});
  Frame buffer(2);auto input=coordinates(0);auto invalid=input;invalid[40].z=NAN;
  rejects([&]{dynamical_observer::acquire(invalid,buffer);});
  invalid=input;invalid[0].x=std::numeric_limits<double>::max();invalid[1].x=-invalid[0].x;
  rejects([&]{dynamical_observer::acquire(invalid,buffer);});input.pop_back();
  rejects([&]{dynamical_observer::acquire(input,buffer);});
  auto large=coordinates(0,1099511627776.);const auto expected=reference_frame(large);
  dynamical_observer::acquire(large,buffer);
  for(unsigned c=0;c<2;++c) {
    require(std::abs(buffer[c].positions[0][0]-expected[c].positions[0][0])<.002,"large-offset CM stability");
    for(unsigned q=1;q<6;++q)require(buffer[c].positions[q]==expected[c].positions[q],"selected mapping at large offset");
  }
  bad=cfg;bad.output="incomplete";dynamical_observer::Observer incomplete(bad,model(),root);
  rejects([&]{incomplete.finish();});require(!fs::exists(root/"incomplete/metadata.json"),"incomplete acquisition published success");
  bad.output="blocked";auto tiny=model(0);dynamical_observer::Observer blocked(bad,tiny,root);
  blocked.observe(0,coordinates(0),true,0,0);
  fs::create_directory(root/"blocked/metadata.json"); // Deterministic final rename error, even as root.
  rejects([&]{blocked.finish();});
  require(!fs::is_regular_file(root/"blocked/metadata.json"),"failed publication marked complete");
  bad.output="zero";dynamical_observer::Observer zero(bad,tiny,root);
  zero.observe(0,coordinates(0),true,0,0);zero.finish();
}
void longer_checks(const fs::path& root,unsigned bonds) {
  const std::array<int,5> expected_indices{{0,int(bonds/4),int(bonds/2),int(3*bonds/4),int(bonds)}};
  require(dynamics::selected_beads(bonds)==expected_indices,"long contour selection");
  for(unsigned m:{2u,3u}) {
    dynamical_observer::Settings cfg;cfg.enabled=true;cfg.stride=3;cfg.replica_id=77;
    cfg.correlation={5,m==2?8u:12u,m};cfg.output="n"+std::to_string(bonds)+"m"+std::to_string(m);
    dynamical_observer::Observer observer(cfg,model(194,bonds),root);
    std::vector<Frame> frames;
    for(unsigned step=0;step<=194;step+=3) {
      auto positions=coordinates(step/3,0,bonds);const auto original=positions;
      Frame actual(2);dynamical_observer::acquire(positions,actual,bonds);
      const auto reference=reference_frame(positions,bonds);
      for(unsigned c=0;c<2;++c)for(unsigned q=0;q<6;++q)for(unsigned d=0;d<3;++d)
        close(actual[c].positions[q][d],reference[c].positions[q][d]);
      observer.observe(step,positions,true,0,positions.size()*sizeof(Position));
      frames.push_back(reference);
      for(unsigned i=0;i<positions.size();++i)require(positions[i].x==original[i].x&&positions[i].y==original[i].y&&
        positions[i].z==original[i].z&&positions[i].w==original[i].w,"long acquisition mutated coordinates");
    }
    observer.finish();const auto directory=root/cfg.output;
    check_csv(directory/"chain_correlations.csv",frames,cfg.correlation,false);
    check_csv(directory/"replica_correlations.csv",frames,cfg.correlation,true);
    const auto text=read(directory/"metadata.json");
    require(text.find("\"N\":"+std::to_string(bonds)+",")!=std::string::npos,"metadata actual N");
    require(text.find("\"beads_per_chain\":"+std::to_string(bonds+1)+",")!=std::string::npos,"metadata bead dimension");
    std::string selected="\"selected_beads\":[";
    for(unsigned j=0;j<5;++j)selected+=(j?",":"")+std::to_string(expected_indices[j]);
    require(text.find(selected+"]")!=std::string::npos,"metadata actual bead selection");
    std::ifstream csv(directory/"chain_correlations.csv");std::string header;std::getline(csv,header);
    const auto names=dynamics::quantity_names_for(bonds);
    for(unsigned j=0;j<5;++j)require(header.find("bead"+std::to_string(expected_indices[j])+"_msd")!=std::string::npos,"CSV actual bead name");
    require(names[dynamics::Center]=="bead"+std::to_string(bonds/2)+"_msd","center slot label");
    auto invalid=model(194,bonds);invalid.kappa.pop_back();rejects([&]{invalid.validate();});
    Frame target(2);auto wrong=coordinates(0);rejects([&]{dynamical_observer::acquire(wrong,target,bonds);});
    auto large=coordinates(0,1099511627776.,bonds);const auto ref=reference_frame(large,bonds);
    dynamical_observer::acquire(large,target,bonds);
    for(unsigned c=0;c<2;++c)require(std::abs(target[c].positions[0][0]-ref[c].positions[0][0])<.002,"long large-offset CM");
  }
}

int main(int argc,char** argv) {
  try {
    if(argc!=2)throw std::runtime_error("usage: dynamical_observer_cpu NEW_PERMANENT_TEST_DIRECTORY");
    const fs::path root=argv[1];if(!fs::create_directory(root))throw std::runtime_error("refusing existing test directory");
    checks(root);longer_checks(root,64);longer_checks(root,128);
    rejects([]{dynamics::selected_beads(48);});
    dynamics::Replica a(101,{0},{3,8,2},{0,1,.0001},1<<20,64);
    dynamics::Replica b(102,{0},{3,8,2},{0,1,.0001},1<<20,128);
    dynamics::Observation sample;sample.chain_id=0;sample.positions[5][0]=1;
    a.observe(0,{sample});b.observe(0,{sample});
    rejects([&]{dynamics::summarize({a.evaluate(),b.evaluate()});});
    std::cout<<"PASS read-only dynamical observer mapping, curves, metadata and failure cases\n";return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
