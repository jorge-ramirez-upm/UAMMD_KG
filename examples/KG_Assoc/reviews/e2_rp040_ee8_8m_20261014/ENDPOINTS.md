# Exact absolute-8M endpoint bindings

System: `F04_N010_RP040_EE08_EA04`. These are scientific-review candidates for qualified production initialization only; no formal acceptance or authorization is registered.

Original plan SHA256: `5884973e9a8db39cf40fbb5e0e4298a65b41c517e76db1b60f0552cfbdb79b50`.

Extension plan SHA256: `b88f2eec2bdff278393d11db52252abb1bcbb9bbdbca3edeb374d3022d10e6c4`.

Original attempt: `equilibrate_704163de5b044a3f8293eedd2e1c5304` (0–6M).

Extension attempt: `examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP040_EE08/equilibrate_ea8bd8e305aa4edfa9871dc977213948/` (6–8M).

Only the following three `r001/state`, `r002/state`, `r003/state` endpoints are proposed for any separately approved formal record. Each is at **absolute 8,000,000**; no intermediate or smoke state is proposed.

| Replica | Chemistry seed (unchanged) | 0–6M MD request / effective | 6–8M MD request / effective |
|---|---:|---:|---:|
| r001 | 420201 | 520094 / 3213336292 | 520100 / 3128719048 |
| r002 | 420202 | 520095 / 3204968164 | 520101 / 3120350920 |
| r003 | 420203 | 520096 / 3095213768 | 520102 / 3145471688 |

## r001/state

Exact prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP040_EE08/equilibrate_ea8bd8e305aa4edfa9871dc977213948/r001/state`.

6M parent restart SHA256: `7bc651d906e354269af8f471854f6c7384473fad605dd670889ea238bbb84e60`.

6M parent chemical-sidecar SHA256: `4179e769e0ccbb58d4161010b255327f0690197e393a68977470fd43c75c3a36`.

8M restart SHA256: `b9e36ec901b0bb20d742d616089eff4b8a6d170b6013227984c0a38cde52ec56`.

8M chemical-sidecar SHA256: `a3965fc8fc2187aa7ed4b0f8a9763e651205f9701bf88754f3f297b093c20602`.

## r002/state

Exact prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP040_EE08/equilibrate_ea8bd8e305aa4edfa9871dc977213948/r002/state`.

6M parent restart SHA256: `0484cbfd05ec537542dcece768f8748adb46b4c88e6884bd5ce9d1a473f17d78`.

6M parent chemical-sidecar SHA256: `7864fccf06521b636c211985da9b70e149cda773ca9ceac38d4dbf9cd6e0e3a2`.

8M restart SHA256: `4a3fac2b911f752e3019945c277bc9fffd4c5f1a6cacf1076b4afff00100996c`.

8M chemical-sidecar SHA256: `347164e17689277872fba48a42be6bc24141ae4f4f8675da40d1a247b2ef5b27`.

## r003/state

Exact prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP040_EE08/equilibrate_ea8bd8e305aa4edfa9871dc977213948/r003/state`.

6M parent restart SHA256: `ea8abfce5585ed526e405e29b525ed2af3ad77db5424f72beadb32429103d1dc`.

6M parent chemical-sidecar SHA256: `cd64cdb6651a7bad9b13b76a2f808d94d2d192b7176bf24201e156c395f80ae5`.

8M restart SHA256: `dacb63ef37f00469569b4fb5ea43e2a06f7152f87443ec84523c2df076d27ce1`.

8M chemical-sidecar SHA256: `52d3f941c1008c9afb609560f87b0312dcfc75d11473fb81658b96227c07921a`.

Full payload, parent, E1 lineage, plan/build/source and completion hashes are in [provenance.json](evidence/provenance.json). [AUTHENTICATION.json](AUTHENTICATION.json) adds actual MD-stream semantics, started receipts and execution-log bindings. The 6M payloads match the prior immutable ENDPOINTS.md exactly. All six source segments were numerically/event/graph/conformation revalidated; original r001/r002/r003 identities and E1 seeds 12001/12002/12003 remain fixed.
