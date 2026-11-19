# A. Associating production closure — 18–19 November 2026

Campaign: `assoc15_uninterrupted100m_20261023_v1`, branch `KremerGrest`.
Starting SHA: `4cfb7d3de92020197a328a5b03c5da7b9096c4ff`.
Final publication SHA: the commit containing this dossier; obtain with
`git log -1 --format=%H -- examples/KG_Assoc/reviews/production_closure_20261119`.

## Decision

**Formally complete for numerical/provenance closure and suitable for scientific
analysis with all existing qualifications retained.** The bounded authority audit
passed in 355.29 seconds: 45 independently validated histories, zero prepared,
5,536 preserved historical bindings, 6,411 distinct files hashed and unchanged
final file/directory identities. Exactly fifteen acceptance/system validations
and 51 distinct snapshot/system checks were executed; repeated identical results
were reused only within the stable-file audit.

[production.csv](production.csv) is the exact 45-history inventory: 15 approved
systems × the original three preparation families, 100,000,000 **additional**
steps each, totaling 4,500,000,000 steps. Absolute starts and ends, requested,
effective and chemistry seeds, history digests, receipt locations/hashes,
atom counts, per-file byte sizes and original scientific qualifications are
included. Every receipt is `validated.json`; no failure or recovery receipt was
substituted. There are no extra production completion or started journals under
the dataset's system production trees. Exactly the approved directories occur.

## Authentication and completeness

The published `production_activation_20261026/VERIFY_FINAL.txt` supplies the
authority checks, run under its authenticated CPU subprocess guard and a
600-second bound. The unmodified attempt and a digest-cache-only attempt each reached timeout
(exit 124) without a result; neither is counted as a pass. The bounded audit
reuses SHA256 values only for unchanged file device/inode/size/mtime/ctime,
checking identity after each read and again at audit end. It also runs each
identical acceptance/system validation and snapshot/system check once, retaining
the original validator results. All JSON read dependencies are pinned; the
entire bank directory inventory and cached file identities must be unchanged at
the end. Changed records/systems have distinct cache keys; snapshot results are
copied before returning. The cache assumes immutable inputs: filesystem metadata
is a change-detection aid, and concurrent same-size rewrites retaining identical
timestamps/identity can evade it. Each distinct file was actually SHA256-hashed;
this is not certification against concurrent adversarial writes. Do not reproduce
while dataset files may be changing. Mutation fixtures explicitly advance mtime
to test the metadata guard deterministically. This avoids repeatedly revalidating the same accepted
three-family bank for each approved production replica. No expected hash,
validator, approval, source map or scientific threshold was changed. The exact
executed wrapper is preserved in ORIGINAL_AUDIT.txt and cache fault checks in
CACHE_TEST.log and VALIDATOR_REUSE_TEST.log. AUTHENTICATE.txt reproduces the same published validator calls
and additionally permits these two documentation directories in the historical
Git-diff scope check; the original verifier allowed only its own activation dossier.
It verifies the activation, exact 45 approvals, frozen preparation, source/build
and executable maps, accepted parent bindings, unchanged journals, independent
receipts and **all current output hashes**, plus the 5,536 historical preservation
bindings and original publication seal. Its result is archived in
[AUTHORITY_AUDIT.log](AUTHORITY_AUDIT.log). This is independent reauthentication
of actual payloads, not inference from the monitoring script or completion flags.

The completion receipts were originally produced by the independent adapter's
`numerical_validation`: endpoint/output validators, event reconstruction,
step-by-step event/thermodynamic counter consistency, inherited counters,
permanent particle/topology/box checks, finite final coordinates, valid final
associating FENE geometry, six-channel normalization and exact multi-tau support.
Closure authenticates those receipts and their payloads rather than redoing
billions of MD steps or replaying all expensive event analyses. The compact
inventory additionally rereads every stress file through the established
`analyze_p42_rheology_pilot` reader and verifies its actual lag/count grid,
completion endpoint, numerical status, file sizes, receipt binding and ancestry.

| Output per history | Authenticated evidence |
|---|---|
| Six stress channels and combined G(t) | 100M samples; existing normalization reader passes |
| Lag grid and support | 195 actual bins; exact `n_pairs` for every bin |
| Thermodynamics | 100,000 measurements at 1,000-step cadence; numerical receipt passes |
| Reaction events | Complete accepted-event stream; reciprocal valence-one reconstruction and counters pass |
| Network topology | 10,000 frames at 10,000-step cadence |
| COM trajectories | 10,000 frames synchronized with topology |
| Bead coordinates | 1,000 schema-v2 frames at 100,000-step cadence |
| Final state | Permanent configuration/velocities and separate final association list |
| Numerical completion | Atomic native completion plus started/native-finished/validated/binding journals |

The nine scientific outputs total **98,992,743,616 bytes (98.99 GB)**, excluding
stdout/stderr, journals and historical evidence. Each file's digest is retained in
[bindings.log](bindings.log), together with review and lineage evidence. No raw
stress trajectory was requested. Final output is archival, not a checkpoint for
bitwise continuation. No dynamical history has been stitched across boundaries.

The unchanged estimator is
`G=(Gxy+Gxz+Gyz)/(5T)+(GNxy+GNxz+GNyz)/(30T)`.
Channels already contain volume normalization. Every-step sampling and
`Correlator6(40,16,2)` remain intact; the actual 100M support is 195 bins,
not an assumed dense linear lag grid.

## Scientific qualifications remain binding

All original per-system qualifications are reproduced verbatim in production.csv.
In particular, Ea10 starts are the explicitly approved **88M endpoints** with an
unresolved r003 elevated triangle/conformation regime. Extensive renewal and
triangle turnover did not distinguish stationary slow fluctuations from remaining
preparation relaxation. This review does not resolve either historical scientific
hold, certify finite-step MD/chemistry equilibrium invariance, or remove inherited
historical executable, decorrelation and initialization qualifications. Preserve
replica-specific early/late rheological and structural checks in later analysis;
the three preparation families remain the uncertainty units.

The additional production initial GPU-state readback and runtime independent
candidate oracle remain **`not_performed`**, as approved in the compatibility
decision. They are not PASS. The prior fifteen 100k compatibility runs and their
independent validation remain historical evidence; none was rerun here.

Numerical completion establishes neither equilibrium nor terminal stress
relaxation, unbiased stress estimates or converged viscosity. Full rheological
and structural analysis is a separate milestone.

## Preservation, reproduction and limits

All work ran locally on hostname `titan`; SSH was unnecessary. The assistant
executed zero GPU kernels or MD steps. Only the inspected native `--help` return
path and the published guard's exact CPU readback-dispatch probe were permitted;
no integration command was invoked. The visible process namespace contained only
tool processes. Host-wide absence of a surviving production process **could not
be established** from that namespace. No host process was signaled and no lock
was removed. Completed, hash-authenticated data do not imply a host-wide process
survey. A host terminal process survey remains an operational confirmation.

Reproduce on the original evidence workspace, with a clean committed checkout:

```bash
timeout 600 python3 examples/KG_Assoc/reviews/production_closure_20261119/AUTHENTICATE.txt
timeout 600 python3 examples/KG_Assoc/reviews/production_closure_20261119/INVENTORY.txt \
  --output work/kg_closure_inventory_NEW
```

The new directory must not exist. The inventory writes only there, fails closed
on discrepancies and creates no dataset state or approval. Its `bindings.log`
contains original receipt-derived output digests: pair it with the full authority
audit, which actually rehashes every payload. Inventory-only PASS is insufficient
for formal closure. New report formats use `.log`/`.txt` so they do not expand
the historical native `.py`/`.json` source-authority map.

[CPU_TESTS.log](CPU_TESTS.log) records eight campaign and eight E1 CPU tests.
The first two broad audits timed out and are explicitly not PASS; no numerical or
provenance discrepancy was found by the successful complete audit.
[INVENTORY_TEST.log](INVENTORY_TEST.log) records the real-data inventory checks,
including all 45 E1 ancestries and direct permanent-topology/box/ID comparisons.
The digest cache rejects same-size mutations and replacements whose signatures
change; fixture timestamps are explicitly advanced to avoid filesystem clock-granularity races. Validator-reuse
fixtures check exact record/system keys, independent returned snapshot objects,
changed JSON dependencies, changed snapshots and bank directory inventory changes.
These are deterministic validation checks, not statistical convergence tests.

The tracked additions are this dossier directory and its sibling readiness
dossier. A new ignored review workspace under
`kg_assoc_100m/aggregate/cpu_closure_review_20261119_v1` preserves working
checkpoints and logs; no existing dataset file was modified.
`examples/KG/`, `src/`, simulation sources, binaries, dataset outputs, E1/E2 banks,
acceptances, source/build records, existing reviews, approvals, registries and
execution journals were not modified. No campaign repair, recovery, new
preparation, seed reservation, activation or execution approval was performed.
