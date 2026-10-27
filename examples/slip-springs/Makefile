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
KG_DIR := $(abspath $(PROJECT_DIR)/../KG)
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

$(GPU_BUILD)/rouse: $(PROJECT_DIR)/rouse.cu $(PROJECT_DIR)/rouse.cuh $(PROJECT_DIR)/stream_correlator.h $(PROJECT_DIR)/stream_pipeline.cuh $(PROJECT_DIR)/cpu_workers.h $(KG_DIR)/correlator.cpp $(PROJECT_DIR)/Makefile
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) -DSLIP_SPRINGS_DIR='"$(PROJECT_DIR)"' -MMD -MP -MF $@.d $< $(KG_DIR)/correlator.cpp -Xcompiler -pthread -o $@ $(LDLIBS)

$(GPU_BUILD)/rouse_tests: $(PROJECT_DIR)/tests/rouse_tests.cu $(PROJECT_DIR)/rouse.cuh $(PROJECT_DIR)/Makefile
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) -MMD -MP -MF $@.d $< -o $@ $(LDLIBS)

$(BUILD)/correlator_smoke: $(PROJECT_DIR)/correlator_smoke.cpp $(KG_DIR)/correlator.cpp $(KG_DIR)/correlator.h $(PROJECT_DIR)/Makefile
	mkdir -p $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I$(KG_DIR) $(PROJECT_DIR)/correlator_smoke.cpp $(KG_DIR)/correlator.cpp -o $@ $(LDLIBS)

check-correlator: correlator
	$(BUILD)/correlator_smoke
check: all pipeline-tests check-workers
	$(BUILD)/correlator_smoke
	$(GPU_BUILD)/smoke_test
	$(GPU_BUILD)/rouse_tests
	$(GPU_BUILD)/pipeline_tests
	python3 $(PROJECT_DIR)/tests/test_theory.py
	python3 $(PROJECT_DIR)/tests/test_stream_theory.py
	python3 $(PROJECT_DIR)/tests/test_stress.py
	python3 $(PROJECT_DIR)/tests/test_cli.py $(GPU_BUILD)/rouse
	python3 $(PROJECT_DIR)/tests/test_stream.py $(GPU_BUILD)/rouse

double:
	$(MAKE) -f $(PROJECT_DIR)/Makefile PRECISION=double all

# Explicit artifact list: never follow a configurable output/root variable here.
clean:
	rm -f $(PROJECT_DIR)/build/single/smoke_test $(PROJECT_DIR)/build/single/smoke_test.d $(PROJECT_DIR)/build/double/smoke_test $(PROJECT_DIR)/build/double/smoke_test.d $(PROJECT_DIR)/build/correlator_smoke $(PROJECT_DIR)/build/stream_lifetime_asan $(PROJECT_DIR)/build/cpu_workers_asan $(foreach p,single double,$(PROJECT_DIR)/build/$(p)/rouse $(PROJECT_DIR)/build/$(p)/rouse.d $(PROJECT_DIR)/build/$(p)/rouse_tests $(PROJECT_DIR)/build/$(p)/rouse_tests.d $(PROJECT_DIR)/build/$(p)/pipeline_tests)

-include $(GPU_BUILD)/smoke_test.d $(GPU_BUILD)/rouse.d $(GPU_BUILD)/rouse_tests.d

.PHONY: check-lifetime
check-lifetime:
	mkdir -p $(BUILD)
	$(CXX) -std=c++17 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(PROJECT_DIR)/tests/stream_lifetime.cpp $(KG_DIR)/correlator.cpp -o $(BUILD)/stream_lifetime_asan
	ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 $(BUILD)/stream_lifetime_asan

$(GPU_BUILD)/pipeline_tests: $(PROJECT_DIR)/tests/pipeline_tests.cu $(PROJECT_DIR)/stream_pipeline.cuh $(PROJECT_DIR)/cpu_workers.h $(PROJECT_DIR)/stream_correlator.h $(PROJECT_DIR)/rouse.cuh $(KG_DIR)/correlator.cpp
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) $< $(KG_DIR)/correlator.cpp -Xcompiler -pthread -o $@ $(LDLIBS)
.PHONY: pipeline-tests
pipeline-tests: $(GPU_BUILD)/pipeline_tests

.PHONY: check-workers
check-workers:
	mkdir -p $(BUILD)
	$(CXX) -std=c++17 -O1 -g -pthread -fsanitize=address,undefined -fno-omit-frame-pointer $(PROJECT_DIR)/tests/cpu_workers.cpp $(KG_DIR)/correlator.cpp -o $(BUILD)/cpu_workers_asan
	ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 $(BUILD)/cpu_workers_asan

# Separate Stage 4A.2 targets; historical all/check/Rouse rules are unchanged.
.PHONY: semiflexible check-semiflexible
semiflexible: $(GPU_BUILD)/semiflexible
$(GPU_BUILD)/semiflexible: $(PROJECT_DIR)/semiflexible.cu $(PROJECT_DIR)/dynamical_observer.h $(PROJECT_DIR)/dynamical_observables.h $(PROJECT_DIR)/orientation_correlator.h $(PROJECT_DIR)/e1_equilibrium_observer.h $(PROJECT_DIR)/semiflexible.cuh $(PROJECT_DIR)/semiflexible_slipspring.cuh $(PROJECT_DIR)/fixed_slip_springs.h $(PROJECT_DIR)/slip_hopping.h $(PROJECT_DIR)/slip_hopping.cuh $(PROJECT_DIR)/slip_renewal.cuh $(PROJECT_DIR)/semiflexible_scalar_output.h $(PROJECT_DIR)/semiflexible_stress.cuh $(PROJECT_DIR)/semiflexible_stress_stream.h $(PROJECT_DIR)/tests/chain_major_correlator.h $(PROJECT_DIR)/cpu_workers.h $(PROJECT_DIR)/stream_correlator.h $(KG_DIR)/correlator.cpp
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) -DSLIP_SPRINGS_DIR='"$(PROJECT_DIR)"' -MMD -MP -MF $@.d $< $(KG_DIR)/correlator.cpp -Xcompiler -pthread -o $@ $(LDLIBS)
check-semiflexible: semiflexible
	python3 $(PROJECT_DIR)/tests/test_semiflexible_gpu.py $(GPU_BUILD)/semiflexible
	python3 $(PROJECT_DIR)/tests/test_semiflexible_host.py $(GPU_BUILD)/semiflexible
	python3 $(PROJECT_DIR)/tests/test_semiflexible_reference.py
-include $(GPU_BUILD)/semiflexible.d

.PHONY: clean-semiflexible
clean-semiflexible:
	rm -f $(PROJECT_DIR)/build/single/semiflexible $(PROJECT_DIR)/build/single/semiflexible.d $(PROJECT_DIR)/build/double/semiflexible $(PROJECT_DIR)/build/double/semiflexible.d $(PROJECT_DIR)/build/single/every_step_gpu_stress_benchmark $(PROJECT_DIR)/build/double/every_step_gpu_stress_benchmark

# Isolated Stage 4A.3c acquisition benchmark; it never links the simulator driver.
.PHONY: every-step-gpu-benchmark
every-step-gpu-benchmark: $(GPU_BUILD)/every_step_gpu_stress_benchmark
$(GPU_BUILD)/every_step_gpu_stress_benchmark: $(PROJECT_DIR)/tests/every_step_gpu_stress_benchmark.cu $(PROJECT_DIR)/semiflexible.cuh $(PROJECT_DIR)/semiflexible_stress.cuh $(PROJECT_DIR)/semiflexible_stress_stream.h
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) $< -o $@ $(LDLIBS)

.PHONY: check-semiflexible-stress
$(BUILD)/semiflexible_stress_correlator: $(PROJECT_DIR)/tests/semiflexible_stress_correlator.cpp $(PROJECT_DIR)/semiflexible_stress_stream.h $(PROJECT_DIR)/cpu_workers.h $(PROJECT_DIR)/stream_correlator.h $(KG_DIR)/correlator.cpp
	mkdir -p $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $< $(KG_DIR)/correlator.cpp -pthread -o $@ $(LDLIBS)
check-semiflexible-stress: semiflexible $(BUILD)/semiflexible_stress_correlator
	timeout 180s python3 $(PROJECT_DIR)/tests/test_semiflexible_stress_gpu.py $(GPU_BUILD)/semiflexible $(BUILD)/semiflexible_stress_correlator

# E1 fixed-anchor development-only smoke (requires CUDA GPU).
.PHONY: check-fixed-slip-springs
check-fixed-slip-springs: check-fixed-slip-initialization semiflexible $(GPU_BUILD)/fixed_slip_forces
	$(GPU_BUILD)/fixed_slip_forces
	python3 $(PROJECT_DIR)/tests/test_fixed_slip_springs.py $(GPU_BUILD)/semiflexible

# CPU initializer tests remain runnable without a CUDA toolkit or GPU.
.PHONY: check-fixed-slip-initialization
$(BUILD)/fixed_slip_initialization: $(PROJECT_DIR)/tests/fixed_slip_initialization.cpp $(PROJECT_DIR)/fixed_slip_springs.h
	mkdir -p $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -UNDEBUG $< -o $@ $(LDLIBS)
check-fixed-slip-initialization: $(BUILD)/fixed_slip_initialization
	$(BUILD)/fixed_slip_initialization

$(GPU_BUILD)/fixed_slip_forces: $(PROJECT_DIR)/tests/fixed_slip_forces.cu $(PROJECT_DIR)/semiflexible_slipspring.cuh $(PROJECT_DIR)/semiflexible.cuh
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) -UNDEBUG $< -o $@ $(LDLIBS)

.PHONY: check-slip-hopping-cpu check-slip-hopping
$(BUILD)/slip_hopping_limits: $(PROJECT_DIR)/tests/slip_hopping_limits.cpp $(PROJECT_DIR)/slip_hopping.h
	mkdir -p $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -UNDEBUG $< -o $@ $(LDLIBS)
check-slip-hopping-cpu: $(BUILD)/slip_hopping_limits
	$(BUILD)/slip_hopping_limits
	timeout 120s python3 $(PROJECT_DIR)/tests/test_slip_hopping_reference.py
$(GPU_BUILD)/slip_hopping_gpu: $(PROJECT_DIR)/tests/slip_hopping_gpu.cu $(PROJECT_DIR)/slip_hopping.cuh $(PROJECT_DIR)/slip_hopping.h $(PROJECT_DIR)/semiflexible.cuh $(PROJECT_DIR)/semiflexible_slipspring.cuh
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) $< -o $@ $(LDLIBS)
check-slip-hopping: check-slip-hopping-cpu semiflexible $(GPU_BUILD)/slip_hopping_gpu
	timeout 180s python3 $(PROJECT_DIR)/tests/test_slip_hopping_gpu.py $(GPU_BUILD)/slip_hopping_gpu $(GPU_BUILD)/semiflexible

.PHONY: check-slip-renewal-cpu check-slip-renewal
check-slip-renewal-cpu:
	timeout 120s python3 $(PROJECT_DIR)/tests/test_slip_renewal_reference.py
$(GPU_BUILD)/slip_renewal_gpu: $(PROJECT_DIR)/tests/slip_renewal_gpu.cu $(PROJECT_DIR)/slip_renewal.cuh $(PROJECT_DIR)/slip_hopping.cuh $(PROJECT_DIR)/slip_hopping.h $(PROJECT_DIR)/semiflexible.cuh $(PROJECT_DIR)/semiflexible_slipspring.cuh
	mkdir -p $(GPU_BUILD)
	$(NVCC) -ccbin=$(CXX) $(CPPFLAGS) $(INCLUDES) $(NVCCFLAGS) $(ARCH_FLAGS) $(PRECISION_FLAGS) $< -o $@ $(LDLIBS)
check-slip-renewal: check-slip-renewal-cpu semiflexible $(GPU_BUILD)/slip_renewal_gpu
	timeout 180s python3 $(PROJECT_DIR)/tests/test_slip_renewal_gpu.py $(GPU_BUILD)/slip_renewal_gpu $(GPU_BUILD)/semiflexible
