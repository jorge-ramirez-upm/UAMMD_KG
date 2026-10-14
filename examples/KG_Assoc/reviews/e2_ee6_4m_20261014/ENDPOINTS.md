# Exact reviewed 4M endpoints

These are proposed qualified initialization identities only. No state is selected,
registered, activated or authorized for production by this dossier.

Attempt: `examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE06/equilibrate_c6051f0ca57140819c10ae01e63036b5`.
Plan SHA256: `20eb13c5047cfce5a26646adb95839b4b575d232943b2b4bf7c37c49b0e623c6`.

| Replica | Absolute step | E1 seed | Chemistry seed | Requested MD seed | Effective MD seed |
|---|---:|---:|---:|---:|---:|
| r001 | 4000000 | 12001 | 420501 | 520082 | 3246776044 |
| r002 | 4000000 | 12002 | 420502 | 520083 | 3238407916 |
| r003 | 4000000 | 12003 | 420503 | 520084 | 3263528676 |

## r001

Prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE06/equilibrate_c6051f0ca57140819c10ae01e63036b5/r001/state`.

| Payload | SHA256 |
|---|---|
| `state.restart.lammpsdat` | `65aac47ce222735e5ace2938f4c65c853c24895af7587fd469870518ef1e3de8` |
| `state.assoc_restart` | `f88b7f7077e918da74059723b3949c65ac3e7f31c8fb5ed2f451d92f2955df4c` |
| `state.final_associations` | `31204ea646903bc6346272e1fae6a6c95a55a72fce4a5cbc3cdad02333ae414c` |
| `state.final_permanent.lammpsdat` | `2505231b084378a052b05772dde7e49dec211ef6b594ef4a6e21e746830a143e` |

## r002

Prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE06/equilibrate_c6051f0ca57140819c10ae01e63036b5/r002/state`.

| Payload | SHA256 |
|---|---|
| `state.restart.lammpsdat` | `fecca86a1b82fe281d4b3516913d8ce7c5971a6a0eb13f930c79c42c524ef08d` |
| `state.assoc_restart` | `1d8e4c6eff0ac7865a597ea636a9ec61ada31cf004aba6ffb9198fed4d854767` |
| `state.final_associations` | `0eff4734aa28f43a72f8f085b456229f785eed66a6584e19ce0c5658e958a72c` |
| `state.final_permanent.lammpsdat` | `3b213faba845ea8eb6d137af2746005934f7cc1bcb840ce40f9044bcdedb32c0` |

## r003

Prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE06/equilibrate_c6051f0ca57140819c10ae01e63036b5/r003/state`.

| Payload | SHA256 |
|---|---|
| `state.restart.lammpsdat` | `d8e7105b87c2eeedca36eb37aa57d44ac9fe0d628360db3c2d2436ff04957ae1` |
| `state.assoc_restart` | `8b9f66345c79c86870e6b07a5fdfce65033e359fee2ecde4fcc7f35925d4a7c8` |
| `state.final_associations` | `80f1913a03964fff3759d6c5b1f592e0b3369a3aa458b815eddf37eb9cd72d70` |
| `state.final_permanent.lammpsdat` | `f296cb44608fba9c285205de844ea3a66a6f531419b9415a802baec959021ba0` |

All output hashes, including state, event, numerical and conformation histories,
are retained in [provenance.json](provenance.json). The restart is the permanent
particle state; the associating sidecar is required to resume chemistry faithfully.
The three endpoints belong to the three original uninterrupted 0–4M histories.
