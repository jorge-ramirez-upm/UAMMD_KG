# CPU-only verification and reproduction

Use the committed `KremerGrest` checkout and existing immutable dataset on `titan`.
No native MD command is present here. Build authentication can invoke the compiled
`--readback-call-path-info` CPU spy; this neither reads the GPU nor integrates MD.
No rebuild, reservation, preparation, approval or acceptance is required.

After checking that the tree is clean, verify the delivered dossier:

```bash
cd /home/jramirez/UAMMD_KG
git status --short --branch
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/VERIFY_DRIVER.txt
```

The verification checks the 4,802 protected bindings, all thirteen acceptance
records and payloads, six new endpoint receipts, original output hashes, archived
analysis/provenance, exact intervals and readback identities. The original Ea8
r001 40M failure/recovery remains an authoritative parent pair of records.

For a fresh full CPU replay, use a new temporary analysis directory. Keep BLAS
thread counts fixed to avoid wasting CPU on small estimator operations. Each
history is an independent validation/analysis job bounded by 600 s. Stop if any
command fails; never replace missing evidence with generated device files.

```bash
review_work=$(mktemp -d /tmp/ea48_88_review.XXXXXX)
mkdir "$review_work/analysis" "$review_work/summary"
for history in 0 1 2 3 4 5; do
  timeout 600 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
    python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/ANALYSIS_DRIVER.txt \
      --history "$history" --output "$review_work/analysis" || exit 1
done
timeout 600 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/ea48_88_mpl \
  python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/SUMMARIZE_DRIVER.txt \
    --analysis "$review_work/analysis" --output "$review_work/summary"
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/REPORT_DRIVER.txt \
  "$review_work/analysis" "$review_work/summary/REPLICA_DIAGNOSTICS.md" "$review_work/summary"
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/MOTIF_DRIVER.txt \
  --analysis "$review_work/analysis" --output "$review_work/summary"
timeout 600 env MPLCONFIGDIR=/tmp/ea48_88_mpl \
  python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/SLOW_MODES_DRIVER.txt "$review_work/summary"
timeout 600 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 KG_ASSOC_REVIEW_ANALYSIS="$review_work/analysis" \
  python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/ANALYSIS_TESTS.txt
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/MOTIF_DRIVER.txt --self-test
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_48m_88m_joint_20261022/ANALYSIS_DRIVER.txt --self-test
```

The replay archives contain SUMMARY, WINDOWS, TIMESERIES, RENEWAL and
ORIGINAL_IDENTITY JSON-formatted `.log` members for each history. Earlier two
segments are loaded from hash-authenticated preceding review archives. Dynamical
origins remain within their own segments; the full-history original-identity ledger
is structural, not an uninterrupted MD lifetime estimate. Integer counts, endpoint
hashes and numerical validation objects must agree exactly. Floating estimator
and image encodings can differ slightly across NumPy/BLAS/Matplotlib versions;
ENVIRONMENT.log records this review's versions. Direct/FFT tests check numerical
agreement with explicit tolerances, without relaxing any device or oracle gate.

To rerun the established shared CPU regressions into a separate new directory:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea_transfer_24m_joint_20261018/CPU_TEST_DRIVER.txt \
  --output "$review_work/cpu_regression"
```

PACK_DRIVER.txt documents byte-archiving of new review evidence into a fresh output
dossier. It never writes original campaign files. PRESERVED.sha256 is the before
snapshot; PROVENANCE.sha256 authenticates originals and their byte archives;
ANALYSIS.sha256 authenticates replay archive members; INTEGRITY.sha256 binds the
review materials. None of these commands launches or prepares a simulation.

The final committed SHA is reported in the milestone handoff; `git rev-parse HEAD`
identifies the checked-out review commit. Source/build identity is preserved in
RESULTS.log and PROVENANCE.tar.gz independently of later documentation commits.
