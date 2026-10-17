#include "../semiflexible_stress_stream.h"
#include <iostream>
int main(int argc,char** argv){
  try{
    if(argc!=11)throw std::runtime_error("input output levels slots m workers batch kbt density dump required");
    std::ifstream input(argv[1]);std::size_t chains,frames;
    if(!(input>>chains>>frames)||!chains||!frames||chains>4096||frames>65536)throw std::runtime_error("invalid sequence dimensions");
    stress3b::Settings s;s.mode="stream";s.correlation.levels=std::stoul(argv[3]);s.correlation.slots=std::stoul(argv[4]);s.correlation.coarsening=std::stoul(argv[5]);s.workers=std::stoul(argv[6]);s.batch=std::stoul(argv[7]);s.density=std::stod(argv[9]);s.dump=std::stoi(argv[10]);s.validate(chains);
    double kbt=std::stod(argv[8]);if(!(kbt>0&&std::isfinite(kbt)))throw std::runtime_error("invalid kbt");
    std::filesystem::path out(argv[2]);if(!std::filesystem::create_directory(out))throw std::runtime_error("output exists");
    stress3b::Correlations correlation(s,chains,out);std::vector<streaming::Sample> batch(s.batch*chains);std::size_t fill=0;
    for(std::size_t f=0;f<frames;++f){
      auto* frame=batch.data()+fill*chains;
      for(std::size_t c=0;c<chains;++c)for(int k=0;k<6;++k)if(!(input>>frame[c].v[k]))throw std::runtime_error("truncated/nonfinite data");
      correlation.received(frame,f);if(++fill==s.batch){correlation.consume(batch.data(),fill);fill=0;}
    }
    std::string extra;if(input>>extra)throw std::runtime_error("extra sequence data");
    if(fill)correlation.consume(batch.data(),fill);
    correlation.write(out,0.125,kbt);std::cout<<"PASS frames="<<correlation.frames<<'\n';
    return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
