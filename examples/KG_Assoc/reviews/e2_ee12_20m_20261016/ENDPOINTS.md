# Exact Ee12 absolute-20M endpoint dossier

System: `F04_N010_RP080_EE12_EA04`. Recommend qualified acceptance of exactly
these three 20M endpoints solely as `production_initial_state`; no formal acceptance,
registry selection or production permission is created. The historical 16M hold remains immutable.

Original attempt: `equilibrate_9be4b5a8840d48b79b2bc5f9d714f9c0` (0–16M).
Original plan SHA256: `80c888e6adb0c5738cd549fe119a6ac188cc08b621dc4554da235f4095c822bc`.
Continuation: `equilibrate_553522b9ed9b4253a6b910d817ad65f8` (16–20M).
Extension plan SHA256: `5d0045e99d2c7631a4c8d96416229c07d9e12d241a9753e8ba721f8d4071b0b9`.

Positions/velocities, chemical partners, seeds, absolute steps and cumulative
creation/break counters continue through 16M. A fresh GJ integrator uses
`initVelocities=false`, `internal_start_step=0` and a new MD random stream.
This is not bitwise MD continuation. No IAT, SEM or bond lifetime is stitched
across 16M. Exact boundary partners/counters and parent bindings are in
[BOUNDARY.json](evidence/BOUNDARY.json).

## r001

20M prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE12/equilibrate_553522b9ed9b4253a6b910d817ad65f8/r001/state`.
16M parent prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE12/equilibrate_9be4b5a8840d48b79b2bc5f9d714f9c0/r001/state`.
E1 snapshot: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e1/F04_N010_RP080/r001/state.e1.lammpsdat`.
E1 snapshot SHA256: `7e6465c8859b565efcc6146b34a643339f9870b438115821c7dc99fe3b02f5fc`.
Chemical seed: `420801`; old/new requested MD seeds: `520124/520130`.
Old/new effective MD seeds: `2927754924/3381585552`.
Preserved 16M counters: creations `10400`, breaks `8424`.

| Step and payload | SHA256 |
|---|---|
| 16M `state.restart.lammpsdat` | `f734ab9550d55c8d7d22ab3fbe1bdbc5aa08e5e119447b34150a4fc9b04c1748` |
| 16M `state.assoc_restart` | `cf860ceef727007fbdcaec4087781bb763441bd2e6990327ac02ec9cde571f8e` |
| 20M `state.assoc_restart` | `97540362878cd52537b6b7c816779682885e6528f4add7be09079ee61e2be34a` |
| 20M `state.conformation.tsv` | `d72d1ec71741e8b951625f115d709b0718df4c3100ac1e630784d3f5a80f4885` |
| 20M `state.events` | `3258484c8ebda8e5e1ae40363c486436500202e18053922bc894c9cb8d9b8c92` |
| 20M `state.final_associations` | `cd411d52995d31d66c3982091204eac6f644f633f803d0996ad0074a59c39a06` |
| 20M `state.final_permanent.lammpsdat` | `df6b688ec0d017a3b9c9ec1c958c30f7746ab3a01334ffa4666a39b538c2d5aa` |
| 20M `state.numerics.tsv` | `b0de98659cb1d59c51e78d1ba9a2ecbe3ba7bc75e3ef580eb3ee24d6b7a1b40a` |
| 20M `state.restart.lammpsdat` | `1771071181cdd88a72e882bf7449e728881c990231a4a9be84578a7f56a1d3a2` |
| 20M `state.state` | `ba43e864224f31cb1d0b86647019a340a24bc8f5ff1786051c9a2fcb32e4407b` |

20M completion receipt SHA256: `a98610b41add2d144a52ecf3252f7795863b33e523b23a31fc786b9689e2d0dd`.
Fresh continuation validation: 4,001 frames, 4,069 accepted events, 1,971 final bonds; numerical status `valid`.

## r002

20M prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE12/equilibrate_553522b9ed9b4253a6b910d817ad65f8/r002/state`.
16M parent prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE12/equilibrate_9be4b5a8840d48b79b2bc5f9d714f9c0/r002/state`.
E1 snapshot: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e1/F04_N010_RP080/r002/state.e1.lammpsdat`.
E1 snapshot SHA256: `2a10ef9abe6de2f46d3167c5926beb6e1ea4ab85e933a797c08d2e54ee9b4c2a`.
Chemical seed: `420802`; old/new requested MD seeds: `520125/520131`.
Old/new effective MD seeds: `2919386796/3373217424`.
Preserved 16M counters: creations `10191`, breaks `8219`.

| Step and payload | SHA256 |
|---|---|
| 16M `state.restart.lammpsdat` | `f28379dc6116d7390b138198cf34629012a9705b93dae453f970d2d090634ff5` |
| 16M `state.assoc_restart` | `9d064e4e09d76fa0c3a447d19b925e11fc6535cf7f21f90ce7f2a8a06727f915` |
| 20M `state.assoc_restart` | `4ad3eb1977b69c3798546e942c290e9635f3b339a01b76ef08e967ef55bc1ec8` |
| 20M `state.conformation.tsv` | `c79c82acc0fe4852283c92fbd45f9e87ba8f43901e54d09be47592c0e18d92fd` |
| 20M `state.events` | `1fad007a7421177f24b7017a55847206fd6a75ed89c406e9653b9dee3065728e` |
| 20M `state.final_associations` | `b805b2500967ef8de95777bca8f295173f756089acf99141f4dc5bbea9f2a4d5` |
| 20M `state.final_permanent.lammpsdat` | `22003133f5487b0cdeab6e36c116d2b033d92cfa7957dc2593ce4362bc0b0333` |
| 20M `state.numerics.tsv` | `84f0bc158939dd502b851cdc246df8053ecaca1d323ede6b36611ef75603a62d` |
| 20M `state.restart.lammpsdat` | `41fe6b3a1ae4aa639424fff0e2c8b304c21a53645ce0f66fdee3e66199a96d00` |
| 20M `state.state` | `98e33a696c02078931f4d6667f89bbb311a3305f04f87835301b3a5d551a6130` |

20M completion receipt SHA256: `096b8968793d278194442e2e3d2a4b07258b16d1a490b4cb3f4741486378067f`.
Fresh continuation validation: 4,001 frames, 4,182 accepted events, 1,962 final bonds; numerical status `valid`.

## r003

20M prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE12/equilibrate_553522b9ed9b4253a6b910d817ad65f8/r003/state`.
16M parent prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE12/equilibrate_9be4b5a8840d48b79b2bc5f9d714f9c0/r003/state`.
E1 snapshot: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e1/F04_N010_RP080/r003/state.e1.lammpsdat`.
E1 snapshot SHA256: `ce4b32b716df594d351e9e24222d4b76a2966f153cb70d05e0b7d9cea1389296`.
Chemical seed: `420803`; old/new requested MD seeds: `520126/520132`.
Old/new effective MD seeds: `2944507564/3398338192`.
Preserved 16M counters: creations `10409`, breaks `8441`.

| Step and payload | SHA256 |
|---|---|
| 16M `state.restart.lammpsdat` | `7a0b50ff4b66ec7dd0af525a202a9419303479e4ec0504f33fc801e962b2c93a` |
| 16M `state.assoc_restart` | `08ddb56006ae80aba11e03c9dece239025ee3a77ea15fdc4c726f159cce70a91` |
| 20M `state.assoc_restart` | `40564a3d8eac898b6a518e551230198ae876bfe58acbfe8cf4679c15702cb06a` |
| 20M `state.conformation.tsv` | `1a9505d2ac500799c9dad12d7924b838669e09c1cc4716844051cfcf24bcbf17` |
| 20M `state.events` | `1209ec8a8738c9b06607710a162e12b956baadac81fb9c47318440887f58e8cd` |
| 20M `state.final_associations` | `30feb080016c37b6857412c3ebb20684ade81856d92879da9640ca8c922ab4eb` |
| 20M `state.final_permanent.lammpsdat` | `e46e1a3c86e2a510e0637d5aefd079609360053d61eab566fe4a00832ab63dd7` |
| 20M `state.numerics.tsv` | `04970961023ba9062f4eab6868dc5290beed0775c3dc32fda5f8230c1f8ebc14` |
| 20M `state.restart.lammpsdat` | `2db8093ea2009332e218469ca66d17117f8d052e96390ee3c07ca15c5bd7266b` |
| 20M `state.state` | `b679d1a0d0daf839518971ab7a8c35654fd8e2f74a8690625b5641a044f04b5b` |

20M completion receipt SHA256: `b5eef103bb3c89c09871d570b784ec2da4f713e7fc6f159575a8164683aae4b3`.
Fresh continuation validation: 4,001 frames, 4,100 accepted events, 1,976 final bonds; numerical status `valid`.

## 0–16M build provenance

Build Git SHA: `81fe5de9cd5ded849202eebab7c14e6bd35fb9ae`.
Recorded `kg_assoc_stars` SHA256: `b119a3c6d158d9ede7319a0baa0de5b4797e400813225b9c5e8c8cfdb8ed5fb4`.
Authentication scope: `historical_build_and_source_authenticated; binary_bytes_not_reauthenticated`.
Forced build command: `make -B -j2 kg_assoc_stars kg_assoc_stars_candidate_smoke kg_assoc_candidates_test kg_assoc_production kg_assoc_campaign_production kg_assoc_campaign_production_smoke`.

## 16–20M build provenance

Build Git SHA: `c1e0b5d472dbf0c5e09274f8079cd92a92d7d3dd`.
Recorded `kg_assoc_stars` SHA256: `6de8969eb85bf80d84c2bd64d59f088b1d533982f8d07e731958edcddafd638c`.
Authentication scope: `current_binary_hashes_authenticated`.
Forced build command: `make -B -j2 kg_assoc_stars kg_assoc_stars_candidate_smoke kg_assoc_candidates_test kg_assoc_production kg_assoc_campaign_production kg_assoc_campaign_production_smoke`.

The original six executable files were replaced before this review by the
continuation rebuild. Original source/build logs, recorded executable digests,
plans/outputs and the integrity-bound 16M review authenticate; original binary
bytes are not independently reauthenticated now. Current extension executable
bytes authenticate. Historical E1 executable bytes remain similarly limited.
Available E1 snapshots, commands, diagnostics and active lineage authenticate.
All replacements predate this CPU-only review; no executable ran here.

Full plans, seeds, output/receipt identities and fresh validation are in
[provenance.json](evidence/provenance.json); execution witnesses and pre-task
binary replacements are in [AUTHENTICATION.json](AUTHENTICATION.json).
The scientific recommendation and qualifications are in [ASSESSMENT.md](ASSESSMENT.md).
