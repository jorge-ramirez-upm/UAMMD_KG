# Read-only audit and CPU reproduction

Run from repository root. No command launches MD or a GPU executable.

```bash
timeout 600 python3 examples/KG_Assoc/reviews/rheology_existing_method_20261023/VERIFY.txt
out=$(mktemp -d /tmp/kg_rheology_review.XXXXXXXX)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/kg_rheology_matplotlib
timeout 600 python3 examples/KG_Assoc/reviews/rheology_existing_method_20261023/REPLAY.txt --output "$out/replay"
timeout 600 python3 examples/KG_Assoc/reviews/rheology_existing_method_20261023/CPU_TESTS.txt --output "$out/native_tests"
```

REPLAY uses the original five 32M `.stress_correlator`/`.state` pairs and native logs.
It invokes the unchanged P4 analyzer API, writes a new directory, checks normalization
and exact support, and does not overwrite historical summaries. In a data-free clone,
PILOT_INPUTS.tar.gz preserves these original bytes at repository-relative paths;
extract only into a fresh scratch tree, never over an existing data directory. The
source analyzer is also included in that archive; original source paths/hashes are
in replay/INPUTS.sha256. No missing MD microtrajectory is synthesized. In the original
host workspace VERIFY directly authenticates all original paths.

The replay reproduces the current method's five-file tail/viscosity result and also
shows its very imprecise two-file noise-floor classification. The older on-disk
summary labels are preserved and discussed, not expected to match a later classifier.
LAG_GRID.csv derives actual populated-count grids without feeding a fictitious
100M-sample trajectory. Its 32M result is checked at every bin against all five real
files. Resources/longer grids are prospective arithmetic, not simulations.

CPU_TESTS runs six deterministic checks, then freshly compiles and executes the two
existing C++ correlator tests with GCC11.2, -O3, into its fresh output directory; it
also runs the unchanged analyzer self-test (fourteen regimes). Source/build identities
are retained in CPP_BUILD_IDENTITIES.log and NATIVE.log. This is not an NVCC/GPU test.
PLOT.txt regenerates PILOT_REVIEW.png from the reproduced CSVs; its shaded intervals
use the five families, not pair counts. Full raw lag tails are shown with the
8-contribution eligibility horizon marked; unsupported points are not terminal evidence.

SOURCE_INPUTS.sha256 binds the implementation and earlier project decisions inspected.
HISTORICAL_CANDIDATE_SOURCE.log pins Git blobs demonstrating that pilot builds predate
the periodic cell-assignment correction. No historical GPU executable is reconstructed
from a SHA or claimed rerun. All original files remain immutable.
