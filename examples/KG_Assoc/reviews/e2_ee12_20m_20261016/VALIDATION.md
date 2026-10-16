# Joint Ee12 CPU validation and reproduction

Starting clean local/remote `KremerGrest` SHA:
`c1e0b5d472dbf0c5e09274f8079cd92a92d7d3dd`. Final SHA is the containing review
commit, reported after push. Only this new `e2_ee12_20m_20261016` dossier changes.

Fresh CPU numerical, accepted-event, graph and conformation validation passes for
all six source segments. Original histories each have 16,001 frames and
18,824/18,410/18,850 events; continuations each have 4,001 frames and
4,069/4,182/4,100 events. Final bonds are 1,971/1,962/1,976. All six fresh
validation dictionaries equal their completion receipts exactly.
[CPU_AUTHENTICATION.log](CPU_AUTHENTICATION.log) preserves the replay results;
[provenance](evidence/provenance.json) binds both plans, parents, seeds and outputs.

The original plan hash, new extension plan hash, exact 16M parent restart/sidecar
pairs, chemistry partners, cumulative counters, chemical seeds, absolute steps,
requested/effective MD streams, E1 lineage, approval/smoke and execution witnesses,
source/build/log manifests, all output hashes and completion identities authenticate.
Current continuation executable bytes authenticate; all 289 common native/build
recipe hashes agree between builds. The original executable files were replaced
by the extension rebuild before this task. Original recorded digests, source/build
logs, outputs and the immutable 16M review authenticate, but original binary bytes
are not independently reauthenticated now. The established archive locations contain
only the older RP040 archive. Historical E1 executable bytes remain similarly
limited. Old/current pre-task executable digest pairs are recorded explicitly in
[AUTHENTICATION.json](AUTHENTICATION.json); no replacement occurred during review.
No executable, build or GPU calculation ran here.

Chemical continuity is exact. [BOUNDARY.json](evidence/BOUNDARY.json) records the
16M partner lists, counters, parent payload hashes and old/new requested/effective
MD seeds. The source/log convention restores positions and velocities into a new
GJ integrator with `initVelocities=false`, `internal_start_step=0` and new seeds
520130/520131/520132 (effective 3381585552/3373217424/3398338192). This is not
bitwise MD continuation. No IAT, SEM, blocking error or bond lifetime crosses 16M.

The four local LAMMPS associating implementation files match the recorded branch
`feature/associating-stickers` and SHA `1c6faf70e94aef2389c208e8c80c60c084a96907`.
Their hashes remain bound; no LAMMPS file or reference simulation was changed.
This reviews existing full-star data rather than advancing the validation hierarchy.

## Statistical and reconstruction checks

There are 20,001 unique displayed steps per history, including unbound step zero;
both raw boundary frames remain authenticated. Exactly tiled 500k/1M/2M/4M
windows cover 0–20M. A segment selector rejects every crossing interval; shifted
and final-quarter comparisons stay within their respective segments. Means use
`(start,end]`; event exposure begins at the boundary. Early transients remain.

Each history has 93 estimator intervals: 60 exact original intervals reused from
the hash-bound 16M review and 33 directly computed continuation intervals. Reuse
is explicitly labeled with source path/hash and occurs only at identical bounds;
no IAT or SEM is averaged to manufacture a longer estimate. Reused metrics,
activity and exposure dictionaries agree exactly with the frozen originals.
Three original histories remain the independent statistical units, df=2; windows,
frames and segments never increase the replica count.

All **8,600 finite scalar entries** shared with the continuation checkpoint match
within **4.440892098500626e-16**: means, slopes, IATs, effective samples, SEMs,
5/10/20-block SEMs and block means. Forty constant-observable effective-sample
sentinels are treated as unresolved rather than compared with a numerical sample
count. The inherited estimator's numerical placeholders remain explicitly flagged
as constant/not mixing evidence. The tested mean cache leaves IAT bytecode and
arithmetic unchanged. These checks are deterministic, not convergence evidence.

All 60,003 combined frames pass inter-bond multiplicity, L1, intra-loop, distinct
degree/moment, component and peripheral conservation. Sampled isolated identities
and satellite memberships agree with every graph count. Accepted-event replay of
inter-bond degree-zero residence independently reproduces all sampled isolate
counts while retaining brief subframe excursions. Observed connectivity residence
across 16M is explicitly labeled as crossing chemical continuity; it is not a bond
lifetime distribution, stitched IAT or stationary survival estimate.

Satellite membership runs are sampled at 1000-step cadence; exact transition
residence between frames is not claimed. A separate edge/loop counter replay
reconstructs multiplicity within sampled satellite components. Actual extension
frames contain no satellites. A synthetic CPU fixture checks parallel-edge
creation, partial breaking and intra-loop bookkeeping even when these rare cases
are absent from the extension. Exact isolation identifies r003's star-531 exit
and star-684/868 entries, explaining its giant-component reduction.

Correlations use separate 12–16M and continuation intervals, raw and 250k/500k
means, with no frame/block p-values. Constants are undefined; algebraically related
observables are not counted as independent scientific confirmation. Ee10 context
reuses the authenticated frozen 12M reader and payloads, not a new reference
trajectory/graph replay. The unchanged qualification and executable limitations
of that reference remain.

A separate tabulation pass in `/tmp/ee12_20m_table_reproduction` produced **22
bitwise matching artifacts**: seven copied summary/provenance/boundary/peripheral/
frame inputs and fifteen regenerated outputs (five Markdown tables, five PNGs,
correlations, isolation, satellite runs, satellite topology and Ee10 comparison).
This repeats derived diagnostics/figures, not a second full raw/IAT pass. Late,
network and full-shape figures were visually inspected.
[REPRODUCIBILITY.json](REPRODUCIBILITY.json) records the scope and hashes.

## CPU tests and commands

**128 inherited tests passed in 15.225 s; 15 new tests passed in 11.864 s.**
Zero failures/errors. Python compilation passed for both helpers and the new test
module. [Baseline log](BASELINE_CPU_TESTS.log), [new tests](CPU_TESTS.log).
Existing reader ResourceWarnings are suppressed; their source is unchanged.

New tests cover exact segment bounds and reseeding rejection, three-history pairing,
immutable outputs, wrong endpoint scope, estimator restoration after failure,
complete transient/frame/multigraph accounting, exact cache reuse, continuation
checkpoint agreement, constant/correlation cases, component membership and all
four tilings, chemical boundary identity and receipt equality, current/historical
executable scopes, protected evidence and eleven records, exact endpoint Markdown/receipt pins, isolation residence
labels, and synthetic parallel-edge/loop satellite replay.

Reproduce from the repository root into a **new** directory:

```bash
PYTHONWARNINGS=ignore::ResourceWarning python3 \
  examples/KG_Assoc/reviews/e2_ee12_20m_20261016/reproduce_ee12_20m.py \
  --output /tmp/NEW_ee12_20m_review
MPLCONFIGDIR=/tmp/ee12_20m_matplotlib PYTHONWARNINGS=ignore::ResourceWarning python3 \
  examples/KG_Assoc/reviews/e2_ee12_20m_20261016/tabulate_ee12_20m.py \
  /tmp/NEW_ee12_20m_review

PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_ee12_20m_20261016:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_ee12_20m

PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_e2_acceptance test_catalog test_e2_g1 test_e2_recover \
  test_joint_e2 test_e2_continuous_review test_e2_continuous4m_review \
  test_e2_continuous8m_review test_e2_satellite_continuation \
  test_e2_peripheral_network test_e2_window_sensitivity test_reproduce test_joint_rp040_8m
```

A later checkout naturally records its own Git SHA in fresh provenance. Scientific
estimates and frame exports should match. Historical tests/dossiers retain their
original live-executable expectations; the shared fixtures and current preservation
guards are run without editing any previous expectation or evidence.

## Integrity and scientific limitations

All **1,258 preexisting relevant file bindings** remain unchanged: previous reviews,
the eleven acceptance records and relevant payloads, protected KG/src and frozen
campaign/analysis files, both Ee12 attempts, checkpoint evidence and current
build/executable bytes. The six pre-task executable replacements are explicitly
identified; the old maps themselves remain immutable. No additional acceptance
record or production registry exists. `INTEGRITY.json` binds every new artifact
except itself; the containing Git commit binds the manifest.

Verify from the repository root:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
d = Path('examples/KG_Assoc/reviews/e2_ee12_20m_20261016')
for name, expected in json.loads((d / 'INTEGRITY.json').read_text())['sha256'].items():
    assert hashlib.sha256((d / name).read_bytes()).hexdigest() == expected, name
for name, expected in json.loads((d / 'PRESERVED_SHA256.json').read_text()).items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
print('PASS dossier integrity and 1258 preserved bindings')
PY
```

The scientific recommendation is qualified initialization of exactly the three
20M pairs, with no formal registration. The exact-16M hold remains unchanged.
Residual common L1 loss, r001 degree/multiplicity evolution, r002's remaining
motif changes, r003's redistribution/isolates/compaction, replica offsets, coherent
late terminal contraction, small slow-mode effective samples, block sensitivity,
rare-event sampling, initialization bias and historical executable limits remain.
Complete stationarity, structural decorrelation, absence of bias and exact
coupled-integrator equilibrium invariance are not demonstrated. Confidence intervals
containing zero and stable bulk chemistry are not used as equilibrium proofs.

No authentication or numerical failure remains. No GPU calculation, additional
equilibration, acceptance registration, registry selection/activation, production
preparation, authorization or launch occurred. Only this new review directory is
added; protected files, prior assessments and eleven formal records are unchanged.
