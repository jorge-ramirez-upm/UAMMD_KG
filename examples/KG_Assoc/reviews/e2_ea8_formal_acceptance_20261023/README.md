# Formal qualified Ea8 acceptance at 48M

Date: 2026-10-23. Starting clean local/remote `KremerGrest` SHA:
`c2418f3232def175d326665047618603e52e112c`.

The user explicitly approved formal registration of only the three exact
`F04_N010_RP080_EE08_EA08` r001/r002/r003 endpoints at absolute **48,000,000**,
identified in `../e2_ea_48m_88m_joint_20261022/ENDPOINTS.csv` and recommended in
that dossier's ASSESSMENT.md. Registration is restricted to
**`production_initial_state`**, with status **`accepted_with_qualification`**.
It is qualified initialization, not proof of thermodynamic equilibrium.

## Record, endpoints and scientific qualifications

REGISTRATION.log gives the immutable acceptance path and SHA256;
ACCEPTANCE_RECORD.log is a byte-exact committed copy of the original dataset JSON.
ACCEPTED_ENDPOINTS.csv binds all three exact restart/sidecar/receipt pairs and hashes,
plan, chemical seeds and requested/effective MD streams. No endpoint was replaced.

The full scientific assessment remains authoritative. Its principal evidence is
r002's reversal from the high intra-star band, r001's multiplicity fluctuations and
returns rather than continued one-way growth, r003's loop/peripheral excursions,
broad actual identity renewal, and stable visited conformation bands. This milestone
does not create a new acceptance threshold or redo the scientific recommendation.

The acceptance retains inherited corrected-C1 Ea4 preparation and historical
reference source/build limitations; unproven equilibrium invariance of the finite-step
coupled algorithm; limited effective samples; replica-specific slow excursions;
incomplete structural decorrelation, initialization-bias removal and rare-state
sampling; paired original families; and non-bitwise fresh-GJ segment boundaries.
No segment-crossing IAT or lifetime inference is introduced. Ea10 remains unaccepted
on the scientific hold identified in the joint review.

Ea8 r001's 40M `validation_recovery.json` remains SHA256
`91a4fa743735a515353d592213d0ee67cf9e2208ca31dc29cfda4b002aaa5091`.
Its original `incomplete.json` remains SHA256
`14772d19744e253097b4376195210f9591eb6c85df0a012b0ad25f60c46b017c`.
The accepted 48M child has its ordinary validated completion; neither historical
file nor recovery classification is rewritten.

## Established mechanism and narrowly scoped administrative support

REGISTER.txt calls the existing `kg_assoc_e2_registry.accept` mechanism, preserving
schema version 1, `E2_acceptance`, the existing segment provenance kind, three
unique replica/chemistry identities, qualification and completion/output bindings.
The registrar also performs its established triplet numerical verification before
publishing exclusively to a new filename. Existing records cannot be overwritten.
No active registry is selected or published.

The previous acceptance dispatcher knew the earlier derived preparation mode but
not `Ea_reviewed_extension_v2`. Its minimal additional branch permits only an Ea8
40M--48M triplet of exactly 8M steps per history, with explicit qualification and
exact lineage, through the existing reviewed-extension planner. Unknown modes,
the old extension mode, Ea10 and altered ranges remain rejected. Legacy acceptance
paths remain intact. Numerical replay and simulation code are unchanged.

The existing source classifier treated the acceptance publisher as scientific
source, so the first positive candidate test correctly hit the build-provenance
guard after the dispatcher change. The publisher is now classified alongside the
existing administrative front ends. Tests show numerical-validator and physics
sources remain classified and checked, including similarly named files outside
the campaign directory. This does not remove the exact full-source launch check:
new CPU registration permission explicitly fails to authorize GPU source evolution.
No historical execution/source approval or plan is modified or reissued.

CPU_SOURCE_AUTHORIZATION.log binds the exact old/new hashes of only
`campaign/kg_assoc_e2.py` (one administrative classification entry) and
`campaign/kg_assoc_e2_registry.py` (acceptance dispatch). AUTHENTICATE.txt checks
all other 665-entry-map values exactly, authenticates the old administrative bytes
from starting Git blobs, and requires Git ancestry. BEFORE.txt files preserve the
old administrative bytes. REGISTRAR.patch records the scoped change. This is
**CPU acceptance authorization only**, with `GPU_execution_authorized=false`.
It does not grant a source override for GPU execution.

The original optimized executable is unchanged:
`ea_extensions_48m_88m_20261021_v1/kg_assoc_stars_candidate_smoke`, SHA256
`6331c034d8ddb494be616770f2bcc56f5a5fb644f5cb30838e593d259eaf451d`.
No CUDA/header source changed; no native rebuild was needed or performed.

## CPU validation and preservation

Each exact endpoint is independently replayed in REVALIDATE.txt, with its validation
object required to match the authenticated complete receipt exactly. The check
covers actual initial GPU-device evidence (43,563 particles each), all 80,000
runtime candidate-oracle sweeps per history, accepted chemical events and counters,
reciprocity, finite numerical/conformation data, sampled bond geometry, particle
and permanent topology, final restart/sidecar and exact output hashes. Total new
segment evidence: **240,000 oracle sweeps and 18,839 accepted events**. The registrar's
ordinary triplet verification repeats the required checks before publication.
No GPU comparison or MD step is newly executed by this milestone.

PRESERVED.sha256 verifies **4,850 unchanged bindings**, including the original thirteen
acceptances and scientific states, all historical attempts/dossiers, r001 failure
and recovery, reservations, source/build metadata, protected simulation outputs
and active-registry files. Only the two explicitly scoped live administrative source
files are excluded from byte preservation; their old bytes, original Git history
and precise new hashes are separately bound. Historical source/build evidence is
not edited. `src/*`, `examples/KG/*`, numerical validators, physical algorithms,
integrator and RNG implementations remain unchanged.

The post-publication inventory contains exactly **14 unique qualified associating
systems**, each permitted only as `production_initial_state`; Ea10 is absent.
PRIOR_ACCEPTANCES.log pins the previous thirteen record hashes.
ACCEPTANCE_INVENTORY.csv records the final inventory and hashes. The verifier
checks every record with the established acceptance validator, in addition to
endpoint/provenance hashes and the new dossier integrity inventory.

Registration tests cover the exact reviewed source, unknown/old modes, wrong
system/ranges, altered endpoints, unqualified use, corrupt/missing evidence,
immutable publication, source classification, CPU/GPU authorization separation,
original recovery and inventory. The initial positive test's build-classification
failure is retained in REGISTRATION_TESTS_INITIAL.log; it was an administrative
compatibility issue, not a numerical trajectory failure. Final test counts and
results are in the test logs and milestone handoff. Each assistant-run job is
CPU-only and bounded by a timeout no greater than 600 seconds.

## Reproduction and read-only checks

From the clean committed checkout and existing dataset:

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea8_formal_acceptance_20261023/VERIFY.txt
timeout 600 python3 examples/KG_Assoc/reviews/e2_ea8_formal_acceptance_20261023/TEST_REGISTRATION.txt --registered
```

For independent CPU revalidation into a fresh analysis directory:

```bash
acceptance_work=$(mktemp -d /tmp/ea8_acceptance.XXXXXX)
for replica in 1 2 3; do
  timeout 600 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
    python3 examples/KG_Assoc/reviews/e2_ea8_formal_acceptance_20261023/REVALIDATE.txt \
      --replica "$replica" --output "$acceptance_work" || exit 1
done
```

REGISTER.txt records the exact publication operation. Do not rerun it to overwrite
an existing record; it rejects reuse before publishing. Use the read-only verifier
instead. Dataset JSONs follow the established convention of immutable originals
with committed byte copies and SHA256 bindings in the review dossier.

No simulation, further extension, Ea10 acceptance, production-registry activation,
100M preparation or production launch is part of this milestone. The final Git SHA,
remote agreement and clean-tree result are reported in the handoff.

Immutable formal record: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE08_EA08_48M_qualified_20261023_v1.json`.

SHA256: `f81d3e2f1d3a36cf4b2a7c09596f939e7adf62bc72c0ca103eeba73bbccdcc05`.

Final CPU tests: **10/10 registration tests passed** and **189/189 shared E2 regressions passed**. Three independent strict endpoint replays and the registrar triplet verification passed.
