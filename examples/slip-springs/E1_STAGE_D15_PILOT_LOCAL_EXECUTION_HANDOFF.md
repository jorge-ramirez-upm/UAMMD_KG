# D1.5 — local T=1 pilot handoff

The user reports that the authenticated four-cell T=.1 benchmark was reviewed
and approves the **previously frozen T=1 pilot**, subject to fresh local readiness
and independent pilot-specific approval records. This supersedes the earlier
T=1 prohibition only for this four-cell scope. T=100 and M>256 remain unapproved.
This handoff was prepared without running tests, builds, preflights, simulations
or analyses. Its new checks await user execution; no local readiness pass is claimed.

Starting preparation commit: `b780c1cff1e21482336fd6ae84db36759bbaa092`.
Scientific source remains `0dea651b58171a72206774bcebb2f4c74960069b`.
Pilot manifest SHA256:
`05f7f06141899d139b9e3fda3f740c92b0fe2b6894b280434ffe48b04c643c69`.
The [frozen preparation](E1_STAGE_D15_LARGER_SYSTEM_PREPARATION_V1.md), manifests,
source, RNG, observer, D0 tolerances and historical evidence are unchanged.

| Cell | M | N | Z | kappa | dt | T | Steps | Seed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 256 | 32 | 2048 | 0 | .0001 | 1 | 10000 | 721520101 |
| 2 | 256 | 32 | 2048 | 0 | .00025 | 1 | 4000 | 721520201 |
| 3 | 256 | 32 | 2048 | 10 | .0001 | 1 | 10000 | 721520301 |
| 4 | 256 | 32 | 2048 | 10 | .00025 | 1 | 4000 | 721520401 |

The executable commands and schedules come directly from the immutable pilot
manifest: Ne=4, A2=5, nu_hop=100, kb=30, kBT=zeta=1, exact E1 initialization,
renewal on, stress off, double precision. Scalar times are 0,.5,1; the seven full
E1 observations and four state audits per run retain their exact frozen steps.
No override, extra trajectory, automatic retry or resume is supplied.

## Stage A — Pilot readiness

**Run locally. No pilot trajectory is started.** Use the clean `slip-springs`
development checkout; leave the main checkout's unrelated KG changes alone.
Requirements remain Python 3.10+/NumPy, configured noninteractive GitHub access,
CUDA13 at `/usr/local/cuda`, `/usr/bin/g++`, and the accepted sm86 RTX3060Ti UUID
`GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274`. No dependencies are installed.

The existing result archive listed below has a recorded checksum alongside it.
**Confirm it is the archive covered by your completed benchmark review.** If
your reviewed archive differs, substitute its absolute path and independently
recorded SHA256; do not simply calculate a new digest to bypass a mismatch.
The review-reference argument explicitly records your already-made benchmark/
resource/observation-suitability decision; it is not an automated scientific review.

```bash
python3 /tmp/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d15_local.py pilot-readiness \
  --evidence-parent /home/jramirez/UAMMD_KG-evidence/d15 \
  --cuda-home /usr/local/cuda \
  --benchmark-return /home/jramirez/UAMMD_KG-evidence/d15/readiness-35puhn4y/returns/benchmark-return-acsjsnxb.tar.gz \
  --benchmark-return-sha256 4446bc2ac99fb13acdc1506037c44c46dd6f141d97582d105c064445c2d268d5 \
  --benchmark-review-reference 'User review: authenticated M256 T=0.1 benchmark accepted; frozen T=1 pilot suitability approved'
```

This command, bounded at each delegated step, performs:

1. Git origin/clean-branch/revision/remote checks and fresh durable preparation
   and pinned-scientific-source worktrees. No existing evidence is overwritten.
2. Verification of the reviewed return archive's external SHA, member checksums,
   stored summary receipt and original local session/launch/completion identities.
   No archive is extracted. The entire benchmark is then reauthenticated using
   the frozen host's `summarize` command (600-second bound), including its prior
   approval/readiness review and all raw evidence. Missing/moved/changed evidence
   blocks readiness; a compact archive alone cannot replace the local cohort.
3. Creation of `benchmark-review.json`, bound to this exact pilot manifest and
   the authenticated benchmark approval/completion identities, plus
   `benchmark-review-source.json` recording your review reference and archive
   identity. Its suitability flag records your explicit prior decision only
   after authentication passes; it does not approve the new pilot readiness.
4. Pure metadata projections, byte comparison, CPU tests (120 seconds each),
   fresh pilot-manifest-bound double build (480-second outer bound), existing
   two nine-step technical GPU fixtures (120 seconds), and read-only pilot
   preflight (180 seconds). These use the existing host and tests, not a new
   scientific runner. The new offline `test_e1_d15_pilot_local.py` joins the
   benchmark handoff's existing CPU regression list.
5. Verification that the preflight's only blocker is missing independent
   approval, and that live free disk/GPU/host resources meet the approved minima.
   Exit code 0 alone is insufficient. The execution runner checks live identities
   and budgets again immediately before and during the actual pilot.
6. Collection of proofs, `readiness.json`, false readiness/approval drafts on
   success, and an automatically generated compact readiness archive, including
   ordinary failure evidence. Failures stop immediately; no stages retry.

The script prints `D15_ROOT=/home/jramirez/UAMMD_KG-evidence/d15/pilot-readiness-...`.
Copy that **one actual path** for subsequent commands:

```bash
export D15_ROOT=/home/jramirez/UAMMD_KG-evidence/d15/pilot-readiness-REPLACE_WITH_PRINTED_SUFFIX
```

Upload the printed matching pair:

```text
$D15_ROOT/returns/pilot-readiness-return-<unique>.tar.gz
$D15_ROOT/returns/pilot-readiness-return-<unique>.tar.gz.sha256
```

They include the benchmark review/authentication provenance, CPU/tiny-GPU logs,
full pilot build receipt and binary hash, full preflight JSON/environment identity,
approved resource values, preparation commit/script identities, errors/blockers,
`SUMMARY.txt`, `contents.json` and `SHA256SUMS`. No executable or raw CSV history
is bundled. Logs over 64 KiB are labeled excerpts with full local hashes; JSON
receipts remain complete. The uncompressed packet is capped at 8 MiB.

**Packaging only; no tests/build/probe/simulation:**

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" package \
  --root "$D15_ROOT" --kind pilot-readiness
```

This creates another fresh packet, preserving originals. If readiness failed
before `preparation/` existed, use the original entry-script path for packaging.
Keep both durable worktrees, the main Git common directory, prior benchmark,
review records and all full evidence at their original absolute paths.

## Stage B — Pilot execution

**Stop after Stage A and obtain independent review of its actual evidence.**
Your pilot-scope authorization does not waive live readiness or its signed-off
records. No helper creates a true execution approval.

On readiness success, all paths/hashes and these approved limits are prefilled
in `pilot-approval.DRAFT.json`:

| Limit | Value |
|---|---:|
| Per-run / aggregate wall time | 120 / 3600 seconds |
| Per-run / aggregate output | 128 MiB / 1 GiB |
| Maximum child host RSS | 2 GiB |
| Minimum available host RAM | 8 GiB |
| Minimum free GPU memory / disk | 4 GiB / 10 GiB |

Limits can be tightened, never enlarged; minimum headroom can be raised, never
reduced. The draft's benchmark-review pointer is already collected automatically.
Do not replace it with a benchmark execution approval or a different review.

Only the human decision fields require editing:

1. After review, make a **fresh external copy** of `readiness-review.DRAFT.json`.
   Preserve its complete artifact map. Set `review_reference` to the independent
   pilot-readiness review reference and `all_local_preparation_checks_reviewed`
   to true only after the actual evidence passes review. Do not edit the original.
2. Collect its path/SHA automatically into a still-false approval draft:

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" approval-draft \
  --root "$D15_ROOT" --review /absolute/path/to/reviewed-pilot-readiness.json
```

3. Make a **fresh external copy** of `pilot-approval.LINKED-DRAFT.json`. Set only
   the independent `approval_reference` and, after explicit sign-off,
   `execution_authorized=true`. Preserve the pilot manifest/build/environment,
   both review pointers, output root and approved budgets. Record the exact
   approved file's SHA256 independently for the command below. No dozens of
   digests or artifact paths need to be copied or edited. Keep approved records
   and referenced artifacts permanently at their recorded paths.

**Actual pilot execution, only after these records are complete:**

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" pilot \
  --root "$D15_ROOT" \
  --approval /absolute/path/to/approved-pilot-execution.json \
  --approval-sha256 REPLACE_WITH_INDEPENDENTLY_RECORDED_APPROVED_FILE_SHA256 \
  --execute-reviewed-pilot
```

This delegates exactly the four frozen independent T=1 runs sequentially to the
existing D1.5 host. It enforces pilot-specific readiness/build/manifest identities,
the benchmark review, external approval SHA, approved ceilings, live GPU identity,
headroom, fresh output root, bounded supervision, per-run and whole-cohort
authentication. Benchmark approvals/build receipts cannot authorize it.
The outer watchdog allows the approved aggregate budget plus 600 seconds for
preflight/authentication/cleanup; it does not enlarge the inner simulation budget.
Output is `$D15_ROOT/pilot-campaign/`. A launch record prevents reuse after failure;
do not remove it, rerun with a fresh root, change seeds or resume partial evidence.
Stop and return failed evidence for review instead.

## Stage C — Results

**Authenticate and summarize existing data only; no new trajectory:**

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" summarize \
  --root "$D15_ROOT"
```

The root's recorded campaign kind selects the pilot automatically. The frozen
host reauthenticates all four runs and the prior benchmark/reviews using the
captured external approval and successful completion identities (600-second
bound). It writes a fresh performance summary, then packages:

```text
$D15_ROOT/returns/pilot-return-<unique>.tar.gz
$D15_ROOT/returns/pilot-return-<unique>.tar.gz.sha256
```

Send that matching pair to ChatGPT. It contains individual integration/production
ns/bead/step, wall/init/final-output and observer/transfer timings, event counts/
rates, output bytes, RSS/headroom, run/approval/completion identities, prior-review
provenance and references/hashes for full local evidence. GPU peak memory is
unmeasured; free-memory snapshots are not peaks. Nested timers are not additive.
No equilibrium/timestep/ergodicity acceptance follows from this performance report.

**Package an existing summary or failed/incomplete evidence only:**

```bash
python3 "$D15_ROOT/preparation/examples/slip-springs/e1_d15_local.py" package \
  --root "$D15_ROOT" --kind pilot
```

Packaging verifies saved summary/anchor byte identities, not the entire raw
cohort again. Incomplete evidence is explicitly labeled; use `summarize` for
fresh full authentication. Archives contain no raw trajectories or executables;
retain those locally. Checksums provide byte identity, not an independent
signature. A failed gate requires review, never automatic retry or looser limits.
No T=100 or larger-system execution is prepared or authorized here.
