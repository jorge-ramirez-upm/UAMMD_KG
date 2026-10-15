# Standalone project build; no repository-wide targets are invoked.
PROJECT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
UAMMD_ROOT ?= $(abspath $(PROJECT_DIR)/../..)
CUDA_HOME ?=
NVCC ?= $(if $(strip $(CUDA_HOME)),$(CUDA_HOME)/bin/nvcc,nvcc)
CXX ?= g++
PRECISION ?= single
CUDA_ARCH ?=
CPPFLAGS ?=
CXXFLAGS ?= -O2 -std=c++17
NVCCFLAGS ?= -O2 -std=c++17 --extended-lambda
LDLIBS ?=

ifeq ($(PRECISION),double)
PRECISION_FLAGS := -DDOUBLE_PRECISION
else ifeq ($(PRECISION),single)
PRECISION_FLAGS :=
else
$(error PRECISION must be single or double)
endif

BUILD := $(PROJECT_DIR)/build
GPU_BUILD := $(BUILD)/$(PRECISION)
KG_DIR := $(UAMMD_ROOT)/examples/KG
INCLUDES := -I$(UAMMD_ROOT)/src -I$(UAMMD_ROOT)/src/third_party
ARCH_FLAGS := $(if $(strip $(CUDA_ARCH)),-arch=$(CUDA_ARCH),)

.PHONY: all cuda correlator rouse rouse-tests check check-correlator double clean
all: cuda correlator rouse rouse-tests
cuda: $(GPU_BUILD)/smoke_test
correlator: $(BUILD)/correlator_smoke
rouse: $(GPU_BUILD)/rouse
rouse-tests: $(GPU_BUILD)/rouse_tests

$(GPU_BUILD)/smoke_test: $(PROJECT_DIR)/smoke_test.cu $(PROJECT_DIR)/Makefile
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) -MMD -MP -MF $@.d $< -o $@ $(LDLIBS)

$(GPU_BUILD)/rouse: $(PROJECT_DIR)/rouse.cu $(PROJECT_DIR)/rouse.cuh $(PROJECT_DIR)/Makefile
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) -DSLIP_SPRINGS_DIR='"$(PROJECT_DIR)"' -MMD -MP -MF $@.d $< -o $@ $(LDLIBS)

$(GPU_BUILD)/rouse_tests: $(PROJECT_DIR)/tests/rouse_tests.cu $(PROJECT_DIR)/rouse.cuh $(PROJECT_DIR)/Makefile
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) -MMD -MP -MF $@.d $< -o $@ $(LDLIBS)

$(BUILD)/correlator_smoke: $(PROJECT_DIR)/correlator_smoke.cpp $(KG_DIR)/correlator.cpp $(KG_DIR)/correlator.h $(PROJECT_DIR)/Makefile
	mkdir -p $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I$(KG_DIR) $(PROJECT_DIR)/correlator_smoke.cpp $(KG_DIR)/correlator.cpp -o $@ $(LDLIBS)

check-correlator: correlator
	$(BUILD)/correlator_smoke
check: all
	$(BUILD)/correlator_smoke
	$(GPU_BUILD)/smoke_test
	$(GPU_BUILD)/rouse_tests
	python3 $(PROJECT_DIR)/tests/test_theory.py
	python3 $(PROJECT_DIR)/tests/test_cli.py $(GPU_BUILD)/rouse

double:
	$(MAKE) -f $(PROJECT_DIR)/Makefile PRECISION=double all

# Explicit artifact list: never follow a configurable output/root variable here.
clean:
	rm -f $(PROJECT_DIR)/build/single/smoke_test $(PROJECT_DIR)/build/single/smoke_test.d $(PROJECT_DIR)/build/double/smoke_test $(PROJECT_DIR)/build/double/smoke_test.d $(PROJECT_DIR)/build/correlator_smoke $(foreach p,single double,$(PROJECT_DIR)/build/$(p)/rouse $(PROJECT_DIR)/build/$(p)/rouse.d $(PROJECT_DIR)/build/$(p)/rouse_tests $(PROJECT_DIR)/build/$(p)/rouse_tests.d)

-include $(GPU_BUILD)/smoke_test.d $(GPU_BUILD)/rouse.d $(GPU_BUILD)/rouse_tests.d
