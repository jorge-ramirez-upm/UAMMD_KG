# E1 D1.6 v1 — evidence, runtime and storage planning

**PROPOSALS ONLY. No new limit or execution is approved by this document.**
No tests, compilation, preflight, draws, trajectories or analysis process ran.
Recorded JSON/text evidence was inspected read-only. All projections below are
arithmetic planning statements, not fresh benchmarks or confidence bounds.
See [scientific design](E1_STAGE_D16_SCIENTIFIC_DESIGN_V1.md) and
[reference procedure](E1_STAGE_D16_REFERENCE_MOMENTS_V1.md).

## 1. Existing evidence and provenance limits

The following evidence exists on this workstation outside Git:

    /home/jramirez/UAMMD_KG-evidence/d15/readiness-35puhn4y/
    /home/jramirez/UAMMD_KG-evidence/d15/pilot-readiness-07m0opzd/

For short names below these are BROOT and PROOT. Inspected reports are
`BROOT/benchmark-summary-20261022T143913608820Z.json` and
`PROOT/pilot-summary-20261022T152928477645Z.json`, their receipts, launch/result
records, pilot campaign ledger and recorded output serialization statistics.
The user reports prior authenticated execution and performance review.
This task **did not** independently rerun the authentication closure, raw-file
hashing or scientific analyses. Identities below are those recorded in the
saved receipts/sidecars, not newly verified digests.

| Evidence | Recorded SHA256 |
|---|---|
| Benchmark summary, 37126 bytes | `9509353bc78c0d5c9f45f1b73e71de98935b94af504e577a90671a4c57b88b1c` |
| Pilot summary, 37190 bytes | `1448d5e83d0d5f52f0b730ffadbdb3ad0ecfc1d433fe4ace85ddcbeea7c5fb83` |
| Benchmark return archive | `4446bc2ac99fb13acdc1506037c44c46dd6f141d97582d105c064445c2d268d5` |
| Pilot return archive | `7802d45f6f3d83d0126e68826cb8137c5144cdfb0f839750cc235479042f5586` |
| Benchmark approval | `2f3499e55e6e39a14b9c13519aa7cb75a653795632af82951323d792f148c646` |
| Benchmark completion | `a55b694877e84decfa59d34598bc3bf6dfed3af61c4cb99ab34c3ea6fef57159` |
| Pilot approval | `02504cdc46db290c582d1298aa93a686b7b8bd025900b886091859de1b40d97e` |
| Pilot completion | `0adc4422462290c8aa97ef7f67cb28284da85767db4a5283b510730295fd430d` |
| Pilot build receipt | `0f072df0eb5363595b4835f70a027d2c30abd5afd9cf6bf09e985ef687e8833e` |
| Pilot recorded environment | `05e9f076948c5d562925dd24b9d9d47bc8611698516efea13808029ad5d8c79a` |

The accepted scientific source remains
`0dea651b58171a72206774bcebb2f4c74960069b`; pilot preparation was
`0ad8fbdda55318e04c835bc02a012708a4ed04de`.
Recorded host: RTX3060Ti, 8 GiB, compute8.6,
UUID `GPU-83d1eede-bd03-c365-6f3a-b6d6e2be6274`, CUDA runtime13000,
driver580.178.04, Linux/x86_64, Python3.10.12, NumPy2.2.4, double precision.
This is not a live machine preflight or portability claim.

Before future resource approval, the user can reauthenticate existing evidence
with these **local postprocessing-only** commands (not executed here):

```bash
python3 /home/jramirez/UAMMD_KG-evidence/d15/readiness-35puhn4y/preparation/examples/slip-springs/e1_d15_local.py summarize \
  --root /home/jramirez/UAMMD_KG-evidence/d15/readiness-35puhn4y
python3 /home/jramirez/UAMMD_KG-evidence/d15/pilot-readiness-07m0opzd/preparation/examples/slip-springs/e1_d15_local.py summarize \
  --root /home/jramirez/UAMMD_KG-evidence/d15/pilot-readiness-07m0opzd
```

These use captured trusted approval/completion identities, create new reports/
compact packets, and do not simulate. Preserve original absolute paths and full
evidence. If these roots are unavailable on another host, consume the matching
reviewed return archives plus externally trusted SHAs first, then restore/access
the complete raw cohorts, reviews, source/build dependency closure and receipts.
A compact packet does not replace full raw authentication. Do not substitute
old M64 projections for absent M256 measurements. No D1.4 scientific/IAT result
is assumed available.

## 2. Recorded M256 timings and resources

All rows have N32,Z2048,Ne4,A2=5,nu100,kb30; one independent run per cell.
Seconds below are rounded from the saved reports. These are measurements,
not model predictions or equilibrium results.

| T | kappa | dt | Integration s | Production s | Supervised child s | E1 exclusive s |
|---:|---:|---:|---:|---:|---:|---:|
| .1 | 0 | .0001 | .125453 | .211403 | .406487 | .075698 |
| .1 | 0 | .00025 | .086073 | .170067 | .357982 | .075926 |
| .1 | 10 | .0001 | .156459 | .246676 | .513308 | .079963 |
| .1 | 10 | .00025 | .107701 | .195786 | .464005 | .080044 |
| 1 | 0 | .0001 | 1.276799 | 1.395845 | 1.622280 | .074648 |
| 1 | 0 | .00025 | .884097 | .981252 | 1.224262 | .074854 |
| 1 | 10 | .0001 | 1.553867 | 1.676938 | 1.888813 | .078807 |
| 1 | 10 | .00025 | .984952 | 1.086134 | 1.281738 | .079025 |

T1 integration ns/bead/step, in the same cell order: 15.113623,26.162921,
18.393316,29.147482. Recorded bead updates/s: approximately66.17,38.22,54.37,
34.31 million respectively. Fine/coarse per-step rates differ because expected
serial events per step differ; compare physical-time cost as well.

T1 initialization was .118220–.158646s, final output .016692–.017954s;
child minus production was about .196–.243s, including startup/initialization/
final output/exit/supervision. It is not an extra cost to add after already
including those components. E1 wall was .081180–.085450s; its transfer subset
was .000653–.000683s. Legacy observation was .007415–.007503s and recurrent
legacy output .000156–.000167s. Observer wall, exclusive, transfer, production
and integration timers have nested/different scopes and are not additive.

Source scope: integration CUDA events include forces, EM update, serial hopping,
invariants, diagnostic D2H and host launch/synchronization gaps, not just a GPU
arithmetic kernel. Production includes initial observation and all recurrent
observation/output plus final force check; excludes initialization and final
data writing. E1 exclusive includes its own serialization/flush work; E1 wall
also covers shared position readback/legacy reductions. P-I is an unpartitioned
gap, not a separately measured “CPU overhead kernel”. Authentication/build/
reference/postprocessing costs lie outside the child simulation timers.

T1 measured peak host RSS was108306432–108765184 bytes (~103.3–103.7 MiB).
Explicit device arrays were1214044 flexible /1214308 stiff bytes, not GPU peak.
For recorded pilot cell3, before/after free GPU was8072724480 bytes, available
host31498440704 bytes, disk1246835855360 bytes before execution. GPU peak is
null; whole-device free memory is not process-specific peak allocation.

T1 output per cell: 9488501,9783123,9434217,9736557 bytes; total38442398.
T.1 total was39697042 bytes. Similar tiny-run output despite tenfold duration
reflects fixed audits/endpoints and text widths, not a storage rate per unit
time. Do not multiply total T1 output by100 to project T100.

## 3. T100 runtime projections and uncertainty

The central integration work proxy is 100 times each T1 integration time at
M256. The simple gross production proxy is 100 times T1 production time.
For larger M multiply by q=M/256. This assumes unchanged per-step/event costs,
host load and hardware; scaling in M is **unverified**. The gross proxy also
over-repeats fixed observations: target full frames56 versus7, scalar201 versus3,
audits4 versus4. It is a transparent planning proxy, not a fitted component
model, guaranteed upper bound or confidence interval.

| M | Integration s/run: k0 fine / coarse | Integration s/run: k10 fine / coarse | 16-run integration proxy | 16-run gross production proxy |
|---:|---|---|---:|---:|
| 256 | 127.7 / 88.4 | 155.4 / 98.5 | 31.3 min | 34.3 min |
| 512 | 255.4 / 176.8 | 310.8 / 197.0 | 62.7 min | 68.5 min |
| 1024 | 510.7 / 353.6 | 621.5 / 394.0 | 125.3 min | 137.1 min |

Each cohort has 8 fine and8 coarse runs, four replicas/cell. At M256 the gross
per-run production proxies are139.6,98.1,167.7,108.6s in cell order.
Even the central fine-run costs exceed the currently approved120-second cap.
The gross whole-cohort M256 proxy is about2056s before new provenance/analysis
costs; it does not promise completion below3600s.

A better future local budget worksheet must consume authenticated per-cell
metadata and row serialization and keep terms separate:

    T_child approximately T_startup + T_integration(M,T,dt)
              + T_legacy_observations + T_E1_exclusive
              + T_recurrent_writes + T_final_output + residual.

Do not add measured E1 wall or transfer again when already within other terms.
Seven pilot full frames include four expensive audits, so simply multiplying
exclusive_seconds by56/7 is not a validated long-run observation model. Keep
actual56 full/206 union frames, four audits and projected rows/bytes explicit;
include filesystem bandwidth/flush variability and separate authentication time.
No counterfactual observer-off pilot exists for causal overhead attribution.
One run/cell cannot give performance replicate uncertainty. Suggested safety
factors in section6 are operational proposals, not empirical quantiles.

## 4. Storage from actual schemas and D1.5 row measurements

The saved T1 report provides per-file rows, data_bytes, mean_row_bytes, headers
and SHA256. In cell3, selected observed means are samples213.583333,
backbone197.216406, sites24.620739, connectors104.793736, chains98.665179,
tangents58.932478, positions72.164329, attachments85.432617 bytes/row.
These are actual M256 serialization observations, not M64 proxies. They differ
by stiffness, timestep/time text and cell. Use each cell's own calibration for
an empirical worksheet and preserve its uncertainty; do not call observed mean
row width a maximum or an output quota.

At T100 and M256 the exact row counts (headers excluded) remain:

| File/group | Rows/run |
|---|---:|
| samples | 51456 |
| supplemental backbone | 1280 |
| tangents / chain populations | 14336 each |
| sites / connectors | 473088 /114688 |
| event intervals | 56 |
| audit positions / attachments | 33792 /8192 |
| initial / final positions | 8448 each |
| initial / final / fixed spring files | 2048 each |
| initial bonds / final bond-statistics | 8192 each |

All counts scale with M except the56 event rows. Intermediate audit placement
does not change counts or the numeric-width envelope; empirical text widths
can change. Initial/final, fixed-spring and bond-histogram files are not omitted.

For any planning alternative below let S=2T+1 be scalar frames,
F=floor(T/2)+1+1[T is not a multiple of2]+5 full frames, and E=5 supplemental
non-scalar full frames. All listed T are multiples of.5. With four audits,
N32,Z=8M and unchanged schema, the 24-character finite-float /20-character
integer envelope inherited from D1.5 is exactly

    CSV_envelope(M,T) = 948 + M*(67550 + 292E +342S +5574F) +323F bytes.

The948 bytes are all16 CSV headers. Per-row widths include commas/newlines;
323 is the event row,342 sample,292 supplemental backbone, and
5574=117 tangents +188 populations +33*109 sites +8*209 connectors.
The67550 term retains all four audits and mandatory legacy endpoints/bond tables.
This is a source-format envelope for finite values under the accepted numeric
format, not a measured size; JSON/log/provenance allowances are additional.

| M, T100,R4/cell | M256 cell3 observed-width proxy CSV/run | Width-envelope CSV/run | 16-run width-envelope CSV |
|---|---:|---:|---:|
| 256 | ~40.96 MiB | 115192412 bytes (109.86 MiB) | 1843078592 bytes |
| 512 | ~81.91 MiB | 230365788 bytes (219.69 MiB) | 3685852608 bytes |
| 1024 | ~163.81 MiB | 460712540 bytes (439.37 MiB) | 7371400640 bytes |

The empirical example follows the actual cell3 data: total T1 CSV9430417
bytes, samples data164032 bytes/3 frames and the combined five recurrent E1
tables3241180 data bytes/7 frames. Hence T100 at the same observed widths is
9430417+66*164032+7*3241180=42944789 bytes at M256. With948 header bytes and
3760 event-data bytes, the corresponding M scaling proxy is
(M/256)*42940081+4708. Time/step digit growth, larger IDs and coordinates mean
this constant-width proxy is **not an exact future file size**. The envelope
and separately approved output limit protect against that uncertainty. The
old committed M64-calibrated empirical numbers are not used as new measurements.

All equal-chain-time allocation options have explicit envelopes:

| Scientific option | S / F per run | Runs | CSV envelope/run bytes | CSV envelope/cohort bytes |
|---|---|---:|---:|---:|
| A M256,R4,T100 | 201 /56 | 16 | 115192412 | 1843078592 |
| B M256,R8,T50 | 101 /31 | 32 | 70755537 | 2264177184 |
| C M512,R4,T50 | 101 /31 | 16 | 141500113 | 2264001808 |
| D M1024,R4,T25 | 51 /19 | 16 | 196981677 | 3151706832 |
| E M256,R16,T25 | 51 /19 | 64 | 49250733 | 3152046912 |
| F M512,R4,T100 | 201 /56 | 16 | 230365788 | 3685852608 |
| G M1024,R4,T100 | 201 /56 | 16 | 460712540 | 7371400640 |

Add a planning allowance of2 MiB/run for JSON/logs/receipts and64 MiB/cohort
for shared build/provenance, separately from any raw backup, references and
analysis cache. These are allowances, not measured maxima or automatic approval.
No compression ratio is assumed. More replicas repeat expensive endpoints and
audits; equal chain-time does not imply equal storage.

If a later review requests extra full frames, each adds5574M+323 envelope bytes,
plus292M when not already on the scalar grid. Quantify this scientific benefit/
storage trade before changing cadence. Baseline counts retain all chain-resolved
records and joint associations; the current final-half bond histogram alone
cannot replace a time-resolved chain record or diagnose drift.

## 5. Work, synchronization, memory and fixed guards

| M | Beads / Z | Attempts expected per T100 run | Fine / coarse bead updates/run | Explicit stiff device bytes | Legacy workspace estimate bytes |
|---:|---|---:|---|---:|---:|
| 256 | 8448 /2048 | 20480000 | 8448000000 /3379200000 | 1214308 | 11652184 |
| 512 | 16896 /4096 | 40960000 | 16896000000 /6758400000 | 2427748 | 23304280 |
| 1024 | 33792 /8192 | 81920000 | 33792000000 /13516800000 | 4854628 | 46608472 |

These are operation/allocation counts, not additional measurements. At fixed N,
bead-owned stretch/bend/slip-force and ping-pong EM work are O(33M). There are
33/66/132 blocks at256 threads. Serial `slip_renewal::hopping<<<1,1>>>` performs
Poisson attempts with replacement, O(K+1) random-arrival generation and serial
updates. Mean K at fine/coarse is20.48/51.2,40.96/102.4,81.92/204.8. More M
does not parallelize this thread. End renewal scans at most33 destination-chain
sites, not all M chains. Occupancy/order/stable-ID invariants remain mandatory.

The accepted driver runs parallel state checks and three small diagnostic D2H
reads every active step, then synchronizes a stop event. At T100 there are1e6
fine or4e5 coarse event waits and3e6 or1.2e6 diagnostic readbacks per run.
The small byte volume does not remove latency. Position observation copies at
206 union frames total55689216 bytes at M256; full E1 adds22541120 bytes at56
frames. Larger M scales these bytes, except the88 counter bytes per full frame.
CPU reductions/slot copying/text formatting and synchronous frame flushes also
grow. Actual cost fractions are unprofiled; do not optimize or thin checks here.

Guard review: maxMean10000 and maxEvents100000/batch remain hard failures with
no clipping. M1024 coarse mean204.8 is below the mean guard, but does not waive
draw/RNG retry bounds. Signed site/diagnostic keys require L<=(INT_MAX-8)/8;
M1024 is far below that. Steps/counters are uint64, with the existing
floor(UINT64_MAX/8) BD-step limit. T100 and its expected counts are far below
these limits; explicit overflow guards remain. No fixed M1024 chain cap was
found in this E1 path. The Rouse CPU-worker1024 cap is unrelated to E1 chains.

Explicit stiff device storage is132L+48Z+16N+8m+92; flexible uses264 fewer
bytes. Legacy workspace is1356L+96Z+88 and observer vectors40(M+Z)+8L.
They exclude CUDA context, allocator/library temporaries and host parsing/
formatting. Do not sum overlapping estimates into a claimed measured peak.
No M512/M1024 RSS/GPU-peak measurement exists. Future analysis must stream one
replica/frame at a time; do not load every raw CSV into an object-heavy table.

## 6. Proposed limits for a future T100,R4 protocol

These **unapproved** proposals apply separately to A,F,G, not their union.
They use roughly three times the worst gross production proxy plus fixed-cost
room, with additional cohort room for authentication. This is a conservative
operational choice, not a probability bound or assurance of completion.

| Budget | A M256 | F M512 | G M1024 |
|---|---:|---:|---:|
| Per-run wall maximum | 600 s | 1200 s | 2400 s |
| Aggregate wall maximum incl supervision/authentication | 14400 s | 28800 s | 57600 s |
| Child host RSS maximum | 2 GiB | 2 GiB | 2 GiB |
| Available host RAM minimum | 8 GiB | 8 GiB | 8 GiB |
| GPU free-memory minimum | 4 GiB | 4 GiB | 4 GiB |
| Output maximum/run | 256 MiB | 512 MiB | 1 GiB |
| Output maximum/cohort | 4 GiB | 8 GiB | 16 GiB |
| Free disk minimum | 10 GiB | 20 GiB | 40 GiB |

Retaining2 GiB child RSS is a proposed ceiling, not a claim of linear RSS
scaling or that parsing a whole campaign fits. Propose a separate4 GiB analysis
RSS cap and streaming postprocessing; reference-only proposed caps are in its
own plan. Fresh measured memory/headroom must still pass before any execution.
Disk minima allow room for preserving full evidence and a backup/scratch copy;
actual filesystem quotas, free space and backup policy require operator review.
Free-space minima are floors to maintain throughout, not the total amount of
storage to provision. Initial free capacity must also cover the chosen output,
backup and scratch allowances above that floor; do not promise completion from
a preflight that has only the minimum free bytes.

The active D1.5 approval stays120s/run,3600s aggregate,128 MiB/run,1 GiB total,
2 GiB RSS,8 GiB available host,4 GiB free GPU,10 GiB disk. The frozen generic
validator additionally has120s/3600s/5 GiB operational ceilings. **Do not edit,
bypass, or silently enlarge those validators or old approvals.** A new versioned
resource amendment and separately reviewed execution protocol are prerequisites.
Scientific D0 accuracy tolerances remain unchanged by an operational amendment.
No true approval, long-run runner or executable T100 manifest is introduced.

For B–E, recompute aggregate/output limits from their run counts and table4;
the A/F/G limits cannot be copied as authorization. Before choosing those
allocations review their startup/observation cost and independent-replica value.
All future execution remains sequential, nonoverwriting, bounded, authenticated
and without automatic retries/adoption; failures are preserved and reviewed.
