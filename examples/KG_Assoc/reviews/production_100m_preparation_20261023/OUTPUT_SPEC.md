# Existing production output contract

The strict front end `kg_assoc_campaign_production.cu` includes the unchanged
`kg_assoc_production.cu`. Its default macro is 100,000,000, with dt=.01, T=1,
nu0=20, chemistry every100 steps, r_assoc=1.25. It has no run-length override,
resume option or full simulation checkpoint. The campaign schema and independent
`kg_assoc_campaign.verify_run` both support this exact100M duration already.

Stress is sampled after integration and scheduled chemistry/cache refresh, every
MD step, excluding step zero. The same buffered GPU reduction and
Correlator6(40,16,2) are retained. Channels are volume-weighted correlations:

    G = (Gxy + Gxz + Gyz)/(5T) + (GNxy + GNxz + GNyz)/(30T)

Nxy=σxx−σyy, Nxz=σxx−σzz, Nyz=σyy−σzz; Nxz=Nxy+Nyz. There are three
preparation families, not six independent channel replicas. No additional volume
factor, raw stress trajectory, temporal correlator or alternative estimator is added.

| Suffix on `run` | Existing content / 100M cadence |
|---|---|
| `.stress_correlator` | time, Gxy, Gxz, Gyz, GNxy, GNxz, GNyz, G, n_pairs; final100M-sample evaluation |
| `.thermo.tsv` |100,000 samples, every1000 steps; finite energies/T/pressure, total/intra/inter bonds, free stickers and **segment** creation/break counts |
| `.events` | all accepted C/B changes, absolute step/time, sticker and molecule identities |
| `.com_trajectory` |10,000 frames, every10k steps; molecule COM for transport/diffusion |
| `.topology` |10,000 post-chemistry frames, synchronized with COM; active sticker-pair graph |
| `.beads.bin` |1000 full-bead frames, every100k; wrapped coordinates, identity/permanent-topology header |
| `.final.lammpsdat`, `.final_associations` | archival final geometry and partners; **not** a reloadable MD/chemistry restart pair |
| `.complete.json` | atomic native completion, absolute initial/final steps and production duration |

Runtime stdout/stderr must also be preserved. The normal footer is historically
named `STAR_ASSOCIATION_SMOKE PASS` even for100M, with `S1 total_timesteps 100000000`.
The footer alone is insufficient validation. Prepared `run.json` and preparation
approvals remain immutable; future runtime journals must be separate.

`rheology_existing_method_20261023/replay/LAG_GRID.csv` gives the exact finite100M
lag/count grid. Fine counts are N−j; coarse counts floor(N/2^k)−j, with averaged
stress blocks and the implementation's deepest-populated-level exclusion. The
preparation recovery helper checks this grid and uses the unchanged P4 reader to
recompute every G row, require finite channels and exact sample/support metadata.
Counts describe products, not independent information. Long-lag precision depends
on the three families and actual relaxation. Use actual nonuniform lag widths for
integration. No correlator simulation or new correlator test was needed here.

Existing `verify_run` requires all nine outputs, exact duration, thermo/cadence,
COM/topology synchronization, bead format/cadence, event replay to final partners,
final geometry and output hashes. The CPU recovery helper additionally authenticates
start/end steps, execution evidence, native footer and full correlator grid/channels.
The production runtime checks reciprocal associations, counter conservation, finite
FENE states and geometry through existing invariant calls. It does **not** contain
the separate E2 initial-device dump or every-sweep all-pairs comparison dispatcher;
CPU `--validate-initial-state` authenticates metadata only. No new device-readback
or independent-oracle execution is claimed for this distinct production binary.

Reuse existing analysis: `analyze_p42_rheology_pilot.py` (six-channel tails and
viscosity), `analyze_p45_topology.py`, `analyze_p46_bond_dynamics.py`,
`analyze_p47_walking_hopping.py`, `analyze_p48_percolation.py`,
`analyze_campaign_structure.py`, `analyze_p44_com_diffusion.py` and
`analyze_p44_com_fsqt.py`. Invoke analyzers directly with explicit accepted-system
metadata/initial partners: the legacy aggregate analysis wrapper assumes an E1
parent path and is not suitable unchanged for these E2-only planning stubs.
Bond lifetimes/COM dynamical origins start within production; no origin spans its
fresh-noise/chemistry boundary. COM sampling supports sampled transport, not
unrecorded sub-10k-step motion. Whole-run G cannot recover age- or motif-conditioned
stress products; these are not requested launch requirements.

Review tails per family and across families using the established P4 method and
raw-support sensitivity. Report eta0 only with a resolved tail, useful uncertainty
and cutoff stability. Unresolved tails allow labeled truncated integrals, not a
converged viscosity claim. The historical corrected-versus-pilot chemistry and
Ea10 qualifications in the existing rheology review remain applicable. No new
initial-equilibration threshold or mandatory early/late stress comparison is imposed.
