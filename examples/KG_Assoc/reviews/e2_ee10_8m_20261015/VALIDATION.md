# Ee10 CPU validation and reproducibility

Starting local/remote `KremerGrest` SHA:
`49ffc4006763e0409e06cc12cdd0dd7eba7d2fe7`; initially clean working tree.
The final SHA is the containing assessment commit, reported after push.
Only this new dossier, read-only helpers, CPU tests and derived evidence change.

All three original 0–8M histories passed fresh CPU authentication, numerical
validation, accepted-event replay, permanent-star graph reconstruction, reciprocal
stable-ID partner checks, conformation validation and independent endpoint
minimum-image unwrapping. Each has 8,001 samples and 80,000 chemical sweeps;
accepted-event counts are 54118/53832/53545 and final bond counts 1932/1918/1921.
E1 parent snapshots, active/frozen inventory, command/seed identities, source/build
manifests, current executable bytes, build logs, approval/smoke evidence, execution
witnesses, completion receipts and all output hashes authenticate. No GPU binary
was executed, rebuilt or probed. No CUDA/native/header source changed.

All 0–8M frames remain, including initially empty chemistry. Each history has
16 nonoverlapping 500k, eight 1M and four 2M windows. Late 250k windows and shifted
contrasts are additional descriptive checks. The inherited estimator computes
each interval separately; its unchanged IAT bytecode caches the repeated identical
mean call without reordering arithmetic. **17,280 scalar checkpoint statistic
entries** match the original review to roundoff, including block means, slopes,
IATs, effective samples, SEMs and 5/10/20-block SEM sensitivity. Maximum absolute
difference is **7.105427357601002e-15**; tests enforce 1e-12 tolerance for Python
statistics roundoff across interpreter versions.

**57 CPU Python tests passed in 14.403 seconds, zero failures.**
[CPU_TESTS.log](CPU_TESTS.log) records every result. Tests cover exact system/8M
scope, rejection of existing output, callback restoration, complete transient
coverage, population/degree/component/multiplicity accounting, paired three-history
units, checkpoint reproduction, corrected Ee8 reference intervals/physics/event
rates, continuous/restart review boundaries, peripheral graphs and the inherited
IAT cache. Existing sidecar ResourceWarnings are suppressed in the command below;
their source is unchanged. Python compilation passed for all three new scripts.

A second end-to-end run reauthenticated the raw histories and independently
recomputed the evidence in `/tmp/ee10_final_reproduction`. Its summary, three
frame CSVs, estimate CSV, full-window Markdown table and **all five PNG figures
match bitwise**. Ee8 comparison record values match exactly; provenance paths
naturally identify each output directory. Full and late chemistry/shape/network
paths were plotted, and the late and full-chemistry figures were visually inspected.

The qualified Ee8 record and its exact corrected-8M payload hashes authenticate.
Only corrected 6–8M reference windows enter the comparison. Their frozen-review
hashes match the original inventory, means match the qualified raw scalar state,
and accepted creation/break counts match cumulative counter increments. Distinct
neighbor counts and event-time exposures reuse that authenticated historical
review; this task does not claim fresh Ee8 graph replay or historical-binary
execution. Other physics parameters match exactly except Ee. Histories are not
paired across Ee. Raw Ee8 scalar files do not supply comparable shape observables.

The four inspected LAMMPS implementation files match the recorded
`feature/associating-stickers` commit
`1c6faf70e94aef2389c208e8c80c60c084a96907`. They were inspected locally, not
claimed to have been fetched anew. No reference simulation or K1 reproduction
was run. This task assesses existing full-star histories and proposes the same
validation level, not a more complex validation stage.

Reproduce from the repository root into a **new** output directory:

```bash
python3 examples/KG_Assoc/reviews/e2_ee10_8m_20261015/reproduce_ee10.py \
  --output /tmp/NEW_ee10_review
MPLCONFIGDIR=/tmp/ee10_matplotlib python3 \
  examples/KG_Assoc/reviews/e2_ee10_8m_20261015/tabulate_ee10.py \
  /tmp/NEW_ee10_review

PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_ee10_8m_20261015:examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_ee10 test_e2_continuous_review \
  test_e2_continuous4m_review test_e2_continuous8m_review \
  test_e2_satellite_continuation test_e2_peripheral_network \
  test_e2_window_sensitivity test_joint_e2 test_reproduce test_joint_rp040_8m
```

974 preexisting file bindings are preserved: exact Ee10 inputs/outputs/checkpoint,
E1 parents, frozen campaign/source/build/executable evidence, all ten acceptance
records, previous reviews and protected KG/src files. `INTEGRITY.json` binds every
new artifact except itself; its containing Git commit binds the manifest.
`decision.json` records scientific hold and a proposal only, not an extension plan
or formal workflow authorization. No registry or production artifact was created.

Limits: finite-window IATs and blocking estimates can miss slower relaxation,
especially under trends; only three independent histories support paired,
unadjusted exploratory intervals. Historical E1 executable bytes are not
independently reauthenticated. `oracle_sweeps=0` remains explicit: no rejected
candidate proposals, GPU oracle or every unsampled MD configuration is reconstructed.
Exact coupled-integrator equilibrium invariance is not established. Complete
stationarity, structural decorrelation and absence of initialization bias remain
unproven. The scientific loop/coordination concern remains unresolved despite
numerical integrity. No GPU, extension, formal acceptance, selection, activation,
production preparation, authorization or launch occurred.
