# D2A.5 N64/N128 long-duration campaign — preparation only

28 October 2026. No build, test, GPU program, simulation, benchmark or scientific
reduction ran in Codex. Independent review precedes all proposed local commands.
This preparation grants no campaign execution or scientific acceptance.

Starting local HEAD: `9324873e69e2ec5d8f424f9b39d072995480aeef`.
Actual remote HEAD queried before changes:
`76b52163d19abf2ae865f08bf65831e82df1d70b` (the last reviewed preparation).
The existing local `.gitignore` commit is retained unchanged; all new work is
inside `examples/slip-springs/`. Physics, RNGs, kernels, observer definitions,
KG arithmetic, old runners, frozen campaigns and existing evidence are unchanged.

## Frozen campaign and identities

[manifest.json](e1_d2a5_production_config/manifest.json) freezes the24 argv arrays,
run identities, seeds, schedules, resource budgets, full lag support, tool hashes
and evidence references. SHA256:

`297ad861edb98232ca91c9fbd11b7eef2443bc685d7c89ec592a7ab86777c365`

The sidecar and tiny [entry point](e1_d2a5_production.py) pin the same identity.
The entry point is trusted through the reviewed Git preparation commit; its
bytes are archived at execution. It is excluded from the manifest's tool hashes
to avoid a circular manifest/entry-point hash dependency. Runtime helpers,
including the existing supervisor and context checker, are hash-pinned.

| Length | Beads/chain | M | T | BD steps | Constrained Z |
|---|---|---|---|---|---|
| N64 | 65 | 256 | 10000 | 100000000 | 4096 |
| N128 | 129 | 256 | 40000 | 400000000 | 8192 |

Both lengths use kBT=zeta=b0=1, kb=30, dt=0.0001, slip-ms2=5 and hop-rate100.
The A/B/C/D matrix is respectively `(kappa,Z)=(0,0),(0,Z),(10,0),(10,Z)`.
Canonical end renewal is on only for constrained systems; bare controls have
renewal off. Constrained nominal density is Z/(MN)=1/4. Stress stays off.

Order: all N64 A-r1..r3, B-r1..r3, C-r1..r3, D-r1..r3, then the same N128 order.
Run IDs are prefixed `n64-` or `n128-`. Seeds are also replica IDs:

| Cell | N64 seeds | N128 seeds |
|---|---|---|
| A | 732505101,732505102,732505103 | 732506101,732506102,732506103 |
| B | 732505201,732505202,732505203 | 732506201,732506202,732506203 |
| C | 732505301,732505302,732505303 | 732506301,732506302,732506303 |
| D | 732505401,732505402,732505403 | 732506401,732506402,732506403 |

Literal whole-number searches found no uses of these seeds in the available
project or D2A.3/D2A.4/D2A.5 evidence before reservation. They differ from every
seed in the frozen D2A.3 and D2A.4 manifests. External uses cannot be excluded.
There are three distinct whole-run seeds per cell; matching seed numbers are
not used to pair configurations. No seed replacement or failed-run substitution.

The unchanged double executable is
`/home/jramirez/UAMMD_KG-slip-springs-dev/examples/slip-springs/build/d2a5-review-v1/double/semiflexible`.
Required SHA256: `54dc84a9aac35fd6574ce6e2890a6c8a0f545743fdc2bbd32bc0a70863dcf9ce`.
Implementation SHA: `d622e0cc34d4019358bebad5ce8a86e64c265351`.
No rebuild, replacement or alternate binary is accepted.

The manifest pins the existing bounded correctness summary, completed sustained
summary, both sustained receipts and dependency file. Authentication checks the
same-binary completed statuses, preflight output hashes and archived provenance
before launch and after completion. These are record-integrity checks, not new
scientific interpretation. Root provenance preserves the records, tool sources,
preflight build/dependency material, source Git tree identities, preparation HEAD,
environment and machine identity. Prior raw evidence stays at its original paths.
Historical compiler invocation remains independently unrecorded; neither the
Makefile, dependency file nor installed compiler is a recovered build transcript.

## Acquisition and exact support derivation

Dynamics stays at step0 and every100 BD steps, delta=0.01, with no shorter final
interval. Selected beads are0,16,32,48,64 for N64 and0,32,64,96,128 for N128.
CM MSD, those five absolute MSDs, end/quarter averages and signed differences,
C1 and C2 remain the accepted observables. P16/m2, L19/L21 and512 MiB observer
allowance are frozen after the following arithmetic derivation.

For F=steps/100+1, level k has floor(F/2^k) complete coarse samples. Let
`K=min(L-1,floor(log2(F)))`. KG omits level K from export. Fine bins are ell=0..15;
on each level1<=k<K, export `ell=8..min(15,floor(F/2^k)-1)`. Integer lag is
`ell*2^k` samples, `100*ell*2^k` BD steps, with
`origins_per_chain=floor(F/2^k)-ell`. No incomplete blocks are padded.
This is the unchanged `exported_grid`/KG rule; the full302-bin union is frozen
in the manifest, including each origin count and primary-support mask.

| Support | N64 | N128 |
|---|---|---|
| Dynamics frames F | 1000001 | 4000001 |
| Configured/deepest-populated K | 18 | 20 |
| Omitted deepest level | 18 | 20 |
| Exported bins/chain | 143 | 159 |
| Chain rows / replica rows | 36608 / 143 | 40704 / 159 |
| Largest exported lag, BD steps | 91750400 | 367001600 |
| Largest exported lag, model time | 9175.04 | 36700.16 |
| Its block width, fine frames | 65536 | 262144 |
| Its origins/chain | 1 | 1 |
| Last primary lag, BD steps | 19660800 | 78643200 |
| Last primary lag, model time | 1966.08 | 7864.32 |
| Its block width / origins | 16384 / 49 | 65536 / 49 |

At k17/k19 only seven coarse samples exist, so neither level has an ell>=8
export. At k16/k18 there are15 samples; ell8..14 contribute seven bins, ending
with one origin. Earlier levels contribute16+15*8 or16+17*8 bins. The final weak
tail is retained and marked as such, not promoted to primary evidence.

Primary support is explicitly `lag_steps <= steps/5 AND origins_per_chain >=32`.
This yields the primary endpoints above. It proves neither effective independence,
stationarity, adequate relaxation nor a terminal regime. Fits would exclude lag0.
MSD uses direct endpoint displacement with last-position decimation and phase b-1;
orientation averages fine unit/vector features in blocks b without renormalizing,
giving triangular lag support. These filters must remain distinct in later work.

LP64 principal payload is1352 bytes/owner/level; there are9 owners per chain.
Payload totals are59185152 bytes (N64) and65415168 bytes (N128). The existing
same-binary L15 estimate is189278720 bytes. Holding ABI and owner counts fixed,
each added level contributes `4*9*256*1352=12460032` conservative bytes. Thus
expected guarded estimates are239118848 and264038912 bytes, below512 MiB.
The runtime validator requires those actual same-binary estimates and the budget.
These are allocation estimates, not RSS or GPU peak measurements.

The observer has1000001/4000001 frames, far below even a32-bit unsigned-long
count limit; the required host is64-bit Linux/LP64. BD/RNG/event clocks are
uint64. Maximum configured lag clocks are393216000/1572864000 steps; exported
clocks and all floating lag integers are exactly representable below2^53.
The largest BD noise offset is8*400000000=3200000000, evaluated as uint64.
Even the existing hard100000 events/batch bound times400000000 steps is
40000000000000, below uint64. Expected constrained attempts are4.096e9/3.2768e10,
not32-bit counters. Poisson means40.96/81.92 remain below the unchanged10000 guard.
Chain/bead IDs and diagnostic indices fit signed32-bit ranges; L*P<=336.
These bounds do not authorize modifying overflow checks or event limits.

## Physical output schedule

D2A.4's scalar stride5000 would produce20001/80001 frames, about5.12/20.48
million chain rows per run. Production here uses stride100000 (N64, time10) and
400000 (N128, time40):1001 frames and256256 chain rows per run, uniformly spaced
at T/1000. All four cells at a given length share this cadence. These slow
scalar diagnostics complement the unchanged delta0.01 dynamics acquisition.
They are not a replacement trajectory for fine-time scalar reconstruction.

Full E1 context is at0,T/10,...,T:11 frames, all shared with scalar/dynamics
readbacks. Joint coordinate/attachment snapshots are only at0 and T; ordinary
initial/final states, initial bond lengths, final bond statistics, occupancy,
connectors, populations, tangents and hopping/renewal counters remain. The
equilibrium_backbone.csv is correctly header-only because these frames reuse
scalar rows. There is no positional trajectory or stress acquisition.
Shared dynamics frames=1001; extra readbacks=999000/3999000. Cumulative full-position
traffic is532480532480/4227073056768 bytes per run, not simultaneous allocation
or disk output. Source/build and output-budget details are in the
[resource and execution guide](E1_STAGE_D2A5_PRODUCTION_OPERATOR_GUIDE.md).

## Completion and review boundaries

[e1_d2a5_validate.py](e1_d2a5_validate.py) checks exact physical/coefficient/seed
identity, launches and chain/bead/spring counts, complete finite JSON/CSVs, exact
row inventories and scalar/E1 schedules, full dynamics grid/origins/phase/labels,
budgets, and initial/final agreement with joint snapshots. It reuses the unchanged
variable-length E1 structural checker for occupancy, contour links, connector
and snapshot serialization consistency, and event identities/totals. Existing
3e-12 structural comparisons are unchanged; no new scientific tolerance is added.
Process exit0 alone is insufficient. Receipts contain hash inventories and
timers; only validated success permits the next child.

The new CPU regression script prepares malformed synthetic correlation records
at both lengths: missing/extra rows, wrong counts/clocks/phases, nonfinite values,
wrong chain IDs, and duplicate/overflow JSON. It also checks the frozen24-run
matrix and support endpoints. It remains unexecuted. It does not verify actual
GPU trajectories, long-run resource enforcement, crash recovery or throughput.

[The analysis handoff](E1_STAGE_D2A5_PRODUCTION_ANALYSIS_HANDOFF.md) describes later
questions and support/statistical safeguards. No analysis code, fits, plots or
hypothetical trajectory results are produced here. D1.6 remains scientifically
closed with qualifications: equilibrium preservation not confirmed. No terminal,
ergodicity, timestep, reptation, entanglement-length or rheology acceptance follows.

Review all preparation before using the exact commands in the operator guide.
No campaign was launched. The final commit SHA and push outcome belong in the
handoff response, not a self-referential file inside that commit.
