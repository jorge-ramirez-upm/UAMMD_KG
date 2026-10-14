# Exact proposed 6M endpoint bindings

These are scientific-review candidates only. No formal acceptance or production permission is created.

System: `F04_N010_RP040_EE08_EA04`. Absolute step: **6,000,000** for every endpoint.

Plan SHA256: `5884973e9a8db39cf40fbb5e0e4298a65b41c517e76db1b60f0552cfbdb79b50`.

Prepared/build commit: `bb7d72acbcadfaef5a09333b27439de763597b93`.

Attempt: `examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP040_EE08/equilibrate_704163de5b044a3f8293eedd2e1c5304/`.

| Replica | E1 seed | Chemistry seed | Requested MD seed | Effective MD seed | Events / frames |
|---|---:|---:|---:|---:|---:|
| r001 | 12001 | 420201 | 520094 | 3213336292 | 197626 / 6001 |
| r002 | 12002 | 420202 | 520095 | 3204968164 | 198337 / 6001 |
| r003 | 12003 | 420203 | 520096 | 3095213768 | 198306 / 6001 |

## r001/state

E1 snapshot: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e1/F04_N010_RP040/r001/state.e1.lammpsdat`.

E1 snapshot SHA256: `4ce13546d99236211940e3a5fc74b21e05d856397be2b63b8bd9555911783846`.

Restart SHA256: `7bc651d906e354269af8f471854f6c7384473fad605dd670889ea238bbb84e60`.

Chemical sidecar SHA256: `4179e769e0ccbb58d4161010b255327f0690197e393a68977470fd43c75c3a36`.

## r002/state

E1 snapshot: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e1/F04_N010_RP040/r002/state.e1.lammpsdat`.

E1 snapshot SHA256: `e4ade1bbb30ad968f53aad774836204929fcb445951dd2c90bb3b2b2d16749a9`.

Restart SHA256: `0484cbfd05ec537542dcece768f8748adb46b4c88e6884bd5ce9d1a473f17d78`.

Chemical sidecar SHA256: `7864fccf06521b636c211985da9b70e149cda773ca9ceac38d4dbf9cd6e0e3a2`.

## r003/state

E1 snapshot: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e1/F04_N010_RP040/r003/state.e1.lammpsdat`.

E1 snapshot SHA256: `c965e8b18e8c1c98a2e82ed61a3b7c14b0bbb0ae9b363416dbed950dce6f2038`.

Restart SHA256: `ea8abfce5585ed526e405e29b525ed2af3ad77db5424f72beadb32429103d1dc`.

Chemical sidecar SHA256: `cd64cdb6651a7bad9b13b76a2f808d94d2d192b7176bf24201e156c395f80ae5`.

All eight endpoint/history payload hashes, receipt hashes, source/build bindings and validators are retained in [provenance.json](evidence/provenance.json). Seeds and endpoint identities were checked against the frozen E1 inventory, seed map, plan commands, MD-stream logs and chemical sidecars. These are fresh 0–6M histories, not the earlier stopped attempt, smoke states or intermediate checkpoints.
