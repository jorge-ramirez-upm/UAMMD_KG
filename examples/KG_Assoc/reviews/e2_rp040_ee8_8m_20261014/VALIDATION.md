# CPU validation and integrity

Starting local and remote KremerGrest HEAD: `020fc07deb7cdf5462019657e21ffe5c13a00f3b`.
The containing commit is the immutable review identity. Only this new directory is added.

All six segments passed fresh read-only authentication and numerical, event,
conformation and graph validation. The original histories each contain 6,001
samples and 60,000 chemical sweeps; extensions each contain 2,001 samples and
20,000 sweeps. Accepted-event counts are 197626/198337/198306 for 0–6M and
65661/65215/65720 for 6–8M. Final bond populations are 1711/1718/1700.
Parent and endpoint restart/chemical payloads, plans, completion receipts,
execution logs and available executable/build bytes authenticated. Historical
E1 executable bytes remain a stated limitation.

All 6,720 shared scalar/vector statistic entries match the authenticated original
and extension 500k checkpoint estimates exactly, including means, IATs, effective
sample counts, slopes, SEMs and 5/10/20-block estimates. The reused read-only
scientific analyzer preserves its validated estimator; a scoped cache accelerates
identical mean calls without changing its function bytecode or numerical results.
Each uncertainty estimate is segment-local. The full-context CSVs have 8,001
unique steps per replica, retaining the initial transient and one display row at
6M; both original raw boundary states remain independently authenticated.
No stitched IAT or SEM is calculated across the actual MD reseeding boundary.

The integrated Python suite passed **86 tests in 8.881 seconds**. It covers
continuous and extended E2 reviews, lineage, peripheral graphs, window sensitivity,
three-history paired evidence, formal acceptance immutability/binding, COM/PBC,
and the prior/current scientific reproduction helpers. Six new tests check
segment boundaries, paired statistics, exact endpoint scope, exclusive outputs,
metric restoration and full-history graph/multiplicity identities.

Both CPU C++ correlator executables compiled with g++ C++14/O2 and passed:
`kg_correlator6_counts_test.cpp` and `kg_assoc_correlator_checkpoint_test.cpp`.
Python compilation passed for the four new scripts and reused review/validation
helpers. Total: **86 Python tests plus two C++ tests, zero failures**. Existing
sidecar ResourceWarnings, unchecked-fscanf compiler warnings and an optional
Matplotlib Axes3D warning did not affect these checks or the five 2D figures.
No GPU executable, simulation, CUDA build, recovery or extension was run.

Reproduce into a **new** directory (the scripts reject existing output):

```bash
python3.11 examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014/reproduce_joint.py \
  --output /tmp/rp040_8m_reproduction
MPLCONFIGDIR=/tmp/rp040_8m_matplotlib python3.11 \
  examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014/figures.py \
  /tmp/rp040_8m_reproduction
python3.11 examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014/supplement.py \
  /tmp/rp040_8m_reproduction
```

Integrated CPU regression command:

```bash
PYTHONPATH=examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3.11 -m unittest -v \
  test_e2_continuous_review test_e2_continuous4m_review \
  test_e2_satellite_continuation test_e2_peripheral_network \
  test_e2_window_sensitivity test_joint_e2 test_e2_g1 test_e2_acceptance \
  test_com_pbc_audit test_reproduce test_joint_rp040_8m
```

The 831 preexisting file bindings in `PRESERVED_SHA256.json` remain unchanged,
including both attempts/checkpoints, previous reviews, all eight acceptance records,
frozen campaign and protected code. No active `banks/e2_registry` exists. No formal
acceptance, production preparation/authorization, selection, activation or launch
was created. `INTEGRITY.json` binds every new dossier artifact except itself;
`decision.json` binds the exact candidate endpoints and underlying evidence.
