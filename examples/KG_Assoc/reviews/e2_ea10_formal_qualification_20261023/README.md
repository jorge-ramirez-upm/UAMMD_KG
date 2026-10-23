# Ea10 formal qualification publication

The user-approved scientific exception is registered; the historical scientific uncertainty remains.

`production_initial_state` only. No registry selection/activation or GPU execution.

Acceptance path: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_acceptance/F04_N010_RP080_EE08_EA10_88M_qualified_exception_20261023_v1.json`

SHA256: `f5252413534787c9313943209892ff4052166a6ace22c77783d0d042947a1f96`

The exact immutable bytes are archived in ACCEPTANCE_RECORD.log. The publisher commit contains the reviewed administrative registrar repair; the final review commit adds this publication evidence.

| Replica | Restart SHA256 | Chemistry-sidecar SHA256 |
|---|---|---|
| r001 | `1a485e2674ec1c3a410d49a829d27ed568edc162ac3c18ea435a611d9114e125` | `d7c46966dd271ec7f8f3551cef503b98d4d109746a876b5fce9219ac01f5dfb0` |
| r002 | `e44bc438b8652fcf87414db4b0d40d588f4e3d715823d09e21bba6dd5dd32fd5` | `b867ff12e421274ba28760880deb759be50d119abc8fa5b631a6eb41923d3ed0` |
| r003 | `0c91bf29b871dae9e78d955bcdce837e6c9bacaddb91f9dab232845f5de6474b` | `e6f03ae0d399ee3aca1b8dccb0fbb6ba04501c29fdcecaa9a18b3d84b3ae52dc` |

All three 32M extensions end at88M; three independent strict CPU replays match the original validation objects, including 960000 total recorded oracle sweeps and three actual GPU initial readbacks. Native source/build/executable lineage remains authenticated; this is not new GPU execution.

Eleven focused registration tests and189 established E2 regressions pass. Prior fourteen records and historical reviews remain byte-identical. The only campaign-source change is a pinned exact-plan acceptance case in kg_assoc_e2_registry.py; no schema, physics, native/stress or numerical-validator change.

Read-only verification (repository root):

```bash
timeout 600 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea10_formal_qualification_20261023/VERIFY.txt
timeout 600 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore::ResourceWarning python3 examples/KG_Assoc/reviews/e2_ea10_formal_qualification_20261023/TEST_REGISTRATION.txt
```

To repeat one strict replay into a fresh scratch directory:

```bash
work=$(mktemp -d /tmp/ea10_registration_replay.XXXXXXXX)
timeout 600 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 examples/KG_Assoc/reviews/e2_ea10_formal_qualification_20261023/REVALIDATE.txt --replica 1 --output "$work"
```

Repeat the last command for replicas 2 and 3 as separate bounded CPU jobs. REGISTER.txt documents publication and deliberately refuses an existing acceptance: do not rerun it to overwrite evidence. No restoration or GPU action is implicit in verification. Full raw replays require the original hash-bound host data/builds. CPU_SOURCE_AUTHORIZATION.log authorizes only the exact committed administrative evolution; it grants no GPU permission.

PRESERVED.sha256 contains 4,962 unchanged historical/source/pilot bindings. It
excludes only the intentionally edited current registrar, whose starting bytes
remain in REGISTRAR_BEFORE.txt and Git at the starting SHA; REGISTRAR.patch and
CPU_SOURCE_AUTHORIZATION.log authenticate the exact administrative change. All
physics/numerical/stress sources and the fourteen prior acceptance records remain
unchanged. The prior Ea8 r001 failure/recovery is preserved as historical evidence.
