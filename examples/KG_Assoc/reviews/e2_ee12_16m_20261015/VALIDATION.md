# Ee12 CPU validation and reproduction

Starting clean local/remote `KremerGrest` HEAD:
`81fe5de9cd5ded849202eebab7c14e6bd35fb9ae`. Final SHA is the containing review
commit, reported after push. Only the new `e2_ee12_16m_20261015` dossier changes.

Fresh read-only numerical, accepted-event, graph and conformation replay passed
for all three uninterrupted 0–16M histories. Each has 16,001 diagnostic samples;
accepted events are 18,824/18,410/18,850 and final bonds 1,976/1,972/1,968.
Fresh validation dictionaries equal the completion receipts exactly. The exact
plan hash, E1 active lineage and snapshots, commands/diagnostics, seeds,
approval/smoke witnesses, started receipts, completion receipts, source/build/log
manifests, executable bytes and every output digest authenticate.
[CPU_AUTHENTICATION.log](CPU_AUTHENTICATION.log) and
[provenance.json](evidence/provenance.json) retain the results and bindings.

The build at the starting SHA replaced all six executables **before** this task.
The six old/current digest pairs are explicitly recorded in
[AUTHENTICATION.json](AUTHENTICATION.json); the current bytes match the Ee12
plan/build. Older dossiers are preserved without pretending their historical live
binary hashes still describe current executable bytes. Historical E1 executable
bytes are not independently reauthenticated. No executable or GPU calculation
ran during this review. Native physics and build recipes were not edited, so
no compilation or rebuild was performed.

The four inspected LAMMPS associating implementation files byte-match commit
`1c6faf70e94aef2389c208e8c80c60c084a96907`, branch
`feature/associating-stickers`; their hashes are recorded. Unrelated preexisting
LAMMPS bench changes were not touched. No reference simulation or K1 reproduction
was run. This task reviews existing full-star data rather than advancing the
validation hierarchy to a more complex simulation.

## Numerical and scientific analysis checks

Full frame exports contain 16,001 unique steps per original history, including
unbound step zero. Exactly tiled nonoverlapping 500k, 1M, 2M and 4M windows retain
all preparation context. Shifted/overlapping and final-quarter contrasts are
labeled. IATs and 5/10/20-block estimates are computed separately on every actual
interval; no averaging of IATs/SEMs constructs a coarser estimate. There is no
internal MD reseeding boundary in the Ee12 histories.

All **13,440 checked scalar entries** shared with the existing 500k checkpoint
agree within **3.552713678800501e-15**: means, slopes, IATs, IAT SEMs and 5/10/20-block
SEMs. Accepted-event counts and event-integrated exposures agree exactly.
The inherited IAT's bytecode and arithmetic are unchanged; the reused tested
helper caches its repeated identical mean calculation. New tests independently
verify coarser-window means, event counts and exposures against disjoint 500k
pieces; this identity is deliberately not applied to uncertainties.

Full multigraph, loop, distinct-degree and peripheral accounting passes on all
48,003 frames. Exact event-time isolation intervals independently reproduce every
sampled isolated-star count, while retaining sub-diagnostic isolation excursions
and right censoring. They are residence measurements, not independent trials.
Raw and 250k/500k correlations are descriptive; constant correlations are undefined,
and algebraically coupled observables are not treated as separate confirmation.

The qualified Ee10 record and exact-12M payloads validate. Reference 10–12M means
and creation/break counters match the raw state; neighbor counts/exposures reuse
the integrity-bound frozen joint review. No new Ee10 graph replay is claimed.
The equal-duration scientific comparison uses Ee12 14–16M. Histories share E1
geometries across Ee; no between-Ee pairing or independence claim is made.

A separate tabulation pass in `/tmp/ee12_16m_table_reproduction` reproduced all
**17 compared artifacts bitwise**: the five copied summary/provenance/frame input
artifacts and twelve derived outputs (four Markdown tables, five PNG figures,
correlations, exact isolation diagnostics and Ee10 reference comparison).
This reruns the derived diagnostics and figure generation, not a second full
raw trajectory validation or a second full IAT calculation. The late and full
shape figures were visually inspected. The frozen 500k checkpoint comparison and
coarse-window additive checks provide independent numerical cross-checks of the
fresh interval calculation. [REPRODUCIBILITY.json](REPRODUCIBILITY.json) binds the
compared artifacts and their scope.

## CPU tests

**128 inherited tests passed in 14.840 s; 11 new tests passed in 6.634 s.**
Zero failures/errors. Python compilation passed for both new helpers and the
new test module. Logs: [baseline](BASELINE_CPU_TESTS.log), [new tests](CPU_TESTS.log).
These are deterministic regression/integrity checks, not stochastic convergence
or equilibrium demonstrations. Existing reader ResourceWarnings are suppressed;
their source remains unchanged.

New tests cover complete tilings/preparation and three-history pairing; full-frame
multiplicity/degree/loop/periphery conservation; fresh scalar checkpoint agreement;
additivity of coarse means/counts/exposures; immutable-output and wrong-plan/scope
rejection; restoration after estimator failure; undefined constant correlations;
exact subframe isolation/censoring; preserved evidence and all eleven records;
current executable scope, completion receipts and exact endpoint/seeds.

Reproduce into a **new** output directory from the repository root:

```bash
PYTHONWARNINGS=ignore::ResourceWarning python3 \
  examples/KG_Assoc/reviews/e2_ee12_16m_20261015/reproduce_ee12.py \
  --output /tmp/NEW_ee12_16m_review
MPLCONFIGDIR=/tmp/ee12_matplotlib PYTHONWARNINGS=ignore::ResourceWarning python3 \
  examples/KG_Assoc/reviews/e2_ee12_16m_20261015/tabulate_ee12.py \
  /tmp/NEW_ee12_16m_review

PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_ee12_16m_20261015:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_ee12

PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_e2_acceptance test_catalog test_e2_g1 test_e2_recover \
  test_joint_e2 test_e2_continuous_review test_e2_continuous4m_review \
  test_e2_continuous8m_review test_e2_satellite_continuation \
  test_e2_peripheral_network test_e2_window_sensitivity test_reproduce test_joint_rp040_8m
```

Reproduction from a later commit naturally records that checkout's Git SHA in
provenance; the scientific estimates and exported frames should match. Historical
registration tests with fixed live-inventory/executable expectations are preserved;
this review runs their shared acceptance fixtures plus a current exact-eleven-record
preservation test rather than editing historical expectations.

## Integrity and decision limitations

All **1,171 preexisting relevant file bindings** remain unchanged, including
protected KG/src and frozen campaign/analysis code, prior assessments, eleven
acceptance records and reference payloads, the Ee12 attempt/checkpoint and current
build/executable evidence. Prior binary replacement is the sole explicitly
identified pre-task digest change inherited from earlier live-binary maps.
The old maps themselves remain unchanged. `INTEGRITY.json` binds all new dossier
artifacts except itself; the containing Git commit binds that manifest.

Verify from the repository root:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
d = Path('examples/KG_Assoc/reviews/e2_ee12_16m_20261015')
for name, expected in json.loads((d / 'INTEGRITY.json').read_text())['sha256'].items():
    assert hashlib.sha256((d / name).read_bytes()).hexdigest() == expected, name
for name, expected in json.loads((d / 'PRESERVED_SHA256.json').read_text()).items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
print('PASS dossier integrity and 1171 preserved bindings')
PY
```

The explicit scientific decision is a hold of the exact three 16M states, with
+4M to 20M proposed only as the next diagnostic checkpoint. r002's continuing
redistribution, r003's late reversal/contraction, rare persistent isolated states,
replica offsets, small slow-mode effective counts, block-size sensitivity,
possible initialization bias and historical E1 byte-authentication limits remain.
Finite-window IATs under drift and zero-containing paired intervals do not prove
stationarity. Complete structural decorrelation is not an automatic requirement;
no claim of full stationarity, absence of bias or exact coupled-integrator
equilibrium invariance is made.

No registration discrepancy or numerical authentication failure remains. No GPU
calculation, equilibration extension, acceptance registration, production registry
action, production preparation, authorization or launch occurred. Only this new
review directory is added; protected physics/data and earlier evidence are unchanged.
