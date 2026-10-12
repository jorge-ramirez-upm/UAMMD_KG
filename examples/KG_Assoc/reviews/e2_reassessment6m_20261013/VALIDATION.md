# Validation of the read-only 6M reassessment

Starting SHA: `30a8e7e415e07bfd69975cfb518e23157f791bd4` (local and remote
`KremerGrest` verified before development). Development used an isolated worktree.

CPU regression command:

```sh
PYTHONPATH=examples/KG_Assoc/campaign python3 -m unittest test_joint_e2 test_catalog test_e2_recover test_run_e2 test_e2_g1 -q
```

**92 tests passed.** Coverage includes six-window/long-window bookkeeping,
three-history paired uncertainty, transient exclusion, restart seed/parent/count
mismatches, immutable authenticated prior estimates, current-executable tampering,
historic review-driver identity, report no-overwrite, endpoint/evidence binding,
explicit documented supersession, retention of a hold on invalid bindings,
schema-two review metadata and separation from formal acceptance/production.
The existing recovery, wrapper and generalized-runner CPU regressions also pass.

The isolated worktree initially lacked ignored executables required by four
existing host-only tests. Existing primary-checkout binaries were reused through
ignored symlinks; the tests perform hash checks, MD-seed queries and host-only
initial-state validation, not GPU trajectories. No rebuild was needed because
no CUDA/header/native simulation source changed. Existing legacy validator
`ResourceWarning` messages about unclosed input files remain unchanged.

Additional checks:

- Full numerical, event replay, network and conformation validation of all nine
  replica segments, with both restart boundaries authenticated.
- SHA256 recheck of all 72 validated output payloads, all bound plan/approval/
  completion sources, and the existing 6M review metadata/reports.
- All prior 4M dossier evidence and decision remain byte-identical to the starting
  Git commit, with their original hashes intact.
- Real-data catalog scan reports the dilute system's new recommendation, retains
  the old documented hold as superseded, reports initialization selection missing
  and production authorization absent.
- Python compilation and `git diff --check` pass.

No original simulation record, restart or provenance was modified. No formal
acceptance record, active registry or production authorization was created.
Protected `src/` and `examples/KG/` and all native simulation code are unchanged.
No GPU, equilibration extension or production calculation was launched.
