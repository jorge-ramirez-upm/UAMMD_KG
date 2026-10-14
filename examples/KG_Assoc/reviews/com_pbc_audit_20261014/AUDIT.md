# Molecular COM / COM MSD periodic-boundary audit

Date: 14 October 2026, Europe/Madrid. Starting local and remote `KremerGrest`:
`97118b8a1fbde4f3cd28002014f345191ec53c40`. The final SHA is the commit containing
this audit and is reported in the task response. Scope: source inspection, one
completed authenticated E2 endpoint, immutable generated input, deterministic CPU
regressions and existing CPU analysis self-tests. No active-job files were read.

## Findings and disposition

| Path | Assessment |
|---|---|
| E2 molecular COM output, COM velocity output, COM MSD | **Not implemented/output.** E2 emits chemistry/network/numerics/conformation streams and final states, not COM trajectories. |
| E1/E2 Rg² and center–terminal R² reconstruction | **PBC-correct for the frozen unit-mass, orthorhombic star model:** permanent-bond traversal, not naive wrapped averages. These are spatial observables, not temporal COM transport. |
| Production `StarComWriter` spatial COM | **Conditionally correct; not a general whole-star reconstruction.** Every bead is mapped directly to one anchor's closest image. It fails when a backbone extends beyond half a box from that anchor. |
| Production temporal COM | **Conditionally correct; silent aliasing defect.** Adjacent recorded COM differences are reduced to minimum image; a true component displacement ≥ L/2 cannot be determined uniquely. Raw continuous input does not prevent the writer from discarding its winding information. |
| Restarted COM history | **Not preserved across segments.** Loader folds each bead, writer maps are new, and chemistry sidecars do not store COM winding/origin. Independent segment-local MSD can be valid; silently concatenating segments is not. |
| P4.4 COM MSD estimator | **Correct on supplied continuous coordinates in deterministic tests**, including rigid-translation time-origin averages; it trusts the COM writer and cannot recover discarded winding. Coarse multi-tau levels subsample origins. |
| Molecular COM velocity | **Absent as a molecular observable.** Per-particle velocities are available in snapshots/dumps; global COM drift removal is mass-weighted but is not a molecular velocity trajectory. |

**The active `F04_N010_RP040_EE08_EA04` E2 equilibration can continue unchanged with
respect to this concern.** It does not use the defective production COM writer,
and its conformation code uses permanent-bond spatial reconstruction. This is a
code-based assessment, not a measurement of the running job's health. The job was
not inspected, interrupted, modified or restarted.

The audit does not reverse past numerical or scientific E2 acceptance decisions:
those decisions use chemistry, connectivity, numerical checks and PBC-safe shape
observables, not production COM/MSD. No existing production COM/MSD file is certified
correct solely by a low apparent frame-to-frame displacement. No numerical
corruption of a particular existing production trajectory is claimed: the tests
establish counterexamples and absent guarantees, not measurements of every run.

## Source/function and output inventory

References below are to the starting commit; these implementation files are unchanged.

| Source / function | Implemented behavior and output |
|---|---|
| `examples/KG/kg_runtime.cuh:55`, `createParticleDataFromLammps` | Centers and folds input coordinates with `Box::apply_pbc`; assigns stable initial IDs, **unit mass**, input velocities or zero. Does not retain input image counters. |
| `src/Integrator/VerletNVT/GronbechJensen.cu:29`, `integrateGPU` | Adds displacement to stored positions without folding. Native coordinates are per-bead continuous **within this MD segment**, relative to separately folded initial beads. They need not form a spatially whole molecule. |
| `src/utils/Box.cuh:51`, `Box::apply_pbc`; `kg_assoc_star_runtime.cuh:213`, `minimumImage` | Orthorhombic componentwise MIC. Box uses a floor convention; associating helper uses `nearbyint`; Python structure helper uses `round`. Half-box tie conventions differ, but short permanent bonds avoid ties. Temporal ambiguity requires strictly less than half a box. |
| `examples/KG/kg_lammps_io.cuh:111`, `readAtomsSection`; `readBondsSection:189` | Reads ID/molecule/type/xyz and permanent bonds; optional trailing LAMMPS image fields are ignored. No triclinic cell matrix or image-counter storage. |
| `examples/KG/kg_lammps_io.cuh:353`, `buildLAMMPSDumpFrame` | Text dump: `id type x y z vx vy vz`, orthorhombic bounds. Emits native positions plus box-center shift, **without wrapping**, despite labels `x y z`; no molecule column or `ix iy iz`. Recover membership from a matching data file, not this dump alone. |
| `examples/KG/kg_lammps_io.cuh:409`, `writeLAMMPSDataSnapshot` / `writeLAMMPSDataRestart` | Native positions plus center shift; `Atoms # bond`: ID/molecule/type/xyz; unit Masses, Velocities and permanent Bonds. No counters, no COM trajectory, default stream precision. Generic writer assumes storage order equals ID order; unlike production COM writer it does not consult `getIdOrderedIndices`. This is a latent risk if ParticleData is reordered; no explicit PD sorting call was found in the audited KG/E2 callers and no reordering failure is established here. |
| `examples/KG_Assoc/kg_assoc_star_equilibrate.cu:549`, `unwrapStar`, `computeConformationSample:585`; limited-position update around 884 | E1 permanent-backbone BFS/MIC reconstruction for shape, with equal-mass arithmetic center. Limited-position stage explicitly folds positions; does not maintain a transport history. Its particle-state reader uses stable-ID mapping. |
| `examples/KG_Assoc/kg_assoc_conformation.cuh:22`, `conformationTopology`, `conformationMeans:84`; `kg_assoc_stars.cu:551`, `writeConformation` | Fixed molecule IDs and **permanent bonds only**, validated center/terminal topology, BFS parent traversal, stable-ID positions; `.conformation.tsv`: `step time mean_rg2 mean_center_terminal_r2`. No COM position/velocity emitted. |
| `examples/KG_Assoc/kg_assoc_stars.cu:176`, `writeRestartMetadata`; final writes around 881 | `.state`, `.events`, `.numerics.tsv`, `.conformation.tsv`; final permanent/restart LAMMPS data, `.final_associations`, `.assoc_restart`. Chemistry sidecar records absolute steps, physical parameters, chemistry seed, event counts and active pairs; **no position images, COM offset, COM velocity or MSD accumulator**. Candidate-oracle stream exists only in special smoke build. |
| `examples/KG_Assoc/kg_assoc_production.cu:619`, `StarComWriter::write` | Groups polymer types 1/2 by immutable `data.mol`, resolves storage via `getIdOrderedIndices`, equal-mass arithmetic mean of one-anchor MIC positions. Maps `previousWrapped_` and `unwrappedCom_` track sampled temporal MIC increments. No backbone traversal, image counter, displacement bound check or serialized state. `wrappedCom` is a variable name, not a guarantee its value is inside the primary box. |
| `kg_assoc_production.cu:965`, writer initialization and sampling around 1195 | `.com_samples` in non-campaign mode, `.com_trajectory` in both; header `# step time molecule_id com_x com_y com_z`. First write is at a sampling cadence, not an initial step-zero COM frame. Non-campaign defaults: comEvery=100 (time 1), frameEvery=10000 (time 100), dt=.01; both outputs share the same writer state, so the denser sampling can help only while that stream is executed. CLI can change cadence. |
| `examples/KG_Assoc/kg_assoc_campaign_production.cu:89`; production campaign sampling branch | Campaign COM/topology every **10000 steps = 100 time units**. The campaign branch uses only frameEvery, not comEvery. Full beads every **100000 steps = 1000 time units**. No every-MD-step COM winding update. Frozen cadence is inspected, not changed. |
| `kg_assoc_production.cu:670`, `FullBeadTrajectoryWriter` | `.bead_trajectory.bin`, magic `KG_BEADS_BIN_V2`, native little-endian v2: uint64 counts, six double orthorhombic bounds, ordered int32 ID/molecule/type, permanent bond endpoints; per frame marker, int64 absolute step, double time and float32 native xyz plus box shift. Stable-ID ordered. No explicit image flags, masses or velocities, but native coordinates retain segment-local per-bead motion. |
| `kg_assoc_production.cu:738`, `writeCampaignFinalSnapshot` | Stable-ID ordered native xyz, 17-digit precision, IDs/molecule/type, unit masses, velocities, permanent bonds. Campaign final archival state/completion receipt is not an implemented resumable COM checkpoint. |
| `analysis/analyze_campaign_structure.py:19,45,66`, `read_header`, `unwrap_star`, `frame_rg2` | Reads v2 bead identity/connectivity/bounds, restricts traversal to the molecule's members, unwraps along permanent bonds. Computes shape; no continuous COM/MSD analysis from the bead stream. |
| `campaign/kg_assoc_e2_validate.py:76`, `snapshot_conformation` | Independent permanent-bond endpoint unwrapping using structure helper, compares to E2 shape stream; not temporal COM reconstruction. |
| `analysis/analyze_p44_com_diffusion.py:19,175,193` | Reads ordered finite six-column COM frames, increasing uniform times/steps and star grid; uses installed `correlator.DiffusionCorrelator`, per-star mean MSD and `brute_force_msd` oracle. Does **not** unwrap positions, inspect box/images, detect temporal aliases or restore restart origins. Intended self-contained independent segments, not concatenated continuations. |
| `analysis/analyze_p44_com_fsqt.py:29` | Uses the same COM reader and supplied continuous differences for self F_s(q,t); inherits writer defects. |
| `analysis/analyze_p47_walking_hopping.py:22,39,52` | COM reader, event-centered displacement and exact-lag origin-averaged displacement statistics. Uses direct COM differences and segment-local event/topology identities. Inherits transport aliasing and restart discontinuities. |
| `analysis/analyze_p48_percolation.py:25,88` | Reads synchronized COMs, assigns MIC lattice translations on transient inter-star graph edges and finds network winding. This graph is deliberately **not permanent molecular membership**. Spatial anchor errors affect geometric edge embeddings; adding whole-box temporal offsets does not change positions modulo the box. Already documents COM proxy rather than synchronized sticker coordinates. |
| `campaign/kg_assoc_campaign.py:667,777,881` | Validates COM frame counts/IDs/cadence against topology/completion; dispatches COM MSD/F_s(q,t) and structure analysis. Does not validate winding/crossing sufficiency. Incomplete production cannot resume (`:587`); no automatic correct COM stitching is supplied. |
| `analysis/plot_analysis.py:186`, `plot_diffusion` | Plots derived MSD/SEM/local slope CSV; no PBC reconstruction. |
| `examples/KG/correlator.cpp:905,1643` | Diffusion and chain/monomer MSD primitives take direct coordinate differences. They are library estimators, not molecular reconstruction and not E2 outputs. Main KG production's stress sampling does not automatically make these molecular COM/MSD outputs. |
| `examples/KG/kg_runtime.cuh:218`, `removeCenterOfMassVelocity` | Mass-weighted **global** velocity subtraction (`sum m_i v_i / sum m_i`), with optional KG CLI drift-removal flag. Does not emit per-molecule velocity; PBC does not change ordinary Cartesian velocities. |

Temporary association pairs remain separate in `StickerState`, chemistry sidecars,
events and topology streams. They do not change `LammpsData.mol` or its permanent
bond list. Using a percolating transient component as a molecule would be a new,
incorrect interpretation for star COM diffusion. The production writer's identity
mapping is correct even when storage order is permuted in the CPU harness.

## Completed immutable configuration evidence

Inspected exactly the requested completed `.../F04_N010_RP020_EE08/
equilibrate_13a6951adf16448cb5365a8b28e28427/r001/state.restart.lammpsdat` at 6M.
Its restart SHA256 is
`344e231f96eb8b1ec318de27f912a351d0c5175dd0b5de858612bed57f6cc6b7`;
completion receipt SHA256 is
`1161d3e4ff7784bbfbf1eda891e845472c078800b18dfe211acef34eb5330b90`.
All receipt-bound outputs authenticated, and the endpoint contains 174250 particles,
40000 permanent bonds and 1000 stars; all written masses are one, atom rows have six
fields and no image counters. The cell is cubic/orthorhombic, L=58.9636.

133595 particles lie outside the primary box. There are 956 permanent bonds whose
raw coordinate differences span more than half a box in at least one component,
while the maximum permanent MIC bond length is only 1.1204035. This confirms that
native/raw segment coordinates are not necessarily primary-box wrapped or whole
molecules. Naive raw-coordinate COM differs modulo the box from permanent-bond COM
for **272 stars**. For molecule 584 the COM error is 35.1093884 in minimum-image
vector norm. The single-anchor method agrees modulo the box for all 1000 stars in
this snapshot; that observation does not establish correctness for larger stars or
all future states. Full scalar evidence is in [COMPLETED_SNAPSHOT.json](COMPLETED_SNAPSHOT.json).

The active condition's **immutable generated input only**,
`inputs/F04_N010_RP040/initial.lammpsdat`, has 87125 particles, 40000 permanent bonds
and bounds ±23.3998 on all axes (L=46.7996), consistent with frozen orthorhombic
geometry. No tilt parameters are present. The six-bound readers/Box routines do
not implement triclinic cells or retain their tilt; use on a general tilted input
would need rejection or a cell-matrix implementation. No such tilted box was found
in the inspected inputs. Unit masses make arithmetic COM correct here; the loaders
ignore arbitrary Masses and force unit mass, so heterogeneous masses are not a
supported physical model.

## Counterexamples, sampling and restart qualifications

The deterministic host harness compiles **the actual unchanged `StarComWriter`
class text and `minimumImage` function** extracted from their source files, using
minimal double-precision ParticleData/vector access shims. No CUDA kernel, force,
integrator, chemistry or GPU runtime is compiled or run. It uses the existing
Python permanent-bond helper and the actual installed Python 3.11 correlator/MSD
reader and walking/hopping consumer. This tests writer logic, not GPU numerical
precision or scheduling.

- A boundary-straddling star gives correct backbone/anchor COM and incorrect naive
  wrapped mean. Opposite-side monomers and independent bead image shifts retain
  the same physical COM modulo the cell.
- A rigid translation over many box lengths, sampled below the half-box threshold,
  reconstructs exactly: MSD(lag)=|v|² lag², including brute-force all-origin averages
  and multi-tau selected lags. Back-and-forth crossings also reconstruct exactly.
- A fixed-seed synthetic non-ballistic walk spans multiple box lengths with bounded
  increments; writer/COM reader reconstruct it and fine-level MSD agrees with the
  prescribed trajectory. It is a deterministic regression, not statistical
  evidence of a diffusion coefficient.
- In L=10, input native x=0,21,42 silently becomes COM x=0,1,2. Lag-one MSD is 1
  instead of 441. Reducing observed differences below L/2 is **not** evidence that
  true differences were below L/2. Endpoints alone cannot distinguish winding.
- A four-arm N=40 star with valid consecutive edges of length 1.1<R0, in L=60,
  extends past L/2. Permanent-backbone reconstruction is exact; the actual
  single-anchor writer differs by more than one coordinate unit. This is a valid
  geometric counterexample, not an observed equilibrium conformation or a simulated
  configuration. For center-anchored N=10 in the inspected boxes, the contour bound
  N*R0=15 is below half the box; the shortcut can be justified there if the anchor
  really is the center. The writer does not enforce that anchor identity or bound.
- A new writer immediately before/after a boundary crossing resets its origin by
  whole box lengths. Restoring a **known saved offset/common-state alignment** gives
  the correct analytic MSD; blindly joining reset segments does not. Ordinary
  E2→production starts can deliberately begin a new MSD origin, but continuations
  cannot be silently treated as one displacement history or extra independent replicas.
- Temporary inter-star edges do not merge fixed molecules. Permuted storage remains
  correctly mapped. Arithmetic averaging matches unit-mass COM/COM velocity; a
  heterogeneous-mass counterexample demonstrates its unsupported generality. There
  is no implemented per-molecule velocity output to validate as an existing product.

At campaign cadence 10000*dt=100, no enforced speed/displacement bound, image
counter or higher-rate tracking certificate proves |ΔCOM_axis|<L_axis/2. A small
observed jump or Gaussian/diffusive estimate cannot supply that deterministic
certificate. A finer `.com_samples` stream helps non-campaign runs only under the
same bound; the writer still has no alias alarm. Higher density, associations or
statistical expectations do not remove the ambiguity. This audit has not measured
the active simulation's displacements and does not claim missed crossings occurred
there (it emits no COM stream).

## Smallest proposed correction — not implemented

Do not change physics or restart the active E2 run. Before relying on production
transport, replace the COM observer's one-anchor construction with permanent-bond
BFS and avoid throwing away native segment winding at coarse output intervals.
Because this integrator already stores continuous per-bead coordinates, a small
observer-only approach is to reconstruct each star once at a known segment origin,
record its per-bead lattice offsets, and average `native_position(t)+initial_offset`
by stable IDs thereafter. This avoids a coarse-frame temporal MIC and retains
motion across arbitrarily many box lengths within the segment, subject to native
coordinate precision and consistent short-bond branches. It is preferable to
trying to infer winding from already aliased COM rows. If coordinates are ever
folded during a future integrator path, maintain exact images/fine-step increments
instead and explicitly detect an ambiguous displacement.

For supported continuations, serialize the mapping/coordinate origin, COM winding
and segment parent identity, or restore an exact common boundary state/offset.
A versioned coordinate convention, orthorhombic bounds/cell matrix, unit-mass
assertion (or actual masses), cadence, stable IDs, permanent connectivity and
restart-origin metadata should accompany transport outputs. Existing full-bead v2
already contains IDs/molecules/permanent bonds/bounds/time and native per-segment
xyz, so explicit image fields are not essential **if** continuous-native semantics
are guaranteed. It has float32 precision and coarser output; that can reconstruct
transport only using preserved native coordinates and initial backbone offsets,
not by temporal MIC alone. The current structure analyzer does not implement this
transport reconstruction. Missing pre-first-frame origins and reset-segment winding
cannot generally be recovered retroactively from COM files alone.

Ordinary LAMMPS/OVITO exports should label continuous coordinates explicitly (e.g.
`xu yu zu`) or provide wrapped coordinates with correct image flags; primary-box
rendering does not by itself prove a physical or numerical defect. Generic snapshot
writers should also use stable-ID ordering if sorting is introduced. These are
prospective observer/output/continuation corrections, requiring separate production
code authorization. This task stops at documented proposals and CPU tests.

## Validation and scope preservation

54 selected CPU unittest regressions passed, including 10 new deterministic COM
regressions and existing campaign, E2-G1, periodic E2, Ee6/N40 and generic acceptance
tests. Four existing analysis self-tests passed: COM diffusion, COM F_s(q,t),
walking/hopping and percolation. Python 3.11 compilation and whitespace checks
passed. Existing legacy sidecar-reader ResourceWarnings remain unchanged.

Reproduce the focused audit with:

```sh
PYTHONPATH=examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3.11 -m unittest -v test_com_pbc_audit
```

Python 3.11 is required here by the already installed `correlator` extension ABI;
its installation bytes and inspected implementation hashes are recorded in the
integrity manifest. No dependency was installed. The C++ harness is compiled by
g++ C++14 to a temporary directory and deleted afterward.

[PRESERVED_SHA256.json](PRESERVED_SHA256.json) binds 668 pre-existing protected source,
KG baseline, historical review/acceptance, inspected completed output and immutable
input files. Their bytes remain unchanged. No active attempt file was hashed or
read, and no job-control tool, GPU program or registry/production action was used.
Only this new audit dossier and CPU test file are committed. No production source,
output format, physical model, frozen campaign, existing data or acceptance record
is modified. No production authorization is created.
