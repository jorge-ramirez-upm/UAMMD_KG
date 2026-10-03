#ifndef EXAMPLES_KG_ASSOC_CLI_CUH
#define EXAMPLES_KG_ASSOC_CLI_CUH
#include <iostream>
#include <stdexcept>
#include <string>
namespace kg_assoc {
struct Params { int steps=10000, every=100; double dt=.005, temperature=1., ee=4., ea=1., nu0=10., rAssoc=1.3, k=30., r0=1.5, friction=.5, box=8.; unsigned long long seed=12345; std::string prefix="kg_assoc_dimer"; bool selfTest=false; };
inline std::string arg(int& i,int n,char**v){if(++i>=n)throw std::runtime_error("missing option value");return v[i];}
inline Params parseArgs(int n,char**v){ Params p; for(int i=1;i<n;++i){std::string a=v[i]; if(a=="--steps"||a=="-n")p.steps=std::stoi(arg(i,n,v)); else if(a=="--dt")p.dt=std::stod(arg(i,n,v)); else if(a=="--temperature"||a=="-T")p.temperature=std::stod(arg(i,n,v)); else if(a=="--Ee")p.ee=std::stod(arg(i,n,v)); else if(a=="--Ea")p.ea=std::stod(arg(i,n,v)); else if(a=="--nu0")p.nu0=std::stod(arg(i,n,v)); else if(a=="--Nevery")p.every=std::stoi(arg(i,n,v)); else if(a=="--r-assoc")p.rAssoc=std::stod(arg(i,n,v)); else if(a=="--K")p.k=std::stod(arg(i,n,v)); else if(a=="--R0")p.r0=std::stod(arg(i,n,v)); else if(a=="--seed")p.seed=std::stoull(arg(i,n,v)); else if(a=="--output"||a=="--prefix")p.prefix=arg(i,n,v); else if(a=="--self-test")p.selfTest=true; else if(a=="--help"){std::cout<<"kg_assoc_dimer --steps N --dt DT --temperature T --Ee E --Ea E --nu0 X --Nevery N --r-assoc R --K K --R0 R --seed S --output PREFIX [--self-test]\n";std::exit(0);} else throw std::runtime_error("unknown argument: "+a); } if(p.steps<0||p.every<=0||p.dt<=0||p.temperature<=0||p.k<=0||p.r0<=0||p.rAssoc<=0||p.rAssoc>=p.r0||p.box<=2*p.r0)throw std::runtime_error("invalid physical parameters (require 0 < r_assoc < R0)"); return p; }
}
#endif
