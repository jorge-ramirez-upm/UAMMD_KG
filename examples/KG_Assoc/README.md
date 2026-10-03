# Associating Kremer--Grest A1

This directory is an isolated A1 scaffold for reversible sticker bonds. `../KG` is the untouched, validated non-associating baseline; its WCA interactor is included rather than copied. The executable follows `lammps` branch `feature/associating-stickers`, specifically `pair_associating` and `fix_associating_kinetics`.

For a transient pair, `U_assoc(r)=U_FENE(r)-U_FENE(r*)-Ee`, where `U_FENE=-K R0^2 log(1-(r/R0)^2)/2`; `r*` is the LAMMPS KG minimum. WCA remains active once per pair. The mechanical FENE force has no `Ee` contribution. Matching the current LAMMPS implementation, `r_assoc` gates the kinetic candidate list for both creation and breaking. An already bonded pair outside `r_assoc` remains mechanically bonded up to `R0` and cannot undergo a kinetic breaking event until it re-enters the chemical range. This is intentional reference equivalence, not a UAMMD limitation.

Build with `make -C examples/KG_Assoc`. Run `./examples/KG_Assoc/kg_assoc_dimer --steps 10000 --seed 17 --output dimer`; it writes `dimer.events` and `dimer.summary`. `--self-test` directly checks the actual interactor energy expression and force, the R0 guard, and detailed balance over signed energy changes with small and moderate finite-step probabilities.

Kinetics use LAMMPS's stateless SplitMix-style hash of seed, timestep, ordered particle ids, and stream; candidate edges are sorted by its order stream and state is re-read before every transition. The host state is synchronized to a device `partner[]` only after accepted kinetic updates. A1 is only a two-sticker dimer validation program: no multi-sticker networks, star polymers, rheology, or production analysis is implemented.

The A2 K1 validation harness is `kg_assoc_k1`; see [`k1/README.md`](k1/README.md). It is a homogeneous many-sticker fluid validation only, not the associating star-polymer model.
