# Reproducing this CPU-only review

Run from the repository root on the Linux host holding the authenticated manual
dataset. No command below launches a simulation, allocates streams, registers
acceptance or modifies a simulation output. Python3, NumPy and Matplotlib versions
are pinned in ENVIRONMENT.log. Existing absolute dataset paths are part of the
provenance contract; a Git clone alone does not contain the ignored raw simulation
data. Do not rewrite plans or bypass path authentication to relocate those data.

## Inspect the committed analysis without simulation data

Each replay archive contains six records for one history: summary, full returned
record, all enriched time series, all window statistics, shifted-window statistics
and exact network/residence histories. It is derived evidence, not a physical
restart. Allocate a fresh temporary directory so existing evidence is preserved:

```bash
set -euo pipefail
review="$PWD/examples/KG_Assoc/reviews/e2_ea_transfer_24m_joint_20261018"
inspection="$(mktemp -d /tmp/ea24m-inspection.XXXXXXXX)"
for archive in "$review"/replay/*.tar.gz; do
    timeout 600 tar -xzf "$archive" -C "$inspection"
done
cp "$review/RESULTS.log" "$inspection/RESULTS.log"
export EA24M_ANALYSIS="$inspection"
timeout 600 python3 "$review/ANALYSIS_TESTS.txt"
export MPLCONFIGDIR="$(mktemp -d /tmp/ea24m-matplotlib.XXXXXXXX)"
timeout 600 python3 "$review/PLOTS_DRIVER.txt" \
    --analysis "$inspection" --output "$inspection/plots"
```

The raw-data host is required for whole-campaign preservation and independent
accepted-event/endpoint revalidation. Archived figures themselves are hashed;
regenerated PDF metadata need not be byte-identical. Derived numerical results
must agree under the documented estimator and software versions.

## Independently replay all nine histories on the raw-data host

Every distinct history is one bounded CPU job. The 600-second timeout is mandatory;
stop and investigate an analysis timeout instead of relaxing it. The existing
manual campaign state is read-only. A fresh directory avoids overwriting previous
analysis records. No extra MD steps are computed.

```bash
set -euo pipefail
review="$PWD/examples/KG_Assoc/reviews/e2_ea_transfer_24m_joint_20261018"
fresh="$(mktemp -d /tmp/ea24m-replay.XXXXXXXX)"
timeout 600 python3 "$review/ANALYSIS_DRIVER.txt" --self-test
for index in 0 1 2 3 4 5 6 7 8; do
    timeout 600 python3 "$review/ANALYSIS_DRIVER.txt" \
        --history "$index" --output "$fresh" || exit 1
    timeout 600 python3 "$review/SHIFTED_DRIVER.txt" \
        --history "$index" --analysis "$fresh" || exit 1
done
timeout 600 python3 "$review/ANALYSIS_DRIVER.txt" --merge --output "$fresh"
export EA24M_ANALYSIS="$fresh"
timeout 600 python3 "$review/ANALYSIS_TESTS.txt"
mkdir "$fresh/tables"
timeout 600 python3 "$review/SUMMARIZE_DRIVER.txt" \
    --analysis "$fresh" --output "$fresh/tables"
export MPLCONFIGDIR="$(mktemp -d /tmp/ea24m-matplotlib.XXXXXXXX)"
timeout 600 python3 "$review/PLOTS_DRIVER.txt" \
    --analysis "$fresh" --output "$fresh/plots"
```

History index order is Ea6 r001/r002/r003, Ea8 r001/r002/r003, Ea10
r001/r002/r003, exactly as the durable manual state. Each replay authenticates
its saved approval, command, original parent, build, completion/output hashes,
exact device readback and every recorded oracle sweep, then calls the existing
full chemical/numerical validator. It compares the independently generated
validation object with the manual runner's completion receipt.

ANALYSIS_DRIVER.txt reuses the existing segment/recovery/statistical helpers.
The only review-local estimator change is an equivalent FFT implementation of
the same biased ACF and first-nonpositive truncation. Deterministic tests compare
direct/FFT values on five synthetic fixtures and three observables from each
real history. Constant-bin mixing flags retain the existing review policy.
Exact graph/residence integration additionally checks simultaneous events,
parallel bonds and boundary censoring. No shared code was changed. Review code
is archived as .txt and structured results as .log to preserve the established
scientific-source build inventory.

## Integrity and test records

```bash
set -euo pipefail
review="$PWD/examples/KG_Assoc/reviews/e2_ea_transfer_24m_joint_20261018"
timeout 600 python3 "$review/VERIFY_DRIVER.txt"
```

VERIFY_DRIVER authenticates current raw outputs, plans, receipts, twelve formal
acceptances, historical evidence, builds and all dossier artifacts. It does not
rerun nine long CPU replays inside one unbounded job. Their independent replay
results are archived and can each be reproduced with the commands above.

E2_REGRESSION.log records the established 189-test E2 suite, rechecked with the
final driver in E2_REGRESSION_FINAL.log; TRANSFER_TESTS.log
records 14 transfer tests; ANALYSIS_TESTS_FINAL.log records 14 review tests.
CPU_TEST_DRIVER.txt reproduces the established suite and writes exclusively to
a fresh directory passed with `--output`. Review and transfer tests never invoke
a GPU path. The full-discovery REGRESSION.log is preserved, including the two
obsolete acceptance-count assertions and unrelated missing correlator import.
These are not represented as passing tests.

The proposed Ea8/Ea10 extensions in ASSESSMENT.md are scientific recommendations
only. Preparing/executing either requires separate authorization and a user-run
handoff under AGENTS.md. This dossier contains no extension launch commands.
