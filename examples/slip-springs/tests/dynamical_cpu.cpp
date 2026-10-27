// Reuse the unchanged orientation oracle/helpers and its full correctness suite.
// Its benchmark and memory-measurement entry points are never invoked here.
#define main existing_orientation_fixture_entry
#include "orientation_cpu.cpp"
#undef main
#include "../dynamical_observables.h"

using Frames=std::vector<std::vector<dynamics::Observation>>;
using Expected=std::array<long double,dynamics::Quantities>;
constexpr orientation::Clock acquisition{17,20,.000025};

Frames positions(std::size_t count,std::size_t chains,int kind,double offset=0,double speed=1) {
  Frames frames(count,std::vector<dynamics::Observation>(chains));
  const auto vectors=prescribed(count,chains,5);
  for(std::size_t t=0;t<count;++t)for(std::size_t c=0;c<chains;++c) {
    auto& frame=frames[t][c];frame.chain_id=100+c;
    const Vector end=kind==2?vectors[t][c]:Vector{{4,2,1}};
    auto bead=[&](int i) {
      Vector r{};
      for(int d=0;d<3;++d)r[d]=offset+double(c)*16+d+
        (kind?speed*(c+1)*(d+1)*double(t)/8:0)+double(i)*end[d]/32+
        (kind==2?std::sin(double(i)*.13)*std::sin(double(t)*.19+d):0);
      return r;
    };
    for(int i=0;i<33;++i) {
      const auto r=bead(i);
      for(int d=0;d<3;++d)frame.positions[0][d]+=r[d]/33;
    }
    for(unsigned i=0;i<5;++i)frame.positions[i+1]=bead(dynamics::bead_indices[i]);
  }
  return frames;
}

Expected oracle(const Frames& data,std::size_t chain,Grid support) {
  Expected out{};
  for(Counter origin=0;origin<support.origins;++origin) {
    const Counter early=(origin+1)*support.block-1,late=early+support.lag;
    for(unsigned q=0;q<6;++q)for(unsigned d=0;d<3;++d) {
      const long double delta=static_cast<long double>(data[late][chain].positions[q][d])-data[early][chain].positions[q][d];
      out[q]+=delta*delta/support.origins;
    }
    for(Counter a=0;a<support.block;++a)for(Counter b=0;b<support.block;++b) {
      auto direction=[&](Counter frame) {
        Vector r{};for(unsigned d=0;d<3;++d)
          r[d]=data[frame][chain].positions[5][d]-data[frame][chain].positions[1][d];
        return independent_unit(r);
      };
      const auto value=dot(direction(origin*support.block+a),direction(origin*support.block+support.lag+b));
      const long double denominator=static_cast<long double>(support.origins)*support.block*support.block;
      out[dynamics::C1]+=value/denominator;
      out[dynamics::C2]+=(3*value*value-1)/2/denominator;
    }
  }
  out[dynamics::Ends]=(out[dynamics::Bead0]+out[dynamics::Bead32])/2;
  out[dynamics::Quarters]=(out[dynamics::Bead8]+out[dynamics::Bead24])/2;
  out[dynamics::EndDifference]=out[dynamics::Bead0]-out[dynamics::Bead32];
  out[dynamics::QuarterDifference]=out[dynamics::Bead8]-out[dynamics::Bead24];
  return out;
}

dynamics::Result verify_positions(const Frames& data,orientation::Parameters cfg,Counter replica_id=1) {
  std::vector<Counter> ids;for(const auto& c:data.front())ids.push_back(c.chain_id);
  dynamics::Replica bank(replica_id,ids,cfg,acquisition);
  require(bank.evaluate().mean.empty(),"empty dynamics bank exports bins");
  for(std::size_t t=0;t<data.size();++t)bank.observe(acquisition.first_step+t*acquisition.stride,data[t]);
  auto result=bank.evaluate();const auto again=bank.evaluate();const auto expected=grid(data.size(),cfg);
  require(result.mean.size()==expected.size() && result.chains.size()==ids.size(),"dynamics result shape");
  require(result.metadata.replica_id==replica_id && result.metadata.frames==data.size(),"replica/frame metadata");
  require(result.metadata.last_step==acquisition.first_step+(data.size()-1)*acquisition.stride,"last step metadata");
  for(std::size_t i=0;i<expected.size();++i) {
    const auto e=expected[i];const auto& support=result.mean[i].support;
    require(support.lag_samples==e.lag && support.origins_per_chain==e.origins &&
            support.decimation_samples==e.block && support.diffusion_phase_samples==e.block-1,"MSD decimation support");
    require(support.lag_steps==e.lag*acquisition.stride,"lag step mapping");
    close(support.lag_time,e.lag*acquisition.stride*acquisition.dt);
    close(support.orientation_block_duration,e.block*acquisition.stride*acquisition.dt);
    Expected average{};
    for(std::size_t c=0;c<ids.size();++c) {
      require(result.chains[c].chain_id==ids[c],"immutable result chain ID");
      const auto reference=oracle(data,c,e);
      for(unsigned q=0;q<dynamics::Quantities;++q) {
        close(result.chains[c].bins[i].values[q],reference[q]);
        close(again.chains[c].bins[i].values[q],result.chains[c].bins[i].values[q]);
        average[q]+=reference[q]/ids.size();
      }
    }
    for(unsigned q=0;q<dynamics::Quantities;++q)close(result.mean[i].values[q],average[q]);
  }
  return result;
}

void dynamics_tests() {
  static_assert(!std::is_copy_constructible<dynamics::OwnedDiffusion>::value);
  static_assert(!std::is_move_constructible<dynamics::Replica>::value);
  for(auto cfg:{orientation::Parameters{6,8,2},orientation::Parameters{5,12,3}})
    for(std::size_t frames:{1,2,7,8,17,65,130})for(int kind=0;kind<3;++kind)
      verify_positions(positions(frames,3,kind),cfg);
  // Binary-exact large offsets expose squared-moment cancellation without hiding
  // the unavoidable quantization of input doubles. References use those inputs.
  for(int kind=0;kind<3;++kind)verify_positions(positions(65,2,kind,1099511627776.),{6,8,2});
  auto translation=verify_positions(positions(65,2,1),{6,8,2});
  for(const auto& chain:translation.chains)for(const auto& bin:chain.bins) {
    close(bin.values[dynamics::EndDifference],0);close(bin.values[dynamics::QuarterDifference],0);
  }
  // Deliberately nonuniform increments: full-origin, block-mean and endpoint-
  // decimated MSDs are different. Compare production only with endpoint sampling.
  dynamics::OwnedDiffusion owner({5,6,3});std::vector<Vector> irregular;
  for(unsigned t=0;t<65;++t){irregular.push_back({{double((t*t)%17),double(t%5),0}});owner.push(irregular.back());}
  owner.evaluate();bool distinguished=false;
  const auto expected=grid(irregular.size(),{5,6,3});
  require(owner.size()==expected.size(),"deepest-level export differs");
  for(unsigned i=0;i<owner.size();++i) {
    const auto e=expected[i];long double decimated=0,full=0,blocked=0;
    for(Counter n=0;n<e.origins;++n) {
      const auto a=(n+1)*e.block-1,b=a+e.lag;
      for(int d=0;d<3;++d){const long double x=irregular[b][d]-irregular[a][d];decimated+=x*x/e.origins;}
      for(int d=0;d<3;++d) {
        long double delta=0;for(Counter j=0;j<e.block;++j)
          delta+=(irregular[n*e.block+e.lag+j][d]-irregular[n*e.block+j][d])/e.block;
        blocked+=delta*delta/e.origins;
      }
    }
    for(Counter n=0;n<irregular.size()-e.lag;++n)for(int d=0;d<3;++d) {
      const long double x=irregular[n+e.lag][d]-irregular[n][d];full+=x*x/(irregular.size()-e.lag);
    }
    close(owner.value(i),decimated);require(owner.origins(i)==e.origins,"MSD exact pair count");
    if(e.block>1 && std::abs(decimated-full)>1e-3 && std::abs(decimated-blocked)>1e-3)distinguished=true;
  }
  require(distinguished,"coarse fixture does not distinguish decimation");
  // Symmetry is combined within each chain before chain/replica uncertainty.
  auto a=verify_positions(positions(65,2,2,0,1),{6,8,2},11);
  auto b=verify_positions(positions(65,2,2,0,2),{6,8,2},12);
  const auto summary=dynamics::summarize({a,b}),single=dynamics::summarize({a});
  for(std::size_t i=0;i<a.mean.size();++i)for(unsigned q=0;q<dynamics::Quantities;++q) {
    const auto reference=mean_se({a.mean[i].values[q],b.mean[i].values[q]});
    close(summary.bins[i].values[q].mean,reference.first);
    close(*summary.bins[i].values[q].standard_error,reference.second);
    require(!single.bins[i].values[q].standard_error,"one replica reports SE");
  }
  rejects([&]{dynamics::summarize({a,a});});rejects([]{dynamics::summarize({});});
  auto mismatch=b;mismatch.metadata.clock.stride++;rejects([&]{dynamics::summarize({a,mismatch});});
  mismatch=b;mismatch.mean.back().support.origins_per_chain++;rejects([&]{dynamics::summarize({a,mismatch});});
  mismatch=b;mismatch.mean[0].values[0]=NAN;rejects([&]{dynamics::summarize({a,mismatch});});

  auto valid=positions(1,2,0)[0];dynamics::Replica atomic(1,{100,101},{4,8,2},{5,2,.1});
  for(auto value:{NAN,INFINITY,-INFINITY}) {
    auto bad=valid;bad.back().positions[4][2]=value;
    rejects([&]{atomic.observe(5,bad);});require(atomic.frames()==0,"partial nonfinite frame");
  }
  auto bad=valid;bad.back().positions[5]=bad.back().positions[1];rejects([&]{atomic.observe(5,bad);});
  bad=valid;bad.back().chain_id=100;rejects([&]{atomic.observe(5,bad);});
  bad=valid;std::swap(bad[0],bad[1]);rejects([&]{atomic.observe(5,bad);});
  rejects([&]{atomic.observe(4,valid);});rejects([&]{atomic.observe(5,{});});
  require(atomic.evaluate().mean.empty(),"invalid first frame mutated correlators");
  atomic.observe(5,valid);rejects([&]{atomic.observe(5,valid);});rejects([&]{atomic.observe(9,valid);});
  bad=valid;bad.back().positions[0][0]-=1e10;rejects([&]{atomic.observe(7,bad);});
  bad=valid;bad.back().positions[0][1]=std::numeric_limits<double>::max();rejects([&]{atomic.observe(7,bad);});
  require(atomic.frames()==1,"invalid later frame mutated clock");atomic.observe(7,valid);
  for(const auto& bin:atomic.evaluate().mean)for(unsigned q=0;q<6;++q)close(bin.values[q],0);
  for(auto cfg:{orientation::Parameters{0,8,2},orientation::Parameters{3,7,2}})
    rejects([&]{dynamics::Replica r(1,{100},cfg,{0,1,1});});
  for(auto clock:{orientation::Clock{0,0,1},orientation::Clock{0,1,0},orientation::Clock{0,1,NAN},
                  orientation::Clock{0,1,INFINITY},orientation::Clock{0,Counter(-1),1}})
    rejects([&]{dynamics::Replica r(1,{100},{4,8,2},clock);});
  rejects([]{dynamics::Replica r(1,{}, {4,8,2},{0,1,1});});
  rejects([]{dynamics::Replica r(1,{1,1},{4,8,2},{0,1,1});});
  rejects([]{dynamics::Replica r(1,{1},{4,8,2},{0,1,1},1);});
  rejects([]{dynamics::Replica::estimated_bytes(std::size_t(-1),{4,8,2});});
  dynamics::Replica overflow(1,{100,101},{3,8,2},{Counter(-1),1,1});
  overflow.observe(Counter(-1),valid);rejects([&]{overflow.observe(0,valid);});
  for(int repeat=0;repeat<100;++repeat) {
    dynamics::OwnedDiffusion d({4,8,2});
    rejects([&]{d.push({{-1e10,0,0}});});rejects([&]{d.push({{0,NAN,0}});});
    for(int i=0;i<35;++i)d.push({{double(i),2,3}});d.evaluate();close(d.value(1),1);
    const auto count=d.origins(0);d.evaluate();require(d.origins(0)==count,"repeated evaluation mutates counts");
    d.clear();d.push({{2,3,4}});d.evaluate();require(d.origins(0)==1,"clear retains data");close(d.value(0),0);
    dynamics::Replica r(1,{100,101},{4,8,2},{0,1,1});r.observe(0,valid);r.evaluate();
  }
  std::cout<<"PASS dynamical CPU prescribed positions, decimated MSD, orientation, replica reduction and lifetime\n";
}

int main() {
  try {tests();dynamics_tests();return 0;}
  catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
