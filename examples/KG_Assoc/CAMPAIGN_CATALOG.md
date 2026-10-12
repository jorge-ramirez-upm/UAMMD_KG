# Campaign catalog: metadata and offline navigation

Phases 1–2 of [the approved design](CAMPAIGN_CATALOG_DESIGN.md) are implemented.
The catalog never launches a simulation, updates a registry, or runs numerical
validators. It reads bounded JSON metadata and stats declared artifacts; it does
not open trajectories, events, restart payloads, executables or logs. Its only
writes are new, Git-ignored report snapshots under `catalog_output/`.

From the repository root, generate and open a complete offline report:

```bash
python3 examples/KG_Assoc/campaign/catalog.py report --open
```

This creates an immutable snapshot with a searchable/filterable 23-condition
index, 23 system pages, `catalog.json`, `systems.csv`, `histories.csv`,
`attempts.csv` and a hash-bound `generation_manifest.json`. Each refresh creates
a new identity. A failed renderer retains its staging snapshot for inspection;
previous reports are never replaced. If a graphical browser is unavailable, the
command prints the exact HTML path. Report links are relative to their pages;
keep the report and dataset in the same relative layout when copying them.

Read-only terminal commands:

```bash
python3 examples/KG_Assoc/campaign/catalog.py status
python3 examples/KG_Assoc/campaign/catalog.py show F04_N010_RP020_EE08_EA04
```

`export --format json`, `export --format csv` and `export --format all` produce
new export snapshots. Every export retains JSON and all three CSV projections;
`--format` chooses the primary path printed. CSV protects formula-like strings,
preserves physical parameters, and labels unknown values and MD-step units.

The dataset defaults to `examples/KG_Assoc/kg_assoc_100m/` beside this script's
repository, independently of the current directory or environment variables.
A checkout without that ignored dataset still lists all 23 expected conditions
and clearly marks local coverage unavailable. It never searches unrelated disks
or assumes missing local data does not exist on the GPU host.

## Reading the evidence

`catalog_model.py` contains version-one metadata adapters and a normalized graph;
`catalog.py` provides rendering and the CLI. Existing `campaign_systems()` supplies
protocol conditions and identifiers. No workflow status/aggregate functions are
called because those functions can mutate runtime records. Original small
records, their observed SHA256/stat tokens and asserting source IDs remain in the
JSON graph alongside normalized attempts, histories, references, reviews,
acceptances, selections and diagnostics. Unknown schemas or malformed records
remain visible and cannot supply recognized completion/acceptance evidence.

The graph exposes independent execution, numerical, scientific, selection,
authorization and integrity fields. A completion receipt means **recorded**
completion. Numerical passes mean **recorded** passes; even hash-checked metadata
is not authenticated trajectory/restart physics. Production initialization
eligibility remains blocked/unknown until the separate operational verifier runs;
scientific acceptance never grants production launch authorization.

Three slots per condition reference 24 shared E1 inputs across eight geometries.
Active E1 replacements are read from the existing map, with its original fallback;
selection is not scientific acceptance. All retained E1 branches remain visible.
E2 lineage uses recorded output/parent identities, absolute steps, chemistry
identity and fresh MD seeds. Forks are displayed without adding independent
replicas. A newer timestamp never supersedes a record; only an explicit
replacement relationship can mark a branch superseded.

Historical pinned C1 6M data carry `historical_pbc_defective_6M` and cannot be
accepted starts. Frozen corrected recovery prefixes carry `corrected_C1_8M`,
retain the defective parent lineage and show the documented qualified decision.
That decision remains separate from formal `E2_acceptance` records. Smokes,
including bounded legacy manifest-based tests and explicit Ea-switch tests, are
never equilibrium segments. Explicit `--switch-ea-from`/`--Ea` evidence is shown;
restart-payload authentication remains deferred.

With multiple registry versions, status/report show an ambiguous view and no
selected acceptance. Choose a view explicitly, **without activating it**:

```bash
python3 examples/KG_Assoc/campaign/catalog.py --registry banks/e2_registry/VIEW.json report --open
```

One available registry is displayed explicitly; no available registry means
missing selection. The catalog checks metadata bindings, three endpoint
identities, numerical receipts, permitted conditions/use and required declared
endpoint hashes. Payload content authentication is always deferred. Old code or
build SHAs are retained provenance, not by themselves evidence of an invalid run.

## Active-run safety and limits

The catalog observes a non-atomic interval on this host. It does not query a GPU
process, acquire simulation locks or infer liveness from a remote PID. A start
receipt without an endpoint is `started_liveness_unknown`; a start older than
24 hours adds a stale-candidate diagnostic, not a failure. Concurrent small JSON
writes receive two bounded stat/read/stat attempts; unstable, truncated, oversized
(4 MiB limit), nonfinite or unsupported metadata produce visible diagnostics.
Paths are confined to trusted repository/dataset roots. Absolute legacy paths
are relocated only using declared dataset roots or the legacy recovery's explicit
command root; unresolved roots remain unavailable rather than basename-matched.

The index provides coverage, observation timestamps, unresolved references,
missing/changed metadata, schema issues, seed/step lineage discrepancies and
review links. Scientific review statistics and figures are linked from existing
analysis records; they are not recomputed. Build and workflow journals remain
inspectable as evidence. `show` includes relevant reference/integrity diagnostics.

These phases have no deep-verification command, cache, database or cross-host
imports. They do not authenticate physical payloads or independently establish
scientific acceptance. Future verification/host support remains separate work.

Tests run without NVIDIA hardware:

```bash
python3 -m unittest discover -s examples/KG_Assoc/campaign -p test_catalog.py -v
```

Fixtures cover condition coverage, shared/retry starts, defective/corrected C1,
smoke exclusion, registry ambiguity and permissions, seed/step lineage, explicit
Ea switching, failures and unknown liveness, changed/unknown/truncated/concurrent
metadata, relocated/unsafe links, HTML/CSV escaping, immutable publication and
failure retention. A sparse 10 GB event file is guarded against opening; runtime
sizes/mtimes are unchanged across scan and report. End-to-end CLI tests require
neither GPU nor simulation entry points.

Update the GPU simulation checkout only after its active run has ended: the E2
runner authenticates its prepared Git SHA between histories. This implementation
was developed and pushed from an isolated worktree; the simulation checkout was
not updated. Once installed, catalog generation itself is safe during active runs.

## Implementation validation

Starting commit: `fa50bb49a57a96ed40a595055df394d01fa7d753`.
The 29 catalog regression tests pass without GPU hardware. Python compilation
and whitespace checks pass. A read-only inspection of the available local data
loads 286 bounded metadata records, covers all 23 system records and 24 selected
E1 inputs, and renders an offline snapshot in roughly 1.3 seconds on this host.
The remaining catalog diagnostics are explicit lineage forks; they do not imply
failed scientific data. These are metadata observations, not GPU-host or payload
authentication results.

An additional broad campaign test run (88 tests at that point in development)
reported four errors because compiled simulation executables are absent from
the isolated worktree. Those existing executable-dependent checks were not
changed or represented as passing. No CUDA source changed, no rebuild is required
for this catalog, and no GPU/MD test was launched. A real graphical browser was
not available for interactive UI testing; static rendering and escaping are
covered by the regression suite.

## Documented joint-review decisions

The catalog also reads version-one `reviews/*/decision.json` records with stage
`E2_scientific_review_decision` and `formal_acceptance: false`. These are documented
assessments, never active-registry or `E2_acceptance` entries. A recorded material
drift hold appears as `review_hold_material_drift`; conflicting registered
acceptance is diagnosed without replacing any registry selection. The system
page links the decision and its bounded metadata/report evidence. Fast catalog
refresh still distinguishes recorded payload-validation evidence from payloads
newly authenticated by the catalog.

An original incomplete receipt remains visible when a later completion records
recovery. The catalog reconciles its execution status only when the valid
completion binds both that failure receipt and a plan-bound approved recovery
authorization by metadata hashes. Changed or missing bindings retain conflicting
status; scientific acceptance is never inferred from recovery completion.

A later recommendation may supersede a documented hold only through an explicit
`supersedes_documented_review` reference to the prior decision path and SHA256,
for the same system with an increased absolute endpoint step. Timestamps never
choose a newer decision. The old hold remains linked and visible as superseded;
missing, changed or unrelated bindings retain a hold or unresolved status.
The 6M dilute reassessment is documented in
[reviews/e2_reassessment6m_20261013/DECISION.md](reviews/e2_reassessment6m_20261013/DECISION.md).
Its recommendation appears as `qualified_acceptance_recommended_not_registered`.
It creates no formal acceptance, active initialization selection or production
authorization. Version-two joint summaries remain derived review evidence.

The separately approved formal acceptances are documented in
[reviews/e2_formal_acceptance_20261013/README.md](reviews/e2_formal_acceptance_20261013/README.md).
Valid records appear in each system's `formal_acceptance_records` and give
`formal_acceptance_recorded_payload_deferred` scientific status. An acceptance
record alone leaves active `selection` missing and production eligibility blocked.
Terminal/HTML status and JSON/CSV exports retain production authorization as a
separate field. No catalog command activates a registry or authorizes execution.
