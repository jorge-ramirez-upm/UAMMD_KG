# CPU validation, reproduction and limitations

Starting SHA: `01ecb1bc0abd072c705096b778e28d611e0a81d7` (`KremerGrest`).
Final SHA is the containing dossier commit, reported after push. Review initiated
2026-10-14, finalized 2026-10-15 (Europe/Madrid). The only changed files are in
`examples/KG_Assoc/reviews/e2_rp060_ee8_6m_20261014/`: assessment, endpoint dossier,
validation notes, read-only helpers, CPU tests and derived immutable evidence.

Fresh raw-data authentication passed for all three exact 0–6M histories before
repository edits. Each has 6,001 frames at 1,000-step cadence and 60,000 chemical
sweeps. Accepted-event counts are 211200/209838/211013 and final bond counts are
1770/1772/1765. CPU checks cover permanent identities, reciprocal valence-one
partners, event/counter/population conservation, graph reconstruction, all
multiplicity accounting, final restart/sidecar identity, numerical diagnostics,
endpoint FENE validity, conformation cadence and independent endpoint unwrapping.
All statuses are numerically valid and scientifically review-required; those
validator statuses are not automatic scientific acceptance.

Plans, approval, current E2 executable/build/source bytes, build logs, runtime
receipts, environment/log outputs, smoke bindings and payload hashes authenticate.
r002's retry snapshot/diagnostics and active/frozen inventory mapping agree.
The failed original E1 command and logs agree with their frozen inventory hashes
and remain preserved. RP040/RP080 qualified records, scientific evidence binding
and all exact endpoint payload bindings authenticate. The local LAMMPS reference
implementation was inspected and its four source files hash-bound; no reference
simulation or K1 reproduction was run.

Every replica has all 12 nonoverlapping 500k, six 1M and three 2M intervals,
including initial transient context. Shifted and terminal-quarter intervals are
additional sensitivity checks. All IATs, event-bin statistics and blocking errors
are computed directly in one uninterrupted MD history. The validated existing
IAT bytecode is reused with its repeated identical mean call cached; arithmetic
and estimator definitions are unchanged. The fresh common 500k results match
**12,960 scalar entries** in the plan-bound original review to roundoff, including
means, slopes, IATs, effective samples, SEMs, 5/10/20-block estimates and block
means. Maximum absolute difference is **3.552713678800501e-15**, from Python
statistics roundoff between interpreter versions. Tests enforce 1e-12 tolerance.

The full Python CPU suite covers the new exact scope, complete transient/window
coverage, paired three-history units, callback restoration, rejection of existing
outputs, all exported graph/multiplicity/population identities and checkpoint
statistic reproduction. Reused tests cover continuous reviews, satellite
definitions, window/lineage boundaries, paired sensitivity, immutable source
authentication, the unchanged IAT cache and multigraph valence guards.
No C++/CUDA source changed; no affected executable requires rebuilding.

**Final results: 46 Python CPU tests passed in 13.180 seconds, zero failures.**
Python compilation passed for all four new helpers/tests. A second end-to-end
run of the final reproduction helper into `/tmp/rp060_final_reproduction` passed
fresh three-history authentication and produced **bitwise identical** summary,
three full-context frame CSVs and window-estimate CSV. The 739 preserved files
passed final hash verification. The four inspected LAMMPS files match their
recorded branch commit bytes. Four full-context 2D figures were generated on CPU
and the shape figure was inspected. Existing sidecar ResourceWarnings are
suppressed in the listed integrated test command; their code is unchanged.

Run the authentication and reproduction commands below from the repository root.
Each derived analysis destination must be new. The historical E1 executable bytes
are not available as authenticated archives; recorded provenance and available
E1 input/output bytes are authenticated. Historical neighbor binaries and neighbor
trajectories are not freshly executed/replayed. Only corrected RP080 recovery
data enter the neighbor comparison. Scalar neighbor files do not provide
comparable RP080 conformation. The reference checkout is pinned by recorded SHA,
not claimed to have been fetched during this read-only assessment.

```bash
python3 examples/KG_Assoc/reviews/e2_rp060_ee8_6m_20261014/validate_rp060.py
python3 examples/KG_Assoc/reviews/e2_rp060_ee8_6m_20261014/reproduce_rp060.py \
  --output /tmp/NEW_rp060_reproduction
MPLCONFIGDIR=/tmp/rp060_matplotlib python3 \
  examples/KG_Assoc/reviews/e2_rp060_ee8_6m_20261014/tabulate_rp060.py \
  /tmp/NEW_rp060_reproduction

PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_rp060_ee8_6m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -q test_rp060 test_e2_continuous_review \
  test_e2_satellite_continuation test_e2_window_sensitivity test_joint_e2 \
  test_reproduce test_joint_rp040_8m
```

Finite-window IAT estimates cannot resolve all slow modes or establish
stationarity. Constant metrics do not certify decorrelation. Only three
independent histories support paired exploratory Student-t intervals (df=2),
without multiple-comparison correction. Common late intra/inter redistribution,
L1 effective samples below ten, rare multiplicities/satellites and r003's late
conformation excursion remain unresolved scientific qualifications. No CPU
replay can reconstruct rejected candidate proposals, every unsampled MD state,
or establish exact coupled-integrator equilibrium invariance. `oracle_sweeps=0`
is explicitly retained: no GPU candidate oracle or new GPU result is claimed.

`PRESERVED_SHA256.json` binds 739 preexisting files, including exact attempts,
checkpoints, E1 parents/retry/failed original, neighbor endpoints and records,
all acceptance records, frozen campaign helpers, protected KG and src files.
`INTEGRITY.json` binds the new dossier artifacts except itself; the containing
Git commit binds the integrity file. `decision.json` is a recommendation only.
No accepted record, raw simulation output, protected evidence, registry, selection,
activation, production authorization or production preparation changed.
