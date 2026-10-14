# Observer-only COM transport correction

Starting local/remote KremerGrest HEAD: `75abee1b4ad671cb85ff87ed948621c32b422020`.
Date: 14 October 2026, Europe/Madrid. The final SHA is the commit containing this
change and is reported in the task response. User authorization covers production
observers, metadata, analysis validation and CPU tests; no simulation was authorized.

## Spatial and temporal behavior

`kg_assoc_com_transport.cuh::ComTransport` constructs permanent molecular membership
from immutable particle IDs and molecule IDs. It traverses each permanent star tree,
reconstructing child coordinates from parent coordinates with orthorhombic MIC. It
rejects disconnected/cyclic trees, cross-molecule permanent edges, invalid short
bonds, unsupported masses/boxes and an unknown native-coordinate convention. A star
may span more than half a box from its center: only each **permanent edge**, not the
whole star, must be short. Temporary association state is never supplied to it.

At the segment origin it stores, by immutable ID,
`offset_i = whole_backbone_position_i(0) - native_position_i(0)`.
Every later COM is the arithmetic mean of `native_position_i(t) + offset_i`, with
unit masses checked from ParticleData. There is **no sampled temporal minimum image**.
The adapter `StarComWriter` in `kg_assoc_production.cu` reads native positions and
masses through `getIdOrderedIndices` and restores the original box-center shift in
output coordinates. Particle storage permutations cannot change membership/offsets.

The explicit contract is the existing GJ integrator's continuous native positions:
that integrator adds displacement without folding, and the production path does
not fold positions after initialization. Unknown conventions fail. Corrected
permanent-bond branches are checked at output samples without applying MIC; internal
coordinate folding or invalid branches fail rather than silently changing an image.
A common rigid whole-box fold is inherently indistinguishable from native motion
from sparse coordinates alone, so the hardwired integrator contract remains
necessary. This is not a probabilistic crossing bound or a claim that such a fold
can be detected from endpoints.

Only COM observers and preflight validation changed. Interactions, reactions,
integrators, particle updates, temperature, dt, cadences and frozen campaign
parameters are unchanged. Non-campaign observer scheduling is now relative to the
new segment origin so the declared cadence phase remains valid for arbitrary
initial steps; the frozen campaign cadence stays 10000 steps (100 physical time).

## Restart policy: explicit unsupported continuation

No COM checkpoint/resume support is introduced. New independent E2→production
segments have a new transport origin. Explicit continuation arguments, restart
prefixes with production COM/topology/completion artifacts, and recognized campaign
production archival inputs fail before MD initialization/output creation. Triclinic
input also fails explicitly (tilt labels are tokenized, so whitespace cannot hide
an unsupported box).

This deliberately blocks existing production/staircase continuation commands until
a versioned, verifiable COM-origin checkpoint is separately implemented. It does
not silently reset a continuation or infer its origin from sparse samples. A
renamed/copied historical state stripped of its provenance cannot be authenticated
as a continuing transport history; output metadata declares a new independent
segment and does not authorize concatenation. No support for automatic stitching,
checkpoint fabrication or resumed simulation is implied.

## Version-2 output contract

Both `.com_samples` and `.com_trajectory` retain the numeric columns
`step time molecule_id com_x com_y com_z`. Immediately after that header the producer
writes `# KG_COM_TRANSPORT 2`, followed by required metadata and an end marker:

- `convention native_continuous_plus_initial_backbone_offsets`;
- `origin_kind independent_segment_no_concatenation` and quoted `origin_id` (absolute output prefix; relative prefixes are scoped to the producer working directory);
- absolute `origin_step`, `cadence_steps`, `dt`;
- `unit_mass 1`, six original orthorhombic `box_bounds`, sorted stable `molecule_ids`.

The helper `analysis/com_transport.py` verifies the version, exact field coverage,
convention, origin semantics, IDs, geometry, mass and cadence. Data samples must be
finite and agree with IDs, absolute time, phase and frame spacing. A concatenated
second header, unsupported convention/version, missing/reordered frames, bad box or
mass cannot silently pass. Metadata verification is not a signed execution
attestation: normal executable/run/output provenance remains required separately.

The COM MSD and self-F_s(q,t) analyzers preserve their numeric algorithms and
three-array reader return values. They now validate the coordinate contract and
ensemble compatibility, including shared origins (two streams from one origin are
not independent replicas). Metadata and legacy status are included in result
provenance. Noncontiguous immutable molecule IDs are supported when declared.
Walking/hopping, percolation and campaign completion readers enforce the same
contract; the geometry analyses also compare it with permanent system membership
and box lengths.

Legacy header-only COM files are **rejected by default**. Analysis scripts accept
`--allow-legacy-com` only as explicit historical, unverified analysis, with a warning
and `legacy_unverified=true` provenance. It does not correct old coordinates, certify
winding, or turn old files into version 2. The campaign completion validator does
not provide this bypass. Corrected and legacy ensemble conventions cannot mix.
Existing files and previous analyses are not rewritten. Full-bead binary output
and its frozen cadence are unchanged.

## CPU validation and build scope

The extended `test_com_pbc_audit.py` compiles the actual observer adapter and pure
host helper using a minimal ParticleData shim and g++ C++14, with no CUDA runtime.
Tests cover permanent-backbone reconstruction of an extended four-arm N40 star,
opposite-side/image-equivalent beads, rigid translation over many boxes, bounded
synthetic walks, back-and-forth motion, reordering, fixed membership under temporary
edges, unit-mass COM, analytic origin-averaged MSD and real COM/MSD readback.

The former alias counterexample now preserves relative COM x=0,21,42 for a boundary-straddling star in L=10, with lag-one MSD 441,
not x=0,1,2 and MSD 1. Unknown conventions and internally folded bead trajectories
fail. Restart requests before/after a crossing and concatenated outputs fail;
unsupported geometry/archives/continuation flags fail in CPU preflight. Version,
convention, mass, cadence, ID, finite-data and duplicate-origin guards are exercised.
These are deterministic regressions, not diffusion convergence or GPU results.

Relevant CPU campaign/acceptance/recovery/catalog tests, four existing analysis
self-tests, Python compilation and integrity checks were run. Two standalone CPU
correlator tests compiled and passed. The affected production executable, campaign
production executable and campaign smoke variant were rebuilt by nvcc 12.8/GCC 11.2
to **temporary paths only**, as required for the included-header change. They were
never run and did not replace the plan-bound binaries. The Makefile now tracks the
new observer header for those targets. No E2 executable or simulation source was
changed or installed. Before any separately authorized future production execution,
its repository executable must be rebuilt and its new source/binary provenance
recorded; a git pull alone is insufficient.

[STOPPED_E2.md](STOPPED_E2.md) reports the separate read-only interruption diagnosis.
[INTEGRITY.json](INTEGRITY.json) records check results, build identities and evidence
bindings. Original trajectories, the stopped attempt, historical dossiers, eight
acceptances, frozen campaign and protected `src/`/`examples/KG/` remain unchanged.
No GPU execution, E2 recovery/equilibration, registry selection/publication,
production preparation/authorization/launch occurred.

### Recorded results

- **111 CPU unittests passed**, including 15 observer/metadata regressions and the
  relevant campaign, acceptance, recovery, E2-G1 and catalog tests.
- Four existing COM MSD/F_s(q,t)/walking/percolation analysis self-tests passed.
- Two separately compiled CPU correlator/count/checkpoint tests passed.
- Three affected production variants compiled successfully into `/tmp`; none was
  executed or installed. Existing nvcc architecture-deprecation and legacy
  unchecked-`fscanf`/unclosed-reader warnings did not cause failures.
- Python compilation and whitespace checks passed. 677 pre-existing protected,
  frozen, historical and stopped-attempt files remain byte-identical. All recorded
  installed E2/production build executable and build-log hashes still match.

Reproduce the CPU suite (no launch/preparation command):

```sh
PYTHONPATH=examples/KG_Assoc/analysis:examples/KG_Assoc/campaign \
python3.11 -m unittest -v test_com_pbc_audit test_campaign test_e2_acceptance \
  test_e2_ee6_acceptance test_e2_n40_acceptance test_e2_recover test_e2_g1 test_catalog
```

Python 3.11 is the installed `correlator` extension ABI. No dependency was installed.
No GPU precision/performance or statistical diffusion validation is claimed. Native
coordinate floating-point precision remains an integrator/output limitation; the
observer uses double accumulation and never attempts to recover lost GPU precision.
