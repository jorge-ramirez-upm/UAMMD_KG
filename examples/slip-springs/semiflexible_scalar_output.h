#pragma once
#include <array>
#include <cstring>
#include <stdexcept>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <vector>
#include <algorithm>
#include <cmath>

namespace scalar_output {
using Count=std::uint64_t;
constexpr const char* schemaHash="78d112f65ed47083976fd692edf959a051bd5b3a85f80dae87fdfc1c7c10deaa";
constexpr Count initialHash=14695981039346656037ULL;
inline Count nextHash(Count h,Count step){return h*1099511628211ULL+step+1;}
inline Count bits(double x){static_assert(sizeof(double)==8&&std::numeric_limits<double>::is_iec559,"binary64 required");Count word;std::memcpy(&word,&x,8);return word;}
inline std::string hex(Count n){std::ostringstream f;f<<std::hex<<std::setw(16)<<std::setfill('0')<<n;return f.str();}
inline std::ofstream file(const std::filesystem::path& path){std::ofstream f(path);f.exceptions(std::ios::badbit|std::ios::failbit);f<<std::setprecision(17);return f;}
inline std::vector<Count> selectedSteps(Count steps,Count stride){
  std::vector<Count> result;
  for(Count j=0;j<=4;++j){Count remainder=j*(steps%4);if(remainder%4)continue;Count step=j*(steps/4)+remainder/4;if(step%stride==0)result.push_back(step);}
  result.erase(std::unique(result.begin(),result.end()),result.end());return result;
}
class Compact {
  struct Row {std::array<double,6> sum{};double minimum=std::numeric_limits<double>::infinity();Count frames=0,half=0,finite=0,hash=initialHash;};
  std::vector<Row> rows;
  std::vector<Count> selected;
  std::filesystem::path output;
  Count steps,stride,frames=0,selectedHash=initialHash;int nextChain=0,tangents;double dt;bool failed=false;
public:
  static std::size_t estimatedBytes(std::size_t chains){return chains*sizeof(Row)+8*sizeof(Count);}
  Compact(int chains,int n,Count steps,Count stride,double dt,const std::filesystem::path& out)
   :rows(chains),selected(selectedSteps(steps,stride)),output(out),steps(steps),stride(stride),tangents(std::min(4,n-1)),dt(dt){}
  bool selectedStep(Count step) const{return std::binary_search(selected.begin(),selected.end(),step);}
  bool record(Count step,int chain,const std::array<double,11>& values){
    if(chain!=nextChain||step!=frames*stride)throw std::runtime_error("compact scalar schedule/order mismatch");
    Row& row=rows[chain];++row.frames;row.hash=nextHash(row.hash,step);row.minimum=std::min(row.minimum,values[6]);
    if(selectedStep(step)){selectedHash=nextHash(selectedHash,step);selectedHash=nextHash(selectedHash,bits(step*dt));selectedHash=nextHash(selectedHash,chain);for(int j=0;j<7+tangents;++j)selectedHash=nextHash(selectedHash,bits(values[j]));}
    bool finite=true;for(int j=0;j<7+tangents;++j)finite&=std::isfinite(values[j]);
    if(finite)++row.finite;
    if(step>=steps/2){++row.half;row.sum[0]+=values[2];row.sum[1]+=values[3];for(int j=0;j<tangents;++j)row.sum[j+2]+=values[j+7];}
    bool overflow=false;for(int j=0;j<2+tangents;++j)overflow|=!std::isfinite(row.sum[j]);
    ++nextChain;if(nextChain==int(rows.size())){nextChain=0;++frames;}
    if((!finite||overflow)&&!failed){
      failed=true;auto f=file(output/"scalar_failure.json");f<<"{\"step\":"<<step<<",\"chain\":"<<chain<<",\"reason\":\""<<(finite?"summary_overflow":"nonfinite_scalar")<<"\"}\n";return true;
    }
    return false;
  }
  void write(int n){
    if(nextChain||frames!=steps/stride+1)throw std::runtime_error("incomplete compact scalar coverage");
    auto f=file(output/"scalar_statistics.csv");
    f<<"chain,frames,finite_rows,final_half_frames,first_step,last_step,schedule_hash,min_length,mean_re2,mean_rg2";
    for(int j=1;j<=tangents;++j)f<<",mean_tangent"<<j;f<<",record_hash\n";
    Count statisticsHash=initialHash;
    double minimum=std::numeric_limits<double>::infinity();Count finite=0;
    for(std::size_t c=0;c<rows.size();++c){const auto& r=rows[c];minimum=std::min(minimum,r.minimum);finite+=r.finite;
      f<<c<<','<<r.frames<<','<<r.finite<<','<<r.half<<",0,"<<(frames-1)*stride<<','<<hex(r.hash)<<','<<r.minimum;
      Count hash=initialHash;for(Count word:{Count(c),r.frames,r.finite,r.half,Count(0),(frames-1)*stride,r.hash,bits(r.minimum)})hash=nextHash(hash,word);
      for(int j=0;j<2+tangents;++j){double mean=r.half?r.sum[j]/r.half:std::numeric_limits<double>::quiet_NaN();f<<','<<mean;hash=nextHash(hash,bits(mean));}
      f<<','<<hex(hash)<<'\n';statisticsHash=nextHash(statisticsHash,hash);
    }
    f.close();auto m=file(output/"scalar_metadata.json");
    m<<"{\"profile\":\"compact\",\"schema\":\"scalar-output-v1\",\"schema_sha256\":\""<<schemaHash<<"\",\"chains\":"<<rows.size()<<",\"springs\":"<<n
     <<",\"steps\":"<<steps<<",\"stride\":"<<stride<<",\"dt\":"<<dt<<",\"frames\":"<<frames<<",\"finite_rows\":"<<finite<<",\"final_half_start_step\":"<<steps/2<<",\"final_half_frames\":"<<rows[0].half
     <<",\"selected_steps\":[";
    for(std::size_t i=0;i<selected.size();++i)m<<(i?",":"")<<selected[i];
    m<<"],\"serialized_rows\":"<<selected.size()*rows.size()<<",\"minimum_sampled_bond\":";
    if(std::isfinite(minimum))m<<minimum;else m<<"null";
    m<<",\"schedule_hash\":\""<<hex(rows[0].hash)<<"\",\"statistics_hash\":\""<<hex(statisticsHash)<<"\",\"selected_hash\":\""<<hex(selectedHash)<<"\",\"host_bytes\":"<<rows.capacity()*sizeof(Row)+selected.capacity()*sizeof(Count)<<",\"gpu_bytes\":0}\n";
  }
};
}
