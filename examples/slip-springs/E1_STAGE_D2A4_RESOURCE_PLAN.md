# D2A.4 resource and lag-support plan

Preparation only, 27 October 2026. No reduction, test, benchmark, build, GPU
query or simulation ran. Arithmetic below is planning from source behavior
and saved D2A.3 measurements, not a new performance measurement.

## Actual correlator support

Read-only source authority: `../KG/correlator.cpp:162–186` (evaluate),
`385–437` (Vector feature block means), `904–960` (Diffusion last-position
promotion), and `orientation_correlator.h:188–205` (integer support export).
Let F=100001, P=16, m=2, b=2^k and delta=100*0.0001=0.01. The raw count
for slot ell is `floor(F/b)-ell`. Fine slots are 0..15; coarse slots are
8..15, provided the count is positive. Incomplete blocks are not promoted.

L15 permits k=0..14. Level14 receives six complete samples and is the deepest
populated level; stock evaluate omits it. Level13 receives twelve samples, so
only ell=8..11 have positive counts. Levels0..12 export 16+12*8=112 bins;
level13 adds four: **116 bins total**, not 120 or 128. The configured ceiling
2457.6 is not an exported lag.

| Level / slot | Nominal lag | Origins per chain | Use |
|---|---:|---:|---|
| k0 / 1 | 0.01 | 100000 | Shortest nonzero lag |
| k0 / 15 | 0.15 | 99986 | Last fine all-origin bin |
| k10 / 15 | 153.6 | 82 | Coarse primary support |
| k11 / 8 | 163.84 | 40 | Coarse primary support |
| k11 / 9 | 184.32 | 39 | Proposed last primary bin |
| k11 / 10 | 204.8 | 38 | Beyond T/5; weak support |
| k12 / 15 | 614.4 | 9 | Weak tail |
| k13 / 8,9,10,11 | 655.36,737.28,819.2,901.12 | 4,3,2,1 | Weak tail |

Use the conservative screens `lag_steps <= steps/5` and count>=32. The longest
qualifying bin is **184.32**, integer lag_samples18432/lag_steps1843200. This
uses integer clocks to avoid floating-point boundary misclassification. Keep
all bins in output, clearly marking longer lags through **901.12** as descriptive.
These screens are not an effective sample size, fit window or terminal-relaxation
test. Correlated origins/lag bins do not become independent observations.

MSD uses direct positions retained at `(j+1)*b-1`: exact nominal displacement
lag with origins decimated every b acquisitions, phase b-1, point width one.
Orientation correlates block means of instantaneous unit/rank-two features,
without renormalizing those means. Its triangular support has half-width
`(b-1)*delta`: 20.47 at the last primary bin and 81.91 at the longest bin.
Equal nominal lag/count does not make these the same temporal estimator.

## Memory, transfer and storage arithmetic

Using the existing 64-bit Linux layout, the Vector-layout payload per owner is
`L*[P*(8*8+2*8)+5*8+3*8+2*4]`. For L15/P16 it is 20280 bytes. Nine owners
per chain (six displacement, three orientation) times 256 chains give
**46725120 bytes, about 44.6 MiB**, plus objects, IDs, offsets and scratch.
The observer preflight allows four times its steady estimate plus frame
scratch and 64 KiB. Relative to the saved L11 preflight139438592 bytes,
the extra payload is12460032 bytes, giving an ABI-dependent proposed preflight
estimate **189278720 bytes, about 180.5 MiB**. The existing **256 MiB observer
allowance** is retained; actual source preflight is authoritative. None of
these formulas measures RSS. The simulator's aggregate allocation guard is
still2 GiB; no allocation or kernel changed.

Each double real4 full-coordinate readback is `256*33*32=270336` bytes.
100001 dynamics frames require27033870336 bytes (~25.18 GiB) transfer/run,
not resident storage. Scalars at stride5000 give2001 shared frames; all eleven
full-E1 frames coincide with scalars. The other98000 frames add26492928000
bytes (~24.67 GiB) synchronous traffic. The same existing host buffer is reused.
Across twelve runs this is about302 GiB total dynamics-frame traffic, not an
on-disk trajectory or a throughput measurement. CPU consumption stays serial;
there are230402304 fine owner-input calls/run before recursive promotion.

Keep scalar cadence0.5 (2001*256=512256 scalar rows/run); sparse full context
at times0,100,...,1000 (11 frames) and two joint endpoint snapshots. Dynamic
output has29696 per-chain rows plus116 replica rows/run. A deliberately generous
1200-byte row envelope gives~34.1 MiB of curves; scalar serialization grows
approximately tenfold relative to T100, with unverified text-width effects.
Allow512 MiB/run and8 GiB aggregate, including provenance/logs. Twelve full run
allowances consume6 GiB, leaving aggregate room for shared records. Expected
raw volume is of order1–2 GiB from previous widths, not a guaranteed cap or a
compression assumption. No dense coordinate dump is introduced.

## Runtime basis and proposed limits

The saved [D2A.3 summary](E1_STAGE_D2A3_SCIENTIFIC_ANALYSIS.md#execution-record-and-current-evidence-status)
records eight T100 runs in907.242383 s, peak child RSS149196800 bytes and no
reported violations. It is execution evidence, not isolated observer timing or
authenticated scientific dynamics; full scientific authentication/reductions
remain a separate user-run stage. Rounded child-wall ranges from its records:

| Cell | T100 child wall (s), two recorded runs | Simple T1000 x10 proxy/run (s) |
|---|---|---|
| A | 59.27–59.43 | 593–594 |
| B | 135.45–135.54 | 1354–1356 |
| C | 92.48–92.61 | 925–926 |
| D | 162.56–162.58 | 1626 |

The gross cohort proxy is `907.24*(12/8)*(1000/100)`, approximately13600 s or
**3.8 hours**. It assumes comparable hardware/load and per-physical-time work.
The increased correlator depth enlarges memory/final exports; it does not
multiply every acquisition's work by15/11 because promotions are geometric.
Longer records, serialization, synchronization, filesystem and driver behavior
remain uncertainties. This proxy is neither a benchmark nor a confidence bound.
Do not add overlapping production/integration/acquisition/observation timers.
The previous RSS is a reference, not a prediction of the new peak; GPU peak
memory remains unmeasured.

| Proposed safeguard | D2A.4 value |
|---|---:|
| Per-run stage, including prelaunch checks/validation/receipt | 3600 s |
| Whole command, all12 runs and closure | 45000 s (12.5 h) |
| Maximum child RSS | 2 GiB |
| Maximum all run outputs/logs/receipt | 512 MiB/run |
| Maximum whole campaign output | 8 GiB |
| Minimum prelaunch host/cgroup headroom | 8 GiB |
| Minimum prelaunch GPU free memory | 4 GiB |
| Maintained free disk floor | 10 GiB |
| Initial free disk | 26 GiB, plus separately preserved source/build storage |

The initial allowance is10 GiB floor plus two8-GiB cohort allowances; it does
not create a backup. Serial worst-case run caps total43200 s, leaving1800 s
in the aggregate budget. No operator confirmation is required between successful
runs. A violation stops the sequence; no automatic retry, budget extension or
sampling/duration reduction is implemented.

Mechanisms are the reused Linux supervisor: process-group termination with
SIGTERM then SIGKILL, parent-death SIGKILL for the direct child, per-file
RLIMIT_FSIZE, nominal50-ms RSS/tree-size/disk polling, wait4 final peak RSS,
and final size checks. Run/whole-stage ITIMER_REAL deadlines and an outer
GNU timeout bound execution. RSS/aggregate bytes/disk are **monitored thresholds
with stop-on-violation, not hard kernel quotas**; transient overshoot and OS/I/O
latency are possible. Headroom is checked before each launch, not continuous
GPU peak measurement. Emergency evidence hashing has up to10 s after abort;
outer timeout escalates after15 s. Cleanup can extend failure-recording time
beyond the scientific deadline. No resource-safety or performance checks ran
in Codex. The operator must reserve the target GPU; advisory locks do not
control unrelated launchers racing the prelaunch compute-process query.
