# Associating-star campaign catalog: design for review

**Design only; no catalog implementation or runtime changes.** Audit baseline:
`862e604d2c9bab193cae03b31ed14d8ea7c7e039`, `KremerGrest`, 11 October 2026.
The catalog will be a read-only projection of existing evidence. It will never
launch MD, approve equilibrium, select new active states, or change source records.

## Audit: what exists and what it means

Inspected the protocol, system/run/production/acceptance schemas, frozen inventory,
E1 selector, E2/production runners, registry resolver, C1 recovery implementation,
and available small runtime manifests, completion records and reports. These
sources define **23 conditions: 15 associating and eight controls**, with three
history slots each. Eight geometries share 24 E1 starts; 12 geometry/Ee banks
include corrected C1 and 11 fresh banks. A condition includes Ea: sharing a
geometry or an equilibrium-preparation bank does not merge kinetic conditions.

The available local dataset snapshot has **452 directories including its root**,
248 empty leaf directories, including 207 under `systems/`. Counts can change
while the GPU host runs. Directory count is not a scientific completion count.
The dataset is ignored by Git; a repository checkout alone does not supply it.

| Location | Observed purpose and authority |
|---|---|
| `inputs/` | Eight externally generated geometry inputs, requirements examples and geometry-validation receipts. Requirements describe intended inputs; a receipt records a check. Neither is an equilibrated state. |
| `banks/e1/` | Original E1 snapshots, commands, diagnostics and some numerical-validation records. `active_states.json` selects replacements; absence of an entry falls back to the original path under the existing selector. Frozen inventory pins 24 selected starts. |
| `banks/e1_retries/` | Retained retries. RP060/r002 uses `attempt001`; its original attempt must remain visible. Selection is from the active map/inventory, not the latest directory name. |
| `banks/e2/` | Legacy generic bank layout; mostly empty placeholders. C1 contains original 6M histories with the PBC-defective candidate search. Their historical numerical receipts do not establish corrected chemistry or equilibrium. |
| `banks/e2_attempts/` | Generalized immutable plans, capped smokes and ordinary segments, each with three replica directories, approval, started/environment and completion/failure records. `plan.smoke` distinguishes roles; extensions reference predecessor plans. |
| `banks/e2_extensions/` | Legacy corrected C1 6M→8M recovery and a prepared infrastructure-check attempt with no replica completion records. Recovery uses `status.json`, unlike generalized `complete.json`. Path naming alone is insufficient. |
| `banks/e2_acceptance/`, `banks/e2_registry/` | Implemented authoritative acceptance/selection interfaces, **not present in this local snapshot**. Acceptance records name reviewer, evidence, endpoint hashes, qualification and permitted conditions/use; registry versions select them. |
| `builds/` | Four retained build manifests/log sets. They pin compiled SHA, sources, compiler and executable hashes. They are provenance, not simulations; an older build may remain valid historical evidence but be incompatible with current executables. |
| `aggregate/` | E1 audits, legacy/C1 validation probes, scientific reviews, figures and wrapper request/result journals. Some legacy smoke payloads live here, so adapters must read their manifests. Analysis outputs are derived; journals record command authorization. |
| `systems/` | 23 `system.json` records and scaffolded production/analysis directories. No local production `run.json` records were found. Empty production/figure directories are placeholders, not results. |

Small records show seven completed smoke test sets, a three-history RP080/Ee4
2M segment and four-window scientific review marked `review_required`. The
RP020/Ee8 2M plan/request and partial replica records are locally visible
(r001 has a completion receipt, r002 a start record, r003 no completion at the
time inspected). The user reports this run active on `titan`. **No GPU-host
process, scheduler or live output was inspected; do not infer remote liveness
or completion from this local mirror.** No MD logs/trajectories were scanned,
large payloads hashed, full numerical validators run or runtime files written
for this design audit. Completion/validation claims above are recorded claims,
not fresh payload authentication.

The frozen inventory records provisional qualified acceptance of corrected C1
8M states, with slow-topology relaxation. That documented scientific decision
must be displayed alongside the absence of a local formal active registry;
it cannot become automatic operational production readiness. The inventory's
older `proposal_only_no_execution_authorized` status is not authorization for
later runs; their own command/approval records provide their execution evidence.
No generic E1 bank `validation.json` was found locally; distinguish selected,
audited E1 starts from the legacy acceptance file required by control production.

Two existing convenience commands are unsuitable for reuse: production
`command_status` can rewrite `run.json`, and `command_aggregate` overwrites CSVs
and per-system summaries. The new catalog must call neither.

## Architecture and data model

Use a small Python reader with explicit versioned adapters, a normalized evidence
graph, and terminal/JSON/CSV/static-HTML renderers. All 23 expected conditions come
from `campaign_protocol.json`/`campaign_systems()` and the dataset manifest;
compare each `systems/*/system.json`, flag disagreements, and retain unknown
extra conditions as anomalies. Do not discover the campaign from populated folders.

| Entity | Minimum derived fields |
|---|---|
| Campaign snapshot | Campaign name, protocol/inventory hashes, catalog schema/generator SHA, scan start/end UTC, reader version, dataset location/host scope, coverage/errors and freshness. |
| Condition | Canonical `system_id`, groups, associating/control, f/N/rho_p/Ee/**target Ea**, common physics, counts/box, geometry/Ee bank references, three history slots and separate readiness gates. |
| History | Condition + r001/r002/r003, selected E1 start, lineage roots, branch/fork edges and segment IDs. Shared starts are references, not copied records or extra independent samples. |
| Attempt / replica segment | Stable ID from role + dataset-relative path + plan/command hash; E1/E2/smoke/recovery/production role, replica, absolute start/end and stage-relative production steps, parent artifact/hash, requested length, actual **preparation Ea**, code/source/build/executable provenance, chemistry/MD/effective seeds, reseeding/switch policy, timestamps/host/PID and evidence references. |
| Artifact / evidence | Relative path, role, declared hash/size, observed existence/stat token, record schema, asserting source/hash, verification scope/time/validator SHA, external location or unresolved reference. Payload stays on disk. |
| Review / acceptance / selection | Review windows/summary/figure links and source-plan hashes; separate reviewer/evidence/qualification/permitted-use acceptance records; explicit registry version and its selected three endpoint snapshot/sidecar hashes. |
| Production | Accepted initialization references or control E1 acceptance, parameter-switch evidence, prepared run parameters, launch-authorization evidence, replica completion/validation, analysis results/units/windows and artifact links. |

Preserve source values and their asserting records alongside normalized fields.
Unknown schemas remain inspectable but cannot supply authenticated readiness.
Use campaign/protocol/inventory fingerprints plus source-relative IDs to identify
copies; location and observation scope remain distinct. Segment steps do not add
across replicas, retries or forks. Successive segments of one history are not new
replicas. Keep Ea=4 preparation versus Ea=6/8/10 downstream use explicit.

### Status is a tuple, not a traffic light

- **Execution:** not prepared, planned, started/liveness unknown, observed running,
  completed receipt, failed receipt, interrupted/unresolved, conflicting evidence.
  An attempt with one completed and one started replica remains partial.
- **Numerical validation:** absent, recorded pass, authenticated pass (scope/time),
  recorded failure, stale/mismatched, not applicable. Completion alone is insufficient.
- **Scientific acceptance:** absent, review required, documented qualified decision,
  formal accepted/qualified/rejected when backed by explicit evidence. Smoke has
  `not_applicable_for_equilibrium`, regardless of numerical success.
- **Active selection:** explicit selected registry/map version, unselected,
  superseded **by an explicit replacement relationship**, ambiguous or missing.
  A newer timestamp does not supersede older data or acceptance.
- **Authorization:** stage-specific plan-bound command/approval evidence, absent,
  scope mismatch or legacy execution evidence without a separate authorization receipt.
  An E2 approval or `production_initial_state` permission never authorizes 100M MD.
- **Integrity:** metadata consistent, payload deferred, cached verified, verified now,
  changed, missing, unreadable, unsupported schema or outside available scope.

Production eligibility requires compatible parameters, all three appropriate
accepted/selected starts, required numerical/integrity evidence and any Ea-switch
validation. Authorization remains a separate gate; never print a bare “ready”
when any gate is unknown. For controls E2 is **N/A**, not missing. Absence from
an incomplete local copy means “not available here,” not “never produced.”

C1 must carry distinct provenance classes: `historical_pbc_defective_6M` and
`corrected_C1_8M`, assigned from the frozen pins and recovery evidence. The latter
retains its defective parent lineage and qualification; recovery does not redeem
historical statistics. Legacy small smokes and C1 Ea-switch smokes remain tests.
An operational selection requires the existing acceptance schema/registry rules,
including exact endpoints and permitted system IDs; no filename, review wording,
low drift or zero warning count can synthesize acceptance.

## Proposed interface and report

Commands are proposals; **`catalog.py` does not exist yet**. Defaults discover the
repository/dataset from the script, require no environment variables and print
the observed commit, dataset coverage and verification mode. Status/show write
nothing; report/export write only new derived output snapshots.

```bash
python3 examples/KG_Assoc/campaign/catalog.py status
python3 examples/KG_Assoc/campaign/catalog.py show F04_N010_RP020_EE08_EA04
python3 examples/KG_Assoc/campaign/catalog.py report
python3 examples/KG_Assoc/campaign/catalog.py export --format json
python3 examples/KG_Assoc/campaign/catalog.py verify --system F04_N010_RP080_EE04_EA04 --scope initialization
```

`verify` is a proposed opt-in read-only audit, never MD or an acceptance action.
Scopes: metadata, initialization (accepted endpoints/lineage), or full (existing
numerical/event/trajectory validators). It writes optional **derived verification
receipts**, never source completion/acceptance records. Full scans are explicitly
expensive and should run on completed snapshots off the busy GPU host.

Illustrative terminal overview (actual output contains all 23 rows; these rows
illustrate the local metadata-only audit, not newly verified scientific results):

```text
Campaign: 23 conditions / 69 history slots; local snapshot; payload checks deferred
SYSTEM                          E1       SMOKE       E2                 SCIENCE          PROD
F04_N010_RP080_EE04_EA04         3 sel.   pass rec.   3/3 @2M rec.       review required  blocked
F04_N010_RP020_EE08_EA04         3 sel.   pass rec.   1 done/1 started   review pending   blocked
F04_N010_RP080_EE08_EA04         3 sel.   separate    corrected @8M rec. qualified report registry absent
F04_N010_RP080_EE08_EA08         shared   pass rec.   shared C1          qualified report registry absent
F04_N010_RP080_NONASSOC          3 sel.   N/A         N/A                E1 record needed unprepared
... 18 further conditions; rec.=recorded claim, sel.=selected E1, not acceptance
```

`show` expands all three histories with E1→segment→restart/production lineage,
absolute steps, seeds and transitions; separates primary selected states from
failed, unselected and defective historical branches. Every claim has a relative
source link, declared hash, verification scope/time and any discrepancy. Show
review windows, rate units, Rg²/arm diagnostics, figures and acceptance qualifications
through linked summaries; do not recompute science during browsing.

HTML: an offline, static index with a 23-row searchable table; filters for geometry,
Ee/Ea, role, execution, validation, scientific acceptance, selection and integrity.
Summary counts distinguish conditions, unique starts, histories and attempts.
Each condition page has parameters/readiness gates, three expandable lineage
columns, an attempts table (smokes clearly labeled), evidence/review/figure links,
and a C1 historical warning where applicable. Include freshness/coverage and
unresolved-reference panels. Use embedded data/vanilla JS, no server, CDN or
`fetch()` requirement for local files; escape untrusted strings and links.

Recommend new immutable snapshots under
`examples/KG_Assoc/catalog_output/<snapshot-id>/` (outside runtime data), containing
`index.html`, condition pages, `catalog.json`, `systems.csv`, `histories.csv`,
`attempts.csv`, and a generation manifest. JSON retains the graph and evidence;
CSV is a compact projection with schema version, units, source IDs and explicit
null/N/A/unknown distinctions. Optional analysis export reads bounded summaries,
not trajectories. Catalog outputs/cache will be Git-ignored in a later phase;
no ignore rules or output directories are added in this design task.

## Integrity, portability and active-run safety

1. Scan recognized small metadata filenames, not every payload recursively.
   Adapters cover E1 commands/validation/audits, original C1 completions, recovery
   statuses, generalized E2 plans/approvals/completions, workflow journals,
   acceptance/registry versions, production runs and analysis manifests.
   Bound metadata reads; oversize/truncated/unknown JSON becomes a visible issue.
2. Check small-record hashes, plan/completion/approval binding, condition/geometry
   agreement, parent existence/hashes, reciprocal lineage references, absolute
   ranges, chemical identity across extensions, MD reseeding and seed collisions.
   Flag cycles, forks, missing replicas, wrong switches and conflicting receipts.
   Report a missing dependency as unresolved; do not select an alternative parent.
3. Routine refresh hashes **metadata only**. Large payloads/executables have declared
   hashes and explicit deferred verification. Full validators/hash checks run once
   on demand after completion, with cached scope, validator version, source hashes,
   size/mtime_ns/inode and observation location. Stat equality is a cache hint,
   not cryptographic proof of unchanged bytes; periodic deep audits remain optional.
   Changed dependencies invalidate cached descendants. Never claim full numerical
   authentication from metadata-only checks or extrapolate a partial verification.
4. Cache parsed metadata by fingerprint; begin with regenerable JSON, add SQLite
   only if measured directory/record volume warrants it. No frame/event data in
   the catalog. Work scales with records/attempts, not MD step count. New files
   must still be discovered; cache cannot hide missing/changed dependencies.
5. While runs are active, read only stable plan/request records and atomically
   completed receipts. Use pre/post stat checks and bounded retries for changing
   legacy JSON; label concurrent change and retain the last observation as stale.
   Never parse/hash growing `.events`, `.state`, trajectories or logs by default,
   acquire simulation locks, query/control a remote GPU process, or write runtime
   files. Catalog generation is a non-atomic observation interval, clearly dated.
   Write derived output to a temporary destination within the catalog-output tree,
   then publish a new snapshot atomically; never replace an old report.
6. A start record without completion is not proof of a live process. Default to
   liveness unknown and show host/start/last observation. Long elapsed time is a
   stale-candidate warning, not failure. Optional local-only observation requires
   host and process identity checks; never test a remote PID against the local
   PID namespace. GPU-host status/export is a later operator action, not an SSH
   scan performed by the catalog. Available-host coverage is always visible.
7. Store canonical dataset-relative links plus original recorded paths. Normalize
   legacy absolute paths only using an exact declared root mapping, never basename
   guessing; missing mappings remain unresolved external references. Resolve path
   traversal/symlinks against trusted read roots. Compute links relative to each
   HTML page and URL-escape paths; copied report+dataset trees remain navigable.
   Remote-only evidence is labeled unavailable locally with its host/root reference.
8. Do not choose the “latest” registry automatically. With one unambiguous available
   registry, display its selection explicitly; with multiple versions show each and
   require a chosen view (optional `--registry`). The catalog cannot activate it.
   Historic selections remain inspectable. Separate provenance completeness from
   current build compatibility; an old SHA is not itself a failed scientific run.

## Testing and implementation phases for approval

Tests will use synthetic metadata and temporary trees, with no GPU required:
23 expected conditions including empty scaffolds; shared starts and E1 retry;
smoke exclusion; defective/corrected C1 and qualified-but-unselected acceptance;
registry conflicts and permitted downstream Ea; exact parent/seed/step lineage;
partial/failed/running-unknown records; missing hashes/files and unsupported schemas;
production completeness versus authorization; source/validator cache invalidation;
relocated links, escaped HTML/CSV and symlink/path traversal; concurrent/truncated
writes. A fake giant payload must never be opened by routine status/report.
Assert identical runtime-tree contents/mtime before and after scans; stub all
launch/mutation entry points to fail. Stable fixture inputs yield deterministic
graphs/exports apart from explicit observation timestamps.

1. **Metadata core and CLI:** approve status vocabulary/source precedence; implement
   adapters, 23-condition model, lineage/anomalies, `status`/`show` and JSON/CSV,
   with no deep payload I/O or runtime writes.
2. **Static navigation:** immutable HTML snapshots, search/filters, relative evidence
   and figure links, with freshness and incomplete-host coverage always shown.
3. **Opt-in authentication:** scoped verification receipts, pure existing validators,
   dependency-aware cache and explicit registry-view selection; retain a fast default.
4. **Later scale/host support:** only if needed, SQLite cache, operator-produced host
   snapshot import with hash/conflict checks, and executable/source archival links.
   Host imports never silently resolve conflicts or promote acceptance.

Review decisions: approve the orthogonal status labels and C1 documented/formal
acceptance distinction; confirm explicit registry selection rather than a “latest”
rule; choose catalog output/retention location; agree default verification scope
and deep-audit cadence; decide whether later remote snapshot imports and standalone
production-authorization receipts are needed. Legacy missing acceptance/authorization
provenance must remain unknown until an authorized separate scientific workflow
records it. **Approve this design before any catalog implementation.**

This document is committed/published through an isolated worktree: the active
checkout remains clean at the audit SHA. Do not pull a new commit into the GPU
checkout during a run; the E2 runner authenticates its prepared SHA/clean tree
between histories. The design can be reviewed on GitHub without updating it.

Only this document is changed. No campaign files, acceptance records or running
simulations were modified; `src/*` and `examples/KG/*` remain untouched. Design
validation is source/metadata inspection and document/diff checks, not GPU or
scientific convergence testing.
