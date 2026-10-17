# Stage 4A.3b.2a — scalar-output audit and implementation proposal

18 October 2026 (Europe/Madrid). Read-only audit against starting/fetched
`origin/slip-springs` SHA `12021181180156e63505cddbb71ac8d043e6248f`, initially
clean. Only this report and documentation links change. No simulation, full-data
analysis, optimization, cleanup, restart or scientific acceptance is performed.

**Recommendation:** an explicitly selected compact stress-campaign profile,
using existing stress/bond summaries plus per-chain scalar summaries, all-frame
validation/coverage records and a few scalar snapshots. Keep the original full
mode as default and preserve every stress observation. First save formatting,
disk and host parsing costs; defer changes to scalar computation cadence.

## Observed evidence and origin of the large file

The supplied directory is accessible:
`/tmp/semiflexible-readiness.oH8Vnc/campaign/single-finite-N8-k10-433201-2.5e-05`.
Inspection was restricted to directory/file existence, sizes and small JSON
metadata. No scalar CSV was scanned, sampled, hashed, modified or validated.

* `samples.csv`: **9,876,334,033 bytes**, 9.876 decimal GB (9.198 GiB).
* All files inside that run directory: 9,883,291,389 bytes; everything except
  samples.csv totals only **6,957,356 bytes**.
* Matching zero-step diagnostic directory: **6,018,884 bytes**, about5.74 MiB;
  its samples.csv is384,555 bytes and stress_tensors.csv1,155,721 bytes.
  These stat measurements refine the user-reported approximate9.88GB/5.8MB.

There is a completion discrepancy to preserve, not repair: simulator metadata
reports8,000,000 updates, physical time200 and20,001 stress frames; final.csv,
stress summaries and correlations exist. The execution receipt nevertheless
says `status=failed`, child `exit_code=0`, blank error and wall972.894s. The
simulator reports production462.338s. This does NOT establish a complete or
scientifically passing run. Source ordering is consistent with an interruption
in post-child validation, but metadata does not prove that diagnosis or the
integrity/row count of the large CSV. Treat the interrupted workflow as evidence;
never automatically adopt, resume, truncate, delete or overwrite it.

The exact producer is [simulate/observe](semiflexible.cu#L261); the consumer
is [validate_run](tests/semiflexible_stress_analysis.py#L331). Stress bookkeeping
is separate in [Correlations](semiflexible_stress_stream.h#L49):

1. Call `stressObserver->sample(current,step)`; this already performs GPU stress
   evaluation and transfers six channels per chain to the correlator.
2. Independently copy ALL bead coordinates to the host, compute conformational
   scalars, format17-significant-digit CSV and append one row per chain.
3. Call observe at step0 and every `--sample` steps, then flush the streams.

For C chains, S steps and stride s, F=floor(S/s)+1. Here C=2048,S=8,000,000,
s=400,F=20,001, so **40,962,048 planned scalar rows**. With N8 there are14 columns,
including four tangent correlations. The measured file size divided by the
metadata-reported planned row count is241.109 bytes/row. This is a planning
conversion, not an independently counted row length. The large output is
conformational CSV, not a retained stress history or multi-tau buffer.

## Complete output/dependency map

Notation: N bonds,C chains,F scheduled frames,Fh final-half frames,
K selected scalar times,B exported correlation bins,L levels,p slots.
Storage orders below count textual values; actual CSV bytes depend on numeric
width. Length units are reduced length l, time reduced time, energy E=kBT units
with configurable kBT; no physical volume is assigned. "Required" means the
current Stage4A.3b.1 analyzer/runner, not necessarily a scientific necessity.

| File | Producer; content/units | Writes and size scaling | Current use, redundancy and preservation |
| --- | --- | --- | --- |
| parameters.txt | simulate; N,b0[l],kb[E/l²],bead-indexed kappa[E] | Once before production; O(N) | validate_run checks rounded arrays/indexing; reproducibility, not a restart checkpoint. Keep. |
| initial.csv | positionsFile; chain,bead,xyz[l] | Once; O(C(N+1)) | Independent tensor reference, initial conditions and bond check. Keep. |
| final.csv | positionsFile; xyz[l] | Finalization; O(C(N+1)) | Completion/finiteness/IDs; zero-step equality and debugging. Keep. No implemented trajectory restart. |
| initial_bonds.csv | observe(0); bond lengths[l] | Once; CN rows | validate_run checks against initial.csv; redundant geometrically but small and useful. Keep. |
| samples.csv | observe; field map below | CF rows, O(CF[10+min(4,N-1)]); append/flush each frame | Mandatory structural/finiteness scan today; almost all numerical values unused by Stage4A.3c science. Main reduction target. |
| bond_statistics.csv | simulate finalization; per-chain/bond final-half mean r[l],mean r²[l²],Fh and33 histogram counts | CN rows once; O(35CN) values | Count/histogram/finiteness checks in validate_run; already sufficient for radial moments/CDF without history. Keep. |
| stress_moments.csv | Correlations::received/write; per-chain final-half six means[E],36 raw products[E²],Fh | Updated every stress frame in final half; C rows once | Actual equilibrium mean/product, timestep and replica gates. Keep exactly; scalar CSV is not its source. |
| stress_correlations_raw.csv | Bank::write via Correlations::write | Once; O(B), B bounded by Lp | Raw six product means/cluster SE[E²],H[E²] under legacy g name, lag times/counts. Analyzer cross-checks normalized file; small duplicate intentionally retained. |
| stress_correlations.csv | Correlations::write | Once; O(B) | Same correlations plus H,g=H/(kBT)² and optional G=n_chain*H/kBT[E/l³]. Gaussian, direct, timestep/replica and terminal gates use this. Keep all bins/counts/SE. |
| metadata.json | simulate finalization | Once; O(1) fields | Model,precision,seed,steps,rounded noise/drift,capacity,minimum sampled bond and measured timers. Required. |
| stress_metadata.json | Observer::write | Once; O(1) fields | F,Fh,spacing,workers,batch,capacity/launches,normalization and timings. Required, especially zero-bending proof. |
| stress_samples.csv, optional | Correlations::received when --stress-dump1 | CF rows of six channels[E]; O(6CF) | Required for all54 frozen C64,F8193 direct-reference runs. Absent in the main pilot. Never decimate these reference sequences. |
| stress_tensors.csv, diagnostic mode only | Observer::sample | 3CF rows, nine raw W entries[E]/term | Separate stretching/bending/total checks and independent initial stress statistics. Frozen zero-step diagnostics have F=1. Keep unchanged. |
| forces.csv, force-input mode only | simulate force readback | C(N+1) rows once; force[E/l],assigned energy[E] | Bounded prescribed-force diagnostics; not ordinary streaming, and force-only+stream is rejected. Keep. |
| failure.json,failure_positions.csv,failure_proposal.csv | force/update diagnose | First detected failure; O(1)+up to two O(CN) snapshots | Step/bead/reason and old/proposed positions. Fatal evidence, never suppress. |
| stress_failure.json,stress_failure_positions.csv | Observer::failure | First detected stress failure; O(1)+O(CN) | Fatal virial/geometry evidence. Keep. |

The frozen diagnostic uses `--steps0`, not force-input mode: it also writes one
ordinary scalar frame and bond summaries. Prescribed force-input diagnostics
have different header-only scalar behavior; do not merge these schemas.

Runner outputs beside the run directory are `<run>.log` (stdout/stderr, normally
O(1)), `.time` (resource summary,KiB/seconds,O(1)), `.execution.json` (command,
hashes,times,status and completion inventory), `.monitor.csv` (elapsed seconds,
process-tree RSS KiB,production flag), `.gpu.csv` (whole-device MiB and flag),
and `.disk.csv` (elapsed seconds,scalar/output bytes). Monitoring is approximately
one observation per wall-second, O(wall duration), independent of stress stride.
memory_observation uses time/RSS/GPU records; pilot_report uses disk monitoring;
provenance_checks uses receipts. Preserve them, with explicit missing/support
statuses. Receipt inventory size scales with the number of files, not frames.

Campaign-level inputs/proofs are manifest.json,parameter inputs,command scripts,
validation-plan.md,PLAN_SHA256,executable/environment provenance and optional
compiler transcript. Host tools additionally write bounded-test logs/receipts,
equilibrium-references.json,analysis-checkpoint.json,scientific-analysis.json,
scientific-summary.txt,pilot-readiness.json and latest readiness-refusal.json,
plus lock files. They are not simulator histories. Size scales with the fixed
run/model counts and bins. Keep their integrity/version handling. Analysis
checkpoints resume analysis only. **There is no supported integration/correlation
restart checkpoint**: final positions and counter-RNG seed/step information do
not include the persistent correlator bank, scalar accumulators or a resume CLI.

## samples.csv: exact field consumers and sufficient replacements

All fields are required by validate_run's exact CSV schema and parsed for
finiteness. No other Stage4A.3c function reads these scalar rows. In particular,
campaign_comparisons uses stress_moments and correlation tables, not samples.csv.

| Fields | Additional current Stage4A.3c dependency | Evidence-preserving treatment proposed |
| --- | --- | --- |
| step,time,chain | Exact frame/chain order/count, time=step*dt | Keep every stress observation; replace redundant scalar identifiers with explicit scheduled-step coverage, per-chain counts and expected/observed first/last steps. Validate selected records separately. |
| mean_r,mean_r2 | No numerical acceptance gate beyond finiteness | Final-half chain averages are reconstructible from per-bond bond_statistics using identical Fh. Keep that file; no new duplicate sums needed. |
| re2,rg2 | No numerical Stage4A.3c gate beyond finiteness | Optional final-half sums/count per chain preserve their ensemble time-average/cluster SE exactly mathematically. Initial values from initial.csv or selected step0. |
| cm_msd,monomer_msd | No diffusion/MSD gate in the frozen Stage4A.3c plan/analyzer | Selected times suffice for specifically selected-time checks only. Keep full mode for Stage4A.2 and any all-time MSD analysis. |
| min_length | Require >0 each row; global minimum must agree with metadata | Keep all-old-frame/per-chain minima, counts and failure/finite status; derive exactly the same global minimum. Selected-time minima alone are insufficient. |
| tangent1..min(4,N-1) | No numerical Stage4A.3c gate beyond finiteness | Optional per-chain final-half sums/count preserve existing static mean tests; do not average only selected frames. |

Keep distinctions explicit:

* **Every stress frame:** six raw total-virial channels must still enter the
  unchanged bank, including initial frame, last scheduled frame and partial
  final CPU batch. Main streams need not serialize those channels; reference
  runs must. Correlations include all frames; stress moments only the original
  final half. Stress total/cross terms, cluster SE and thermal/density factors
  already survive without scalar CSV.
* **Online sufficient statistics:** retain per-chain final-half sums/counts,
  not an ensemble mean alone. Across-chain SE uses the variance of chain means,
  not within-chain fluctuations or the number of time origins. Keep Fh defined
  by integer step>=floor(S/2), including exact endpoints. Preserve radial
  histograms/bond identities and per-frame finite/degeneracy decisions.
* **Selected times:** optional full scalar rows at0,T/4,T/2,3T/4,T give modest
  diagnostic context. These are all scheduled frames for the frozen examples;
  record actual steps/times, never fabricate an off-grid observation. They do
  not reconstruct arbitrary dynamic curves or diffusion fits.
* **Earlier acceptance is different:** tests/semiflexible_host.py (Stage4A.2)
  uses initial/final-half dimensions/tangents, COM at0.02,0.1,1,5,20,50 when in
  range, and Gaussian monomer/COM MSD at every recorded Gaussian time. Five
  snapshots are NOT equivalent to that suite. Preserve its original full
  behavior and tests; do not present compact Stage4A.3c as a replacement.

For mathematical equality of a per-chain mean, store sum_t x_ct and count_t on
exactly the same frame set; SE is then computed across these C means. Existing
bond summaries similarly commute with averaging over bonds. CSV17-digit values
round-trip doubles, but online summation and NumPy reduction may differ by
roundoff: validate this explicitly without relaxing scientific thresholds.
All-frame finiteness and min checks can become compact status/min summaries
only if the same original scalar arithmetic/geometry is still evaluated on
all original frames. This changes the structural evidence representation;
it does not provide lossless recovery of omitted scalar history or byte-identical
independent enumeration of the old CSV. Producer/reader equivalence tests and
file-integrity proofs must replace that mechanical row scan, not delete it
without replacement.

Exact Gaussian EM stress predictions use metadata rounded drift/noise,F,stride
and exported lag/block counts. Direct comparisons use stress_samples.csv;
terminal support uses H,H_se,pairs and block widths. None uses COM,monomer,
tangent,Re² orRg² histories. Numerical safety still requires per-step accepted
force/update diagnostics, every-stress-frame tensor diagnostics and the original
scalar finite/min audit. Initial tensor means/covariances remain in diagnostic
runs, independently of all final-half summaries.

## Alternatives and quantitative estimates

Decimal MB/GB below; estimates assume C2048 and the metadata-referenced241.109
bytes/scalar row. N32,T4000,stress spacing0.01 has F400001 and819,202,048 rows
at every frozen dt (40/80/160 million steps). Its scalar file would be about
**197.52GB**. Numeric widths/model/precision differ; these are planning estimates,
not completed N32 measurements. The162 main streams total49,103,179,776 planned
rows: roughly11.84TB at this conversion, excluding other outputs. N1 rows have
fewer columns, so a uniform conversion is approximate.

Fixed non-scalar files measured6.96MB for the pilot. Scaling snapshots with N+1,
bond summaries with N and correlation rows with B gives about21.6MB for N32;
this is an estimate. B is about179 versus248 here, bounded by Lp. Existing
histogram count widths vary weakly with Fh.

| Proposed profile | Pilot scalar frames/rows retained | Pilot total in-directory disk | N32,T4000 total disk | Lost information |
| --- | --- | ---: | ---: | --- |
| Current full | 20001 frames,40,962,048 rows | 9.883GB measured | ~197.54GB estimated | None relative to present output |
| A: compact online summaries + coverage | No history; per-chain final-half Re²,Rg²,tangent sums and existing bond/stress files | ~8MB | ~23MB | Scalar time evolution/post-hoc arbitrary-time tests; frozen stress gates preserved |
| B: independently write every100th old scalar frame | 201 frames,411,648 rows | ~0.107GB | ~2.00GB (4001 frames) | Intermediate scalar records; selected-only averages are not original final-half averages |
| Recommended hybrid: A plus five selected scalar frames | 10240 rows in either system | ~11MB | ~26MB | Intermediate scalar history only; original-frame summary statistics retained |

For B, scalar physical spacing is1 rather than stress spacing0.01; stress
stride remains400 in the pilot. Even a10x write reduction leaves~0.995GB/
19.77GB in the two cases. B's100x reduction is illustrative, not a new frozen
sampling prescription. Force a final selected record only at an explicitly
scheduled step; do not invent an extra stress frame.

**Memory and work:** all profiles keep the existing GPU allocations and
correlator architecture; incremental GPU memory is **zero**. Pilot metadata
reports1,146,992 combined integration/stress GPU bytes (~1.094MiB), excluding
CUDA context/allocator overhead. N32's analogous allocation is~3.51MB. The
stress/bank/batch estimate is252,444,680 bytes (~240.75MiB) in either system at
fixed C,L,p,batch; it includes host storage and is not device RSS. Bond
accumulators already cost C*N*(2*8+33*8):4.375MiB/17.5MiB. Do not add overlapping
workspace estimates as measured resident memory.

A/hybrid needs at most C*(6 double sums + count + minimum), **128KiB** extra
host state for N8/N32, plus small coverage flags/hash state and one output
frame buffer, not a history. The six sums are Re²,Rg² and four tangents; bond
means already exist. B with writer thinning alone needs only small coverage/min
state, about32KiB before optional checks. B also needs A's sums if the original
final-half static estimates are to remain available exactly. Stream selected
rows immediately rather than retaining K frames in memory.

For the first implementation, all old scalar geometry/D2H/finite checks and
bond histograms remain at every old frame. This bounds scientific risk but saves
formatting and writes, not all observation computation. Single-precision full
coordinate transfers remain294,912 bytes/frame (pilot) and1,081,344 (N32), plus
unchanged98,304 stress-channel bytes/frame. A adds O(6C) host additions per final-
half frame; formatting falls from CF rows to O(C+CK). Pure B writer thinning has
similar savings without these extra sums. Actual host overhead/speedup is
unmeasured. Metadata reports124.021s observation work (including formatting),
3.001s recurrent writes and462.338s production; buffered write time is not a
full durability/disk-cost measure. Do not sum overlapping diagnostic/GPU timers.

A more aggressive B that skips scalar computation/readback can save CPU/D2H,
but would also change final-half bond statistics and finite/min coverage unless
those remain at original cadence. Even unused derived scalars can overflow when
coordinates are finite. That variant is not evidence-equivalent by assumption;
it requires a separately justified protocol decision. It is not recommended
for the first change.

## Frozen-plan classification and proposed implementation scope

This is **an output-schema change requiring analyzer compatibility**, with
unchanged mathematical stress gates, not a transparent operational switch:
current validate_run mandates every scalar row, authentication pins source and
exact commands, and the plan explicitly discusses existing scalar output.
A lossless file-compression transport could be purely operational scientifically,
but its achievable compression ratio is unknown and parsing still scales with
CF; no compressor benchmark is authorized here. It is not a substitute for
reviewing which evidence is actually needed.

Before implementation/execution, propose a separately versioned
`STAGE4A3C_OUTPUT_SCHEMA_V1.md` operational addendum and derived output-profile
manifest. Preserve the original plan/hash,282 commands, prior schema and results.
The addendum would specify the following only; it is **not applied by this audit**:

1. Explicit opt-in full/compact scalar profile for stress-stream mode, full as
   default; never reinterpret --sample, change stress scheduling, or use a hidden
   environment variable to alter frozen commands. Preserve diagnostic/reference
   runs in full form initially, including all54 stress-dump reference sequences.
2. Compact summary/coverage/selected-row schemas, units, windows, exact original
   frame sets, finite checks, per-chain identities and absence/error semantics.
   Maintain all stress/bond summaries and failure snapshots. Use counters and
   scheduled-step coverage proofs; a bare "passed" flag is insufficient evidence.
3. Keep scientific arguments bit-for-bit; a derived execution manifest maps
   parent run IDs/hashes to new binaries, explicit output flags and schemas.
   Do not mutate original commands or silently make old authentication accept
   different source/binaries. Separate caches/receipts by version/profile.
4. Analyzer compatibility reads either the original complete CSV or the new
   authenticated coverage+summary schema, reproducing all frozen numerical gates
   with unchanged thresholds. No success fallback for missing legacy files.
   Update runner completion validation, per-file identities, disk estimates and
   production-observed monitoring: today that flag relies on nonempty samples.csv.
   Record child/validation/hash lifecycle stages and exception class explicitly,
   so a successful child with interrupted postprocessing is distinguishable.
5. Preserve timing scopes, report profile/schema and separate scalar compute,
   formatting/output and validation/hash costs. Compare short/long memory runs
   with identical profiles. Never merge performance claims across output modes.

Required future edits would be host portions of semiflexible.cu (output policy,
accumulators,coverage), host analysis/runner compatibility, explicit versioned
campaign-profile preparation and new bounded tests/docs. No force/update/RNG,
GPU virial kernel, multi-tau estimator, normalization, Rouse or Stage4A.2 default
change is needed. Existing per-step and zero-bending fast paths stay intact.
No compact reconstruction of the old raw history is claimed.

No scientific-protocol amendment is necessary **if** the reviewed addendum
proves exact gate/frame/window equivalence and only changes serialization and
structural validation. A scientific amendment WOULD be required to replace
original-frame final-half means with thinned-frame means, lose existing required
finite/min checks, remove direct-reference frames, alter stress cadence/lag
construction, reduce chain clustering evidence, or impose new selected-time
scientific gates. Such variants need a new plan before execution, not relaxed
thresholds. No amendment or execution overlay is authorized/applied here.

## Bounded validation and remaining uncertainties

After separate implementation authorization: compare full and compact runs
on identical initial states/seeds in both precisions, homogeneous/heterogeneous,
N1/N2/N8 and mixed/zero bending, short/odd step counts, partial scalar/stress
intervals and incomplete batches. Require unchanged trajectories, stress
channels/correlation files/moments, frame/origin grids and zero-angle counters.
Reconstruct each new per-chain summary from the bounded full CSV; compare
window endpoints, cluster SE, minima, finite failure decisions and selected-time
records within justified reduction-roundoff tolerances. Do not weaken acceptance
thresholds. Inject missing/duplicate IDs, missing coverage, invalid scalar values,
wrong minima/windows, corrupt schema/hash/profile and partial output. Reject
cross-profile cache reuse. Keep legacy full regression bytes/CLI behavior.
A bounded test can verify disk/count scaling; long performance/memory and new
scientific host execution still require separate authorization.

The runner currently calls validate_run before declaring completion, later hashes
all files, and pilot_report/analyze can perform further validation. Thus large
CSV also causes repeated O(CF) parsing/hashing, despite bounded RAM. Reducing its
evidence representation addresses that cost; no measured speedup is claimed.
The exact interruption point, actual CSV row count/completeness, achieved future
serialization size/speed, selected-time policy and review approval for the
operational addendum remain unresolved. Preserve the accessible failed receipt
and all pilot files untouched; do not "repair" status based on metadata alone.
