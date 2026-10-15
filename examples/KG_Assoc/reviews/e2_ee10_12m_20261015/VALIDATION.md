# Joint Ee10 CPU validation and reproduction

Starting local/remote `KremerGrest` SHA:
`4ada00d18cff6ac5e83872faf469409ee892f28f`; working tree initially clean.
The final SHA is the containing review commit, reported after push. Only this
new review directory is added: assessment/endpoints, authentication/integrity,
read-only helpers, CPU tests and derived scientific evidence.

Fresh CPU authentication and numerical/event/graph/conformation validation passed
for all six segments. Original histories each have 8,001 samples and
54118/53832/53545 accepted events. Extensions each have 4,001 samples and
25674/25653/25903 accepted events. Final bond counts are 1926/1915/1926.
All three 8M restart/sidecar parent pairs match the prior immutable dossier,
extension plan bindings and live bytes. Chemistry seeds, partners, cumulative
counters, absolute steps, permanent identities and physics agree across the
boundary. Requested/effective MD seeds change as authenticated in plans and logs.
The source creates a new GJ integrator with restored velocities and a new MD
stream; it does not provide bitwise continuation of the old MD random state.

Current extension executable bytes, source/build manifests, forced-build logs,
approval/smoke bindings, execution witnesses, completion receipts and all output
hashes authenticate. All 289 common native/build-recipe source hashes match.
Original executable bytes were replaced by the rebuild; their recorded digests,
build logs, sources and approved dossier authenticate, but no old binary archive
was found. Historical E1 executable bytes are not independently reauthenticated.
These limits remain in the scientific recommendation and endpoint dossier.

The full-context CSVs have 12,001 unique steps per original history, retaining
step zero and the initial transient. Only one 8M display row is exported; both
raw boundary states remain independently authenticated. There are 24 complete
nonoverlapping 500k, 12 1M and six 2M windows per history, plus shifted and late
quarter windows. A selector rejects every interval crossing the actual 8M MD
boundary. No stitched IAT, SEM, blocking estimate or bond lifetime is calculated.

Exact-bound original interval estimates are reused from the integrity-bound 8M
dossier and labeled with their source path/hash. Every extension estimate is
computed directly with the inherited tested estimator. All **8,640 scalar
entries** shared with the extension checkpoint match at roundoff: means, slopes,
IATs, effective samples, SEMs, 5/10/20-block SEMs and block means. Maximum absolute
difference is **8.881784197001252e-16**; tests use 1e-12 tolerance for interpreter
statistics roundoff. IAT bytecode is unchanged; the inherited helper caches its
repeated identical mean call without reordering arithmetic.

**57 CPU Python tests passed in 10.231 seconds, zero failures.**
[CPU_TESTS.log](CPU_TESTS.log) preserves every result. New tests check actual 8M
boundary rejection, exact 0–8M/8–12M scope, complete transient/frame exports,
paired three-history units, exclusive output, restoration after estimation failure,
full multigraph/degree/component/loop identities, isolation of fully intra-bonded
stars, exact reuse of original estimates, checkpoint agreement and defined/constant
correlation cases. Reused tests cover continuous and restart-aware reviews,
lineage, peripheral graphs, mean-window sensitivity and the inherited IAT cache.
These are deterministic CPU regression/integrity tests, not stochastic convergence
proofs. Existing sidecar ResourceWarnings are suppressed in the listed command;
their source remains unchanged. Python compilation passed for all three new scripts.

A second end-to-end run freshly authenticated both segments and computed the
evidence in `/tmp/ee10_12m_final_reproduction`. The summary, all three full frame
CSVs, window table, correlation JSON, reused Ee8 comparison JSON and **all five
PNG figures match bitwise**. The full and late paths were plotted; the late and
full-shape figures were visually inspected. Segment-local raw and 250k/500k
correlations are descriptive only, with no frame/block independence or p-values.

Qualified Ee8 record and payload bindings authenticate again. Comparison values
reuse the frozen corrected 6–8M reference review; no defective historical C1
windows enter and no new Ee8 trajectory/graph replay is claimed. The inspected
LAMMPS implementation files match the recorded branch commit
`1c6faf70e94aef2389c208e8c80c60c084a96907`, whose source hashes are preserved.
No reference simulation or K1 reproduction was run. This task reassesses existing
full-star histories rather than advancing to a more complex validation stage.

Reproduce from the repository root into a **new** directory:

```bash
python3 examples/KG_Assoc/reviews/e2_ee10_12m_20261015/reproduce_ee10_12m.py \
  --output /tmp/NEW_ee10_12m_review
MPLCONFIGDIR=/tmp/ee10_12m_matplotlib python3 \
  examples/KG_Assoc/reviews/e2_ee10_12m_20261015/tabulate_ee10_12m.py \
  /tmp/NEW_ee10_12m_review

PYTHONWARNINGS=ignore::ResourceWarning \
PYTHONPATH=examples/KG_Assoc/reviews/e2_ee10_12m_20261015:examples/KG_Assoc/reviews/e2_rp040_ee8_8m_20261014:examples/KG_Assoc/reviews/e2_rp040_ee8_6m_20261014:examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3 -m unittest -v test_ee10_12m test_e2_continuous_review \
  test_e2_continuous4m_review test_e2_continuous8m_review \
  test_e2_satellite_continuation test_e2_peripheral_network \
  test_e2_window_sensitivity test_joint_e2 test_reproduce test_joint_rp040_8m
```

1074 preexisting file bindings remain unchanged, including both attempts and
checkpoints, all prior assessments, the ten immutable acceptance records,
current build/executable evidence, qualified reference payloads, frozen campaign
and protected KG/src files. Old executable replacement occurred before this task;
the old dossier's integrity is preserved without pretending its historical live
binary hashes still match the rebuilt files. `INTEGRITY.json` binds every new
artifact except itself, and the containing Git commit binds that manifest.

Residual limitations include very few effective slow-mode samples, block-size
sensitivity, rare multiplicities/satellites, replica-dependent populations, r003's
late redistribution and shared shape offsets. Finite-window IATs can miss slower
relaxation and are unreliable under drift. Exact coupled-integrator equilibrium
invariance, complete stationarity/decorrelation and absence of initialization bias
are not established. `oracle_sweeps=0` is retained: no rejected candidates, GPU
oracle or every unsampled MD configuration is reconstructed. No native source
changed, so no rebuild is needed. No GPU, further equilibration, acceptance
registration, registry selection/activation, production preparation or launch
occurred.
