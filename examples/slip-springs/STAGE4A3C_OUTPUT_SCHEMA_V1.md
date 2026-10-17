# Stage 4A.3c scalar output schema V1 — operational addendum

Authorized 18 October 2026 for implementation/bounded verification, not production
execution. The original STAGE4A3C_VALIDATION_PLAN.md and 282 commands remain
immutable. This addendum changes serialization/structural evidence only; no
scientific gate, numerical threshold, physical argument or stress frame changes.

## Selection and compatibility

`--scalar-output full|compact` defaults to full. Full preserves the original
file set, headers, scalar arithmetic, cadence and numerical behavior. Compact
requires stress-mode stream and no force-only mode. It still computes every
original scalar on every original observation, with identical bond histograms,
stress kernels, six channels, moments, correlator and normalizations. It creates
no samples.csv. Existing snapshots/diagnostics and stress/bond files remain.
No omitted scalar time history is reconstructible from these summaries.

For S steps,stride s,C chains,N bonds, F=floor(S/s)+1 and
Fh=F-ceil(floor(S/2)/s). Final-half membership is step>=floor(S/2), exactly as
before. The selected set is the sorted unique integer steps j*S/4, j=0..4,
ONLY when j*S is divisible by4 and the resulting step is divisible by s.
Implement using quotient/remainder arithmetic without overflowing uint64.
T=0 gives only step0; off-grid quarters/final times are omitted, never rounded.

## Compact files (CSV doubles have 17 significant digits)

* scalar_selected.csv: the original samples.csv columns/order and units,
  only at selected steps, ascending step then chain. Headers: step,time,chain,
  mean_r,mean_r2,re2,rg2,cm_msd,monomer_msd,min_length,tangent1..min(4,N-1).
  Lengths are reduced length; squared dimensions/MSD length squared; time is
  reduced time, tangents dimensionless. Step/chain are exact identifiers.
* scalar_statistics.csv: chain,frames,finite_rows,final_half_frames,
  first_step,last_step,schedule_hash,min_length,mean_re2,mean_rg2,
  mean_tangent1..min(4,N-1),record_hash. One ascending record per chain. Means are double
  sequential sums over the ORIGINAL final-half observations divided by Fh.
  min_length is over ALL F observations, not only the final half/selected set.
* scalar_metadata.json: profile="compact",schema="scalar-output-v1",
  schema_sha256 (hash of this document), chains,springs,steps,stride,dt,frames,
  finite_rows,final_half_start_step,final_half_frames,selected_steps,
  serialized_rows,minimum_sampled_bond,schedule_hash,statistics_hash,selected_hash,
  host_bytes,gpu_bytes=0.
  host_bytes reports actual extra vector capacities; selected rows are streamed.
  Missing/partial files are not valid completion. Metadata is finalized last.

Schedule checksum: initialize h=14695981039346656037; for each observed step in
order set h=(1099511628211*h+step+1) modulo2^64. Encode as exactly16 lowercase
hex digits. Every chain has its own counter/hash and strict expected next step;
record ordering is checked. The metadata hash must agree with all chain hashes
and the independently reconstructed F-step schedule. This checksum detects
accidental coverage/order errors; it is not cryptographic authentication.
For record_hash apply the same recurrence to each CSV field in order except
record_hash: integer fields as uint64 words, schedule_hash as its uint64 value,
and finite doubles as IEEE754 binary64 bit words. statistics_hash applies the
recurrence to the ascending record_hash words. selected_hash applies it to every
selected row field in order (step/time/chain then original scalars), with time
and scalar values as binary64 words. These detect accidental value corruption
as well as missing/reordered records. Runner SHA-256 file proofs and versioned
provenance protect the serialized files. They do not sign against malicious
rewriting of both data and checksums.

Every original scalar is evaluated. finite_rows counts rows where all original
fields are finite; all-frame minima retain the legacy domain check in analysis.
On the first invalid scalar/summary, scalar_failure.json records step/chain/reason
and scalar_failure_positions.csv preserves the full observation configuration.
These are fatal acceptance evidence. Integration is not silently skipped or
regularized; full-mode arithmetic/behavior stays unchanged. Degenerate smooth
zero-rest-length bonds remain force-defined; an undefined tangent remains NaN,
as in full mode. Frozen analyzer positivity/finiteness rules are not relaxed.
Summary overflow is reported explicitly, never clamped.

## Authenticated execution overlay

The profile generator writes a NEW root, preserving a separately generated/read-
only full parent campaign. execution-profile.json pins parent path/manifest hash,
original plan hash, this schema hash, build path and profile version. Its derived
manifest maps each parent ID to a new ID/command/output under the new root.
Only stream and memory phases add --scalar-output compact; diagnostic/reference
phases retain full mode (and all reference stress dumps). All physical arguments,
seeds,strides,counts,dt and durations remain unchanged. No hidden environment
switch, command mutation or legacy-run adoption is permitted. Overlay validation
reconstructs this mapping exactly and authenticates the parent first.

Receipts/checkpoints/output directories are separate; provenance pins manifest,
profile/schema,binaries and approved source versions. Legacy and current driver
source identities are distinguished. Cached analysis cannot cross manifest or
profile identities. Production monitoring uses the flushed initial-bond records,
which exist in either output mode, rather than samples.csv. Receipts distinguish
child execution, scalar/stress validation, hashing, completion and interruption,
with separate timings; child exit0 alone is not accepted completion.

Independent-chain clustering and all stress gates are unchanged. Selected rows
are diagnostic context, not replacement inputs for all-time MSD or thinned-frame
means. Original Stage4A.2/Rouse output remains full. This is an operational schema
addendum; reducing actual observation/stress frequency, changing windows or
thresholds would require a separate scientific protocol amendment. None is made.
