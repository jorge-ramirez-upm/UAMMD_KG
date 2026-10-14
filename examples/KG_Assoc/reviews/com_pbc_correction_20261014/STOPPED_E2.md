# Read-only diagnosis: RP040 Ee8 E2 wrapper stopped after r001 MD

Attempt:
`examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP040_EE08/equilibrate_16a4b0c048e6484bb73910a53c5e84ce`.
This report creates no recovery authorization and does not modify any attempt file.
Exact plan, hash inventories, replica/seed identities and fresh r001 validation are
in [STOPPED_E2_EVIDENCE.json](STOPPED_E2_EVIDENCE.json).

## Cause and stage

The plan was prepared at `97118b8a1fbde4f3cd28002014f345191ec53c40`.
r001 started at 10:39:55.781406 on 14 October (Europe/Madrid).
The previous COM **audit-only** commit `75abee1…` advanced HEAD at 11:09:13.
The wrapper recorded `prepared code SHA changed` at 11:17:11.526604.

`kg_assoc_e2.py::launch` waits for the MD executable, checks its PASS marker and
parent hashes, then calls `live_code(plan)` **before** numerical validation and
`complete.json` creation. `live_code` first requires a clean tree, then exact HEAD
identity with `plan['git_sha']`. That HEAD comparison failed. The failure is in the
post-MD wrapper guard, not in the GPU integrator or event validation. It prevented
receipt creation and launch of the following two replicas.

At investigation start, **zero existing prepared source-file digests changed and
zero prepared executable digests changed**; there is no evidence of a build-artifact
replacement. The audit commit added a new CPU test and three audit JSON files to
the broad tracked source inventory. It changed Git identity even though every
previously prepared byte remained intact. The full broad recovery source dictionary
would also differ because those JSON keys are new. The original guard failed on
HEAD before reaching that distinction or the executable/make checks.

The earlier audit's statement that the active job was "unaffected" was too broad:
its physics and MD execution were untouched, but committing in the shared repository
triggered this wrapper guard after r001 finished. The cause was repository
development during a strict frozen-HEAD workflow. The observer changes approved in
this task occurred afterward and are separately listed in the forensic JSON;
they did not cause the original stop.

## Replica disposition and checkpoints

| Replica | Existing evidence | Fresh read-only classification |
|---|---|---|
| r001 | Bound `started.json`, environment/logs, PASS marker, all eight final/history outputs; `incomplete.json` names the SHA guard; no `complete.json` | `validate_preserved`; MD completed **0–6M**, and independent CPU numerical/event/network/restart/conformation validation passes |
| r002 | Empty directory; no start, logs, state, endpoint or completion | `run_missing`; never started |
| r003 | Empty directory; no start, logs, state, endpoint or completion | `run_missing`; never started |

r001 has 6001 frames, 60000 chemistry sweeps, 198494 accepted events, creations
100094, breaks 98400, and 1694 final bonds (140 intra, 1554 inter). Its final
`state.restart.lammpsdat` and `state.assoc_restart` are genuine absolute 6M endpoint
payloads; their digests are respectively:

- `e47ef5faec83cada706690ae8be28a23caa7433e513796d712b441bd37146573`
- `a4892e04c2b32403488c6c6438fe6ffe1c0c66925a84651289aa2a97275ca957`

The complete event, numerical, state, conformation and mirror histories authenticate
against the original plan/parent/start provenance and current bytes. No partial
MD history was found. The available r001 checkpoint is its **final 6M endpoint**;
this E2 executable does not produce periodic MD restart checkpoints. r002/r003 have
none. Their original frozen E1 inputs and the original three-history smoke evidence
remain available. There is no reason to rerun r001 or reinterpret r002/r003 as partial
continuations. Numerical validity is not equilibrium acceptance: two independent
histories and joint scientific assessment are still missing.

## Supported recovery and safest recommendation

`kg_assoc_e2_recover.py` already supports this exact orphan pattern: original bound
start + all final outputs + PASS → `validate_preserved`; truly empty replicas →
`run_missing`. It freezes all existing bytes in a **new** recovery journal,
validates preserved endpoints first, runs only missing original histories, and
adds completion evidence without overwriting original outputs/failure receipts.
It explicitly refuses partial MD reruns. Its recovery mechanism does not require
starting r001 from its 6M checkpoint or deleting its failure marker.

However, recovery authentication requires a clean tree, original-plan ancestry,
**equality of the broad scientific source dictionary**, matching original executable
bytes/build logs, original approval and matching smoke evidence. The current/final
COM-correction checkout fails that source compatibility policy: production observer
and analysis files changed, a Makefile dependency changed, and audit/observer metadata
keys were added. The policy includes files beyond the E2 runtime dependency graph.
Do **not** run recovery here assuming that "observer only" exempts those checks.
Neither the recovery guard nor original plan/build/smoke records was weakened.

Safest procedure, requiring separate user authorization for actual recovery:

1. Keep every original byte, including `incomplete.json`, r001 outputs and the empty
   r002/r003 directories. Retain the original plan, approval, smoke and executable
   archives. Confirm no remaining MD/wrapper process owns the attempt before acting.
2. Arrange a clean **frozen original-code execution context at the prepared commit
   `97118b8…`**, preserving the plan's absolute source/executable/dataset paths and
   original executable bytes. A relocated worktree alone will not satisfy the
   path-keyed source dictionary; use a controlled isolated context with identical
   paths rather than rewriting the plan or disturbing the final development checkout.
3. In that context, recheck the source/build/binary/smoke/approval hashes, original
   ancestry and absence of the launch lock. Require exactly the classifications
   `validate_preserved/run_missing/run_missing`, and rerun the preserved endpoint
   validation before authorizing missing MD. Do not use `--force`, delete files,
   clear failure receipts or prepare a replacement 0–6M attempt.
4. The supported entry point is `run_e2.py recover --system
   F04_N010_RP040_EE08_EA04` in that frozen context. This is a recommendation only;
   it was **not invoked**. It would create new recovery evidence, authenticate r001
   without MD repetition, and run only the original r002/r003 commands/seeds to 6M.
   Keep that execution context immutable until all post-MD guards finish.
5. Then obtain the three-history read-only scientific review. No scientific
   acceptance or production initialization permission follows from this diagnosis.

If recovery must instead use the final COM-correction checkout, a **separate approved
E2-scoped compatibility/provenance transition** is needed first, followed by matching
build/smoke evidence. This is not implemented in the observer task. Never blanket-ignore
source differences or manually edit recorded digests.

Rebuilding under the final COM commit is physically compatible with preserved E2
physics/chemistry: `kg_assoc_stars.cu`, its included physics/kinetics/integrator headers,
KG baseline and frozen parameter definitions are unchanged; the production COM
observer is not included by E2. The E2 compile recipes/flags remain unchanged. But
physical compatibility is **not** automatic acceptance of a new binary/build record.
A full `run_e2` build also rebuilds the production programs, whose bytes legitimately
change with this correction and are bound by the old build manifest. Therefore a
new full build cannot be substituted into the old recovery plan without satisfying
its provenance transition. This task compiled affected production variants only to
`/tmp`; installed plan-bound executables were preserved and still match their digests.
No recovery, GPU calculation, new E2 preparation or authorization was performed.
