# CPU verification and preservation

Starting local/remote SHA: `a292d97efb12e81910908d1c06d7f6ee420fef17`.
Development used an isolated worktree; simulation inputs/results were read only.

```sh
PYTHONPATH=examples/KG_Assoc/campaign python3 -m unittest test_joint_e2 test_catalog test_e2_acceptance test_e2_recover test_run_e2 test_e2_g1 -q
```

**101 CPU tests passed.** New coverage verifies one continuous six-window history,
separate 2–4M/4–6M intervals, exactly three paired independent units, complete
transient context, non-automatic acceptance and the immutable dossier's exact
endpoint/evidence bindings. Existing restart-boundary, source/executable/parent/
seed authentication, no-overwrite, catalog, acceptance, recovery and wrapper
regressions remain successful. The previously published dilute analyzer hash is
checked against its archived publication-commit bytes rather than requiring that
a new read-only driver be identical forever; no old evidence is edited.

Python compilation and `git diff --check` pass. Existing executables were reused
only for the pre-existing host-only seed/hash/initial-state regression checks;
no native simulation source/header changed, no executable rebuild was necessary
and no GPU calculation was launched. Existing legacy validator unclosed-file
`ResourceWarning` messages remain unchanged.

Scientific evidence checks:

- Original f=6 plan SHA256 matches the user-supplied reference exactly.
- All three source histories were independently numerically revalidated, including
  full accepted-event replay, network statistics and conformations.
- Original review input/config/report hashes authenticate, along with E1 parent
  identities, approvals, completion receipts, physical parameters and RNG seeds.
- Current source/build/log/executable hashes authenticate. Exact analysis-driver
  bytes are frozen by the new configuration.
- All 24 f=6 payload hashes and all new analysis source bindings were rechecked
  after analysis. Original review and simulation records are unchanged.
- Both earlier scientific-review dossiers, the formal-acceptance dossier and all
  three existing acceptance records remain byte-identical to the starting commit.
- Real-data catalog status is `qualified_acceptance_recommended_not_registered`
  for f=6, with no formal record, missing selection and absent production
  authorization. The existing three formal acceptances remain unchanged; registry
  views and selections remain empty.

The recommendation retains small late conformation/repartitioning changes,
neighbor-loss activity change and slow-correlation uncertainty; no difference
compatible with zero is interpreted as proof of stationarity. No scientific
acceptance record, extension, registry selection or production authorization was
created. Protected `src/` and `examples/KG/` remain unchanged.
