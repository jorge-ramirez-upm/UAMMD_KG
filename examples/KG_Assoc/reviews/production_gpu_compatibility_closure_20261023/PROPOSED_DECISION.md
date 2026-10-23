# Proposed subsequent CPU decision — not issued, not approved

**This document proposes a decision record. It is not a waiver, acceptance record,
execution approval or registry activation. No such record was created.**
The original compatibility-hold notice and false capability flags remain unchanged.

If the user approves the recommendation in ASSESSMENT.md, a separate administrative
milestone could publish one new immutable, hash-bound CPU record, provisionally under
`kg_assoc_100m/banks/production_compatibility_decisions/` (directory/record **not
created here**). Its scientific meaning should be:

> Accept the existing production GPU compatibility evidence for the frozen campaign
> with explicit residual software-validation limitations. Do not require additional
> production-specific initial-state device-readback or per-sweep independent candidate-
> oracle certification as a prerequisite for a separately authorized activation.
> Both certifications remain not performed for this production executable; neither
> is relabeled PASS. All observed numerical, provenance and completion requirements
> remain mandatory and unchanged.

The proposal is narrowly scoped to additional certification requirements; it does
not waive a failed numerical check or reinterpret missing scientific data as present.
A future record should contain the following explicit bindings and restrictions:

| Field / binding | Required content in a subsequent approved record |
|---|---|
| User decision | Exact explicit approval/reference, reviewer and timestamp; no inferred approval. |
| Review | This final review Git SHA and INTEGRITY.sha256 file hash; PER_SYSTEM.csv, source-equivalence and limitation evidence. |
| Frozen production scope | `assoc15_uninterrupted100m_20261023_v1`, exact plan SHA b9a6101c14f3fca645463b605adde6daa978f9c5db3a7e2f2aa885b71711ed47 and dormant-registry SHA739477c443f01c6cdbe0f4f96e765a66cb64a224531235cf47984ea354b28dfd;45 exact parents, original seeds/outputs, uninterrupted100M policy. |
| Existing GPU evidence | `assoc15_production_100k_compatibility_20261023_v1`, exact15 ordinary validated receipts and output hashes in COMPLETED_OUTPUTS.sha256; test plan d31fec4e07ec7a52aaa05f6a217802bab14e122b39513071d55ae341ae54dd34. |
| Source/build identity | Exact current source map, optimized native manifests, smoke SHA e1a00204f8753b4e513e6817169f40ec4aca0854decf52553550aaf25756d6d7 and100M SHA5c396533482e08a48bd20fc27e6bb63bec790efecf843ae73cf01a52bf6265e5; tested TITAN Xp/single-precision configuration. |
| Additional certification #1 | Exact initial GPU coordinates/velocities/IDs/types/partners before first integration were not independently dumped/compared by production; source-sharing and prior E2 GPU evidence support them indirectly. |
| Additional certification #2 | Independent per-sweep production candidate-set/distance/rounding-environment equality was not measured; the shared corrected host search is supported by earlier E2 GPU-evolved-position comparisons and existing CPU tests. |
| Coverage limits | One family per condition, Ea10 r003 and otherwise r001. Thirty other production starts are formally qualified/host authenticated, not directly covered by new production100k runs. No exhaustive future-state, hardware/compiler, or100M-stability proof. |
| Non-waivable gates | Exact accepted parents, source/build/approval/seed/output bindings, runtime numerical/FENE/reciprocity/conservation checks, strict endpoint/event/stress/lag-count validation, immutable journal authentication, stop-on-failure and non-destructive recovery. |
| Scientific qualifications | Existing15 formal records unchanged, including Ea10 r003's unresolved triangle/conformation mode and finite-step/equilibrium/statistical qualifications. No proof of equilibrium, stationary production or resolved viscosity. |
| Execution boundary | The CPU decision itself grants no GPU execution, activates no registry and creates no100M approvals. Activation and exact45 execution authorizations still require a subsequent explicit user decision. |
| Future changes | Any native/physical/source/executable/precision change outside the exact bindings requires new compatibility review/authorization; no whitelist of future modifications or silent edits to plans/old approvals. |

The existing validation-plan capability flags, original hold notice, receipts and
journals must remain immutable. If tooling later reports the approved policy outcome,
it should authenticate this separate decision and say **accepted with additional
certification limitations**; it must not print a fictitious readback/oracle PASS or
rewrite the original holds. Any administrative support for consuming that future
record belongs to the separately approved decision/activation milestone.

If the user instead requires direct certification, the smallest justified next
implementation is validation-only initial-readback and independent-oracle dispatch
in a new authenticated production diagnostic build, followed by separately authorized
bounded user-run tests. Reuse the existing exact readback/oracle helpers, preserve
physics/RNG, and bind executable compatibility through new immutable records rather
than overwriting the45 frozen preparations. This alternative is described only;
no code hook, build, test plan, seed, approval or GPU command is prepared here.
