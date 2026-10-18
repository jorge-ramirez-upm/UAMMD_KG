# Scoped continuation implementation

This milestone prepares user-run extensions only. Codex runs CPU checks/builds
with 600-second limits and launches no GPU calculations. AUTHORIZATION.md is the
immutable scope and restart-overhead clarification. RUN_YOURSELF.md supplies
commands; BUILD_RESULTS.md and VALIDATION.md record the completed checks.

## Exact continuation contract

Ea8 r001–r003: absolute 24M→40M, +16M each, 32 scientific 500k windows.
Ea10 r001–r003: absolute 24M→56M, +32M each, 64 scientific 500k windows.
There are exactly six completed extension slots, totaling 144M steps. No new
Ea6/Ea4 trajectory or later extension can be selected. Fine numerical/conformation
records remain every 1000 steps and chemistry/oracle records every 100 steps.

`kg_assoc_e2_extension.py` authenticates the exact joint-review 24M endpoint table,
complete predecessor plans, accepted reference ancestry, all parent outputs and
receipts. New plans use `Ea_24M_extension_v1` and bind immediate parent hashes,
original family/branch, counter offsets, source/build identity and a fresh MD-only
reservation. Every planned source/parent/command/seed is reconstructed and checked.
The same-Ea chemistry seed and absolute-step counter keys are inherited unchanged.
No chemical RNG is allocated or reseeded.

Fresh requested and effective GJ streams are reserved immutably under
`banks/e2_md_reservations/`. Allocation excludes all prior requested/effective
streams, reserved policies, discarded attempts and actual recorded histories.
Existing transfer/ordinary allocators also see these unused reservations. Original
transfer stream ownership recognizes authenticated same-condition descendants.
These are still the original three paired families, not six independent original
preparations. GJ restarts its internal noise step at zero: no bitwise MD
continuation, segment-crossing IAT/SEM or unqualified full lifetime stitching.

## Validation-only native support

The existing candidate diagnostic executable gains `--e2-extension`. Its front-end
accepts only Ea8 +16M or Ea10 +32M from a 24M parent with the exact manual family
chemistry seed, frozen parent parameters and a matching branch suffix. It forbids
chemistry reseeding, Ea switching, physical overrides and force/overwrite. The
ordinary executable rejects this extension flag. All original ordinary/derived
paths retain their original simulation semantics.

The change adds guarded metadata and diagnostic duration support. The actual
physical restart restoration, expected-float32 materialization repair, DeviceData
initialization, force kernels, reaction probabilities, production candidate search,
integrator, timestep, temperature and random-number implementation are unchanged.
The diagnostic build still performs exact initial device readback before MD and
the corrected independent oracle at every reaction sweep. Python validation forces
oracle/readback checks for either extension duration even if a caller passes
`oracle=False`.

VALIDATION_TRANSITIONS.log contains the exact reversible changes to three existing
scientific-source files: the native validation front-end, validator lineage/forced
oracle dispatch, and administrative seed-ownership/MD-reservation accounting.
The planner pins that file's SHA256 and both before/after digests. Reversing only
those exact edits must reproduce the authenticated parent source hashes; every
other scientific source must match byte-for-byte. The two new administrative
modules are separately bound by the committed plan and native build manifest.
A physics/header/force/search/integrator change cannot inherit GPU evidence.

The same-Ea 24M parent provides authenticated existing GPU evidence for this
unchanged physical restart path. Before each selected GPU launch the standard
validator independently replays that immediate parent's full 16M segment and
checks equality with its completion receipt. This explicit continuation evidence
gate replaces neither diagnostics nor a failed smoke with host-only results. The
new administrative flag has not been GPU-tested by Codex; its first real device
readback/oracle execution occurs only when the user starts an extension. Any
failure stops the campaign and preserves evidence.

## Approval and execution lifecycle

Each immutable triplet plan has separate plan-bound per-replica approvals with
purpose `e2_derived_extension`, scope `Ea_transfer_24M_extensions_v1`, exact system,
selected replica, 24M start, 40M/56M endpoint, exact per-history/aggregate cap and
500k partition. A missing selector cannot implicitly launch a triplet. Omitted
replica directories are untouched. Existing ordinary E2 gates are retained.
Execution is restricted to titan and clean, committed, authenticated sources.
Documentation-only descendant commits may reuse a plan only when its complete
source map is identical and source history is ancestral; every executable and
build log hash is checked. Changes to physical or administrative source invalidate
that prepared source map.

`run_ea_extensions.py --prepare` creates the six CPU-only preparations.
`--check` and `--status` do not mutate plans, reservations, state or outputs.
Only `--execute` invokes MD. It holds the established global workflow lock,
skips independently replayed completions and recovers a finished trajectory's
missing receipt without repeating MD. A partial without an integrator checkpoint
is retired and retried from its exact 24M parent with fresh MD in a new immutable
attempt; reservations and output bytes are never reclaimed or overwritten.

The user explicitly authorized recorded restart overhead. Partial execution has a
flushed-step lower bound and a conservative per-attempt upper bound, never an
invented exact count. Partial and successful event streams are separate, including
any repeated chemical absolute-step keys on a fresh-MD retry. Actual completed
extensions remain capped at 144M; no automatic extra scientific trajectories are
created. Numerical, chemistry, oracle, build or provenance failures become sticky
campaign failures with no automatic retry. Scientific incompleteness never causes
a retry or further extension.

New-mode receipts publish atomically without overwriting. The existing SIGINT/
SIGTERM path terminates and waits for the native child. Linux parent-death
supervision also terminates the child if the runner is killed; birth-qualified
PID receipts detect a still-active child and prevent duplicate launches. A stale
PID belonging to a different process birth is not treated as the old trajectory.
Hard interruptions can leave immutable metadata-only allocations; they are kept
and excluded from future stream allocation. No output-folder deletion is needed.

## Intended subsequent scientific review

Retain the full 8M→24M evidence and review each new 24M-start segment separately,
with the same three original parent families paired across barriers. Use all 500k
windows, 1M/2M/4M sensitivity (plus 8M Ea10 late blocks), thirds and final-quarter
comparisons. Do not stitch IAT/SEM or lifetime origins across the GJ reseed.
Report boundary-censored survival conditional on 24M, with initial inherited
identities explicitly labelled.

Track bond/free populations, intra/inter balance and loop distributions, all
multiplicities/L1/L2, distinct degrees, giant/satellite/isolated identities and
residence/returns, conformation, accepted event/exposure rates, actual identity
coverage and unresolved autocorrelation/block sensitivity. Ea8 r002's falling
intra population and r003's high-intra/satellite regime must be inspected
individually. Ea10 requires original-edge survival, slow renewal, persistent
isolates/satellites and coherent late intra changes. Stable means or completed
step counts do not prove stationarity; low activity does not prove equilibration.
Neither system is automatically accepted at 40M/56M. Further scientific review
and separate user approval are required for either formal acceptance.
