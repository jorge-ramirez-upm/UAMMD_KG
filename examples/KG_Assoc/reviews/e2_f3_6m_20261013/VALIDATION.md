# CPU verification and immutable evidence

Starting local/remote `KremerGrest` SHA:
`5640a03b22a72f6be009538dca565a2a343e66ed`. An isolated development worktree was used.

```sh
PYTHONPATH=examples/KG_Assoc/campaign:examples/KG_Assoc/analysis python3 -m unittest test_e2_peripheral_network test_e2_window_sensitivity test_joint_e2 test_catalog test_e2_acceptance test_e2_recover test_run_e2 test_e2_g1 -q
```

**110 CPU tests passed.** New deterministic coverage verifies three-history
pairing, overlapping-window interpretation, duration weighting, transient
exclusion, exact tiling and restart-boundary rejection, validated graph replay
without row mutation, correct distinct-neighbor histograms, covariance-preserving
satellite accounting, source/window mismatch rejection, immutable dossier hashes,
endpoint identities and the documented scientific hold. Actual f=3 histogram
fractions sum to one and reproduce both independently validated degree moments.
Existing no-overwrite, authentication, approval/seed/parent, acceptance, catalog,
recovery and wrapper CPU tests remain successful.

Python compilation and `git diff --check` pass. No native source/header changed,
so no executable rebuild or GPU test was required. Existing binaries were reused
only for pre-existing host seed/hash/initial-state fixture checks. Existing legacy
validator unclosed-file `ResourceWarning` messages remain unchanged.

Scientific integrity checks:

- The source plan SHA256 equals the supplied reference exactly.
- All three original E1 parents, replica identities, seeds, approvals, completions,
  source/build/log/executable hashes and numerical/event/network/conformation
  outputs authenticate independently.
- The original checkpoint input/config/report hashes were checked; every bound
  source and all 24 f=3 output payload hashes were rechecked after analysis.
- Derived degree/peripheral statistics preserve the three original histories as
  independent units, never individual stars/frames or additional windows.
- The nonisolated giant identity used in peripheral accounting was verified at
  every retained diagnostic (absolute step >=1M).
- Accepted f=4/f=6 context source hashes authenticate; only corrected C1 6–8M
  statistics are used, with its historical qualifications retained.
- All prior scientific dossiers and four formal acceptance records remain
  byte-identical to the starting commit. No simulation or historical record was
  rewritten, moved or renamed.
- A real-data catalog scan reports f=3 `review_hold_material_drift`, no f=3 formal
  acceptance, missing active selection and absent production authorization.
  The four previous formal acceptances and empty registry/selection state remain
  unchanged.

No GPU simulation, E2 extension, extension plan or launch approval, formal
acceptance record, registry publication/selection or production preparation was
created. The proposed 6–8M checkpoint is a scientific recommendation awaiting
separate user authorization. Protected `src/`, `examples/KG/`, numerical/reaction
code and all existing simulation workflows remain unchanged.
