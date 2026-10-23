# Approved production compatibility decision

The user explicitly approves `accepted_with_additional_certification_limitations`
for the exact `assoc15_uninterrupted100m_20261023_v1` campaign. This is a separate
administrative decision about two additional certification prerequisites. It
neither activates production nor authorizes a GPU launch.

The scientific/numerical basis remains the unchanged
[compatibility closure](../production_gpu_compatibility_closure_20261023/ASSESSMENT.md)
and its final Git commit `cb025ec6d734bc077dc485ae229cd7b77d6bc2e3`.
The closure independently replayed all fifteen actual 100k completions: 1.5M existing
MD steps, 15,000 chemistry sweeps, 46,901 formations and 46,926 breaks. All six-channel
stress reconstructions agreed exactly with stored G(t). These are historical GPU
results; this publication executes zero GPU/MD steps.

| Additional certification | Recorded status | Administrative effect |
|---|---|---|
| Exact initial production GPU coordinates, velocities, identities, types and chemical partners independently read back and compared | **not performed** | No longer an additional prerequisite for separately approved activation |
| Independent production runtime candidate-set and rounding oracle | **not performed** | No longer an additional prerequisite for separately approved activation |

Neither certification is PASS. The original hold, false capability flags, plans,
receipts, journals, source authorizations and closure proposal remain byte-identical.
The separate approved decision resolves the additional-certification policy; it
does not rewrite what the tests measured. Shared E2 implementation evidence supports
the reviewed production path indirectly, with the coverage limits retained in the
closure. No concrete production defect was identified there.

Exact accepted-parent authentication, source/build/executable/approval/seed/output
bindings, chemistry replay and conservation, numerical/bond geometry integrity,
six-channel stress reconstruction, lag/count/output integrity, immutable journals,
independent completion validation, stop-on-failure and non-destructive recovery all
remain mandatory. The fifteen existing formal qualifications remain unchanged,
including Ea10 r003's unresolved late triangle/conformation regime. This decision
establishes neither equilibrium nor stationarity nor unbiased stress measurements.

## Immutable publication and scope

The actual record is:

`examples/KG_Assoc/kg_assoc_100m/banks/production_compatibility_decisions/assoc15_compatibility_additional_certification_decision_20261023_v1.json`

SHA256: `f7e8a98bcc8a0b94d65a714b4daea394e6c2cb1892d8aa4eb6ec07faf4913516`.

`DECISION_RECORD.log` preserves its exact JSON bytes in Git. `PUBLICATION.log` binds
both copies by SHA256. The record binds the explicit conversation approval, exact
source map, native build, frozen production plan/registry/reservations, all 45 initial
state/seed/output identities and qualifications, fifteen native and independently
validated completion journal chains, final closure seal, and preservation inventory.
The inventory authenticates 5,523 existing file bindings, including all fifteen
acceptances, production preparations, compatibility outputs and historical reviews.
Git submodule entries are commit identities rather than files; no submodule changes
are made. Exact source-map equality and ancestry are required, with no future-source
whitelist. Reuse with different native sources, binaries, parents, plans or seeds
fails authentication. Newly added administration uses `.txt` helpers, avoiding a
change to the existing native/planner source map.

`VERIFY.txt` provides a read-only preactivation resolver that authenticates the
Git-published decision, hashes, source map, ancestry, historical independent replay
receipts, current fifteen completion statuses, fifteen acceptance inventory and all
45 untouched production preparations. A Git-only subprocess guard forbids native
program execution. This adds no launch path or production authority. A separately
authorized activation milestone must bind this decision SHA256 into its exact
execution authorities and retain every mandatory validator; this preactivation
auditor deliberately requires the registry dormant and production outputs absent.

## Verification and boundaries

`TEST_DECISION.txt` contains thirteen deterministic CPU tests with temporary fixtures:
exact policy, narrow scope/ancestry, both unperformed certifications, mandatory gates,
no activation/execution/future-source permissions, retained hold/Ea10 qualifications,
changed/missing evidence and Git-publication authentication. Evidence mutations never
touch a real attempt. Existing adapter regressions are reused for numerical/provenance
and immutable-journal behavior; no native implementation or numerical validator changes.

See `CPU_TESTS.log`, `ADAPTER_TESTS.log` and `VERIFICATION.log` for results. All
assistant jobs use a 600-second timeout. Starting SHA is the closure SHA above.
Only this new dossier is changed; `src/` and `examples/KG/` remain untouched. No
new simulation seeds/plans, registry activation or production execution approvals
are created. Production remains unauthorized pending the user's separate decision.
