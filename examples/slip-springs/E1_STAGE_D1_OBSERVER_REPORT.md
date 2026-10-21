# E1 Stage D1.0 — read-only equilibrium observer

Implementation and bounded technical verification, 21 October 2026. Starting
local and independently queried remote `slip-springs` HEAD both matched
`ad5a741d1c986a9f57d7d3cdbeab6b2a815aee1a`; tracked tree initially clean.
Stages A–C, E1, D0/D0.1, project status, local rules and reuse roadmap were
inspected. **Independent observer acceptance is still required. No Stage D1/D2
scientific pilot, production campaign or timestep validation was performed.**

## Architecture, phase and non-perturbation

`e1_equilibrium_observer.h` is a host-only serializer with const state inputs;
it has no CUDA kernel or RNG dependency. The driver opts in only through
`--equilibrium-steps FILE`. Disabled behavior has no observer allocation or
readback. All force, Brownian, hopping/renewal, initializer, RNG and stress
implementations remain unchanged; the integration/event loop's only functional
addition is a read-only observation after its existing completed-step barrier.

Step 0 observes the actual initialized, precision-rounded state before any
update. Later observations occur after the BD update, coordinate-buffer swap,
the entire sequential hopping/renewal batch and existing invariant readback.
The blocking default-stream D2H copies see that same completed `(R_n,S_n,A_n)`.
At final step, the existing later force evaluation changes no positions or
attachments. No observation occurs at the pre-BD or intermediate post-BD phase.

The existing scalar reduction code computes Re², Rg², bond moments and tangent
separations 1–4 once per requested state. Existing `samples.csv` supplies those
values at legacy `--sample` steps. A supplement supplies only observer steps
between legacy samples; long tangents reuse the already computed bonds/lengths.
Extra frames do **not** accumulate old bond histograms, change their frame count,
change `minimum_sampled_bond`, or enter old scalar files. This preserves legacy
bytes even for an irregular observer schedule. Existing initial/final files and
counter meanings remain unchanged. No observer draw consumes simulation RNG.

For active hopping the observer copies stable slots, occupancy, dense anchors
and cumulative counters to existing host buffers. Observer-owned slot/map copies
are checked for dimensions, finite positions/anchors, single occupancy, exact
dense/slot agreement, chain assignment, full contour links and global population.
With NU=0, where production has no slots, fixed identities are assigned in
initial site order for diagnostics only; they stay fixed. Z=0 is supported with
all populations zero and header-only connector/attachment files. Empty chains,
multiple springs per chain and full occupancy are supported.

## Schedule semantics and version-1 schemas

The input is whitespace-separated **unsigned integer BD steps**. It must be
sorted, unique, in `[0,steps]`, start at zero and include final `steps`. Both
schedules are validated before creating the output directory or executing CUDA.
Decimals, signs, exponent notation, overflow and time-valued requests are
rejected; there is no floating-time conversion or silent rounding. Time is the
same `double(step)*dt` convention as legacy scalars, with integer step primary.
This supports dt=1e-4,2.5e-4,5e-5 without freezing their scientific use.

A schedule is validated in one pass and streamed from the same open file in a
second pass, O(1) schedule storage. Count/order checks and an internal rolling
fingerprint reject inconsistent consumption or changed content before completion;
this fingerprint is not campaign authentication. Optional
`--equilibrium-snapshots FILE` is a subset of observer steps with the same ordering
rules, includes zero/final, and has at most **eight** entries. Default: zero/final
(one snapshot for zero steps). The schedule can be early-dense and later-sparse;
it changes neither dt nor the legacy sample stride. The driver observes the union
of the two cadences but writes each output only at its declared steps.

All CSVs use zero-based chain/bead/stable spring IDs, 17-digit numeric output,
and explicit `step,time`. `equilibrium_schema.json` carries version 1, phase,
dt, final step, legacy stride, M,m,Z, canonical mode, expected observation count
and the bounded snapshot step list. Existing model coefficients and precision
remain in `parameters.txt` and `metadata.json`.

| File | Row identity and payload |
|---|---|
| Existing `samples.csv` | Legacy per-chain sizes, bond moments, minimum length and tangents 1–4; join by step/chain at observer steps divisible by legacy stride |
| `equilibrium_backbone.csv` | Only scheduled **nonlegacy** steps, one row/chain: mean_r, mean_r2, re2, rg2, min_length and supported tangents 1–4; no duplicated legacy scalar rows |
| `equilibrium_tangents.csv` | Each scheduled step/chain when supported: tangent8 for N>8, tangent16 for N>16; header only for N<=8 |
| `equilibrium_sites.csv` | Each scheduled step, every chain/bead, spring ID or -1 for vacant; retains individual-site occupancy and chain identity |
| `equilibrium_connectors.csv` | Each scheduled step, every live ID: chain, bead, ex,ey,ez,e2, with e=r_site-a and e2=e.e |
| `equilibrium_chains.csv` | Each scheduled step, every chain: z,ex_sum,ey_sum,ez_sum,e2_sum, including zero rows for empty chains |
| `equilibrium_events.csv` | Each scheduled step: previous_step, interval_time, and the eleven counter **differences** below; initial interval/differences are zero |
| `equilibrium_positions.csv` | Only selected snapshot steps: complete unwrapped bead x,y,z |
| `equilibrium_attachments.csv` | Same snapshot steps: complete live IDs, chain, bead, ax,ay,az, previous,next contour IDs (-1 at free ends) |
| `equilibrium_complete.json` | Final version-1 completion record, frame count, file sizes and observer telemetry; published by same-directory rename only after data close and successful legacy final output/metadata |

The complete snapshot is positions + attachments + same-step sites. It retains
state associations and contour links but is **not a restart checkpoint**.
Coordinates/anchors are not serialized at arbitrary observer frames. Raw live
connectors permit component variances, cross moments, radial/CDF diagnostics and
conditional distributions without choosing bins or throwing away tail values.
Tangent(s) is the mean over N-s bond pairs in each chain, defined only for s<N.
Bond moments in each frame are means over that chain's N bonds. Existing
`bond_statistics.csv` remains the legacy final-half per-bond aggregate, not a new
D1 drift estimator. No density, stress or diffusion observable is added.

The interval counter columns, in accepted semantic order, are:

```text
batches,attempts,accepted,boundary,occupied,metropolis,
renewal_proposed,renewal_accepted,renewal_occupied,renewal_same_chain,renewal_cross_chain
```

`accepted` means interior hops only. `boundary` means outward proposals with
canonical renewal enabled, and rejected outward attempts otherwise. `occupied`
means interior occupancy rejections; `metropolis` means interior energy
rejections. `renewal_proposed` includes occupied-end rejections, and equals
boundary in canonical mode. `renewal_occupied` is separate. An occupied source
end remains a renewal rejection under the accepted pre-event occupancy rule.
The serializer checks monotonic counters and both cumulative and interval
identities:

```text
attempts = accepted + boundary + occupied + metropolis
renewal_proposed = renewal_accepted + renewal_occupied
renewal_accepted = renewal_same_chain + renewal_cross_chain
```

Record physical interval duration from integer endpoints; final-step inclusion
prevents an omitted final partial interval. These are exact count identities,
not Poisson assumptions about accepted events. No event engine or counter is
modified. Per-ID renewal coverage and per-chain event entry/exit counters are
not newly instrumented; endpoint records cannot reconstruct every event.

To reconstruct the D0 joint statistics, join per-chain Re² with z/e2_sum. With
`f_c=Re²_c/<Re²>_bb-1`, `rho=Z/(M*m)` and
`sigma_Z²=m*rho*(1-rho)*(M*m-m)/(M*m-1)`:

```text
A_joint = sum_c f_c*(z_c-Z/M) / (M*sigma_Z)
B_joint = sum_c f_c*(e2_sum_c-z_c*A2) / (Z*A2)
```

A_joint is undefined when sigma_Z=0 (Z=0 or full occupancy); B_joint is
undefined at Z=0. These degenerate cases are technical fixtures, not D0
canonical mixing cells. Reference targets
and error budgets belong to the separately approved scientific analysis. Frames,
chains, connectors and contour pairs are not independent statistical replicas.

## Correctness, failure and regression evidence

`e1_observer_check.py` streams one observation at a time, merges legacy scalar
rows with the supplement, checks exact version-1 headers, completion/file sizes,
integer/time identity, row counts/order, unique sites, populations, connector
squares/sums and interval identities. At every selected snapshot it independently
reconstructs bonds, sizes, tangents, connectors and links using NumPy, with
3e-12 absolute/relative reconstruction tolerances. These floating reconstruction
tolerances are software checks, **not amendments to D0 accuracy margins**.

`tests/test_e1_observer.py` compares on/off pairs using the same seed and
parameters in **both single and double precision**. Each main fixture has M=4,
12 BD steps, sample stride 4, seed 914203, A2=5, and observation/snapshot steps
`0,1,2,5,12`. Thus steps 1,2,5 explicitly exercise extra observer frames. All
observations have full snapshots for independent reconstruction. The six cases:

| N | kappa | dt | Z | nu_hop | Coverage |
|---:|---:|---:|---:|---:|---|
| 8 | 0 | 1e-4 | 6 | 20000 | Flexible, accepted hops, same/cross-chain renewal |
| 32 | 10 | 2.5e-4 | 6 | 20000 | Stiff, tangents 8/16, accepted interior hops |
| 8 | 10 | 5e-5 | 6 | 20000 | Reserved-step compatibility |
| 8 | 0 | 2.5e-4 | 0 | 0 | Bare/empty-spring limit |
| 8 | 10 | 1e-4 | 6 | 0 | Fixed attachments, no event counters |
| 1 | 0 | 2.5e-4 | 8 | 20000 | Fully occupied sites, renewal rejections, no tangent pairs |

The deliberately high test rate exercises event branches in a few steps; it is
not a pilot rate proposal. Empty and multiply occupied chains are present and
checked across the fixtures. Flexible accepted interior/cross/same-chain counts
were **80/9/3 single**, **73/10/2 double**; full-occupancy fixtures each recorded
222 occupied-renewal rejections. N32 had 231/235 accepted hops, respectively;
its tiny fixture had no renewal, so cross-chain coverage is asserted across the
fixture set rather than demanded from every stochastic case. No result is a
scientific equilibrium or rate-accuracy test.

For every pair, initial/final coordinates, initial/final spring states, legacy
scalar/bond outputs, parameters and hopping metadata were **byte-identical**.
Main metadata was byte-identical after replacing only timing/rate-valued fields;
all remaining fields, including capacities, launches, initialization identities,
minimum bond and output/timer descriptions, matched. Every saved endpoint also
matched the actual legacy initialized/final state. Snapshot-derived D0 A_joint
and B_joint matched streamed-state reconstructions using the independent
backbone target helper; no fit to observed equilibrium was performed.

Four new Python tests passed per precision (3.493 s single, 3.515 s double).
The additional 13-step Stage B pair ends between legacy samples and tests a
nonlegacy final snapshot/partial interval with renewal disabled, retaining all
legacy bytes and boundary-rejection semantics. They also cover zero steps,
default two-snapshot behavior, invalid/missing/
duplicate/out-of-range/noninteger schedules, invalid snapshot subsets/caps,
time-valued option rejection, missing completion marker and truncated output.
The host C++ fixture checks read-only input bytes, malformed state and contour
links, nonfinite inputs/derived diagnostics, inconsistent counters, incomplete
frames/finish, and `/dev/full` write failures. Failed runs have no completion
marker and must be excluded, retaining their partial artifacts as failure
records. Ordinary stream open/write/flush/close errors propagate to a nonzero
exit; no observation is silently discarded.

Final host ASan/UBSan/LSan verification passed without suppression. CUDA
**memcheck, racecheck, initcheck and synccheck** each passed with zero reported
errors/hazards in both precisions on a 12-step N8,kappa10,M4,Z6 technical fixture.
The existing `check`, `check-lifetime`, `check-semiflexible`,
`check-semiflexible-stress` and fixed-slip Python regressions passed in both
precisions. Semiflexible suites comprise 7 GPU, 2 host-analysis and 12 independent
reference tests per precision; stress has 7 tests and fixed-slip 4. Original
lifetime tests passed 200 ownership cycles, and worker sanitizer checks passed.
Existing historical criteria, campaign authentication and source allowlists were
not edited or bypassed; no frozen campaign was executed.

## Bounded runtime and memory

Development host: RTX 3060 Ti (sm_86), driver 580.178.04, CUDA **13.0.88** via
`/usr/local/cuda`, g++ 11.4, Python 3.10.12, NumPy 2.2.4; one OpenBLAS thread.
System `/usr/bin/nvcc` is the separately installed CUDA 11.5.119, unused here.
GPU and leak-sanitizer runs used execution outside the sandbox to access the
GPU driver/thread inspection. Builds went to isolated `/tmp` directories.

Measured five-frame technical fixtures (milliseconds; not repeated benchmarks):

| Precision | N,kappa | Production wall off / on | Observer call wall | Observer-exclusive work | D2H time | D2H bytes |
|---|---|---:|---:|---:|---:|---:|
| single | 8,0 | 1.098 / 1.567 | 0.527 | 0.457 | 0.118 | 7880 |
| single | 32,10 | 1.673 / 2.878 | 1.278 | 1.156 | 0.120 | 25160 |
| double | 8,0 | 1.161 / 1.646 | 0.567 | 0.498 | 0.118 | 14120 |
| double | 32,10 | 1.997 / 3.144 | 1.223 | 1.069 | 0.122 | 46760 |

`observer_wall_seconds` includes the shared scalar reduction and D2H, validation,
new serialization/flushes and any coincident legacy scalar write.
`exclusive_seconds` measures the new state transfers, validation, long tangents
and observer serialization, excluding shared backbone work. Legacy observation
seconds exclude this exclusive work; legacy output seconds retain their old
scope. Transfer time/bytes include the shared coordinate readback at scheduled
frames: do not add these overlapping timers or call all bytes incremental.
Constructor/schema output belongs to initialization; final close/marker publication
is outside the production and observer-call timers, as is legacy main metadata.
These sub-millisecond differences are noisy, not estimates of pilot throughput.

**Additional device allocation is zero**, confirmed by unchanged on/off device
capacities/metadata. Production readbacks reuse existing position, dense-anchor,
slot and occupancy host storage. Actual observer vector capacity payloads were:

| M,N,Z | Persistent sums/map bytes | Peak temporary slot/map bytes | Total tracked extra vector bytes |
|---|---:|---:|---:|
| 4,8,6 | 304 | 384 | 688 |
| 4,32,6 | 688 | 768 | 1456 |

On this ABI `sizeof(ChainSums)=sizeof(Slot)=40`, int=4. Persistent payload is
40M+4L; temporary payload is 40Z+4L. Snapshot IDs use at most eight integers;
file/schedule buffers and object/allocator overhead are constant in frame count.
An unsanitized glibc `mallinfo2().uordblks` measurement around construction in
the M3,N2 host fixture found **79,328 additional heap bytes**, including streams,
paths, the streaming schedule and persistent arrays; this is a host-fixture
allocator measurement, not a portable total-process RSS or GPU-memory figure.
ASan's allocator does not provide that glibc measurement (it reports zero there).
No memory slope against long trajectories is inferred. Allocation structure is
O(L+Z), independent of observation count; output disk grows with frames. The
existing 2-GiB workspace guard includes the new vector estimate. There is no
buffer for an entire coordinate history, event history or observation schedule.

## Reproducible verification and evidence

From the repository root, representative **executed** commands below use fresh
output paths; simulator outputs and host fixtures refuse existing directories.
README contains the executed 12-step/64-step double-precision examples (both
checkers passed; 5/7 observations, two snapshots each). These remain technical
serialization examples, not pilot manifests.

```sh
D1_BUILD=/tmp/e1-d1-build
for precision in single double; do
  make -C examples/slip-springs semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION="$precision" GPU_BUILD="$D1_BUILD/$precision"
done
# The evidence root must be new; omit it to use automatically cleaned fixtures.
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 180s python3 examples/slip-springs/tests/test_e1_observer.py "$D1_BUILD/single/semiflexible" /tmp/e1-d1-final-evidence-v4/single -v
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 timeout 180s python3 examples/slip-springs/tests/test_e1_observer.py "$D1_BUILD/double/semiflexible" /tmp/e1-d1-final-evidence-v4/double -v

c++ -std=c++17 -O2 examples/slip-springs/tests/e1_observer_host.cpp -o /tmp/e1-d1-host/observer_host
/tmp/e1-d1-host/observer_host /tmp/e1-d1-host/fixture-memory
c++ -std=c++17 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer examples/slip-springs/tests/e1_observer_host.cpp -o /tmp/e1-d1-host/observer_asan
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 timeout 60s /tmp/e1-d1-host/observer_asan /tmp/e1-d1-host/final-asan
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 examples/slip-springs/e1_observer_check.py /tmp/e1-d1-host/fixture-memory

mkdir -p /tmp/e1-d1-final-sanitizers
printf '0 1 2 5 12\n' > /tmp/e1-d1-final-sanitizers/steps
for precision in single double; do
  for tool in memcheck racecheck initcheck synccheck; do
    timeout 60s /usr/local/cuda/bin/compute-sanitizer --tool "$tool" --error-exitcode 99 "$D1_BUILD/$precision/semiflexible" --output "/tmp/e1-d1-final-sanitizers/$precision-$tool" --springs 8 --chains 4 --steps 12 --sample 4 --seed 914203 --kappa 10 --dt .00025 --slip-count 6 --slip-ms2 5 --hop-rate 20000 --end-renewal 1 --equilibrium-steps /tmp/e1-d1-final-sanitizers/steps --equilibrium-snapshots /tmp/e1-d1-final-sanitizers/steps
  done
done
```

Additional executed regression commands (all with
`PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1`, timeouts 60–240 s):

```sh
make -C examples/slip-springs check check-lifetime CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single BUILD=/tmp/e1-d1-original/cpu GPU_BUILD=/tmp/e1-d1-original/single
make -C examples/slip-springs check check-semiflexible-stress check-lifetime CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double BUILD=/tmp/e1-d1-original/cpu GPU_BUILD=/tmp/e1-d1-original/double
make -C examples/slip-springs check-semiflexible check-semiflexible-stress CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=single BUILD=/tmp/e1-d1-original/cpu GPU_BUILD=/tmp/e1-d1-build/single
make -C examples/slip-springs check-semiflexible CUDA_HOME=/usr/local/cuda CUDA_ARCH=sm_86 PRECISION=double GPU_BUILD=/tmp/e1-d1-build/double
python3 examples/slip-springs/tests/test_fixed_slip_springs.py /tmp/e1-d1-build/single/semiflexible
python3 examples/slip-springs/tests/test_fixed_slip_springs.py /tmp/e1-d1-build/double/semiflexible
```

Final paired raw observer outputs and timing/capacity records are under
`/tmp/e1-d1-final-evidence-v4/{single,double}/`; sanitizer outputs/logs are under
`/tmp/e1-d1-final-sanitizers/`; host fixtures under `/tmp/e1-d1-host/`;
README examples under `/tmp/e1-d1-example.xi5G5J/`. Local evidence/binary
SHA256 receipts (419 files) were saved to `/tmp/e1-d1-verification-SHA256SUMS`.
Final tested binary SHA256 values:

```text
single e02320178dcf17072395dea0ad6b0527be6c40a793f1459460c7dd2521d2815d
double 4246b6e01926b5de6ef5d10c1ed5eb835edc4858aab5324087c6845e445ac2c4
```
 Build/regression logs are
`/tmp/e1-d1-build-{single,double}.log`, `/tmp/e1-d1-original-{single,double}.log`,
`/tmp/e1-d1-final-regressions-{single,double}.log`, and
`/tmp/e1-d1-fixed-{single,double}.log`. These local temporary artifacts are not
a permanent scientific archive; this committed report and runnable tests
preserve the bounded verification result. Earlier intermediate builds/checks
were rerun after the observer output was reduced to reuse legacy rows.

## Limitations and review gate

The checker is a structural/snapshot audit, not an equilibrium analysis or
campaign authenticator. Completion markers/file sizes reject incomplete output;
they do not provide cryptographic integrity, durable fsync/restart guarantees
or detect every same-length modification. Future scientific runs still need
approved source/executable/schedule/parameter identities, raw SHA256 receipts,
reference error budgets and separately reviewed analysis. No historical source
allowlist is changed to accept this later executable. No timestep proposal or
D0 accuracy margin is changed. Programmatic isolation checks found every tracked,
untracked and ignored path within `examples/slip-springs/`, including comparison
against the Stage0 source `81fe5de9cd5ded849202eebab7c14e6bd35fb9ae`. Force,
Brownian, hopping/renewal, initialization and D0/D0.1 authority files were verified
byte-identical to starting HEAD. `git diff --check` passed.

Per-ID renewal history/coverage, per-chain event entry/exit instrumentation,
D2 state imports, restart, stress, rheology and terminal dynamics remain absent.
All live connector values are retained, so observation output volume can dominate;
there is no compression or asynchronous I/O optimization. Only selected snapshots
permit independent positional reconstruction between endpoints. Non-perturbation
is established for the bounded tested pairs and precisions, not every hardware/
compiler configuration. High-rate technical timings do not predict pilot costs.

Independent acceptance of this observer and a separately approved pilot manifest,
resource caps and scientific analysis are required before Stage D1 validation.
