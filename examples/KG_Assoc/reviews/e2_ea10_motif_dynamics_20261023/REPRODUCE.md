# CPU-only reproduction

Run from `/home/jramirez/UAMMD_KG`, using Python with NumPy and Matplotlib (versions
in ENVIRONMENT.log). Every computation below is bounded by `timeout 600`. No command
calls a native simulation or GPU launcher. Original data paths are hash-bound absolute
paths on this host. A clone contains archived derived data and metadata, not all raw
simulation outputs or native binaries; full raw replays require those authenticated
original files. Do not invent absent inputs.

Read-only authentication:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/VERIFY.txt
```

Focused tests and shared established E2 regression driver:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/ea10_motif_matplotlib
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/TESTS.txt
work=$(mktemp -d /tmp/ea10_motif_reproduce.XXXXXXXX)
export EA10_MOTIF_REPRO_WORK="$work"
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_transfer_24m_joint_20261018/CPU_TEST_DRIVER.txt --output "$work/shared"
```

Extract the authenticated derived ledgers into that fresh scratch directory. This
writes no simulation output or historical evidence. The archive uses gzip-compressed
JSON; ANALYSIS.sha256 pins each uncompressed payload. The verifier above authenticates
both compressed files and these payloads.

```bash
python3 - <<'PY'
import gzip, os
from pathlib import Path
folder=Path('examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023')
work=Path(os.environ['EA10_MOTIF_REPRO_WORK'])
for source in (folder/'analysis').glob('*.gz'):
    with (work/source.stem).open('xb') as target:
        target.write(gzip.decompress(source.read_bytes()))
PY
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/SUMMARIZE.txt --work "$work" --output "$work/summary"
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/TEST_DATA.txt --work "$work" --summary "$work/summary"
```

To independently replay original accepted events instead, use a separate fresh
scratch directory and run each family as its own bounded CPU analysis:

```bash
raw=$(mktemp -d /tmp/ea10_motif_raw.XXXXXXXX)
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/ANALYZE.txt --replica 1 --output "$raw"
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/ANALYZE.txt --replica 2 --output "$raw"
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/ANALYZE.txt --replica 3 --output "$raw"
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/SUMMARIZE.txt --work "$raw" --output "$raw/summary"
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea10_motif_dynamics_20261023/TEST_DATA.txt --work "$raw" --summary "$raw/summary"
```

ANALYZE refuses existing ledger filenames. SUMMARIZE requires a new directory.
These are analysis partitions by original preparation family, not small simulations
or segments of a new long computation. Each actual job completed below ten minutes.

PACK.txt documents archival assembly: `--work RAW --summary SUMMARY --preserved
PRESERVED.sha256 --output NEW_ARCHIVE`. It requires fresh artifact destinations,
authenticates original inputs and approval bindings, and only copies/compresses
existing evidence. PRESERVED.sha256 is the pre-analysis snapshot (4,881 file bindings).
PROVENANCE.tar.gz contains exact original metadata bytes; PROVENANCE.sha256 maps their
absolute original paths, while archive members are repository-relative paths.
INTEGRITY.sha256 covers all dossier artifacts except itself (final commit identity is
reported by VERIFY, avoiding a self-referential commit hash).

Tables distinguish event-integrated and sampled measures. PARTICIPATION.csv uses
exact triangle-incidence exposure; WINDOWS/CONDITIONALS/PMF use right-endpoint
1k-step samples with the initial boundary frame removed once per segment. Nine
initial frames remain in archived raw ledgers for continuity checks. Pooled static
80M family histories are descriptive; dynamics never cross 24M or 56M. Kaplan–Meier
curves exclude initial unknown-age motifs and retain terminal right censoring;
positive-only results explicitly omit zero-duration episodes, with all-episode results
also retained. Thresholds 35/40/45 are sensitivity choices, not detected basin boundaries.

Plots: `structural_history.png` shows family-resolved 1M/4M histories and MD boundaries;
`regime_distributions_residence.png` shows segment distributions and exact ≥40 dwell
intervals (arrows denote right censoring); `joint_distributions.png` shows coupled
static states; `incident_survival.png` shows censor-aware incident motif survival;
`participation_concentration.png` compares identity concentration;
`segment_correlations.png` shows correlation sensitivity; `block_sensitivity.png`
shows segment-local SEM versus block size. No plot implies independent frames or
stationary equilibrium errors.

ABSENCE_EPISODES.csv retains every within-segment absence after an observed motif
death, ending at its return or right-censored at the segment endpoint. No pre-history
waiting time or non-return is silently replaced by an observed return. Joint plots
use blue raw 2D sample counts with panel-local y bins/color scales; orange points
are conditional means at each integer L2. Color intensity is not a cross-panel
probability or significance comparison.

The IAT convention is tau = 0.5 + sum of the biased normalized ACF through the
lag preceding its first nonpositive value, times the 1k-step sample interval;
ESS = N/(2 tau_in_samples). These estimates assume stationarity and are descriptive
when drift or occupancy changes invalidate that assumption.
