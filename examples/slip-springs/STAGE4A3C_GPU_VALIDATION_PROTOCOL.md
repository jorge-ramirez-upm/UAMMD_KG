# Stage 4A.3c GPU validation protocol — Milestone A

This protocol validates the existing every-step benchmark on `cholosimeone`.
It does not authorize the chain-major/asynchronous production integration in
Milestone B. Run it only from `/tmp/UAMMD_KG-slip-springs-dev`; the runner rejects
a dirty worktree, a checkout not descended from `ac468c7`, a non-13.0 toolkit,
missing protected checkouts, and a pre-existing result directory.

```sh
cd /tmp/UAMMD_KG-slip-springs-dev
git pull --ff-only origin slip-springs
CUDA_HOME=/usr/local/cuda-13.0 CXX=g++ CUDA_ARCH=sm_86 \
  bash examples/slip-springs/tests/run_stage4a3c_gpu_validation.sh
```

`CXX=g++` is intentional: the runner records its identity and lets CUDA 13.0
perform the compatibility check during the bounded build. Do not install a
compiler, alter alternatives, drivers, CUDA, packages or either protected
checkout to make it pass. If the local CUDA 13.0 install is elsewhere, set only
`CUDA_HOME` to its absolute directory. Every build/test command has a 120-second
wall-time cap. The result root defaults to a unique `/tmp/stage4a3c-gpu-validation-*
` directory and can be explicitly selected with `STAGE4A3C_RESULTS_ROOT` if it
does not already exist.

Expected evidence includes `commands/`, command logs, `status.tsv`, `git-head`,
protected-checkout SHA/status logs, GPU/driver/memory query, compiler/toolkit/OS/
CPU/load identities, binary SHA-256 values and `RESULT`. A nonzero command exits
the runner immediately but leaves all prior logs and `status.tsv` for review.

Coverage is intentionally bounded:

* both precision simulator builds and every-step benchmark builds;
* the existing prescribed-coordinate stretch/bend/total tensor oracle in both
  precisions, including all six derived channels and zero-bending behavior;
* existing stress-off/on deterministic trajectory replay, stress stream order,
  incomplete final streaming batches, diagnostics and failure fixtures;
* direct, bounded batch and benchmark-only async every-step transport hashes in
  each precision, for κ=0 at capacity256 and active κ=10 at capacities256 and
  1,024. Every replay contains nine frames (step0 through step8), intentionally
  leaving a partial final batch at either capacity; a hash mismatch, frame-count
  mismatch, dropped final partial transfer or mode reordering fails.

Review `RESULT`, every `status.tsv` line and the logs before treating GPU
correctness as established. No rate matrix or production pipeline work occurs in
this protocol. The existing benchmark capacity comparison (256/1024) and full
throughput matrix remain a separate post-correctness measurement action.
