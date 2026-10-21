# E1 Stage D1.3 — authorized Phase A benchmark results v1

**Completed: exactly eight sequential processes, four paired physical initializations,
14000 BD steps; all exits zero, all resource/authentication checks passed and all four
paired physical-output comparisons were byte-identical.** No repetitions, other cells,
technical trajectories, old D1.1 pilot, Phase B/C or D2 simulations were run in this task.
These are performance/output results, not scientific equilibrium validation.

Local and remote `slip-springs` HEAD were verified as
`1e037244f4085dfc9b3fca5d0532d94458062a49` before execution. The user’s explicit
“Stage D1.3 — Authorized Phase A Benchmark Execution” instruction supplied the scope
and exact limits; no further scientific authorization was requested. Accepted preparation,
D1.2 design, local rules, frozen modules/manifest and scientific source checkout were inspected.

## 1. Evidence and trust anchors

Raw campaign evidence, preserved separately and unchanged:
`/tmp/e1-d13-phase-a-authorized-20261021-v1/campaign`. Approval, preflight, runner logs, independent verification and analysis
are siblings under `/tmp/e1-d13-phase-a-authorized-20261021-v1`. No raw CSV or binary is committed.
The small committed [execution reference index](e1_d13_phase_a_execution_references.json) binds
artifact locations, byte counts, inventory digests, all eight receipt hashes and paired checks.

- Execution/tool commit: `1e037244f4085dfc9b3fca5d0532d94458062a49`.
- Accepted scientific source commit: `0dea651b58171a72206774bcebb2f4c74960069b`.
- Frozen manifest SHA256: `0c2df3279faf6a7457125cdc12f78c233d5d8999c6e459560edbfe1cb9a3fd3e`.
- Verified fresh-build receipt SHA256: `1739e51ebbe43a81a810d09274d9a9304fafb339166d7e13f5e4600bd32d37e0`.
- Executable SHA256: `41b778f5ce4087be5f7713b3c5df788035d911354810824d028bfab605ffe7f7`.
- Environment SHA256: `05e9f076948c5d562925dd24b9d9d47bc8611698516efea13808029ad5d8c79a`.
- User-approved external record SHA256: `a3677de024445816d5fa2e59dfd6e923b039442efd22f966f36876ff28879fe0`.
- Read-only preflight SHA256: `9fd903cbb5fb2c0d1f4712a8cda21cc6b50c7cc8bbba139ea3d774a4401f69a7`.
- Externally recorded completion SHA256: `8cad8e59c2ea7501655f5ea75661fb4de490aed10c9a941f925135866bc3c180`.
- Independent authentication SHA256: `af21d1e1bb4d71e99ad07817735958fc658a96f59e2a2b5afa92623b662d470f`.
- Accepted-adapter analysis SHA256: `b33235ef913ca410bbfa94b3757081be1a809470aeab648c6cc9a4bf281f044b`.

The existing `/tmp/e1-d13-build/build.json` and its entire live identity closure authenticated:
correct GitHub repository/origin, clean `/tmp/e1-d11-source` checkout at the accepted source
commit, executable, observed fresh compilation transcript, compiler/runtime identities,
1914 dependency records and five linked-library records. The previously accepted binary
was reused; no rebuild was necessary. Scientific source, observer, frozen D1.1/D1.2/D1.3
files, schedules, limits and historical allowlists were not changed. The frozen manifest and
approval template remain false/null; the separate execution approval is true for this root only.

The completion hash above came from the successful runner’s returned JSON and was recorded
outside the campaign in `completion.sha256` before independent authentication. The consumer
received literal external manifest/approval/completion hashes; it did not derive trust from
filenames or a checksum stored solely beside raw data. The accepted analysis adapter authenticated
the whole cohort again before reading/reducing and again before publishing `analysis.json`.

## 2. Exact scope and approved limits

Common settings: M=64,kb=30,b0=1,kBT=zeta=1,A2=5,T=.25,double precision,
canonical end renewal on, stress off, direct exact E1 equilibrium initialization.
C− means observer disabled; C+ means sparse observer enabled. Ordering was C1−,C1+,
C2−,C2+,C3−,C3+,C4−,C4+. Z=round_half_up(M*N/Ne); each pair shares its frozen seed.

| Cell | N | kappa | Ne | nu_hop | dt | Z | rho | BD steps/profile | Seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8 | 0 | 16 | 10 | 0.0001 | 32 | 1/18 | 2500 | 721300101 |
| 2 | 8 | 0 | 16 | 10 | 0.00025 | 32 | 1/18 | 1000 | 721300201 |
| 3 | 32 | 10 | 4 | 100 | 0.0001 | 512 | 8/33 | 2500 | 721300301 |
| 4 | 32 | 10 | 4 | 100 | 0.00025 | 512 | 8/33 | 1000 | 721300401 |

| Approval field | Exact approved value |
| --- | --- |
| aggregate_output_bytes | 1073741824 |
| aggregate_seconds | 3600 |
| max_host_rss_bytes | 2147483648 |
| min_available_host_bytes | 8589934592 |
| min_free_disk_bytes | 10737418240 |
| min_free_gpu_bytes | 4294967296 |
| per_run_output_bytes | 134217728 |
| per_run_seconds | 120 |

No ceiling was increased or bypassed. Per-file RLIMIT_FSIZE, serial process-group supervision,
per-run/aggregate wall/output checks, host RSS and resource headroom gates were active within
the runner’s documented .05-second polling and post-exit limitations. No failure, timeout,
interruption, automatic retry/resume or parameter change occurred.

## 3. Live preflight and execution receipts

| Item | Measured/verified immediately before execution |
| --- | --- |
| GPU UUID | GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 |
| GPU model / capability | NVIDIA GeForce RTX 3060 Ti / 8.6 |
| GPU driver / toolkit | 580.178.04 / CUDA13.0.88 |
| Runtime / driver API | 13000 / 13000 |
| Total GPU reported bytes | 8589934592 |
| free_disk_bytes | 1247450877952 |
| available_host_bytes | 30925139968 |
| free_gpu_bytes | 8072724480 |
| Preflight blockers | none |
| Runner exit code | 0 |
| Campaign start UTC | 2026-10-21T18:36:27.466414+00:00 |
| Campaign end UTC | 2026-10-21T18:36:43.817486+00:00 |

Measured availability is distinct from the approved headroom thresholds. The authenticated
preflight passed before the explicit execution gate was invoked; the runner rechecked identities,
environment and resources around every process. `execution-command.json` records the exact
outer CLI; each `runs/ID/execution.json` records the exact simulator argv, seed/profile,
environment identity, start/end/exit, supervision results, raw hashes and pre/post GPU availability.

Every on profile has v1 schema/completion, seven full E1 observations and four complete-state
snapshots. Every off profile has exactly eleven legacy files and no optional E1 files. Scalar
steps are 0,1000,2000 at dt=.0001 and 0,400,800 at dt=.00025. Full E1 steps are
0,1,5,25,100,500,2500 and 0,1,2,10,40,200,1000, respectively; snapshots are
0,1,100,2500 and 0,1,40,1000. Thus final t=.25 is recorded despite being off the .1
scalar cadence. First-step frames remain diagnostics at different physical times. No rounding
or interpolation was used. The independent observer checker reconstructed the selected states,
verified synchronized joint quantities, occupancy and population sums, and linked endpoints
to legacy coordinate/anchor files. Counter identities and interval/cumulative totals all passed.

Paired equality covers initial/final polymer coordinates; initial/final spring IDs, chain/site
and anchors; fixed anchors; parameters; scalar/bond data; and hopping/renewal metadata.
Independent verification additionally compared the actual legacy file bytes directly. Only
the ten accepted numeric timer/rate spans were masked in `metadata.json`; all other metadata
bytes matched. Observer-owned files and timing values were not required equal.

## 4. Measured timings and event throughput

Seconds below are recorded values rounded for display. Int is the CUDA integration timer;
Prod is simulation production wall; Child is supervised process wall. The JSON retains full precision.

| Run | Steps | Init s | Int s | Prod s | Child s | Int s/BD | Prod s/BD | Child s/BD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1− | 2500 | 0.115894 | 0.158238 | 0.168020 | 0.355351 | 6.3295334e-05 | 6.7207971e-05 | 0.0001421402 |
| C1+ | 2500 | 0.104910 | 0.159494 | 0.174712 | 0.356736 | 6.3797542e-05 | 6.9884824e-05 | 0.00014269429 |
| C2− | 1000 | 0.106296 | 0.063042 | 0.067498 | 0.256459 | 6.3041761e-05 | 6.7498103e-05 | 0.00025645941 |
| C2+ | 1000 | 0.128470 | 0.064715 | 0.074421 | 0.256437 | 6.4714657e-05 | 7.4421071e-05 | 0.00025643683 |
| C3− | 2500 | 0.114345 | 0.271009 | 0.281572 | 0.462002 | 0.00010840344 | 0.00011262871 | 0.00018480068 |
| C3+ | 2500 | 0.120334 | 0.270636 | 0.302016 | 0.515492 | 0.00010825431 | 0.00012080628 | 0.00020619668 |
| C4− | 1000 | 0.148334 | 0.138106 | 0.143233 | 0.368166 | 0.00013810586 | 0.00014323294 | 0.00036816583 |
| C4+ | 1000 | 0.144630 | 0.137550 | 0.163778 | 0.365353 | 0.00013754998 | 0.00016377767 | 0.00036535289 |

Across the eight disjoint process intervals: initialization sums to 0.983213461 s,
integration 1.262788833 s, production 1.375249262 s,
and supervised children 2.935994583 s. Campaign wall was 16.351083196 s;
the outer runner invocation, including CLI preflight/startup, took 17.835876004 s.
The 13.415088613 s campaign-minus-child difference includes repeated identity/resource
probes, authentication, formatting and bookkeeping; it is not additional simulated production.
Do not add initialization, integration, production or observer timers into a purported total:
integration is inside production and includes hopping/invariants/forces/update/diagnostic D2H
and host gaps; force/diagnostic and observer wall/exclusive/transfer scopes overlap. Production
excludes initialization/final output; supervised child wall includes startup/exit/polling granularity.

Counts and per-physical-time rates are identical within each pair; every trajectory has T=.25.

| Cell (both profiles) | Attempts | Interior accepted | Renewal proposed | Renewal accepted | Same/cross renewal | Attempts/T | Interior/T | Renewal accepted/T |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 77 | 48 | 7 | 6 | 0/6 | 308 | 192 | 24 |
| 2 | 76 | 44 | 4 | 4 | 0/4 | 304 | 176 | 16 |
| 3 | 12969 | 6499 | 355 | 262 | 3/259 | 51876 | 25996 | 1048 |
| 4 | 12941 | 6482 | 284 | 226 | 2/224 | 51764 | 25928 | 904 |

| Run | Attempts / production wall s | Interior accepted / production wall s | Renewals accepted / production wall s |
| --- | --- | --- | --- |
| C1− | 458.279 | 285.680 | 35.710 |
| C1+ | 440.725 | 274.738 | 34.342 |
| C2− | 1125.958 | 651.870 | 59.261 |
| C2+ | 1021.216 | 591.230 | 53.748 |
| C3− | 46059.303 | 23081.148 | 930.491 |
| C3+ | 42941.476 | 21518.749 | 867.505 |
| C4− | 90349.326 | 45254.952 | 1577.849 |
| C4+ | 79015.656 | 39578.045 | 1379.919 |

Recorded totals across eight processes are 52126 attempts, 26146 accepted interior hops and
996 accepted renewals. These totals count each paired replay twice, not eight independent stochastic realizations.
Accepted interior and renewal events retain their separate original counter semantics. Throughput
is end-to-end per production wall, not an isolated hopping-kernel rate or a statistically precise estimate.

## 5. Observer overhead and timestep comparison

| Cell | On−off production s | Production change % | On−off child s | Exclusive s | Observer wall s | Transfer s | Transferred bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.006692131 | 3.98 | 0.001385215 | 0.005040019 | 0.005724061 | 0.000189907 | 285544 |
| 2 | 0.006922968 | 10.26 | -0.000022587 | 0.004957465 | 0.005569544 | 0.000198313 | 285544 |
| 3 | 0.020443918 | 7.26 | 0.053489990 | 0.020137593 | 0.021647520 | 0.000286965 | 1177960 |
| 4 | 0.020544725 | 14.34 | -0.002812949 | 0.020370041 | 0.021861941 | 0.000292485 | 1177960 |

There is one on/off pair per cell. Child-wall differences include startup and polling
variability; the negative signs in cells 2 and 4 cannot support a speedup claim. Positive production
differences of roughly 7–21 ms coexist with different initialization times and coarse supervision
granularity. Internal observer scopes are overlapping diagnostics, not additive overhead components.

| System/profile | Coarse/fine integration ratio | Coarse/fine production ratio | Coarse/fine child ratio |
| --- | --- | --- | --- |
| N8 / off | 0.3984 | 0.4017 | 0.7217 |
| N8 / sparse | 0.4058 | 0.4260 | 0.7188 |
| N32 / off | 0.5096 | 0.5087 | 0.7969 |
| N32 / sparse | 0.5082 | 0.5423 | 0.7087 |

Coarse dt uses 60% fewer BD steps. Production reductions were about 57–60% for the small
flexible cells and 46–49% for the dense stiff cells. The two timestep cells have different frozen
independent seeds, counts and conformations, so these are unpaired descriptive comparisons.
Expected attempts per physical time remain Z*nu: 320 in the small cells and 51200 in dense
cells. Larger event batches at coarse dt, serial hopping/renewal and synchronous diagnostics
prevent equating BD-step reduction with end-to-end runtime reduction. No timestep accuracy
or convergence conclusion follows from these costs.

## 6. Output sizes and resource accounting

| Run | Raw bytes | Whole per-run evidence bytes | Peak host RSS bytes | Explicit device arrays bytes |
| --- | --- | --- | --- | --- |
| C1− | 193676 | 198109 | 104783872 | 77788 |
| C1+ | 589348 | 595476 | 105164800 | 77788 |
| C2− | 193602 | 198037 | 105058304 | 77788 |
| C2+ | 610470 | 616603 | 105553920 | 77788 |
| C3− | 696972 | 701444 | 106229760 | 304228 |
| C3+ | 2349170 | 2355341 | 106184704 | 304228 |
| C4− | 697629 | 702100 | 105619456 | 304228 |
| C4+ | 2432929 | 2439104 | 106020864 | 304228 |

The campaign contains 174 files totaling **10931433 B** (10.425 MiB).
Its 128 raw output files total **7763796 B**; copied build/binary/configuration, approval, receipts and
logs account for the remaining 3167637 B. The complete external bundle, including preflight,
independent proof and analysis, totals 11011124 B across 194 files at reporting time. The frozen
build binary itself is 2709792 B. No data compression, selective connector deletion or trajectory thinning was applied.

| Raw category | Campaign bytes |
| --- | --- |
| audit_snapshots | 1957707 |
| legacy_backbone | 1747754 |
| legacy_state | 1795480 |
| metadata_provenance | 24951 |
| observer_backbone | 358287 |
| spring_site_connector | 1879617 |

Per-file raw byte accounting follows. A dash means the optional file is absent in an off profile;
header-only N8 long-tangent streams are 16 B. Sizes include headers/newlines. Metadata byte-length
differences within pairs come from excluded timing values, while all non-timing bytes match.

| File | C1− | C1+ | C2− | C2+ | C3− | C3+ | C4− | C4+ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bond_statistics.csv | 57191 | 57191 | 57242 | 57242 | 229691 | 229691 | 229565 | 229565 |
| equilibrium_attachments.csv | — | 10435 | — | 10927 | — | 170846 | — | 178744 |
| equilibrium_backbone.csv | — | 76403 | — | 77472 | — | 74930 | — | 75944 |
| equilibrium_chains.csv | — | 25829 | — | 27922 | — | 44159 | — | 44993 |
| equilibrium_complete.json | — | 839 | — | 840 | — | 842 | — | 852 |
| equilibrium_connectors.csv | — | 22927 | — | 23345 | — | 371733 | — | 379324 |
| equilibrium_events.csv | — | 575 | — | 603 | — | 623 | — | 648 |
| equilibrium_positions.csv | — | 165179 | — | 173611 | — | 607456 | — | 640509 |
| equilibrium_schema.json | — | 262 | — | 276 | — | 264 | — | 278 |
| equilibrium_sites.csv | — | 93216 | — | 101856 | — | 355092 | — | 386772 |
| equilibrium_tangents.csv | — | 16 | — | 16 | — | 26270 | — | 27236 |
| final.csv | 37496 | 37496 | 37386 | 37386 | 135762 | 135762 | 136160 | 136160 |
| fixed_slip_springs.csv | 2084 | 2084 | 2089 | 2089 | 32911 | 32911 | 32958 | 32958 |
| hopping_metadata.json | 747 | 747 | 747 | 747 | 766 | 766 | 766 | 766 |
| initial.csv | 33946 | 33946 | 33922 | 33922 | 132203 | 132203 | 132581 | 132581 |
| initial_bonds.csv | 12346 | 12346 | 12348 | 12348 | 50781 | 50781 | 50764 | 50764 |
| metadata.json | 1621 | 1612 | 1663 | 1663 | 1640 | 1623 | 1672 | 1672 |
| parameters.txt | 60 | 60 | 60 | 60 | 260 | 260 | 260 | 260 |
| samples.csv | 43830 | 43830 | 43786 | 43786 | 43252 | 43252 | 43081 | 43081 |
| slip_springs_final.csv | 2178 | 2178 | 2177 | 2177 | 34850 | 34850 | 34919 | 34919 |
| slip_springs_initial.csv | 2177 | 2177 | 2182 | 2182 | 34856 | 34856 | 34903 | 34903 |

Every per-file SHA256 and size is also bound by the run receipt, whose hash is in the completion
record and committed reference index. All eight processes stayed far below the 128 MiB per-run
output and 2 GiB RSS ceilings; campaign evidence stayed below 1 GiB and wall below 3600 s.
Maximum measured child RSS was 106229760 B (101.309 MiB),
not the simulator’s host-workspace estimate. All sixteen prelaunch/postexit free-GPU readings
were 8072724480 B, above the required 4294967296 B. Available host memory and disk were
checked before each process and recorded in receipts: host availability ranged from
31069868032 to 31085350912 B, and free disk from 1247441682432 to 1247447449600 B.
Required headroom passed throughout.
**Peak GPU memory use was not measured.** Free-memory snapshots and explicit device-array
bytes are not GPU peak utilization; no such inference is made.

## 7. Phase B feasibility recommendations and scientific limits

The tested host readily met Phase A limits, and output was about 10.43 MiB including authenticated
campaign provenance. This supports preparing a separately reviewed Phase B feasibility budget;
it does not authorize Phase B or establish the E1 stationary law.

For matched N32,kappa10,Ne4,nu100 profiles, T10 has 40 times the physical horizon, BD steps
and expected attempts of T.25. A deliberately conditional 40x multiplication of the two sparse
production times gives about **12.08 s at .0001 and 6.55 s at .00025 per run**. These are arithmetic
planning proxies, not measured T10 times, bounds or linear-runtime promises. Initial/final I/O and
early diagnostics do not scale that way; later scalar/full-E1 counts are 101/26 instead of 3/7,
snapshots remain four, provenance/analysis costs are separate, and serial event/renewal/diagnostic
costs, system load and longer evolving states may change throughput. N32,kappa0 at the dense
Phase B parameters was not benchmarked here; N8,kappa0 does not substitute for that measurement.

Retain conservative resource headroom for review rather than lowering limits to the observed
~106 MB RSS. The D1.2 T10 eight-run raw estimate remains 63.28 MB nominal / 70.06 MB wide,
before its separate provenance/log allowances (~140–147 MiB total planning envelope). Its grids,
matrix/R=2, exact horizon, runner/analyzer changes and safe budgets still require separate review
and explicit authorization. Do not multiply the 17.84 s campaign wall by 40: it mixes systems and
is dominated by setup/authentication as well as physical simulation. No Phase B configuration or
authorization was enabled. Phase C and the old D1.1 proposal remain untouched.

This benchmark establishes bounded execution, output completeness and paired non-perturbation
for these trajectories only. It does **not** establish equilibrium preservation, timestep convergence,
long-time mixing, reliable relaxation times, chain independence, reptation/tube dynamics or rheology.
The accepted analyzer leaves scientific acceptance null. D0 tolerances remain unchanged.

## 8. Actual commands and read-only audit

The evidence bundle preserves complete JSON argv records (`preflight-command.json`,
`execution-command.json`, `analysis-command.json`) and stdout/stderr/exit receipts. The actual
authorized runner CLI, after the separate successful read-only preflight, was:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 /usr/bin/python3 /tmp/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d13_phase_a_runner.py preflight --manifest /tmp/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d13_phase_a_config/manifest.json --manifest-sha256 0c2df3279faf6a7457125cdc12f78c233d5d8999c6e459560edbfe1cb9a3fd3e --build-receipt /tmp/e1-d13-build/build.json --build-sha256 1739e51ebbe43a81a810d09274d9a9304fafb339166d7e13f5e4600bd32d37e0 --approval /tmp/e1-d13-phase-a-authorized-20261021-v1/approval.json --approval-sha256 a3677de024445816d5fa2e59dfd6e923b039442efd22f966f36876ff28879fe0 --gpu-uuid GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274 --output-root /tmp/e1-d13-phase-a-authorized-20261021-v1/campaign --authorize-phase-a-execution
```

This is an execution record, **not a rerun instruction**. The root now exists and is nonresumable;
do not change the approval/root or run another process. Reproduce verification without simulation:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 - <<'PY'
import sys
sys.path.insert(0, 'examples/slip-springs')
import e1_d13_phase_a_auth as auth
manifest, items = auth.authenticate_campaign(
    '/tmp/e1-d13-phase-a-authorized-20261021-v1/campaign',
    'examples/slip-springs/e1_d13_phase_a_config/manifest.json',
    '0c2df3279faf6a7457125cdc12f78c233d5d8999c6e459560edbfe1cb9a3fd3e',
    'a3677de024445816d5fa2e59dfd6e923b039442efd22f966f36876ff28879fe0',
    '8cad8e59c2ea7501655f5ea75661fb4de490aed10c9a941f925135866bc3c180',
)
print('Authenticated', len(items), 'processes; no scientific acceptance')
PY
```

The accepted analysis command was:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 /usr/bin/python3 /tmp/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d13_phase_a_analysis.py --campaign /tmp/e1-d13-phase-a-authorized-20261021-v1/campaign --manifest /tmp/UAMMD_KG-slip-springs-dev/examples/slip-springs/e1_d13_phase_a_config/manifest.json --manifest-sha256 0c2df3279faf6a7457125cdc12f78c233d5d8999c6e459560edbfe1cb9a3fd3e --approval-sha256 a3677de024445816d5fa2e59dfd6e923b039442efd22f966f36876ff28879fe0 --completion-sha256 8cad8e59c2ea7501655f5ea75661fb4de490aed10c9a941f925135866bc3c180 --output /tmp/e1-d13-phase-a-authorized-20261021-v1/analysis.json
```

Its output already exists and is preserved; the adapter refuses overwrite. For an independently
requested repeat analysis only, select a new analysis output, never a new simulation root. No new
unit or technical simulation suite was run in this execution task: verification used the actual
eight-process campaign, full independent raw/observer/cohort authentication, direct byte checks,
the accepted analysis adapter and arithmetic/resource/preservation checks. Final inventory checks
confirmed all 174 campaign files and all 194 bundle files unchanged; 73 frozen scientific/source,
tool, configuration and authority files remained byte-identical to starting HEAD. The accepted
scientific source checkout remains clean. No failures remain.
