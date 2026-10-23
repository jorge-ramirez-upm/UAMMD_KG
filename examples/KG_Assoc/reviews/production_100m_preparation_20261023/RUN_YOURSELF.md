# CPU preflight and future user-run handoff

Run from `/home/jramirez/UAMMD_KG` on `KremerGrest`. The commands below are
read-only CPU checks (except tests, which write only temporary fixtures):

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 python3 examples/KG_Assoc/reviews/production_100m_preparation_20261023/PREPARE.txt check
timeout 600 python3 examples/KG_Assoc/reviews/production_100m_preparation_20261023/PREPARE.txt status
timeout 600 python3 examples/KG_Assoc/reviews/production_100m_preparation_20261023/VERIFY.txt
```

Do not run `prepare` again: the immutable identity already exists. Existing
preparations and output directories deliberately cannot be overwritten. `check`
and `status` authenticate the sealed preparation receipt, all45 plans/approvals,
parents, streams, source map and build before reporting. They do not launch native
code, mutate status or infer validated completion from native PASS alone.

## What remains before any GPU launch

1. Separate user approval for bounded GPU compatibility validation on exact accepted
   parents; reserve distinct validation streams, authenticate an isolated output
   namespace and publish narrowly scoped validation approvals. Historical stress,
   corrected-chemistry and E2 GPU evidence is preserved, not a fresh GPU validation
   of this production build on today's45 starts. No validation streams or approvals
   are created here. Authenticate the preserved optimized100k smoke build in
   BUILD_AUTHENTICATION.log; it uses the same implementation with a100k length macro.
2. Review those bounded results and issue separate production activation/execution
   authorization bound to this exact dormant registry, plan, source map, executable,
  45 identities and100M caps. This milestone grants neither.
3. Add/test a minimal authorized-launch adapter using the existing native commands,
   output validator and registry resolver. Preserve the sealed planning `run.json`
   and approvals, use separate started/failure/completion journals, and pass the
   **same authorized source map** to immediate prelaunch and post-native validation.
   Test numerical/provenance failure stop, output reuse rejection, independently
   validated completion skip and immutable administrative recovery. Activation alone
   is not sufficient: the legacy launcher/verify/status mutate run.json and must not
   be used directly on these preparations.

`HISTORIES.csv` and the sealed plan contain the exact **eventual**100M native argv
for every history. `COMMANDS_PENDING.txt` contains shell-quoted versions. They are
planning artifacts, **not approved launch commands**. No unrestricted `--execute`
entry point is supplied in this CPU-only milestone. A tested executable production
launch command will be supplied with the subsequent authorization/adapter milestone;
providing one now would bypass the registry and execution gates.

For future bounded validation, the command construction is precisely:

    [authenticated preserved kg_assoc_campaign_production_smoke]
    + prepared production argv[1:], replacing only --output with a fresh isolated
      validation prefix and --seed with a separately reserved validation seed.

Do not use any of the45 production seeds or production output directories for that
validation. The native front end itself does not enforce administrative approvals;
therefore call it only through the future approved validation launcher. This is a
specific pending workflow, not a claim that smoke tests were executed here.

## Interruption and completion policy for the future launcher

Run one uninterrupted native100M process per history. A correlator checkpoint is
not a simulation checkpoint. On Ctrl-C/termination preserve outputs, logs, plans,
seeds and execution journals. A genuine partial trajectory remains held; rerunning
needs a new immutable attempt, new streams and explicit replacement authorization.
Never overwrite it, append to it, split100M or stitch its G into another run.
Never automatically retry a numerical/provenance failure. Record abandoned work
separately from the4.5B completed-trajectory budget.

Native completion followed by a CPU administrative exception is not a partial MD
retry. Authenticate the native logs/receipt first; the preparation helper's CPU-only
`validate-completed --system SID --replica N` can publish a distinct immutable
validation-recovery receipt **only after** future execution authorization, active
registry, started evidence and every independent output check pass. Original
`incomplete.json` is preserved byte-for-byte. Repetition is idempotent. A validated
receipt is reauthenticated by `status`; source/output changes fail closed.

No production GPU job, execution approval or registry activation has occurred here.
