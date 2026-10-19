# Stage 4A.3c Milestone B — every-step stress pipeline implementation

This implementation adds the explicit `--stress-mode every-step` path only.
Legacy `off`, `diagnostic` and `stream` modes retain their prior sample clocks
and code paths. No campaign was launched and this report does not claim GPU
validation or scientific acceptance.

## Design

Every-step mode calls the existing stretch/bend/channel kernels at state0 and
after every Euler–Maruyama update. Scalar diagnostics remain controlled only by
`--sample`; the new stress clock is `dt`. Each six-component frame enters one of
two bounded device slabs. A ready event orders its async pinned D2H copy on a
transfer stream; the consumer waits for completion and invokes the validated
chain-major bank through persistent fixed-range workers. A full pair of slots
blocks the producer until ownership returns. It never drops/merges frames.

The existing stress diagnostic key remains read after each acquisition, so a
nonfinite/symmetry/trace failure still fails before another trajectory step and
retains the existing geometry snapshot path. Stretch then bending then channels
are unchanged, preserving complete stretch–bend products. Chain-major workers
keep each chain chronological and the existing `OwnedCorrelator6`/chain-cluster
reduction remains the estimator.

Defaults for the new mode are batch256 and slots64. These are engineering
defaults, not approved production physics settings. At C=2048 a double six-value
frame is 98,304 bytes; two 256-frame device slabs plus two pinned slabs each use
48 MiB. `stress_metadata.json` records slot capacity, maximum in-flight slots
and producer buffer wait time for bounded queue/backpressure review. The correlator allocation is checked against `--correlator-mib`; levels
and physical lag coverage must be selected from the intended duration before a
production run. No assumption that 24 levels/64 slots is admissible is made.

## CPU checks and GPU command

Run CPU-only contract/equivalence coverage:

```sh
python3 examples/slip-springs/tests/test_every_step_pipeline_contract.py
```

On `cholosimeone`, after reviewing a clean checkout and without touching either
protected checkout:

```sh
cd /tmp/UAMMD_KG-slip-springs-dev
CUDA_HOME=/usr/local/cuda-13.0 CXX=g++ CUDA_ARCH=sm_86 \
  bash examples/slip-springs/tests/run_stage4a3c_every_step_pipeline_validation.sh
```

The GPU run builds both precisions and runs N8 κ=10 stress-off/on replay with
batches1/7/256 (including many turnovers and a final partial batch), then N8
κ=0 fast-path checks. It is bounded to120 seconds per build/test invocation.
Run the Milestone-A oracle/evidence runner separately for tensor numerical
validation, GPU identity and binary receipts. The N8 batch1/7 bounded replay is
a simultaneous producer/consumer check; inspect its slot-capacity, in-flight and
producer-wait metadata. A larger throughput fixture is still required before a
production performance claim.

## Limits

The new path writes correlations and metadata but does not add orientation/C1/C2
sampling. GPU validation, queue-occupancy telemetry and same-host performance
remain pending user execution. Milestone B is implementation-complete only after
those host results are reviewed; it is not scientifically accepted here.
