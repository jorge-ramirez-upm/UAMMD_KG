

#Default log level is 5, which prints up to MESSAGE, 0 will only print critical errors and 14 will print everything up to the most low level debug information
LOG_LEVEL=5
DEBUG_LOG_LEVEL=14

NVCC=nvcc
CXX=/usr/local/gcc-11.2.0/bin/g++

CUDA_ROOT=$(shell dirname `which nvcc`)/..
UAMMD_ROOT=../../
#Uncomment to compile in double precision mode
#DOUBLE_PRECISION=-DDOUBLE_PRECISION
INCLUDEFLAGS=-I. -I$(CUDA_ROOT)/include -I$(UAMMD_ROOT)/src -I$(UAMMD_ROOT)/src/third_party
COMMON_NVCCFLAGS=-ccbin=$(CXX) -std=c++14 $(INCLUDEFLAGS) $(DOUBLE_PRECISION) --extended-lambda
LDLIBS=-lz
RELEASE_NVCCFLAGS=-O3
DEBUG_NVCCFLAGS=-O0 -g -G

PROGRAMS=kg_uammd
DEBUG_PROGRAMS=$(addsuffix _debug,$(PROGRAMS))
UTILITY_HEADERS=kg_cli.cuh kg_lammps_io.cuh kg_interactors.cuh kg_runtime.cuh

all: $(PROGRAMS)
debug: $(DEBUG_PROGRAMS)

kg_uammd: kg_uammd.cu $(UTILITY_HEADERS) Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) $(RELEASE_NVCCFLAGS) $< -o $@ $(LDLIBS)

kg_uammd_debug: kg_uammd.cu $(UTILITY_HEADERS) Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(DEBUG_LOG_LEVEL) $(DEBUG_NVCCFLAGS) $< -o $@ $(LDLIBS)

%: %.cu Makefile
	$(NVCC) $(COMMON_NVCCFLAGS) -DMAXLOGLEVEL=$(LOG_LEVEL) $(RELEASE_NVCCFLAGS) $< -o $(@:.out=) $(LDLIBS)

clean: $(patsubst %, %.clean, $(PROGRAMS) $(DEBUG_PROGRAMS))

%.clean:
	rm -f $(@:.clean=)
