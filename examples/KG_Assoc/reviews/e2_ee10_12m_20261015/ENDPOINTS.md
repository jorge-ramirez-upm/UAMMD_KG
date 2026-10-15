# Exact Ee10 absolute-12M endpoint dossier

System: `F04_N010_RP080_EE10_EA04`. Recommendation: qualified acceptance solely
as `production_initial_state` of exactly these three 12M states. No formal
acceptance registration, selection, activation or production permission is created.

Original attempt: `equilibrate_fb8954dc860740d6b923759b2b21a703` (0–8M).
Original plan SHA256: `489af3d03ca1d54a1c42515b59961fea7fa889378410b5ddac8b835bd8f06812`.
Extension: `equilibrate_18d492ee0f4b4a7d98ca32e39ce8f95a` (8–12M).
Extension plan SHA256: `9ceb3ce52582e1e781ee36072b4018254dca0f663f58a73edb3111093322f28a`.

At 8M the restart positions/velocities, permanent identities and chemical partners,
seed and counters continue. A new GJ integrator uses a fresh MD stream with
`internal_start_step=0` and `initVelocities=false`. This is not bitwise MD continuation.

## r001

12M prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE10/equilibrate_18d492ee0f4b4a7d98ca32e39ce8f95a/r001/state`.
8M parent prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE10/equilibrate_fb8954dc860740d6b923759b2b21a703/r001/state`.
Chemical seed: `420701`; old/new requested MD seeds: `520112/520118`.
Old/new effective MD seeds: `2961194660/3011452588`.
Preserved 8M chemistry counters: creations `28025`, breaks `26093`.

| Step and payload | SHA256 |
|---|---|
| 8M `state.restart.lammpsdat` | `57bc22947e5fe82998fbcc78cc8c278209cf6222d9a5ecaf499818e0aeff5ce6` |
| 8M `state.assoc_restart` | `50fc8ea243d78555744d1141322fb431c51f2203af619f2f2e7bfb548e1708ac` |
| 12M `state.assoc_restart` | `1b01ba5479644faaa2cbebaad01139690e39278082bb116498cb2a0ab967f1ec` |
| 12M `state.conformation.tsv` | `e86d90908814fc7bbf467542c94b620929a701f9bfcc58e1513fb832ac0ba884` |
| 12M `state.events` | `ae9805c63b9218b0981e29e59e973fb09c3d209e638a3b1cf03cd23b193fec61` |
| 12M `state.final_associations` | `9d6d8ea812e4410c3684dc7d38b32e60859b790ca6781fb37cf407556eb6d40b` |
| 12M `state.final_permanent.lammpsdat` | `50f82e883f34709a6c8c38dea9b807099745a9ac94d925361434b3aa2630c8bf` |
| 12M `state.numerics.tsv` | `72773ef8ac7a54db939b31ce69973fb1177802847c78321ab0438d348fc2f3f1` |
| 12M `state.restart.lammpsdat` | `1abe47f801ef69c65d14057125ca08850782dc79bebf1232ce234daa038f3ae5` |
| 12M `state.state` | `70ce090c5dfa5f7d73d6610fb5ac60905ee250ad7391afbc069efbfbf635a821` |

12M completion receipt SHA256: `ec6cab99cbcbea8add783993c5e970eb82b9430163d015d3e02aa99c34da3349`.
Extension CPU validation: 4,001 frames, 25,674 accepted events, 1,926 final bonds; numerical status valid.

## r002

12M prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE10/equilibrate_18d492ee0f4b4a7d98ca32e39ce8f95a/r002/state`.
8M parent prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE10/equilibrate_fb8954dc860740d6b923759b2b21a703/r002/state`.
Chemical seed: `420702`; old/new requested MD seeds: `520113/520119`.
Old/new effective MD seeds: `2952826532/3003084460`.
Preserved 8M chemistry counters: creations `27875`, breaks `25957`.

| Step and payload | SHA256 |
|---|---|
| 8M `state.restart.lammpsdat` | `cab132c7c6872c4e98d67969681385f1b482dc39ccc29c1a98ac1af68829f0dd` |
| 8M `state.assoc_restart` | `ae78ee044342409fca1f7a6cbf0d906aaca2d789230387ed749c5f7e0c6d5b01` |
| 12M `state.assoc_restart` | `e89e39b6734a65bd126de368df1a58bac255dbef1ae4153cb02068585a2ac2d8` |
| 12M `state.conformation.tsv` | `0008722b6149f347349366c847c08d7eb2ddd9c70592e5589d9b65dfaa64df6c` |
| 12M `state.events` | `45a732754c9932220374b00810fb29b8ff3034420f3a0e51dca774c02de66f17` |
| 12M `state.final_associations` | `40fec6caa511034be67335a8f274b272724e360caa22e1386409fb49f15cff1a` |
| 12M `state.final_permanent.lammpsdat` | `6c4bbdd3248b317b4c2884ef0013227bad2ab337a930070db61cc2d67a04f6fc` |
| 12M `state.numerics.tsv` | `49ffd62c71a5adeea1dde0e1e7658c084f5a2a513be0a4a6cdba0054f96a17a9` |
| 12M `state.restart.lammpsdat` | `6d4f52474befbfe2f1d1fb37a3ab7bb88e26c76f8a5f3000cc08bcc06c8c8884` |
| 12M `state.state` | `203d6e2bd9c81eb6e1a3360f75702025937b53244950048f754b1341d3041559` |

12M completion receipt SHA256: `2394f3cfcba74b6fac3a2a04a7ac72b1010e2eb57bc1a1c6759bf29ce00548d9`.
Extension CPU validation: 4,001 frames, 25,653 accepted events, 1,915 final bonds; numerical status valid.

## r003

12M prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE10/equilibrate_18d492ee0f4b4a7d98ca32e39ce8f95a/r003/state`.
8M parent prefix: `/home/jramirez/UAMMD_KG/examples/KG_Assoc/kg_assoc_100m/banks/e2_attempts/F04_N010_RP080_EE10/equilibrate_fb8954dc860740d6b923759b2b21a703/r003/state`.
Chemical seed: `420703`; old/new requested MD seeds: `520114/520120`.
Old/new effective MD seeds: `2977947300/2894249636`.
Preserved 8M chemistry counters: creations `27733`, breaks `25812`.

| Step and payload | SHA256 |
|---|---|
| 8M `state.restart.lammpsdat` | `5d0fe43a0520d875175fc9634884dada9985ebfdb2751f9a44824baacdb2624f` |
| 8M `state.assoc_restart` | `bf080e697734e91b98d636ccb4175f839da0f046a645f1d5284a24d2c8665a5b` |
| 12M `state.assoc_restart` | `136351973a9e8a555e08ff327d7bfcc6ce3f8f61492903e9044f0113b8ce53e3` |
| 12M `state.conformation.tsv` | `b6f52e592840631b19236588ac502245b63bd9076c92c7120b5f8019625de646` |
| 12M `state.events` | `f5fcd40a5c14e528ed06ebd25ba8e340496fdd6e4f446f1f1ab954fd71f84df6` |
| 12M `state.final_associations` | `16424e62281a6012f9a9d1356cbb2e9bf79e8f3009cfa8078d56c9ba66f7dee5` |
| 12M `state.final_permanent.lammpsdat` | `80bfe0fabcaf5a3fafdd0c19e772c547e6484373360e00646b85fd0d593194b6` |
| 12M `state.numerics.tsv` | `20719b1a4012b5e6c79fece0e6207256a4d9ed9650279656cd692b4b923fe289` |
| 12M `state.restart.lammpsdat` | `c704178a3769932927ef647ba40e1754928ba188fb42d5c45ffb154ef80a32e1` |
| 12M `state.state` | `f8f439e7a11ff1bf5eaed9426e7445e8f7a1731d0c12b439a5742f610b3a4fc5` |

12M completion receipt SHA256: `df0afdd486c3536207e5c38d5e33f952a54f27f64e835c45ff59b4620f61d017`.
Extension CPU validation: 4,001 frames, 25,903 accepted events, 1,926 final bonds; numerical status valid.

## 0–8M build provenance

Recorded Git SHA: `49ffc4006763e0409e06cc12cdd0dd7eba7d2fe7`.
Recorded `kg_assoc_stars` SHA256: `fb620c052e916e8dbb4bcd3f0fb8358da4ec8ee3a912e35d8c2f91716457ef31`.
Authentication scope: `historical_build_and_source_authenticated; binary_bytes_not_reauthenticated`.
Build command: `make -B -j2 kg_assoc_stars kg_assoc_stars_candidate_smoke kg_assoc_candidates_test kg_assoc_production kg_assoc_campaign_production kg_assoc_campaign_production_smoke`.

## 8–12M build provenance

Recorded Git SHA: `4ada00d18cff6ac5e83872faf469409ee892f28f`.
Recorded `kg_assoc_stars` SHA256: `ec07defac25de62accdee0ff89593db4c632750053cfa23fe9e522475b229d30`.
Authentication scope: `current_binary_hashes_authenticated`.
Build command: `make -B -j2 kg_assoc_stars kg_assoc_stars_candidate_smoke kg_assoc_candidates_test kg_assoc_production kg_assoc_campaign_production kg_assoc_campaign_production_smoke`.

All 289 common native/build-recipe source hashes match between builds. The
original binary bytes were replaced by the rebuild and no archive was found;
the original recorded executable digests, build logs, source and approved 8M
dossier authenticate, but old binary bytes are not reauthenticated now. Current
extension executable bytes and build provenance authenticate. Historical E1
executable bytes likewise remain a limitation; available parent/input/output
bytes and provenance are checked. No executable or GPU calculation ran here.

Full plans, source/build hashes, seeds, parent/output/receipt identities and fresh
validation: [provenance.json](evidence/provenance.json). Execution witnesses:
[AUTHENTICATION.json](AUTHENTICATION.json). Previous evidence remains unchanged.
