# CPU-only reproduction and evidence layout

From repository root, on the authenticated host workspace:

```bash
cd /home/jramirez/UAMMD_KG
timeout 600 python3 examples/KG_Assoc/reviews/production_gpu_compatibility_closure_20261023/VERIFY.txt
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/production_gpu_compatibility_closure_20261023/TEST_REVIEW.txt
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/TEST_ADAPTER.txt
timeout 600 env PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/production_launch_validation_20261023/TEST_SOURCE_BOUNDARIES.txt
out=$(mktemp -d /tmp/kg_compatibility_closure.XXXXXXXX)
timeout 600 python3 examples/KG_Assoc/reviews/production_gpu_compatibility_closure_20261023/REVALIDATE.txt --output "$out/replay"
timeout 600 python3 examples/KG_Assoc/reviews/production_gpu_compatibility_closure_20261023/SOURCE_REVIEW.txt --output "$out/source"
timeout 600 python3 examples/KG_Assoc/reviews/production_gpu_compatibility_closure_20261023/LOG_AUDIT.txt --output "$out/native_logs.log"
timeout 600 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/kg_closure_matplotlib python3 examples/KG_Assoc/reviews/production_gpu_compatibility_closure_20261023/PLOT.txt --input "$out/replay" --output "$out/plots"
```

No command executes a GPU executable or any MD step. REVALIDATE and VERIFY permit
only Git subprocesses; the other review tools only read existing data, hash files
or plot saved observables. No invocation of the old driver's --execute/--recover
entry point is needed. Formal records are authenticated by immutable bindings/use/
triplet/evidence checks, without re-running the registrar's native CPU build probes. Keep Git clean for the existing strict source gates.
Use fresh output paths: review tools reject reused destinations and do not change
simulation journals or completion status. CPU jobs are timeout-bounded at600s.

The revalidation directly calls the existing numerical validator rather than the
adapter's validate/status completion shortcut. It authenticates status/receipts and
then recomputes endpoint/event/thermo/stress checks, requiring the full result object
to equal the immutable original. Results in replay/ are new review artifacts, not
replacement completion receipts. Native final velocities are additionally checked
for presence and finiteness; they are not compared to initial velocities after
integration. The P4 reader recomputes the same established six-channel G, with no
new estimator or raw stress output. Signed curves use their actual lag/count grid.

SOURCE_REVIEW compares actual shared source/build hashes and duplicated code blocks,
authenticates original late E2 output hashes, reruns its exact readback decoder on
six real historical payloads, and verifies recorded oracle cadence/completion counts.
It does not reconstruct an oracle from unavailable production microtrajectories or
run new candidate comparisons on a GPU. The accepted historical comparisons remain
E2 evidence. The thirteen selected files include both common physics and the header
containing distinct stress/standard force wrappers; the latter are explicitly
not claimed to be identical functions or bitwise trajectories.

COMPLETED_OUTPUTS.sha256 is the complete240-file pre-review snapshot of the fifteen
completed short-test directories. PRESERVED.sha256 additionally protects the entire
previous corpus, source/build/qualification evidence and frozen45 production
preparations:5476 bindings. ARCHIVED_INPUTS.sha256 binds the206 exact metadata/small-
observable members of COMPLETED_EVIDENCE.tar.gz. That archive includes original
started/native-finished/validated/binding receipts, native logs, atomic completions,
thermo, stress, events, final associations and the authority/preparation chain.
Extract only into a fresh scratch tree, never over live data.

The archive intentionally does not duplicate large COM/topology/bead/final-snapshot
files or all earlier E2 payloads; their exact original hashes and preserved locations
are recorded. Full independent endpoint replay requires those original host files
(or an independently authenticated copy), not a data-free Git checkout. Archive
members and review CSVs support inspection of the actual recorded rheology/event
findings without pretending to regenerate missing microscopic data.

All code/data/plots in this new dossier are sealed by INTEGRITY.sha256, excluding
the manifest itself. Original assessments, false diagnostic capability flags,
compatibility-hold notice and all simulation journals remain unchanged. The prior
pre-launch VERIFY script correctly asserted output absence at its own publication;
it is historical preflight evidence, not the appropriate post-execution audit.
Use this closure VERIFY for the completed state.

PROPOSED_DECISION.md is a prose proposal only. It must not be copied into banks as
an approval or treated as an already issued waiver. The user must separately approve
any additional-certification policy decision and any later activation/execution.
