# E2 initialization review: registration held

Starting repository: `b7e5dbcd05ccb02fc9f7d1c79d4f4371ca8622a7`, branch
`KremerGrest`. This is a **documented scientific review**, not a formal
`E2_acceptance` record, active-registry publication or production authorization.
No simulation, extension or production was launched. Original inputs, outputs,
plans, approvals, completion/failure records and historical data were not modified.

## Decision

**Do not confirm or automatically register dilute qualified acceptance yet.**
The joint 4M analysis exposes a coherent change in the requested triangle motif
observable L2. Treat this as potentially material unresolved topology drift;
the earlier recommendation cannot substitute for an explicit assessment of this
new evidence. Registration for the requested three-system batch is held in
accordance with the instruction to stop on material unresolved drift. No formal
acceptance records or active registry were created or changed.

| Condition | Endpoint / independent histories | Current disposition |
|---|---|---|
| `F04_N010_RP080_EE04_EA04` | 2M / three | Full numerical/provenance revalidation passed. Earlier qualified recommendation retained; not formally registered in this task. |
| `F04_N010_RP020_EE08_EA04` | 4M / three | Full six-segment validation passed. Acceptance deferred pending explicit assessment of the L2 shift. |
| `F04_N010_RP080_EE08_EA04` | corrected 8M / three | Pinned corrected payloads and earlier qualified initialization decision retained. Historical defective 6M data remain ineligible; not formally registered in this task. |

Numerical validation, scientific acceptance, selection of initialization states
and permission to launch production remain separate gates. A future qualified
record must permit **production initialization only** and explicitly say that
slow topology is **not proven fully decorrelated**. No permission for higher-Ea
conditions is inferred from the Ea=4 review.

## Joint dilute analysis

Sources are the original 0–2M attempt
`equilibrate_9845cd937e6f4aca85f6828dc4d441ae` (prepared at `862e604`) and its
2–4M extension `equilibrate_25125eea270c487a8279b5d6f6ca008c` (prepared at
`b7e5dbc`). Three E1 histories remain three independent units, not six replicas.
The first 1M window retains the unbound transient as context. The stationary
candidate comparisons use (1M,2M], (2M,3M] and (3M,4M]. An additional whole
(2M,4M] window evaluates the last segment at a longer correlation scale.

Existing event/network/conformation validators and correlation-aware window
helpers were reused. IATs, exact accepted-event population exposures, chemical
rates and 5/10/20-block SEM sensitivity are calculated within each segment.
No IAT, lifetime, transport or stress history is stitched through the independently
reseeded 2M restart. Paired window-mean differences use the three histories with
Student-t df=2. These exploratory intervals are not multiplicity-adjusted and
are not an equivalence test or an automatic acceptance rule.

| Observable | 1–2M | 2–3M | 3–4M | Late minus early, mean ± paired 95% half-width |
|---|---:|---:|---:|---:|
| Bound fraction | 0.789244 | 0.790453 | 0.791336 | +0.002092 ± 0.003340 |
| Intra bonds | 237.603 | 245.799 | 239.680 | +2.077 ± 12.602 |
| Inter bonds | 1340.885 | 1335.108 | 1342.992 | +2.107 ± 16.325 |
| Largest-cluster fraction | 0.967455 | 0.963929 | 0.968074 | +0.000619 ± 0.008537 |
| L1 parallel-pair motifs | 65.311 | 68.708 | 66.789 | +1.478 ± 10.939 |
| L2 distinct-star triangles | 37.269 | 36.423 | 34.565 | **−2.704 ± 1.507** |
| Star Rg² | 8.011595 | 7.990339 | 8.009634 | −0.001961 ± 0.023023 |
| Arm end-to-center R² | 18.19475 | 18.13488 | 18.18454 | −0.010207 ± 0.041256 |
| Accepted creations / time | 1.480433 | 1.481000 | 1.482433 | +0.002000 ± 0.024472 |
| Accepted breaks / time | 1.480933 | 1.478433 | 1.482100 | +0.001167 ± 0.026410 |
| Distinct-neighbor gains / time | 1.136033 | 1.135300 | 1.137533 | +0.001500 ± 0.050863 |
| Distinct-neighbor losses / time | 1.137533 | 1.132200 | 1.137167 | −0.000367 ± 0.047007 |

Populations, intra/inter balance, conformations, cluster connectivity and chemical
turnover are broadly compatible across the early/late windows at this resolution.
This compatibility does not prove stationarity. Mean degree and its second moment
have exploratory late-minus-previous positive intervals excluding zero, although
their early-to-late contrasts include zero; inspect their slow fluctuations too.

L2 declines in **every history in both consecutive comparisons**:

| History | 1–2M L2 | 2–3M L2 | 3–4M L2 | Late minus early |
|---|---:|---:|---:|---:|
| r001 | 37.192 | 36.654 | 33.804 | −3.388 |
| r002 | 38.249 | 37.719 | 35.755 | −2.494 |
| r003 | 36.367 | 34.895 | 34.136 | −2.231 |

The ensemble early-to-late decline is about **7.3%**. Its unadjusted paired interval
excludes zero. The last-minus-previous L2 difference is −1.858 ± 2.607 and includes
zero; that broader uncertainty does not establish that the decline has stopped.
Within the final 1M window the slopes have mixed signs, so this evidence does not
prove a continuing deterministic downward drift or identify its mechanism.
Nevertheless, the coherent mean shift is unresolved for the requested topology
review and cannot silently be covered by a generic slow-decorrelation qualification.
No universal percentage cutoff is being introduced.

Local topology sampling remains limited. Final-window L1 effective-sample estimates
are approximately 13.2, 5.0 and 7.1; mean-degree estimates are approximately 35.0,
13.1 and 3.9. Whole-extension L2 effective samples are approximately 16.9, 26.6 and
42.9, with estimated correlation times of 593, 375 and 233 physical time units.
Whole-extension mean-degree estimates are only about 9.1, 14.2 and 8.8.
IAT SEMs assume local stationarity and are heuristic estimates; they cannot waive
a visible change of mean or prove complete topology mixing.

[Complete window statistics and block sensitivity](joint4m_checked/summary.json),
[comparison table](joint4m_checked/REPORT.md),
[analysis configuration](joint4m_checked/analysis_config.json), and
[endpoint/provenance audit](provenance.json) retain the evidence.

## Provenance and qualifications

The six dilute segments and three weak-binding histories were fully revalidated:
parent identities/hashes, frozen geometry/physics, reciprocal sticker state,
absolute steps, chemical and effective MD seeds, numerical stability, permanent
particle identity, accepted-event replay, intra/inter bonds, L1/L2/connectivity,
conformations, final snapshot and restart sidecar consistency. All three chemistry
streams persist across the dilute extension; all three MD streams change.
Ordinary executable hashes, build logs, approvals and recorded scientific source
hashes were authenticated. The dilute recovery authorization, original-file hash
snapshot and completion bindings were checked without rerunning MD.

Corrected C1 uses exclusively
`banks/e2_extensions/C1_periodic_recovery_v1/r00{1,2,3}/state` at 8M. The frozen
inventory pins its plans, completion receipts and payloads; corrected event/network
and numerical outputs were independently revalidated against the authenticated
6M parents. The parent histories retain their **PBC-defective** provenance and
must never be used as equilibrium targets or active production starts.

C1's historical commit and Makefile digest were authenticated. The old compiled
executable bytes are not archived locally: their recorded digests are preserved,
not newly authenticated against those historical binaries. The current ordinary
E2 executable hashes were authenticated separately. This limitation is explicit
in the provenance audit; no missing executable archive or scientific evidence is
invented. It does not reverse the user's earlier documented C1 initialization
decision, and that decision is not converted into formal registered acceptance.

## Next scientific action

Review whether the coherent L2 shift is acceptable as a quantified initialization
bias, or whether further equilibration would be needed. That is a separate explicit
scientific decision; no extension is requested or scheduled by this report. If a
qualified initialization decision is made, identify the accepted final segments,
reviewer and evidence through the existing `kg_assoc_e2_registry.accept()` mechanism,
then publish an explicitly selected immutable registry with `publish()`. Publication
must remain separate from production launch authorization. **There is no activation
command for this held batch.** No candidate acceptance has been fabricated.

## Implementation checks

The joint analyzer is read-only with exclusive derived outputs. Four focused
regressions cover history/step/chemical and MD seed boundaries, paired independent
units, constant-observable mixing flags, no automatic acceptance and no overwrite.
The catalog reads a versioned documented-review decision and displays this hold,
without treating it as an `E2_acceptance` record. Existing registered acceptance
handling remains intact; a conflicting documented hold is flagged without silently
replacing a registry selection. Protected `src/` and `examples/KG/` are unchanged.
