LOG_LEVEL=5
DEBUG_LOG_LEVEL=14
NVCC=/usr/local/cuda-12.8/bin/nvcc
CXX=/usr/local/gcc-11.2.0/bin/g++
CUDA_ROOT=/usr/local/cuda-12.8
UAMMD_ROOT=../../
INCLUDEFLAGS=-I. -I$(CUDA_ROOT)/include -I$(UAMMD_ROOT)/src -I$(UAMMD_ROOT)/src/third_party
COMMON_NVCCFLAGS=-ccbin=$(CXX) -std=c++14 $(INCLUDEFLAGS) --extended-lambda
LDLIBS=-lz
all: kg_assoc_dimer kg_assoc_k1 kg_assoc_star_audit kg_assoc_stars kg_assoc_star_equilibrate kg_assoc_stress_test kg_assoc_production
kg_assoc_dimer: kg_assoc_dimer.cu kg_assoc_cli.cuh kg_assoc_cutoff_audit.cuh kg_assoc_state.cuh kg_assoc_interactors.cuh kg_assoc_kinetics.cuh Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) -O3 $< -o $@ $(LDLIBS)
kg_assoc_k1: kg_assoc_k1.cu kg_assoc_cutoff_audit.cuh kg_assoc_state.cuh kg_assoc_interactors.cuh kg_assoc_kinetics.cuh Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) -O3 $< -o $@ $(LDLIBS)
kg_assoc_star_audit: kg_assoc_star_audit.cu kg_assoc_star_topology.cuh ../KG/kg_lammps_io.cuh Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) -O3 $< -o $@ $(LDLIBS)
kg_assoc_stars: kg_assoc_stars.cu kg_assoc_star_runtime.cuh kg_assoc_star_topology.cuh kg_assoc_state.cuh kg_assoc_kinetics.cuh kg_assoc_interactors.cuh ../KG/kg_lammps_io.cuh ../KG/kg_runtime.cuh ../KG/kg_interactors.cuh Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) -O3 $< -o $@ $(LDLIBS)
kg_assoc_star_equilibrate: kg_assoc_star_equilibrate.cu kg_assoc_star_topology.cuh ../KG/kg_lammps_io.cuh ../KG/kg_runtime.cuh ../KG/kg_interactors.cuh Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) -O3 $< -o $@ $(LDLIBS)
kg_assoc_stress_test: kg_assoc_stress_test.cu kg_assoc_interactors.cuh kg_assoc_state.cuh ../KG/kg_runtime.cuh ../KG/kg_interactors.cuh Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) -O3 $< -o $@ $(LDLIBS)
kg_assoc_production: kg_assoc_production.cu kg_assoc_star_runtime.cuh kg_assoc_star_topology.cuh kg_assoc_state.cuh kg_assoc_kinetics.cuh kg_assoc_interactors.cuh ../KG/correlator.cpp ../KG/correlator.h ../KG/kg_lammps_io.cuh ../KG/kg_runtime.cuh ../KG/kg_interactors.cuh Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) -O3 kg_assoc_production.cu ../KG/correlator.cpp -o $@ $(LDLIBS)
debug: kg_assoc_dimer.cu kg_assoc_cli.cuh kg_assoc_state.cuh kg_assoc_interactors.cuh kg_assoc_kinetics.cuh Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(DEBUG_LOG_LEVEL) -O0 -g -G kg_assoc_dimer.cu -o kg_assoc_dimer_debug $(LDLIBS)
clean:
	rm -f kg_assoc_dimer kg_assoc_dimer_debug kg_assoc_k1 kg_assoc_star_audit kg_assoc_stars kg_assoc_star_equilibrate kg_assoc_stress_test kg_assoc_production
